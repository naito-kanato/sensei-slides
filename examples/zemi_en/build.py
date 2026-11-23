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
OUT = HERE / "Gravitational_Waves_slides.pptx"   # 見本では作業フォルダの中に（スキルで作るときは発表フォルダ <資料名>/ に出る）

P = load_profile(HERE)
AUTHOR = author(P)   # 表紙の名前（発表は一覧の「発表者名」、無ければ空。講座は「講座名（全N回）」。仮の名前を入れない）
deck = Deck(workdir=HERE / "build", **deck_options(P))   # テンプレートを選ぶなら deck_options(P, name="テンプレート2") など

# ---------------------------------------------------------------- 1 表紙
deck.title_slide(["Observation of Gravitational Waves", "from a Binary Black Hole Merger"], author=None, subtitle="B. P. Abbott et al., PRL 116, 061102 (2016)", bold=False, roadmap=["Background（What was missing?）", "Detector（How to read a 10⁻²¹ strain?）", "Observation（What was seen?）", "Significance（Just noise?）", "Source（What emitted it?）"])

# ---------------------------------------------------------------- 2 A century of waiting
s = deck.slide("Background", summary="Predicted in 1916, gravitational waves were seen only indirectly until 2015")
s.heading("A century of waiting")
s.block("Prediction：", ["strain waves at light speed"])
s.block("Indirect proof：", ["binary pulsar loses energy"])
s.block("Direct search：", ["bars, then interferometers"])
if (FIG / "s02.png").exists(): s.figure_beside(FIG / "s02.png")   # 図：時期：年表：1916 Einstein predicts gravitational waves〔I〕／1957 Cha（図は figs/s02.png）

# ---------------------------------------------------------------- 3 How small is the signal?
s = deck.slide("Background", summary="A strain of 10⁻²¹ moves a 4-km arm by only about 4×10⁻¹⁸ m")
s.heading("How small is the signal?")
s.cur_y = s.key_message("4×10⁻¹⁸ m", sub="arm change at h = 1.0×10⁻²¹, L = 4 km", y=deck.area["top"] + 0.1).bottom + 0.45   # 図の案から scaffold.py が組んだ（言い方を確かめる）
s.block("Strain h = ΔL/L：", ["1.0×10⁻²¹ at peak"])
s.block("Question：", ["{r:catch it, prove not noise?}"])
if (FIG / "s03.png").exists(): s.figure_beside(FIG / "s03.png")   # 図：印象：大きな数字：4×10⁻¹⁸ m（arm change at h = 1.0×10⁻²¹, L = 4 km）（図は figs/s03.png）

# ---------------------------------------------------------------- 4 Michelson interferometer
s = deck.slide("Detector", summary="A Michelson interferometer turns the arm difference ΔL = hL into light")
s.heading("Michelson interferometer")
s.peq(r"\Delta L = \delta L_x - \delta L_y = hL")
s.defs(s.cur_x + 0.4, s.cur_y, [("h", "strain projected\nonto the detector"), ("ΔL", "shifts the phase of\nthe returning beams")])
if (FIG / "s04.png").exists(): s.figure_beside(FIG / "s04.png", caption="Simplified from Fig. 3; recycling mirrors omitted")   # 図：仕組み：資料の図：Fig. 3 main diagram（laser at left, beam splitter at（図は figs/s04.png）

# ---------------------------------------------------------------- 5 Cavities and recycling
s = deck.slide("Detector", summary="Arm cavities multiply the phase shift 300-fold, with 100 kW stored per arm")
s.heading("Cavities and recycling")
s.block("Arm cavity：", ["phase effect ×300 over a plain arm"])
s.block("Power recycling：", ["sends light back, 20 W → 700 W"])
s.flow(["Laser\n20 W", "Power-recycling mirror\n700 W on the beam splitter", "Arm cavities\n100 kW in each arm"], deck.area["fig_x"], deck.area["top"], 5.0, h=1.0, gap=0.6, direction="down")

# ---------------------------------------------------------------- 6 Noise remains
s = deck.slide("Detector", summary="One detector alone cannot tell a wave from its own bursts of noise")
s.heading("Noise remains")
s.cases([("Above 150 Hz", "photon shot noise"), ("Below 150 Hz", "thermal and ground noise"), ("Any band", "non-Gaussian noise bursts")])
if (FIG / "s06.png").exists(): s.figure_beside(FIG / "s06.png", caption="Abbott et al. 2016, Fig. 3(b)")   # 図：仕組み：資料の図：Fig. 3(b) strain noise vs frequency（H1 red, L1 blue（図は figs/s06.png）

