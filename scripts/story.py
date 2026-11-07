"""話の筋の確認：構成案（outline.md）・設計メモ（memo.md）の「筋」の表と、構成の表の「前の枚から」の列（references/story.md）。

check_outline.py・check_memo.py から呼ばれる。面白いかどうかは採点しない。数えられる形だけを見る。
  筋の表：見出しの1列目が「筋」の表（| 筋 | 型 | 一文 | 枚 |）。行は 状況・複雑化・問い・答え（SCQ）と、語り手（任意）
    - 表が無い・4行のどれかが空なら ✘（本文5枚以下の小さな依頼は ・）
    - 「型」の列が無い・複雑化の型が「しかし」の種類（壁・意外・疑い・限り）に無い・問いの型が Q_KINDS に無いなら △
    - 複雑化の枚が本文の枚（最初の枚は除く）なら、その枚の「前の枚から」が「しかし（複雑化の型）」でなければ △
    - 問いが疑問の形（？で終わる）でなければ △
    - 問いの枚が本文の前のほう（最初の3枚か、本文の3分の1まで）に無ければ △
    - 答えの枚：オプション「答えの位置」が「後」（講座の既定）なら本文の後ろ3分の1、「先」（発表の既定。Minto 流の結論から）なら
      本文の前のほう（問いの枚か、そのすぐ後）に無ければ △
  前の枚から：本文の枚ごとに、前の本文の枚の青帯からどうつながるか。「語（種類）」で書く（例：しかし（壁）。本文の最初の枚は「—」）
    - 列が無い・分からない語・種類が無いか表に無いものは △（種類は KINDS）
    - 「そして」が4つ以上続いたら △（並べるだけの所。しかし・だからでつなぐか、まとめる。理由があれば「つなぎの理由：…」）
    - 「しかし」が1つも無ければ △（山場＝意外・対立・壁が無い）
    - しかし（壁）・しかし（疑い）のあと、次の「しかし」か本文の最後までに「だから」が無ければ △（出しっぱなし）
"""
import re

STORY_KEYS = ("状況", "複雑化", "問い", "答え")
LINKS = ("そして", "しかし", "だから")
KINDS = {"そして": ("並べる", "詳しく", "次へ"),
         "しかし": ("壁", "意外", "疑い", "限り"),
         "だから": ("帰結", "手段", "問い")}
GUIDE = {   # (語, 種類): (原稿の1文目の形, 青帯と前後の枚でやること)。references/story.md 2節の表と同じ
    ("そして", "並べる"): ("「もう1つの〜は」", "足す項目そのものを青帯に。並べるのは3つまで"),
    ("そして", "詳しく"): ("「この中の〜を詳しく見ます」", "拡大した所で言えることを青帯に。前の枚のどこを拡大したかを図か原稿で指す"),
    ("そして", "次へ"): ("「次に〜」「〜の後、」", "次の段で起きたことを青帯に"),
    ("しかし", "壁"): ("「しかし、ここに壁があります」", "壁そのものを青帯で言い切る。越え方は同じ青帯か、あとの「だから（手段）」で"),
    ("しかし", "意外"): ("「ところが、結果は〜でした」", "違った結果を数値で言い切る。前の枚か原稿の頭で、先に聞き手に予想させる"),
    ("しかし", "疑い"): ("「ここで疑問が出ます。〜ではないか」", "疑いを青帯で言い切る。確かめ方と結果はあとの「だから（帰結）」で"),
    ("しかし", "限り"): ("「ただし、〜までは言えません」", "言える範囲を青帯で言い切る"),
    ("だから", "帰結"): ("「ここから〜と言えます」", "前の枚の何から言えるかを原稿で1文"),
    ("だから", "手段"): ("「そこで〜を使います」", "そのやり方と、それで何ができるかを青帯に"),
    ("だから", "問い"): ("「なぜ〜でしょうか」", "問いを原稿の1文目で声に出し、青帯でその答えを言う"),
}
TYPE_COLUMN = "型"
COMP_KINDS = KINDS["しかし"]   # 複雑化の型＝「しかし」の種類
Q_KINDS = {   # 問いの型: どんなときに使うか。references/story.md 1節の表と同じ
    "なぜ": "意外な結果・決まりの理由を知りたいとき（複雑化が 意外）",
    "どうやって": "目的はあるのに、やり方が見えないとき（複雑化が 壁）",
    "本当か": "主張や結果に疑いがあり、確かめたいとき（複雑化が 疑い）",
    "どちらか": "2つの説・やり方を比べて、1つに決めたいとき",
    "どこまで": "使える範囲・信じてよい範囲を知りたいとき（複雑化が 限り）",
    "何が": "正体・中身・決め手が分からないとき（初めて出会うものの入口）",
}
OPEN = ("壁", "疑い")   # 越え方・確かめ方（だから）が要る「しかし」
AND_LIMIT = 3          # 「そして」が続いてよい数（4つ目から △）
COLUMN = "前の枚から"
EMPTY = ("", "—", "-", "－", "なし")
POSITION_KEY = "答えの位置"


