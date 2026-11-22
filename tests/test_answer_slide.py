"""題の問いの答え（地震の比べ）：筋の問いを題の問いにつなぐ・答えの枚の図・たとえ・確認問題の題の問い・まとめの要点。"""
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
    assert ans == {10: "筋の答えの枚"}   # 10枚目は筋の答えで、だから（問い）も兼ねる
    t2 = text.replace("| 11 | 誤りが出やすい所 | だから（帰結） |", "| 11 | 誤りが出やすい所 | だから（問い） |")
    assert story.answer_slides(t2, "memo")[11] == "だから（問い）の枚"
    zemi = (Path(__file__).resolve().parents[1] / "examples" / "zemi" / "outline.md").read_text(encoding="utf-8")
    assert story.answer_slides(zemi, "outline") == {10: "答えの拍「確かめた結果」の枚", 13: "筋の答えの枚"}   # 型の答えの拍はゼミの見本で


def test_table_on_the_answer_slide_warns(memo):
    """答えの枚の図が表・カードだけなら △（デッキの模式図1枚は、易しい枚で満たされていた）。外す理由があれば通す。"""
    assert got(memo)["答えの枚の図"][0] == "✔"
    edit(memo, "| 仕組み：模式図：実線の枠の中に", "| 観点：表：理由×中身（計算に入る／入らない） 模式図：実線の枠の中に")
    mark, msg = got(memo)["答えの枚の図"]
    assert mark == "△" and "[10] 表" in msg and "見える形" in msg
    edit(memo, "観点：表：理由×中身（", "観点：表：理由×中身（外す理由：見本、")
    assert got(memo)["答えの枚の図"][0] == "✔"


def test_story_question_far_from_the_title_warns(memo):
    """筋の問いが題の問いと語を1つも共有しなければ △。題が問いの形でなければ見ない（迷ったら知らせない）。"""
    assert got(memo)["題の問い"][0] == "✔"
    edit(memo, "答えを知らないのに流暢に書けるなら、生成AIは答えるとき何をしているのか？", "確率が低い所は、本当に安心してよいのか？")
    mark, msg = got(memo)["題の問い"]
    assert mark == "△" and "経験か予想" in msg
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
    edit(memo, "| 問い | 何が |", "| 問い | なぜ |")   # なぜの問いなら、仕組みの問が要る
    edit(memo, "〔題の問い〕〔ゴール1・10枚目〕", "〔ゴール1・6枚目〕")   # 印を外し、根拠も答えの枚でない枚に
    mark, msg = got(memo)["確認問題の題の問い"]
    assert mark == "△" and "〔題の問い〕" in msg and "答えの枚：10" in msg
    edit(memo, "〔ゴール1・6枚目〕〔型：仕組み〕", "〔ゴール1・10枚目〕〔型：仕組み〕")   # 答えの枚（10）を根拠にした仕組みの問
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


def test_figure_step_is_only_for_answer_and_but_slides(root):
    """図の段は答えの枚と しかし の枚だけ（全部の枚を2周すると設計の担当が重くなる。残りは本文と一緒に1枚ずつ）。"""
    for rel in ("assets/briefs/設計の担当.md", "assets/briefs/軽量の設計の担当.md", "references/figures.md"):
        t = (root / rel).read_text(encoding="utf-8")
        assert "全部の枚の図で見せる" not in t and "全部の枚の「図で見せるもの」" not in t
        assert "しかし の枚" in t and "本文と一緒に" in t
