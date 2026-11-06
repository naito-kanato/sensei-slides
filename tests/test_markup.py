"""スライド本文の装飾（{r:赤} {u:下線} ^{上付き} _{下付き}）の読み取り。"""
import pytest

from zemi import C, parse_markup, split_lines, text_width_pt


def texts(runs):
    return [r.text for r in runs]


def test_plain_text_is_one_run():
    runs = parse_markup("温度測定")
    assert texts(runs) == ["温度測定"]
    assert runs[0].color is None and not runs[0].u


def test_red_and_underline():
    runs = parse_markup("前{r:赤字}後{u:下線}")
    assert texts(runs) == ["前", "赤字", "後", "下線"]
    assert runs[1].color == C.RED
    assert runs[3].u and runs[3].color is None


def test_combined_flags_and_nesting():
    runs = parse_markup("{ru:赤と{b:太字}}")
    assert texts(runs) == ["赤と", "太字"]
    assert all(r.color == C.RED and r.u for r in runs)
    assert runs[1].b and not runs[0].b


def test_superscript_and_subscript():
    runs = parse_markup("^{3}He と {i:k}_{B}")
    by_text = {r.text: r for r in runs}
    assert by_text["3"].baseline == 30000
    assert by_text["B"].baseline == -25000
    assert by_text["k"].i


def test_escaped_brace_is_literal():
    assert "".join(texts(parse_markup(r"集合 \{1, 2\}"))) == "集合 {1, 2}"


def test_unclosed_brace_raises():
    with pytest.raises(ValueError):
        parse_markup("{r:閉じていない")


def test_braces_without_flag_are_kept():
    # 「{」のあとがフラグでなければ、そのまま文字として残す
    assert "".join(texts(parse_markup("{x}"))) == "{x}"


def test_split_lines_keeps_style():
    lines = split_lines(parse_markup("1行目\n{r:2行目}"))
    assert [texts(l) for l in lines] == [["1行目"], ["2行目"]]
    assert lines[1][0].color == C.RED


def test_text_width_grows_with_length_and_size():
    short = text_width_pt(parse_markup("温度"), 20)
    long = text_width_pt(parse_markup("温度測定"), 20)
    assert 0 < short < long
    assert text_width_pt(parse_markup("温度"), 40) == pytest.approx(short * 2)


def test_full_width_is_wider_than_half_width():
    assert text_width_pt(parse_markup("あいう"), 20) > text_width_pt(parse_markup("abc"), 20)
