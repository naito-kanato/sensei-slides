"""型の見本で使う図。shift_・same_wave は説明のための例（値は例。実在の測定ではない）。
strain・michelson・power・scale・timeshift と en_michelson・en_cavities は、以前のゼミの見本（日本語・英語）の図を写したもの
（見本を作り直したあとも、型の見本の見た目が変わらないように。論文 Abbott et al., PRL 116, 061102 (2016) をもとに描いた）。
論文の図の切り出しは paper_figs/（出典は paper_figs/ATTRIBUTION.md）。
en_ で始まる図は英語版の見本（build_en.py）用：文字だけ英語にした同じ図。
en_strain は、英語の論文紹介の見本の輪の図（下に横長に置く幅 8.4 in）を、見本帳の本文の右に置く幅（約 5.6 in）で描き直したもの
（日本語の figs/strain.png と同じ大きさ。縮めて置くと図の文字が 14pt を下回る）。

    python figs.py
"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle

SKILL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILL / "scripts"))
from figkit import COL, arrow, blank, box, callout, fig, save  # noqa: E402

OUT = Path(__file__).parent / "figs"
FS = 14  # 図中ラベル


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
    """重力波が通ると、輪に並んだ粒子が縦横交互に伸び縮みする（+ 偏光の模式図）。f_strain と同じ図を英語で"""
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


def f_strain():
    """重力波が通ると、輪に並んだ粒子が縦横交互に伸び縮みする（+ 偏光の模式図）。伸びる向きを細い両矢印で。
    置く幅（2枚目の本文の右、約 5.7 in）で描き、描いた幅のまま置く（以前は 6 in で描いて 5.85 in に縮め、文字が 13.4pt になった）"""
    f, ax = blank(5.6, 3.2)
    th = np.linspace(0, 2 * np.pi, 13)[:-1]
    ring = np.linspace(0, 2 * np.pi, 100)
    r, cy = 0.7, 1.9
    for k, (sx, sy, name) in enumerate([(1, 1, "波の前"), (1.25, 0.8, "1/4 周期後"), (0.8, 1.25, "3/4 周期後")]):
        cx = 0.95 + k * 1.85
        ax.plot(cx + r * np.cos(ring), cy + r * np.sin(ring), color=COL.gray, lw=1.0, ls="--")
        ax.scatter(cx + r * sx * np.cos(th), cy + r * sy * np.sin(th), s=55, color=COL.blue, zorder=3)
        ax.text(cx, 0.3, name, ha="center", fontsize=FS)
        if sx > 1:      # 横に伸びる
            arrow(ax, (cx - 0.55, cy), (cx + 0.55, cy), color=COL.gray, style="<|-|>", lw=1.0, ms=12)
        elif sy > 1:    # 縦に伸びる
            arrow(ax, (cx, cy - 0.55), (cx, cy + 0.55), color=COL.gray, style="<|-|>", lw=1.0, ms=12)
    ax.set_xlim(0, 5.6); ax.set_ylim(0, 3.2)
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
    """連星の大きさと間隔（縮尺どおり、等質量の例）：半径 105 km の円2つ（半径の和 210 km ＝ 1つの直径）、中心の間隔 350 km。
    公転の向き（軌道の上下の弧）を添え、円は小さめに（大きな無地の円2つだけでは、言うことが少なく見えた）"""
    from matplotlib.patches import FancyArrowPatch
    k = 0.0075  # in/km
    f, ax = blank(5.8, 3.9)
    mx, y0 = 2.9, 1.85
    d, R = 350 * k, 105 * k
    x0 = mx - d / 2
    for a0, a1 in ((65, 115), (245, 295)):            # 公転の向き（2つが回る軌道の上下に、反時計回りの弧）
        t0, t1 = np.radians(a0), np.radians(a1)
        ax.add_patch(FancyArrowPatch((mx + d / 2 * np.cos(t0), y0 + d / 2 * np.sin(t0)),
                                     (mx + d / 2 * np.cos(t1), y0 + d / 2 * np.sin(t1)),
                                     connectionstyle="arc3,rad=0.12", arrowstyle="-|>", mutation_scale=16,
                                     color=COL.lblue, lw=2.0))
    ax.text(mx, y0 + d / 2 + 0.14, "公転 75 Hz", ha="center", va="bottom", fontsize=FS)
    for x in (x0, x0 + d):
        ax.add_patch(plt.Circle((x, y0), R, fc=COL.blue, ec="none"))
    arrow(ax, (x0 - R, y0 + R + 0.14), (x0 + R, y0 + R + 0.14), color=COL.ink, style="<|-|>", lw=1.0, ms=12)
    ax.text(x0, y0 + R + 0.24, "直径 ≳210 km", ha="center", va="bottom", fontsize=FS)
    yb = y0 - d / 2 - 0.1
    ax.plot([x0, x0], [yb - 0.08, y0 - R - 0.06], color=COL.gray, lw=0.8, ls=":")
    ax.plot([x0 + d, x0 + d], [yb - 0.08, y0 - R - 0.06], color=COL.gray, lw=0.8, ls=":")
    arrow(ax, (x0, yb), (x0 + d, yb), color=COL.red, style="<|-|>", lw=1.4, ms=12)
    ax.text(mx, yb - 0.12, "中心の間隔 ≃350 km", ha="center", va="top", fontsize=FS)
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


def f_en_michelson():
    """実物：マイケルソン干渉計（レーザー・ビームスプリッター・2本の 4 km の腕・吊るした鏡・光検出器、光路は赤）
    気づく：波が来ると片方の腕が伸び、もう片方が縮む（鏡の元の位置を灰の破線で残し、ずれを細い矢印で）
    配置：真上から見た L 字（Fig. 3 をもとに、腕の共振器とリサイクリングの鏡は省く）
    ラベル：Laser／Photodetector／Free-hanging test mass（＋腕の長さ L_x, L_y）
    """
    f, ax = blank(6.0, 4.6)
    bx, by = 1.8, 1.45
    mx, my = 5.3, 4.05          # x-mirror face, y-mirror face
    ax.plot([0.7, mx], [by, by], color=COL.red, lw=2.0)                 # laser -> x arm
    ax.plot([bx, bx], [by, my], color=COL.red, lw=2.0)                  # y arm
    ax.plot([bx, bx], [0.55, by], color=COL.red, lw=1.4, ls="--")       # to the detector
    ax.plot([bx - 0.26, bx + 0.26], [by - 0.26, by + 0.26], color=COL.ink, lw=2.5)   # beam splitter
    # mirrors (test masses) and their displaced positions while the wave passes
    ax.add_patch(Rectangle((mx, by - 0.36), 0.19, 0.72, fc=COL.pale, ec=COL.ink, lw=1.2))
    ax.add_patch(Rectangle((mx + 0.22, by - 0.36), 0.19, 0.72, fc="none", ec=COL.gray, lw=1.0, ls="--"))
    ax.add_patch(Rectangle((bx - 0.36, my), 0.72, 0.19, fc=COL.pale, ec=COL.ink, lw=1.2))
    ax.add_patch(Rectangle((bx - 0.36, my - 0.22), 0.72, 0.19, fc="none", ec=COL.gray, lw=1.0, ls="--"))
    ax.add_patch(Rectangle((0.0, by - 0.26), 0.7, 0.52, fc=COL.ink, ec=COL.ink))     # laser
    ax.add_patch(Rectangle((bx - 0.22, 0.32), 0.44, 0.22, fc=COL.ink, ec=COL.ink))   # photodetector
    ax.text(0.35, by - 0.45, "Laser", ha="center", va="top", fontsize=FS)
    ax.text(bx + 0.35, 0.43, "Photodetector", ha="left", va="center", fontsize=FS)
    callout(ax, "Free-hanging\ntest mass", (mx + 0.1, by + 0.4), (4.3, 3.15), boxed=False)
    arrow(ax, (2.1, 0.95), (mx - 0.05, 0.95), color=COL.ink, style="<|-|>", lw=1.0, ms=12)
    ax.text(3.7, 0.78, r"$L_x = 4$ km", ha="center", va="top", fontsize=FS)
    arrow(ax, (2.35, 1.75), (2.35, my - 0.05), color=COL.ink, style="<|-|>", lw=1.0, ms=12)
    ax.text(2.5, 2.85, r"$L_y = 4$ km", ha="left", va="center", fontsize=FS)
    ax.set_xlim(-0.1, 6.0); ax.set_ylim(0.0, 4.6)
    save(f, OUT / "en_michelson.png")


def f_en_cavities():
    """実物：Advanced LIGO の光の通り道（レーザー → パワーリサイクリングの鏡 → ビームスプリッター → 2本の 4 km の腕の共振器 → 光検出器）
    気づく：20 W の光が、ビームスプリッターで 700 W、腕の中で 100 kW になる（光の線の太さを 20 W・700 W・100 kW の3段に）
    配置：真上から見た L 字（Fig. 3 をもとに、信号リサイクリングの鏡と入力の光学系は省く。腕の共振器は試験質量の鏡2枚の間）
    ラベル：Laser／Power recycling／700 W（赤）／100 kW ×2（＋20 W・腕の長さ 4 km。光検出器は5枚目と同じ黒い四角で、名前は原稿で言う）
    """
    f, ax = blank(5.6, 4.5)
    bx, by = 1.95, 1.6            # beam splitter
    ix, ex = 3.0, 5.3             # x arm: input / end test mass (left face)
    iy, ey = 2.5, 4.25            # y arm: input / end test mass (bottom face)
    t = 0.12                      # mirror thickness
    # light: thin at 20 W, medium at 700 W, thick inside the arm cavities
    ax.plot([0.5, 1.2], [by, by], color=COL.red, lw=1.2)
    ax.plot([1.3, ix], [by, by], color=COL.red, lw=2.0)
    ax.plot([bx, bx], [by, iy], color=COL.red, lw=2.0)
    ax.plot([ix + t, ex], [by, by], color=COL.red, lw=3.4)
    ax.plot([bx, bx], [iy + t, ey], color=COL.red, lw=3.4)
    ax.plot([bx, bx], [0.52, by], color=COL.red, lw=1.2, ls="--")
    ax.plot([bx - 0.25, bx + 0.25], [by - 0.25, by + 0.25], color=COL.ink, lw=2.5)        # beam splitter
    # mirrors: power recycling and the four test masses
    ax.add_patch(Rectangle((1.2, by - 0.32), 0.1, 0.64, fc=COL.pale, ec=COL.ink, lw=1.2))
    for x in (ix, ex):
        ax.add_patch(Rectangle((x, by - 0.32), t, 0.64, fc=COL.pale, ec=COL.ink, lw=1.2))
    for y in (iy, ey):
        ax.add_patch(Rectangle((bx - 0.32, y), 0.64, t, fc=COL.pale, ec=COL.ink, lw=1.2))
    ax.add_patch(Rectangle((0.0, by - 0.22), 0.5, 0.44, fc=COL.ink, ec=COL.ink))           # laser
    ax.add_patch(Rectangle((bx - 0.2, 0.32), 0.4, 0.2, fc=COL.ink, ec=COL.ink))            # photodetector
    ax.text(0.25, by - 0.36, "Laser", ha="center", va="top", fontsize=FS)
    ax.text(0.85, by + 0.14, "20 W", ha="center", va="bottom", fontsize=FS)
    ax.text(1.25, by - 0.45, "Power\nrecycling", ha="center", va="top", fontsize=FS)
    ax.text(bx + 0.15, by - 0.2, "700 W", ha="left", va="top", fontsize=FS, color=COL.red)
    ax.text((ix + ex) / 2, by + 0.15, "100 kW", ha="center", va="bottom", fontsize=FS)
    ax.text(bx - 0.18, (iy + ey) / 2, "100 kW", ha="right", va="center", fontsize=FS)
    # arm lengths
    arrow(ax, (ix + 0.06, 0.95), (ex + 0.06, 0.95), color=COL.ink, style="<|-|>", lw=1.0, ms=12)
    ax.text((ix + ex) / 2 + 0.06, 0.82, "4 km", ha="center", va="top", fontsize=FS)
    arrow(ax, (bx + 0.55, iy + 0.06), (bx + 0.55, ey + 0.06), color=COL.ink, style="<|-|>", lw=1.0, ms=12)
    ax.text(bx + 0.68, (iy + ey) / 2, "4 km", ha="left", va="center", fontsize=FS)
    ax.set_xlim(-0.05, 5.6); ax.set_ylim(0.2, 4.5)
    save(f, OUT / "en_cavities.png")


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    names = sys.argv[1:] or [n[2:] for n in dict(globals()) if n.startswith("f_")]
    for n in names:
        globals()["f_" + n]()
