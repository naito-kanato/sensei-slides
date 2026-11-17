"""ゼミの見本の英語版：論文紹介 "Observation of Gravitational Waves from a Binary Black Hole Merger"（表紙＋本文16枚）。
英語の依頼でスキルに一から作らせたもの（設定は examples/zemi と同じ。依頼文は README）。outline.md の表から scaffold.py が作り、担当が書き上げた。

論文：B. P. Abbott et al., Phys. Rev. Lett. 116, 061102 (2016)（CC BY 3.0）。論文の図は paper_figs/（出典は ATTRIBUTION.md）。

    python figs.py      # 自分で描く図を figs/ に書き出す
    python build.py     # Gravitational_Waves_slides.pptx を生成（notes.md を発表者ノートに入れる）
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parents[1]
sys.path.insert(0, str(SKILL / "scripts"))
from set_notes import load_notes  # noqa: E402
from slide_profile import author, deck_options, load_profile  # noqa: E402
from zemi import Deck  # noqa: E402

T = "Observation of Gravitational Waves from a Binary Black Hole Merger"
FIG = HERE / "figs"
PAPER = HERE / "paper_figs"
OUT = HERE / "Gravitational_Waves_slides.pptx"

P = load_profile(HERE)
AUTHOR = author(P)
AUTHOR = "" if AUTHOR == "なし" else AUTHOR   # 表紙の名前（発表は一覧の「発表者名」、無ければ空。講座は「講座名（全N回）」。仮の名前を入れない）
deck = Deck(workdir=HERE / "build", **deck_options(P))   # テンプレートを選ぶなら deck_options(P, name="テンプレート2") など

# ---------------------------------------------------------------- 1 表紙
deck.title_slide(["Paper Review: The First Observation of Gravitational Waves"], author=AUTHOR)

# ---------------------------------------------------------------- 2 Gravitational waves
s = deck.slide("Background", summary="Einstein's 1916 waves stretch and squeeze space itself at light speed")
s.heading("Gravitational waves")
# 上に文・下に図：3つのラベルを横に並べ、輪の図（横長）を下に。以前は左に文・右に図で、その型が本文の半分を超えていた
y0 = deck.area["top"] + 0.15
# 文の塊は2つ（予言と正体を1つに。1枚の文の塊は2つまで：style-guide 8節）
bs = [s.block("Einstein's prediction, 1916:", ["from GR field equations", "transverse strain wave", "source: changing quadrupole"],
              x=1.6, y=y0, gap=0),
      s.block("Size:", ["amplitude {r:remarkably small}", "Einstein himself knew it", "reality debated until 1957"], x=7.6, y=y0, gap=0)]
s.cur_y = max(b.bottom for b in bs)
s.figure_below(FIG / "s02.png", caption="(schematic)")

# ---------------------------------------------------------------- 3 Indirect evidence
s = deck.slide("Background", summary="Binary pulsar energy loss showed GWs only indirectly")
s.heading("Indirect evidence")
# 文の塊は2つ：発見と観測を1つに、目標と問いを1つに（問いは目標の帰結の赤字）
s.block("Binary pulsar PSR B1913+16:", ["found by Hulse, Taylor (1975)", "energy loss: Taylor, Weisberg (1982)"],
        then="GWs exist, but {r:only indirectly}", gap=0.45)
s.block("Next goal:", ["direct amplitude, phase ⇒ GR tests"], then="how to catch a stretch this tiny}\n{r:   and tell it from noise?")   # 2行の赤字（{r:} を行ごとに）
s.figure_beside(FIG / "s03.png", caption="(schematic)")

# ---------------------------------------------------------------- 4 the paper
deck.title_slide(["Observation of Gravitational Waves", "from a Binary Black Hole Merger"],
                 subtitle="The discovery paper of GW150914",
                 author="B. P. Abbott et al., LIGO and Virgo Collaborations\n"
                        "Phys. Rev. Lett. 116, 061102 (2016), CC BY 3.0\n"
                        "DOI: 10.1103/PhysRevLett.116.061102",
                 bold=False)

# ---------------------------------------------------------------- 5 Advanced LIGO
s = deck.slide("Detector", summary="4 km arms convert ΔL = hL into a light phase shift")
s.heading("Advanced LIGO")
s.block("Michelson interferometer:", ["two perpendicular 4 km arms", "one stretches, {r:the other shrinks}",
                                     "ΔL ⇒ phase shift of returning light"])
e = s.peq(r"\Delta L(t) = \delta L_x - \delta L_y = h(t)L")
s.defs(e.x + 0.4, e.bottom + 0.1, [("h", "strain = ΔL/L, no unit"), ("L", "arm length, 4 km")], sep=": ")
# 文の塊は2つ（干渉計と式の定義）。試験質量（鏡は目印だけ）は図の「Free-hanging test mass」のラベルが担い、言うことは原稿へ
s.figure_beside(FIG / "s05.png", caption="After Fig. 3 (schematic)")

# ---------------------------------------------------------------- 6 How small the signal is
s = deck.slide("Detector", summary="h ≈ 10⁻²¹ changes the arm-length difference by only ~4×10⁻¹⁸ m")
s.heading("How small the signal is")
# 上に文・下に図：対数の物差し（横長）を下に。左に式の展開（陽子との比まで）と陽子の幅、右の列に以前の検出器
y0 = deck.area["top"] + 0.15
s.develop("peak h ≈ 10⁻²¹\nL = 4 km", "ΔL = hL ≈ 4×10⁻¹⁸ m\n≈ {r:1/400 of a proton}\n(proton ≈ 1.7×10⁻¹⁵ m)", x=0.9, y=y0, after=0)
left_end = s.cur_y   # 陽子の幅は展開の右に（「Scale」の塊をやめて文の塊を2つに）
s.block("Earlier:", ["resonant bars (1960s–)", "interferometers 2002–2011"], then="upper limits only", x=7.6, y=y0, gap=0)
s.cur_y = max(left_end, s.cur_y)
s.figure_below(FIG / "s06.png", caption="(schematic, log scale)")

# ---------------------------------------------------------------- 7 Boosting the light
s = deck.slide("Detector", summary="Cavities build 20 W of laser light up to 100 kW in each arm")
s.heading("Boosting the light")
# 図が主役：光の通り道の図そのものを読ませる（20 W → 700 W → 100 kW を線の太さで）。文は右の列に
s.figure_main(FIG / "s07.png", caption="After Fig. 3, PRL 116, 061102 (2016) (schematic)")
# 文の塊は2つ：ねらい（ショット雑音）は光を戻す工夫の帰結に
s.block("Arm cavities:", ["light bounces many times", "between two test-mass mirrors"], then="phase effect {r:×300}", gap=0.45)
s.block("Power recycling:", ["light sent back in at the input", "(partially transmissive mirror)", "20 W → 700 W → {r:100 kW per arm}"],
        then="less relative shot noise", gap=0)

# ---------------------------------------------------------------- 8 Where the noise is lowest
s = deck.slide("Detector", summary="Most sensitive at 100–300 Hz, 3–5× better than initial LIGO")
s.heading("Where the noise is lowest")
s.block("Reading:", ["strain noise: lower = quieter"])
s.cases([("Above 150 Hz", "photon shot noise (slide 7)"),
         ("Low frequencies", "ground motion ⇒ quadruple pendulum\n+ platform: {r:>10 orders} above 10 Hz"),
         ("Intermediate", "thermal noise ⇒ 40 kg fused-silica\nmirrors on silica fibers")])
s.figure_beside(PAPER / "fig3b_noise.png", caption="Fig. 3(b), PRL 116, 061102 (2016); band = signal 35–250 Hz, added")

# ---------------------------------------------------------------- 9 Same signal at two sites
s = deck.slide("Result 1", summary="H1 and L1 saw the same waveform 6.9 ms apart")
s.heading("Same signal at two sites")
# 上の1行に「展開（左）→ 大きさ（右）」の2つの塊だけ、下に論文の図を横いっぱいに（以前は縮んで小さかった）。
# 図は Fig. 1 の上段に、同じ図の縦軸の名前と最下段の時間軸を付けたもの。2か所で見る意味は原稿へ
y0 = deck.area["top"] + 0.1
d = s.develop("L1 first\n(Sept. 14, 2015)", "H1 {r:6.9 ms later}\n< 10 ms light travel", x=1.0, y=y0, after=0)
k = s.block("Size:", ["peak strain 1.0×10⁻²¹", "combined SNR 24 (signal-to-noise)"], x=d.right + 0.6, y=y0, gap=0)
s.cur_y = max(d.bottom, k.bottom)
s.figure_below(PAPER / "fig1_strain_axes.png", gap=0.25,
               caption="Fig. 1 top row with its shared axes, PRL 116, 061102 (2016); right: H1 shifted, inverted")

# ---------------------------------------------------------------- 10 A rising chirp
s = deck.slide("Result 1", summary="In 0.2 s the frequency rose from 35 to 150 Hz")
s.heading("A rising chirp")
# 図が主役：時間と周波数の図そのものを読ませる。図の読み方を右の列に
b = s.figure_main(PAPER / "fig1_timefreq_H1.png", w=6.0, caption="Fig. 1 bottom row (H1), PRL 116, 061102 (2016); label added")
s.note(b.x + 0.16 * b.w, b.y + 0.05 * b.h, "color: signal power")   # 図の読み方は図の中に（軸は図の軸の名前が言う）
s.block("Track:", ["{r:35 → 150 Hz in 0.2 s}", "~8 cycles, peak at 150 Hz", "whole signal: 35 → 250 Hz",
                   "(same track in L1)"], gap=0.45)
s.block("Meaning:", ["most likely: two masses spiraling in", "energy lost to GWs", "GW frequency = 2 × orbital"],
        then="shrinking orbit ⇒ faster", gap=0)

# ---------------------------------------------------------------- 11 Chirp mass
s = deck.slide("Result 2", summary="Chirp rate implies a total mass of at least 70 M_{⊙}")
s.heading("Chirp mass")
# 文の塊は2つ。一般式（分数の入った長い式）は原稿へ、本文は1行の関係「ℳ ≈ 30 M⊙ ⇒ total ≳ 70 M⊙」に絞る。
# ℳ は本文の文字だけで書き（式の画像の ℳ と字形が食い違っていた）、M⊙ は ⊙ を下付きに（大きな ⊙ が「MO」に見えた）
s.block("Chirp mass ℳ:", ["one combination of m_{1}, m_{2}", "set by f and ḟ (the track's slope)",
                          "alone controls the chirp at low f"], gap=0.45)
s.block("From Fig. 1:", ["ℳ ≈ 30 M_{⊙}", "detector frame: masses as observed", "total smallest at m_{1} = m_{2}"],
        then="total ≳ 70 M_{⊙}", gap=0)
s.figure_beside(PAPER / "fig1_timefreq_H1_marks.png", caption="Fig. 1 bottom row (H1), PRL 116, 061102 (2016); f, ḟ marks added")

# ---------------------------------------------------------------- 12 Why black holes
s = deck.slide("Result 2", summary="Of known objects, only black holes are compact enough to orbit at 75 Hz")
s.heading("Why black holes")
# 文の塊は2つ：軌道と地平面を「75 Hz の軌道」に、2つの問いを「ほかの候補」に
s.block("Orbit at 75 Hz:", ["half of the 150 Hz GW peak", "equal masses ≃350 km apart", "horizons: sum ≳210 km",
                            "(≈3 km per M_{⊙})"], gap=0.45)
s.block("Other candidates:", ["two neutron stars:", "{r:not enough mass}", "neutron star + black hole:", "merges at {r:lower frequency}"], gap=0)
s.figure_beside(FIG / "s12.png", caption="(schematic, to scale)")

# ---------------------------------------------------------------- 13 Ruling out chance noise
s = deck.slide("Result 3", summary="Chance? Time shifts built 608,000 years of noise-only background")
s.heading("Ruling out chance noise")
# 文の塊は2つ（問題と手順）。背景が多めになる偏り（控えめな評価）は原稿へ
s.block("Problem:", ["noise non-Gaussian, nonstationary", "⇒ count it from the data", "no detector shielded from GWs"], gap=0.45)
s.numbered(["Shift one detector by ≫10 ms", "Search coincidences again", "Count each as 16 noise-only days\n~10⁷ shifts ⇒ {r:608,000 years}"], gap=0)
s.figure_beside(FIG / "s13.png", y=1.6, caption="(schematic)")

# ---------------------------------------------------------------- 14 False alarm rate
s = deck.slide("Result 3", summary="Noise would mimic it less than once per 203,000 years")
s.heading("False alarm rate")
s.figure_main(PAPER / "fig4_search.png", caption="Fig. 4 right, Abbott et al., PRL 116, 061102 (2016); red circle added")
# 文の塊は2つ（結果）。図の読み方（軸・黒線・橙・上の σ の帯）は図の軸の名前と凡例が言い、原稿で補う
s.block("GW150914:", ["ρ̂_{c} = 23.6, past all noise", "{r:< 1 per 203,000 years}", "(upper bound: none louder)",
                      "p < 2×10⁻⁷ = 5.1σ"], gap=0.45)
s.block("Generic search:", ["no waveform model", "< 1 per 22,500 years: 4.6σ"], gap=0)

# ---------------------------------------------------------------- 15 The source
s = deck.slide("Discussion", summary="A 36 and 29 M_{⊙} pair merged, radiating 3.0 M_{⊙}c²")
s.heading("The source")
b = s.cards([("Masses", "36 and 29\nmerged into one\n(source frame)", "62 M_{⊙}"),            # 並列カード（3つ目は大きな値）
             ("Energy", "radiated as\ngravitational waves\n(± 0.5)", "3.0 M_{⊙}c²"),
             ("Distance", "about 1.3 billion\nlight-years\n(z = 0.09)", "410 Mpc")], y=2.0, h=3.35, size=22)
cap = s.caption(b, "Table I, Abbott et al., PRL 116, 061102 (2016); medians, GW150914")
# 一般相対論の検証の塊は原稿へ（カードの値3つで文の塊が3つ。4つ目を置かない）

# ---------------------------------------------------------------- 16 Anticipated questions
s = deck.slide(T)   # summary なし：帯も●も無い枚になる
s.heading("Expected Questions")
s.at(1.0, 1.9)
s.qa_pairs([("Q1", "Why is the H1 trace inverted\nbefore it is overlaid on L1?", "Two detectors oriented differently\nSame wave appears with opposite sign",
             (PAPER / "fig1_strain_L1_axes.png", "Slide 9: Fig. 1 top right with its axes, PRL 116, 061102 (2016)")),
            ("Q2", "Could an earthquake or a local\ndisturbance have caused it?", "Sensors saw nothing like GW150914\nFluctuations: at most 6% of strain\nNo correlated two-site disturbance")])

# ---------------------------------------------------------------- 17 Anticipated questions
s = deck.slide(T)   # summary なし：帯も●も無い枚になる
s.heading("Expected Questions")
s.at(1.0, 1.9)
s.qa_pairs([("Q3", "What does 5.1σ mean here?", "False alarm p < 2×10⁻⁷\n= Gaussian tail beyond 5.1σ\nNoise not Gaussian: counted",
             (PAPER / "fig4_search.png", "Slide 14: Fig. 4 right, PRL 116, 061102 (2016); red circle added")),
            ("Q4", "Where in the sky\nwas the source?", "Only 2 detectors: time delay\nabout 600 deg² (90%)\nVirgo, KAGRA to narrow it")])

NOTES = load_notes(HERE / "notes.md")
for i, sl in enumerate(deck.slides, 1):
    if i in NOTES:
        sl.notes(NOTES[i])
OUT.parent.mkdir(parents=True, exist_ok=True)
deck.save(OUT, title=T, author=AUTHOR)
