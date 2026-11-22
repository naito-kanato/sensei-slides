"""今どこまで済んでいて、次に何をするか：作業フォルダの中のファイルから決める（覚えていなくても戻れるように）。

    python <skill>/scripts/next_step.py                    # スライドを作るフォルダの一番上で：作業の一覧と、それぞれの次の手順
    python <skill>/scripts/next_step.py _work/<資料名>     # その作業フォルダの、済んだ手順と次の手順
    python <skill>/scripts/next_step.py <講座フォルダ>      # 講座：次に作る回と、その作業フォルダ（途中の回があれば、その回の次の手順）
    python <skill>/scripts/next_step.py --start 講座 [--set 項目=値 ...]   # メインが最初に1回：道具の読み替え・環境・最初の質問・設定の一覧・次の1手

会話が長くなって前半を忘れたとき、途中で止まったあと、別の AI に引き継いだときに走らせる。
判断はしない（ファイルの有無・日時と、検査のスクリプトの ✘ だけを見る）。「次」に書いた手順書の節を読んでから進める。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))

SKILL = "<skill>"


def _mtime(p: Path):
    return p.stat().st_mtime if p.exists() else None


def _newer(a: Path, b: Path) -> bool:
    """a が b より新しい（どちらも有る）。"""
    return a.exists() and b.exists() and a.stat().st_mtime >= b.stat().st_mtime - 1


def needs_final_fix(review: Path, pptx: Path) -> bool:
    """完成後のレビューの判定が「直してから渡す」なのに、そのあとデッキを作り直していない（pptx が review.md より新しくない）。
    review.md に「## 採否と直した点」（か「## 直した点」）の中身があれば直し済み：仕上げの直しの担当は組み直したあとに
    review.md へ採否を書き足すので、時刻だけで見ると review.md が新しくなり、手順9から進まなかった（英語の試しで見つけた）。"""
    if not (review.exists() and pptx.exists()):
        return False
    import re as _re
    text = review.read_text(encoding="utf-8")
    m = _re.search(r"判定\s*[:：]\s*[「『]?([^」』\n]*)", text)
    done = _re.search(r"^##\s*(?:採否と)?直した点[^\n]*\n(.*?)(?=^##\s|\Z)", text, _re.S | _re.M)
    if done and _re.search(r"^\s*[-*]\s*\S", done.group(1), _re.M):
        return False
    return bool(m and "直してから" in m.group(1)) and pptx.stat().st_mtime <= review.stat().st_mtime


def _fails(res):
    return [f"{item}：{msg[:60]}" for mark, item, msg in res if mark == "✘"]


def find_pptx(work: Path):
    """作業フォルダから作られたデッキ（check_done.find_work で作業フォルダに戻れる *_スライド.pptx）。新しいもの。"""
    import check_done
    here = sorted([*work.glob("*_スライド.pptx"), *work.glob("*_slides.pptx")], key=lambda p: p.stat().st_mtime)   # 作業フォルダの中に出したデッキ（見本など）
    if here:
        return here[-1]
    root = work.parent.parent if work.parent.name == "_work" else work.parent
    if work.name == "質問回答":
        root = work.parent.parent.parent
    hits = []
    for p in [*root.rglob("*_スライド.pptx"), *root.rglob("*_slides.pptx")]:
        rel = p.relative_to(root).parts if p.is_relative_to(root) else p.parts   # 一式の外の _work（上のフォルダの名前）は見ない
        if "_work" in rel and p.parent.name != "build" and not p.parent.samefile(work):
            continue
        try:
            w = check_done.find_work(p.resolve())
        except Exception:
            w = None
        if w is not None and w.resolve() == work.resolve():
            hits.append(p)
    return max(hits, key=lambda p: p.stat().st_mtime) if hits else None


def usage_line(work: Path):
    """この作業フォルダを扱った Codex の会話で、枠の％がいくつ動いたか（記録が無ければ None）。"""
    try:
        import run_record
        rows = run_record.codex_rows(work, run_record._since(work), run_record.project_root(work))
    except Exception:
        return None
    import budget
    # この作業フォルダにファイルを書いていた間だけを数える（あとで別の回の会話がこのフォルダを読んでも足さない）
    ts = [f.stat().st_mtime for f in Path(work).rglob("*") if f.is_file() and f.name not in (budget.LOG, "run_record.md", "run_record.json")]
    lo_t, hi_t = (min(ts) - 3600, max(ts) + 600) if ts else (0, float("inf"))
    used = budget.used_by_window([p for r in rows for p in r.get("limits", []) if lo_t <= p[0] <= hi_t])
    if not used:
        return None
    lims = budget.percent_limits(work)   # オプション「使用量の上限」（枠ごと）
    over = [n for n, u in used.items() if lims.get(n) is not None and u > lims[n]]
    body = "・".join(f"{n}の枠 約{u:.0f}%" + (f"（上限 {lims[n]:g}%）" if lims.get(n) is not None else "")
                     for n, u in sorted(used.items(), key=lambda x: budget.WINDOWS.index(x[0])))
    return (f"{'△' if over else '・'} この回で使った Codex の枠：{body}"
            + (f"。{'・'.join(over)}の枠が上限を超えた：続ける前にユーザーに【質問】で聞く（続ける・ここで止める）" if over else ""))


def _shown(work: Path) -> str:
    """次の手順の文に書く作業フォルダ：作業ディレクトリからの相対（担当が返答の最後の行に写し、メインがそのまま brief.py に渡す）。"""
    import os
    try:
        r = Path(os.path.relpath(Path(work).resolve(), Path.cwd()))
        return (r if not r.as_posix().startswith("..") else Path(work)).as_posix()
    except ValueError:
        return Path(work).as_posix()


def leave_outline(work: Path) -> bool:
    """オプション「構成案の確認」が「任せる」（見せずに完成まで）か。"""
    try:
        import slide_profile
        v = slide_profile.option(slide_profile.load_profile(work), "構成案の確認", "見せる") or ""
    except Exception:
        return False
    return any(k in v.lower() for k in ("任せる", "まかせる", "leave", "skip"))


RETURN_HEAD = "## 設計に戻す穴"


def returned_holes(review: Path, plan: Path, pending: bool = True) -> list:
    """推論距離の担当が {review} の「## 設計に戻す穴」に書いた行（pending なら、設計の担当がまだ ✔ を付けていない行だけ）。
    更新時刻では決めない（推論距離の担当は、穴を書いたあとに自分の手当てで設計メモを書き換えるので、時刻では直したかどうか分からない）。"""
    if not review.exists():
        return []
    t = review.read_text(encoding="utf-8")
    m = re.search(rf"^{re.escape(RETURN_HEAD)}\s*$(.*?)(?=^##\s|\Z)", t, re.S | re.M)
    rows = [l.strip() for l in (m.group(1).splitlines() if m else []) if l.strip().startswith("- ") and "なし" not in l]
    if pending:
        rows = [r for r in rows if not r.startswith(("- ✔", "- [✔"))]
    return rows


def light_steps(work: Path, kind: str):
    """講座・発表の回（担当2人）：設計の担当 → 推論距離の担当（戻す穴があれば設計の担当へ）→ 制作の担当 → 渡す前の確認。"""
    import budget
    out = []

    def add(ok, step, msg=""):
        out.append((ok, step, msg))
        return ok

    w = _shown(work)
    launched = {r.get("role") for r in budget.load(work)}
    # 前の版の「念入り」の作業フォルダ：設計の担当（軽量の）はまだいないので、続けて頼めない。新しく起動する
    again = ("設計の担当に続けて頼む（【続けて頼む】。新しく起動しない）" if "軽量の設計の担当" in launched or not budget.old_careful(work)
             else f"軽量の設計の担当を新しく起動して頼む（`brief.py 軽量の設計の担当 {w}`。前の版の念入りの作業フォルダなので）")
    plan = work / ("memo.md" if kind == "memo" else "outline.md")
    if not plan.exists():
        add(False, "設計（軽量）", "まだ")
        if "軽量の設計の担当" in launched:
            return out, "軽量：設計の担当が書き終えるのを待つ（終わりの知らせを待つ。コマンドで様子を見ない）"
        return out, (f"標準：設計の担当1人を起動（`brief.py 軽量の設計の担当 {w}`）。"
                     "数字・筋・事実の確かめまで1人で、検査の ✘ 0 まで")
    if kind == "memo":
        import check_memo
        import facts
        bad = _fails(check_memo.check(plan))
        _, fh, frows = facts.memo_facts(plan.read_text(encoding="utf-8"))
        i_ok = next((k for k, h in enumerate(fh) if "確認" in h), 3)
        todo = [r for r in frows if facts.unchecked(r, i_ok)]
    else:
        import check_outline
        bad, todo = _fails(check_outline.check(plan)), []
    add(not bad and not todo, "設計（軽量）", "；".join(bad[:3]) + (f"（確認がまだの事実 {len(todo)} 行）" if todo else ""))
    review = work / ("memo_review.md" if kind == "memo" else "outline_review.md")
    holes = returned_holes(review, plan)
    if bad or todo:
        # 穴を設計の担当に戻した回は、直しで出た ✘ も設計の担当へ（推論距離の担当に行くと、設計の担当の直しを知らずに直す）
        if review.exists() and "推論距離の担当" in launched and not (work / "build.py").exists() and not returned_holes(review, plan, pending=False):
            # 推論距離の担当が手当てまで入れる（設計の担当の長い会話を読み直さない）。手当てで出た ✘ もこの担当が直す
            return out, ("推論距離の担当に続けて頼む（【続けて頼む】。新しく起動しない）：" + "；".join(bad[:3])
                         + "（手当ては `guide.py inference-distance 5`。青帯・話の筋を変えないと直らない筋の穴だけは、設計の担当に【続けて頼む】）")
        return out, ("軽量：" + again + "：" + "；".join(bad[:3])
                     + (f"。確認がまだの事実 {len(todo)} 行をその場で確かめる" if todo else ""))
    build = work / "build.py"
    if holes and not build.exists():   # 推論距離の担当が、事実か筋が要る穴を設計の担当に戻した
        add(False, "設計に戻す穴", f"{len(holes)} 件")
        return out, (f"{again}：{review.name} の「{RETURN_HEAD[3:]}」の {len(holes)} 件を埋める"
                     "（事実が要る穴は確かめて3節の行に足し、筋の穴は青帯・筋を直す）。埋めた行は頭を「- ✔ 」に書き換える。直したら検査の ✘ 0 まで")
    # 推論距離（スキルの要）：設計の担当とは別の目で推論距離を見て、手当てまで入れる小さな担当（会話が短いので、設計の担当に続けて頼むより安い）
    if not build.exists():
        add(review.exists(), "推論距離", "" if review.exists() else "まだ")
        if not review.exists():
            if "推論距離の担当" in launched:
                return out, "推論距離の担当が書き終えるのを待つ（終わりの知らせを待つ）"
            return out, (f"推論距離の担当1人を起動（`brief.py 推論距離の担当 {w}`）。設計の担当とは別の目で推論距離を見て {review.name} に書き、"
                         "手当てまで入れる。戻ったら、その返答の最後の「次：」の行のとおりに（無ければ next_step をもう一度）")
    pptx = find_pptx(work) if build.exists() else None
    import language
    html = language.sibling(pptx, "slides", "script") if pptx else None
    done = bool(pptx) and _newer(pptx, build) and _newer(work / "render" / "shapes.json", pptx) and _newer(html, pptx)
    add(done, "制作（軽量）", "" if done else "まだ")
    if not done:
        if "軽量の制作の担当" in launched:
            return out, "軽量：制作の担当が書き終えるのを待つ（終わりの知らせを待つ）。担当がもう戻っていて残っているなら、残った所を【続けて頼む】"
        if kind == "outline" and not build.exists() and not leave_outline(work):   # 発表：構成案をユーザーに見せてから組む（オプション「構成案の確認：見せる」）
            return out, ("構成案をユーザーに見せる（最初に筋の表の「対立」「それで」の2行＝問いの深め、次に outline.md の話の順番の表。オプション「構成案の確認：見せる」）。直しは設計の担当に【続けて頼む】（直した枚は script.md の原稿も）。"
                         f"OK が出たら、制作の担当1人を起動（`brief.py 軽量の制作の担当 {w}`）")
        return out, (f"軽量：制作の担当1人を起動（`brief.py 軽量の制作の担当 {w}`）。scaffold（設計メモから組む）→ 図 → 残った TODO と原稿 → make_deck（3回まで）→ 原稿HTML")
    return out, (f"手順7：制作の担当の返答に make_deck の「渡す前の確認：渡してよい」があれば、そのままユーザーに渡す（check_done は make_deck が最後の回に走らせ済み。"
                 f"返答に無いときだけ python {SKILL}/scripts/check_done.py \"{pptx.as_posix()}\"）。"
                 "✘ が残ったら（制作の担当が make_deck の上限で止まったとき）、残った所を報告してユーザーに【質問】（越えて直す・このまま受け取る）。"
                 "越えて直すなら、制作の担当に【続けて頼む】（`make_deck.py <work> --over` で残った所だけ。"
                 "新しい担当を起動しない：起動のたびに資料と設計メモを読み直す分が丸ごと増える）")


def steps_for(work: Path):
    """[(済んだか, 手順, 説明)] と 次の手順の文。"""
    work = Path(work)
    kind = "answers" if (work / "answers.md").exists() else "memo" if (work / "memo.md").exists() else "outline"
    if kind != "answers":
        if kind == "outline" and re.search(r"_\d{2}$", work.name):
            kind = "memo"   # 講座の回（設計メモはまだ）
        return light_steps(work, kind)
    # ここから下は質問回答のデッキ（references/answer-deck.md）：制作役（と図の担当）→ 仕上げ役 → 完成後のレビュー → 仕上げの直し
    out = []

    def add(ok, step, msg=""):
        out.append((ok, step, msg))
        return ok

    nxt = None
    add((work / "answers.md").exists(), "答えの下書き（answers.md）")
    # 2. 図
    figs = work / "figs.py"
    pngs = list((work / "figs").glob("*.png")) if (work / "figs").is_dir() else []
    import figdraft
    fsrc = figdraft.fig_files(work)   # figs.py と、図の担当が2人のときの figs_1.py・figs_2.py
    fig_ok = figs.exists() and pngs and max(p.stat().st_mtime for p in pngs) >= max(f.stat().st_mtime for f in fsrc) - 1
    if add(bool(fig_ok), "図（figs.py → figs/）", "" if fig_ok else ("figs.py が無い" if not figs.exists() else "figs.py を直したあと描き直していない")) is False and not nxt:
        import brief
        nc = len(brief.card_numbers(work))
        nf = len(figdraft.drawn(figdraft.plan_cells(work)[1])) if nc >= brief.SPLIT_AT else 0
        who = (f"カードが {nc} 枚・自分で描く図が {nf} 枚なので、制作役2人と図の担当2人の4人を同時に起動（`brief.py 制作役 <work> --part 1/2` は前半、"
               "`--part 2/2` は後半、`brief.py 図の担当 <work> --part 1/2`・`--part 2/2` は図を半分ずつ figs_1.py・figs_2.py に。merge は仕上げ役が最初にする）"
               if nf >= figdraft.FIG_SPLIT_AT else
               f"カードが {nc} 枚なので、制作役2人と図の担当1人の3人を同時に起動（`brief.py 制作役 <work> --part 1/2` は前半、`--part 2/2` は後半、"
               "`brief.py 図の担当 <work>` は図。merge は仕上げ役が最初にする）" if nc >= brief.SPLIT_AT else
               "制作役1人（`brief.py 制作役 <work>`）が figs.py で図、カードを1枚ずつ読んで parts/NN.py・parts/NN.md、scaffold.py <work> --merge で戻す")
        nxt = ("手順3〜5（SKILL.md「手順と担当」）：" + ("" if nc else "python <skill>/scripts/scaffold.py <work> で骨組みとカード（cards/）を作り、") + who +
               "。そのあと仕上げ役1人が python <skill>/scripts/make_deck.py <work> で組んで検査して直し、原稿HTMLまで")
        try:   # もう起動していれば、起動し直させずに待たせる（図の担当がまだ描いている間など）
            import budget
            launched = {r.get("role") for r in budget.load(work)}
        except Exception:
            launched = set()
        if nc and launched & {"制作役", "図の担当"} and not (launched & {"仕上げ役"}):
            nxt = ("手順3〜4：制作役・図の担当が書き終えるのを待つ（図：" + ("figs.py がまだ" if not figs.exists() else "描き直しがまだ")
                   + "）。担当がもう戻っていて残っているなら、図の担当を新しく起動する")
    # 3. ビルド
    build = work / "build.py"
    notes = work / "notes.md"
    pptx = find_pptx(work) if build.exists() else None
    add(build.exists(), "build.py")
    add(notes.exists(), "原稿（notes.md）")
    if pptx is None:
        add(False, "スライド（*_スライド.pptx）", "まだ組んでいない")
        if not nxt:
            import brief
            nums = brief.card_numbers(work)
            left = [n for n in nums if not (work / "parts" / f"{n:02d}.py").exists()]
            if nums and not left:   # 制作役（と図の担当）が書き終えた：組むのは仕上げ役（merge から）
                nxt = "手順5：仕上げ役を起動（`brief.py 仕上げ役 <work>`。scaffold.py --merge → make_deck.py → 原稿HTML）"
            elif nums:
                nxt = (f"手順3〜4：制作役（と図の担当）が書き終えるのを待つ（parts がまだの枚：{'・'.join(map(str, left[:10]))}{'…' if len(left) > 10 else ''}）。"
                       "担当がもう戻っていて残っているなら、その枚だけを新しい制作役に頼む")
            else:
                nxt = ("手順4：python <skill>/scripts/scaffold.py <work> で骨組みとカード（cards/）を作り、カードを読んで parts/NN.py・parts/NN.md を書き、"
                       "scaffold.py <work> --merge で戻して、python <skill>/scripts/make_deck.py <work> で組んで検査する（`guide.py steps 4`）")
        return out, nxt
    add(_newer(pptx, build) and (not notes.exists() or _newer(pptx, notes)), "スライド", f"{pptx.name}" + ("" if _newer(pptx, build) else "（build.py より古い。組み直す）"))
    # 4. 描画の検査
    shapes = work / "render" / "shapes.json"
    rend = _newer(shapes, pptx)
    if add(rend, "描画（render/shapes.json）", "" if rend else "今の pptx をまだ描いていない") is False and not nxt:
        nxt = f"手順5（仕上げ役）：python {SKILL}/scripts/make_deck.py {work.as_posix()} を走らせ、出た所をまとめて直す"
    # 5. 完成後のレビュー
    review = work / "review.md"
    if add(review.exists(), "完成後のレビュー（review.md）") is False and not nxt:
        nxt = "手順5b：一覧の画像（render/grid-*.jpg）を空の会話の【別のエージェント】に、final-review.md の「指摘の型」とあわせてレビューさせ、review.md に判定・指摘と採否・直した点を書く（references/final-review.md）"
    if not nxt and needs_final_fix(review, pptx):   # 判定が「直してから渡す」なら、渡す前の確認より先に直す（SKILL.md 9）
        nxt = (f"手順9：仕上げの直しの担当を新しく起動（`brief.py 仕上げの直しの担当 {work.as_posix()}`）。review.md の採否を決めて直し、"
               "make_deck と notes_html をやり直す。そのあと手順7（check_done.py）")
    # 6. 原稿のページ
    import language
    html = language.sibling(pptx, "slides", "script")
    if add(_newer(html, pptx), "原稿のページ（*_原稿.html）", "" if _newer(html, pptx) else ("無い" if not html.exists() else "pptx より古い")) is False and not nxt:
        nxt = f"手順6：python {SKILL}/scripts/notes_html.py で原稿のページを作る（`guide.py steps 6`）"
    # 7. 渡す前の確認
    if not nxt:
        nxt = f"手順7：python {SKILL}/scripts/check_done.py \"{pptx.as_posix()}\" を走らせる。「渡してよい」が出たらユーザーに渡す（✘ があれば直す）"
    return out, nxt


def course_next(course: Path):
    """講座フォルダ：作った回と、次に作る回の作業フォルダ。"""
    made = sorted({p.name[:2] + "_" for p in [*course.glob("[0-9][0-9]_*_スライド.pptx"), *course.glob("[0-9][0-9]_*_slides.pptx")]})   # 回の番号ごとに1つ（題名を変える前の古い版を数えない）
    readme = course / "00_README.md"
    root = course.parent / "_work"
    works = sorted(root.glob(f"{course.name}_[0-9][0-9]")) if root.is_dir() else []
    lines = [f"講座フォルダ：{course.name}（作った回 {len(made)}：{'・'.join(m[:2] for m in made) or 'なし'}）"]
    if not readme.exists():
        return lines, "references/course.md 手順1〜3：ヒアリング → 00_README.md（全体の地図）を作る"
    unfinished = [w for w in works if not any(m.startswith(w.name[-2:] + "_") for m in made)]
    if unfinished:
        w = unfinished[0]
        return lines, f"{w.name} の途中：{steps_for(root / w.name)[1]}"   # その回の次の1手まで（メインが next_step をもう1回呼ばずに済む）
    n = max(int(m[:2]) for m in made) + 1 if made else 1
    w = f"_work/{course.name}_{n:02d}"
    first = f"軽量の設計の担当を起動（`brief.py 軽量の設計の担当 {w}`）。数字・筋・事実の確かめまで1人で {w}/memo.md を書く"
    if made:
        return lines, f"第{n}回：{first}。設計の前に、前の回のコメント・答え（00_README.md のつまずき一覧）を読む"
    t = readme.read_text(encoding="utf-8")
    m = re.search(r"全\s*(\d+)\s*回", t)
    total = int(m.group(1)) if m else len(re.findall(r"^\|\s*\d+\s*\|", t, re.M))
    if total == 1:   # 全1回の講座：地図は見せずに進む（1回分の題とゴールは、ヒアリングの答えでもう決まっている）
        return lines, f"第1回：{first}（全1回の講座なので、地図はユーザーに見せずに進む）"
    return lines, f"第1回：ユーザーが 00_README.md の地図に OK を出したら、{first}"


def overview(top: Path):
    """スライドを作るフォルダの一番上：作業フォルダと講座フォルダの一覧と、それぞれの次。"""
    out = []
    root = top / "_work"
    for course in sorted(p for p in top.iterdir() if p.is_dir() and (p / "00_README.md").exists()):
        _, nxt = course_next(course)
        out.append(f"・講座 {course.name}：{nxt}")
    if root.is_dir():
        for w in sorted(p for p in root.iterdir() if p.is_dir() and not p.name.startswith(("_", "."))):
            if not any((w / f).exists() for f in ("outline.md", "memo.md", "build.py")):
                continue
            _, nxt = steps_for(w)
            out.append(f"・{w.name}：{nxt}")
    return out


def tool_lines() -> list:
    """references/agents.md「道具」の表を、道具ごとの1行にする（メインが表を丸ごと読まずに、自分の道具の行だけ見る）。"""
    import guide
    t = guide.section("agents", "道具") or ""
    rows = [[c.strip() for c in ln.strip().strip("|").split("|")] for ln in t.splitlines() if ln.startswith("|")]
    if len(rows) < 3:
        return []
    head, body = rows[0], [r for r in rows[2:] if len(r) == len(rows[0])]
    return [f"- {tool}：" + "／".join(f"{r[0]}＝{r[j]}" for r in body) for j, tool in enumerate(head[2:], start=2)]


START_ASK = {
    "講座": ("① 詳しさ（必須）：初学者・多少知っている／かなり知っている（問いに「学習者が自分でない（後輩・受講者など）ときは、その他にどんな人かを書く」と添える）"
            "　② 回数：3回／5回／おまかせ　③ 資料：テーマだけ／手元の PDF を土台に／あとで決める。"
            "答えのあとに、学習者のプロフィール（専門・研究テーマ）を一言で勧める（任意）。受講者が本人だけでない・手元の資料を橋渡しに使うときだけ `guide.py course 1`"),
    "発表": ("① 詳しさ（必須）：初学者・多少知っている／かなり知っている　② 発表時間：15分／30分／決まっていない　③ 構成案：見せる（おすすめ）／任せる。"
            "資料は、フォルダの一番上を `materials.py --scan <フォルダ>` で見て、同じ質問の中で使うかを確かめる。細部は `guide.py steps 0`"),
}
START_NEXT = {
    "講座": ("答えがそろったら（聞かない回はすぐ）、地図の担当を【別のエージェント】で起動：依頼は「`python <skill>/scripts/brief.py 地図の担当 <講座名>` を走らせ、出た依頼のとおりに進める」の1行と、"
            "その下の「ユーザーの答え：…」（テーマ・詳しさ・回数・資料・ゴール。講座名は講座フォルダの名前になる）。"),
    "発表": ("答えがそろったら（聞かない回はすぐ）、設計の担当を【別のエージェント】で起動：依頼は「`python <skill>/scripts/brief.py 軽量の設計の担当 _work/<資料名>` を走らせ、出た依頼のとおりに進める」の1行と、"
            "その下の「ユーザーの答え：…」（詳しさ・発表時間・構成案・資料の場所）。"),
}


def start_text(kind: str, sets: dict) -> str:
    """メインが最初に1回だけ走らせる：道具の読み替え・環境・最初の【質問】・設定の一覧・次の1手（guide.py agents・course 1・slide_profile を別に呼ばない）。"""
    import io
    from contextlib import redirect_stdout
    import slide_profile
    kind = "講座" if "講" in kind else "発表"
    out = [f"## 始める（{kind}。この出力で足りる。guide.py agents・course 1・steps 0・slide_profile を別に走らせない）", "",
           "道具の読み替え（【】の言葉を、使っている道具の行で読む。表に無い道具・細部は `guide.py agents 道具`）："]
    out += tool_lines()
    try:
        import check_env
        buf = io.StringIO()
        with redirect_stdout(buf):
            check_env.main()
        bad = [ln for ln in buf.getvalue().splitlines() if ln[:1] in ("✘", "△")]
        out += ["", "環境：" + ("そろっている" if not bad else "足りない所がある（`check_env.py` の表を見せ、`guide.py steps 0` のとおりに）")] + bad
    except Exception:
        pass
    out += ["", "最初の【質問】（ボタンで1回・3問・各3択。依頼文で分かる問いは省く。依頼に「質問はせず」「既定で」とあれば聞かない。言語は聞かない：依頼文の言語）：",
            START_ASK[kind], "",
            "設定の一覧（ユーザーへの文に、そのまま貼る。答えで値が変わったら `slide_profile.py --table"
            + (" --kind 講座" if kind == "講座" else "") + " --set 項目=値` で出し直す）：",
            slide_profile.language_line(None, sets), "",
            slide_profile.options_table(None, sets, "講座" if kind == "講座" else "ゼミ"), "",
            "次：" + START_NEXT[kind] + "起動と同じ応答の文に設定の一覧を貼り「この設定で進めます。変えたい所があれば言ってください」と添え、"
            "応答を一言で終えて担当の知らせを待つ（sleep・ls・next_step で様子を見ない）。担当の返答の最後の「次：」の行のとおりに、次の担当を起動する"]
    return "\n".join(out)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] == "--start":
        kind = argv[1] if len(argv) > 1 and not argv[1].startswith("--") else "講座"
        sets = dict(argv[i + 1].split("=", 1) for i, a in enumerate(argv) if a == "--set" and i + 1 < len(argv) and "=" in argv[i + 1])
        print(start_text(kind, sets))
        return 0
    p = Path(argv[0]) if argv else Path.cwd()
    if not p.exists():
        print(f"{p} が無い")
        return 1
    import budget
    note = budget.careful_note(p.resolve())   # 前の版の「念入り」の作業フォルダ・講座：標準として読み、1行だけ知らせる
    if note:
        print(note)
    if (p / "00_README.md").exists() and not any((p / f).exists() for f in ("outline.md", "memo.md")):
        lines, nxt = course_next(p)
        print("\n".join(lines))
        print(f"\n次：{nxt}")
        return 0
    short = "--short" in argv
    if any((p / f).exists() for f in ("outline.md", "memo.md", "answers.md", "build.py")) or p.parent.name == "_work":
        steps, nxt = steps_for(p)
        if short:   # メイン用：止める理由と次の1手だけ（メインは担当が戻るたびに走らせるので、会話を太らせない）
            try:
                import budget
                solo = budget.solo_problem(p.resolve())
                t = budget.token_line(p.resolve())
                web = budget.main_web_problem(p.resolve())
            except Exception:
                solo, t, web = None, None, None
            for line in [solo, web, (t if t and t.startswith("△") else None)]:
                if line:
                    print(line)
            print(f"次：{nxt}")
            return 0
        print(f"作業フォルダ：{p.name}")
        try:
            import budget
            solo = budget.solo_problem(p.resolve())
            web = budget.main_web_problem(p.resolve())
        except Exception:
            solo, web = None, None
        for line in (solo, web):
            if line:
                print(line)
        for ok, step, msg in steps:
            print(f"  {'✔' if ok else '・'} {step}{'：' + msg if msg else ''}")
        u = usage_line(p.resolve())
        if u:
            print(u)
        try:
            import budget
            print("・ " + budget.summary(p.resolve()))
            t = budget.token_line(p.resolve())
            if t:
                hint = ("budget.py <work> --allow-role <会話のID>（止めた文に出ている ID。全員なら --allow-role all）" if "担当ごとの上限を超えた" in t
                        else "budget.py <work> --allow-tokens")
                print(t + (f"。上限を超えた：続ける前にユーザーに【質問】で聞く。続けるなら {hint}" if t.startswith("△") else ""))
        except Exception:
            pass
        print(f"\n次：{nxt}")
        return 0
    items = overview(p)
    print("\n".join(items) if items else "作業フォルダも講座フォルダもまだ無い。\n\n次：手順0（聞き手と設定の一覧）から。SKILL.md の「まず決める：発表か講座か」")
    return 0


if __name__ == "__main__":
    sys.exit(main())
