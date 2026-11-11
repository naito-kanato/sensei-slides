"""構成案（outline.md）・設計メモ（memo.md）の表から、build.py と notes.md の骨組みを作る。決まった形の部分を AI が書かずに済ませる
（書いた量は読む量の約8倍の重さで使用量に数えられる）。

    python <skill>/scripts/scaffold.py <work>           # <work>/build.py と <work>/notes.md を作る（すでにあれば作らない）
    python <skill>/scripts/scaffold.py <work> --force   # 上書きする（書きかけを捨てるので、ふつうは使わない）
    python <skill>/scripts/scaffold.py <work> --merge   # 書き手が書いた parts/NN.py・parts/NN.md を build.py・notes.md の N 枚目に戻す
    python <skill>/scripts/scaffold.py <work> --try NN  # parts/NN.py の1枚だけを組み、本文の形・図・結論・字数を短く出す（描かない）
    python <skill>/scripts/scaffold.py <work> --source <資料.pdf|.txt>   # カードに入れる抜き出しの資料（省くと 資料/ に1つだけある PDF・テキスト）

骨組みに入るもの
  build.py：スキルの読み込み、Deck、表紙、枚ごとに deck.slide(タイトル, summary=青帯) と s.heading(●見出し)、
            本文の形の列に合った部品の呼び出し（本文の要点の列の語を入れておく）、図の行（図で見せるものの列。コメントにしてある）、
            確認問題・解答の枚（役割の列）。「TODO」の所を中身に書き換える
  notes.md：枚ごとの「## 番号」と、その枚の目安（字数・ノートへの列・原稿に回した手当て）をコメントで
  cards/NN.md：本文の枚ごとのカード。その枚を書くのに要るものだけ（筋の問いと答え・前とこの枚と次の青帯・前の枚からの語と書き方・
            見出し・本文の形・要点・図・ノートへ・手当て・資料の範囲とその抜き出し（excerpt.py）・使う部品の書き方・目安・骨組みのコード）。書き手はカードとその範囲の資料だけを見て、
            1枚ずつ parts/NN.py（build.py のその枚の所）と parts/NN.md（原稿）を書く。全ページを一度に書かない（SKILL.md 手順4）
骨組みのあと：figs.py に図を描き、build.py の TODO と図の行、notes.md を書いて、make_deck.py で組んで検査する。
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
sys.path.insert(0, str(HERE))

EMPTY = ("", "—", "-", "－", "なし")


def q(s: str) -> str:
    """Python の文字列の中身に（" と \\ を逃がす）。"""
    return (s or "").replace("\\", "\\\\").replace('"', '\\"')


def items_of(cell: str):
    """本文の要点のセル → 項目のリスト（／ / ； 改行で分ける。「★」の付いた項目は赤字 {r:…} にする）。
    「・」では分けない（「眠気・気分・集中」のような並びを1項目に保つ）。"""
    cell = re.sub(r"<br\s*/?>", "／", cell or "")
    parts = [p.strip() for p in re.split(r"\s*(?:／|/|；|;)\s*", cell) if p.strip()]
    return [underline(red(re.sub(r"\s*〔[^〕]*〕", "", p))) for p in parts[:5]]


def underline(p: str) -> str:
    """「PSR B1913+16（下線）」→「{u:PSR B1913+16}」（構成案の下線の印を、骨組みの書き方に）。"""
    return re.sub(r"((?:[A-Za-z0-9+\-.]+ )*[A-Za-z0-9+\-.]+|[^\sA-Za-z0-9・、：:／/（(]+)（下線）", r"{u:\1}", p)


