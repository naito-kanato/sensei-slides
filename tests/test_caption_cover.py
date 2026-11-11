"""図の注記が図の左へ伸びないこと、表紙の長い題が幅に入るまで小さくなること（zemi.py）。"""
from pptx import Presentation

import figkit
from zemi import Deck, SLIDE_W


def fig_png(path, w, h):
    f, ax = figkit.fig(w, h)
    ax.plot([0, 1], [0, 1])
    figkit.save(f, path)
    return path


def test_long_caption_stays_right_of_figure(tmp_path):
    side = fig_png(tmp_path / "side.png", 3.0, 2.6)
    d = Deck(workdir=tmp_path / "build")
    s = d.slide("型", summary="左に文・右に図")
    s.at(1, 1.9); s.p(chr(10).join(["左の本文の行"] * 8))
    fig = s.figure_beside(side, caption="長い出典の例 ほか arXiv:0000.00000v1 (2009) p.1・3・4、別の総説 (2004)")
    cap = s.boxes[-1][1]
    assert cap.x >= fig.x - 0.01
    assert cap.right <= SLIDE_W


def test_long_caption_may_extend_left_over_empty_space(tmp_path):
    wide = fig_png(tmp_path / "wide.png", 3.0, 2.0)
    d = Deck(workdir=tmp_path / "build")
    s = d.slide("型", summary="図だけ")
    fig = s.image(wide, x=8.0, y=2.0)
    s.caption(fig, "長い出典の例 ほか arXiv:0000.00000v1 (2009) p.1・3・4、別の総説 (2004)")
    cap = s.boxes[-1][1]
    assert abs(cap.right - fig.right) < 0.01 and cap.x < fig.x


def test_short_caption_is_right_aligned(tmp_path):
    side = fig_png(tmp_path / "side.png", 4.5, 3.2)
    d = Deck(workdir=tmp_path / "build")
    s = d.slide("型", summary="左に文・右に図")
    s.at(1, 1.9); s.p("本文")
    fig = s.figure_beside(side, caption="（概略）")
    cap = s.boxes[-1][1]
    assert abs(cap.right - fig.right) < 0.01


def test_long_cover_title_shrinks(tmp_path, capsys):
    d = Deck(workdir=tmp_path / "build")
    d.title_slide(["第1回 長い題の講座はなぜ冷やすと損失が変わるのか"])
    out = tmp_path / "cover.pptx"
    d.save(out)
    prs = Presentation(out)
    tb = next(sh for sh in prs.slides[0].shapes if sh.has_text_frame and "長い題" in sh.text_frame.text)
    assert tb.left >= 0 and tb.left + tb.width <= prs.slide_width
    size = tb.text_frame.paragraphs[0].runs[0].font.size.pt
    assert size < 44