def answer_position(text: str, kind: str) -> str:
    """「先」か「後」。一覧（outline.md の ## オプション・設計メモの1節）の「答えの位置」。無ければ発表は先、講座は後。"""
    from slide_profile import read_options
    v = read_options(text).get(POSITION_KEY, "")
    if "先" in v or "結論から" in v:
        return "先"
    if "後" in v:
        return "後"
    return "後" if kind == "memo" else "先"


def _story_rows(text: str):
    """筋の表の (見出しのセル, [行のセル])。見出しの1列目が「筋」の表が無ければ None。"""
    lines = text.splitlines()
    for k, l in enumerate(lines):
        cells = [c.strip() for c in l.strip().strip("|").split("|")] if l.strip().startswith("|") else []
        if not cells or cells[0] != "筋":
            continue
        rows = []
        for r in lines[k + 2:]:
            if not r.strip().startswith("|"):
                break
            rows.append([x.strip() for x in r.strip().strip("|").split("|")])
        return cells, rows
    return None


def _key(cell: str) -> str:
    return re.sub(r"[（(].*", "", cell).strip()


def story_table(text: str):
    """{筋の語: (一文, 枚の番号か None)}。見出しの1列目が「筋」の表が無ければ None。"""
    got = _story_rows(text)
    if got is None:
        return None
    cells, rows = got
    i_s = next((j for j, h in enumerate(cells) if "一文" in h), 1)
    i_n = next((j for j, h in enumerate(cells) if h == "枚"), None)
    out = {}
    for c in rows:
        sent = c[i_s] if len(c) > i_s else ""
        m = re.search(r"\d+", c[i_n]) if i_n is not None and len(c) > i_n else None
        out[_key(c[0])] = (sent, int(m.group(0)) if m else None)
    return out


def story_types(text: str):
    """{筋の語: 型}（括弧の補足は外す）。筋の表か「型」の列が無ければ None。"""
    got = _story_rows(text)
    if got is None:
        return None
    cells, rows = got
    i_t = next((j for j, h in enumerate(cells) if h == TYPE_COLUMN), None)
    if i_t is None:
        return None
    return {_key(c[0]): (_key(c[i_t]) if len(c) > i_t else "") for c in rows}


def type_notes(text: str, st: dict, body_no: list, links):
    """筋の表の「型」の列についての注意 [文]。links は {番号: 前の枚から}（列が無ければ None）。"""
    menu = (f"複雑化は しかし の種類（{'・'.join(COMP_KINDS)}）、問いは問いの型（{'・'.join(Q_KINDS)}）から選ぶ。"
            "状況・答え・語り手は「—」。references/story.md 1節")
    ty = story_types(text)
    if ty is None:
        return [f"筋の表に「{TYPE_COLUMN}」の列が無い（「| 筋 | {TYPE_COLUMN} | 一文 | 枚 |」にする。{menu}）"]
    notes = []
    ct, qt = ty.get("複雑化", ""), ty.get("問い", "")
    bad = [f"{k}「{v or '空'}」" for k, v, ok in (("複雑化", ct, COMP_KINDS), ("問い", qt, Q_KINDS)) if v not in ok]
    if bad:
        notes.append("型が無い・選択肢に無い：" + "・".join(bad) + f"（{menu}）")
    cn = st.get("複雑化", ("", None))[1]
    if links is not None and cn in body_no[1:]:
        w, k = split_link(links.get(cn, ""))
        want = f"しかし（{ct}）" if ct in COMP_KINDS else "しかし"
        if w != "しかし" or (ct in COMP_KINDS and k != ct):
            notes.append(f"複雑化の枚 {cn} の「{COLUMN}」が「{links.get(cn, '') or '空'}」（複雑化の枚は「{want}」でつなぐ。"
                         "つなぎを直すか、複雑化の「枚」を、その しかし の枚に直す）")
    return notes


