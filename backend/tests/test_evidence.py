"""证据采集与时间门禁的回归测试。

`evidence.py` 的截止日过滤是防前视偏差的核心门禁：它失效时不会报错，
只会静默放过晚于截止日的证据，直接污染研究结论。

所有用例均不访问外网：`verify_page` 通过替换 `read_page` 注入可控 HTML，
`public_url` 只使用无需外部 DNS 即可判定的地址。

覆盖：
- `ArticleParser.dates()`：日期元数据抽取、去重排序、脏数据忽略
- `source_id()`：稳定且与 URL 一一对应
- `public_url()`：SSRF 防护拒绝非公共网络来源
- `verify_page()`：截止日门禁的接受与拒绝分支
"""

import json

import pytest

from agent.value import evidence


URL = "https://example.com/report"
CUTOFF = "2025-03-01"
BODY = "卡特彼勒经营观察与行业周期分析。" * 20  # 280 字，超过 200 字正文下限


def _html(published=None, modified=None, body=BODY, ldjson=None):
    """拼装一个带日期元数据的 HTML，供 ArticleParser 或 verify_page 消费。"""
    meta = []
    if published:
        meta.append(f'<meta property="article:published_time" content="{published}">')
    if modified:
        meta.append(f'<meta property="article:modified_time" content="{modified}">')
    script = ""
    if ldjson is not None:
        script = f'<script type="application/ld+json">{json.dumps(ldjson)}</script>'
    return (f"<html><head>{''.join(meta)}{script}</head>"
            f"<body><p>{body}</p></body></html>")


def _parse(html):
    parser = evidence.ArticleParser()
    parser.feed(html)
    return parser.dates()


def _verify(monkeypatch, html, cutoff=CUTOFF, category="news"):
    """用受控 HTML 驱动一次 verify_page，返回 (accepted, rejected)。"""
    monkeypatch.setattr(evidence, "read_page", lambda url: (html, url))
    return evidence.verify_page({"url": URL, "title": "测试页面"}, category, cutoff)


# --- ArticleParser.dates() ---


def test_dates_extracted_from_meta_tags():
    published, modified = _parse(_html(published="2025-01-10T08:00:00Z",
                                       modified="2025-02-01"))
    assert published == ["2025-01-10"]
    assert modified == ["2025-02-01"]


def test_dates_extracted_from_nested_ld_json():
    ldjson = {"@graph": [{"@type": "NewsArticle",
                          "datePublished": "2025-01-10T08:00:00Z",
                          "dateModified": "2025-02-01"}]}
    published, modified = _parse(_html(ldjson=ldjson))

    assert published == ["2025-01-10"]
    assert modified == ["2025-02-01"]


def test_dates_are_deduplicated_and_sorted():
    ldjson = {"datePublished": "2025-01-10"}
    published, _ = _parse(_html(published="2025-01-10", ldjson=ldjson))

    assert published == ["2025-01-10"]


def test_non_iso_date_is_ignored():
    published, modified = _parse(_html(published="昨天", modified="unknown"))

    assert published == []
    assert modified == []


# --- source_id() ---


def test_source_id_is_stable_and_prefixed():
    identifier = evidence.source_id(URL)

    assert identifier.startswith("WEB-")
    assert identifier == evidence.source_id(URL)


def test_source_id_differs_by_url():
    assert evidence.source_id(URL) != evidence.source_id(URL + "/other")


# --- public_url()：SSRF 防护 ---


@pytest.mark.parametrize("url", [
    "file:///etc/passwd",
    "https://user:pass@example.com/report",
    "https://example.com:8080/report",
    "http://127.0.0.1/admin",
    "http://localhost/admin",
])
def test_public_url_rejects_non_public_sources(url):
    with pytest.raises(ValueError):
        evidence.public_url(url)


# --- verify_page()：截止日门禁 ---


def test_page_within_cutoff_is_accepted(monkeypatch):
    accepted, rejected = _verify(monkeypatch, _html(published="2025-01-10"))

    assert rejected == {}
    item = accepted[evidence.source_id(URL)]
    assert item["published"] == "2025-01-10"
    assert item["category"] == "news"
    assert item["date_basis"] == "原网页日期元数据"
    assert item["kind"] == "当前抓取的历史网页，非归档快照"


def test_published_after_cutoff_is_rejected(monkeypatch):
    accepted, rejected = _verify(monkeypatch, _html(published="2025-03-05"))

    assert accepted == {}
    assert rejected[evidence.source_id(URL)]["reason"] == "发布时间或已知修改时间晚于截止日"


def test_modified_after_cutoff_is_rejected(monkeypatch):
    """正文发布于截止日前，但已知修改时间晚于截止日，同样必须排除。"""
    accepted, rejected = _verify(monkeypatch,
                                 _html(published="2025-01-10", modified="2025-04-01"))

    assert accepted == {}
    assert rejected[evidence.source_id(URL)]["reason"] == "发布时间或已知修改时间晚于截止日"


def test_missing_published_date_is_rejected(monkeypatch):
    accepted, rejected = _verify(monkeypatch, _html())

    assert accepted == {}
    assert rejected[evidence.source_id(URL)]["reason"] == "原文发布日期缺失或冲突"


def test_conflicting_published_dates_are_rejected(monkeypatch):
    ldjson = {"datePublished": "2025-01-11"}
    accepted, rejected = _verify(monkeypatch,
                                 _html(published="2025-01-10", ldjson=ldjson))

    assert accepted == {}
    assert rejected[evidence.source_id(URL)]["reason"] == "原文发布日期缺失或冲突"


def test_too_short_excerpt_is_rejected(monkeypatch):
    accepted, rejected = _verify(monkeypatch, _html(published="2025-01-10", body="太短"))

    assert accepted == {}
    assert rejected[evidence.source_id(URL)]["reason"] == "无法取得足够正文"


def test_invalid_calendar_date_is_rejected_not_crashed(monkeypatch):
    """形如 2025-13-45 的日期应被拒绝，而不是抛出未捕获异常中断采集。"""
    accepted, rejected = _verify(monkeypatch, _html(published="2025-13-45"))

    assert accepted == {}
    assert evidence.source_id(URL) in rejected
