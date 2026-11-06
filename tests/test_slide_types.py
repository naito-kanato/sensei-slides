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
