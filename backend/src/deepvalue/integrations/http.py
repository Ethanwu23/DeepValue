import time
import httpx
from deepvalue.contracts.common import CapabilityError


class HttpGateway:
    """只对明确的暂时性错误重试，每次尝试共享同一预算。"""
    def __init__(self, client: httpx.Client, budget, sleep=time.sleep):
        self.client, self.budget, self.sleep = client, budget, sleep

    def get_json(self, url, *, params=None, headers=None, timeout=40):
        for attempt in range(2):
            self.budget.reserve()
            try:
                response = self.client.get(url, params=params, headers=headers,
                                           timeout=min(timeout, self.budget.remaining()),
                                           follow_redirects=False)
            except (httpx.TimeoutException, httpx.ConnectError):
                code = "SOURCE_TIMEOUT"
            except httpx.RequestError:
                raise CapabilityError("SOURCE_UNAVAILABLE", "http", "来源连接失败") from None
            else:
                if response.status_code in (429, 502, 503, 504):
                    code = "SOURCE_RATE_LIMITED" if response.status_code == 429 else "SOURCE_UNAVAILABLE"
                elif response.status_code != 200:
                    raise CapabilityError("SOURCE_UNAVAILABLE", "http", "来源返回不可重试状态")
                else:
                    try:
                        return response.json()
                    except ValueError:
                        raise CapabilityError("SOURCE_SCHEMA_ERROR", "http", "来源未返回有效JSON") from None
            if attempt == 0:
                if self.budget.remaining() <= 1:
                    raise CapabilityError("DEADLINE_EXCEEDED", "http", "剩余时间不足以重试")
                self.sleep(1)
        raise CapabilityError(code, "http", "来源请求失败，尝试次数已耗尽")
