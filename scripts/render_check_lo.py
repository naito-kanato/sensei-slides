"""LibreOffice 版の描画の検査（PowerPoint が無いとき・開けないときの代わり）。

render_check.ps1 と同じ形の shapes.json と slide-NN.png を作る。shapes.json には "engine": "libreoffice" が入り、
check_layout.py は本文と図の間隔を少しきびしめ（0.5 in）に見る（LibreOffice は文字の範囲を PowerPoint より少し狭く測るため）。

    python render_check_lo.py -Pptx deck.pptx -OutDir <work>/render [-Width 1600] [-NoImages] [-KeepPdf]

Windows で見本3つ（33枚）を PowerPoint と比べたとき、検査の判定（ERROR・WARN）と一覧の字数・行数・最長行は全部一致した。
文字の範囲の差は中央値で数 pt。違いは、見出しの●が少し小さく出ることと、文字の幅が数 pt 違うこと。
Mac・Linux では試していない（pptx の指定のフォント（MS PGothic・Meiryo など）が無いと別のフォントで描くので、幅がもっとずれうる）。
最後の確認は、描いた画像を目で見て行う。

手順
  1. pptx を一時フォルダへ別名で複製（OneDrive の古い版を開かないため。ps1 と同じ）
  2. soffice --headless で PDF にする（専用のプロファイルを使い、起動中の LibreOffice と衝突しない）
  3. PDF を PyMuPDF で PNG にする（幅 -Width px）
  4. 図形の枠・名前・種類・ph・文字・文字の大きさは python-pptx で pptx から取る
  5. 「実際に描画された文字の範囲」（tl/tt/tw/th/lines）は PDF の文字行（PyMuPDF の行）から取り、図形と対応づける
     - 行の中心が図形の枠（2pt 広げる）に入り、行の文字の6割以上が図形の文字に含まれる → その図形の行
       （複数の図形が候補なら枠の面積が小さい方）
     - 行の中心か左端が枠に入る場合も同じ（左寄せの文字が枠の右へ溢れた行を拾うため）
     - どの枠にも入らない行（枠から溢れた文字）は、行の文字が図形の文字に含まれ、横の位置が合う図形のうち
       縦に一番近いものへ
     - 同じ図形の行のうち、縦に半分以上重なるものは1行にまとめる（フォントが変わる所で PDF の行が分かれるため）
     - tl/tt/tw/th は行の外接矩形、lines は行の数。表のセル・グループの中の文字は ps1 と同じく対象外
"""
import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path


from pptx import Presentation

EMU_PT = 12700.0


def find_soffice():
    """soffice の場所。環境変数 SOFFICE -> PATH -> OS ごとの標準の場所の順に探す。"""
    env = os.environ.get("SOFFICE")
    if env and Path(env).exists():
        return env
    for n in ("soffice", "libreoffice", "soffice.exe"):
        p = shutil.which(n)
        if p:
            return p
    cands = []
    if platform.system() == "Windows":
        for base in (os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)")):
            if base:
                cands.append(Path(base) / "LibreOffice" / "program" / "soffice.exe")
    elif platform.system() == "Darwin":
        cands += [Path("/Applications/LibreOffice.app/Contents/MacOS/soffice"),
                  Path.home() / "Applications/LibreOffice.app/Contents/MacOS/soffice"]
    else:
        cands += [Path(p) for p in ("/usr/bin/soffice", "/usr/bin/libreoffice", "/usr/local/bin/soffice",
                                    "/opt/libreoffice/program/soffice", "/snap/bin/libreoffice")]
    for c in cands:
        if c.exists():
            return str(c)
    sys.exit("soffice が見つからない。LibreOffice を入れるか、環境変数 SOFFICE に soffice のパスを入れる")


