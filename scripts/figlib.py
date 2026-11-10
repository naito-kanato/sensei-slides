"""図の「型」：これまでのデッキで描いた図のうち、話題が変わっても使える形を関数にしたもの。

figkit（色・線・小道具）の上に作ってある。どの関数も渡された ax に描くだけなので、figkit の fig() / blank() と組み合わせる。
ラベル位置などの細部は呼び出し側で調整する（型は「描き方の決まり」をそろえるためのもの）。

    import sys; sys.path.insert(0, r"<skill>/scripts")
    from figkit import fig, save, COL
    from figlib import compare, decompose
    f, ax = fig(5.0, 3.6)
    compare(ax, T, semi, metal, main_label=("半導体", (16, 2e3)), ref_label=("金属", (1.2, 2e-2)))
    save(f, "figs/semi.png")

型の一覧とサンプル画像:  python figlib.py --demo <出力フォルダ>   （各型の例と catalog.jpg を書き出す）

| 型 | 何に使うか（元の図） |
|---|---|
| compare         | 主役（青実線）と比較対象（灰破線）の重ね描き |
| decompose       | 成分（破線）とその和（青実線） |
| tangent         | 曲線の1点での接線と、傾きの意味のラベル |
| extrapolate     | 何本かの直線を x→0 へ点線で外挿し、切片が共通になることを示す |
| data_fit        | 資料の数値（赤丸）と（対数）空間の多項式補間、値ラベル |
| range_bars      | 名前つきの範囲を横の両矢印で並べる |
| equal_area_peaks| 面積が同じローレンツ形を重ね、線幅とピーク高さの関係を見せる |
| polar_pattern   | 角度分布 W(θ) を極座標の形で |
| precession      | 軸のまわりの歳差運動（傾いたベクトル＋円錐の楕円） |
| decay_signal    | 減衰する振動と包絡線 |
| dipole_lattice  | 格子上の双極子を矢印で並べ、1つを強調して周りからの寄与を示す |
| bars            | 図の種類「棒グラフ」：2〜8個の値を横棒で比べる（主役だけ青、ほかは灰、値を棒の先に） |
| share_bar       | 図の種類「帯グラフ」：全体の内訳を1本の100%の帯で（主役だけ青、ほかは淡い色） |
| timeline        | 図の種類「年表」：時代の帯と、いつ何が起きたかの印（主役の出来事だけ赤） |
"""
from __future__ import annotations

import numpy as np
from matplotlib.patches import Circle, Ellipse, FancyArrowPatch

from figkit import COL, LW, arrow, noticks


def _label(ax, spec, color, fs=12, **kw):
    """spec = (文字列, (x, y)) なら ax.text で置く。None なら何もしない。"""
    if spec:
        text, (x, y) = spec
        ax.text(x, y, text, color=color, fontsize=fs, **kw)


def compare(ax, x, main, ref, main_label=None, ref_label=None, main_color=COL.blue, ref_color=COL.gray, fs=12):
    """主役を青の実線、比較対象を灰色の破線で重ねる。ラベルは (文字列, (x, y)) で線の近くに直接書く（凡例は使わない）。"""
    ax.plot(x, ref, color=ref_color, ls="--", lw=2)
    ax.plot(x, main, color=main_color)
    _label(ax, main_label, main_color, fs)
    _label(ax, ref_label, ref_color, fs)


def decompose(ax, x, parts, total_label=None, part_styles=None, fs=12):
    """成分を破線で描き、その和を青の実線で重ねる。parts = [(配列, (ラベル, (x, y)) or None, 色), ...]。
    戻り値は和の配列。"""
    total = np.zeros_like(np.asarray(x, dtype=float))
    for k, (y, lab, color) in enumerate(parts):
        ax.plot(x, y, color=color, ls="--", lw=2)
        _label(ax, lab, color, fs)
        total = total + y
    ax.plot(x, total, color=COL.blue)
    _label(ax, total_label, COL.blue, fs + 3)
    return total


