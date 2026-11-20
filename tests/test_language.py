"""出力の言語（設定の「言語」）：スライド・原稿・原稿のページをその言語で作り、検査の目安を言語に合わせる。"""
import json
import re

import brief
import cards
import check_layout as cl
import check_notes
import language as LG
import notes_html
import slide_profile as sp
import zemi

W, H = 960, 540


def test_names_codes_and_width():
    assert LG.lang_name("") == "日本語" and LG.lang_name("English") == "英語" and LG.lang_name("英語（スライドと原稿）") == "英語"
    assert LG.lang_name("日本語（スライド・原稿・確認問題）。16:9") == "日本語"   # 注記のあとに文が続いても先頭の語で読む（英語の名前で組まれた）
    assert LG.lang_name("中国語（繁体字）") == "中国語（繁体字）" and LG.lang_name("English (slides). 16:9") == "英語"
    assert LG.lang_code("英語") == "en-US" and LG.lang_code("en") == "en-US" and LG.lang_code("日本語") == "ja-JP"
    assert LG.lang_code("スワヒリ語") == "en-US"                       # 知らない言語も作れる（つづりの検査は英語）
    assert LG.name_of_code("en-US") == "英語" and LG.name_of_code("") == "日本語"   # 印の無い今までのデッキは日本語
    assert LG.measure("重力 波", "日本語") == 3                         # 日本語は今までどおり（空白を除いた字数）
    assert LG.measure("Wave seen", "英語") == 4.5                      # 半角は0.5（空白も）
    assert LG.spaced("英語") and not LG.spaced("中国語")


def test_sentence_lines_and_quiz_headings():
    assert LG.is_sentence("The model cannot see the source.", "英語")
    assert not LG.is_sentence("No access to the source", "英語")
    assert not LG.is_sentence("Abbott et al.", "英語") and not LG.is_sentence("Done.", "英語")
    assert LG.quiz_kind("Review Questions (1-1 to 1-3)") == "確認問題" and LG.quiz_kind("Answers (1-1 to 1-3)") == "解答"
    assert LG.quiz_kind("●確認問題（1-1〜1-3）") == "確認問題" and LG.quiz_kind("●解答（1-1〜1-3）") == "解答"
    assert LG.quiz_kind("How to Ask") is None


def test_option_row_and_deck_options(tmp_path):
    assert "| 言語 | 日本語 |" in sp.options_table(kind="講座")
    (tmp_path / "outline.md").write_text("## オプション\n\n| オプション | 今の値 |\n|---|---|\n| 言語 | English |\n", encoding="utf-8")
    p = sp.load_profile(tmp_path)
    assert sp.language(p) == "英語" and sp.deck_options(p)["lang"] == "英語"
    assert "lang" not in sp.deck_options({})                           # 日本語なら渡さない（今までの build.py と同じ）


def test_deck_marks_language_and_uses_its_words(tmp_path):
    deck = zemi.Deck(workdir=tmp_path / "build", lang="英語")
    s = deck.slide("Rules", summary="Two questions decide it")
    s.heading("How to Decide")
    s.decision([("Is it for enjoyment?", "Permission needed")], "Free to use")
    s.defs(1.0, 5.0, [("x", "position")])
    out = tmp_path / "d.pptx"
    deck.save(out)
    from pptx import Presentation
    prs = Presentation(str(out))
    assert prs.core_properties.language == "en-US"
    texts = [sh.text_frame.text for sh in prs.slides[0].shapes if sh.has_text_frame]
    assert "Yes" in texts and "No" in texts and "はい" not in texts
    assert any(t.startswith("x: position") for t in texts)
    langs = set(re.findall(r'lang="([^"]+)"', prs.slides[0].shapes._spTree.xml))
    assert "en-US" in langs and "ja-JP" not in langs
    assert zemi.wrap_to("Plausible content that is false or has no basis", 3.0, 20).count("\n") == 1
    assert "\n " not in zemi.wrap_to("Plausible content that is false or has no basis", 3.0, 20)


def box(name, left, top, width, height, text="", size=20, ph=None, type_=17):
    return {"slide": 1, "name": name, "type": type_, "left": left, "top": top, "width": width, "height": height,
            "ph": ph, "text": text, "tl": left + 5, "tt": top + 3, "tw": width - 10, "th": height - 6,
            "lines": max(1, text.count("\r") + 1), "paras": max(1, text.count("\r") + 1), "size": size}


