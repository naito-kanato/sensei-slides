"""図 → 組む → 描く → 検査 を1回で（手順3〜5の往復を1つのコマンドに）。出力は直す所だけ。

    python <skill>/scripts/make_deck.py <work>               # 作業フォルダ（_work/<資料名>/）
    python <skill>/scripts/make_deck.py <work> --no-render   # 描かずに組むだけ（PowerPoint も LibreOffice も無いとき）

やること（どれも作業フォルダの中で）
  1. figs.py が figs/ の画像より新しければ、python figs.py（図の WARN だけ出す）
  2. python build.py（WARN と、できた pptx の場所だけ出す）
  3. PowerPoint で描く（render_check.ps1。無ければ LibreOffice の render_check_lo.py）→ render/
  4. 一覧の画像 render/grid-N.jpg（6枚ずつ。レビューと目視はこれで見る。1枚ずつ開かない）
  5. 描画の検査（check_layout.py --brief：直す所だけ）と、原稿の確認（check_notes.py：✘・△ だけ）
  6. 最後に1行：ERROR・WARN・原稿の ✘ の数と、次にやること

直すときは、出た所を全部まとめて直してから、もう一度これだけを走らせる（render_check・check_layout を別々に呼ばない）。
会話に載る出力を短くして、使用量を抑えるための部品。終了コード：ERROR か原稿の ✘ があれば 1。
"""
from __future__ import annotations

import io
import platform
import re
import subprocess
import sys
from contextlib import redirect_stdout
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

KEEP = re.compile(r"WARN|ERROR|Error|Traceback|失敗|見つから|無い|✘|△")


def run(cmd, cwd):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def short(text, limit=12):
    lines = [l for l in text.splitlines() if KEEP.search(l)]
    return lines[:limit] + ([f"  …ほか {len(lines) - limit} 行"] if len(lines) > limit else [])


def figs_stale(work: Path) -> bool:
    f = work / "figs.py"
    if not f.exists():
        return False
    pngs = list((work / "figs").glob("*.png")) if (work / "figs").is_dir() else []
    return not pngs or max(p.stat().st_mtime for p in pngs) < f.stat().st_mtime


def render(pptx: Path, out: Path):
    """PowerPoint で描く。描けなければ LibreOffice。戻り値 (成功, 使った道具, 失敗の行)。"""
    if platform.system() == "Windows":
        code, text = run(["powershell", "-ExecutionPolicy", "Bypass", "-File", str(HERE / "render_check.ps1"),
                          "-Pptx", str(pptx), "-OutDir", str(out)], pptx.parent)
        if code == 0 and (out / "shapes.json").exists():
            return True, "PowerPoint", []
        bad = short(text, 4)
    else:
        bad = []
    code, text = run([sys.executable, str(HERE / "render_check_lo.py"), "-Pptx", str(pptx), "-OutDir", str(out)], pptx.parent)
    if code == 0 and (out / "shapes.json").exists():
        return True, "LibreOffice", []
    return False, "", bad + short(text, 4)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print(__doc__)
        return 1
    work = Path(argv[0]).resolve()
    no_render = "--no-render" in argv
    if not (work / "build.py").exists():
        print(f"✘ {work / 'build.py'} が無い（手順4で build.py を書く）")
        return 1
    # 1. 図
    if figs_stale(work):
        code, text = run([sys.executable, "-X", "utf8", "figs.py"], work)
        lines = short(text)
        print(f"図：{'✘ figs.py が失敗' if code else '描き直した'}" + ("" if not lines else "\n  " + "\n  ".join(lines)))
        if code:
            return 1
    # 2. 組む
    code, text = run([sys.executable, "-X", "utf8", "build.py"], work)
    m = re.findall(r"saved (.+?\.pptx) \((\d+) slides\)", text)
    lines = short(text)
    if code or not m:
        print("✘ build.py が失敗\n  " + "\n  ".join(lines or text.strip().splitlines()[-8:]))
        return 1
    pptx = Path(m[-1][0])
    print(f"組んだ：{pptx.name}（{m[-1][1]}枚）" + ("" if not lines else "\n  " + "\n  ".join(lines)))
    if no_render:
        print("描画は省いた（--no-render）。描けるようになったら、もう一度これを走らせる")
        return 0
    # 3. 描く
    out = work / "render"
    ok, tool, bad = render(pptx, out)
    if not ok:
        print("✘ 描けなかった（PowerPoint も LibreOffice も）。check_env.py で確かめる。サンドボックスで止められているなら、"
              "ユーザーの許可を得て、このコマンドをサンドボックスの外で走らせる\n  " + "\n  ".join(bad))
        return 1
    # 4. 一覧の画像
    import grid
    with redirect_stdout(io.StringIO()):
        grid.main(str(out), str(out / "grid"), 2, 6, 800)
    sheets = sorted(out.glob("grid-*.jpg"))
    # 5. 検査
    import check_layout
    check_layout.BRIEF = True
    buf = io.StringIO()
    with redirect_stdout(buf):
        lay_code = check_layout.main(str(out / "shapes.json"), str(pptx))
    lay = buf.getvalue().strip()
    n_err = len(re.findall(r"\[ERROR\]", lay))
    n_warn = len(re.findall(r"\[WARN\]", lay))
    print(f"描いた（{tool}）：一覧の画像 {len(sheets)}枚（{', '.join(s.name for s in sheets)}）")
    if n_err or n_warn or "←" in lay:
        print(lay)
    import check_notes
    notes = [(mk, item, msg) for mk, item, msg in check_notes.check(work) if mk in ("✘", "△")]
    for mk, item, msg in notes:
        print(f"{mk} {item}：{msg}")
    n_x = sum(mk == "✘" for mk, _, _ in notes)
    nxt = ("直す所をまとめて直し、もう一度 make_deck.py" if (n_err or n_warn or n_x or "←" in lay)
           else "完成後のレビュー（手順5b。レビュー担当には render/grid-*.jpg を見せる）")
    print(f"\n=> ERROR {n_err}・WARN {n_warn}・原稿 ✘ {n_x}・△ {len(notes) - n_x}。次：{nxt}")
    return 1 if (n_err or n_x or lay_code) else 0


if __name__ == "__main__":
    sys.exit(main())