def tangent(ax, x, y, x0, span, label=None, color=COL.red, mark=True, fs=14):
    """曲線 (x, y) の x0 での接線を、x0±span の範囲に赤い破線で引く。label = (文字列, (x, y))。戻り値は傾き。"""
    x = np.asarray(x, dtype=float); y = np.asarray(y, dtype=float)
    k = np.interp(x0, x, np.gradient(y, x))
    y0 = np.interp(x0, x, y)
    xx = np.linspace(x0 - span, x0 + span, 10)
    ax.plot(xx, y0 + k * (xx - x0), color=color, ls="--", lw=2)
    if mark:
        ax.plot([x0], [y0], "o", color=color, ms=7, zorder=5)
    _label(ax, label, color, fs)
    return k


def extrapolate(ax, lines, x_from, x_to=1.0, intercept=1.0, mark_label=None, fs=14):
    """y = intercept + s·x の直線を x_from〜x_to は実線、0〜x_from は点線で描き、x=0 の共通の切片に赤丸。
    lines = [(傾き s, ラベル, 色), ...]（ラベルは線の右端に置く）。mark_label = (文字列, (x, y))。"""
    xs = np.linspace(x_from, x_to, 50)
    for s, lab, color in lines:
        ax.plot(xs, intercept + s * xs, color=color)
        ax.plot([0, x_from], [intercept, intercept + s * x_from], color=color, ls=":", lw=2)
        if lab:
            ax.text(x_to * 1.02, intercept + s * x_to, lab, color=color, fontsize=fs, va="center")
    ax.plot([0], [intercept], "o", color=COL.red, ms=9, zorder=5)
    if mark_label:
        text, (tx, ty) = mark_label
        ax.annotate(text, xy=(0.01 * x_to, intercept), xytext=(tx, ty), fontsize=fs, color=COL.red,
                    arrowprops=dict(arrowstyle="-|>", color=COL.red, lw=1.3))


def data_fit(ax, xs, ys, labels=None, deg=2, logx=True, logy=True, x_range=None, label_dx=1.18, label_dy=1.25, fs=13):
    """資料の数値を赤丸で、(対数)空間の deg 次多項式による補間を青線で描く。labels は各点の注記（同じ長さのリスト）。
    3点なら deg=2 で全点を通る（「log R を log T の多項式で表す」ような経験式の形）。戻り値は係数。"""
    xs = np.asarray(xs, dtype=float); ys = np.asarray(ys, dtype=float)
    fx = np.log10 if logx else (lambda v: v)
    fy = np.log10 if logy else (lambda v: v)
    gy = (lambda v: 10 ** v) if logy else (lambda v: v)
    co = np.polyfit(fx(xs), fy(ys), deg)
    lo, hi = x_range if x_range else (xs.min() * 0.85, xs.max() * 1.2)
    xx = np.logspace(np.log10(lo), np.log10(hi), 100) if logx else np.linspace(lo, hi, 100)
    ax.plot(xx, gy(np.polyval(co, fx(xx))), color=COL.blue, lw=2)
    ax.plot(xs, ys, "o", color=COL.red, ms=10, zorder=5)
    for x, y, s in zip(xs, ys, labels or []):
        ax.text(x * label_dx if logx else x + label_dx, y * label_dy if logy else y + label_dy, s, fontsize=fs, color=COL.red)
    if logx:
        ax.set_xscale("log")
    if logy:
        ax.set_yscale("log")
    return co


def range_bars(ax, ranges, log=False, y_step=1.0, fs=12, label_side="above"):
    """名前つきの範囲を横の両矢印で並べる。ranges = [(名前, 下限, 上限, 色), ...]（上から順）。
    片側だけ開いた範囲は下限/上限に None（その向きに矢印を伸ばす）。"""
    xmin, xmax = ax.get_xlim()
    for k, (name, lo, hi, color) in enumerate(ranges):
        y = -k * y_step
        a = lo if lo is not None else xmin
        b = hi if hi is not None else xmax
        ax.annotate("", xy=(a, y), xytext=(b, y), arrowprops=dict(arrowstyle="<->", color=color, lw=1.8))
        xm = np.sqrt(a * b) if log else (a + b) / 2
        dy = 0.18 * y_step if label_side == "above" else -0.35 * y_step
        ax.text(xm, y + dy, name, ha="center", fontsize=fs, color=color)
    if log:
        ax.set_xscale("log")
    ax.set_ylim(-(len(ranges) - 0.4) * y_step, 0.7 * y_step)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)


