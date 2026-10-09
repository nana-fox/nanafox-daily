# 日报网站与 Grok Bot 协作约定

2026-10-09，通过 Grok Bot 的「AI 日报」聊天核对。本文记录迁移设计，尚未启用新定时任务或部署新网站。

## 分工

- Codex：网站设计、历史阅读、浏览器端主图与完整长图导出及模板代码。
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
- Python 7 项测试、前端 3 项测试通过；当前版本实际下载两张 PNG 的 ZIP，手机面板和 4 条要点样例已验证。前一版的渠道组图与自定义设置按用户要求从界面移除。
- Bot 联调时先在独立临时 clone 检出候选分支，使用现有两期数据构建并检查最新 JSON/历史路径；可在临时目录复制新日期数据演练，不能推送虚构期数，也不修改生产发布副本与定时任务。
- 候选通过并合并 main 后，再同步生产发布副本与更新任务正文。仅修改定时任务提示词不足以证明运行成功。

## 迁移前待完成

- 网站验收后，将已确认的发布约定写入 Bot 任务正文并验证一次真实运行。
- Bot 已对前一候选 6430a129 在独立 clone 验证 Python 构建、历史保留、latest.json 与次日演练；最终代码 93ca24082a6ce2bb9970c161ac2c4b1acdc8df26 已于 16:28 按相同方式复验通过。
- 已在 Bot 环境验证最终代码的纯 Python 构建入口；合并后仍需生产副本同步和真实任务运行。
- 单独完善失败通知与有边界的重试；当前不声称已具备自动恢复。
- 正式域名与新版发布链路验收后再切换模板；平台上传另行验证。

## 原版图片模板迁移（2026-10-09）

Bot 提供 `bot-longform-template.zip`，包含原始 `render.py`、内嵌 CSS、当期 HTML、渲染参数与 `export_pack.py`。原件只保存在 `reference/bot-template/` 作为视觉与字段依据，不执行或替换 Bot 本地脚本。

网站直接从当前 JSON 生成 HTML/CSS，再在浏览器本地导出图片。第一版收敛为一张主图和一张完整长图：主图展示全部 tldr，数量不截断，字号固定、高度自适应；长图复用原版版式，保留全部分类内容。两张 PNG 打包下载，无日期选择或渠道配置。JSON 字段与发布接口不变，公开 JSON、PNG、ZIP 历史继续保留，Bot 不需要提供新图片模板字段。

## 最终代码复验回执

Bot 于 2026-10-09 16:28 报告：`codex/daily-reader-export @ 93ca24082a6ce2bb9970c161ac2c4b1acdc8df26` 复验通过，无阻塞。以下为 Bot 在其云环境核查后报告：

- 临时 clone `/tmp/nanafox-daily-verify-HQ92oS/repo` 检出精确提交。
- Python 7 项测试通过；PATH 去掉 Node 后纯 Python 构建两期成功，重建后工作区干净，与提交的 dist 一致。
- latest.json 日期 10/09，公开摘要接口仍最多三条，这是已有摘要接口约定；网站阅读和导出主图使用原始 JSON 的全量 tldr。
- 两期历史、assets、原始 ZIP 和 reader 资源齐全；确认新导出仅主图和长图。
- 次日演练含 4 条 tldr，仅在临时 sim/，未提交或推送。
- 再次确认 Bot 供每日 JSON 与既有 PNG，Web 负责阅读和浏览器生成主图/长图。浏览器实际 ZIP 下载由本地 Codex 验证，Bot 未自行点击下载。
- 未合并 PR、未推 main、未改生产或定时任务；生产副本仍是 1dba507。合并后生产副本同步、任务正文更新与真实发布实跑待执行。

本回执后的提交只补充验证文档，前端与构建代码保持上述已验提交。

