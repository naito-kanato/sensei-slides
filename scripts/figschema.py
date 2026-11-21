"""仕組みの模式図の型：答えの枚（なぜ〜か）によく出る、話題によらない「仕組みの形」を関数にしたもの。

figkit の blank()（座標がインチ）の上に描く。ラベルは引数で渡す（名詞か短い句。3〜5個まで）。
area=(x0, y0, w, h) を渡すと、その四角の中だけに描く（2つの型を1枚に並べられる：見えない所 ＋ 分かれ道 など）。

    import sys; sys.path.insert(0, r"<skill>/scripts")
    from figkit import blank, save
    import figschema
    f, ax = blank(5.6, 3.4)
    figschema.branch(ax, "破れの始まり", ["小さく止まる", "大きく広がる"], highlight=1, stops=[0])
    save(f, "figs/s10.png")

設計メモの図の案の言葉から型を探す:  python figschema.py --match "<図の案の一文>"
見本（各型の図と一覧 catalog.jpg）:      python figschema.py --demo <出力フォルダ>

| 型 | 名前 | 何を見せるか |
|---|---|---|
| branch        | 分かれ道         | 同じ始まりから違う結末に分かれる。分かれ目では、どちらになるか見分けられない |
| hidden        | 見える所と見えない所 | 上から測れるのは浅い所まで。肝心の物は、測れない深い所にある |
| need_have     | 要る量と手に入る量 | 要る量の器に、手に入る量が少ししか入っていない（足りない分） |
| build_release | たまって一気に   | 少しずつたまり、限界で一気に放たれる。限界も間隔も毎回ちがう |
| funnel        | ふるい           | 候補が段ごとに減り、最後に少ししか残らない（数は図の中の数字で読む） |
| cone          | 先ほど広がる幅   | 今から先へ行くほど、見込みの幅が広がる |
| sensitive     | 小さな違いが大きく | ほぼ同じ始まりの2本が、だんだん離れる |
| black_box     | 中の見えない箱   | 入るものと出るものは見えるが、中で何が起きているかは見えない |
| balance       | つり合い         | 2つの重みの、どちらに傾くか |
| section       | 断面の層         | 層の重なりと、どの層のどこに何があるか |

試しで、設計メモの答えの枚の図の案は「同じ始まりから小さく止まる道と大きく広がる道に分かれる断面」だったのに、
図の担当は描く部品が無く、一本の線に点と矢印だけの図にした。原稿は「分かれる道を描いています」と話し、2人の採点者が食い違いで減点した。
"""
from __future__ import annotations

import re
from collections import namedtuple

import numpy as np
from matplotlib.patches import Circle, FancyBboxPatch, Polygon, Rectangle

from figkit import COL, LW, arrow

DEEP = "#D9D9D9"     # 見えない所の塗り（light より一段濃い灰）
LAYER_FILLS = ["#EAF2FB", "#F6EBD9", "#EDEDED", "#E3EEDC", "#F3E6EF"]   # 断面の層の淡い塗り（均一・陰影なし）


def _area(ax, area):
    if area is not None:
        return area
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    return x0, y0, x1 - x0, y1 - y0


def _t(ax, x, y, s, fs, color=COL.ink, **kw):
    if s:
        ax.text(x, y, s, fontsize=fs, color=color, **kw)


def _smooth(t):
    return 3 * t ** 2 - 2 * t ** 3


# ---- 分かれ道 ---------------------------------------------------------------------------------

