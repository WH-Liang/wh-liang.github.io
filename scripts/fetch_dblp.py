"""从 DBLP 抓取计算机顶会论文（含反爬检测与降级）。

DBLP 自 2024 年起对自动化访问启用了 Anubis 反爬挑战，若检测到拦截，
本脚本返回空列表并在 _dblp_status.json 中标记 blocked=True，
由 merge.py 用 arXiv 分类数据兜底。
"""
import json
import os
import urllib.parse

from common import http_get, load_config, save_json, RAW_DIR, norm_doi


def is_blocked(text):
    return not text or "not a bot" in text.lower() or text.strip().lower().startswith("<!doctype html")


def fetch_venue(dblp_key, name, limit):
    q = urllib.parse.quote(f"stream:streams/{dblp_key}:")
    url = f"https://dblp.org/search/publ/api?q={q}&format=json&h={min(limit * 3, 1000)}"
    text = http_get(url)
    if is_blocked(text):
        return None
    try:
        data = json.loads(text)
    except Exception:
        return []
    hits = (data.get("result", {}).get("hits", {}).get("hit") or [])
    papers = []
    for h in hits:
        info = h.get("info", {})
        title = info.get("title", "")
        if not title:
            continue
        auth = info.get("authors", {}).get("author", [])
        if isinstance(auth, dict):
            auth = [auth]
        authors = [a.get("text", "") for a in auth if isinstance(a, dict)]
        doi = info.get("doi")
        ee = info.get("ee")
        key = info.get("key", "")
        papers.append({
            "id": "dblp:" + key,
            "title": title,
            "authors": authors,
            "venue": name,
            "venue_short": name,
            "venue_type": "conference",
            "year": int(info.get("year") or 0) or None,
            "date": None,
            "doi": norm_doi(doi),
            "pdf": None,
            "url": ee or (f"https://dblp.org/rec/{key}.html" if key else None),
            "abstract": None,
            "citation_count": 0,
            "concepts": [],
            "source": "dblp",
        })
    return papers


def run():
    cfg = load_config()
    limit = cfg["fetch"].get("papers_per_venue", 40)
    all_papers = []
    blocked = False
    for c in cfg.get("conferences", []):
        print(f"[dblp] {c['name']} ...")
        res = fetch_venue(c["dblp_key"], c["name"], limit)
        if res is None:
            print("    [blocked] DBLP 反爬拦截，改由 arXiv 分类兜底")
            blocked = True
            break
        res = sorted(res, key=lambda p: -(p["year"] or 0))[:limit]
        all_papers.extend(res)
        print(f"    -> {len(res)} 篇")
    save_json(os.path.join(RAW_DIR, "dblp.json"), all_papers)
    save_json(os.path.join(RAW_DIR, "_dblp_status.json"), {"blocked": blocked})
    return all_papers


if __name__ == "__main__":
    run()
