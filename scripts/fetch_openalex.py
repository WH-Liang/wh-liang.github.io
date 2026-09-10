"""从 OpenAlex 按 ISSN 抓取顶刊（遥感 + 计算机）最新论文。"""
import json
import os
import time
import urllib.parse

from common import http_get, load_config, save_json, RAW_DIR, norm_doi


def reconstruct_abstract(inv):
    if not inv:
        return None
    pos = {}
    for word, ps in inv.items():
        for p in ps:
            pos[p] = word
    return " ".join(pos[i] for i in sorted(pos))


def fetch_journal(journal, limit):
    issn = journal["issn"]
    qs = urllib.parse.urlencode({
        "filter": f"primary_location.source.issn:{issn}",
        "sort": "publication_date:desc",
        "per-page": min(limit, 200),
        "select": "id,title,display_name,publication_year,publication_date,doi,authorships,abstract_inverted_index,cited_by_count,concepts,primary_location",
        "mailto": "research-site@example.com",
    })
    text = http_get(f"https://api.openalex.org/works?{qs}")
    if not text:
        return []
    data = json.loads(text)
    papers = []
    for w in data.get("results", []):
        title = w.get("title") or w.get("display_name") or ""
        if not title:
            continue
        authors = [a.get("author", {}).get("display_name", "") for a in w.get("authorships", [])]
        authors = [a for a in authors if a]
        concepts = [c.get("display_name", "") for c in w.get("concepts", []) if c.get("score", 0) > 0.3][:3]
        loc = w.get("primary_location") or {}
        doi = norm_doi(w.get("doi"))
        papers.append({
            "id": "openalex:" + (w.get("id", "").split("/")[-1] or ""),
            "title": title,
            "authors": authors,
            "venue": journal["name"],
            "venue_short": journal["short"],
            "venue_type": "journal",
            "year": w.get("publication_year"),
            "date": w.get("publication_date"),
            "doi": doi,
            "pdf": loc.get("pdf_url"),
            "url": loc.get("landing_page_url") or (f"https://doi.org/{doi}" if doi else None),
            "abstract": reconstruct_abstract(w.get("abstract_inverted_index")),
            "citation_count": w.get("cited_by_count", 0) or 0,
            "concepts": concepts,
            "source": "openalex",
        })
    return papers


def run():
    cfg = load_config()
    limit = cfg["fetch"].get("papers_per_venue", 40)
    years_back = cfg["fetch"].get("years_back", 0)
    all_papers = []
    for j in cfg.get("journals", []):
        print(f"[openalex] {j['short']} (ISSN {j['issn']}) ...")
        papers = fetch_journal(j, limit)
        if years_back and papers:
            max_year = max((p["year"] or 0) for p in papers)
            papers = [p for p in papers if (p["year"] or 0) >= max_year - years_back + 1]
        all_papers.extend(papers)
        print(f"    -> {len(papers)} 篇")
        time.sleep(0.3)
    save_json(os.path.join(RAW_DIR, "openalex.json"), all_papers)
    return all_papers


if __name__ == "__main__":
    run()
