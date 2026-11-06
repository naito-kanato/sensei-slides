"""excerpt.py：資料の、構成案の「範囲」に当たる所を抜き出す。"""
import excerpt

PAPER = "\f".join([
    "Title\nI. INTRODUCTION\nIn 1916 Einstein predicted waves.\nII. OBSERVATION\nOn September 14 the detectors saw it.\n",
    "FIG. 1. The event observed by H1 and L1.\nIII. DETECTORS\nThe arms are 4 km long.\nIV. METHODS\nWe searched.\n",
    "3.2 熱容量\n定積熱容量の定義。\n3.3 エントロピー\n別の話。\n",
])


def test_roman_section_stops_at_next_heading():
    got, miss = excerpt.pieces(PAPER, "III. Detectors")
    assert miss == [] and "4 km" in got[0][1] and "We searched" not in got[0][1]


def test_figure_and_page_and_numbered_section():
    assert "H1 and L1" in excerpt.one(PAPER, "Fig. 1 上段")
    assert "4 km" in excerpt.one(PAPER, "p.2")
    sec = excerpt.one(PAPER, "3.2節")
    assert "定積熱容量" in sec and "別の話" not in sec


def test_unknown_range_is_reported():
    got, miss = excerpt.pieces(PAPER, "II. Observation, 付録Z")
    assert len(got) == 1 and miss == ["付録Z"]


def test_same_part_once():
    got, _ = excerpt.pieces(PAPER, "Fig. 1 上段, Fig. 1 下段")
    assert len(got) == 1
