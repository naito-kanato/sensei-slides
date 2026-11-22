"""図。python figs.py [名前 ...]（名前は f_ を除いた部分）。データの棒グラフは scaffold.py が設計メモの3b節から描いた。TODO の図を描く

論文の図の切り出しは paper_figs/ にある（論文は CC BY 3.0。出典と変更は paper_figs/ATTRIBUTION.md）。f_s07 などはそれを figs/ に写す。"""
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parents[1]   # 見本はリポジトリの scripts/ を使う
sys.path.insert(0, str(SKILL / "scripts"))
from figkit import COL, LW, arrow, blank, box, fig, noticks, save  # noqa: E402,F401
import figlib  # noqa: E402,F401
import figschema  # noqa: E402,F401
import numpy as np  # noqa: E402
from figkit import callout  # noqa: E402
from matplotlib.patches import Circle, Rectangle, Wedge  # noqa: E402

OUT = HERE / "figs"
OUT.mkdir(exist_ok=True)
PAPER = HERE / "paper_figs"   # 論文の図の切り出し（スキルで作ったときは pdf_pages.py crop で figs/ に直接書いた）


def _paper(name):
    shutil.copy2(PAPER / name, OUT / name)


def f_s02():
    """実物：自由に浮かぶ粒子12個の輪（重力波は紙面に垂直に通る）
    気づく：横に伸びると縦が縮み、半周期後には逆になる
    配置：前後（3コマを横に並べ、元の輪を灰の破線で重ねる）
    ラベル：t = 0, t = T/4, t = 3T/4
    図の案：仕組み：模式図：a ring of free particles stretched one way, then the other, over one wave cycle（伸びは誇張）"""
    f, ax = blank(5.6, 3.0)
    th = np.linspace(0, 2 * np.pi, 12, endpoint=False)
    tt = np.linspace(0, 2 * np.pi, 200)
    r, h0, cy = 0.62, 0.28, 1.55
    for cx, sgn, lab in [(0.95, 0.0, "$t = 0$"), (2.8, 1.0, "$t = T/4$"), (4.65, -1.0, "$t = 3T/4$")]:
        ax.plot(cx + r * np.cos(tt), cy + r * np.sin(tt), color=COL.gray, lw=1.0, ls="--")
        xy = np.c_[cx + r * (1 + sgn * h0) * np.cos(th), cy + r * (1 - sgn * h0) * np.sin(th)]
        ax.scatter(xy[:, 0], xy[:, 1], s=60, color=COL.blue, edgecolors="none", zorder=3)
        ax.text(cx, 0.42, lab, ha="center", va="center")
    ax.text(2.8, 2.78, "dots = free masses, ring shape = stretch now", ha="center", va="center")
    save(f, OUT / "s02.png")


