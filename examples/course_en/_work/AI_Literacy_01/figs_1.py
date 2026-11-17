"""AI_Literacy 第1回の図（図の担当1：2・3・5・6枚目）。

    python figs_1.py               # 全部を figs/ に描く
    python figs_1.py temperature   # 一部だけ（関数名から f_ を除いた名前）
"""
import sys
from pathlib import Path

import numpy as np
from matplotlib.patches import Polygon, Rectangle

SKILL = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(SKILL / "scripts"))
from figkit import COL, arrow, blank, callout, fig, save  # noqa: E402

OUT = Path(__file__).resolve().parent / "figs"
FS = 14
# 2枚目の例（説明のための例。実在のモデルの値ではない）。6枚目もこの値から計算する
WORDS = ["Canberra", "Sydney", "Melbourne", "other"]
PROBS = np.array([0.62, 0.25, 0.08, 0.05])


def f_s02():
    """2枚目：比べる：棒グラフ："The capital of Australia is" の次のトークンの候補と確率（確率は例）〔事実16〕
    気づく：一番の Canberra（青）でも 62% で 100% ではなく、首都でない Sydney（赤）にも 25% の確率が付く。Sydney に引き出し線で「Largest city, not the capital」
    """
    f, ax = fig(5.8, 4.0)
    words, probs = WORDS[::-1], PROBS[::-1] * 100
    colors = [COL.gray, COL.gray, COL.dred, COL.blue]   # 赤の棒は落ち着いた赤（原色の赤の面は浮く）
    ax.barh(words, probs, color=colors, height=0.6)
    for w, p in zip(words, probs):
        ax.text(p + 1.2, w, f"{p:.0f}%", va="center", fontsize=FS)
    ax.set_xlim(0, 80)
    ax.set_xlabel("Probability of coming next (%)", fontsize=FS)
    ax.set_title("Next token after \"The capital of Australia is\"", fontsize=FS)
    ax.tick_params(labelsize=FS)
    callout(ax, "Largest city,\nnot the capital", target=(16, 1.72), at=(52, 1.05), color=COL.red)
    save(f, OUT / "s02.png")


def f_s03():
    """3枚目：仕組み：模式図："The capital of Australia is" をトークンの箱に分ける（分け方は例。モデルで違う）
    実物：1文字ずつのマス目に並べた文の帯と、それを切ったトークンの札（空白は次の語の札の頭に付く）
    気づく：27文字が5つの札になる＝1札に数文字。上の文字のマスと下の札を同じ幅でそろえ、比べの相手（文字）を同じ図に置く
    配置：上に文字のマス、下に同じ位置で切った札（前後＝切る前と後）
    ラベル：27 characters、5 tokens
    下の段：まれな語（Wollongong）が語の一部の2つの札に割れる例（外から見た採点の指摘：語の一部に分かれる様子が見えなかった）
    """
    W, H = 8.6, 3.35                                           # 上に文・下に図の型（s.figure_below）で横いっぱいに置く幅
    cw = 0.28                                                  # 1文字のマスの幅（in）
    f, ax = blank(W, H)

    def row(text, toks, yc, yt):
        """上に1文字ずつのマス（yc）、下に同じ位置で切った札（yt）。左端の x を返す"""
        x0 = (W - cw * len(text)) / 2
        ax.add_patch(Rectangle((x0 - 0.06, yc - 0.1), cw * len(text) + 0.12, 0.52, fc=COL.light, ec="none"))
        for i, ch in enumerate(text):
            ax.text(x0 + (i + 0.5) * cw, yc + 0.16, "·" if ch == " " else ch, ha="center", va="center",
                    fontsize=FS, color=COL.gray if ch == " " else COL.ink, family="monospace")
        for a, b in toks:
            g = 0.035
            ax.add_patch(Rectangle((x0 + a * cw + g, yt), (b - a) * cw - 2 * g, 0.56, fc=COL.pale, ec=COL.blue, lw=1.2))
            ax.text(x0 + (a + b) / 2 * cw, yt + 0.28, text[a:b].strip(), ha="center", va="center", fontsize=FS + 1)
            for xx in (x0 + a * cw, x0 + b * cw):               # 切れ目を上下でつなぐ点線
                ax.plot([xx, xx], [yt + 0.6, yc - 0.14], color=COL.gray, lw=0.8, ls=(0, (2, 2)))
        return x0, x0 + cw * len(text)

    text = "The capital of Australia is"
    toks = [(0, 3), (3, 11), (11, 14), (14, 24), (24, 27)]     # GPT-2 型の分け方の例（空白は後ろの語の頭）
    row(text, toks, 2.85, 1.95)
    ax.text(W / 2, 1.62, f"{len(toks)} tokens", ha="center", va="center", fontsize=FS + 2, color=COL.blue)
    # 下の段：まれな語は語の一部に割れる（分け方は例）
    xa, xb = row("Dubbo", [(0, 3), (3, 5)], 0.85, 0.05)   # まれな地名（分け方は例）
    ax.text(xa - 0.25, 1.0, "A rare word", ha="right", va="center", fontsize=FS, color=COL.text)
    ax.text(xb + 0.25, 0.33, "2 tokens", ha="left", va="center", fontsize=FS + 2, color=COL.blue)
    save(f, OUT / "s03.png")


