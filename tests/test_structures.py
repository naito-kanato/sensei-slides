"""型の辞書（structures.py）・本文の形と図解の部品（zemi.py）・帯の無い構造・組み方の分析（analyze_structure.py）。

本文の形を構成案で決め、部品で組み、渡す前の確認で突き合わせる。どの AI で作っても同じ組み方になるように。
"""
import json

import pytest
from PIL import Image
from pptx import Presentation

import analyze_structure as az
import check_layout as cl
import figplan
import slide_profile as sp
import structures as stc
from zemi import C, Deck


@pytest.fixture
def png(tmp_path):
    p = tmp_path / "fig.png"
    Image.new("RGB", (880, 660), "white").save(p, dpi=(220, 220))   # 4 × 3 in
    return p


def deck_with_all_parts(tmp_path, png, name="下の帯"):
    deck = Deck(workdir=tmp_path / "build", **sp.deck_options({}, name=name))
    deck.title_slide(["表紙"])
    s = deck.slide("t", summary="帰結"); s.heading("h"); s.at(1, 2); s.lead(["前提の説明の1行目", "前提の説明の2行目"], "帰結の一言"); s.image(png, x=8, y=2)
    s = deck.slide("t", summary="ラベル"); s.heading("h"); s.block("ラベル：", ["説明"]); s.image(png, x=8, y=2)
    s = deck.slide("t", summary="展開"); s.heading("h"); s.develop("条件", "{r:結果}"); s.image(png, x=8, y=2)
    s = deck.slide("t"); s.heading("h"); s.lead_down("前提", "結論")
    s = deck.slide("t", summary="場合分け"); s.heading("h"); s.cases([("A", "a"), ("B", "b")], x=1, y=2); s.image(png, x=8, y=2)
    s = deck.slide("t", summary="問い"); s.heading("h"); s.at(1, 2); s.ask("〜ではないのか？", "否定"); s.image(png, x=8, y=2)
    s = deck.slide("t", summary="手順"); s.heading("h"); s.numbered(["一", "二"], x=1, y=2); s.image(png, x=8, y=2)
    s = deck.slide("t", summary="並列"); s.heading("h"); s.cards([("A", "a"), ("B", "b"), ("C", "c")], y=2)
    s = deck.slide("t", summary="段違い"); s.heading("h"); s.cards([("A", ""), ("B", ""), ("C", "")], layout="steps", y=2)
    s = deck.slide("t", summary="循環"); s.heading("h"); s.cards([("A", ""), ("B", ""), ("C", ""), ("D", "")], layout="cycle", y=2)
    s = deck.slide("t", summary="ツリー"); s.heading("h"); s.tree("根", ["枝1", "枝2"], y=2)
    s = deck.slide("t", summary="前後"); s.heading("h"); s.before_after(("前", ["a"]), ("後", ["b"]), value="2 倍", y=2)
    s = deck.slide("t", summary="2つ"); s.heading("h"); s.pair(png, png, labels=["a", "b"], values=["1", "2"], y=2)
    deck.section(2, "章")
    out = tmp_path / "parts.pptx"
    deck.save(out)
    return deck, Presentation(out)


def test_forms_are_detected_by_part_names(tmp_path, png):
    _, prs = deck_with_all_parts(tmp_path, png)
    got = {i: stc.detect_forms(sl) for i, sl in enumerate(prs.slides, 1)}
    assert "帰結" in got[2] and "ラベル" in got[3] and "展開" in got[4] and "縦の結論" in got[5]
    assert "場合分け" in got[6] and {"問い", "帰結"} <= got[7] and "手順" in got[8]


