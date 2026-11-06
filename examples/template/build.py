"""テンプレートを差し替える見本：ゼミの見本（重力波の初観測、テンプレート1）の4枚を、別のテンプレート（既定は テンプレート2）で組む。

中身は examples/zemi/build.py の1・2・5・8枚目と同じ。違うのはテンプレートだけ（deck_options の name）。
本文・図の位置は構造の本文の場所（deck.area）から取る（テンプレート1 の座標のままだと、結論の囲みの構造で下の図が囲みにかかり、
左の淡い柱の構造で本文が柱からはみ出していた。check_layout の構造の検査で見つけた）。
図はゼミの見本のものを使うので、先に examples/zemi で figs.py を走らせておく。

    python build.py           # テンプレートの見本_スライド.pptx を生成（テンプレート2）
    python build.py テンプレート3  # 同梱のほかのテンプレートで（テンプレート3_テンプレートの見本_スライド.pptx）
    python build.py 研究室    # プロフィールに追加したテンプレート「研究室」で組む（<名前>_テンプレートの見本_スライド.pptx）
"""
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
SKILL = HERE.parents[1]
sys.path.insert(0, str(SKILL / "scripts"))
from slide_profile import author, deck_options, load_profile  # noqa: E402
from zemi import Deck, wrap_to  # noqa: E402

ZEMI = HERE.parent / "zemi"
FIG = ZEMI / "figs"
PAPER = ZEMI / "paper_figs"
NAME = sys.argv[1] if len(sys.argv) > 1 else "テンプレート2"
OUT = HERE / ("テンプレートの見本_スライド.pptx" if NAME == "テンプレート2" else f"{NAME}_テンプレートの見本_スライド.pptx")
SRC = "Abbott et al., PRL 116, 061102 (2016)"

P = load_profile(HERE)
AUTHOR = author(P) or "発表者名"
deck = Deck(workdir=HERE / "build", **deck_options(P, name=NAME))   # ← ここだけがゼミの見本と違う
A = deck.area                       # 構造ごとの本文の場所（x・top・fig_x、柱の構造では text_right）
COL = "text_right" in A             # 左の淡い柱の構造：本文は柱の中（1行14字前後）、図は右の白い所
R = 12.65                           # 図の右端（ページの右の余白 0.4 in の内側）
IND = 0.35                          # ラベルの下の行の字下げ（s.block の indent）


def fit(text, indent=0.0):
    """柱の構造では、柱の幅に入らない行を2行に折る（ほかの構造ではそのまま）。indent はラベルの下の行の字下げ。"""
    if not COL:
        return text
    return "\n".join(wrap_to(line, A["text_right"] - A["x"] - indent, 20) for line in text.split("\n"))


def lines(*items):
    """ラベルの下の行（柱の構造では字下げの分を引いた幅で折る）。"""
    return [fit(t, IND) for t in items]


def beside(s, path, y, caption=None):
    """本文の右に、描いた幅の図を置く。柱の構造では右の白い所の fig_x から。本文の下端・右端に入らなければ縮める
    （ゼミの見本の図は結論ヘッダーの広い本文の場所に合わせて大きく描いてあるので、本文の狭い構造では少し縮む）。"""
    with Image.open(path) as im:
        w, h = im.size[0] / im.info["dpi"][0], im.size[1] / im.info["dpi"][0]
    tr = max(b.right for kind, b in s.boxes if kind != "image" and deck.header_bottom - 0.2 < b.y < deck.content_bottom)
    x0 = A["fig_x"] if COL else tr + 0.6
    k = min(1.0, (deck.content_bottom - (0.35 if caption else 0) - y) / h, (R - x0) / w)
    w, h = w * k, h * k
    x = x0 if COL else min(tr + max(0.6, (R - w - tr) / 2), R - w)
    b = s.image(path, x=x, y=y, w=w, h=h)
    if caption:
        s.caption(b, caption)
    return b


deck.title_slide(["論文紹介：重力波の初観測"], author=AUTHOR)

s = deck.slide("背景", summary="重力波は予言から100年、直接の観測がなかった")
s.heading("重力波")
s.at(A["x"], A["top"])
s.block("予言：", lines("1916年 アインシュタイン"), gap=0.25)
s.block("正体：", lines("時空のひずみが光速で伝わる横波") + ([] if COL else ["四重極モーメントの変化で発生"]), gap=0.25)   # 柱は短い要点だけ
s.block("これまで：", lines("振幅はきわめて微小", "連星パルサーで{r:間接的}に確認"), gap=0)
beside(s, FIG / "strain.png", y=A["top"] + 0.3, caption="（概略：輪に並べた粒子の動き）")

s = deck.slide("実験手法", summary="2本の腕の長さの差を、レーザー干渉計で読み取る")
s.heading("Advanced LIGO 検出器")
s.at(A["x"], A["top"])
if COL:   # 柱は短い要点だけ（細部はノートへ）
    s.block("干渉計：", ["腕 4 km の2本", "片方が伸長、{r:他方は収縮}"], gap=0.15)
else:
    s.block("マイケルソン干渉計：", ["腕の長さ 4 km、直交する2本", "重力波で片方が伸長、{r:他方は収縮}"], gap=0.15)
e = s.peq(r"\Delta L=\delta L_x-\delta L_y=hL", dx=IND, gap=0.3)
if COL:   # 柱の中は式の右に入らないので、記号の定義は式の下に
    d = s.defs(A["x"] + IND, s.cur_y - 0.1, [("h", "ひずみ"), ("L", "腕の長さ")])
    s.at(A["x"], d.bottom + 0.3)
else:
    s.defs(e.right + 0.3, e.y + 0.02, [("h", "ひずみ"), ("L", "腕の長さ")])
s.block("2台で同時観測：", lines(*([] if COL else ["ハンフォードとリビングストン"]), "光で 10 ms 離れた2か所"), gap=0)
beside(s, FIG / "michelson.png", y=max(1.7, deck.header_bottom), caption=f"（{SRC}, Fig. 3 をもとに作図）")

s = deck.slide("結果①", summary="2台の検出器が、同じ形の信号を7 ms差で検出")
s.heading("2台で同じ信号")
s.at(A["x"], A["top"])
if COL:   # 横の矢印の展開は柱に入らないので、柱では2行で
    s.p("L1 が先に検出\n（2015年9月14日）\n⇒ 6.9 ms 後に H1\n＜ 光の到達時間 {r:10 ms}", gap=0.12)
else:
    s.develop("L1 が先に検出\n（2015年9月14日）", "6.9 ms 後に H1\n＜ 光の到達時間 {r:10 ms}", after=0.15)
s.p(fit("ひずみの最大 1.0×10^{−21}\n2台合わせた SN 比（信号と雑音の比）24"))
s.figure_below(PAPER / "fig1_strain.png", caption=f"（{SRC}, Fig. 1 上段。縦軸はひずみ ×10^{{−21}}）")   # 構造の下端に収める

for sl, note in zip(deck.slides, ["テンプレートの見本（表紙）。", "ゼミの見本の2枚目と同じ中身。", "ゼミの見本の5枚目と同じ中身。", "ゼミの見本の8枚目と同じ中身。"]):
    sl.notes(note)
deck.save(OUT, title="テンプレートの見本", author=AUTHOR)
