import json


def parse_search_response(response, *, expected_count: int):
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
