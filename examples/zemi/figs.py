"""図。python figs.py [名前 ...]（名前は f_ を除いた部分）。データの棒グラフは scaffold.py が設計メモの3b節から描いた。TODO の図を描く"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parents[1]   # 見本はリポジトリの scripts/ を使う
sys.path.insert(0, str(SKILL / "scripts"))
from figkit import COL, LW, arrow, blank, box, fig, noticks, save  # noqa: E402,F401
import figlib  # noqa: E402,F401
import figschema  # noqa: E402,F401
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402
from matplotlib.patches import Circle, Rectangle  # noqa: E402

OUT = HERE / "figs"
OUT.mkdir(exist_ok=True)


PX = 1.1   # 頁の画像を 1545×2000 で見たときの座標 → 1700×2200 の画素
SRC = HERE / "src"   # 見本では使う頁だけ（出典は src/ATTRIBUTION.md）


def _page(n):
    return np.asarray(Image.open(SRC / f"p{n:02d}.png").convert("RGB")).copy()


def _cut(arr, x0, y0, x1, y1, white=()):
    """頁から（見た座標で）切り出し、white の箱（同じ座標）を白で消す"""
    a = arr[int(y0 * PX):int(y1 * PX), int(x0 * PX):int(x1 * PX)].copy()
    for (a0, b0, a1, b1) in white:
        a[max(0, int((b0 - y0) * PX)):max(0, int((b1 - y0) * PX)), max(0, int((a0 - x0) * PX)):max(0, int((a1 - x0) * PX))] = 255
    return a


class _Map:
    """切り出した図の座標（見た座標）→ 図の中のインチ。X0・Y0 は切り出しの左上"""

    def __init__(self, box, X0, Y0, s):
        self.x0, self.y0, self.X0, self.Y0, self.s = box[0], box[1], X0, Y0, s
        self.ext = (X0, X0 + (box[2] - box[0]) * s, Y0 - (box[3] - box[1]) * s, Y0)

    def __call__(self, x, y):
        return self.X0 + (x - self.x0) * self.s, self.Y0 - (y - self.y0) * self.s


def _put(ax, arr, m, W, H):
    ax.imshow(arr, extent=m.ext, interpolation="lanczos", zorder=0, aspect="auto")
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)


def f_s03():
    """仕組み：資料の図：Fig. 3 の本体（レーザー → ビームスプリッター → 直交する 4 km の腕2本 → 光検出器。差し込みの (a)(b) は白で消した）。読み方：太い灰色の線＝光の通り道、四角＝鏡（テストマス）
    実物：干渉計の光路（論文の図そのもの）
    気づく：腕は直交する2本で、差が光検出器へ
    配置：論文の配置のまま（英語のラベルを白で消し、日本語の名詞に）
    ラベル：レーザー・ビームスプリッター・鏡・光検出器
    外したもの：Power/Signal Recycling の名前（鏡の形は残す）。出典：p.4 Fig. 3"""
    box_ = (250, 135, 1210, 860)
    W = 5.4
    s = W / (box_[2] - box_[0])
    H = (box_[3] - box_[1]) * s
    white = [(250, 250, 508, 452), (738, 135, 1210, 600),
             (512, 136, 580, 194), (512, 516, 580, 574), (472, 594, 582, 649), (650, 603, 740, 650),
             (285, 713, 375, 765), (730, 737, 798, 790), (1138, 737, 1208, 790), (490, 768, 583, 825),
             (655, 820, 812, 856), (420, 706, 487, 737), (826, 703, 1104, 740), (905, 610, 1040, 646),
             (666, 283, 704, 414), (490, 820, 583, 832)]
    arr = _cut(_page(4), *box_, white=white)
    f, ax = blank(W, H)
    m = _Map(box_, 0, H, s)
    _put(ax, arr, m, W, H)
    for (x, y) in [(546, 165), (546, 545), (764, 764), (1172, 764)]:
        ax.text(*m(x, y), "鏡", ha="center", va="center")
    ax.text(*m(330, 742), "レーザー", ha="center", va="center")
    ax.text(*m(662, 838), "光検出器", ha="left", va="center")
    ax.annotate("ビームスプリッター", xy=m(648, 668), xytext=m(760, 555), ha="left", va="center",
                arrowprops=dict(arrowstyle="-", color="#222222", lw=1.0))
    ax.text(*m(972, 628), "$L_x$ = 4 km", ha="center", va="center", bbox=dict(fc="white", ec="none", pad=1))
    ax.text(*m(686, 350), "$L_y$ = 4 km", rotation=90, ha="center", va="center", bbox=dict(fc="white", ec="none", pad=1))
    ax.text(*m(745, 165), "読み方：\n太い灰色の線＝光の通り道\n四角＝鏡（テストマス）", ha="left", va="top", fontsize=14,
            linespacing=1.4)
    save(f, OUT / "s03.png")


def f_s04():
    """仕組み：資料の図：Fig. 3(b) の雑音の大きさ（横軸＝周波数、縦軸＝雑音をひずみに直した値。H1 赤・L1 青。谷が 100〜300 Hz、とがった線は較正や電源の線）
    実物：論文の雑音のスペクトル（1.5倍）
    気づく：谷の 100〜300 Hz が最良の帯
    配置：論文のまま、100〜300 Hz に薄い灰の帯を重ねる
    ラベル：最良の帯（100〜300 Hz）
    出典：p.4 Fig. 3(b)。とがった線の説明は原稿で"""
    box_ = (748, 112, 1340, 598)
    s = 1.5 * 0.0055
    W = (box_[2] - box_[0]) * s
    H = (box_[3] - box_[1]) * s
    arr = _cut(_page(4), *box_)
    f, ax = blank(W, H)
    m = _Map(box_, 0, H, s)
    _put(ax, arr, m, W, H)
    xa, ya = m(1020, 123)
    xb, yb = m(1133, 521)
    ax.add_patch(Rectangle((xa, yb), xb - xa, ya - yb, fc="#888888", ec="none", alpha=0.18, zorder=1))
    ax.text(*m(1076, 232), "最良の帯\n100〜300 Hz", ha="center", va="center", linespacing=1.2,
            bbox=dict(fc="white", ec="none", pad=1))
    save(f, OUT / "s04.png")


def f_s06():
    """実物：資料の図：Fig. 1 の1段目（H1 の赤い線と、L1 の青い線に、ずらして反転した H1 のうすい赤を重ねたもの）
    実物：論文の2パネル（横並びを上下に並べ替え、時間の軸をそろえた）
    気づく：下の青と薄い赤が重なる
    配置：上に H1、下に L1（横に並べると 1.1倍にしかならず字が読めないため）
    ラベル：H1・ワシントン州・L1・ルイジアナ州・薄い赤＝ずらした H1
    出典：p.2 Fig. 1 の1段目（上の見出しは外し、右の日本語に）"""
    W, H = 6.6, 4.25
    s = 0.0077
    b1 = (190, 440, 776, 695)
    b2 = (778, 440, 1302, 695)
    pg = _page(2)
    f, ax = blank(W, H)
    X1 = 0.45
    m1 = _Map(b1, X1, 4.15, s)
    ph = (b1[3] - b1[1]) * s
    m2 = _Map(b2, X1 + 60 * s, 4.15 - ph - 0.15, s)
    ax.imshow(_cut(pg, *b1, white=[(190, 450, 250, 690), (260, 655, 412, 688)]), extent=m1.ext, interpolation="lanczos", zorder=0, aspect="auto")
    ax.imshow(_cut(pg, *b2, white=[(786, 630, 1090, 684)]), extent=m2.ext, interpolation="lanczos", zorder=0, aspect="auto")
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    for v, yy in (("1.0", 490), ("0.0", 567), ("−1.0", 644)):
        ax.text(m1(246, yy)[0], m1(246, yy)[1], v, ha="right", va="center", fontsize=14)
    ax.text(0.14, 4.15 - ph - 0.075, "ひずみ（$10^{-21}$）", rotation=90, ha="center", va="center")
    xr = m1.ext[1] + 0.12
    yc1 = (m1.ext[2] + m1.ext[3]) / 2
    yc2 = (m2.ext[2] + m2.ext[3]) / 2
    ax.text(xr, yc1 + 0.25, "H1", color=COL.red, fontsize=20, fontweight="bold", ha="left", va="center")
    ax.text(xr, yc1 - 0.15, "ワシントン州", ha="left", va="center")
    ax.text(xr, yc2 + 0.55, "L1", color=COL.blue, fontsize=20, fontweight="bold", ha="left", va="center")
    ax.text(xr, yc2 + 0.15, "ルイジアナ州", ha="left", va="center")
    ax.text(xr, yc2 - 0.45, "薄い赤＝\nずらした H1", ha="left", va="center", linespacing=1.3)
    save(f, OUT / "s06.png")


def f_s07():
    """実物：資料の図：Fig. 1 の最下段の左（H1 の時間と周波数の図。明るい帯が右上へ上がる）
    実物：論文の時間・周波数の図（約1.8倍）
    気づく：明るい帯が 35 Hz 付近から 150 Hz へ上がる
    配置：論文のまま。色の目盛り（右の L1 の横）は外した
    ラベル：35 Hz・150 Hz（白字の矢印）
    出典：p.2 Fig. 1 の最下段の左"""
    box_ = (148, 1088, 778, 1418)
    s = 0.0098
    W = (box_[2] - box_[0]) * s + 0.1
    H = (box_[3] - box_[1]) * s + 0.1
    arr = _cut(_page(2), *box_)
    f, ax = blank(W, H)
    m = _Map(box_, 0.05, H - 0.05, s)
    _put(ax, arr, m, W, H)
    ax.annotate("35 Hz", xy=m(330, 1298), xytext=m(330, 1240), color="white", fontsize=16, ha="center", va="center",
                arrowprops=dict(arrowstyle="-|>", color="white", lw=1.2))
    ax.annotate("150 Hz", xy=m(658, 1204), xytext=m(540, 1150), color="white", fontsize=16, ha="center", va="center",
                arrowprops=dict(arrowstyle="-|>", color="white", lw=1.2))
    save(f, OUT / "s07.png")


def f_s08():
    """仕組み：模式図：中心どうし 350 km で回る2つの円（半径の合計 210 km 以上）を縮尺どおりに並べ、すき間が狭いことを見せる。読み方：円の大きさ＝ブラックホールの半径（シュワルツシルト半径）、横の矢印＝公転の間隔
    実物：同じ大きさの2つのブラックホール（平塗りの円、半径 105 km ずつ＝合計 210 km を等分した概略）
    気づく：間隔 350 km に対して、円どうしのすき間が狭い
    配置：横に2つ、上に中心の間隔、下に半径の合計（赤）
    ラベル：ブラックホール・中心の間隔 約 350 km・半径の合計 210 km 以上"""
    W, H = 5.6, 4.0
    f, ax = blank(W, H)
    k = 0.0085
    r = 105 * k
    d = 175 * k
    cx, y0 = W / 2, 2.2
    xs = (cx - d, cx + d)
    for x in xs:
        ax.add_patch(Circle((x, y0), r, fc=COL.blue, ec="none", zorder=2))
    ax.text(xs[0], y0, "ブラック\nホール", color="white", ha="center", va="center", linespacing=1.2, zorder=3)
    yt = y0 + r + 0.3
    for x in xs:
        ax.plot([x, x], [y0 + r + 0.05, yt + 0.1], ls=":", color=COL.gray, lw=1.0)
    arrow(ax, (xs[0], yt), (xs[1], yt), lw=1.2, ms=12, style="<|-|>")
    ax.text(cx, yt + 0.27, "中心の間隔 約 350 km", ha="center", va="center")
    yb = y0 - r - 0.3
    for x in (xs[0], xs[0] + r, xs[1] - r, xs[1]):
        ax.plot([x, x], [y0 - (0.0 if x in xs else 0.0) - (r if x in xs else 0.0) - 0.05 if x in xs else y0 - 0.05, yb - 0.1],
                ls=":", color=COL.gray, lw=1.0)
    arrow(ax, (xs[0], yb), (xs[0] + r, yb), color=COL.red, lw=1.2, ms=12, style="<|-|>")
    arrow(ax, (xs[1] - r, yb), (xs[1], yb), color=COL.red, lw=1.2, ms=12, style="<|-|>")
    ax.text(cx, yb - 0.33, "半径の合計 210 km 以上", color=COL.red, ha="center", va="center")
    ax.text(cx, 0.15, "読み方：円の大きさ＝半径、横の矢印＝公転の間隔", ha="center", va="center", fontsize=14)
    save(f, OUT / "s08.png")


def f_s09():
    """仕組み：模式図：H1 と L1 の出力を上下2本の線で描き、突発的な雑音の山がばらばらに立つ。たまたま 15 ms の窓に2つの山が入った所を赤で囲む。読み方：横＝時間、縦の山＝突発的な雑音、灰色の帯＝2台がそろったと見なす 15 ms の窓
    実物：2台の出力の線（雑音＋ばらばらの山）
    気づく：別々の山が、たまたま同じ窓に入る
    配置：上下に2本、時間の軸をそろえる
    ラベル：H1・L1・15 ms の窓・偶然の一致"""
    W, H = 6.6, 4.3
    f, ax = blank(W, H)
    rng = np.random.default_rng(3)
    t = np.linspace(0.7, 6.4, 1400)
    base = {"H1": 3.0, "L1": 1.7}
    peaks = {"H1": [(1.4, 0.8), (2.9, 0.6), (4.7, 0.9)], "L1": [(2.1, 0.7), (3.6, 0.8), (4.76, 0.75)]}
    col = {"H1": COL.blue, "L1": COL.lblue}
    x0, x1 = 4.48, 4.98
    ax.add_patch(Rectangle((x0, 1.4), x1 - x0, 2.55, fc="#DDDDDD", ec="none", zorder=0))
    for k in ("H1", "L1"):
        y = 0.04 * rng.standard_normal(t.size)
        for p, a in peaks[k]:
            y = y + a * np.exp(-((t - p) / 0.03) ** 2)
        ax.plot(t, base[k] + y, color=col[k], lw=1.5, zorder=2)
        ax.text(0.35, base[k], k, fontsize=18, fontweight="bold", ha="center", va="center", color=col[k])
    ax.add_patch(Rectangle((x0 - 0.08, 1.3), x1 - x0 + 0.16, 2.75, fc="none", ec=COL.red, lw=2.0, zorder=3))
    ax.text(x0 - 0.2, 3.85, "15 ms の窓", ha="right", va="center")
    ax.text((x0 + x1) / 2, 0.98, "偶然の一致", color=COL.red, ha="center", va="center")
    arrow(ax, (0.7, 0.62), (6.4, 0.62), lw=1.0, ms=10)
    ax.text(6.4, 0.38, "時間", ha="right", va="center")
    ax.text(0.05, 0.15, "読み方：横＝時間、山＝突発的な雑音、灰の帯＝15 ms の窓", ha="left", va="center", fontsize=14)
    save(f, OUT / "s09.png")


def f_s11():
    """実物：資料の図：Fig. 4 の右（横軸＝検出統計量 ρ̂c、縦軸＝事象の数。黒い線＝時刻ずらしの背景、橙の点＝実際の候補。右端 23.6 の GW150914 に赤丸）
    実物：論文のヒストグラムの枠の中だけを切り出し、軸・目盛り・ラベルは figkit で描き直した（論文の字は小さすぎるため）
    気づく：GW150914 の点だけが背景の線の右に離れている
    配置：論文のまま。上の σ の目盛りと凡例は外し、日本語の注記に
    ラベル：23.6・GW150914・時刻ずらしの背景・実際の候補
    出典：p.6 Fig. 4 の右。目盛りの位置は論文の目盛り（8→24、10^2→10^-8）から合わせた"""
    box_ = (861, 1078, 1382, 1427)

    def X(px):
        return 8 + (px - 862) / 30.81

    def Y(py):
        return 2 - (py - 1082) / 34.8

    arr = _cut(_page(6), *box_, white=[(948, 1083, 1292, 1172), (1282, 1230, 1385, 1254)])
    f, ax = fig(5.4, 4.0)
    ext = (X(box_[0]), X(box_[2]), Y(box_[3]), Y(box_[1]))
    ax.imshow(arr, extent=ext, aspect="auto", interpolation="lanczos", zorder=0)
    ax.set_xlim(ext[0], ext[1])
    ax.set_ylim(ext[2], ext[3])
    ax.set_xticks([8, 12, 16, 20, 24])
    ax.set_yticks([2, 0, -2, -4, -6, -8])
    ax.set_yticklabels([f"$10^{{{k}}}$" for k in (2, 0, -2, -4, -6, -8)])
    ax.tick_params(labelsize=14)
    ax.set_xlabel("検出統計量 $\\hat{\\rho}_c$")
    ax.set_ylabel("事象の数")
    ax.plot([X(1333)], [Y(1153)], marker="o", ms=20, mfc="none", mec=COL.red, mew=2.0)
    ax.text(X(1333), Y(1153) + 1.25, "23.6", color=COL.red, ha="center", va="center")
    ax.text(X(1333) - 0.3, -3.0, "GW150914", ha="center", va="center", fontsize=14)
    ax.annotate("時刻ずらし\nの背景", xy=(20.6, -5.0), xytext=(23.0, -6.4), ha="center", va="center", fontsize=14,
                linespacing=1.2, arrowprops=dict(arrowstyle="-", color="#222222", lw=1.0))
    ax.annotate("実際の候補", xy=(9.7, 0.0), xytext=(11.0, 0.9), ha="left", va="center", fontsize=14,
                arrowprops=dict(arrowstyle="-", color="#222222", lw=1.0))
    save(f, OUT / "s11.png")


def f_s12():
    """比べる：棒グラフ：データ1（36・29・62・3.0 M⊙ を上から。重力波になった 3.0 だけ赤）（データ1：合体の前後の質量（GW150914 の源）。scaffold.py が3b節の表から描いた。強調する棒は highlight）"""
    f, ax = fig(5.6, 0.7 + 0.55 * 4)
    figlib.bars(ax, ["重いほうのブラックホール", "軽いほうのブラックホール", "合体後のブラックホール", "重力波で出たエネルギー（質量に直して）"], [36, 29, 62, 3], highlight=3, unit="M⊙")
    save(f, OUT / "s12.png")


if __name__ == "__main__":
    names = sys.argv[1:] or [n[2:] for n in list(globals()) if n.startswith("f_")]
    for n in names:
        globals()["f_" + n]()