def test_diagram_types_are_recognized(tmp_path, png):
    _, prs = deck_with_all_parts(tmp_path, png)
    W, H = prs.slide_width, prs.slide_height
    types = [figplan.slide_type(sl, W, H) for sl in prs.slides]
    assert types[8:15] == ["並列カード", "段違いの順序", "循環", "ツリー", "前後", "2つ並べた図", "区切り"]
    assert types[4] == "文のみ"                                   # 縦の矢印で結論へだけの枚は、図が無い
    assert "流れ図" in figplan.actual_kinds(prs.slides[9])        # 段違い・循環のカードは流れ図の数に入る
    assert figplan.actual_kinds(prs.slides[8]) == {"図"}          # 並列カードは図
    assert figplan.actual_kinds(prs.slides[4]) == set()           # 結論の囲み（縦の矢印で結論へ）は図に数えない


def test_plan_column_and_checks(tmp_path):
    text = ("## 構成\n\n| 番号 | タイトル | ●見出し | 図で見せるもの | 本文の形 |\n|---|---|---|---|---|\n"
            + "".join(f"| {i} | t | h | 図 | 帰結 |\n" for i in range(2, 8))
            + "| 8 | t | h | 図 | ラベル・なぞ |\n")
    plan = stc.plan_forms(text, "outline")
    assert plan[2] == ["帰結"] and plan[8][0] == "ラベル" and plan[8][1] == ("?", "なぞ")
    res = {item: mark for mark, item, _ in stc.check_plan(text, "outline", list(range(2, 9)), "構成案")}
    assert res["本文の形"] == "△" and res["本文の形の続き方"] == "△"     # 分からない語、帰結が6枚続く
    no_col = text.replace("| 本文の形 |", "|").replace("|---|---|---|---|---|", "|---|---|---|---|")
    assert stc.check_plan(no_col, "outline", [2], "構成案")[0][0] == "△"   # 列が無い


def test_examples_have_form_column(root):
    for path, kind in ((root / "examples/zemi/outline.md", "outline"), (root / "examples/course/_work/AI活用講座_01/memo.md", "memo")):
        plan = stc.plan_forms(path.read_text(encoding="utf-8"), kind)
        assert plan and not any(isinstance(k, tuple) for ks in plan.values() for k in ks), path


def test_mismatch_when_part_is_missing(tmp_path, png):
    _, prs = deck_with_all_parts(tmp_path, png)
    plan = {2: ["帰結"], 3: ["展開"], 4: ["展開"], 9: ["箇条"]}
    bad = dict(stc.mismatches(prs, plan, skip={1}))
    assert 3 in bad and 2 not in bad and 4 not in bad and 9 not in bad   # 箇条は見ない


def test_template_red_applies_to_markup(tmp_path):
    deck = Deck(workdir=tmp_path / "b", **sp.deck_options({}, name="上の帯"))
    s = deck.slide("t")
    s.text(1, 2, "{r:赤}")
    run = s.slide.shapes[-1].text_frame.paragraphs[0].runs[0]
    assert str(run.font.color.rgb) == C.RED == "C8102E"


@pytest.mark.parametrize("k,mode,name", [("結論の囲み", "box", "結論の囲み"), ("結論タイトル", "title", "見出し"), ("細い左帯と副題", "lead", "見出し"),
                                         ("左の淡い柱", "column", "結論の一文"), ("結論ヘッダー", "header", "見出し")])
def test_skeletons_without_band(tmp_path, k, mode, name):
    t = sp.deck_options({}, name=k)["template"]
    assert json.loads(t.with_suffix(".json").read_text(encoding="utf-8"))["conclusion"] == mode
    deck = Deck(workdir=tmp_path / "b", template=t)
    assert deck.band_idx is None and deck.conclusion == mode
    s = deck.slide("話題", summary="この枚の結論")
    shapes = {sh.name: sh for sh in s.slide.shapes}
    assert name in shapes and "この枚の結論" in shapes[name].text_frame.text
    assert "青帯" not in shapes
    if mode == "box":
        assert deck.content_bottom < 6.25
    if mode == "column":   # 柱のある構造：横いっぱいの部品は右の白い所に、柱の結論は柱の幅で折り返す
        assert deck.wide[0] == deck.area["fig_x"] > 4.5 > deck.area["text_right"]   # 柱 34%、右の白い所が図
        s2 = deck.slide("話題", summary="とても長い結論の一文が、柱の幅には入りきらない場合")
        assert "\n" in next(sh for sh in s2.slide.shapes if sh.name == "結論の一文").text_frame.text


