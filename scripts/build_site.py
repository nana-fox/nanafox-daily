#!/usr/bin/env python3
"""Build a zero-build static site from YYYY-MM-DD.{json,png}.

BASE_PATH env or --base-path: e.g. /daily for nanafox.com/daily/
When BASE_PATH is set, HTML uses absolute links under that prefix, and
files are nested under dist{BASE_PATH}/ so a root deploy serves /daily/.
"""

from __future__ import annotations

import argparse
import html
import hashlib
import json
import os
import re
import shutil
import zipfile
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

REPO = Path(__file__).resolve().parents[1]  # repo root
SITE = REPO / "site"
DIST = REPO / "dist"
DEFAULT_DIGEST = REPO / "data"
DEFAULT_GUIDES = REPO / "guides" / "codex"
DATE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})\.json$")
GUIDE_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SITE_ORIGIN = "https://nanafox.com"

SITE_TITLE = "AI 前沿日报"
SITE_TAGLINE = "前沿动态 · 高质量文章 · 一图总览"
ROUTER_REGISTER_URL = "https://router.nanafox.com/register?aff=UG937JQ67MRS&use=codex"
ROUTER_DOCS_URL = "https://router.nanafox.com/docs"


def esc(s: object) -> str:
    return html.escape("" if s is None else str(s), quote=True)


def normalize_base(base: str) -> str:
    base = (base or "").strip()
    if not base or base == "/":
        return ""
    if not base.startswith("/"):
        base = "/" + base
    return base.rstrip("/")


def join_base(base: str, *parts: str) -> str:
    """Join BASE_PATH with path segments → absolute site path."""
    segs = []
    for p in parts:
        segs.extend(str(p).strip("/").split("/"))
    segs = [s for s in segs if s]
    tail = "/".join(segs)
    if not base:
        return "/" + tail if tail else "/"
    return f"{base}/{tail}" if tail else f"{base}/"


def load_digests(digest_dir: Path) -> list[dict]:
    items: list[dict] = []
    for path in sorted(digest_dir.glob("*.json")):
        m = DATE_RE.match(path.name)
        if not m:
            continue
        day = m.group(1)
        date.fromisoformat(day)
        png = digest_dir / f"{day}.png"
        if not png.is_file():
            print(f"skip {path.name}: missing {png.name}")
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        data["_day"] = day
        data["_json_path"] = path
        data["_png_path"] = png
        items.append(data)
    items.sort(key=lambda d: d["_day"], reverse=True)
    return items


def tldr_html(data: dict) -> str:
    tldr = data.get("tldr") or []
    if not tldr:
        return ""
    heading = esc(data.get("tldr_heading") or "⚡ 今日要点")
    lis = []
    for item in tldr:
        if isinstance(item, str):
            lis.append(f"<li>{esc(item)}</li>")
        else:
            title = esc(item.get("title") or "")
            text = esc(item.get("text") or "")
            if title and text:
                lis.append(f"<li><strong>{title}</strong> — {text}</li>")
            else:
                lis.append(f"<li>{title or text}</li>")
    return f'<section class="tldr"><h2>{heading}</h2><ol>{"".join(lis)}</ol></section>'


def safe_url(value: object) -> str:
    if isinstance(value, str):
        parsed = urlparse(value)
        if parsed.scheme in ("http", "https") and parsed.netloc:
            return value
    return ""


def item_li(item: dict) -> str:
    """Readable article summary with original and related sources."""
    title = esc(item.get("title") or "无标题")
    url = safe_url(item.get("url"))
    tag = item.get("tag")
    related = item.get("related") or []
    related_urls = [safe_url(value) for value in (item.get("related_urls") or [])]

    if url:
        title_html = f'<a class="link-title" href="{esc(url)}" target="_blank" rel="noopener">{title}</a>'
    else:
        title_html = f'<span class="link-title">{title}</span>'
    tag_html = f'<span class="tag">{esc(tag)}</span>' if tag else ""
    detail = item.get("detail") or item.get("summary")
    detail_html = f'<p class="item-detail">{esc(detail)}</p>' if detail else ""
    why_html = f'<p class="item-why"><strong>关注点：</strong>{esc(item["why"])}</p>' if item.get("why") else ""
    source_html = f'<p class="item-source">来源：{esc(item["source"])}</p>' if item.get("source") else ""

    links = []
    for i, label in enumerate(related):
        href = related_urls[i] if i < len(related_urls) else ""
        if href:
            links.append(f'<a href="{esc(href)}" target="_blank" rel="noopener">{esc(label)}</a>')
        elif label:
            links.append(f"<span>{esc(label)}</span>")
    for href in related_urls[len(related) :]:
        if href:
            links.append(f'<a href="{esc(href)}" target="_blank" rel="noopener">另见</a>')
    related_html = (
        f'<div class="related">{"".join(links)}</div>' if links else ""
    )

    return (
        f'<li><div class="link-row">{title_html}{tag_html}</div>'
        f'<div class="item-body">{detail_html}{why_html}{source_html}{related_html}</div></li>'
    )


