#!/usr/bin/env python3
"""Render an AI digest JSON file into a portrait infographic PNG.

Usage:
    .venv/bin/python render.py INPUT.json [-o OUTPUT.png] [--width 1080] [--scale 2] [--html OUT.html]
"""
import argparse, html, json, pathlib, sys

TAG_COLORS = {  # tag -> (bg, fg)
    "模型发布": ("#ede9fe", "#6d28d9"),
    "产品":     ("#dbeafe", "#1d4ed8"),
    "研究":     ("#dcfce7", "#15803d"),
    "评测":     ("#e0e7ff", "#4338ca"),
    "论文":     ("#d1fae5", "#047857"),
    "文章":     ("#fef3c7", "#b45309"),
    "观点":     ("#ffe4e6", "#be123c"),
    "工程":     ("#e0f2fe", "#0369a1"),
    "开源":     ("#fce7f3", "#be185d"),
    "融资":     ("#f1f5f9", "#334155"),
    "Agent":    ("#d1fae5", "#047857"),
    "政策":     ("#fee2e2", "#b91c1c"),
    "市场":     ("#e0e7ff", "#4338ca"),
    "标准":     ("#ccfbf1", "#0f766e"),
    "芯片":     ("#fef9c3", "#a16207"),
}
DEFAULT_TAG = ("#f1f5f9", "#475569")
FOOTER_HINT = "原文链接见消息正文"  # fixed, neutral footer text; never put a sources list on the image
# default accent per section position (7 sections: 模型 / Agent / 产品 / 论文 / 行业 / 国内 / 讨论热点)
SECTION_ACCENTS = ["#f97316", "#10b981", "#3b82f6", "#8b5cf6", "#0ea5e9", "#ef4444", "#ec4899"]

CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { background: #eef1f7; }
body { width: %(width)dpx; font-family: "Noto Sans CJK SC", "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif;
       color: #0f172a; -webkit-font-smoothing: antialiased; }
.card { margin: 0; background: #f6f7fb; }
.header { position: relative; overflow: hidden; padding: 64px 64px %(hpad)dpx;
  background: radial-gradient(circle at 85%% 10%%, rgba(139,92,246,.55), transparent 45%%),
              radial-gradient(circle at 10%% 100%%, rgba(14,165,233,.45), transparent 50%%),
              linear-gradient(135deg, #0b1023 0%%, #1e1b4b 60%%, #312e81 100%%); color: #fff; }
.header .eyebrow { font-size: 22px; letter-spacing: 6px; color: #a5b4fc; font-weight: 700; }
.header h1 { font-size: 76px; font-weight: 900; letter-spacing: 4px; margin-top: 10px; line-height: 1.1; }
.header .meta { display: flex; gap: 14px; margin-top: 26px; align-items: center; flex-wrap: wrap; }
.pill { font-size: 24px; padding: 8px 20px; border-radius: 999px; background: rgba(255,255,255,.12);
        border: 1px solid rgba(255,255,255,.22); color: #e0e7ff; }
.pill.date { background: #fff; color: #1e1b4b; font-weight: 800; border: none; }
.grid-deco { position: absolute; right: -40px; top: -40px; width: 360px; height: 360px; opacity: .18;
  background-image: linear-gradient(#fff 1px, transparent 1px), linear-gradient(90deg, #fff 1px, transparent 1px);
  background-size: 36px 36px; transform: rotate(12deg); border-radius: 40px; }
.body { padding: 44px 48px 28px; }
.section { margin-bottom: 40px; }
.section:last-child { margin-bottom: 14px; }
.section h2 { font-size: 36px; font-weight: 900; display: flex; align-items: center; gap: 14px; margin: 0 8px 22px; }
.section h2 .bar { width: 8px; height: 34px; border-radius: 4px; }
.section h2 .count { margin-left: auto; font-size: 20px; color: #94a3b8; font-weight: 500; }
.item { position: relative; display: flex; gap: 22px; align-items: flex-start; background: #fff; border-radius: 22px;
  padding: 26px 30px 24px 26px; margin-bottom: 18px; box-shadow: 0 1px 2px rgba(15,23,42,.04), 0 6px 20px rgba(15,23,42,.06); }
.idx { flex: none; width: 46px; height: 46px; border-radius: 14px; display: flex; align-items: center; justify-content: center;
  font-size: 23px; font-weight: 900; color: #fff; font-family: "Noto Sans", "DejaVu Sans", sans-serif; margin-top: 2px; }
.content { flex: 1; min-width: 0; }
.row1 { display: flex; align-items: flex-start; gap: 14px; }
.title { font-size: 31px; font-weight: 800; line-height: 1.35; flex: 1; min-width: 0; color: #0f172a; }
.tag { flex: none; font-size: 19px; font-weight: 700; padding: 5px 13px; border-radius: 10px; margin-top: 4px; }
.summary { font-size: 24px; color: #475569; line-height: 1.5; margin-top: 8px;
           white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.detail { font-size: 25px; color: #334155; line-height: 1.68; margin-top: 10px; }
.why { display: flex; gap: 10px; align-items: baseline; margin-top: 14px; padding: 10px 16px; border-radius: 12px;
       font-size: 23px; line-height: 1.55; font-weight: 600; }
.why .label { flex: none; font-weight: 800; }
.source { display: inline-block; margin-top: 14px; font-size: 19px; color: #64748b; background: #f1f5f9;
          padding: 4px 12px; border-radius: 8px; font-family: "Noto Sans", "Noto Sans CJK SC", sans-serif; }
.source.inline { margin: 0; padding: 2px 10px; font-size: 18px; vertical-align: 2px; white-space: nowrap; }
.bullets { background: #fff; border-radius: 22px; padding: 10px 30px;
  box-shadow: 0 1px 2px rgba(15,23,42,.04), 0 6px 20px rgba(15,23,42,.06); }
.bullet { display: flex; gap: 16px; align-items: flex-start; padding: 18px 0; border-bottom: 1px dashed #e2e8f0; }
.bullet:last-child { border-bottom: none; }
.bullet .dot { flex: none; width: 12px; height: 12px; border-radius: 50%%; margin-top: 15px; }
.bullet .txt { font-size: 24px; line-height: 1.65; color: #475569; }
.bullet .bt { font-size: 26px; font-weight: 800; color: #0f172a; margin-right: 10px; }
.tldr { margin: -30px 48px 0; position: relative; background: #fff; border-radius: 24px; padding: 26px 32px 18px;
  box-shadow: 0 10px 30px rgba(30,27,75,.16); border-top: 6px solid #6366f1; }
.tldr .th { font-size: 30px; font-weight: 900; color: #1e1b4b; margin-bottom: 8px; }
.tldr .tl { display: flex; gap: 14px; align-items: flex-start; padding: 10px 0; }
.tldr .tn { flex: none; width: 34px; height: 34px; border-radius: 50%%; background: #eef2ff; color: #4f46e5; font-weight: 900;
  font-size: 19px; display: flex; align-items: center; justify-content: center; margin-top: 3px; font-family: "Noto Sans", sans-serif; }
.tldr .tt { font-size: 25px; line-height: 1.6; color: #334155; }
.tldr .tt b { color: #0f172a; font-weight: 800; }
.sec-note { margin: -10px 8px 18px; font-size: 22px; line-height: 1.6; color: #64748b; padding: 10px 16px; border-radius: 12px;
  background: #fff; border: 1px dashed #cbd5e1; }
.related { margin-top: 12px; font-size: 20px; line-height: 1.6; color: #64748b; }
.related .rl { font-weight: 700; color: #94a3b8; margin-right: 6px; }
.footer { padding: 6px 56px 40px; display: flex; justify-content: space-between; gap: 24px; white-space: nowrap; color: #94a3b8; font-size: 20px; }
"""

def esc(s): return html.escape(str(s or ""))

def hex_to_rgba(h, a):
    h = h.lstrip("#"); r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{a})"

def render_item(i, it, accent):
    bg, fg = TAG_COLORS.get(it.get("tag", ""), DEFAULT_TAG)
    tag = f'<span class="tag" style="background:{bg};color:{fg}">{esc(it["tag"])}</span>' if it.get("tag") else ""
    parts = [f'<div class="row1"><div class="title">{esc(it["title"])}</div>{tag}</div>']
    if it.get("summary"):
        parts.append(f'<div class="summary">{esc(it["summary"])}</div>')
    src_chip = f'<span class="source">{esc(it["source"])}</span>' if it.get("source") else ""
    if it.get("detail"):  # source chip rides inline at the end of the detail paragraph
        parts.append(f'<div class="detail">{esc(it["detail"])} {src_chip.replace("source", "source inline", 1)}</div>')
        src_chip = ""
    if it.get("why"):
        parts.append(f'<div class="why" style="background:{hex_to_rgba(accent, .09)};color:#1e293b">'
                     f'<span class="label" style="color:{accent}">💡 看点</span><span>{esc(it["why"])}</span></div>')
    if src_chip:
        parts.append(src_chip)
    if it.get("related"):  # extra coverage of the SAME event (dedupe): short labels, no URLs
        parts.append(f'<div class="related"><span class="rl">🔗 另见</span>{" · ".join(esc(r) for r in it["related"])}</div>')
    return (f'<div class="item"><div class="idx" style="background:{accent}">{i}</div>'
            f'<div class="content">{"".join(parts)}</div></div>')

def render_bullets(items, accent):
    rows = "".join(f'<div class="bullet"><span class="dot" style="background:{accent}"></span>'
                   f'<div class="txt"><span class="bt">{esc(it["title"])}</span>{esc(it.get("detail") or it.get("summary"))}</div></div>'
                   for it in items)
    return f'<div class="bullets">{rows}</div>'

def build_html(d, width):
    secs = []
    for si, sec in enumerate(d["sections"]):
        accent = sec.get("accent") or SECTION_ACCENTS[si % len(SECTION_ACCENTS)]
        items = sec.get("items", [])
        if sec.get("style") == "bullets":
            inner = render_bullets(items, accent); count = ""
        else:
            inner = "".join(render_item(i + 1, it, accent) for i, it in enumerate(items))
            count = f'<span class="count">{len(items)} 条</span>'
        note = f'<div class="sec-note">{esc(sec["note"])}</div>' if sec.get("note") else ""
        if not items: count = ""
        secs.append(f'<div class="section"><h2><span class="bar" style="background:{accent}"></span>'
                    f'{esc(sec["heading"])}{count}</h2>{note}{inner}</div>')
    pills = f'<span class="pill date">{esc(d["date"])}</span>'
    # subtitle / coverage-window pill intentionally omitted (date only)
    # Footer never lists data sources (per-card source chips are enough); the legacy "footer" field is ignored.
    if d.get("footer"):
        print("NOTE: 'footer' field is ignored; the image footer is fixed to FOOTER_HINT", file=sys.stderr)
    footer_l = esc(FOOTER_HINT)
    tldr = ""
    if d.get("tldr"):  # list of strings, or {"title","text"} objects
        rows = []
        for n, t in enumerate(d["tldr"], 1):
            body = (f'<b>{esc(t["title"])}</b>　{esc(t.get("text"))}' if isinstance(t, dict) else esc(t))
            rows.append(f'<div class="tl"><span class="tn">{n}</span><div class="tt">{body}</div></div>')
        tldr = f'<div class="tldr"><div class="th">{esc(d.get("tldr_heading", "⚡ 今日要点"))}</div>{"".join(rows)}</div>'

    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><style>{CSS % {"width": width, "hpad": 86 if d.get("tldr") else 56}}</style></head>
<body><div class="card" id="card">
<div class="header"><div class="grid-deco"></div><div class="eyebrow">{esc(d.get("eyebrow", "DAILY AI BRIEFING"))}</div>
<h1>{esc(d.get("title", "AI 前沿日报"))}</h1><div class="meta">{pills}</div></div>
{tldr}<div class="body">{"".join(secs)}</div>
<div class="footer"><span>{footer_l}</span><span>{esc(d.get("brand", ""))}</span></div>
</div></body></html>'''

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input"); ap.add_argument("-o", "--output")
    ap.add_argument("--width", type=int, default=1080); ap.add_argument("--scale", type=float, default=2)
    ap.add_argument("--html", help="also save the intermediate HTML here")
    a = ap.parse_args()
    src = pathlib.Path(a.input)
    d = json.loads(src.read_text(encoding="utf-8"))
    out = pathlib.Path(a.output) if a.output else src.with_suffix(".png")
    page_html = build_html(d, a.width)
    if a.html: pathlib.Path(a.html).write_text(page_html, encoding="utf-8")
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="chrome")  # system Google Chrome
        except Exception:
            browser = p.chromium.launch()  # fallback: `playwright install chromium`
        page = browser.new_page(viewport={"width": a.width, "height": 800}, device_scale_factor=a.scale)
        page.set_content(page_html, wait_until="load")
        page.evaluate("document.fonts.ready")
        # warn about truncated (ellipsized) lines so the routine can shorten text
        clipped = page.evaluate("""() => [...document.querySelectorAll('.summary')]
            .filter(e => e.scrollWidth > e.clientWidth + 1).map(e => e.textContent)""")
        for t in clipped: print(f"WARNING: text truncated on image: {t}", file=sys.stderr)
        page.locator("#card").screenshot(path=str(out))
        browser.close()
    print(out)

if __name__ == "__main__":
    main()
