"""README と使い方のページに載せる見本の縮小画像（docs/*-slides-*.jpg と、型の見本帳の docs/structures.jpg）を、見本の描画結果（render/slide-NN.png）から作り直す。
原稿のページの画面（docs/*-notes.jpg）は、Edge が入っていればヘッドレスで写して、見出しの帯と3枚目を切り出す。
見本を組み直したら（make_deck.py のあと）これを走らせる。

    python tools/make_docs_images.py
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
COURSE = ROOT / "examples" / "course" / "_work" / "AI活用講座_01" / "render"
ZEMI = ROOT / "examples" / "zemi" / "render"
STRUCT = ROOT / "examples" / "structures" / "render"
# 型の見本帳から載せる枚（スライド番号, 名前）
STRUCT_TILES = [(2, "前提 ⇒ 帰結"), (3, "ラベル＋説明"), (4, "横の矢印で展開"), (5, "条件の場合分け"), (6, "問い → 答え"), (7, "番号の手順"),
                (8, "縦の矢印で結論へ"), (10, "並列カード"), (11, "段違いの順序"), (12, "循環"), (14, "前後"), (15, "2つ並べた図")]
PAD, GAP = 15, 14
JOBS = [  # (出力, 描画のフォルダ, スライド番号, 列の数, 全体の幅)
    ("course-slides-1.jpg", COURSE, range(1, 5), 2, 1648),
    ("course-slides-2.jpg", COURSE, range(5, 16), 3, 1654),
    ("zemi-slides-1.jpg", ZEMI, range(1, 5), 2, 1648),
    ("zemi-slides-2.jpg", ZEMI, range(5, 17), 3, 1654),
]
# README の一番上の動く画像（講座と発表の見本を交互に）：(描画のフォルダ, スライド番号, 上の帯の文字)
DEMO = [(COURSE, 1, "講座：AI が講師の連続講座"), (COURSE, 3, "講座：結論の一文と図"), (COURSE, 6, "講座：数値はグラフで"),
        (COURSE, 12, "講座：確認問題"), (ZEMI, 1, "発表：論文紹介"), (ZEMI, 8, "発表：論文の図と数値"),
        (ZEMI, 13, "発表：結果と赤丸"), (ZEMI, 15, "発表：想定質問と回答案")]


def demo_gif(out: Path, width: int = 800, bar: int = 40, ms: int = 1800):
    """DEMO の枚を、上に短い帯を付けて GIF にする（大きさは 2〜3 MB 以内を目安に、幅 800）。"""
    h = round(width * 9 / 16)
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/YuGothB.ttc", 22)
    except OSError:
        font = ImageFont.load_default()
    frames = []
    for folder, n, label in DEMO:
        f = folder / f"slide-{n:02d}.png"
        if not f.exists():
            continue
        im = Image.new("RGB", (width, h + bar), "white")
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, width, bar], fill=(31, 56, 100))
        d.text((16, bar // 2), label, fill="white", font=font, anchor="lm")
        sl = Image.open(f).convert("RGB").resize((width, h), Image.LANCZOS)
        im.paste(sl, (0, bar))
        d.rectangle([0, bar, width - 1, bar + h - 1], outline=(200, 200, 200))
        frames.append(im.convert("P", palette=Image.ADAPTIVE, colors=128))
    if frames:
        frames[0].save(out, save_all=True, append_images=frames[1:], duration=ms, loop=0, optimize=True)



def tile(folder: Path, nums, cols: int, width: int) -> Image.Image:
    cw = (width - 2 * PAD - (cols - 1) * GAP) // cols
    ch = round(cw * 9 / 16)
    rows = math.ceil(len(nums) / cols)
    im = Image.new("RGB", (width, 2 * PAD + rows * ch + (rows - 1) * GAP), "white")
    d = ImageDraw.Draw(im)
    for k, n in enumerate(nums):
        src = Image.open(folder / f"slide-{n:02d}.png").convert("RGB").resize((cw, ch), Image.LANCZOS)
        x, y = PAD + (k % cols) * (cw + GAP), PAD + (k // cols) * (ch + GAP)
        im.paste(src, (x, y))
        d.rectangle((x - 1, y - 1, x + cw, y + ch), outline=(200, 200, 200))
    return im


def labeled(folder: Path, tiles, cols: int = 3, width: int = 1654, label_h: int = 44) -> Image.Image:
    """名前つきの一覧（型の見本帳）。各枚の上に型の名前を太字で。"""
    cw = (width - 2 * PAD - (cols - 1) * GAP) // cols
    ch = round(cw * 9 / 16)
    rows = math.ceil(len(tiles) / cols)
    cell = label_h + ch
    im = Image.new("RGB", (width, 2 * PAD + rows * cell + (rows - 1) * GAP), "white")
    d = ImageDraw.Draw(im)
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/YuGothB.ttc", 30)
    except OSError:
        font = ImageFont.load_default()
    for k, (n, name) in enumerate(tiles):
        x, y = PAD + (k % cols) * (cw + GAP), PAD + (k // cols) * (cell + GAP)
        d.text((x, y + 2), name, font=font, fill=(30, 30, 30))
        src = Image.open(folder / f"slide-{n:02d}.png").convert("RGB").resize((cw, ch), Image.LANCZOS)
        im.paste(src, (x, y + label_h))
        d.rectangle((x - 1, y + label_h - 1, x + cw, y + label_h + ch), outline=(200, 200, 200))
    return im


EDGE = [Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"), Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe")]
NOTES = [("course-notes.jpg", ROOT / "examples" / "course" / "AI活用講座" / "01_生成AIは何をしているか_原稿.html"),
         ("zemi-notes.jpg", ROOT / "examples" / "zemi" / "重力波の初観測_原稿.html")]


def notes_shots():
    """原稿のページを 1360×1700 で写し、上の帯（0〜88px）と3枚目のカード（1112〜1630px）をつなぐ。Edge が無ければ飛ばす。"""
    import subprocess
    import tempfile
    edge = next((e for e in EDGE if e.exists()), None)
    if edge is None:
        print("（Edge が無いので原稿のページの画面は作らない）")
        return
    with tempfile.TemporaryDirectory() as td:
        for name, html in NOTES:
            shot = Path(td) / f"shot_{Path(name).stem}.png"   # 1枚ごとに別の名前（同じ名前だと、前の画像を写し違えることがあった）
            subprocess.run([str(edge), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--window-size=1360,1700",
                            "--virtual-time-budget=3000", f"--screenshot={shot}", html.as_uri()], capture_output=True, timeout=120)
            import time
            for _ in range(40):           # Edge は起動役のプロセスがすぐ戻ることがあるので、画像ができるまで待つ
                if shot.exists() and shot.stat().st_size > 0:
                    time.sleep(0.5)
                    break
                time.sleep(0.5)
            if not shot.exists():
                print(f"（{html.name} を写せなかった）")
                continue
            im = Image.open(shot).convert("RGB")
            head, card = im.crop((0, 0, im.width, 88)), im.crop((0, 1112, im.width, 1630))
            out = Image.new("RGB", (im.width, head.height + card.height), "white")
            out.paste(head, (0, 0))
            out.paste(card, (0, head.height))
            out.save(ROOT / "docs" / name, quality=88)
            print(Path("docs") / name)


def main():
    for name, folder, nums, cols, width in JOBS:
        out = ROOT / "docs" / name
        tile(folder, list(nums), cols, width).save(out, quality=88)
        print(out.relative_to(ROOT))
    out = ROOT / "docs" / "structures.jpg"
    labeled(STRUCT, STRUCT_TILES).save(out, quality=88)
    print(out.relative_to(ROOT))
    out = ROOT / "docs" / "demo.gif"
    demo_gif(out)
    print(out.relative_to(ROOT), f"{out.stat().st_size / 1e6:.1f} MB")
    notes_shots()


if __name__ == "__main__":
    main()