# ---------------------------------------------------------------- 7 Two distant sites
s = deck.slide("Detector", summary="A real wave must reach Hanford and Livingston within 10 ms")
s.heading("Two distant sites")
if (FIG / "s07.png").exists(): s.figure_main(FIG / "s07.png", caption="Abbott et al. 2016, Fig. 3(a)")   # 図：実物：資料の図：Fig. 3(a) map（H1 at upper left in red, L1 at lower r（図が主役の型。scaffold.py が左文右図を半分までにするため選んだ）
s.ask("Local noise?", "seen at one site only")
s.ask("Real wave?", "both sites within 10 ms")

# ---------------------------------------------------------------- 8 GW150914
s = deck.slide("Observation", summary="On 14 Sep 2015 both detectors recorded the same signal 6.9 ms apart")
s.heading("GW150914")
s.block("When：", ["14 Sep 2015, 09:50:45 UTC"])
s.block("Timing：", ["L1 first, H1 6.9 ms later"])
s.block("Size：", ["peak h 1.0×10⁻²¹, combined SNR 24"])
if (FIG / "s08.png").exists(): s.figure_beside(FIG / "s08.png", caption="Abbott et al. 2016, Fig. 1 (top right)")   # 図：実物：資料の図：Fig. 1 top row（left: H1 strain in red; right: L1 str（図は figs/s08.png）

# ---------------------------------------------------------------- 9 A rising chirp
s = deck.slide("Observation", summary="In 0.2 s the signal rose from 35 to 150 Hz in about 8 cycles")
s.heading("A rising chirp")
s.develop("35 Hz", "150 Hz, loudest")
s.block("Chirp：", ["frequency and amplitude rise together"])
s.block("GR fit：", ["residuals look like noise"])
if (FIG / "s09.png").exists(): s.figure_beside(FIG / "s09.png", caption="Abbott et al. 2016, Fig. 1 (bottom left)")   # 図：実物：資料の図：Fig. 1 bottom row（time–frequency maps, H1 left and L（図は figs/s09.png）

# ---------------------------------------------------------------- 10 Is it just noise?
s = deck.slide("Significance", summary="Noise bursts in two detectors can also line up by chance within 10 ms")
s.heading("Is it just noise?")
s.ask("Environmental disturbance?", "under 6% of the strain")
s.ask("Glitch shared by both sites?", "none found")
s.compare(("Gravitational wave", ["same shape at both sites", "within 10 ms", "rising frequency"]), ("Chance coincidence", ["independent at each site", "random timing", "many shapes"]), size=20)

# ---------------------------------------------------------------- 11 Time-slide background
s = deck.slide("Significance", summary="Shifting one detector's data in time gave 608,000 years of noise-only pairs")
s.heading("Time-slide background")
if (FIG / "s11.png").exists(): s.figure_main(FIG / "s11.png")   # 図：仕組み：模式図：two time lines H1 (red) above and L1 (blue) below; L（図が主役の型。scaffold.py が左文右図を半分までにするため選んだ）
s.numbered(["Shift one site's time\nstamps ≫ 10 ms", "Count coincidences again", "Repeat ~10⁷ times"])
s.block("Conservative：", ["a real wave can enter the\nbackground"])

# ---------------------------------------------------------------- 12 Above all background
s = deck.slide("Significance", summary="No background event reached GW150914: < 1 false alarm per 203,000 years")
s.heading("Above all background")
s.block("Matched filter：", ["data vs ~250,000 GR waveforms"])
s.block("Model-free search：", ["4.6σ, 1 per 22,500 yr"])
s.ask("Can noise reach 23.6?", "{r:< 1 per 203},000 yr, > 5.1σ")
if (FIG / "s12.png").exists(): s.figure_beside(FIG / "s12.png", caption="Abbott et al. 2016, Fig. 4 (right)")   # 図：実物：資料の図：Fig. 4 right（binary coalescence search; black backgr（図は figs/s12.png）

