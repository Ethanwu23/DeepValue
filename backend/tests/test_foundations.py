"""验证共享契约、并发预算与接入失败边界，不调用真实服务。"""
import json
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from types import SimpleNamespace
import httpx
import pytest
from pydantic import ValidationError
from deepvalue.config import Settings, parse_models
from deepvalue.contracts.research import ResearchRequest
from deepvalue.contracts.common import CapabilityError, RoleResult
from deepvalue.runtime.budget import Budget
from deepvalue.integrations.http import HttpGateway
from deepvalue.integrations.search import parse_search_response
from deepvalue.integrations.structured import invoke_structured


def test_google_request_and_decimal_contract():
    req = ResearchRequest(as_of="2025-03-01", model="research")
    assert (req.ticker, req.cik, req.industry) == ("GOOGL", "0001652044", "computer_services")
    assert req.pe_low == Decimal("10")
    with pytest.raises(ValidationError):
        ResearchRequest(as_of="2025-03-01", model="research", years=3.5)
    with pytest.raises(ValidationError):
        req.ticker = "OTHER"


@pytest.mark.parametrize("raw", ["", "[]", "{}", '[{"model_id":"x","display_name":"X"},{"model_id":"x","display_name":"X"}]'])
def test_model_config_never_falls_back(raw):
    with pytest.raises(CapabilityError) as error:
        parse_models(raw)
    assert error.value.info.code == "CONFIG_ERROR"


def test_snapshot_does_not_contain_credentials():
    env = dict(APP_TOKEN="secret-token", MCP_APP_ID="private-app", FRED_API_KEY="private-fred",
               SEC_USER_AGENT="private-contact", LLM_BASE_URL="https://model.example/v1",
               AVAILABLE_MODELS='[{"model_id":"research","display_name":"Research"}]')
    config = Settings.load(env)
    snapshot = json.dumps(config.public_snapshot())
    assert all(env[k] not in snapshot for k in ("APP_TOKEN", "MCP_APP_ID", "FRED_API_KEY", "SEC_USER_AGENT"))
    env.pop("FRED_API_KEY")
    with pytest.raises(CapabilityError):
        Settings.load(env)


def test_atomic_budget_and_cancellation():
    budget = Budget(requests=3)
    def acquire(_):
        try:
            budget.reserve()
            return True
        except CapabilityError:
            return False
    with ThreadPoolExecutor(max_workers=8) as executor:
        assert sum(executor.map(acquire, range(30))) == 3
    budget.cancel()
    with pytest.raises(CapabilityError) as error:
        budget.reserve()
    assert error.value.info.code == "CANCELLED"


def test_model_budget_is_part_of_global_budget():
    budget = Budget(requests=4, models=1)
    budget.reserve(model=True)
    with pytest.raises(CapabilityError):
        budget.reserve(model=True)
    assert budget.requests == budget.models == 1


def test_deadline_prevents_network():
    now = [0]
    budget = Budget(clock=lambda: now[0], seconds=10)
    now[0] = 5
    with pytest.raises(CapabilityError):
        budget.reserve()
    assert budget.requests == 0


def test_http_retry_is_counted_and_protocol_error_is_not_retried():
    calls = []
    def respond(request):
        calls.append(request)
        return httpx.Response(429 if len(calls) == 1 else 200, json={"ok": True})
    budget = Budget()
    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        assert HttpGateway(client, budget, sleep=lambda _: None).get_json("https://source.example") == {"ok": True}
    assert budget.requests == 2
    with httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(200, text="private-response"))) as client:
        budget = Budget()
        with pytest.raises(CapabilityError) as error:
            HttpGateway(client, budget).get_json("https://source.example")
        assert budget.requests == 1
        assert "private-response" not in str(error.value)


def test_search_protocol_is_copied_without_loose_parsing():
    payload = {"isError": False, "content": [{"type": "text", "text": json.dumps({"status": 0, "pages": []})}]}
    response = SimpleNamespace(status_code=200, output=SimpleNamespace(text=json.dumps(payload)+"5"))
    assert parse_search_response(response, expected_count=5) == []
    with pytest.raises(ValueError):
        parse_search_response(response, expected_count=3)


def test_invalid_model_output_is_not_retried():
    calls = []
    def send(prompt, **kwargs):
        calls.append(prompt)
        return "private-invalid-output"
    budget = Budget()
    with pytest.raises(CapabilityError) as error:
        invoke_structured(send, "prompt", ResearchRequest, budget)
    assert len(calls) == budget.models == 1
    assert error.value.info.code == "MODEL_OUTPUT_INVALID"
    assert "private-invalid-output" not in str(error.value)


def test_withdrawn_claim_cannot_reappear():
    claim = dict(claim_id="c1", question_id="q1", kind="fact", text="事实",
                 citations=[dict(evidence_id="e1", locator="p1", quote="source evidence quote")])
    with pytest.raises(ValidationError):
        RoleResult(role="bull", evidence_version="v1", initial_claims=[claim],
                   reflection=[dict(claim_id="c1", action="withdraw", reason="证据不足")],
                   revised_claims=[claim])


def test_alphabet_financial_concepts_are_explicit():
    from agent.value.sec import METRICS
    assert METRICS["revenue"][0] == "RevenueFromContractWithCustomerExcludingAssessedTax"
    assert METRICS["profit"][0] == "NetIncomeLoss"
