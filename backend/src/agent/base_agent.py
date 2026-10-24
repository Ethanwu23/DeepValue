import os
import copy
import traceback
import time
import threading
from loguru import logger
from agent.llm.llm import OpenAICompatibleLLM
from dashscope import Application
from agent.post import Post
import json


class RateLimiter:
    """
    简单的令牌桶速率限制器
    用于控制API请求频率，避免触发429错误
    """
    def __init__(self, max_qps: float = 15.0):
        """
        初始化速率限制器
        
        Args:
            max_qps: 最大每秒请求数，默认15 QPS
        """
        self.max_qps = max_qps
        self.min_interval = 1.0 / max_qps  # 最小请求间隔（秒）
        self.last_request_time = 0
        self.lock = threading.Lock()
        logger.info(f"速率限制器已初始化: 最大QPS={max_qps}, 最小间隔={self.min_interval:.3f}秒")
    
    def acquire(self):
        """
        获取请求许可，如果频率超限则等待
        
        Returns:
            float: 实际等待的时间（秒）
        """
        with self.lock:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            
            if time_since_last < self.min_interval:
                wait_time = self.min_interval - time_since_last
                logger.debug(f"速率限制：需要等待 {wait_time:.3f} 秒")
                time.sleep(wait_time)
                self.last_request_time = time.time()
                return wait_time
            else:
                self.last_request_time = current_time
                return 0.0


# 全局速率限制器实例（单例模式）
_web_search_rate_limiter = None

def get_web_search_rate_limiter(max_qps: float = None) -> RateLimiter:
    """
    获取全局Web搜索速率限制器实例
    
    Args:
        max_qps: 最大QPS，如果为None则从环境变量读取或使用默认值
        
    Returns:
        RateLimiter: 速率限制器实例
    """
    global _web_search_rate_limiter
    
    if _web_search_rate_limiter is None:
        if max_qps is None:
            # 从环境变量读取，默认为12 QPS（留有余量）
            max_qps = float(os.getenv("WEB_SEARCH_MAX_QPS", "12"))
        _web_search_rate_limiter = RateLimiter(max_qps=max_qps)
    
    return _web_search_rate_limiter

class Agent:
    step_prompt = """{prompt}"""
    def __init__(self, model_id="qwen2.5-72b-instruct"):
        self.llm = OpenAICompatibleLLM(model_id=model_id)

    def __call__(self, prompt):
        response = self.llm.generate_response(prompt)
        return response

    def set_step_prompt(self, prompt):
        self.step_prompt = prompt

    def step(self, **kwargs):
        step_prompt = self.prompt_format(self.step_prompt, **kwargs)
        response = ""
        for attempt in range(3):
            try:
                response = self(step_prompt)
                response = self.post_process(response)
                break
            except Exception as e:
                logger.error(f"大模型调用错误：{e}\n{traceback.format_exc()}")
                if attempt == 2:
                    raise
                continue
        return response

    def post_process(self, response):
        return response

    def prompt_format(self, prompt, **kwargs):
        prompt_ = copy.deepcopy(prompt)
        for k in kwargs.keys():
            rep = "{"+k+"}"
            prompt_ = prompt_.replace(rep, str(kwargs[k]))
        return prompt_


class JsonAgent(Agent):
    def __init__(self, model_id="qwen2.5-72b-instruct", keys=None):
        super().__init__(model_id)
        self.keys = keys

    def post_process(self, response):
        result = json.loads(Post.extract_pattern(response, pattern="json"))
        if not self.keys:
            return result
        return self.keys(**result)


class MCPAgent(Agent):

    def step(self, **kwargs):
        try:
            step_prompt = self.step_prompt.format(**kwargs)
        except Exception as e:
            step_prompt = self.step_prompt

        for _ in range(3):
            try:
                response = Application.call(
                    api_key=os.getenv("APP_TOKEN"),
                    app_id=os.getenv("MCP_APP_ID"),
                    prompt = step_prompt,
                    biz_params=kwargs
                )
                response = self.post_process(response)
                if response is None:
                    raise Exception("MCP返回结果不正确")
                return response
            except Exception as e:
                logger.error(f"MCP调用错误：{e}\n{traceback.format_exc()}")
                continue
        return None

    def post_process(self, response):
        if response.status_code == 200:
            response = json.loads(response.output.text)
            return response
        else:
            logger.error(f"MCP调用失败：{response}")
            return None


