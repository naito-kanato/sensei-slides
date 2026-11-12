"""Course sample, Lecture 1 "What Does Generative AI Do?" (cover + 10 body + 2 quiz + 2 answer = 15 slides).
English version of examples/course/_work/AI活用講座_01/build.py (same structure, same slide order).

    python figs.py      # write the figures to figs/
    python build.py     # build ../../AI_Literacy/01_What_Generative_AI_Does_slides.pptx (notes from notes.md)
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parents[3]
sys.path.insert(0, str(SKILL / "scripts"))
from set_notes import load_notes  # noqa: E402
from slide_profile import author, deck_options, load_profile  # noqa: E402
from zemi import Deck  # noqa: E402

T = "Lecture 1: What Does Generative AI Do?"
SUB = "— Plausible Is Not the Same as Correct"
FIG = HERE / "figs"
OUT = HERE.parents[1] / "AI_Literacy" / "01_What_Generative_AI_Does_slides.pptx"

P = load_profile(HERE)
AUTHOR = author(P) or "Learner's name"
deck = Deck(workdir=HERE / "build", **deck_options(P, name="テンプレート2"))   # the course sample uses template 2


def qa(s, items, size=20, gap=0.45):
    """Body of the quiz / answer slides. items = [(number, text)]. Numbers are in the form "1-1"."""
    s.at(1.0, 2.0)
    for j, (k, txt) in enumerate(items):
        s.p("{b:" + k + "}　" + txt, size=size, gap=gap if j < len(items) - 1 else 0.2)


# The conclusion is stated in the line at the top (the conclusion title), so the body does not repeat it as a final
# red line; it shows the grounds instead (steps, labels, cases, questions, developments). Red marks the key word or
# number of the grounds. Figures are drawn to fill the white space on the right and placed 0.75 in or more right of the text.
R = 12.6   # right edge of figures (inside the 0.4 in page margin)


def text_right(s):
    return max(b.right for kind, b in s.boxes if kind != "image" and b.y > 1.4)


def beside(s, path, y, caption=None):
    """Place a figure to the right of the body text (at its drawn width). If there is a lot of room, split it evenly
    between the gap before the figure and the space after it."""
    from PIL import Image
    with Image.open(path) as im:
        w = im.size[0] / im.info["dpi"][0]
    tr = text_right(s)
    b = s.image(path, x=min(tr + max(0.75, (R - w - tr) / 2), R - w), y=y)
    if caption:
        s.caption(b, caption)
    return b


def flow_beside(s, items, y, w=4.2, h=0.75, gap=0.5):
    """Place a flow chart (PowerPoint shapes) to the right of the body text."""
    tr = text_right(s)
    x = min(tr + max(0.75, (R - w - tr) / 2), R - w)
    s.flow(items, x=x, y=y, w=w, h=h, gap=gap)


# ---------------------------------------------------------------- 1 cover
deck.title_slide([T], author=AUTHOR, subtitle=SUB)

# ---------------------------------------------------------------- 2 predicting the next word
s = deck.slide(T, summary="A model that learned from vast text how likely each next word is")
s.heading("Predicting the Next Word")
s.at(1.0, 2.0)
s.block("Large language model (LLM):", ["Learns from vast text which words", "tend to follow which"], gap=0.3)
s.numbered(["Read the preceding context",                                             # body form: steps
            "Compute each next word's probability\n(how likely it follows, {r:not truth})",
            "Pick one word by probability, append it"], gap=0.3)
s.block("Common misconception:", ["It looks up answers and shows them", "In fact it generates word by word"], gap=0)
beside(s, FIG / "next_token.png", y=1.85, caption="(Simplified; probabilities are examples)")

# ---------------------------------------------------------------- 3 splitting into tokens
s = deck.slide(T, summary="Text is split into words or pieces; length is counted in those")
s.heading("Splitting into Tokens")
s.at(1.0, 1.9)
s.block("Token:", ["A word or part of a word", "Splitting differs by model", "5 in \"Tomorrow's weather is sunny\""], gap=0.3)   # body form: labels
s.block("Length counts in tokens:", ["A limit on how much it reads at once", "(GPT-3 in 2020: 2048)", "Newer models: longer, still limited",
                                     "{r:A long document may not fit}", "Fix: split it by chapter"], gap=0)
beside(s, FIG / "tokens.png", y=2.5, caption="(The split is an example)")

# ---------------------------------------------------------------- 4 two stages of training
s = deck.slide(T, summary="Tuning adds instruction-following on top of continuing text")
s.heading("Two Stages of Training")
s.at(1.0, 1.85)
s.block("Pretraining:", ["Predict the next word in vast text"], gap=0.25)                # body form: labels
s.block("Tuning:", ["Human examples and ratings teach it", "to follow instructions"], gap=0.25)
s.block("Comparison:", ["A tuned 1.3-billion-parameter model", "was {r:rated higher} than 175-billion GPT-3"], gap=0.25)
s.p("Parameter: a number inside the model\nwhose value is set by training", dx=0.35, size=18, gap=0)
flow_beside(s, ["Vast text", "Pretraining", "Tuning by human feedback (RLHF)", "Chat model"], y=1.75, h=0.7)

# ---------------------------------------------------------------- 5 bigger models do better
s = deck.slide(T, summary="As models grew, their prediction error fell in a regular way")
s.heading("Bigger Models Do Better")
s.key_message("1.5B → 175B", "Parameters in billions (GPT-2 → GPT-3)\n2019 → 2020: over 100× in about a year\n"
              "More size, data, and compute\n⇒ error falls by a {r:power law}\n"
              "Each 10× in size cuts it by a fixed ratio\nThe trend held over 7+ orders of magnitude", y=2.2)   # big-number form

# ---------------------------------------------------------------- 6 not the same every time
s = deck.slide(T, summary="Even big models pick by probability, so answers can vary each time")
s.heading("Not the Same Every Time")
s.at(1.0, 1.85)
s.block("Sampling:", ["Picks like a lottery weighted by probability", "Always taking #1 gets repetitive"], gap=0.2)   # body form: labels, cases
s.block("Temperature:", ["Sets how much the choice varies", "Low: nearly the same answer each time"], gap=0.25)
s.cases([("Low temperature (0.5)", "Focuses on the likely \"sunny\""), ("High temperature (2)", "{r:Unlikely words like \"snowy\" get a chance}")])
beside(s, FIG / "temperature.png", y=1.85, caption="(Renormalized over slide 2's 4 candidates)")

# ---------------------------------------------------------------- 7 plausible but wrong
s = deck.slide(T, summary="Even natural-sounding text can be factually wrong")
s.heading("Plausible but Wrong")
s.at(1.0, 1.9)
s.block("Hallucination:", ["Plausible-sounding content that is", "false or has no basis"])     # body form: label, questions
s.ask("If it reads naturally, isn't it right?", "It computes likelihood (slide 2)")
s.ask("If it cites sources, isn't it safe?", "{r:Nonexistent references}: 18% even in GPT-4\n(55% in GPT-3.5; 2023 versions)", gap=0)
beside(s, FIG / "fabricated.png", y=1.85, caption="(Plotted from values in Walters & Wilder,\nSci. Rep. 13, 14045 (2023))")

# ---------------------------------------------------------------- 8 why errors happen
s = deck.slide(T, summary="It links words without checking facts, so it errs where it knows little")
s.heading("Why Errors Happen")
s.cases([("The model alone", ["No checking against facts", "Search in some services: an add-on"]),   # body form: cases (where errors are likely)
         ("Rare or missing in training data", ["e.g., {r:rare names, detailed numbers}", "Rarer facts, more wrong answers"]),
         ("Events after the cutoff", ["Unknown (GPT-4 then: Sep. 2021)", "Current versions still have a cutoff"])], x=1.0, y=1.9)
beside(s, FIG / "cutoff.png", y=2.6, caption="(Simplified)")

# ---------------------------------------------------------------- 9 check as you use it
s = deck.slide(T, summary="Trace sources to the originals; don't use what can't be verified")
s.heading("Check as You Use It")
s.at(1.0, 1.85)
s.block("Primary sources:", ["Papers, official documents, originals", "Search by title, author, DOI", "Beware papers with similar titles"], gap=0.3)   # body form: labels, development
s.develop("Source not found\nor content differs", "Hold as\n{r:\"needs checking\"}", gap=0.25, after=0.3)
s.block("Give it materials:", ["It answers from given materials (RAG)", "Even post-cutoff topics, if covered"], gap=0)
flow_beside(s, ["AI's answer", "Ask for sources", "Check primary sources", "Use / needs checking"], y=1.75, h=0.7)

# ---------------------------------------------------------------- 10 how to ask
s = deck.slide(T, summary="State the goal and conditions, and have it show its reasoning")
s.heading("How to Ask")
s.at(1.0, 2.0)
s.numbered(["State the goal, conditions, answer form\n(e.g., 3 lines for a seminar, define terms)",   # body form: steps (order when asking)
            "Attach the materials it should use",
            "Have it write out {r:its reasoning}\n(chain of thought)"], gap=0.3)
s.p("Accuracy gap: a 540-billion-parameter\nmodel (no effect in small models)", gap=0.3)
s.p("\"Think step by step\" works even\nwithout examples", gap=0)
beside(s, FIG / "cot.png", y=1.8, caption="(Plotted from values in Wei et al., NeurIPS 2022, Table 2)")

# ---------------------------------------------------------------- 11 information to check before input
s = deck.slide(T, summary="Before input, check terms and settings for how it will be used")
s.heading("Check Before You Input")
s.at(1.0, 1.85)
s.ask("Is my input used for training?", "{r:Some services are set to do so}\n(it may appear in answers to others)", gap=0.3)   # body form: questions
s.ask("Where do I check?", "Terms of use, settings, your org's rules\n(Japan's privacy commission advises it)", gap=0.3)
s.ask("What if I can't check?", "Hold off (especially the 3 at right)", gap=0)
beside(s, FIG / "dont_input.png", y=1.8)

# ---------------------------------------------------------------- 12, 13 review questions
s = deck.slide(T)   # quiz / answers: no summary, so no band and no bullet
s.heading("Review Questions (1-1 to 1-3)")
qa(s, [("1-1", "What does a large language model compute when it writes text?"),
       ("1-2", "Why can the same question get different answers?"),
       ("1-3", "Why is a model tuned with human examples and ratings after pretraining?")], gap=0.75)

s = deck.slide(T)   # quiz / answers: no summary, so no band and no bullet
s.heading("Review Questions (1-4 to 1-6)")
qa(s, [("1-4", "What is hallucination? Give one case where it is likely."),
       ("1-5", "How would you check that a reference cited by AI really exists?"),
       ("1-6", "You want AI to summarize unpublished experimental data.\nWhat should you check before entering it?")], gap=0.75)

# ---------------------------------------------------------------- 14, 15 answers
s = deck.slide(T)   # quiz / answers: no summary, so no band and no bullet
s.heading("Answers (1-1 to 1-3)")
qa(s, [("1-1", "The {r:probability of the next token}, given the preceding context.\nIt picks tokens one by one by probability and joins them."),
       ("1-2", "It {r:picks by probability}, so unlikely words are sometimes chosen.\nThe temperature setting changes how much answers vary."),
       ("1-3", "With pretraining alone, it only continues text.\nTuning makes it {r:answer by following instructions}.")])

s = deck.slide(T)   # quiz / answers: no summary, so no band and no bullet
s.heading("Answers (1-4 to 1-6)")
qa(s, [("1-4", "Producing plausible content that is false or has no basis.\ne.g., nonexistent references or numbers; also new or detailed topics."),
       ("1-5", "Search by title, author, journal, and DOI; open the original and check it.\nIf not found or the content differs, don't use it: \"{r:needs checking}\"."),
       ("1-6", "Check the terms and settings: is your input used for training?\nAlso check your organization's rules; {r:if unsure, don't enter it}.")])

NOTES = load_notes(HERE / "notes.md")
for i, sl in enumerate(deck.slides, 1):
    if i in NOTES:
        sl.notes(NOTES[i])
OUT.parent.mkdir(parents=True, exist_ok=True)
deck.save(OUT, title=T, author=AUTHOR)
