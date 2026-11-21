"""仕組みの模式図の型（figschema）：どの型も、文字の大きさ・ラベルの数・文字と線の重なりの検査を通る。図の案の言葉から型が出る。"""
import figkit
import figschema
import pytest

W, H = 5.6, 3.4
CASES = {
    "branch": lambda ax: figschema.branch(ax, "破れの始まり", ["小さく止まる", "大きく広がる"], highlight=1, stops=[0]),
    "branch3": lambda ax: figschema.branch(ax, "始まり", ["A", "B", "C"], highlight=2),
    "hidden": lambda ax: figschema.hidden(ax, "地表の観測点", "見えない深さ", target="断層"),
    "need_have": lambda ax: figschema.need_have(ax, "要る情報", "測れる情報", gap="足りない分"),
    "build_release": lambda ax: figschema.build_release(ax),
    "funnel": lambda ax: figschema.funnel(ax, [("報告", "729件"), ("記録", "160件"), ("観察", "14件")]),
    "cone": lambda ax: figschema.cone(ax, actual="実際"),
    "sensitive": lambda ax: figschema.sensitive(ax),
    "black_box": lambda ax: figschema.black_box(ax, ["入力A", "入力B"], ["出力"]),
    "balance": lambda ax: figschema.balance(ax, "手間", "安心", result="安心の側に傾く"),
    "section": lambda ax: figschema.section(ax, [("地殻", 1), ("マントル", 2)], marks=[("震源", 0.5, 0.45)], top="地表"),
    "combo": lambda ax: (figschema.hidden(ax, "観測点", "見えない所", area=(0, 0, 2.6, H)),
                         figschema.branch(ax, "始まり", ["止まる", "広がる"], highlight=1, stops=[0],
                                          unknown="見分けられない", area=(2.75, 0, 2.85, H))),
}


@pytest.mark.parametrize("name", sorted(CASES))
def test_each_pattern_passes_the_figure_checks(name, tmp_path, capsys):
    f, ax = figkit.blank(W, H)
    CASES[name](ax)
    assert figkit.min_font(f) >= figkit.MIN_FONT
    assert figkit.text_on_lines(f) == []
    figkit.save(f, tmp_path / f"{name}.png")
    assert "WARN" not in capsys.readouterr().out
    assert (tmp_path / f"{name}.png").exists()


def test_every_pattern_is_listed_and_drawable():
    names = {p.func for p in figschema.PATTERNS}
    assert names <= set(dir(figschema))
    assert {"branch", "hidden", "build_release", "funnel"} <= names


def test_match_finds_the_branch_and_hidden_for_the_answer_plan():
    # 試しの答えの枚の図の案（描く部品が無く、一本の線に点と矢印だけになった）
    plan = "仕組み：模式図：地表（観測できる所）と地下の断層（見えない所）の断面。断層上の1点から破れが始まり、小さく止まる道と大きく広がる道"
    funcs = [p.func for p in figschema.match(plan)]
    assert "branch" in funcs and "hidden" in funcs
    h = figschema.hint(plan)
    assert "figschema.branch(" in h and "area=" in h


def test_no_hint_for_plain_plans():
    assert figschema.match("比べる：棒グラフ：データ1") == []
    assert figschema.hint("比べる：棒グラフ：データ1") == ""


def test_figdraft_template_shows_the_pattern():
    import figdraft
    t = figdraft.template(10, "模式図", "仕組み：模式図：少しずつたまり、限界で一気にずれる", "")
    assert "figschema.build_release" in t