def sections_html(data: dict) -> str:
    sections = data.get("sections") or []
    chunks = []
    for index, sec in enumerate(sections, 1):
        heading = esc(sec.get("heading") or "条目")
        note = sec.get("note") or ""
        items = sec.get("items") or []
        body = (
            f'<ul class="link-list">{"".join(item_li(it) for it in items)}</ul>'
            if items
            else '<p class="empty">暂无条目</p>'
        )
        note_html = f'<p class="note">{esc(note)}</p>' if note else ""
        chunks.append(
            f'<section class="section" id="section-{index}"><h2>{heading}</h2>{note_html}{body}</section>'
        )
    return "\n".join(chunks)


def layout(
    *,
    title: str,
    active: str,
    body: str,
    base: str,
    canonical_path: str | None = None,
    description: str | None = None,
    keywords: list[str] | None = None,
    og_type: str = "website",
    reader: dict | None = None,
    reader_assets: dict | None = None,
) -> str:
    latest_href = f"{base}/" if base else "/"
    archive_href = join_base(base, "archive") + "/"
    guides_href = join_base(base, "guides", "codex") + "/"
    css_href = join_base(base, "css", "style.css")
    meta_desc = description or SITE_TAGLINE
    keywords_html = (
        f'  <meta name="keywords" content="{esc(", ".join(keywords))}" />\n'
        if keywords
        else ""
    )

    nav = [
        ("home", "https://nanafox.com/", "返回官网"),
        ("latest", latest_href, "最新"),
        ("archive", archive_href, "归档"),
        ("guides", guides_href, "Codex 排错"),
    ]
    nav_html = "".join(
        f'<a class="{"active" if key == active else ""}" href="{href}">{label}</a>'
        for key, href, label in nav
    )
    canonical_url = f"{SITE_ORIGIN}{canonical_path}" if canonical_path else ""
    canonical_html = (
        f'  <link rel="canonical" href="{esc(canonical_url)}" />\n'
        f'  <meta property="og:url" content="{esc(canonical_url)}" />\n'
        if canonical_url else ""
    )
    page = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(meta_desc)}" />
{keywords_html}  <meta name="theme-color" content="#fffdf9" />
  <meta property="og:title" content="{esc(title)} · NanaFox" />
  <meta property="og:description" content="{esc(meta_desc)}" />
  <meta property="og:type" content="{esc(og_type)}" />
  <meta name="twitter:card" content="summary" />
{canonical_html}  <link rel="stylesheet" href="{esc(css_href)}" />
</head>
<body>
  <header class="topbar">
    <div class="wrap topbar-inner">
      <a class="brand" href="https://nanafox.com/">NanaFox<span class="brand-divider"> / </span><span class="brand-section">AI 日报</span>
      </a>
      <nav class="nav" aria-label="日报导航">{nav_html}</nav>
    </div>
  </header>
  <main class="wrap">
{body}
  </main>
  <footer class="footer">
    <div class="wrap">
      <span>NanaFox · 每日 AI 精选 · 图片可下载分享</span>
      <div class="footer-links">
        <a href="{esc(guides_href)}">Codex 排错指南</a>
        <a href="{esc(archive_href)}">全部归档</a>
      </div>
    </div>
  </footer>
