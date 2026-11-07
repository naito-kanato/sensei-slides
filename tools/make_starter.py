"""配布用の一式（スキルを入れ終わったスライド作業フォルダ）を、リポジトリの今のコミットから zip にする。

    python tools/make_starter.py                 # dist/sensei-slides.zip（名前は版で変えない。README の「最新版を落とす」リンクが
                                                 # …/releases/latest/download/sensei-slides.zip を指すので、毎回同じ名前で Releases に添付する）
    python tools/make_starter.py --out <フォルダ>  # zip の置き場所を変える

zip の中身（フォルダで包まずに一番上に置く。Windows の「すべて展開」・Mac の解凍は、zip の名前のフォルダ sensei-slides/ を作ってその中に出すので、
包むと sensei-slides/スライド作業フォルダ/ の二重になっていた）：
    .agents/skills/sensei-slides/      スキル（Codex・Antigravity・VS Code の Copilot が読む）
    .claude/skills/sensei-slides/      同じスキル（Claude Code が読む。Windows の zip にはリンクを入れられないので2組）
    .codex/rules/sensei-slides.rules   Codex で PowerPoint を使う3つのスクリプトだけを外で動かす決まり
    .setup/準備.bat・.setup/準備.sh     assets/starter/ から（自分で準備するときのスクリプト。足りない部品は AI も聞いてから入れるので、
                                       一番上に出さず隠しフォルダに置く。スクリプトは一つ上のフォルダに移ってから動く）
    スキルの使い方.html                 使い方のページ（画像の場所を .agents/skills/sensei-slides/docs/ に書き換えた写し。隠しフォルダの奥まで探さずに開ける）

スキルの中身は git archive HEAD（コミット済みのもの）。まだコミットしていない変更は入らないので、残っていれば知らせる。
tools/（このスクリプトなど、配る側の道具）は入れない。
"""
from __future__ import annotations

import argparse
import io
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
NAME = "sensei-slides"
GUIDE = "スキルの使い方.html"
SKILL_DIRS = (".agents/skills", ".claude/skills")
LEAVE_OUT = ("tools/",)
RULES = "assets/codex/sensei-slides.rules"
STARTER = "assets/starter/"


def git(*args) -> bytes:
    return subprocess.run(["git", "-C", str(ROOT), *args], check=True, capture_output=True).stdout


def skill_files():
    """[(リポジトリの中の場所, 中身, 実行できるか)]：今のコミットのファイル（tools/ を除く）。"""
    tar = tarfile.open(fileobj=io.BytesIO(git("archive", "--format=tar", "HEAD")))
    out = []
    for m in tar.getmembers():
        if m.isfile() and not m.name.startswith(LEAVE_OUT):
            out.append((m.name, tar.extractfile(m).read(), bool(m.mode & 0o111)))
    return out


def build(out_dir: Path) -> Path:
    files = skill_files()
    by_name = {n: b for n, b, _ in files}
    if RULES not in by_name or not any(n.startswith(STARTER) for n in by_name):
        raise SystemExit(f"{RULES} か {STARTER} がコミットに無い")
    dirty = git("status", "--porcelain").decode("utf-8", "replace").strip()
    if dirty:
        print("[注意] コミットしていない変更は入らない（git archive HEAD から作る）：\n  " + "\n  ".join(dirty.splitlines()[:8]))
    out_dir.mkdir(parents=True, exist_ok=True)
    zpath = out_dir / f"{NAME}.zip"   # 中身はフォルダで包まない（解凍すると sensei-slides/ の中にそのまま出る）

    def add(z, arc, data, exe=False):
        info = zipfile.ZipInfo(arc, date_time=(2026, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = ((0o755 if exe else 0o644) | 0o100000) << 16
        z.writestr(info, data)

    with zipfile.ZipFile(zpath, "w") as z:
        for d in SKILL_DIRS:
            for n, b, exe in files:
                add(z, f"{d}/{NAME}/{n}", b, exe)
        add(z, f".codex/rules/{NAME}.rules", by_name[RULES])
        for n, b, _ in files:
            if n.startswith(STARTER):
                add(z, ".setup/" + n[len(STARTER):], b, exe=n.endswith(".sh"))
        guide = by_name[GUIDE].decode("utf-8").replace('src="docs/', f'src=".agents/skills/{NAME}/docs/')
        add(z, GUIDE, guide.encode("utf-8"))
    head = git("rev-parse", "--short", "HEAD").decode().strip()
    size = zpath.stat().st_size / 1e6
    print(f"{zpath}（{size:.1f} MB、コミット {head}）")
    return zpath


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=str(ROOT / "dist"), help="zip を置くフォルダ（既定は dist/）")
    a = ap.parse_args(argv)
    build(Path(a.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
