"""資料置き場を作り、ユーザーがスライドを作るフォルダに入れた資料をそこへ格納し、足りないものを確かめる。
発表（論文・教科書・研究発表）でも講座でも同じ。ユーザーは資料をフォルダの一番上に入れて「入れたから、このテーマで作って」と頼む。

    python <skill>/scripts/materials.py --scan [スライドを作るフォルダ]            # 一番上の資料らしいファイルと、その中身の手がかり（頁数・題・最初の文。最初に1回）
    python <skill>/scripts/materials.py <発表フォルダ> --collect ファイル名 ...    # 確かめたファイルを 資料/ の中へ写す（元はそのまま残す）
    python <skill>/scripts/materials.py <発表フォルダ>                         # 置いた資料の一覧と、足りないもの（✘ があれば終了コード 1）
    python <skill>/scripts/materials.py <発表フォルダ> --source                # 論文・教科書など資料がそろっている発表と講座（方針.md・図は任意）
    python <skill>/scripts/materials.py <発表フォルダ> --text                  # 過去のスライドの文字を 資料/過去のスライド/<名前>_文字.md に書き出す
    python <skill>/scripts/materials.py <発表フォルダ> --init                  # 資料置き場だけ作る（--collect も作る）

発表フォルダは、スライドを作るフォルダの一番上の `<資料名>/`（講座なら `<講座名>/`）。できたスライドと原稿のページもここに置く。

資料置き場：
    <発表フォルダ>/資料/方針.md          目的・結果・結論（必須。ファイルに無ければチャットで聞く）と、背景・方法（任意。資料から下書き）
    <発表フォルダ>/資料/図/              結果の図・写真（png・jpg・svg・pdf）
    <発表フォルダ>/資料/過去のスライド/  前の発表のスライド（pptx・pdf）
    <発表フォルダ>/資料/その他/          論文・要旨・メモ・データ
格納のしかた（--collect）：--scan で中身を確かめ、使うとユーザーが言ったものだけを名前で渡す。元のファイルは消さずに写す。画像 → 図/、pptx と名前に「スライド」「発表」「slides」がある pdf → 過去のスライド/、ほかの pdf・文書・データ → その他/。
    スキルの一式（.agents など・はじめに.md・準備.*）・できたスライド（*_スライド.pptx・*_原稿.html）・コメントの書き出し（*_コメント.json）は候補に出さない
確かめること（資料が全部はそろっていない発表。--source のときは方針と図は任意）：
    ✘ 方針.md の必須の節（目的・結果・結論）が空（`<…>` のまま）→ チャットで聞いて書く
    ✘ 結果の図が1つも無い（図/ にも 過去のスライド/ にも無い）
    △ 図/ の図のうち、方針.md の「結果」に名前が出てこないもの（何が見えるかを聞く）
"""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SKILL = Path(__file__).resolve().parents[1]
TEMPLATE = SKILL / "assets" / "presentation" / "方針.md"
DIRS = {"図": "結果の図・写真（png・jpg・svg・pdf）", "過去のスライド": "前の発表のスライド（pptx・pdf）", "その他": "論文・要旨・メモ・データ"}
REQUIRED = ("目的", "結果", "結論")   # 発表する本人しか知らないもの。背景・方法は AI が資料から下書きし、無いときだけ聞く
FIG_EXT = {".png", ".jpg", ".jpeg", ".svg", ".pdf", ".tif", ".tiff", ".gif", ".bmp"}
SLIDE_EXT = {".pptx", ".pdf"}


MATERIAL_EXT = FIG_EXT | {".pptx", ".ppt", ".docx", ".doc", ".md", ".txt", ".xlsx", ".xls", ".csv", ".key", ".tex", ".bib", ".zip"}
KEEP = ("はじめに", "準備", "~$", ".")
KEEP_SUFFIX = ("_スライド.pptx", "_原稿.html", "_コメント.json")


def kind_of(p: Path) -> str:
    """資料置き場のどこに入れるか（図／過去のスライド／その他）。"""
    ext = p.suffix.lower()
    if ext in FIG_EXT - {".pdf"}:
        return "図"
    if ext in (".pptx", ".ppt", ".key") or (ext == ".pdf" and re.search(r"スライド|発表|slide", p.stem, re.I)):
        return "過去のスライド"
    return "その他"


