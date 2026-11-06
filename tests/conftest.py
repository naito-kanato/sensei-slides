"""テストの共通設定。scripts/ を import できるようにし、リポジトリの場所を渡す。

PowerPoint は使わない（描画検査 render_check.ps1 と原稿ページの PDF 書き出しはテストの外）。
"""
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import matplotlib  # noqa: E402

matplotlib.use("Agg")  # 画面のない環境（CI）でも図を描けるように


@pytest.fixture(autouse=True)
def no_agent_records(tmp_path_factory, monkeypatch):
    """AI の道具の会話の記録（review_record.py が読む）を、空のフォルダに向ける。手元の記録を読まない・テストを遅くしない。"""
    home = tmp_path_factory.mktemp("records")
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(home / "claude"))
    monkeypatch.setenv("CODEX_HOME", str(home / "codex"))


@pytest.fixture
def root():
    return ROOT


@pytest.fixture(scope="session")
def built(tmp_path_factory):
    """リポジトリの scripts・assets・examples を写し、見本（ゼミ・講座・テンプレート・型）の figs.py と build.py を走らせる。"""
    src = Path(__file__).resolve().parents[1]
    dst = tmp_path_factory.mktemp("repo")
    outputs = shutil.ignore_patterns("build", "render", "figs", "*.pptx", "*_原稿.html", "__pycache__")   # 見本の出力は写さない
    shutil.copytree(src / "scripts", dst / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(src / "assets", dst / "assets")                     # テンプレートの pptx はここ
    shutil.copytree(src / "examples", dst / "examples", ignore=outputs)
    for work in (dst / "examples" / "zemi", dst / "examples" / "course" / "_work" / "AI活用講座_01", dst / "examples" / "template",
                 dst / "examples" / "structures"):
        for script in ("figs.py", "build.py"):
            if not (work / script).exists():                            # テンプレートの見本は図をゼミの見本から借りる
                continue
            r = subprocess.run([sys.executable, "-X", "utf8", script], cwd=work, capture_output=True, text=True, encoding="utf-8")
            assert r.returncode == 0, f"{work.name}/{script} が失敗:\n{r.stdout}\n{r.stderr}"
    return dst
