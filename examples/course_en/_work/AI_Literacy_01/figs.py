"""Course sample, Lecture 1 "What Does Generative AI Do?": figures (all drawn here; English version of examples/course/_work/AI活用講座_01/figs.py).

    python figs.py              # write all figures to figs/
    python figs.py temperature  # redraw only some (function name without the f_ prefix)

Figures are drawn to fill the space to the right of the body text (5.4-6 in wide, 3-4.3 in tall) and placed at the
width they were drawn. Figure text stays at 14pt or larger.
"""
import sys
from pathlib import Path

import numpy as np
from matplotlib.patches import Rectangle

SKILL = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(SKILL / "scripts"))
from figkit import COL, arrow, blank, box, fig, save  # noqa: E402

OUT = Path(__file__).parent / "figs"
FS = 14
WORDS = ["sunny", "rainy", "cloudy", "snowy"]
PROBS = [0.42, 0.25, 0.18, 0.06]          # example for explanation (not values from a real model)


def f_next_token():
    """Candidates and probabilities for the token after "Tomorrow's weather is" (example for explanation)"""
    f, ax = fig(5.8, 4.3)
    words, probs = WORDS[::-1], PROBS[::-1]
    colors = [COL.gray, COL.gray, COL.gray, COL.blue]
    ax.barh(words, probs, color=colors, height=0.6)
    for w, p in zip(words, probs):
        ax.text(p + 0.01, w, f"{p:.2f}", va="center", fontsize=FS)
    ax.set_xlim(0, 0.55)
    ax.set_xlabel("Probability of coming next", fontsize=FS)
    ax.set_title("Next word after \"Tomorrow's weather is\"", fontsize=FS)
    ax.tick_params(labelsize=FS)
    save(f, OUT / "next_token.png")


def f_tokens():
    """ "Tomorrow's weather is sunny" split into tokens (the split is an example; it differs by model)"""
    W, H = 6.0, 2.9
    f, ax = blank(W, H)
    ax.text(W / 2, 2.45, "Tomorrow's weather is sunny", ha="center", va="center", fontsize=20)
    arrow(ax, (W / 2, 2.1), (W / 2, 1.56))
    toks = ["Tomorrow", "'s", "weather", "is", "sunny"]
    ws = [1.55, 0.55, 1.3, 0.55, 1.1]
    gap = 0.14
    x = (W - sum(ws) - gap * (len(ws) - 1)) / 2
    for t, w in zip(toks, ws):
        box(ax, x, 0.66, w, 0.72, t, fs=18)
        x += w + gap
    ax.text(W / 2, 0.24, "5 tokens", ha="center", va="center", fontsize=16, color=COL.blue)
    save(f, OUT / "tokens.png")


def f_params():
    """Number of parameters: GPT-2 (Radford et al., 2019) and GPT-3 (Brown et al., 2020)"""
    f, ax = fig(4.4, 3.2)
    names, vals = ["GPT-2\n(2019)", "GPT-3\n(2020)"], [1.5, 175]
    ax.bar(names, vals, color=[COL.gray, COL.blue], width=0.55)
    for x, v in zip([0, 1], ["1.5B", "175B"]):
        ax.text(x, vals[x] + 5, v, ha="center", fontsize=FS)
    ax.set_ylim(0, 205)
    ax.set_ylabel("Parameters (billions)", fontsize=FS)
    ax.tick_params(labelsize=FS)
    save(f, OUT / "params.png")


def f_temperature():
    """How the probability of being picked changes with temperature (slide 2's probabilities renormalized over the 4 candidates, computed from p^(1/T))"""
    p = np.array(PROBS) / sum(PROBS)
    f, ax = fig(5.8, 4.3)
    x = np.arange(len(WORDS))
    temps = [(0.5, COL.blue), (1.0, COL.gray), (2.0, COL.orange)]   # red is the color of the body's conclusion, so not used
    w = 0.26
    for k, (T, c) in enumerate(temps):
        q = p ** (1 / T)
        q /= q.sum()
        ax.bar(x + (k - 1) * w, q, width=w, color=c)
        ax.text(0 + (k - 1) * w, q[0] + 0.015, f"{T:g}", ha="center", va="bottom", fontsize=FS, color=c)   # temperature above the "sunny" bars instead of a legend
    ax.text(0.75, 0.66, "Number above bar: temperature", ha="left", va="center", fontsize=FS)
    ax.set_xticks(x, WORDS)
    ax.set_ylim(0, 0.75)
    ax.set_ylabel("Probability of being picked", fontsize=FS)
    ax.tick_params(labelsize=FS)
    save(f, OUT / "temperature.png")


