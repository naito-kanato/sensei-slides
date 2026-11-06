"""Codex の試作（睡眠講座 第1回）で見つかった抜け：赤字0か所・比較の枚の薄さ・行数で削らせる警告・要点2個の設計メモ・表の見出しのずれ。"""
import json

import pytest
from pptx import Presentation

import check_layout as cl
import check_memo
from zemi import Deck

W, H = 960, 540


def box(slide, name, left, top, width, height, text="", size=20, ph=None, type_=17):
    return {"slide": slide, "name": name, "type": type_, "left": left, "top": top, "width": width, "height": height,
            "ph": ph, "text": text, "tl": left + 5, "tt": top + 3, "tw": width - 10, "th": height - 6,
            "lines": max(1, text.count("\r") + 1), "paras": max(1, text.count("\r") + 1), "size": size}


def run(tmp_path, shapes, capsys, slides=1, pptx=None):
    f = tmp_path / "shapes.json"
    data = {"slideWidth": W, "slideHeight": H, "slides": slides, "shapes": shapes}
    if pptx:
        data["pptx"] = str(pptx)
    f.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    cl.main(str(f))
    return capsys.readouterr().out


def title(i=1):
    return box(i, "Title 1", 40, 20, 600, 60, "例", size=44, ph=cl.PH_TITLE, type_=14)


def heading(i=1):
    return box(i, "見出し", 40, 85, 500, 36, "見出し", size=28)


def test_compare_slide_is_checked_for_thin_text(tmp_path, capsys):
    """左右に1語ずつの比較の枚（17字）が「少ない」の検査から外れていた。"""
    out = run(tmp_path, [title(), heading(), box(1, "比較の左", 72, 140, 300, 40, "推奨時間の違い"),
                         box(1, "比較の右", 500, 140, 300, 40, "必要時間の幅")], capsys)
    assert "本文が少ない" in out


def test_line_count_alone_does_not_ask_to_cut_a_thin_slide():
    """66字・9行の枚に「目安を超えている」と出て、制作役が削っていた。目安の下端（80字）より少なければ行数だけでは超えにしない。"""
    assert not cl.over_target(66, 11)
    assert cl.over_target(120, 11) and cl.over_target(190, 5)
    assert not cl.over_target(150, 9)       # 目安（100〜150字）の中は通す


def test_deck_median_warns_when_whole_deck_is_thin(tmp_path, capsys):
    shapes = []
    for i in range(1, 6):
        shapes += [title(i), heading(i), box(i, "TextBox 2", 72, 140, 400, 200, "あ" * 66)]
    out = run(tmp_path, shapes, capsys, slides=5)
    assert "デッキ全体の本文が薄い" in out
    shapes = []
    for i in range(1, 6):
        shapes += [title(i), heading(i), box(i, "TextBox 2", 72, 140, 400, 200, "あ" * 110)]
    assert "デッキ全体の本文が薄い" not in run(tmp_path, shapes, capsys, slides=5)


def test_red_colors_of_all_palettes_are_found():
    for c in ("FF0000", "C00000", "C8102E", "D62D20", "C62828", "B42318", "C0392B", "B23A48"):
        assert cl.is_red(c), c
    for c in ("545455", "213CFF", "215F99", "8C8C8C", "FBE3D6", "4E95D9"):
        assert not cl.is_red(c), c


def _deck(tmp_path, with_red):
    d = Deck(workdir=tmp_path / "build")
    d.title_slide(["題"], author="名前")
    s = d.slide("題", summary="結論の一文をここに書く")
    s.heading("見出し")
    s.at(1.0, 2.0)
    s.block("要点：", ["{r:一番言いたい語句}" if with_red else "一番言いたい語句", "根拠の数値 42%"])
    out = tmp_path / ("red.pptx" if with_red else "plain.pptx")
    d.save(out, title="題", author="名前")
    return out