@pytest.mark.parametrize("k", ["結論タイトル", "細い左帯と副題", "結論ヘッダー"])
def test_heading_joins_title_when_message_is_on_top(tmp_path, k):
    """結論の一文・副題が上にある構造では、見出しはタイトルの行に「／ 見出し」と足し、別の行にしない（上を2段に）"""
    deck = Deck(workdir=tmp_path / "b", template=sp.deck_options({}, name=k)["template"])
    s = deck.slide("背景", summary="結論の一文")
    s.heading("重力波")
    title = next(ph for ph in s.slide.placeholders if ph.placeholder_format.type == 1)
    assert title.text_frame.text == "背景　／　重力波"
    assert [sh.name for sh in s.slide.shapes].count("見出し") == 1       # 結論の一文・副題だけ
    s2 = deck.slide("目的")                                               # 結論の無い枚では、見出しを結論の場所に
    b = s2.heading("問題から目的へ")
    assert abs(b.y - deck.area["heading"][1]) < 1e-6


def test_nav_structure_draws_sections(tmp_path):
    t = sp.deck_options({}, name="章のナビ")["template"]
    deck = Deck(workdir=tmp_path / "b", template=t)
    deck.title_slide(["表紙"])
    for sec in ("背景", "背景", "結果", "考察"):
        deck.slide(sec, summary="結論")
    deck.save(tmp_path / "nav.pptx")
    prs = Presentation(tmp_path / "nav.pptx")
    tabs = [[sh for sh in sl.shapes if sh.name == "章のナビ"] for sl in prs.slides]
    assert tabs[0] == [] and [len(t) for t in tabs[1:]] == [3, 3, 3, 3]          # 章は出てきた順に3つ
    cur = [next(sh.text_frame.text for sh in t if sh.text_frame.paragraphs[0].runs[0].font.bold) for t in tabs[1:]]
    assert cur == ["背景", "背景", "結果", "考察"]
    assert figplan.actual_kinds(prs.slides[1]) == set()                           # ナビは図・表に数えない


def test_layout_does_not_count_text_boxes_as_figures():
    box = {"slide": 1, "name": "結論の囲み", "type": cl.MSO_AUTOSHAPE, "left": 100, "top": 300, "width": 300, "height": 40, "ph": None}
    cases = dict(box, name="場合分け", text="A\r説明", size=20)
    card = dict(box, name="カード_並列")
    assert not cl.is_figure(box) and not cl.is_figure(cases) and cl.is_figure(card)
    assert cl.is_body(cases)


def test_analyze_structure_counts_forms(tmp_path, png, capsys):
    deck_with_all_parts(tmp_path, png)
    assert az.main([str(tmp_path / "parts.pptx")]) == 0
    out = capsys.readouterr().out
    assert "| 帰結 |" in out and "本文の形の割合" in out and "下の帯" in out


@pytest.mark.parametrize("k,moved", [("結論ヘッダー", True), ("下の帯", False)])
def test_body_is_centered_without_band(tmp_path, k, moved):
    """下の帯の無い構造では、本文の塊を縦の中央に寄せる（上寄せのままだと下が空く）。帯のある構造では上寄せのまま"""
    deck = Deck(workdir=tmp_path / "b", template=sp.deck_options({}, name=k)["template"])
    s = deck.slide("背景", summary="結論の一文")
    s.heading("見出し")
    s.lead(["短い本文"], "帰結")
    before = min(sh.top for sh in s.slide.shapes if sh.name in ("塊の本文", "帰結"))
    deck.save(tmp_path / "v.pptx")
    after = min(sh.top for sh in Presentation(tmp_path / "v.pptx").slides[0].shapes if sh.name in ("塊の本文", "帰結"))
    assert (after > before) == moved
