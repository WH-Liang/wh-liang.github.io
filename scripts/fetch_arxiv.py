"""从 arXiv 按关键词 + 分类订阅最新预印本。"""
import os
import re
import time
import urllib.parse
import xml.etree.ElementTree as ET

from common import http_get, load_config, save_json, RAW_DIR

NS = {"a": "http://www.w3.org/2005/Atom"}


def parse_feed(xml_text):
    if not xml_text:
        return []
    try:
        root = ET.fromstring(xml_text)
    except Exception:
        return []
    papers = []
    for e in root.findall("a:entry", NS):
        title = re.sub(r"\s+", " ", (e.findtext("a:title", default="", namespaces=NS) or "").strip())
        if not title:
            continue
        summary = re.sub(r"\s+", " ", (e.findtext("a:summary", default="", namespaces=NS) or "").strip())
        aid = (e.findtext("a:id", default="", namespaces=NS) or "").strip()
        arxiv_id = aid.split("/abs/")[-1]
        published = (e.findtext("a:published", default="", namespaces=NS) or "")[:10]
        authors = [(a.findtext("a:name", default="", namespaces=NS) or "") for a in e.findall("a:author", NS)]
        cats = [c.get("term") for c in e.findall("a:category", NS) if c.get("term")]
        pdf = page = None
        for l in e.findall("a:link", NS):
            if l.get("title") == "pdf":
                pdf = l.get("href")
            if l.get("rel") == "alternate":
                page = l.get("href")
        papers.append({
            "id": "arxiv:" + arxiv_id,
            "title": title,
            "authors": authors,
            "venue": "arXiv",
            "venue_short": "arXiv",
            "venue_type": "preprint",
            "year": int(published[:4]) if published else None,
            "date": published or None,
            "doi": None,
            "pdf": pdf,
            "url": page,
            "abstract": summary,
            "citation_count": 0,
            "concepts": cats[:3],
            "arxiv_id": arxiv_id,
            "source": "arxiv",
        })
    return papers


def fetch(query, n):
    url = ("https://export.arxiv.org/api/query?search_query="
           + urllib.parse.quote(query, safe="")
           + f"&sortBy=submittedDate&sortOrder=descending&max_results={n}")
    return parse_feed(http_get(url))


def run():
    cfg = load_config()
    arx = cfg.get("arxiv", {})
    n = arx.get("max_results", 60)
    seen = {}

    kws = arx.get("keywords", [])
    if kws:
        q = " OR ".join(f'all:"{k}"' for k in kws)
        print(f"[arxiv] 关键词 {len(kws)} 个 ...")
        for p in fetch(q, n):
            seen[p["arxiv_id"]] = p
        time.sleep(1)

    for c in arx.get("categories", []):
        print(f"[arxiv] 分类 {c} ...")
        for p in fetch(f"cat:{c}", n):
            seen.setdefault(p["arxiv_id"], p)
        time.sleep(1)

    papers = list(seen.values())
    save_json(os.path.join(RAW_DIR, "arxiv.json"), papers)
    print(f"[arxiv] 共 {len(papers)} 篇")
    return papers


if __name__ == "__main__":
    run()
