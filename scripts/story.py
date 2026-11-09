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
import sys

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


# ---- 話の型：筋の4行と青帯の並びのあいだの「骨」。型を1つ選び、拍（つなぎの語と種類）1つにつき1枚の青帯をまず書き、
# あとから拍と拍のあいだに そして の枚を足して肉付けする。検査は、「前の枚から」の並びの中に拍がこの順で全部あるかを見る。
# (名前, 向くデッキ, 元の答えの位置, どんなときに使うか, [(語, 種類, その拍の枚でやること), ...])
# どの型も、答えの位置の「先」「後」の両方で使える（arc_beats が拍を入れ替える）。元の答えの位置は、その型がもともと向く形
ARCS = [
    ("論文紹介（問題から）", "発表", "後", "未解決の問題が先にあり、論文がそれを解いた",
     [("しかし", "壁", "未解決のこと"), ("だから", "手段", "この論文の方法"), ("そして", "次へ", "結果"),
      ("しかし", "疑い", "別の説明・偶然では"), ("だから", "帰結", "確かめた結果"), ("しかし", "限り", "言えないこと")]),
    ("論文紹介（方法から）", "発表", "後", "方法・装置そのものが見どころで、その難しさを越えて結果を出した",
     [("だから", "手段", "方法・装置"), ("しかし", "壁", "越えるべき難しさ"), ("そして", "次へ", "結果"),
      ("しかし", "疑い", "別の説明・偶然では"), ("だから", "帰結", "確かめた結果")]),
    ("研究発表", "発表", "後", "自分の研究：予想と違う結果が山場",
     [("しかし", "壁", "未解決のこと"), ("だから", "手段", "自分の方法"), ("しかし", "意外", "予想と違った結果"),
      ("だから", "問い", "なぜか"), ("しかし", "限り", "今後")]),
    ("提案", "発表", "先", "やり方・予算・方針を提案して、納得してもらう",
     [("しかし", "壁", "今の困りごと"), ("だから", "帰結", "提案と柱の一覧"), ("だから", "手段", "やり方"),
      ("しかし", "疑い", "予想される反論"), ("だから", "帰結", "反論への答え"), ("しかし", "限り", "条件・費用")]),
    ("事例・問題解決", "どちらも", "どちらも", "ある現場の問題をどう解いたか",
     [("しかし", "壁", "起きた問題"), ("だから", "手段", "打った手"), ("しかし", "意外", "思ったのと違った所"), ("だから", "帰結", "わかったこと")]),
    ("輪読（節の筋）", "どちらも", "どちらも", "教科書の1節：定義から例、使えない場合、まとめ",
     [("だから", "手段", "定義・式"), ("そして", "詳しく", "例"), ("しかし", "限り", "成り立たない場合"), ("だから", "帰結", "節のまとめ")]),
    ("素朴な見方を崩す", "講座", "後", "学習者の思い込みが外れる所が山場",
     [("そして", "詳しく", "仕組み"), ("しかし", "意外", "素朴な見方が外れる所"), ("だから", "問い", "なぜか"), ("だから", "手段", "どう使うか")]),
    ("今の形から由来へ", "講座", "後", "制度・規格・歴史：今の形から入り、なぜこの形になったかをたどる",
     [("そして", "詳しく", "今の形"), ("しかし", "壁", "今の形の引っかかり"), ("だから", "問い", "なぜこの形か"),
      ("そして", "次へ", "由来の段"), ("だから", "帰結", "だから今の形")]),
    ("手順を身につける", "どちらも", "どちらも", "やり方を覚えて使えるようにする",
     [("だから", "手段", "やり方"), ("そして", "次へ", "次の段"), ("しかし", "壁", "つまずく所"), ("だから", "手段", "越え方")]),
    ("誤解を正す", "どちらも", "後", "よくある誤解を確かめて、正しい範囲を示す",
     [("しかし", "疑い", "よくある誤解"), ("だから", "帰結", "確かめると"), ("しかし", "限り", "どこまで言えるか")]),
    ("比べて選ぶ", "どちらも", "どちらも", "候補を並べ、弱みを見て、選び方を決める",
     [("そして", "並べる", "候補"), ("しかし", "限り", "それぞれの弱み"), ("だから", "帰結", "選び方")]),
    ("定義から応用へ", "どちらも", "どちらも", "新しい考え方を定義して、使えるところまで",
     [("だから", "手段", "定義"), ("そして", "詳しく", "例"), ("だから", "帰結", "応用"), ("しかし", "限り", "使えない場合")]),
    ("原因を探る", "どちらも", "後", "不思議な現象の原因を、説明を退けながら突き止める",
     [("しかし", "意外", "不思議な現象"), ("しかし", "疑い", "よくある説明"), ("だから", "帰結", "確かめた結果"), ("だから", "問い", "本当の原因")]),
]
ARC_NAMES = [a[0] for a in ARCS]
# 回のねらい（講座は地図の「ねらい」の列、発表は構成案のオプション「ねらい」）→ 既定の話の型。
# 型を自由に選ばせると、強い数字や目立つ話に筋が引っぱられる（ゴールが「なぜこの形か」の回で数字の型が選ばれた）。
# ねらいは学習者・発表者が地図や一覧で見て直せる言葉にし、型はそこから決める。別の型にするなら「型を外す理由：…」
AIMS = [
    # (ねらい, 既定の型, どんな回か)
    ("なぜこの形か", "今の形から由来へ", "制度・規格・設計の由来。今の形から入り、なぜそうなったかをたどる"),
    ("仕組みが分かる", "素朴な見方を崩す", "どう動くか。素朴な見方が外れる所を山場に"),
    ("原因が分かる", "原因を探る", "なぜ起きるか。よくある説明を退けながら"),
    ("正しく判断できる", "誤解を正す", "よくある誤解と、言える範囲"),
    ("使えるようになる", "手順を身につける", "やり方と、つまずく所の越え方"),
    ("新しい考え方を使える", "定義から応用へ", "定義・式から、使える所と使えない場合まで"),
    ("選べるようになる", "比べて選ぶ", "候補を並べ、弱みを見て、選び方を決める"),
    ("事例から学ぶ", "事例・問題解決", "現場の問題をどう解いたか"),
    ("論文を紹介する（問題から）", "論文紹介（問題から）", "未解決の問題を論文が解いた"),
    ("論文を紹介する（方法から）", "論文紹介（方法から）", "方法・装置そのものが見どころ"),
    ("自分の研究を伝える", "研究発表", "自分の研究。予想と違う結果が山場"),
    ("提案して納得してもらう", "提案", "やり方・予算・方針の提案"),
    ("教科書の節を読む", "輪読（節の筋）", "教科書の1節を、定義から例・使えない場合・まとめへ"),
]
AIM_LINE = re.compile(r"^\s*-\s*ねらい\s*[：:]\s*(.+?)\s*$|^\|\s*ねらい\s*\|\s*([^|]+?)\s*\|", re.M)


