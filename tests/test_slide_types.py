"""スライドの型の部品（zemi.py）と、型の見分け・単調さの確認（figplan.py）。"""
from pptx import Presentation

import figkit
import figplan as fp
from zemi import Deck


def fig_png(path, w, h):
    f, ax = figkit.fig(w, h)
    ax.plot([0, 1], [0, 1])
    figkit.save(f, path)
    return path


def test_each_type_is_recognized(tmp_path):
    wide = fig_png(tmp_path / "wide.png", 9.0, 2.6)
    side = fig_png(tmp_path / "side.png", 4.5, 3.2)
    d = Deck(workdir=tmp_path / "build")
    d.title_slide(["型の見本"])
    s = d.slide("型", summary="左に文・右に図"); s.heading("左文右図"); s.at(1, 1.9); s.p("本文"); s.image(side, x=7.6, y=1.8)
    s = d.slide("型", summary="上に文・下に図"); s.heading("上文下図"); s.at(1, 1.9); s.p("本文"); s.figure_below(wide, caption="（例）")
    s = d.slide("型", summary="全面の図"); s.heading("全面の図"); s.full_figure(wide)
    s = d.slide("型", summary="比べる"); s.heading("比較"); s.compare(("A", ["速い", "高い"]), ("B", ["遅い", "安い"]))
    s = d.slide("型", summary="1つの値"); s.heading("大きな数字"); s.key_message("5.1σ 以上", "偶然なら20万年に1回未満")
    out = tmp_path / "types.pptx"
    d.save(out)
    prs = Presentation(out)
    W, H = prs.slide_width, prs.slide_height
    assert [fp.slide_type(sl, W, H) for sl in list(prs.slides)[1:]] == ["左文右図", "上文下図", "全面の図", "比較", "大きな数字"]


def test_monotony_is_found(tmp_path):
    side = fig_png(tmp_path / "side.png", 4.5, 3.2)
    d = Deck(workdir=tmp_path / "build")
    d.title_slide(["単調"])
    for i in range(6):
        s = d.slide("型", summary=f"{i}"); s.heading(f"{i}"); s.at(1, 1.9); s.p("本文"); s.image(side, x=7.6, y=1.8)
    out = tmp_path / "same.pptx"
    d.save(out)
    assert fp.monotony(Presentation(out), skip={1}) == [(2, 7, "左文右図")]


def test_figure_main_puts_a_big_figure_left_and_text_right(tmp_path):
    """図が主役の型：左に図を大きく、そのあとの本文は右の細い列。型は「右文左図」と見分ける（大きくても全面の図ではない）。"""
    big = fig_png(tmp_path / "big.png", 8.0, 5.0)
    d = Deck(workdir=tmp_path / "build")
    s = d.slide("型", summary="図が主役")
    s.heading("図が主役")
    b = s.figure_main(big, caption="（例）")
    t = s.block("補足：", ["短い説明"])
    assert b.x < 1.5 and b.w > 6.5 and t.x >= b.right + 0.4 and t.right <= 13.33
    out = tmp_path / "main.pptx"
    d.save(out)
    prs = Presentation(out)
    assert fp.slide_type(prs.slides[0], prs.slide_width, prs.slide_height) == "右文左図"


def test_expected_questions_can_show_a_figure(tmp_path):
    """想定質問の枚：答えが前の枚の図につながる組だけ、右に図を添える。注記の頭に番号。文の列と図は重ならない。"""
    side = fig_png(tmp_path / "side.png", 5.0, 3.0)
    d = Deck(workdir=tmp_path / "build")
    s = d.slide("想定質問")
    s.heading("想定質問")
    s.qa_pairs([("Q1", "なぜ反転？", "腕の向きが違う", (side, "9枚目の図")), ("Q2", "地震では？", "計測器に信号なし")])
    shapes = {sh.name: sh for sh in s.slide.shapes}
    pic = shapes["想定質問の図"]
    texts = [sh for sh in s.slide.shapes if sh.name in ("想定質問", "回答")]
    assert all(t.left + t.width <= pic.left for t in texts)
    assert any(sh.has_text_frame and sh.text_frame.text.startswith("Q1：9枚目の図") for sh in s.slide.shapes)


