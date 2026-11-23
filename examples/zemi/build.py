"""Observation of Gravitational Waves from a Binary Black Hole Merger（構成案 outline.md の表から scaffold.py が作った骨組み。TODO を書き換える）。

    python <skill>/scripts/make_deck.py <この作業フォルダ>   # 図→組む→描く→検査を1回で
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parents[1]   # 見本はリポジトリの scripts/ を使う
sys.path.insert(0, str(SKILL / "scripts"))
from set_notes import load_notes  # noqa: E402
from slide_profile import author, deck_options, load_profile  # noqa: E402
from zemi import Deck  # noqa: E402

T = "Observation of Gravitational Waves from a Binary Black Hole Merger"
FIG = HERE / "figs"
OUT = HERE / "Abbott2016_PRL116_061102_スライド.pptx"   # 見本では作業フォルダの中に（スキルで作るときは発表フォルダ <資料名>/ に出る）

P = load_profile(HERE)
AUTHOR = author(P)   # 表紙の名前（発表は一覧の「発表者名」、無ければ空。講座は「講座名（全N回）」。仮の名前を入れない）
deck = Deck(workdir=HERE / "build", **deck_options(P))   # テンプレートを選ぶなら deck_options(P, name="テンプレート2") など

# ---------------------------------------------------------------- 1 表紙
deck.title_slide(["Observation of Gravitational Waves", "from a Binary Black Hole Merger"], author=AUTHOR, roadmap=["背景（何がとらえにくいか）", "検出器（どうやって伸びを測るか）", "観測（何が見えたか）", "探索（偶然ではないか）", "結論（何が言えるか）"])

# ---------------------------------------------------------------- 2 小さすぎる伸び
s = deck.slide("背景", summary="重力波が 4 km の腕に起こす伸びは約 4×10⁻¹⁸ m")
s.heading("小さすぎる伸び")
s.cur_y = s.key_message("4", sub="4 km の腕の伸び。光の波長の約1兆分の4", y=deck.area["top"] + 0.1).bottom + 0.45   # 図の案から scaffold.py が組んだ（言い方を確かめる）
s.block("背景：", ["1916年に Einstein が予言", "直接の検出は100年無し"])
s.block("問い：", ["{r:どうとらえ}、雑音と見分ける？"])
if (FIG / "s02.png").exists(): s.figure_beside(FIG / "s02.png")   # 図：印象：大きな数字：4×10⁻¹⁸ m（4 km の腕の伸び。光の波長の約1兆分の4）（図は figs/s02.png）

# ---------------------------------------------------------------- 3 腕の長さの差を読む
s = deck.slide("検出器", summary="4 km の腕2本の長さの差 ΔL＝hL を、光の明暗に変える")
s.heading("腕の長さの差を読む")
s.peq(r"\Delta L = \delta L_x - \delta L_y = hL")
_y3 = s.cur_y
s.defs(deck.area.get("left", 0.6) + 0.5, _y3 + 0.15, [("h", "ひずみ（伸びの割合）"), ("L", "腕の長さ 4 km")])
s.block("読み方：", ["{r:差が干渉光の明暗に}"], y=_y3 + 1.5)
if (FIG / "s03.png").exists(): s.figure_beside(FIG / "s03.png", caption="出典：Abbott et al., PRL 116, 061102 (2016) Fig. 3（ラベルを和訳）")   # 図：仕組み：資料の図：Fig. 3 の本体（レーザー → ビームスプリッター → 直交する 4 km の腕2本 → 光検出器（図は figs/s03.png）

# ---------------------------------------------------------------- 4 周波数で替わる雑音
s = deck.slide("検出器", summary="周波数ごとに雑音の源が違い、最良の帯は 100〜300 Hz")
s.heading("周波数で替わる雑音")
s.cases([("低い周波数", "地面の揺れ"), ("中ほど", "鏡と吊り線の熱"), ("150 Hz より上", "光の粒のゆらぎ")])
if (FIG / "s04.png").exists(): s.figure_beside(FIG / "s04.png", caption="出典：Abbott et al., PRL 116, 061102 (2016) Fig. 3(b)")   # 図：仕組み：資料の図：Fig. 3(b) の雑音の大きさ（横軸＝周波数、縦軸＝雑音をひずみに直した値。H1 赤・L1 青。谷（図は figs/s04.png）

# ---------------------------------------------------------------- 5 雑音を抑える工夫
s = deck.slide("検出器", summary="光を 20 W から 100 kW にため、鏡を4段の振り子でつるす")
s.heading("雑音を抑える工夫")
_x5 = deck.area.get("left", 0.6)
_y5 = s.table(_x5, deck.area["top"] + 0.1, [2.8, 3.9, 3.9], 0.8, ["雑音", "対策", "効き"],
              [("", ["地面の揺れ", "4段の振り子と防振台", "10 Hz より上で\n10桁以上減らす"]),
               ("", ["熱", "溶融石英の鏡と吊り線", "鏡は 40 kg"]),
               ("", ["光の粒のゆらぎ", "腕の共振器と光の再利用", "位相の変化を300倍"])], size=18)
s.block("ほかに：", ["管の中は 1 μPa 未満", "較正の誤差 10% 未満"], x=_x5, y=_y5 + 0.45)
s.block("感度：", ["{r:初代 LIGO の 3〜5倍}"], x=_x5 + 6.0, y=_y5 + 0.45)

# ---------------------------------------------------------------- 6 2台にそろった揺れ
s = deck.slide("観測", summary="2台は 6.9 ms ずれて、同じ形の揺れをとらえた")
s.heading("2台にそろった揺れ")
if (FIG / "s06.png").exists(): s.figure_main(FIG / "s06.png", caption="出典：Abbott et al., PRL 116, 061102 (2016) Fig. 1（上下に並べ替え）")   # 図：実物：資料の図：Fig. 1 の1段目（左＝H1 の赤い線、右＝L1 の青い線に、ずらして反転した H1 のうすい赤を重（図が主役の型。scaffold.py が左文右図を半分までにするため選んだ）
s.block("読み方：", ["縦軸＝ひずみ（×10⁻²¹）"])
s.develop("ずらした H1", "{r:L1 と重なる}")

# ---------------------------------------------------------------- 7 上がっていく周波数
s = deck.slide("観測", summary="揺れは 0.2 秒で 35 Hz から 150 Hz へ上がり、振幅も増えた")
s.heading("上がっていく周波数")
if (FIG / "s07.png").exists(): s.figure_main(FIG / "s07.png", caption="出典：Abbott et al., PRL 116, 061102 (2016) Fig. 1")   # 図：実物：資料の図：Fig. 1 の最下段の左（H1 の時間と周波数の図。明るい帯が右上へ上がる）（図が主役の型。scaffold.py が左文右図を半分までにするため選んだ）
s.develop("35 Hz", "150 Hz\n（0.2 秒・8周期）")
s.block("解釈：", ["{r:2天体が近づきつつ公転}"])

# ---------------------------------------------------------------- 8 ブラックホールだけが残る
s = deck.slide("観測", summary="既知の天体で 350 km まで近づけるのはブラックホールだけ")
s.heading("ブラックホールだけが残る")
s.block("合計質量：", ["等質量で最小の約 70 M⊙"])
s.cases([("中性子星2つ", "軽すぎる（70 M⊙ に届かない）"), ("BH＋中性子星", "低い周波数で合体"), ("BH 2つ", "{r:接触せず回れる}")])
if (FIG / "s08.png").exists(): s.figure_beside(FIG / "s08.png", caption="（概略：2つを同じ質量とした）")   # 図：仕組み：模式図：中心どうし 350 km で回る2つの円（半径の合計 210 km 以上）を縮尺どおりに並べ、すき間が狭（図は figs/s08.png）

# ---------------------------------------------------------------- 9 偶然の一致では？
s = deck.slide("探索", summary="雑音は正規分布でなく、偶然の一致の頻度を式で出せない")
s.heading("偶然の一致では？")
if (FIG / "s09.png").exists(): s.figure_main(FIG / "s09.png", caption="（概略）")   # 図：仕組み：模式図：H1 と L1 の出力を上下2本の線で描き、突発的な雑音の山がばらばらに立つ。たまたま 15 ms の窓（図が主役の型。scaffold.py が左文右図を半分までにするため選んだ）
s.ask("環境の揺れでは？", "振幅の 6% 未満")
s.ask("2台の雑音の偶然では？", "{r:正規分布でなく式で出せない}")

# ---------------------------------------------------------------- 10 時刻をずらして数える
s = deck.slide("探索", summary="時刻をずらして作った偶然の一致は 60万8千年分")
s.heading("時刻をずらして数える")
s.block("決め手：", ["本物は 15 ms 以内にそろう", "ずらすと本物の一致は消える"])
s.block("背景：", ["{r:残るのは偶然の一致だけ}"])
s.flow(["片方の時刻を\n伝わる時間より大きくずらす", "2台の一致を数え直す", "約10⁷回くり返す", "偶然の一致の強さの分布"], x=deck.area["fig_x"] + 0.8, y=deck.area["top"], w=3.6, h=0.75, gap=0.45, size=18)   # 図の案から scaffold.py が組んだ（言い方を確かめる）

# ---------------------------------------------------------------- 11 背景を超えた1点
s = deck.slide("探索", summary="誤報率は 20万3千年に1回未満、5.1σ を超える")
s.heading("背景を超えた1点")
s.block("読み方：", ["横軸＝2台の SN 比の合計"])
s.block("上限：", ["60万8千年÷探索の3区分"])
s.ask("背景を超えるか？", "{r:23.6 はどれより強い}")
if (FIG / "s11.png").exists(): s.figure_beside(FIG / "s11.png", caption="出典：Abbott et al., PRL 116, 061102 (2016) Fig. 4")   # 図：実物：資料の図：Fig. 4 の右（横軸＝検出統計量 ρ̂c、縦軸＝事象の数。黒い線＝時刻ずらしの背景、橙の点＝実際の候（図は figs/s11.png）

# ---------------------------------------------------------------- 12 源の正体
s = deck.slide("結論", summary="合体で太陽3個分の質量が重力波のエネルギーになった")
s.heading("源の正体")
s.block("分かったこと：", ["距離 約 410 Mpc\n（約13億光年）", "一般相対論と矛盾なし"])
s.block("限り：", ["2台だけで位置は 600 deg²"])
if (FIG / "s12.png").exists(): s.figure_beside(FIG / "s12.png", caption="（Abbott et al. 2016 の値）")   # 図：比べる：棒グラフ：データ1（36・29・62・3.0 M⊙ を上から。重力波になった 3.0 だけ赤）（図は figs/s12.png）

# ---------------------------------------------------------------- 13 まとめ
s = deck.slide(T, summary="2台の一致はブラックホール合体の重力波")   # まとめ：結論の一文はこの回の答え
s.heading("まとめ")
s.recap(kind="筋", steps=["1916年に予言\n干渉で差を測る", "伸びは\n約 4×10⁻¹⁸ m", "2台の干渉計\n時刻ずらし", "BH 合体の\n重力波"], points=["どう見分けた？⇒ {r:時刻ずらし}"])   # まとめの形「筋」（話の型から。合わなければ kind を変える。新しい事実は入れない。references/story.md 3節）

# ---------------------------------------------------------------- 14 想定質問
s = deck.slide(T)   # summary なし：帯も●も無い枚になる
s.heading("想定質問")
s.at(1.0, 1.9)
s.qa_pairs([("Q1", "外の揺れや装置の不調が、2台で同時に起きただけでは？", "環境センサーの揺れは振幅の 6% 未満しか説明できず、2か所で同時にそろう外乱も見つからなかった"), ("Q2", "20万3千年に1回と 5.1σ は、どういう関係か？", "解析した16日の間に、雑音だけでこの強さが1回以上出る確率 2×10⁻⁷ 未満を、正規分布の σ に直した値が 5.1σ")])   # 1行25字までに \n を入れて折る（回答は2〜3行）。戻る枚は原稿に

# ---------------------------------------------------------------- 15 想定質問
s = deck.slide(T)   # summary なし：帯も●も無い枚になる
s.heading("想定質問")
s.at(1.0, 1.9)
s.qa_pairs([("Q3", "なぜ中性子星ではないと言えるのか？", "中性子星2つでは質量が足りず、ブラックホールと中性子星の組では合計が大きすぎ、もっと低い周波数で合体するため"), ("Q4", "源が空のどこにあるかは分からないのか？", "2台だけでは到着の時刻差しか使えず 600 deg² まで。Advanced Virgo・KAGRA・インドの LIGO が加わると位置が絞れる")])   # 1行25字までに \n を入れて折る（回答は2〜3行）。戻る枚は原稿に

NOTES = load_notes(HERE / "notes.md")
for i, sl in enumerate(deck.slides, 1):
    if i in NOTES:
        sl.notes(NOTES[i])
OUT.parent.mkdir(parents=True, exist_ok=True)
deck.save(OUT, title=T, author=AUTHOR)
