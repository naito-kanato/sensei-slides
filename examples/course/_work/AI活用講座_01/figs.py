"""図。python figs.py [名前 ...]（名前は f_ を除いた部分）。データの棒グラフは scaffold.py が設計メモの3b節から描いた。TODO の図を描く"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parents[3]   # 見本はリポジトリの scripts/ を使う
sys.path.insert(0, str(SKILL / "scripts"))
from figkit import COL, LW, arrow, blank, box, fig, noticks, save  # noqa: E402,F401
import figlib  # noqa: E402,F401
import figschema  # noqa: E402,F401

OUT = HERE / "figs"
OUT.mkdir(exist_ok=True)


def f_s02():
    """2枚目：素朴な見方（質問 → AIの中の答えの棚 → 正しい答えを取り出して返す）
    実物：AIの箱の中に横板の棚、棚にカード（覚えた答え）が並ぶ。1枚を取り出して外へ返す
    気づく：正しい答えが先に棚にあり、AIは運ぶだけ、という見方
    配置：左から 質問 → AI（棚）→ 答え
    ラベル：質問・答えの棚・答え（＋読み方の1行）"""
    from matplotlib.patches import Rectangle, FancyBboxPatch
    f, ax = blank(5.6, 4.0)
    box(ax, 0.1, 2.55, 1.1, 0.6, text="質問", fc=COL.light, lw=LW.thin)
    # AI の箱
    ax.add_patch(FancyBboxPatch((1.75, 0.95), 2.3, 2.75, boxstyle="round,pad=0,rounding_size=0.12",
                                fc="white", ec=COL.blue, lw=LW.shape))
    ax.text(2.9, 3.45, "AI", ha="center", va="center", fontsize=16, color=COL.blue, weight="bold")
    # 棚（3段）とカード
    for k, y in enumerate([1.25, 1.9, 2.55]):
        ax.add_patch(Rectangle((2.0, y), 1.8, 0.06, fc=COL.sand, ec="none"))
        for j in range(5):
            x = 2.08 + j * 0.34
            red = (k == 2 and j == 3)
            ax.add_patch(Rectangle((x, y + 0.06), 0.24, 0.42, fc=COL.red if red else COL.lblue,
                                   ec="none", alpha=1.0 if red else 0.55))
    ax.text(2.9, 0.72, "答えの棚", ha="center", va="center", fontsize=14, color=COL.ink)
    arrow(ax, (1.25, 2.85), (1.95, 2.85), color=COL.ink, lw=LW.thin)
    box(ax, 4.45, 2.55, 1.05, 0.6, text="答え", fc=COL.pale, lw=LW.thin)
    arrow(ax, (3.32, 3.1), (4.4, 2.85), color=COL.red, lw=LW.arrow)
    ax.text(2.8, 0.22, "読み方：棚＝覚えた答え、矢印＝取り出す向き", ha="center", va="center",
            fontsize=14, color=COL.text)
    save(f, OUT / "s02.png")


def f_s03():
    """3枚目：比べる：棒グラフ：データ1（Walters & Wilder 2023、Sci. Rep. 13, 14045）
    気づく：流暢な文献レビューを書けるなら、挙げた文献も実在すると思われがちだが、GPT-3.5 では半数以上が実在しなかった
    強調：GPT-3.5 の「実在しない」55% を赤。ほかの「実在しない」は青、「誤りあり」は灰
    （「誤りあり」の分母は実在した文献。原稿の ※ 行で断る）"""
    f, ax = fig(5.6, 4.0)
    rows = [("GPT-3.5", 55, 43, True), ("GPT-4", 18, 24, False)]
    h = 0.36
    yt = []
    for i, (name, fab, err, hl) in enumerate(rows):
        y0 = 1.0 - i * 1.15
        ax.barh(y0 + 0.21, fab, height=h, color=COL.dred if hl else COL.blue, ec="none")
        ax.barh(y0 - 0.21, err, height=h, color=COL.gray, ec="none")
        ax.text(fab + 1.5, y0 + 0.21, f"{fab}%　実在しない", va="center", fontsize=15,
                color=COL.dred if hl else COL.ink)
        ax.text(err + 1.5, y0 - 0.21, f"{err}%　誤りあり", va="center", fontsize=15, color=COL.text)
        yt.append(y0)
    ax.set_yticks(yt)
    ax.set_yticklabels([r[0] for r in rows], fontsize=16)
    ax.set_xticks([])
    ax.set_xlim(0, 112)
    ax.set_ylim(-0.75, 1.55)
    ax.spines["bottom"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    save(f, OUT / "s03.png")


def f_s04():
    """4枚目：仕組み：模式図：文脈「日本の首都は」→ 次の候補（東京・京都・大阪）と確からしさの横棒
    実物：文脈の箱から3つの候補へ矢印、候補ごとに横棒
    気づく：答えは1つに決まっているのでなく、候補ごとに確からしさがあり、東京が長い
    配置：左に文脈、右に候補と棒
    ラベル：日本の首都は・確からしさ（＋読み方の1行）。棒の長さは講師の例（数値なし）"""
    f, ax = blank(5.6, 4.0)
    box(ax, 0.1, 1.75, 1.75, 0.7, text="日本の首都は", fc=COL.light, lw=LW.thin, fs=15)
    cands = [("東京", 3.0, 2.3, COL.blue), ("京都", 2.1, 0.7, COL.gray), ("大阪", 1.2, 0.45, COL.gray)]
    for name, y, L, c in cands:
        arrow(ax, (1.9, 2.1), (2.45, y), color=COL.ink, lw=LW.thin)
        ax.text(2.55, y, name, ha="left", va="center", fontsize=16, color=COL.ink)
        ax.barh(y, L, left=3.25, height=0.42, color=c, ec="none")
    ax.text(3.25, 3.6, "確からしさ", ha="left", va="center", fontsize=15, color=COL.text)
    ax.text(2.8, 0.35, "読み方：棒の長さ＝確からしさ（例）", ha="center", va="center",
            fontsize=14, color=COL.text)
    save(f, OUT / "s04.png")


def f_s06():
    """6枚目：仕組み：模式図：文章の先を隠す → 次の語を当てる → 数を少し直す、を回る輪
    実物：3つの段を矢印の輪でつなぎ、輪の中にモデルのつまみ（パラメータ）を3つ
    気づく：人が正解を付けず、文章そのものを使って何度も回す練習であること
    配置：輪（上・右下・左下）
    ラベル：文章の先を隠す・次の語を当てる・数を少し直す（＋読み方の1行）"""
    from matplotlib.patches import FancyArrowPatch, Circle
    f, ax = blank(5.6, 4.0)
    bw, bh = 1.95, 0.55
    nodes = {"top": (2.8, 3.35), "right": (4.05, 1.45), "left": (1.55, 1.45)}
    texts = {"top": "文章の先を隠す", "right": "次の語を当てる", "left": "数を少し直す"}
    for k, (cx, cy) in nodes.items():
        box(ax, cx - bw / 2, cy - bh / 2, bw, bh, text=texts[k], fc=COL.pale, lw=LW.thin, fs=15)

    def arc(p0, p1, rad):
        ax.add_patch(FancyArrowPatch(p0, p1, connectionstyle=f"arc3,rad={rad}", arrowstyle="-|>",
                                     mutation_scale=16, color=COL.blue, lw=LW.arrow))
    arc((3.8, 3.3), (4.45, 1.78), -0.35)
    arc((3.3, 1.12), (2.3, 1.12), -0.45)
    arc((1.15, 1.78), (1.8, 3.3), -0.35)
    # つまみ（パラメータ）
    import math
    for j, (x, ang) in enumerate([(2.35, 60), (2.8, 120), (3.25, 20)]):
        ax.add_patch(Circle((x, 2.3), 0.17, fc=COL.lblue, ec="none"))
        a = math.radians(ang)
        ax.plot([x, x + 0.15 * math.cos(a)], [2.3, 2.3 + 0.15 * math.sin(a)], color="white", lw=2)
    ax.text(2.8, 0.3, "読み方：輪1周＝1回の練習、つまみ＝パラメータ", ha="center", va="center",
            fontsize=14, color=COL.text)
    save(f, OUT / "s06.png")


def f_s09():
    """比べる：棒グラフ：データ2（データ2：検索付きの AI に記事の抜粋を見せ、元の記事を答えさせたときの誤答の割合。scaffold.py が3b節の表から描いた。強調する棒は highlight：誤答の多い Grok 3（94%）。8種全体の「60%超」は原稿で言う）"""
    f, ax = fig(5.6, 0.7 + 0.55 * 2)
    figlib.bars(ax, ["Perplexity", "Grok 3"], [37, 94], highlight=1, unit="%", xmax=110)
    save(f, OUT / "s09.png")


def f_s10():
    """10枚目：仕組み：模式図：実線の枠の中＝計算に入るもの → 次のトークンの確からしさ。点線の外＝計算に入らないもの〔事実5・8・9〕
    実物：実線の枠（入るもの3つ）から出力の箱へ矢印。下の点線の枠（実在・事実）からの矢印は途中で途切れる（×）
    気づく：実在するか・事実と合うかは、確からしさの計算に入っていない
    配置：左に枠2つ（上＝実線、下＝点線）、右に出力
    ラベル：入るもの（1つの囲み）・次のトークンの確からしさ・入らないもの（1つの囲み）（＋読み方の1行）
    （figschema.black_box は「中は見えない」型で案と合わないので、figkit の箱で描いた）"""
    from matplotlib.patches import FancyBboxPatch
    f, ax = blank(6.6, 4.3)
    ax.add_patch(FancyBboxPatch((0.2, 1.75), 3.3, 2.3, boxstyle="round,pad=0,rounding_size=0.12",
                                fc="white", ec=COL.blue, lw=LW.shape))
    ax.text(1.85, 2.9, "いまの文脈\n学んだ言葉のつながり\n人の評価の好み", ha="center", va="center",
            fontsize=16, color=COL.ink, linespacing=1.7)
    arrow(ax, (3.55, 2.9), (4.35, 2.9), color=COL.blue, lw=LW.arrow)
    box(ax, 4.4, 2.4, 2.05, 1.0, text="次のトークンの\n確からしさ", fc=COL.pale, lw=LW.thin, fs=16)
    ax.add_patch(FancyBboxPatch((0.2, 0.7), 3.3, 0.7, boxstyle="round,pad=0,rounding_size=0.12",
                                fc="white", ec=COL.gray, lw=LW.shape, ls="--"))
    ax.text(1.85, 1.05, "実在するか・事実と合うか", ha="center", va="center", fontsize=15, color=COL.text)
    arrow(ax, (3.55, 1.05), (4.05, 1.6), color=COL.gray, lw=LW.thin, ls="--")
    ax.text(4.4, 1.95, "×", ha="center", va="center", fontsize=22, color=COL.red, weight="bold")
    ax.text(3.3, 0.25, "読み方：実線の中＝計算に使う、点線＝使わない", ha="center", va="center",
            fontsize=14, color=COL.text)
    save(f, OUT / "s10.png")


def f_s11():
    """11枚目：傾向：概略グラフ：横軸＝同じ形が出る多さ（まれ → よく出る）、縦軸＝誤りやすさ〔事実9・12〕
    気づく：まれな事実（左上）は誤りが残り、型のある所（右下）は誤りが消えやすい
    強調：左上のまれな事実の点を赤、右下の点は青。線は右下がり（数値なし、形は指数の減り方で描いた概略）"""
    import numpy as np
    f, ax = fig(6.6, 4.3)
    x = np.linspace(0.3, 9.7, 200)
    g = lambda t: 0.9 + 8.0 * np.exp(-0.33 * (t - 0.3))
    ax.plot(x, g(x), color=COL.blue, lw=LW.curve)
    ax.plot([1.2], [g(1.2)], "o", ms=11, color=COL.red, mec="none")
    ax.plot([8.6], [g(8.6)], "o", ms=11, color=COL.blue, mec="none")
    ax.text(1.65, g(1.2) + 0.35, "まれな事実\n（ペットの誕生日、文献、判例）", ha="left", va="bottom",
            fontsize=14, color=COL.ink)
    ax.text(8.6, g(8.6) + 0.9, "型のある所\n（つづり、括弧）", ha="center", va="bottom",
            fontsize=14, color=COL.ink)
    ax.text(9.7, 5.6, "読み方：右ほど型から\n当てやすい", ha="right", va="center", fontsize=14, color=COL.text)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 11.5)
    ax.set_xlabel("同じ形が出る多さ（まれ → よく出る）")
    ax.set_ylabel("誤りやすさ")
    noticks(ax)
    save(f, OUT / "s11.png")


if __name__ == "__main__":
    names = sys.argv[1:] or [n[2:] for n in list(globals()) if n.startswith("f_")]
    for n in names:
        globals()["f_" + n]()
