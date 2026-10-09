# 发布方案摘要 · Cloudflare Pages + Wrangler

> 目标：每天生成 `YYYY-MM-DD.png` + `.json` 后，发布到 **nanafox.com/daily/**。  
> 本仓版本化站点代码；**部署走 Wrangler 直传**，不在此索取或保存 Cloudflare Token。

## 站点路径（BASE_PATH=/daily）

| 路径 | 作用 |
|------|------|
| `/daily/` | 最新一期 |
| `/daily/archive/` | 归档列表 |
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

| | Wrangler 直传（默认） | Git 连接 Pages |
|--|----------------------|----------------|
| 流程 | build → `wrangler pages deploy dist` | push → Pages 自动发布 |
| 大图 | 不必进 Git | 仓库易膨胀 |
| 本仓角色 | 代码 + 可选近几日样例 | 亦可作构建源 |

当前选择：**Wrangler 直传**。本 GitHub 仓用于代码审计与备份；日后若要改 Git 集成，把 Pages 连到本仓并设输出目录为 `dist` 即可。

## 每日命令

```bash
python3 scripts/build_site.py          # BASE_PATH 默认 /daily
npx wrangler pages deploy dist --project-name=nanafox-daily
```

密钥仅通过环境变量：`CLOUDFLARE_API_TOKEN`、`CLOUDFLARE_ACCOUNT_ID`。
