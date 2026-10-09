#!/usr/bin/env python3
"""Export a multi-platform image pack from a digest JSON.

Outputs under exports/YYYY-MM-DD/:
  overview.png       — portrait long card (same as render.py, 1080 CSS @2x)
  xhs-01.png …       — 小红书 3:4 (1080×1440) cover + one page per section
  wechat-cover.png   — 公众号封面 ≈2.35:1 (1080×460)
  wechat-strip.png   — 公众号文内长图条（900 宽，含要点 + 各板块摘要）
  x-cover.png        — X 横版封面 16:9 (1600×900)
  YYYY-MM-DD.zip     — all of the above + source JSON

Usage:
  .venv/bin/python export_pack.py 2026-10-09.json
  .venv/bin/python export_pack.py 2026-10-09.json -o exports/2026-10-09
  .venv/bin/python export_pack.py 2026-10-09.json --skip-overview   # reuse existing PNG
"""
from __future__ import annotations

import argparse
import html
import json
import pathlib
import re
import shutil
import sys
import zipfile

# Reuse overview renderer
import render as overview_render

TAG_COLORS = dict(overview_render.TAG_COLORS)
TAG_COLORS.setdefault("评测", ("#e0e7ff", "#4338ca"))  # indigo, missing in overview palette
DEFAULT_TAG = overview_render.DEFAULT_TAG
SECTION_ACCENTS = overview_render.SECTION_ACCENTS

# --- sizes (CSS px; rendered at device_scale_factor) ---
XHS_W, XHS_H = 1080, 1440
WECHAT_COVER_W, WECHAT_COVER_H = 1080, 460  # ≈2.35:1
WECHAT_STRIP_W = 900
X_W, X_H = 1600, 900  # 16:9


def esc(s):
    return html.escape(str(s or ""))


