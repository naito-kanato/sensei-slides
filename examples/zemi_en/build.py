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
OUT = HERE / "Abbott2016_PRL116_061102_slides.pptx"   # 見本では作業フォルダの中に（スキルで作るときは発表フォルダ <資料名>/ に出る）

P = load_profile(HERE)
AUTHOR = author(P)   # 表紙の名前（発表は一覧の「発表者名」、無ければ空。講座は「講座名（全N回）」。仮の名前を入れない）
deck = Deck(workdir=HERE / "build", **deck_options(P))   # テンプレートを選ぶなら deck_options(P, name="テンプレート2") など

# ---------------------------------------------------------------- 1 表紙
deck.title_slide(["Paper review: Observation of Gravitational Waves from a Binary Black Hole Merger"], author=AUTHOR)

# ---------------------------------------------------------------- 2 A century-old prediction
s = deck.slide("Background", summary="Before 2015, the only evidence was one pulsar's energy loss")
s.heading("A century-old prediction")
s.block("Prediction (1916)：", ["transverse waves of spatial strain\n(space itself stretches and squeezes)\nmoving at the speed of light"])
s.block("Indirect evidence：", ["binary pulsar PSR B1913+16,\norbital {r:energy loss} (the orbit\nshrinks as GWs carry energy away)"])
s.block("Your guess：", ["how far would a 4 km ruler stretch?"])
if (FIG / "s02.png").exists(): s.figure_beside(FIG / "s02.png", caption="(schematic, stretch exaggerated)")

# ---------------------------------------------------------------- 3 表紙
deck.title_slide(["Observation of Gravitational Waves", "from a Binary Black Hole Merger"], subtitle="B. P. Abbott et al. (LIGO Scientific Collaboration and Virgo Collaboration)\nPhys. Rev. Lett. 116, 061102 (2016)\nCC BY 3.0, DOI 10.1103/PhysRevLett.116.061102", size=36)

# ---------------------------------------------------------------- 4 Interferometer as a ruler
s = deck.slide("Detector", summary="Two perpendicular 4 km arms turn a stretch of space into a phase shift")
s.heading("Interferometer as a ruler")
b = s.peq(r"\Delta L(t) = \delta L_x - \delta L_y = h(t)\,L")
d = s.defs(b.x, b.bottom + 0.2, [("h", "strain, the fractional stretch\n(no unit)"), ("L", "arm length, {r:4 km}")])
s.cur_y = d.bottom + 0.45
s.block("Readout：", ["ΔL shifts the phase of the\nreturning light → photodetector"])
if (FIG / "s04.png").exists(): s.figure_beside(FIG / "s04.png", caption="(schematic after Fig. 3, not to scale)")

# ---------------------------------------------------------------- 5 The size of the target
s = deck.slide("Detector", summary="The target stretch, 4×10⁻¹⁸ m, is about 1/400 of a proton")
s.heading("The size of the target")
s.cur_y = s.key_message("4×10⁻¹⁸ m", sub="about 1/400 of a proton (1.7 fm wide),\npresenter's estimate", y=deck.area["top"] + 0.1).bottom + 0.45   # 図の案から scaffold.py が組んだ（言い方を確かめる）
s.develop("10⁻²¹ (peak strain of the signal we\nwill see) × 4 km", "{r:4×10⁻¹⁸ m}")
s.block("Question：", ["how can we catch it?"])
if (FIG / "s05.png").exists(): s.figure_beside(FIG / "s05.png")   # 図：印象：大きな数字：4×10⁻¹⁸ m（about 1/400 of a proton, 1.7 fm wide; pre（図は figs/s05.png）

# ---------------------------------------------------------------- 6 More light, sharper ruler
s = deck.slide("Detector", summary="Recycled light reaches 100 kW per arm, 5,000× the 20 W input")
s.heading("More light, sharper ruler")
s.block("Arm cavity：", ["light bounces between the two test\nmasses, each trip adds the shift again"], then="phase effect {r:×300}")
s.block("Power recycling：", ["a partly transmitting input mirror\nsends light heading back to the laser\ninto the arms again, 20 W → 700 W →\n{r:100 kW}"])
s.flow(["Laser 20 W", "Beam splitter 700 W", "Each arm cavity 100 kW"], x=deck.area["fig_x"] + 0.8, y=deck.area["top"], w=3.6, h=0.75, gap=0.45, size=18)   # 図の案から scaffold.py が組んだ（言い方を確かめる）

