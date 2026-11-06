"""下線は必要なだけ（1枚2か所まで、小見出しは太字）・枚の役割（本文だけに結論の一文。ほかは帯も●も無い枚）。"""
from pathlib import Path

from pptx import Presentation

import check_layout
import structures
import zemi

ROOT = Path(__file__).resolve().parents[1]
TPL = ROOT / "assets" / "templates"


def _deck(tmp_path, n=1):
    return zemi.Deck(template=TPL / f"テンプレート{n}.pptx", workdir=tmp_path / "build")


# ---- 下線
def test_label_and_question_heads_are_bold_not_underlined(tmp_path):
    d = _deck(tmp_path)
    s = d.slide("背景", summary="重力波は予言から100年、直接の観測がなかった")
    s.block("予言：", ["1916年 アインシュタイン"])
    s.ask("中性子星2つでは？", "質量が不足")
    out = tmp_path / "a.pptx"
    d.save(out)
    assert check_layout.underlines(out) == {}
    runs = [r for sh in Presentation(str(out)).slides[0].shapes if sh.name in ("塊の見出し", "問い")
            for p in sh.text_frame.paragraphs for r in p.runs if r.text.strip()]
    assert runs and all(r.font.bold for r in runs)


def test_too_many_underlines_are_counted(tmp_path):
    d = _deck(tmp_path)
    s = d.slide("背景", summary="重力波は予言から100年、直接の観測がなかった")
    s.p("{u:アインシュタイン}が予言、{u:連星パルサー}で確認、{u:LIGO} で観測")
    out = tmp_path / "b.pptx"
    d.save(out)
    u = check_layout.underlines(out)[1]
    assert len(u) == 3 > check_layout.UNDERLINE_MAX


# ---- 帯も●も無い枚
def test_slide_without_summary_becomes_plain_automatically(tmp_path):
    """summary の無い枚は、AI が選ばなくても「本文（帯なし）」になる。●も付かない。結論の置き場は無い。"""
    d = _deck(tmp_path, 4)   # 下の帯
    d.slide("背景", summary="重力波は予言から100年、直接の観測がなかった").p("本文")
    q = d.slide("第1回")
    q.heading("確認問題（1-1〜1-3）")
    q.p("1-1 …")
    out = tmp_path / "c.pptx"
    d.save(out)
    prs = Presentation(str(out))
    plain = prs.slides[1]
    assert prs.slides[0].slide_layout.name != zemi.PLAIN_LAYOUT_NAME
    assert plain.slide_layout.name == zemi.PLAIN_LAYOUT_NAME and plain.name == zemi.PLAIN_MARK
    assert not any(sh.name.startswith(("まとめの", "青帯")) for sh in list(plain.shapes) + list(plain.slide_layout.shapes))
    head = next(sh for sh in plain.shapes if sh.name == "見出し")
    assert not head.text_frame.text.lstrip().startswith(("●", "■"))
    assert zemi.has_conclusion(prs.slides[0], prs.slide_height) and not zemi.has_conclusion(plain, prs.slide_height)


def test_band_summary_counts_as_conclusion(tmp_path):
    d = _deck(tmp_path, 4)   # 下の帯
    d.slide("背景", summary="重力波は予言から100年、直接の観測がなかった").p("本文")
    out = tmp_path / "d.pptx"
    d.save(out)
    prs = Presentation(str(out))
    assert zemi.has_conclusion(prs.slides[0], prs.slide_height)


def test_every_bundled_template_has_the_plain_layout():
    for n in range(1, 9):
        names = [l.name for l in Presentation(str(TPL / f"テンプレート{n}.pptx")).slide_layouts]
        assert zemi.PLAIN_LAYOUT_NAME in names, (n, names)


# ---- 役割
ROLE_PLAN = """## 構成

| 番号 | タイトル | ●見出し | 青帯（結論） | 役割 |
|---|---|---|---|---|
| 1 | 表紙 | — | — | 表紙 |
| 2 | 背景 | 重力波 | 予言から100年、直接の観測がなかった | 本文 |
| 3 | 目的 | — | {c3} | {r3} |
| 4 | 第1回 | 確認問題 | {c4} | 確認問題 |
"""


def test_roles_must_match_the_conclusion_column():
    ok = ROLE_PLAN.format(c3="2台の干渉計で波そのものをとらえる", r3="本文", c4="—")
    assert [m for m, _, _ in structures.check_roles(ok, "outline", "構成案")] == ["✔"]
    marks = {i: m for m, i, _ in structures.check_roles(ROLE_PLAN.format(c3="—", r3="本文", c4="答えを確かめる"), "outline", "構成案")}
    assert marks == {"結論の一文": "✘", "役割と結論": "✘"}
    marks = {i: m for m, i, _ in structures.check_roles(ROLE_PLAN.format(c3="x", r3="図だけ", c4="—"), "outline", "構成案")}
    assert marks.get("役割") == "✘"                  # 一覧に無い役割
    assert structures.check_roles("## 構成\n\n| 番号 | 青帯（結論） |\n|---|---|\n| 1 | — |\n", "outline", "構成案") is None


def test_outline_without_role_column_is_an_error(tmp_path):
    import check_outline
    text = ("## 構成\n\n| 番号 | タイトル | ●見出し | 青帯（結論） | 図で見せるもの |\n|---|---|---|---|---|\n"
            "| 1 | 表紙 | — | — | — |\n| 2 | 背景 | 重力波 | 予言から100年、直接の観測がなかった | テーマ：粒子の輪の図 |\n")
    got = {item: m for m, item, _ in check_outline.flows(text, tmp_path)}
    assert got.get("役割") == "✘"


def test_roles_are_checked_against_the_built_deck(tmp_path):
    d = _deck(tmp_path, 1)
    d.title_slide(["表紙"])
    d.slide("背景", summary="重力波は予言から100年、直接の観測がなかった").p("本文")
    d.slide("目的").p("本文")                          # 結論を書き忘れた
    q = d.slide("第1回", summary="答えを確かめる")       # 確認問題なのに結論がある
    q.heading("確認問題（1-1）")
    out = tmp_path / "g.pptx"
    d.save(out)
    prs = Presentation(str(out))
    got = dict(structures.role_mismatches(prs, {1: "表紙", 2: "本文", 3: "本文", 4: "確認問題"}))
    assert set(got) == {3, 4}


# ---- 見本
def test_examples_follow_the_rules(built):
    ex = built / "examples"
    for p, plan, kind in ((ex / "zemi" / "重力波の初観測_スライド.pptx", ex / "zemi" / "outline.md", "outline"),
                          (next((ex / "course").glob("*/01_*_スライド.pptx")), ex / "course" / "_work" / "AI活用講座_01" / "memo.md", "memo"),
                          (ex / "structures" / "型の見本_スライド.pptx", None, None),
                          (ex / "template" / "テンプレートの見本_スライド.pptx", None, None)):
        many = {i: u for i, u in check_layout.underlines(p).items() if len(u) > check_layout.UNDERLINE_MAX}
        assert not many, f"{p.name}: 下線が多い枚 {many}"
        if plan:
            roles = structures.plan_roles(plan.read_text(encoding="utf-8"), kind)
            assert roles, plan
            assert structures.role_mismatches(Presentation(str(p)), roles) == [], p.name
