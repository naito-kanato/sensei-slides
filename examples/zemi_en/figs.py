"""English version of the seminar sample (paper review: first observation of gravitational waves): figures we draw ourselves.
The paper's figures are in ../zemi/paper_figs/ (cropped from the paper; sources in ATTRIBUTION.md).

    python figs.py            # write all figures to figs/
    python figs.py michelson  # redraw only some (function name without the f_ prefix)

Each figure is drawn at the size it fills on the slide (5.6-6 in wide, 3.5-4.5 in tall) and placed at that width,
so the text in the figure stays at 14 pt.
"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle

SKILL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILL / "scripts"))
from figkit import COL, arrow, blank, box, save  # noqa: E402

OUT = Path(__file__).parent / "figs"
FS = 14  # labels in figures


def f_strain():
    """As a gravitational wave passes, particles on a ring stretch and squeeze in turn (+ polarization). Thin double arrows show the stretch."""
    f, ax = blank(6.0, 3.3)
    th = np.linspace(0, 2 * np.pi, 13)[:-1]
    ring = np.linspace(0, 2 * np.pi, 100)
    r, cy = 0.72, 1.9
    for k, (sx, sy, name) in enumerate([(1, 1, "Before"), (1.25, 0.8, "1/4 period"), (0.8, 1.25, "3/4 period")]):
        cx = 1.0 + k * 2.0
        ax.plot(cx + r * np.cos(ring), cy + r * np.sin(ring), color=COL.gray, lw=1.0, ls="--")
        ax.scatter(cx + r * sx * np.cos(th), cy + r * sy * np.sin(th), s=55, color=COL.blue, zorder=3)
        ax.text(cx, 0.3, name, ha="center", fontsize=FS)
        if sx > 1:      # stretched horizontally
            arrow(ax, (cx - 0.55, cy), (cx + 0.55, cy), color=COL.gray, style="<|-|>", lw=1.0, ms=12)
        elif sy > 1:    # stretched vertically
            arrow(ax, (cx, cy - 0.55), (cx, cy + 0.55), color=COL.gray, style="<|-|>", lw=1.0, ms=12)
    ax.set_xlim(0, 6.0); ax.set_ylim(0, 3.3)
    save(f, OUT / "strain.png")


def f_michelson():
    """Michelson interferometer (drawn after the paper's Fig. 3; arm cavities and recycling mirrors omitted)."""
    s = 1.2   # the earlier 4.8 x 3.8 in coordinates scaled by 1.2
    f, ax = blank(4.8 * s, 3.8 * s)
    bx, by = 1.5 * s, 1.2 * s
    ax.plot([0.55 * s, 4.3 * s], [by, by], color=COL.red, lw=2.4)              # laser -> x arm
    ax.plot([bx, bx], [by, 3.4 * s], color=COL.red, lw=2.4)                    # y arm
    ax.plot([bx, bx], [0.35 * s, by], color=COL.red, lw=1.6, ls="--")          # to the detector
    ax.plot([bx - 0.26, bx + 0.26], [by - 0.26, by + 0.26], color=COL.ink, lw=3)   # beam splitter
    ax.add_patch(Rectangle((4.3 * s, by - 0.36), 0.19, 0.72, fc=COL.pale, ec=COL.ink, lw=1.4))   # x mirror
    ax.add_patch(Rectangle((bx - 0.36, 3.4 * s), 0.72, 0.19, fc=COL.pale, ec=COL.ink, lw=1.4))   # y mirror
    ax.add_patch(Rectangle((0.0, by - 0.26), 0.66, 0.52, fc=COL.ink, ec=COL.ink))
    ax.text(0.33, by - 0.48, "Laser", ha="center", va="top", fontsize=FS)
    ax.text(bx + 0.14, 0.33, "Photodetector", ha="left", va="center", fontsize=FS)
    ax.text(4.3 * s + 0.1, by + 0.5, "Mirror", ha="center", fontsize=FS)
    arrow(ax, (2.0 * s, 0.75 * s), (4.25 * s, 0.75 * s), color=COL.ink, style="<|-|>")
    ax.text(3.1 * s, 0.42 * s, r"$L_x = 4$ km", ha="center", fontsize=FS)
    arrow(ax, (2.0 * s, 1.65 * s), (2.0 * s, 3.35 * s), color=COL.ink, style="<|-|>")
    ax.text(2.15 * s, 2.5 * s, r"$L_y = 4$ km", ha="left", va="center", fontsize=FS)
    ax.set_xlim(-0.1, 4.8 * s); ax.set_ylim(0.0, 3.8 * s)
    save(f, OUT / "michelson.png")


def f_pulsar():
    """Binary pulsar sketch: the orbit shrinks (energy lost to gravitational waves). Sizes are schematic."""
    f, ax = blank(5.6, 4.0)
    cx, cy = 2.8, 1.85
    ring = np.linspace(0, 2 * np.pi, 200)
    ax.plot(cx + 1.4 * np.cos(ring), cy + 1.4 * np.sin(ring), color=COL.gray, lw=1.0, ls="--")
    ax.plot(cx + 0.85 * np.cos(ring), cy + 0.85 * np.sin(ring), color=COL.lblue, lw=1.6)
    ax.add_patch(plt.Circle((cx + 0.85, cy), 0.18, fc=COL.red, ec="none"))
    ax.add_patch(plt.Circle((cx - 0.85, cy), 0.13, fc=COL.blue, ec="none"))
    ax.text(cx + 1.55, cy, "Pulsar", ha="left", va="center", fontsize=FS)
    ax.text(cx - 1.55, cy, "Companion", ha="right", va="center", fontsize=FS)
    th = 0.9
    arrow(ax, (cx + 1.4 * np.cos(th), cy + 1.4 * np.sin(th)), (cx + 0.85 * np.cos(th) + 0.02, cy + 0.85 * np.sin(th) + 0.02),
          color=COL.red, lw=1.6)
    ax.text(cx + 1.5, cy + 1.55, "Orbit shrinks", ha="center", va="bottom", fontsize=FS)
    ax.set_xlim(0, 5.6); ax.set_ylim(0, 4.0)
    save(f, OUT / "pulsar.png")


def f_power():
    """Light power inside the detector (values from the paper's Sec. III): laser 20 W -> beam splitter 700 W -> each arm 100 kW."""
    f, ax = blank(5.6, 4.5)
    box(ax, 0.1, 3.5, 2.9, 0.85, "Laser 20 W", fc=COL.light)
    box(ax, 0.1, 1.9, 2.9, 0.85, "Beam splitter 700 W", fc=COL.pale)
    box(ax, 0.1, 0.3, 2.9, 0.85, "Each arm 100 kW", fc=COL.pale)
    arrow(ax, (1.55, 3.45), (1.55, 2.8), color=COL.lblue)   # red is the color of conclusions in the text, so arrows are light blue
    arrow(ax, (1.55, 1.85), (1.55, 1.2), color=COL.lblue)
    ax.text(1.85, 3.12, "Power recycling", ha="left", va="center", fontsize=FS)
    ax.text(1.85, 1.52, "Arm cavities", ha="left", va="center", fontsize=FS)
    ax.set_xlim(0, 5.6); ax.set_ylim(0, 4.5)
    save(f, OUT / "power.png")


def f_scale():
    """Size and separation of the binary (to scale, equal masses): two circles of radius 105 km
    (sum of radii 210 km = one diameter), centers 350 km apart."""
    k = 0.01  # in/km
    f, ax = blank(5.8, 3.9)
    x0, y0 = 1.12, 2.0
    d, R = 350 * k, 105 * k
    mx = x0 + d / 2
    for x in (x0, x0 + d):
        ax.add_patch(plt.Circle((x, y0), R, fc=COL.blue, ec="none"))
    arrow(ax, (x0 - R, y0 + 1.35), (x0 + R, y0 + 1.35), color=COL.ink, style="<|-|>", lw=1.2)
    ax.text(x0, y0 + 1.5, "Diameter ≳210 km", ha="center", va="bottom", fontsize=FS)
    arrow(ax, (x0, y0 - 1.45), (x0 + d, y0 - 1.45), color=COL.red, style="<|-|>", lw=1.6)
    ax.text(mx, y0 - 1.7, "Center separation ≃350 km", ha="center", va="top", fontsize=FS)
    ax.set_xlim(0, 5.8); ax.set_ylim(0, 3.9)
    save(f, OUT / "scale.png")


def f_timeshift():
    """Time-shift sketch: the same signal on top of random noise in H1 and L1. Shifting L1 makes the signals no longer line up."""
    rng = np.random.default_rng(7)
    f, ax = blank(5.8, 4.6)
    n = 300
    x = np.linspace(0.9, 5.6, n)

    def noise():
        v = rng.normal(0, 1, n)
        return np.convolve(v, np.ones(4) / 4, mode="same") * 0.11

    def burst(c):
        u = (x - c) / 0.4
        return 0.8 * np.exp(-u ** 2) * np.sin(13 * (x - c))
    rows = [(3.9, "H1", 3.2), (2.4, "L1", 3.2), (0.9, "L1", 4.3)]
    for yy, lab, c in rows:
        ax.plot(x, yy + noise() + burst(c), color=COL.blue, lw=1.2)
        ax.plot([0.9, 5.6], [yy - 0.55] * 2, color=COL.gray, lw=0.6)
    ax.plot([3.2, 3.2], [-0.2, 4.6], color=COL.red, lw=1.0, ls="--")
    ax.text(0.8, 3.9, "H1", ha="right", va="center", fontsize=FS)
    ax.text(0.8, 2.4, "L1", ha="right", va="center", fontsize=FS)
    ax.text(0.8, 0.9, "L1\nshifted", ha="right", va="center", fontsize=FS)
    arrow(ax, (3.25, -0.12), (4.25, -0.12), color=COL.red, lw=1.6)
    ax.set_xlim(0, 5.8); ax.set_ylim(-0.3, 4.6)
    save(f, OUT / "timeshift.png")


if __name__ == "__main__":
    names = sys.argv[1:] or [k[2:] for k in list(globals()) if k.startswith("f_")]
    for nm in names:
        globals()["f_" + nm]()
