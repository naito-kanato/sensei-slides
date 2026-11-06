"""配布用の一式（tools/make_starter.py）：スキルが2か所に入り、Codex の決まりと準備のファイルがそろう。"""
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

pytestmark = pytest.mark.skipif(shutil.which("git") is None or not (ROOT / ".git").exists(), reason="git のリポジトリでない")


def _in_head(path):
    return subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e", f"HEAD:{path}"], capture_output=True).returncode == 0


def test_starter_zip_has_everything(tmp_path):
    if not (_in_head("tools/make_starter.py") and _in_head("assets/starter/はじめに.bat")):
        pytest.skip("一式の部品がまだコミットされていない")
    import make_starter
    z = zipfile.ZipFile(make_starter.build(tmp_path))
    names = set(z.namelist())
    top = make_starter.TOP
    for d in (".agents/skills", ".claude/skills"):
        assert f"{top}/{d}/sensei-slides/SKILL.md" in names
        assert f"{top}/{d}/sensei-slides/scripts/zemi.py" in names
        assert f"{top}/{d}/sensei-slides/scripts/MANIFEST.txt" in names
        assert not any(n.startswith(f"{top}/{d}/sensei-slides/tools/") for n in names)   # 配る側の道具は入れない
    assert f"{top}/.codex/rules/sensei-slides.rules" in names
    for f in ("はじめに.bat", "はじめに.sh", "はじめに.md"):
        assert f"{top}/{f}" in names
    assert b"\r\n" in z.read(f"{top}/はじめに.bat")                     # bat は CRLF
    assert (z.getinfo(f"{top}/はじめに.sh").external_attr >> 16) & 0o111   # sh は実行できる
    # はじめに.bat が呼ぶ場所が、一式の中にある
    bat = z.read(f"{top}/はじめに.bat").decode("utf-8")
    for p in (r".agents\skills\sensei-slides\requirements.txt", r".agents\skills\sensei-slides\scripts\check_env.py"):
        assert p in bat and f"{top}/" + p.replace("\\", "/") in names
