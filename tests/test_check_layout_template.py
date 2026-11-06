"""テンプレートの形（構造）に合わせた描画の検査（check_layout.py の template_*）。

PowerPoint の代わりに、作ったデッキの pptx から図形の位置を写した shapes.json（fake_render）を渡す。
文字の範囲は枠から内側の余白を引き、高さは段落の数×文字の大きさ×1.2 で見積もる（実描画に近い値）。
"""
import json

import pytest
from PIL import Image
from pptx import Presentation

import check_layout as cl
from zemi import Deck

EMU_PT = 12700


def template(root, n):
    """n：番号（1〜8）か構造の名前（「下の帯」など）。番号は見やすさの順で変わるので、特定の構造を試すときは名前で書く。"""
    if isinstance(n, str):
        import slide_profile
        n = int(slide_profile.structure_names()[n].removeprefix("テンプレート"))
    return root / "assets" / "templates" / f"テンプレート{n}.pptx"


def fake_render(pptx, tmp_path):
    """pptx の図形を shapes.json の形に写す（render_check.ps1 の代わり）。"""
    prs = Presentation(str(pptx))
    shapes = []
    for i, sl in enumerate(prs.slides, 1):
        for sh in sl.shapes:
            l, t, w, h = (v / EMU_PT for v in (sh.left, sh.top, sh.width, sh.height))
            d = {"slide": i, "name": sh.name, "type": int(sh.shape_type), "left": l, "top": t, "width": w, "height": h,
                 "ph": int(sh.placeholder_format.type) if sh.is_placeholder else None, "text": "",
                 "tl": None, "tt": None, "tw": None, "th": None, "lines": 0, "paras": 0, "size": None}
            if sh.has_text_frame and sh.text_frame.text.strip():
                paras = sh.text_frame.paragraphs
                size = next((r.font.size.pt for p in paras for r in p.runs if r.font.size), None)
                n = len(paras)
                d.update(text="\r".join(p.text for p in paras), tl=l + 7, tt=t + 3.6, tw=max(w - 14, 1.0),
                         th=n * (size or 20) * 1.2, lines=n, paras=n, size=size)
            shapes.append(d)
    f = tmp_path / "shapes.json"
    f.write_text(json.dumps({"pptx": str(pptx), "slideWidth": prs.slide_width / EMU_PT, "slideHeight": prs.slide_height / EMU_PT,
                             "slides": len(prs.slides), "shapes": shapes}, ensure_ascii=False), encoding="utf-8")
    return f


@pytest.fixture
def png(tmp_path):
    """全面が描いてある図（描いてある範囲＝枠）。"""
    p = tmp_path / "fig.png"
    Image.new("RGB", (660, 440), (40, 40, 40)).save(p, dpi=(220, 220))
    return p


def check(deck, tmp_path, capsys):
    out = tmp_path / "deck.pptx"
    deck.save(out)
    capsys.readouterr()
    code = cl.main(str(fake_render(out, tmp_path)))
    return code, capsys.readouterr().out


def deck_of(root, n, tmp_path, **kw):
    return Deck(template=template(root, n), workdir=tmp_path / "build", valign="top", **kw)   # 縦の中央寄せで位置が動かないように


def test_bundled_templates_have_consistent_geometry(root):
    """同梱の8構造は、タイトル・結論の一文・見出し・本文・帯・ページ番号の寸法が食い違わない"""
    for n in range(1, 9):
        p = template(root, n)
        prs = Presentation(str(p))
        style = json.loads(p.with_suffix(".json").read_text(encoding="utf-8"))
        content = next(cl.layout_geometry(l, prs.slide_height) for l in prs.slide_layouts if l.name == "本文")
        assert cl.template_problems(content, style, cl.area_pt(style), prs.slide_width / EMU_PT, prs.slide_height / EMU_PT) == [], n


def test_broken_template_geometry_is_found(root):
    """結論の一文の行を見出しの下の線に重ねた寸法（結論ヘッダーの message の y を下げたもの）は、描画の前に見つかる"""
    p = template(root, 1)
    prs = Presentation(str(p))
    style = json.loads(p.with_suffix(".json").read_text(encoding="utf-8"))
    style["area"]["message"] = [0.66, 1.0]
    content = next(cl.layout_geometry(l, prs.slide_height) for l in prs.slide_layouts if l.name == "本文")
    probs = cl.template_problems(content, style, cl.area_pt(style), 960, 540)
    assert any("見出しの下の線" in m for m in probs)


