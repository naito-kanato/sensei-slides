"""書き出したスライド画像(slide-XX.png)を一覧画像(コンタクトシート)にまとめる。

    python grid.py <画像フォルダ> <出力の接頭辞> [列数=2] [1枚あたり=6] [サムネ幅=800]
"""
import glob
import os
import re
import sys

from PIL import Image, ImageDraw


def main(src, prefix, cols=2, per=6, tw=800):
    files = sorted(glob.glob(os.path.join(src, "slide-*.png")))
    # 前回の一覧（同じ接頭辞の <prefix>-N.jpg）を消す。枚数が減ったとき古いシートが残らないように
    pat = re.compile(re.escape(os.path.basename(prefix)) + r"-\d+\.jpg$")
    for old in glob.glob(glob.escape(prefix) + "-*.jpg"):
        if pat.match(os.path.basename(old)):
            os.remove(old)
    for gi in range(0, len(files), per):
        chunk = files[gi:gi + per]
        ims = [Image.open(f).convert("RGB") for f in chunk]
        th = int(tw * ims[0].height / ims[0].width)
        rows = (len(ims) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * (tw + 10) + 10, rows * (th + 34) + 10), "white")
        d = ImageDraw.Draw(sheet)
        for k, (f, im) in enumerate(zip(chunk, ims)):
            r, c = divmod(k, cols)
            x, y = 10 + c * (tw + 10), 10 + r * (th + 34)
            d.text((x, y), os.path.basename(f), fill="black")
            sheet.paste(im.resize((tw, th)), (x, y + 20))
            d.rectangle([x - 1, y + 19, x + tw, y + 20 + th], outline="gray")
        out = f"{prefix}-{gi // per + 1}.jpg"
        sheet.save(out, quality=85)
        print(out)


if __name__ == "__main__":
    a = sys.argv
    main(a[1], a[2], *(int(v) for v in a[3:6]))
