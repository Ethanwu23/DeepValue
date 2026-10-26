"""请求日志中间件的回归测试。

直接调用 `agent.app.log_requests`，不经过 TestClient，这样可以精确观测异常是否向上传播，
也避免为了异步测试引入额外依赖。

覆盖：
- 合法 JSON 请求体记录结构化数据
- 非 JSON 请求体回退记录原文
- 非 UTF-8 请求体回退记录可解码文本，而不是再次抛出 UnicodeDecodeError
- 请求体解析过程中产生的 SystemExit 不得被中间件吞掉
"""

import asyncio
import json

import pytest
from starlette.requests import Request
from starlette.responses import Response

from agent import app as app_module


def _make_request(body: bytes) -> Request:
    """构造一个带请求体的 HTTP scope，供中间件直接消费。"""
    async def receive():
        return {"type": "http.request", "body": body, "more_body": False}

    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/probe",
        "raw_path": b"/probe",
        "query_string": b"",
        "headers": [(b"content-type", b"application/json")],
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 80),
        "root_path": "",
    }
    return Request(scope, receive)


def _run_middleware(body: bytes) -> Response:
    """同步驱动一次中间件调用，返回下游响应。"""
    async def scenario():
        request = _make_request(body)

        async def call_next(_request):
            return Response(status_code=404)

        return await app_module.log_requests(request, call_next)

    return asyncio.run(scenario())


def _record_calls(monkeypatch) -> list:
    """把 log_request_details 换成记录器，返回被记录的载荷列表。"""
    recorded: list = []
    monkeypatch.setattr(app_module, "log_request_details", recorded.append)
    return recorded


def test_valid_json_body_is_logged_as_structured_data(monkeypatch):
    recorded = _record_calls(monkeypatch)

    response = _run_middleware(b'{"company": "CAT"}')

    assert response.status_code == 404
    assert recorded == [{"company": "CAT"}]


def test_non_json_body_falls_back_to_raw_text(monkeypatch):
    recorded = _record_calls(monkeypatch)

    response = _run_middleware(b"plain text body")

    assert response.status_code == 404
    assert recorded == ["plain text body"]


def test_non_utf8_body_is_logged_as_text_instead_of_raising(monkeypatch):
    """非 UTF-8 请求体必须回退成可解码文本，不得让解析异常外溢成错误日志。"""
    recorded = _record_calls(monkeypatch)

    response = _run_middleware(b"\xff\xfe\x00cat")

    assert response.status_code == 404
    assert len(recorded) == 1
    assert "cat" in recorded[0]


def test_systemexit_from_body_parsing_is_not_swallowed(monkeypatch):
    """bare except 会吞掉 SystemExit / KeyboardInterrupt，阻塞进程正常退出。"""

    def _raise_systemexit(*_args, **_kwargs):
        raise SystemExit("模拟进程退出信号")

    monkeypatch.setattr(json, "loads", _raise_systemexit)

    with pytest.raises(SystemExit):
        _run_middleware(b'{"probe": 1}')
