"""スライド用の図（グラフ・模式図）を matplotlib で描くときの共通設定と小道具。

    from figkit import fig, blank, save, COL, LW, arrow, box, callout, particles, cylinder, coil, noticks
    f, ax = fig(5.0, 3.6)            # スライド上に置く実寸（インチ）で作る → 文字の大きさが本文と揃う
    ax.plot(T, R, color=COL.blue)
    save(f, "figs/rt.png")

図の方針（詳しくは references/figures.md）:
  模式図として伝わりやすさ優先。立体的な描き方は可だが、濃い陰影・光沢・グロー・グラデーション・
  主張の強い太い輪郭線は使わない。塗りは均一な淡色、線は細め、ラベルは対象の横に直接書く。
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib import rcParams  # noqa: E402
from matplotlib.path import Path as MplPath  # noqa: E402
from matplotlib.patches import Circle, Ellipse, FancyArrowPatch, FancyBboxPatch, Polygon  # noqa: E402


class COL:
    text = "#545455"   # 本文と同じ灰色
    ink = "#222222"    # 軸・線画
    blue = "#215F99"   # テンプレートの青（帯と同色）。主役の線・液体の濃い部分
    lblue = "#4E95D9"  # 矢印の水色。流れ・補助の線
    red = "#FF0000"    # 強調（結論・注目点）だけに使う
    green = "#4EA72E"
    orange = "#E97132"
    gray = "#9A9A9A"   # 比較対象・参考線（破線で）
    pale = "#DCE9F7"   # 薄い青の塗り（液体・冷たい側・範囲の網掛け）
    warm = "#FBE1E1"   # 薄い赤の塗り（高温側）
    sand = "#E8C07D"   # 試料・金属ブロックなどの塗り
    light = "#F2F2F2"  # 背景的な塗り


class LW:
    curve = 2.5    # グラフの主線
    shape = 1.5    # 模式図の輪郭（これより太くしない）
    thin = 1.0     # 補助線・引き出し線
    arrow = 2.0    # 矢印


# 主フォントは和欧両方を持つ Meiryo にする。"温度 $T$" のように日本語と $数式$ が混ざったラベルでは、
# 数式以外の部分が先頭フォントだけで描かれる（フォールバックが効かない）ため、Arial を先頭にすると日本語が□になる。
# Windows に無いときの代わり：Mac はヒラギノ、Linux は Noto Sans CJK（apt の fonts-noto-cjk）か IPAex。どれも和欧両方を持つ。
JA_FONTS = ["Meiryo", "Yu Gothic", "Hiragino Sans", "Hiragino Kaku Gothic ProN", "Noto Sans CJK JP",
            "Noto Sans JP", "IPAexGothic", "IPAGothic", "MS Gothic"]
def _installed(names):
    """入っているフォントだけを残す（無いものを並べると、matplotlib が「見つからない」を大量に出す）。"""
    from matplotlib import font_manager
    have = {f.name for f in font_manager.fontManager.ttflist}
    return [n for n in names if n in have] or ["sans-serif"]


rcParams.update({
    "font.family": _installed(JA_FONTS),
    "mathtext.fontset": "cm",
    "font.size": 15,
    "axes.labelsize": 16,
    "axes.titlesize": 16,
    "xtick.labelsize": 13,
    "ytick.labelsize": 13,
    "axes.edgecolor": COL.ink,
    "axes.labelcolor": COL.ink,
    "xtick.color": COL.ink,
    "ytick.color": COL.ink,
    "axes.linewidth": 1.4,
    "xtick.direction": "in",
    "ytick.direction": "in",
    "xtick.major.width": 1.2,
    "ytick.major.width": 1.2,
    "lines.linewidth": LW.curve,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "legend.frameon": False,
    "savefig.dpi": 220,
    "savefig.facecolor": "white",
})


def fig(w_in=5.0, h_in=3.6, **kw):
    """グラフ用。上と右の枠なし、目盛り内向き。"""
    f, ax = plt.subplots(figsize=(w_in, h_in), **kw)
    return f, ax


def blank(w_in=5.0, h_in=3.6):
    """模式図用: 軸なし・座標は 0〜w_in, 0〜h_in（インチ単位で描ける）。"""
    f = plt.figure(figsize=(w_in, h_in))
    ax = f.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, w_in)
    ax.set_ylim(0, h_in)
    ax.set_aspect("equal")
    ax.axis("off")
    return f, ax


import sys  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):  # cp932 の端末でも WARN の日本語が化けないように
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MIN_FONT = 13      # 図の文字の下限（基本は14pt。これ未満は WARN）
MAX_LABELS = 5     # 1つの図に書くラベル（自由テキスト・注釈）の数の目安


def lint(f, name=""):
    """図の文字の大きさとラベルの数を検査して WARN を出す（save が呼ぶ）。
    過去の質問回答デッキで、全部の図を下限の12ptで書き、ラベルを5〜6個詰めて読めなくなった反省。"""
    import re
    small, n_lab = [], 0
    for ax in f.axes:
        labs = [t for t in ax.texts if t.get_text().strip()]
        # ラベルの数は4文字以上の文（原子記号「Si」や「結晶」のような短い名札は数えない）
        n_lab += sum(len(re.sub(r"[$_^{}\\\s]", "", t.get_text())) >= 4 for t in labs)
        texts = labs + [ax.xaxis.label, ax.yaxis.label] + list(ax.get_xticklabels()) + list(ax.get_yticklabels())
        for t in texts:
            if t.get_text().strip() and t.get_fontsize() < MIN_FONT:
                small.append(f"「{t.get_text().strip()[:10]}」{t.get_fontsize():g}pt")
    if small:
        print(f"  [WARN] {name}: 文字が {MIN_FONT}pt 未満 → 14pt を基本にする（図を大きく描くか、ラベルを減らす）: " + "、".join(small[:6]))
    if n_lab > MAX_LABELS:
        print(f"  [WARN] {name}: ラベルが {n_lab} 個（目安 {MAX_LABELS} 個まで）→ 本文・ノートに回すか、図を2枚に分ける")
    hits = text_on_lines(f)
    if hits:
        print(f"  [WARN] {name}: 文字が枠の縁・線にかかっている → 箱を広げる・改行する・ラベルを線から離す"
              f"（すき間は文字の高さの半分ほど）: " + "、".join(hits[:6]))
    return bool(small) or n_lab > MAX_LABELS or bool(hits)


TEXT_GAP_PT = 3    # 文字と、枠の縁・線との最小のすき間（pt）


def text_on_lines(f, gap_pt=TEXT_GAP_PT):
    """図の中の文字（ax.text・annotate）が、枠（四角・角丸・円・弧などの縁）や線・矢印にかかっているものを
    「文字」→ かかっている相手 の形で返す。塗りだけで縁の無い図形（縁の色が透明・線幅 0）は見ない。
    以前の講座で、箱の中の「ドライヤー」「漏電を検知」が箱の縁にはみ出し、「フード」の文字が弧の線と重なった反省。"""
    f.canvas.draw()
    r = f.canvas.get_renderer()
    pad = gap_pt * f.dpi / 72
    hits = []
    for ax in f.axes:
        shapes = []
        for p in ax.patches:
            ec = p.get_edgecolor()
            if p.get_visible() and p.get_linewidth() > 0 and (len(ec) < 4 or ec[3] > 0):
                shapes.append(("枠の縁" if not isinstance(p, FancyArrowPatch) else "矢印", p))
        shapes += [("線", l) for l in ax.lines if l.get_visible() and l.get_linewidth() > 0 and l.get_linestyle() not in ("None", "")]
        for t in ax.texts:
            s = t.get_text().strip()
            if not s or not t.get_visible():
                continue
            bb = t.get_window_extent(r).expanded(1, 1)
            bb = bb.from_extents(bb.x0 - pad, bb.y0 - pad, bb.x1 + pad, bb.y1 + pad)
            for kind, a in shapes:
                path = a.get_transform().transform_path(a.get_path())
                # 折れ線に直してから調べる（CLOSEPOLY の頂点や曲線の制御点で、離れた文字まで当たりにしないため）
                if any(MplPath(poly).intersects_bbox(bb, filled=False) for poly in path.to_polygons(closed_only=False)):
                    hits.append(f"「{s[:8]}」→{kind}")
                    break
    return hits


def save(f, path, tight=True):
    from pathlib import Path
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    lint(f, Path(path).name)
    if tight:
        f.savefig(path, bbox_inches="tight", pad_inches=0.06)
    else:
        f.savefig(path)
    plt.close(f)
    print(f"saved {path}")


# ---- 小道具 -------------------------------------------------------------------------

def noticks(ax):
    """定性的なグラフ（概略図）で目盛りを消す。軸ラベルは残す。"""
    ax.set_xticks([])
    ax.set_yticks([])


def arrow(ax, p0, p1, color=COL.ink, lw=LW.arrow, ms=18, style="-|>", ls="-"):
    """細身の矢印。流れ・熱・因果に。style="<->" で両矢印（寸法線）。"""
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle=style, mutation_scale=ms, color=color, lw=lw, linestyle=ls))


def box(ax, x, y, w, h, text=None, fc=COL.pale, ec=COL.ink, fs=14, color=COL.ink, lw=LW.shape, r=0.1):
    """角丸の箱（熱浴・装置・工程のブロック）。(x, y) は左下。"""
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0.02,rounding_size={r}", fc=fc, ec=ec, lw=lw))
    if text:
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=color)


def callout(ax, text, target, at, color=COL.ink, fs=12, boxed=True):
    """引き出し線つきラベル（図の中の一部を名指しする囲みラベル）。
    target = 指す点、at = ラベルの中心。"""
    bbox = dict(boxstyle="square,pad=0.25", fc="white", ec=color, lw=LW.thin) if boxed else None
    ax.annotate(text, xy=target, xytext=at, ha="center", va="center", fontsize=fs, color=color, bbox=bbox,
                arrowprops=dict(arrowstyle="-", color=color, lw=LW.thin, shrinkA=0, shrinkB=2))


def particles(ax, xy, r=0.08, fc=COL.blue, ec="none", alpha=1.0):
    """原子・分子を平らな円で描く（光沢・グラデーションは付けない）。xy = [(x, y), ...]"""
    for x, y in xy:
        ax.add_patch(Circle((x, y), r, fc=fc, ec=ec, lw=LW.thin, alpha=alpha))


def cylinder(ax, x, y, w, h, fc="white", ec=COL.ink, level=None, liquid=COL.pale, lw=LW.shape, ell=0.18):
    """立体の容器・管を平塗りで描く（上面の楕円＋側面）。level を与えると液面までを liquid で塗る。
    (x, y) は底面の楕円の左端の高さ。陰影は付けず、線は細めにする。"""
    e = ell * w
    body = Polygon([(x, y), (x, y + h), (x + w, y + h), (x + w, y)], closed=True, fc=fc, ec="none")
    ax.add_patch(body)
    ax.add_patch(Ellipse((x + w / 2, y), w, e, fc=fc, ec="none"))
    if level is not None:
        ax.add_patch(Polygon([(x, y), (x, y + level), (x + w, y + level), (x + w, y)], closed=True, fc=liquid, ec="none"))
        ax.add_patch(Ellipse((x + w / 2, y), w, e, fc=liquid, ec="none"))
        ax.add_patch(Ellipse((x + w / 2, y + level), w, e, fc=liquid, ec=ec, lw=lw * 0.7))
    t = np.linspace(np.pi, 2 * np.pi, 60)  # 底面の手前半分
    ax.plot(x + w / 2 + w / 2 * np.cos(t), y + e / 2 * np.sin(t), color=ec, lw=lw)
    ax.plot([x, x], [y, y + h], color=ec, lw=lw)
    ax.plot([x + w, x + w], [y, y + h], color=ec, lw=lw)
    ax.add_patch(Ellipse((x + w / 2, y + h), w, e, fc="none", ec=ec, lw=lw))


def coil(ax, xc, y0, y1, r=0.28, n=7, color=COL.ink):
    """ソレノイド（検出コイルなど）を楕円の重なりで描く。"""
    for y in np.linspace(y0, y1, n):
        ax.add_patch(Ellipse((xc, y), 2 * r, 0.16, fc="none", ec=color, lw=1.8))


# ---- 原子配置の部品（過去の講座で作ったものを汎用化） --------------------------------
# 液体・ガラス・結晶・網目の模式図で、同じ配置を複数の図・複数の回で使い回すための関数。
# 例: p, L = disordered_disks(cache="build/disks.npy"); draw_disks(ax, p[窓の中], 0.36, COL.lblue, clip=枠)

def disordered_disks(n=900, phi=0.80, seed=3, iters=600, cache=None):
    """周期境界の箱に直径1の円盤を n 個、重なりを押し離して詰めた乱れた配置（液体・ガラスの模型）。
    phi = 面積充填率。戻り値 (座標 (n,2), 箱の一辺 L)。計算に1分ほどかかるので cache（.npy のパス）を渡すと再利用する。"""
    from pathlib import Path
    L = np.sqrt(n * np.pi / 4 / phi)
    if cache is not None and Path(cache).exists():
        return np.load(cache), L
    rng = np.random.default_rng(seed)
    p = rng.random((n, 2)) * L
    for _ in range(iters):
        dx = p[:, None, :] - p[None, :, :]
        dx -= L * np.round(dx / L)
        r = np.sqrt((dx ** 2).sum(-1)) + np.eye(n) * 1e9
        ov = np.clip(1.0 - r, 0, None)
        p += 0.5 * ((ov / r)[:, :, None] * dx).sum(1)
        p %= L
    if cache is not None:
        Path(cache).parent.mkdir(parents=True, exist_ok=True)
        np.save(cache, p)
    return p, L


def tri_lattice(nx, ny, a=1.0):
    """三角格子（2Dの最密充填・結晶の模型）。最近接距離 a。"""
    return np.array([((i + 0.5 * (j % 2)) * a, j * a * np.sqrt(3) / 2) for j in range(ny) for i in range(nx)])


def draw_disks(ax, pts, r, color, clip=None):
    """原子を平塗りの円で並べる。clip に Rectangle(..., transform=ax.transData) を渡すと枠で切り取る。"""
    for x, y in pts:
        c = Circle((x, y), r, fc=color, ec="none")
        ax.add_patch(c)
        if clip is not None:
            c.set_clip_path(clip)


def random_network(pts, margin=1.0, iters=300):
    """乱れた点配置のボロノイ図から3配位の連続ランダム網目（ザッカリアセン流の2D網目）を作り、
    ばねで辺の長さをそろえる。戻り値 (頂点 V, 辺 E[(i,j)])、辺の長さ≈1 に規格化。
    頂点＝網目形成イオン（Si など、2Dでは3配位）、辺の中点＝架橋酸素として描く。"""
    from scipy.spatial import Voronoi
    v = Voronoi(pts)
    V = v.vertices.copy()
    lo, hi = pts.min(0) + margin, pts.max(0) - margin
    ok = np.all((V > lo) & (V < hi), axis=1)
    E = np.array([(i, j) for i, j in v.ridge_vertices if i >= 0 and j >= 0 and ok[i] and ok[j]])
    L0 = np.median(np.linalg.norm(V[E[:, 0]] - V[E[:, 1]], axis=1))
    for _ in range(iters):
        d = V[E[:, 1]] - V[E[:, 0]]
        r = np.linalg.norm(d, axis=1)[:, None]
        f = 0.25 * (r - L0) * d / r
        F = np.zeros_like(V)
        np.add.at(F, E[:, 0], f)
        np.add.at(F, E[:, 1], -f)
        V += F
    return V / L0, E
