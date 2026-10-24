from statistics import median
from decimal import Decimal, ROUND_HALF_UP


def calculate(financials: list[dict], scope: dict, issues: list[str]) -> dict:
    if issues:
        return {"status": "blocked", "reason": "财务校验未通过，不执行估值", "issues": issues}
    rows = financials[-3:]
    if len(rows) != 3:
        return {"status": "blocked", "reason": "至少需要三个完整财年"}
    eps = [Decimal(str(row["metrics"]["eps"]["value"])) for row in rows]
    if any(v <= 0 for v in eps):
        return {"status": "blocked", "reason": "近三年存在非正 EPS，当前市盈率情景法不适用"}
    base = median(eps)
    scenarios = []
    for label, key in [("低倍数", "pe_low"), ("基准倍数", "pe_base"), ("高倍数", "pe_high")]:
        multiple = Decimal(str(scope[key]))
        price = (base * multiple).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        scenarios.append({"label": label, "pe": float(multiple), "value_per_share": float(price)})
    sensitivity = [{"eps_change": change, "values": [
        float((base * Decimal(str(1 + change)) * Decimal(str(s["pe"]))).quantize(Decimal("0.01")))
        for s in scenarios]} for change in [-0.2, 0, 0.2]]
    return {"status": "calculated", "method": "近三年披露稀释 EPS 中位数 × 用户市盈率假设",
            "normalized_eps": float(base), "currency": "USD/share", "scenarios": scenarios,
            "sensitivity": sensitivity, "periods": [r["period_end"] for r in rows],
            "evidence_ids": [r["evidence_id"] for r in rows],
            "limitations": ["EPS 未剔除一次性损益，中位数不是经审计的正常化盈利",
                           "三个倍数是用户设定的情景，不是同业统计、目标价或投资建议",
                           "未接入截止日股价，不计算安全边际或涨跌空间",
                           "合并数据包含金融业务时，不据此构造工业分部 DCF"]}