def equal_area_peaks(ax, widths, colors=None, x=None, fill=True, halfwidth_arrows=True):
    """面積が同じローレンツ形 (g/π)/(x²+g²) を重ねる。最も狭いピークの高さを1に規格化。戻り値は x。"""
    x = np.linspace(-6, 6, 600) if x is None else x
    colors = colors or [COL.lblue, COL.blue, COL.red][:len(widths)]
    lor = lambda g: (g / np.pi) / (x ** 2 + g ** 2)
    scale = 1 / lor(min(widths)).max()
    for z, (g, c) in enumerate(sorted(zip(widths, colors), key=lambda t: -t[0])):
        y = lor(g) * scale
        if fill:
            ax.fill_between(x, y, color=c, alpha=0.18, lw=0, zorder=2 + z)
        ax.plot(x, y, color=c, zorder=3 + z)
        if halfwidth_arrows:
            h = y.max() / 2
            ax.annotate("", xy=(-g, h), xytext=(g, h), arrowprops=dict(arrowstyle="<->", color=c, lw=1.3))
    noticks(ax)
    return x


def polar_pattern(ax, patterns, center=(0.0, 0.0), scale=1.0, axis_len=1.4, axis_label=None, fs=12):
    """角度分布 W(θ)（θ は軸からの角）を極座標の形で描く。patterns = [(W関数, 色, 線種), ...]。
    例: 等方 lambda t: 1+0*t（灰の破線）と異方 lambda t: 1-0.45*P2(cos t)（赤）。axis_label は軸の先の注記。"""
    th = np.linspace(0, 2 * np.pi, 400)
    cx, cy = center
    for W, color, ls in patterns:
        r = W(th) * scale
        ax.plot(cx + r * np.sin(th), cy + r * np.cos(th), color=color, ls=ls, lw=2.4)
    arrow(ax, (cx, cy - axis_len * scale), (cx, cy + axis_len * 1.05 * scale), lw=1.6, ms=14)
    ax.add_patch(Circle((cx, cy), 0.09 * scale, fc=COL.blue, ec="none"))
    if axis_label:
        ax.text(cx + 0.08 * scale, cy + axis_len * scale, axis_label, fontsize=fs, va="center")


def precession(ax, origin=(0.0, 0.0), length=2.2, tilt_deg=20, axis_label="$z$", vec_label="$M$", fs=14):
    """軸（黒）と、そこから tilt_deg 傾いたベクトル（赤）、先端が回る円錐の楕円（水色の破線）。"""
    ox, oy = origin
    arrow(ax, (ox, oy), (ox, oy + length * 1.02), lw=1.6, ms=14)
    ax.text(ox + 0.1, oy + length * 1.02, axis_label, fontsize=fs - 1, va="center")
    t = np.radians(tilt_deg)
    tip = (ox + 0.75 * length * np.sin(t) * 1.5, oy + 0.75 * length * np.cos(t))
    ax.add_patch(Ellipse((ox, tip[1]), 2 * (tip[0] - ox), 0.28, fc="none", ec=COL.lblue, lw=1.5, ls="--"))
    arrow(ax, (ox, oy), tip, color=COL.red, lw=2.8, ms=18)
    ax.text(tip[0] + 0.07, tip[1] - 0.45, vec_label, fontsize=fs + 2, color=COL.red)


def decay_signal(ax, tau=1.6, freq=3.0, t_max=6.0, envelope_label=r"$\propto e^{-t/\tau}$", fs=14):
    """減衰する振動（青）と包絡線（赤破線）。軸は中央の横線だけにして目盛りなし。"""
    t = np.linspace(0, t_max, 1200)
    ax.plot(t, np.exp(-t / tau) * np.cos(2 * np.pi * freq * t), color=COL.blue, lw=1.4)
    ax.plot(t, np.exp(-t / tau), color=COL.red, ls="--", lw=1.4)
    if envelope_label:
        ax.text(tau * 1.2, np.exp(-1.2) + 0.25, envelope_label, fontsize=fs, color=COL.red)
    ax.axhline(0, color=COL.ink, lw=0.8)
    ax.set_ylim(-1.05, 1.1)
    noticks(ax)


