"""型の見本で使う、説明のための図（値は例。実在の測定ではない）。ほかの図はゼミの見本（examples/zemi/figs）のものを使う。
en_ で始まる図は英語版の見本（build_en.py）用：文字だけ英語にした同じ図。
en_strain は、英語の論文紹介の見本の輪の図（下に横長に置く幅 8.4 in）を、見本帳の本文の右に置く幅（約 5.6 in）で描き直したもの
（日本語の examples/zemi/figs/strain.png と同じ大きさ。縮めて置くと図の文字が 14pt を下回る）。

    python figs.py
"""
import sys
from pathlib import Path

import numpy as np

SKILL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILL / "scripts"))
from figkit import COL, arrow, blank, fig, save  # noqa: E402

OUT = Path(__file__).parent / "figs"


def _overlay(name, shift, xlabel="時刻（例）", size=(4.3, 2.8)):
    """2台の検出器の信号を重ねた図（説明のための例）。shift=0 なら同じ形がそろい、大きくずらすとそろわない"""
    f, ax = fig(*size)
    t = np.linspace(0, 1, 400)
    rng = np.random.default_rng(7)

    def chirp(t0):
        x = np.clip((t - t0) / 0.35, 0, 1)
        return np.where((t > t0) & (t < t0 + 0.38), np.sin(2 * np.pi * (6 * x + 10 * x ** 3)) * x ** 2, 0)

    ax.plot(t, chirp(0.4) + rng.normal(0, 0.12, t.size), color=COL.blue, lw=1.2, label="H1")
    ax.plot(t, chirp(0.4 + shift) + rng.normal(0, 0.12, t.size) - 2.4, color=COL.text, lw=1.2, label="L1")
    ax.set_xlabel(xlabel)
    ax.set_yticks([0, -2.4], ["H1", "L1"])
    ax.set_ylim(-3.6, 1.4)
    save(f, OUT / f"{name}.png")


def f_shift_before():
    _overlay("shift_before", 0.0)


def f_shift_after():
    _overlay("shift_after", 0.3)


def f_en_shift_before():
    _overlay("en_shift_before", 0.0, "Time (example)")


def f_en_shift_after():
    _overlay("en_shift_after", 0.3, "Time (example)")


def f_same_wave():
    """横の矢印で展開の枚（4枚目）の右の図：2台で同じ波形（shift_before を、本文の右に置く幅で大きく）"""
    _overlay("same_wave", 0.0, size=(5.0, 3.6))


def f_en_same_wave():
    _overlay("en_same_wave", 0.0, "Time (example)", size=(5.0, 3.6))


def f_en_strain():
    """重力波が通ると、輪に並んだ粒子が縦横交互に伸び縮みする（+ 偏光の模式図）。examples/zemi/figs.py の f_strain と同じ図を英語で"""
    f, ax = blank(5.6, 3.2)
    th = np.linspace(0, 2 * np.pi, 13)[:-1]
    ring = np.linspace(0, 2 * np.pi, 100)
    r, cy = 0.7, 1.9
    for k, (sx, sy, name) in enumerate([(1, 1, "Before"), (1.25, 0.8, "1/4 period"), (0.8, 1.25, "3/4 period")]):
        cx = 0.95 + k * 1.85
        ax.plot(cx + r * np.cos(ring), cy + r * np.sin(ring), color=COL.gray, lw=1.0, ls="--")
        ax.scatter(cx + r * sx * np.cos(th), cy + r * sy * np.sin(th), s=55, color=COL.blue, zorder=3)
        ax.text(cx, 0.3, name, ha="center", fontsize=14)
        if sx > 1:      # 横に伸びる
            arrow(ax, (cx - 0.55, cy), (cx + 0.55, cy), color=COL.gray, style="<|-|>", lw=1.0, ms=12)
        elif sy > 1:    # 縦に伸びる
            arrow(ax, (cx, cy - 0.55), (cx, cy + 0.55), color=COL.gray, style="<|-|>", lw=1.0, ms=12)
    ax.set_xlim(0, 5.6); ax.set_ylim(0, 3.2)
    save(f, OUT / "en_strain.png")


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    names = sys.argv[1:] or [n[2:] for n in dict(globals()) if n.startswith("f_")]
    for n in names:
        globals()["f_" + n]()