def candidates(top: Path):
    """一番上に入れられた資料らしいファイル（スキルの一式・できたスライド・コメントの書き出しは除く）。"""
    return [p for p in sorted(top.iterdir()) if p.is_file() and p.suffix.lower() in MATERIAL_EXT
            and not p.name.startswith(KEEP) and not p.name.endswith(KEEP_SUFFIX)]


def describe(p: Path) -> str:
    """中身の手がかり（頁数・枚数・題・最初の文・画像の大きさ）。何の資料かを、開かずに確かめるため。"""
    ext = p.suffix.lower()
    try:
        if ext == ".pdf":
            import pymupdf
            with pymupdf.open(str(p)) as doc:
                first = next((l.strip() for l in doc[0].get_text().splitlines() if len(l.strip()) > 3), "") if len(doc) else ""
                return f"{len(doc)} 頁・最初の行「{first[:40]}」"
        if ext == ".pptx":
            from pptx import Presentation
            prs = Presentation(str(p))
            title = next((sh.text_frame.text.strip() for sl in prs.slides for sh in sl.shapes
                          if getattr(sh, "has_text_frame", False) and sh.has_text_frame and sh.text_frame.text.strip()), "")
            return f"{len(prs.slides)} 枚・最初の文字「{title[:40]}」"
        if ext == ".docx":
            import docx  # noqa: F401（python-docx が無ければ下の except）
            d = docx.Document(str(p))
            first = next((x.text.strip() for x in d.paragraphs if x.text.strip()), "")
            return f"最初の段落「{first[:40]}」"
        if ext in (".md", ".txt", ".csv", ".tex"):
            first = next((l.strip() for l in p.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()), "")
            return f"最初の行「{first[:40]}」"
        if ext in FIG_EXT:
            from PIL import Image
            with Image.open(p) as im:
                return f"画像 {im.size[0]}×{im.size[1]}"
    except Exception:
        pass
    return f"{p.stat().st_size // 1024} KB"


def collect(folder: Path, names=None, top: Path | None = None):
    """一番上（既定は発表フォルダの親）の資料を 資料/ の中へ写す（元のファイルは残す）。[(元, 先)] を返す。同じ名前があれば上書きせず飛ばす。
    names を渡す（--scan で中身を確かめ、使うものだけ）。names が無いときは候補を全部写す。"""
    top = (top or folder.parent).resolve()
    m = init(folder)
    srcs = [top / n for n in names] if names else candidates(top)
    moved = []
    for p in srcs:
        if not p.is_file():
            print(f"[WARN] {p.name} が {top} に無い")
            continue
        dst = m / kind_of(p) / p.name
        if dst.exists():
            print(f"[WARN] {dst} がもうあるので写さない")
            continue
        shutil.copy2(str(p), str(dst))
        moved.append((p, dst))
    return moved


def init(folder: Path) -> Path:
    m = folder / "資料"
    for d in DIRS:
        (m / d).mkdir(parents=True, exist_ok=True)
    plan = m / "方針.md"
    if not plan.exists():
        shutil.copy(TEMPLATE, plan)
    return m


def sections(text: str) -> dict:
    """{節の名前: 中身}（`<…>` の雛形の行・空行は中身に数えない）。"""
    out, cur = {}, None
    for line in text.splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            cur = m.group(1)
            out[cur] = ""
            continue
        if cur is None:
            continue
        t = re.sub(r"<[^<>]*>", "", line).strip(" -：:\t")
        if t:
            out[cur] += t + "\n"
    return out


def files(d: Path, exts=None):
    if not d.is_dir():
        return []
    return sorted(p for p in d.iterdir() if p.is_file() and not p.name.startswith(("~$", ".")) and (exts is None or p.suffix.lower() in exts))


