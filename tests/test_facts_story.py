"""裏取りの分け方（facts.py）・答えの位置（story.py）・作業フォルダの置き場所（scaffold.py）。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import facts  # noqa: E402
import scaffold  # noqa: E402
import story  # noqa: E402

MEMO = """# 設計メモ

## 1. この回のゴールと前提

- 答えの位置：後

## 2. 話の順番

| # | ●見出し | 青帯（結論） | 本文の要点 | 役割 |
|---|---|---|---|---|
| 1 | 表紙 | — | — | 表紙 |
| 2 | 今の形 | 今は5年ごと | 期間〔事実1〕 / 数〔事実2〕 | 本文 |
| 3 | 由来 | 2013年に変わった | 年〔事実3〕〔事実1〕 | 本文 |

## 3. 事実と出典

| 主張 | 値・式 | 出典（書名・URL） | 確認 |
|---|---|---|---|
| 認定の期間 | 5年 | 「審査の流れ」https://e.x/a | ○ |
| 認定病院の数 | 2,000 | | 未確認 |
| 改定の年 | 2013年 | | |
| 図の例 | 例 | | 図に（例）と書く |

## 4. 用語
"""


def _work(tmp_path):
    w = tmp_path / "_work" / "X講座_01"
    w.mkdir(parents=True)
    (w / "memo.md").write_text(MEMO, encoding="utf-8")
    return w


def test_split_only_unchecked_rows(tmp_path):
    w = _work(tmp_path)
    out = facts.split(w, 2)
    assert [p.name for p in out] == ["facts_1.md", "facts_2.md"]
    t1, t2 = (p.read_text(encoding="utf-8") for p in out)
    assert "| 2 | 認定病院の数" in t1 and "| 3 | 改定の年" in t2      # ○ と「図に（例）」の行は渡さない
    assert "| 3 | 改定の年 | 2013年 |  |  | 3 |" in t2                # 使う枚は2節の〔事実N〕から
    assert "1行終えるごとに" in t1                                    # やり方はファイルの先頭に


def test_merge_back_and_diff(tmp_path):
    w = _work(tmp_path)
    facts.split(w, 2)
    p = w / "facts_1.md"
    p.write_text(p.read_text(encoding="utf-8").replace(
        "| 2 | 認定病院の数 | 2,000 |  | 未確認 | 2 |  |",
        "| 2 | 認定病院の数 | 2,188（2026年3月末） | 「報告書」https://e.x/b 2026 | ○ | 2 | 違う：数が古い |\n"
        "| + | 新しい版 | Ver.3.0 | 「一覧」https://e.x/c 2023 | ○ | 3 | 新しく足した |"), encoding="utf-8")
    diffs = facts.merge(w)
    memo = (w / "memo.md").read_text(encoding="utf-8")
    assert "| 認定病院の数 | 2,188（2026年3月末） | 「報告書」https://e.x/b 2026 | ○ |" in memo
    assert "| 新しい版 | Ver.3.0 |" in memo and memo.index("新しい版") < memo.index("## 4.")
    assert len(diffs) == 2 and (w / "facts_diff.md").exists()
    assert "事実5" in (w / "facts_diff.md").read_text(encoding="utf-8")   # 足した行は表の最後の番号


def test_answer_position_default_and_option():
    assert story.answer_position(MEMO, "memo") == "後"
    assert story.answer_position("# x\n", "outline") == "先"
    assert story.answer_position("## オプション\n\n| オプション | 値 |\n|---|---|\n| 答えの位置 | 後 |\n", "outline") == "後"


def _outline(answer_slide: int, position: str = ""):
    opt = f"## オプション\n\n| オプション | 値 |\n|---|---|\n| 答えの位置 | {position} |\n\n" if position else ""
    rows = "\n".join(f"| {n} | 見出し{n} | {'—' if n == 2 else 'そして（次へ）' if n % 3 else 'しかし（壁）'} | 青帯{n}の一文 | 本文 |"
                     for n in range(2, 14))
    return (opt + f"## 話の筋\n\n| 筋 | 一文 | 枚 |\n|---|---|---|\n| 状況 | 今 | 2 |\n| 複雑化 | しかし | 3 |\n"
            f"| 問い | なぜか？ | 3 |\n| 答え | こうだ | {answer_slide} |\n\n"
            "## 構成\n\n| 番号 | ●見出し | 前の枚から | 青帯（結論） | 役割 |\n|---|---|---|---|---|\n"
            "| 1 | 表紙 | — | — | 表紙 |\n" + rows + "\n")


def _story_mark(text):
    body = story.body_numbers(text, "outline")
    return {i: (m, msg) for m, i, msg in story.check(text, "outline", body, "構成案")}["話の筋"]


def test_answer_first_for_presentations():
    assert _story_mark(_outline(4))[0] == "✔"                      # 発表の既定は先：問いのすぐ後で答える
    mark, msg = _story_mark(_outline(12))
    assert mark == "△" and "答えの位置「先」" in msg
    assert _story_mark(_outline(12, "後"))[0] == "✔"               # 後にすれば後ろで回収してよい
    assert _story_mark(_outline(4, "後"))[0] == "△"


def test_scaffold_refuses_work_inside_course_folder(tmp_path, capsys):
    w = tmp_path / "X講座" / "_work" / "X講座_01"
    w.mkdir(parents=True)
    assert "講座フォルダ X講座/ の中" in scaffold.misplaced(w, "memo")
    assert scaffold.misplaced(tmp_path / "_work" / "X講座_01", "memo") == ""


def test_brief_fills_template_and_keeps_kind_lines(tmp_path, monkeypatch):
    import brief
    monkeypatch.chdir(tmp_path)
    w = _work(tmp_path)
    for role in brief.roles():
        text = brief.build(role, "X講座" if role in brief.NO_WORK else str(w))
        assert "{" not in text and "[発表]" not in text and "[講座]" not in text, role
        assert "ユーザーには質問しません" in text and "10行まで" in text
    t = brief.build("直しの担当", str(w))
    assert "_work/X講座_01/memo_review.md" in t and "facts_diff.md" in t and "outline.md" not in t
    p = tmp_path / "_work" / "論文"
    p.mkdir()
    assert "outline_review.md" in brief.build("直しの担当", str(p))


def test_brief_refuses_misplaced_work(tmp_path):
    import brief
    import pytest
    w = tmp_path / "X講座" / "_work" / "X講座_01"
    w.mkdir(parents=True)
    with pytest.raises(SystemExit):
        brief.build("仕上げ役", str(w))
