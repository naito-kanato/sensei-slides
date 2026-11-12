"""描画結果（shapes.json）からの検査。PowerPoint の代わりに、図形の位置を手で書いた shapes.json を渡す。"""
import json

import check_layout as cl

W, H = 960, 540


def box(slide, name, left, top, width, height, text="", size=20, ph=None, type_=17):
    return {"slide": slide, "name": name, "type": type_, "left": left, "top": top, "width": width, "height": height,
            "ph": ph, "text": text, "tl": left + 5, "tt": top + 3, "tw": width - 10, "th": height - 6,
            "lines": max(1, text.count("\r") + 1), "paras": max(1, text.count("\r") + 1), "size": size}


def run(tmp_path, shapes, capsys):
    f = tmp_path / "shapes.json"
    f.write_text(json.dumps({"slideWidth": W, "slideHeight": H, "slides": 1, "shapes": shapes}, ensure_ascii=False), encoding="utf-8")
    code = cl.main(str(f))
    return code, capsys.readouterr().out


def title():
    return box(1, "Title 1", 40, 20, 600, 60, "例：温度測定", size=44, ph=cl.PH_TITLE, type_=14)


def test_clean_slide_has_no_error(tmp_path, capsys):
    code, out = run(tmp_path, [title(), box(1, "TextBox 2", 72, 140, 400, 200, "熱平衡での占有確率\r低温：ほぼ全部が下の準位")], capsys)
    assert code == 0
    assert "0 errors" in out


def test_text_over_the_band_is_an_error(tmp_path, capsys):
    code, out = run(tmp_path, [title(), box(1, "TextBox 2", 72, 400, 400, 120, "下まで伸びた本文")], capsys)
    assert code == 1
    assert "青帯にかかっている" in out


def test_overlap_is_an_error(tmp_path, capsys):
    shapes = [title(), box(1, "TextBox 2", 72, 140, 400, 120, "本文"),
              box(1, "Picture 3", 300, 150, 300, 200, type_=cl.MSO_PICTURE)]
    code, out = run(tmp_path, shapes, capsys)
    assert code == 1 and "重なり" in out


def test_outside_the_slide_is_an_error(tmp_path, capsys):
    code, out = run(tmp_path, [title(), box(1, "TextBox 2", 700, 140, 300, 100, "右にはみ出す本文")], capsys)
    assert code == 1 and "スライド外にはみ出し" in out


def test_sentence_style_lines_are_found():
    items = [box(1, "TextBox 2", 72, 140, 400, 200, "温度は上がります\r低温で比熱が0\r上の準位へ進む")]
    assert cl.sentence_lines(items) == ["温度は上がります"]   # です・ます調
    assert cl.verb_lines(items) == ["上の準位へ進む"]         # 動詞の終止形


def test_question_slides_are_not_counted_for_amount():
    items = [box(1, "見出し", 40, 80, 300, 40, "●確認問題（1-1〜1-3）", size=24)]
    assert cl.is_qa_slide(items)


def test_body_amount_counts_only_body_text():
    items = [box(1, "TextBox 2", 72, 140, 400, 200, "あいう\rかきくけ"),
             box(1, "注記", 500, 140, 100, 30, "小さな注記", size=14)]
    assert cl.body_amount(items) == (7, 2, 4)


def test_cover_slides_are_not_body():
    """表紙・区切り（●見出しが無い）は、文字量・行長の目安を当てない（論文の表紙の書誌・DOI を本文として数えない）"""
    import check_layout as cl
    cover = [{"text": "Observation of Gravitational Waves"}, {"text": "Phys. Rev. Lett. 116, 061102 (2016)　CC BY 3.0\nDOI: 10.1103/PhysRevLett.116.061102"}]
    body = [{"text": "●重力波"}, {"text": "1916年 アインシュタインが予言"}]
    assert cl.is_cover_slide(cover) is True
    assert cl.is_cover_slide(body) is False


def table_cells(rows, cols, size=16):
    out = [box(1, "見出し", 40, 80, 300, 40, "●表の枚", size=24)]   # ●見出しの無い枚は表紙とみなされ、見ない
    out += [box(1, "表の見出し", 72 + 120 * c, 140, 110, 30, f"列{c}", size=17) for c in range(cols)]
    for r in range(rows):
        out += [box(1, "表のセル", 72 + 120 * c, 175 + 32 * r, 110, 30, f"中身{r}{c}", size=size) for c in range(cols)]
    return out


def test_small_table_text_is_warned(tmp_path, capsys):
    _, out = run(tmp_path, [title()] + table_cells(3, 3, size=12), capsys)
    assert "表の文字が小さい" in out
    _, out = run(tmp_path, [title()] + table_cells(3, 3, size=16), capsys)
    assert "表の文字が小さい" not in out and "表のマスが多い" not in out


def test_crowded_table_is_warned(tmp_path, capsys):
    _, out = run(tmp_path, [title()] + table_cells(5, 5), capsys)   # 25 マス
    assert "表のマスが多い" in out


def test_small_text_in_figure_is_warned(tmp_path):
    """figkit.save が書いた MinFontPt と縮尺から、置いた大きさでの図の文字を見る。"""
    import figkit
    from pptx import Presentation
    from pptx.util import Inches
    paths = {}
    for size in (12, 16):
        f, ax = figkit.fig(4.0, 3.0)
        ax.plot([0, 1], [0, 1])
        ax.tick_params(labelsize=size)
        paths[size] = tmp_path / f"f{size}.png"
        figkit.save(f, paths[size])
    prs = Presentation()
    for size in (12, 16):
        s = prs.slides.add_slide(prs.slide_layouts[6])
        s.shapes.add_picture(str(paths[size]), Inches(1), Inches(1))
    pptx = tmp_path / "d.pptx"
    prs.save(pptx)
    fonts = cl.picture_fonts(pptx)
    assert fonts[1][0][1] == 12.0 and abs(fonts[1][0][2] - 1.0) < 0.05
    assert fonts[2][0][1] == 16.0
