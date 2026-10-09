#!/usr/bin/env python3
"""Optional export helpers: ZIP pack for a single day.

Usage:
  python scripts/export_pack.py 2026-10-09
  python scripts/export_pack.py 2026-10-09 --out dist/daily/export
"""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("day", help="YYYY-MM-DD")
    ap.add_argument("--digest-dir", type=Path, default=REPO / "data")
    ap.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output directory (default: dist/daily/export)",
    )
    args = ap.parse_args()

    day = args.day
    json_path = args.digest_dir / f"{day}.json"
    png_path = args.digest_dir / f"{day}.png"
    if not json_path.is_file() or not png_path.is_file():
        raise SystemExit(f"Missing {json_path.name} and/or {png_path.name} under {args.digest_dir}")

    out_dir = args.out or (REPO / "dist" / "daily" / "export")
    out_dir.mkdir(parents=True, exist_ok=True)
    zpath = out_dir / f"{day}.zip"
    with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(png_path, arcname=f"{day}.png")
        zf.write(json_path, arcname=f"{day}.json")
    print(zpath)


if __name__ == "__main__":
    main()
