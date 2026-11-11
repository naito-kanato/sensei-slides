"""これまでのデッキで描いた図の一覧（カタログ）を作る。新しい図を描く前に見て、使い回せる図・型を探す。

    python catalog.py <_work フォルダ> <出力の接頭辞>
    例) python catalog.py "_work" "_work/figure-catalog"   → _work/figure-catalog-1.jpg, -2.jpg ...

各デッキの figs/*.png をデッキごとに並べ、サムネイルの下に「ファイル名 ← figs.py の関数名」を書く。
関数名が分かれば、その figs.py から関数をコピーするか、importlib で読み込んで流用できる（references/series.md 参照）。
よく使う形は figlib.py（図の型）にもある。
"""
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT = Path(r"C:\Windows\Fonts\meiryo.ttc")


def font(size):
    try:
        return ImageFont.truetype(str(FONT), size)
    except OSError:
        return ImageFont.load_default()


def func_map(figs_py: Path) -> dict:
    """figs.py の中で 'xxx.png' を保存している関数名を探す（直前の def f_...）。"""
    if not figs_py.exists():
        return {}
    out, current = {}, None
    for line in figs_py.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\s*def (f_\w+)\(", line)
        if m:
            current = m.group(1)
        for name in re.findall(r"""["']([\w\-.]+\.png)["']""", line):
            if current and name not in out:
                out[name] = current
    return out


def main(work, prefix, cols=6, tw=300, th=210, page_h=2400):
    work = Path(work)
    decks = [d for d in sorted(work.iterdir()) if d.is_dir() and (d / "figs").is_dir()]
    blocks = []
    for d in decks:
        files = sorted((d / "figs").glob("*.png"))
        if files:
            fmap = {}
            for f in [d / "figs.py", *sorted(d.glob("figs_[0-9].py"))]:   # 図の担当が2人なら figs_1.py・figs_2.py
                fmap.update(func_map(f))
            blocks.append((d.name, files, fmap))
    pages, cur, y = [], [], 0
    for name, files, fmap in blocks:
        h = 46 + ((len(files) + cols - 1) // cols) * (th + 44)
        if cur and y + h > page_h:
            pages.append(cur); cur, y = [], 0
        cur.append((name, files, fmap)); y += h
    if cur:
        pages.append(cur)
    W = cols * (tw + 14) + 14
    for pi, page in enumerate(pages, 1):
        H = sum(46 + ((len(f) + cols - 1) // cols) * (th + 44) for _, f, _ in page) + 10
        sheet = Image.new("RGB", (W, H), "white")
        dr = ImageDraw.Draw(sheet)
        y = 6
        for name, files, fmap in page:
            dr.text((14, y), f"■ {name}（{len(files)}枚）  _work/{name}/figs/", fill="#215F99", font=font(22))
            y += 40
            for k, f in enumerate(files):
                r, c = divmod(k, cols)
                x, yy = 14 + c * (tw + 14), y + r * (th + 44)
                try:
                    im = Image.open(f).convert("RGB")
                    im.thumbnail((tw, th))
                    sheet.paste(im, (x + (tw - im.width) // 2, yy + (th - im.height) // 2))
                except OSError:
                    pass
                dr.rectangle([x, yy, x + tw, yy + th], outline="#BBBBBB")
                fn = fmap.get(f.name, "")
                dr.text((x, yy + th + 4), f.stem, fill="#222222", font=font(14))
                if fn:
                    dr.text((x, yy + th + 22), f"← {fn}", fill="#666666", font=font(12))
            y += ((len(files) + cols - 1) // cols) * (th + 44) + 6
        out = f"{prefix}-{pi}.jpg"
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        sheet.save(out, quality=82)
        print(out, sheet.size)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):   # パイプで走らせると日本語の Windows では cp932 になり、✔ や珍しい字で落ちる
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    main(sys.argv[1], sys.argv[2])
