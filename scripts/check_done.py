"""渡す前の確認：手順を最後までやったかを、できたファイルから機械的に確かめる（SKILL.md 手順7）。

    python <skill>/scripts/check_done.py "<資料名>_スライド.pptx"            # 作業フォルダは自動で探す
    python <skill>/scripts/check_done.py "<資料名>_スライド.pptx" --work _work/<資料名>

確かめること（✘ が1つでもあれば終了コード 1。直してから渡す）
  0. スキルの部品：scripts/ と assets/ が配布時のまま（scripts/MANIFEST.txt の指紋と同じ）。エージェントは部品を書き換えない
  （講座の本文の枚数は、スライドを作る前に設計メモの段階で check_memo.py が見る）
  1. 作業フォルダ：構成案（outline.md。講座は memo.md、質問回答デッキは answers.md）・build.py・notes.md がある
  1c. 構成案（発表の回だけ。<work>/outline.md）：check_outline.py と同じ確認。前提知識と丁寧さ、構成案のレビューの結果 outline_review.md と
      「## 引っかかりへの手当て」の突き合わせ（本文5枚以下の小さな依頼はレビュー結果を求めない）。
      講座の回は設計メモ（memo.md）で同じ照合をする（レビューの結果は memo_review.md、丁寧さの既定は 0）
  1a. 作業フォルダのスクリプト：置いてよいのは build.py と figs.py だけ。部品の代わり（自作の原稿HTML・図の描き方など）を作らない
  1b. 図の検査：図は <work>/figs.py に figkit の save で描いている（save が文字の大きさ・ラベルの数・文字と線の重なりを検査する）。
      作業フォルダのほかのスクリプトが savefig や PIL の ImageDraw で図を描いていたら ✘
  2. 描画の検査：<work>/render/shapes.json が今の pptx から作られていて（pptx より新しく、文字が食い違わない）、check_layout の ERROR が 0
  3. 読み上げ原稿：全スライドに発表者ノートが入っている
  3b. 原稿の中身（check_notes.py）：構成案・設計メモの「引っかかりへの手当て」で原稿に回した枚に、その中身（「…」の言い回し・用語の説明）がある。
      無ければ ✘。1文の長さ・中身の無いつなぎ・発表時間との釣り合いは △
  4. 原稿のページ：<資料名>_原稿.html が pptx と同じフォルダにあり、pptx より新しく、notes_html.py で作ってある（コメント機能つき）
  5. 完成後のレビュー：<work>/review.md に、判定と直した点が書いてある
  5a. レビューを別の担当がしたか：outline_review.md・memo_review.md・review.md があれば、AI の道具の会話の記録で、
      サブエージェントが outline.md・memo.md・スライドの画像を開いた跡があるか（review_record.py）。記録はあるのに跡が無ければ ✘
      （メインが自分でレビューした疑い）。記録が読めない道具（Antigravity など）は △（確かめられなかった）
  5b. 図の案どおりか：講座は設計メモの「図の案」、発表は構成案の「図で見せるもの」と、スライドの図の種類（流れ図・表・図）が合う。
      案と違う図・案に無い流れ図は ✘（変えたいなら、先に案を直して理由を書く）。流れ図が上限（本文4枚に1枚、最低2枚）を超えても ✘。
      図・表・大きな数字・比較のどれも無い本文のスライド（文だけの枚）も ✘。
      案に「本文の形」の列があれば、案の形（帰結・ラベル・展開…）の部品がその枚で使われているか。無ければ ✘
  （最後に参考の2行：make_deck の回数と作り直した枚（build_log.py）、会話ごとのモデル・思考の強さ・トークン（run_record.py が
   <work>/run_record.md に残す）。合否には使わない）
  6. 出典（講座の回だけ。<work>/memo.md の「事実と出典」の表）：確認が「○」の行の出典に、
     資料を特定できる手がかり（URL・DOI・「題名」・著者と年・条番号・頁や図の番号）がある。「厚生労働省」「薬機法」だけ、のような行は ✘
作業フォルダの探し方：pptx のあるフォルダから上へたどって _work を見つけ、次の順に探す
  _work/<資料名>/、講座なら _work/<講座フォルダ名>_<回の番号>/（01_〇〇_スライド.pptx の 01）、質問回答デッキならその下の 質問回答/
"""
import argparse
import contextlib
import io
import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_layout  # noqa: E402
import skill_manifest  # noqa: E402