def aim_of(text: str):
    """「- ねらい：…」（設計メモの1節）か、オプションの表の「| ねらい | … |」→ (ねらい, 既定の型)。無い・一覧に無ければ (書いた値 or None, None)。"""
    m = AIM_LINE.search(text)
    if not m:
        return None, None
    val = (m.group(1) or m.group(2) or "").strip()
    hit = next((a for a in sorted(AIMS, key=lambda a: -len(a[0])) if a[0] in val), None)
    return (hit[0], hit[1]) if hit else (val or None, None)


def aims_table() -> str:
    return "\n".join(["| ねらい | 既定の話の型 | どんな回か |", "|---|---|---|"] + [f"| {a} | {t} | {d} |" for a, t, d in AIMS])
ANSWER_BEAT = ("だから", "帰結", "答えと柱の一覧")
# 「話の型：<名前>×N」で何周かするときに、くり返す拍（ARCS の拍の番号で [始め, 終わり)）。書いていない型は全部をくり返す。
# 例：輪読は小節ごとに全部、論文紹介は実験・結果ごとに「結果 → 疑い → 確かめた結果」
REPEAT = {
    "論文紹介（問題から）": (2, 5), "論文紹介（方法から）": (2, 5), "研究発表": (2, 4), "提案": (3, 5),
    "素朴な見方を崩す": (1, 3), "今の形から由来へ": (3, 4), "手順を身につける": (1, 4), "比べて選ぶ": (1, 2),
    "原因を探る": (1, 3),
}


