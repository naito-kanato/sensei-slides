"""図の案とスライドの図の突き合わせ（figplan.py）と、流れ図の上限。"""
from pptx import Presentation

import figplan as fp


def test_planned_kind():
    assert fp.planned_kind("学習の2段階の流れ図") == "流れ図"
    assert fp.planned_kind("表：推定値と 90% の範囲") == "表"
    assert fp.planned_kind("経路図に所要時間・休息・駐車場所") == "図"
    assert fp.planned_kind("—") is None


def test_slide_numbers_and_limit():
    assert fp.slide_numbers("8–9") == [8, 9] and fp.slide_numbers("12") == [12]
    assert [fp.flow_limit(n) for n in (5, 10, 12, 16)] == [2, 2, 3, 4]      # 本文4枚に1枚、最低2枚


def test_course_example_follows_its_plan(built):
    work = built / "examples" / "course" / "_work" / "AI活用講座_01"
    prs = Presentation(built / "examples" / "course" / "AI活用講座" / "01_生成AIは何をしているか_スライド.pptx")
    plan = fp.plan_from_text((work / "memo.md").read_text(encoding="utf-8"), "memo")
    assert fp.actual_kinds(prs.slides[3]) == {"流れ図"}                     # 4枚目：学習の2段階
    assert "図" in fp.actual_kinds(prs.slides[1])                          # 2枚目：棒グラフ
    assert fp.mismatches(prs, plan, skip={1, 12, 13, 14, 15}) == []
    plan[2] = "—"                                                           # 案から図を消すと…（図は残っていてよい）
    plan[4] = "—"                                                           # 案に無い流れ図は見つかる
    assert fp.mismatches(prs, plan, skip={1, 12, 13, 14, 15}) == [(4, "図の案に無い流れ図")]


def test_too_many_flows_need_a_reason():
    assert fp.flow_check(8, 11, "", "設計メモ")[0] is None                   # 上限 2枚を超える
    assert fp.flow_check(8, 11, "流れ図の理由：手順の講座", "設計メモ")[0] == "✔"
    assert fp.flow_check(2, 10, "", "設計メモ")[0] == "✔"


def test_decision_kind_is_not_taken_for_flow():
    """「判定の流れ図」を「流れ図」と取り違えない（menu_name は前から探す）。判定の目的のおすすめの先頭。"""
    import figplan
    assert figplan.parse_fig("判定：判定の流れ図：30条の4の判定") == ("判定", "判定の流れ図")
    assert figplan.menu_name("流れ図：申請の手順") == "流れ図"
    rec = dict((p, k) for p, _, k in figplan.FIG_PURPOSES)
    assert rec["判定"][0] == "判定の流れ図"
    assert figplan.pptx_part("判定：判定の流れ図：要件") == "s.decision"


def test_decision_slide_kinds(tmp_path):
    """s.decision の枚は「判定の流れ図」として数え、手順の流れ図の数には入れない。問いが4つ以上は止める。"""
    import pytest
    import figplan
    import slide_profile as sp
    from pptx import Presentation
    from zemi import Deck
    deck = Deck(workdir=tmp_path / "build", **sp.deck_options({}, name="下の帯"))
    s = deck.slide("t", summary="享受目的が無ければ許諾は不要")
    s.heading("判定")
    s.decision([("享受が目的か？", "許諾が要る"), ("利益を不当に害するか？", "許諾が要る")], "許諾なしで使える", y=1.9)
    with pytest.raises(ValueError):
        s.decision([("a", "b")] * 4, "c")
    out = tmp_path / "d.pptx"
    deck.save(out)
    slide = Presentation(out).slides[0]
    kinds = figplan.actual_kinds(slide)
    assert "判定の流れ図" in kinds and "流れ図" not in kinds
    assert figplan.slide_type(slide, 1, 1) == "判定の流れ図"
