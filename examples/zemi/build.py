"""ゼミの見本：論文紹介「重力波の初観測」（表紙＋本文13枚）。outline.md の表を1行ずつコードにしたもの。

論文：B. P. Abbott et al., Phys. Rev. Lett. 116, 061102 (2016)（CC BY 3.0）。論文の図は paper_figs/（出典は ATTRIBUTION.md）。

    python figs.py      # 自分で描く図を figs/ に書き出す
    python build.py     # 重力波の初観測_スライド.pptx を生成（notes.md を発表者ノートに入れる）
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parents[1]
sys.path.insert(0, str(SKILL / "scripts"))
from set_notes import load_notes  # noqa: E402
from slide_profile import author, deck_options, load_profile  # noqa: E402
from zemi import Box, Deck  # noqa: E402

FIG = HERE / "figs"
PAPER = HERE / "paper_figs"
OUT = HERE / "重力波の初観測_スライド.pptx"
SRC = "Abbott et al., PRL 116, 061102 (2016)"

P = load_profile(HERE)
AUTHOR = author(P) or "発表者名"
deck = Deck(workdir=HERE / "build", **deck_options(P))
TOP = deck.header_bottom   # 図を上げてよい高さ（テンプレートの構造で変わる。上に結論の見出しがある構造では下がる）

# ---------------------------------------------------------------- 1 表紙
deck.title_slide(["論文紹介：重力波の初観測"], author=AUTHOR)

# 本文の形は outline.md の「本文の形」の列のとおり。結論は上の一文（結論ヘッダー）で言うので、本文の最後に「⇒ 赤字の結論」を
# 繰り返さず、根拠を見せる形（ラベル・手順・式の注釈・場合分け・展開・問い）で組む。図は右の白い所を埋める大きさで描いてあり、
# 本文の右 0.75 in 以上空けて置く（右端は R まで）。本文と図の間を 0.5〜1 in に（以前は図を x 7.5 に固定していて、2〜3 in 空いていた）
R = 12.65   # 図の右端（ページの右の余白 0.4 in の内側）


def beside(s, path, y, w=None, h=None, caption=None):
    """本文の右に図を置く：x は本文の右端 + 0.75 in 以上（入らなければ右端 R にそろえる）。幅を渡さなければ描いた幅のまま。"""
    from PIL import Image
    with Image.open(path) as im:
        pw, ph = im.size
        dpi = (im.info.get("dpi") or (0, 0))[0]
    if w is None:
        w = h * pw / ph if h is not None else pw / dpi
    text_right = max(b.right for kind, b in s.boxes if kind != "image" and b.y > 1.5)
    off = max(0.75, (R - w - text_right) / 2)   # 空きが大きければ、本文と図の間と図の右を半分ずつに
    b = s.image(path, x=min(text_right + off, R - w), y=y, w=w)
    if caption:
        s.caption(b, caption)
    return b


# ---------------------------------------------------------------- 2 背景
s = deck.slide("背景", summary="重力波は予言から100年、直接の観測がなかった")
s.heading("重力波")
s.at(1.0, 1.9)
s.block("予言：", ["1916年 アインシュタイン", "一般相対論からの帰結"], gap=0.3)     # 本文の形：ラベル
s.block("正体：", ["時空のひずみが光速で伝わる横波", "四重極モーメントの変化で発生", "横に伸長・縦に収縮、半周期で逆"], gap=0.3)
s.block("これまで：", ["振幅はきわめて微小（予言者も認識）", "連星パルサーで{r:間接的}に確認"], gap=0)
beside(s, FIG / "strain.png", y=2.4, w=5.85, caption="（概略：輪に並べた粒子の動き）")

# ---------------------------------------------------------------- 3 背景：連星パルサー
s = deck.slide("背景", summary="連星パルサーで間接的には確認、次は波そのものの観測")
s.heading("連星パルサー")
s.at(1.0, 1.9)
s.block("発見：", ["Hulse と Taylor が", "{u:PSR B1913+16}", "（電波を規則正しく出す中性子星）"], gap=0.3)   # 本文の形：ラベル
s.block("観測：", ["Taylor と Weisberg が", "{r:エネルギーの損失}を観測"], gap=0.3)
s.block("次の目標：", ["振幅と位相の直接の観測", "（強い重力場での一般相対論の検証）"], gap=0)
beside(s, FIG / "pulsar.png", y=1.9, caption="（概略：連星の軌道の縮小）")

# ---------------------------------------------------------------- 4 論文の表紙
deck.title_slide(["Observation of Gravitational Waves", "from a Binary Black Hole Merger"],
                 subtitle="連星ブラックホールの合体からの重力波の観測",
                 author="B. P. Abbott et al.（LIGO Scientific Collaboration and Virgo Collaboration）\n"
                        "Phys. Rev. Lett. 116, 061102 (2016)　CC BY 3.0\n"
                        "DOI: 10.1103/PhysRevLett.116.061102",
                 bold=False)

# ---------------------------------------------------------------- 5 実験手法①
s = deck.slide("実験手法", summary="2本の腕の長さの差を、レーザー干渉計で読み取る")
s.heading("Advanced LIGO 検出器")
s.at(1.0, 1.9)
s.block("マイケルソン干渉計：", ["腕の長さ 4 km、直交する2本", "重力波で片方が伸長、{r:他方は収縮}",
                               "長さの差を戻り光の位相差で検出"], gap=0.15)   # 本文の形：ラベル・式の注釈
e = s.peq(r"\Delta L=\delta L_x-\delta L_y=hL", dx=0.35, gap=0.35)
s.defs(e.right + 0.3, e.y + 0.02, [("h", "ひずみ"), ("L", "腕の長さ")])
s.block("2台で同時観測：", ["ハンフォードとリビングストン", "光で 10 ms 離れた2か所", "その場だけの雑音と区別"], gap=0)
beside(s, FIG / "michelson.png", y=1.85, caption=f"（{SRC}, Fig. 3 をもとに作図）")

# ---------------------------------------------------------------- 6 実験手法②
s = deck.slide("実験手法", summary="差は陽子より小さく、腕の中の光を 100 kW に強める")
s.heading("感度を上げる光の工夫")
s.at(1.0, 1.9)
s.block("腕の共振器：", ["2枚の鏡の間で光を往復", "位相の効果が{r:300倍}"], gap=0.3)   # 本文の形：ラベル
s.block("パワーリサイクリング鏡：", ["入力側で光を溜め、強度を増大"], gap=0.3)
s.block("シグナルリサイクリング鏡：", ["出力側で共振器の帯域を拡大"], gap=0.3)
s.block("ねらい：", ["陽子より小さな差を光で拡大", "高周波のショット雑音の抑制"], gap=0)
beside(s, FIG / "power.png", y=1.85, caption=f"（{SRC}, Sec. III の値をもとに作図）")

# ---------------------------------------------------------------- 7 実験手法③
s = deck.slide("実験手法", summary="鏡を吊るして雑音を抑え、100〜300 Hz で最も敏感に")
s.heading("雑音を抑える工夫")
s.cases([("高周波：光子のショット雑音", ["光子の数のゆらぎ・150 Hz 以上", "光を強める工夫で軽減"]),   # 本文の形：場合分け（周波数の帯ごと）
         ("低周波：地面の振動", ["{r:4段の振り子}で吊って遮断", "防振台と合わせ10桁以上（10 Hz 以上）"]),
         ("中間：鏡の熱雑音", ["40 kg の石英ガラスの鏡と吊り糸", "損失の小さい材料で低減"])], x=1.0, y=1.85)
beside(s, PAPER / "fig3b_noise.png", y=max(1.6, TOP), w=5.6, caption=f"（{SRC}, Fig. 3(b)）")

# ---------------------------------------------------------------- 8 結果①
s = deck.slide("結果①", summary="2台の検出器が、同じ形の信号を7 ms差で検出")
s.heading("2台で同じ信号")
s.at(1.0, 1.85)
s.develop("L1 が先に検出\n（2015年9月14日）", "6.9 ms 後に H1\n＜ 光の到達時間 {r:10 ms}", after=0.15)   # 本文の形：横の矢印で展開
s.p("ひずみの最大 1.0×10^{−21}\n2台合わせた SN 比（信号と雑音の比）24\n右の図：H1 を反転・ずらして L1 に重ね", gap=0)
left_end = s.cur_y
s.block("長さの変化：", ["ΔL ≈ 10^{−18} m（4 km の腕）", "陽子の大きさよりずっと小"], x=8.4, y=1.85, gap=0)
w = 9.4
b = s.image(PAPER / "fig1_strain.png", x=(13.333 - w) / 2, y=max(left_end, s.cur_y) + 0.4, w=w)
s.caption(b, f"（{SRC}, Fig. 1 上段。縦軸はひずみ ×10^{{−21}}）")

# ---------------------------------------------------------------- 9 結果①（時間–周波数）
s = deck.slide("結果①", summary="時間と周波数の図で、信号の周波数が時間とともに上昇")
s.heading("周波数が上がっていく")
s.at(1.0, 1.85)
s.block("図の読み方：", ["横軸：時刻、縦軸：周波数、色：信号の強さ", "H1・L1 の両方で同じ上がり方"], gap=0.2)        # 本文の形：ラベル・展開
s.develop("始まり 35 Hz", "{r:250 Hz} まで約 0.2 s で上昇", after=0.2)
left_end = s.cur_y
s.block("明るい筋：", ["左下から右上へ＝周波数の上昇", "振幅の最大は約 150 Hz", "上がる速さから天体の質量を推定"],
        x=8.0, y=1.85, gap=0.2)
w = 8.6
b = s.image(PAPER / "fig1_timefreq.png", x=(13.333 - w) / 2, y=max(left_end, s.cur_y) + 0.1, w=w)
s.caption(b, f"（{SRC}, Fig. 1 下段。左：H1、右：L1）")

# ---------------------------------------------------------------- 10 結果②
s = deck.slide("結果②", summary="波形の変化から、2つの天体が回りながら合体したと判断")
s.heading("波形が示す正体")
s.at(1.0, 1.9)
s.block("波形の変化：", ["約 0.2 s で8周期", "周期が短く振幅が増大", "35→150 Hz で振幅が最大"], gap=0.3)   # 本文の形：ラベル
s.block("チャープ質量：", ["約 30 {i:M}_{⊙} ⇒ 合計 {r:70 {i:M}_{⊙} 以上}", "（検出器の系・{i:M}_{⊙}：太陽の質量）"], gap=0.3)
s.block("理論との比較：", ["一般相対論の数値計算と一致", "下段：相対速度は光速の半分超"], gap=0)
beside(s, PAPER / "fig2_waveform.png", y=max(1.55, TOP), h=5.0, caption=f"（{SRC}, Fig. 2）")

# ---------------------------------------------------------------- 11 結果②（なぜブラックホールか）
s = deck.slide("結果②", summary="75 Hz で回れるほど小さい既知の天体は、ブラックホールだけ")
s.heading("なぜブラックホールか")
s.at(1.0, 1.9)
s.block("公転 75 Hz（重力波 150 Hz の半分）：", ["中心の間隔 約 350 km", "{u:シュヴァルツシルト半径}の和", "≳ 210 km（70 {i:M}_{⊙}）"], gap=0.25)   # 本文の形：ラベル・問い
s.ask("中性子星2つでは？", "コンパクトだが{r:質量が不足}", gap=0.25)
s.ask("中性子星＋ブラックホールでは？", "{r:より低い周波数}で合体\n（同じチャープ質量なら総質量が大）", gap=0)
beside(s, FIG / "scale.png", y=2.0, caption="（縮尺どおり。等質量なら1つの直径＝半径の和）")

# ---------------------------------------------------------------- 12 結果③（背景の作り方）
s = deck.slide("結果③", summary="雑音の偶然でも2台はそろいうるので、その頻度を数える")
s.heading("時刻をずらして背景を作る")
s.at(1.0, 1.9)
s.p("疑い：雑音が2台で偶然そろった？", gap=0.2)
s.p("前提：雑音だけの測定は不可", gap=0.2)
s.p("本物の信号：10 ms 以内に2台へ", gap=0.3)
s.numbered(["片方の時刻を 10 ms より\n大きくずらした組合せ",                          # 本文の形：手順
            "2台の一致の探索\n（本物の信号は不一致）",
            "16日分で約 10^{7} 通り\n＝ {r:60万8千年分}の背景"], gap=0.3)
s.p("背景は多めの見積り ⇒ 評価は控えめ", gap=0)
beside(s, FIG / "timeshift.png", y=max(1.75, TOP), caption="（概略：信号と雑音の例）")

# ---------------------------------------------------------------- 13 結果③
s = deck.slide("結果③", summary="雑音で偶然起きる頻度は、20万年に1回未満")
s.heading("偶然の雑音でない確かさ")
s.at(1.0, 1.9)
s.block("図の読み方：", ["黒線：時刻ずらしの背景", "橙の点：実際のデータ", "紫線：GW150914 を除いた背景"], gap=0.3)   # 本文の形：ラベル
s.block("GW150914（赤丸）：", ["検出統計量 23.6：背景の最大を超過", "誤報率 20万3千年に1回未満",
                               "誤報の確率 < 2×10^{−7} ＝ {r:5.1σ} 以上"], gap=0.3)
s.block("波形を仮定しない別の探索：", ["誤報率 2万2500年に1回未満・4.6σ"], gap=0)
w = 5.8
b = beside(s, PAPER / "fig4_search.png", y=max(1.55, TOP), w=w, caption=f"（{SRC}, Fig. 4 右。赤丸は発表者が追加）")
k = w / 5.4   # 赤丸の位置は、幅 5.4 in で置いたときに合わせた値を幅に比例させる
s.oval(b.x + 4.6 * k, b.y + 1.25 * k, 0.52 * k, 0.48 * k)

# ---------------------------------------------------------------- 14 考察
s = deck.slide("考察", summary="重力波を初めて直接観測し、連星ブラックホールを実証")
s.heading("わかったこと")
y = s.table(1.0, 1.9, [3.6], 0.55, ["中央値（90% の範囲）・波源の系"],
            [("合体前（大）", ["36 (+5, −4) {i:M}_{⊙}"]),
             ("合体前（小）", ["29 (+4, −4) {i:M}_{⊙}"]),
             ("合体後", ["62 (+4, −4) {i:M}_{⊙}"]),
             ("放出エネルギー", ["{r:3.0 (±0.5) {i:M}_{⊙}{i:c}^{2}}"]),
             ("距離", ["410 (+160, −180) Mpc"])], label_w=2.0)
s.caption(Box(1.0, 1.9, 4.98, y - 1.96), "（論文 Table I・本文より）")
s.at(7.2, 1.95)
s.block("意義：", ["重力波の初の直接観測", "連星ブラックホールの合体の初観測"], gap=0.3)          # 本文の形：ラベル
s.block("質量の収支：", ["36＋29−62 ≈ 3 {i:M}_{⊙} が重力波へ", "検出器の系では ×1.09 ≈ 71 {i:M}_{⊙}"], gap=0.3)
s.block("検証：", ["一般相対論の3つの検証に{r:矛盾なし}"], gap=0.3)
s.block("今後：", ["Virgo・KAGRA で音源の位置を改善"], gap=0)

NOTES = load_notes(HERE / "notes.md")
for i, sl in enumerate(deck.slides, 1):
    if i in NOTES:
        sl.notes(NOTES[i])
deck.save(OUT, title="論文紹介：重力波の初観測", author=AUTHOR)