</body>
</html>
"""

    if reader is not None and reader_assets:
        # JSON remains original data. Escape HTML script delimiters without changing it.
        payload = json.dumps(reader, ensure_ascii=False).replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
        css = "".join(f'<link rel="stylesheet" href="{esc(join_base(base, "reader", path))}" />' for path in reader_assets.get("css", []))
        script = esc(join_base(base, "reader", reader_assets["file"]))
        page = page.replace("</head>", css + "\n</head>")
        page = page.replace("<body>", '<body><div id="daily-reader">')
        page = page.replace("</body>", f'</div><script id="daily-data" type="application/json">{payload}</script><script type="module" src="{script}"></script></body>')
    return page


def load_reader_assets() -> dict:
    bundle = SITE / "reader"
    meta = json.loads((bundle / "build-meta.json").read_text(encoding="utf-8"))
    for name, expected in meta["sources"].items():
        actual = hashlib.sha256((REPO / name).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError("Reader source changed: run npm --prefix web run build before building the site")
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    entry = manifest["src/main.jsx"]
    for name in [entry["file"], *entry.get("css", [])]:
        if not (bundle / name).is_file():
            raise ValueError(f"Missing reader asset: {name}; rebuild web")
    return entry



def day_nav_html(
    data: dict,
    *,
    base: str,
    prev_day: str | None,
    next_day: str | None,
) -> str:
    parts = []
    if prev_day:
        href = join_base(base, prev_day) + "/"
        parts.append(f'<a href="{esc(href)}">← {esc(prev_day)}</a>')
    else:
        parts.append('<span class="spacer"></span>')
    parts.append('<span class="spacer"></span>')
    if next_day:
        href = join_base(base, next_day) + "/"
        parts.append(f'<a href="{esc(href)}">{esc(next_day)} →</a>')
    else:
        parts.append('<span class="spacer"></span>')
    return f'<nav class="day-nav" aria-label="相邻日期">{"".join(parts)}</nav>'


def day_body(
    data: dict,
    *,
    base: str,
    is_latest: bool,
    prev_day: str | None = None,
    next_day: str | None = None,
    show_day_nav: bool = True,
) -> str:
    day = data["_day"]
    display_date = esc(data.get("date") or day)
    page_title = esc(data.get("title") or SITE_TITLE)
    img_src = join_base(base, "assets", f"{day}.png")
    json_href = join_base(base, "assets", f"{day}.json")
    zip_href = join_base(base, "export", f"{day}.zip")
    badge = '<span class="pill">最新一期</span>' if is_latest else ""

    actions = [
        f'<a class="btn primary" href="{esc(img_src)}" download="{day}.png">下载原图</a>',
        f'<a class="btn" href="{esc(img_src)}" target="_blank" rel="noopener">查看大图</a>',
    ]
    download_menu = (
        '<details class="download-menu"><summary>更多下载</summary><div>'
        f'<a href="{esc(json_href)}" download="{day}.json">结构化数据 JSON</a>'
        f'<a href="{esc(zip_href)}" download="{day}.zip">图片与数据 ZIP</a>'
        '</div></details>'
    )
    toc = ''.join(
        f'<a href="#section-{index}">{esc(section.get("heading") or "条目")}</a>'
        for index, section in enumerate(data.get("sections") or [], 1)
    )

    nav = (
        day_nav_html(data, base=base, prev_day=prev_day, next_day=next_day)
        if show_day_nav and (prev_day or next_day)
        else ""
    )

    return f"""
    <div class="page-head">
      <p class="eyebrow">NanaFox · Daily AI Briefing{badge}</p>
      <h1>{page_title}</h1>
      <p class="date-line">{display_date}</p>
    </div>
    {tldr_html(data)}
    <nav class="section-nav" aria-label="日报分类">{toc}</nav>
    {sections_html(data)}
    <section class="poster-section" aria-labelledby="poster-heading">
      <div class="poster-heading"><div><h2 id="poster-heading">一图总览</h2><p>保存长图，随时回看或分享。</p></div></div>
      <div class="hero-actions">{"".join(actions)}{download_menu}</div>
      <details class="poster-preview">
        <summary>展开长图预览</summary>
        <a href="{esc(img_src)}" target="_blank" rel="noopener">
          <img src="{esc(img_src)}" alt="{page_title} {display_date} 一图总览" loading="lazy" />
        </a>
      </details>
    </section>
    <aside class="router-note" aria-label="NanaFox Router">
      <span>在用 Codex / Claude Code？NanaFox Router 支持一键导入 CC Switch</span>
      <div class="router-note-links">
        <a class="router-note-secondary" href="{esc(join_base(base, 'guides', 'codex') + '/')}">Codex 排错指南</a>
        <a href="{esc(ROUTER_REGISTER_URL)}" target="_blank" rel="noopener noreferrer">立即接入 →</a>
      </div>
    </aside>
    {nav}
"""


def archive_body(digests: list[dict], *, base: str) -> str:
    if not digests:
        return '<div class="empty">还没有归档。先生成日报 JSON/PNG，再运行 build_site.py。</div>'
    lis = []
    for d in digests:
        day = d["_day"]
        date_label = esc(d.get("date") or day)
        summary = ""
        tldr = d.get("tldr") or []
        if tldr:
            first = tldr[0]
            if isinstance(first, dict):
                title = first.get("title") or ""
                text = first.get("text") or ""
                summary = f"{title}：{text}" if title else text
            else:
                summary = str(first)
        day_href = join_base(base, day) + "/"
        lis.append(
            f'<li><a href="{esc(day_href)}">'
            f'<span class="d">{esc(day)}</span>'
            f'<div class="meta"><p class="title">{date_label}</p>'
            f'<p class="s">{esc(summary)}</p></div></a></li>'
        )
    return f"""
    <div class="page-head">
      <p class="eyebrow">Archive</p>
      <h1>归档</h1>
      <p class="date-line">共 {len(digests)} 期 · 按日期倒序</p>
    </div>
    <ul class="archive-list">{"".join(lis)}</ul>
