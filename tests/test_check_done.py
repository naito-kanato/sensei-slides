"""渡す前の確認（check_done.py）。講座の見本を一時フォルダで組み、足りないものを ✘ にし、そろえたら ✔ になるかを見る。

描画の検査そのもの（PowerPoint が要る）は、check_layout の判定を差し替えて扱う。
"""
import json
import os
import shutil

import pytest

import check_done as cd


@pytest.fixture
def course(built, tmp_path):
    """組んだ講座の見本を写す（テストごとに別のフォルダ）。戻り値 (pptx, 作業フォルダ)。"""
    dst = tmp_path / "course"
    shutil.copytree(built / "examples" / "course", dst)
    pptx = dst / "AI活用講座" / "01_生成AIは何をしているか_スライド.pptx"
    return pptx, dst / "_work" / "AI活用講座_01"


def marks(res):
    return {item: mark for mark, item, _ in res}


GOOD_HTML = '<html><head><meta name="generator" content="sensei-slides notes_html.py"></head></html>'


def finish(pptx, work, monkeypatch):
    """描画結果・原稿ページ・レビューの記録を置き、描画の検査は ERROR 0 として扱う。"""
    (work / "render").mkdir(exist_ok=True)
    (work / "render" / "shapes.json").write_text(json.dumps({"slideWidth": 960, "slideHeight": 540, "slides": 15, "shapes": []}), encoding="utf-8")
    pptx.with_name("01_生成AIは何をしているか_原稿.html").write_text(GOOD_HTML, encoding="utf-8")
    (work / "review.md").write_text("## 判定\n直してから渡す → 直した\n## 直した点\n- 1枚目の文字量\n", encoding="utf-8")
    monkeypatch.setattr(cd.check_layout, "stale_slides", lambda *a: [])
    monkeypatch.setattr(cd.check_layout, "main", lambda *a: print("6 slides: 0 errors, 2 warnings") or 0)


def test_finds_course_work_folder(course):
    pptx, work = course
    assert cd.find_work(pptx) == work


def test_unfinished_deck_is_not_ready(course):
    pptx, work = course
    (work / "review.md").unlink(missing_ok=True)                  # 見本にはレビューの記録が入っているので、まだの状態にする
    m = marks(cd.check(pptx, cd.find_work(pptx)))
    assert m["作業フォルダ"] == "✔"           # memo.md・build.py・notes.md がある
    assert m["読み上げ原稿"] == "✔"           # build.py が notes.md を入れている
    assert m["描画の検査"] == "✘"             # まだ描画していない
    assert m["原稿のページ"] == "✘"
    assert m["完成後のレビュー"] == "✘"
    assert cd.main([str(pptx)]) == 1


def test_finished_deck_is_ready(course, monkeypatch, capsys):
    pptx, work = course
    finish(pptx, work, monkeypatch)
    assert set(marks(cd.check(pptx, work, record=False)).values()) == {"✔"}
    assert cd.main([str(pptx)]) == 0
    assert "渡してよい" in capsys.readouterr().out


def test_stale_outputs_are_caught(course, monkeypatch):
    pptx, work = course
    finish(pptx, work, monkeypatch)
    old = pptx.stat().st_mtime - 100
    html = pptx.with_name("01_生成AIは何をしているか_原稿.html")
    os.utime(html, (old, old))                                    # pptx を直したあと、原稿ページを作り直していない
    os.utime(work / "render" / "shapes.json", (old, old))         # 描画もし直していない
    m = marks(cd.check(pptx, work))
    assert m["原稿のページ"] == "✘" and m["描画の検査"] == "✘"


def test_layout_errors_block(course, monkeypatch):
    pptx, work = course
    finish(pptx, work, monkeypatch)
    monkeypatch.setattr(cd.check_layout, "main", lambda *a: print("6 slides: 2 errors, 0 warnings") or 1)
    assert marks(cd.check(pptx, work))["描画の検査"] == "✘"


def test_review_needs_verdict(course, monkeypatch):
    pptx, work = course
    finish(pptx, work, monkeypatch)
    (work / "review.md").write_text("見た。\n", encoding="utf-8")
    assert marks(cd.check(pptx, work))["完成後のレビュー"] == "✘"