def red(p: str) -> str:
    """「★」の付いた要点 → 赤字。★が語の前にあれば、そこから次の「・」「、」「（」までだけ（「腕 4 km・★他方は収縮・…」）。
    ★が頭か終わりにだけあれば、「見出し：説明」の説明の側（無ければ全体）を赤字にする（設計メモで決めた強調を骨組みに残す）。"""
    if "★" not in p:
        return p
    m = re.search(r"★([^・、，,（(）)★]+)", p)
    core = p.replace("★", "").strip()
    if m and not p.strip().startswith("★") and m.group(1).strip():
        seg = m.group(1).rstrip()
        return (p[:m.start()] + "{r:" + seg + "}" + p[m.start() + 1 + len(seg):]).replace("★", "")
    h, sep, rest = core.partition("：")
    return f"{h}：{{r:{rest.strip()}}}" if sep and rest.strip() else f"{{r:{core}}}"


def plan(work: Path):
    """(kind, 題, 行のリスト[{列名: 値}], 手当て {番号: 行})。"""
    from check_memo import table_rows
    import check_notes
    if (work / "memo.md").exists():
        kind, src, sec = "memo", work / "memo.md", "話の順番"
    elif (work / "outline.md").exists():
        kind, src, sec = "outline", work / "outline.md", "構成"
    elif (work / "answers.md").exists():          # 質問回答デッキ：answers.md の「## 構成」の表（コメント・元の枚の列つき）
        kind, src, sec = "answers", work / "answers.md", "構成"
    else:
        raise SystemExit(f"{work} に outline.md も memo.md も無い（先に構成案・設計メモを作る）")
    text = src.read_text(encoding="utf-8")
    rows = table_rows(text, sec)
    if not rows:
        raise SystemExit(f"{src.name} に「{sec}」の表が無い")
    head = [h.strip() for h in rows[0]]
    out = []
    for r in rows[1:]:
        if not r or not r[0].strip().isdigit():
            continue
        out.append({h: (r[k].strip() if k < len(r) else "") for k, h in enumerate(head)} | {"#": int(r[0])})
    m = re.search(r"^#\s+(?:設計メモ|構成案)[^：:]*[：:]\s*(.+?)\s*(?:（[^）]*）)?\s*$", text, re.M)
    title = m.group(1).strip() if m else work.name
    care = {}
    for n, say, terms, line in check_notes.care_items(text):
        care.setdefault(n, []).append(re.sub(r"^\s*[-*]\s*", "", line))
    return kind, title, out, care


def col(row, *names):
    for n in names:
        for k, v in row.items():
            if isinstance(k, str) and n in k:
                return v
    return ""


def qs(items):
    """["a", "b"] の形の文字列（f 文字列の中に \\ を書かないため）。"""
    return ", ".join('"' + q(p) + '"' for p in items)


