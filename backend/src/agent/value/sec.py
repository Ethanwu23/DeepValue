import os
import threading
import time
from datetime import date
import httpx

_LOCK = threading.Lock()
_LAST = 0.0
BASE = "https://data.sec.gov"

# 固定的概念映射保留会计含义；缺失时明确报告，不让模型填数。
METRICS = {
    "revenue": ("Revenues", "USD", True, "收入"),
    "profit": ("ProfitLoss", "USD", True, "含非控股权益净利润"),
    "operating_cash": ("NetCashProvidedByUsedInOperatingActivities", "USD", True, "经营现金流"),
    "capex": ("PaymentsToAcquirePropertyPlantAndEquipment", "USD", True, "购建固定资产现金支出"),
    "eps": ("EarningsPerShareDiluted", "USD/shares", True, "稀释每股收益"),
    "assets": ("Assets", "USD", False, "资产"),
    "liabilities_equity": ("LiabilitiesAndStockholdersEquity", "USD", False, "负债及权益"),
}


def sec_json(path: str) -> dict:
    global _LAST
    with _LOCK:
        delay = 0.3 - (time.monotonic() - _LAST)
        if delay > 0:
            time.sleep(delay)
        _LAST = time.monotonic()
    headers = {"User-Agent": os.getenv("SEC_USER_AGENT", "DeepValue/0.1 single-company research"),
               "Accept": "application/json"}
    response = httpx.get(BASE + path, headers=headers, timeout=40)
    response.raise_for_status()
    return response.json()


def rows_from_columns(columns: dict) -> list[dict]:
    return [dict(zip(columns, values)) for values in zip(*columns.values())]


def filing_url(cik: str, accession: str) -> str:
    return f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession.replace('-', '')}/{accession}-index.html"


def collect(scope: dict) -> dict:
    cik = scope["cik"].zfill(10)
    submission = sec_json(f"/submissions/CIK{cik}.json")
    if scope["ticker"] not in submission["tickers"]:
        raise ValueError("证券代码与 CIK 不匹配")
    if not 3500 <= int(submission["sic"]) <= 3599:
        raise ValueError("第一版仅支持 SEC SIC 3500–3599 机械制造业")
    rows = rows_from_columns(submission["filings"]["recent"])
    # 截止日较早时读取官方历史索引，禁止用当前财报冒充历史披露。
    def available():
        return [r for r in rows if r["form"] == "10-K" and r["filingDate"] <= scope["as_of"]]
    for item in submission["filings"].get("files", []):
        if len(available()) >= scope["years"]:
            break
        if item["filingFrom"] <= scope["as_of"]:
            rows.extend(rows_from_columns(sec_json("/submissions/" + item["name"])))
    annual = sorted(available(), key=lambda r: (r["reportDate"], r["filingDate"]), reverse=True)
    selected = {}
    for row in annual:
        selected.setdefault(row["reportDate"], row)
    annual = list(selected.values())[:scope["years"]]
    facts = sec_json(f"/api/xbrl/companyfacts/CIK{cik}.json")["facts"]["us-gaap"]
    company = {"name": submission["name"], "ticker": scope["ticker"], "cik": cik,
               "sic": submission["sic"], "sic_description": submission["sicDescription"]}
    issues, financials, evidence = [], [], {}
    if len(annual) < scope["years"]:
        issues.append(f"截止日前仅找到 {len(annual)} 份年度报告，需要 {scope['years']} 份")
    for filing in annual:
        accession, end = filing["accessionNumber"], filing["reportDate"]
        source_id = "SEC-" + accession
        item = {"period_end": end, "filed": filing["filingDate"], "accession": accession,
                "url": filing_url(cik, accession), "metrics": {}, "evidence_id": source_id}
        for metric, (tag, unit, duration, label) in METRICS.items():
            candidates = []
            for fact in facts.get(tag, {}).get("units", {}).get(unit, []):
                if fact["accn"] != accession or fact["end"] != end or fact["filed"] > scope["as_of"]:
                    continue
                if duration and not (fact.get("start") and 330 <= (date.fromisoformat(end) - date.fromisoformat(fact["start"])).days <= 380):
                    continue
                if not duration and fact.get("start"):
                    continue
                candidates.append(fact)
            unique = {(r.get("start"), r["end"], r["val"]) for r in candidates}
            if len(unique) != 1:
                issues.append(f"{end} {label}：缺失或存在冲突（{tag}）")
                continue
            fact = candidates[0]
            item["metrics"][metric] = {"value": fact["val"], "unit": unit, "tag": tag,
                                      "start": fact.get("start"), "end": end,
                                      "filed": fact["filed"], "accession": accession}
        m = item["metrics"]
        if len({m[k]["start"] for k in m if METRICS[k][2]}) > 1:
            issues.append(f"{end} 年度流量指标起始日不一致")
        if "assets" in m and "liabilities_equity" in m:
            if abs(m["assets"]["value"] - m["liabilities_equity"]["value"]) > max(1, abs(m["assets"]["value"]) * 0.0001):
                issues.append(f"{end} 资产与负债权益不平衡")
        if "capex" in m and m["capex"]["value"] < 0:
            issues.append(f"{end} 资本支出符号不符合概念约定")
        # 采用原始年度申报；截止日前修订存在时阻断估值，不能忽略修订影响。
        amendments = [r for r in rows if r["form"] == "10-K/A" and r["reportDate"] == end
                      and r["filingDate"] <= scope["as_of"]]
        if amendments:
            issues.append(f"{end} 存在 10-K/A，需要核对修订内容后才能估值")
        financials.append(item)
        excerpt = f"{company['name']} 合并财报，期间截至 {end}，披露日 {filing['filingDate']}。\n"
        excerpt += "\n".join(f"{METRICS[k][3]}：{v['value']} {v['unit']}；概念 {v['tag']}" for k, v in m.items())
        evidence[source_id] = {"id": source_id, "category": "financials", "title": f"{end} Form 10-K",
                               "url": item["url"], "published": filing["filingDate"],
                               "date_basis": "SEC filingDate", "excerpt": excerpt,
                               "kind": "SEC XBRL 合并数值", "retrieved": date.today().isoformat()}
    return {"company": company, "financials": sorted(financials, key=lambda x: x["period_end"]),
            "financial_issues": issues, "evidence": evidence}
