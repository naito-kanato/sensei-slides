"""原稿が言う色が、その枚の図・図形にあるか（check_colors.py）。

見本のゼミの原稿が「一番下の赤い棒が…」と言うのに、棒グラフの強調の棒は青かった（伏せた採点者2人とも減点）。
"""
import pytest
from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Inches, Pt

import check_colors as cc
import figkit

DECKS = {
    "zemi": ("zemi", "Abbott2016_PRL116_061102_スライド.pptx"),
    "zemi_en": ("zemi_en", "Gravitational_Waves_slides.pptx"),
    "course": ("course/AI活用講座", "01_生成AIは何をしているか_スライド.pptx"),
    "course_en": ("course_en/AI_Literacy", "01_What Generative AI Actually Computes_slides.pptx"),
}


def _deck(built, key):
    folder, name = DECKS[key]
    return Presentation(built / "examples" / folder / name)


@pytest.mark.parametrize("text, want", [
    ("一番下の赤い棒が、太陽3個分です", [("赤", "赤い棒")]),
    ("上が H1 の赤い線、下が L1 の青い線です", [("赤", "赤い線"), ("青", "青い線")]),
    ("H1 の信号を、うすい赤で重ねています", [("赤", "うすい赤で重ね")]),
    ("赤で囲んだ所のように", [("赤", "赤で囲")]),
    ("橙の点が実際の候補、赤丸で囲んだ右端", [("橙", "橙の点"), ("赤", "赤丸")]),
    ("The red bar at the bottom", [("赤", "red bar")]),
    ("the orange square at the far right", [("橙", "orange square")]),
    ("the curve shown in light blue", [("青", "curve shown in light blue")]),
])
def test_color_mentions(text, want):
    assert cc.color_mentions(text) == want


@pytest.mark.parametrize("text", [
    "灰色の帯が 15 ms の窓", "黒い線が背景",            # 無彩色は数えない
    "赤字で書いた所", "赤い文字の注意",                  # 文字の色は図の部品ではない
    "赤外線と紫外線", "a black hole", "infrared lines",  # 色の語ではない
    "赤が Hanford の H1、H1 in red",                     # 部品の語が無い（何を指すか決められない）
])
def test_not_color_mentions(text):
    assert cc.color_mentions(text) == []


@pytest.mark.parametrize("name, hue", [
    ("red", "赤"), ("dred", "赤"), ("warm", "赤"), ("blue", "青"), ("lblue", "青"), ("pale", "青"),
    ("orange", "橙"), ("green", "緑"), ("sand", "橙"),
])
def test_figkit_colors_fall_in_their_hue(name, hue):
    counts = cc.hue_counts(Image.new("RGB", (20, 20), getattr(figkit.COL, name)))
    assert counts[hue] == 400   # 隣の色相と重なる所（橙は赤寄り）では2つに入ってよい


@pytest.mark.parametrize("name", ["text", "ink", "gray", "light"])
def test_figkit_grays_are_not_colors(name):
    assert cc.present(cc.hue_counts(Image.new("RGB", (20, 20), getattr(figkit.COL, name)))) == []


def _slide(prs, notes, fill=None, text_red=False, line=None):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    if text_red:
        tb = s.shapes.add_textbox(Inches(1), Inches(1), Inches(4), Inches(1))
        r = tb.text_frame.paragraphs[0].add_run()
        r.text, r.font.size = "強調の赤い文字", Pt(40)
        r.font.color.rgb = RGBColor(255, 0, 0)
    if fill or line:
        b = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1), Inches(3), Inches(3), Inches(0.5))
        if fill:
            b.fill.solid()
            b.fill.fore_color.rgb = RGBColor.from_string(fill)
        else:
            b.fill.background()
        if line:
            b.line.color.rgb = RGBColor.from_string(line)
            b.line.width = Pt(2)
        else:
            b.line.fill.background()
    s.notes_slide.notes_text_frame.text = notes


def test_text_color_does_not_count_but_shapes_do():
    prs = Presentation()
    _slide(prs, "一番下の赤い棒が答えです。", fill="215F99", text_red=True)   # 赤いのは文字だけ、棒は青
    _slide(prs, "The red bar at the bottom.", fill="C0504D")                  # dred の棒
    _slide(prs, "赤で囲んだ所を見てください。", line="FF0000")              # 赤い線の枠
    bad = cc.mismatches(prs)
    assert [(i, hue) for i, _, hue, _ in bad] == [(1, "赤")]
    assert bad[0][3] == ["青"]


def test_zemi_example_flags_only_the_red_bar(built):
    """見本のゼミ：12枚目（源の正体を数で見る枚）の「赤い棒」だけが出る。赤い線・青い線・うすい赤・赤で囲んだ所・橙の点・赤丸・紫の線は図にある。"""
    prs = _deck(built, "zemi")
    bad = cc.mismatches(prs)
    assert [(i, ps, hue) for i, ps, hue, _ in bad] == [(12, ["赤い棒"], "赤")]
    said = {i for i, t in cc.notes_of(prs).items() if cc.color_mentions(t)}
    assert {6, 9, 11} <= said                                  # 正しい指し方の枚も原稿から拾っている
    marks = cc.check(built / "examples" / DECKS["zemi"][0] / DECKS["zemi"][1])
    assert marks[0][0] == "△" and "[12]" in marks[0][2] and "原稿の色を画面に合わせるか" in marks[0][2]


@pytest.mark.parametrize("key", ["zemi_en", "course", "course_en"])
def test_other_examples_have_no_mismatch(built, key):
    assert cc.mismatches(_deck(built, key)) == []
