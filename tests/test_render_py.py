"""PowerPoint を使わない描画（render_check_py.py）。PowerPoint も LibreOffice も使わないので、どの環境でも走る。

文字の幅は PC の書体で測る（MS PGothic・Segoe UI が無い環境では代わりの書体）ので、幅の値そのものは見ず、
書体によらない所（行数・縦の位置・余白・揃え・禁則）を見る。PowerPoint との突き合わせはテストの外（作者の手元の道具）で行う。
"""
import json
import subprocess
import sys

import pytest
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

import check_layout
import make_deck
import render_check_py as rp


def _deck(tmp_path, make):
    """白紙のスライド1枚に make(slide) で図形を置いた pptx を保存して、(パス, 図形の一覧) を返す。"""
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    s = prs.slides.add_slide(prs.slide_layouts[6])
    make(s)
    p = tmp_path / "t.pptx"
    prs.save(str(p))
    return p


def _ja(run):
    rpr = run._r.get_or_add_rPr()
    rpr.set("lang", "ja-JP")
    rpr.set("altLang", "en-US")


def _rows(p, tmp_path):
    js = rp.render(p, tmp_path / "render", images=False)
    return js, [r for r in js["shapes"] if r["text"]]


def _lines(p):
    """各図形の行の文字（layout_text の結果）。"""
    prs = Presentation(str(p))
    deck = rp.Deck(prs)
    s = prs.slides[0]
    out = []
    for sh in s.shapes:
        ctx = rp.TextCtx(deck, sh, s.slide_layout.slide_master)
        lay = rp.layout_text(ctx, (sh.left / 12700, sh.top / 12700, sh.width / 12700, sh.height / 12700))
        out.append(["".join(c.c for c in ln.chars).strip("\v") for ln in lay["lines"]])
    return out


def test_unwrapped_box_lines_and_insets(tmp_path):
    """折り返さない枠（zemi の本文）：行数＝段落の数、文字の上端＝枠の上端＋3.6pt、高さ＝行数×大きさ×1.2、左端＝枠の左端＋7.2pt。"""
    def make(s):
        tb = s.shapes.add_textbox(Inches(1), Inches(2), Inches(3), Inches(1.6))
        tf = tb.text_frame
        tf.word_wrap = False
        for i, t in enumerate(["散乱なし", "P=0.80・Z=0.96", "（電波を規則正しく出す中性子星）"]):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = PP_ALIGN.LEFT
            r = p.add_run()
            r.text = t
            r.font.size = Pt(20)
            _ja(r)
    js, rows = _rows(_deck(tmp_path, make), tmp_path)
    assert js["engine"] == "python" and js["slides"] == 1
    r = rows[0]
    assert r["lines"] == 3 and r["paras"] == 3 and r["size"] == 20
    assert r["tl"] == pytest.approx(72 + 7.2, abs=0.01)
    assert r["tt"] == pytest.approx(144 + 3.6, abs=0.01)
    assert r["th"] == pytest.approx(3 * 24, abs=0.01)
    assert r["tw"] > 100


def test_wrapped_box_keeps_kinsoku_and_words(tmp_path):
    """折り返す枠：「、」「。」「ー」などで行を始めない、英単語の途中で切らない。"""
    text = ("アンドレーエフ反射の電流は、ギャップの内側で2倍になる。The spin polarization is about 0.55 below Tc, "
            "フィッティングのパラメータ（Blonder–Tinkham–Klapwijk）を、根拠を添えて判定せよ。")

    def make(s):
        for k, w in enumerate((2.2, 3.1, 4.3)):
            tb = s.shapes.add_textbox(Inches(0.3 + 4.3 * (k % 3)), Inches(1), Inches(w), Inches(4))
            tb.text_frame.word_wrap = True
            r = tb.text_frame.paragraphs[0].add_run()
            r.text = text
            r.font.size = Pt(20)
            _ja(r)
    p = _deck(tmp_path, make)
    words = set(text.replace("（", " ").replace("）", " ").replace("–", " ").split())
    for lines in _lines(p):
        assert len(lines) >= 3
        assert "".join(lines).replace(" ", "") == text.replace(" ", "")
        for a, b in zip(lines, lines[1:]):
            assert b[0] not in rp.NO_START, (a, b)
            assert a.rstrip()[-1] not in rp.NO_END, (a, b)
            # 英単語の途中で切らない（行の末の語と次の行の頭の語が、もとの1語の前と後ろにならない）
            tail, head = a.rstrip().split(" ")[-1], b.split(" ")[0]
            if tail.isascii() and head.isascii() and tail[-1:].isalpha() and head[:1].isalpha():
                assert (tail + head) not in words, (a, b)


