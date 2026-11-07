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
    if not (_in_head("tools/make_starter.py") and _in_head("assets/starter/準備.bat")):
        pytest.skip("一式の部品がまだコミットされていない")
    import make_starter
    z = zipfile.ZipFile(make_starter.build(tmp_path))
    names = set(z.namelist())
    assert not any("スライド作業フォルダ" in n for n in names)              # フォルダで包まない（解凍で二重にならない）
    for d in (".agents/skills", ".claude/skills"):
        assert f"{d}/sensei-slides/SKILL.md" in names
        assert f"{d}/sensei-slides/scripts/zemi.py" in names
        assert f"{d}/sensei-slides/scripts/MANIFEST.txt" in names
        assert not any(n.startswith(f"{d}/sensei-slides/tools/") for n in names)   # 配る側の道具は入れない
    assert f".codex/rules/sensei-slides.rules" in names
    for f in (".setup/準備.bat", ".setup/準備.sh", "スキルの使い方.html"):
        assert f in names
    assert {n.split("/")[0] for n in names} == {".agents", ".claude", ".codex", ".setup", "スキルの使い方.html"}   # 一番上に見えるのは使い方だけ
    assert b"\r\n" in z.read(".setup/準備.bat")                     # bat は CRLF
    assert (z.getinfo(".setup/準備.sh").external_attr >> 16) & 0o111   # sh は実行できる
    # 準備.bat が呼ぶ場所が、一式の中にある
    bat = z.read(".setup/準備.bat").decode("utf-8")
    assert 'cd /d "%~dp0.."' in bat                                       # .setup の一つ上で動く
    for p in (r".agents\skills\sensei-slides\requirements.txt", r".agents\skills\sensei-slides\scripts\check_env.py"):
        assert p in bat and p.replace("\\", "/") in names
    # 一番上の使い方のページは、画像を .agents の中の docs から読む
    guide = z.read("スキルの使い方.html").decode("utf-8")
    assert 'src="docs/' not in guide and 'src=".agents/skills/sensei-slides/docs/course-notes.jpg"' in guide
    assert ".agents/skills/sensei-slides/docs/course-notes.jpg" in names
    assert "スキルの使い方.html" in bat                                   # 準備のあとに開く
