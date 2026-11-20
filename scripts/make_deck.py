"""図 → 組む → 描く → 検査 を1回で（手順3〜5の往復を1つのコマンドに）。出力は直す所だけ。

    python <skill>/scripts/make_deck.py <work>               # 作業フォルダ（_work/<資料名>/）
    python <skill>/scripts/make_deck.py <work> --no-render   # 描かずに組むだけ（ふだんは使わない）
    python <skill>/scripts/make_deck.py <work> --pp          # 毎回 PowerPoint で描く（前のやり方。ふだんは使わない）
    python <skill>/scripts/make_deck.py <work> --no-pp       # ERROR 0 の回も PowerPoint で確かめない
    python <skill>/scripts/make_deck.py <work> --lo          # LibreOffice で描く（ふだんは使わない）
    python <skill>/scripts/make_deck.py <work> --over        # 回数の上限を超えて回す（ユーザーが許したときだけ）
    python <skill>/scripts/make_deck.py <work> --final       # 上限のあと、直したものを描いて確かめるだけの1回（段階ごとに1回。回数に数えない）

回数の上限：仕上げは4回、完成後のレビューのあとの直しは2回（budget.py。オプション「回数の上限」で多め・なしにできる）。上限に来たら組まずに止まる。
描くのは、ふだんは PowerPoint を使わない描画（render_check_py.py。pptx だけから文字の配置を計算し、PowerPoint と同じ形の
shapes.json と画像を作る）。PowerPoint がある PC では、それで ERROR 0 になった回にだけ PowerPoint で1回描いて確かめ、
PowerPoint の結果を検査の結果にする（食い違った所は出す）。PowerPoint が無い PC（Mac・Linux など）は新しい描画だけで最後まで進む。
PowerPoint で確かめられなかったとき（サンドボックスで止められたなど）は、新しい描画の結果のまま進む（そう出す）。

やること（どれも作業フォルダの中で）
  1. figs.py が figs/ の画像より新しければ、python figs.py（図の WARN だけ出す）
  2. python build.py（WARN と、できた pptx の場所だけ出す）
  3. 描く（render_check_py.py）→ render/
  4. 描画の検査（check_layout.py --brief：直す所だけ）。ERROR 0 なら、PowerPoint があれば render_check.ps1 で描いて確かめ、
     PowerPoint の検査の結果を使う（PowerPoint の画像と shapes.json を render/ に置き、新しい描画の分は render/python/ に移す）
  5. 一覧の画像 render/grid-N.jpg（6枚ずつ。レビューと目視はこれで見る。1枚ずつ開かない）と、原稿の確認（check_notes.py：✘・△ だけ）
  6. 最後に1行：ERROR・WARN・原稿の ✘ の数と、次にやること
  7. 組みの記録：枚ごとの指紋を <work>/build_log.jsonl に1行足す（何枚作り直したか。build_log.py）
  8. 最後の回（ERROR・WARN・✘ が0、回数の上限の回、--final）なら、原稿HTML（notes_html.py）も作る（担当が別に走らせる1回を省く）

直すときは、出た所を全部まとめて直してから、もう一度これだけを走らせる（render_check_py・render_check・check_layout を別々に呼ばない）。
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
    import figdraft
    fs = figdraft.fig_files(work)   # figs.py と、図の担当が2人のときの figs_1.py・figs_2.py
    if not (work / "figs.py").exists() or not fs:
        return False
    pngs = list((work / "figs").glob("*.png")) if (work / "figs").is_dir() else []
    return not pngs or max(p.stat().st_mtime for p in pngs) < max(f.stat().st_mtime for f in fs)


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


def render_py(pptx: Path, out: Path):
    """PowerPoint を使わない描画（render_check_py.py）。戻り値 (成功, 失敗の行)。"""
    try:
        import render_check_py
        with redirect_stdout(io.StringIO()):
            render_check_py.render(pptx, out)
        return True, []
    except Exception as e:   # 描けない pptx（壊れた図形など）。PowerPoint・LibreOffice に代える
        return False, [f"新しい描画で描けなかった（{type(e).__name__}: {e}）"]


def render_pp(pptx: Path, out: Path):
    """PowerPoint で描く（render_check.ps1）。戻り値 (成功, 失敗の行)。"""
    if platform.system() != "Windows":
        return False, ["PowerPoint で描けるのは Windows だけ"]
    code, text = run(["powershell", "-ExecutionPolicy", "Bypass", "-File", str(HERE / "render_check.ps1"),
                      "-Pptx", str(pptx), "-OutDir", str(out)], pptx.parent)
    if code == 0 and (out / "shapes.json").exists():
        return True, []
    return False, [why_pp_failed(text)] + short(text, 3)


def render_lo(pptx: Path, out: Path):
    code, text = run([sys.executable, "-X", "utf8", str(HERE / "render_check_lo.py"), "-Pptx", str(pptx), "-OutDir", str(out)], pptx.parent)
    if code == 0 and (out / "shapes.json").exists():
        return True, []
    return False, short(text, 4)


def render(pptx: Path, out: Path, mode: str = "py"):
    """描く。mode："py"（ふだん。PowerPoint を使わない描画）・"pp"（PowerPoint）・"lo"（LibreOffice）。
    戻り値 (成功, 使った道具, 失敗の行)。新しい描画で描けないときだけ、PowerPoint（無ければ LibreOffice）に代える。"""
    if mode == "lo":
        ok, bad = render_lo(pptx, out)
        return ok, "LibreOffice" if ok else "", bad
    if mode == "pp":
        ok, bad = render_pp(pptx, out)
        return ok, "PowerPoint" if ok else "", bad
    ok, bad = render_py(pptx, out)
    if ok:
        return True, "新しい描画（PowerPoint を使わない）", []
    if platform.system() == "Windows" and has_powerpoint():
        ok, bad2 = render_pp(pptx, out)
        return ok, "PowerPoint" if ok else "", bad + bad2
    ok, bad2 = render_lo(pptx, out)
    return ok, "LibreOffice" if ok else "", bad + bad2


def layout_items(text: str):
    """check_layout の出力から (枚, 種類, 中身) の一覧（→ から後の直し方は除く）。"""
    items, slide = [], None
    for line in text.splitlines():
        m = re.match(r"--- slide (\d+)", line)
        if m:
            slide = int(m.group(1))
            continue
        m = re.search(r"\[(ERROR|WARN)\] (.*)", line)
        if m:
            items.append((slide, m.group(1), m.group(2).split(" → ")[0]))
    return items


def run_layout(out: Path, pptx: Path):
    """check_layout.py --brief を走らせる。戻り値 (出力, 終了コード)。"""
    import check_layout
    check_layout.BRIEF = True
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = check_layout.main(str(out / "shapes.json"), str(pptx))
    return buf.getvalue().strip(), code


def line_diffs(a: Path, b: Path, limit: int = 6):
    """2つの shapes.json（a：PowerPoint、b：新しい描画）で、行数が違う図形。"""
    import json
    try:
        A = json.loads(a.read_text(encoding="utf-8-sig"))["shapes"]
        B = json.loads(b.read_text(encoding="utf-8-sig"))["shapes"]
    except Exception:
        return []
    out = []
    for x, y in zip(A, B):
        if x.get("slide") == y.get("slide") and x.get("name") == y.get("name") and (x.get("text") or y.get("text")) \
                and x.get("lines") != y.get("lines"):
            out.append(f"スライド {x['slide']}「{x['name']}」の行数：PowerPoint {x.get('lines')}行・新しい描画 {y.get('lines')}行")
    return out[:limit] + ([f"…ほか {len(out) - limit} 個"] if len(out) > limit else [])


def verify_with_powerpoint(pptx: Path, out: Path, lay_py: str):
    """新しい描画で ERROR 0 の回に、PowerPoint で1回描いて確かめる。
    描けたら、PowerPoint の画像と shapes.json を render/ に置き（新しい描画の分は render/python/ へ）、
    戻り値 (PowerPoint の検査の出力, 終了コード, 食い違いの行)。描けなければ (None, None, 理由の行)。"""
    import shutil
    from collections import Counter
    tmp = out / "powerpoint"
    shutil.rmtree(tmp, ignore_errors=True)
    ok, bad = render_pp(pptx, tmp)
    if not ok:
        shutil.rmtree(tmp, ignore_errors=True)
        return None, None, bad
    keep = out / "python"
    shutil.rmtree(keep, ignore_errors=True)
    keep.mkdir(parents=True, exist_ok=True)
    for f in list(out.glob("slide-*.png")) + [out / "shapes.json"]:
        if f.exists():
            shutil.move(str(f), str(keep / f.name))
    for f in tmp.iterdir():
        shutil.move(str(f), str(out / f.name))
    shutil.rmtree(tmp, ignore_errors=True)
    lay_pp, code = run_layout(out, pptx)
    a, b = Counter(layout_items(lay_pp)), Counter(layout_items(lay_py))
    diffs = [f"PowerPoint だけ：スライド {s_} [{k}] {m[:100]}" for s_, k, m in (a - b).elements()]
    diffs += [f"新しい描画だけ：スライド {s_} [{k}] {m[:100]}" for s_, k, m in (b - a).elements()]
    diffs += line_diffs(out / "shapes.json", keep / "shapes.json")
    return lay_pp, code, diffs


def budget_tokens(work: Path, over: bool):
    try:
        import budget
        return budget.check_tokens(work, over)
    except Exception:
        return None


def second_final_ok(work: Path) -> bool:
    """最後の確かめ（--final）を1回使い、そこで ERROR が1〜2個だけ（原稿と構成案どおりかの ✘ は無し）なら、
    その ERROR だけを直したあとの確かめをもう1回許す（聞かずに）。試しで、上限まで直して ERROR 1つで止まった。"""
    import build_log
    fin = [r for r in build_log.load(work) if r.get("final")]
    return len(fin) == 1 and 1 <= (fin[0].get("error") or 0) <= 2 and not fin[0].get("x")


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
        stage, used = "完成後のレビューのあとの直し", sum(1 for i, r in enumerate(recs)
                                                    if r.get("t", "") >= t0 and not r.get("final") and not build_log.same_as_before(recs, i))
    else:
        stage, used = "仕上げ", sum(1 for i, r in enumerate(recs) if not r.get("final") and not build_log.same_as_before(recs, i))
    # 中身が前の回とまったく同じ回（何も直さずにもう一度回した）は数えない。Codex の試しで、仕上げの4回のうち2回がこれだった
    base = budget.LIGHT_MAKE_DECK if stage == "仕上げ" and budget.light(work) else budget.MAKE_DECK_CAPS[stage]
    c = budget.cap(work, base)   # オプション「回数の上限」（標準・多め・なし）
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
    if final and final_used(work, stage) and not second_final_ok(work):
        print(f"✘ 最後の確かめ（--final）は、{stage}で1回だけ。もう使った。残った所を返答に書いて終える")
        return 1
    if used >= cap and "--over" not in argv and not final:
        try:
            import budget
            light = budget.light(work)
        except Exception:
            light = False
        print(f"✘ make_deck の上限：{stage}は {cap} 回まで（もう {used} 回回した）。ここで止める。"
              + ("残った ERROR・WARN・✘ を返答に書いて終える（ユーザーが越えてよいと言ったら、メインがあなたに続けて頼む。"
                 "そのときは --over を付けて、残った所だけ直す）。" if light else
                 "残った ERROR・WARN・✘ を返答に書いて終える（完成後のレビューが、直すかを決める）。")
              + ("完成後のレビューのあとの直しには、これとは別に回数がある（許可は要らない）。" if stage == "仕上げ" and not light else "")
              + "上限のあとに直した所があるなら、確かめるだけの1回（--final）は許可なしで回せる。"
              + "続けるのは、ユーザーが許したときだけ（--over を付ける）" + "（依頼に「質問はせず」とあっても、上限は越えない。止まるのは正しい動き。残った所を報告して終える。越えるのは、ユーザーが上限を越えてよいと言ったときだけ）")
        return 1
    if not (work / "build.py").exists():
        print(f"✘ {work / 'build.py'} が無い（手順4で build.py を書く）")
        return 1
    try:   # 担当を起動せずにメインが組んでいたら止める（仕上げは仕上げ役、レビューのあとは仕上げの直しの担当が走らせる）
        import budget
        solo = budget.solo_problem(work, "仕上げ役|仕上げの直しの担当|軽量の制作の担当")
    except Exception:
        solo = None
    if solo and "--over" not in argv:
        print(solo)
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
        if re.search(r"PermissionError.*\.pptx|Permission denied.*\.pptx", text):   # PowerPoint などで開いたまま（OneDrive の同期中のことも）
            print("✘ pptx に書けない：PowerPoint などでこのスライドを開いたまま（か、OneDrive が同期中）。"
                  "ユーザーにスライドを閉じてもらってから、もう一度 make_deck.py（この1回は回数に数えない）。build.py は直さない")
            return 1
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
    if (out / "python").exists():   # 前の回の PowerPoint の確かめで移した新しい描画の分（この回は描き直す）
        import shutil
        shutil.rmtree(out / "python", ignore_errors=True)
    mode = "lo" if "--lo" in argv else ("pp" if "--pp" in argv else "py")
    ok, tool, bad = render(pptx, out, mode)
    if not ok:
        print("✘ 描けなかった。" + "\n  ".join(bad or ["check_env.py で確かめる"]))
        return 1
    # 4. 描画の検査（新しい描画で ERROR 0 なら、PowerPoint で1回描いて確かめ、PowerPoint の結果を使う）
    lay, lay_code = run_layout(out, pptx)
    pp_note = []
    if tool.startswith("新しい描画") and not re.search(r"\[ERROR\]", lay) and "--no-pp" not in argv \
            and platform.system() == "Windows" and has_powerpoint():
        lay_pp, code_pp, diffs = verify_with_powerpoint(pptx, out, lay)
        if lay_pp is None:
            pp_note = ["△ PowerPoint で確かめられなかった（新しい描画の結果のまま進める）：" + " / ".join(diffs[:2])]
        else:
            lay, lay_code = lay_pp, code_pp
            tool = "新しい描画で ERROR 0 → PowerPoint で確かめた"
            pp_note = (["PowerPoint と新しい描画が食い違った所（検査は PowerPoint の結果を使う）："] + ["  " + d for d in diffs]) if diffs \
                else ["PowerPoint で確かめた：新しい描画と同じ判定"]
    # 5. 一覧の画像（PowerPoint で確かめた回は、PowerPoint の画像で）
    import grid
    with redirect_stdout(io.StringIO()):
        grid.main(str(out), str(out / "grid"), 2, 6, 800)
    sheets = sorted(out.glob("grid-*.jpg"))
    n_err = len(re.findall(r"\[ERROR\]", lay))
    n_warn = len(re.findall(r"\[WARN\]", lay))
    print(f"描いた（{tool}）：一覧の画像 {len(sheets)}枚（{', '.join(s.name for s in sheets)}）")
    for line in pp_note:
        print(line)
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
    recs = build_log.load(work)
    same = bool(recs) and build_log.same_as_before(recs, len(recs) - 1)
    if len(recs) >= 2 and not same and recs[-1].get("sig") and recs[-2].get("sig"):
        a, b = recs[-2]["sig"], recs[-1]["sig"]
        changed = [k + 1 for k in range(max(len(a), len(b))) if k >= len(a) or k >= len(b) or a[k] != b[k]]
        if changed:   # 画像はこの枚だけを見る（一覧の grid を毎回開くと、開いた画像が会話に残って読み直される）
            print("前の回から変わった枚：" + "・".join(map(str, changed))
                  + "（見るのは " + "・".join(f"render/slide-{n:02d}.png" for n in changed[:6]) + ("…" if len(changed) > 6 else "") + " だけ）")
    if same:
        print("（前の回とスライドの中身がまったく同じ：何も直していない。回数には数えないが、直してから回す）")
        used -= 1   # 下の「n 回目」の表示も数えない
    if final:
        print("（最後の確かめ：回数に数えない。ここで直したら、もう確かめられない。残った所は返答に書く）")
    if runs > 6 and (n_err or n_warn or n_x):
        print(f"△ make_deck は {runs} 回目。出た所を1回で全部直す（直す前に、上の一覧を全部読んでから手を付ける）。"
              "同じ枚が何度も出るなら、本文を削るか図を小さくするなど、形を変える")
    # 標準（担当2人）は ERROR 0・✘ 0 で止める。WARN・← は返答に並べるだけ（念入りは WARN まで直す）。
    # コミュニケーション講座の試しで、合格のあと WARN を追った3回が新しい ✘・ERROR を生み、制作の担当の読み直しの4割を使った
    try:
        stop_at_pass = stage == "仕上げ" and budget.light(work)
    except Exception:
        stop_at_pass = False
    todo = n_err or n_x or (not stop_at_pass and (n_warn or "←" in lay))
    last = final or not todo or used + 1 >= cap
    if last:
        code, text = run([sys.executable, "-X", "utf8", str(HERE / "notes_html.py"), str(pptx)], pptx.parent)
        saved = re.findall(r"saved (.+?\.html)", text)
        if code == 0 and saved:   # 原稿HTMLができたら、渡す前の確認まで続けて（担当が別に呼ぶ1回を省く）
            try:
                import check_done
                rows = check_done.check(pptx, work, record=True)
                bad_ = [(mk, item, msg) for mk, item, msg in rows if mk == "✘"]
                for mk, item, msg in bad_[:6]:
                    print(f"渡す前の確認 ✘ {item}：{msg[:160]}")
                print("渡す前の確認：" + ("渡してよい" if not bad_ else f"✘ が {len(bad_)} 件"))
            except Exception as e:
                print(f"渡す前の確認：走らせられなかった（{type(e).__name__}）。check_done.py を単独で")
        print(f"原稿HTML：作った（{Path(saved[-1]).name}）" if code == 0 and saved
              else "✘ 原稿HTMLが作れなかった：" + " / ".join(short(text, 3) or text.strip().splitlines()[-3:])
              + f"（python {HERE.as_posix()}/notes_html.py \"{pptx.name}\" を単独で走らせる）")
    if todo:
        nxt = ("上に出た ERROR・✘ を**全部**直してから、もう一度だけ make_deck.py（1か所ずつ回さない。WARN・← は直さなくてよい：標準の流れは ERROR 0・✘ 0 で止める）"
               if stop_at_pass else
               "上に出た所を**全部**（ERROR・WARN・←・✘、直せる △ も）直してから、もう一度だけ make_deck.py（1か所ずつ回さない）")
    elif stop_at_pass:
        nxt = ("できあがり。ここで止めて返答を書く（WARN・← は直さず、返答に1行ずつ並べる。直すかはユーザーが決める）"
               if (n_warn or "←" in lay) else "できあがり。ここで止めて返答を書く")
    else:
        nxt = "完成後のレビュー（手順5b。レビュー担当には render/grid-*.jpg を見せる）"
    print(f"\n=> ERROR {n_err}・WARN {n_warn}・原稿と構成案どおりか ✘ {n_x}・△ {len(notes) - n_x}（{stage} {used + 1}/{cap} 回目"
          + ("。完成後のレビューのあとの直しは別に数える" if stage == "仕上げ" else "") + f"）。次：{nxt}")
    return 1 if (n_err or n_x or lay_code) else 0


if __name__ == "__main__":
    sys.exit(main())
