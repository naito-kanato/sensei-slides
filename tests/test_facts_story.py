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
    assert [p.name for p in out] == ["facts_1.md"]                   # 2行だけなら1人（1人に6行まで）
    t1 = out[0].read_text(encoding="utf-8")
    assert "| 2 | 認定病院の数" in t1 and "| 3 | 改定の年" in t1      # ○ と「図に（例）」の行は渡さない
    assert "| 3 | 改定の年 | 2013年 |  |  | 3 |" in t1                # 使う枚は2節の〔事実N〕から
    assert "1行終えるごとに" in t1                                    # やり方はファイルの先頭に


def test_split_skips_general_rows_but_not_numbers(tmp_path):
    w = _work(tmp_path)
    m = (w / "memo.md").read_text(encoding="utf-8").replace(
        "| 図の例 | 例 | | 図に（例）と書く |",
        "| パンダは竹を主に食べる | 竹 | 教科書 | 一般 |\n| 竹を1日20kg食べる | 20kg | | 一般 |"
        + "".join(f"\n| 数{i} | {i}件 | | 未確認 |" for i in range(6)))
    (w / "memo.md").write_text(m, encoding="utf-8")
    out = facts.split(w, 2)
    text = "".join(p.read_text(encoding="utf-8") for p in out)
    assert "竹を主に食べる" not in text and "1日20kg" in text      # 数値のある「一般」は回す
    assert len(out) == 2                                             # 9行なら2人


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


def _arc_outline(links, arc, position="後", answer=None):
    rows = "\n".join(f"| {n} | 見出し{n} | {l} | 青帯{n}の一文 | 本文 |" for n, l in enumerate(links, start=2))
    an = answer or (len(links) + 1)
    return (f"## オプション\n\n| オプション | 値 |\n|---|---|\n| 答えの位置 | {position} |\n\n"
            "## 話の筋\n\n| 筋 | 型 | 一文 | 枚 |\n|---|---|---|---|\n| 状況 | — | 今 | 2 |\n| 複雑化 | 壁 | しかし | 3 |\n"
            f"| 問い | どうやって | どうするか？ | 3 |\n| 答え | — | こうする | {an} |\n\n話の型：{arc}\n\n"
            "## 構成\n\n| 番号 | ●見出し | 前の枚から | 青帯（結論） | 役割 |\n|---|---|---|---|---|\n| 1 | 表紙 | — | — | 表紙 |\n" + rows + "\n")


def _arc_mark(text):
    return {i: (m, msg) for m, i, msg in story.check(text, "outline", story.body_numbers(text, "outline"), "構成案")}.get("話の型")


def test_story_arc_both_positions():
    late = ["—", "しかし（壁）", "そして（詳しく）", "だから（手段）", "そして（次へ）", "しかし（疑い）", "だから（帰結）", "しかし（限り）"]
    assert _arc_mark(_arc_outline(late, "論文紹介（問題から）", "後"))[0] == "✔"
    mark, msg = _arc_mark(_arc_outline(late, "論文紹介（問題から）", "先", answer=4))
    assert mark == "△" and "答えと柱の一覧" in msg                       # 先にすると、壁のすぐ後に答えの拍が要る
    early = ["—", "しかし（壁）", "だから（帰結）"] + late[3:]
    assert _arc_mark(_arc_outline(early, "論文紹介（問題から）", "先", answer=4))[0] == "✔"
    assert "答えの枚は 5" in _arc_mark(_arc_outline(early, "論文紹介（問題から）", "先", answer=5))[1]
    swapped = ["—", "だから（手段）", "しかし（壁）"] + late[4:]
    assert _arc_mark(_arc_outline(swapped, "論文紹介（問題から）", "後"))[0] == "△"
    assert _arc_mark(_arc_outline(swapped, "論文紹介（問題から）", "後") + "\n型を外す理由：方法が見どころ\n")[0] == "✔"
    assert _arc_mark(_arc_outline(late, "ない型", "後"))[0] == "△"