def test_template_is_found_even_after_recolor(root, tmp_path):
    """デッキの pptx から、どのテンプレートで作ったかを飾りと枠の形で見つける（配色を変えても当たる）。
    配色を変えると、ページ番号の色も下の帯の文字の色に合わせて変わる（濃い帯→淡い帯で白い番号が消えていた）"""
    deck = deck_of(root, "下の帯", tmp_path, color="紺とオレンジ")
    deck.slide("背景", summary="結論")
    out = tmp_path / "d.pptx"
    deck.save(out)
    geo = cl.template_geometry(str(out))
    assert geo["name"] == "テンプレート4" and geo["style"]["label"] == "下の帯"
    assert geo["area"]["bottom"] == pytest.approx(6.62 * 72)
    assert geo["content"]["sldnum_color"] == "1F3A5F"


def test_own_template_is_given_with_template_option(root, tmp_path):
    """形を変えたテンプレート（自分で足したもの）は同梱のどれとも合わない。--template で渡せば、その .json の本文の場所で見る"""
    import shutil
    own = tmp_path / "研究室.pptx"
    prs = Presentation(str(template(root, "下の帯")))
    ph = next(p for p in prs.slide_master.placeholders if p.placeholder_format.type == 1)
    ph.top = ph.top + 91440                     # タイトルの枠を 0.1 in 下げる
    prs.save(own)
    shutil.copy(template(root, "下の帯").with_suffix(".json"), own.with_suffix(".json"))
    deck = Deck(template=own, workdir=tmp_path / "build")
    deck.slide("背景", summary="結論")
    out = tmp_path / "d.pptx"
    deck.save(out)
    assert cl.template_geometry(str(out))["style"] is None
    geo = cl.template_geometry(str(out), template=own)
    assert geo["name"] == "研究室" and geo["area"]["x"] == pytest.approx(72.0)


def test_figure_below_the_box_area_is_an_error(root, tmp_path, png, capsys):
    """結論の囲みの構造では、本文・図は囲みの上（6.1 in）まで"""
    deck = deck_of(root, "結論の囲み", tmp_path)
    s = deck.slide("背景")
    s.image(png, x=2.0, y=4.7, w=3.0, h=1.6)
    code, out = check(deck, tmp_path, capsys)
    assert code == 1 and "本文の場所の下端を超える" in out


def test_figure_in_the_header_zone_is_an_error(root, tmp_path, png, capsys):
    """結論ヘッダーの構造で、図を見出しの下の線より上に上げると ERROR"""
    deck = deck_of(root, 1, tmp_path)
    s = deck.slide("背景", summary="重力波は予言から100年、直接の観測がなかった")
    s.image(png, x=7.6, y=1.0, w=3.0, h=2.0)
    code, out = check(deck, tmp_path, capsys)
    assert code == 1 and "上の見出しの領域" in out


def test_text_on_the_left_strip_is_an_error(root, tmp_path, capsys):
    deck = deck_of(root, "細い左帯と副題", tmp_path)
    s = deck.slide("背景")
    s.text(0.05, 3.0, "左の帯に重なる本文")
    code, out = check(deck, tmp_path, capsys)
    assert code == 1 and "「左の細い帯」に重なる" in out and "本文の場所より左にはみ出す" in out


def test_column_text_and_figures(root, tmp_path, png, capsys):
    """左の淡い柱：柱から右へはみ出す文は ERROR、柱の中の図は WARN、柱の縁をまたぐ図は ERROR"""
    deck = deck_of(root, 8, tmp_path)
    s = deck.slide("背景", summary="短い結論")
    s.text(0.5, 3.0, "柱の中に置いた長い一文が右の白い所まで伸びる")
    s.image(png, x=0.6, y=4.6, w=3.0, h=1.5)
    s = deck.slide("結果")
    s.image(png, x=3.5, y=3.0, w=3.0, h=2.0)
    code, out = check(deck, tmp_path, capsys)
    assert code == 1
    assert "柱からはみ出す文" in out and "図が柱の中にある" in out and "柱の縁" in out and "をまたぐ" in out