"""


def _unquote_yaml(raw: str) -> str:
    raw = raw.strip()
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in ('"', "'"):
        return raw[1:-1]
    return raw


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Parse lightweight YAML frontmatter (scalars and flat string lists)."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    end_idx = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            end_idx = idx
            break
    if end_idx is None:
        return {}, text

    meta: dict[str, object] = {}
    current_list_key: str | None = None
    for line in lines[1:end_idx]:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- ") and current_list_key is not None:
            meta[current_list_key].append(_unquote_yaml(stripped[2:]))
            continue
        current_list_key = None
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not value:
            meta[key] = []
            current_list_key = key
        elif value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            if not inner:
                meta[key] = []
            else:
                meta[key] = [_unquote_yaml(part) for part in inner.split(",") if part.strip()]
        else:
            meta[key] = _unquote_yaml(value)

    body = "\n".join(lines[end_idx + 1 :]).lstrip("\n")
    return meta, body


def _safe_guide_href(url: str) -> str:
    url = url.strip()
    if url.startswith("/") and not url.startswith("//"):
        return url
    return safe_url(url)


INLINE_CODE_RE = re.compile(r"`([^`\n]+)`")
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")


def render_inline_md(text: str) -> str:
    """Render inline Markdown (`code`, **bold**, [text](url)) with HTML escaping."""
    placeholders: list[str] = []

    def stash(html_fragment: str) -> str:
        token = f"\x00MD{len(placeholders)}\x00"
        placeholders.append(html_fragment)
        return token

    def replace_code(match: re.Match[str]) -> str:
        return stash(f"<code>{esc(match.group(1))}</code>")

    def replace_link(match: re.Match[str]) -> str:
        label = esc(match.group(1))
        href = _safe_guide_href(match.group(2))
        if not href:
            return stash(label)
        if href.startswith(("http://", "https://")):
            return stash(
                f'<a href="{esc(href)}" target="_blank" rel="noopener noreferrer">{label}</a>'
            )
        return stash(f'<a href="{esc(href)}">{label}</a>')

    # Protect inline code first so links/bold inside code spans stay literal.
    out = INLINE_CODE_RE.sub(replace_code, text)
    out = LINK_RE.sub(replace_link, out)
    out = esc(out)
    out = BOLD_RE.sub(r"<strong>\1</strong>", out)
    for idx, fragment in enumerate(placeholders):
        out = out.replace(f"\x00MD{idx}\x00", fragment)
    return out


HEADING_RE = re.compile(r"^(#{1,4})\s+(.+)$")
UL_RE = re.compile(r"^(\s*)-\s+(.+)$")
OL_RE = re.compile(r"^(\s*)\d+\.\s+(.+)$")


def render_markdown(md: str, *, strip_first_h1: bool = True) -> str:
    """Render lightweight Markdown to safe semantic HTML using stdlib only."""
    lines = md.splitlines()
    blocks: list[str] = []
    i = 0
    skipped_h1 = False

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        # Fenced code block
        if stripped.startswith("```"):
            lang = stripped[3:].strip()
            code_lines: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            if i < len(lines):
                i += 1
            lang_attr = f' class="lang-{esc(lang)}"' if lang else ""
            blocks.append(f"<pre><code{lang_attr}>{esc(chr(10).join(code_lines))}</code></pre>")
            continue

        # Horizontal rule
        if stripped in ("---", "***", "___"):
            blocks.append("<hr />")
            i += 1
            continue

        # Headings
        hm = HEADING_RE.match(stripped)
        if hm:
            level = len(hm.group(1))
            content = hm.group(2).strip()
            i += 1
            if level == 1 and strip_first_h1 and not skipped_h1:
                skipped_h1 = True
                continue
            blocks.append(f"<h{level}>{render_inline_md(content)}</h{level}>")
            continue

        # Unordered / Ordered lists (with 1-level nested list support)
        um = UL_RE.match(line)
        om = OL_RE.match(line)
        if um or om:
            list_tag = "ul" if um else "ol"
            base_indent = len((um or om).group(1))
            items: list[str] = []
            while i < len(lines):
                cur = lines[i]
                if not cur.strip():
                    break
                cur_ul = UL_RE.match(cur)
                cur_ol = OL_RE.match(cur)
                m_same = cur_ul if list_tag == "ul" else cur_ol
                if m_same and len(m_same.group(1)) == base_indent:
                    item_html = render_inline_md(m_same.group(2).strip())
                    i += 1
                    # Collect nested sub-list items if indented deeper
                    sub_items: list[str] = []
                    sub_tag: str | None = None
                    while i < len(lines):
                        sub_line = lines[i]
                        sub_ul = UL_RE.match(sub_line)
                        sub_ol = OL_RE.match(sub_line)
                        sub_m = sub_ul or sub_ol
                        if sub_m and len(sub_m.group(1)) > base_indent:
                            if sub_tag is None:
                                sub_tag = "ul" if sub_ul else "ol"
                            sub_items.append(f"<li>{render_inline_md(sub_m.group(2).strip())}</li>")
                            i += 1
                        else:
                            break
                    if sub_items and sub_tag:
                        item_html += f"<{sub_tag}>{''.join(sub_items)}</{sub_tag}>"
                    items.append(f"<li>{item_html}</li>")
                else:
                    break
            blocks.append(f"<{list_tag}>{''.join(items)}</{list_tag}>")
            continue

        # Paragraph
        para_lines: list[str] = [stripped]
        i += 1
        while i < len(lines):
            nxt = lines[i]
            nxt_s = nxt.strip()
            if (
                not nxt_s
                or nxt_s.startswith("```")
                or nxt_s in ("---", "***", "___")
                or HEADING_RE.match(nxt_s)
                or UL_RE.match(nxt)
                or OL_RE.match(nxt)
            ):
                break
            para_lines.append(nxt_s)
            i += 1
        blocks.append(f"<p>{render_inline_md(' '.join(para_lines))}</p>")

    return "\n".join(blocks)


def validate_guide_slug(slug: str, source_path: Path | None = None) -> str:
    slug = (slug or "").strip()
    if not GUIDE_SLUG_RE.fullmatch(slug):
        where = f" in {source_path}" if source_path else ""
        raise ValueError(
            f"Invalid guide slug {slug!r}{where}: must match {GUIDE_SLUG_RE.pattern}"
        )
    return slug


def load_guides(guides_dir: Path | None) -> list[dict]:
    if not guides_dir or not guides_dir.is_dir():
        return []
    guides: list[dict] = []
    seen_slugs: set[str] = set()
    for path in sorted(guides_dir.glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        meta, body_md = parse_frontmatter(raw)
        raw_slug = meta["slug"] if "slug" in meta else path.stem
        slug = validate_guide_slug(str(raw_slug), path)
        if slug in seen_slugs:
            raise ValueError(f"Duplicate guide slug {slug!r} in {path}")
        seen_slugs.add(slug)
        guides.append(
            {
                "slug": slug,
                "title": str(meta.get("title") or slug),
                "description": str(meta.get("description") or ""),
                "keywords": [str(k) for k in (meta.get("keywords") or [])],
                "error_codes": [str(c) for c in (meta.get("error_codes") or [])],
                "date": str(meta.get("date") or ""),
                "category": str(meta.get("category") or "codex-troubleshooting"),
                "body_md": body_md,
                "source_path": path,
            }
        )
    return guides


def guides_index_body(guides: list[dict], *, base: str) -> str:
    cards: list[str] = []
    for guide in guides:
        href = join_base(base, "guides", "codex", guide["slug"]) + "/"
        badges = "".join(
            f'<span class="guide-badge">{esc(code)}</span>'
            for code in guide["error_codes"]
        )
        cards.append(
            f'<li class="guide-card"><a href="{esc(href)}">'
            f'<div class="guide-card-head"><div class="guide-badges">{badges}</div>'
            f'<span class="guide-date">{esc(guide["date"])}</span></div>'
            f'<h2>{esc(guide["title"])}</h2>'
            f'<p>{esc(guide["description"])}</p>'
            f'<span class="guide-more">查看排查步骤 →</span>'
            f"</a></li>"
        )
    return f"""
    <nav class="breadcrumb" aria-label="面包屑导航">
      <a href="{esc(f'{base}/' if base else '/')}">AI 日报</a>
      <span>/</span>
      <span>Codex 排错指南</span>
    </nav>
    <div class="page-head">
      <p class="eyebrow">Codex Troubleshooting Guides</p>
      <h1>Codex 常见报错排错指南</h1>
      <p class="date-line">覆盖 Codex CLI 与 Codex Desktop 高频 400 / 401 / 403 / 404 / 408 / 429 / 502 / 503 报错 · 全服务商通用排查步骤</p>
    </div>
    <ul class="guide-list">{"".join(cards)}</ul>
    <aside class="router-note" aria-label="NanaFox Router">
      <span>需要支持 Codex 原生 Responses 接口的路由服务？NanaFox Router 支持按用途建 Key，并可一键导入 CC Switch</span>
      <div class="router-note-links">
        <a class="router-note-secondary" href="{esc(ROUTER_DOCS_URL)}" target="_blank" rel="noopener noreferrer">接入文档</a>
        <a href="{esc(ROUTER_REGISTER_URL)}" target="_blank" rel="noopener noreferrer">立即接入 →</a>
      </div>
    </aside>