def link_cells(rows):
    """{スライド番号: 前の枚からの語}。列が無ければ None。"""
    i = next((k for k, h in enumerate(rows[0]) if COLUMN in h), None)
    if i is None:
        return None
    return {int(r[0]): (r[i].strip() if len(r) > i else "") for r in rows[1:] if r and r[0].strip().isdigit()}


def split_link(cell: str):
    """「しかし（壁）」「しかし：壁」「しかし」→ (語, 種類か "")。"""
    m = re.match(r"\s*(そして|しかし|だから)\s*(?:[（(:：]\s*([^）)]*?)\s*[）)]?)?\s*$", cell or "")
    return (m.group(1), (m.group(2) or "").strip()) if m else ((cell or "").strip(), "")


def open_buts(seq):
    """しかし（壁・疑い）のうち、次の「しかし」か最後までに「だから」が無いものの番号。"""
    out = []
    for k, (n, w, kind) in enumerate(seq):
        if w == "しかし" and kind in OPEN:
            rest = []
            for _, w2, _ in seq[k + 1:]:
                if w2 == "しかし":
                    break
                rest.append(w2)
            if "だから" not in rest:
                out.append((n, kind))
    return out


def and_runs(seq):
    """[(番号, 語)] から、「そして」が AND_LIMIT を超えて続いた所 [(始め, 終わり)]。"""
    out, run = [], []
    for n, w in list(seq) + [(None, None)]:
        if w == "そして":
            run.append(n)
            continue
        if len(run) > AND_LIMIT:
            out.append((run[0], run[-1]))
        run = []
    return out


def body_numbers(text: str, kind: str):
    """本文の枚の番号（役割の列が「本文」の枚。列が無ければ、結論の列が空でない番号の枚）。"""
    import structures
    roles = structures.plan_roles(text, kind)
    if roles is not None:
        return sorted(n for n, r in roles.items() if r == "本文")
    rows = structures._plan_table(text, kind) or [[]]
    cons = structures._conclusion_cells(rows) or {}
    return sorted(n for n, c in cons.items() if c not in EMPTY)