def form_code(forms: str, pts):
    """本文の形 → 部品の呼び出しの行。要点は、形の入れる所の書き方（structures.SLOTS）から入れる所に割り振る。
    入れる所が空なら TODO（書き手が埋める）。"""
    import structures
    out = []
    keys = [k for k in structures.form_key(forms or "") if isinstance(k, str)]
    for k, ps in structures.assign(keys, list(pts)):
        ps = ps or []
        if k in ("帰結", "縦の結論"):
            pre, then = [], ""
            for p in ps:
                if "⇒" in p and not then:
                    a, _, b = p.partition("⇒")
                    if a.strip():
                        pre.append(a.strip())
                    then = b.strip()
                else:
                    pre.append(p)
            pre = pre or ["TODO 前提"]
            then = then or "TODO 帰結の一言（赤字になる）"
            if k == "帰結":
                out.append("s.lead([" + qs(pre[:3]) + f'], "{q(then)}")')
            else:
                out.append(f's.lead_down("{q(chr(10).join(pre[:3]))}", "{q(then)}")')
        elif k == "ラベル":
            for p in (ps or ["TODO 見出し：説明"])[:4]:
                h, _, rest = p.partition("：")   # 半角の「:」は文字の書式 {r:…} に使うので、全角の「：」だけで分ける
                body, _, then = rest.partition("⇒")
                then_arg = f', then="{q(then.strip())}"' if then.strip() else ""
                out.append(f's.block("{q(h.strip())}：", ["{q(body.strip()) or "TODO 説明"}"]{then_arg})')
        elif k == "場合分け":
            pairs = [p.partition("：")[::2] for p in ps] or [("TODO 条件", "TODO 説明")]
            out.append("s.cases([" + ", ".join(f'("{q(c.strip())}", "{q(d.strip()) or "TODO 説明"}")' for c, d in pairs[:3]) + "])")
        elif k == "展開":
            p = ps[0] if ps else "TODO 左 → TODO 右"
            a, _, b = p.partition("→")
            out.append(f's.develop("{q(a.strip())}", "{q(b.strip()) or "TODO 結果"}")')
            out += [f's.p("{q(x)}")   # TODO 展開に入らなかった要点（入れる所を決める）' for x in ps[1:]]
        elif k == "問い":
            for p in (ps or ["TODO 問い？⇒ TODO 確かめた結果"])[:3]:
                a, _, b = p.partition("⇒")
                out.append(f's.ask("{q(a.strip())}", "{q(b.strip()) or "TODO 確かめた結果"}")')
        elif k == "手順":
            steps = []
            for p in ps:
                chunks = re.split(r"(?<![0-9])[0-9０-９][.．](?![0-9])\s*", p)
                steps += [x.strip() for x in (chunks[1:] if len(chunks) > 1 else chunks) if x.strip()]   # 「1.」の前（見出し）は外す
            out.append("s.numbered([" + qs((steps or ["TODO 段1", "TODO 段2"])[:5]) + "])")
        elif k == "式の注釈":
            out.append('# TODO 式と項の注釈：s.peq(...) と s.defs(...)（references/structures.md「式の注釈」）'
                       + (f'  要点：{"／".join(ps)[:80]}' if ps else ""))
        elif k == "余り":
            out += [f's.p("{q(p)}")   # TODO 形の入れる所の書き方でない要点（入れる所に移すか、ノートへ）' for p in ps]
        else:
            out += [f's.p("{q(p)}")' for p in (ps or ["TODO 要点"])[:4]]
    return out


def misplaced(work: Path, kind) -> str:
    """作業フォルダの置き場所の誤り（出力先 OUT は「作業ディレクトリ/_work/<名前>/」の2つ上から決めるので、ずれると出力が二重のフォルダに入る）。"""
    if kind == "answers":
        return ""
    course = re.sub(r"_\d{2}$", "", work.name)
    if kind == "memo" and work.parents[1].name == course:
        return (f"_work/ が講座フォルダ {course}/ の中にある（出力が {course}/{course}/ に入る）。"
                f"_work/ を作業ディレクトリ直下（{course}/ と並ぶ所）に移してから scaffold.py をやり直す")
    return ""


