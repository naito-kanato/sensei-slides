"""figkit の図に貼った資料の図（論文の図の切り出し）の文字の大きさを、save が RasterFontPt に書き、組む時点と描画の検査が置いた大きさで見る。
見本のゼミで、論文の図を figkit の図に貼って大きな注記を足したため、MinFontPt（注記の 14pt）だけが記録され、論文の図の 7pt ほどの字が
どの検査にもかからず、採点者2人が「投影で読めない」と減点した。"""
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "examples" / "zemi" / "src" / "p04.png"


def _paper_fig(tmp_path, w_in, name):
    from figkit import blank, save
    im = np.asarray(Image.open(PAGE).convert("RGB"))
    h, w = im.shape[:2]
    a = im[int(h * 0.08):int(h * 0.55), int(w * 0.08):int(w * 0.80)]      # Fig. 3 のあたり（軸・目盛りの文字を含む）
    f, ax = blank(w_in, w_in * a.shape[0] / a.shape[1])
    ax.imshow(a, extent=(0, 1, 0, 1), aspect="auto")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.text(0.5, 0.5, "注記", fontsize=16)
    p = tmp_path / name
    save(f, p)
    return p


def test_pasted_paper_figure_records_its_text_size(tmp_path):
    small = _paper_fig(tmp_path, 3.0, "small.png")
    big = _paper_fig(tmp_path, 8.0, "big.png")
    rs = float(Image.open(small).text["RasterFontPt"])
    rb = float(Image.open(big).text["RasterFontPt"])
    assert Image.open(small).text.get("MinFontPt")     # 注記の記録はあるが、貼った図の字は別に測る
    assert rs < 12                           # 小さく貼ると 12pt を切る
    assert rb / rs > 2


def test_build_warns_when_the_pasted_paper_text_is_small(tmp_path):
    from zemi import Deck
    small = _paper_fig(tmp_path, 3.0, "small.png")
    deck = Deck(workdir=tmp_path / "build")
    s = deck.slide("t", summary="論文の図")
    s.heading("論文の図")
    s.figure_beside(small)
    notes = " ".join(t for _, t in deck._notes)
    assert "資料の図の文字が小さい" in notes