def test_cards_can_carry_a_big_value(tmp_path):
    d = Deck(workdir=tmp_path / "build")
    s = d.slide("型", summary="カード")
    s.heading("カード")
    box = s.cards([("質量", "合体の前と後", "36+29 → 62"), ("距離", "約 13億光年", "410 Mpc")])
    vals = [sh for sh in s.slide.shapes if sh.name.startswith("カードの値")]
    assert len(vals) == 2 and all(box.y < v.top / 914400 < box.bottom for v in vals)


def test_text_left_figure_right_is_at_most_half(tmp_path):
    """「左に文・右に図」は本文の枚の半分まで（続かなくても、多いと単調に見えた）。"""
    side = fig_png(tmp_path / "side.png", 4.5, 3.2)
    d = Deck(workdir=tmp_path / "build")
    d.title_slide(["題"])
    for k in range(5):
        s = d.slide("型", summary=f"左文右図 {k}"); s.heading(f"枚 {k}"); s.at(1, 1.9); s.p("本文"); s.image(side, x=7.6, y=1.8)
        if k < 3:
            s = d.slide("型", summary=f"数字 {k}"); s.heading(f"数 {k}"); s.key_message("5.1σ", "偶然なら20万年に1回未満")
    out = tmp_path / "share.pptx"
    d.save(out)
    n, total = fp.side_share(Presentation(out), skip={1})
    assert (n, total) == (5, 8) and n > fp.MAX_SHARE * total


def test_recap_slide_ties_back_to_the_opening(tmp_path):
    """まとめの枚：上に「最初の問い → 答え」、下に持ち帰る一言。型は「まとめ」、結論の一文あり。"""
    d = Deck(workdir=tmp_path / "build")
    s = d.slide("まとめ", summary="自然な文でも、確率で選ぶので事実と違うことがある")
    s.heading("まとめ")
    box = s.recap("AI は答えを調べている？", "{r:確率で次の語を選んでいる}。調べてはいない",
                  ["自然な文でも誤りうる", "出典は自分で開いて確かめる"])
    names = [sh.name for sh in s.slide.shapes]
    assert {"まとめの問い", "まとめの答え", "まとめの要点"} <= set(names) and box.h > 2.5
    out = tmp_path / "recap.pptx"
    d.save(out)
    prs = Presentation(out)
    assert fp.slide_type(prs.slides[0], prs.slide_width, prs.slide_height) == "まとめ"
    import structures
    assert "まとめ" in structures.ROLES and "まとめ" not in structures.NO_CONCLUSION_ROLES


def test_every_story_type_has_a_recap_kind_and_each_kind_builds(tmp_path):
    """まとめの5つの形：13の話の型すべてに既定があり、どの形も組める（日英）。"""
    import story
    assert set(story.ARC_NAMES) == set(story.RECAP_OF_ARC) and set(story.RECAP_OF_ARC.values()) == set(Deck.RECAP_KINDS if hasattr(Deck, "RECAP_KINDS") else __import__("zemi").Slide.RECAP_KINDS)
    for lang in (None, "英語"):
        d = Deck(workdir=tmp_path / f"b{lang}", lang=lang)
        for kind in __import__("zemi").Slide.RECAP_KINDS:
            s = d.slide("まとめ", summary="答え"); s.heading("まとめ")
            s.recap("問い？", "答え", ["一言"], kind=kind, pairs=[("前", "後"), ("前2", "後2")], steps=["状況", "しかし", "答え"],
                    actions=["やること"])
            assert any(sh.name.startswith("まとめの") for sh in s.slide.shapes)
        out = tmp_path / f"k{lang}.pptx"
        d.save(out)
        prs = Presentation(out)
        assert {fp.slide_type(sl, prs.slide_width, prs.slide_height) for sl in prs.slides} == {"まとめ"}
