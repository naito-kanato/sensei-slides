"""使用量を抑える部品：guide.py（節だけ出す）・make_deck.py（組む→検査を1回で。描画は試験では省く）・少なすぎる本文と原稿の検査。"""
import subprocess
import sys
from pathlib import Path

import check_layout
import check_notes
import guide

ROOT = Path(__file__).resolve().parents[1]


def test_guide_prints_only_the_section(capsys):
    assert guide.main(["course", "4"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("### 4.") and "### 5." not in out
    full = (ROOT / "references" / "course.md").read_text(encoding="utf-8")
    assert len(out) < 0.6 * len(full)                      # 丸ごと読むより短い


def test_guide_lists_headings(capsys):
    assert guide.main(["skill"]) == 0
    assert "使用量を抑える進め方" in capsys.readouterr().out


def test_make_deck_builds_and_reports_briefly(built):
    w = built / "examples" / "course" / "_work" / "AI活用講座_01"
    r = subprocess.run([sys.executable, "-X", "utf8", str(built / "scripts" / "make_deck.py"), str(w), "--no-render"],
                       capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stdout + r.stderr
    assert r.stdout.startswith("組んだ：") and len(r.stdout.splitlines()) <= 6


def test_thin_body_is_flagged():
    W, H = 960, 540
    items = [{"slide": 1, "name": "TextBox 3", "text": "表面加熱 → 中心加熱に遅れ", "size": 20, "ph": None}]
    assert check_layout.content_chars(items) < check_layout.TEXT_MIN_CHARS
    items.append({"slide": 1, "name": "場合分け", "text": "熱板 120〜220℃：表面の焼き色。中心 55〜85℃：硬さと厚さ。厚さ 20 mm の牛肉で比べた研究。焼き色は約 140℃ から", "size": 18, "ph": None})
    assert check_layout.content_chars(items) >= check_layout.TEXT_MIN_CHARS   # 囲みの中の文字も数える


def test_short_notes_per_slide_are_flagged(tmp_path):
    plan = ("## 2. 話の順番\n\n| # | ●見出し | 青帯（結論） | 図で見せるもの | 役割 |\n|---|---|---|---|---|\n"
            "| 1 | 表紙 | — | — | 表紙 |\n| 2 | 熱の通り方 | 表面から熱が入る | 断面の図 | 本文 |\n")
    (tmp_path / "memo.md").write_text(plan, encoding="utf-8")
    (tmp_path / "notes.md").write_text("## 1\n始めます。\n\n## 2\n熱は表面から入ります。\n", encoding="utf-8")
    got = {item: m for m, item, _ in check_notes.check(tmp_path)}
    assert got.get("1枚あたりの原稿") == "△"
