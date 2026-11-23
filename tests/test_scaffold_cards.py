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
    names = sorted(p.name for p in (work / "cards").glob("[0-9][0-9].md"))
    assert names[0] == "02.md" and "01.md" not in names and len(names) == 14   # 表紙はカードなし（見本に論文の表紙は無い）
    c = (work / "cards" / "04.md").read_text(encoding="utf-8")
    assert "この枚の青帯：周波数ごとに雑音の源が違い" in c
    assert "前の枚（3）の青帯" in c and "次の枚（5）の青帯" in c                     # 前後のつながり
    assert "しかし（壁）" in c and "ここに壁があります" in c                          # 前の枚からの書き方
    common = (work / "cards" / "00_共通.md").read_text(encoding="utf-8")
    assert "筋の問い（2枚目）" in common and "筋の問い（" not in c and "00_共通.md" in c   # どのカードにも同じ決まりは共通の紙に1回だけ
    assert "figs/s04.png" in c and 'summary="周波数ごとに雑音の源が違い' in c             # 図の名前と骨組み


def test_merge_puts_parts_back(work):
    (work / "parts" / "04.py").write_text(
        's = deck.slide("検出器", summary="周波数ごとに雑音の源が違い、最良の帯は 100〜300 Hz")\ns.p("書いた本文")\n', encoding="utf-8")
    (work / "parts" / "04.md").write_text("## 4\nしかし、ここに壁があります。\n", encoding="utf-8")
    assert scaffold.main([str(work), "--merge"]) == 0
    b = (work / "build.py").read_text(encoding="utf-8")
    assert 's.p("書いた本文")' in b and b.count("deck.slide(") >= 12
    n = (work / "notes.md").read_text(encoding="utf-8")
    assert "## 4\nしかし、ここに壁があります。" in n and "## 5" in n
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
    c = (work / "cards" / "13.md").read_text(encoding="utf-8")   # 図が「—」の枚（まとめ）
    assert "s13.png" not in c and "s.table" in c
    assert "1行は20字まで" in (work / "cards" / "00_共通.md").read_text(encoding="utf-8")


def test_points_go_to_the_slots_of_each_form(root, tmp_path):
    # 見本の6枚目がラベル・展開の形
    text = (root / "examples" / "zemi" / "outline.md").read_text(encoding="utf-8")
    assert text.count("| ラベル・展開 |") == 1
    (tmp_path / "outline.md").write_text(text, encoding="utf-8")
    shutil.copy2(root / "examples" / "zemi" / "outline_review.md", tmp_path / "outline_review.md")
    assert scaffold.main([str(tmp_path)]) == 0
    c = (tmp_path / "cards" / "06.md").read_text(encoding="utf-8")   # ラベル・展開：「→」の要点は展開へ、「見出し：」の要点はラベルへ
    assert 's.develop("ずらした H1", "{r:L1 と重なる' in c   # 見本の構成案の文言は手直しで変わるので、頭だけ見る
    assert any(line.startswith('s.block("') and "：" in line for line in c.splitlines())
    assert not any("ずらした H1" in line for line in c.splitlines() if line.startswith("s.block"))   # 同じ要点を2つの形に入れない


def test_cards_share_excerpt_files(root, tmp_path):
    for f in ("outline.md", "outline_review.md"):
        shutil.copy2(root / "examples" / "zemi" / f, tmp_path / f)
    src = tmp_path / "paper.txt"
    src.write_text("I. INTRODUCTION\nEinstein 1916.\nII. OBSERVATION\nSeen.\nIII. DETECTORS\nArms 4 km.\nIV. X\n", encoding="utf-8")
    assert scaffold.main([str(tmp_path), "--source", str(src)]) == 0
    files = sorted(p.name for p in (tmp_path / "cards").glob("資料*.md"))
    assert files                                                   # 抜き出しは別のファイル
    c5 = (tmp_path / "cards" / "05.md").read_text(encoding="utf-8")
    c4 = (tmp_path / "cards" / "04.md").read_text(encoding="utf-8")
    pointer = [l for l in c5.splitlines() if "抜き出し：" in l][0]
    assert "cards/資料" in pointer and "Arms 4 km" not in c5      # カードは抜き出しを指すだけ
    assert pointer.split("抜き出し：")[1].split("（")[0] in c4     # 同じ節の枚は同じファイルを指す
    assert "s.block(" in c5                                        # 使う部品の書き方


