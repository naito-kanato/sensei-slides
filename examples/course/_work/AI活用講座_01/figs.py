"""講座の見本 第1回「生成AIは何をしているか」の図（すべて自分で描く。値の出どころは memo.md の3節）。

    python figs.py            # 全部の図を figs/ に書き出す
    python figs.py temperature  # 一部だけ描き直す（関数名の f_ を除いた名前）

図は右の本文の場所（幅 5.4〜6 in・高さ 3〜4.3 in）を埋める大きさで描き、描いた幅のまま置く
（以前は幅 4.2〜4.6 in で描いていて、本文と図の間が 2 in 以上空いていた）。図の文字は 14pt のまま。
"""
import sys
from pathlib import Path

import numpy as np
from matplotlib.patches import Rectangle

SKILL = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(SKILL / "scripts"))
from figkit import COL, arrow, blank, box, fig, save  # noqa: E402

OUT = Path(__file__).parent / "figs"
FS = 14
WORDS = ["晴れ", "雨", "曇り", "雪"]
PROBS = [0.42, 0.25, 0.18, 0.06]          # 説明のための例（実在のモデルの値ではない）


def f_next_token():
    """「明日の天気は」の次のトークンの候補と確率（説明のための例）"""
    f, ax = fig(5.8, 4.3)
    words, probs = WORDS[::-1], PROBS[::-1]
    colors = [COL.gray, COL.gray, COL.gray, COL.blue]
    ax.barh(words, probs, color=colors, height=0.6)
    for w, p in zip(words, probs):
        ax.text(p + 0.01, w, f"{p:.2f}", va="center", fontsize=FS)
    ax.set_xlim(0, 0.55)
    ax.set_xlabel("次に来る確率", fontsize=FS)
    ax.set_title("「明日の天気は」の次", fontsize=FS)
    ax.tick_params(labelsize=FS)
    save(f, OUT / "next_token.png")


def f_tokens():
    """「明日の天気は晴れ」をトークンに分けた例（分け方は例。実際はモデルで違う）"""
    k = 1.2   # 以前の 5.0×2.4 in の座標を 1.2 倍に
    f, ax = blank(5.0 * k, 2.4 * k)
    ax.text(2.5 * k, 2.05 * k, "明日の天気は晴れ", ha="center", va="center", fontsize=20)
    arrow(ax, (2.5 * k, 1.75 * k), (2.5 * k, 1.3 * k))
    toks = ["明日", "の", "天気", "は", "晴れ"]
    ws = [0.95 * k, 0.6 * k, 0.95 * k, 0.6 * k, 0.95 * k]
    gap = 0.12 * k
    x = (5.0 * k - sum(ws) - gap * (len(ws) - 1)) / 2
    for t, w in zip(toks, ws):
        box(ax, x, 0.55 * k, w, 0.6 * k, t, fs=18)
        x += w + gap
    ax.text(2.5 * k, 0.2 * k, "5 トークン", ha="center", va="center", fontsize=16, color=COL.blue)
    save(f, OUT / "tokens.png")


def f_params():
    """パラメータの数：GPT-2（Radford et al., 2019）と GPT-3（Brown et al., 2020）"""
    f, ax = fig(4.4, 3.2)
    names, vals = ["GPT-2\n（2019）", "GPT-3\n（2020）"], [15, 1750]
    ax.bar(names, vals, color=[COL.gray, COL.blue], width=0.55)
    for x, v in zip([0, 1], ["15億", "1750億"]):
        ax.text(x, vals[x] + 50, v, ha="center", fontsize=FS)
    ax.set_ylim(0, 2050)
    ax.set_ylabel("パラメータの数（億）", fontsize=FS)
    ax.tick_params(labelsize=FS)
    save(f, OUT / "params.png")


