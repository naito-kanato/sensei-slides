"""題の問いの答え（地震の比べ）：筋の問いを題の問いにつなぐ・答えの枚の図・たとえ・確認問題の題の問い・まとめの要点、
推論距離の担当が自分で事実を確かめる依頼文、大きな数字の範囲と限定。"""
import re
import shutil

import pytest
from pptx import Presentation

import brief
import check_memo as cm
import scaffold
import story
from zemi import Deck


@pytest.fixture
def memo(root, tmp_path):
    dst = tmp_path / "memo.md"
    shutil.copy2(root / "examples" / "course" / "_work" / "AI活用講座_01" / "memo.md", dst)
    return dst


def got(memo_path):
    return {item: (mark, msg) for mark, item, msg in cm.check(memo_path)}


def edit(path, a, b):
    t = path.read_text(encoding="utf-8")
    assert a in t, a
    path.write_text(t.replace(a, b, 1), encoding="utf-8")


def test_answer_slides_are_the_story_answer_the_beat_and_why():
    """答えの枚＝筋の答えの枚・型の答えの拍の枚・だから（問い）の枚。"""
    from pathlib import Path
    text = (Path(__file__).resolve().parents[1] / "examples" / "course" / "_work" / "AI活用講座_01" / "memo.md").read_text(encoding="utf-8")
    ans = story.answer_slides(text, "memo")
    assert ans[9] == "筋の答えの枚" and 8 in ans   # 8枚目は「素朴な見方を崩す」の答えの拍（なぜか）＝だから（問い）


def test_table_on_the_answer_slide_warns(memo):
    """答えの枚の図が表・カードだけなら △（デッキの模式図1枚は、易しい枚で満たされていた）。外す理由があれば通す。"""
    assert got(memo)["答えの枚の図"][0] == "✔"
    edit(memo, "| 時期：年表：", "| 観点：表：理由×中身（地下＝見えない／始まり＝分からない） 年表：")
    mark, msg = got(memo)["答えの枚の図"]
    assert mark == "△" and "[8] 表" in msg and "見える対比" in msg
    edit(memo, "観点：表：理由×中身（", "観点：表：理由×中身（外す理由：見本、")
    assert got(memo)["答えの枚の図"][0] == "✔"


def test_story_question_far_from_the_title_warns(memo):
    """筋の問いが題の問いと語を1つも共有しなければ △。題が問いの形でなければ見ない（迷ったら知らせない）。"""
    assert got(memo)["題の問い"][0] == "✔"
    edit(memo, "生成AIは中で何をしていて、その答えはどこまで信じてよいか？", "確率が低い所は、本当に安心してよいのか？")
    mark, msg = got(memo)["題の問い"]
    assert mark == "△" and "冒頭の謎" in msg
    t = memo.read_text(encoding="utf-8")
    memo.write_text(re.sub(r"^# 設計メモ：.*$", "# 設計メモ：第1回 ベイズの定理（X講座）", t, count=1, flags=re.M), encoding="utf-8")
    assert "題の問い" not in got(memo)


def test_title_question_reads_the_course_map(tmp_path):
    """講座の地図のこの回の「題」も題の問いの候補にする（設計メモの見出しが空でも）。"""
    (tmp_path / "地震講座").mkdir()
    (tmp_path / "地震講座" / "00_README.md").write_text(
        "# 地震講座\n\n## 全体の地図\n\n| 回 | 題 | ねらい |\n|---|---|---|\n| 1 | 地震はなぜ予知できないのか | 正しく判断できる |\n", encoding="utf-8")
    w = tmp_path / "_work" / "地震講座_01"
    w.mkdir(parents=True)
    text = "# 設計メモ：第N回 <題>（<講座名>）\n\n| 筋 | 型 | 一文 | 枚 |\n|---|---|---|---|\n| 問い | 本当か | 確率が低い所は安心か？ | 3 |\n"
    assert cm.lesson_titles(text, w / "memo.md") == (["地震はなぜ予知できないのか"], [])
    assert cm.title_question_check(text, w / "memo.md")[0][0] == "△"
    ok = text.replace("確率が低い所は安心か？", "繰り返すのに、なぜ日時を当てられないのか？")   # 同じ問いの語（なぜ）なら通す
    assert cm.title_question_check(ok, w / "memo.md")[0][0] == "✔"


