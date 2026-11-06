"""scaffold.py：構成案・設計メモの表から build.py と notes.md の骨組みを作り、そのまま組める。"""
import shutil
import subprocess
import sys
from pathlib import Path

import scaffold
import structures
from pptx import Presentation

ROOT = Path(__file__).resolve().parents[1]


def _make(tmp_path, src, name):
    w = tmp_path / "_work" / name
    w.mkdir(parents=True)
    shutil.copy(src, w)
    assert scaffold.main([str(w)]) == 0
    r = subprocess.run([sys.executable, "-X", "utf8", "build.py"], cwd=w, capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stdout + r.stderr
    return w


def test_course_skeleton_builds_with_roles(tmp_path):
    memo = ROOT / "examples" / "course" / "_work" / "AI活用講座_01" / "memo.md"
    (tmp_path / "AI活用講座").mkdir()
    w = _make(tmp_path, memo, "AI活用講座_01")
    deck = tmp_path / "AI活用講座" / "01_生成AIは何をしているか_スライド.pptx"
    prs = Presentation(str(deck))
    assert len(prs.slides) == 15
    roles = structures.plan_roles(memo.read_text(encoding="utf-8"), "memo")
    assert structures.role_mismatches(prs, roles) == []           # 本文には結論、確認問題・解答には無い
    notes = (w / "notes.md").read_text(encoding="utf-8")
    assert notes.count("\n## ") + notes.startswith("## ") == 15 and "手当て：[2]" in notes


def test_zemi_skeleton_builds(tmp_path):
    w = _make(tmp_path, ROOT / "examples" / "zemi" / "outline.md", "重力波の初観測")
    assert (tmp_path / "重力波の初観測" / "重力波の初観測_スライド.pptx").exists()
    assert "TODO" in (w / "build.py").read_text(encoding="utf-8")


def test_star_becomes_red():
    """設計メモの★（赤字にする結論の印）は消さずに {r:…} にする（消していたので、Codex のデッキが赤字0か所になった）。"""
    assert scaffold.items_of("時間だけで評価しない★／日中の調子も観察") == ["{r:時間だけで評価しない}", "日中の調子も観察"]
    assert scaffold.items_of("トークン：語の一部★<br>眠気・気分・集中") == ["トークン：{r:語の一部}", "眠気・気分・集中"]
    code = "\n".join(scaffold.form_code("ラベル", scaffold.items_of("トークン：語の一部★")))
    assert '{r:語の一部}' in code


def test_existing_files_are_kept(tmp_path, capsys):
    w = tmp_path / "_work" / "x"
    w.mkdir(parents=True)
    shutil.copy(ROOT / "examples" / "zemi" / "outline.md", w)
    (w / "build.py").write_text("# 書きかけ\n", encoding="utf-8")
    scaffold.main([str(w)])
    assert (w / "build.py").read_text(encoding="utf-8") == "# 書きかけ\n"