def hex_to_rgba(h, a):
    h = h.lstrip("#")
    r, g, b = (int(h[i : i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{a})"


def day_slug(d: dict, src: pathlib.Path) -> str:
    """Prefer ISO date from filename; fall back to parsing date field."""
    m = re.match(r"(\d{4}-\d{2}-\d{2})", src.stem)
    if m:
        return m.group(1)
    m = re.search(r"(\d{4}-\d{2}-\d{2})", str(d.get("date", "")))
    return m.group(1) if m else src.stem


def short(text: str, n: int) -> str:
    text = (text or "").strip()
    if len(text) <= n:
        return text
    return text[: n - 1] + "…"


def strip_emoji_heading(h: str) -> str:
    """Keep Chinese heading; leave leading emoji if present (looks good on cards)."""
    return (h or "").strip()


# ---------------------------------------------------------------------------
# Shared base CSS tokens
# ---------------------------------------------------------------------------
BASE_FONT = (
    '"Noto Sans CJK SC", "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif'
)


def launch_browser(p):
    try:
        return p.chromium.launch(channel="chrome")
    except Exception:
        return p.chromium.launch()


def screenshot_fixed(browser, page_html: str, out: pathlib.Path, width: int, height: int, scale: float = 2):
    """Render fixed-size viewport shot (for covers / xhs pages)."""
    page = browser.new_page(
        viewport={"width": width, "height": height}, device_scale_factor=scale
    )
    try:
        page.set_content(page_html, wait_until="load")
        page.evaluate("document.fonts.ready")
        page.screenshot(path=str(out), clip={"x": 0, "y": 0, "width": width, "height": height})
    finally:
        page.close()


def screenshot_card(browser, page_html: str, out: pathlib.Path, width: int, scale: float = 2):
    """Render #card element (variable height), like overview."""
    page = browser.new_page(
        viewport={"width": width, "height": 800}, device_scale_factor=scale
    )
    try:
        page.set_content(page_html, wait_until="load")
        page.evaluate("document.fonts.ready")
        page.locator("#card").screenshot(path=str(out))
    finally:
        page.close()


# ---------------------------------------------------------------------------
# 小红书 3:4
# ---------------------------------------------------------------------------
XHS_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { width: %(w)dpx; height: %(h)dpx; overflow: hidden;
  font-family: %(font)s; color: #0f172a; -webkit-font-smoothing: antialiased; background: #0b1023; }
.page { width: %(w)dpx; height: %(h)dpx; position: relative; overflow: hidden; display: flex; flex-direction: column; }
.page.cover {
  background: radial-gradient(circle at 88%% 8%%, rgba(139,92,246,.55), transparent 42%%),
              radial-gradient(circle at 8%% 95%%, rgba(14,165,233,.4), transparent 48%%),
              linear-gradient(145deg, #0b1023 0%%, #1e1b4b 55%%, #312e81 100%%); color: #fff; padding: 72px 56px 56px; }
.page.section { background: #f6f7fb; }
.eyebrow { font-size: 22px; letter-spacing: 6px; color: #a5b4fc; font-weight: 700; }
.cover h1 { font-size: 72px; font-weight: 900; letter-spacing: 3px; margin-top: 14px; line-height: 1.1; }
.cover .date-pill { display: inline-block; margin-top: 28px; font-size: 28px; font-weight: 800;
  padding: 10px 24px; border-radius: 999px; background: #fff; color: #1e1b4b; }
.cover .tldr { margin-top: 48px; flex: 1; display: flex; flex-direction: column; gap: 18px; }
.cover .tl { background: rgba(255,255,255,.1); border: 1px solid rgba(255,255,255,.18);
  border-radius: 20px; padding: 22px 26px; backdrop-filter: blur(6px); }
.cover .tl .tt { font-size: 30px; font-weight: 800; color: #fff; margin-bottom: 8px; }
.cover .tl .td { font-size: 24px; line-height: 1.55; color: #c7d2fe; }
.cover .foot { margin-top: auto; display: flex; justify-content: space-between; align-items: center;
  font-size: 22px; color: #a5b4fc; padding-top: 24px; }
.cover .swipe { font-weight: 700; color: #e0e7ff; }
.sec-head { padding: 48px 48px 0; }
.sec-head .bar { width: 10px; height: 40px; border-radius: 5px; display: inline-block; vertical-align: middle; margin-right: 14px; }
.sec-head h2 { display: inline; font-size: 40px; font-weight: 900; vertical-align: middle; }
.sec-head .pg { float: right; font-size: 22px; color: #94a3b8; font-weight: 600; margin-top: 10px; }
.sec-note { margin: 16px 48px 0; font-size: 22px; color: #64748b; line-height: 1.5;
  padding: 12px 16px; background: #fff; border-radius: 14px; border: 1px dashed #cbd5e1; }
.sec-body { flex: 1; padding: 28px 40px 20px; overflow: hidden; display: flex; flex-direction: column; gap: 18px; justify-content: flex-start; }
.sec-body.sparse { justify-content: space-evenly; }
.sec-body.sparse .item { padding: 28px 28px; }
.sec-body.sparse .title { font-size: 32px; }
.sec-body.sparse .detail { font-size: 24px; line-height: 1.6; }
.sec-body.sparse .why { font-size: 22px; }
.sec-body.sparse .bullets { padding: 16px 28px; }
.sec-body.sparse .bullet .bt { font-size: 28px; }
.sec-body.sparse .bullet .bd { font-size: 24px; }
.item { background: #fff; border-radius: 20px; padding: 22px 26px; box-shadow: 0 4px 16px rgba(15,23,42,.06);
  display: flex; gap: 18px; align-items: flex-start; }
.idx { flex: none; width: 42px; height: 42px; border-radius: 12px; color: #fff; font-weight: 900;
  font-size: 22px; display: flex; align-items: center; justify-content: center; margin-top: 2px; }
.content { flex: 1; min-width: 0; }
.row1 { display: flex; gap: 12px; align-items: flex-start; }
.title { font-size: 28px; font-weight: 800; line-height: 1.35; flex: 1; color: #0f172a; }
.tag { flex: none; font-size: 18px; font-weight: 700; padding: 4px 12px; border-radius: 8px; margin-top: 4px; }
.detail { font-size: 22px; color: #475569; line-height: 1.55; margin-top: 8px; }
.why { margin-top: 10px; font-size: 20px; font-weight: 600; padding: 8px 14px; border-radius: 10px; line-height: 1.45; }
.bullets { background: #fff; border-radius: 20px; padding: 8px 28px; box-shadow: 0 4px 16px rgba(15,23,42,.06); }
.bullet { display: flex; gap: 14px; padding: 18px 0; border-bottom: 1px dashed #e2e8f0; }
.bullet:last-child { border-bottom: none; }
.bullet .dot { flex: none; width: 12px; height: 12px; border-radius: 50%%; margin-top: 12px; }
.bullet .bt { font-size: 26px; font-weight: 800; color: #0f172a; display: block; margin-bottom: 4px; }
.bullet .bd { font-size: 22px; color: #475569; line-height: 1.5; }
.sec-foot { padding: 12px 48px 40px; display: flex; justify-content: space-between;
  font-size: 20px; color: #94a3b8; }
"""


def build_xhs_cover(d: dict, page_i: int, total: int) -> str:
    rows = []
    for t in (d.get("tldr") or [])[:3]:
        if isinstance(t, dict):
            title, text = t.get("title", ""), t.get("text", "")
        else:
            title, text = "", str(t)
        rows.append(
            f'<div class="tl"><div class="tt">{esc(short(title, 16))}</div>'
            f'<div class="td">{esc(short(text, 48))}</div></div>'
        )
    css = XHS_CSS % {"w": XHS_W, "h": XHS_H, "font": BASE_FONT}
    return f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><style>{css}</style></head>
<body><div class="page cover">
  <div class="eyebrow">{esc(d.get("eyebrow", "DAILY AI BRIEFING"))}</div>
  <h1>{esc(d.get("title", "AI 前沿日报"))}</h1>
  <div class="date-pill">{esc(d.get("date", ""))}</div>
  <div class="tldr">{"".join(rows)}</div>
  <div class="foot"><span>{esc(d.get("brand", "AI 前沿日报"))}</span>
    <span class="swipe">左滑看详情 {page_i}/{total}</span></div>
</div></body></html>"""


def build_xhs_section(d: dict, si: int, sec: dict, page_i: int, total: int) -> str:
    accent = sec.get("accent") or SECTION_ACCENTS[si % len(SECTION_ACCENTS)]
    items = sec.get("items") or []
    note = (
        f'<div class="sec-note">{esc(short(sec["note"], 90))}</div>'
        if sec.get("note")
        else ""
    )
    n = len(items)
    sparse = " sparse" if n <= 2 or sec.get("style") == "bullets" else ""
    if sec.get("style") == "bullets":
        rows = []
        for it in items[:5]:
            rows.append(
                f'<div class="bullet"><span class="dot" style="background:{accent}"></span>'
                f'<div><span class="bt">{esc(short(it.get("title"), 28))}</span>'
                f'<div class="bd">{esc(short(it.get("detail") or it.get("summary"), 100))}</div></div></div>'
            )
        body = f'<div class="bullets">{"".join(rows)}</div>'
    else:
        cards = []
        # Fit up to 3 items; longer copy when fewer cards (fills 3:4 better)
        max_items = 3
        if n <= 1:
            title_len, detail_len, why_len = 36, 140, 36
        elif n == 2:
            title_len, detail_len, why_len = 30, 90, 30
        else:
            title_len, detail_len, why_len = 26, 56, 28
        for i, it in enumerate(items[:max_items]):
            bg, fg = TAG_COLORS.get(it.get("tag", ""), DEFAULT_TAG)
            tag = (
                f'<span class="tag" style="background:{bg};color:{fg}">{esc(it["tag"])}</span>'
                if it.get("tag")
                else ""
            )
            why = ""
            if it.get("why"):
                why = (
                    f'<div class="why" style="background:{hex_to_rgba(accent,.09)};color:#1e293b">'
                    f'💡 {esc(short(it["why"], why_len))}</div>'
                )
            cards.append(
                f'<div class="item"><div class="idx" style="background:{accent}">{i+1}</div>'
                f'<div class="content"><div class="row1"><div class="title">{esc(short(it.get("title"), title_len))}</div>{tag}</div>'
                f'<div class="detail">{esc(short(it.get("detail") or it.get("summary"), detail_len))}</div>'
                f"{why}</div></div>"
            )
        body = "".join(cards)

    css = XHS_CSS % {"w": XHS_W, "h": XHS_H, "font": BASE_FONT}
    return f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><style>{css}</style></head>
<body><div class="page section">
  <div class="sec-head">
    <span class="pg">{page_i}/{total}</span>
    <h2><span class="bar" style="background:{accent}"></span>{esc(strip_emoji_heading(sec.get("heading")))}</h2>
  </div>
  {note}
  <div class="sec-body{sparse}">{body}</div>
  <div class="sec-foot"><span>{esc(d.get("brand", "AI 前沿日报"))}</span>
    <span>{esc(d.get("date", ""))}</span></div>
</div></body></html>"""


# ---------------------------------------------------------------------------
# 微信封面 + 文内长条
# ---------------------------------------------------------------------------
WECHAT_COVER_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { width: %(w)dpx; height: %(h)dpx; overflow: hidden; font-family: %(font)s;
  -webkit-font-smoothing: antialiased; }
.cover { width: %(w)dpx; height: %(h)dpx; color: #fff; padding: 40px 48px;
  display: flex; flex-direction: column; justify-content: space-between;
  background: radial-gradient(circle at 90%% 20%%, rgba(139,92,246,.5), transparent 40%%),
              radial-gradient(circle at 5%% 90%%, rgba(14,165,233,.35), transparent 45%%),
              linear-gradient(120deg, #0b1023, #1e1b4b 60%%, #312e81); }
.top { display: flex; justify-content: space-between; align-items: center; }
.eyebrow { font-size: 18px; letter-spacing: 4px; color: #a5b4fc; font-weight: 700; }
.date { font-size: 22px; font-weight: 800; background: #fff; color: #1e1b4b;
  padding: 6px 18px; border-radius: 999px; }
h1 { font-size: 56px; font-weight: 900; letter-spacing: 2px; margin-top: 8px; }
.highlights { display: flex; gap: 14px; margin-top: 8px; }
.hl { flex: 1; background: rgba(255,255,255,.1); border: 1px solid rgba(255,255,255,.16);
  border-radius: 14px; padding: 14px 16px; }
.hl .t { font-size: 22px; font-weight: 800; margin-bottom: 4px; }
.hl .d { font-size: 18px; color: #c7d2fe; line-height: 1.4; }
"""


def build_wechat_cover(d: dict) -> str:
    hls = []
    for t in (d.get("tldr") or [])[:3]:
        if isinstance(t, dict):
            title, text = t.get("title", ""), t.get("text", "")
        else:
            title, text = str(t)[:12], ""
        hls.append(
            f'<div class="hl"><div class="t">{esc(short(title, 12))}</div>'
            f'<div class="d">{esc(short(text, 42))}</div></div>'
        )
    css = WECHAT_COVER_CSS % {"w": WECHAT_COVER_W, "h": WECHAT_COVER_H, "font": BASE_FONT}
    return f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><style>{css}</style></head>
<body><div class="cover">
  <div>
    <div class="top"><span class="eyebrow">{esc(d.get("eyebrow", "DAILY AI BRIEFING"))}</span>
      <span class="date">{esc(d.get("date", ""))}</span></div>
    <h1>{esc(d.get("title", "AI 前沿日报"))}</h1>
  </div>
  <div class="highlights">{"".join(hls)}</div>
</div></body></html>"""


WECHAT_STRIP_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { background: #eef1f7; font-family: %(font)s; color: #0f172a; -webkit-font-smoothing: antialiased;
  width: %(w)dpx; }
.card { width: %(w)dpx; background: #f6f7fb; }
.header { padding: 40px 36px 36px; color: #fff;
  background: linear-gradient(135deg, #0b1023, #1e1b4b 60%%, #312e81); }
.header .eyebrow { font-size: 16px; letter-spacing: 4px; color: #a5b4fc; font-weight: 700; }
.header h1 { font-size: 40px; font-weight: 900; margin-top: 8px; }
.header .date { display: inline-block; margin-top: 14px; font-size: 18px; font-weight: 800;
  background: #fff; color: #1e1b4b; padding: 5px 14px; border-radius: 999px; }
.tldr { margin: -20px 24px 0; background: #fff; border-radius: 16px; padding: 18px 22px;
  box-shadow: 0 8px 24px rgba(30,27,75,.14); border-top: 5px solid #6366f1; position: relative; }
.tldr .th { font-size: 22px; font-weight: 900; color: #1e1b4b; margin-bottom: 8px; }
.tldr .tl { display: flex; gap: 10px; padding: 8px 0; }
.tldr .tn { flex: none; width: 26px; height: 26px; border-radius: 50%%; background: #eef2ff; color: #4f46e5;
  font-weight: 900; font-size: 14px; display: flex; align-items: center; justify-content: center; margin-top: 2px; }
.tldr .tt { font-size: 18px; line-height: 1.5; color: #334155; }
.tldr .tt b { color: #0f172a; }
.body { padding: 28px 24px 16px; }
.section { margin-bottom: 28px; }
.section h2 { font-size: 26px; font-weight: 900; display: flex; align-items: center; gap: 10px; margin: 0 4px 14px; }
.section h2 .bar { width: 6px; height: 24px; border-radius: 3px; }
.item { background: #fff; border-radius: 14px; padding: 16px 18px; margin-bottom: 10px;
  box-shadow: 0 2px 10px rgba(15,23,42,.05); }
.item .title { font-size: 20px; font-weight: 800; line-height: 1.35; }
.item .detail { font-size: 16px; color: #475569; line-height: 1.55; margin-top: 6px; }
.item .why { font-size: 15px; font-weight: 600; margin-top: 8px; color: #1e293b; }
.bullets .bullet { padding: 10px 0; border-bottom: 1px dashed #e2e8f0; font-size: 16px; color: #475569; line-height: 1.5; }
.bullets .bullet:last-child { border-bottom: none; }
.bullets .bt { font-weight: 800; color: #0f172a; margin-right: 6px; }
.footer { padding: 8px 28px 28px; color: #94a3b8; font-size: 14px; display: flex; justify-content: space-between; }
"""


def build_wechat_strip(d: dict) -> str:
    tldr_rows = []
    for n, t in enumerate(d.get("tldr") or [], 1):
        if isinstance(t, dict):
            body = f'<b>{esc(t.get("title"))}</b>　{esc(short(t.get("text"), 40))}'
        else:
            body = esc(short(str(t), 50))
        tldr_rows.append(
            f'<div class="tl"><span class="tn">{n}</span><div class="tt">{body}</div></div>'
        )
    secs = []
    for si, sec in enumerate(d.get("sections") or []):
        accent = sec.get("accent") or SECTION_ACCENTS[si % len(SECTION_ACCENTS)]
        items = sec.get("items") or []
        if sec.get("style") == "bullets":
            rows = "".join(
                f'<div class="bullet"><span class="bt">{esc(short(it.get("title"), 20))}</span>'
                f'{esc(short(it.get("detail") or it.get("summary"), 60))}</div>'
                for it in items
            )
            inner = f'<div class="bullets" style="background:#fff;border-radius:14px;padding:4px 18px">{rows}</div>'
        else:
            cards = []
            for it in items:
                why = (
                    f'<div class="why">💡 {esc(short(it.get("why"), 30))}</div>'
                    if it.get("why")
                    else ""
                )
                cards.append(
                    f'<div class="item"><div class="title">{esc(short(it.get("title"), 28))}</div>'
                    f'<div class="detail">{esc(short(it.get("detail") or it.get("summary"), 90))}</div>{why}</div>'
                )
            inner = "".join(cards)
        secs.append(
            f'<div class="section"><h2><span class="bar" style="background:{accent}"></span>'
            f'{esc(sec.get("heading"))}</h2>{inner}</div>'
        )
    css = WECHAT_STRIP_CSS % {"w": WECHAT_STRIP_W, "font": BASE_FONT}
    return f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><style>{css}</style></head>
<body><div class="card" id="card">
  <div class="header"><div class="eyebrow">{esc(d.get("eyebrow", "DAILY AI BRIEFING"))}</div>
    <h1>{esc(d.get("title", "AI 前沿日报"))}</h1>
    <span class="date">{esc(d.get("date", ""))}</span></div>
  <div class="tldr"><div class="th">⚡ 今日要点</div>{"".join(tldr_rows)}</div>
  <div class="body">{"".join(secs)}</div>
  <div class="footer"><span>原文链接见消息正文</span><span>{esc(d.get("brand", ""))}</span></div>
</div></body></html>"""


# ---------------------------------------------------------------------------
# X 16:9 cover
# ---------------------------------------------------------------------------
X_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { width: %(w)dpx; height: %(h)dpx; overflow: hidden; font-family: %(font)s;
  -webkit-font-smoothing: antialiased; }
.cover { width: %(w)dpx; height: %(h)dpx; color: #fff; padding: 56px 64px;
  display: flex; flex-direction: column; justify-content: space-between;
  background: radial-gradient(circle at 92%% 15%%, rgba(139,92,246,.55), transparent 42%%),
              radial-gradient(circle at 8%% 85%%, rgba(14,165,233,.4), transparent 48%%),
              linear-gradient(125deg, #0b1023, #1e1b4b 55%%, #312e81); position: relative; }
.grid { position: absolute; right: -30px; top: -30px; width: 280px; height: 280px; opacity: .15;
  background-image: linear-gradient(#fff 1px, transparent 1px), linear-gradient(90deg, #fff 1px, transparent 1px);
  background-size: 28px 28px; transform: rotate(12deg); border-radius: 32px; }
.top .eyebrow { font-size: 20px; letter-spacing: 5px; color: #a5b4fc; font-weight: 700; }
.top h1 { font-size: 64px; font-weight: 900; letter-spacing: 2px; margin-top: 10px; }
.top .date { display: inline-block; margin-top: 18px; font-size: 24px; font-weight: 800;
  background: #fff; color: #1e1b4b; padding: 8px 20px; border-radius: 999px; }
.bottom { display: flex; gap: 16px; }
.hl { flex: 1; background: rgba(255,255,255,.1); border: 1px solid rgba(255,255,255,.18);
  border-radius: 16px; padding: 18px 20px; }
.hl .t { font-size: 24px; font-weight: 800; margin-bottom: 6px; }
.hl .d { font-size: 18px; color: #c7d2fe; line-height: 1.4; }
"""


def build_x_cover(d: dict) -> str:
    hls = []
    for t in (d.get("tldr") or [])[:3]:
        if isinstance(t, dict):
            title, text = t.get("title", ""), t.get("text", "")
        else:
            title, text = str(t)[:14], ""
        hls.append(
            f'<div class="hl"><div class="t">{esc(short(title, 14))}</div>'
            f'<div class="d">{esc(short(text, 36))}</div></div>'
        )
    css = X_CSS % {"w": X_W, "h": X_H, "font": BASE_FONT}
    return f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><style>{css}</style></head>
<body><div class="cover"><div class="grid"></div>
  <div class="top">
    <div class="eyebrow">{esc(d.get("eyebrow", "DAILY AI BRIEFING"))}</div>
    <h1>{esc(d.get("title", "AI 前沿日报"))}</h1>
    <span class="date">{esc(d.get("date", ""))}</span>
  </div>
  <div class="bottom">{"".join(hls)}</div>
</div></body></html>"""


# ---------------------------------------------------------------------------
# Pack orchestration
# ---------------------------------------------------------------------------
def export_pack(
    src: pathlib.Path,
    out_dir: pathlib.Path | None = None,
    *,
    skip_overview: bool = False,
    scale_fixed: float = 2,
) -> pathlib.Path:
    d = json.loads(src.read_text(encoding="utf-8"))
    day = day_slug(d, src)
    out = out_dir or (src.parent / "exports" / day)
    out.mkdir(parents=True, exist_ok=True)

    # Copy source JSON into pack
    json_out = out / f"{day}.json"
    if src.resolve() != json_out.resolve():
        shutil.copy2(src, json_out)

    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = launch_browser(pw)

        # 1) overview — reuse render.py
        overview_path = out / "overview.png"
        if skip_overview and (src.with_suffix(".png")).is_file():
            shutil.copy2(src.with_suffix(".png"), overview_path)
            print(f"overview (copied): {overview_path}", flush=True)
        else:
            page_html = overview_render.build_html(d, 1080)
            screenshot_card(browser, page_html, overview_path, 1080, scale=2)
            print(f"overview: {overview_path}", flush=True)

        # 2) 小红书 pages
        sections = d.get("sections") or []
        total_pages = 1 + len(sections)
        xhs_files = []
        cover_html = build_xhs_cover(d, 1, total_pages)
        p1 = out / "xhs-01.png"
        screenshot_fixed(browser, cover_html, p1, XHS_W, XHS_H, scale=scale_fixed)
        xhs_files.append(p1)
        print(f"xhs-01 (cover): {p1}", flush=True)

        for si, sec in enumerate(sections):
            page_i = si + 2
            name = f"xhs-{page_i:02d}.png"
            path = out / name
            html_page = build_xhs_section(d, si, sec, page_i, total_pages)
            screenshot_fixed(browser, html_page, path, XHS_W, XHS_H, scale=scale_fixed)
            xhs_files.append(path)
            print(f"{name}: {path}", flush=True)

        # 3) WeChat
        wc = out / "wechat-cover.png"
        screenshot_fixed(browser, build_wechat_cover(d), wc, WECHAT_COVER_W, WECHAT_COVER_H, scale=scale_fixed)
        print(f"wechat-cover: {wc}", flush=True)

        ws = out / "wechat-strip.png"
        screenshot_card(browser, build_wechat_strip(d), ws, WECHAT_STRIP_W, scale=2)
        print(f"wechat-strip: {ws}", flush=True)

        # 4) X
        xc = out / "x-cover.png"
        screenshot_fixed(browser, build_x_cover(d), xc, X_W, X_H, scale=scale_fixed)
        print(f"x-cover: {xc}", flush=True)

        browser.close()

    # 5) ZIP
    zpath = out / f"{day}.zip"
    with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for f in [overview_path, *xhs_files, wc, ws, xc, json_out]:
            zf.write(f, arcname=f.name)
    print(f"zip: {zpath}", flush=True)

    # manifest
    manifest = {
        "day": day,
        "sizes": {
            "overview": "1080 CSS wide @2x (variable height)",
            "xhs": f"{XHS_W}x{XHS_H} @2x (3:4)",
            "wechat_cover": f"{WECHAT_COVER_W}x{WECHAT_COVER_H} @2x (~2.35:1)",
            "wechat_strip": f"{WECHAT_STRIP_W} CSS wide @2x (variable height)",
            "x_cover": f"{X_W}x{X_H} @2x (16:9)",
        },
        "files": sorted(p.name for p in out.iterdir() if p.is_file()),
    }
    (out / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help="digest YYYY-MM-DD.json")
    ap.add_argument("-o", "--output", type=pathlib.Path, help="output folder (default: exports/YYYY-MM-DD)")
    ap.add_argument("--skip-overview", action="store_true", help="copy existing YYYY-MM-DD.png as overview")
    ap.add_argument("--scale", type=float, default=2, help="device scale for fixed-size covers (default 2)")
    a = ap.parse_args()
    src = pathlib.Path(a.input)
    if not src.is_file():
        raise SystemExit(f"missing {src}")
    out = export_pack(src, a.output, skip_overview=a.skip_overview, scale_fixed=a.scale)
    print(out)


if __name__ == "__main__":
    main()