"""


def guide_detail_body(guide: dict, all_guides: list[dict], *, base: str) -> str:
    index_href = join_base(base, "guides", "codex") + "/"
    badges = "".join(
        f'<span class="guide-badge">{esc(code)}</span>'
        for code in guide["error_codes"]
    )
    article_html = render_markdown(guide["body_md"], strip_first_h1=True)
    others = [g for g in all_guides if g["slug"] != guide["slug"]]
    related_lis = "".join(
        f'<li><a href="{esc(join_base(base, "guides", "codex", g["slug"]) + "/")}">{esc(g["title"])}</a></li>'
        for g in others
    )
    related_html = (
        f'<section class="guide-related" aria-labelledby="related-guides-heading">'
        f'<h2 id="related-guides-heading">其他 Codex 排错指南</h2>'
        f"<ul>{related_lis}</ul>"
        f"</section>"
        if related_lis
        else ""
    )
    return f"""
    <nav class="breadcrumb" aria-label="面包屑导航">
      <a href="{esc(f'{base}/' if base else '/')}">AI 日报</a>
      <span>/</span>
      <a href="{esc(index_href)}">Codex 排错指南</a>
    </nav>
    <article class="guide-page">
      <header class="page-head">
        <div class="guide-meta">
          <div class="guide-badges">{badges}</div>
          <span class="date-line">更新于 {esc(guide["date"])}</span>
        </div>
        <h1>{esc(guide["title"])}</h1>
        <p class="guide-summary">{esc(guide["description"])}</p>
      </header>
      <div class="guide-article">
{article_html}
      </div>
    </article>
    {related_html}
    <nav class="day-nav" aria-label="指南导航">
      <a href="{esc(index_href)}">← 返回 Codex 排错指南合集</a>
      <span class="spacer"></span>
      <a href="{esc(f'{base}/' if base else '/')}">查看最新 AI 日报 →</a>
    </nav>
