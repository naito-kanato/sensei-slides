"""原稿HTMLで書き出したコメント（<資料名>_コメント.json）を、回答づくりの作業リストにする。

    python comments_read.py --find                                   # *_コメント*.json の候補を新しい順に表示（移さない）
    python comments_read.py --collect GA                             # 講座ID GA のコメントを、ダウンロードから保存先へまとめて移す
    （JSON を指定して読むと、ダウンロードフォルダにある同じ講座IDのコメントを全部、その講座の README の保存先へ移してから読む）
    python comments_read.py "<資料名>_コメント.json" --out <work>/comments
    python comments_read.py <json> --deck "<資料名>_スライド.pptx" --out <dir>   # デッキの場所を指定

- デッキ（pptx と PDF）は JSON に記録された原稿HTMLの場所から探す（<資料名>_原稿.html → <資料名>_スライド.pptx / .pdf）
- スライドの範囲へのコメントは、PDF からその範囲を少し広めに切り抜き、囲んだ範囲に赤枠を描いて
  <out>/c<番号>_s<スライド>.png に保存する（Read で見て、どこを指しているか確かめる）
- 文章へのコメントは、選んだ部分を【】で示し、前後の文脈つきで出す
"""
import argparse
import json
import sys
from pathlib import Path

import pymupdf as fitz  # PyMuPDF（古い呼び名 fitz は将来なくなる）
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))


def html_path(data):
    h = data.get("html", "")
    if len(h) > 3 and h[0] == "/" and h[2] == ":":      # /C:/Users/... → C:/Users/...
        h = h[1:]
    return Path(h) if h else None


DL = Path.home() / "Downloads"


def _move(q, dest):
    import re
    target = Path(dest) / re.sub(r" \(\d+\)(?=\.json$)", "", q.name)   # ブラウザが付ける「 (1)」を外す
    try:
        q.replace(target)
    except OSError:
        import shutil
        shutil.copy2(q, target)
        q.unlink()
    print(f"移しました（README の保存先へ）: {target}")
    return target


def move_course_files(data, p=None):
    """原稿HTMLの「書き出し」はダウンロードフォルダに保存されるので、README で決めた保存先（JSON の save_dir）へ移す。
    移すのは、読むと決めたコメントと**同じ講座ID**（JSON の course_id、ファイル名の頭の GA など）のコメントだけ。
    IDのない古い書き出しは、読むと決めた1ファイルだけ移す。別の講座のコメントには触らない。戻り値は p の移動後の場所"""
    from notes_html import save_setting
    dest = data.get("save_dir") or ""
    if not dest and html_path(data):                      # 古い書き出し：原稿HTMLのフォルダの README から決める
        s = save_setting(html_path(data))
        dest = s[1] if s else ""
    if not dest or not Path(dest).is_dir():
        return p
    cid, todo = data.get("course_id") or "", []
    if cid:
        for q in sorted(DL.glob(f"{cid}*_コメント*.json"), key=lambda q: q.stat().st_mtime):   # 新しいものが最後に上書き
            try:
                if json.loads(q.read_text(encoding="utf-8")).get("course_id") == cid:
                    todo.append(q)
            except Exception:
                pass
    if p is not None and p.resolve().parent == DL.resolve() and p.resolve() not in [q.resolve() for q in todo]:
        todo.append(p)
    moved = {q.resolve(): _move(q, dest) for q in todo}
    return moved.get(p.resolve(), p) if p is not None else None


def collect(cid):
    """ダウンロードフォルダの、講座ID cid のコメントを全部その講座の保存先へ移す（読まずに片づけるだけ）"""
    for q in DL.glob(f"{cid}*_コメント*.json"):
        try:
            data = json.loads(q.read_text(encoding="utf-8"))
        except Exception:
            continue
        if data.get("course_id") == cid:
            move_course_files(data)
            return
    print(f"ダウンロードフォルダに講座ID {cid} のコメントはありません")


def find_recent(n=8):
    """ダウンロードフォルダと、いまのフォルダ以下（_work を除く）のコメントJSONを新しい順に表示する（移さない）"""
    dl = Path.home() / "Downloads"
    files = set(dl.glob("*_コメント*.json"))
    files |= {p for p in Path.cwd().rglob("*_コメント*.json") if "_work" not in p.parts}
    files = sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)
    for p in files[:n]:
        print(p)
    if not files:
        print(f"{dl} と {Path.cwd()} 以下に *_コメント*.json がありません")