def dipole_lattice(ax, nx=5, ny=4, x0=1.25, y0=0.8, dx=0.51, dy=0.72, highlight=(2, 1), neighbor_arcs=True,
                   color=COL.lblue, hl_color=COL.red, ring=0.62):
    """格子上に上向きの双極子（矢印）を並べ、highlight=(i, j) を赤で強調し点線の円で囲む。
    neighbor_arcs=True なら、左右と上の隣から強調した双極子へ細い曲線矢印（周りがつくる場）を引く。戻り値は強調点の座標。"""
    hi, hj = highlight
    cx, cy = x0 + hi * dx, y0 + hj * dy
    for i in range(nx):
        for j in range(ny):
            if (i, j) == (hi, hj):
                continue
            x, y = x0 + i * dx, y0 + j * dy
            arrow(ax, (x, y - 0.17), (x, y + 0.17), color=color, lw=2.0, ms=11)
    arrow(ax, (cx, cy - 0.22), (cx, cy + 0.22), color=hl_color, lw=2.8, ms=14)
    ax.add_patch(Circle((cx, cy), ring, fc="none", ec=hl_color, lw=1.2, ls="--"))
    if neighbor_arcs:
        for (nx_, ny_), rad in [((cx - dx, cy), -0.5), ((cx + dx, cy), 0.5), ((cx, cy + dy), 0.6)]:
            ax.add_patch(FancyArrowPatch((nx_, ny_ + 0.05), (cx, cy + 0.08), connectionstyle=f"arc3,rad={rad}",
                                         arrowstyle="-|>", mutation_scale=10, color=COL.gray, lw=1.1))
    return cx, cy


# ---- サンプル（python figlib.py --demo out_dir） -----------------------------------------------

def bars(ax, labels, values, highlight=None, unit="", fmt="{:g}", xmax=None, fs=14):
    """図の種類「棒グラフ」：値を横棒で比べる。labels・values は上から順。highlight（番号か番号のリスト）の棒だけ青、ほかは灰。
    値を棒の先に書く（目盛りは消す）。大小の順に並べると読みやすい。"""
    hi = set([highlight] if isinstance(highlight, int) else (highlight or []))
    n = len(values)
    ys = list(range(n))[::-1]
    colors = [COL.blue if i in hi else COL.gray for i in range(n)]
    ax.barh(ys, values, color=colors, height=0.6)
    top = xmax or max(values) * 1.25
    for y, v, i in zip(ys, values, range(n)):
        ax.text(v + top * 0.015, y, fmt.format(v) + unit, va="center", fontsize=fs,
                color=COL.blue if i in hi else COL.ink, fontweight="bold" if i in hi else "normal")
    ax.set_yticks(ys)
    ax.set_yticklabels(labels, fontsize=fs)
    ax.set_xlim(0, top)
    ax.set_xticks([])
    ax.tick_params(axis="y", length=0)
    for side in ("top", "right", "bottom"):
        ax.spines[side].set_visible(False)


def share_bar(ax, parts, highlight=0, fs=14, label_min=0.08):
    """図の種類「帯グラフ」：全体の内訳を1本の帯で。parts = [(名前, 値), ...]（合計で割って100%にする）。
    highlight の部分だけ青、ほかは淡い色。狭い部分（label_min 未満）の名前は帯の下に出す。"""
    total = float(sum(v for _, v in parts))
    x = 0.0
    pale = [COL.lblue, COL.pale, COL.gray]
    for i, (name, v) in enumerate(parts):
        w = v / total
        c = COL.blue if i == highlight else pale[i % len(pale)]
        ax.barh(0, w, left=x, height=0.5, color=c, edgecolor="white", lw=2)
        txt = f"{name}\n{w * 100:.0f}%"
        if w >= label_min:
            ax.text(x + w / 2, 0, txt, ha="center", va="center", fontsize=fs, color="white" if i == highlight else COL.ink)
        else:
            ax.text(x + w / 2, -0.45, txt, ha="center", va="top", fontsize=fs - 2, color=COL.ink)
        x += w
    ax.set_xlim(0, 1)
    ax.set_ylim(-0.9, 0.4)
    ax.axis("off")


