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


def test_small_boxes_with_large_margins_are_errors(tmp_path, capsys):
    """箱の型の枚：箱が小さく余白が大きいと ERROR（下が空く形として見逃し、寂しく見えた）。"""
    head = box(1, "見出し", 40, 60, 600, 30, "●並列カード", size=24)
    small = [box(1, f"カード_並列", 60 + k * 290, 200, 270, 90, "見出し\r説明") for k in range(3)]
    code, out = run(tmp_path, [title(), head] + small, capsys)
    assert code == 1 and "箱の図のまわりが空いている" in out
    tall = [box(1, f"カード_並列", 60 + k * 290, 130, 270, 300, "見出し\r説明\r\r62") for k in range(3)]
    code, out = run(tmp_path, [title(), head] + tall, capsys)
    assert "箱の図のまわりが空いている" not in out and "箱が小さい" not in out
    thin = [box(1, "比較の左", 60, 120, 200, 60, "A\r2行"), box(1, "比較の右", 400, 120, 200, 60, "B\r2行"),
            box(1, "TextBox 9", 60, 300, 800, 120, "Re-ask:\rsame question\rNumbers:\rrecompute")]
    code, out = run(tmp_path, [title(), head] + thin, capsys)
    assert "箱が小さい" in out and "比較の列が短い" in out
    # 比較は各列3行なら、文字の枠が細くても「箱が小さい」にしない（面積の目安は各列4行が要り、行数の目安とぶつかった）
    three = [box(1, "比較の左", 60, 120, 200, 130, "A\r2行\r3行"), box(1, "比較の右", 400, 120, 200, 130, "B\r2行\r3行"),
             box(1, "TextBox 9", 60, 300, 800, 120, "Re-ask:\rsame question\rNumbers:\rrecompute")]
    code, out = run(tmp_path, [title(), head] + three, capsys)
    assert "箱が小さい" not in out


def test_many_text_units_are_errors(tmp_path, capsys):
    """1枚の文の塊：3つで WARN、4つ以上で ERROR（言いたいことは1枚に1つ）。"""
    head = box(1, "見出し", 40, 60, 600, 30, "●結果", size=24)
    blocks = []
    for k in range(4):
        blocks += [box(1, "塊の見出し", 60, 110 + k * 95, 300, 30, f"ラベル{k}："), box(1, "塊の本文", 85, 140 + k * 95, 300, 30, "説明")]
    code, out = run(tmp_path, [title(), head] + blocks, capsys)
    assert "文の塊が多い（4 つ" in out
    code, out = run(tmp_path, [title(), head] + blocks[:6], capsys)
    assert "文の塊が 3 つ" in out and "文の塊が多い" not in out


def test_figure_position_words_must_match(tmp_path, capsys):
    head = box(1, "見出し", 40, 60, 600, 30, "●結果", size=24)
    fig = box(1, "Picture 3", 100, 300, 700, 180, "", type_=13)
    text = box(1, "TextBox 2", 60, 110, 500, 80, "右の図：H1 を反転して重ねる")
    code, out = run(tmp_path, [title(), head, fig, text], capsys)
    assert "「右の図」と言うが" in out
    text = box(1, "TextBox 2", 60, 110, 500, 80, "下の図：H1 を反転して重ねる")
    code, out = run(tmp_path, [title(), head, fig, text], capsys)
    assert "の図」と言うが" not in out
    import check_layout as cl2
    assert not cl2.WHERE_WORDS[0][1].search("In the right panel, blue is L1")   # 図の中のパネルは数えない


def test_red_fills_are_warned(capsys, tmp_path):
    import figkit as fk
    f, ax = fk.fig(5, 3)
    ax.bar([0, 1], [1, 2], color=fk.COL.red)
    fk.save(f, tmp_path / "r.png")
    assert "原色の赤の塗り" in capsys.readouterr().out
    f, ax = fk.fig(5, 3)
    ax.bar([0, 1], [1, 2], color=fk.COL.dred)
    ax.plot([0, 1], [1, 2], color=fk.COL.red)
    fk.save(f, tmp_path / "r2.png")
    assert "原色の赤の塗り" not in capsys.readouterr().out


def test_many_boxes_are_warned(tmp_path, capsys):
    """箱が5個以上か、本文の場所の半分を超えると WARN（目線が散る）。4個までの小さな箱は通す。"""
    head = box(1, "見出し", 40, 60, 600, 30, "●手順", size=24)
    four = [box(1, "Rounded Rectangle 5", 60 + k * 210, 200, 180, 80, f"段{k}", type_=1) for k in range(4)]
    code, out = run(tmp_path, [title(), head] + four, capsys)
    assert "箱が多い・広い" not in out
    six = [box(1, "判定の問い", 60 + (k % 3) * 280, 150 + (k // 3) * 120, 250, 90, f"問{k}", type_=1) for k in range(6)]
    code, out = run(tmp_path, [title(), head] + six, capsys)
    assert "箱が多い・広い（6 個" in out


def test_one_long_block_or_lonely_line_is_warned(tmp_path, capsys):
    """文の塊は釣り合う2つが基本。長い塊が1つだけ・長い塊＋1〜2行の塊は WARN。"""
    head = box(1, "見出し", 40, 60, 600, 30, "●結果", size=24)
    long1 = [box(1, "塊の見出し", 60, 110, 300, 30, "ラベル："), box(1, "塊の本文", 85, 140, 400, 160, "a\rb\rc\rd\re", )]
    for s in long1[1:]:
        s["paras"] = 5
    code, out = run(tmp_path, [title(), head] + long1, capsys)
    assert "文が1つの塊で長い" in out
    lonely = long1 + [box(1, "TextBox 9", 60, 340, 400, 30, "⇒ 結論")]
    code, out = run(tmp_path, [title(), head] + lonely, capsys)
    assert "短い塊が、長い塊に付いている" in out


def test_figure_numbers_repeated_in_text_are_found(tmp_path):
    """figkit が図の中の文字を PNG に書き、本文と同じ数字（2つ以上）を見つける（図と文の二重）。"""
    import figkit
    from pptx import Presentation
    from pptx.util import Inches
    f, ax = figkit.fig(4.0, 3.0)
    ax.bar([0, 1], [22, 75])
    ax.text(0, 22, "22%"); ax.text(1, 75, "75%")
    png = tmp_path / "f.png"
    figkit.save(f, png)
    prs = Presentation()
    s = prs.slides.add_slide(prs.slide_layouts[6])
    s.shapes.add_picture(str(png), Inches(1), Inches(1))
    pptx = tmp_path / "d.pptx"
    prs.save(pptx)
    ft = cl.figure_texts(pptx)
    assert "22%" in ft[1] and "75%" in ft[1]
    assert cl._nums("誤答は 22% と 75%、3倍") & cl._nums(ft[1]) == {"22%", "75%"}


def test_quiz_text_small_or_long_is_warned(tmp_path, capsys):
    head = box(1, "見出し", 40, 60, 600, 30, "●確認問題（1-1〜1-3）", size=24)
    long_q = box(1, "TextBox 3", 60, 120, 820, 90,
                 "1-1 生成AIが文を作る仕組みを、事前学習・調整・トークン・確率の4つの語を使って、学習の2段階と1語ごとの計算の両方が分かるように説明してください。", size=20)
    code, out = run(tmp_path, [title(), head, long_q], capsys)
    assert "確認問題・解答の字が小さい" in out and "確認問題・解答の1つが長い" in out