# ---------------------------------------------------------------- 7 Noise by frequency band
s = deck.slide("Detector", summary="Above 10 Hz, ground motion is cut by >10 orders of magnitude")
s.heading("Noise by frequency band")
s.figure_main(FIG / "s07.png", caption="Abbott et al., PRL 116, 061102 (2016), Fig. 3(b), CC BY 3.0")
s.cases([("Above 150 Hz", "photon shot noise\n⇒ more light"), ("Middle", "thermal noise\n⇒ heavy 40 kg mirrors"), ("Low", "seismic noise\n⇒ {r:quadruple pendulum}\non active isolation")])

# ---------------------------------------------------------------- 8 GW150914
s = deck.slide("Result 1", summary="On 14 Sep 2015, Livingston saw it 6.9 ms before Hanford")
s.heading("GW150914")
y0 = s.cur_y
s.develop("L1 first", "H1 {r:6.9 ms later}\n(within the 10 ms light time)")
y1 = s.cur_y
b2 = s.block("Strength：", ["peak strain 1.0×10⁻²¹,\nSNR 24 (24× typical noise)"], x=deck.area["fig_x"], y=y0)
w = 10.0
im = s.image(FIG / "s08.png", (13.333 - w) / 2, max(y1, b2.bottom) + 0.25, w=w)
s.caption(im, "Abbott et al., PRL 116, 061102 (2016), Fig. 1 top row, CC BY 3.0")

# ---------------------------------------------------------------- 9 Frequency and amplitude grow
s = deck.slide("Result 1", summary="Eight cycles in 0.2 s, rising to 150 Hz at peak amplitude")
s.heading("Frequency and amplitude grow")
y0 = s.cur_y
b1 = s.block("Track：", ["35 → 150 Hz, ~8 cycles in 0.2 s,\namplitude peaks at {r:150 Hz}", "same track in H1 and L1"], y=y0)
b2 = s.block("Reading：", ["a 'chirp': masses spiral in,\norbit faster, so frequency\nand amplitude rise"], x=deck.area["fig_x"], y=y0)
w = 10.0
im = s.image(FIG / "s09.png", (13.333 - w) / 2, max(b1.bottom, b2.bottom) + 0.25, w=w)
s.caption(im, "Abbott et al., PRL 116, 061102 (2016), Fig. 1 bottom row, CC BY 3.0")

# ---------------------------------------------------------------- 10 Weighing by the chirp
s = deck.slide("Result 2", summary="The rate of the rise weighs the pair at 70 M⊙ or more in total")
s.heading("Weighing by the chirp")
s.figure_main(FIG / "s10.png", w=6.3, caption="Abbott et al., PRL 116, 061102 (2016), Fig. 2 top, CC BY 3.0")
b = s.peq(r"\mathcal{M} = \frac{(m_1 m_2)^{3/5}}{(m_1+m_2)^{1/5}}", dx=0.0, size=20)
b = s.peq(r"= \frac{c^3}{G}\left[\frac{5}{96}\pi^{-8/3} f^{-11/3}\dot{f}\right]^{3/5}", dx=0.2, size=20)
d = s.defs(b.x, b.bottom + 0.15, [("f, ḟ", "observed frequency and\nits rate of change")])
s.cur_y = d.bottom + 0.4
s.lead(["From the data: ℳ ≃ 30 M⊙"], "total mass {r:≳ 70 M⊙}")

# ---------------------------------------------------------------- 11 Ruling out neutron stars
s = deck.slide("Result 2", summary="At about 350 km apart, only black holes can hold 70 M⊙")
s.heading("Ruling out neutron stars")
if (FIG / "s11.png").exists(): s.figure_main(FIG / "s11.png", caption="(to scale, equal point masses)")
s.ask("Two neutron stars？", "{r:each ≲ 2 M⊙}")
s.ask("Neutron star + black\nhole？", "merges at a much lower\nfrequency")
s.ask("Two black holes？", "{r:350 km apart} (Kepler,\n75 Hz orbit), radii sum\n≳210 km (3 km per M⊙)")

# ---------------------------------------------------------------- 12 Glitches and disturbances
s = deck.slide("Result 3", summary="Non-Gaussian glitches in the data could fake a coincidence")
s.heading("Glitches and disturbances")
s.ask("Local disturbance？", "under {r:6% of the signal's strain},\ntoo small to make it")
s.ask("Chance coincidence？", "must be counted (next)")
s.compare(("Gravitational wave", ["same shape at both", "≤10 ms apart", "sensors quiet"]), ("Noise", ["shapes differ", "any offset", "sensors see it"]), y=s.cur_y + 0.3)

