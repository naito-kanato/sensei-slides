"""English version of the seminar sample: paper review "First Observation of Gravitational Waves" (cover + 15 slides).
A translation of ../zemi/build.py (same structure and slide order).

Paper: B. P. Abbott et al., Phys. Rev. Lett. 116, 061102 (2016) (CC BY 3.0). The paper's figures are in ../zemi/paper_figs/
(sources in ATTRIBUTION.md).

    python figs.py      # write our own figures to figs/
    python build.py     # build First_Observation_of_Gravitational_Waves_slides.pptx (notes.md goes into the speaker notes)
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
PAPER = HERE.parent / "zemi" / "paper_figs"
OUT = HERE / "First_Observation_of_Gravitational_Waves_slides.pptx"
SRC = "Abbott et al., PRL 116, 061102 (2016)"

P = load_profile(HERE)
AUTHOR = author(P) or "Presenter"
deck = Deck(workdir=HERE / "build", **deck_options(P))
TOP = deck.header_bottom   # how high a figure may go (depends on the template; lower when a conclusion header is on top)

# ---------------------------------------------------------------- 1 cover
deck.title_slide(["Paper Review:", "First Observation of Gravitational Waves"], author=AUTHOR)

# The body follows the "body form" column of ../zemi/outline.md. The conclusion is said in the header line, so the body
# shows the evidence (labels, steps, equation notes, cases, development, questions) instead of repeating it.
# Figures are drawn to fill the white space on the right, at least 0.75 in right of the body text (right edge at R).
R = 12.65   # right edge of figures (inside the 0.4 in page margin)


def beside(s, path, y, w=None, h=None, caption=None):
    """Place a figure right of the body: x = body's right edge + 0.75 in or more (aligned to R if it does not fit).
    Without a width, it keeps the drawn width."""
    from PIL import Image
    with Image.open(path) as im:
        pw, ph = im.size
        dpi = (im.info.get("dpi") or (0, 0))[0]
    if w is None:
        w = h * pw / ph if h is not None else pw / dpi
    text_right = max(b.right for kind, b in s.boxes if kind != "image" and b.y > 1.5)
    off = max(0.75, (R - w - text_right) / 2)   # split a large gap between the text side and the right side
    b = s.image(path, x=min(text_right + off, R - w), y=y, w=w)
    if caption:
        s.caption(b, caption)
    return b


# ---------------------------------------------------------------- 2 background
s = deck.slide("Background", summary="Predicted 100 years ago, yet never observed directly")
s.heading("Gravitational waves")
s.at(1.0, 1.9)
s.block("Prediction:", ["Einstein, 1916", "From general relativity"], gap=0.3)     # body form: labels
s.block("Nature:", ["Strain of spacetime, moving at c", "From a changing quadrupole", "x stretches, y squeezes, then flips"], gap=0.3)
s.block("So far:", ["Tiny amplitude (Einstein knew it)", "Seen {r:indirectly} in binary pulsars"], gap=0)
beside(s, FIG / "strain.png", y=2.4, caption="(Sketch: motion of particles on a ring)")

# ---------------------------------------------------------------- 3 background: binary pulsar
s = deck.slide("Background", summary="Binary pulsars confirmed them indirectly; next, the wave itself")
s.heading("Binary pulsar")
s.at(1.0, 1.9)
s.block("Discovery:", ["Hulse and Taylor found", "{u:PSR B1913+16}", "(a neutron star with", "regular radio pulses)"], gap=0.3)   # body form: labels
s.block("Observation:", ["Taylor and Weisberg", "observed its {r:energy loss}"], gap=0.3)
s.block("Next goal:", ["Observe amplitude and phase", "(test GR in strong gravity)"], gap=0)
beside(s, FIG / "pulsar.png", y=1.9, caption="(Sketch: shrinking orbit of the binary)")

# ---------------------------------------------------------------- 4 the paper
deck.title_slide(["Observation of Gravitational Waves", "from a Binary Black Hole Merger"],
                 subtitle="The discovery paper of GW150914",
                 author="B. P. Abbott et al. (LIGO Scientific Collaboration and Virgo Collaboration)\n"
                        "Phys. Rev. Lett. 116, 061102 (2016)   CC BY 3.0\n"
                        "DOI: 10.1103/PhysRevLett.116.061102",
                 bold=False)

# ---------------------------------------------------------------- 5 method 1
s = deck.slide("Method", summary="A laser interferometer reads the length difference of two arms")
s.heading("Advanced LIGO detector")
s.at(1.0, 1.9)
s.block("Michelson interferometer:", ["Two perpendicular 4 km arms", "A wave stretches one,", "{r:squeezes the other}",
                                     "Read as a phase difference"], gap=0.15)   # body form: labels, equation notes
e = s.peq(r"\Delta L=\delta L_x-\delta L_y=hL", dx=0.35, gap=0.35)
s.defs(e.right + 0.3, e.y + 0.02, [("h", "strain"), ("L", "arm length")], sep=": ")
s.block("Two sites at once:", ["Hanford and Livingston", "10 ms apart at light speed", "Rules out local noise"], gap=0)
beside(s, FIG / "michelson.png", y=1.85, caption=f"(Drawn after {SRC}, Fig. 3)")

# ---------------------------------------------------------------- 6 method 2
s = deck.slide("Method", summary="The difference is below a proton; light in the arms reaches 100 kW")
s.heading("Boosting sensitivity with light")
s.at(1.0, 1.9)
s.block("Arm cavities:", ["Light bounces between mirrors", "Phase effect boosted {r:300×}"], gap=0.3)   # body form: labels
s.block("Power-recycling mirror:", ["Stores light at the input"], gap=0.3)
s.block("Signal-recycling mirror:", ["Widens the bandwidth at the output"], gap=0.3)
s.block("Aim:", ["Amplify a sub-proton difference", "Suppress high-frequency shot noise"], gap=0)
beside(s, FIG / "power.png", y=1.85, caption=f"(Drawn from values in {SRC}, Sec. III)")

# ---------------------------------------------------------------- 7 method 3
s = deck.slide("Method", summary="Suspended mirrors cut noise; most sensitive at 100–300 Hz")
s.heading("Reducing noise")
s.cases([("High f: photon shot noise", ["Photon-number noise, >150 Hz", "Reduced by more light"]),   # body form: cases (by band)
         ("Low f: ground vibration", ["{r:4-stage pendulum} isolation", "With active platforms:", ">10 orders above 10 Hz"]),
         ("Middle: mirror thermal noise", ["40 kg fused-silica mirrors", "and fibers of low-loss material"])], x=1.0, y=1.85)
beside(s, PAPER / "fig3b_noise.png", y=max(1.6, TOP), w=5.6, caption=f"({SRC}, Fig. 3(b))")

# ---------------------------------------------------------------- 8 results 1
s = deck.slide("Results 1", summary="Both detectors saw the same signal, 7 ms apart")
s.heading("The same signal in both")
s.at(1.0, 1.85)
s.develop("L1 detects first\n(Sept. 14, 2015)", "H1 6.9 ms later\n< light travel {r:10 ms}", after=0.15)   # body form: development with an arrow
s.p("Peak strain 1.0×10^{−21}\nCombined SNR (signal-to-noise) 24\nRight: H1 inverted, shifted onto L1", gap=0)
left_end = s.cur_y
s.block("Length change:", ["ΔL ≈ 10^{−18} m (4 km arm)", "Far below a proton size"], x=8.4, y=1.85, gap=0)
w = 9.4
b = s.image(PAPER / "fig1_strain.png", x=(13.333 - w) / 2, y=max(left_end, s.cur_y) + 0.4, w=w)
s.caption(b, f"({SRC}, Fig. 1 top. Vertical axis: strain ×10^{{−21}})")

# ---------------------------------------------------------------- 9 results 1 (time-frequency)
s = deck.slide("Results 1", summary="In the time–frequency map, the frequency rises with time")
s.heading("The frequency goes up")
s.at(1.0, 1.85)
s.block("How to read:", ["x: time, y: frequency, color: power", "Same rise in both H1 and L1"], gap=0.2)        # body form: labels, development
s.develop("Starts at 35 Hz", "Up to {r:250 Hz} in ~0.2 s", after=0.2)
left_end = s.cur_y
s.block("Bright track:", ["Lower left to upper right", "Peak amplitude near 150 Hz", "Rise rate gives the masses"],
        x=8.0, y=1.85, gap=0.2)
w = 8.6
b = s.image(PAPER / "fig1_timefreq.png", x=(13.333 - w) / 2, y=max(left_end, s.cur_y) + 0.1, w=w)
s.caption(b, f"({SRC}, Fig. 1 bottom. Left: H1, right: L1)")

# ---------------------------------------------------------------- 10 results 2
s = deck.slide("Results 2", summary="The waveform shows two bodies spiraling in and merging")
s.heading("What the waveform reveals")
s.at(1.0, 1.9)
s.block("Waveform:", ["8 cycles in about 0.2 s", "Period shortens, amplitude grows", "35→150 Hz, then peak amplitude"], gap=0.3)   # body form: labels
s.block("Chirp mass:", ["≈30 {i:M}_{⊙} ⇒ total {r:≥70 {i:M}_{⊙}}", "(detector frame; {i:M}_{⊙}: solar mass)"], gap=0.3)
s.block("Comparison with theory:", ["Matches numerical relativity", "Bottom: speed exceeds c/2"], gap=0)
beside(s, PAPER / "fig2_waveform.png", y=max(1.55, TOP), h=5.0, caption=f"({SRC}, Fig. 2)")

# ---------------------------------------------------------------- 11 results 2 (why black holes)
s = deck.slide("Results 2", summary="Of known objects, only black holes are small enough to orbit at 75 Hz")
s.heading("Why black holes?")
s.at(1.0, 1.9)
s.block("Orbit at 75 Hz (GW at 150 Hz):", ["Separation ≈ 350 km", "Sum of {u:Schwarzschild radii}", "≳ 210 km (70 {i:M}_{⊙})"], gap=0.25)   # body form: labels, questions
s.ask("Two neutron stars?", "Compact, but {r:too light}", gap=0.25)
s.ask("Neutron star + black hole?", "Merges at a {r:lower frequency}\n(same chirp mass: larger total)", gap=0)
beside(s, FIG / "scale.png", y=2.0, caption="(To scale. Equal masses: one diameter = sum of radii)")

# ---------------------------------------------------------------- 12 results 3 (building the background)
s = deck.slide("Results 3", summary="Noise could coincide by chance, so count how often it does")
s.heading("Background from time shifts")
s.at(1.0, 1.9)
s.p("Doubt: noise lined up by chance?", gap=0.2)
s.p("Problem: noise alone can't be measured", gap=0.2)
s.p("Real signal: in both within 10 ms", gap=0.3)
s.numbered(["Shift one detector by\nmore than 10 ms",                          # body form: steps
            "Search for coincidences\n(real signals no longer align)",
            "~10^{7} shifts of 16 days\n= {r:608,000 years} of background"], gap=0.3)
s.p("Overestimated background ⇒ conservative", gap=0)
beside(s, FIG / "timeshift.png", y=max(1.75, TOP), caption="(Sketch: example signal and noise)")

# ---------------------------------------------------------------- 13 results 3
s = deck.slide("Results 3", summary="Noise mimics it by chance less than once in 200,000 years")
s.heading("Not a chance noise event")
s.at(1.0, 1.9)
s.block("How to read:", ["Black: time-shift background", "Orange: actual data", "Purple: background w/o GW150914"], gap=0.3)   # body form: labels
s.block("GW150914 (red circle):", ["Statistic 23.6: above all background", "False alarms < 1 per 203,000 yr",
                                  "Probability < 2×10^{−7} = {r:≥5.1σ}"], gap=0.3)
s.block("Search without a waveform model:", ["< 1 per 22,500 yr, 4.6σ"], gap=0)
w = 5.8
b = beside(s, PAPER / "fig4_search.png", y=max(1.55, TOP), w=w, caption=f"({SRC}, Fig. 4 right. Red circle added)")
k = w / 5.4   # the circle's position was set for a 5.4 in wide figure; scale it with the width
s.oval(b.x + 4.6 * k, b.y + 1.25 * k, 0.52 * k, 0.48 * k)

# ---------------------------------------------------------------- 14 discussion
s = deck.slide("Discussion", summary="First direct detection of gravitational waves and of a black hole binary")
s.heading("What we learned")
y = s.table(1.0, 1.9, [3.6], 0.55, ["Median (90% range)"],
            [("Primary BH", ["36 (+5, −4) {i:M}_{⊙}"]),
             ("Secondary BH", ["29 (+4, −4) {i:M}_{⊙}"]),
             ("Final BH", ["62 (+4, −4) {i:M}_{⊙}"]),
             ("Radiated", ["{r:3.0 (±0.5) {i:M}_{⊙}{i:c}^{2}}"]),
             ("Distance", ["410 (+160, −180) Mpc"])], label_w=2.0)
s.caption(Box(1.0, 1.9, 4.98, y - 1.96), "(Source frame. From Table I and the text)")
s.at(7.2, 1.95)
s.block("Significance:", ["First direct detection of GWs", "First binary black hole merger"], gap=0.3)          # body form: labels
s.block("Mass budget:", ["36 + 29 − 62 ≈ 3 {i:M}_{⊙} into GWs", "Detector frame: ×1.09 ≈ 71 {i:M}_{⊙}"], gap=0.3)
s.block("Tests:", ["{r:Consistent} with 3 tests of GR"], gap=0.3)
s.block("Outlook:", ["Virgo and KAGRA: better sky location"], gap=0)

# ---------------------------------------------------------------- 15 anticipated questions
s = deck.slide("Q&A")   # no summary: a slide without the band
s.heading("Anticipated questions")
s.at(1.0, 1.9)
s.qa_pairs([("Q1", "Isn't it just noise lining up by chance?",
             "We counted the background with time-shifted pairs:\nfalse alarms < 1 per 203,000 yr (≥5.1σ)"),
            ("Q2", "Couldn't it be a pair of neutron stars?",
             "A 75 Hz orbit means a separation of ≈350 km\nTwo neutron stars would be too light")])

# ---------------------------------------------------------------- 16 anticipated questions
s = deck.slide("Q&A")
s.heading("Anticipated questions")
s.at(1.0, 1.9)
s.qa_pairs([("Q3", "What does the 6.9 ms delay between the two detectors mean?",
             "It is shorter than the 10 ms light travel time\nConsistent with one wave passing both sites"),
            ("Q4", "How much energy was released?",
             "About 3 solar masses (3.0 {i:M}_{⊙}{i:c}^{2})\nThe difference between 36 + 29 before and 62 after")])

NOTES = load_notes(HERE / "notes.md")
for i, sl in enumerate(deck.slides, 1):
    if i in NOTES:
        sl.notes(NOTES[i])
deck.save(OUT, title="Paper Review: First Observation of Gravitational Waves", author=AUTHOR)
