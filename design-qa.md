# 网站接入视觉验收

final result: passed

2026-10-09。本报告仅覆盖本地候选版本，不表示生产部署、Bot 定时执行或公众号/小红书平台上传已经验收。

## 视觉基准与浏览器实现

视觉基准为用户已确认的设计原型，而非重新生成的设计图。

| 状态 | 基准 | 实现 | CSS viewport | 密度处理 |
| --- | --- | --- | --- | --- |
| 10/09 阅读页桌面 | `/Users/nio/project/nanafox/nanafox-daily-design/output/reader-desktop.jpg` | `qa/reader-desktop-final.jpg` | 1440×1024 | 基准 1440×1024；浏览器 DPR 2 截图 2880×2048，归一化到 1440×1024 |
| 10/09 阅读页手机 | `/Users/nio/project/nanafox/nanafox-daily-design/output/reader-mobile.jpg` | `qa/reader-mobile-final.jpg` | 390×844 | 基准与实现归一化后均 390×844，DPR 2 |
| 公众号导出第 3 页桌面 | `/Users/nio/project/nanafox/nanafox-daily-design/output/export-wechat-desktop.jpg` | `qa/export-desktop-final.jpg` | 1440×1024 | 基准 1440×1024，实现原始 2880×2048；组合时归一化到 1440×1024 |
| 手机导出面板 | 原型相同结构；功能要求为当前一期无日期选择 | `qa/export-mobile-final.jpg` | 390×844 | 归一化后 390×844 |
| 自定义暖色封面 | 原型暖色模板与用户指定字段 | `qa/custom-paper.png`、`qa/custom-template.jpg` | 默认 1280×720 | 实际导出 PNG 1080×608 |

站点为 `http://127.0.0.1:4188/daily/`，截图来自实际构建 dist 的浏览器渲染。全幅并排比较输入：`qa/desktop-comparison-final.jpg`、`qa/mobile-comparison-final.jpg`、`qa/export-comparison-final.jpg`。已打开组合图共同判断，非分别看图。重点区域：`qa/type-comparison-final.jpg`，核对正文行距、段落和来源信息。

## 修正与比较历史

1. 首轮桌面 `qa/reader-desktop.jpg`、`qa/desktop-comparison.jpg`：P2，旧静态 CSS 的 body 背景、字体与行距继承导致新版颜色和纵向阅读节奏偏离原型。显式恢复新版 body/font/line-height、品牌字距和链接状态后重新捕获；最终全幅与重点排版比较均吻合。
2. 手机交互 P2：历史抽屉关闭后离屏链接仍可获得键盘焦点。补充 visibility、背景 inert、焦点移入/返回、Tab 限制与 Escape 关闭。最终手机截图右侧焦点环为关闭抽屉后回到触发按钮的预期状态。
3. 导出内容 P2：小红书原型仅封面展示要点标题，缺少完整要点正文。补充要点正文分页，长文章续页重复标题并按实际标题高度留空间；单元测试验证正文行完整保留。`qa/xhs-contact.jpg` 包含实测 20 页，均为 1080×1440。
4. 频繁切换模板时释放旧 Canvas 像素内存，缩略图只绘制封面；随后重新构建并成功导出自定义暖色封面。期间一次浏览器会话超时，未将其作为功能通过证据，恢复后按操作验证。

## 交互与验证

- 两期真实日报 10/08、10/09 切换，标题、日期、19/17 条动态与当前选中状态一致；归档倒序列出两期，链接为真实日期路径。
- 手机无横向溢出；历史抽屉打开、Escape 关闭和焦点返回；导出底部按钮完整位于 844 像素视口内。
- 当前一期直接导出，无日期输入；白底/纸张切换、标题、署名和来源开关改变图片，阅读正文不变。
- 实际下载：10/08 长图 1080×11358；公众号 ZIP 13 页；小红书 ZIP 20 页，均 1080×1440；JSON 深度比较等于源 JSON。
- 自定义 10/09 暖色封面 1080×608，标题 `NanaFox 今日 AI 精选`，署名 `NanaFox 编辑部`；来源关闭后分页数量相应改变。
- 原始 Bot 长图默认折叠，原 PNG/JSON/ZIP 路径保留。
- 最终页面浏览器 error/warn 日志为空。Python 7 项、前端 3 项测试通过；依赖审计 0 漏洞。仅 Python 的 PATH 环境构建两期成功。

## 剩余事项

无未解决 P0/P1/P2 视觉问题。P3：部分分类结束页留白较多，可后续微调，但正文、来源和页码未截断。公众号和小红书平台内实际上传尚未验证；Bot 环境联调、定时任务更新与生产发布待执行。

截图和下载样本为本地 `qa/` 证据，不提交到生产站点。构建产物与全部公开历史提交到候选分支。
