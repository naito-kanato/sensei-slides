"""図のフォルダ（figs/*.png）を一覧画像にまとめて、まとめて目視確認する。

    python figgrid.py <図のフォルダ> <出力.jpg> [ファイル名に含まれる語 ...]
    例) python figgrid.py figs render/figs_grid.jpg            # 全部
        python figgrid.py figs render/figs_grid.jpg kondo he_vp  # 直した図だけ

図を描いたら・直したら毎回これで見る。ラベルと線の重なり、□（文字化け）、はみ出しがよく起きる。
"""
import glob
import os
import sys

from PIL import Image, ImageDraw


def main(src, out, keys, cols=4, tw=520):
    files = sorted(glob.glob(os.path.join(src, "*.png")))
    if keys:
        files = [f for f in files if any(k in os.path.basename(f) for k in keys)]
    if not files:
        print("no images"); return
    cells = []
    for f in files:
        im = Image.open(f).convert("RGB")
        cells.append((f, im.resize((tw, int(tw * im.height / im.width)))))
    rows = [cells[i:i + cols] for i in range(0, len(cells), cols)]
    H = sum(max(c[1].height for c in r) + 24 for r in rows)
    sheet = Image.new("RGB", (cols * (tw + 10) + 10, H), "white")
    d = ImageDraw.Draw(sheet)
    y = 0
    for r in rows:
        x = 10
        for f, im in r:
            d.text((x, y + 2), os.path.basename(f), fill="black")
            sheet.paste(im, (x, y + 18))
            x += tw + 10
        y += max(c[1].height for c in r) + 24
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    sheet.save(out, quality=88)
    print(f"{out} ({len(files)} figs)")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3:])