"""


def build_sitemap_xml(urls: list[tuple[str, str | None]]) -> str:
    entries: list[str] = []
    for loc, lastmod in urls:
        lastmod_tag = f"<lastmod>{esc(lastmod)}</lastmod>" if lastmod else ""
        entries.append(f"  <url><loc>{esc(loc)}</loc>{lastmod_tag}</url>")
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(entries)
        + "\n</urlset>\n"
    )


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build(
    digest_dir: Path,
    dist: Path,
    *,
    base: str = "",
    copy_json: bool = True,
    guides_dir: Path | None = DEFAULT_GUIDES,
) -> list[str]:
    base = normalize_base(base)
    digests = load_digests(digest_dir)
    # Validate bundled UI before replacing output; daily publishing needs Python only.
    reader_assets = load_reader_assets()
    history = []
    for data in digests:
        first = (data.get("tldr") or [""])[0]
        summary = str(first.get("title") or first.get("text") or "") if isinstance(first, dict) else str(first)
        history.append({"day": data["_day"], "title": data.get("title") or SITE_TITLE,
                        "url": join_base(base, data["_day"]) + "/", "summary": summary,
                        "count": sum(len(section.get("items") or []) for section in (data.get("sections") or []))})
    def bootstrap(data=None, view="reader"):
        raw = json.loads(data["_json_path"].read_text(encoding="utf-8")) if data else None
        return {"base": base, "view": view, "day": data["_day"] if data else None, "data": raw, "issues": history}

    if dist.exists():
        shutil.rmtree(dist)
    dist.mkdir(parents=True)

    site_root = dist / base.lstrip("/") if base else dist
    site_root.mkdir(parents=True, exist_ok=True)

    shutil.copytree(SITE / "reader", site_root / "reader")
    write(site_root / "issues.json", json.dumps({"issues": history}, ensure_ascii=False, indent=2) + "\n")

    css_src = SITE / "css" / "style.css"
    css_dst = site_root / "css" / "style.css"
    css_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(css_src, css_dst)

    assets = site_root / "assets"
    assets.mkdir()
    export_dir = site_root / "export"
    export_dir.mkdir()

    # Chronological neighbors: digests are newest-first
    day_index = {d["_day"]: i for i, d in enumerate(digests)}

    built: list[str] = []

    for i, data in enumerate(digests):
        day = data["_day"]
        shutil.copy2(data["_png_path"], assets / f"{day}.png")
        if copy_json:
            shutil.copy2(data["_json_path"], assets / f"{day}.json")

        zpath = export_dir / f"{day}.zip"
        with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            # Worktree checkout times must not change otherwise identical packs.
            issue_date = date.fromisoformat(day)
            for suffix, source in [("png", data["_png_path"]), ("json", data["_json_path"])]:
                info = zipfile.ZipInfo(f"{day}.{suffix}", (issue_date.year, issue_date.month, issue_date.day, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                zf.writestr(info, source.read_bytes())

        # prev = older (next in newest-first list), next = newer (previous index)
        older = digests[i + 1]["_day"] if i + 1 < len(digests) else None
        newer = digests[i - 1]["_day"] if i > 0 else None

        is_latest = i == 0
        body = day_body(
            data,
            base=base,
            is_latest=is_latest,
            prev_day=older,
            next_day=newer,
            show_day_nav=True,
        )
        page = layout(
            title=f'{data.get("title") or SITE_TITLE} · {day}',
            active="latest" if is_latest else "",
            body=body,
            base=base,
            canonical_path=join_base(base, day) + "/",
            reader=bootstrap(data), reader_assets=reader_assets,
        )
        write(site_root / day / "index.html", page)
        built.append(day)

        if is_latest:
            # Homepage: same content as latest day page (no day-nav clutter optional)
            home_body = day_body(
                data,
                base=base,
                is_latest=True,
                prev_day=older,
                next_day=None,
                show_day_nav=bool(older),
            )
            home = layout(
                title=f'{data.get("title") or SITE_TITLE} · 最新',
                active="latest",
                body=home_body,
                base=base,
                canonical_path=join_base(base),
                reader=bootstrap(data), reader_assets=reader_assets,
            )
            write(site_root / "index.html", home)
            summaries = [
                {"title": str(item.get("title") or ""), "text": str(item.get("text") or "")}
                if isinstance(item, dict) else {"title": str(item), "text": ""}
                for item in (data.get("tldr") or [])[:3]
            ]
            write(site_root / "latest.json", json.dumps({
                "date": day,
                "title": data.get("title") or SITE_TITLE,
                "url": join_base(base, day) + "/",
                "tldr": summaries,
            }, ensure_ascii=False, indent=2) + "\n")

    if not digests:
        write(site_root / "latest.json", json.dumps({"date": None, "tldr": []}) + "\n")
        empty = layout(
            title=f"{SITE_TITLE} · 暂无内容",
            active="latest",
            body='<div class="empty">还没有日报。生成 YYYY-MM-DD.json 与 .png 后再构建。</div>',
            base=base, reader=bootstrap(), reader_assets=reader_assets,
        )
        write(site_root / "index.html", empty)

    arch = layout(
        title=f"{SITE_TITLE} · 归档",
        active="archive",
        body=archive_body(digests, base=base),
        base=base,
        canonical_path=join_base(base, "archive") + "/",
        reader=bootstrap(view="archive"), reader_assets=reader_assets,
    )
    write(site_root / "archive" / "index.html", arch)

    guides = load_guides(guides_dir)
    if guides:
        guides_out_root = (site_root / "guides" / "codex").resolve()
        guides_index_path = join_base(base, "guides", "codex") + "/"
        guides_index_html = layout(
            title=f"Codex 常见报错排错指南 · {SITE_TITLE}",
            active="guides",
            body=guides_index_body(guides, base=base),
            base=base,
            canonical_path=guides_index_path,
            description="Codex CLI 与 Codex Desktop 高频报错排错指南合集，覆盖 400 / 401 / 403 / 404 / 408 / 429 / 502 / 503 根因定位与通用修复步骤。",
            keywords=["Codex 报错", "Codex CLI 排错", "Codex Desktop 排错", "Codex config.toml", "Codex auth.json"],
        )
        write(guides_out_root / "index.html", guides_index_html)
        for guide in guides:
            slug = validate_guide_slug(guide["slug"], guide.get("source_path"))
            guide_out_path = (guides_out_root / slug / "index.html").resolve()
            if not guide_out_path.is_relative_to(guides_out_root):
                raise ValueError(f"Guide output path escapes guides root: {guide_out_path}")
            guide_path = join_base(base, "guides", "codex", slug) + "/"
            guide_html = layout(
                title=f'{guide["title"]} · NanaFox',
                active="guides",
                body=guide_detail_body(guide, guides, base=base),
                base=base,
                canonical_path=guide_path,
                description=guide["description"],
                keywords=guide["keywords"],
                og_type="article",
            )
            write(guide_out_path, guide_html)

    sitemap_urls: list[tuple[str, str | None]] = [
        (f"{SITE_ORIGIN}{join_base(base)}", digests[0]["_day"] if digests else None),
        (f"{SITE_ORIGIN}{join_base(base, 'archive') + '/'}", digests[0]["_day"] if digests else None),
    ]
    if guides:
        latest_guide_date = max((g["date"] for g in guides if g["date"]), default=None)
        sitemap_urls.append(
            (f"{SITE_ORIGIN}{join_base(base, 'guides', 'codex') + '/'}", latest_guide_date)
        )
        for guide in guides:
            sitemap_urls.append(
                (
                    f"{SITE_ORIGIN}{join_base(base, 'guides', 'codex', guide['slug']) + '/'}",
                    guide["date"] or None,
                )
            )
    for data in digests:
        sitemap_urls.append((f"{SITE_ORIGIN}{join_base(base, data['_day']) + '/'}", data["_day"]))
    write(site_root / "sitemap.xml", build_sitemap_xml(sitemap_urls))

    home_link = f"{base}/" if base else "/"
    archive_link = join_base(base, "archive") + "/"
    write(
        site_root / "404.html",
        layout(
            title="未找到页面",
            active="",
            body=(
                f'<div class="empty">页面不存在。'
                f'<a href="{esc(home_link)}">回首页</a> · '
                f'<a href="{esc(archive_link)}">归档</a></div>'
            ),
            base=base,
        ),
    )

    (site_root / "_headers").write_text(
        "/*\n  X-Content-Type-Options: nosniff\n"
        "/assets/*\n  Cache-Control: public, max-age=0, must-revalidate\n"
        + (f"{base}/assets/*\n  Cache-Control: public, max-age=0, must-revalidate\n" if base else "")
        + f"{join_base(base, 'reader', 'assets')}/*\n  Cache-Control: public, max-age=31536000, immutable\n"
        + f"{join_base(base, 'latest.json')}\n  Cache-Control: public, max-age=60, must-revalidate\n"
        + f"{join_base(base, 'issues.json')}\n  Cache-Control: public, max-age=0, must-revalidate\n",
        encoding="utf-8",
    )

    if base:
        write(
            dist / "index.html",
            f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta http-equiv="refresh" content="0; url={esc(home_link)}" />
  <link rel="canonical" href="{esc(home_link)}" />
  <title>跳转到 AI 前沿日报</title>
</head>
<body>
  <p><a href="{esc(home_link)}">进入 AI 前沿日报</a></p>
</body>
</html>
""",
        )
        shutil.copy2(site_root / "_headers", dist / "_headers")
        write(
            dist / "404.html",
            layout(
                title="未找到页面",
                active="",
                body=(
                    f'<div class="empty">页面不存在。'
                    f'<a href="{esc(home_link)}">回首页</a> · '
                    f'<a href="{esc(archive_link)}">归档</a></div>'
                ),
                base=base,
            ),
        )

    return built


