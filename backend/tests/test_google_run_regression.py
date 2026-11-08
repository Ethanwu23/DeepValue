"""复现GOOGL 2026-11-08运行中发现的收入与无关来源问题。"""
from unittest.mock import patch
import pytest
from agent.value.sec import collect, metric_definition, METRICS
from agent.value.evidence import check_relevance
from agent.value.workflow import validate_evidence, write_report


def test_revenue_mapping_is_period_bound_not_missing_value_fallback():
    assert metric_definition("revenue", "1652044", "2024-12-31")[0] == "RevenueFromContractWithCustomerExcludingAssessedTax"
    assert metric_definition("revenue", "1652044", "2025-12-31")[0] == "Revenues"
    accn = "0001652044-26-000018"
    rows = {"form": ["10-K"], "filingDate": ["2026-02-05"],
            "reportDate": ["2025-12-31"], "accessionNumber": [accn]}
    submission = dict(tickers=["GOOGL"], sic="7370", name="Alphabet", sicDescription="Services",
                      filings={"recent": rows, "files": []})
    facts = {}
    for key in METRICS:
        tag, unit, duration, _ = metric_definition(key, "1652044", "2025-12-31")
        row = dict(accn=accn, end="2025-12-31", filed="2026-02-05", val=10)
        if duration:
            row["start"] = "2025-01-01"
        facts[tag] = {"units": {unit: [row]}}
    scope = dict(cik="1652044", ticker="GOOGL", as_of="2026-11-08", years=1)
    with patch("agent.value.sec.sec_json", side_effect=[submission, {"facts": {"us-gaap": facts}}]):
        result = collect(scope)
    assert result["financial_issues"] == []
    assert result["financials"][0]["metrics"]["revenue"]["tag"] == "Revenues"
    del facts["Revenues"]
    with patch("agent.value.sec.sec_json", side_effect=[submission, {"facts": {"us-gaap": facts}}]):
        result = collect(scope)
    assert result["financial_issues"]


@pytest.mark.parametrize("title", [
    "Further Definition of Swap To Exclude Casino-Style Gambling Products",
    "Patient Protection and Affordable Care Act, Exchange Pre-Eligibility Verification",
])
def test_unrelated_official_policies_do_not_count_as_coverage(title):
    with pytest.raises(ValueError, match="不相关"):
        check_relevance(title, "Official regulatory document", "policy", "https://www.federalregister.gov/document")


def test_social_repost_is_not_accepted_as_company_news():
    with pytest.raises(ValueError, match="社交转载"):
        check_relevance("Alphabet earnings", "Google reported results", "news", "https://weibo.com/1")


def test_primary_company_news_and_relevant_policy():
    check_relevance("Alphabet results", "Google cloud revenue", "news", "https://abc.xyz/results")
    check_relevance("Artificial intelligence regulation", "Public comment", "policy", "https://www.federalregister.gov/document")


def test_financial_block_retains_context_gaps():
    result = validate_evidence({"financial_issues": ["收入缺失"], "financials": [],
                                "scope": {"years": 3}, "evidence": {}})
    assert result["review"]["missing_categories"] == ["news", "industry", "policy"]
    state = dict(scope=dict(as_of="2026-11-08", ticker="GOOGL"), company=dict(name="Alphabet", sic="7370"),
                 financial_issues=result["financial_issues"], financials=[], review=result["review"],
                 evidence={}, collector_errors={}, rejected={}, round=1)
    report = write_report(state)["report"]
    assert "已跳过" in report
    assert "缺少可核验的 industry" in report
    assert "未执行估值" in report


def test_news_claim_requires_explicit_attribution():
    from agent.value.workflow import claim_gate
    evidence = {"e": dict(category="news", excerpt="Google cloud demand improved")}
    claim = dict(text="云业务需求改善", citations=[dict(evidence_id="e", quote="cloud demand improved")])
    assert not claim_gate(claim, evidence)
    claim["text"] = "据报道，云业务需求改善"
    assert claim_gate(claim, evidence)


def test_annual_fact_cannot_be_used_as_next_year_quarter_fact():
    from agent.value.workflow import claim_gate
    evidence = {"e": dict(category="financials", excerpt="期间截至 2025-12-31，资本支出：91447000000 USD")}
    claim = dict(text="2026年第三季度资本开支上升", citations=[dict(evidence_id="e", quote="资本支出：91447000000 USD")])
    assert not claim_gate(claim, evidence)
    claim["text"] = "2025年资本支出为91447000000 USD"
    assert claim_gate(claim, evidence)