def check(text: str, kind: str, body_no: list, where: str):
    """[(印, 項目, 説明)]。kind は "outline" か "memo"。body_no は本文の枚の番号（並び順）。"""
    import structures
    res = []
    small = len(body_no) <= 5
    st = story_table(text)
    rows = structures._plan_table(text, kind)
    links = link_cells(rows) if rows else None
    if st is None:
        res.append(("・" if small else "✘", "話の筋",
                    "筋の表が無い。構成の前に「| 筋 | 型 | 一文 | 枚 |」の表で 状況・複雑化・問い・答え を1文ずつ書き、"
                    "複雑化と問いの型を選び、問いと答えの枚の番号を入れる"
                    "（references/story.md）" + ("。本文5枚以下なので省いてよい" if small else "")))
    else:
        miss = [k for k in STORY_KEYS if st.get(k, ("", None))[0] in EMPTY]
        if miss:
            res.append(("✘", "話の筋", f"筋の表で空の行：{'・'.join(miss)}（4つとも1文で書く。references/story.md）"))
        else:
            notes = type_notes(text, st, body_no, links)
            q, qn = st["問い"]
            if not re.search(r"[？?]\s*$", q):
                notes.append("問いが疑問の形でない（「…か？」「なぜ…？」で終える）")
            third = max(3, -(-len(body_no) // 3))
            head, tail = body_no[:third], body_no[-max(2, len(body_no) // 3):]
            an = st["答え"][1]
            pos = answer_position(text, kind)
            if qn is None or an is None:
                notes.append("問いか答えの「枚」が空（その一文を言う枚の番号）")
            else:
                if qn not in head and qn not in (1,):
                    notes.append(f"問いの枚 {qn} が前のほうに無い（本文の {head[0]}〜{head[-1]} 枚目までに問いを立てる）")
                if pos == "後" and an not in tail:
                    notes.append(f"答えの枚 {an} が後ろのほうに無い（答えの位置「後」：本文の {tail[0]}〜{tail[-1]} 枚目で問いに答える）")
                if pos == "先" and an in head:
                    import figplan
                    rows = structures._plan_table(text, kind) or []
                    i_fig = next((k for k, h in enumerate(rows[0]) if "図で見せる" in h), None) if rows else None
                    cell = next((r[i_fig] for r in rows[1:] if i_fig is not None and r and r[0].strip() == str(an) and len(r) > i_fig), None)
                    if cell is not None and figplan.parse_fig(cell)[1] not in ("カード", "ツリー", "流れ図", "表"):
                        notes.append(f"答えの枚 {an} の図が柱の一覧になっていない（答えの位置「先」：答えを支える柱2〜4個を「柱：カード：…」で並べる）")
                if pos == "先" and (an not in head or an < qn):
                    notes.append(f"答えの枚 {an} が前のほうに無い（答えの位置「先」：問いの枚か、そのすぐ後の本文 {head[0]}〜{head[-1]} 枚目で答えを言い、"
                                 "あとの枚はその根拠を順に。答えを後ろで回収するなら一覧の「答えの位置」を「後」に）")
            ty = story_types(text) or {}
            res.append(("△" if notes else "✔", "話の筋", "。".join(notes) if notes else
                        f"複雑化（{ty.get('複雑化')}）→ 問い（{qn}枚目・{ty.get('問い')}）「{q[:24]}」→ 答え（{an}枚目、答えの位置「{pos}」）"))
    if links is None:
        res.append(("・" if small else "△", "前の枚から",
                    f"{where}の表に「{COLUMN}」の列が無い。本文の枚ごとに、前の枚の青帯から「そして・しかし・だから」のどれでつながるかを書く"
                    "（本文の最初の枚は「—」。references/story.md）"))
        return res
    full = [(n,) + split_link(links.get(n, "")) for n in body_no[1:]]
    seq = [(n, w) for n, w, _ in full]
    bad = [(n, w) for n, w in seq if w not in LINKS]
    notes = []
    if bad:
        notes.append("分からない語・空：" + "・".join(f"[{n}]「{w or '空'}」" for n, w in bad[:6]) + f"（{'・'.join(LINKS)} から選ぶ）")
    nokind = [(n, w, k) for n, w, k in full if w in LINKS and k not in KINDS[w]]
    if nokind:
        notes.append("種類が無い・表に無い：" + "・".join(f"[{n}]「{w}（{k or '?'}）」" for n, w, k in nokind[:6])
                     + "（" + "／".join(f"{w}：{'・'.join(v)}" for w, v in KINDS.items()) + "。references/story.md 2節）")
    ob = open_buts(full)
    if ob:
        notes.append("出しっぱなしの「しかし」：" + "・".join(f"[{n}]（{k}）" for n, k in ob)
                     + "（次の「しかし」か最後までに、越え方・確かめ方の「だから」の枚を置く）")
    runs = and_runs(seq)
    if runs and not re.search(r"つなぎの理由[：:]\s*\S", text):
        notes.append("「そして」が続く：" + "、".join(f"{a}〜{b}枚目" for a, b in runs)
                     + f"（{AND_LIMIT}つまで。並べるだけの所を、しかし・だからでつなぐか、まとめる。手順などで続けるなら「つなぎの理由：…」を書く）")
    if not any(w == "しかし" for _, w in seq):
        notes.append("「しかし」が1つも無い（意外な結果・対立・壁の枚を、山場として青帯に出す）")
    if notes:
        res.append(("△", "前の枚から", "。".join(notes)))
    else:
        buts = "・".join(k for _, w, k in full if w == "しかし")
        cnt = {w: sum(x == w for _, x in seq) for w in LINKS}
        res.append(("✔", "前の枚から", "・".join(f"{w} {c}" for w, c in cnt.items()) + f"（しかし：{buts}）"))
    return res
