"""第1回 What a Chat AI Computes の図（図の担当 2/2：7〜10枚目）。値の出どころは memo.md の3節・3b節。

    python figs_2.py                 # 7〜10枚目の図を figs/ に書き出す
    python figs_2.py s08_personqa    # 一部だけ描き直す（関数名の f_ を除いた名前）

図は右の本文の場所（幅 5.4〜6 in・高さ 3.6〜4.3 in）を埋める大きさで描き、描いた幅のまま置く。
"""
import sys
from pathlib import Path

import numpy as np

SKILL = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(SKILL / "scripts"))
from figkit import COL, callout, fig, save  # noqa: E402

OUT = Path(__file__).resolve().parent / "figs"
FS = 14


def f_s07_fabricated():
    """7枚目（figs/s07.png）：比べる：棒グラフ：データ2
    気づく：GPT-3.5 が挙げた参考文献の半分以上（55%）は存在しない。新しい GPT-4 でも約5件に1件（18%）。
    （GPT-3.5 の棒だけ赤、GPT-4 は灰。半分の線を灰の破線で引き、赤い棒が線を越えるのを見せる。
    実在の文献の誤り 43%・24% は分母が違うので図に入れず、原稿・11枚目のノートで言う）
    出典：Walters & Wilder, Sci. Rep. 13, 14045 (2023)。参考文献 636 件
    """
    f, ax = fig(5.4, 4.3)
    names, vals = ["GPT-3.5", "GPT-4"], [55, 18]
    ax.bar(names, vals, color=[COL.dred, COL.gray], width=0.55)
    for x, v in zip([0, 1], vals):
        ax.text(x, v + 2, f"{v}%", ha="center", fontsize=FS)
    ax.axhline(50, color=COL.gray, ls="--", lw=1)
    ax.text(1.42, 51.5, "Half", ha="right", va="bottom", fontsize=FS, color=COL.gray)
    callout(ax, "1 in 5", target=(1.2, 12), at=(1.25, 32), color=COL.ink)
    ax.set_xlim(-0.55, 1.55)
    ax.set_ylim(0, 70)
    ax.set_ylabel("References that do not exist (%)", fontsize=FS)
    ax.tick_params(labelsize=FS)
    save(f, OUT / "s07.png")


def f_s08_personqa():
    """8枚目（figs/s08.png）：比べる：棒グラフ：データ3
    気づく：新しいモデルほど作り話が減ると思いがちだが、o3 の作り話の率は前の o1 の約2倍（33% 対 16%）、o4-mini は約3倍（48%）
    （古い o1 の棒は灰、新しい o3・o4-mini は赤。o1 の高さに灰の破線を横に引き、新しい2本がその上に伸びるのを見せる。
    倍率 ×2・×3 を棒の値の下に赤で）
    出典：OpenAI o3 and o4-mini System Card (2025-04-16) Table 4。割合 0.16・0.33・0.48 を % で描く
    """
    f, ax = fig(5.6, 4.3)
    names = ["o1\n(older)", "o3\n(newer)", "o4-mini\n(newer)"]
    vals = [16, 33, 48]
    x = np.arange(3)
    ax.bar(x, vals, color=[COL.gray, COL.dred, COL.dred], width=0.5)
    for xi, v in zip(x, vals):
        ax.text(xi, v + 1.5, f"{v}%", ha="center", fontsize=FS)
    for xi, k in [(1, "×2"), (2, "×3")]:
        ax.text(xi, vals[xi] - 5, k, ha="center", va="center", fontsize=FS, color="white", fontweight="bold")
    ax.plot([-0.3, 3.0], [16, 16], color=COL.gray, ls="--", lw=1)
    ax.text(2.7, 17.5, "o1 level", ha="center", va="bottom", fontsize=FS, color=COL.gray)
    ax.set_xticks(x, names)
    ax.set_xlim(-0.5, 3.1)
    ax.set_ylim(0, 58)
    ax.set_ylabel("Made-up answers (%)", fontsize=FS)
    ax.tick_params(labelsize=FS)
    save(f, OUT / "s08.png")


