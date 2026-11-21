"""仕組みの模式図の型（figschema）：どの型も、文字の大きさ・ラベルの数・文字と線の重なりの検査を通る。図の案の言葉から型が出る。"""
import figkit
import figschema
import pytest

W, H = 5.6, 3.4
CASES = {
    "branch": lambda ax: figschema.branch(ax, "始まり", ["結末A", "結末B"], highlight=1, stops=[0], unknown="ここでは見分けられない"),
    "branch3": lambda ax: figschema.branch(ax, "始まり", ["A", "B", "C"], highlight=2),
    "hidden": lambda ax: figschema.hidden(ax, "測る所", "見えない所", target="肝心の物"),
    "need_have": lambda ax: figschema.need_have(ax, "要る量", "手に入る量", gap="足りない分"),
    "build_release": lambda ax: figschema.build_release(ax),
    "build_release_uneven": lambda ax: figschema.build_release(ax, intervals=(1.0, 0.6, 1.4, 0.8), limits=(0.8, 0.6, 0.95, 0.7),
                                                               band="限界の幅", gap="間隔のばらつき"),
    "funnel": lambda ax: figschema.funnel(ax, [("候補", "1000件"), ("条件", "120件"), ("残り", "8件")]),
    "cone": lambda ax: figschema.cone(ax, actual="実際"),
    "sensitive": lambda ax: figschema.sensitive(ax),
    "black_box": lambda ax: figschema.black_box(ax, ["入力A", "入力B"], ["出力"]),
    "balance": lambda ax: figschema.balance(ax, "重みA", "重みB", result="Bに傾く"),
    "section": lambda ax: figschema.section(ax, [("上の層", 1), ("下の層", 2)], marks=[("ここ", 0.5, 0.45)], top="表面"),
    "combo": lambda ax: (figschema.hidden(ax, "測る所", "見えない所", area=(0, 0, 2.6, H)),
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
    plan = "仕組み：模式図：外から観測できる所と、内部の見えない所。同じ始まりから2つの結末に分かれる道"
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
