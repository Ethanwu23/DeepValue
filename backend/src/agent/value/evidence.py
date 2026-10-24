import hashlib
import ipaddress
import json
import re
import socket
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from html.parser import HTMLParser
from urllib.parse import urlsplit, urljoin
import httpx
from agent.base_agent import WebSearchAgent


class ArticleParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.meta = {}
        self.parts = []
        self.scripts = []
        self.script = None
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "meta":
            self.meta[attrs.get("property", attrs.get("name", ""))] = attrs.get("content", "")
        if tag in ("script", "style"):
            self.skip += 1
            if tag == "script" and attrs.get("type") == "application/ld+json":
                self.script = []
        if tag == "time" and attrs.get("itemprop") == "datePublished":
            self.meta["datePublished"] = attrs.get("datetime", "")

    def handle_endtag(self, tag):
        if tag == "script" and self.script is not None:
            self.scripts.append("".join(self.script))
            self.script = None
        if tag in ("script", "style"):
            self.skip = max(0, self.skip - 1)

    def handle_data(self, data):
        if self.script is not None:
            self.script.append(data)
        if not self.skip and data.strip():
            self.parts.append(data.strip())

    def dates(self):
        published, modified = [], []
        for key in ("article:published_time", "datePublished"):
            if self.meta.get(key):
                published.append(self.meta[key])
        for key in ("article:modified_time", "dateModified"):
            if self.meta.get(key):
                modified.append(self.meta[key])
        def visit(value):
            if isinstance(value, dict):
                if value.get("datePublished"):
                    published.append(value["datePublished"])
                if value.get("dateModified"):
                    modified.append(value["dateModified"])
                for child in value.values():
                    visit(child)
            elif isinstance(value, list):
                for child in value:
                    visit(child)
        for script in self.scripts:
            try:
                visit(json.loads(script))
            except json.JSONDecodeError:
                continue
        def parse(values):
            return sorted({date.fromisoformat(str(v)[:10]).isoformat() for v in values
                           if re.match(r"^\d{4}-\d{2}-\d{2}", str(v))})
        return parse(published), parse(modified)


def source_id(url: str) -> str:
    return "WEB-" + hashlib.sha256(url.encode()).hexdigest()[:16]


def public_url(url: str):
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https") or not parts.hostname or parts.username or parts.password:
        raise ValueError("不支持的来源地址")
    if parts.port not in (None, 80, 443):
        raise ValueError("来源端口不允许")
    addresses = socket.getaddrinfo(parts.hostname, parts.port or 443, type=socket.SOCK_STREAM)
    if any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
        raise ValueError("来源地址不是公共网络")


def read_page(url: str) -> tuple[str, str]:
    # 每次跳转均重新校验地址，限定大小与超时，不访问本机或内网资料。
    with httpx.Client(timeout=12, follow_redirects=False) as client:
        for _ in range(4):
            public_url(url)
            with client.stream("GET", url, headers={"User-Agent": "DeepValue/0.1 research"}) as response:
                if response.is_redirect:
                    url = urljoin(url, response.headers["location"])
                    continue
                response.raise_for_status()
                if "text/html" not in response.headers.get("content-type", ""):
                    raise ValueError("第一版仅解析有日期元数据的 HTML 正文")
                content = bytearray()
                for chunk in response.iter_bytes():
                    content.extend(chunk)
                    if len(content) > 2_000_000:
                        raise ValueError("页面超过 2 MB")
                return content.decode(response.encoding or "utf-8", errors="replace"), url
    raise ValueError("页面重定向次数超过限制")


def verify_page(page: dict, category: str, cutoff: str) -> tuple[dict, dict]:
    url, identifier = page["url"], source_id(page["url"])
    try:
        html, final_url = read_page(url)
        parser = ArticleParser()
        parser.feed(html)
        published, modified = parser.dates()
        if len(published) != 1:
            raise ValueError("原文发布日期缺失或冲突")
        if published[0] > cutoff or any(d > cutoff for d in modified):
            raise ValueError("发布时间或已知修改时间晚于截止日")
        excerpt = "\n".join(parser.parts)[:12000]
        if len(excerpt) < 200:
            raise ValueError("无法取得足够正文")
        item = {"id": identifier, "category": category, "title": page["title"], "url": final_url,
                "published": published[0], "modified": modified, "date_basis": "原网页日期元数据",
                "excerpt": excerpt, "kind": "当前抓取的历史网页，非归档快照",
                "retrieved": date.today().isoformat()}
        return {identifier: item}, {}
    except (httpx.HTTPError, ValueError, OSError) as error:
        return {}, {identifier: {"title": page["title"], "url": url, "category": category,
                                "reason": str(error)[:250]}}


def collect_web(task: dict, scope: dict) -> dict:
    pages = WebSearchAgent().step(prompt=task["query"], count=5)
    evidence, rejected = {}, {}
    with ThreadPoolExecutor(max_workers=3) as executor:
        for accepted, excluded in executor.map(lambda p: verify_page(p, task["category"], scope["as_of"]), pages[:5]):
            evidence.update(accepted)
            rejected.update(excluded)
    return {"evidence": evidence, "rejected": rejected}


def collect_policy(task: dict, scope: dict) -> dict:
    start = (date.fromisoformat(scope["as_of"]) - timedelta(days=365)).isoformat()
    params = {"conditions[term]": "manufacturing tariffs", "conditions[publication_date][lte]": scope["as_of"],
              "conditions[publication_date][gte]": start, "per_page": 3, "order": "newest"}
    response = httpx.get("https://www.federalregister.gov/api/v1/documents.json",
                         params=params, timeout=25, headers={"User-Agent": "DeepValue/0.1 research"})
    response.raise_for_status()
    evidence = {}
    for item in response.json()["results"]:
        published = date.fromisoformat(item["publication_date"]).isoformat()
        if published > scope["as_of"]:
            raise ValueError("政策接口返回晚于截止日的数据")
        url = item["html_url"]
        if urlsplit(url).hostname != "www.federalregister.gov":
            raise ValueError("政策来源域名不符合协议")
        identifier = source_id(url)
        abstract = item.get("abstract")
        if not abstract:
            continue
        evidence[identifier] = {"id": identifier, "category": "policy", "title": item["title"],
            "url": url, "published": published, "date_basis": "Federal Register publication_date",
            "excerpt": abstract[:6000], "kind": "政策官方摘要；未核验全文、生效日期及公司适用性",
            "retrieved": date.today().isoformat()}
    return {"evidence": evidence, "rejected": {}}
