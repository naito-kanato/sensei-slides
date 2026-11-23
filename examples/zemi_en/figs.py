"""図。python figs.py [名前 ...]（名前は f_ を除いた部分）。データの棒グラフは scaffold.py が設計メモの3b節から描いた。TODO の図を描く"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parents[1]   # 見本はリポジトリの scripts/ を使う
sys.path.insert(0, str(SKILL / "scripts"))
from figkit import COL, LW, arrow, blank, box, fig, noticks, save  # noqa: E402,F401
import figlib  # noqa: E402,F401
import figschema  # noqa: E402,F401

OUT = HERE / "figs"
OUT.mkdir(exist_ok=True)


from PIL import Image, ImageDraw  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import Rectangle, Wedge  # noqa: E402
from figkit import callout  # noqa: E402

SRC = HERE / "paper_figs"     # pdf_pages.py extract --dpi 400（見本では使う頁だけ。出典は paper_figs/ATTRIBUTION.md）
PX = 1.1 * 2.0            # 1545-px-wide view of the page -> 400-dpi pixels
DPI = 400.0               # 1 page inch = 400 px, so scale 1.0 = printed size


def _crop(page, box, white=()):
    """Crop a page image (box in view coordinates); white = rectangles to blank out (panel letters)."""
    im = Image.open(SRC / f"p{page:02d}.png").convert("RGB")
    c = im.crop(tuple(int(round(v * PX)) for v in box))
    d = ImageDraw.Draw(c)
    for wx0, wy0, wx1, wy1 in white:
        d.rectangle([(wx0 - box[0]) * PX, (wy0 - box[1]) * PX, (wx1 - box[0]) * PX, (wy1 - box[1]) * PX], fill="white")
    return np.asarray(c)


def _place(ax, arr, x, y, scale):
    """Place a crop at (x, y) inches, enlarged by scale over the printed size."""
    h, w = arr.shape[:2]
    Wd, Ht = w / DPI * scale, h / DPI * scale
    xl, yl = ax.get_xlim(), ax.get_ylim()
    ax.imshow(arr, extent=(x, x + Wd, y, y + Ht), interpolation="lanczos", aspect="auto", zorder=1)
    ax.set_xlim(xl)
    ax.set_ylim(yl)
    return Wd, Ht


def _pt(box, px, py, x, y, Ht, scale):
    """View coordinates of a point in the crop -> figure inches."""
    k = PX / DPI * scale
    return x + (px - box[0]) * k, y + Ht - (py - box[1]) * k


def f_s02():
    """時期：年表（上から古い順に6つ。2015 だけ赤）
    実物：縦の時間の線に点、左に年、右に出来事の名詞
    気づく：直接の観測は 2015 年まで無かった（予言から約100年）
    配置：縦の年表（間隔は等間隔。年に比例させない）
    ラベル：年と出来事の名詞だけ
    """
    f, ax = blank(5.0, 4.0)
    ev = [("1916", "Einstein's prediction"), ("1957", "Chapel Hill conference"), ("1960s", "Weber's resonant bars"),
          ("1975", "Hulse–Taylor binary pulsar"), ("2002–11", "initial interferometers"), ("2015", "Advanced LIGO")]
    xl = 1.3
    ys = np.linspace(3.7, 0.3, len(ev))
    ax.plot([xl, xl], [ys[-1], ys[0]], color=COL.gray, lw=1.5, zorder=1)
    for i, ((yr, txt), y) in enumerate(zip(ev, ys)):
        last = i == len(ev) - 1
        c = COL.red if last else COL.blue
        ax.plot([xl], [y], "o", ms=12 if last else 8, color=c, mec="none", zorder=3)
        ax.text(xl - 0.22, y, yr, ha="right", va="center", color=c, fontweight="bold" if last else "normal")
        ax.text(xl + 0.25, y, txt, ha="left", va="center", color=c if last else "#222222",
                fontweight="bold" if last else "normal")
    save(f, OUT / "s02.png")


def f_s04():
    """仕組み：模式図（論文 Fig. 3 の主図を描き直し。投影で読める字にするため。パワー・シグナルリサイクリング鏡は省略し、5枚目の流れ図で扱う）
    実物：レーザー、ビームスプリッター、2本の腕の両端の試験質量（鏡）、光検出器。光路は赤、検出器への光は破線
    気づく：片方の腕が伸び、もう片方が縮む（灰の破線が動いた鏡。誇張して描いた）
    配置：上から見た平面図（レーザー左、腕は右と上、検出器は下）
    ラベル：Laser, Beam splitter, Test mass, Photodetector, L_x, L_y
    """
    f, ax = blank(5.6, 4.0)
    red, sand, gray = COL.red, COL.sand, COL.gray
    bx, by = 1.75, 1.15
    ax.add_patch(Rectangle((0.15, by - 0.2), 0.8, 0.4, fc=gray, ec="none"))
    ax.text(0.55, by - 0.32, "Laser", ha="center", va="top")
    ax.plot([0.95, 4.95], [by, by], color=red, lw=2.2, zorder=2)
    ax.plot([bx, bx], [by, 3.25], color=red, lw=2.2, zorder=2)
    ax.plot([bx, bx], [by, 0.5], color=red, lw=1.8, ls="--", zorder=2)
    ax.plot([bx - 0.2, bx + 0.2], [by - 0.2, by + 0.2], color=COL.blue, lw=3, zorder=3)
    ax.text(bx - 0.25, by + 0.3, "Beam splitter", ha="right", va="bottom")
    # test masses (mirrors)
    for (x, y, w, h) in [(2.4, by - 0.25, 0.12, 0.5), (4.95, by - 0.25, 0.12, 0.5),
                         (bx - 0.25, 1.8, 0.5, 0.12), (bx - 0.25, 3.25, 0.5, 0.12)]:
        ax.add_patch(Rectangle((x, y), w, h, fc=sand, ec="none", zorder=3))
    # moved end mirrors: x arm stretches, y arm shrinks (exaggerated)
    ax.add_patch(Rectangle((5.2, by - 0.25), 0.12, 0.5, fc="none", ec=gray, ls="--", lw=1.0, zorder=3))
    ax.add_patch(Rectangle((bx - 0.25, 3.0), 0.5, 0.12, fc="none", ec=gray, ls="--", lw=1.0, zorder=3))
    arrow(ax, (2.52, 1.75), (4.95, 1.75), lw=1.0, style="<->")
    ax.text(3.75, 1.82, "$L_x$", ha="center", va="bottom")
    arrow(ax, (2.25, 1.92), (2.25, 3.25), lw=1.0, style="<->")
    ax.text(2.35, 2.6, "$L_y$", ha="left", va="center")
    callout(ax, "Test mass", (5.0, by - 0.25), (4.3, 0.45))
    ax.add_patch(Wedge((bx, 0.42), 0.17, 180, 360, fc=COL.blue, ec="none", zorder=3))
    ax.text(bx + 0.3, 0.32, "Photodetector", ha="left", va="center")
    ax.text(1.4, 3.78, "One arm stretches, the other shrinks", ha="left", va="center")
    save(f, OUT / "s04.png")


def f_s06():
    """仕組み：資料の図（Fig. 3(b) の雑音スペクトルを切り出し、1.5倍。(b) の文字は消した）
    実物：H1（赤）・L1（青）の雑音の曲線。100〜300 Hz で最も低い
    気づく：下の曲線ほど静か。鋭い線は較正の信号と電力線
    配置：グラフ1枚、上に読み方の1行
    ラベル：読み方の1行だけ（凡例 H1/L1 は元の図のまま）
    """
    box = (748, 115, 1340, 598)
    a = _crop(4, box, white=[(796, 115, 845, 160)])
    f, ax = blank(5.3, 4.45)
    Wd, Ht = _place(ax, a, 0.2, 0.0, 1.5)
    ax.text(0.2 + Wd / 2, Ht + 0.27, "Lower curve = quieter detector", ha="center", va="center")
    save(f, OUT / "s06.png")


def f_s07():
    """実物：資料の図（Fig. 3(a) の地図を切り出し、3.6倍。(a) の文字は消した）
    実物：H1（左上・赤）と L1（右下・青）、間の破線「10 ms light travel time」
    気づく：2か所は光で 10 ms 離れている
    配置：地図1枚、上に Hanford、下に Livingston の名前
    ラベル：Hanford (H1), Livingston (L1)
    """
    box = (212, 278, 500, 447)
    a = _crop(4, box, white=[(206, 400, 252, 442)])
    f, ax = blank(6.6, 4.3)
    x0, y0, sc = 0.45, 0.45, 3.6
    Wd, Ht = _place(ax, a, x0, y0, sc)
    hx, hy = _pt(box, 268, 302, x0, y0, Ht, sc)
    lx, ly = _pt(box, 410, 425, x0, y0, Ht, sc)
    ax.text(hx, Ht + y0 + 0.22, "Hanford (H1)", ha="center", va="center", color=COL.red, fontweight="bold")
    ax.text(lx, 0.2, "Livingston (L1)", ha="center", va="center", color=COL.blue, fontweight="bold")
    save(f, OUT / "s07.png")


def f_s08():
    """実物：資料の図（Fig. 1 上段の右パネル：L1 の青と、6.9 ms ずらして反転した H1 の橙。×1.5）
    実物：左パネルの縦軸の目盛りと、下段右の時間軸を同じ倍率で継いだ。縦軸の名前は足した
    気づく：2つの曲線がほぼ重なる
    配置：グラフ1枚
    ラベル：Strain (10^-21)（凡例は元の図のまま）
    """
    sc = 1.5
    panel, ticks, strip = (780, 395, 1302, 695), (186, 395, 248, 695), (780, 1340, 1302, 1420)
    f, ax = blank(5.5, 3.25)
    a_s = _crop(2, strip)
    _, hs = _place(ax, a_s, 0.55 + 62 * PX / DPI * sc, 0.0, sc)
    wt, hp = _place(ax, _crop(2, ticks), 0.55, hs, sc)
    _place(ax, _crop(2, panel), 0.55 + wt, hs, sc)
    _, ymid = _pt(panel, 0, 566, 0, hs, hp, sc)
    ax.text(0.22, ymid, "Strain ($10^{-21}$)", rotation=90, ha="center", va="center")
    save(f, OUT / "s08.png")


def f_s09():
    """実物：資料の図（Fig. 1 下段の左パネル：H1 の時間-周波数図。×1.5。カラーバーは省略）
    実物：0.40〜0.43 s で右上がりの明るい筋
    気づく：周波数が時間とともに上がる（チャープ）
    配置：グラフ1枚、上に題
    ラベル：Hanford (H1), chirp
    """
    sc = 1.5
    box = (145, 1088, 776, 1422)
    f, ax = blank(5.6, 3.35)
    Wd, Ht = _place(ax, _crop(2, box), 0.2, 0.0, sc)
    ax.text(0.2 + Wd / 2, Ht + 0.3, "Hanford (H1)", ha="center", va="center", fontweight="bold")
    tx, ty = _pt(box, 674, 1204, 0.2, 0.0, Ht, sc)
    callout(ax, "chirp", (tx, ty), (4.85, Ht + 0.3), color=COL.red)
    save(f, OUT / "s09.png")


def f_s11():
    """仕組み：模式図（タイムスライド）
    実物：H1（赤）と L1（青）の2本の時間の線と、雑音のバースト（縦の短い線）
    気づく：L1 を 10 ms よりずっと大きくずらしても、たまたま重なる組（淡い帯）がある＝雑音だけの一致
    配置：上に H1、下にずらした L1、下にずらしの矢印
    ラベル：shift ≫ 10 ms, noise-only pair
    """
    f, ax = blank(6.6, 4.3)
    x0, x1 = 0.75, 6.4
    yh, yl = 2.85, 1.5
    h1 = [(1.30, .45), (2.05, .30), (2.95, .55), (3.70, .35), (4.45, .40), (5.25, .60), (5.95, .30)]
    l1 = [(1.70, .35), (2.95, .45), (3.40, .30), (4.10, .50), (5.25, .40), (6.10, .35)]
    for x in (2.95, 5.25):
        ax.add_patch(Rectangle((x - 0.14, yl - 0.1), 0.28, yh + 0.75 - yl, fc=COL.pale, ec="none", zorder=0))
    for ys, ev, c, name in [(yh, h1, COL.red, "H1"), (yl, l1, COL.blue, "L1")]:
        ax.plot([x0, x1], [ys, ys], color=c, lw=2.0, zorder=2)
        for x, hgt in ev:
            ax.plot([x, x], [ys, ys + hgt], color=c, lw=2.5, zorder=2)
        ax.text(x0 - 0.15, ys, name, ha="right", va="center", color=c, fontweight="bold")
    arrow(ax, (0.9, 0.95), (1.9, 0.95), color=COL.blue, lw=1.5)
    ax.text(2.05, 0.95, "shift ≫ 10 ms", ha="left", va="center")
    callout(ax, "noise-only pair", (5.25, yh + 0.65), (4.0, 3.95))
    ax.text(3.6, 0.3, "Each shift = one fake experiment", ha="center", va="center")
    save(f, OUT / "s11.png")


def f_s12():
    """実物：資料の図（Fig. 4 右パネル：binary coalescence search。×1.7）
    実物：黒の背景の線は 21 ほどで尽き、橙の四角 GW150914 だけが 23.6 にある
    気づく：GW150914 より強い背景は1つも無い
    配置：グラフ1枚、右下に 23.6 の注記
    ラベル：23.6
    """
    sc = 1.7
    box = (783, 993, 1392, 1482)
    f, ax = blank(5.95, 4.75)
    Wd, Ht = _place(ax, _crop(6, box), 0.25, 0.1, sc)
    tx, _ = _pt(box, 1335, 1152, 0.25, 0.1, Ht, sc)
    _, ty = _pt(box, 0, 1350, 0.25, 0.1, Ht, sc)
    ax.text(tx, ty, "23.6", ha="center", va="center", color=COL.red, fontweight="bold", fontsize=18)
    save(f, OUT / "s12.png")


def f_s14():
    """比べる：棒グラフ：データ2（上から Primary 36、Secondary 29、Sum 65、Final 62、Radiated 3.0。Radiated （データ2：Masses before and after the merger (sour。scaffold.py が3b節の表から描いた。強調する棒は highlight）"""
    f, ax = fig(5.6, 0.7 + 0.55 * 5)
    figlib.bars(ax, ["Primary black hole", "Secondary black hole", "Sum of the two", "Final black hole", "Radiated as gravitational waves"], [36, 29, 65, 62, 3], highlight=4, unit="M☉")
    save(f, OUT / "s14.png")


if __name__ == "__main__":
    names = sys.argv[1:] or [n[2:] for n in list(globals()) if n.startswith("f_")]
    for n in names:
        globals()["f_" + n]()