def build_py(work: Path, kind, title, rows) -> str:
    try:
        rel = os.path.relpath(SKILL / "scripts", work).replace("\\", "/")
    except ValueError:      # Windows でドライブが違う（作業フォルダが C:、スキルが D: など）ときは、絶対パスで
        rel = (SKILL / "scripts").as_posix()
    if kind == "memo":
        course = re.sub(r"_\d{2}$", "", work.name)
        num = re.search(r"_(\d{2})$", work.name)
        nn = num.group(1) if num else "01"
        short_title = q(re.sub(r"^第\d+回\s*", "", title))
        out_line = f'OUT = HERE.parents[1] / "{q(course)}" / "{nn}_{short_title}_スライド.pptx"'
    elif kind == "answers":
        out_line = 'OUT = HERE / "TODO_質問回答_スライド.pptx"   # 元のデッキと同じフォルダ・「<資料名>_質問回答_スライド.pptx」に'
    else:
        out_line = f'OUT = HERE.parents[1] / "{q(work.name)}" / "{q(work.name)}_スライド.pptx"   # 発表フォルダ（資料置き場と同じ）。一覧の「出力先」があれば合わせる'
    L = [f'"""{title}（{kind == "memo" and "設計メモ memo.md" or "構成案 outline.md"} の表から scaffold.py が作った骨組み。TODO を書き換える）。',
         "",
         "    python <skill>/scripts/make_deck.py <この作業フォルダ>   # 図→組む→描く→検査を1回で",
         '"""',
         "import sys",
         "from pathlib import Path",
         "",
         "HERE = Path(__file__).resolve().parent",
         f'sys.path.insert(0, str((HERE / "{rel}").resolve()))',
         "from set_notes import load_notes  # noqa: E402",
         "from slide_profile import author, deck_options, load_profile  # noqa: E402",
         "from zemi import Deck  # noqa: E402",
         "",
         f'T = "{q(title)}"',
         'FIG = HERE / "figs"',
         out_line,
         "",
         "P = load_profile(HERE)",
         'AUTHOR = author(P)   # 表紙の名前（発表は一覧の「発表者名」、無ければ空。講座は「講座名（全N回）」。仮の名前を入れない）',
         'deck = Deck(workdir=HERE / "build", **deck_options(P))   # テンプレートを選ぶなら deck_options(P, name="テンプレート2") など',
         ""]
    if any(col(r, "役割") in ("確認問題", "解答") for r in rows):
        L += ["",
              "def qa(s, items, size=20, gap=0.45):",
              '    """確認問題・解答の本文。items = [(番号, 本文)]。番号は「1-1」の形（原稿HTMLの「1-1 に答える」ボタンになる）"""',
              "    s.at(1.0, 2.0)",
              "    for j, (k, txt) in enumerate(items):",
              '        s.p("{b:" + k + "}　" + txt, size=size, gap=gap if j < len(items) - 1 else 0.2)',
              ""]
    qa_slices = qa_split(work, kind, rows)
    for r in rows:
        n, role = r["#"], col(r, "役割") or "本文"
        head = col(r, "●見出し")
        stitle = col(r, "タイトル") if kind == "outline" else ""
        stitle = stitle if stitle not in EMPTY and "表紙" not in stitle and "区切り" not in stitle else ""
        summary = col(r, "青帯", "結論")
        fig = col(r, "図で見せるもの", "図")
        pts = items_of(col(r, "本文の要点"))
        L.append(f"# {'-' * 64} {n} {head if head not in EMPTY else role}")
        if role == "表紙":
            lines = pts[:1] if pts and kind == "outline" else ["T"]
            first = f'["{q(lines[0])}"]' if lines != ["T"] else "[T]"
            L.append(f"deck.title_slide({first}, author=AUTHOR)" if n == 1 else
                     f'deck.title_slide(["TODO 題名"], subtitle="TODO")   # 論文の表紙など（{q(fig) or "表紙"}）')
        elif role == "区切り":
            L.append(f'deck.section({n}, "{q(head or "TODO 章の名前")}")')
        elif role == "想定質問":
            L.append("s = deck.slide(T)   # summary なし：帯も●も無い枚になる")
            L.append('s.heading("想定質問")')
            pairs = [(k, qq, re.sub(r"\s*〔[^〕]*〕", "", a)) for k, qq, a, _ in qa_slices.get(n, [])]   # 〔出どころ〕はスライドに出さない
            L.append("s.at(1.0, 1.9)")
            L.append("s.qa_pairs([" + ", ".join(f'("{q(k)}", "{q(qq)}", "{q(a)}")' for k, qq, a in pairs)
                     + "])   # 1行25字までに \\n を入れて折る（回答は2〜3行）。戻る枚は原稿に")
        elif role in ("確認問題", "解答"):
            L.append("s = deck.slide(T)   # summary なし：帯も●も無い枚になる")
            L.append(f's.heading("{q(head or role)}")')
            L.append(f'qa(s, [("TODO 番号", "TODO {role}の本文")])   # 設計メモの6節から')
        elif role != "本文":
            L.append(f's = deck.slide("{q(stitle or head or role)}")   # {role}：結論なし（帯も●も無い枚）')
            L.append('s.p("TODO")')
        else:
            first = ('"' + q(stitle) + '"') if stitle else "T"
            summ = q(summary) if summary not in EMPTY else "TODO 結論の一文"
            L.append(f's = deck.slide({first}, summary="{summ}")')
            if head not in EMPTY:
                L.append(f's.heading("{q(head)}")')
            L += form_code(col(r, "本文の形"), pts)
            import figplan
            ppt = figplan.pptx_part(fig) if fig not in EMPTY else None
            if ppt:
                L.append(f'# TODO {fig[:60]}（画像ではなく {ppt} で組む）')
            elif fig not in EMPTY:
                import figplan
                mn = figplan.parse_fig(fig)[1]
                part = next((x[2] for x in figplan.FIG_MENU if x[0] == mn), "")
                hint = f"。{mn}は {part}" if mn else ""
                L.append(f'# s.figure_beside(FIG / "s{n:02d}.png", caption="（TODO 出典）")   # 図：{fig[:60]}（図は figs/s{n:02d}.png{hint}）')
        L.append("")
    L += ['NOTES = load_notes(HERE / "notes.md")',
          "for i, sl in enumerate(deck.slides, 1):",
          "    if i in NOTES:",
          "        sl.notes(NOTES[i])",
          "OUT.parent.mkdir(parents=True, exist_ok=True)",
          "deck.save(OUT, title=T, author=AUTHOR)"]
    return "\n".join(L) + "\n"


