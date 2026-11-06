"""型の見本で使う、説明のための図（値は例。実在の測定ではない）。ほかの図はゼミの見本（examples/zemi/figs）のものを使う。

    python figs.py
"""
import sys
from pathlib import Path

import numpy as np

SKILL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILL / "scripts"))
from figkit import COL, fig, save  # noqa: E402

OUT = Path(__file__).parent / "figs"


def _overlay(name, shift):
    """2台の検出器の信号を重ねた図（説明のための例）。shift=0 なら同じ形がそろい、大きくずらすとそろわない"""
    f, ax = fig(4.3, 2.8)
    t = np.linspace(0, 1, 400)
    rng = np.random.default_rng(7)

    def chirp(t0):
        x = np.clip((t - t0) / 0.35, 0, 1)
        return np.where((t > t0) & (t < t0 + 0.38), np.sin(2 * np.pi * (6 * x + 10 * x ** 3)) * x ** 2, 0)

    ax.plot(t, chirp(0.4) + rng.normal(0, 0.12, t.size), color=COL.blue, lw=1.2, label="H1")
    ax.plot(t, chirp(0.4 + shift) + rng.normal(0, 0.12, t.size) - 2.4, color=COL.text, lw=1.2, label="L1")
    ax.set_xlabel("時刻（例）")
    ax.set_yticks([0, -2.4], ["H1", "L1"])
    ax.set_ylim(-3.6, 1.4)
    save(f, OUT / f"{name}.png")


def f_shift_before():
    _overlay("shift_before", 0.0)


def f_shift_after():
    _overlay("shift_after", 0.3)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    names = sys.argv[1:] or [n[2:] for n in dict(globals()) if n.startswith("f_")]
    for n in names:
        globals()["f_" + n]()
