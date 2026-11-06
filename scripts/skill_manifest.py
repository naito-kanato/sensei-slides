"""スキルの部品（scripts/ と assets/）が書き換えられていないかを、同梱の指紋（MANIFEST.txt）と照合する。

    python <skill>/scripts/skill_manifest.py            # 照合だけ（check_done.py も同じことをする）

エージェントは部品を書き換えない（SKILL.md「スキルの部品は書き換えない」）。部品を直すのはスキルの作者で、
直したら tests/update_manifest.py で MANIFEST.txt を作り直す（テストが、作り直し忘れを見つける）。
テキストは改行コードの違い（Windows の CRLF）を同じとみなす。
"""
import hashlib
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
MANIFEST = SKILL / "scripts" / "MANIFEST.txt"
TEXT = {".py", ".ps1", ".md", ".rules", ".txt", ".json"}


def targets(root: Path = SKILL):
    """指紋を取るファイル：scripts/ と assets/ の中身（キャッシュと MANIFEST.txt 自身は除く）。"""
    out = []
    for d in ("scripts", "assets"):
        for p in sorted((root / d).rglob("*")):
            if p.is_file() and "__pycache__" not in p.parts and p.name != MANIFEST.name and not p.name.startswith("~$"):
                out.append(p)
    return out


def digest(p: Path) -> str:
    b = p.read_bytes()
    if p.suffix.lower() in TEXT:
        b = b.replace(b"\r\n", b"\n")
    return hashlib.sha256(b).hexdigest()


def build(root: Path = SKILL) -> str:
    return "".join(f"{digest(p)}  {p.relative_to(root).as_posix()}\n" for p in targets(root))


def changes(root: Path = SKILL):
    """(書き換えられた, 足された, 消された) のパスのリスト。MANIFEST.txt が無ければ None。"""
    m = root / "scripts" / MANIFEST.name
    if not m.exists():
        return None
    want = {}
    for line in m.read_text(encoding="utf-8").splitlines():
        if line.strip():
            h, path = line.split("  ", 1)
            want[path] = h
    have = {p.relative_to(root).as_posix(): digest(p) for p in targets(root)}
    changed = sorted(k for k in want if k in have and have[k] != want[k])
    added = sorted(k for k in have if k not in want)
    removed = sorted(k for k in want if k not in have)
    return changed, added, removed


def main():
    c = changes()
    if c is None:
        print(f"[ERROR] {MANIFEST} が無い")
        return 1
    changed, added, removed = c
    for label, xs in (("書き換えられた", changed), ("足された", added), ("消された", removed)):
        for x in xs:
            print(f"{label}: {x}")
    if any(c):
        print("✘ スキルの部品が配布時と違う。元に戻す（配布元から入れ直す）")
        return 1
    print("✔ スキルの部品は配布時のまま")
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