# ---------------------------------------------------------------- 13 What can orbit at 75 Hz?
s = deck.slide("Source", summary="A chirp mass of 30 M☉ at a 75-Hz orbit leaves only black holes")
s.heading("What can orbit at 75 Hz?")
s.develop("Chirp mass ≈ 30 M☉", "total ≳ 70 M☉")
s.block("Size：", ["Schwarzschild radii sum ≳\n210 km"])
s.block("75-Hz orbit：", ["only ≈ 350 km apart"])
s.decision([("Two neutron stars?", "ruled out,\ntoo light"), ("Black hole +\nneutron star?", "ruled out, merges\nat lower frequency")], "Two black holes", x=deck.area["fig_x"] - 0.3, y=deck.area["top"], q_w=2.6, out_w=2.0)   # 図の案から scaffold.py が組んだ（言い方を確かめる）

# ---------------------------------------------------------------- 14 Masses of the pair
s = deck.slide("Source", summary="Black holes of 36 and 29 M☉ became 62 M☉, radiating 3 M☉ as waves")
s.heading("Masses of the pair")
s.block("Radiated：", ["{r:3.0 M☉c² as waves}"])
s.block("Source：", ["410 Mpc away, spin 0.67"])
if (FIG / "s14.png").exists(): s.figure_beside(FIG / "s14.png", caption="(Abbott et al. 2016)")   # 図：比べる：棒グラフ：データ2（上から Primary 36、Secondary 29、Sum 65、Final 62、Ra（図は figs/s14.png）

# ---------------------------------------------------------------- 15 What is not yet known
s = deck.slide("Source", summary="Matches GR in strong gravity, but two detectors place it only within 600 deg²")
s.heading("What is not yet known")
s.ask("Does GR hold in strong gravity?", "three tests, no deviation")
s.ask("Where is the source?", "only within ~600 deg²")
s.table(deck.area["fig_x"] - 0.7, deck.area["top"], 3.13, 0.48, ["Check", "Result"], [("Remnant mass and\nspin, early vs late", ["consistent"]), ("Inspiral phase\ncoefficients", ["no deviation from GR"]), ("Graviton mass", ["< 1.2×10⁻²² eV/c²"]), ("Sky position,\n90% region", ["about 600 deg²"])], label_w=2.27, size=16)   # 図の案から scaffold.py が組んだ（言い方を確かめる）

# ---------------------------------------------------------------- 16 Caught, and not noise
s = deck.slide(T, summary="Two distant interferometers caught a black-hole merger far beyond chance")   # まとめ：結論の一文はこの回の答え
s.heading("Summary")
s.ask("How?", "{r:amplify}, coincide, count noise")
s.ask("What?", "{r:first black-hole merger}")
s.flow(["Cavities read h ≈ 10⁻²¹", "Same chirp at two sites\n6.9 ms apart", "Noise fakes it\n< 1 per 203,000 years", "Only two black holes fit"], deck.area["fig_x"], deck.area["top"], 5.0, h=0.85, gap=0.45, direction="down")

# ---------------------------------------------------------------- 17 想定質問
s = deck.slide(T)   # summary なし：帯も●も無い枚になる
s.heading("Expected Questions")
s.at(1.0, 1.9)
s.qa_pairs([("Q1", "Could a disturbance common to both sites, not noise at each site, fake the signal?", "Sensors found no such disturbance; environment explains under 6% of the strain"), ("Q2", "Why are there two significances, 5.1σ and 4.6σ?", "Matched filter uses GR waveforms (5.1σ); the model-free search assumes less (4.6σ)")])   # 1行25字までに \n を入れて折る（回答は2〜3行）。戻る枚は原稿に

# ---------------------------------------------------------------- 18 想定質問
s = deck.slide(T)   # summary なし：帯も●も無い枚になる
s.heading("Expected Questions")
s.at(1.0, 1.9)
s.qa_pairs([("Q3", "Why is the time-slide background conservative?", "A real wave in one detector can pair with shifted noise and enter the background"), ("Q4", "How will the sky position improve?", "Advanced Virgo, KAGRA and a LIGO detector in India will extend the network")])   # 1行25字までに \n を入れて折る（回答は2〜3行）。戻る枚は原稿に

NOTES = load_notes(HERE / "notes.md")
for i, sl in enumerate(deck.slides, 1):
    if i in NOTES:
        sl.notes(NOTES[i])
OUT.parent.mkdir(parents=True, exist_ok=True)
deck.save(OUT, title=T, author=AUTHOR)