def timeline(ax, start, end, eras=(), events=(), highlight=None, fs=14):
    """図の種類「年表」：横の時間軸に、時代の帯 eras = [(名前, 始め, 終わり), ...] と、
    出来事 events = [(年, 名前), ...] の印を置く。highlight（出来事の番号）だけ赤。年は数（1997.25 のような小数も可）。
    出来事と時代の帯が合わせて2つ以下なら WARN（線の上に点が2つだけの年表は、表か本文の1行で足りる。試しの回で2枚あった）。"""
    if len(events) + len(eras) <= 2:
        print(f"  [WARN] 年表：出来事と時代の帯が {len(events) + len(eras)} つだけ → 3つ以上の出来事・時代の区切りが無いなら、"
              "本文の1行か表にする（年表にするなら、前後の出来事を足して流れが見えるように）")
    pale = [COL.pale, COL.lblue, COL.blue]
    for i, (name, a, b) in enumerate(eras):
        c = pale[i % len(pale)]
        ax.barh(0.5, (b or end) - a, left=a, height=0.5, color=c, edgecolor="white", lw=2)
        ax.text((a + (b or end)) / 2, 0.5, name, ha="center", va="center", fontsize=fs,
                color="white" if c == COL.blue else COL.ink)
    ax.plot([start, end], [0, 0], color=COL.ink, lw=LW.axis if hasattr(LW, "axis") else 1.5)
    for i, (year, name) in enumerate(events):
        c = COL.red if i == highlight else COL.ink
        ax.plot([year], [0], marker="o", color=c, ms=7)
        up = i % 2 == 0
        ax.text(year, -0.25 if up else -0.75, f"{int(year)}\n{name}" if name else f"{int(year)}", ha="center", va="top",
                fontsize=fs - 1, color=c, fontweight="bold" if i == highlight else "normal")
    ax.set_xlim(start - (end - start) * 0.03, end + (end - start) * 0.03)
    ax.set_ylim(-1.6, 1.0)
    ax.axis("off")


