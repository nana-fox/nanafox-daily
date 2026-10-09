import importlib.util
import json
import tempfile
import unittest
import re
import os
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("build_site", Path(__file__).resolve().parents[1] / "scripts/build_site.py")
site = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(site)


class WebsiteBuildTest(unittest.TestCase):
    def bootstrap(self, path):
        html = path.read_text()
        return json.loads(re.search(r'<script id="daily-data" type="application/json">(.*?)</script>', html, re.S).group(1))
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = self.root / "data"
        self.data.mkdir()
        self.dist = self.root / "dist"

    def add_day(self, day, title, with_image=True):
        payload = {
            "title": "AI 前沿日报",
            "date": day,
            "tldr": [{"title": title, "text": "今日摘要"}],
            "sections": [{"heading": "模型", "items": [{"title": "发布", "detail": "可读摘要", "url": "https://example.com/source"}]}],
        }
        (self.data / f"{day}.json").write_text(json.dumps(payload), encoding="utf-8")
        if with_image:
            (self.data / f"{day}.png").write_bytes(b"test image bytes")

    def test_next_issue_updates_summary_and_keeps_previous_dates(self):
        self.add_day("2026-10-08", "旧一期")
        self.add_day("2026-10-09", "新一期")
        self.add_day("2026-10-10", "未完成一期", with_image=False)
        built = site.build(self.data, self.dist, base="/daily")
        self.assertEqual(built, ["2026-10-09", "2026-10-08"])
        root = self.dist / "daily"
        latest = json.loads((root / "latest.json").read_text())
        self.assertEqual(latest["date"], "2026-10-09")
        self.assertEqual(latest["url"], "/daily/2026-10-09/")
        self.assertEqual(latest["tldr"][0]["title"], "新一期")
        for day in built:
            self.assertTrue((root / day / "index.html").is_file())
            self.assertTrue((root / "export" / f"{day}.zip").is_file())
        self.add_day("2026-10-10", "下一期")
        site.build(self.data, self.dist, base="/daily")
        self.assertEqual(json.loads((root / "latest.json").read_text())["date"], "2026-10-10")
        self.assertTrue((root / "2026-10-08/index.html").is_file())

    def test_reading_precedes_collapsed_poster_and_canonical_uses_public_domain(self):
        self.add_day("2026-10-09", "<script>unsafe</script>")
        site.build(self.data, self.dist, base="/daily")
        html = (self.dist / "daily/index.html").read_text()
        self.assertLess(html.index('class="tldr"'), html.index('class="poster-section"'))
        self.assertLess(html.index('class="section"'), html.index('class="poster-section"'))
        self.assertIn('<details class="poster-preview">', html)
        self.assertNotIn('<details class="poster-preview" open', html)
        self.assertIn('href="https://nanafox.com/daily/"', html)
        self.assertIn('href="https://nanafox.com/"', html)
        self.assertIn('可读摘要', html)
        self.assertIn('&lt;script&gt;unsafe&lt;/script&gt;', html)
        day_html = (self.dist / "daily/2026-10-09/index.html").read_text()
        self.assertIn('href="https://nanafox.com/daily/2026-10-09/"', day_html)

    def test_empty_input_clears_latest_summary_and_keeps_navigation(self):
        self.add_day("2026-10-09", "上一期")
        site.build(self.data, self.dist, base="/daily")
        for item in self.data.iterdir():
            item.unlink()
        site.build(self.data, self.dist, base="/daily")
        self.assertEqual(json.loads((self.dist / "daily/latest.json").read_text()), {"date": None, "tldr": []})
        self.assertTrue((self.dist / "daily/archive/index.html").is_file())
        self.assertTrue((self.dist / "404.html").is_file())

    def test_reader_tracks_real_issues_with_original_json_on_every_route(self):
        self.add_day("2026-10-08", "旧摘要")
        self.add_day("2026-10-09", "新摘要")
        site.build(self.data, self.dist, base="/daily")
        root = self.dist / "daily"
        history = json.loads((root / "issues.json").read_text())["issues"]
        self.assertEqual([issue["day"] for issue in history], ["2026-10-09", "2026-10-08"])
        for route, day in [("index.html", "2026-10-09"), ("2026-10-08/index.html", "2026-10-08")]:
            payload = self.bootstrap(root / route)
            self.assertEqual(payload["data"], json.loads((self.data / f"{day}.json").read_text()))
            self.assertEqual(payload["day"], day)
            self.assertEqual(payload["issues"], history)
            self.assertNotIn("_day", payload["data"])
        self.assertEqual(self.bootstrap(root / "archive/index.html")["view"], "archive")
        html = (root / "index.html").read_text()
        for href in re.findall(r'(?:src|href)="(/daily/reader/[^\"]+)"', html):
            self.assertTrue((self.dist / href.lstrip("/")).is_file(), href)

    def test_script_delimiters_and_unsafe_links_do_not_execute(self):
        self.add_day("2026-10-09", "</script><script>alert(1)</script>")
        path = self.data / "2026-10-09.json"
        data = json.loads(path.read_text())
        data["sections"][0]["items"][0]["url"] = "javascript:alert(1)"
        path.write_text(json.dumps(data))
        site.build(self.data, self.dist, base="/daily")
        html_path = self.dist / "daily/index.html"
        html = html_path.read_text()
        self.assertNotIn('<script>alert(1)</script>', html)
        self.assertNotIn('href="javascript:', html)
        self.assertEqual(self.bootstrap(html_path)["data"], data)

    def test_root_base_and_no_json_keep_reader_and_original_download_data(self):
        self.add_day("2026-10-09", "摘要")
        site.build(self.data, self.dist, base="", copy_json=False)
        payload = self.bootstrap(self.dist / "index.html")
        self.assertEqual(payload["base"], "")
        self.assertEqual(payload["issues"][0]["url"], "/2026-10-09/")
        self.assertEqual(payload["data"]["tldr"][0]["title"], "摘要")
        self.assertFalse((self.dist / "assets/2026-10-09.json").exists())
        self.assertTrue((self.dist / "export/2026-10-09.zip").is_file())

    def test_checkout_timestamps_do_not_change_original_download_pack(self):
        self.add_day("2026-10-09", "摘要")
        site.build(self.data, self.dist, base="/daily")
        pack = self.dist / "daily/export/2026-10-09.zip"
        original = pack.read_bytes()
        for path in self.data.iterdir():
            os.utime(path, (1600000000, 1600000000))
        site.build(self.data, self.dist, base="/daily")
        self.assertEqual(pack.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