def main() -> None:
    ap = argparse.ArgumentParser(description="Build AI digest static site for Cloudflare Pages")
    ap.add_argument(
        "--digest-dir",
        type=Path,
        default=DEFAULT_DIGEST,
        help="Directory containing YYYY-MM-DD.json and .png (default: data/)",
    )
    ap.add_argument(
        "--dist",
        type=Path,
        default=DIST,
        help="Output directory (default: dist/)",
    )
    ap.add_argument(
        "--base-path",
        default=os.environ.get("BASE_PATH", "/daily"),
        help="URL base path, e.g. /daily (env BASE_PATH; default /daily)",
    )
    ap.add_argument(
        "--guides-dir",
        type=Path,
        default=DEFAULT_GUIDES,
        help="Directory containing Codex troubleshooting Markdown guides (default: guides/codex/)",
    )
    ap.add_argument("--no-json", action="store_true", help="Do not copy JSON into assets/")
    args = ap.parse_args()

    built = build(
        args.digest_dir,
        args.dist,
        base=args.base_path,
        copy_json=not args.no_json,
        guides_dir=args.guides_dir,
    )
    guides_count = len(load_guides(args.guides_dir))
    print(f"Built {len(built)} digests + {guides_count} Codex guides → {args.dist} (BASE_PATH={normalize_base(args.base_path)!r})")
    for day in built:
        print(f"  - {day}/")
    print("Next: commit data/ and dist/ to main for the connected Pages deployment.")


if __name__ == "__main__":
    main()
