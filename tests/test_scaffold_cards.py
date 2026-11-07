"""scaffold.py の枚ごとのカード（cards/NN.md）と、書き手の parts を戻す --merge。"""
import shutil

import pytest

import scaffold


@pytest.fixture
def work(root, tmp_path):
    for f in ("outline.md", "outline_review.md"):
        shutil.copy2(root / "examples" / "zemi" / f, tmp_path / f)
    assert scaffold.main([str(tmp_path)]) == 0
    return tmp_path


def test_cards_for_body_slides(work):
    names = sorted(p.name for p in (work / "cards").glob("*.md"))
    assert names[0] == "02.md" and "04.md" not in names and "01.md" not in names   # 表紙・論文の表紙はカードなし
    c = (work / "cards" / "06.md").read_text(encoding="utf-8")
    assert "この枚の青帯：差は陽子より小さく" in c
    assert "前の枚（5）の青帯" in c and "次の枚（7）の青帯" in c                     # 前後のつながり
    assert "しかし（壁）" in c and "ここに壁があります" in c                          # 前の枚からの書き方
    assert "筋の問い（3枚目）" in c
    assert "figs/s06.png" in c and 'summary="差は陽子より小さく' in c                 # 図の名前と骨組み


def test_merge_puts_parts_back(work):
    (work / "parts" / "06.py").write_text(
        's = deck.slide("実験手法", summary="差は陽子より小さく、腕の中の光を 100 kW に強める")\ns.p("書いた本文")\n', encoding="utf-8")
    (work / "parts" / "06.md").write_text("## 6\nしかし、ここに壁があります。\n", encoding="utf-8")
    assert scaffold.main([str(work), "--merge"]) == 0
    b = (work / "build.py").read_text(encoding="utf-8")
    assert 's.p("書いた本文")' in b and b.count("deck.slide(") >= 12
    n = (work / "notes.md").read_text(encoding="utf-8")
    assert "## 6\nしかし、ここに壁があります。" in n and "## 7" in n
    compile(b, "build.py", "exec")


def test_merge_refuses_changed_conclusion(work):
    (work / "parts" / "06.py").write_text('s = deck.slide("実験手法", summary="別の青帯")\n', encoding="utf-8")
    assert scaffold.main([str(work), "--merge"]) == 1
    assert "別の青帯" not in (work / "build.py").read_text(encoding="utf-8")


def test_red_marks_only_the_starred_part():
    assert scaffold.red("腕 4 km・片方が伸長、★他方は収縮・長さの差") == "腕 4 km・片方が伸長、{r:他方は収縮}・長さの差"
    assert scaffold.red("見出し：説明★") == "見出し：{r:説明}"
    assert scaffold.red("★全体") == "{r:全体}"


def test_underline_marker_becomes_markup():
    assert scaffold.underline("Hulse と Taylor が PSR B1913+16（下線）・電波") == "Hulse と Taylor が {u:PSR B1913+16}・電波"
    assert scaffold.underline("チャープ質量（下線）：約30") == "{u:チャープ質量}：約30"


def test_table_slide_gets_no_figure_file(work):
    c = (work / "cards" / "14.md").read_text(encoding="utf-8")
    assert "s14.png" not in c and "s.table" in c
    assert "1行は20字まで" in c


def test_points_go_to_the_slots_of_each_form(work):
    c = (work / "cards" / "09.md").read_text(encoding="utf-8")   # ラベル・展開：「→」の要点は展開へ、「見出し：」の要点はラベルへ
    assert 's.develop("始まり 35 Hz", "{r:250 Hz まで上昇}")' in c
    assert 's.block("図の読み方："' in c
    assert not any("35 Hz" in line for line in c.splitlines() if line.startswith("s.block"))   # 同じ要点を2つの形に入れない


def test_cards_share_excerpt_files(root, tmp_path):
    for f in ("outline.md", "outline_review.md"):
        shutil.copy2(root / "examples" / "zemi" / f, tmp_path / f)
    src = tmp_path / "paper.txt"
    src.write_text("I. INTRODUCTION\nEinstein 1916.\nII. OBSERVATION\nSeen.\nIII. DETECTORS\nArms 4 km.\nIV. X\n", encoding="utf-8")
    assert scaffold.main([str(tmp_path), "--source", str(src)]) == 0
    files = sorted(p.name for p in (tmp_path / "cards").glob("資料*.md"))
    assert files                                                   # 抜き出しは別のファイル
    c5 = (tmp_path / "cards" / "05.md").read_text(encoding="utf-8")
    c6 = (tmp_path / "cards" / "06.md").read_text(encoding="utf-8")
    pointer = [l for l in c5.splitlines() if "抜き出し：" in l][0]
    assert "cards/資料" in pointer and "Arms 4 km" not in c5      # カードは抜き出しを指すだけ
    assert pointer.split("抜き出し：")[1].split("（")[0] in c6     # 同じ節の枚は同じファイルを指す
    assert "s.block(" in c5                                        # 使う部品の書き方


def test_card_has_notes_frame_and_keep_numbers_rule(work):
    c = (work / "cards" / "08.md").read_text(encoding="utf-8")
    assert "①導入" in c and "②図の読み方" in c and "⑤次の枚へのつなぎ" in c
    assert "不等号" in c and "変えない" in c
    assert "〔要旨〕" in c                                   # 要点の出どころはカードに見せる
    assert "〔" not in (work / "build.py").read_text(encoding="utf-8")   # 骨組み（スライド）には出さない


def test_course_card_lists_fact_rows(root, tmp_path):
    src = root / "examples" / "course" / "_work" / "AI活用講座_01"
    w = tmp_path / "AI活用講座_01"
    w.mkdir()
    for f in ("memo.md", "memo_review.md"):
        shutil.copy2(src / f, w / f)
    assert scaffold.main([str(w)]) == 0
    c = (w / "cards" / "07.md").read_text(encoding="utf-8")
    assert "この枚の要点が使う事実" in c and "事実7：" in c and "55%" in c