def layout(tmp_path, capsys, monkeypatch, body, head="● How to Decide", lang="英語"):
    monkeypatch.setattr(cl, "LANG", cl.LANG)   # main が変える言語を、テストのあとに戻す
    shapes = [box("Title 1", 40, 20, 600, 60, "Rules", size=44, ph=cl.PH_TITLE, type_=14),
              box("見出し", 40, 90, 600, 40, head, size=24), box("TextBox 2", 72, 140, 400, 200, body)]
    f = tmp_path / "shapes.json"
    f.write_text(json.dumps({"slideWidth": W, "slideHeight": H, "slides": 1, "shapes": shapes}, ensure_ascii=False), encoding="utf-8")
    cl.main(str(f), lang=lang)
    return capsys.readouterr().out


def test_layout_counts_width_and_sentences_for_english(tmp_path, capsys, monkeypatch):
    body = "Large language model:\rLearns which words tend to follow\rPicks tokens by probability"
    out = layout(tmp_path, capsys, monkeypatch, body)
    assert "言語：英語" in out
    assert "1行が長い" not in out and "動詞で終わる" not in out and "文の形の行" not in out
    out = layout(tmp_path, capsys, monkeypatch, "The model cannot see the source.\rIt only predicts the next token.")
    assert "文の形の行が 2 行" in out
    out = layout(tmp_path, capsys, monkeypatch, "A very long line of English text that keeps going past the line limit here")
    assert "1行が長い" in out                                        # 半角74字 → 全角37 > 25
    out = layout(tmp_path, capsys, monkeypatch, "The model cannot see the source.", head="● Review Questions (1-1 to 1-3)")
    assert "文の形の行" not in out and "（問題・解答）" in out          # 確認問題の枚には目安を当てない


def test_layout_japanese_is_unchanged(tmp_path, capsys, monkeypatch):
    out = layout(tmp_path, capsys, monkeypatch, "熱平衡での占有確率\r低温ではほぼ全部が下の準位にいる\r温度とともに上の準位へ移る", head="●占有確率", lang=None)
    assert "（言語：" not in out and "文章調の行が 1 行" in out and "動詞で終わる行が 1 行" in out


def test_notes_are_counted_in_words(tmp_path):
    plan = "## オプション\n\n| 項目 | 値 |\n|---|---|\n| 言語 | 英語 |\n| 発表時間 | 1分 |\n"
    (tmp_path / "outline.md").write_text(plan, encoding="utf-8")
    long = " ".join(["word"] * 45) + "."
    (tmp_path / "notes.md").write_text("## 1\n" + " ".join(["Gravitational waves stretch space."] * 37) + "\n\n## 2\n" + long + "\nNext slide.\n",
                                       encoding="utf-8")
    res = {item: (m, msg) for m, item, msg in check_notes.check(tmp_path)}
    assert res["原稿の1文の長さ"][0] == "△" and "40語" in res["原稿の1文の長さ"][1]
    assert res["原稿のつなぎ"][0] == "△"
    assert "語" in res["原稿の長さ"][1]                                  # 1分150語に対して語数で見る


def test_notes_page_speaks_the_deck_language():
    items = [("Title", "Head", "", "Hello there."), ("Q", "Review Questions (1-1 to 1-3)", "", "")]
    page = notes_html.build_html("Deck", items, ["", ""], [[], [("1-1", "What?")]], lang="英語")
    body = re.sub(r"/\*.*?\*/", "", page, flags=re.S)
    body = re.sub(r"(?m)//[^\n]*$", "", body)
    left = set(re.findall(r"[ぁ-んァ-ヶ一-龥]+", body))
    assert left <= {"コメント", "原稿"}, left                             # 残るのはファイルの名前の決まり（_コメント.json・_原稿.html）だけ
    assert 'lang="en"' in page and "Answer 1-1</button>" in page and "（" not in page.split("<script>")[0].split("<body")[1] and "Deck Script" in page
    ja = notes_html.build_html("Deck", items, ["", ""], [[], [("1-1", "What?")]])
    assert 'lang="ja"' in ja and "1-1 に答える" in ja


