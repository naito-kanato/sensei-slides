# Sources of the images in this folder

The images in this folder are pages of the following paper, rendered from the PDF at 400 dpi (only the pages the slides use).
To keep the files small, everything except the parts that `../figs.py` cuts out was blanked to white.
`../figs.py` cuts the figures out of these pages, adds labels, and writes them to `figs/`; the slides use them from there.

- B. P. Abbott et al. (LIGO Scientific Collaboration and Virgo Collaboration),
  "Observation of Gravitational Waves from a Binary Black Hole Merger",
  *Physical Review Letters* **116**, 061102 (2016). DOI: [10.1103/PhysRevLett.116.061102](https://doi.org/10.1103/PhysRevLett.116.061102)
- License: [Creative Commons Attribution 3.0 (CC BY 3.0)](https://creativecommons.org/licenses/by/3.0/).
  The paper states that it may be reused, in whole or in part, without permission, provided the authors, title, journal and DOI are cited.

| File | Page |
|---|---|
| `p02.png` | p.2 (Fig. 1) |
| `p04.png` | p.4 (Fig. 3) |
| `p06.png` | p.6 (Fig. 4) |

## Which figure is used on which slide

| Slide | Figure (`figs/`) | Original figure | Changes besides cropping |
|---|---|---|---|
| 6 | `s06.png` | p.4, Fig. 3(b) (strain noise of the H1 and L1 detectors) | Enlarged 1.5x; the panel letter (b) removed; a one-line reading guide added |
| 7 | `s07.png` | p.4, Fig. 3(a) (map of the two sites) | Enlarged 3.6x; the panel letter (a) removed; the site names added |
| 8 | `s08.png` | p.2, Fig. 1, top row, right panel (L1, with H1 shifted and inverted on top) | Enlarged 1.5x; the strain ticks of the left panel and the time axis of the bottom row joined on; the axis name added |
| 9 | `s09.png` | p.2, Fig. 1, bottom row, left panel (H1 time–frequency map) | Enlarged 1.5x; the color bar left out; a title and the label "chirp" added |
| 12 | `s12.png` | p.6, Fig. 4, right panel (result of the binary coalescence search and its background) | Enlarged 1.7x; the label "23.6" added |

The other figures drawn by `../figs.py` (the timeline on slide 2, the Michelson interferometer on slide 4, which was redrawn in simplified form from Fig. 3, the time slides on slide 11, and the bar chart of the masses on slide 14) were drawn in this repository based on the paper.
