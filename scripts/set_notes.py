"""読み上げ原稿（notes.md）を pptx の発表者ノートに書き込む。

    python set_notes.py "<資料名>_スライド.pptx" <work>/notes.md

notes.md の形（「## スライド番号」ごとに1枚分。空行で段落、「※」で始まる行は読まない補足）:

    ## 2
    最初に、少し挑発的な問いから入ります。AI の答えを、そのまま使ったことはありますか。

    比べるために、……

    ※（資料外の補足）……

build.py から使うとき（ビルドし直してもノートが元に戻らないように、保存の直前で上書きする）:

    from set_notes import load_notes
    for i, s in enumerate(deck.slides, 1):
        if i in NOTES: s.notes(NOTES[i])
"""
import re
import sys
from pathlib import Path


def load_notes(path):
    """notes.md → {スライド番号: 原稿}。段落は空行1つ＝改行1つにまとめる（原稿HTMLで1段落ずつ表示される）。"""
    text = Path(path).read_text(encoding="utf-8")
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    notes = {}
    for m in re.finditer(r"^##\s*(\d+)\s*$(.*?)(?=^##\s*\d+\s*$|\Z)", text, flags=re.S | re.M):
        paras = [" ".join(p.split("\n")).strip() for p in re.split(r"\n\s*\n", m.group(2).strip())]
        notes[int(m.group(1))] = "\n".join(p for p in paras if p)
    return notes


def main():
    from pptx import Presentation
    pptx, md = Path(sys.argv[1]), Path(sys.argv[2])
    notes = load_notes(md)
    prs = Presentation(str(pptx))
    n = len(prs.slides)
    for i, sl in enumerate(prs.slides, 1):
        if i in notes:
            sl.notes_slide.notes_text_frame.text = notes[i]
    missing = [i for i in range(1, n + 1) if i not in notes]
    extra = [i for i in notes if i > n]
    prs.save(str(pptx))
    print(f"saved {pptx} (notes {len(notes)} / {n} slides)"
          + (f"  原稿なし: {missing}" if missing else "") + (f"  余分: {extra}" if extra else ""))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):   # パイプで走らせると日本語の Windows では cp932 になり、✔ や珍しい字で落ちる
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    main()
