# 日报网站与 Grok Bot 协作约定

2026-10-09，通过 Grok Bot 的「AI 日报」聊天核对。本文记录迁移设计，尚未启用新定时任务或部署新网站。

## 分工

- Codex：网站设计、历史阅读、浏览器端长图/微信公众号图文配图/小红书组图/JSON 导出及模板代码。
- Grok Bot：定时采集、来源核实、筛选去重、每日结构化数据与内容发布。
- 迁移期保留 Bot 原有 PNG、ZIP 和聊天附件流程；正式模板切换需在网站与 Bot 环境验证后进行。

## Bot 核对结果

以下为 Bot 在聊天中核查后报告，本地不具备其任务执行环境：

- 「AI 前沿日报」启用中，每天 07:35，Asia/Shanghai，包含周末；这是启动时间，不是网站更新完成时间。
- 2026-10-09 最近任务状态 failed，当日人工补跑完成；无平台级自动重试，采集侧使用超时与跳过。
- 采集目录 `/workspace/ai-digest/`，包含 collect.py、CURATION.md、seen.jsonl、render.py、export_pack.py。
- 发布副本 `/workspace/ai-digest/publish/repo` 的本地 main 为 1dba507，远端为 7ebf637，落后四个提交。
- 正式仓库 nana-fox/nanafox-daily，Pages 连接 main，空构建命令，发布已生成 dist。
- Bot 于 13:47 确认最终分工与发布约定。现有定时任务正文已经要求 Git 推送自动部署，没有 Wrangler 直传；部分外部旧文档仍有 Wrangler 提示。
- 定时任务正文尚未加入“只提交 data/dist、冲突同步后重建、禁止强推”等约定；这是迁移启用前的待办。

## 数据兼容

- `data/YYYY-MM-DD.json` 是日期标识与历史排序依据；JSON 的 date 允许显示文本，例如 `2026-10-09 周五`。
- 顶层 title、eyebrow、date、tldr、sections；brand、tldr_heading 可选。
- tldr 支持 `{title,text}`，兼容旧字符串条目。
- sections 包含 heading、items，可选 note、style、accent；页面不依赖其装饰字段。
- items 包含 title、detail、why、source、tag、url；related、related_urls 可选，兼容旧 summary。
- 新字段默认可选，不随意改变既有字段含义；导出绑定当前阅读的 JSON。
- 保留所有公开历史。修改当日内容使用同名文件，Git 记录修订。

## 发布约定

1. 同步最新 origin/main，确认使用当前仓库代码。
2. 写入当日 data，迁移期保持同名 JSON/PNG 配对。
3. 使用仓库维护的统一构建入口生成完整 dist，不使用 Bot 外部旧网站模板。
4. 校验产物后只提交每日 data 与 dist，不提交 Bot 本地对 site/scripts 的旧版本覆盖。
5. 推送遇到并发更新时，重新同步并重建；禁止强推或重推旧 dist。
6. 如新网站需要 Node 构建，先提供统一入口与依赖说明，在 Bot 环境验证后启用。

## 网站候选版本（2026-10-09）

- 分支 `codex/daily-reader-export`：从远端 main 的 7ebf637 创建，网站与浏览器导出已接入两期真实数据，生产 main 未修改。
- 源码 `web/`，已编译模板 `site/reader/`，每日仍使用 `python3 scripts/build_site.py`。本地已在 PATH 仅 `/usr/bin:/bin`（无 Node）的环境构建成功。
- Python 7 项测试、前端 3 项测试通过；已实际下载长图、公众号 ZIP、小红书 ZIP 和原始 JSON；手机抽屉、归档、日期切换、自定义模板验证通过。
- Bot 联调时先在独立临时 clone 检出候选分支，使用现有两期数据构建并检查最新 JSON/历史路径；可在临时目录复制新日期数据演练，不能推送虚构期数，也不修改生产发布副本与定时任务。
- 候选通过并合并 main 后，再同步生产发布副本与更新任务正文。仅修改定时任务提示词不足以证明运行成功。

## 迁移前待完成

- 网站验收后，将已确认的发布约定写入 Bot 任务正文并验证一次真实运行。
- 新版接入与本地兼容测试已完成，等待 Bot 环境独立联调。
- 在 Bot 环境验证更新后的构建入口。
- 单独完善失败通知与有边界的重试；当前不声称已具备自动恢复。
- 验证公众号插图、小红书图片上传与正式域名访问，再切换模板。