def test_briefs_and_cards_tell_the_language(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    work = tmp_path / "_work" / "X"
    work.mkdir(parents=True)
    (work / "outline.md").write_text("## オプション\n\n| オプション | 今の値 |\n|---|---|\n| 言語 | 英語 |\n", encoding="utf-8")
    text = brief.build("設計の担当", str(work), "発表")
    assert "出力の言語：英語" in text and "●見出し" in text.split("出力の言語")[1]
    (work / "outline.md").write_text("## オプション\n\n| オプション | 今の値 |\n|---|---|\n| 言語 | 日本語 |\n", encoding="utf-8")
    assert "出力の言語" not in brief.build("設計の担当", str(work), "発表")
    assert "言語：英語" in brief.build("地図の担当", "X講座", note="学習者：学生／言語：英語")
    rules = "\n".join(cards.language_rules("英語", "380字"))
    assert "190語" in rules and "Review Questions" in rules and "Yes／No" in rules
    assert cards.language_rules("日本語", "380字") == []


def test_table_starts_with_the_language_line(capsys):
    assert sp.language_line(overrides={"言語": "English"}).startswith("**英語で作ります**")
    assert sp.language_line().startswith("**日本語で作ります**")
    import sys
    argv = sys.argv
    try:
        sys.argv = ["slide_profile.py", "--table", "--set", "言語=英語"]
        sp.main()
    finally:
        sys.argv = argv
    out = capsys.readouterr().out
    assert out.index("英語で作ります") < out.index("| オプション |")


def test_notes_page_script_still_parses_in_english(tmp_path):
    """英語にした画面の言葉が JS の文字列を壊さない（README's の ' で JS が止まり、英語のページでコメントが書けなかった）。"""
    import shutil
    import subprocess
    import pytest
    if not shutil.which("node"):
        pytest.skip("node が無い")
    items = [("Title", "Head", "", "Hello there."), ("Q", "Review Questions (1-1 to 1-3)", "", "")]
    for lang in ("英語", None):
        page = notes_html.build_html("Deck", items, ["", ""], [[], [("1-1", "What?")]], lang=lang)
        js = re.findall(r"<script>(.*?)</script>", page, re.S)[-1]
        f = tmp_path / "page.js"
        f.write_text(js, encoding="utf-8")
        r = subprocess.run(["node", "--check", str(f)], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr[-400:]


def test_cover_words_follow_the_language(tmp_path):
    """表紙の名前と上の題に「全N回」「第N回」が残らない（英語の試しで残った）。"""
    p = {"_course": ("How_GPS_Works", 1), "オプション": {"言語": "英語"}}
    assert sp.author(p) == "How GPS Works (1 lecture)"
    p["オプション"]["学習者の名前"] = "Sam"
    assert sp.author(p) == "How GPS Works (1 lecture), for Sam"
    assert sp.author({"_course": ("GPS講座", 3), "オプション": {}}) == "GPS講座（全3回）"
    import scaffold
    work = tmp_path / "_work" / "How_GPS_Works_01"
    work.mkdir(parents=True)
    (work / "memo.md").write_text("## 1. 学習者とゴール\n- 言語：英語\n", encoding="utf-8")
    py = scaffold.build_py(work, "memo", "第1回 How GPS Finds You", [])
    assert 'T = "Lecture 1: How GPS Finds You"' in py and "01_How GPS Finds You_slides.pptx" in py



def test_japanese_left_in_an_english_deck_is_an_error(tmp_path, capsys, monkeypatch):
    """英語の試しで、表紙の「第1回」「全1回」がどの検査にも出なかった。"""
    out = layout(tmp_path, capsys, monkeypatch, "Signals from 4 satellites", head="● 第1回 How GPS Finds You")
    assert "[ERROR] 日本語の文字が残っている" in out
    assert LG.japanese_left("GPS（全1回）", "英語") and not LG.japanese_left("北斗 BeiDou", "中国語")
    assert LG.japanese_left("ひらがな", "中国語") and not LG.japanese_left("第1回", "日本語")


def test_course_parts_follow_the_language(tmp_path, monkeypatch):
    import check_memo
    import scaffold
    assert check_memo.not_body_heading("Check questions (1-1 to 1-3)") and not check_memo.not_body_heading("How GPS Works")
    assert check_memo.HEDGE.search("Apps may get it") and not check_memo.HEDGE.search("Apps get it")
    work = tmp_path / "_work" / "How_GPS_Works_01"
    work.mkdir(parents=True)
    (work / "memo.md").write_text("## 1. 学習者とゴール\n- 言語：英語\n", encoding="utf-8")
    rows = [{"#": 14, "役割": "確認問題", "●見出し": "確認問題（1-1〜1-3）"}, {"#": 16, "役割": "解答", "●見出し": "解答（1-1〜1-3）"}]
    py = scaffold.build_py(work, "memo", "第1回 How GPS Finds You", rows)
    assert 's.heading("Review Questions (1-1 to 1-3)")' in py and 's.heading("Answers (1-1 to 1-3)")' in py and "　" not in py.split("def qa")[1].split("\n\n")[0]
    deck = zemi.Deck(workdir=tmp_path / "build", lang="英語")
    s = deck.slide("T", summary="x")
    s.block("Label:", ["first", "second"])
    deck.section(2, "Results")
    out = tmp_path / "d.pptx"
    deck.save(out)
    from pptx import Presentation
    texts = [sh.text_frame.text for sl in Presentation(str(out)).slides for sh in sl.shapes if sh.has_text_frame]
    assert not any("　" in t for t in texts)
    # 設計の担当（memo.md がまだ無い）にも、講座の README の言語が届く
    monkeypatch.chdir(tmp_path)
    (work / "memo.md").unlink()
    (tmp_path / "How_GPS_Works").mkdir()
    (tmp_path / "How_GPS_Works" / "00_README.md").write_text("## 学習者とゴール\n\n- 言語：英語\n", encoding="utf-8")
    assert "出力の言語：英語" in brief.build("設計の担当", str(work), "講座")


def test_course_readme_settings_reach_the_build(tmp_path):
    """講座の README の学習者とゴールに書いた設定（テンプレート・言語）が、組むときに届く。設計メモの1節が先。"""
    (tmp_path / "X").mkdir()
    (tmp_path / "X" / "00_README.md").write_text("## 学習者とゴール\n\n- テンプレート：テンプレート2\n- 言語：英語\n- 回数：全1回\n", encoding="utf-8")
    work = tmp_path / "_work" / "X_01"
    work.mkdir(parents=True)
    (work / "memo.md").write_text("## 1. 学習者とゴール\n- 聞き手のテーマへの詳しさ：初学者\n", encoding="utf-8")
    p = sp.load_profile(work)
    assert sp.template_name(p) == "テンプレート2" and sp.language(p) == "英語" and sp.deck_options(p)["lang"] == "英語"
    (work / "memo.md").write_text("## 1. 学習者とゴール\n- テンプレート：テンプレート5\n", encoding="utf-8")
    assert sp.template_name(sp.load_profile(work)) == "テンプレート5"


def test_wrapped_question_lines_are_joined_with_a_space_in_english():
    """英語の見本で、折った問題文が「Smith(2021)」「usethe claim」のようにくっついた。日本語どうしは今までどおり詰める。"""
    assert notes_html.join_lines("a claim with Smith\n(2021). You want to use\nthe claim") == "a claim with Smith (2021). You want to use the claim"
    assert notes_html.join_lines("生成AIは何を\n計算しているか") == "生成AIは何を計算しているか"


def test_list_items_keep_one_form_in_english(tmp_path, capsys):
    """英語の体言止めに当たる決まり：並べる項目の形をそろえる（名詞句・命令形・-ing・文を混ぜない）。"""
    f = lambda t: LG.item_form(t, "英語")
    assert f("each model has its own split") == "文" and f("a word or a piece of a word") == "名詞句"
    assert f("generated text that is nonsensical") == "名詞句"          # 関係詞のあとの be動詞は数えない
    assert f("Open it yourself") == "命令形" and f("Sampling one token") == "-ing" and f("free-hanging mirrors") == "名詞句"
    assert f("10 ms apart") is None and f("Why inverted?") is None and f("InstructGPT: tuned on humans") is None
    assert LG.item_form("each model has its own split", "日本語") is None
    assert LG.mixed_forms(["a word or a piece of a word", "each model has its own split"], "英語")[1][0][0] == "文"
    assert LG.mixed_forms(["a word or a piece of a word", "a different split per model"], "英語") is None
    steps = ["Shift one detector", "Search coincidences again", "Each shift = 16 noise-only days"]
    assert LG.mixed_forms(steps, "英語", steps=True)[0] == "命令形"
    assert LG.mixed_forms(["test results", "noise floor"], "英語") is None    # 名詞にもなる動詞は、はっきりした命令形が無ければ名詞句
    deck = zemi.Deck(workdir=tmp_path / "build", lang="英語")
    s = deck.slide("Tokens", summary="Text is split into tokens")
    s.block("Token:", ["a word or a piece of a word", "each model has its own split"])
    s.numbered(["Read it", "Draw one"])
    out = capsys.readouterr().out
    assert out.count("並べる項目の形") == 1 and "1枚目の塊「Token:」" in out
    ja = zemi.Deck(workdir=tmp_path / "ja")
    ja.slide("T", summary="S").block("A：", ["each model has its own split", "a word"])
    assert "並べる項目の形" not in capsys.readouterr().out
