"""スキルの作者用：scripts/ と assets/ を直したあとに、指紋（scripts/MANIFEST.txt）を作り直す。

    python tests/update_manifest.py

エージェントはこれを走らせない（部品を書き換えたのを隠すことになる。SKILL.md「必ず守る」）。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import skill_manifest as sm  # noqa: E402

sm.MANIFEST.write_text(sm.build(), encoding="utf-8", newline="\n")
print(f"wrote {sm.MANIFEST}")