def test_missing_notes_are_listed(course, monkeypatch):
    from pptx import Presentation
    pptx, work = course
    prs = Presentation(pptx)
    prs.slides[2].notes_slide.notes_text_frame.text = ""
    prs.save(pptx)
    res = cd.check(pptx, work)
    msg = next(m for _, item, m in res if item == "読み上げ原稿")
    assert "3" in msg and marks(res)["読み上げ原稿"] == "✘"


def test_work_folder_missing(built, tmp_path):
    pptx = tmp_path / "単独_スライド.pptx"
    shutil.copy2(built / "examples" / "zemi" / "重力波の初観測_スライド.pptx", pptx)
    assert cd.find_work(pptx) is None
    assert marks(cd.check(pptx, None))["作業フォルダ"] == "✘"


def test_vague_sources_are_caught(course, monkeypatch):
    """講座の設計メモで、確認が ○ なのに出典から資料を特定できない行は ✘（「厚生労働省」だけ、など）"""
    pptx, work = course
    finish(pptx, work, monkeypatch)
    memo = work / "memo.md"
    s = memo.read_text(encoding="utf-8")
    s = s.replace("| ○ |\n", "| ○ |\n| 規制の内容 | 表示できない | 厚生労働省 | ○ |\n", 1)
    memo.write_text(s, encoding="utf-8")
    res = cd.check(pptx, work)
    assert marks(res)["出典"] == "✘"
    assert "厚生労働省" in next(m for _, item, m in res if item == "出典")


def test_source_hints():
    ok = ["https://example.org/a", "T. Brown et al., NeurIPS 2020", "厚生労働省「医薬品の範囲に関する基準」", "薬機法第68条", "教科書 p. 41"]
    ng = ["厚生労働省", "薬機法", "各製品の添付文書", "日本耳鼻咽喉科頭頸部外科学会、口腔乾燥関連知見"]
    assert all(cd.SOURCE_HINT.search(t) for t in ok)
    assert not any(cd.SOURCE_HINT.search(t) for t in ng)



def test_figures_must_go_through_figkit(course, monkeypatch):
    """figs.py が savefig を直接呼んでいると ✘（figkit の save の検査が走らないため）"""
    pptx, work = course
    finish(pptx, work, monkeypatch)
    assert marks(cd.check(pptx, work))["図の検査"] == "✔"
    (work / "figs.py").write_text("import matplotlib.pyplot as plt\nf = plt.figure()\nf.savefig('figs/a.png')\n", encoding="utf-8")
    assert marks(cd.check(pptx, work))["図の検査"] == "✘"


def test_handmade_notes_page_is_caught(course, monkeypatch):
    """原稿のページを notes_html.py 以外で作ると ✘（コメント機能が無い。以前の試験で、PowerPoint が止められて自作した）"""
    pptx, work = course
    finish(pptx, work, monkeypatch)
    pptx.with_name("01_生成AIは何をしているか_原稿.html").write_text("<html><body>スライドと原稿</body></html>", encoding="utf-8")
    assert marks(cd.check(pptx, work))["原稿のページ"] == "✘"


def test_figures_drawn_elsewhere_are_caught(course, monkeypatch):
    """figs.py 以外のスクリプトで PIL などから図を描くと ✘（figkit の検査が走らない）"""
    pptx, work = course
    finish(pptx, work, monkeypatch)
    (work / "draw_diagrams.py").write_text("from PIL import Image, ImageDraw\nd = ImageDraw.Draw(Image.new('RGB', (10, 10)))\n", encoding="utf-8")
    res = cd.check(pptx, work)
    assert marks(res)["図の検査"] == "✘"
    assert "draw_diagrams.py" in next(m for _, item, m in res if item == "図の検査")


def test_extra_scripts_in_work_folder_are_caught(course, monkeypatch):
    """作業フォルダに build.py・figs.py 以外のスクリプトを置くと ✘（部品の代わりを自作させない）"""
    pptx, work = course
    finish(pptx, work, monkeypatch)
    assert marks(cd.check(pptx, work))["作業フォルダのスクリプト"] == "✔"
    (work / "make_html.py").write_text("print('html')\n", encoding="utf-8")
    assert marks(cd.check(pptx, work))["作業フォルダのスクリプト"] == "✘"