def repeat_part(arc):
    """型のくり返す拍 [(語, 種類, やること)]。"""
    s, e = REPEAT.get(arc[0], (0, len(arc[4])))
    return arc[4][s:e]


def arc_beats(arc, pos: str, rounds: int = 1):
    """型の拍 [(語, 種類, やること, 周)] を、答えの位置と周の数に合わせて返す。周は、くり返す拍なら 1〜N、それ以外は 0。
    「先」：最初の しかし の拍のすぐ後（しかし が無ければ先頭）に、答えと柱の一覧の拍を1回だけ入れる。
    「後」：答えと柱の一覧の拍を外す（提案のように、もともと先の型を後で使うとき）。"""
    own = next((x for x in arc[4] if x[2].endswith("柱の一覧")), None)   # 提案のように、型に答えの拍があればその言い方で
    s, e = REPEAT.get(arc[0], (0, len(arc[4])))
    pre = [x + (0,) for x in arc[4][:s] if x is not own]
    core = [x for x in arc[4][s:e] if x is not own]
    post = [x + (0,) for x in arc[4][e:] if x is not own]
    n = max(1, rounds)
    beats = pre + [x + ((r if n > 1 else 0),) for r in range(1, n + 1) for x in core] + post
    if pos == "先":
        i = next((k + 1 for k, x in enumerate(beats) if x[0] == "しかし"), 0)
        beats = beats[:i] + [(own or ANSWER_BEAT) + (0,)] + beats[i:]
    return beats
ARC_LINE = re.compile(r"話の型\s*[：:]\s*([^\n|]+)")
ROUNDS = re.compile(r"\s*[×xX＊*]\s*([0-9０-９]+)\s*(?:周)?\s*$")


def arc_rounds(text: str) -> int:
    """「話の型：<名前>×N」の N（書いていなければ 1）。"""
    m = ARC_LINE.search(text)
    r = ROUNDS.search(m.group(1).strip()) if m else None
    return int(r.group(1).translate(str.maketrans("０１２３４５６７８９", "0123456789"))) if r else 1


def arc_of(text: str):
    """一覧・筋の表の下の「話の型：<名前>」→ (名前, ARCS の行 or None)。書いていなければ (None, None)。"""
    m = ARC_LINE.search(text)
    if not m:
        return None, None
    name = ROUNDS.sub("", re.sub(r"\s+$", "", m.group(1)).strip("　 ")).strip("　 ")
    hit = next((a for a in ARCS if a[0] == name), None) or next((a for a in ARCS if a[0].split("（")[0] == name), None)
    return name, hit


def beat_map(text: str, kind: str):
    """{枚の番号: (拍の番号, 語, 種類, その拍の枚でやること)}：選んだ話の型の拍を、「前の枚から」の並びに先頭から順に当てた結果。"""
    import structures
    _, arc = arc_of(text)
    rows = structures._plan_table(text, kind)
    links = link_cells(rows) if rows else None
    if not arc or links is None:
        return {}
    body = body_numbers(text, kind)
    out, k = {}, 0
    beats = arc_beats(arc, answer_position(text, kind), arc_rounds(text))
    for n in body[1:]:
        if k >= len(beats):
            break
        w, kd = split_link(links.get(n, ""))
        if (w, kd) == beats[k][:2]:
            out[n] = (k + 1,) + beats[k]
            k += 1
    return out


