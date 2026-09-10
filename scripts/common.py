"""公共工具：HTTP 请求、配置加载、JSON 读写、归一化、主题打标。"""
import json
import os
import re
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")
PUBLIC_DATA_DIR = os.path.join(ROOT, "public", "data")
RAW_DIR = os.path.join(DATA_DIR, "_raw")
CONFIG_PATH = os.path.join(ROOT, "scripts", "config.json")

UA = "Mozilla/5.0 (compatible; ResearchHomepageBot/1.0; mailto:contact@example.com)"


def ensure_dirs():
    for d in (DATA_DIR, PUBLIC_DATA_DIR, RAW_DIR):
        os.makedirs(d, exist_ok=True)


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def http_get(url, headers=None, timeout=40, retries=3):
    h = {"User-Agent": UA}
    if headers:
        h.update(headers)
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=h)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except Exception as e:
            if attempt == retries - 1:
                print(f"  [warn] 请求失败 {url[:90]}: {e}")
                return None
            time.sleep(2 * (attempt + 1))
    return None


def save_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)


def norm_title(t):
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]", "", (t or "").lower())


def norm_doi(d):
    if not d:
        return None
    d = d.strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "http://dx.doi.org/", "doi:"):
        d = d.replace(prefix, "")
    return d or None


def tag_topics(text, topics):
    """基于关键词给论文打主题标签（标题+摘要+概念），返回最多 3 个。"""
    if not text:
        return []
    t = " " + (text or "").lower() + " "
    out = []
    for topic, kws in topics.items():
        if any(k.lower() in t for k in kws):
            out.append(topic)
    return out[:3]