def f_s09_simpleqa():
    """9枚目（figs/s09.png）：比べる：棒グラフ（100% の横の積み上げ）：データ1
    気づく：正解率はほぼ同じ（22 と 24）なのに、「分からない」と言わない古いモデル（o4-mini）は間違いが3倍近い（26 → 75）。
    当てずっぽうで答えると正解はわずかに増えるが、作り話が大きく増える
    （1モデル1本の横棒を「答えない（灰）・正解（青）・間違い（赤）」に分け、上下に並べる。青の幅がほぼ同じで、
    赤の幅だけが大きく違うのが見える。区分の名前は上の棒の各区間の上に直接書く。凡例なし）
    出典：OpenAI "Why language models hallucinate" (2025-09-05) の SimpleQA の表
    """
    f, ax = fig(5.8, 3.6)
    rows = [("o4-mini", [1, 24, 75]), ("gpt-5-\nthinking-mini", [52, 22, 26])]
    cols = [COL.gray, COL.blue, COL.dred]   # 赤の面は落ち着いた赤
    cats = ["I don't know", "Right", "Wrong"]
    for yi, (name, v) in enumerate(rows):
        left = 0
        for k, (val, c) in enumerate(zip(v, cols)):
            ax.barh(yi, val, left=left, color=c, height=0.5)
            if val >= 10:
                ax.text(left + val / 2, yi, f"{val}%", ha="center", va="center", fontsize=FS, color="white")
            else:
                ax.text(left + val / 2 + 1, yi - 0.4, f"{val}%", ha="left", va="center", fontsize=FS, color=COL.ink)
            if yi == 1:
                ax.text(left + val / 2, yi + 0.42, cats[k], ha="center", va="bottom", fontsize=FS, color=c)
            left += val
    ax.set_yticks([0, 1], [r[0] for r in rows])
    ax.set_xlim(0, 100)
    ax.set_ylim(-0.6, 1.75)
    ax.set_xticks([])
    ax.spines["bottom"].set_visible(False)
    ax.tick_params(labelsize=FS, left=False)
    save(f, OUT / "s09.png")


def f_s10_longtail():
    """10枚目（figs/s10.png）：傾向：折れ線（横軸は対数）：Kandpal et al. (ICML 2023) Figure 1 から読んだ2点（BLOOM-176B・TriviaQA）
    気づく：関連する学習の文書が約10件しかない事実は正答率が約25%。約1万件ある事実では55%を超える。
    見たことの少ない事実ほど、当たらない
    （2点を青の線で結ぶ。少ない側の点を赤にし「Rare facts」の引き出し線、多い側は青の点に「Common facts」。
    2点は図から読んだ概略の値なので、スライド側で「（概略）」と出典の注記を付ける）
    """
    # 外から見た採点の指摘：2点を直線で結んだだけで意味が薄い → 2つの事実の答えを「正解（青）」と「正解でない（赤）」の
    # 積み上げ棒にし、まれな事実では4つに3つが外れるのを面で見せる。値は同じ2点（≈25%、>55%）だけ
    f, ax = fig(5.8, 4.3)
    x = [0, 1.35]
    right, low = [25, 55], ["≈", ">"]
    ax.bar(x, right, color=COL.blue, width=0.5)
    ax.bar(x, [100 - r for r in right], bottom=right, color=COL.dred, width=0.5)
    for xi, r, sym in zip(x, right, low):
        ax.text(xi, r / 2, f"{sym}{r}%", ha="center", va="center", fontsize=FS, color="white")
        if sym == "≈":   # 外れの割合は、まれな事実の側だけ書く（ラベルは5つまで）
            ax.text(xi, r + (100 - r) / 2, f"≈{100 - r}%", ha="center", va="center", fontsize=FS, color="white")
    ax.text(1.65, 27, "Right", ha="left", va="center", fontsize=FS, color=COL.blue)
    ax.text(1.65, 78, "Not right", ha="left", va="center", fontsize=FS, color=COL.dred)
    ax.set_xticks(x, ["Rare fact\n(≈10 documents)", "Common fact\n(≈10,000 documents)"])
    ax.set_xlim(-0.5, 2.3)
    ax.set_ylim(0, 100)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_ylabel("Answers (%)", fontsize=FS)
    ax.set_title("BLOOM-176B on TriviaQA", fontsize=FS)
    ax.tick_params(labelsize=FS)
    save(f, OUT / "s10.png")


if __name__ == "__main__":
    names = sys.argv[1:]
    for n, fn in list(globals().items()):
        if n.startswith("f_") and callable(fn) and (not names or n[2:] in names):
            fn()