def test_data_arc_needs_a_number_figure_on_the_surprise():
    """話の型「数字で崩す」：意外の拍の枚の図は、数字の比べ（比べる・推移・内訳のグラフ）。"""
    links = ["—", "そして（詳しく）", "しかし（意外）", "だから（問い）", "だから（帰結）", "しかし（限り）"]

    def outline(fig3):
        rows = "\n".join(f"| {n} | 見出し{n} | {l} | 青帯{n}の一文 | {fig3 if n == 4 else '—'} | 本文 |" for n, l in enumerate(links, start=2))
        return (_arc_outline(links, "数字で崩す").split("## 構成")[0]
                + "## 構成\n\n| 番号 | ●見出し | 前の枚から | 青帯（結論） | 図で見せるもの | 役割 |\n|---|---|---|---|---|---|\n"
                "| 1 | 表紙 | — | — | — | 表紙 |\n" + rows + "\n")
    assert _arc_mark(outline("比べる：棒グラフ：自己評価と中間結果（論文 Table 2）"))[0] == "✔"
    mark, msg = _arc_mark(outline("仕組み：模式図：審査の流れ"))
    assert mark == "△" and "数字の比べ" in msg


def test_presentation_data_from_the_source(tmp_path):
    """発表：設計の担当が資料の表・図から書いた data_1.md を、構成案の3b節（構成の表の前）に入れる。3b節が無くても何も言わない。"""
    import data
    import check_memo
    w = tmp_path / "_work" / "論文"
    w.mkdir(parents=True)
    links = ["—", "そして（詳しく）", "しかし（意外）", "だから（問い）", "だから（帰結）", "しかし（限り）"]
    rows = "\n".join(f"| {n} | 見出し{n} | {l} | 青帯{n}の一文 | {'比べる：棒グラフ：データ1' if n == 4 else '—'} | 本文 |"
                     for n, l in enumerate(links, start=2))
    text = (_arc_outline(links, "数字で崩す").split("## 構成")[0]
            + "## 構成\n\n| 番号 | ●見出し | 前の枚から | 青帯（結論） | 図で見せるもの | 役割 |\n|---|---|---|---|---|---|\n"
            "| 1 | 表紙 | — | — | — | 表紙 |\n" + rows + "\n")
    (w / "outline.md").write_text(text, encoding="utf-8")
    assert [m for m, _, _ in check_memo.data_rows(text, w, [2, 3], "outline")] == ["✘"]   # 発表も data_1.md は必須
    (w / "data_1.md").write_text("## 見つからなかった：比べる表が無い\n- 調べたこと：Table 1〜3\n", encoding="utf-8")
    data.merge(w)
    nf = (w / "outline.md").read_text(encoding="utf-8")
    rows = check_memo.data_rows(nf, w, [2, 3], "outline")
    assert any(m == "✘" and "数字で崩す" in x for m, _, x in rows)      # 型が数字で崩すなのに組が無い
    other = nf.replace("話の型：数字で崩す", "話の型：原因を探る").replace("比べる：棒グラフ：データ1", "比べる：棒グラフ：x")
    assert [m for m, _, _ in check_memo.data_rows(other, w, [2, 3], "outline")] == ["・"]
    (w / "data_1.md").write_text(
        "## データ：条件ごとの正答率\n- 驚き：手がかりを足すと下がる\n- 単位：％／分母：問題のうち／時点：論文の実験\n- 出典：Table 2\n- 確認：○\n"
        "- 別の読み方：1つのデータセットだけ\n| 条件 | 値 |\n|---|---|\n| なし | 62 |\n| あり | 48 |\n", encoding="utf-8")
    assert data.merge(w) == 1
    out = (w / "outline.md").read_text(encoding="utf-8")
    assert out.index("## 3b. データ") < out.index("## 構成") and "| なし | 62 |" in out
    assert [m for m, _, _ in check_memo.data_rows(out, w, [2, 3], "outline")] == ["✔"]
    assert _arc_mark(out)[0] == "✔"


