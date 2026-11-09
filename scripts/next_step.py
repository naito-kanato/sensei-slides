"""今どこまで済んでいて、次に何をするか：作業フォルダの中のファイルから決める（覚えていなくても戻れるように）。

    python <skill>/scripts/next_step.py                    # スライドを作るフォルダの一番上で：作業の一覧と、それぞれの次の手順
    python <skill>/scripts/next_step.py _work/<資料名>     # その作業フォルダの、済んだ手順と次の手順
    python <skill>/scripts/next_step.py <講座フォルダ>      # 講座：次に作る回と、その作業フォルダ

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


def _fails(res):
    return [f"{item}：{msg[:60]}" for mark, item, msg in res if mark == "✘"]


def find_pptx(work: Path):
    """作業フォルダから作られたデッキ（check_done.find_work で作業フォルダに戻れる *_スライド.pptx）。新しいもの。"""
    import check_done
    here = sorted(work.glob("*_スライド.pptx"), key=lambda p: p.stat().st_mtime)   # 作業フォルダの中に出したデッキ（見本など）
    if here:
        return here[-1]
    root = work.parent.parent if work.parent.name == "_work" else work.parent
    if work.name == "質問回答":
        root = work.parent.parent.parent
    hits = []
    for p in root.rglob("*_スライド.pptx"):
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


def steps_for(work: Path):
    """[(済んだか, 手順, 説明)] と 次の手順の文。"""
    work = Path(work)
    kind = "answers" if (work / "answers.md").exists() else "memo" if (work / "memo.md").exists() else "outline"
    out = []

    def add(ok, step, msg=""):
        out.append((ok, step, msg))
        return ok

    nxt = None
    # 1. 構成（ゼミ：outline.md、講座：memo.md、質問回答：answers.md）
    plan = work / {"memo": "memo.md", "outline": "outline.md", "answers": "answers.md"}[kind]
    if not plan.exists() and re.search(r"_\d{2}$", work.name) and kind == "outline":   # 講座の回（設計メモはまだ）
        import data
        found = data.files(work)
        add(bool(found), "数字を探す（data_N.md）", "・".join(f.name for f in found) if found else "まだ")
        add(False, "設計メモ（memo.md）", "まだ")
        return out, ("references/course.md 手順4⓪：数字を探す担当を2人、同時に起動（`brief.py 数字を探す担当 <work> --n 1` と `--n 2`）" if not found else
                     "references/course.md 手順4①：設計の担当（`brief.py 設計の担当 <work>`）。data_N.md を見てから筋を決め、data.py merge で3b節に入れる"
                     + ("（数字を探す担当を2人起動したなら、もう1人が返してから）" if len(found) == 1 else ""))
    if not plan.exists():
        add(False, "構成案", "outline.md が無い")
        return out, ("手順2：構成案（outline.md）を作る。`guide.py steps 2`。講座なら references/course.md の手順4（設計メモ memo.md）")
    if kind == "outline":
        import check_outline
        res_ = check_outline.check(plan)
        if (work / "build.py").exists():   # 組み始めたあとは、数字の組の抜けで構成案に戻さない（前の版で作り始めた構成案にも無い）
            res_ = [r for r in res_ if not (r[1] == "データ" and r[2].startswith("data_1.md が無い"))]
        bad = _fails(res_)
        rv = work / "outline_review.md"
        add(not bad, "構成案の確認（check_outline）", "；".join(bad[:3]))
        add(rv.exists(), "構成案のレビュー（outline_review.md）")
        if bad and not nxt:
            nxt = f"手順2：check_outline の ✘ を直す（python {SKILL}/scripts/check_outline.py {plan.as_posix()}）"
        if not rv.exists() and not nxt:
            nxt = "手順2：構成案を【別のエージェント】にレビューさせ、結果を outline_review.md に残す（references/outline-review.md の B）。そのあとユーザーに構成案を見せて OK をもらう"
    elif kind == "memo":
        import check_memo
        bad = _fails(check_memo.check(plan))
        rv = work / "memo_review.md"
        add(not bad, "設計メモの確認（check_memo）", "；".join(bad[:3]))
        import facts
        _, fh, frows = facts.memo_facts(plan.read_text(encoding="utf-8"))
        i_ok = next((k for k, h in enumerate(fh) if "確認" in h), 3)
        todo = [r for r in frows if facts.unchecked(r, i_ok)]
        split = [f for f in work.glob("facts_*.md") if f.name != "facts_diff.md"]
        add(not todo, "事実の裏取り（3節の確認）", f"まだ {len(todo)} 行" if todo else "")
        add(rv.exists(), "設計メモのレビュー（memo_review.md）")
        if bad and not nxt:
            nxt = f"references/course.md 手順4：check_memo の ✘ を直す（python {SKILL}/scripts/check_memo.py {plan.as_posix()}）"
        if todo and not nxt and not (work / "build.py").exists():   # 制作に進んだあとは、裏取りに戻さない（直しの担当が足した行など）
            nxt = (f"references/course.md 手順4②：裏取りの担当（facts_N.md ごとに1人、同時に）の結果を待ち、python {SKILL}/scripts/facts.py merge {work.as_posix()}"
                   if split else
                   f"references/course.md 手順4①の終わり：python {SKILL}/scripts/facts.py split {work.as_posix()} --n 2 → 裏取りの担当を2人、同時に起動")
        if not rv.exists() and not nxt:
            nxt = "references/course.md 手順4：設計メモを【別のエージェント】にレビューさせ、結果を memo_review.md に残し、9節に手当てを書く"
    else:
        add(True, "答えの下書き（answers.md）")
    # 2. 図
    figs = work / "figs.py"
    pngs = list((work / "figs").glob("*.png")) if (work / "figs").is_dir() else []
    fig_ok = figs.exists() and pngs and max(p.stat().st_mtime for p in pngs) >= figs.stat().st_mtime - 1
    if add(bool(fig_ok), "図（figs.py → figs/）", "" if fig_ok else ("figs.py が無い" if not figs.exists() else "figs.py を直したあと描き直していない")) is False and not nxt:
        import brief
        nc = len(brief.card_numbers(work))
        who = (f"カードが {nc} 枚なので制作役を2人、同時に起動（`brief.py 制作役 <work> --part 1/2` は図と前半、`--part 2/2` は後半。"
               "merge は仕上げ役が最初にする）" if nc >= brief.SPLIT_AT else
               "制作役1人（`brief.py 制作役 <work>`）が figs.py で図、カードを1枚ずつ読んで parts/NN.py・parts/NN.md、scaffold.py <work> --merge で戻す")
        nxt = ("手順3〜5（SKILL.md「役割を分ける」）：" + ("" if nc else "python <skill>/scripts/scaffold.py <work> で骨組みとカード（cards/）を作り、") + who +
               "。そのあと仕上げ役1人が python <skill>/scripts/make_deck.py <work> で組んで検査して直し、原稿HTMLまで")
    # 3. ビルド
    build = work / "build.py"
    notes = work / "notes.md"
    pptx = find_pptx(work) if build.exists() else None
    add(build.exists(), "build.py")
    add(notes.exists(), "原稿（notes.md）")
    if pptx is None:
        add(False, "スライド（*_スライド.pptx）", "まだ組んでいない")
        if not nxt:
            nxt = ("手順4：python <skill>/scripts/scaffold.py <work> で骨組みとカード（cards/）を作り、カードを1枚ずつ読んで parts/NN.py・parts/NN.md を書き、"
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
    # 6. 原稿のページ
    html = pptx.with_name(pptx.name.replace("_スライド.pptx", "_原稿.html"))
    if add(_newer(html, pptx), "原稿のページ（*_原稿.html）", "" if _newer(html, pptx) else ("無い" if not html.exists() else "pptx より古い")) is False and not nxt:
        nxt = f"手順6：python {SKILL}/scripts/notes_html.py で原稿のページを作る（`guide.py steps 6`）"
    # 7. 渡す前の確認
    if not nxt:
        nxt = f"手順7：python {SKILL}/scripts/check_done.py \"{pptx.as_posix()}\" を走らせる。「渡してよい」が出たらユーザーに渡す（✘ があれば直す）"
    return out, nxt


def course_next(course: Path):
    """講座フォルダ：作った回と、次に作る回の作業フォルダ。"""
    made = sorted({p.name[:2] + "_" for p in course.glob("[0-9][0-9]_*_スライド.pptx")})   # 回の番号ごとに1つ（題名を変える前の古い版を数えない）
    readme = course / "00_README.md"
    root = course.parent / "_work"
    works = sorted(root.glob(f"{course.name}_[0-9][0-9]")) if root.is_dir() else []
    lines = [f"講座フォルダ：{course.name}（作った回 {len(made)}：{'・'.join(m[:2] for m in made) or 'なし'}）"]
    if not readme.exists():
        return lines, "references/course.md 手順1〜3：ヒアリング → 00_README.md（全体の地図）を作る"
    unfinished = [w for w in works if not any(m.startswith(w.name[-2:] + "_") for m in made)]
    if unfinished:
        w = unfinished[0]
        return lines, f"{w.name} の途中：python {SKILL}/scripts/next_step.py {(root / w.name).as_posix()} で続きを見る"
    n = max(int(m[:2]) for m in made) + 1 if made else 1
    first = (f"数字を探す担当を2人、同時に起動（`brief.py 数字を探す担当 _work/{course.name}_{n:02d} --n 1` と `--n 2`）→ "
             f"設計の担当が data_N.md を見て _work/{course.name}_{n:02d}/memo.md を書く（references/course.md 手順4）")
    return lines, (f"第{n}回：{first}。設計の前に、前の回のコメント・答え（00_README.md のつまずき一覧）を読む" if made else
                   f"第1回：ユーザーが 00_README.md の地図に OK を出したら、{first}")


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


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    p = Path(argv[0]) if argv else Path.cwd()
    if not p.exists():
        print(f"{p} が無い")
        return 1
    if (p / "00_README.md").exists() and not any((p / f).exists() for f in ("outline.md", "memo.md")):
        lines, nxt = course_next(p)
        print("\n".join(lines))
        print(f"\n次：{nxt}")
        return 0
    if any((p / f).exists() for f in ("outline.md", "memo.md", "answers.md", "build.py")) or p.parent.name == "_work":
        steps, nxt = steps_for(p)
        print(f"作業フォルダ：{p.name}")
        try:
            import budget
            solo = budget.solo_problem(p.resolve())
        except Exception:
            solo = None
        if solo:
            print(solo)
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
