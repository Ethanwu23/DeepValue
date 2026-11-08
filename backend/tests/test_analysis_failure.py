"""模型输出违反契约时必须进入有限报告，而非中断研究。"""
import json
from types import SimpleNamespace
from unittest.mock import patch
import pytest
from agent.value import workflow
from agent.value.models import Analysis
from agent.base_agent import JsonAgent
from pydantic import ValidationError


def invalid_output():
    return json.dumps({"claims": [{"topic": "business", "text": "判断",
        "citations": [{"evidence_id": "news", "quote": "x" * 351}]}], "gaps": []})


def test_long_quote_is_still_rejected_without_retry():
    agent = JsonAgent(model_id="research", keys=Analysis)
    with patch.object(JsonAgent, "__call__", return_value=invalid_output()) as call:
        with pytest.raises(ValidationError):
            agent.step(prompt="研究")
    assert call.call_count == 1


@pytest.mark.parametrize("output", [invalid_output(), "not valid json"])
def test_invalid_analysis_finishes_as_limited_report(monkeypatch, output):
    rows = []
    for year in (2022, 2023, 2024):
        rows.append(dict(period_end=f"{year}-12-31", filed=f"{year+1}-02-01",
            url="https://www.sec.gov/example", evidence_id=f"SEC-{year}",
            metrics={key: {"value": 10} for key in workflow.METRICS}))
    monkeypatch.setattr(workflow, "load_available_models_from_env",
                        lambda: [SimpleNamespace(model_id="research")])
    monkeypatch.setattr(workflow, "collect", lambda _: dict(
        company=dict(name="Alphabet", sic="7370", sic_description="Services"),
        financials=rows, financial_issues=[], evidence={}))
    def context(task, scope):
        category = task["category"]
        return {"evidence": {category: dict(category=category, published="2025-01-01",
            title=category, url=f"https://example.com/{category}",
            excerpt="可引用的来源原文", kind="fixture")}, "rejected": {}}
    monkeypatch.setattr(workflow, "collect_web", context)
    monkeypatch.setattr(workflow, "collect_policy", context)
    with patch.object(JsonAgent, "__call__", return_value=output) as call:
        result = workflow.graph.invoke({"request": {"as_of": "2025-03-01", "model": "research"}})
    assert call.call_count == 1
    assert result["valuation"]["status"] == "calculated"
    assert result["review"]["status"] == "limited"
    assert result["analysis"]["claims"] == []
    assert "MODEL_OUTPUT_INVALID" in result["report"]
    assert "有限结论" in result["report"]
    assert len(result["financials"]) == 3
    assert output not in result["report"]