def qa_split(work: Path, kind, rows):
    """{想定質問の枚の番号: [(番号, 質問, 回答, 戻る枚), …]}：構成案の「## 想定質問」の表を、役割「想定質問」の枚に2組ずつ割り振る。"""
    if kind != "outline":
        return {}
    import structures
    items = structures.expected_qa((work / "outline.md").read_text(encoding="utf-8")) or []
    slides = [r["#"] for r in rows if col(r, "役割") == "想定質問"]
    k = structures.QA_PER_SLIDE
    return {n: items[i * k:(i + 1) * k] for i, n in enumerate(slides)}


def notes_md(kind, rows, care, minutes=None) -> str:
    body = [r for r in rows if (col(r, "役割") or "本文") == "本文"]
    per = f"{minutes * 300 / max(len(body), 1):.0f}字" if minutes else "400字"
    L = []
    for r in rows:
        n, role = r["#"], col(r, "役割") or "本文"
        note = col(r, "ノートへ", "ノート")
        hint = [f"目安 {per}前後（導入・図の読み方・根拠・例か間違いやすい所・次へのつなぎ）" if role == "本文" else f"{role}の枚"]
        link = col(r, "前の枚から")
        if role == "本文" and link not in EMPTY:
            hint.append(f"前の枚から：{link}（1文目でこの語のつながりを言う）")
        if note not in EMPTY:
            hint.append(f"ノートへ：{note}")
        for c in care.get(n, []):
            hint.append(f"手当て：{c}")
        L += [f"## {n}", "<!-- " + " ／ ".join(hint).replace("--", "—") + " -->", "", "TODO", ""]
    return "\n".join(L)


MARK = re.compile(r"^# -{64} (\d+)\b.*$", re.M)


def blocks(build_text: str):
    """build.py の枚ごとの所 {番号: (始め, 終わり)}（印の行の次から、次の印か NOTES = の前まで）。"""
    marks = list(MARK.finditer(build_text))
    end_all = build_text.find("\nNOTES = ")
    end_all = len(build_text) if end_all < 0 else end_all + 1
    out = {}
    for k, m in enumerate(marks):
        a = m.end() + 1
        b = marks[k + 1].start() if k + 1 < len(marks) else end_all
        out[int(m.group(1))] = (a, b)
    return out


def note_sections(text: str):
    """notes.md の {番号: (始め, 終わり)}（「## N」の次の行から、次の「## 」の前まで）。"""
    heads = list(re.finditer(r"^##\s*(\d+)\s*$", text, re.M))
    return {int(h.group(1)): (h.end() + 1, heads[k + 1].start() if k + 1 < len(heads) else len(text))
            for k, h in enumerate(heads)}