QA = "_質問回答"
# 出典として資料を特定できる手がかり：URL・DOI・題名の括弧・「et al.」・年・条番号・頁/図/表/式の番号
SOURCE_HINT = re.compile(r"https?://|doi|10\.\d{4,}/|「[^」]+」|『[^』]+』|\"[^\"]+\"|“[^”]+”|et al\.|(?<!\d)(19|20)\d\d(?!\d)"
                         r"|第\s*\d+\s*条|p+\.\s*\d|\d+\s*頁|(図|表|式|Fig\.|Table)\s*\d", re.I)


def vague_sources(memo: Path):
    """設計メモの「事実と出典」の表で、確認が ○ なのに出典から資料を特定できない行の [(主張, 出典)]。表が無ければ None。"""
    text = memo.read_text(encoding="utf-8")
    m = re.search(r"^##\s*3\.?\s*事実と出典.*?$(.*?)(?=^##\s|\Z)", text, re.S | re.M)
    if not m:
        return None
    rows = [l for l in m.group(1).splitlines() if l.strip().startswith("|")]
    if len(rows) < 2:
        return None
    head = [c.strip() for c in rows[0].strip().strip("|").split("|")]
    try:
        i_src = next(i for i, h in enumerate(head) if "出典" in h)
        i_ok = next(i for i, h in enumerate(head) if "確認" in h)
    except StopIteration:
        return None
    bad = []
    for l in rows[2:]:
        cells = [c.strip() for c in l.strip().strip("|").split("|")]
        if len(cells) <= max(i_src, i_ok) or "○" not in cells[i_ok]:
            continue
        if not SOURCE_HINT.search(cells[i_src]):
            bad.append((cells[0], cells[i_src]))
    return bad


def deck_name(pptx: Path) -> str:
    """「講義メモ_スライド.pptx」→「講義メモ」"""
    return re.sub(r"_スライド$", "", pptx.stem)


def find_work_root(start: Path):
    for d in [start, *start.parents]:
        if (d / "_work").is_dir():
            return d / "_work"
    return None


def find_work(pptx: Path):
    """作業フォルダの候補を順に探す。見つからなければ None。"""
    name = deck_name(pptx)
    qa = name.endswith(QA)
    base = name[: -len(QA)] if qa else name
    root = find_work_root(pptx.parent)
    if root is None:
        return None
    cands = [root / base]
    m = re.match(r"^(\d{2})_", base)
    if m:                                    # 講座：講座フォルダ名＋回の番号
        cands.append(root / f"{pptx.parent.name}_{m.group(1)}")
    for c in cands:
        w = c / "質問回答" if qa else c
        if w.is_dir():
            return w
    return None


# _work に残りやすい一時ファイル・フォルダ（原稿HTML・LibreOffice の描画・書き出しの途中でできる）
TEMP_NAMES = re.compile(r"^(notes_html_tmp|render_lo_[0-9a-f]+|lo_profile.*|export_[0-9a-f]{16,}\.pptx|~\$.*)$")