def check(folder: Path, source: bool = False):
    """[(印, 項目, 説明)]。source＝論文・教科書など資料がそろっている（方針.md と図は任意）。"""
    m = folder / "資料"
    res = []
    if not m.is_dir():
        return [("✘", "資料置き場", f"{m} が無い（--init で作る）")]
    plan = m / "方針.md"
    secs = sections(plan.read_text(encoding="utf-8")) if plan.exists() else {}
    if source:
        docs = files(m / "その他") + files(m / "過去のスライド")
        res.append(("✔" if docs else "✘", "資料", f"{len(docs)} 個" if docs else "資料/ に論文・教科書が無い（一番上に入れてもらい --collect）"))
        return res
    if not plan.exists():
        res.append(("✘", "方針", "資料/方針.md が無い（--init で作る）"))
    else:
        empty = [k for k in REQUIRED if not next((v for name, v in secs.items() if name.startswith(k)), "").strip()]
        res.append(("✘" if empty else "✔", "方針",
                    f"空の節：{'・'.join(empty)}。チャットで聞いて、聞いた言葉のまま 資料/方針.md に書く（ファイルにあるなら、その場所を書く）" if empty
                    else "必須の節（" + "・".join(REQUIRED) + "）が全部書いてある"))
    figs = files(m / "図", FIG_EXT)
    slides = files(m / "過去のスライド", SLIDE_EXT)
    if not figs and not slides:
        res.append(("✘", "結果の図", "図/ にも 過去のスライド/ にも何も無い。結果の図を 資料/図/ に置いてもらう（過去のスライドの図を使うなら 過去のスライド/ に）"))
    else:
        res.append(("✔", "結果の図", f"図 {len(figs)} 個・過去のスライド {len(slides)} 個"))
    result = next((v for name, v in secs.items() if name.startswith("結果")), "")
    unnamed = [f.name for f in figs if f.stem not in result and f.name not in result]
    if figs and unnamed:
        res.append(("△", "図の説明", f"方針.md の「結果」に名前が出てこない図：{'・'.join(unnamed)}（何が見えるか・読み取ってほしい数値を聞く）"))
    return res


def inventory(folder: Path):
    m = folder / "資料"
    lines = []
    for d, what in DIRS.items():
        fs = files(m / d)
        lines.append(f"{d}/（{what}）：" + ("、".join(f.name for f in fs) if fs else "なし"))
    return lines


def slide_text(pptx: Path) -> str:
    """過去のスライドの文字（枚ごと。タイトルと本文）。AI が pptx を開かずに中身を読むため。"""
    from pptx import Presentation
    prs = Presentation(str(pptx))
    out = [f"# {pptx.name} の文字（{len(prs.slides)} 枚）", ""]
    for i, sl in enumerate(prs.slides, 1):
        texts = []
        for sh in sl.shapes:
            if getattr(sh, "has_text_frame", False) and sh.has_text_frame:
                t = " ".join(p.text.strip() for p in sh.text_frame.paragraphs if p.text.strip())
                if t:
                    texts.append(t)
        pics = sum(1 for sh in sl.shapes if sh.shape_type == 13)
        out.append(f"## {i}" + (f"（図 {pics} 個）" if pics else ""))
        out += [f"- {t}" for t in texts] or ["- （文字なし）"]
        out.append("")
    return "\n".join(out)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] == "--scan":
        top = Path(argv[1]).resolve() if len(argv) > 1 else Path.cwd()
        found = candidates(top)
        print(f"{top} の一番上の資料らしいファイル：" + ("" if found else "なし"))
        for p in found:
            print(f"  {p.name}（→ {kind_of(p)}/）：{describe(p)}")
        return 0
    if not argv or argv[0].startswith("-"):
        print(__doc__)
        return 2
    folder = Path(argv[0]).resolve()
    if "--collect" in argv:
        names = [a for a in argv[argv.index("--collect") + 1:] if not a.startswith("--")]
        moved = collect(folder, names or None)
        print(f"資料置き場：{folder / '資料'}")
        print("\n".join(f"  写した：{a.name} → 資料/{b.parent.name}/（元はそのまま）" for a, b in moved) or "  写したもの：なし")
        argv = [a for a in argv if a != "--collect" and a not in names]
    if "--init" in argv:
        m = init(folder)
        print(f"資料置き場を作った：{m}")
        for d, what in DIRS.items():
            print(f"  {d}/  … {what}")
        print("  方針.md … 目的・結果・結論（必須。ファイルに無ければチャットで聞く）。背景・方法は資料から下書き")
        return 0
    if "--text" in argv:
        for p in files(folder / "資料" / "過去のスライド", {".pptx"}):
            out = p.with_name(p.stem + "_文字.md")
            out.write_text(slide_text(p), encoding="utf-8")
            print(f"書いた：{out}")
        return 0
    print("\n".join(inventory(folder)))
    res = check(folder, source="--source" in argv)
    for mark, item, msg in res:
        print(f"{mark} {item}：{msg}")
    bad = sum(m == "✘" for m, _, _ in res)
    print("\n" + (f"✘ が {bad} 件。足りないものをチャットで聞くか、置いてもらってから先へ" if bad else "そろった。手順1（資料を読む）へ"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
