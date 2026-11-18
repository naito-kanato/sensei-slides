"""資料PDF（教科書スキャン・論文）を読むための画像化と、図の切り出し。

  ページを画像化（スキャンPDFは埋め込み画像をそのままの解像度で、見開きは左右に分割）:
    python pdf_pages.py extract 資料.pdf out_dir
      -> out_dir/p01.png, p01_L.png, p01_R.png（見開きのとき）, p01.txt（テキスト層があるとき）

  文だけを頁ごとに（テキスト層のある PDF。1回だけ作り、メインと担当はみなこれを読む。PDF を Read で開かない・読み出しを自分で書かない）:
    python pdf_pages.py text 資料.pdf [out_dir]          -> out_dir（既定は 資料_text/）に pNN.txt と目次 index.md。目次を出す
    python pdf_pages.py text 資料.pdf [out_dir] --pages 3-5   -> その頁の文を出す

  図の切り出し（黄ばんだ紙を白に、余白を自動トリム）:
    python pdf_pages.py crop out_dir/p05_L.png figs/fig7_14.png --box 380 1820 2200 2990
      --box は元画像のピクセル座標 (x0 y0 x1 y1)。--frac を付けると 0〜1 の比率で指定。
      --no-clean で色をそのまま残す（カラー写真など）。

Readツールで半ページ画像を見ると「Multiply coordinates by N」と表示されるので、
画面上の座標×N が元画像のピクセル座標になる。
"""
import argparse
import io
from pathlib import Path

from PIL import Image, ImageChops, ImageOps


def extract(pdf, outdir, dpi=200):
    import pymupdf as fitz
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf)
    for i, page in enumerate(doc, 1):
        text = page.get_text()
        imgs = page.get_images()
        stem = out / f"p{i:02d}"
        if len(text.strip()) < 30 and len(imgs) == 1:  # スキャンページ
            pix = fitz.Pixmap(doc, imgs[0][0])
            if pix.n - pix.alpha >= 4:
                pix = fitz.Pixmap(fitz.csRGB, pix)
            im = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
        else:
            if text.strip():
                Path(f"{stem}.txt").write_text(text, encoding="utf-8")
            pix = page.get_pixmap(dpi=dpi)
            im = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
        im.save(f"{stem}.png")
        w, h = im.size
        msg = f"p{i:02d}: {w}x{h}"
        if w > h * 1.2:  # 見開き
            im.crop((0, 0, w // 2, h)).save(f"{stem}_L.png")
            im.crop((w // 2, 0, w, h)).save(f"{stem}_R.png")
            msg += "  (見開き -> _L/_R)"
        if text.strip():
            msg += f"  text={len(text)}chars"
        print(msg)


def text(pdf, outdir=None, pages=None):
    """テキスト層を頁ごとに pNN.txt へ（画像は作らない）。1回だけ作り、あとの担当はそれを読む。
    コミュニケーション講座の試しで、メイン・地図・設計・制作の4人が同じ PDF を別々に読み、自分で書いた読み出しが文字コードで何度も止まった。
    pages（「3-5」「2,7」）を渡すと、その頁の文を出す（作ったファイルから読む）。"""
    import pymupdf as fitz
    pdf = Path(pdf)
    out = Path(outdir) if outdir else pdf.with_name(pdf.stem + "_text")
    index = out / "index.md"
    if not (index.exists() and index.stat().st_mtime >= pdf.stat().st_mtime):
        out.mkdir(parents=True, exist_ok=True)
        doc = fitz.open(str(pdf))
        rows = []
        for i, page in enumerate(doc, 1):
            t = page.get_text().strip()
            if t:
                (out / f"p{i:02d}.txt").write_text(t + "\n", encoding="utf-8")
            first = next((x.strip() for x in t.splitlines() if x.strip()), "")
            rows.append(f"| {i} | {len(t)} | {first[:40] if t else '（文字なし：スキャンなら extract で画像に）'} |")
        index.write_text(f"# {pdf.name} の頁（{len(rows)}頁。文は pNN.txt）\n\n| 頁 | 字数 | 最初の行 |\n|---|---|---|\n" + "\n".join(rows) + "\n",
                         encoding="utf-8")
        made = True
    else:
        made = False
    if pages:
        want = []
        for part in str(pages).split(","):
            a, _, b = part.partition("-")
            want += list(range(int(a), int(b or a) + 1))
        for n in want:
            f = out / f"p{n:02d}.txt"
            print(f"--- p{n}\n" + (f.read_text(encoding="utf-8").strip() if f.exists() else "（文字なし）"))
        return
    print(("作った" if made else "もうある（作り直さない）") + f"：{out.as_posix()}（頁ごとの文 pNN.txt と目次 index.md）")
    print(index.read_text(encoding="utf-8"))


def clean_scan(im: Image.Image) -> Image.Image:
    """紙の地色を白に飛ばし、線をくっきりさせる（線画・グラフ向け）。"""
    g = ImageOps.grayscale(im)
    hist = g.histogram()
    total = sum(hist)
    acc, paper = 0, 255
    for v in range(255, -1, -1):  # 明るい側から30%の位置を紙の色とみなす
        acc += hist[v]
        if acc > total * 0.3:
            paper = v
            break
    white = max(paper - 12, 60)
    black = 40
    lut = [0 if v <= black else 255 if v >= white else int((v - black) * 255 / (white - black)) for v in range(256)]
    return g.point(lut).convert("RGB")


def trim(im: Image.Image, pad=12) -> Image.Image:
    bg = Image.new(im.mode, im.size, (255, 255, 255))
    diff = ImageChops.difference(im, bg).convert("L").point(lambda v: 255 if v > 40 else 0)
    bbox = diff.getbbox()
    if not bbox:
        return im
    x0, y0, x1, y1 = bbox
    return im.crop((max(0, x0 - pad), max(0, y0 - pad), min(im.width, x1 + pad), min(im.height, y1 + pad)))


def crop(src, dst, box, frac=False, clean=True, do_trim=True):
    im = Image.open(src).convert("RGB")
    if frac:
        box = [box[0] * im.width, box[1] * im.height, box[2] * im.width, box[3] * im.height]
    im = im.crop(tuple(int(v) for v in box))
    if clean:
        im = clean_scan(im)
    if do_trim:
        im = trim(im)
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    im.save(dst)
    print(f"saved {dst} {im.size}")


if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, "reconfigure"):   # パイプで走らせると日本語の Windows では cp932 になり、✔ や珍しい字で落ちる
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("extract"); e.add_argument("pdf"); e.add_argument("outdir"); e.add_argument("--dpi", type=int, default=200)
    c = sub.add_parser("crop"); c.add_argument("src"); c.add_argument("dst")
    c.add_argument("--box", type=float, nargs=4, required=True); c.add_argument("--frac", action="store_true")
    c.add_argument("--no-clean", action="store_true"); c.add_argument("--no-trim", action="store_true")
    t = sub.add_parser("text"); t.add_argument("pdf"); t.add_argument("outdir", nargs="?"); t.add_argument("--pages")
    a = ap.parse_args()
    if a.cmd == "extract":
        extract(a.pdf, a.outdir, a.dpi)
    elif a.cmd == "text":
        text(a.pdf, a.outdir, a.pages)
    else:
        crop(a.src, a.dst, a.box, a.frac, not a.no_clean, not a.no_trim)