def deck_paths(data, deck_arg):
    if deck_arg:
        pptx = Path(deck_arg)
    else:
        hp = html_path(data) or Path("不明_原稿.html")
        stem = hp.stem[:-len("_原稿")] if hp.stem.endswith("_原稿") else hp.stem
        pptx = hp.with_name(f"{stem}_スライド.pptx")
    return pptx, pptx.with_suffix(".pdf")


def crop(pdf, slide, rect, out, width=1600, margin=0.12):
    doc = fitz.open(pdf)
    page = doc[slide - 1]
    z = width / page.rect.width
    pix = page.get_pixmap(matrix=fitz.Matrix(z, z))
    doc.close()
    im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    W, H = im.size
    x, y, w, h = rect
    box = [x * W, y * H, (x + w) * W, (y + h) * H]
    ImageDraw.Draw(im).rectangle(box, outline=(220, 30, 30), width=5)
    mx, my = margin * W, margin * H
    c = im.crop((max(0, box[0] - mx), max(0, box[1] - my), min(W, box[2] + mx), min(H, box[3] + my)))
    out.parent.mkdir(parents=True, exist_ok=True)
    c.save(out)
    return out


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")   # Windows のコンソール既定（cp932）でも日本語が化けないように
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("json", nargs="?")
    ap.add_argument("--find", action="store_true", help="ダウンロードフォルダの新しいコメントJSONを表示")
    ap.add_argument("--collect", metavar="ID", help="講座ID（GA など）のコメントを、ダウンロードからその講座の保存先へまとめて移す")
    ap.add_argument("--deck", help="スライドの pptx（省略時は JSON の原稿HTMLの場所から探す）")
    ap.add_argument("--out", help="範囲コメントの切り抜きの出力先（省略時は JSON の隣の <名前>_切り抜き）")
    a = ap.parse_args()
    if a.collect:
        collect(a.collect)
        return
    if a.find or not a.json:
        find_recent()
        return
    jp = Path(a.json)
    data = json.loads(jp.read_text(encoding="utf-8"))
    jp = move_course_files(data, jp)
    cm = data.get("comments", [])
    pptx, pdf = deck_paths(data, a.deck)
    out = Path(a.out) if a.out else jp.with_name(jp.stem + "_切り抜き")

    tmp = None
    if not pdf.exists() and pptx.exists() and any(c["kind"] == "region" for c in cm):
        # スライドの PDF は残さない運用なので、切り抜き用に一時フォルダへ書き出す
        import tempfile
        from notes_html import export_temp_pdf
        tmp = tempfile.mkdtemp()
        pdf = export_temp_pdf(pptx, tmp)

    info = {}
    if pptx.exists():
        from pptx import Presentation
        from notes_html import slide_texts
        info = {i + 1: t for i, t in enumerate(slide_texts(Presentation(str(pptx))))}
    else:
        print(f"注意: デッキが見つかりません: {pptx}（--deck で指定）")

    print(f"# コメント：{data.get('deck', jp.stem)}（{len(cm)}件、書き出し {data.get('exported', '')[:16]}）")
    print(f"デッキ: {pptx}")
    last = None
    for c in sorted(cm, key=lambda c: (c["slide"], c["n"])):
        s = c["slide"]
        if s != last:
            title, heading, band, _ = info.get(s, ("", "", "", ""))
            print(f"\n## スライド {s}　●{heading or title}" + (f"　［青帯］{band}" if band else ""))
            last = s
        if c["kind"] == "answer":
            print(f"- #{c['n']} 【{c['q']} への答え】問題：{c.get('quote', '')}")
        elif c["kind"] == "text":
            pre, suf = c.get("prefix", "")[-25:], c.get("suffix", "")[:25]
            print(f"- #{c['n']} 原稿：…{pre}【{c['quote']}】{suf}…".replace("\n", " / "))
        else:
            x, y, w, h = c["rect"]
            where = f"左{x:.0%}・上{y:.0%}・幅{w:.0%}・高さ{h:.0%}"
            if pdf.exists():
                png = crop(pdf, s, c["rect"], out / f"c{c['n']}_s{s}.png")
                print(f"- #{c['n']} スライドの範囲（{where}）→ 切り抜き {png}")
            else:
                print(f"- #{c['n']} スライドの範囲（{where}）※PDFがないので切り抜きなし")
        print(("  答え：" if c["kind"] == "answer" else "  コメント：") + c["comment"].replace("\n", "\n  　　　　　"))
    if tmp:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