def arc_check(text: str, kind: str, body_no: list):
    """[(印, 項目, 説明)]：話の型が選んであり、「前の枚から」の並びに型の拍がこの順で全部あるか。"""
    small = len(body_no) <= 5
    name, arc = arc_of(text)
    aim, want = aim_of(text)
    if name is None:
        if want:
            return [("△", "話の型", f"話の型が無い。ねらい「{aim}」の既定の型は「{want}」。筋の表の下に「話の型：{want}」を1行")]
        if small:
            return []
        return [("△", "話の型", "話の型が無い。筋の表の下に「話の型：<名前>」を1行（" + "・".join(ARC_NAMES)
                 + "。references/story.md 2節）。拍1つに1枚の青帯を先に書き、あとで そして の枚を足す")]
    if arc is None:
        return [("△", "話の型", f"「{name}」は話の型に無い（" + "・".join(ARC_NAMES) + "）")]
    notes = []
    if want and arc[0] != want:   # ねらいと型が合わない（強い数字・目立つ話に引っぱられた など）
        notes.append(f"ねらい「{aim}」の既定の型は「{want}」なのに「{arc[0]}」を選んでいる（データの驚きは、既定の型の しかし の拍に入れる）")
    pos = answer_position(text, kind)
    rounds = arc_rounds(text)
    beats = arc_beats(arc, pos, rounds)
    got = beat_map(text, kind)
    done = len(got)
    if done < len(beats):
        rest = beats[done:]
        notes.append(f"型の拍が {done}/{len(beats)} しか順に出ていない（答えの位置「{pos}」" + (f"・{rounds}周" if rounds > 1 else "") + "）。次に要る拍："
                     + " → ".join(f"{w}（{kd}：{role}" + (f"・{r}周目" if r else "") + "）" for w, kd, role, r in rest)
                     + "（「前の枚から」をこの順に。間に そして の枚を挟んでよい）")
    if pos == "先" and got:
        st = story_table(text) or {}
        an = st.get("答え", ("", None))[1]
        at = next((n for n, v in got.items() if v[3].endswith("柱の一覧")), None)
        if at is not None and an is not None and at != an:
            notes.append(f"答えと柱の一覧の拍は {at}枚目なのに、筋の答えの枚は {an}（どちらかに合わせる）")
    if notes and re.search(r"型を外す理由[：:]\s*\S", text):
        return [("✔", "話の型", f"「{arc[0]}」から外している（型を外す理由あり）")]
    if notes:
        return [("△", "話の型", "。".join(notes) + "。合わないなら別の型を選ぶか、「型を外す理由：…」を書く")]
    return [("✔", "話の型", f"「{arc[0]}」（答えの位置「{pos}」" + (f"・{rounds}周" if rounds > 1 else "") + f"）の拍 {len(beats)} つが順に出ている："
             + "・".join(f"[{n}]{w}（{kd}）" for n, (_, w, kd, *_x) in got.items()))]


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


METHOD_ANSWER = re.compile(r"(で|を)(比べ|見れば|読め|読む|確かめ|調べ|判断す)[るれ]?(ばよい|とよい|る|。|$)|として扱う|を見ればよい|で判断する|に注目する")


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
            ans = st["答え"][0]
            if METHOD_ANSWER.search(ans):
                notes.append("答えが見方・方法になっている（「〜で比べる」「〜を見ればよい」「〜として扱う」）。"
                             "対象について分かったこと（「〜だった」「〜である」と数値・年・固有の名前）で答える。方法を教える回でも、それで何が分かるかまで言う")
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
    res += arc_check(text, kind, body_no)
    return res


if __name__ == "__main__":   # python story.py --aims：ねらいと既定の型の一覧（地図の担当・設計の担当が見る）
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if "--aims" in sys.argv:
        print(aims_table())
    else:
        print("python story.py --aims   # 回のねらいと、既定の話の型の一覧")
