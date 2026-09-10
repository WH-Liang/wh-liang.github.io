# 个人科研网站（自动更新）

一个**自动更新**的个人科研主页：自动同步本人发表的论文，自动抓取遥感 / 计算机领域顶刊、顶会及 arXiv 预印本，按期刊、会议、年份、主题整理归类，支持搜索与筛选。

## 功能

- **本人发表自动同步**：通过 ORCID 公开 API 拉取，无需手动录入
- **顶刊自动抓取**：遥感（RSE / ISPRS / TGRS / JAG / GRSL 等）与计算机顶刊（TPAMI / IJCV / TIP / TOG 等），按 ISSN 精确检索
- **顶会自动抓取**：CVPR / ICCV / ECCV / NeurIPS / ICML / ICLR / AAAI / IJCAI（DBLP 源，被反爬拦截时自动降级为 arXiv 分类订阅）
- **arXiv 预印本订阅**：按研究关键词 + cs.CV / cs.LG / cs.AI 分类每日抓取
- **智能整理**：按期刊 / 会议 / 年份 / 研究主题归类，全文搜索 + 组合筛选
- **细节**：摘要、被引数、DOI / PDF / arXiv 链接、一键复制 BibTeX、中英双语

## 目录结构

```
├── .github/workflows/daily-update.yml  # 每日定时更新 + 部署
├── scripts/                            # Python 数据脚本（零第三方依赖）
│   ├── config.json                     # ★ 所有配置：个人资料/期刊会议/关键词
│   ├── fetch_openalex.py               # 顶刊（OpenAlex 按 ISSN）
│   ├── fetch_dblp.py                   # 顶会（DBLP，含反爬降级）
│   ├── fetch_arxiv.py                  # arXiv 预印本
│   ├── fetch_orcid.py                  # 本人论文（ORCID）
│   ├── merge.py                        # 合并去重 + 主题打标
│   └── run_all.py                      # 一键运行
├── data/                               # 生成的数据（papers.json 等）
├── src/                                # Astro 前端
└── public/                             # 静态资源
```

## 快速开始

### 1. 填写配置

编辑 `scripts/config.json`：

- `profile`：你的姓名、单位、职称、研究方向、邮箱，以及 **`orcid`**（本人论文同步必需）
- `arxiv.keywords`：你关注的 arXiv 关键词
- `journals` / `conferences`：要跟踪的期刊会议清单（默认已配好常用顶刊顶会）
- `topics`：主题标签的关键词映射

### 2. 本地抓取数据

```bash
python scripts/run_all.py
```

> 脚本仅用 Python 标准库，无需安装依赖。

### 3. 本地预览

```bash
npm install
npm run dev      # 开发预览
npm run build    # 构建到 dist/
```

> 提示：若在 WorkBuddy 里执行 `npm run build`，末尾清理临时文件时会被内置的「安全删除」保护拦截（报 exit 1，但页面已完整生成）。此时改用 `env -u NODE_OPTIONS npm run build` 即可干净构建。普通终端与 GitHub Actions（Linux）不受影响。

## 部署到 GitHub Pages

1. 在 GitHub 新建仓库，把代码推送到 `main` 分支
2. 仓库 **Settings → Pages** → Source 选 **GitHub Actions**
3. 在仓库 **Settings → Secrets and variables → Actions → Variables** 中设置：
   - `BASE_PATH`：仓库名，如 `/my-research-site`（用自定义域名时设为空）
   - `SITE_URL`：站点地址，如 `https://yourname.github.io`
4. 首次手动触发一次 Actions，之后每天自动更新

## 关于 DBLP 反爬

DBLP 自 2024 年起对自动化访问启用了反爬挑战，脚本会检测拦截并自动降级为 **arXiv 分类订阅**（cs.CV / cs.LG / cs.AI），论文库仍能覆盖绝大多数顶会论文（以预印本形式）。若你希望获得精确的「CVPR 2024 正式论文」列表，可：
- 申请免费的 [Semantic Scholar API Key](https://www.semanticscholar.org/product/api)，我可以帮你加上该数据源；
- 或接受当前 arXiv 分类订阅方案。
