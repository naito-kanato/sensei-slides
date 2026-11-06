"""同梱のテンプレート（構造：テンプレート1〜8）と配色（配色.json）、テンプレートを差し替える見本（examples/template）。"""
import json

import pytest
from pptx import Presentation

import notes_html as nh
import slide_profile as sp
from zemi import C, Deck, band_placeholder_idx, palettes, pick_layouts

N_STRUCTURES = 8


def style_of(k):
    t = sp.deck_options({}, name=f"テンプレート{k}")["template"]
    return t, json.loads(t.with_suffix(".json").read_text(encoding="utf-8"))


def test_bundled_template_is_selectable_by_name():
    """プロフィールに書かなくても、名前（テンプレート1〜8）でも構造の名前でも選べる。名前を言わなければ テンプレート1"""
    for k in range(1, N_STRUCTURES + 1):
        assert sp.deck_options({}, name=f"テンプレート{k}")["template"].name == f"テンプレート{k}.pptx"
    assert sp.deck_options({})["template"].name == "テンプレート1.pptx"
    for label, n in sp.structure_names().items():
        assert sp.deck_options({}, name=label)["template"].name == f"{n}.pptx"


def test_simple_template_has_the_needed_layouts():
    prs = Presentation(sp.deck_options({}, name="上の帯")["template"])
    content, title = pick_layouts(prs)
    assert (content.name, title.name) == ("本文", "表紙")
    assert band_placeholder_idx(content, prs.slide_height) == 13            # 下のまとめの帯の枠


def test_template_example_builds(built):
    prs = Presentation(built / "examples" / "template" / "テンプレートの見本_スライド.pptx")
    items = nh.slide_texts(prs)
    assert len(items) == 4
    assert items[1][1] == "重力波" and items[1][2] == "重力波は予言から100年、直接の観測がなかった"   # ゼミの見本と同じ中身
    assert prs.slides[1].slide_layout.name == "本文"                         # テンプレートだけが違う


def test_structures_differ_in_shape_not_only_color():
    """構造ごとに、結論の置き場か本文の場所が違う（色だけ違うテンプレートを並べない）"""
    seen = set()
    for k in range(1, N_STRUCTURES + 1):
        t, st = style_of(k)
        prs = Presentation(t)
        content, title = pick_layouts(prs)
        assert (content.name, title.name) == ("本文", "表紙"), k
        has_band = band_placeholder_idx(content, prs.slide_height) == 13
        assert has_band == (st["conclusion"] == "band"), k
        assert st["palette"] in palettes() and len(st["colors"]) >= 8, k
        key = (st["conclusion"], st["area"]["x"], st["area"]["top"], st["area"].get("fig_x"), st.get("nav", False),
               st["title_color"])
        assert key not in seen, k
        seen.add(key)


def test_template_colors_follow_the_template_and_reset(tmp_path):
    """テンプレートの横の .json で●などの色が変わり、次に既定のテンプレートで組むと元に戻る"""
    Deck(template=sp.deck_options({}, name="上の帯")["template"], workdir=tmp_path)
    assert C.BULLET == "E8772E"
    Deck(workdir=tmp_path)
    assert C.BULLET == style_of(1)[1]["colors"]["BULLET"]          # 既定（テンプレート1）の色に戻る


def test_color_option_recolors_structure(tmp_path):
    """どの構造にも別の配色を当てられる：飾りの図形・タイトルの文字・C の色が配色に変わり、形は変わらない"""
    pal = palettes()["深緑"]
    opts = sp.deck_options({}, name="上の帯", color="深緑")
    assert opts["color"] == "深緑"
    deck = Deck(workdir=tmp_path, **opts)
    assert C.BAND == pal["main"] and C.RED == pal["emph"]
    band = next(sh for sh in deck.prs.slide_master.shapes if sh.name.startswith("タイトルの帯"))
    assert str(band.fill.fore_color.rgb) == pal["main"]
    assert deck.area["top"] == 1.9 and deck.conclusion == "band"     # 構造（上の帯）はそのまま
    with pytest.raises(KeyError):
        Deck(workdir=tmp_path, template=opts["template"], color="無い色")


def test_color_from_the_decks_options():
    p = {"オプション": {"テンプレート": "結論の囲み", "色": "青緑"}}
    opts = sp.deck_options(p)
    assert opts["template"].name == sp.structure_names()["結論の囲み"] + ".pptx" and opts["color"] == "青緑"
    assert "color" not in sp.deck_options({}, name="結論の囲み")           # 書かなければ標準の色
