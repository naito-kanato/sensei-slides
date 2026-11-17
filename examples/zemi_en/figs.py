"""Figures we draw ourselves for the paper review (first observation of gravitational waves, English deck).

    python figs.py            # write all figures to figs/
    python figs.py michelson  # redraw only some (function name without the f_ prefix)

Each figure is drawn at the size it fills on the slide and placed at that width, so the text stays at 14 pt.
Several functions follow the figures of the earlier version of this sample (same paper).
"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle

SKILL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILL / "scripts"))
from figkit import COL, arrow, blank, callout, fig, save  # noqa: E402

OUT = Path(__file__).parent / "figs"
FS = 14


def f_strain():
    """実物：輪に並べた12個の試験粒子（波は紙面に垂直に進む、+偏光）
    気づく：横に伸びると縦に縮み、半周期後には逆になる（元の輪を灰の破線で重ねて比べる）
    配置：左から時間順に3つ並べる（波の前・1/4 周期・3/4 周期）
    ラベル：Before／1/4 period／3/4 period
    置き方：本文の下に横長に（上に文・下に図。s.figure_below が描いた幅のまま置く）
    """
    f, ax = blank(7.4, 2.65)   # 上の文の塊（3行）の下に縮めずに入る大きさ（同じ座標を縮めて描く。文字は 14pt のまま）
    th = np.linspace(0, 2 * np.pi, 13)[:-1]
    ring = np.linspace(0, 2 * np.pi, 100)
    r, cy = 0.95, 1.75
    for k, (sx, sy, name) in enumerate([(1, 1, "Before"), (1.25, 0.8, "1/4 period"), (0.8, 1.25, "3/4 period")]):
        cx = 1.4 + k * 2.8
        ax.plot(cx + r * np.cos(ring), cy + r * np.sin(ring), color=COL.gray, lw=1.0, ls="--")
        ax.scatter(cx + r * sx * np.cos(th), cy + r * sy * np.sin(th), s=55, color=COL.blue, zorder=3)
        ax.text(cx, 0.3, name, ha="center", fontsize=FS)
        if sx > 1:
            arrow(ax, (cx - 0.75, cy), (cx + 0.75, cy), color=COL.gray, style="<|-|>", lw=1.0, ms=12)
        elif sy > 1:
            arrow(ax, (cx, cy - 0.75), (cx, cy + 0.75), color=COL.gray, style="<|-|>", lw=1.0, ms=12)
    ax.set_xlim(0, 8.4); ax.set_ylim(0, 3.0)
    save(f, OUT / "s02.png")


def f_pulsar():
    """実物：パルサーと伴星の連星、2つの軌道（前の軌道＝灰の破線、今の軌道＝青の実線）
    気づく：軌道がだんだん縮む（重力波でエネルギーを失う）。前の軌道と今の軌道を同じ図に重ねる
    配置：真上から見た軌道、縮む向きを赤い矢印1本
    ラベル：Pulsar／Companion／Orbital decay
    """
    f, ax = blank(5.6, 4.0)
    cx, cy = 2.8, 1.85
    ring = np.linspace(0, 2 * np.pi, 200)
    ax.plot(cx + 1.4 * np.cos(ring), cy + 1.4 * np.sin(ring), color=COL.gray, lw=1.0, ls="--")
    ax.plot(cx + 0.85 * np.cos(ring), cy + 0.85 * np.sin(ring), color=COL.lblue, lw=1.6)
    ax.add_patch(plt.Circle((cx + 0.85, cy), 0.18, fc=COL.blue, ec="none"))
    ax.add_patch(plt.Circle((cx - 0.85, cy), 0.13, fc=COL.gray, ec="none"))
    ax.text(cx + 1.55, cy, "Pulsar", ha="left", va="center", fontsize=FS)
    ax.text(cx - 1.55, cy, "Companion", ha="right", va="center", fontsize=FS)
    th = 0.9
    arrow(ax, (cx + 1.4 * np.cos(th), cy + 1.4 * np.sin(th)), (cx + 0.85 * np.cos(th) + 0.02, cy + 0.85 * np.sin(th) + 0.02),
          color=COL.red, lw=1.6)
    ax.text(cx + 0.95, cy + 1.22, "Orbital decay", ha="left", va="bottom", fontsize=FS)
    ax.set_xlim(0, 5.6); ax.set_ylim(0, 4.0)
    save(f, OUT / "s03.png")


def f_michelson():
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
    save(f, OUT / "s05.png")


def f_ruler():
    """実物：対数目盛りの長さの物差し（腕 4 km・陽子の幅 1.7×10⁻¹⁵ m・腕の長さの差 ΔL ≈ 4×10⁻¹⁸ m を縦棒で立てる）
    気づく：ΔL は陽子よりさらに約 400 分の 1 小さい（ΔL と陽子の間だけ赤い両矢印、腕の 4 km は右端の比べの相手）
    配置：横一本の対数の物差し、左が小さい
    ラベル：ΔL ≈ 4×10⁻¹⁸ m／Proton 1.7×10⁻¹⁵ m／Arm 4 km（＋1/400）
    置き方：本文の下に横長に（上に文・下に図。s.figure_below が描いた幅のまま置く）
    """
    f, ax = fig(8.6, 2.1)
    f.subplots_adjust(left=0.03, right=0.97, bottom=0.34, top=0.97)   # 軸を図いっぱいに（切り詰めたあとの幅＝置く幅）
    ax.set_xscale("log")
    ax.set_xlim(1e-20, 1e5); ax.set_ylim(0, 1.05)
    ax.spines["left"].set_visible(False)
    ax.set_yticks([])
    ax.set_xticks([10.0 ** k for k in range(-18, 4, 3)])
    ax.minorticks_off()
    ax.set_xlabel("Length (m)")
    marks = [(4e-18, 0.72, COL.red, r"$\mathregular{\Delta L \approx 4\times10^{-18}}$ m", "left"),   # 書体を目盛り・ほかのラベルにそろえる
             (1.7e-15, 0.32, COL.blue, r"Proton $\mathregular{1.7\times10^{-15}}$ m", "left"),
             (4e3, 0.55, COL.blue, "Arm 4 km", "right")]
    for x, h, c, lab, ha in marks:
        ax.plot([x, x], [0, h], color=c, lw=2.0)
        ax.plot([x], [h], "o", color=c, ms=7)
        ax.text(x, h + 0.07, lab, ha=ha, va="bottom", fontsize=FS)
    arrow(ax, (4e-18, 0.13), (1.7e-15, 0.13), color=COL.red, style="<|-|>", lw=1.0, ms=10)
    ax.text(4e-15, 0.13, "1/400", ha="left", va="center", fontsize=FS, color=COL.red)
    save(f, OUT / "s06.png")


def f_cavities():
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
    save(f, OUT / "s07.png")


def f_scale():
    """実物：等しい2つのブラックホールの地平面（半径 105 km の円2つ、縮尺どおり）、中心間 350 km、公転の向き（軌道の上下の弧）
    気づく：半径の和 210 km が中心間 350 km にぎりぎり収まる＝それほど小さく重い物体（中心間の矢印を赤）
    配置：横に並べた断面（縮尺 0.0075 in/km。大きな無地の円2つだけでは言うことが少なく見えたので、円を小さくし公転の向きを添えた）
    ラベル：Sum of radii ≳210 km（左の円の上）／Orbit 75 Hz／Center separation ≃350 km／Horizon
    """
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
    ax.text(mx, y0 + d / 2 + 0.14, "Orbit 75 Hz", ha="center", va="bottom", fontsize=FS)
    for x in (x0, x0 + d):
        ax.add_patch(plt.Circle((x, y0), R, fc=COL.blue, ec="none"))
    arrow(ax, (x0 - R, y0 + R + 0.14), (x0 + R, y0 + R + 0.14), color=COL.ink, style="<|-|>", lw=1.0, ms=12)
    ax.text(x0, y0 + R + 0.24, "Sum of radii\n≳210 km", ha="center", va="bottom", fontsize=FS, linespacing=1.1)
    yb = y0 - d / 2 - 0.1
    ax.plot([x0, x0], [yb - 0.08, y0 - R - 0.06], color=COL.gray, lw=0.8, ls=":")
    ax.plot([x0 + d, x0 + d], [yb - 0.08, y0 - R - 0.06], color=COL.gray, lw=0.8, ls=":")
    arrow(ax, (x0, yb), (x0 + d, yb), color=COL.red, style="<|-|>", lw=1.4, ms=12)
    ax.text(mx, yb - 0.22, "Center separation ≃350 km", ha="center", va="top", fontsize=FS)
    callout(ax, "Horizon", (x0 + d + R * np.cos(0.5), y0 + R * np.sin(0.5)), (x0 + d + 0.75, y0 + 1.45), boxed=False)
    ax.set_xlim(0, 5.8); ax.set_ylim(0, 3.9)
    save(f, OUT / "s12.png")


def f_timeshift():
    """実物：H1 と L1 の記録（雑音の上に同じ信号）、L1 をずらしたもう1本
    気づく：L1 を 10 ms よりずっと大きくずらすと、本物の信号は H1 と並ばなくなる（ずらす前の L1 を比べの相手に同じ図に）
    配置：上から H1・L1・ずらした L1 の3段、信号の時刻に赤の破線
    ラベル：H1／L1／L1 shifted（＋Shift ≫10 ms）
    """
    rng = np.random.default_rng(7)
    f, ax = blank(5.8, 4.9)
    n = 300
    x = np.linspace(0.9, 5.6, n)

    def noise():
        v = rng.normal(0, 1, n)
        return np.convolve(v, np.ones(4) / 4, mode="same") * 0.11

    def burst(c):
        u = (x - c) / 0.4
        return 0.8 * np.exp(-u ** 2) * np.sin(13 * (x - c))
    rows = [(4.2, 3.2), (2.7, 3.2), (1.2, 4.3)]
    for yy, c in rows:
        ax.plot(x, yy + noise() + burst(c), color=COL.blue, lw=1.2)
        ax.plot([0.9, 5.6], [yy - 0.55] * 2, color=COL.gray, lw=0.6)
    ax.plot([3.2, 3.2], [0.45, 4.9], color=COL.red, lw=1.0, ls="--")
    ax.text(0.8, 4.2, "H1", ha="right", va="center", fontsize=FS)
    ax.text(0.8, 2.7, "L1", ha="right", va="center", fontsize=FS)
    ax.text(0.8, 1.2, "L1\nshifted", ha="right", va="center", fontsize=FS)
    arrow(ax, (3.25, 0.4), (4.25, 0.4), color=COL.red, lw=1.4, ms=12)
    ax.text(4.4, 0.4, r"Shift $\gg$10 ms", ha="left", va="center", fontsize=FS)
    ax.set_xlim(0, 5.8); ax.set_ylim(0.0, 4.9)
    save(f, OUT / "s13.png")


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    names = sys.argv[1:] or [k[2:] for k in list(globals()) if k.startswith("f_")]
    for nm in names:
        globals()["f_" + nm]()