# ---------------------------------------------------------------- 13 Manufacturing background
s = deck.slide("Result 3", summary="Sliding one site's 16 days by ≫10 ms gave 608,000 years of noise")
s.heading("Manufacturing background")
if (FIG / "s13.png").exists(): s.figure_main(FIG / "s13.png", caption="(schematic)")
s.numbered(["Shift one site by ≫10 ms\n(beyond the light time, so\nno real wave lines up)", "Re-count coincidences", "Repeat ~10⁷ times\n⇒ {r:608,000 years}"])
s.block("Bias：", ["conservative, a real\nsignal left in makes noise\nlook stronger"])

# ---------------------------------------------------------------- 14 Beyond every background event
s = deck.slide("Result 3", summary="No background event beat it: < 1 false alarm per 203,000 yr")
s.heading("Beyond every background event")
b = s.figure_main(FIG / "s14.png", caption="Abbott et al., PRL 116, 061102 (2016), Fig. 4 right, CC BY 3.0")
s.oval(b.x + 0.907 * b.w - 0.3, b.y + 0.326 * b.h - 0.3, 0.6, 0.6)
s.block("Binary coalescence：", ["merger templates,\nρ̂c = 23.6 (loudness)"], then="< 1 per 203,000 yr, {r:5.1σ}")
s.block("Generic transient：", ["no waveform model,\nηc = 20.0"], then="< 1 per 22,500 yr, 4.6σ")
s.block("Two searches：", ["independent, both detect it"])

# ---------------------------------------------------------------- 15 Masses from the full waveform
s = deck.slide("Discussion", summary="Bayesian fits give 36 and 29 M⊙ before, 62 M⊙ after")
s.heading("Masses from the full waveform")
if (FIG / "s15.png").exists(): s.figure_main(FIG / "s15.png", caption="Abbott et al., PRL 116, 061102 (2016), Table I, CC BY 3.0")
s.develop("36 + 29 M⊙", "{r:62 M⊙}")
s.block("Radiated：", ["the missing 3.0 ± 0.5 M⊙c²\nas GWs"])
s.block("GR tests：", ["three checks, {r:no deviation}"])

# ---------------------------------------------------------------- 16 Back to the question
s = deck.slide(T, summary="A sub-proton stretch, caught at two sites and not by chance")   # まとめ：結論の一文はこの回の答え
s.heading("Summary")
s.recap(kind="筋", steps=["Tiny stretch: 4×10⁻¹⁸ m", "Strong light, quiet mirrors", "Same chirp, two sites", "Not chance: 5.1σ"], points=["Catch it？⇒ strong light, quiet mirrors", "Noise？⇒ < 1 per 203,000 yr", "Source？⇒ {r:merging black holes}"])

# ---------------------------------------------------------------- 17 Anticipated questions
s = deck.slide(T)   # summary なし：帯も●も無い枚になる
s.heading("Expected Questions")
s.at(1.0, 1.9)
s.qa_pairs([("Q1", "Could noise in the two detectors\nhave lined up by chance?", "Time-shifted background (608,000 yr):\nnoise this strong < 1 per 203,000 yr,\n5.1σ"), ("Q2", "Could an earthquake or a power-line\ndisturbance have caused it?", "Site sensors: all fluctuations under\n6% of the strain amplitude; no\ncorrelated disturbance at both sites")])

# ---------------------------------------------------------------- 18 Anticipated questions
s = deck.slide(T)   # summary なし：帯も●も無い枚になる
s.heading("Expected Questions")
s.at(1.0, 1.9)
s.qa_pairs([("Q3", "What does the 6.9 ms delay mean?", "Shorter than the 10 ms light travel\ntime between the sites, so one wave\ncould have passed both", (FIG / "s18.png", "Slide 8 figure: Abbott et al., PRL 116, 061102 (2016), Fig. 1 top right, CC BY 3.0")), ("Q4", "Where in the sky was the source?", "Only two detectors: about 600 deg²\n(90% region), set mainly by arrival\ntime; Virgo and KAGRA will narrow it")])

NOTES = load_notes(HERE / "notes.md")
for i, sl in enumerate(deck.slides, 1):
    if i in NOTES:
        sl.notes(NOTES[i])
OUT.parent.mkdir(parents=True, exist_ok=True)
deck.save(OUT, title=T, author=AUTHOR)
