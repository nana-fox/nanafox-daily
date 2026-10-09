# AI 前沿日报 · nanafox-daily

面向 [nanafox.com/daily/](https://nanafox.com/daily/) 的静态站点仓库：每天把一图总览 PNG + 结构化 JSON 建成可部署到 **Cloudflare Pages** 的站点。

本仓库归属 GitHub 组织 **nana-fox**，用于版本化站点代码与近期样例内容；**日常发布推荐 Wrangler 直传 `dist/`**，不必每次把大图推进 Git。

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
| `dist/daily/YYYY-MM-DD/` | 历史日页 |
| `dist/daily/assets/*` | PNG / JSON |
| `dist/daily/export/*.zip` | 图+JSON 打包 |

## Wrangler 直传（推荐）

用户已选定 **Wrangler Direct Upload**，不要把 Cloudflare API Token 提交进 Git。

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

1. Cloudflare 上建好 Pages 项目 `nanafox-daily`，用 Wrangler 每天上传 `dist/`。
2. 在 `nanafox.com` 所在账号里用 **Workers 路由 / 反向代理**，把 `nanafox.com/daily/*` 指到本项目（保留路径前缀 `/daily`，与 `BASE_PATH=/daily` 一致）。
3. 官网仓库本身不必包含日报大图。

## 每日流水线（含周末）

```text
1. 采集 + 筛选 + 渲染 → data/YYYY-MM-DD.{json,png}
2. python3 scripts/build_site.py
3. npx wrangler pages deploy dist --project-name=nanafox-daily
```

可选：把近 1–2 天的 `data/` 与 `dist/` 提交本仓库做备份；历史大图可不进 Git（见 `.gitignore` 说明）。

## 自定义域名路径

最终对外地址：**https://nanafox.com/daily/**

- 首页：`/daily/`
- 归档：`/daily/archive/`
- 某日：`/daily/2026-10-09/`

## 相关

- 筛选标准与信源库在日报流水线侧维护，不在本仓展开。
- 更详细的架构对比见 [PLAN.md](./PLAN.md)。