def _doc(ax, x, y, w, h):
    """角を折った紙（平塗り・細い輪郭）"""
    c = 0.22
    ax.add_patch(Polygon([(x, y), (x + w, y), (x + w, y + h - c), (x + w - c, y + h), (x, y + h)],
                         closed=True, fc="white", ec=COL.ink, lw=1.2))
    ax.add_patch(Polygon([(x + w - c, y + h), (x + w - c, y + h - c), (x + w, y + h - c)],
                         closed=True, fc=COL.light, ec=COL.ink, lw=1.0))


def _rows(ax, x, ytop, w, rows):
    """文書の中の行：左に話し手の札、右に文の行（灰色の帯）。最後の AI は空きの1マス（次のトークン）。空きの中心を返す"""
    dy, slot = 0.45, None
    for k, (who, n) in enumerate(rows):
        y = ytop - k * dy
        ax.text(x + 0.12, y, who, ha="left", va="center", fontsize=FS,
                color=COL.blue if who == "You" else COL.ink)
        bx = x + 1.3
        if n == 0:                                             # 次のトークンの空き
            ax.add_patch(Rectangle((bx, y - 0.14), 0.34, 0.28, fc="white", ec=COL.red, lw=1.5))
            slot = (bx + 0.17, y - 0.14)
        else:
            fc = {"You": COL.lblue, "AI": COL.gray}.get(who, COL.pale)
            ax.add_patch(Rectangle((bx, y - 0.07), (w - 1.45) * n, 0.14, fc=fc, ec="none"))
    return slot


def f_s05():
    """5枚目：仕組み：模式図：チャット全体を1枚の文書として描き、最後に次のトークンの空き〔事実6〕
    実物：角を折った紙の文書。中に話し手（Instructions・You・AI）の行が文の帯で並び、最後の AI の行は空きの1マス
    気づく：2回目の文書は、1回目の全部（指示・質問・返事）を含んだまるごとの文書で、続きの空きはいつも末尾の1マス。比べの相手に1回目の文書を左に置く
    配置：左右で比べる（左に1回目、右に2回目。間に矢印）
    ラベル：Turn 1、Turn 2、Next token
    """
    W, H = 5.8, 3.9
    f, ax = blank(W, H)
    dw = 2.55
    # 1回目
    _doc(ax, 0.1, 1.6, dw, 1.7)
    _rows(ax, 0.1, 2.95, dw, [("Instructions", 0.9), ("You", 0.7), ("AI", 0)])
    ax.text(0.1 + dw / 2, 3.6, "Turn 1", ha="center", va="center", fontsize=FS + 1)
    # 2回目（1回目をまるごと含む）
    x2 = W - dw - 0.1
    _doc(ax, x2, 0.25, dw, 3.05)
    slot = _rows(ax, x2, 2.95, dw, [("Instructions", 0.9), ("You", 0.7), ("AI", 0.85), ("You", 0.5), ("AI", 0)])
    ax.text(x2 + dw / 2, 3.6, "Turn 2", ha="center", va="center", fontsize=FS + 1)
    ax.add_patch(Rectangle((x2 + 0.06, 1.8), dw - 0.12, 1.4, fc="none", ec=COL.gray, lw=1.0, ls=(0, (3, 2))))
    arrow(ax, (0.1 + dw + 0.05, 2.5), (x2 - 0.05, 2.5), color=COL.gray, lw=1.2, ms=14)
    ax.plot([slot[0], slot[0]], [0.7, slot[1]], color=COL.red, lw=1.0)   # 空きへの引き出し線
    ax.text(slot[0], 0.5, "Next token", ha="center", va="center", fontsize=FS, color=COL.red)
    save(f, OUT / "s05.png")


def f_s06():
    """6枚目：比べる：棒グラフ：2枚目の候補を温度 0.5・1・2 で（p^(1/T) を4候補で正規化、other は1候補として計算）〔事実16〕
    気づく：Canberra は温度 0.5 で 84%、2 で 44% に下がり、Sydney は 14% → 28% に上がる。Canberra と Sydney の棒の上に値を書き、温度の色を3色（0.5 青・1 灰・2 橙）で
    """
    temps = [(0.5, COL.blue), (1.0, COL.gray), (2.0, COL.orange)]   # 赤は Sydney の色なので使わない
    f, ax = fig(6.4, 4.7)   # 図が主役の型（s.figure_main）で左に大きく置く幅
    x = np.arange(len(WORDS))
    w = 0.27
    for k, (T, c) in enumerate(temps):
        q = PROBS ** (1 / T)
        q = q / q.sum() * 100
        ax.bar(x + (k - 1) * w, q, width=w * 0.92, color=c)
        for i in (0, 1):                                      # 値は Canberra と Sydney だけ
            ax.text(i + (k - 1) * w, q[i] + 1.5, f"{q[i]:.0f}", ha="center", va="bottom", fontsize=FS, color=c)
    # 凡例の代わりに、温度の色を名指しする1行（空いている右上）
    ax.text(2.0, 80, "Temperature", ha="left", va="center", fontsize=FS)
    for k, (T, c) in enumerate(temps):
        ax.add_patch(Rectangle((2.0 + k * 0.62, 69), 0.16, 5, fc=c, ec="none"))
        ax.text(2.2 + k * 0.62, 71.5, f"{T:g}", ha="left", va="center", fontsize=FS, color=c)
    ax.set_xticks(x, WORDS)
    ax.set_ylim(0, 95)
    ax.set_ylabel("Chance of being drawn (%)", fontsize=FS)
    ax.tick_params(labelsize=FS)
    save(f, OUT / "s06.png")


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    names = sys.argv[1:] or [k[2:] for k in list(globals()) if k.startswith("f_")]
    for nm in names:
        globals()["f_" + nm]()