def test_analogy_row(memo):
    """筋の表の「たとえ」が無ければ △。"""
    assert got(memo)["筋のたとえ"][0] == "✔"
    t = memo.read_text(encoding="utf-8")
    memo.write_text(re.sub(r"^\| たとえ \|.*\n", "", t, flags=re.M), encoding="utf-8")
    assert got(memo)["筋のたとえ"][0] == "△"


def test_quiz_must_ask_the_title_question(memo):
    """6問のうち1問が題の問いに答える問：〔題の問い〕か、答えの枚を根拠にした〔型：仕組み〕・なぜ の問。"""
    assert got(memo)["確認問題の題の問い"][0] == "✔"
    edit(memo, "〔題の問い〕", "")
    mark, msg = got(memo)["確認問題の題の問い"]
    assert mark == "△" and "〔題の問い〕" in msg and "8・9" in msg
    edit(memo, "〔ゴール1・6枚目〕〔型：仕組み〕", "〔ゴール1・8枚目〕〔型：仕組み〕")   # 答えの枚（8）を根拠にした仕組みの問
    assert got(memo)["確認問題の題の問い"][0] == "✔"
    assert got(memo)["確認問題"][0] == "✔" and got(memo)["確認問題の型"][0] == "✔"   # 6問ちょうど・型3種類以上は変わらない


def test_recap_points_carry_the_answer():
    """前と後のまとめの対の右に、筋の答え（仕組みの一言）の語が無ければ △。"""
    text = ("| 筋 | 型 | 一文 | 枚 |\n|---|---|---|---|\n| 答え | — | 地下の破壊の始まりが見えず、間隔もばらつくので日時を絞れない | 8 |\n\n"
            "話の型：誤解を正す\n")
    body = [{"#": n, "役割": "本文"} for n in range(2, 9)]
    rec = {"#": 9, "役割": "まとめ", "青帯（結論）": "日時を絞る手がかりが無い", "本文の要点": "予知はいつか当たる → 研究で進む / 確率が低い → 起きうる"}
    res = {i: m for m, i, _ in cm.recap_check(text, body + [rec], scaffold.col)}
    assert res["まとめの枚"] == "✔" and res["まとめの要点と答え"] == "△"
    rec["本文の要点"] = "前兆で当たる → 地下の破壊が見えない / 確率が低い → 起きうる"
    res = {i: m for m, i, _ in cm.recap_check(text, body + [rec], scaffold.col)}
    assert "まとめの要点と答え" not in res


def test_figs_table_points_to_the_figure_step():
    """前の「どの型も：答えの理由の枚は〜」の一行は、図の段に吸収した（重ねて書かない）。"""
    t = story.figs_table("誤解を正す")
    assert "図の段" in t and "確かめると" in t
    assert "どの型も：答えの理由" not in t


def test_design_briefs_put_the_figure_step_before_the_points():
    """設計の依頼文：筋の表 → 話の型 → 青帯を全部 → 図の段 → 本文の形と要点 → まとめ・確認問題。題の問いにつなぐ。"""
    for role in ("軽量の設計の担当", "設計の担当"):
        t = (brief.BRIEFS / f"{role}.md").read_text(encoding="utf-8")
        assert "図の段" in t and "題の問い" in t and "たとえ" in t
        assert t.index("青帯の並びを全部") < t.index("図の段") < t.index("本文の形（")


def test_light_design_brief_does_not_grow_much(tmp_path, monkeypatch):
    """軽量の設計の担当の依頼文（写した節を含む）を大きく増やさない（道具の出力が長いとファイルに逃がされ、読み直しが重くなる）。"""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "_work").mkdir()
    t = brief.build("軽量の設計の担当", str(tmp_path / "_work" / "X講座_01"), kind="講座")
    assert len(t) < 25000


def test_inference_brief_checks_facts_itself():
    """推論距離の担当は、事実が要る穴を自分で Web で確かめて埋める（検索3回まで・確かめずに書かない）。設計の担当に戻すのは、
    検索3回で足りないときと、筋が変わる穴だけ。"""
    t = (brief.BRIEFS / "推論距離の担当.md").read_text(encoding="utf-8")
    assert "新しい事実は足さない" not in t
    assert "検索は合わせて3回まで" in t and "確かめずに書かない" in t and "事実と出典" in t
    import next_step
    import inspect
    src = inspect.getsource(next_step)
    assert "検索3回で確かめきれなかった" in src


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
