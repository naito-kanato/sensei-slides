"""図の担当が2人で描いた figs_1.py・figs_2.py を順に動かす（brief.py が置いた。図を直すときは figs_N.py を直す）。"""
import runpy
from pathlib import Path

for p in sorted(Path(__file__).resolve().parent.glob("figs_[0-9].py")):
    runpy.run_path(str(p), run_name="__main__")
