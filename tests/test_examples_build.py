"""同梱の見本（ゼミ examples/zemi・zemi_en、講座 examples/course・course_en）を一時フォルダに写して組み、できた pptx と原稿ページの中身を確かめる。"""

import pytest
from pptx import Presentation

import notes_html as nh

# 原稿ページの画像の代わり（build_html は base64 の文字列を埋め込むだけ。PowerPoint で PDF を書き出す部分はテストしない）
DUMMY_JPG = "AAAA"


def band_texts(prs):
    return [t[2] for t in nh.slide_texts(prs)]


def test_zemi_example_builds(built):
    pptx = built / "examples" / "zemi" / "Abbott2016_PRL116_061102_スライド.pptx"
    prs = Presentation(pptx)
    items = nh.slide_texts(prs)
    assert len(items) == 17                                          # 表紙＋本文14（まとめを含む）＋想定質問2
    assert items[1][1] == "重力波とひずみ h"                         # ●見出し
    assert items[1][2] == "重力波が 4 km の腕を伸ばす量は約 4×10⁻¹⁸ m"   # 青帯
    assert "1916年" in items[1][3]                                   # notes.md が発表者ノートに入っている
    assert "Observation of Gravitational Waves" in items[0][0]       # 表紙は論文の題
    assert items[15][2] == items[16][2] == "想定質問"


def test_zemi_paper_figures_have_sources(built):
    """論文から切り出した図のあるスライドには、出典の注記（著者・雑誌・図番号）が付いている"""
    prs = Presentation(built / "examples" / "zemi" / "Abbott2016_PRL116_061102_スライド.pptx")
    for i in (2, 3, 4, 6, 7, 10):                                    # 干渉計・雑音・工夫・結果①〜③（0 始まり。図は src/ の頁から切り出す）
        texts = [sh.text_frame.text for sh in prs.slides[i].shapes if sh.has_text_frame]
        assert any("Abbott ほか 2016, Fig." in t for t in texts), i
    prs = Presentation(built / "examples" / "zemi_en" / "Abbott2016_PRL116_061102_slides.pptx")
    for i in (6, 7, 8, 9, 13):                                       # 英語版：雑音・結果①〜③（paper_figs/ の切り出し）
        texts = [sh.text_frame.text for sh in prs.slides[i].shapes if sh.has_text_frame]
        assert any("Abbott et al., PRL 116, 061102 (2016), Fig." in t for t in texts), i


def test_course_example_builds_with_questions(built):
    folder = built / "examples" / "course" / "AI活用講座"
    pptx = folder / "01_生成AIは何をしているか_スライド.pptx"
    prs = Presentation(pptx)
    assert len(prs.slides) == 17                                    # 表紙＋本文12＋確認問題2＋解答2
    qs = nh.slide_questions(prs)
    assert [q for q, _ in qs[13]] == ["1-1", "1-2", "1-3"]         # 確認問題のスライドから3問ずつ
    assert [q for q, _ in qs[14]] == ["1-4", "1-5", "1-6"]
    assert qs[15] == [] and qs[16] == []                            # 解答のスライドにはボタンを出さない
    assert nh.course_id(pptx) == "AI"                               # README の講座ID
    assert nh.save_setting(pptx)[0] == "AI活用講座"                 # README の書き出しの保存先


def test_notes_page_has_answer_buttons_and_course_id(built):
    pptx = built / "examples" / "course" / "AI活用講座" / "01_生成AIは何をしているか_スライド.pptx"
    prs = Presentation(pptx)
    items = nh.slide_texts(prs)
    page = nh.build_html("第1回 生成AIは何をしているか", items, [DUMMY_JPG] * len(items), nh.slide_questions(prs),
                         nh.save_setting(pptx), nh.course_id(pptx))
    assert page.count('class="qa-btn"') == 6
    assert 'data-course-id="AI"' in page
    assert page.count("<section id=") == 17


def test_english_examples_build(built):
    """英語の見本：原稿の決まり文句（確認問題の前置き・解答の行）も英語になっている"""
    pptx = built / "examples" / "course_en" / "AI_Literacy" / "01_What Generative AI Actually Computes_slides.pptx"
    prs = Presentation(pptx)
    items = nh.slide_texts(prs)
    assert len(items) == 18                                          # 表紙＋本文13＋確認問題2＋解答2
    assert [q for q, _ in nh.slide_questions(prs)[14]] == ["1-1", "1-2", "1-3"]
    assert items[14][3].startswith("Review questions.") and "確認問題" not in items[14][3]
    assert "Recall what you saw on slide" in items[16][3]
    assert len(Presentation(built / "examples" / "zemi_en" / "Abbott2016_PRL116_061102_slides.pptx").slides) == 18


def test_structures_example_uses_every_part(built):
    """型の見本（examples/structures）：本文の形と図解の型を1枚ずつ。部品の名前で見分けられる"""
    import figplan
    import structures as stc
    prs = Presentation(built / "examples" / "structures" / "型の見本_スライド.pptx")
    forms = set().union(*(stc.detect_forms(sl) for sl in prs.slides))
    assert {"帰結", "ラベル", "展開", "場合分け", "問い", "手順", "縦の結論"} <= forms
    types = {figplan.slide_type(sl, prs.slide_width, prs.slide_height) for sl in prs.slides}
    assert {"並列カード", "段違いの順序", "循環", "ツリー", "前後", "2つ並べた図", "区切り"} <= types
