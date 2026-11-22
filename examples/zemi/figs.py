"""図。python figs.py [名前 ...]（名前は f_ を除いた部分）。データの棒グラフは scaffold.py が設計メモの3b節から描いた。TODO の図を描く

論文の頁の画像は src/（論文は CC BY 3.0。出典と、どの枚にどの図を使ったかは src/ATTRIBUTION.md）。"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parents[1]   # 見本はリポジトリの scripts/ を使う
sys.path.insert(0, str(SKILL / "scripts"))
from figkit import COL, LW, arrow, blank, box, callout, fig, noticks, particles, save  # noqa: E402,F401
import numpy as np  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Circle, Ellipse, Rectangle  # noqa: E402
import figlib  # noqa: E402,F401
import figschema  # noqa: E402,F401

OUT = HERE / "figs"
OUT.mkdir(exist_ok=True)


def f_s02():
    """実物：輪に並べた12個の粒子（平らな円）と、波が来る前の輪（点線の円）・来たときの輪（実線の楕円）
    気づく：半周期ごとに縦に伸びて横に縮み、次の半周期で逆になる（同じ図に前・半周期後・次の半周期を並べて比べる）
    配置：左右に3コマ（前 → 半周期後 → 次の半周期）
    ラベル：波が来る前・半周期後・次の半周期
    読み方：点線＝波が来る前、実線＝波が来たとき（伸び縮みの割合＝ひずみ h。誇張はスライドの注記で断る）"""
    f, ax = blank(5.6, 4.0)
    R, e, cy = 0.72, 0.25, 2.35
    th = np.linspace(0, 2 * np.pi, 240)
    ang = np.linspace(0, 2 * np.pi, 12, endpoint=False)
    for cx, (sx, sy), name in [(0.95, (1, 1), "波が来る前"), (2.8, (1 - e / 2, 1 + e / 2), "半周期後"),
                               (4.65, (1 + e / 2, 1 - e / 2), "次の半周期")]:
        ax.plot(cx + R * np.cos(th), cy + R * np.sin(th), color=COL.gray, ls="--", lw=1.2)
        if sx != 1:
            ax.plot(cx + R * sx * np.cos(th), cy + R * sy * np.sin(th), color=COL.blue, lw=1.5)
        particles(ax, [(cx + R * sx * np.cos(a), cy + R * sy * np.sin(a)) for a in ang], r=0.07)
        ax.text(cx, 1.2, name, ha="center", va="center")
    arrow(ax, (1.74, cy), (1.96, cy), lw=1.0)
    arrow(ax, (3.62, cy), (3.82, cy), lw=1.0)
    ax.text(2.8, 0.62, "読み方：点線＝波が来る前、実線＝波が来たとき", ha="center", va="center")
    ax.text(2.8, 0.2, r"ひずみ $h = \Delta L\,/\,L$", ha="center", va="center")
    save(f, OUT / "s02.png")


SRC = HERE / "src"
K = 1700 / 1545   # 頁の画像（1700 px 幅）÷ 座標を読んだ縮小表示（1545 px 幅）
FIG3 = (150, 130, 1215, 870)                                   # p.4 Fig. 3 本体（左の余白を足した）
FIG3_WHITE = [(150, 232, 512, 458), (735, 112, 1215, 600)]     # 挿入図 (a)・(b) を白で消す


def _paper(ax, page, box, x, y, w, white=()):
    """資料の頁の画像（src/pNN.png）から box（縮小表示の座標）を切り出し、ax の (x, y) を左下に幅 w インチで置く。
    white の四角は白で消す。縮小表示の座標 → ax の座標の関数を返す。"""
    x0, y0, x1, y1 = box
    im = plt.imread(str(SRC / f"p{page:02d}.png"))
    a = im[int(y0 * K):int(y1 * K), int(x0 * K):int(x1 * K)].copy()
    if a.ndim == 2:
        a = np.stack([a] * 3, -1)
    wv = 1.0 if a.dtype.kind == "f" else 255
    for wx0, wy0, wx1, wy1 in white:
        a[max(0, int((wy0 - y0) * K)):max(0, int((wy1 - y0) * K)), max(0, int((wx0 - x0) * K)):max(0, int((wx1 - x0) * K)), :3] = wv
    h = w * (y1 - y0) / (x1 - x0)
    xl, yl = ax.get_xlim(), ax.get_ylim()
    ax.imshow(a, extent=(x, x + w, y, y + h), aspect="auto", interpolation="lanczos", zorder=0)
    ax.set_xlim(*xl)
    ax.set_ylim(*yl)
    return lambda px, py: (x + (px - x0) / (x1 - x0) * w, y + h - (py - y0) / (y1 - y0) * h)


def f_s03():
    """実物：LIGO の検出器（レーザー → ビームスプリッター → 4 km の腕2本 → 光検出器、腕の端の鏡）
    気づく：腕の端の鏡（試験質量）の間の長さの差を、下の光検出器の明暗で読む
    配置：上から見た配置（資料の Fig. 3 本体。挿入図 (a)(b) は白で消した）
    ラベル：レーザー・光検出器・鏡＝試験質量
    資料の図：Abbott ほか 2016 p.4 Fig. 3 本体を切り出し、日本語の名詞の注記を3つ足した"""
    f, ax = blank(5.6, 4.0)
    m = _paper(ax, 4, FIG3, 0.0, 0.05, 5.6, white=FIG3_WHITE)
    ax.text(*m(330, 615), "レーザー", ha="center", va="center")
    ax.text(*m(455, 848), "光検出器", ha="center", va="center")
    callout(ax, "鏡＝試験質量", target=m(668, 168), at=m(985, 250))
    save(f, OUT / "s03.png")


def f_s04():
    """実物：H1・L1 の雑音のスペクトル（資料の Fig. 3(b)）
    気づく：低い周波数は地面の揺れ、中ほどは熱、150 Hz 以上は光の粒の雑音が底を決める
    配置：グラフ（軸・目盛り・凡例は資料のまま）
    ラベル：地面の揺れ・熱・光の粒
    資料の図：Abbott ほか 2016 p.4 Fig. 3(b) を切り出し、注記を3つ足した"""
    f, ax = blank(5.6, 4.0)
    m = _paper(ax, 4, (745, 112, 1340, 598), 0.4, 0.05, 3.9 * 595 / 486)
    callout(ax, "地面の揺れ", target=m(870, 300), at=m(935, 225))
    callout(ax, "熱", target=m(995, 470), at=m(1000, 395))
    callout(ax, "光の粒", target=m(1255, 425), at=m(1190, 335))
    save(f, OUT / "s04.png")


def f_s05():
    """実物：LIGO の検出器（資料の Fig. 3 本体の再掲）
    気づく：腕の共振器・パワーリサイクリング鏡・吊った鏡の3か所が雑音を抑える工夫の場所
    配置：上から見た配置（挿入図 (a)(b) は白で消し、その空きに注記）
    ラベル：腕の共振器・パワーリサイクリング鏡・試験質量＝吊った鏡
    資料の図：Abbott ほか 2016 p.4 Fig. 3 本体を切り出し、注記を3つ足した"""
    f, ax = blank(5.6, 4.0)
    m = _paper(ax, 4, FIG3, 0.0, 0.05, 5.6, white=FIG3_WHITE)
    callout(ax, "試験質量＝吊った鏡", target=m(668, 168), at=m(985, 235))
    callout(ax, "腕の共振器", target=m(960, 686), at=m(960, 520))
    callout(ax, "パワー\nリサイクリング鏡", target=m(517, 695), at=m(330, 465))
    save(f, OUT / "s05.png")


def f_s07():
    """実物：H1 と L1 のひずみの時系列（資料の Fig. 1 上段。左右の2パネルを上下に並べ替えた）
    気づく：L1 の上に重ねた橙の線（H1 を 6.9 ms ずらして反転）が L1 とほぼ重なる
    配置：上に H1、下に L1、いちばん下に時刻の目盛り（Fig. 1 最下段の目盛りを流用。列ごとに時刻の軸は共通）
    ラベル：H1・L1・橙＝H1 を 6.9 ms ずらし反転
    資料の図：Abbott ほか 2016 p.2 Fig. 1 上段"""
    f, ax = blank(5.6, 3.85)
    s, X0 = 0.0062, 0.45
    _paper(ax, 2, (185, 1345, 778, 1422), X0, 0.0, 593 * s)                  # 時刻の目盛り
    yL = 0.50
    _paper(ax, 2, (779, 438, 1302, 694), X0 + 67 * s, yL, 523 * s)           # L1
    _paper(ax, 2, (185, 438, 252, 694), X0, yL, 67 * s)                      # L1 の縦の目盛り（H1 と同じ）
    yH = yL + 256 * s + 0.04
    _paper(ax, 2, (185, 438, 776, 694), X0, yH, 591 * s)                     # H1
    hp = 256 * s
    ax.text(0.12, (yL + yH + hp) / 2, "ひずみ（$10^{-21}$）", rotation=90, ha="center", va="center")
    ax.text(4.22, yH + hp / 2, "H1", ha="left", va="center", fontsize=18)
    ax.text(4.22, yL + hp * 0.78, "L1", ha="left", va="center", fontsize=18)
    ax.text(4.22, yL + hp * 0.55, "橙＝H1 を\n6.9 ms ずらし\n反転", ha="left", va="top")
    save(f, OUT / "s07.png")


def f_s08():
    """実物：H1 の時間周波数の図（資料の Fig. 1 最下段の左）と色の目盛り
    気づく：明るい帯が 0.2 s ほどで 35 Hz から 150 Hz へ上がる
    配置：グラフ（軸・目盛りは資料のまま）＋上がる帯に沿った赤の矢印
    ラベル：H1（ハンフォード）・35 Hz → 150 Hz
    資料の図：Abbott ほか 2016 p.2 Fig. 1 最下段"""
    f, ax = blank(6.6, 3.35)
    s = 5.4 / 633
    m = _paper(ax, 2, (145, 1088, 778, 1422), 0.0, 0.0, 5.4)
    _paper(ax, 2, (1305, 1062, 1405, 1368), 5.5, (1422 - 1368) * s, 100 * s)
    x_mid = m((253 + 773) / 2, 1088)[0]
    ax.text(x_mid, 3.08, "H1（ハンフォード）", ha="center", va="center")
    arrow(ax, m(430, 1278), m(655, 1168), color=COL.red, lw=2.5)
    ax.text(*m(405, 1148), "35 Hz → 150 Hz", ha="center", va="center", color=COL.red,
            bbox=dict(fc="white", ec="none", pad=2))
    save(f, OUT / "s08.png")


def f_s10():
    """実物：同じ縮尺（1 in＝100 km）で、間隔 350 km の円軌道（点線）と、半径 約105 km のブラックホール2つ（塗りの円）
    気づく：半径の和 210 km の2つが、350 km の間隔なら触れずに入る（すき間が残る）
    配置：上から見た軌道面（2つを同じ質量とした概略）
    ラベル：間隔 350 km・BH の半径 約105 km
    読み方：同じ縮尺。点線＝軌道、塗りの円＝BH の大きさ
    （figschema.hidden は「見える所と見えない所」の型で、長さの比べのこの図に合わないので使わなかった）"""
    f, ax = blank(6.6, 4.3)
    sc = 1 / 100
    cx, cy = 2.9, 2.15
    R, r = 175 * sc, 105 * sc
    th = np.linspace(0, 2 * np.pi, 300)
    ax.plot(cx + R * np.cos(th), cy + R * np.sin(th), color=COL.gray, ls="--", lw=1.2)
    for x in (cx - R, cx + R):
        ax.add_patch(Circle((x, cy), r, fc=COL.blue, ec="none"))
    arrow(ax, (cx - R, cy), (cx + R, cy), color=COL.red, lw=1.5, style="<|-|>")
    ax.text(cx, cy + 0.25, "間隔 350 km", ha="center", va="center", color=COL.red)
    callout(ax, "BH の半径 約105 km", target=(cx + R + 0.15, cy - r + 0.03), at=(5.1, 0.55))
    ax.text(3.3, 4.15, "読み方：同じ縮尺。点線＝軌道、塗りの円＝BH の大きさ", ha="center", va="center")
    save(f, OUT / "s10.png")


def f_s11():
    """実物：2つの探索の候補の数と背景（資料の Fig. 4 左右）
    気づく：どちらの探索でも GW150914 だけが右端に離れている
    配置：グラフ2つを左右に（軸・目盛り・凡例は資料のまま）、上に日本語のパネル名、GW150914 に赤丸
    ラベル：型を使わない探索・型を使う探索
    資料の図：Abbott ほか 2016 p.6 Fig. 4"""
    f, ax = blank(6.6, 3.0)
    m = _paper(ax, 6, (150, 995, 1392, 1482), 0.05, 0.0, 6.5)
    ax.text(m(497, 995)[0], 2.82, "型を使わない探索", ha="center", va="center")
    ax.text(m(1121, 995)[0], 2.82, "型を使う探索", ha="center", va="center")
    for p in ((670, 1153), (1333, 1153)):
        ax.add_patch(Circle(m(*p), 0.12, fill=False, ec=COL.red, lw=2))
    save(f, OUT / "s11.png")


def f_s06():
    """実物：H1 と L1 の2本の出力の線（模式図）
    気づく：灰の山は片方だけ、赤の山は2本に 10 ms 以内でそろう
    配置：上下に2台の出力、横軸＝時刻
    ラベル：H1・L1・地元の雑音・重力波・10 ms 以内
    読み方：横軸＝時刻、灰＝片方だけ、赤＝2台にそろう"""
    f, ax = blank(6.6, 4.3)
    rng = np.random.default_rng(3)
    t = np.linspace(0.8, 6.3, 1100)

    def bump(tc, amp=0.5, w=0.22):
        return amp * np.exp(-((t - tc) / w) ** 2) * np.sin(2 * np.pi * (t - tc) / 0.09)

    for y0, gray_t, red_t in [(3.0, 1.9, 3.6), (1.7, 5.2, 3.68)]:
        noise = 0.05 * np.convolve(rng.normal(size=t.size), np.ones(7) / 2.5, "same")
        sig = y0 + noise + bump(gray_t) + bump(red_t)
        ax.plot(t, sig, color=COL.blue, lw=1.2)
        for tc, c in ((gray_t, COL.gray), (red_t, COL.red)):
            k = np.abs(t - tc) < 0.42
            ax.plot(t[k], sig[k], color=c, lw=2.2)
    ax.add_patch(Rectangle((3.42, 1.05), 0.44, 2.6, fc=COL.pale, ec="none", zorder=0))
    ax.text(0.45, 3.0, "H1", ha="center", va="center", fontsize=18)
    ax.text(0.45, 1.7, "L1", ha="center", va="center", fontsize=18)
    ax.text(1.9, 3.75, "地元の雑音", ha="center", va="center", color=COL.gray)
    ax.text(5.2, 0.95, "地元の雑音", ha="center", va="center", color=COL.gray)
    ax.text(3.64, 3.88, "重力波", ha="center", va="center", color=COL.red)
    ax.text(3.64, 0.78, "10 ms 以内", ha="center", va="center")
    ax.text(3.4, 0.2, "読み方：横軸＝時刻、灰＝片方だけ、赤＝2台にそろう", ha="center", va="center")
    save(f, OUT / "s06.png")


def f_s12():
    """実物：H1 と L1 の出力の線と、ばらばらに立つ突発雑音の縦棒（模式図）
    気づく：たまたま 15 ms 以内に重なった1組（赤丸）が、本物と同じ「2台にそろう」形になる
    配置：上下に2台の出力、横軸＝時刻
    ラベル：突発雑音・偶然の一致
    読み方：縦棒＝突発雑音、赤丸＝偶然の一致"""
    f, ax = fig(6.6, 4.3)
    ax.set_xlim(0, 6.2)
    ax.set_ylim(0, 3.9)
    for y0, ts, hs in [(2.4, [0.9, 1.8, 3.0, 4.3, 5.5], [0.45, 0.3, 0.55, 0.5, 0.35]),
                       (0.95, [1.3, 2.4, 3.08, 4.9, 5.8], [0.35, 0.5, 0.5, 0.3, 0.45])]:
        ax.plot([0.6, 6.1], [y0, y0], color=COL.blue, lw=1.5)
        ax.vlines(ts, y0, [y0 + h for h in hs], color=COL.gray, lw=3)
    ax.add_patch(Ellipse((3.04, 1.95), 0.6, 2.45, fill=False, ec=COL.red, lw=2))
    ax.text(0.3, 2.4, "H1", ha="center", va="center", fontsize=18)
    ax.text(0.3, 0.95, "L1", ha="center", va="center", fontsize=18)
    ax.text(3.04, 3.45, "偶然の一致", ha="center", va="center", color=COL.red)
    callout(ax, "突発雑音", target=(4.3, 2.92), at=(5.05, 3.45))
    ax.text(3.1, 0.3, "読み方：縦棒＝突発雑音、赤丸＝偶然の一致", ha="center", va="center")
    noticks(ax)
    ax.spines["left"].set_visible(False)
    ax.set_xlabel("時刻")
    save(f, OUT / "s12.png")


def f_s13():
    """比べる：棒グラフ：データ1（探索ごとの「誤報1回あたりの年数」。主役の型を使う探索だけ青、棒の先に値と σ）（データ1：探索ごとの誤報率（偶然でこの強さが出る間隔）。scaffold.py が3b節の表から描いた。強調する棒は highlight）"""
    f, ax = fig(5.0, 0.7 + 0.55 * 3)
    figlib.bars(ax, ["型を使う（5.1σ）", "型なし C3（4.6σ）", "型なし C2+C3（4.4σ）"], [203000, 22500, 8400], highlight=0, unit="年")
    save(f, OUT / "s13.png")


def f_s14():
    """比べる：棒グラフ：データ2（合体前の2つ・合体後・放出。放出だけ赤）（データ2：合体の前と後のブラックホールの質量。scaffold.py が3b節の表から描いた。強調する棒は highlight）"""
    f, ax = fig(5.6, 0.7 + 0.55 * 4)
    figlib.bars(ax, ["主のブラックホール", "副のブラックホール", "合体後のブラックホール", "重力波で放出（M⊙c²）"], [36, 29, 62, 3], highlight=3, unit="M⊙")
    save(f, OUT / "s14.png")


if __name__ == "__main__":
    names = sys.argv[1:] or [n[2:] for n in list(globals()) if n.startswith("f_")]
    for n in names:
        globals()["f_" + n]()