def test_card_has_notes_frame_and_keep_numbers_rule(work):
    c = (work / "cards" / "08.md").read_text(encoding="utf-8")
    common = (work / "cards" / "00_共通.md").read_text(encoding="utf-8")   # 原稿の型と数値の決まりは共通の紙に
    assert "①導入" in common and "②図の読み方" in common and "⑤次の枚へのつなぎ" in common
    assert "不等号" in common and "変えない" in common
    assert "〔II〕" in c                                     # 要点の出どころはカードに見せる
    assert "〔" not in (work / "build.py").read_text(encoding="utf-8")   # 骨組み（スライド）には出さない


def test_course_card_lists_fact_rows(root, tmp_path):
    src = root / "examples" / "course" / "_work" / "AI活用講座_01"
    w = tmp_path / "AI活用講座_01"
    w.mkdir()
    for f in ("memo.md", "memo_review.md"):
        shutil.copy2(src / f, w / f)
    assert scaffold.main([str(w)]) == 0
    c = (w / "cards" / "07.md").read_text(encoding="utf-8")
    assert "この枚の要点が使う事実" in c and "事実7：" in c and "利用者の意図に沿うとは限らず" in c


def test_try_one_part_reports_plan_checks(work, capsys):
    """書き手が部品のソースを読まずに自分の1枚を確かめる道具（scaffold.py --try NN）。描かず、作業フォルダに残さない。"""
    (work / "parts" / "06.py").write_text(
        's = deck.slide("実験方法", summary="2台の間は光で 10 ms、そろって揺れたものだけを候補にする")\ns.p("書いた本文")\n', encoding="utf-8")
    scaffold.main([str(work), "--try", "6"])
    out = capsys.readouterr().out
    assert "結論の一文：ある" in out and "本文の字数" in out
    assert not list(work.glob("_try_*.py")) and not list((work / "build").glob("_try_*.pptx"))


def test_card_lists_every_part_in_skeleton(work):
    """骨組みに出てくる部品は、全部カードに書き方がある（無いと書き手が zemi.py を読みに行く）。"""
    import re
    for c in (work / "cards").glob("[0-9][0-9].md"):
        t = c.read_text(encoding="utf-8")
        if "## 使う部品の書き方" not in t:   # 想定質問・確認問題のカードは骨組みのコメントに書き方がある
            continue
        skel = t.split("## 骨組み", 1)[-1]
        for name in set(re.findall(r"\bs\.([a-z_]+)\(", skel)) - {"heading", "at"}:
            assert f"`s.{name}(" in t, (c.name, name)


def test_producer_split_at_eight_cards(work):
    """カードが8枚以上なら制作役を2人（前半・後半）と図の担当に。merge は仕上げ役が最初にする。"""
    import brief
    w = work.parent / "_work" / "zemi"
    shutil.copytree(work, w)
    work = w
    nums = brief.card_numbers(work)
    assert len(nums) >= brief.SPLIT_AT
    a = brief.build("制作役", str(work), part="1/2")
    b = brief.build("制作役", str(work), part="2/2")
    one = brief.build("制作役", str(work))
    h1, h2 = brief.halves(nums)
    assert f"{h1[0]:02d}.md" in a and f"{h2[0]:02d}.md" not in a.split("②", 1)[1].split("\n", 1)[0]
    assert "figs.py" not in a and "figs.py" not in b and f"{h2[-1]:02d}.md" in b   # 2人のときは、図は図の担当
    fig = brief.build("図の担当", str(work))
    assert "figdraft.py" in fig and "figs.py" in fig and "parts" in fig
    assert "figs.py" in one                                                     # 1人のときは制作役が図も描く
    assert "--merge" not in a and "--merge" not in b and "--merge" in one
    assert "--merge" in brief.build("仕上げ役", str(work))


def test_recap_role_is_built_from_the_story_table(root, tmp_path):
    """役割「まとめ」の枚は、筋の表の問いと答えを入れた s.recap で組む（まとめの形を決めて縛る）。"""
    import story
    text = (root / "examples" / "zemi" / "outline.md").read_text(encoding="utf-8")
    row = next(l for l in text.splitlines() if l.startswith("| 13 "))
    assert row.rstrip().rstrip("|").rsplit("|", 1)[-1].strip() == "まとめ"   # 見本の13枚目が役割「まとめ」（最後の列）
    for f in ("outline.md", "outline_review.md"):
        shutil.copy2(root / "examples" / "zemi" / f, tmp_path / f)
    assert scaffold.main([str(tmp_path)]) == 0
    py = (tmp_path / "build.py").read_text(encoding="utf-8")
    ans = story.story_table(text)["答え"][0]
    assert 's.heading("まとめ")' in py and "s.recap(" in py and ans[:10] in py
