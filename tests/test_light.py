"""オプション「軽さ：軽量」：担当2人（設計・制作）で作る流れ。"""
from pathlib import Path

import brief
import budget
import next_step


def _course(tmp_path, light=True):
    (tmp_path / "X講座").mkdir()
    (tmp_path / "X講座" / "00_README.md").write_text(
        "# X講座\n\n## 学習者とゴール\n\n- 学習者：初学者\n" + ("- 軽さ：軽量\n" if light else "- 軽さ：念入り\n") + "\n## 地図\n\n| 回 | 題 |\n|---|---|\n| 1 | はじめに |\n",
        encoding="utf-8")
    w = tmp_path / "_work" / "X講座_01"
    w.mkdir(parents=True)
    return w


def test_light_is_read_from_the_course_readme(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir()
    b.mkdir()
    assert budget.light(_course(a))
    assert not budget.light(_course(b, light=False))


def test_next_step_sends_the_light_design_role_first(tmp_path):
    w = _course(tmp_path)
    _, nxt = next_step.steps_for(w)
    assert "軽量の設計の担当" in nxt and "数字を探す" not in nxt.split("：")[0]


def test_light_briefs_are_whole(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    w = _course(tmp_path)
    (w / "memo.md").write_text("# 設計メモ\n", encoding="utf-8")
    d = brief.build("軽量の設計の担当", str(w), count=False)
    own = d.split("\n---\n# 手順書の節")[0]
    assert "{" not in own and "[講座]" not in own and "[節]" not in own
    assert "① **数字**" in d and "facts.py split はしない" in d and "split --n" not in d
    assert "4a. 流れと設計メモの中身" in d                     # 設計の担当と同じ節を写す
    m = brief.build("軽量の制作の担当", str(w), count=False)
    assert "scaffold.py" in m and "--light" in m and "1回の応答で書く" in m and "3回まで" in m and "## 5. 描画して確認する" in m


def test_light_make_deck_cap(tmp_path):
    import make_deck
    w = _course(tmp_path)
    (w / "memo.md").write_text("# 設計メモ\n", encoding="utf-8")
    assert make_deck.run_budget(w)[2] == budget.LIGHT_MAKE_DECK


def test_light_memo_stops_on_unchecked_facts(tmp_path):
    """軽量の回は裏取りの担当がいないので、確認がまだの事実を check_memo が ✘ にする（標準の回は裏取りの段で見る）。"""
    import check_memo
    src = (Path(__file__).resolve().parents[1] / "examples" / "course" / "_work" / "AI活用講座_01" / "memo.md").read_text(encoding="utf-8")
    m = src.replace("| 1750億、2048 トークン | T. Brown et al., \"Language Models are Few-Shot Learners\", NeurIPS 2020（GPT-3） | ○ |",
                    "| 1750億、2048 トークン |  | 未確認 |")
    assert m != src
    (tmp_path / "l").mkdir()
    lw = _course(tmp_path / "l")
    (lw / "memo.md").write_text(m, encoding="utf-8")
    items = {item: mk for mk, item, _ in check_memo.check(lw / "memo.md")}
    assert items.get("事実の確かめ") == "✘"
    (tmp_path / "s").mkdir()
    sw = _course(tmp_path / "s", light=False)
    (sw / "memo.md").write_text(m, encoding="utf-8")
    assert "事実の確かめ" not in {item for _, item, _ in check_memo.check(sw / "memo.md")}


def test_scaffold_builds_more_from_the_memo():
    """設計メモから、比較・流れ図・判定の流れ図・図の置き方・データの出典を組む（担当が書き直す所を減らす）。"""
    import scaffold
    assert scaffold.compare_code("違い：比較：素朴な見方（棚から取り出す）と実際（確率で選ぶ）").startswith('s.compare(("素朴な見方"')
    assert scaffold.flow_code("流れ：流れ図：確かめ方（出典を開く → 原文と照らす → 自分で計算）").startswith('s.flow(["出典を開く", "原文と照らす", "自分で計算"]')
    d = scaffold.decision_code("判定：判定の流れ図：出典・数値を含む？→ はい：確かめる／いいえ：新しい事か？→ はい：確かめる／いいえ：下書きに使う")
    assert d and d.startswith("s.decision([") and "下書きに使う" in d
    assert scaffold.flow_code("流れ：流れ図：中身の無い案") is None
    assert scaffold.short_source("Walters, W. H. & Wilder, E. I.「Fabrication」Scientific Reports 13（2023）") == "（Walters ほか 2023）"
    rows = [{"#": 1, "役割": "表紙"}] + [{"#": n, "役割": "本文", "本文の要点": "a / b / c" if n % 2 else "a", "図で見せるもの": "仕組み：模式図：x"} for n in range(2, 12)]
    pl = scaffold.placements(rows)
    assert list(pl.values()).count("beside") <= 5 and "main" in pl.values()   # 左文右図は本文の半分まで


def test_design_content_hook_and_repeat():
    """設計の中身：本文の最初の2枚に問いか意外な事実が無い・同じデータを2枚で見せる、を軽量の回は ✘、標準の回は △。"""
    import check_memo
    head = "## 2. 話の順番\n\n| # | ●見出し | 前の枚から | 青帯（結論） | 図で見せるもの | 本文の要点 | 役割 |\n|---|---|---|---|---|---|---|\n"
    weak = head + ("| 1 | 表紙 | — | — | — | — | 表紙 |\n| 2 | 仕組み | — | 文はトークンに分かれる | 仕組み：模式図：x | a | 本文 |\n"
                   "| 3 | 確率 | そして | 次の語を確率で選ぶ | 仕組み：模式図：y | b | 本文 |\n"
                   "| 4 | 意外 | しかし | 誤りは17〜33%だった | 比べる：棒グラフ：データ1 | c | 本文 |\n"
                   "| 5 | 限り | しかし | 検索しても17〜33%残る | 比べる：棒グラフ：データ1 | d | 本文 |\n")
    marks = {i: m for m, i, _ in check_memo.design_content(weak, True)}
    assert marks.get("冒頭の問い") == "✘" and marks.get("同じデータのくり返し") == "✘"
    assert {m for m, _, _ in check_memo.design_content(weak, False)} == {"△"}
    good = weak.replace("| 2 | 仕組み | — | 文はトークンに分かれる |", "| 2 | 問い | — | AIは調べて答えている？ |").replace("| 5 | 限り | しかし | 検索しても17〜33%残る | 比べる：棒グラフ：データ1 |", "| 5 | 限り | しかし | 検索しても残る | 仕組み：模式図：z |")
    assert [m for m, _, _ in check_memo.design_content(good, True)] == ["✔"]


def test_light_presentation_shows_the_outline_first(tmp_path):
    """発表（担当2人）：構成案の検査が通ったら、組む前にユーザーに見せる（「構成案の確認：任せる」なら見せずに制作へ）。"""
    import shutil
    import check_outline
    root = Path(__file__).resolve().parents[1]
    w = tmp_path / "_work" / "ゼミ"
    w.mkdir(parents=True)
    for f in ("outline.md", "data_1.md"):
        if (root / "examples" / "zemi" / f).exists():
            shutil.copy(root / "examples" / "zemi" / f, w / f)
    p = w / "outline.md"
    p.write_text(p.read_text(encoding="utf-8").replace("| 軽さ | 念入り |", "| 軽さ | 標準 |"), encoding="utf-8")
    assert budget.light(w)
    assert not [r for r in check_outline.check(p) if r[0] == "✘"]
    _, nxt = next_step.steps_for(w)
    assert nxt.startswith("構成案をユーザーに見せる") and "軽量の制作の担当" in nxt
    p.write_text(p.read_text(encoding="utf-8").replace("| 軽さ | 標準 |", "| 軽さ | 標準 |\n| 構成案の確認 | 任せる |"), encoding="utf-8")
    assert next_step.steps_for(w)[1].startswith("軽量：制作の担当1人を起動")


def test_opening_mystery_points_to_the_surprise():
    """冒頭の謎：3b節に驚きがあれば、本文の最初の2枚でそのデータを指す（「しかし（壁）」だけでは通さない）。
    謎の枚の数字は、あとの枚でグラフを見せても くり返しに数えない。最後の枚が「？」で終わるなら △。"""
    import check_memo
    head = "## 2. 話の順番\n\n| # | ●見出し | 前の枚から | 青帯（結論） | 図で見せるもの | 本文の要点 | 役割 |\n|---|---|---|---|---|---|---|\n"
    tail = "\n## 3b. データ\n\n### データ1：P\n\n- 驚き：0.7 のはずが 0.55\n\n## 4. 次\n"
    rows = ("| 1 | 表紙 | — | — | — | — | 表紙 |\n| 2 | 背景 | — | 表面は金属 | 仕組み：模式図：x | a | 本文 |\n"
            "| 3 | 未検証 | しかし（壁） | 深さを分けた実験は無い | 違い：比較：x | 表面だけ弱いか？ | 本文 |\n"
            "| 4 | 結果 | だから | P は約55% | 比べる：棒グラフ：データ1 | c | 本文 |\n"
            "| 5 | まとめ | だから | 表面は弱まり P は TI より低い | 仕組み：模式図：z | d | 本文 |\n")
    marks = {i: m for m, i, _ in check_memo.design_content(head + rows + tail, True)}
    assert marks.get("冒頭の問い") == "✘"                       # 問い（？）はあるが、驚きのデータを指していない
    teaser = rows.replace("| 2 | 背景 | — | 表面は金属 | 仕組み：模式図：x | a |",
                          "| 2 | 謎 | — | TKI なら約70%のはずが約55%。なぜ？ | 仕組み：模式図：x | 謎（データ1） |")
    res = check_memo.design_content(head + teaser + tail, True)
    assert [m for m, _, _ in res] == ["✔"], res                # 謎の枚の約55%は、4枚目のグラフと くり返しに数えない
    ends = teaser.replace("| 表面は弱まり P は TI より低い |", "| 混成の抑制がトポロジーを抑える？ |")
    assert {i: m for m, i, _ in check_memo.design_content(head + ends + tail, True)}.get("結びの答え") == "△"


def test_quoted_speech_is_not_prose():
    """会話の例（かぎかっこの中）と、動詞の形の名前を＋で並べた行は、文章調・動詞止めに数えない。"""
    import check_layout as c
    c.LANG = "ja"
    assert not c.SENTENCE_END.search(c.unquoted("例：「趣味は？」「映画です」"))
    assert c.SENTENCE_END.search(c.unquoted("話が止まってしまいます"))
    assert c.unquoted("「すごい！」") == ""


def test_scaffold_lists_todos_and_fills_notes(tmp_path):
    """scaffold --light の準備：notes.md・figs.py の TODO を一覧にし、--fill-notes で原稿を TODO の所に入れる（※ の行は残す）。"""
    import scaffold
    w = tmp_path / "w"
    w.mkdir()
    (w / "notes.md").write_text("## 1\n<!-- 表紙の枚 -->\n\nTODO\n\n## 2\n<!-- 目安 400字前後（導入） ／ 前の枚から：そして（詳しく）（1文目でこの語のつながりを言う） -->\n\nTODO\n\n※ 出典：A\n\n## 3\n<!-- 目安 400字前後（導入） ／ 前の枚から：しかし（壁）（1文目でこの語のつながりを言う） -->\n\nもう書いた\n", encoding="utf-8")
    (w / "figs.py").write_text('def f_s02():\n    """TODO 図の案：仕組み：模式図：x\n    """\n    raise NotImplementedError\n', encoding="utf-8")
    todo = scaffold.notes_todo(w)
    assert todo[0].startswith("[1]") and todo[1].startswith("[2] 目安") and not any(t.startswith("[3]") for t in todo)
    assert "1文目でこの語" not in todo[1]
    assert scaffold.figs_todo(w)[0].startswith("f_s02（1行目）：図の案：仕組み")
    src = tmp_path / "n.md"
    src.write_text("## 2\n二枚目の原稿\n", encoding="utf-8")
    done, left = scaffold.fill_notes(w, src)
    t = (w / "notes.md").read_text(encoding="utf-8")
    assert done == [2] and left == [1] and "二枚目の原稿\n\n※ 出典：A" in t and "もう書いた" in t


def test_light_memo_has_no_review_pending_line(tmp_path):
    """担当2人の回はレビューが無いので、「推論距離の手当て：まだレビュー前」を出さない。"""
    import check_memo
    src = (Path(__file__).resolve().parents[1] / "examples" / "course" / "_work" / "AI活用講座_01" / "memo.md").read_text(encoding="utf-8")
    w = _course(tmp_path)
    (w / "memo.md").write_text(src, encoding="utf-8")
    assert "推論距離の手当て" not in {item for _, item, _ in check_memo.check(w / "memo.md")}
