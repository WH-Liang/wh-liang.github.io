"""一键运行：抓取全部数据源 → 合并 → 输出最终数据。"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import ensure_dirs  # noqa: E402
import fetch_openalex  # noqa: E402
import fetch_arxiv  # noqa: E402
import fetch_dblp  # noqa: E402
import fetch_orcid  # noqa: E402
import merge  # noqa: E402


def main():
    t0 = time.time()
    ensure_dirs()
    fetch_openalex.run()
    fetch_arxiv.run()
    fetch_dblp.run()
    fetch_orcid.run()
    merge.run()
    print(f"[done] 全部完成，耗时 {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