def check(pptx: Path, work: Path | None, record: bool = True):
    """[(✔/✘, 項目, 説明)] を返す。"""
    from pptx import Presentation
    res = []
    name = deck_name(pptx)
    qa = name.endswith(QA)

    # 0. スキルの部品（エージェントが書き換えていないか）
    c = skill_manifest.changes()
    if c is None:
        res.append(("✘", "スキルの部品", "scripts/MANIFEST.txt が無い（スキルを配布元から入れ直す）"))
    elif any(c):
        changed, added, removed = c
        what = "・".join([f"書き換え {x}" for x in changed] + [f"追加 {x}" for x in added] + [f"削除 {x}" for x in removed][:6])
        res.append(("✘", "スキルの部品", f"配布時と違う：{what}（スキルの部品は書き換えない。元に戻し、動かない所はユーザーに伝える）"))
    else:
        res.append(("✔", "スキルの部品", "配布時のまま"))

    # 1. 作業フォルダ
    if work is None or not work.is_dir():
        res.append(("✘", "作業フォルダ", f"見つからない（_work/{name}/ などに build.py・notes.md・構成案を置く。--work で指定もできる）"))
    else:
        plan = ["answers.md"] if qa else ["outline.md", "memo.md"]   # 講座の回は memo.md が構成案を兼ねる
        missing = [f for f in ("build.py", "notes.md") if not (work / f).exists()]
        if not any((work / f).exists() for f in plan):
            missing.append("／".join(plan))
        res.append(("✘" if missing else "✔", "作業フォルダ",
                    f"{work} に {'・'.join(missing)} が無い" if missing else str(work)))

    # 1c. 構成案（発表の回だけ。講座の回は memo.md を check_memo.py が見る）
    outline = work / "outline.md" if work else None
    if outline and outline.exists() and not (work / "memo.md").exists() and not qa:
        import check_outline  # 関数の中で読む（check_outline → check_memo → check_done の循環を避ける）
        for mark, item, msg in check_outline.check(outline, require_review=True):
            if mark != "・":
                if item == "データ" and msg.startswith("data_1.md が無い"):
                    mark = "△"   # 渡す前に筋を組み直させない（数字の組を探すのは構成案の段。前の版の構成案にも無い）
                res.append((mark, f"構成案：{item}", msg))
        import slide_profile
        if not slide_profile.author(slide_profile.load_profile(work)):   # 仮の名前は入れない。渡すときに一言添えるため
            res.append(("・", "表紙の名前", "無し（名前の行を作らずに組んだ。入れるなら outline.md のオプションの表に「発表者名」を書いて組み直す）"))
    memo = work / "memo.md" if work else None
    if memo and memo.exists() and not qa:
        import check_memo
        for mark, item, msg in check_memo.check(memo, require_review=True):
            if item in ("前提と丁寧さ", "推論距離の手当て") and mark != "・":
                res.append((mark, f"設計メモ：{item}", msg))

    # 1a. 作業フォルダのスクリプト（部品の代わりを作っていないか）
    if work and work.is_dir():
        extra = sorted(p.name for p in work.glob("*.py") if p.name not in ("build.py", "figs.py"))
        res.append(("✘" if extra else "✔", "作業フォルダのスクリプト",
                    f"{'・'.join(extra)} がある（置いてよいのは build.py と figs.py だけ。原稿HTMLは notes_html.py、図は figs.py と figkit、"
                    "一覧画像は grid.py で作る。部品が動かないなら、代わりを作らずユーザーに伝える）" if extra else "build.py と figs.py だけ"))

    # 1b. 図の検査（figkit の save を通したか。別名のスクリプトで描いていないか）
    if work and work.is_dir():
        uses_figkit = re.compile(r"\bfrom\s+(figkit|figlib)\s+import|\bimport\s+(figkit|figlib)\b")
        draws = re.compile(r"\bsavefig\s*\(|\bImageDraw\b")
        bad_figs = []
        for py in sorted(work.glob("*.py")):
            t = py.read_text(encoding="utf-8", errors="replace")
            if py.name == "figs.py":
                if not (uses_figkit.search(t) and re.search(r"\bsave\s*\(", t)) or "savefig" in t:
                    bad_figs.append(py.name)
            elif draws.search(t) and not uses_figkit.search(t):
                bad_figs.append(py.name)
        if bad_figs:
            res.append(("✘", "図の検査", f"{'・'.join(bad_figs)} が figkit を通さずに図を描いている（savefig・ImageDraw を直接使うと、"
                        "文字の大きさ・文字と枠や線の重なりの検査が走らない。図は figs.py に `from figkit import save` で描き直し、WARN を直す）"))
        elif (work / "figs.py").exists():
            res.append(("✔", "図の検査", "figs.py は figkit の save で保存している"))

    # 2. 描画の検査
    shapes = work / "render" / "shapes.json" if work else None
    if not shapes or not shapes.exists():
        res.append(("✘", "描画の検査", "render/shapes.json が無い（render_check.ps1 → check_layout.py を走らせる）"))
    else:
        data = json.loads(shapes.read_text(encoding="utf-8-sig"))
        items = data["shapes"] if isinstance(data["shapes"], list) else [data["shapes"]]
        stale = check_layout.stale_slides(str(pptx), data, items)
        if shapes.stat().st_mtime < pptx.stat().st_mtime or stale:
            res.append(("✘", "描画の検査", "描画結果が今の pptx より古い（pptx を作り直したあとに描画し直していない）"))
        else:
            with contextlib.redirect_stdout(io.StringIO()) as out:
                code = check_layout.main(str(shapes), str(pptx))
            m = re.search(r"(\d+) errors, (\d+) warnings", out.getvalue())
            errs = int(m.group(1)) if m else (1 if code else 0)
            warns = int(m.group(2)) if m else 0
            eng = "（LibreOffice で描画。最後は画像を目で見て確かめる）" if data.get("engine") == "libreoffice" else ""
            res.append(("✘" if errs else "✔", "描画の検査", f"ERROR {errs}・WARN {warns}" + ("（直してから渡す）" if errs else "") + eng))

    # 3. 読み上げ原稿
    prs = Presentation(pptx)
    empty = [i for i, s in enumerate(prs.slides, 1)
             if not (s.has_notes_slide and s.notes_slide.notes_text_frame.text.strip())]
    res.append(("✘" if empty else "✔", "読み上げ原稿",
                f"原稿の無いスライド：{', '.join(map(str, empty))}" if empty else f"全{len(prs.slides)}枚に入っている"))
    # 3b. 原稿の中身：手当てで原稿に回した枚に中身があるか（✘）、1文の長さ・中身の無いつなぎ・発表時間との釣り合い（△）
    if work and (work / "notes.md").exists() and not qa:
        import check_notes
        stexts = {i: "\n".join(sh.text_frame.text for sh in s.shapes if getattr(sh, "has_text_frame", False) and sh.has_text_frame)
                  for i, s in enumerate(prs.slides, 1)}
        res += check_notes.check(work, slide_texts=stexts)

    # 4. 原稿のページ
    html = pptx.with_name(f"{name}_原稿.html")
    if not html.exists():
        res.append(("✘", "原稿のページ", f"{html.name} が無い（notes_html.py を走らせる）"))
    elif html.stat().st_mtime < pptx.stat().st_mtime:
        res.append(("✘", "原稿のページ", f"{html.name} が pptx より古い（pptx を直したら作り直す）"))
    elif not re.search(r'(?:sensei-slides|zemi-and-course) notes_html\.py|id="cm-export"', html.read_text(encoding="utf-8", errors="replace")):
        res.append(("✘", "原稿のページ", f"{html.name} が notes_html.py で作られていない（コメント機能が無い）。自作の HTML で代えず、"
                    "notes_html.py を走らせる（PowerPoint が止められるなら、ユーザーの許可を得てサンドボックスの外で動かす）"))
    else:
        res.append(("✔", "原稿のページ", html.name))

    # 5. 完成後のレビュー
    review = work / "review.md" if work else None
    if not review or not review.exists():
        res.append(("✘", "完成後のレビュー", "review.md が無い（手順5b のレビューの判定と直した点を書く）"))
    else:
        t = review.read_text(encoding="utf-8")
        ok = "判定" in t and ("直した" in t or "直す点" in t or "指摘" in t)
        res.append(("✔" if ok else "✘", "完成後のレビュー",
                    "review.md あり" if ok else "review.md に「判定」と「直した点」が無い"))

    # 5a. レビューを別の担当がしたか（AI の道具の会話の記録。review_record.py）
    if work and record:
        import review_record
        found = review_record.actors(work, __import__("time").time() - (review_record.WINDOW_DAYS + 60) * 86400)
        for k, (_, fn, _) in review_record.KINDS.items():
            if (work / fn).exists():
                res.append(review_record.check(work, k, found=found))

    # 5c. 結論の一文：本文の枚（確認問題・解答・区切り・漸進表示を除く）に、結論か要約の一文がある
    import structures
    psrc = (work / "memo.md") if work and (work / "memo.md").exists() else (work / "outline.md") if work and (work / "outline.md").exists() else None
    roles = structures.plan_roles(psrc.read_text(encoding="utf-8"), "memo" if psrc.name == "memo.md" else "outline") if psrc else None
    if roles:
        bad_roles = structures.role_mismatches(prs, roles)
        res.append(("✘" if bad_roles else "✔", "役割と結論",
                    "；".join(f"[{i}] {m}" for i, m in bad_roles[:6]) if bad_roles
                    else f"{psrc.name} の役割どおり（本文の枚には結論の一文、ほかの枚には無い）"))
    elif psrc:   # 構成案・設計メモはあるのに役割の列が無い（質問回答のデッキは対象外）
        res.append(("✘", "役割と結論", f"{psrc.name} の表に「役割」の列が無い（枚ごとに {'・'.join(structures.ROLES)} から選ぶ）"))

    # 5b. 図の案どおりか
    import figplan
    src = (work / "memo.md") if work and (work / "memo.md").exists() else (work / "outline.md") if work and (work / "outline.md").exists() else None
    plan = figplan.plan_from_text(src.read_text(encoding="utf-8"), "memo" if src.name == "memo.md" else "outline") if src and not qa else None
    if plan is not None:
        skip = {1} | {i for i, s in enumerate(prs.slides, 1)
                     if any(sh.name == "見出し" and sh.has_text_frame and re.search(r"問題|解答|想定質問", sh.text_frame.text) for sh in s.shapes)}
        bad_plan = figplan.mismatches(prs, plan, skip)
        res.append(("✘" if bad_plan else "✔", "図の案どおりか",
                    "；".join(f"[{i}] {m}" for i, m in bad_plan[:6]) + "（案どおり描くか、案を直して理由を書く）" if bad_plan
                    else f"{src.name} の図の案と合っている"))
        body = [i for i in range(1, len(prs.slides) + 1) if i not in skip]
        bare = [i for i in body if figplan.slide_type(prs.slides[i - 1], prs.slide_width, prs.slide_height) == "文のみ"
                and any(sh.name == "見出し" for sh in prs.slides[i - 1].shapes)]   # ●見出しの無い表紙・区切りは除く
        res.append(("✘" if bare else "✔", "図の無いスライド",
                    f"文だけの本文のスライド：{'・'.join(map(str, bare))}。{figplan.NO_FIGURE_HINT}" if bare
                    else "本文のスライドすべてに図・表・大きな数字・比較がある"))
        import structures
        fplan = structures.plan_forms(src.read_text(encoding="utf-8"), "memo" if src.name == "memo.md" else "outline")
        if fplan is not None:
            bad_form = structures.mismatches(prs, fplan, skip)
            # 図・表・流れ図などがある枚は、図が案の形の中身を担っていることがある（本文と図で同じことを2回言わせない）→ △
            hard = [(i, m) for i, m in bad_form if not figplan.actual_kinds(prs.slides[i - 1])]
            soft = [(i, m) for i, m in bad_form if (i, m) not in hard]
            if hard:
                res.append(("✘", "本文の形", "；".join(f"[{i}] {m}" for i, m in hard[:6]) + "（案の形の部品で組むか、案を直す。references/structures.md）"))
            if soft:
                res.append(("△", "本文の形", "；".join(f"[{i}] {m}" for i, m in soft[:6])
                            + "（図が同じ中身を担っているなら、本文で言い直さなくてよい。そのときは案の本文の形を「箇条」（短い要点だけ）に直し、plan_changes.md に1行）"))
            if not bad_form:
                res.append(("✔", "本文の形", f"{src.name} の本文の形と合っている"))
        n_flow = sum("流れ図" in figplan.actual_kinds(prs.slides[i - 1]) for i in body)
        mark, msg = figplan.flow_check(n_flow, len(body), src.read_text(encoding="utf-8"), src.name)
        res.append((mark or "✘", "流れ図の数", msg))
        runs_ = figplan.monotony(prs, skip)
        res.append(("△" if runs_ else "✔", "スライドの型",
                    "同じ型が続いている：" + "、".join(f"{a}〜{b}枚目が「{t}」" for a, b, t in runs_)
                    + f"（{figplan.MAX_RUN}枚まで。内容に合う別の型にできないか見直す。references/figures.md「スライドの型」）" if runs_
                    else f"同じ型が {figplan.MAX_RUN} 枚を超えて続いていない"))

    # 5d. 後始末：同じ回の古い版の pptx と、_work に残った一時ファイル
    m = re.match(r"^(\d{2})_", pptx.name)
    if m:
        old = [p.name for p in pptx.parent.glob(f"{m.group(1)}_*_スライド.pptx") if p.resolve() != pptx.resolve()]
        if old:
            res.append(("△", "古い版のスライド", f"同じ回の別の pptx が残る：{'・'.join(old)}（題名を変える前の版など。この回で作った古い版なら消し、"
                        "迷うならユーザーに伝える）"))
    if work and work.parent.name == "_work":
        junk = [p.name for p in work.parent.iterdir() if TEMP_NAMES.match(p.name)]
        if junk:
            res.append(("△", "一時ファイル", f"_work に一時ファイル・フォルダが残る：{'・'.join(junk[:5])}（作業の途中でできたもの。消す）"))

    # 6. 出典（講座の回の設計メモだけ）
    memo = work / "memo.md" if work else None
    bad = vague_sources(memo) if memo and memo.exists() else None
    if bad is not None:
        if bad:
            res.append(("✘", "出典", f"○ なのに資料を特定できない行が {len(bad)} 件（書名・URL・頁などを足すか、確認を × にする）："
                        + " / ".join(f"「{a[:14]}」→{b[:20]}" for a, b in bad[:4])))
        else:
            res.append(("✔", "出典", "○ の行はすべて資料を特定できる"))

    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description="渡す前の確認（手順を最後までやったか）")
    ap.add_argument("pptx")
    ap.add_argument("--work", help="作業フォルダ（省略時は自動で探す）")
    ap.add_argument("--no-record", action="store_true", help="レビューの会話の記録を見ない（見本の確認など。ふだんは付けない）")
    ap.add_argument("--all", action="store_true", help="✔ の行も1行ずつ出す（ふだんは ✔ を1行にまとめる）")
    a = ap.parse_args(argv)
    pptx = Path(a.pptx).resolve()
    if not pptx.exists():
        print(f"[ERROR] {pptx} が無い")
        return 1
    work = Path(a.work).resolve() if a.work else find_work(pptx)
    res = check(pptx, work, record=not a.no_record)
    import report
    report.show(res, a.all)
    if work:
        import build_log
        t = build_log.line(work)
        if t:
            print(f"（記録）作り直し：{t}")
    if work and not a.no_record:
        try:
            import run_record
            print(f"（記録）会話：{run_record.short(run_record.save(work))}（{work.name}/run_record.md）")
        except Exception as e:   # 記録が読めなくても確認の結果は出す
            print(f"（記録）会話の記録を集められなかった（{type(e).__name__}）")
    bad = sum(m == "✘" for m, _, _ in res)
    print(f"\n{'渡してよい' if not bad else f'✘ が {bad} 件。直してから渡す'}（{pptx.name}）")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
