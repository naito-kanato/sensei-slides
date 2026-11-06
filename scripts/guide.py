"""手順書（SKILL.md・references/*.md）の、今要る節だけを出す。ファイルを丸ごと読まずに済ませる（会話を短く保つ）。

    python <skill>/scripts/guide.py course              # references/course.md の見出しの一覧（節の名前と字数）
    python <skill>/scripts/guide.py course 4            # 「4.」で始まる節（その下の小見出しも含む）
    python <skill>/scripts/guide.py skill 4 5 5b        # SKILL.md の手順4・5・5b
    python <skill>/scripts/guide.py skill コマンドの書き方 # 見出しにその語を含む節

ファイルの名前：skill（SKILL.md）か、references の名前（course・figures・style-guide・structures・final-review・
outline-review・agents・answer-deck・series・templates など。.md は省ける）。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SKILL = Path(__file__).resolve().parents[1]
HEAD = re.compile(r"^(#{2,4})\s+(.+?)\s*$")


def path_of(name: str) -> Path:
    if name.lower() in ("skill", "skill.md"):
        return SKILL / "SKILL.md"
    p = SKILL / "references" / (name if name.endswith(".md") else name + ".md")
    if not p.exists():
        names = ", ".join(sorted(f.stem for f in (SKILL / "references").glob("*.md")))
        raise SystemExit(f"{p.name} が無い。使える名前：skill, {names}")
    return p


def sections(text: str):
    """[(深さ, 見出し, 開始行, 終了行)]。終了は、同じか浅い次の見出しの手前。"""
    lines = text.splitlines()
    heads = [(i, len(m.group(1)), m.group(2)) for i, l in enumerate(lines) if (m := HEAD.match(l))]
    out = []
    for k, (i, d, h) in enumerate(heads):
        end = next((j for j, dd, _ in heads[k + 1:] if dd <= d), len(lines))
        out.append((d, h, i, end))
    return lines, out


def match(head: str, key: str) -> bool:
    if re.fullmatch(r"\d+[a-z]?", key):   # 番号：「4.」「5b.」「手順4」で始まる見出し
        return bool(re.match(rf"^(手順)?{re.escape(key)}[.．\s]", head))
    return key in head


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print(__doc__)
        return 1
    p = path_of(argv[0])
    lines, secs = sections(p.read_text(encoding="utf-8"))
    if len(argv) == 1:
        print(f"{p.name} の節（{len(''.join(lines))}字）：")
        for d, h, a, b in secs:
            print(f"{'  ' * (d - 2)}- {h}（{len('' .join(lines[a:b]))}字）")
        return 0
    shown = 0
    for key in argv[1:]:
        hit = [(d, h, a, b) for d, h, a, b in secs if match(h, key)]
        if not hit:
            print(f"（{p.name} に「{key}」の節が無い。python guide.py {argv[0]} で一覧を見る）")
            continue
        d, h, a, b = hit[0]
        print("\n".join(lines[a:b]).rstrip() + "\n")
        shown += 1
    return 0 if shown else 1


if __name__ == "__main__":
    sys.exit(main())
