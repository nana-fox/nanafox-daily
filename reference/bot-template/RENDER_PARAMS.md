# render.py 视觉与渲染参数（竖版总览）

来源：`/workspace/ai-digest/render.py`（HTML/CSS **全部内嵌**，无外部模板文件）

## 页面与截图

| 项 | 值 |
|---|---|
| CSS 页面宽度 `--width` | **1080** px（默认） |
| Playwright `device_scale_factor` `--scale` | **2**（默认）→ 输出约 **2160** px 宽 |
| 初始 viewport | `{width: 1080, height: 800}`，截图前按 `#card` 实际高度 `set_viewport_size` |
| 浏览器 | 优先 `channel="chrome"`，否则 Playwright Chromium |
| 截图目标 | `#card` 元素 `screenshot(type="png")` |
| 等待 | `wait_until="load"` + `document.fonts.ready` |

## 字体（按 CSS font-family）

- 正文中文：`"Noto Sans CJK SC", "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif`
- 序号/部分拉丁：`"Noto Sans", "DejaVu Sans", sans-serif`；source chip 回退含 CJK
- 本机依赖：`fonts-noto-cjk`（Noto Sans CJK SC）、`fonts-noto-color-emoji`（板块标题 emoji 如 🔥📚💬）
- 检查：`fc-list :lang=zh | grep "Sans CJK"`

## 色彩与版式要点

- 页背景 `#eef1f7`；卡片白底圆角阴影；页头渐变紫蓝 `#1e1b4b → #312e81 → #4338ca`
- 默认板块强调色按顺序：橙 `#f97316`、绿 `#10b981`、蓝 `#3b82f6`、紫 `#8b5cf6`、天空 `#0ea5e9`、红 `#ef4444`、粉 `#ec4899`
- 有 `tldr` 时页头下 padding `hpad=86`，否则 `56`
- 页脚固定左：`原文链接见消息正文`；忽略 JSON `footer` / 覆盖时间 `subtitle`

## 文件说明

- `render.py` — 完整源码（含 `CSS` 字符串与 `build_html`）
- `embedded.css` — 从源码抽出的 CSS（宽已替换为 1080，hpad=86）
- `sample-2026-10-09.html` — 用当期 JSON 生成的中间 HTML（便于浏览器打开对照）

公众号 / 小红书多尺寸模板在同目录上级的 `export_pack.py`（另套 HTML/CSS），本包仅含竖版总览 `render.py`。

## 补充：多平台 `export_pack.py`

同包已附 `export_pack.py`（HTML/CSS 亦内嵌）。默认尺寸（CSS px，@2x）：小红书 1080×1440、公众号封面 1080×460、公众号长条宽 900、X 1600×900；总览复用 `render.build_html` 宽 1080。字体串与总览一致（`BASE_FONT`）。