def test_red_counts_from_pptx(tmp_path):
    assert cl.red_counts(_deck(tmp_path, True))[2] >= 1
    assert cl.red_counts(_deck(tmp_path, False))[2] == 0


def test_body_slide_without_red_is_warned(tmp_path, capsys):
    pptx = _deck(tmp_path, False)
    shapes = [box(1, "TextBox 1", 100, 150, 700, 80, "題", size=40), box(1, "TextBox 2", 300, 260, 300, 30, "名前"),
              title(2), heading(2), box(2, "TextBox 2", 72, 140, 400, 200, "あ" * 90)]
    out = run(tmp_path, shapes, capsys, slides=2, pptx=pptx)
    assert "赤字が無い" in out


def test_memo_with_two_points_per_row_is_an_error():
    head = ["#", "●見出し", "青帯（結論）", "図で見せるもの", "本文の要点", "ノートへ", "本文の形", "役割"]
    thin = [head] + [[str(i), f"見出し{i}", "結論", "図", "要点A★／要点B", "", "箇条", "本文"] for i in range(2, 8)]
    rich = [head] + [[str(i), f"見出し{i}", "結論", "図", "要点A★／根拠 42%／よくある間違い", "", "箇条", "本文"] for i in range(2, 8)]
    assert check_memo.thin_points(thin)[0] == "✘"
    assert check_memo.thin_points(rich)[0] == "✔"
    qa = [head] + [[str(i), "確認問題", "—", "—", "1問", "", "—", "確認問題"] for i in range(2, 8)]
    assert check_memo.thin_points(qa) is None     # 本文の行が無ければ見ない


def test_table_header_for_the_label_column(tmp_path):
    """行ラベル列の見出しまで渡すと1列ずれていた（「年齢」が値の列の上、「推奨時間」の下が空）。"""
    d = Deck(workdir=tmp_path / "build")
    s = d.slide("題", summary="結論の一文をここに書く")
    s.table(6.6, 2.0, 1.5, 0.9, ["年齢", "推奨時間"], [("18〜60歳", ["7時間以上"]), ("65歳以上", ["7〜8時間"])], label_w=1.6)
    out = tmp_path / "t.pptx"
    d.save(out, title="題", author="名前")
    sl = Presentation(str(out)).slides[0]
    pos = {sh.text_frame.text: sh.left for sh in sl.shapes if sh.has_text_frame and sh.text_frame.text in ("年齢", "推奨時間", "18〜60歳", "7時間以上")}
    assert pos["年齢"] == pos["18〜60歳"]          # 行ラベル列の見出しは行ラベルの真上
    assert pos["推奨時間"] == pos["7時間以上"]      # 値の列の見出しは値の真上


def test_table_mismatch_is_an_error(tmp_path):
    d = Deck(workdir=tmp_path / "build")
    s = d.slide("題", summary="結論の一文をここに書く")
    with pytest.raises(ValueError, match="合わない"):
        s.table(6.6, 2.0, 1.4, 0.75, ["項目", "月曜", "火曜", "水曜"], [("昼寝", ["なし", "あり"])], label_w=1.5)
    with pytest.raises(ValueError, match="合わない"):
        s.table(6.6, 2.0, 1.4, 0.75, ["月曜", "火曜"], [("昼寝", ["なし"]), ("起床", ["7時", "8時"])], label_w=1.5)


def test_table_text_is_not_counted(tmp_path):
    """表のセルの短い語（「7時間以上」「なし」など）で字数が増え、本文の薄い枚が通っていた。表の文字は数えない。"""
    d = Deck(workdir=tmp_path / "build")
    s = d.slide("題", summary="結論の一文をここに書く")
    s.table(6.6, 2.0, 1.5, 0.9, ["年齢", "推奨時間"], [("18〜60歳", ["7時間以上"]), ("65歳以上", ["7〜8時間"])], label_w=1.6)
    out = tmp_path / "t.pptx"
    d.save(out, title="題", author="名前")
    names = {sh.name for sh in Presentation(str(out)).slides[0].shapes}
    assert {"表の見出し", "表の行ラベル", "表のセル"} <= names
    items = [box(1, n, 500, 140, 100, 40, "あいうえおかきくけこ") for n in ("表の見出し", "表の行ラベル", "表のセル")]
    assert cl.content_chars(items) == 0
    assert cl.content_chars(items + [box(1, "塊の本文", 72, 140, 300, 40, "あいうえお")]) == 5