def cards(work: Path, kind, rows, care, minutes=None, source=None):
    """本文の枚ごとの書き手のカード（cards.py の writer）。{番号: カード} と {"資料N.md": 抜き出し}。"""
    import cards as cardmod
    return cardmod.writer(work, kind, rows, care, minutes, source)


def api_lines(forms: str, figure: bool, table: bool, extra=()):
    import cards as cardmod
    return cardmod.api_lines(forms, figure, table, extra)


def _flat(t: str) -> str:
    return re.sub(r"\{[rubi]:([^{}]*)\}", r"\1", t)


def try_part(work: Path, n: int) -> int:
    """parts/NN.py の1枚だけを組んで、構成案どおりか（本文の形・図・結論）と字数を短く出す。描かない。
    書き手が部品のソースや検査のスクリプトを読みに行かずに、自分の1枚を確かめるための道具。"""
    import subprocess
    part = work / "parts" / f"{n:02d}.py"
    if not part.exists():
        print(f"✘ {part} が無い")
        return 1
    b = (work / "build.py").read_text(encoding="utf-8")
    bl = blocks(b)
    if not bl:
        print("✘ build.py に枚の印（# ---- N）が無い")
        return 1
    head = b[:min(a for a, _ in bl.values())]
    code = MARK.sub("", part.read_text(encoding="utf-8")).strip("\n")
    tmp = work / f"_try_{n:02d}.py"
    out = work / "build" / f"_try_{n:02d}.pptx"
    tmp.write_text(head + "\n" + code + "\n\n(HERE / \"build\").mkdir(exist_ok=True)\n"
                   f"deck.save(HERE / \"build\" / \"{out.name}\", title=T, author=AUTHOR)\n", encoding="utf-8")
    try:
        r = subprocess.run([sys.executable, "-X", "utf8", tmp.name], cwd=work, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
    finally:
        tmp.unlink(missing_ok=True)
    if r.returncode or not out.exists():
        err = [l for l in (r.stderr or r.stdout).strip().splitlines() if l.strip()][-4:]
        if re.search(r"(FileNotFoundError|No such file|見つから).*figs|figs.*(FileNotFoundError|No such file|見つから)", " ".join(err)):
            print(f"△ parts/{part.name}：図の画像がまだ無い（図の担当が描いている）。この枚は確かめずに次の枚へ")
            return 0
        print(f"✘ parts/{part.name} が組めない：\n  " + "\n  ".join(err))
        return 1
    import figplan
    import structures
    from pptx import Presentation
    import check_layout
    prs = Presentation(str(out))
    tm = check_layout.text_marks(out).get(1, {})   # 仕上げの描画の検査と同じ見方を、書いたその場で（仕上げの組み直しを減らす）
    out.unlink(missing_ok=True)
    kind = "memo" if (work / "memo.md").exists() else "answers" if (work / "answers.md").exists() else "outline"
    text = (work / {"memo": "memo.md", "answers": "answers.md"}.get(kind, "outline.md")).read_text(encoding="utf-8")
    rows_ = []
    fp = structures.plan_forms(text, kind) or {}
    if n in fp:
        bad = structures.mismatches(prs, {1: fp[n]})
        rows_.append(("✘" if bad else "✔", "本文の形", bad[0][1] if bad else "・".join(k for k in fp[n] if isinstance(k, str)) + " の部品がある"))
    pl = figplan.plan_from_text(text, kind) or {}
    if pl.get(n):
        bad = figplan.mismatches(prs, {1: pl[n]})
        rows_.append(("✘" if bad else "✔", "図", bad[0][1] if bad else f"案（{pl[n][:20]}）どおり"))
    roles = structures.plan_roles(text, kind) or {}
    if roles.get(n) == "本文":
        bad = structures.role_mismatches(prs, {1: "本文"})
        rows_.append(("✘" if bad else "✔", "結論の一文", bad[0][1] if bad else "ある"))
    lines = []
    for sh in prs.slides[0].shapes:
        tx = sh.has_text_frame and sh.text_frame.text.strip()
        if tx and not sh.is_placeholder and sh.name != "見出し":   # 上の帯・ページ番号・青帯は数えない
            lines += [l.strip() for l in sh.text_frame.text.splitlines() if l.strip()]
    chars = sum(len(_flat(l)) for l in lines)
    long_ = [l for l in lines if len(_flat(l)) > 20]
    rows_.append(("△" if long_ else "✔", "1行20字", "超える行：" + "／".join(l[:24] for l in long_[:3]) if long_ else "すべて20字まで"))
    if tm.get("notes"):
        rows_.append(("△", "出どころの断り", "／".join(x[:28] for x in tm["notes"][:3]) + " → スライドから外し、原稿の ※ 行へ"
                      "（残してよいのは図の「（概略）」と「（講師の解釈）」〔発表は「（発表者の解釈）」〕だけ）"))
    if tm.get("subs"):
        rows_.append(("△", "下付き", "・".join(dict.fromkeys(tm["subs"])) + " → 下付きは `_{p}` で書く（例 \"Q⁻¹_{p}\"）"))
    rows_.append(("・", "本文の字数", f"{chars}字（図の代わりの部品の文字も含む参考値。字数の合否は仕上げ役の make_deck が見る）"))
    for mk, item, msg in rows_:
        print(f"{mk} {item}：{msg}")
    print("（描画の検査は仕上げ役の make_deck が見る。これ以上は確かめずに次の枚へ）")
    return 1 if any(mk == "✘" for mk, _, _ in rows_) else 0


def merge(work: Path):
    """parts/NN.py・parts/NN.md を build.py・notes.md の N 枚目に戻す。(戻した番号, 青帯が構成案と違って戻さなかった番号) を返す。"""
    parts = work / "parts"
    bp, npth = work / "build.py", work / "notes.md"
    b, nt = bp.read_text(encoding="utf-8"), npth.read_text(encoding="utf-8")
    done, refused = [], []
    _, _, rows, _ = plan(work)
    want = {r["#"]: col(r, "青帯", "結論") for r in rows}
    for f in sorted(parts.glob("[0-9][0-9].py"), key=lambda p: -int(p.stem)):   # 後ろの枚から（前の位置がずれない）
        n = int(f.stem)
        m = re.search(r'summary\s*=\s*"((?:[^"\\]|\\.)*)"', f.read_text(encoding="utf-8"))
        if m and want.get(n) not in EMPTY and m.group(1).replace('\\"', '"') != want.get(n):
            print(f"✘ parts/{f.name}：青帯が構成案と違う（「{m.group(1)}」≠「{want.get(n)}」）。戻さなかった。"
                  "上の段で決めたことは変えない：変えるなら先に構成案（設計メモ）を直してから書き直す")
            refused.append(n)
            continue
        bl = blocks(b)
        if n not in bl:
            print(f"・parts/{f.name}：build.py に {n} 枚目の印（# ---- {n}）が無い。戻さなかった")
            continue
        a, e = bl[n]
        body = MARK.sub("", f.read_text(encoding="utf-8")).strip("\n") + "\n\n"
        b = b[:a] + body + b[e:]
        done.append(n)
    for f in sorted(parts.glob("[0-9][0-9].md"), key=lambda p: -int(p.stem)):
        n = int(f.stem)
        sec = note_sections(nt)
        if n not in sec:
            print(f"・parts/{f.name}：notes.md に「## {n}」が無い。戻さなかった")
            continue
        a, e = sec[n]
        body = re.sub(r"^##\s*\d+\s*\n", "", f.read_text(encoding="utf-8").lstrip()).strip("\n") + "\n\n"
        nt = nt[:a] + body + nt[e:]
        done.append(n)
    bp.write_text(b, encoding="utf-8")
    npth.write_text(nt, encoding="utf-8")
    return sorted(set(done)), refused


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print(__doc__)
        return 1
    work = Path(argv[0]).resolve()
    force = "--force" in argv
    if "--try" in argv:
        which = argv[argv.index("--try") + 1]
        if which != "all":
            return try_part(work, int(which))
        import contextlib
        import io
        bad = 0
        for f in sorted((work / "parts").glob("[0-9][0-9].py")):   # 全部の枚：直す所がある枚だけ中身を出す
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                code = try_part(work, int(f.stem))
            rows = [l for l in buf.getvalue().splitlines() if l[:1] in ("✘", "△")]
            bad += code
            print(f"[{f.stem}] " + ("✔" if not rows else "\n  " + "\n  ".join(rows)))
        import budget   # 担当ごとのトークンの上限（制作役が最後に走らせる所で見る）
        g = budget.role_guard(work)
        if g:
            print(g)
            return 1
        import figdraft   # 図の下書き（模式図は実物・気づく・配置・ラベル、グラフは気づく）
        fig_rows = [r for r in figdraft.check(work) if r[0] in ("✘", "△")]
        if fig_rows:
            print("[図]\n  " + "\n  ".join(f"{m} {msg}" for m, _, msg in fig_rows))
        bad += any(m == "✘" for m, _, _ in fig_rows)
        print(f"\n✘ のある枚：{bad}。✘ と「1行20字」「出どころの断り」「下付き」の △ を直してから渡す（字数の値は参考）")
        return 1 if bad else 0
    if "--merge" in argv:
        done, refused = merge(work)
        b = (work / "build.py").read_text(encoding="utf-8")
        left = [n for n, (x, y) in sorted(blocks(b).items()) if "TODO" in b[x:y]]
        print(f"戻した：{'・'.join(map(str, done)) or 'なし'}" + (f"。build.py に TODO が残る枚：{'・'.join(map(str, left))}" if left else "")
              + ("。次は make_deck.py" if not refused else ""))
        return 1 if refused else 0
    kind, title, rows, care = plan(work)
    bad = misplaced(work, kind)
    if bad:
        print(f"✘ {bad}")
        return 1
    if work.parent.name != "_work" and kind != "answers":
        print(f"△ 作業フォルダ {work.name} が _work/ の直下に無い（出力先 OUT は2つ上のフォルダから決まる。ずれたら build.py の OUT を直す）")
    import check_notes
    minutes = check_notes.talk_minutes((work / {"memo": "memo.md", "answers": "answers.md"}.get(kind, "outline.md")).read_text(encoding="utf-8"))
    made = []
    cd = work / "cards"
    if force or not cd.exists():
        cd.mkdir(exist_ok=True)
        import excerpt
        src = Path(argv[argv.index("--source") + 1]).resolve() if "--source" in argv else excerpt.find_source(work)
        for n, text in cards(work, kind, rows, care, minutes, src).items():
            (cd / (f"{n:02d}.md" if isinstance(n, int) else n)).write_text(text, encoding="utf-8")
        (work / "parts").mkdir(exist_ok=True)
        made.append(f"cards/（本文 {len(list(cd.glob('[0-9][0-9].md')))}枚" + (f"、{src.name} の抜き出しつき）" if src else "。資料の抜き出しなし：--source で渡せる）"))
    for name, text in (("build.py", build_py(work, "outline" if kind == "answers" else kind, title, rows) if kind != "answers"
                         else build_py(work, kind, title, rows)), ("notes.md", notes_md(kind, rows, care, minutes))):
        p = work / name
        if p.exists() and not force:
            print(f"・{name} はもうある（作らなかった。作り直すなら --force）")
            continue
        p.write_text(text, encoding="utf-8")
        made.append(name)
    if made:
        print(f"作った：{'・'.join(made)}（{len(rows)}枚）。TODO と、コメントにした図の行を書き換えてから make_deck.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
