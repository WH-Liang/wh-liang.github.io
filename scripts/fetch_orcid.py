"""从 ORCID 公开 API 同步本人已发表论文。"""
import json
import os

from common import http_get, load_config, save_json, RAW_DIR, norm_doi


def _val(x):
    return x.get("value") if isinstance(x, dict) else x


def parse_works(data):
    papers = []
    for g in data.get("group", []):
        summaries = g.get("work-summary", [])
        if not summaries:
            continue
        ws = summaries[0]
        for s in summaries:
            eids = s.get("external-ids", {}).get("external-id", [])
            if any(e.get("external-id-type") == "doi" for e in eids):
                ws = s
                break
        title = _val(ws.get("title", {}).get("title")) or ""
        journal = _val(ws.get("journal-title")) or ""
        year = None
        y = ws.get("publication-date", {}).get("year")
        y = _val(y)
        if y:
            try:
                year = int(y)
            except (TypeError, ValueError):
                year = None
        doi = None
        for e in ws.get("external-ids", {}).get("external-id", []):
            if e.get("external-id-type") == "doi":
                doi = norm_doi(e.get("external-id-value"))
                break
        url = _val(ws.get("url"))
        papers.append({
            "title": title,
            "authors": [],
            "venue": journal,
            "venue_short": journal[:40] if journal else "",
            "venue_type": "journal",
            "year": year,
            "date": None,
            "doi": doi,
            "pdf": None,
            "url": url or (f"https://doi.org/{doi}" if doi else None),
            "abstract": None,
            "citation_count": 0,
            "concepts": [],
            "orcid_type": ws.get("type"),
            "source": "orcid",
        })
    return papers


def run():
    cfg = load_config()
    orcid = (cfg.get("profile", {}).get("orcid") or "").strip()
    if not orcid:
        print("[orcid] 未配置 ORCID（config.json -> profile.orcid），跳过")
        save_json(os.path.join(RAW_DIR, "orcid.json"), [])
        return []
    text = http_get(f"https://pub.orcid.org/v3.0/{orcid}/works",
                    headers={"Accept": "application/json"})
    papers = []
    if text:
        try:
            papers = parse_works(json.loads(text))
        except Exception as e:
            print(f"  [warn] ORCID 解析失败: {e}")
    print(f"[orcid] {len(papers)} 篇")
    save_json(os.path.join(RAW_DIR, "orcid.json"), papers)
    return papers


if __name__ == "__main__":
    run()