def f_s04():
    """実物：レーザー・ビームスプリッター・直交する2本の腕と鏡（テストマス）・検出器（Fig. 3 をもとに、縮尺なし）
    気づく：x の腕が伸びると y の腕が縮む（灰の破線が動いた鏡）
    配置：上から見た平面図
    ラベル：Laser, Beam splitter, Mirror, Detector（腕の長さは $L$ の寸法線）
    図の案：仕組み：模式図：Michelson interferometer drawn after Fig. 3（Power/Signal recycling の鏡は省いた。6枚目で言う）"""
    f, ax = blank(5.6, 4.2)
    y0, xb = 1.5, 1.9
    red = COL.red
    box(ax, 0.15, y0 - 0.25, 0.95, 0.5, text="Laser", fc=COL.pale)
    ax.plot([1.1, 5.0], [y0, y0], color=red, lw=2.0, zorder=1)
    ax.plot([xb, xb], [y0, 3.6], color=red, lw=2.0, zorder=1)
    ax.plot([xb, xb], [y0, 0.8], color=red, lw=1.5, ls="--", zorder=1)
    ax.plot([xb - 0.2, xb + 0.2], [y0 - 0.2, y0 + 0.2], color=COL.blue, lw=3.0, zorder=2)

    def mirror(x, y, w, h):
        ax.add_patch(Rectangle((x - w / 2, y - h / 2), w, h, fc=COL.sand, ec="none", zorder=2))

    mirror(2.55, y0, 0.12, 0.5)
    mirror(5.0, y0, 0.12, 0.5)
    mirror(xb, 2.15, 0.5, 0.12)
    mirror(xb, 3.6, 0.5, 0.12)
    ax.add_patch(Rectangle((5.25 - 0.06, y0 - 0.25), 0.12, 0.5, fc="none", ec=COL.gray, ls="--", lw=1.0))
    ax.add_patch(Rectangle((xb - 0.25, 3.35 - 0.06), 0.5, 0.12, fc="none", ec=COL.gray, ls="--", lw=1.0))
    arrow(ax, (5.08, y0 + 0.42), (5.32, y0 + 0.42), lw=1.0, ms=10)
    arrow(ax, (xb + 0.38, 3.66), (xb + 0.38, 3.36), lw=1.0, ms=10)
    ax.add_patch(Wedge((xb, 0.72), 0.18, 180, 360, fc=COL.blue, ec="none"))
    ax.text(xb + 0.32, 0.6, "Detector", va="center")
    arrow(ax, (2.55, 0.98), (5.0, 0.98), lw=1.0, ms=10, style="<|-|>")
    ax.text(3.78, 0.86, "$L$", ha="center", va="top")
    callout(ax, "Beam splitter", (xb - 0.12, y0 + 0.12), (0.95, 2.6), boxed=False)
    callout(ax, "Mirror", (5.0, y0 + 0.27), (4.55, 2.6), boxed=False)
    ax.text(2.75, 4.1, "red = light path\none arm stretches,\nthe other shrinks", va="top")
    save(f, OUT / "s04.png")


def f_s07():
    """実物：資料の図：Fig. 3(b)（pdf_pages.py crop で切り出し済み。paper_figs/ATTRIBUTION.md）"""
    _paper("s07.png")


def f_s08():
    """実物：資料の図：Fig. 1 上の段（切り出し済み。paper_figs/ATTRIBUTION.md）"""
    _paper("s08.png")


def f_s09():
    """実物：資料の図：Fig. 1 下の段（切り出し済み。paper_figs/ATTRIBUTION.md）"""
    _paper("s09.png")


def f_s10():
    """実物：資料の図：Fig. 2 の上のパネル（波形と地平面の挿絵。切り出し済み。下のパネルは字が小さくなるので原稿で言う）"""
    _paper("s10.png")


def f_s11():
    """実物：同じ質量の2つのブラックホール（地平面の円）を縮尺どおりに、中心間 350 km
    気づく：半径の和 ≳210 km に対して 350 km しか離れていない（すき間がわずか）
    配置：横に並べた断面（縮尺 1 in = 100 km、上に 100 km の物差し）
    ラベル：350 km, radii sum ≳ 210 km, 100 km
    図の案：仕組み：模式図：scale drawing of two equal masses ≃350 km apart, summed Schwarzschild radii ≳210 km（各半径 105 km＝210 の半分）"""
    f, ax = blank(6.6, 4.3)
    cy, c1, c2, R = 2.25, 1.55, 5.05, 1.05
    for c in (c1, c2):
        ax.add_patch(Circle((c, cy), R, fc=COL.blue, ec="none"))
        ax.plot([c, c], [cy - R - 0.08, 0.86], color=COL.gray, lw=1.0, ls=":")
    ax.plot([c1, c1 + R], [cy, cy], color=COL.red, lw=2.5)
    ax.plot([c2 - R, c2], [cy, cy], color=COL.red, lw=2.5)
    ax.plot([c1 + R, c2 - R], [cy, cy], color=COL.gray, lw=1.0, ls="--")
    ax.text(c1 + R / 2, cy + 0.12, "$R_S$", color="white", ha="center", va="bottom")
    ax.text(c2 - R / 2, cy + 0.12, "$R_S$", color="white", ha="center", va="bottom")
    ax.text(3.3, 3.62, r"radii sum $\gtrsim$ 210 km", ha="center", va="bottom")
    ax.plot([0.3, 1.3], [4.1, 4.1], color="#222222", lw=2.0)
    ax.text(0.8, 3.98, "100 km", ha="center", va="top")
    arrow(ax, (c1, 0.8), (c2, 0.8), lw=1.0, ms=10, style="<|-|>")
    ax.text(3.3, 0.68, "350 km", ha="center", va="top")
    ax.text(3.3, 0.08, "circles = horizon size, gap = separation at 75 Hz", ha="center", va="bottom")
    save(f, OUT / "s11.png")


