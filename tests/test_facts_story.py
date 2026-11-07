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


def _outline(answer_slide: int, position: str = "", comp="壁", ask="どうやって", comp_slide=3, typed=True):
    opt = f"## オプション\n\n| オプション | 値 |\n|---|---|\n| 答えの位置 | {position} |\n\n" if position else ""
    rows = "\n".join(f"| {n} | 見出し{n} | {'—' if n == 2 else 'そして（次へ）' if n % 3 else 'しかし（壁）'} | 青帯{n}の一文 | 本文 |"
                     for n in range(2, 14))
    t = (lambda v: f" {v} |") if typed else (lambda v: "")
    story_rows = (f"| 筋 |{t('型')} 一文 | 枚 |\n|---|{'---|' if typed else ''}---|---|\n| 状況 |{t('—')} 今 | 2 |\n"
                  f"| 複雑化 |{t(comp)} しかし | {comp_slide} |\n| 問い |{t(ask)} どうやって取るか？ | 3 |\n"
                  f"| 答え |{t('—')} こうだ | {answer_slide} |\n")
    return (opt + "## 話の筋\n\n" + story_rows + "\n"
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


def test_story_types_complication_and_question():
    mark, msg = _story_mark(_outline(4))
    assert mark == "✔" and "複雑化（壁）" in msg and "どうやって" in msg
    assert story.story_types(_outline(4)) == {"状況": "—", "複雑化": "壁", "問い": "どうやって", "答え": "—"}
    old = _outline(4, typed=False)                                    # 型の列が無い古い書き方
    assert story.story_table(old)["問い"] == ("どうやって取るか？", 3) and story.story_types(old) is None
    mark, msg = _story_mark(old)
    assert mark == "△" and "「型」の列が無い" in msg and "| 筋 | 型 | 一文 | 枚 |" in msg
    mark, msg = _story_mark(_outline(4, comp="", ask="いつ"))          # 型が無い・選択肢に無い
    assert mark == "△" and "複雑化「空」" in msg and "問い「いつ」" in msg
    mark, msg = _story_mark(_outline(4, comp="意外"))                 # 3枚目は しかし（壁）なので合わない
    assert mark == "△" and "複雑化の枚 3" in msg and "しかし（意外）" in msg
    mark, msg = _story_mark(_outline(4, comp_slide=4))                # 4枚目は そして（次へ）
    assert mark == "△" and "複雑化の枚 4" in msg
    assert _story_mark(_outline(4, comp="意外", comp_slide=2))[0] == "✔"   # 本文の最初の枚なら見ない


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


def test_body_form_slots():
    import structures as S
    assert S.slot_problems(["展開"], ["条件A だと結果B"]) == [("展開", S.SLOTS["展開"]["write"])]
    assert S.slot_problems(["帰結"], ["前提", "⇒ 結論"]) == []
    assert S.slot_problems(["場合分け"], ["高い：x"])                       # 場合分けは2つ以上
    assert S.slot_problems(["ラベル", "場合分け"], ["名前：説明", "高い：x", "低い：y"]) == []
    got = dict(S.assign(["ラベル", "展開"], ["図の読み方：横軸は時刻", "始まり 35 Hz → 250 Hz", "ひずみ 1e-21"]))
    assert got["展開"] == ["始まり 35 Hz → 250 Hz"] and got["ラベル"] == ["図の読み方：横軸は時刻"] and got["余り"] == ["ひずみ 1e-21"]
    assert dict(S.assign(["ラベル"], ["波形：35→150 Hz で最大"]))["ラベル"]           # 見出しの中の「→」は展開にしない


def test_figure_menu_and_question_types():
    import figplan
    import structures as S
    assert figplan.menu_name("棒グラフ：認定率") == "棒グラフ" and figplan.menu_name("論文 Fig. 2（右）") == "資料の図"
    assert figplan.menu_name("光のパワーの段階") is None
    memo = MEMO.replace("## 4. 用語", "## 6. 確認問題\n\n### 問題\n1-1. a〔ゴール1・2枚目〕〔型：定義〕\n1-2. b〔型：定義〕\n"
                        "1-3. c〔型：仕組み〕\n\n### 解答\n1-1. x\n\n## 4. 用語")
    mark, _, msg = S.check_quiz_types(memo)[0]
    assert mark == "△" and "2種類" in msg
    ok = memo.replace("1-3. c〔型：仕組み〕", "1-3. c〔型：誤り指摘〕\n1-4. d〔型：仕組み〕")
    assert S.check_quiz_types(ok)[0][0] == "✔"


def test_new_figure_parts_draw(tmp_path):
    from figkit import fig, save
    from figlib import bars, share_bar, timeline
    f, ax = fig(5, 2.5)
    bars(ax, ["a", "b"], [3, 1], highlight=0, unit="%")
    save(f, tmp_path / "b.png")
    f, ax = fig(5, 1.5)
    share_bar(ax, [("a", 3), ("b", 7)])
    save(f, tmp_path / "s.png")
    f, ax = fig(6, 2.4)
    timeline(ax, 1990, 2020, eras=[("x", 1990, 2005)], events=[(2000, "e")], highlight=0)
    save(f, tmp_path / "t.png")
    assert all((tmp_path / n).exists() for n in ("b.png", "s.png", "t.png"))


def test_figure_purpose_and_recommended_kind():
    import figplan
    assert figplan.parse_fig("比べる：棒グラフ：発表の数") == ("比べる", "棒グラフ")   # 中身の「発表」の「表」を拾わない
    assert figplan.parse_fig("論文 Fig. 2") == (None, "資料の図")
    rows = ("## 構成\n\n| 番号 | ●見出し | 図で見せるもの | 役割 |\n|---|---|---|---|\n"
            "| 2 | a | 比べる：棒グラフ：x | 本文 |\n| 3 | b | 比べる：年表：y | 本文 |\n| 4 | c | 棒グラフ：z | 本文 |\n"
            "| 5 | d | 時期：表：w（外す理由：年が2つだけ） | 本文 |\n")
    mark, _, msg = figplan.check_menu(rows, "outline", [2, 3, 4, 5])[0]
    assert mark == "△" and "[3] 比べるに年表" in msg and "目的が無い：[4]" in msg and "[5]" not in msg
    assert figplan.planned_kind("観点：表：推定値") == "表" and figplan.planned_kind("比べる：棒グラフ：x") == "図"
