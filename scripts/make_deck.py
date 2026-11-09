"""図 → 組む → 描く → 検査 を1回で（手順3〜5の往復を1つのコマンドに）。出力は直す所だけ。

    python <skill>/scripts/make_deck.py <work>               # 作業フォルダ（_work/<資料名>/）
    python <skill>/scripts/make_deck.py <work> --no-render   # 描かずに組むだけ（PowerPoint も LibreOffice も無いとき）
    python <skill>/scripts/make_deck.py <work> --lo          # PowerPoint があっても LibreOffice で描く（ふだんは使わない）
    python <skill>/scripts/make_deck.py <work> --over        # 回数の上限を超えて回す（ユーザーが許したときだけ）
    python <skill>/scripts/make_deck.py <work> --final       # 上限のあと、直したものを描いて確かめるだけの1回（段階ごとに1回。回数に数えない）

回数の上限：仕上げは4回、完成後のレビューのあとの直しは2回（budget.py。オプション「回数の上限」で多め・なしにできる）。上限に来たら組まずに止まる。
PowerPoint があるのに描けないときは、LibreOffice に代えずに止まる（描き方が変わると検査の数値が変わるため）。

やること（どれも作業フォルダの中で）
  1. figs.py が figs/ の画像より新しければ、python figs.py（図の WARN だけ出す）
  2. python build.py（WARN と、できた pptx の場所だけ出す）
  3. PowerPoint で描く（render_check.ps1。無ければ LibreOffice の render_check_lo.py）→ render/
  4. 一覧の画像 render/grid-N.jpg（6枚ずつ。レビューと目視はこれで見る。1枚ずつ開かない）
  5. 描画の検査（check_layout.py --brief：直す所だけ）と、原稿の確認（check_notes.py：✘・△ だけ）
  6. 最後に1行：ERROR・WARN・原稿の ✘ の数と、次にやること
  7. 組みの記録：枚ごとの指紋を <work>/build_log.jsonl に1行足す（何枚作り直したか。build_log.py）

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


def decode(b: bytes) -> str:
    """子のプロセスの出力。UTF-8 で読めなければ OS の既定の文字コードで読む（日本語の Windows の PowerShell は cp932 で書くので、
    「アクセスが拒否されました」などのエラーが UTF-8 では化けて、理由を見分けられなかった）。"""
    try:
        return b.decode("utf-8")
    except UnicodeDecodeError:
        import locale
        return b.decode(locale.getpreferredencoding(False) or "cp932", errors="replace")


def run(cmd, cwd):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True)
    return r.returncode, decode(r.stdout or b"") + decode(r.stderr or b"")


def short(text, limit=12):
    lines = [l for l in text.splitlines() if KEEP.search(l)]
    return lines[:limit] + ([f"  …ほか {len(lines) - limit} 行"] if len(lines) > limit else [])


def figs_stale(work: Path) -> bool:
    f = work / "figs.py"
    if not f.exists():
        return False
    pngs = list((work / "figs").glob("*.png")) if (work / "figs").is_dir() else []
    return not pngs or max(p.stat().st_mtime for p in pngs) < f.stat().st_mtime


def has_powerpoint() -> bool:
    try:
        import check_env
        return bool(check_env.has_powerpoint())
    except Exception:
        return False


def why_pp_failed(text: str) -> str:
    if re.search(r"80070005|Access is denied|UnauthorizedAccess|アクセスが拒否", text):
        return ("PowerPoint があるのに開けない：サンドボックスの中で動いている。make_deck だけを1行のコマンドで（ほかのコマンドと"
                "改行や ; でつなげずに）走らせる。それでも止められたら、ここで止めてメインに返す（メインがユーザーに許可を求める）")
    if re.search(r"ファイルを開けません|cannot open|could not open|開けません", text, re.I):
        return ("PowerPoint がこの pptx を開けない：中に壊れた図形がある（大きさがマイナスの矢印・図形など）。"
                "直前に変えた枚の位置と大きさ（gap・w・h）を見直す")
    return "PowerPoint で描けなかった"


def render(pptx: Path, out: Path, allow_lo: bool = False):
    """PowerPoint で描く。PowerPoint が無いとき（か --lo）だけ LibreOffice。戻り値 (成功, 使った道具, 失敗の行)。
    PowerPoint があるのに描けないときは LibreOffice に代えない（描き方が変わると検査の数値が変わり、無い問題を追いかけることになる）。"""
    if platform.system() == "Windows" and not allow_lo:
        code, text = run(["powershell", "-ExecutionPolicy", "Bypass", "-File", str(HERE / "render_check.ps1"),
                          "-Pptx", str(pptx), "-OutDir", str(out)], pptx.parent)
        if code == 0 and (out / "shapes.json").exists():
            return True, "PowerPoint", []
        if has_powerpoint():
            return False, "", [why_pp_failed(text)] + short(text, 3)
        bad = short(text, 4)
    else:
        bad = []
    code, text = run([sys.executable, "-X", "utf8", str(HERE / "render_check_lo.py"), "-Pptx", str(pptx), "-OutDir", str(out)], pptx.parent)
    if code == 0 and (out / "shapes.json").exists():
        return True, "LibreOffice", []
    return False, "", bad + short(text, 4)




def budget_tokens(work: Path, over: bool):
    try:
        import budget
        return budget.check_tokens(work, over)
    except Exception:
        return None


def final_used(work: Path, stage: str) -> bool:
    """この段階で、最後の確かめ（--final）をもう使ったか。"""
    import build_log
    import budget
    import time
    recs = [r for r in build_log.load(work) if r.get("final")]
    if stage == "仕上げ":
        rv = Path(work) / "review.md"
        return any(True for r in recs) and not rv.exists()
    launched = [r.get("ts") for r in budget.load(work) if r.get("role") == "完成後のレビュー担当" and r.get("ts")]
    t0 = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(launched[0])) if launched else ""
    return any(r.get("t", "") >= t0 for r in recs)


def run_budget(work: Path):
    """(段階の名前, この段階で回した回数, 上限)。review.md ができたあとは、そのあとに回した回数を数える。"""
    import build_log
    import time
    recs = build_log.load(work)
    rv = work / "review.md"
    import budget
    if rv.exists():
        # review.md ができた時刻（直しの担当が末尾に「採否と直した点」を書き足すと更新時刻が後ろにずれるので、それは使わない）：
        # 完成後のレビュー担当を起動した時刻があればそれ、無ければファイルを作った時刻
        st = rv.stat()
        launched = [r.get("ts") for r in budget.load(work) if r.get("role") == "完成後のレビュー担当" and r.get("ts")]
        born = launched[0] if launched else getattr(st, "st_birthtime", st.st_ctime if platform.system() == "Windows" else st.st_mtime)
        t0 = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(born))
        stage, used = "完成後のレビューのあとの直し", sum(1 for r in recs if r.get("t", "") >= t0 and not r.get("final"))
    else:
        stage, used = "仕上げ", sum(1 for r in recs if not r.get("final"))
    c = budget.cap(work, budget.MAKE_DECK_CAPS[stage])   # オプション「回数の上限」（標準・多め・なし）
    return stage, used, (10 ** 6 if c is None else c)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print(__doc__)
        return 1
    work = Path(argv[0]).resolve()
    no_render = "--no-render" in argv
    import build_log
    stage, used, cap = run_budget(work)
    tok = budget_tokens(work, "--over" in argv)
    if tok:
        print(tok)
        return 1
    final = "--final" in argv
    if final and final_used(work, stage):
        print(f"✘ 最後の確かめ（--final）は、{stage}で1回だけ。もう使った。残った所を返答に書いて終える")
        return 1
    if used >= cap and "--over" not in argv and not final:
        print(f"✘ make_deck の上限：{stage}は {cap} 回まで（もう {used} 回回した）。ここで止める。"
              "残った ERROR・WARN・✘ を返答に書いて終える（完成後のレビューが、直すかを決める）。"
              + ("完成後のレビューのあとの直しには、これとは別に回数がある（許可は要らない）。" if stage == "仕上げ" else "")
              + "上限のあとに直した所があるなら、確かめるだけの1回（--final）は許可なしで回せる。"
              + "続けるのは、ユーザーが許したときだけ（--over を付ける）")
        return 1
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
        build_log.append(work, pptx)
        print("描画は省いた（--no-render）。描けるようになったら、もう一度これを走らせる")
        return 0
    # 3. 描く
    out = work / "render"
    ok, tool, bad = render(pptx, out, "--lo" in argv)
    if not ok:
        print("✘ 描けなかった。" + "\n  ".join(bad or ["check_env.py で確かめる"]))
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
    # 構成案・設計メモどおりに組んだか（渡す前の確認と同じ項目。仕上げの1周目で気づけるように）
    import check_done
    PLAN_ITEMS = ("役割と結論", "図の案どおりか", "図の無いスライド", "本文の形", "流れ図の数", "スライドの型")
    try:
        plan_rows = [(mk, item, msg) for mk, item, msg in check_done.check(pptx, work, record=False)
                     if item in PLAN_ITEMS and mk in ("✘", "△")]
    except Exception as e:   # 確認が動かなくても組んだ結果は出す
        plan_rows = [("△", "構成案どおりか", f"確かめられなかった（{type(e).__name__}）")]
    for mk, item, msg in plan_rows:
        print(f"{mk} {item}：{msg}")
    notes += plan_rows
    n_x = sum(mk == "✘" for mk, _, _ in notes)
    runs = build_log.append(work, pptx, n_err, n_warn, n_x, final=final)
    if final:
        print("（最後の確かめ：回数に数えない。ここで直したら、もう確かめられない。残った所は返答に書く）")
    if runs > 6 and (n_err or n_warn or n_x):
        print(f"△ make_deck は {runs} 回目。出た所を1回で全部直す（直す前に、上の一覧を全部読んでから手を付ける）。"
              "同じ枚が何度も出るなら、本文を削るか図を小さくするなど、形を変える")
    nxt = ("上に出た所を**全部**（ERROR・WARN・←・✘、直せる △ も）直してから、もう一度だけ make_deck.py（1か所ずつ回さない）"
           if (n_err or n_warn or n_x or "←" in lay)
           else "完成後のレビュー（手順5b。レビュー担当には render/grid-*.jpg を見せる）")
    print(f"\n=> ERROR {n_err}・WARN {n_warn}・原稿と構成案どおりか ✘ {n_x}・△ {len(notes) - n_x}（{stage} {used + 1}/{cap} 回目"
          + ("。完成後のレビューのあとの直しは別に数える" if stage == "仕上げ" else "") + f"）。次：{nxt}")
    return 1 if (n_err or n_x or lay_code) else 0


if __name__ == "__main__":
    sys.exit(main())