def f_s13():
    """実物：H1 と L1 の雑音の波形（2段）。本物の信号（赤）が両方に同じ時刻で入っている
    気づく：L1 を 10 ms よりずっと大きくずらすと、本物の信号はもう揃わない（残る一致は雑音だけ）
    配置：前後（上＝元のデータ、下＝L1 をずらしたデータ）
    ラベル：Original, L1 shifted by Δt ≫ 10 ms
    図の案：仕組み：模式図：time shift: H1 and L1 noise traces, L1 slid by an offset much larger than 10 ms（概略）"""
    f, ax = blank(6.6, 4.3)
    rng = np.random.default_rng(3)
    x = np.linspace(0.8, 6.4, 700)

    def trace(y0, xc):
        n = np.convolve(rng.normal(size=x.size), np.ones(5) / 5, "same")
        n = 0.07 * n / n.std()
        u = (x - (xc - 0.3)) / 0.6
        m = (u >= 0) & (u <= 1)
        sig = np.zeros_like(x)
        sig[m] = (0.06 + 0.2 * u[m]) * np.sin(2 * np.pi * (3 * u[m] + 4 * u[m] ** 2))
        base = np.where(m, np.nan, y0 + n)
        ax.plot(x, base, color=COL.lblue, lw=1.0)
        ax.plot(x[m], y0 + n[m] + sig[m], color=COL.red, lw=1.5)

    ax.text(0.3, 4.15, "Original", va="center", fontweight="bold")
    ax.text(0.3, 2.2, r"L1 shifted by $\Delta t \gg$ 10 ms", va="center", fontweight="bold")
    for y0, lab, xc in [(3.4, "H1", 3.3), (2.8, "L1", 3.3), (1.6, "H1", 3.3), (1.0, "L1", 4.9)]:
        ax.text(0.35, y0, lab, va="center")
        trace(y0, xc)
    ax.plot([3.3, 3.3], [2.45, 3.8], color=COL.gray, lw=1.0, ls="--")
    ax.plot([3.3, 3.3], [0.65, 1.95], color=COL.gray, lw=1.0, ls="--")
    arrow(ax, (3.3, 0.45), (4.9, 0.45), lw=1.0, ms=10)
    save(f, OUT / "s13.png")


def f_s14():
    """実物：資料の図：Fig. 4 右（切り出し済み。GW150914 の赤い輪はスライドで s.oval）"""
    _paper("s14.png")


def f_s15():
    """比べる：棒グラフ：データ2（データ2：Black hole masses before and after the m。scaffold.py が3b節の表から描いた。強調する棒は highlight）"""
    f, ax = fig(5.6, 0.7 + 0.55 * 3)
    figlib.bars(ax, ["Primary (before)", "Secondary (before)", "Final (after)"], [36, 29, 62], highlight=2, unit=" $M_\odot$")
    save(f, OUT / "s15.png")


def f_s18():
    """実物：資料の図：Fig. 1 上の段の右（想定質問 Q3 の図。切り出し済み。paper_figs/ATTRIBUTION.md）"""
    _paper("s18.png")


if __name__ == "__main__":
    names = sys.argv[1:] or [n[2:] for n in list(globals()) if n.startswith("f_")]
    for n in names:
        globals()["f_" + n]()
