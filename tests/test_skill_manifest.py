"""スキルの部品の指紋（scripts/MANIFEST.txt）。エージェントが部品を書き換えたら、渡す前の確認で見つかる。"""
import shutil

import skill_manifest as sm


def test_manifest_is_current(root):
    """部品を直したら tests/update_manifest.py で作り直す（作り直し忘れをここで見つける）"""
    assert (root / "scripts" / "MANIFEST.txt").read_text(encoding="utf-8") == sm.build(root), \
        "scripts/ か assets/ を直したら `python tests/update_manifest.py` を走らせる"


def test_tampering_is_found(root, tmp_path):
    for d in ("scripts", "assets"):
        shutil.copytree(root / d, tmp_path / d, ignore=shutil.ignore_patterns("__pycache__"))
    assert sm.changes(tmp_path) == ([], [], [])
    p = tmp_path / "scripts" / "notes_html.py"
    p.write_text(p.read_text(encoding="utf-8") + "\n# 書き換え\n", encoding="utf-8")
    (tmp_path / "scripts" / "my_html.py").write_text("print(1)\n", encoding="utf-8")
    (tmp_path / "scripts" / "grid.py").unlink()
    assert sm.changes(tmp_path) == (["scripts/notes_html.py"], ["scripts/my_html.py"], ["scripts/grid.py"])


def test_line_endings_do_not_count(root, tmp_path):
    """Windows で取り出したときの改行（CRLF）の違いは、書き換えとみなさない"""
    for d in ("scripts", "assets"):
        shutil.copytree(root / d, tmp_path / d, ignore=shutil.ignore_patterns("__pycache__"))
    p = tmp_path / "scripts" / "zemi.py"
    p.write_bytes(p.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
    assert sm.changes(tmp_path) == ([], [], [])