def test_centered_and_right_aligned(tmp_path):
    """中央揃えは行末の空白の分を除いた幅で揃え、範囲はその分だけ右へ出る（PowerPoint の実測）。"""
    def make(s):
        for k, al in enumerate((PP_ALIGN.CENTER, PP_ALIGN.RIGHT)):
            tb = s.shapes.add_textbox(Inches(1), Inches(1 + 1.5 * k), Inches(6), Inches(0.6))
            tb.text_frame.word_wrap = True
            p = tb.text_frame.paragraphs[0]
            p.alignment = al
            r = p.add_run()
            r.text = "中央と右の揃え"
            r.font.size = Pt(24)
            _ja(r)
    _, rows = _rows(_deck(tmp_path, make), tmp_path)
    ctr, right = rows
    inner_l, inner_r = 72 + 7.2, 72 + 6 * 72 - 7.2
    # 右揃え：文字（段落記号の分を除く）の右端が使える幅の右端に来て、範囲は段落記号の分だけ外へ出る
    w_text = inner_r - right["tl"]
    assert 0 < w_text < right["tw"]
    assert right["tw"] == pytest.approx(ctr["tw"], abs=0.01)
    # 中央揃え：文字（段落記号の分を除く）の中心が、使える幅の中心に来る
    assert ctr["tl"] + w_text / 2 == pytest.approx((inner_l + inner_r) / 2, abs=0.01)


def test_round_rect_text_is_inset(tmp_path):
    """角丸の図形の文字は、角の丸みの分だけ内側に置かれる（プリセットの図形の text rect）。"""
    def make(s):
        for k, kind in enumerate((MSO_SHAPE.RECTANGLE, MSO_SHAPE.ROUNDED_RECTANGLE)):
            sh = s.shapes.add_shape(kind, Inches(1 + 5 * k), Inches(1), Inches(4), Inches(2))
            tf = sh.text_frame
            tf.vertical_anchor = MSO_ANCHOR.TOP
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT
            r = p.add_run()
            r.text = "角の内側"
            r.font.size = Pt(20)
            _ja(r)
    _, rows = _rows(_deck(tmp_path, make), tmp_path)
    rect, rr = rows
    inset = 2 * 72 * 0.16667 * 0.29289      # 既定の丸み 16.667%（短い辺に対して）× (1 − 1/√2)
    assert rect["tl"] - rect["left"] == pytest.approx(7.2, abs=0.01)
    assert rr["tl"] - rr["left"] == pytest.approx(7.2 + inset, abs=0.05)
    assert rr["tt"] - rr["top"] == pytest.approx(3.6 + inset, abs=0.05)


def test_empty_paragraph_takes_previous_size(tmp_path):
    """endParaRPr の無い空の段落は、前の段落の字の大きさの行の高さになる（PowerPoint の実測）。"""
    def make(s):
        tb = s.shapes.add_textbox(Inches(1), Inches(1), Inches(5), Inches(3))
        tf = tb.text_frame
        tf.word_wrap = False
        for i, t in enumerate(["上の段落", "", "下の段落"]):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            if t:
                r = p.add_run()
                r.text = t
                r.font.size = Pt(28)
                _ja(r)
    _, rows = _rows(_deck(tmp_path, make), tmp_path)
    assert rows[0]["lines"] == 3 and rows[0]["th"] == pytest.approx(3 * 28 * 1.2, abs=0.01)


