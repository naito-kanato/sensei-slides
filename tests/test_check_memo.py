"""設計メモの確認（check_memo.py）。講座の見本の memo.md を写して、本文の枚数と出典の書き方を見る。

枚数はスライドを作る前（設計メモの段階）に確かめる。作ってからでは直しにくいため。
"""
import re
import shutil

import pytest

import check_memo as cm


@pytest.fixture
def memo(root, tmp_path):
    dst = tmp_path / "memo.md"
    shutil.copy2(root / "examples" / "course" / "_work" / "AI活用講座_01" / "memo.md", dst)
    return dst


def marks(res):
    return {item: mark for mark, item, _ in res}


def keep_body_rows(memo, n):
    """2節の表の本文の行を、最初の n 行だけ残す（表紙・問題・解答の行は残す）。"""
    lines = memo.read_text(encoding="utf-8").splitlines(keepends=True)
    out, seen = [], 0
    for l in lines:
        m = re.match(r"\|\s*\d+\s*\|\s*([^|]+)\|", l)
        if m and not any(w in m.group(1) for w in ("表紙", "問題", "解答")) and "話の順番" not in l:
            seen += 1
            if seen > n:
                continue
        out.append(l)
    memo.write_text("".join(out), encoding="utf-8")


def test_example_memo_is_ready(memo):
    assert cm.body_rows(memo.read_text(encoding="utf-8"))[0] == "次の語を予測する"
    assert len(cm.body_rows(memo.read_text(encoding="utf-8"))) == 10    # 表紙・確認問題・解答の行は数えない
    assert set(marks(cm.check(memo)).values()) <= {"✔", "・"}   # 「・」＝レビュー前（memo_review.md を写していない）
    assert cm.main([str(memo)]) == 0


def test_short_memo_warns_before_building(memo, capsys):
    """本文が既定（10〜15枚）より少ないと △。✘ ではないのでレビューには進めるが、足すか理由を書くよう促す"""
    keep_body_rows(memo, 5)
    assert marks(cm.check(memo))["本文の枚数"] == "△"
    assert cm.main([str(memo)]) == 0
    assert "△ 本文の枚数" in capsys.readouterr().out


def test_reason_clears_the_warning(memo):
    keep_body_rows(memo, 5)
    memo.write_text(memo.read_text(encoding="utf-8").replace(
        "青帯だけを上から読む", "枚数の理由：見本なので短くした\n\n青帯だけを上から読む", 1), encoding="utf-8")
    assert marks(cm.check(memo))["本文の枚数"] == "✔"


def test_vague_source_blocks(memo):
    s = memo.read_text(encoding="utf-8").replace("| ○ |\n", "| ○ |\n| 規制の内容 | 表示できない | 厚生労働省 | ○ |\n", 1)
    memo.write_text(s, encoding="utf-8")
    assert marks(cm.check(memo))["出典"] == "✘"
    assert cm.main([str(memo)]) == 1


# ---- 推論距離（講座の既定の丁寧さは 0）


@pytest.fixture
def reviewed_memo(memo, root):
    """見本の設計メモと、設計メモのレビューの結果（memo_review.md）を同じフォルダに写す。"""
    shutil.copy2(root / "examples" / "course" / "_work" / "AI活用講座_01" / "memo_review.md", memo.with_name("memo_review.md"))
    return memo


def test_example_memo_reasoning_is_covered(reviewed_memo):
    m = marks(cm.check(reviewed_memo, require_review=True))
    assert m["前提と丁寧さ"] == "✔" and m["推論距離の手当て"] == "✔"


def test_memo_without_familiarity_blocks(memo):
    """必須の「聞き手のテーマへの詳しさ」が無いと ✘（先へ進めない）。丁寧さは、書いていなければ詳しさから決まるので無くてよい。"""
    s = memo.read_text(encoding="utf-8")
    memo.write_text(re.sub(r"^- 丁寧さ：.*\n", "", s, flags=re.M), encoding="utf-8")
    assert marks(cm.check(memo))["前提と丁寧さ"] == "✔"
    memo.write_text(re.sub(r"^- 聞き手のテーマへの詳しさ：.*\n", "", s, flags=re.M), encoding="utf-8")
    res = cm.check(memo)
    assert marks(res)["前提と丁寧さ"] == "✘"
    assert "聞き手のテーマへの詳しさ" in next(msg for _, item, msg in res if item == "前提と丁寧さ")


def test_course_default_level_is_zero(memo):
    """丁寧さ 0：用語以外の「要」が1つでもあれば手当てが要る（ゼミの既定 1 なら要らない）。「深」は数えない。"""
    s = memo.read_text(encoding="utf-8")
    s = re.sub(r"^- 丁寧さ：.*\n", "", s, flags=re.M)
    s = re.sub(r"^## 9\..*", "## 9. 引っかかりへの手当て\n", s, flags=re.M | re.S)
    memo.write_text(s, encoding="utf-8")
    memo.with_name("memo_review.md").write_text(
        "[2] 「前提 ⇒ 結論」｜論拠｜要｜補う前提：なぜそうなるか｜使う所：2｜架け方：原稿で1文\n"
        "[3] 「図 ⇒ 結論」｜根拠｜深｜補う前提：出典｜使う所：なし｜架け方：※で出典\n", encoding="utf-8")
    res = cm.check(memo)
    assert marks(res)["推論距離の手当て"] == "✘"
    msg = next(msg for _, item, msg in res if item == "推論距離の手当て")
    assert "[2]" in msg and "[3]" not in msg     # 深（3枚目）は手当てを求めない


def test_memo_review_required_only_at_the_end(memo):
    assert marks(cm.check(memo))["推論距離の手当て"] == "・"
    assert marks(cm.check(memo, require_review=True))["推論距離の手当て"] == "✘"


def test_numeric_points_need_sources(memo):
    text = memo.read_text(encoding="utf-8")
    memo.write_text(text.replace("〔事実7〕", "", 1), encoding="utf-8")
    assert marks(cm.check(memo))["要点の出どころ"] == "△"
