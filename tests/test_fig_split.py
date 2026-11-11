"""図の担当が2人のとき（figs_1.py・figs_2.py と、2つを動かすだけの figs.py）。"""
import os
import time

import check_done as cd
import figdraft
import make_deck
from test_check_done import course  # noqa: F401  （講座の見本を写す fixture）


def test_part_of_splits_in_order():
    assert figdraft.part_of([2, 3, 5, 6, 7], "1/2") == [2, 3, 5]
    assert figdraft.part_of([2, 3, 5, 6, 7], "2/2") == [6, 7]


def test_runner_is_placed_once(tmp_path):
    figdraft.ensure_runner(tmp_path)
    t = (tmp_path / "figs.py").read_text(encoding="utf-8")
    assert "runpy" in t and "figs_[0-9].py" in t
    (tmp_path / "figs.py").write_text("# 自分で書いた", encoding="utf-8")
    figdraft.ensure_runner(tmp_path)
    assert (tmp_path / "figs.py").read_text(encoding="utf-8") == "# 自分で書いた"


def test_stale_looks_at_part_files(tmp_path):
    figdraft.ensure_runner(tmp_path)
    (tmp_path / "figs").mkdir()
    png = tmp_path / "figs" / "s02.png"
    png.write_bytes(b"x")
    part = tmp_path / "figs_1.py"
    part.write_text("# 図", encoding="utf-8")
    old = time.time() - 100
    os.utime(tmp_path / "figs.py", (old, old))
    os.utime(png, (old + 10, old + 10))
    assert make_deck.figs_stale(tmp_path)          # figs_1.py が画像より新しい
    os.utime(part, (old, old))
    assert not make_deck.figs_stale(tmp_path)


def test_check_done_accepts_part_files(course):  # noqa: F811
    pptx, work = course
    for f in work.glob("figs*.py"):
        f.unlink()
    figdraft.ensure_runner(work)
    (work / "figs_1.py").write_text("from figkit import save\nsave(None, 's02')\n", encoding="utf-8")
    marks = {item: (mark, msg) for mark, item, msg in cd.check(pptx, work, record=False)}
    assert marks["作業フォルダのスクリプト"][0] == "✔"
    assert marks.get("図の検査", ("✔", ""))[0] == "✔"
