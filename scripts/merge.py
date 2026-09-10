"""合并去重、打主题标签、补全本人论文，输出最终数据。"""
import json
import os
import time

from common import DATA_DIR, RAW_DIR, load_config, save_json, norm_doi, norm_title, tag_topics


def _load(name):
    p = os.path.join(RAW_DIR, name)
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    return []


def run():
    cfg = load_config()
    topics = cfg.get("topics", {})
    profile = cfg.get("profile", {})

    openalex = _load("openalex.json")
    arxiv = _load("arxiv.json")
    dblp = _load("dblp.json")
    dblp_status = _load("_dblp_status.json")
    orcid = _load("orcid.json")

    # ---- 本人论文：标记 + 用抓取数据补全（引用数/摘要/作者）----
    own_dois = set(p.get("doi") for p in orcid if p.get("doi"))
    own_titles = set(norm_title(p.get("title")) for p in orcid if p.get("title"))
    pool = openalex + dblp + arxiv
    for p in orcid:
        match = None
        if p.get("doi"):
            match = next((x for x in pool if norm_doi(x.get("doi")) == p["doi"]), None)
        if not match and p.get("title"):
            nt = norm_title(p.get("title"))
            match = next((x for x in pool if norm_title(x.get("title")) == nt), None)
        if match:
            p["citation_count"] = p.get("citation_count") or match.get("citation_count") or 0
            p["abstract"] = p.get("abstract") or match.get("abstract")
            p["authors"] = p.get("authors") or match.get("authors") or []
        p["topics"] = tag_topics(
            " ".join([p.get("title") or "", p.get("venue") or "", p.get("abstract") or ""]), topics)
        p["id"] = p.get("id") or ("orcid:" + (p.get("doi") or norm_title(p.get("title")) or "")[:40])

    # ---- 合并抓取论文 ----
    merged = []
    seen = set()

    def add(p):
        key = norm_doi(p.get("doi")) or ("title:" + norm_title(p.get("title")))
        if not key or key in seen:
            return
        seen.add(key)
        p["topics"] = tag_topics(
            " ".join([p.get("title") or "", p.get("abstract") or ""] + (p.get("concepts") or [])), topics)
        p["is_own"] = (norm_doi(p.get("doi")) in own_dois) or (norm_title(p.get("title")) in own_titles)
        merged.append(p)

    for p in openalex:
        add(p)
    for p in dblp:
        add(p)
    for p in arxiv:
        add(p)

    def sort_key(p):
        return p.get("date") or f"{p.get('year') or 0:04d}"

    merged.sort(key=sort_key, reverse=True)
    orcid.sort(key=lambda p: -(p.get("year") or 0))

    # ---- 统计 ----
    meta = {
        "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "dblp_blocked": bool(dblp_status.get("blocked", False)),
        "counts": {
            "total_papers": len(merged),
            "publications": len(orcid),
            "journals": sum(1 for p in merged if p.get("venue_type") == "journal"),
            "conferences": sum(1 for p in merged if p.get("venue_type") == "conference"),
            "preprints": sum(1 for p in merged if p.get("venue_type") == "preprint"),
            "total_citations": sum(p.get("citation_count") or 0 for p in merged),
        },
        "venues": {},
        "years": {},
        "profile": profile,
    }
    for p in merged:
        v = p.get("venue_short") or p.get("venue") or "其他"
        meta["venues"][v] = meta["venues"].get(v, 0) + 1
        y = p.get("year")
        if y:
            meta["years"][str(y)] = meta["years"].get(str(y), 0) + 1

    save_json(os.path.join(DATA_DIR, "papers.json"), merged)
    save_json(os.path.join(DATA_DIR, "publications.json"), orcid)
    save_json(os.path.join(DATA_DIR, "latest.json"), merged[:8])
    save_json(os.path.join(DATA_DIR, "meta.json"), meta)
    print(f"[merge] 论文 {len(merged)} 篇 | 本人发表 {len(orcid)} 篇 | DBLP blocked={meta['dblp_blocked']}")
    return merged


if __name__ == "__main__":
    run()