def branch(ax, start, outcomes, highlight=None, stops=(), unknown="ここでは見分けられない", area=None, fs=14):
    """同じ始まりから、違う結末に分かれる道。outcomes は上から順の結末の名前（2〜3個）。
    highlight（番号）の道だけ青で太く、stops（番号の並び）の道は途中で止まる（⊥の印）。
    unknown は分かれ目の赤い破線の輪に付ける一言（None で付けない）。"""
    x0, y0, w, h = _area(ax, area)
    n = len(outcomes)
    sx, sy = x0 + 0.08 * w, y0 + 0.50 * h
    fx, ex = x0 + 0.36 * w, x0 + 0.66 * w
    ys = [y0 + h * (0.84 - 0.68 * i / (n - 1)) for i in range(n)] if n > 1 else [sy]
    r = 0.035 * min(w, h * 1.4)
    ax.plot([sx, fx], [sy, sy], color=COL.ink, lw=LW.curve, solid_capstyle="round", zorder=2)
    ax.add_patch(Circle((sx, sy), r, fc=COL.ink, ec="none", zorder=3))
    _t(ax, x0 + 0.01 * w, sy + 0.07 * h, start, fs, ha="left", va="bottom")
    for i, (lab, y) in enumerate(zip(outcomes, ys)):
        stop = i in set(stops)
        main = i == highlight
        end = fx + (ex - fx) * (0.55 if stop else 1.0)
        t = np.linspace(0, 1, 80)
        xs = fx + (end - fx) * t
        yy = sy + (y - sy) * _smooth(np.clip((xs - fx) / (ex - fx), 0, 1))
        c = COL.blue if main else COL.gray
        ax.plot(xs, yy, color=c, lw=LW.curve * (1.5 if main else 1.0), solid_capstyle="round", zorder=2)
        if stop:
            dy = 0.06 * h
            ax.plot([end, end], [yy[-1] - dy, yy[-1] + dy], color=c, lw=LW.curve, zorder=3)
        else:
            ax.add_patch(Circle((end, yy[-1]), r * (1.3 if main else 1.0), fc=c, ec="none", zorder=3))
        _t(ax, end + r * 1.3 + 0.03 * w, yy[-1], lab, fs, color=COL.blue if main else COL.ink, ha="left", va="center",
           fontweight="bold" if main else "normal")
    if unknown:
        ax.add_patch(Circle((fx, sy), 0.09 * h, fc="none", ec=COL.red, lw=LW.thin, ls="--", zorder=4))
        room = fx - 0.02 * w - x0                     # 幹の下に入る幅。入らなければ2行に分けて左に寄せる
        if len(unknown) * fs / 72 <= room:
            _t(ax, fx - 0.02 * w, sy - 0.12 * h, unknown, fs, color=COL.red, ha="right", va="top")
        else:
            k = -(-len(unknown) // 2)
            _t(ax, x0 + 0.01 * w, sy - 0.12 * h, unknown[:k] + "\n" + unknown[k:], fs, color=COL.red, ha="left", va="top")


# ---- 見える所と見えない所 ---------------------------------------------------------------------

def hidden(ax, seen, unseen, target=None, reach="測れる深さ", sensors=3, area=None, fs=14):
    """上（地表・外側）から測れるのは浅い所まで。肝心の物（target）は、その下の見えない所にある。
    seen＝上の測る所の名前、unseen＝見えない所の名前、target＝見えない所にある物の名前（赤い「？」の印）。"""
    x0, y0, w, h = _area(ax, area)
    gy = y0 + 0.66 * h            # 上と下の境（地表）
    ry = gy - 0.26 * h            # 測れる深さ
    ax.add_patch(Rectangle((x0, y0), w, ry - y0, fc=DEEP, ec="none", zorder=0))
    ax.add_patch(Rectangle((x0, ry), w, gy - ry, fc=COL.pale, ec="none", zorder=0))
    ax.plot([x0, x0 + w], [gy, gy], color=COL.ink, lw=LW.shape, zorder=2)
    ax.plot([x0, x0 + w], [ry, ry], color=COL.blue, lw=LW.thin, ls="--", zorder=2)
    xs = np.linspace(x0 + 0.10 * w, x0 + 0.50 * w, sensors)
    s = 0.05 * h
    for x in xs:
        ax.add_patch(Polygon([(x - s, gy), (x + s, gy), (x, gy + 1.6 * s)], closed=True, fc=COL.blue, ec="none", zorder=3))
        arrow(ax, (x, gy - 0.01 * h), (x, ry + 0.02 * h), color=COL.lblue, lw=LW.thin, ms=12)
    lx = x0 + 0.60 * w
    _t(ax, lx, gy + 0.05 * h, seen, fs, ha="left", va="bottom")
    _t(ax, lx, ry + 0.04 * h, reach, fs, color=COL.blue, ha="left", va="bottom")
    _t(ax, lx, y0 + 0.06 * h, unseen, fs, ha="left", va="bottom")
    if target is not None:
        tx, ty = x0 + 0.30 * w, y0 + 0.17 * h
        ax.plot([tx], [ty], marker="*", ms=20, color=COL.red, zorder=3)
        _t(ax, tx + 0.04 * w, ty, target + "　？", fs, color=COL.red, ha="left", va="center")


# ---- 要る量と手に入る量 -----------------------------------------------------------------------

def need_have(ax, need, have, gap=None, level=0.3, area=None, fs=14):
    """要る量の器（破線）に、手に入る量（青）が level の割合だけ入っている。足りない分を赤の両矢印と gap の一言で。
    数の比べなら棒グラフ（figlib.bars）にする。これは「器に足りない」という仕組みの図。"""
    x0, y0, w, h = _area(ax, area)
    bx, bw = x0 + 0.14 * w, 0.30 * w
    by, bh = y0 + 0.08 * h, 0.80 * h
    hy = by + bh * level
    ax.add_patch(Rectangle((bx, by), bw, bh * level, fc=COL.blue, ec="none", zorder=1))
    ax.add_patch(Rectangle((bx, by), bw, bh, fc="none", ec=COL.ink, lw=LW.shape, ls="--", zorder=2))
    ax.add_patch(Rectangle((bx, hy), bw, by + bh - hy, fc=COL.warm, ec="none", zorder=0))
    ax_x = bx + bw + 0.06 * w
    lx = ax_x + 0.05 * w
    _t(ax, lx, by + bh, need, fs, ha="left", va="center")
    _t(ax, lx, by + bh * level / 2, have, fs, color=COL.blue, ha="left", va="center", fontweight="bold")
    if gap:
        arrow(ax, (ax_x, hy), (ax_x, by + bh), color=COL.red, lw=LW.thin, ms=12, style="<|-|>")
        _t(ax, lx, (hy + by + bh) / 2, gap, fs, color=COL.red, ha="left", va="center")


# ---- たまって一気に ---------------------------------------------------------------------------

def build_release(ax, intervals=(1.0, 0.65, 1.45, 0.85), limits=(0.80, 0.62, 0.94, 0.72),
                  amount="たまる量", time="時間", release="一気に放たれる", band="限界（毎回ちがう）",
                  gap="間隔がそろわない", area=None, fs=14):
    """少しずつたまり（右上がり）、限界で一気に放たれる（縦に落ちる）のくり返し。
    intervals＝くり返しの間隔（相対）、limits＝毎回の限界（0〜1）。限界の幅を淡い帯で、間隔の不ぞろいを下の括弧で。"""
    x0, y0, w, h = _area(ax, area)
    px0, px1 = x0 + 0.08 * w, x0 + 0.97 * w
    py0, py1 = y0 + 0.30 * h, y0 + 0.86 * h
    ax.annotate("", xy=(px1, py0), xytext=(px0, py0), arrowprops=dict(arrowstyle="-|>", color=COL.ink, lw=LW.shape))
    ax.annotate("", xy=(px0, py1 + 0.06 * h), xytext=(px0, py0),
                arrowprops=dict(arrowstyle="-|>", color=COL.ink, lw=LW.shape))
    _t(ax, px0 + 0.02 * w, py1 + 0.06 * h, amount, fs, ha="left", va="top")
    _t(ax, px1, py0 - 0.03 * h, time, fs, ha="right", va="top")
    total = sum(intervals) * 1.18
    X = lambda t: px0 + 0.02 * w + (px1 - px0 - 0.05 * w) * t / total
    Y = lambda v: py0 + (py1 - py0) * 0.80 * v
    lo, hi = min(limits), max(limits)
    ax.add_patch(Rectangle((px0 + 0.01 * w, Y(lo)), px1 - px0 - 0.02 * w, Y(hi) - Y(lo), fc=COL.warm, ec="none", zorder=0))
    t, v0 = 0.0, 0.08
    xs, ys, drops = [X(0)], [Y(v0)], []
    for d, lim in zip(intervals, limits):
        t += d
        xs += [X(t), X(t)]
        ys += [Y(lim), Y(v0)]
        drops.append((X(t), Y(lim)))
    t_end = t + intervals[0] * 0.3
    xs.append(X(t_end))
    ys.append(Y(v0 + (limits[0] - v0) * 0.3))
    ax.plot(xs, ys, color=COL.blue, lw=LW.curve, zorder=2)
    _t(ax, px1, Y(hi) + 0.02 * h, band, fs, color=COL.dred, ha="right", va="bottom")
    if release and drops:
        x, y = drops[0]
        ax.annotate(release, xy=(x, y + 0.01 * h), xytext=(x - 0.04 * w, Y(hi) + 0.03 * h),
                    fontsize=fs, color=COL.ink, ha="left", va="bottom",
                    arrowprops=dict(arrowstyle="-", color=COL.ink, lw=LW.thin, shrinkA=0, shrinkB=2))
    if gap:
        by = py0 - 0.07 * h
        prev = X(0)
        for x, _ in drops:
            ax.plot([prev + 0.01 * w, x - 0.01 * w], [by, by], color=COL.gray, lw=LW.thin)
            for e in (prev + 0.01 * w, x - 0.01 * w):
                ax.plot([e, e], [by, by + 0.03 * h], color=COL.gray, lw=LW.thin)
            prev = x
        _t(ax, (X(0) + drops[-1][0]) / 2, by - 0.04 * h, gap, fs, color=COL.ink, ha="center", va="top")


# ---- ふるい -----------------------------------------------------------------------------------

def funnel(ax, stages, highlight=None, area=None, fs=14):
    """候補が段ごとに減る。stages = [(名前, 数の文字列), ...]（上から順）。highlight（番号。既定は最後）の段だけ青。
    幅は段の順だけを表す（数の大きさは図の中の数字で読む。面積で数を表さない）。"""
    x0, y0, w, h = _area(ax, area)
    n = len(stages)
    hi = n - 1 if highlight is None else highlight
    cx = x0 + 0.30 * w
    top = y0 + 0.94 * h
    sh = 0.86 * h / n
    widths = [0.56 * w - (0.56 * w - 0.20 * w) * i / max(n - 1, 1) for i in range(n + 1)]
    widths[n] = widths[n - 1] * 0.85
    for i, (name, num) in enumerate(stages):
        yt, yb = top - i * sh, top - (i + 1) * sh + 0.06 * sh
        wt, wb = widths[i], widths[i + 1]
        c = COL.blue if i == hi else COL.pale
        ax.add_patch(Polygon([(cx - wt / 2, yt), (cx + wt / 2, yt), (cx + wb / 2, yb), (cx - wb / 2, yb)], closed=True,
                             fc=c, ec="none", zorder=1))
        _t(ax, cx, (yt + yb) / 2, num, fs + 2, color="white" if i == hi else COL.ink, ha="center", va="center",
           fontweight="bold")
        _t(ax, x0 + 0.62 * w, (yt + yb) / 2, name, fs, color=COL.blue if i == hi else COL.ink, ha="left", va="center",
           fontweight="bold" if i == hi else "normal")


# ---- 先ほど広がる幅 ---------------------------------------------------------------------------

def cone(ax, now="今", band="見込みの幅", past="これまで", actual=None, spread=0.40, area=None, fs=14, seed=4):
    """今（縦の点線）までは記録の線、今から先は見込みの中心（青の破線）と、先へ行くほど広がる幅（淡い青）。
    actual を渡すと、幅の中の1点に実際の値（赤の点）を置く。"""
    x0, y0, w, h = _area(ax, area)
    px0, px1 = x0 + 0.03 * w, x0 + 0.97 * w
    nx = x0 + 0.40 * w
    cy = y0 + 0.55 * h
    rng = np.random.default_rng(seed)
    xs = np.linspace(px0, nx, 60)
    ys = cy + 0.05 * h * np.sin((xs - px0) * 4.0 / w * 6) + 0.025 * h * rng.standard_normal(60).cumsum() / 4
    ys += cy - ys[-1]
    ax.plot(xs, ys, color=COL.ink, lw=LW.curve * 0.8, zorder=2)
    fx = np.linspace(nx, px1, 60)
    half = spread * h * ((fx - nx) / (px1 - nx)) ** 1.3
    ax.fill_between(fx, cy - half, cy + half, color=COL.pale, lw=0, zorder=0)
    ax.plot(fx, cy + half, color=COL.lblue, lw=LW.thin, zorder=1)
    ax.plot(fx, cy - half, color=COL.lblue, lw=LW.thin, zorder=1)
    ax.plot(fx, np.full_like(fx, cy), color=COL.blue, lw=LW.curve * 0.8, ls="--", zorder=2)
    ax.plot([nx, nx], [y0 + 0.10 * h, y0 + 0.97 * h], color=COL.gray, lw=LW.thin, ls=":", zorder=1)
    _t(ax, nx, y0 + 0.08 * h, now, fs, ha="center", va="top")
    _t(ax, px0, cy + 0.14 * h, past, fs, ha="left", va="bottom")
    _t(ax, px1, cy + half[-1] + 0.02 * h, band, fs, color=COL.blue, ha="right", va="bottom")
    if actual:
        ax_, ay = nx + 0.78 * (px1 - nx), cy - 0.62 * spread * h * 0.78 ** 1.3
        ax.plot([ax_], [ay], marker="o", ms=9, color=COL.red, zorder=3)
        _t(ax, ax_, ay + 0.04 * h, actual, fs, color=COL.red, ha="center", va="bottom")


# ---- 小さな違いが大きく -----------------------------------------------------------------------

def sensitive(ax, labels=("A", "B"), start="ほぼ同じ始まり", diff="わずかな違い", area=None, fs=14):
    """ほぼ同じ所から始まった2本（青と灰）が、だんだん離れていく。start は始まりの名前、diff は始まりの差に付ける一言。"""
    x0, y0, w, h = _area(ax, area)
    px0, px1 = x0 + 0.06 * w, x0 + 0.74 * w
    x = np.linspace(0, 1, 300)
    base = 0.52 + 0.10 * np.sin(2 * np.pi * 1.6 * x)
    sep = 0.30 * (np.exp(4.5 * x) - 1) / (np.exp(4.5) - 1) + 0.006
    a = base + sep
    b = base - sep * 0.9 + 0.03 * np.sin(2 * np.pi * 3.1 * x) * x
    X = px0 + (px1 - px0) * x
    ax.plot(X, y0 + h * b, color=COL.gray, lw=LW.curve, zorder=2)
    ax.plot(X, y0 + h * a, color=COL.blue, lw=LW.curve, zorder=2)
    ax.add_patch(Circle((X[0], y0 + h * base[0]), 0.07 * h, fc="none", ec=COL.red, lw=LW.thin, ls="--", zorder=3))
    _t(ax, X[0], y0 + h * base[0] - 0.12 * h, diff, fs, color=COL.red, ha="left", va="top")
    _t(ax, X[0], y0 + h * base[0] + 0.13 * h, start, fs, ha="left", va="bottom")
    _t(ax, X[-1] + 0.02 * w, y0 + h * a[-1], labels[0], fs, color=COL.blue, ha="left", va="center", fontweight="bold")
    _t(ax, X[-1] + 0.02 * w, y0 + h * b[-1], labels[1], fs, ha="left", va="center")


# ---- 中の見えない箱 ---------------------------------------------------------------------------

def black_box(ax, inputs, outputs, inside="中は見えない", area=None, fs=14):
    """入るもの（左）と出るもの（右）は見えるが、箱の中は見えない（灰の箱に「？」）。inputs・outputs は名前の並び（1〜3個）。"""
    x0, y0, w, h = _area(ax, area)
    bx, bw = x0 + 0.37 * w, 0.26 * w
    by, bh = y0 + 0.24 * h, 0.58 * h
    ax.add_patch(FancyBboxPatch((bx, by), bw, bh, boxstyle="round,pad=0.02,rounding_size=0.08",
                                fc=DEEP, ec=COL.ink, lw=LW.shape, zorder=1))
    _t(ax, bx + bw / 2, by + bh / 2, "？", fs + 16, color=COL.text, ha="center", va="center", fontweight="bold")
    _t(ax, bx + bw / 2, by - 0.05 * h, inside, fs, color=COL.ink, ha="center", va="top")

    def side(names, left):
        n = len(names)
        for i, nm in enumerate(names):
            y = by + bh * (0.5 if n == 1 else 0.82 - 0.64 * i / (n - 1))
            if left:
                arrow(ax, (bx - 0.12 * w, y), (bx - 0.01 * w, y), color=COL.lblue, ms=14)
                _t(ax, bx - 0.13 * w, y, nm, fs, ha="right", va="center")
            else:
                arrow(ax, (bx + bw + 0.01 * w, y), (bx + bw + 0.12 * w, y), color=COL.blue, ms=14)
                _t(ax, bx + bw + 0.13 * w, y, nm, fs, color=COL.blue, ha="left", va="center", fontweight="bold")
    side(inputs, True)
    side(outputs, False)


# ---- つり合い ---------------------------------------------------------------------------------

def balance(ax, left, right, heavier="right", result=None, area=None, fs=14):
    """天秤：left・right の2つの重み。heavier（"left"・"right"・None）の側に傾く。重い側の重りを大きく青に。
    result は支点の下に置く一言（「〜の側に傾く」など）。"""
    x0, y0, w, h = _area(ax, area)
    cx, py = x0 + 0.50 * w, y0 + 0.40 * h
    ang = {"left": 7, "right": -7}.get(heavier, 0) * np.pi / 180
    L = 0.36 * w
    ax.add_patch(Polygon([(cx - 0.05 * w, y0 + 0.20 * h), (cx + 0.05 * w, y0 + 0.20 * h), (cx, py)], closed=True,
                         fc=COL.gray, ec="none", zorder=1))
    ax.plot([x0 + 0.06 * w, x0 + 0.94 * w], [y0 + 0.20 * h] * 2, color=COL.ink, lw=LW.shape)
    ends = [(cx - L * np.cos(ang), py - L * np.sin(ang)), (cx + L * np.cos(ang), py + L * np.sin(ang))]
    ax.plot([ends[0][0], ends[1][0]], [ends[0][1], ends[1][1]], color=COL.ink, lw=LW.curve, solid_capstyle="round", zorder=2)
    for (ex, ey), name, side in zip(ends, (left, right), ("left", "right")):
        big = side == heavier
        s = (0.16 if big else 0.10) * h
        c = COL.blue if big else COL.lblue
        ax.add_patch(Rectangle((ex - s * 0.8, ey), s * 1.6, s, fc=c, ec="none", zorder=3))
        _t(ax, ex, ey + s + 0.04 * h, name, fs, color=COL.blue if big else COL.ink, ha="center", va="bottom",
           fontweight="bold" if big else "normal")
    if result:
        _t(ax, cx, y0 + 0.16 * h, result, fs, ha="center", va="top")


# ---- 断面の層 ---------------------------------------------------------------------------------

def section(ax, layers, marks=(), top=None, area=None, fs=14):
    """横から切った断面。layers = [(名前, 厚さの比), ...]（上から順。淡い均一の塗り）。名前は層の左に。
    marks = [(名前, 横の位置 0〜1, 深さ 0〜1), ...]：その場所に赤い印と名前（1〜2個）。top は一番上の面の名前（地表・皮膚 など）。"""
    x0, y0, w, h = _area(ax, area)
    ty = y0 + (0.88 if top else 0.98) * h
    total = float(sum(t for _, t in layers))
    y = ty
    for i, (name, t) in enumerate(layers):
        dh = (ty - y0) * t / total
        ax.add_patch(Rectangle((x0, y - dh), w, dh, fc=LAYER_FILLS[i % len(LAYER_FILLS)], ec="none", zorder=0))
        if i:
            ax.plot([x0, x0 + w], [y, y], color=COL.gray, lw=LW.thin, zorder=1)
        _t(ax, x0 + 0.02 * w, y - dh / 2, name, fs, ha="left", va="center")
        y -= dh
    ax.plot([x0, x0 + w], [ty, ty], color=COL.ink, lw=LW.shape, zorder=2)
    if top:
        _t(ax, x0 + 0.02 * w, ty + 0.02 * h, top, fs, ha="left", va="bottom")
    for name, fx, depth in marks:
        mx, my = x0 + fx * w, ty - depth * (ty - y0)
        ax.plot([mx], [my], marker="*", ms=18, color=COL.red, zorder=3)
        _t(ax, mx + 0.03 * w, my, name, fs, color=COL.red, ha="left", va="center")


# ---- 図の案の言葉から型を探す -----------------------------------------------------------------

Pattern = namedtuple("Pattern", "func name words shows example")
PATTERNS = [
    Pattern("branch", "分かれ道", r"分かれ|分岐|枝分|同じ始まり|止まる.{0,14}(広がる|育つ)|(育つ|広がる).{0,14}止まる|どちらに転",
            "同じ始まりから違う結末に分かれる（分かれ目では見分けられない）",
            'branch(ax, "始まり", ["結末A", "結末B"], highlight=1, stops=[0])'),
    Pattern("hidden", "見える所と見えない所", r"見えない|見える所|測れない|届かない|観測できない|直接.{0,4}(見|測)|地下|奥の|内部",
            "上から測れるのは浅い所まで。肝心の物は測れない所にある",
            'hidden(ax, "観測する所", "見えない所", target="肝心の物")'),
    Pattern("need_have", "要る量と手に入る量", r"要る(もの|量)|必要な量|足りない|不足|手に入る",
            "要る量の器に、手に入る量が少ししか入っていない",
            'need_have(ax, "要る量", "手に入る量", gap="足りない分", level=0.3)'),
    Pattern("build_release", "たまって一気に", r"たま(る|り|って)|ため(る|て)|蓄積|一気に|解放|限界で",
            "少しずつたまり、限界で一気に放たれる。限界も間隔も毎回ちがう",
            "build_release(ax)"),
    Pattern("funnel", "ふるい", r"ふるい|篩|絞り込|絞られ|漏斗|残ったのは|段ごとに減",
            "候補が段ごとに減り、最後に少ししか残らない",
            'funnel(ax, [("報告", "729件"), ("記録あり", "160件"), ("続けて観察", "14件")])'),
    Pattern("cone", "先ほど広がる幅", r"幅が広が|広がる幅|先ほど|先へ行くほど|見込みの幅|予測の幅|不確かさが",
            "今から先へ行くほど、見込みの幅が広がる",
            'cone(ax, now="今", band="見込みの幅", actual="実際")'),
    Pattern("sensitive", "小さな違いが大きく", r"わずかな違い|小さな違い|ほぼ同じ始まり|初期値|カオス|鋭敏",
            "ほぼ同じ始まりの2本が、だんだん離れる",
            'sensitive(ax, labels=("結果A", "結果B"))'),
    Pattern("black_box", "中の見えない箱", r"ブラックボックス|中が見えない|中身が見えない|入るもの|入力.{0,6}出力",
            "入るものと出るものは見えるが、中は見えない",
            'black_box(ax, ["入るもの"], ["出るもの"])'),
    Pattern("balance", "つり合い", r"つり合|釣り合|天秤|てんびん|綱引き|トレードオフ|せめぎ|傾く",
            "2つの重みの、どちらに傾くか",
            'balance(ax, "重みA", "重みB", heavier="right", result="Bの側に傾く")'),
    Pattern("section", "断面の層", r"断面|地層|層の|層が|層を|重なった層",
            "層の重なりと、どの層のどこに何があるか",
            'section(ax, [("層1", 1), ("層2", 2), ("層3", 2)], marks=[("ここ", 0.5, 0.7)], top="表面")'),
]


def match(text: str) -> list:
    """図の案の一文に合う型（Pattern）の並び。語の当たりの多い順。"""
    hits = []
    for i, p in enumerate(PATTERNS):
        k = len(re.findall(p.words, text or ""))
        if k:
            hits.append((-k, i, p))
    return [p for _, _, p in sorted(hits)]


def hint(text: str, limit: int = 2) -> str:
    """図の担当への一言（figdraft・scaffold が図の案の下に出す）。合う型が無ければ空。"""
    ps = match(text)[:limit]
    if not ps:
        return ""
    s = "使える型：" + "／".join(f"figschema.{p.func}（{p.name}：{p.shows}。blank() の ax に、例 figschema.{p.example}）"
                               for p in ps)
    if len(ps) > 1:
        s += "。2つを1枚にするなら area=(x0, y0, w, h) で左右に分ける"
    return s


# ---- 見本 -------------------------------------------------------------------------------------

def _demo(outdir):
    import os
    from figkit import blank, save
    os.makedirs(outdir, exist_ok=True)
    W, H = 5.6, 3.4
    out = []

    def go(name, draw, w=W, h=H):
        f, ax = blank(w, h)
        draw(ax)
        p = f"{outdir}/{name}.png"
        save(f, p)
        out.append(p)

    go("branch", lambda ax: branch(ax, "破れの始まり", ["小さく止まる", "大きく広がる"], highlight=1, stops=[0]))
    go("hidden", lambda ax: hidden(ax, "地表の観測点", "見えない深さ", target="断層"))
    go("need_have", lambda ax: need_have(ax, "予知に要る情報", "今測れる情報", gap="足りない分", level=0.28))
    go("build_release", lambda ax: build_release(ax))
    go("funnel", lambda ax: funnel(ax, [("前兆の報告", "729件"), ("記録が残る", "160件"), ("続けて観察", "14件")]))
    go("cone", lambda ax: cone(ax, now="今", band="見込みの幅", past="これまでの記録", actual="実際"))
    go("sensitive", lambda ax: sensitive(ax, labels=("大雨", "晴れ"), start="ほぼ同じ空模様"))
    go("black_box", lambda ax: black_box(ax, ["入力の文"], ["次の単語"], inside="中の計算は見えない"))
    go("balance", lambda ax: balance(ax, "手間", "安心", heavier="right", result="備える側に傾く"))
    go("section", lambda ax: section(ax, [("地殻", 1.0), ("マントル", 2.2)], marks=[("震源", 0.55, 0.45)], top="地表"))

    def combo(ax):   # 2つの型を1枚に（area で左右に分ける）
        hidden(ax, "観測点", "見えない所", target=None, area=(0.0, 0.0, 2.6, 3.4))
        branch(ax, "始まり", ["止まる", "広がる"], highlight=1, stops=[0], unknown="見分けられない", area=(2.75, 0.0, 2.85, 3.4))
    go("combo_hidden_branch", combo)

    try:
        from PIL import Image
        ims = [Image.open(p).convert("RGB") for p in out]
        tw, cols = 520, 3
        cells = [im.resize((tw, int(tw * im.height / im.width))) for im in ims]
        rows = [cells[i:i + cols] for i in range(0, len(cells), cols)]
        H_ = sum(max(c.height for c in r) + 16 for r in rows)
        sheet = Image.new("RGB", (cols * (tw + 16) + 16, H_ + 16), "white")
        y = 16
        for r in rows:
            x = 16
            for c in r:
                sheet.paste(c, (x, y))
                x += tw + 16
            y += max(c.height for c in r) + 16
        sheet.save(f"{outdir}/catalog.jpg", quality=88)
        print(f"saved {outdir}/catalog.jpg")
    except ImportError:
        pass


if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if len(sys.argv) >= 3 and sys.argv[1] == "--demo":
        _demo(sys.argv[2])
    elif len(sys.argv) >= 3 and sys.argv[1] == "--match":
        ps = match(" ".join(sys.argv[2:]))
        if not ps:
            print("合う型なし（figkit の blank() に描く。下書きは figdraft.py）")
        for p in ps:
            print(f"{p.func}（{p.name}）：{p.shows}\n    例：figschema.{p.example}")
    else:
        print(__doc__)