def test_two_line_message_is_an_error(root, tmp_path, capsys):
    """結論ヘッダーの結論の一文は1行の場所。2行にすると見出しの下の線にかかる"""
    deck = deck_of(root, 1, tmp_path)
    deck.slide("背景", summary="重力波は予言から100年\n直接の観測がなかった")
    code, out = check(deck, tmp_path, capsys)
    assert code == 1 and "結論の一文が 2 行" in out


def test_title_taller_than_its_slot_is_an_error(root, tmp_path, capsys):
    """結論ヘッダーのタイトルの枠（0.4 in）に2段落のタイトルは入らない"""
    deck = deck_of(root, 1, tmp_path)
    deck.slide("背景\n補足", summary="結論")
    code, out = check(deck, tmp_path, capsys)
    assert code == 1 and "タイトルが枠" in out


def test_figure_on_the_slide_number_is_an_error(root, tmp_path, png, capsys):
    deck = deck_of(root, 1, tmp_path)
    s = deck.slide("背景")
    s.image(png, x=11.9, y=6.6, w=1.0, h=0.8)
    code, out = check(deck, tmp_path, capsys)
    assert code == 1 and "ページ番号に重なる" in out


def test_slide_number_contrast_on_a_pale_band():
    """灰色のページ番号を淡い帯の上に置くと読みにくい（上の帯の構造で 2.9:1 だった）"""
    g = {"decos": [{"name": "まとめの地", "role": "band_bg", "rect": (0, 487, 960, 540), "fill": "F5EFE6"}],
         "title": None, "title_size": None, "sldnum": (878, 502, 947, 528), "sldnum_color": "8C8C8C", "band": None, "cover": True}
    num = {"slide": 1, "name": "Slide Number", "type": 14, "left": 878, "top": 502, "width": 69, "height": 26, "ph": cl.PH_SLDNUM,
           "text": "2", "tl": 930, "tt": 508, "tw": 10, "th": 14, "lines": 1, "paras": 1, "size": 12}
    msgs, _ = cl.template_checks([num], g, None, None, 960, 540, 507.6)
    assert any("ページ番号の文字" in m for _, m in msgs)
    assert cl.contrast("FFFFFF", "000000") == pytest.approx(21.0)


def test_cover_title_avoids_the_column(root, tmp_path, capsys):
    """左の淡い柱の構造の表紙では、題を柱の右の白い所の中央に置く（ページの中央だと柱の縁をまたいでいた）"""
    deck = deck_of(root, 8, tmp_path)
    s = deck.title_slide(["型の見本", "本文の形と図解の部品"], author="sensei-slides")
    assert min(sh.left for sh in s.slide.shapes if sh.has_text_frame and sh.text_frame.text.strip()) / 914400 >= 4.5
    code, out = check(deck, tmp_path, capsys)
    assert "縁をまたぐ" not in out


def test_heading_appended_to_a_big_title_is_shrunk(root, tmp_path):
    """細い左帯と副題（タイトル 28pt）では、タイトルの後ろに足す見出しが枠に入らなければ小さくする（折り返して副題に重なっていた）"""
    deck = deck_of(root, "細い左帯と副題", tmp_path)
    s = deck.slide("型の見本：重力波の初観測と本文の形", summary="段違いの順序：段階を階段状にずらし、細い矢印で")
    s.heading("段違いの順序（s.cards steps の見本）")
    title = next(ph for ph in s.slide.placeholders if ph.placeholder_format.type == 1)
    sizes = [r.font.size.pt for r in title.text_frame.paragraphs[-1].runs if r.font.size]
    assert sizes and max(sizes) < deck.title_size


def test_header_bottom_follows_the_title_slot(root, tmp_path):
    """図を上げてよい高さは、タイトルの低い構造（章のナビ：タイトル 0.6〜1.3 in）ではタイトルの枠の下"""
    assert deck_of(root, 6, tmp_path).header_bottom >= 1.35
    assert deck_of(root, "下の帯", tmp_path).header_bottom == pytest.approx(1.1)
