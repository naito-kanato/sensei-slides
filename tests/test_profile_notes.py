"""デッキごとの設定の一覧と読み上げ原稿（notes.md）の読み込み、原稿HTMLの段落づくり。"""
from pathlib import Path

import slide_profile as sp
from notes_html import format_notes
from set_notes import load_notes

OUTLINE = """# 構成案：試し

## オプション

| オプション | 今の値 |
|---|---|
| 聞き手のテーマへの詳しさ | 多少知っている |
| 発表者名 | 山田太郎 |
| 発表時間 | 20分 |
| テンプレート | 結論の囲み |
| 色 | 青緑 |

## 構成
"""

MEMO = """# 設計メモ：第1回 試し

## 1. この回のゴールと前提

- 聞き手のテーマへの詳しさ：初学者
- 聞き手の前提知識：知っている＝確率／知らない＝言語モデル

## 2. 話の順番
"""


def test_options_come_from_the_decks_own_list(tmp_path):
    """共通のプロフィールは無い。設定はデッキごとの一覧（構成案の ## オプション）から読む。"""
    (tmp_path / "outline.md").write_text(OUTLINE, encoding="utf-8")
    p = sp.load_profile(tmp_path)
    assert sp.author(p) == "山田太郎"
    assert sp.politeness(p) == 1                          # 多少知っている → 丁寧さ 1
    opts = sp.deck_options(p)
    assert opts["template"].name == sp.structure_names()["結論の囲み"] + ".pptx" and opts["color"] == "青緑"


def test_course_memo_gives_politeness_from_familiarity(tmp_path):
    (tmp_path / "memo.md").write_text(MEMO, encoding="utf-8")
    p = sp.load_profile(tmp_path)
    assert sp.politeness(p) == 0 and sp.author(p) == ""


def test_no_list_gives_empty_values(tmp_path):
    p = sp.load_profile(tmp_path)
    assert sp.author(p) == "" and sp.politeness(p) is None
    assert sp.deck_options(p)["template"].exists()       # 同梱のテンプレートに落ちる


def test_options_table_marks_missing_required():
    table = sp.options_table({}, {"発表時間": "15"})
    assert "（必須・未設定）" in next(l for l in table.splitlines() if l.startswith("| 聞き手のテーマへの詳しさ"))
    assert sp.missing_required({"発表時間": "15"}) == ["聞き手のテーマへの詳しさ"]
    table = sp.options_table({}, {"聞き手のテーマへの詳しさ": "初学者"}, kind="講座")
    assert "0（詳しさから）" in next(l for l in table.splitlines() if l.startswith("| 丁寧さ"))
    assert "発表時間" not in table and sp.missing_required({"聞き手のテーマへの詳しさ": "初学者"}, "講座") == []


def test_load_notes_splits_slides_and_paragraphs(tmp_path):
    f = tmp_path / "notes.md"
    f.write_text("## 1\n最初の段落。\n続き。\n\n二つ目の段落。\n\n<!-- 読まないメモ -->\n## 3\n※（資料外の補足）補足。\n", encoding="utf-8")
    notes = load_notes(f)
    assert set(notes) == {1, 3}
    assert notes[1] == "最初の段落。 続き。\n二つ目の段落。"
    assert "読まないメモ" not in notes[1]


def test_format_notes_marks_asides():
    html = format_notes("話す文です。\n※（資料外の補足）読まない補足。\n※（要確認）値を確かめる。")
    lines = html.splitlines()
    assert lines[0] == "<p>話す文です。</p>"
    assert 'class="aside"' in lines[1] and '<span class="tag">資料外の補足</span>' in lines[1]
    assert 'class="aside check"' in lines[2]


def test_format_notes_empty():
    assert "原稿なし" in format_notes("")
