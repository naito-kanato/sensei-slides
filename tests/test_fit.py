"""部品が置く瞬間に測る（zemi.py）と、設計メモの時点の入りの見込み（scaffold.fit_estimate・check_memo）。

試しで、制作の担当の出力の半分近くが「組む → 描いて ERROR → 直す」の往復に使われ、1回目の ERROR は
量が多くて縦に入らない・1行が長くて図に重なる・比較を手で決めた y に置いて上の文と重なる、が多かった。
"""
import re
import shutil

import pytest
from PIL import Image
from pptx import Presentation

import check_layout as CL
import check_memo as cm
import render_check_py as rcp
import scaffold
import zemi


@pytest.fixture
def deck(tmp_path):
    return zemi.Deck(workdir=tmp_path / "build")


def _rows(path):
    """保存した pptx を描画の検査と同じ計算で測る：{図形の名前: [行, …]}（行は render_check_py.shape_rows の形）。"""
    prs = Presentation(str(path))
    rd = rcp.Deck(prs)
    out = {}
    for i, sl in enumerate(prs.slides, 1):
        for r in rcp.shape_rows(rd, sl, i):
            out.setdefault(r["name"], []).append(r)
    return out


def _fig(path, w, h):
    Image.new("RGB", (int(w * 220), int(h * 220)), "white").save(path, dpi=(220, 220))
    return path


def test_width_is_the_same_as_the_render_check(deck, tmp_path):
    """zemi の文字の枠の幅は、描画の検査（render_check_py）の文字の範囲と同じ計算（前の PIL の見積もりは数 % 食い違った）。"""
    s = deck.slide("題", summary="結論")
    texts = ["本文の幅を測る行", "Mixed 英字 and 日本語 22pt", "{b:太字の見出し}と{r:赤字}"]
    boxes = [s.text(1.0, 2.0 + k, t, name=f"測る{k}") for k, t in enumerate(texts)]
    out = tmp_path / "w.pptx"
    deck.save(out)
    rows = _rows(out)
    for k, b in enumerate(boxes):
        r = rows[f"測る{k}"][0]
        # 枠の幅 ＝ 字の幅 ＋ 余白 0.1 in × 2 ＋ 0.05 in。検査の範囲 tw は字の幅 ＋ 行末の段落記号の分
        line = zemi.split_lines(zemi.parse_markup(texts[k]))[0]
        assert abs((b.w - 2 * zemi.INSET_X - 0.05) * 72 - zemi.text_width_pt(line, 22)) < 0.01
        assert abs(r["tw"] - zemi.line_extent_pt(line, 22)) < 0.6
        assert abs(r["th"] / 72 - (b.h - 2 * zemi.INSET_Y)) < 0.01


def test_compare_moves_the_cursor_and_avoids_the_block_above(deck):
    """s.compare は置いたあと cur_y を下端の下へ進める（戻り値は今までどおり左右の下端）。手で渡した y が上の塊に重なるなら、塊の下へずらす。"""
    s = deck.slide("題", summary="結論")
    s.heading("見出し")
    blk = s.block("ラベル：", ["説明の1行目", "説明の2行目"])
    yb = s.compare(("A", ["a1", "a2", "a3"]), ("B", ["b1", "b2", "b3"]), y=deck.area["top"] + 0.1)   # 上の塊に重なる y
    assert isinstance(yb, list) and len(yb) == 2
    heads = [b for kind, b in s.boxes if kind == "shape"]
    assert min(b.y for b in heads) >= blk.bottom + 0.25          # 塊の下へずれた
    assert s.cur_y >= max(yb) - 0.25 and s.cur_y > max(b.bottom for b in heads)
    after = s.p("比較のあとの一言")
    assert after.y >= max(yb) - 0.25                               # 続けて置いた文が比較に重ならない


def test_compare_without_y_goes_below_the_blocks(deck):
    s = deck.slide("題", summary="結論")
    blk = s.block("ラベル：", ["説明"])
    s.compare(("A", ["a1", "a2", "a3"]), ("B", ["b1", "b2", "b3"]))
    assert min(b.y for kind, b in s.boxes if kind == "shape") >= blk.bottom