def test_images_and_slide_number(tmp_path):
    """画像を描く。スライド番号の欄は番号そのもの。"""
    def make(s):
        tb = s.shapes.add_textbox(Inches(1), Inches(1), Inches(4), Inches(1))
        tb.text_frame.text = "Hello"
        s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(6), Inches(2), Inches(2), Inches(2))
        s.shapes.add_connector(1, Inches(1), Inches(5), Inches(8), Inches(6))
    p = _deck(tmp_path, make)
    js = rp.render(p, tmp_path / "render", width=800)
    from PIL import Image
    im = Image.open(tmp_path / "render" / "slide-01.png")
    assert im.size == (800, 450)
    lo, hi = im.convert("L").getextrema()
    assert lo < 128 < hi                                     # 白一色ではない


def test_examples_render_like_powerpoint(built, tmp_path, capsys):
    """講座の見本を新しい描画で描くと、PowerPoint と同じく ERROR 0（作者の手元で PowerPoint と突き合わせたときの結果）。"""
    for pptx, n in ((built / "examples" / "course" / "AI活用講座" / "01_生成AIは何をしているか_スライド.pptx", 15),):
        out = tmp_path / pptx.stem
        r = subprocess.run([sys.executable, "-X", "utf8", str(rp.__file__), "-Pptx", str(pptx), "-OutDir", str(out)],
                           capture_output=True, text=True, encoding="utf-8", timeout=300)
        assert r.returncode == 0, r.stderr
        data = json.loads((out / "shapes.json").read_text(encoding="utf-8"))
        assert data["engine"] == "python" and data["slides"] == n
        assert len(list(out.glob("slide-*.png"))) == n
        # 全ての文字の図形に範囲がある（ps1 と同じく、表・グループの中は対象外）
        assert all(s["tw"] is not None for s in data["shapes"] if s["text"])
        capsys.readouterr()
        assert check_layout.main(str(out / "shapes.json"), str(pptx)) == 0
        out_text = capsys.readouterr().out
        assert "0 errors" in out_text and "LibreOffice" not in out_text   # PowerPoint と同じ基準（ゆるめの補正なし）


def test_make_deck_uses_python_render(built):
    """make_deck は PowerPoint で確かめずに（--no-pp）新しい描画だけで最後まで回る。"""
    w = built / "examples" / "course" / "_work" / "AI活用講座_01"
    r = subprocess.run([sys.executable, "-X", "utf8", str(built / "scripts" / "make_deck.py"), str(w), "--no-pp", "--over"],
                       capture_output=True, text=True, encoding="utf-8", timeout=600)
    assert "描いた（新しい描画" in r.stdout, r.stdout + r.stderr
    data = json.loads((w / "render" / "shapes.json").read_text(encoding="utf-8"))
    assert data["engine"] == "python"
    assert list((w / "render").glob("grid-*.jpg"))


def test_make_deck_compares_layout_items(tmp_path):
    a = "--- slide 2\n  [ERROR] 重なり: A × B → 直す\n--- slide 3\n  [WARN] 行が長い → 削る"
    b = "--- slide 3\n  [WARN] 行が長い → 削る"
    assert make_deck.layout_items(a) == [(2, "ERROR", "重なり: A × B"), (3, "WARN", "行が長い")]
    assert make_deck.layout_items(b) == [(3, "WARN", "行が長い")]
    rows = lambda n: [{"slide": 1, "name": "本文", "text": "x", "lines": n}]   # noqa: E731
    (tmp_path / "a.json").write_text(json.dumps({"shapes": rows(2)}), encoding="utf-8")
    (tmp_path / "b.json").write_text(json.dumps({"shapes": rows(3)}), encoding="utf-8")
    assert make_deck.line_diffs(tmp_path / "a.json", tmp_path / "b.json") == ["スライド 1「本文」の行数：PowerPoint 2行・新しい描画 3行"]