def f_temperature():
    """温度を変えると、選ばれる確率がどう変わるか（2枚目の例の確率を4候補で規格化し、p^(1/T) から計算）"""
    p = np.array(PROBS) / sum(PROBS)
    f, ax = fig(5.8, 4.3)
    x = np.arange(len(WORDS))
    temps = [(0.5, COL.blue), (1.0, COL.gray), (2.0, COL.orange)]   # 赤は本文の結論の色なので使わない
    w = 0.26
    for k, (T, c) in enumerate(temps):
        q = p ** (1 / T)
        q /= q.sum()
        ax.bar(x + (k - 1) * w, q, width=w, color=c)
        ax.text(0 + (k - 1) * w, q[0] + 0.015, f"{T:g}", ha="center", va="bottom", fontsize=FS, color=c)   # 凡例の代わりに、晴れの棒の上に温度
    ax.text(0.95, 0.66, "棒の上の数：温度", ha="left", va="center", fontsize=FS)
    ax.set_xticks(x, WORDS)
    ax.set_ylim(0, 0.75)
    ax.set_ylabel("選ばれる確率", fontsize=FS)
    ax.tick_params(labelsize=FS)
    save(f, OUT / "temperature.png")


def f_fabricated():
    """ChatGPT が挙げた文献のうち実在しないものの割合（Walters & Wilder, Sci. Rep. 13, 14045 (2023)）"""
    f, ax = fig(5.4, 4.3)
    ax.bar(["GPT-3.5", "GPT-4"], [55, 18], color=[COL.red, COL.blue], width=0.55)
    for x, v in zip([0, 1], [55, 18]):
        ax.text(x, v + 2, f"{v}%", ha="center", fontsize=FS)
    ax.set_ylim(0, 70)
    ax.set_ylabel("実在しない文献の割合（%）", fontsize=FS)
    ax.tick_params(labelsize=FS)
    save(f, OUT / "fabricated.png")


def f_cutoff():
    """学習データの範囲と締め切り、その後の時間軸（GPT-4 は 2021年9月：OpenAI, 2023）"""
    k = 1.15   # 以前の 5.2×2.6 in の座標を 1.15 倍に
    f, ax = blank(5.2 * k, 2.6 * k)
    ax.add_patch(Rectangle((0.2 * k, 1.0 * k), 3.0 * k, 0.7 * k, fc=COL.pale, ec=COL.ink, lw=1.5))
    ax.text(1.7 * k, 1.35 * k, "学習データ", ha="center", va="center", fontsize=16)
    ax.plot([3.2 * k, 3.2 * k], [0.75 * k, 2.0 * k], color=COL.red, lw=2.5)
    ax.text(3.2 * k, 2.25 * k, "締め切り", ha="center", va="center", fontsize=16, color=COL.red)
    ax.text(4.15 * k, 1.35 * k, "知らない", ha="center", va="center", fontsize=16, color=COL.gray)
    arrow(ax, (0.2 * k, 0.55 * k), (5.05 * k, 0.55 * k))
    ax.text(4.95 * k, 0.2 * k, "今", ha="center", va="center", fontsize=16)
    save(f, OUT / "cutoff.png")


def f_cot():
    """算数の文章題（GSM8K）の正答率：答えだけの例を見せる 17.9%、途中の考えを書いた例を見せる 56.9%（Wei et al., NeurIPS 2022, Table 2, PaLM 540B）"""
    f, ax = fig(5.4, 4.3)
    names, vals = ["答えだけの例", "途中の考えを\n書いた例"], [17.9, 56.9]
    ax.bar(names, vals, color=[COL.gray, COL.blue], width=0.55)
    for x, v in zip([0, 1], vals):
        ax.text(x, v + 2, f"{v}%", ha="center", fontsize=FS)
    ax.set_ylim(0, 70)
    ax.set_ylabel("正答率（%）", fontsize=FS)
    ax.set_title("算数の文章題", fontsize=FS)
    ax.tick_params(labelsize=FS)
    save(f, OUT / "cot.png")


def f_dont_input():
    """入れる前に止まる3つ（個人情報保護委員会「生成AIサービスの利用に関する注意喚起等」2023 をもとに）"""
    s = 1.15   # 以前の 4.2×3.6 in の座標を 1.15 倍に
    f, ax = blank(4.2 * s, 3.6 * s)
    ax.text(2.1 * s, 3.3 * s, "入れる前に確認", ha="center", va="center", fontsize=18, color=COL.red)
    for k, t in enumerate(["個人情報", "社外秘の資料", "未発表のデータ"]):
        box(ax, 0.5 * s, (2.25 - k * 0.95) * s, 3.2 * s, 0.7 * s, t, fc="white", ec=COL.ink, fs=18)
    save(f, OUT / "dont_input.png")


if __name__ == "__main__":
    names = sys.argv[1:] or [k[2:] for k in list(globals()) if k.startswith("f_")]
    for nm in names:
        globals()["f_" + nm]()