def f_fabricated():
    """Share of references cited by ChatGPT that do not exist (Walters & Wilder, Sci. Rep. 13, 14045 (2023))"""
    f, ax = fig(5.4, 4.3)
    ax.bar(["GPT-3.5", "GPT-4"], [55, 18], color=[COL.red, COL.blue], width=0.55)
    for x, v in zip([0, 1], [55, 18]):
        ax.text(x, v + 2, f"{v}%", ha="center", fontsize=FS)
    ax.set_ylim(0, 70)
    ax.set_ylabel("Nonexistent references (%)", fontsize=FS)
    ax.tick_params(labelsize=FS)
    save(f, OUT / "fabricated.png")


def f_cutoff():
    """The span of training data, its cutoff, and the time after it (GPT-4: September 2021; OpenAI, 2023)"""
    k = 1.0
    f, ax = blank(5.2 * k, 2.6 * k)
    ax.add_patch(Rectangle((0.2 * k, 1.0 * k), 3.0 * k, 0.7 * k, fc=COL.pale, ec=COL.ink, lw=1.5))
    ax.text(1.7 * k, 1.35 * k, "Training data", ha="center", va="center", fontsize=16)
    ax.plot([3.2 * k, 3.2 * k], [0.75 * k, 2.0 * k], color=COL.red, lw=2.5)
    ax.text(3.2 * k, 2.25 * k, "Cutoff", ha="center", va="center", fontsize=16, color=COL.red)
    ax.text(4.15 * k, 1.35 * k, "Unknown", ha="center", va="center", fontsize=16, color=COL.gray)
    arrow(ax, (0.2 * k, 0.55 * k), (5.05 * k, 0.55 * k))
    ax.text(4.95 * k, 0.2 * k, "Now", ha="center", va="center", fontsize=16)
    save(f, OUT / "cutoff.png")


def f_cot():
    """Accuracy on math word problems (GSM8K): answer-only examples 17.9%, examples with written-out reasoning 56.9% (Wei et al., NeurIPS 2022, Table 2, PaLM 540B)"""
    f, ax = fig(5.4, 4.3)
    names, vals = ["Answer-only\nexamples", "Examples with\nreasoning"], [17.9, 56.9]
    ax.bar(names, vals, color=[COL.gray, COL.blue], width=0.55)
    for x, v in zip([0, 1], vals):
        ax.text(x, v + 2, f"{v}%", ha="center", fontsize=FS)
    ax.set_ylim(0, 70)
    ax.set_ylabel("Accuracy (%)", fontsize=FS)
    ax.set_title("Math word problems", fontsize=FS)
    ax.tick_params(labelsize=FS)
    save(f, OUT / "cot.png")


def f_dont_input():
    """Three things to stop for before input (based on the Personal Information Protection Commission's advisory on generative AI services, 2023)"""
    s = 1.15   # the earlier 4.2 x 3.6 in coordinates scaled by 1.15
    f, ax = blank(4.2 * s, 3.6 * s)
    ax.text(2.1 * s, 3.3 * s, "Check before input", ha="center", va="center", fontsize=18, color=COL.red)
    for k, t in enumerate(["Personal information", "Confidential documents", "Unpublished data"]):
        box(ax, 0.3 * s, (2.25 - k * 0.95) * s, 3.6 * s, 0.7 * s, t, fc="white", ec=COL.ink, fs=18)
    save(f, OUT / "dont_input.png")


if __name__ == "__main__":
    names = sys.argv[1:] or [k[2:] for k in list(globals()) if k.startswith("f_")]
    for nm in names:
        globals()["f_" + nm]()