def test_text_beside_a_figure_is_wrapped_to_the_figure(deck, tmp_path):
    """図の横の文は、図の左端から 0.4 in の所で折り返す（1行が長くて図に重なる・間が狭い、を置く時点で直す）。"""
    s = deck.slide("題", summary="結論")
    s.heading("見出し")
    s.block("長い行：", ["この行は図の横に置くには長すぎるので、図の左端までの幅で折り返される", "短い行"])
    s.p("下の文")
    fig = s.figure_beside(_fig(tmp_path / "f.png", 5.6, 3.6))
    out = tmp_path / "b.pptx"
    deck.save(out)
    rows = _rows(out)
    body = rows["塊の本文"][0]
    assert body["lines"] >= 3                                       # 折り返した
    assert fig.x - (body["tl"] + body["tw"]) / 72 >= 0.4 - 0.005    # 図との間は 0.4 in 以上（描画の検査と同じ計算で）
    below = rows[None][0] if None in rows else next(r for k, v in rows.items() for r in v if r["text"] == "下の文")
    assert below["top"] >= body["top"] + body["height"] - 1         # 下の文は、高くなった塊の下へずれた


def test_small_overflow_is_squeezed_and_big_one_is_reported(tmp_path, capsys):
    """本文の下端の小さな超え（0.3 in まで）は塊の間を詰めて直し、知らせない。大きな超えは、組む時点に1行で知らせる。"""
    d = zemi.Deck(workdir=tmp_path / "build")
    s = d.slide("題", summary="結論")
    s.block("ラベル：", ["説明の行"])
    lim = s._bottom_limit()
    y = lim + 0.2 - zemi.INSET_Y - zemi.line_height_in(22)   # 文字の下端がちょうど 0.2 in はみ出す所
    last = s.text(d.area["x"], y, "はみ出す1行")
    big = d.slide("題2", summary="結論")
    for k in range(3):
        big.block(f"ラベル{k}：", ["説明の1行目", "説明の2行目", "説明の3行目"])
    d.save(tmp_path / "o.pptx")
    out = capsys.readouterr().out
    assert "1枚目" not in out                                        # 小さな超えは詰めて直した
    assert last.bottom - zemi.INSET_Y <= lim + 0.001
    m = re.search(r"\[WARN\] 2枚目：文の下端 ([\d.]+) in、限り ([\d.]+) in（([\d.]+) in 超え）→ 要点を1つ減らすか短く", out)
    assert m and float(m.group(3)) > 0.3


def test_compare_overflow_keeps_the_box_rule(deck, capsys, tmp_path):
    """比較が下に入らないときの知らせは、比較の列を削りすぎない直し方を言う（削ると「箱が小さい」と往復した）。"""
    s = deck.slide("題", summary="結論")
    for k in range(3):
        s.block(f"ラベル{k}：", ["説明の1行目", "説明の2行目"])
    s.compare(("A", ["a1", "a2", "a3"]), ("B", ["b1", "b2", "b3"]))
    deck.save(tmp_path / "c.pptx")
    out = capsys.readouterr().out
    assert re.search(r"\[WARN\] 1枚目：比較の下端 .*各列は3行以上のまま", out)


def test_structure_rules_are_reported_when_building(deck, capsys, tmp_path):
    """描画の検査の構造の決まり（文の塊が多い・比較の列が短い）は、組む時点にも同じ基準（check_layout の関数）で知らせる。"""
    s = deck.slide("題", summary="結論")
    s.heading("見出し")
    for k in range(4):
        s.block(f"ラベル{k}：", ["説明"])
    s2 = deck.slide("題", summary="結論")
    s2.heading("見出し")
    s2.compare(("A", ["a1", "a2"]), ("B", ["b1", "b2"]))
    deck.save(tmp_path / "s.pptx")
    out = capsys.readouterr().out
    assert f"1枚目：文の塊が多い（4 つ" in out
    assert f"2枚目：箱が小さい（比較の列が短い：左 2行・右 2行。各列 {CL.COMPARE_MIN_LINES}行以上）" in out


