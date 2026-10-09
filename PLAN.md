# 发布方案摘要 · Cloudflare Pages + Wrangler

> 目标：每天生成 `YYYY-MM-DD.png` + `.json` 后，发布到 **nanafox.com/daily/**。  
> 当前生产已连接 GitHub main，Pages 直接发布 dist；Wrangler 直传仍可选。Grok 负责生成日报，官网独立展示固定介绍与阅读入口；不在仓库索取或保存 Cloudflare Token。

## 站点路径（BASE_PATH=/daily）

| 路径 | 作用 |
|------|------|
| `/daily/` | 最新一期 |
| `/daily/archive/` | 归档列表 |
| `/daily/latest.json` | 最新一期摘要文件，供后续集成使用 |
| `/daily/YYYY-MM-DD/` | 历史日页 |
| `/daily/assets/YYYY-MM-DD.png` | 总览图 |
| `/daily/assets/YYYY-MM-DD.json` | 结构化数据 |
| `/daily/export/YYYY-MM-DD.zip` | 图+JSON 打包 |

构建脚本会把文件嵌在 `dist/daily/` 下，并在 `dist/index.html` 做跳转，便于 Pages 根部署后直接访问 `/daily/`。

## 为何独立 Pages 项目

- 官网 `nanafox.com` 与日报更新节奏不同，避免每天上传碰官网仓库。
- 项目名建议：`nanafox-daily`。
- 用 Worker / 路由把 `nanafox.com/daily/*` 转到该项目，HTML 内链接一律带 `/daily` 前缀。

## Wrangler 直传 vs Git 连接

| | Wrangler 直传（可选） | Git 连接 Pages（当前） |
|--|----------------------|----------------|
| 流程 | build → `wrangler pages deploy dist` | push → Pages 自动发布 |
| 大图 | 不必进 Git | 仓库易膨胀 |
| 本仓角色 | 代码 + 可选近几日样例 | 亦可作构建源 |

2026-10-09 实际生产配置：**GitHub 自动部署，输出 dist，构建命令为空**。推送前运行构建器并提交完整输出。官网 Worker 已负责主域名与 www 的日报路由，HTML 链接保留 `/daily` 前缀。

## 每日命令

```bash
python3 scripts/build_site.py          # BASE_PATH 默认 /daily
git add data dist scripts site
git commit -m "Publish daily briefing"
git push origin main
```

密钥仅通过环境变量：`CLOUDFLARE_API_TOKEN`、`CLOUDFLARE_ACCOUNT_ID`。
