"""発表の構成案の確認（check_outline.py）。ゼミの見本の outline.md を写して、本文の枚数を発表時間と比べる。

枚数は中身を作る前（構成案の段階）に確かめる。下限は発表時間÷2分、上限はゆるめに÷1.2分。
"""
import re
import shutil

import pytest

import check_outline as co


@pytest.fixture
def outline(root, tmp_path):
    dst = tmp_path / "outline.md"
    shutil.copy2(root / "examples" / "zemi" / "outline.md", dst)
    return dst


def set_minutes(p, t):
    s = p.read_text(encoding="utf-8")
    s, n = re.subn(r"(\|\s*発表時間\s*\|\s*)[^|]*\|", rf"\g<1>{t} |", s, count=1)
    assert n == 1
    p.write_text(s, encoding="utf-8")


def mark(p):
    return co.check(p)[0][0]


def test_example_outline_is_ready(outline):
    body = co.body_rows(outline.read_text(encoding="utf-8"))
    assert len(body) == 12                      # 表紙と論文の表紙（●見出しが「—」）は数えない
    assert body[0] == "重力波"
    assert co.minutes(outline.read_text(encoding="utf-8")) == 20
    assert mark(outline) == "✔"
    assert co.main([str(outline)]) == 0


def test_bounds():
    assert co.bounds(20) == (10, 16)            # 下限 20÷2、上限はゆるめに 20÷1.2
    assert co.bounds(15) == (7, 12)


def test_too_few_for_the_time_warns(outline, capsys):
    set_minutes(outline, "40分")                # 40分で本文12枚は、下限 20枚を下回る
    assert mark(outline) == "△"
    assert co.main([str(outline)]) == 0          # △ では止めない
    assert "下限 20枚" in capsys.readouterr().out


def test_upper_bound_is_loose(outline):
    set_minutes(outline, "15分")                # 15分で12枚は目安（7〜10枚）を超えるが、ゆるめの上限 12枚の内
    assert mark(outline) == "✔"
    set_minutes(outline, "10分")                # 10分で12枚は上限 8枚を超える
    assert mark(outline) == "△"


def test_reason_and_missing_time(outline):
    set_minutes(outline, "40分")
    outline.write_text(outline.read_text(encoding="utf-8") + "\n枚数の理由：主要な結果に絞った\n", encoding="utf-8")
    assert mark(outline) == "✔"
    set_minutes(outline, "")                    # ひとりゼミなど、発表時間が無いときは数えない
    assert "数えない" in co.check(outline)[0][2]


def marks(p, **kw):
    return {item: m for m, item, _ in co.check(p, **kw)}


@pytest.fixture
def reviewed(outline, root):
    """見本の構成案と、構成案のレビューの結果（outline_review.md）を同じフォルダに写す。"""
    shutil.copy2(root / "examples" / "zemi" / "outline_review.md", outline.with_name("outline_review.md"))
    return outline


def test_example_reasoning_is_covered(reviewed):
    m = marks(reviewed, require_review=True)
    assert m["前提と丁寧さ"] == "✔" and m["推論距離の手当て"] == "✔"
    hs = co.holes(reviewed.with_name("outline_review.md").read_text(encoding="utf-8"))
    assert any(kind == "用語" and need == "要2" for _, kind, need in hs[10])
    assert any(need == "深" for hl in hs.values() for _, _, need in hl)          # 深の行もあるが数えない
    assert co.need_care(hs, 1) == [2, 3, 6, 7, 8, 10, 11, 13, 14]
    assert 12 in co.need_care(hs, 0) and 12 not in co.need_care(hs, 1)           # 要3 が1つだけの枚は、丁寧さ 0 でだけ手当て


def test_need_tiers():
    """要1（この枚の結論のなぜ）と要2（名前の付いた知らない語）は丁寧さによらず手当て。丁寧さは1枚あたりの要3の数にだけ効く。"""
    t = ("[3] 「A ⇒ B」｜論拠｜要1｜補う前提：なぜ｜使う所：3｜架け方：x\n"
         "[4] 「C ⇒ D」｜用語｜要2｜補う前提：意味｜使う所：4｜架け方：x\n"
         "[5] 「E ⇒ F」｜論拠｜要3｜補う前提：前提｜使う所：8｜架け方：x\n"
         "[6] 「G ⇒ H」｜論拠｜要3｜補う前提：前提｜使う所：8｜架け方：x\n[6] 「I ⇒ J」｜比較｜要3｜補う前提：前提｜使う所：9｜架け方：x\n"
         "[7] 「K ⇒ L」｜根拠｜深｜補う前提：出典｜使う所：なし｜架け方：x\n")
    hs = co.holes(t)
    assert co.need_care(hs, 0) == [3, 4, 5, 6]
    assert co.need_care(hs, 1) == [3, 4, 6]
    assert co.need_care(hs, 2) == [3, 4]


def test_missing_prior_knowledge_blocks(reviewed):
    s = reviewed.read_text(encoding="utf-8")
    s = re.sub(r"\|\s*聞き手の前提知識\s*\|[^\n]*\n", "", s)
    reviewed.write_text(s, encoding="utf-8")
    assert marks(reviewed)["前提と丁寧さ"] == "✘"


def test_uncared_hole_blocks(reviewed):
    """レビューで丁寧さを超えたスライドが「引っかかりへの手当て」に無いと ✘"""
    s = reviewed.read_text(encoding="utf-8")
    s = re.sub(r"^- \[13\][^\n]*\n", "", s, flags=re.M)
    reviewed.write_text(s, encoding="utf-8")
    res = co.check(reviewed)
    assert marks(reviewed)["推論距離の手当て"] == "✘"
    assert "[13]" in next(msg for _, item, msg in res if item == "推論距離の手当て")


def test_review_file_required_only_at_the_end(outline):
    """レビューの前（outline_review.md が無い）は数えない。渡す前の確認（require_review）では ✘"""
    assert marks(outline)["推論距離の手当て"] == "・"
    assert marks(outline, require_review=True)["推論距離の手当て"] == "✘"


def test_missing_familiarity_blocks(reviewed):
    """必須の「聞き手のテーマへの詳しさ」が無いと、小さな依頼でも ✘（先へ進めない）。"""
    s = reviewed.read_text(encoding="utf-8")
    s = re.sub(r"\|\s*聞き手のテーマへの詳しさ\s*\|[^\n]*\n", "", s)
    reviewed.write_text(s, encoding="utf-8")
    res = co.check(reviewed)
    assert marks(reviewed)["前提と丁寧さ"] == "✘"
    assert "聞き手のテーマへの詳しさ" in next(msg for _, item, msg in res if item == "前提と丁寧さ")
