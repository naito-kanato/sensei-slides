"""ゼミの見本（論文紹介：重力波の初観測）の、自分で描く図。論文の図は paper_figs/ にある（切り出したもの、出典は ATTRIBUTION.md）。

    python figs.py            # 全部の図を figs/ に書き出す
    python figs.py michelson  # 一部だけ描き直す（関数名の f_ を除いた名前）

図は右の本文の場所（幅 5.6〜6 in・高さ 3.5〜4.5 in）を埋める大きさで描き、描いた幅のまま置く
（以前は幅 4.8〜5 in で描いていて、本文と図の間が 2〜3 in 空いていた）。図の文字は 14pt のまま。
"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle

SKILL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILL / "scripts"))
from figkit import COL, arrow, blank, box, save  # noqa: E402

OUT = Path(__file__).parent / "figs"
FS = 14  # 図中ラベル


def f_strain():
    """重力波が通ると、輪に並んだ粒子が縦横交互に伸び縮みする（+ 偏光の模式図）。伸びる向きを細い両矢印で"""
    f, ax = blank(6.0, 3.3)
    th = np.linspace(0, 2 * np.pi, 13)[:-1]
    ring = np.linspace(0, 2 * np.pi, 100)
    r, cy = 0.72, 1.9
    for k, (sx, sy, name) in enumerate([(1, 1, "波の前"), (1.25, 0.8, "1/4 周期後"), (0.8, 1.25, "3/4 周期後")]):
        cx = 1.0 + k * 2.0
        ax.plot(cx + r * np.cos(ring), cy + r * np.sin(ring), color=COL.gray, lw=1.0, ls="--")
        ax.scatter(cx + r * sx * np.cos(th), cy + r * sy * np.sin(th), s=55, color=COL.blue, zorder=3)
        ax.text(cx, 0.3, name, ha="center", fontsize=FS)
        if sx > 1:      # 横に伸びる
            arrow(ax, (cx - 0.55, cy), (cx + 0.55, cy), color=COL.gray, style="<|-|>", lw=1.0, ms=12)
        elif sy > 1:    # 縦に伸びる
            arrow(ax, (cx, cy - 0.55), (cx, cy + 0.55), color=COL.gray, style="<|-|>", lw=1.0, ms=12)
    ax.set_xlim(0, 6.0); ax.set_ylim(0, 3.3)
    save(f, OUT / "strain.png")


def f_michelson():
    """マイケルソン干渉計の模式図（論文 Fig. 3 をもとに作図。腕の共振器・リサイクリングの鏡は省く）"""
    s = 1.2   # 以前の 4.8×3.8 in の座標を 1.2 倍に
    f, ax = blank(4.8 * s, 3.8 * s)
    bx, by = 1.5 * s, 1.2 * s
    ax.plot([0.55 * s, 4.3 * s], [by, by], color=COL.red, lw=2.4)              # レーザー → x の腕
    ax.plot([bx, bx], [by, 3.4 * s], color=COL.red, lw=2.4)                    # y の腕
    ax.plot([bx, bx], [0.35 * s, by], color=COL.red, lw=1.6, ls="--")          # 検出器へ
    ax.plot([bx - 0.26, bx + 0.26], [by - 0.26, by + 0.26], color=COL.ink, lw=3)   # ビームスプリッタ
    ax.add_patch(Rectangle((4.3 * s, by - 0.36), 0.19, 0.72, fc=COL.pale, ec=COL.ink, lw=1.4))   # x の鏡
    ax.add_patch(Rectangle((bx - 0.36, 3.4 * s), 0.72, 0.19, fc=COL.pale, ec=COL.ink, lw=1.4))   # y の鏡
    ax.add_patch(Rectangle((0.0, by - 0.26), 0.66, 0.52, fc=COL.ink, ec=COL.ink))
    ax.text(0.33, by - 0.48, "レーザー", ha="center", va="top", fontsize=FS)
    ax.text(bx + 0.14, 0.33, "光検出器", ha="left", va="center", fontsize=FS)
    ax.text(4.3 * s + 0.1, by + 0.5, "鏡", ha="center", fontsize=FS)
    arrow(ax, (2.0 * s, 0.75 * s), (4.25 * s, 0.75 * s), color=COL.ink, style="<|-|>")
    ax.text(3.1 * s, 0.42 * s, r"$L_x = 4$ km", ha="center", fontsize=FS)
    arrow(ax, (2.0 * s, 1.65 * s), (2.0 * s, 3.35 * s), color=COL.ink, style="<|-|>")
    ax.text(2.15 * s, 2.5 * s, r"$L_y = 4$ km", ha="left", va="center", fontsize=FS)
    ax.set_xlim(-0.1, 4.8 * s); ax.set_ylim(0.0, 3.8 * s)
    save(f, OUT / "michelson.png")


def f_pulsar():
    """連星パルサーの概略：軌道が縮む（エネルギーを重力波で失う）。大きさは概略"""
    f, ax = blank(5.6, 4.0)
    cx, cy = 2.8, 1.85
    ring = np.linspace(0, 2 * np.pi, 200)
    ax.plot(cx + 1.4 * np.cos(ring), cy + 1.4 * np.sin(ring), color=COL.gray, lw=1.0, ls="--")
    ax.plot(cx + 0.85 * np.cos(ring), cy + 0.85 * np.sin(ring), color=COL.lblue, lw=1.6)
    ax.add_patch(plt.Circle((cx + 0.85, cy), 0.18, fc=COL.red, ec="none"))
    ax.add_patch(plt.Circle((cx - 0.85, cy), 0.13, fc=COL.blue, ec="none"))
    ax.text(cx + 1.55, cy, "パルサー", ha="left", va="center", fontsize=FS)
    ax.text(cx - 1.55, cy, "伴星", ha="right", va="center", fontsize=FS)
    th = 0.9
    arrow(ax, (cx + 1.4 * np.cos(th), cy + 1.4 * np.sin(th)), (cx + 0.85 * np.cos(th) + 0.02, cy + 0.85 * np.sin(th) + 0.02),
          color=COL.red, lw=1.6)
    ax.text(cx + 1.5, cy + 1.55, "軌道の縮小", ha="center", va="bottom", fontsize=FS)
    ax.set_xlim(0, 5.6); ax.set_ylim(0, 4.0)
    save(f, OUT / "pulsar.png")


def f_power():
    """検出器の中の光のパワー（論文 Sec. III の値）：レーザー 20 W → ビームスプリッタ 700 W → 各腕 100 kW"""
    f, ax = blank(5.6, 4.5)
    box(ax, 0.1, 3.5, 2.9, 0.85, "レーザー 20 W", fc=COL.light)
    box(ax, 0.1, 1.9, 2.9, 0.85, "ビームスプリッタ 700 W", fc=COL.pale)
    box(ax, 0.1, 0.3, 2.9, 0.85, "各腕 100 kW", fc=COL.pale)
    arrow(ax, (1.55, 3.45), (1.55, 2.8), color=COL.lblue)   # 赤は本文の結論の色なので、矢印は水色
    arrow(ax, (1.55, 1.85), (1.55, 1.2), color=COL.lblue)
    ax.text(1.85, 3.12, "パワーリサイクリング", ha="left", va="center", fontsize=FS)
    ax.text(1.85, 1.52, "腕の共振器", ha="left", va="center", fontsize=FS)
    ax.set_xlim(0, 5.6); ax.set_ylim(0, 4.5)
    save(f, OUT / "power.png")


def f_scale():
    """連星の大きさと間隔（縮尺どおり、等質量の例）：半径 105 km の円2つ（半径の和 210 km ＝ 1つの直径）、中心の間隔 350 km"""
    k = 0.01  # in/km
    f, ax = blank(5.8, 3.9)
    x0, y0 = 1.12, 2.0
    d, R = 350 * k, 105 * k
    mx = x0 + d / 2
    for x in (x0, x0 + d):
        ax.add_patch(plt.Circle((x, y0), R, fc=COL.blue, ec="none"))
    arrow(ax, (x0 - R, y0 + 1.35), (x0 + R, y0 + 1.35), color=COL.ink, style="<|-|>", lw=1.2)
    ax.text(x0, y0 + 1.5, "直径 ≳210 km", ha="center", va="bottom", fontsize=FS)
    arrow(ax, (x0, y0 - 1.45), (x0 + d, y0 - 1.45), color=COL.red, style="<|-|>", lw=1.6)
    ax.text(mx, y0 - 1.7, "中心の間隔 ≃350 km", ha="center", va="top", fontsize=FS)
    ax.set_xlim(0, 5.8); ax.set_ylim(0, 3.9)
    save(f, OUT / "scale.png")


def f_timeshift():
    """時刻ずらしの模式図：H1 と L1 の雑音（乱数）に同じ形の信号。L1 をずらすと信号が揃わなくなる"""
    rng = np.random.default_rng(7)
    f, ax = blank(5.8, 4.6)
    n = 300
    x = np.linspace(0.9, 5.6, n)

    def noise():
        v = rng.normal(0, 1, n)
        return np.convolve(v, np.ones(4) / 4, mode="same") * 0.11

    def burst(c):
        u = (x - c) / 0.4
        return 0.8 * np.exp(-u ** 2) * np.sin(13 * (x - c))
    rows = [(3.9, "H1", 3.2), (2.4, "L1", 3.2), (0.9, "L1", 4.3)]
    for yy, lab, c in rows:
        ax.plot(x, yy + noise() + burst(c), color=COL.blue, lw=1.2)
        ax.plot([0.9, 5.6], [yy - 0.55] * 2, color=COL.gray, lw=0.6)
    ax.plot([3.2, 3.2], [-0.2, 4.6], color=COL.red, lw=1.0, ls="--")
    ax.text(0.8, 3.9, "H1", ha="right", va="center", fontsize=FS)
    ax.text(0.8, 2.4, "L1", ha="right", va="center", fontsize=FS)
    ax.text(0.8, 0.9, "L1\nずらし", ha="right", va="center", fontsize=FS)
    arrow(ax, (3.25, -0.12), (4.25, -0.12), color=COL.red, lw=1.6)
    ax.set_xlim(0, 5.8); ax.set_ylim(-0.3, 4.6)
    save(f, OUT / "timeshift.png")


if __name__ == "__main__":
    names = sys.argv[1:] or [k[2:] for k in list(globals()) if k.startswith("f_")]
    for nm in names:
        globals()["f_" + nm]()