def test_answer_as_method_and_few_facts_are_flagged(tmp_path):
    """答えが見方・方法だけ、事実の行が本文より少ない、図の案が架空の名前、を △ で拾う（具体の無い講座を防ぐ）。"""
    import check_memo
    import figplan
    assert story.METHOD_ANSWER.search("系統樹で共通祖先の新しさを比べ、竹食は適応の例として扱う")
    assert not story.METHOD_ANSWER.search("二種は約4000万年前に分かれた別の科で、竹食は別々に獲得した")
    assert check_memo.fact_count(MEMO) == 4
    assert figplan.generic_names({4: "階層：ツリー：架空の分類群で包含関係", 5: "比べる：表：パンダ2種の科と属"}) == [4]
    assert figplan.generic_names({6: "仕組み：模式図：分類群Aと分類群Bの分岐"}) == [6]


def test_data_sets_merge_check_and_cards(tmp_path):
    """数字を探す段：data_N.md → 設計メモ3b節。書き方の抜け、図の案が指すデータ、カードにデータの表が写ること。"""
    import data
    import check_memo
    w = _work(tmp_path)
    (w / "data_1.md").write_text(
        "## データ：自己評価と中間結果の差\n- 驚き：自己評価は8割が S・A、中間結果は半分が B・C\n- 問いの候補：なぜずれるのか？\n"
        "- 単位：％／分母：判定のうち／時点：2019年4月\n- 出典：「審査結果」厚生労働省 2019 p.5\n- 確認：○\n"
        "- 別の読み方：資料が挙げた2項目で、全項目の平均ではない\n"
        "| 項目 | 自己評価 | 中間 |\n|---|---|---|\n| 2.1.2 | 79.5 | 52.1 |\n| 1.5.2 | 82 | 45 |\n", encoding="utf-8")
    (w / "data_2.md").write_text("## データ：悪い例\n- 単位：件\n| 区分 | 値 |\n|---|---|\n| A | たくさん |\n", encoding="utf-8")
    assert data.main(["check", str(w)]) == 1
    assert data.merge(w) == 2
    memo = (w / "memo.md").read_text(encoding="utf-8")
    ds = data.datasets(memo)
    assert ds[1]["rows"][0] == ["2.1.2", "79.5", "52.1"] and memo.index("## 3b.") < memo.index("## 4.")
    marks = [m for m, item, _ in check_memo.data_rows(memo, w, [2, 3])]
    assert "✘" in marks                                            # データ2 の書き方の抜け
    (w / "data_2.md").unlink()
    data.merge(w)
    memo = (w / "memo.md").read_text(encoding="utf-8")
    assert [m for m, item, _ in check_memo.data_rows(memo, w, [2, 3])] == ["△"]   # データがあるのに描く図が無い
    memo = memo.replace("## 2.", "データを使わない理由：差が2項目だけで弱い\n\n## 2.", 1)
    assert [m for m, item, _ in check_memo.data_rows(memo, w, [2, 3])] == ["✔"]   # 弱い組を使わないと書けば △ にしない


def test_data_not_found_is_a_result(tmp_path):
    """比べられる数字が無い回：「見つからなかった：理由」も正規の結果。設計の担当へ進み、△ を出さない。"""
    import data
    import check_memo
    w = _work(tmp_path)
    (w / "data_1.md").write_text("## 見つからなかった：定義の導入で、統計の対象でない\n", encoding="utf-8")
    assert data.main(["check", str(w)]) == 1                       # 調べたことが無い
    (w / "data_1.md").write_text("## 見つからなかった：定義の導入で、統計の対象でない\n- 調べたこと：問い2つ・検索6回\n", encoding="utf-8")
    assert data.main(["check", str(w)]) == 0
    assert data.merge(w) == 0
    memo = (w / "memo.md").read_text(encoding="utf-8")
    rows = check_memo.data_rows(memo, w, [2, 3])
    assert [m for m, _, _ in rows] == ["・"] and "統計の対象でない" in rows[0][2]


def test_data_without_other_reading_is_flagged():
    import data
    d = data.parse("## データ：x\n- 驚き：a\n- 単位：件\n- 時点：2020\n- 出典：b\n- 確認：○\n| 区分 | 値 |\n|---|---|\n| a | 1 |\n| b | 2 |\n")[0]
    assert data.problems(d) == ["「別の読み方」が無い"]