def _demo(outdir):
    import os
    from figkit import blank, box, fig, save
    os.makedirs(outdir, exist_ok=True)
    T = np.logspace(0, np.log10(300), 300)

    f, ax = fig(5.0, 3.6)
    semi = np.exp(60 * (1 / T - 1 / 300)); metal = 0.01 + (T / 300) ** 1.5
    compare(ax, T, semi, metal, ("主役（青実線）", (12, 2e3)), ("比較対象（灰破線）", (1.2, 2e-2)))
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_ylim(3e-3, 1e6); noticks(ax)
    ax.set_xlabel("温度 $T$"); ax.set_ylabel("$\\rho$（対数）"); ax.set_title("compare", fontsize=13)
    save(f, f"{outdir}/compare.png")

    f, ax = fig(5.0, 3.6)
    p1 = np.full_like(T, 0.01); p2 = (T / 300) ** 3 / (1 + (T / 120) ** 2) * 2
    decompose(ax, T, [(p1, ("成分1（一定）", (1.2, 0.013)), COL.gray), (p2, ("成分2", (40, 1e-3)), COL.lblue)],
              total_label=("和 = 成分1 + 成分2", (5, 0.3)))
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_ylim(5e-5, 2); noticks(ax); ax.set_title("decompose", fontsize=13)
    save(f, f"{outdir}/decompose.png")

    f, ax = fig(5.0, 3.6)
    x = np.linspace(0, 10, 300); y = 1 / (1 + np.exp(-(x - 5) / 1.3))
    ax.plot(x, y, color=COL.blue)
    tangent(ax, x, y, 5.0, 1.1, label=("接線の傾き＝分解能", (5.8, 0.25)))
    noticks(ax); ax.set_title("tangent", fontsize=13)
    save(f, f"{outdir}/tangent.png")

    f, ax = fig(5.0, 3.6)
    extrapolate(ax, [(0.04, "A", COL.blue), (0.09, "B", COL.lblue), (-0.05, "C", COL.green)], x_from=0.18,
                mark_label=("$x\\to0$ で共通", (0.15, 0.86)))
    ax.set_xlim(0, 1.15); ax.set_ylim(0.8, 1.13); noticks(ax); ax.set_title("extrapolate", fontsize=13)
    save(f, f"{outdir}/extrapolate.png")

    f, ax = fig(5.0, 3.6)
    data_fit(ax, [0.3, 1.0, 4.0], [21e3, 840, 170], labels=["0.3 K：21 kΩ", "1 K：840 Ω", "4 K：170 Ω"],
             x_range=(0.25, 5))
    ax.minorticks_off(); ax.set_title("data_fit", fontsize=13)
    save(f, f"{outdir}/data_fit.png")

    f, ax = fig(5.0, 3.0)
    ax.set_xlim(1e-3, 300)
    range_bars(ax, [("範囲A", 1, 5, COL.blue), ("範囲B", 0.3, 3.3, COL.red), ("範囲C（上は開放）", 3, None, COL.green)], log=True)
    ax.set_xlabel("温度 (K)"); ax.set_title("range_bars", fontsize=13)
    save(f, f"{outdir}/range_bars.png")

    f, ax = fig(5.0, 3.6)
    equal_area_peaks(ax, [1.8, 0.45]); ax.set_ylim(0, 1.12); ax.set_title("equal_area_peaks", fontsize=13)
    save(f, f"{outdir}/equal_area_peaks.png")

    f, ax = fig(5.0, 2.6)
    bars(ax, ["主役", "比較A", "比較B", "比較C"], [56.9, 33.0, 17.9, 9.0], highlight=0, unit="%")
    ax.set_title("bars", fontsize=13)
    save(f, f"{outdir}/bars.png")

    f, ax = fig(5.0, 1.6)
    share_bar(ax, [("主役", 27), ("その他", 66), ("小", 7)])
    ax.set_title("share_bar", fontsize=13)
    save(f, f"{outdir}/share_bar.png")

    f, ax = fig(6.0, 2.4)
    timeline(ax, 1995, 2026, eras=[("第1期", 1997, 2002), ("第2期", 2002, 2013), ("第3期", 2013, None)],
             events=[(1997, "開始"), (2013, "改定"), (2023, "今の版")], highlight=2)
    ax.set_title("timeline", fontsize=13)
    save(f, f"{outdir}/timeline.png")

    f, ax = blank(4.6, 4.0)
    P2 = lambda t: 0.5 * (3 * np.cos(t) ** 2 - 1)
    polar_pattern(ax, [(lambda t: 1 + 0 * t, COL.gray, "--"), (lambda t: 1 - 0.45 * P2(t), COL.red, "-")],
                  center=(2.3, 1.9), scale=1.35, axis_label="対称軸")
    ax.text(2.3, -0.15, "polar_pattern", ha="center", fontsize=13)
    save(f, f"{outdir}/polar_pattern.png")

    f, ax = blank(3.0, 3.2)
    precession(ax, origin=(1.2, 0.3)); ax.text(1.5, 0.0, "precession", ha="center", fontsize=13)
    save(f, f"{outdir}/precession.png")

    f, ax = fig(4.0, 2.6)
    decay_signal(ax); ax.set_title("decay_signal", fontsize=13)
    save(f, f"{outdir}/decay_signal.png")

    f, ax = blank(4.2, 3.6)
    box(ax, 0.9, 0.45, 2.75, 2.85, fc=COL.pale, ec="none", r=0.15)
    dipole_lattice(ax)
    ax.text(2.25, 0.1, "dipole_lattice", ha="center", fontsize=13)
    save(f, f"{outdir}/dipole_lattice.png")


if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, "reconfigure"):   # パイプで走らせると日本語の Windows では cp932 になり、✔ や珍しい字で落ちる
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    import sys
    if len(sys.argv) >= 3 and sys.argv[1] == "--demo":
        _demo(sys.argv[2])
    else:
        print(__doc__)
