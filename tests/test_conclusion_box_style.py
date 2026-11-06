"""結論の囲みの見分け：下の結論の置き場の囲みは淡い塗り、本文の中の囲み（s.lead_down の結論）は線だけ。

結論の囲みの構造で、同じ塗りの囲みが2つ並ぶと、どちらがスライドの結論か見分けられない（名前を伏せた読みやすさの採点で指摘）。
"""
import pytest

import slide_profile as sp
import zemi
from zemi import BOX_TOP, C, Deck


def _boxes(slide):
    return sorted((sh for sh in slide.shapes if sh.name == "結論の囲み"), key=lambda sh: sh.top)


@pytest.mark.parametrize("k", ["結論の囲み", "結論ヘッダー", "下の帯"])
def test_lead_down_box_is_outline_only(tmp_path, k):
    deck = Deck(workdir=tmp_path / "b", **sp.deck_options({}, name=k))
    s = deck.slide("研究の目的", summary="2台の干渉計で波そのものをとらえる")
    s.heading("問題から目的へ")
    s.lead_down("直接の観測はまだ", "離れた2台で同時に測る")
    boxes = _boxes(s.slide)
    body = [b for b in boxes if b.top / 914400 < BOX_TOP - 0.1]
    assert len(body) == 1
    b = body[0]
    assert b.fill.type != 1                                   # 塗らない（MSO_FILL.SOLID でない）
    assert str(b.line.color.rgb) == C.BAND                    # 細い濃い色の線
    run = b.text_frame.paragraphs[0].runs[0]
    assert str(run.font.color.rgb) == C.TEXT                  # 文字は濃い墨（白地に 4.5:1 以上）
    if deck.conclusion == "box":                              # 下の結論の置き場は淡い塗りのまま
        slot = [x for x in boxes if x.top / 914400 >= BOX_TOP - 0.1]
        assert len(slot) == 1 and slot[0].fill.type == 1 and str(slot[0].fill.fore_color.rgb) == C.CONCLUDE
        assert zemi.has_conclusion(s.slide, deck.prs.slide_height)


def test_outline_box_counts_as_conclusion_only_at_bottom(tmp_path):
    """本文の中の線だけの囲みは、結論の一文に数えない（下の置き場の囲みだけ数える）"""
    deck = Deck(workdir=tmp_path / "b", **sp.deck_options({}, name="結論の囲み"))
    s = deck.slide("研究の目的")
    s.heading("問題から目的へ")
    s.lead_down("直接の観測はまだ", "離れた2台で同時に測る")
    assert not zemi.has_conclusion(s.slide, deck.prs.slide_height)
