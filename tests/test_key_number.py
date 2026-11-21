"""大きな数字（範囲・単位・限定まで）と、原稿から読み上げない物を外す所。"""
import pytest
from pptx import Presentation

import scaffold
from zemi import Deck


@pytest.mark.parametrize("cell,full,short", [
    ("印象：大きな数字：60〜90%程度以上（南海トラフ地震の30年以内・2025年9月時点）", "60〜90%程度以上", "60〜90%"),
    ("印象：大きな数字：ほぼ0〜0.9%（熊本地震前の30年確率）〔事実1〕", "ほぼ0〜0.9%", "0〜0.9%"),
    ("印象：大きな数字：8割以上（死者のうち）", "8割以上", "8割"),
    ("印象：大きな数字：17%（手放した報酬）", "17%", "17%"),
    ("印象：大きな数字：3人に1人（x）", "3人に1人", "3人に1人"),
    ("印象：大きな数字：5.1σ 以上（偶然なら）", "5.1σ 以上", "5.1σ"),
])
def test_key_number_keeps_range_unit_and_qualifier(cell, full, short):
    """大きな数字は、範囲・単位・限定（ほぼ・程度以上・以上）まで載せる。地震の比べで「60」「0」だけになった。"""
    h, _ = scaffold._head_inner(scaffold._fig_body(cell))
    assert scaffold.key_number(h) == (full, short)
    code = scaffold.key_message_code(cell)
    assert f's.key_message("{full}"' in code and ((f'short="{short}"' in code) == (short != full))


def test_key_message_falls_back_to_number_and_unit_when_too_wide(tmp_path):
    """全体が横の場所に入らないときだけ、数字＋単位を大きく出し、全体は説明の頭に回す（限定を落とさない）。"""
    d = Deck(workdir=tmp_path / "build")
    d.title_slide(["大きな数字"])
    s = d.slide("型", summary="入る"); s.heading("入る"); s.key_message("60〜90%程度以上", "南海トラフ", short="60〜90%")
    long_ = "約1,234,567,890,123億円程度以上"
    s = d.slide("型", summary="入らない"); s.heading("入らない"); s.key_message(long_, "例", short="1,234,567,890,123億円")
    out = tmp_path / "km.pptx"
    d.save(out)
    slides = list(Presentation(out).slides)[1:]
    texts = [{sh.name: sh.text_frame.text for sh in sl.shapes if sh.has_text_frame} for sl in slides]
    assert texts[0]["大きな数字"] == "60〜90%程度以上" and texts[0]["大きな数字の説明"] == "南海トラフ"
    assert texts[1]["大きな数字"] == "1,234,567,890,123億円" and texts[1]["大きな数字の説明"].startswith(long_)


def test_notes_drop_fact_tags_and_memo_lines():
    """原稿を notes.md に入れるとき、〔事実N〕の印と「※（メモ）」の行を外す（地震の試しで原稿に残り、採点者2人が減点した）。"""
    import scaffold
    assert scaffold.spoken("前兆は確かめられていません〔事実17〕。\n※（メモ）原資料は開いていない\n※（出典）気象庁 2019\n次へ") == \
        "前兆は確かめられていません。\n※（出典）気象庁 2019\n次へ"


def test_points_drop_data_marks():
    """要点の「（データN）」はスライドに出さない（地震の試しで本文に残り、採点者2人が減点した）。"""
    assert scaffold.items_of("最短：12年（データ1）／最長：38年（データ1・2）〔事実3〕") == ["最短：12年", "最長：{r:38年}"]   # ★が無い枚は、事実の印の付いた要点の数値を赤字に