class WebSearchAgent(MCPAgent):
    def step(self, prompt, *, count: int = 10):
        try:
            step_prompt = self.step_prompt.format(prompt=prompt)
        except Exception as e:
            step_prompt = self.step_prompt

        api_key = os.getenv("APP_TOKEN")
        app_id = os.getenv("MCP_APP_ID")
        
        # 获取速率限制器
        rate_limiter = get_web_search_rate_limiter()
        
        for attempt in range(3):
            try:
                # 在发送请求前进行速率限制检查
                wait_time = rate_limiter.acquire()
                if wait_time > 0:
                    logger.debug(f"速率限制等待: {wait_time:.3f}秒")
                
                response = Application.call(
                    api_key=api_key,
                    app_id=app_id,
                    prompt = step_prompt,
                    biz_params={"count": count}
                )
                response = self.post_process(response, expected_count=count)
                return response
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Web搜索错误（尝试 {attempt + 1}/3）：{e}\n{traceback.format_exc()}")
                
                if attempt == 2:
                    raise

                # 如果是429错误，增加等待时间后重试
                if "429" in error_msg:
                    wait_time = 5 * (attempt + 1)  # 递增等待时间：5秒、10秒、15秒
                    logger.warning(f"检测到429错误，等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                elif attempt < 2:  # 非429错误，短暂等待后重试
                    time.sleep(2)
                continue

    def post_process(self, response, *, expected_count: int):
        """解析当前工作流输出的 MCP 结果 JSON 和紧随其后的数量字段。"""
        if response is None:
            raise ValueError("搜索应用未返回响应")
        if response.status_code != 200:
            raise RuntimeError(f"搜索应用请求失败，HTTP {response.status_code}")

        # 工作流将工具结果和 count 两个输出串接；必须完整解析并校验两段。
        text = response.output.text.strip()
        result, offset = json.JSONDecoder().raw_decode(text)
        returned_count = json.loads(text[offset:])
        if type(returned_count) is not int or returned_count != expected_count:
            raise ValueError("搜索应用返回的数量字段与请求不一致")
        if not isinstance(result, dict):
            raise ValueError("搜索应用的工具结果必须为 JSON 对象")
        if result.get("isError") is not False:
            raise RuntimeError("搜索应用返回 MCP 工具错误")

        content = result.get("content")
        if not isinstance(content, list) or len(content) != 1:
            raise ValueError("搜索应用必须返回一个文本结果块")
        item = content[0]
        if not isinstance(item, dict) or item.get("type") != "text":
            raise ValueError("搜索应用结果块必须为 text 类型")
        payload = json.loads(item["text"])
        if not isinstance(payload, dict):
            raise ValueError("搜索结果正文必须为 JSON 对象")
        if payload.get("status") != 0:
            raise RuntimeError(f"搜索服务返回错误状态：{payload.get('status')}")
        pages = payload.get("pages")
        if not isinstance(pages, list):
            raise ValueError("搜索结果必须包含 pages 列表")

        processed_pages = []
        for page in pages:
            if not isinstance(page, dict):
                raise ValueError("搜索页面必须为对象")
            if any(not isinstance(page.get(key), str) for key in ("snippet", "title", "url")):
                raise ValueError("搜索页面的 snippet、title、url 必须为字符串")
            if not page["url"].startswith(("https://", "http://")):
                raise ValueError("搜索页面缺少有效的 HTTP 地址")
            processed_pages.append({key: page[key] for key in ("snippet", "title", "url")})
        return processed_pages


if __name__ == '__main__':
    agent = WebSearchAgent()
    response = agent.step(prompt="稳定币", count=10)
    logger.info(response)