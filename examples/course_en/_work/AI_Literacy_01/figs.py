"""図。python figs.py [名前 ...]（名前は f_ を除いた部分）。データの棒グラフは scaffold.py が設計メモの3b節から描いた。TODO の図を描く"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parents[3]   # 見本はリポジトリの scripts/ を使う
sys.path.insert(0, str(SKILL / "scripts"))
from figkit import COL, LW, arrow, blank, box, fig, noticks, save  # noqa: E402,F401
import figlib  # noqa: E402,F401
import figschema  # noqa: E402,F401
from matplotlib.patches import FancyBboxPatch  # noqa: E402

C = COL if isinstance(COL, dict) else vars(COL)
INK = "#333333"


def _box(ax, x, y, w, h, text, fc, ec, ls="-", fs=15, color=INK):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.08",
                                fc=fc, ec=ec, lw=1.2, ls=ls))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=color)


def _arr(ax, p0, p1, color=None):
    ax.annotate("", xy=p1, xytext=p0,
                arrowprops=dict(arrowstyle="-|>", color=color or C["blue"], lw=1.2,
                                shrinkA=0, shrinkB=0, mutation_scale=14))

OUT = HERE / "figs"
OUT.mkdir(exist_ok=True)


def f_s04():
    """図の案：仕組み：模式図：the sentence "Chatbots predict text." cut into four boxes；読み方：1 box = 1 token
    実物：1文の文字列と、それを切った4つの箱（トークン）
    気づく：1語がそのまま1トークンとは限らず、句読点も1つのトークンになる
    配置：上に元の文、下に切ったあとの箱（前後）
    ラベル：Chatbots / predict / text"""
    f, ax = blank(5.6, 4.0)
    ax.text(2.8, 3.55, "Chatbots predict text.", ha="center", va="center", fontsize=17, color=INK)
    _arr(ax, (2.8, 3.2), (2.8, 2.7), color=C["gray"])
    toks = [("Chatbots", 1.55), ("predict", 1.35), ("text", 0.9), (".", 0.45)]
    gap = 0.15
    x = (5.6 - (sum(w for _, w in toks) + gap * (len(toks) - 1))) / 2
    for t, w in toks:
        _box(ax, x, 1.6, w, 0.85, t, fc=C["pale"], ec=C["blue"])
        x += w + gap
    ax.text(2.8, 0.6, "Reading: 1 box = 1 token\n(splits shown are an illustration)",
            ha="center", va="center", fontsize=14, color=INK)
    save(f, OUT / "s04.png")


def f_s05():
    """図の案：仕組み：模式図：after "The capital of France is", candidate next tokens Paris, a, the, located（数字なしの棒）；読み方：longer bar = rated more likely to come next
    実物：入力の文と、次のトークンの候補ごとの棒（長さ＝付いた確率の大きさ。値は例で数字は書かない）
    気づく：候補は1つではなく、全部に確率が付き、Paris が飛び抜けて長い
    配置：上に入力の文、下に候補の横棒（長い順）
    ラベル：Paris / a / the / located"""
    f, ax = blank(5.6, 4.0)
    ax.text(2.8, 3.6, '"The capital of France is ..."', ha="center", va="center", fontsize=16, color=INK)
    rows = [("Paris", 3.9, C["blue"]), ("a", 1.3, C["lblue"]), ("the", 0.9, C["lblue"]), ("located", 0.45, C["lblue"])]
    x0, h = 1.35, 0.38
    for i, (t, L, c) in enumerate(rows):
        y = 2.85 - i * 0.6
        ax.add_patch(FancyBboxPatch((x0, y - h / 2), L, h, boxstyle="square,pad=0", fc=c, ec="none"))
        ax.text(x0 - 0.15, y, t, ha="right", va="center", fontsize=15, color=INK)
    ax.text(2.8, 0.35, "Reading: longer bar = rated more\nlikely to come next",
            ha="center", va="center", fontsize=14, color=INK)
    save(f, OUT / "s05.png")


def f_s07():
    """比べる：棒グラフ：データ1（データ1：Share of ChatGPT-generated citations tha。scaffold.py が3b節の表から描いた。強調する棒は highlight）"""
    f, ax = fig(5.6, 0.7 + 0.55 * 2)
    figlib.bars(ax, ["GPT-3.5", "GPT-4"], [55, 18], highlight=0, unit="%")
    save(f, OUT / "s07.png")


def f_s10():
    """図の案：仕組み：模式図：the pick-and-repeat loop (text so far → probabilities → pick → append) with a dashed, crossed-out box "Check: is it true?"；読み方：dashed box = a step the loop does not have
    実物：4つの段がぐるりと回る輪と、輪から離れた破線の箱（確かめる段）
    気づく：輪のどの矢印も「Check: is it true?」を通らない
    配置：上に回る輪、下に離れた破線の箱と赤の ×
    ラベル：Text so far / Probabilities / Pick（Add は短い語）"""
    f, ax = blank(5.6, 4.0)
    bw, bh = 2.1, 0.6
    xl, xr, yt, yb = 0.35, 3.15, 2.95, 1.75
    for (x, y, t) in [(xl, yt, "Text so far"), (xr, yt, "Probabilities"), (xr, yb, "Pick"), (xl, yb, "Add")]:
        _box(ax, x, y, bw, bh, t, fc=C["pale"], ec=C["blue"])
    _arr(ax, (xl + bw, yt + bh / 2), (xr, yt + bh / 2))
    _arr(ax, (xr + bw / 2, yt), (xr + bw / 2, yb + bh))
    _arr(ax, (xr, yb + bh / 2), (xl + bw, yb + bh / 2))
    _arr(ax, (xl + bw / 2, yb + bh), (xl + bw / 2, yt))
    _box(ax, 1.75, 0.8, 2.6, 0.55, "Check: is it true?", fc="white", ec=C["gray"], ls="--", color=C["gray"])
    ax.text(1.4, 1.075, "×", ha="center", va="center", fontsize=26, color=C["red"])
    ax.text(2.8, 0.3, "Reading: dashed box = a step\nthe loop does not have",
            ha="center", va="center", fontsize=14, color=INK)
    save(f, OUT / "s10.png")


def f_s12():
    """内訳：帯グラフ：データ2（データ2：What 115 ChatGPT-3.5 references in medic。scaffold.py が3b節の表から描いた。強調する棒は highlight）"""
    f, ax = fig(5.6, 0.7 + 0.55 * 3)
    figlib.bars(ax, ["Fabricated", "Real but inaccurate", "Real and accurate"], [47, 46, 7], highlight=2, unit="%")
    save(f, OUT / "s12.png")


if __name__ == "__main__":
    names = sys.argv[1:] or [n[2:] for n in list(globals()) if n.startswith("f_")]
    for n in names:
        globals()["f_" + n]()
