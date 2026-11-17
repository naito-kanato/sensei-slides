"""型の見本の英語版：build.py の full() と同じ順・同じ枚数・同じ部品で、文字を英語にしたもの（設定の「言語」= 英語）。
使い方のページの英語版と英語の README の、型の一覧の画像（tools/make_docs_images.py）のもと。題材は同じ重力波の初観測。

    python figs.py         # 説明のための図（en_shift_before・en_shift_after）を figs/ に
    python build_en.py     # Structures_slides.pptx（テンプレート1。全部の型）

図は英語の論文紹介の見本（examples/zemi_en/figs・paper_figs）と、このフォルダの figs/ の en_ の図を使う
（論文紹介の図のうち、置き方が違って縮むもの＝輪の図 s02 は、figs/en_strain に描き直してある）。
日本語の文字が入った図（examples/zemi/figs・figs/shift_*）は使わない。en_shift_before・en_shift_after は説明のための例（実在の測定ではない）。
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parents[1]
sys.path.insert(0, str(SKILL / "scripts"))
from slide_profile import deck_options, load_profile  # noqa: E402
from zemi import Deck  # noqa: E402

ZFIG = HERE.parent / "zemi_en" / "figs"          # 英語の論文紹介の見本の図（s02 = strain、s05 = michelson など）
ZPAPER = HERE.parent / "zemi_en" / "paper_figs"  # 論文の図（解像度の印つき）
PAPER = HERE.parent / "zemi" / "paper_figs"      # 論文の図（build.py と同じもの）
FIG = HERE / "figs"
OUT = HERE / "Structures_slides.pptx"
T = "Structure Samples: The First Gravitational-Wave Detection"
SRC = "PRL 116, 061102 (2016)"

deck = Deck(workdir=HERE / "build", **deck_options(load_profile(HERE), name="テンプレート1", lang="英語"))
A = deck.area
deck.title_slide(["Structure Samples", "Text Shapes and Diagram Parts"], author="sensei-slides")
R = 12.65   # 図の右端（ページの右の余白 0.4 in の内側）


def zfig(s, path, y):
    """見本の図を、描いた幅のまま本文の右に置く（build.py の zfig と同じ。本文の下端・右端に入らなければ縮める）。"""
    from PIL import Image
    with Image.open(path) as im:
        w, h = im.size[0] / im.info["dpi"][0], im.size[1] / im.info["dpi"][0]
    col = "text_right" in A
    tr = max([b.right for kind, b in s.boxes if kind != "image" and deck.header_bottom - 0.2 < b.y < deck.content_bottom] + [A["x"]])
    x0 = A["fig_x"] if col else tr + 0.6
    k = min(1.0, (deck.content_bottom - 0.35 - y) / h, (R - x0) / w)
    w, h = w * k, h * k
    x = x0 if col else min(tr + max(0.6, (R - w - tr) / 2), R - w)
    return s.image(path, x=x, y=y, w=w, h=h)


# ---- 本文の形
s = deck.slide(T, summary="Premise ⇒ result: explanation first, result in red")
s.heading("Premise ⇒ result (s.lead)")
s.at(1.0, 1.95)
s.lead(["Predicted by Einstein in 1916", "spacetime strain at light speed"], "No direct observation")
s.lead(["Orbital decay of a binary pulsar", "rate as predicted (Nobel Prize 1993)"], "Confirmed only indirectly")
b = zfig(s, FIG / "en_strain.png", y=2.3)   # 論文紹介の s02 は下に横長に置く幅（8.4 in）で、右に置くと縮んで文字が 14pt を下回る
s.caption(b, "(schematic)")

s = deck.slide(T, summary="Label + explanation: name as a subheading, details indented")
s.heading("Label + explanation (s.block)")
s.at(1.0, 1.95)
s.block("Michelson interferometer:", ["arm-length difference (4 km arms)", "laser interference as the ruler",
                                     "strain changes down to 10^{-21}"])
s.block("Two sites at once:", ["Hanford and Livingston", "two detectors ~3000 km apart", "arrival gap about 7 ms"],
        then="told apart from noise")
zfig(s, ZFIG / "s05.png", y=1.9)

s = deck.slide(T, summary="Horizontal arrow: condition on the left, result on the right")
s.heading("Horizontal arrow (s.develop)")
s.at(1.0, 2.0)
s.develop(("Strain:", ["1.0 × 10^{-21}"]), "4 km arm changes by\n{r:about 4 × 10^{-18} m}")
s.develop("Same waveform\nat two detectors", "{r:not explained}\n{r:by detector noise}")
s.develop("Frequency 35 Hz", "up to 250 Hz\nin about 0.2 s")
b = zfig(s, FIG / "en_same_wave.png", y=2.0)   # 置く幅で描いた図（論文紹介の s06 は横長で、右に置くと縮んで文字が 14pt を下回る）
s.caption(b, "(illustrative example)")

s = deck.slide(T, summary="Cases: conditions in bold, details indented in a gray box")
s.heading("Cases (s.cases)")
s.cases([("Before merger (inspiral)", "frequency from 35 Hz to 250 Hz\n8 cycles in about 0.2 s"),
         ("Merger", "peak amplitude (strain 1.0 × 10^{-21})"),
         ("After merger (ringdown)", "damped ringing of one black hole\n(62 solar masses)")], x=1.0, y=1.95)
b = zfig(s, ZPAPER / "fig1_timefreq_H1.png", y=2.1)
s.caption(b, f"Fig. 1 bottom row (H1), {SRC}")

s = deck.slide(T, summary="Question → answer: check other explanations one by one")
s.heading("Question → answer (s.ask)")
s.at(1.0, 1.95)
s.ask("Just detector noise?", "same waveform at both sites,\n~7 ms apart")
s.ask("Chance coincidence?", "{r:significance above 5.1σ}\nfalse alarm < once\nin 200,000 years")
s.ask("Strong enough signal?", "SNR 24\n(two detectors combined)")
b = zfig(s, ZPAPER / "fig4_search.png", y=1.9)
s.caption(b, f"Fig. 4 right, {SRC}; red circle added")

s = deck.slide(T, summary="Numbered steps: the order of an analysis or a measurement")
s.heading("Numbered steps (s.numbered)")
s.numbered(["Divide by the noise\n(whitening, both sites)", "Compare with model waveforms\n(matched filter, SNR 24)",
            "Shift one site in time\nto estimate chance matches"], x=1.0, y=1.95)
zfig(s, ZFIG / "s07.png", y=1.85)   # s13（時刻ずらし）は縦に長く、縮んで文字が 14pt を下回る

s = deck.slide(T, summary="First direct detection confirms binary black holes exist")
s.heading("Vertical arrow to a conclusion (s.lead_down)")
# 前提を4行・文字 24pt にして、本文の場所の高さ・幅を埋める（2行・20pt では、まわりが空いて ERROR）
s.lead_down("Black holes of 36 and 29 solar masses merged into one\nGravitational waves that traveled 1.3 billion light-years\n"
            "The same waveform at two detectors, about 7 ms apart\nFirst direct detection of gravitational waves (Sept. 14, 2015)",
            "Binary black holes exist,\nas general relativity predicts", x=1.0, y=1.85, size=24, gap=0.3)

# ---- 図解の型
deck.section(2, "Diagram Patterns", lead="Cards, trees, before/after, paired figures, callouts")

s = deck.slide(T, summary="Parallel cards: equal boxes for equal-rank items")
s.heading("Parallel cards (s.cards row; third with a big value)")
b = s.cards([("Mass", "two merged into one\n(in solar masses)", "36+29 → 62"), ("Distance", "about 1.3 billion\nlight-years (z = 0.09)", "410 Mpc"),
             ("Radiated energy", "emitted as GWs\n(in solar masses)", "≈ 3")], y=1.9)
# カードの下に、値から言えることをラベルで（カードだけでは下が空き、箱のまわりが空いていると ERROR になる）
y = b.bottom + 0.45
s.block("Significance:", ["first direct detection of GWs", "first binary black hole merger seen"], x=b.x, y=y, gap=0)
s.block("Test:", ["{r:consistent} with general relativity"], x=b.x + b.w / 2 + 0.3, y=y, gap=0)

s = deck.slide(T, summary="Staggered steps: stages offset like stairs, thin arrows between")
s.heading("Staggered steps (s.cards steps)")
s.cards([("Binary", "two black holes"), ("Inspiral", "tightening orbit"), ("Merger", "burst of gravitational waves"),
         ("Detection", "1.3 billion years later\nSept. 14, 2015")], layout="steps", y=1.9)

s = deck.slide(T, summary="Cycle: four cards for repeating stages")
s.heading("Cycle (s.cards cycle)")
# 横いっぱい・カードの高さ 1.6 in・説明2行で、本文の場所を埋める（幅 8.9 in・説明1行では、まわりが空いて ERROR）
s.cards([("Observation", "data from the two detectors"), ("Noise analysis", "search for noise sources\n(ground motion, mirror heat, photons)"),
         ("Upgrade", "noise reduction\n(pendulums, more laser power)"), ("Higher sensitivity", "sources farther away\n{r:next observing run}")],
        layout="cycle", y=1.85, h=1.6)

s = deck.slide(T, summary="Tree: categories and hierarchy as branches")
s.heading("Tree (s.tree)")
# 箱を高く（h 0.8）・文字 20pt・子の箱を横いっぱいに（h 0.62・18pt では、まわりが空いて ERROR）
s.tree("GW sources", [("Binary mergers", "black holes, neutron stars ({r:this event})"), ("Supernovae", "stellar core collapse"),
                      ("Spinning neutron stars", "continuous waves"), ("Background GWs", "early universe")],
       y=1.85, root_w=3.0, child_w=7.5, h=0.8, gap=0.3, size=20)

s = deck.slide(T, summary="Before/after: old vs. improved, the gap as one number")
s.heading("Before/after (s.before_after)")
# 各側3行（何年・何を変えたか・結果）と箱の高さ 2.9 in で、本文の場所を埋める（2行ずつでは、まわりが空いて ERROR）
s.before_after(("Initial detectors", ["observing runs 2002–2010", "1-stage pendulum, 10 kg mirrors", "no gravitational waves found"]),
               ("Advanced detectors", ["observing from 2015", "4-stage pendulum, 40 kg mirrors", "detection on Sept. 14, 2015"]),
               value="3 times the sensitivity", y=1.9, h=2.9)

s = deck.slide(T, summary="Paired figures: two conditions side by side, values below")
s.heading("Two figures side by side (s.pair)")
s.pair(FIG / "en_shift_before.png", FIG / "en_shift_after.png", labels=["Unshifted", "Time-shifted"],
       values=["two detectors align", "no match"], y=1.85, caption="(illustrative example)")

s = deck.slide(T, summary="Callout: from a point in the figure to its meaning")
s.heading("Callout on a figure (s.callout)")
s.at(1.0, 1.95)
s.lead(["Output normally dark", "(the two beams cancel)", "arm lengths change:", "brightness changes"],
       "Light level gives\nthe length difference")
b = zfig(s, ZFIG / "s05.png", y=1.85)
k = b.w / 6.12   # 光検出器の位置は、幅 6.12 in（描いた幅）の図で測った値を幅に比例させる
s.callout((b.x + 1.7 * k, b.y + 4.15 * k), (b.x - 3.0, b.y + 3.9 * k), "brightness read here")

deck.build_up(T, "Adding items one by one (deck.build_up)",
              ["1. First direct detection of GWs", "2. Merger of two black holes", "3. General relativity confirmed"],
              summary="Build-up: current item dark, earlier items gray", figure=FIG / "en_strain.png", fig_x=6.4)

# ---- 図が主役：左に大きな図、右の細い列に補足
s = deck.slide(T, summary="Figure first: large figure left, how to read it right")
s.heading("Figure as the main element (s.figure_main)")
b = s.figure_main(PAPER / "fig2_waveform_lower.png", caption=f"(Abbott et al., {SRC}, part of Fig. 2)")
s.block("Top: strain waveform", ["gray: reconstructed from data", "red: general relativity"], then="nearly identical")
s.block("Bottom: speed and gap", ["green: relative speed (c = 1)", "black: separation", "over c/2 just before merger"], gap=0)

# ---- 想定質問：答えが前の枚の図につながる組だけ、その図を右に添える
from PIL import Image  # noqa: E402
crop = HERE / "build" / "q_strain_right.png"
crop.parent.mkdir(parents=True, exist_ok=True)
with Image.open(PAPER / "fig1_strain.png") as im:   # 切り出すだけ（描き足さない）
    im.crop((im.width * 53 // 100, 0, im.width, im.height)).save(crop)
s = deck.slide(T)
s.heading("Expected questions (s.qa_pairs; figure as 4th item)")
s.qa_pairs([("Q1", "Why is the H1 trace inverted\nbefore it is overlaid?", "Arms of the two detectors differ\nSame wave with opposite sign",
             (crop, f"Fig. 1 top row, right (Abbott et al., {SRC})")),
            ("Q2", "Could a local shake, like\nan earthquake, cause it?", "No matching signal in vibration sensors\nNo reason for both sites to shake")])

deck.save(OUT, title=T)
