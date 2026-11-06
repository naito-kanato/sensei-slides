"""materials.py：資料が全部はそろっていない発表の資料置き場と、足りないものの確認。"""
from pptx import Presentation
from pptx.util import Inches

import materials


def marks(res):
    return {item: m for m, item, _ in res}


def test_init_makes_folders_and_plan(tmp_path):
    m = materials.init(tmp_path)
    for d in ("図", "過去のスライド", "その他"):
        assert (m / d).is_dir()
    assert (m / "方針.md").exists()
    res = materials.check(tmp_path)
    assert marks(res)["方針"] == "✘" and marks(res)["結果の図"] == "✘"      # 雛形のまま・図なしでは進めない


def test_filled_plan_and_figure_pass(tmp_path):
    m = materials.init(tmp_path)
    (m / "図" / "spectrum.png").write_bytes(b"x")
    (m / "方針.md").write_text(
        "## 発表の場と聞き手\n物理学会、15分、同じ分野\n## 背景\nX が未解明\n## 目的\nY を測る\n## 方法\nレーザー干渉計\n"
        "## 結果（図ごとに：何が見えるか・数値）\n- spectrum.png：ピークが 2 meV\n## 結論・いちばん言いたいこと\nZ が分かった\n", encoding="utf-8")
    res = materials.check(tmp_path)
    assert marks(res)["方針"] == "✔" and marks(res)["結果の図"] == "✔" and "図の説明" not in marks(res)


def test_figure_without_description_is_flagged(tmp_path):
    m = materials.init(tmp_path)
    (m / "図" / "fit.png").write_bytes(b"x")
    assert marks(materials.check(tmp_path))["図の説明"] == "△"


def test_past_slides_text(tmp_path):
    m = materials.init(tmp_path)
    prs = Presentation()
    s = prs.slides.add_slide(prs.slide_layouts[1])
    s.shapes.title.text = "結果"
    s.placeholders[1].text = "ピークが 2 meV"
    prs.save(m / "過去のスライド" / "中間.pptx")
    assert materials.main([str(tmp_path), "--text"]) == 0
    t = (m / "過去のスライド" / "中間_文字.md").read_text(encoding="utf-8")
    assert "## 1" in t and "ピークが 2 meV" in t


def test_collect_copies_loose_files_into_the_store(tmp_path):
    """ユーザーはフォルダの一番上に資料を入れて頼む。AI が発表フォルダの 資料/ に種類ごとに格納する。"""
    for n in ("spectrum.png", "前回の発表.pptx", "要旨.docx", "教科書.pdf", "はじめに.md", "前回_スライド.pptx"):
        (tmp_path / n).write_bytes(b"x")
    folder = tmp_path / "物理学会2026"
    moved = {a.name: b.parent.name for a, b in materials.collect(folder)}
    assert moved == {"spectrum.png": "図", "前回の発表.pptx": "過去のスライド", "要旨.docx": "その他", "教科書.pdf": "その他"}
    assert (tmp_path / "はじめに.md").exists() and (tmp_path / "前回_スライド.pptx").exists()   # 一式とできたスライドは候補に出さない
    assert (tmp_path / "spectrum.png").exists() and (folder / "資料" / "図" / "spectrum.png").exists()   # 元は残して写す


def test_collect_only_named_files_and_source_mode(tmp_path):
    (tmp_path / "paper.pdf").write_bytes(b"x")
    (tmp_path / "other.pdf").write_bytes(b"x")
    folder = tmp_path / "論文紹介"
    materials.collect(folder, ["paper.pdf"])
    assert (folder / "資料" / "その他" / "paper.pdf").exists() and (tmp_path / "other.pdf").exists()
    assert {i: m for m, i, _ in materials.check(folder, source=True)} == {"資料": "✔"}   # 論文がそろっていれば方針は任意


def test_scan_lists_without_moving(tmp_path, capsys):
    (tmp_path / "paper.pdf").write_bytes(b"x")
    assert materials.main(["--scan", str(tmp_path)]) == 0
    assert "paper.pdf" in capsys.readouterr().out and (tmp_path / "paper.pdf").exists()