def test_notes_html_images_without_powerpoint(built):
    """PowerPoint も LibreOffice も無い PC では、原稿のページの画像を新しい描画で作る。"""
    import notes_html
    imgs = notes_html.python_images(built / "examples" / "zemi" / "重力波の初観測_スライド.pptx", width=400)
    assert len(imgs) == 16 and all(len(x) > 1000 for x in imgs)


def test_math_box_in_alternate_content_is_kept(tmp_path):
    """PowerPoint で数式を入れた文字の枠は mc:AlternateContent に包まれる（python-pptx の slide.shapes は飛ばす）。
    手作りのデッキでこの枠が丸ごと抜け、重なり・はみ出しを見落としていた。Choice の側の枠を、数式の字も入れて数える。"""
    import copy
    from lxml import etree

    def make(s):
        tb = s.shapes.add_textbox(Inches(1), Inches(1), Inches(4), Inches(0.6))
        tb.text_frame.word_wrap = False
        r = tb.text_frame.paragraphs[0].add_run()
        r.text = "速さ"
        r.font.size = Pt(20)
        _ja(r)
        s.shapes.add_textbox(Inches(1), Inches(3), Inches(4), Inches(0.6)).text_frame.text = "ふつうの枠"

    p = _deck(tmp_path, make)
    prs = Presentation(str(p))
    slide = prs.slides[0]
    sp = slide.shapes[0]._element
    MC = "http://schemas.openxmlformats.org/markup-compatibility/2006"
    A14 = "http://schemas.microsoft.com/office/drawing/2010/main"
    M = "http://schemas.openxmlformats.org/officeDocument/2006/math"
    para = sp.find(".//{http://schemas.openxmlformats.org/drawingml/2006/main}p")
    m = etree.SubElement(para, f"{{{A14}}}m")
    om = etree.SubElement(m, f"{{{M}}}oMath")
    mr = etree.SubElement(om, f"{{{M}}}r")
    rpr = etree.SubElement(mr, "{http://schemas.openxmlformats.org/drawingml/2006/main}rPr", sz="2000")
    etree.SubElement(rpr, "{http://schemas.openxmlformats.org/drawingml/2006/main}latin", typeface="Cambria Math")
    etree.SubElement(mr, f"{{{M}}}t").text = "𝑣=𝑑/𝑡"
    para.remove(m)
    para.insert(len(para) - 1 if para[-1].tag.endswith("endParaRPr") else len(para), m)
    tree = sp.getparent()
    ac = etree.Element(f"{{{MC}}}AlternateContent")
    choice = etree.SubElement(ac, f"{{{MC}}}Choice", Requires="a14")
    fb = etree.SubElement(ac, f"{{{MC}}}Fallback")
    tree.replace(sp, ac)
    choice.append(sp)
    fb.append(copy.deepcopy(sp))
    prs.save(str(p))
    assert len(Presentation(str(p)).slides[0].shapes) == 1   # python-pptx は数式の枠を飛ばす
    js, rows = _rows(p, tmp_path)
    assert [r["text"] for r in js["shapes"]] == ["速さ𝑣=𝑑/𝑡", "ふつうの枠"]   # XML の順。数式の字も入る
    math = rows[0]
    assert math["lines"] == 1 and math["tw"] > 0


def test_picture_ink_found_by_position_when_names_differ():
    """PowerPoint は日本語の既定の名前（図 23）を英語（Picture 23）で返す。名前が違っても、位置が同じなら同じ画像として測る。"""
    inks = [("図 23", 100.0, 50.0, 60.0, 120.0, 900.0, 110.0, 200.0)]
    s = {"name": "Picture 23", "left": 100.5, "top": 50.2, "width": 200.0, "height": 150.0, "type": check_layout.MSO_PICTURE}
    assert check_layout.ink_of(s, inks) == (60.0, 120.0, 900.0)
    assert check_layout.visible_rect(s, inks) == (110.0, 60.0, 200.0, 120.0)
