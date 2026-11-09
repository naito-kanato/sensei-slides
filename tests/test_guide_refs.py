"""手順書・依頼文・スクリプトの文が指す `guide.py <名前> <節>` が、本当にある節か（節の名前を変えたときに、指し先が切れるのを防ぐ）。"""
import re
from pathlib import Path

import guide

ROOT = Path(__file__).resolve().parents[1]
REF = re.compile(r"guide\.py\s+([A-Za-z][\w.-]*)((?:\s+(?![<`'\"（(|→、。])[^\s`'\"（()|、。]+)*)")


def refs():
    files = [ROOT / "SKILL.md", *sorted((ROOT / "references").glob("*.md")), *sorted((ROOT / "assets" / "briefs").glob("*.md")),
             *sorted(f for f in (ROOT / "scripts").glob("*.py") if f.name != "guide.py")]   # guide.py の説明文は例
    out = []
    for f in files:
        for m in REF.finditer(f.read_text(encoding="utf-8")):
            name, rest = m.group(1), m.group(2).split()
            keys = [k for k in rest if not k.startswith("-") and not k.startswith("<") and k not in ("...", "…")]
            out.append((f.name, name, keys))
    return out


def test_guide_references_exist():
    bad = []
    for where, name, keys in refs():
        try:
            p = guide.path_of(name)
        except SystemExit:
            bad.append(f"{where}: guide.py {name}（手順書が無い）")
            continue
        _, secs = guide.sections(p.read_text(encoding="utf-8"))
        for k in keys:
            if not any(guide.match(h, k) for _, h, _, _ in secs):
                bad.append(f"{where}: guide.py {name} {k}（節が無い）")
    assert not bad, "\n".join(sorted(set(bad)))