def _memo(q_rows, n_questions):
    head = "| # | ●見出し | 青帯（結論） | 図で見せるもの | 本文の要点 | ノートへ | 本文の形 | 役割 |\n|---|---|---|---|---|---|---|---|\n"
    rows = "| 1 | 表紙 | — | — | 題 | — | — | 表紙 |\n| 2 | 見出し | 結論の一文 | 図 | A★／B／C | — | 箇条 | 本文 |\n" + q_rows
    qs = "\n".join(f"1-{k}. 問{k}" for k in range(1, n_questions + 1))
    return f"# 設計メモ：第1回 題\n\n## 2. 話の順番\n\n{head}{rows}\n## 6. 確認問題と模範解答\n\n### 問題\n{qs}\n\n### 解答\n{qs}\n\n## 7. 前の回から\n"


def test_quiz_plan_is_fixed_to_six_in_two_slides():
    import structures
    ok = ("| 3 | 確認問題（1-1〜1-3） | — | — | 1-1〜1-3 | — | — | 確認問題 |\n| 4 | 確認問題（1-4〜1-6） | — | — | 1-4〜1-6 | — | — | 確認問題 |\n"
          "| 5 | 解答（1-1〜1-3） | — | — | — | — | — | 解答 |\n| 6 | 解答（1-4〜1-6） | — | — | — | — | — | 解答 |\n")
    marks = {item: m for m, item, _ in structures.check_quiz_plan(_memo(ok, 6))}
    assert marks["確認問題"] == "✔"
    assert marks["確認問題のひもづけ"] == "△"      # 〔ゴールN・M枚目〕〔要素：…〕が無い
    marks = {item: m for m, item, _ in structures.check_quiz_plan(_memo(ok, 9))}
    assert marks.get("確認問題の数") == "✘"
    merged = "| 3〜8 | 確認問題①〜⑥ | — | — | 6問 | — | 問題 | 問題 |\n"
    marks = {item: m for m, item, _ in structures.check_quiz_plan(_memo(merged, 6))}
    assert marks.get("表の行") == "✘" and marks.get("確認問題の枚数") == "✘"


def _quiz_slide(i, head, ids):
    return [box(i, "見出し", 40, 85, 500, 36, head, size=24),
            box(i, "TextBox 2", 72, 160, 700, 200, "\r".join(f"{k}　問題の文" for k in ids))]


def test_deck_quiz_slides_are_checked():
    good = (_quiz_slide(1, "確認問題（1-1〜1-3）", ["1-1", "1-2", "1-3"]) + _quiz_slide(2, "確認問題（1-4〜1-6）", ["1-4", "1-5", "1-6"])
            + _quiz_slide(3, "解答（1-1〜1-3）", ["1-1", "1-2", "1-3"]) + _quiz_slide(4, "解答（1-4〜1-6）", ["1-4", "1-5", "1-6"]))
    assert cl.quiz_problems(good, 4) == []
    one_each = [s for k in range(1, 7) for s in _quiz_slide(k, f"確認問題（1-{k}）", [f"1-{k}"])]
    probs = cl.quiz_problems(one_each, 6)
    assert any("確認問題の枚が 6枚" in m for m in probs) and any("3問でない" in m for m in probs)
    assert cl.quiz_problems([box(1, "見出し", 40, 85, 500, 36, "結果", size=24)], 1) == []   # 確認問題の無いデッキ（発表）は見ない