def to_pdf(pptx_copy, outdir, timeout=300):
    soffice = find_soffice()
    profile = Path(tempfile.gettempdir()) / "lo_profile_render_check"
    cmd = [soffice, f"-env:UserInstallation={profile.resolve().as_uri()}", "--headless", "--norestore",
           "--convert-to", "pdf", "--outdir", str(outdir), str(pptx_copy)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    pdf = Path(outdir) / (Path(pptx_copy).stem + ".pdf")
    if not pdf.exists():
        sys.exit(f"PDF ができなかった: {r.stdout} {r.stderr}")
    return pdf


def export_pdf(pptx, pdf):
    """pptx を LibreOffice で PDF にする（notes_html.py が、PowerPoint で書き出せないときに使う）。"""
    pptx, pdf = Path(pptx).resolve(), Path(pdf)
    tmp = Path(tempfile.gettempdir()) / ("render_lo_" + uuid.uuid4().hex)
    tmp.mkdir()
    try:
        copy = tmp / ("render_" + uuid.uuid4().hex[:8] + ".pptx")
        shutil.copyfile(pptx, copy)
        strip_autofit(copy)
        shutil.copyfile(to_pdf(copy, tmp), pdf)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return pdf


def strip_autofit(pptx_path):
    """複製の pptx の各スライドで <a:spAutoFit/>（図形を文字に合わせて自動調整）を <a:noAutofit/> にする。
    LibreOffice は wrap="none" の図形でも、文字が図形の幅より広いと自動調整で折り返してしまい（Meiryo の見本で確認）、
    PowerPoint では折り返さない箱が折り返す偽の ERROR になる。図形の位置・大きさは pptx の値のまま描かれる。"""
    import zipfile
    tmp = str(pptx_path) + ".tmp"
    with zipfile.ZipFile(pptx_path) as zi, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zo:
        for it in zi.infolist():
            d = zi.read(it.filename)
            if re.match(r"ppt/slides/slide\d+\.xml$", it.filename):
                d = d.replace(b"<a:spAutoFit/>", b"<a:noAutofit/>")
            zo.writestr(it, d)
    os.replace(tmp, pptx_path)


def norm(t):
    return re.sub(r"\s+", "", t or "")


def first_run_size(shape):
    try:
        for p in shape.text_frame.paragraphs:
            for r in p.runs:
                if r.font.size:
                    return r.font.size.pt
    except Exception:
        pass
    return None


def shape_info(slide, idx):
    rows = []
    for sh in slide.shapes:
        try:
            typ = int(sh.shape_type) if sh.shape_type is not None else 0
        except Exception:
            typ = 0
        ph = None
        if sh.is_placeholder:
            typ = 14
            try:
                ph = int(sh.placeholder_format.type)
            except Exception:
                pass

        def g(a):
            try:
                v = getattr(sh, a)
                return float(v) / EMU_PT if v is not None else 0.0
            except Exception:
                return 0.0
        text = ""
        paras = 0
        if sh.has_text_frame and sh.text_frame.text.strip() != "":
            # python-pptx は段落を \n、行区切りを \v にする。PowerPoint は段落が \r
            text = "\r".join(p.text for p in sh.text_frame.paragraphs)
            paras = len(sh.text_frame.paragraphs)
            if ph == 13:     # スライド番号（フィールド）は番号そのものにする
                text = str(idx)
        rows.append(dict(slide=idx, name=sh.name, type=typ, left=g("left"), top=g("top"), width=g("width"),
                         height=g("height"), ph=ph, text=text, tl=None, tt=None, tw=None, th=None,
                         lines=0, paras=paras, size=first_run_size(sh) if text else None))
    return rows


def pdf_lines(page):
    """PDF ページの文字行 [{text, bbox, size}]。"""
    out = []
    d = page.get_text("dict")
    for b in d["blocks"]:
        if b.get("type") != 0:
            continue
        for ln in b["lines"]:
            spans = [s for s in ln["spans"] if s["text"].strip()]
            if not spans:
                continue
            x0 = min(s["bbox"][0] for s in spans)
            y0 = min(s["bbox"][1] for s in spans)
            x1 = max(s["bbox"][2] for s in spans)
            y1 = max(s["bbox"][3] for s in spans)
            out.append(dict(text=norm("".join(s["text"] for s in spans)), bbox=(x0, y0, x1, y1),
                            size=spans[0]["size"]))
    return out


def overlap_ratio(line_text, shape_text):
    if not line_text:
        return 0.0
    pool = {}
    for c in shape_text:
        pool[c] = pool.get(c, 0) + 1
    hit = 0
    for c in line_text:
        if pool.get(c, 0) > 0:
            pool[c] -= 1
            hit += 1
    return hit / len(line_text)


def assign(rows, lines):
    """PDF の行を図形へ対応づける。{行の番号: 図形の番号}"""
    texts = {i: norm(r["text"]) for i, r in enumerate(rows) if r["text"]}
    res = {}
    for li, ln in enumerate(lines):
        cx = (ln["bbox"][0] + ln["bbox"][2]) / 2
        cy = (ln["bbox"][1] + ln["bbox"][3]) / 2
        cands = []
        for i, t in texts.items():
            r = rows[i]
            # 行の中心か左端が枠に入る（左寄せの文字が枠の右へ溢れると、中心は枠の外になる）
            in_x = any(r["left"] - 2 <= x <= r["left"] + r["width"] + 2 for x in (cx, ln["bbox"][0]))
            if in_x and r["top"] - 2 <= cy <= r["top"] + r["height"] + 2 and overlap_ratio(ln["text"], t) >= 0.6:
                cands.append((r["width"] * r["height"], i))
        if cands:
            res[li] = min(cands)[1]
            continue
        # 枠から溢れた行：文字が図形の文字に含まれ、横が合うもののうち縦に一番近い
        best = None
        for i, t in texts.items():
            r = rows[i]
            if len(ln["text"]) < 2 or ln["text"] not in t:
                continue
            if not any(r["left"] - 20 <= x <= r["left"] + r["width"] + 20 for x in (cx, ln["bbox"][0])):
                continue
            dy = max(r["top"] - cy, cy - (r["top"] + r["height"]), 0)
            if best is None or dy < best[0]:
                best = (dy, i)
        if best:
            res[li] = best[1]
    return res


def merge_visual_lines(boxes):
    """縦に半分以上重なる行を1行にまとめる（フォントの変わり目で PDF の行が分かれるため）。"""
    boxes = sorted(boxes, key=lambda b: (b[1] + b[3]) / 2)
    groups = []
    for b in boxes:
        for g in groups:
            ov = min(g[3], b[3]) - max(g[1], b[1])
            if ov > 0.5 * min(g[3] - g[1], b[3] - b[1]):
                g[0] = min(g[0], b[0])
                g[1] = min(g[1], b[1])
                g[2] = max(g[2], b[2])
                g[3] = max(g[3], b[3])
                break
        else:
            groups.append(list(b))
    return groups


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-Pptx", "--pptx", required=True)
    ap.add_argument("-OutDir", "--outdir", required=True)
    ap.add_argument("-Width", "--width", type=int, default=1600)
    ap.add_argument("-NoImages", "--noimages", action="store_true")
    ap.add_argument("-KeepPdf", "--keeppdf", action="store_true",
                    help="LibreOffice が作った PDF を OutDir/slides.pdf に残す")
    ap.add_argument("-KeepAutofit", "--keepautofit", action="store_true",
                    help="spAutoFit を外さずに変換する（既定は外す。折り返しの偽 ERROR を避けるため）")
    a = ap.parse_args()
    pptx = Path(a.pptx).resolve()
    out = Path(a.outdir)
    out.mkdir(parents=True, exist_ok=True)
    for f in out.glob("slide-*.png"):
        f.unlink()
    tmp = Path(tempfile.gettempdir()) / ("render_lo_" + uuid.uuid4().hex)
    tmp.mkdir()
    try:
        copy = tmp / ("render_" + uuid.uuid4().hex[:8] + ".pptx")
        shutil.copyfile(pptx, copy)
        if not a.keepautofit:
            strip_autofit(copy)
        pdf = to_pdf(copy, tmp)
        prs = Presentation(str(copy))
        W = prs.slide_width / EMU_PT
        H = prs.slide_height / EMU_PT
        import pymupdf as fitz  # PyMuPDF（古い呼び名 fitz は将来なくなる）。PDF を使う所でだけ読む（無くても他は動く）
        fitz.TOOLS.mupdf_display_errors(False)   # 構造ツリーの警告（無害）を出さない
        doc = fitz.open(pdf)
        n = len(prs.slides)
        if doc.page_count != n:
            print(f"注意: スライド {n} 枚に対し PDF は {doc.page_count} 枚", file=sys.stderr)
        allrows = []
        for i, slide in enumerate(prs.slides, 1):
            rows = shape_info(slide, i)
            if i <= doc.page_count:
                page = doc[i - 1]
                sx = W / page.rect.width       # PDF のページ幅が違えばスライドの pt に合わせる
                if not a.noimages:
                    zoom = a.width / page.rect.width
                    page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False).save(
                        str(out / f"slide-{i:02d}.png"))
                lines = pdf_lines(page)
                for ln in lines:
                    ln["bbox"] = tuple(v * sx for v in ln["bbox"])
                    ln["size"] *= sx
                amap = assign(rows, lines)
                per = {}
                for li, ri in amap.items():
                    per.setdefault(ri, []).append(li)
                for ri, lis in per.items():
                    r = rows[ri]
                    vis = merge_visual_lines([lines[li]["bbox"] for li in lis])
                    r["tl"] = min(v[0] for v in vis)
                    r["tt"] = min(v[1] for v in vis)
                    r["tw"] = max(v[2] for v in vis) - r["tl"]
                    r["th"] = max(v[3] for v in vis) - r["tt"]
                    r["lines"] = len(vis)
                    if r["size"] is None:
                        r["size"] = round(lines[min(lis)]["size"], 1)
            allrows.extend(rows)
        doc.close()
        if a.keeppdf:
            shutil.copyfile(pdf, out / "slides.pdf")
        js = dict(pptx=str(pptx), engine="libreoffice", slideWidth=W, slideHeight=H, slides=n, shapes=allrows)
        (out / "shapes.json").write_text(json.dumps(js, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"rendered {n} slides -> {out}（LibreOffice。最後は画像を目で見て確かめる）")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
