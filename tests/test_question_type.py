"""答えの形・答えの枚の図・題の問いの確認問題は、問いの型（なぜ・どうやって・本当か・どちらか・どこまで・何が）で決める。"""
import check_memo as cm
import story

TABLE = "| 筋 | 型 | 一文 | 枚 |\n|---|---|---|---|\n| 問い | {t} | {q} | 3 |\n| 答え | — | {a} | 9 |\n"


def test_question_type_from_the_column_or_the_words():
    assert story.q_type(TABLE.format(t="どちらか", q="AとBのどちらを選ぶか？", a="x")) == "どちらか"
    assert story.q_type(TABLE.format(t="", q="どうすれば続けられるか？", a="x")) == "どうやって"
    assert story.q_type(TABLE.format(t="", q="なぜ冬は寒いのか？", a="x")) == "なぜ"
    assert story.q_type(TABLE.format(t="", q="題について", a="x")) == ""


def test_every_question_type_has_an_answer_form():
    assert set(story.ANSWER_FORM) == set(story.Q_KINDS)
    for form, fig, quiz in story.ANSWER_FORM.values():
        assert form and fig and quiz


def test_method_answer_is_fine_for_a_how_question():
    """「どうやって」の問いなら、やり方の答えは正しい形（見方・方法だけの答えを止めるのは、ほかの問いのとき）。"""
    how = TABLE.format(t="どうやって", q="どうやって確かめるか？", a="出典を一次資料で確かめる")
    why = TABLE.format(t="なぜ", q="なぜ外れるのか？", a="出典を一次資料で確かめる")
    assert story.METHOD_ANSWER.search("出典を一次資料で確かめる")
    assert story.q_type(how) == "どうやって" and story.q_type(why) == "なぜ"


def test_measurement_conditions_count_as_when():
    """数字に添える条件は、統計の時点だけでなく、測定の温度・試料・測り方でもよい。"""
    assert cm.WHEN.search("4 K で測った抵抗")
    assert cm.WHEN.search("試料Aの値")
    assert cm.WHEN.search("2024年3月末")
    assert not cm.WHEN.search("抵抗が下がった")
