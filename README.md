# AI 前沿日报 · nanafox-daily

面向 [nanafox.com/daily/](https://nanafox.com/daily/) 的静态站点仓库：每天把一图总览 PNG + 结构化 JSON 建成可部署到 **Cloudflare Pages** 的站点。

本仓库归属 GitHub 组织 **nana-fox**。2026-10-09 核实：Cloudflare Pages 已连接本仓库的 `main`，输出目录为 `dist`，构建命令为空；推送生产分支即发布已生成的 `dist/`。官网与日报独立发布，官网通过 Cloudflare Worker 访问本项目。

## 目录结构

```text
data/                 日报源文件 YYYY-MM-DD.{json,png}（构建输入）
scripts/
  build_site.py       生成静态站（支持 BASE_PATH）
  export_pack.py      单日 ZIP 导出
site/css/style.css    样式
dist/                 构建输出（可直接 wrangler pages deploy）
  index.html          → 跳转到 /daily/
  daily/              站点本体（BASE_PATH=/daily）
wrangler.toml.example 部署示例（勿把 Token 写进仓库）
PLAN.md               发布架构说明
```

## 本地构建

```bash
# 默认 BASE_PATH=/daily（也可用环境变量）
python3 scripts/build_site.py

# 或显式指定
BASE_PATH=/daily python3 scripts/build_site.py --digest-dir data --dist dist

# 本地预览（注意路径在 /daily/）
python3 -m http.server 8080 --directory dist
# 打开 http://127.0.0.1:8080/daily/
```

构建产物：

| 路径 | 内容 |
|------|------|
| `dist/daily/index.html` | 最新一期 |
| `dist/daily/archive/` | 归档 |
| `dist/daily/latest.json` | 最新日期与三条摘要，供后续集成使用 |
| `dist/daily/YYYY-MM-DD/` | 历史日页 |
| `dist/daily/assets/*` | PNG / JSON |
| `dist/daily/export/*.zip` | 图+JSON 打包 |

## GitHub 自动发布（当前生产方式）

Cloudflare GitHub App 必须授权 nanafox-daily。2026-10-09 曾因安装仅授权官网仓库，出现「自动部署已启用」但推送未触发；仓库授权与 Pages 开关需同时有效。

```bash
python3 -m unittest discover -s tests -v
python3 scripts/build_site.py
git add data dist scripts site
git commit -m "Publish daily briefing"
git push origin main
```

Pages 直接发布 `dist/`，提交前必须重新构建。构建会重建整个输出目录，`data/` 中应保留所有需要公开的历史期数，并保持同名 JSON/PNG 成对。Grok 的采集、筛选与长图生成流程继续负责写入 `data/`。

网页正文按「今日要点 → 分类摘要 → 一图总览」呈现；长图默认折叠。首页、归档和日期页使用 NanaFox 品牌导航并提供返回官网入口。

`/daily/latest.json` 由构建器自动生成，格式为 `{date, title, url, tldr: [{title, text}]}`；`date` 为 ISO 日期，摘要最多三条，缓存 60 秒。官网首页当前只展示固定介绍与阅读入口，不读取当日摘要；日报更新不需要重新发布官网。

## Wrangler 直传（可选）

Git 集成项目仍可用 Wrangler 直传。后续推送 `main` 会再次发布仓库中的 `dist/`，因此应同步仓库产物，避免旧版本覆盖直传版本。不要把 Cloudflare API Token 提交进 Git。

```bash
export CLOUDFLARE_API_TOKEN=...    # Account · Cloudflare Pages · Edit
export CLOUDFLARE_ACCOUNT_ID=...

# 仅首次：在 Dashboard 或命令行建空项目
npx wrangler pages project create nanafox-daily

# 构建后上传
python3 scripts/build_site.py
npx wrangler pages deploy dist --project-name=nanafox-daily
```

预览域名形如 `https://nanafox-daily.pages.dev/daily/`。

### 挂到 nanafox.com/daily/

官网（另仓）与日报（本仓）分开维护时：

1. Pages 项目 `nanafox-daily` 已连接 `main`，从 `dist/` 独立发布。
2. 官网仓库中的 Worker `nanafox-daily-router` 将主域名与 www 下的 `/daily/` 请求转发到本项目（保留路径前缀）。`/daily` 自动跳转到 `/daily/`，其他路径回到官网。Worker 源码和回退说明在 `nanafox-landing/cloudflare/daily-router/` 与官网 `DEPLOY.md`。
3. 官网仓库本身不必包含日报大图。

## 每日流水线（含周末）

```text
1. 采集 + 筛选 + 渲染 → data/YYYY-MM-DD.{json,png}
2. python3 scripts/build_site.py
3. 提交完整 data/ 与 dist/，推送 main → Pages 自动部署
```

使用 Git 自动部署时，仓库中的输出应包含完整公开历史。采用独立上传与外部归档存储之前，不要只保留最近一期再重建整个 `dist/`。

## 自定义域名路径

最终对外地址：**https://nanafox.com/daily/**

- 首页：`/daily/`
- 归档：`/daily/archive/`
- 某日：`/daily/2026-10-09/`

## 相关

- 筛选标准与信源库在日报流水线侧维护，不在本仓展开。
- 更详细的架构对比见 [PLAN.md](./PLAN.md)。
