"""估值情景计算的回归测试。

固定 `agent.value.valuation.calculate` 的当前口径，用于后续重构与依赖升级的回归保护。

覆盖：
- 三个 blocked 出口（财务校验未通过 / 财年不足 / 非正 EPS）及其优先级
- 近三年稀释 EPS 中位数 × 用户 PE 假设
- EPS ±20% 敏感性
- 每股价值 0.01 精度的 ROUND_HALF_UP 舍入

测试用 EPS 一律以字符串传入，避免浮点字面量引入精度噪声。
"""

import pytest

from agent.value.valuation import calculate


SCOPE = {"pe_low": 10, "pe_base": 15, "pe_high": 20}


def _row(period_end: str, evidence_id: str, eps: str) -> dict:
    """构造一个财年记录，结构与 sec.py 产出的财务行一致。"""
    return {
        "period_end": period_end,
        "evidence_id": evidence_id,
        "metrics": {"eps": {"value": eps}},
    }


def _three_years() -> list[dict]:
    return [
        _row("2022-12-31", "e2", "4.00"),
        _row("2023-12-31", "e3", "5.00"),
        _row("2024-12-31", "e4", "6.00"),
    ]


def test_blocked_by_validation_issues_takes_precedence():
    """财务校验未通过时优先阻断，即使财年数量也不足。"""
    result = calculate([_row("2024-12-31", "e1", "4.00")], SCOPE, ["净利润缺失"])

    assert result["status"] == "blocked"
    assert result["reason"] == "财务校验未通过，不执行估值"
    assert result["issues"] == ["净利润缺失"]


@pytest.mark.parametrize("rows", [[], [_row("2023-12-31", "e1", "4.00")],
                                  [_row("2022-12-31", "e1", "4.00"),
                                   _row("2023-12-31", "e2", "5.00")]])
def test_blocked_when_fewer_than_three_fiscal_years(rows):
    result = calculate(rows, SCOPE, [])

    assert result["status"] == "blocked"
    assert result["reason"] == "至少需要三个完整财年"


@pytest.mark.parametrize("bad_eps", ["0", "0.00", "-1.50"])
def test_blocked_when_any_recent_eps_is_not_positive(bad_eps):
    rows = [
        _row("2022-12-31", "e2", "4.00"),
        _row("2023-12-31", "e3", bad_eps),
        _row("2024-12-31", "e4", "6.00"),
    ]
    result = calculate(rows, SCOPE, [])

    assert result["status"] == "blocked"
    assert result["reason"] == "近三年存在非正 EPS，当前市盈率情景法不适用"


def test_uses_median_eps_of_last_three_fiscal_years():
    """超过三个财年时只取最近三年，中位数不受更早年度影响。"""
    rows = [
        _row("2020-12-31", "e0", "1.00"),
        _row("2021-12-31", "e1", "2.00"),
        *_three_years(),
    ]
    result = calculate(rows, SCOPE, [])

    assert result["status"] == "calculated"
    assert result["normalized_eps"] == 5.0
    assert result["scenarios"] == [
        {"label": "低倍数", "pe": 10.0, "value_per_share": 50.0},
        {"label": "基准倍数", "pe": 15.0, "value_per_share": 75.0},
        {"label": "高倍数", "pe": 20.0, "value_per_share": 100.0},
    ]


def test_reports_periods_and_evidence_of_selected_years():
    result = calculate(
        [
            _row("2020-12-31", "e0", "1.00"),
            _row("2021-12-31", "e1", "2.00"),
            *_three_years(),
        ],
        SCOPE,
        [],
    )

    assert result["periods"] == ["2022-12-31", "2023-12-31", "2024-12-31"]
    assert result["evidence_ids"] == ["e2", "e3", "e4"]


def test_sensitivity_applies_plus_minus_twenty_percent_on_eps():
    result = calculate(_three_years(), SCOPE, [])

    assert result["sensitivity"] == [
        {"eps_change": -0.2, "values": [40.0, 60.0, 80.0]},
        {"eps_change": 0, "values": [50.0, 75.0, 100.0]},
        {"eps_change": 0.2, "values": [60.0, 90.0, 120.0]},
    ]


def test_per_share_value_rounds_half_up_to_two_decimals():
    """3.5185 × 10 = 35.185，ROUND_HALF_UP 进位为 35.19（HALF_EVEN 会得到 35.18）。"""
    rows = [
        _row("2022-12-31", "e2", "2.00"),
        _row("2023-12-31", "e3", "3.5185"),
        _row("2024-12-31", "e4", "5.00"),
    ]
    result = calculate(rows, SCOPE, [])

    assert [s["value_per_share"] for s in result["scenarios"]] == [35.19, 52.78, 70.37]


def test_result_declares_currency_and_limitations():
    result = calculate(_three_years(), SCOPE, [])

    assert result["currency"] == "USD/share"
    assert result["limitations"], "估值结果必须声明口径限制，避免被当作目标价"
