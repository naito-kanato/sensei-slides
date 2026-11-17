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
    """「明日の天気は晴れ」と「ハルシネーション」をトークンに分けた例（分け方は例。実際はモデルで違う）。
    上の段は語ごとに1つ、下の段は1語が語の一部（3つ）に分かれる様子"""
    W, H = 6.0, 4.7
    f, ax = blank(W, H)

    def row(y, text, toks, ws, label):
        ax.text(W / 2, y + 1.3, text, ha="center", va="center", fontsize=20)
        arrow(ax, (W / 2, y + 1.0), (W / 2, y + 0.78))
        gap = 0.14
        x = (W - sum(ws) - gap * (len(ws) - 1)) / 2
        for t, w in zip(toks, ws):
            box(ax, x, y, w, 0.62, t, fs=18)
            x += w + gap
        ax.text(W / 2, y - 0.32, label, ha="center", va="center", fontsize=16, color=COL.blue)

    row(2.75, "明日の天気は晴れ", ["明日", "の", "天気", "は", "晴れ"], [1.0, 0.65, 1.0, 0.65, 1.0], "5 トークン（語ごと）")
    row(0.45, "ハルシネーション", ["ハル", "シネー", "ション"], [1.1, 1.35, 1.35], "1語が 3 トークン（語の一部）")
    save(f, OUT / "tokens.png")


def f_scaling():
    """大きさと予測の誤差（概略）：両方の軸を対数目盛りにすると、べき乗則は右下がりの直線になる。
    大きさ10倍ごとに誤差が決まった割合で下がり、傾向は7桁以上の範囲で続いた（Kaplan et al., 2020）。
    誤差の値・傾きは説明のための形（実際の値ではない）。横軸は一番小さいモデルを1とした倍率"""
    f, ax = fig(6.6, 4.6)
    x = np.logspace(0, 7, 50)
    y = 4.0 * x ** (-0.11)
    ax.plot(x, y, color=COL.blue, lw=2.5)
    for x0, lab in ((1e1, "決まった割合で減少"), (1e5, "同じ割合で減少")):   # 10倍ごとの段（同じ形が2か所）
        x1, y0, y1 = x0 * 10, 4.0 * x0 ** (-0.11), 4.0 * (x0 * 10) ** (-0.11)
        ax.plot([x0, x1], [y0, y0], color=COL.gray, lw=1.2, ls="--")
        ax.plot([x1, x1], [y0, y1], color=COL.red, lw=2.0)
        ax.text(10 ** (np.log10(x0) + 0.5), y0 * 1.04, "10倍", ha="center", va="bottom", fontsize=14, color=COL.text)
        ax.text(x1 * 1.4, (y0 * y1) ** 0.5, lab, ha="left", va="center", fontsize=14, color=COL.red)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(0.6, 2e7)
    ax.set_ylim(0.6, 4.8)
    ax.set_xticks([1, 1e2, 1e4, 1e6], ["1", "100", "1万", "100万"])
    ax.set_yticks([])
    ax.minorticks_off()
    ax.set_xlabel("モデルの大きさ（最小を1とした倍率・対数目盛り）", fontsize=14)
    ax.set_ylabel("予測の誤差（対数目盛り）", fontsize=14)
    ax.tick_params(labelsize=14)
    save(f, OUT / "scaling.png")


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
    f, ax = fig(6.4, 4.6)   # 図が主役の型（s.figure_main）で左に大きく置く幅
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
    ax.bar(["GPT-3.5", "GPT-4"], [55, 18], color=[COL.dred, COL.blue], width=0.55)   # 赤の棒は落ち着いた赤（原色の赤の面は浮く）
    for x, v in zip([0, 1], [55, 18]):
        ax.text(x, v + 2, f"{v}%", ha="center", fontsize=FS)
    ax.set_ylim(0, 70)
    ax.set_ylabel("実在しない文献の割合（%）", fontsize=FS)
    ax.tick_params(labelsize=FS)
    save(f, OUT / "fabricated.png")


def f_cutoff():
    """学習データの範囲と締め切り、その後の時間軸（GPT-4 は 2021年9月：OpenAI, 2023）。図が主役の型で左に大きく置く"""
    W, H = 6.4, 4.6   # 置く幅（右の列に場合分けを置いた残り）で描く。縮めて置くと文字が 14pt を切った
    f, ax = blank(W, H)
    xc = 3.9   # 締め切りの位置
    ax.add_patch(Rectangle((0.15, 1.45), xc - 0.15, 1.95, fc=COL.pale, ec=COL.ink, lw=1.5))
    ax.text((0.15 + xc) / 2, 2.42, "学習データ（文章）", ha="center", va="center", fontsize=20)
    ax.add_patch(Rectangle((xc, 1.45), W - 0.15 - xc, 1.95, fc="white", ec=COL.gray, lw=1.2, ls=(0, (4, 3))))
    ax.text((xc + W - 0.15) / 2, 2.75, "締め切りの後の\n出来事", ha="center", va="center", fontsize=16, color=COL.text)
    ax.text((xc + W - 0.15) / 2, 1.95, "→ 知らない", ha="center", va="center", fontsize=18, color=COL.text)
    ax.plot([xc, xc], [1.15, 3.7], color=COL.red, lw=2.5)
    ax.text(xc, 4.35, "締め切り", ha="center", va="center", fontsize=20, color=COL.red)
    ax.text(xc, 3.95, "（GPT-4 は 2021年9月）", ha="center", va="center", fontsize=16, color=COL.ink)
    arrow(ax, (0.15, 0.8), (W - 0.05, 0.8))
    ax.text(0.15, 0.4, "時間", ha="left", va="center", fontsize=16)
    ax.text(W - 0.25, 0.4, "今", ha="center", va="center", fontsize=16)
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