def test_table_rows_grow_with_wrapped_cells(deck, tmp_path):
    """表の行の高さは、折り返したセルの文字に合わせる（行の高さが足りず、セルの文字が下の行のセルに重なっていた）。"""
    s = deck.slide("題", summary="結論")
    y1 = s.table(1.0, 2.0, 2.0, 0.45, ["見出し"], [("行1", ["とても長いセルの文字で、箱の幅では2行か3行に折り返す"]), ("行2", ["短い"])],
                 label_w=1.2)
    out = tmp_path / "t.pptx"
    deck.save(out)
    cells = _rows(out)["表のセル"]
    first, second = sorted(cells, key=lambda r: r["top"])
    assert first["tt"] + first["th"] <= first["top"] + first["height"] + 0.5   # 文字が箱に入る
    assert second["top"] >= first["top"] + first["height"]
    assert y1 > 2.0 + 0.58 + 2 * 0.45


def test_decision_does_not_stop_the_build(deck, capsys, tmp_path):
    """判定の流れ図が下に入らなくても、組むのを止めずに詰めて置き、入らなければ知らせる（前は ValueError で build.py が止まった）。"""
    s = deck.slide("題", summary="結論")
    s.at(deck.area["x"], 4.0)
    s.decision([("問い1？", "結論1"), ("問い2？", "結論2"), ("問い3？", "結論3")], "最後")
    deck.save(tmp_path / "d.pptx")
    assert "1枚目：判定の流れ図の下端" in capsys.readouterr().out


def test_long_cover_title_is_wrapped(tmp_path):
    """表紙の題が 32pt でも幅に入らなければ、2行に折る（題がスライドの外にはみ出していた）。"""
    d = zemi.Deck(workdir=tmp_path / "build")
    d.title_slide(["第1回 とても長い講座の題名がここに入って表紙の幅を大きく超えてしまうときの折り返し"])
    out = tmp_path / "c.pptx"
    d.save(out)
    r = next(v[0] for k, v in _rows(out).items() if v[0]["text"].startswith("第1回"))
    assert r["paras"] == 2 and r["tl"] >= 0 and r["tl"] + r["tw"] <= 13.333 * 72


@pytest.fixture
def memo(root, tmp_path):
    dst = tmp_path / "memo.md"
    shutil.copy2(root / "examples" / "course" / "_work" / "AI活用講座_01" / "memo.md", dst)
    return dst


def test_memo_fit_estimate_warns_before_building(memo):
    """設計メモの時点で、骨組みと同じ部品・幅で組んで、本文の場所に入らない枚を △（✘ にはしない）で出す。"""
    assert dict((i, m) for m, i, _ in cm.check(memo))["入りの見込み"] == "✔"   # 見本は入る
    text = memo.read_text(encoding="utf-8")
    rows = [l for l in text.splitlines() if re.match(r"\|\s*4\s*\|", l)]
    assert rows
    cells = rows[0].split("|")
    head = [c.strip() for c in next(l for l in text.splitlines() if "本文の要点" in l and l.startswith("|")).split("|")]
    k = head.index(next(h for h in head if "本文の要点" in h))
    cells[k] = " " + "／".join(f"見出し{j}：とても長い説明の要点がここに入るので、骨組みは何行にも折り返して縦に入らなくなる{j}" for j in range(4)) + " "
    memo.write_text(text.replace(rows[0], "|".join(cells)), encoding="utf-8")
    est = scaffold.fit_estimate(memo.parent)
    assert est and est[0][0] == 4 and est[0][1] > 0.3 and "4枚目：要点が" in est[0][2] and "入らない見込み" in est[0][2]
    res = {i: (m, msg) for m, i, msg in cm.check(memo)}
    assert res["入りの見込み"][0] == "△" and "4枚目" in res["入りの見込み"][1]
