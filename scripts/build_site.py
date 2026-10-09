#!/usr/bin/env python3
"""Build a zero-build static site from YYYY-MM-DD.{json,png}.

BASE_PATH env or --base-path: e.g. /daily for nanafox.com/daily/
When BASE_PATH is set, HTML uses absolute links under that prefix, and
files are nested under dist{BASE_PATH}/ so a root deploy serves /daily/.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]  # repo root
SITE = REPO / "site"
DIST = REPO / "dist"
DEFAULT_DIGEST = REPO / "data"
DATE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})\.json$")

SITE_TITLE = "AI 前沿日报"
SITE_TAGLINE = "前沿动态 · 高质量文章 · 一图总览"


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


def item_li(item: dict) -> str:
    """Readable article summary with original and related sources."""
    title = esc(item.get("title") or "无标题")
    url = item.get("url") or ""
    tag = item.get("tag")
    related = item.get("related") or []
    related_urls = item.get("related_urls") or []

    if url:
        title_html = f'<a class="link-title" href="{esc(url)}" target="_blank" rel="noopener">{title}</a>'
    else:
        title_html = f'<span class="link-title">{title}</span>'
    tag_html = f'<span class="tag">{esc(tag)}</span>' if tag else ""
    detail_html = f'<p class="item-detail">{esc(item["detail"])}</p>' if item.get("detail") else ""
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


def layout(*, title: str, active: str, body: str, base: str, canonical_path: str | None = None) -> str:
    latest_href = f"{base}/" if base else "/"
    archive_href = join_base(base, "archive") + "/"
    css_href = join_base(base, "css", "style.css")

    nav = [
        ("home", "https://nanafox.com/", "返回官网"),
        ("latest", latest_href, "最新"),
        ("archive", archive_href, "归档"),
    ]
    nav_html = "".join(
        f'<a class="{"active" if key == active else ""}" href="{href}">{label}</a>'
        for key, href, label in nav
    )
    canonical_url = f"https://nanafox.com{canonical_path}" if canonical_path else ""
    canonical_html = (
        f'<link rel="canonical" href="{esc(canonical_url)}" />'
        f'<meta property="og:url" content="{esc(canonical_url)}" />'
        if canonical_url else ""
    )
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(SITE_TAGLINE)}" />
  <meta name="theme-color" content="#fffdf9" />
  <meta property="og:title" content="{esc(title)} · NanaFox" />
  <meta property="og:description" content="{esc(SITE_TAGLINE)}" />
  <meta property="og:type" content="website" />
  <meta name="twitter:card" content="summary" />
{canonical_html}
  <link rel="stylesheet" href="{esc(css_href)}" />
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
      <a href="{esc(archive_href)}">全部归档</a>
    </div>
  </footer>
</body>
</html>
"""


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


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build(
    digest_dir: Path,
    dist: Path,
    *,
    base: str = "",
    copy_json: bool = True,
) -> list[str]:
    base = normalize_base(base)
    digests = load_digests(digest_dir)

    if dist.exists():
        shutil.rmtree(dist)
    dist.mkdir(parents=True)

    site_root = dist / base.lstrip("/") if base else dist
    site_root.mkdir(parents=True, exist_ok=True)

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
            zf.write(data["_png_path"], arcname=f"{day}.png")
            zf.write(data["_json_path"], arcname=f"{day}.json")

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
            base=base,
        )
        write(site_root / "index.html", empty)

    arch = layout(
        title=f"{SITE_TITLE} · 归档",
        active="archive",
        body=archive_body(digests, base=base),
        base=base,
        canonical_path=join_base(base, "archive") + "/",
    )
    write(site_root / "archive" / "index.html", arch)

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
        "/assets/*\n  Cache-Control: public, max-age=86400\n"
        + (f"{base}/assets/*\n  Cache-Control: public, max-age=86400\n" if base else "")
        + f"{join_base(base, 'latest.json')}\n  Cache-Control: public, max-age=60, must-revalidate\n",
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
    ap.add_argument("--no-json", action="store_true", help="Do not copy JSON into assets/")
    args = ap.parse_args()

    built = build(
        args.digest_dir,
        args.dist,
        base=args.base_path,
        copy_json=not args.no_json,
    )
    print(f"Built {len(built)} digests → {args.dist} (BASE_PATH={normalize_base(args.base_path)!r})")
    for day in built:
        print(f"  - {day}/")
    print("Next: commit data/ and dist/ to main for the connected Pages deployment.")


if __name__ == "__main__":
    main()
