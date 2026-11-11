"""スライドに出た出どころの断りと、下付きになっていない文字（check_layout.text_marks）。"""
import check_layout as cl
from zemi import Deck


def deck_with(tmp_path, lines):
    d = Deck(workdir=tmp_path / "build")
    for t in lines:
        s = d.slide("型", summary="結論")
        s.at(1, 1.9)
        s.p(t)
    out = tmp_path / "marks.pptx"
    d.save(out)
    return cl.text_marks(out)


def test_source_notes_are_found(tmp_path):
    m = deck_with(tmp_path, ["縦横比 94（資料外・概算）", "条件（講師の計算）：", "1972 年は資料外", "この読みは仮説（講師の解釈）"])
    assert [bool(m.get(i, {}).get("notes")) for i in (1, 2, 3, 4)] == [True, True, True, False]


def test_plain_subscript_is_found(tmp_path):
    m = deck_with(tmp_path, ["プラトー Q⁻¹p ＝ πC/2", "プラトー Q⁻¹_{p} ＝ πC/2", "C ＝ 2.5×10⁻⁵m の梁",
                             "∫e^{−NE}p(θ)dθ", "単位 m⁻¹s⁻¹", "T³ か T¹"])
    assert m.get(1, {}).get("subs") == ["Q⁻¹p"]
    assert all(not m.get(i, {}).get("subs") for i in (2, 3, 4, 5, 6))
