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
    return (s or "").replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def items_of(cell: str):
    """本文の要点のセル → 項目のリスト（／ / ； 改行で分ける。「★」の付いた項目は赤字 {r:…} にする）。
    「・」では分けない（「眠気・気分・集中」のような並びを1項目に保つ）。"""
    cell = re.sub(r"<br\s*/?>", "／", cell or "")
    parts = [p.strip() for p in re.split(r"\s*(?:／|/|；|;)\s*", cell) if p.strip()]
    # 〔事実N〕の印と「（データN）」（3b節の組を指す設計メモの印）はスライドに出さない（地震の試しで「（データ1）」が本文に残り、採点者2人が減点した）
    return [underline(red(re.sub(r"\s*(?:〔[^〕]*〕|[（(]データ\s*\d+(?:[・,、]\s*\d+)*[)）])", "", p))) for p in parts[:5]]


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
    # 「⇒ 帰結」は部品が別に赤字で出すので、赤字のかっこに入れない（入れると ⇒ で分けたときに } が閉じなくなる）
    body, arrow, then = (rest if sep else core).partition("⇒")
    tail = f"⇒{then}" if arrow else ""
    if not body.strip():
        return core
    return (f"{h}：{{r:{body.strip()}}}" if sep else f"{{r:{body.strip()}}}") + tail


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


BREAK_AFTER = set("、。，,・）」』】：:；;")
PARTICLES = ("では", "には", "とは", "から", "まで", "より", "ので", "のに", "が", "を", "に", "は", "で", "と", "も", "へ", "や", "の")


def _vis(t: str) -> str:
    return re.sub(r"\{[a-z]+:|\}", "", t)


def wrap_jp(t: str, lim: float) -> str:
    """1行が lim（全角に直した字数）を超える文を、句読点・空白・助詞の後ろで改行する（{r:…} の中では切らない）。
    スクリプトで組む本文が枠からはみ出さないように。lim が 0 なら何もしない。"""
    import language as LG
    meas = lambda x: LG.width(_vis(x))   # noqa: E731
    if not lim or "\n" in t or meas(t) <= lim:
        return t
    out, s = [], t
    while meas(s) > lim and len(out) < 6:
        best, best_rank, depth = None, -1, 0
        for i in range(1, len(s)):
            depth += (s[i - 1] == "{") - (s[i - 1] == "}")
            if meas(s[:i]) > lim:
                break
            if depth > 0:
                continue
            prev = s[i - 1]
            rank = 3 if prev in BREAK_AFTER or s[i] == " " else 2 if any(s[:i].endswith(p) for p in PARTICLES[:-1]) else 1 if s[:i].endswith("の") else 0
            if rank and (rank > best_rank or meas(s[:i]) >= lim * 0.6):
                best, best_rank = i, max(rank, best_rank)
        if best is None or meas(s[:best]) < lim * 0.4:
            best = next((i for i in range(1, len(s)) if meas(s[:i]) > lim), len(s)) - 1
            if depth > 0 or best <= 0:
                break
        out.append(s[:best].rstrip())
        s = s[best:].lstrip()
    out.append(s)
    return "\n".join(x for x in out if x)


def form_code(forms: str, pts, lim: float = 0):
    """本文の形 → 部品の呼び出しの行。要点は、形の入れる所の書き方（structures.SLOTS）から入れる所に割り振る。
    入れる所が空なら TODO（書き手が埋める）。"""
    import structures
    out = []
    w = lambda t: wrap_jp(t, lim)   # noqa: E731
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
                out.append("s.lead([" + qs([w(x) for x in pre[:3]]) + f'], "{q(w(then))}")')
            else:
                out.append(f's.lead_down("{q(chr(10).join(pre[:3]))}", "{q(then)}")')
        elif k == "ラベル":
            # 見出しが同じ要点（「例：a」「例：b」）は1つの塊に（塊は2つまで・多くて3つ。要点を1つずつ塊にすると4つになって ERROR だった）
            groups = {}
            for p in (ps or ["TODO 見出し：説明"])[:4]:
                h, _, rest = p.partition("：")   # 半角の「:」は文字の書式 {r:…} に使うので、全角の「：」だけで分ける
                body, _, then = rest.partition("⇒")
                g = groups.setdefault(h.strip(), [[], ""])
                g[0].append(w(body.strip()) or "TODO 説明")
                g[1] = then.strip() or g[1]
            for h, (bodies, then) in groups.items():
                then_arg = f', then="{q(w(then))}"' if then else ""
                out.append(f's.block("{q(h)}：", [' + qs(bodies) + f"]{then_arg})")
        elif k == "場合分け":
            pairs = [p.partition("：")[::2] for p in ps] or [("TODO 条件", "TODO 説明")]
            out.append("s.cases([" + ", ".join(f'("{q(c.strip())}", "{q(w(d.strip())) or "TODO 説明"}")' for c, d in pairs[:3]) + "])")
        elif k == "展開":
            p = ps[0] if ps else "TODO 左 → TODO 右"
            a, _, b = p.partition("→")
            out.append(f's.develop("{q(w(a.strip()))}", "{q(w(b.strip())) or "TODO 結果"}")')
            out += [f's.p("{q(x)}")   # TODO 展開に入らなかった要点（入れる所を決める）' for x in ps[1:]]
        elif k == "問い":
            for p in (ps or ["TODO 問い？⇒ TODO 確かめた結果"])[:3]:
                a, _, b = p.partition("⇒")
                out.append(f's.ask("{q(w(a.strip()))}", "{q(w(b.strip())) or "TODO 確かめた結果"}")')
        elif k == "手順":
            steps = []
            for p in ps:
                chunks = re.split(r"(?<![0-9])[0-9０-９][.．](?![0-9])\s*", p)
                steps += [x.strip() for x in (chunks[1:] if len(chunks) > 1 else chunks) if x.strip()]   # 「1.」の前（見出し）は外す
            out.append("s.numbered([" + qs([w(x) for x in (steps or ["TODO 段1", "TODO 段2"])[:5]]) + "])")
        elif k == "式の注釈":
            out.append('# TODO 式と項の注釈：s.peq(...) と s.defs(...)（references/structures.md「式の注釈」）'
                       + (f'  要点：{"／".join(ps)[:80]}' if ps else ""))
        elif k == "余り":
            out += [f's.p("{q(p)}")   # TODO 形の入れる所の書き方でない要点（入れる所に移すか、ノートへ）' for p in ps]
        else:
            out += [f's.p("{q(w(p))}")' for p in (ps or ["TODO 要点"])[:4]]
    return out


TAG = re.compile(r"\s*〔[^〕]*〕")   # 〔ゴール1〕〔事実3〕などの印（スライドには出さない）


def placements(rows) -> dict:
    """{枚: "beside" | "main"}：画像の図を置く型。左文右図（figure_beside）は本文の枚の半分まで（渡す前の確認と同じ基準）。
    要点の少ない枚から「図が主役」（figure_main：左に図・右に補足）にする。試しで、全部を左文右図にして10枚中9枚になった。"""
    import figplan
    body = [r for r in rows if (col(r, "役割") or "本文") == "本文"]
    imgs = []
    for r in body:
        fig = col(r, "図で見せるもの", "図")
        if fig not in EMPTY and not figplan.pptx_part(fig):
            imgs.append((len(items_of(col(r, "本文の要点"))), r["#"]))
    cap = int(figplan.MAX_SHARE * len(body))
    imgs.sort(key=lambda x: (-x[0], x[1]))   # 要点の多い枚ほど文を左に（左文右図）
    return {n: ("beside" if i < cap else "main") for i, (_, n) in enumerate(imgs)}


def compare_code(fig: str):
    """図の案「…：比較：A（a、b）と B（c）…」から s.compare の行。読めなければ None（TODO のまま）。"""
    body = fig.split("：", 2)[-1]
    m = re.search(r"([^（）：。、]{1,16})（([^（）]{2,80})）\s*と\s*([^（）：。、]{1,16})（([^（）]{2,80})）", body)
    if not m:
        return None
    side = lambda h, t: '("' + q(h.strip()) + '", [' + qs([x.strip() for x in re.split(r"[、／/]", t) if x.strip()][:4]) + "])"   # noqa: E731
    return f"s.compare({side(m.group(1), m.group(2))}, {side(m.group(3), m.group(4))}, y=s.cur_y + 0.3)"


def _fold(t: str, width: float, size: float = 18) -> str:
    """箱に入る幅で2行に（zemi.wrap_to）。読めなければそのまま。"""
    try:
        import zemi
        return zemi.wrap_to(t.strip(), width, size)
    except Exception:
        return t.strip()


def flow_code(fig: str):
    """図の案「…：流れ図：A → B → C」から、右の列に縦に並べる s.flow の行（比べの build.py の置き方）。読めなければ None。"""
    body = fig.split("：", 2)[-1]
    inner = [x for x in re.findall(r"[（(]([^（）()]*)[）)]", body) if re.search(r"→|⇒|->", x)]
    body = inner[0] if inner else re.sub(r"[（(][^）)]*[）)]\s*$", "", body)   # 「確かめ方（A → B → C）」はかっこの中が流れ
    body = body.strip()
    items = [x.strip(" 。") for x in re.split(r"\s*(?:→|⇒|->)\s*", body) if x.strip(" 。")]
    if not 3 <= len(items) <= 5 or any(len(x) > 24 for x in items):
        return None
    its = ", ".join('"' + q(_fold(x, 3.4)) + '"' for x in items)
    return f's.flow([{its}], x=deck.area["fig_x"] + 0.8, y=deck.area["top"], w=3.6, h=0.75, gap=0.45, size=18)'


def decision_code(fig: str):
    """図の案「…：判定の流れ図：問い1？→ はい：結論1／いいえ：問い2？→ はい：結論2／いいえ：最後」から s.decision の行。読めなければ None。"""
    body = fig.split("：", 2)[-1]
    steps = re.findall(r"([^？?：／→（(]{3,40}[？?])\s*→\s*はい\s*[：:]\s*([^／)）]{1,30})", body)
    last = re.findall(r"いいえ\s*[：:]\s*([^／？?)）]{1,30})(?:[)）]|$|。)", body)
    if not steps:   # 「問い1？→ 結論1、問い2？→ 結論2、全部いいえ → 最後」の書き方（見本の講座の書き方）
        steps = [(a.strip("、／ "), b.strip()) for a, b in re.findall(r"([^、／？?→（(：]{3,40}[？?])\s*→\s*([^、／→？?（(]{1,30})(?=[、／。）)]|$)", body)]
        last = re.findall(r"(?:全部|すべて|どれも)\s*いいえ\s*(?:→|[：:])\s*([^、／。）)]{1,30})", body)
    if not 1 <= len(steps) <= 3 or not last:
        return None
    st = ", ".join('("' + q(_fold(a, 3.0)) + '", "' + q(_fold(b, 2.2)) + '")' for a, b in steps)
    return f's.decision([{st}], "{q(_fold(last[-1], 2.2))}", x=deck.area["fig_x"] - 1.3, y=deck.area["top"], q_w=3.0, out_w=2.2)'


def _fig_body(fig: str) -> str:
    """図の案の「目的：種類：」より後ろ。「（外す理由：…）」と〔事実N〕の印は外す。"""
    body = fig.split("：", 2)[-1]
    body = re.sub(r"[（(]\s*外す理由[：:][^）)]*[）)]", "", body)
    return TAG.sub("", body).strip(" 。")


def _top_split(s: str, seps: str) -> list:
    """かっこ・かぎかっこの外にある区切り（seps のどれか）で分ける。"""
    out, cur, depth = [], "", 0
    for ch in s:
        if ch in "（(「『":
            depth += 1
        elif ch in "）)」』":
            depth = max(0, depth - 1)
        if ch in seps and depth == 0:
            out.append(cur)
            cur = ""
        else:
            cur += ch
    out.append(cur)
    return [x.strip() for x in out if x.strip()]


def _head_inner(part: str):
    """「見出し（a、b）」→ ("見出し", "a、b")。かっこが無ければ (part, "")。"""
    m = re.match(r"^(.*?)[（(](.*)[）)]\s*$", part.strip())
    return (m.group(1).strip(), m.group(2).strip()) if m and m.group(1).strip() else (part.strip(), "")


def before_after_code(fig: str):
    """図の案「…：前後：A（a、b）→ B（c）」から s.before_after の行。見出しが長ければ「前」「後」を見出しに。読めなければ None。"""
    parts = _top_split(_fig_body(fig), "→⇒")
    if len(parts) != 2:
        return None
    sides = []
    for p, label in zip(parts, ("前", "後")):
        h, inner = _head_inner(p)
        lines = [x.strip() for x in re.split(r"[、／/]", inner) if x.strip()] if inner and "→" not in inner else ([inner] if inner else [])
        if len(h) > 12:
            h, lines = label, [h] + lines
        sides.append('("' + q(h) + '", [' + qs([_fold(x, 4.6, 22) for x in lines[:3]]) + "])")
    # 帯のすぐ下に置き、本文はその下へ（本文のあとに置くと、要点の多い枚で下にはみ出して高さが負になった）
    return f's.cur_y = s.before_after({sides[0]}, {sides[1]}, y=deck.area["top"] + 0.1, h=1.5).bottom + 0.4'


def cards_code(fig: str):
    """図の案「…：カード：題（見出し1＝説明1／見出し2＝説明2）」か「題（「a」「b」「c」）」から s.cards の行（2〜4枚）。読めなければ None。"""
    _, inner = _head_inner(_fig_body(fig))
    if not inner:
        return None
    if "＝" in inner:
        items = [tuple(x.strip() for x in it.split("＝", 1)) for it in _top_split(inner, "／/") if "＝" in it]
    else:
        quoted = re.findall(r"「([^」]+)」", inner)
        texts = quoted or [x.strip() for x in re.split(r"[、／/]", inner) if x.strip()]
        items = [(f"{'①②③④'[i]}", t) for i, t in enumerate(texts[:4])]
    if not 2 <= len(items) <= 4:
        return None
    its = ", ".join('("' + q(h) + '", "' + q(_fold(d, 3.4, 20)) + '")' for h, d in items)
    return f's.cards([{its}], layout="row", y=s.cur_y + 0.3, size=20)'


_KM_NUM = r"[0-9０-９][0-9０-９.,，．]*"
_KM_UNIT = r"(?:[万億千兆])?(?:%|％|倍|人|件|円|点|年|割|回|時間|分|日|か月|ヶ月|週|歳|個|社|校|本|枚|台|km|kg|m|t|℃|度|σ)?"
_KM_PRE = r"(?:約|ほぼ|およそ|最大|最小|最低|最高|少なくとも|わずか|平均)?"
_KM_CORE = rf"(?:[MＭ]\s*)?{_KM_NUM}\s*{_KM_UNIT}(?:\s*[〜~～\-－–—]\s*{_KM_PRE}{_KM_NUM}\s*{_KM_UNIT})?(?:に\s*{_KM_NUM}\s*{_KM_UNIT})?"
_KM_QUAL = r"(?:程度以上|程度以下|程度|以上|以下|未満|超え|超|前後|強|弱|近く|ほど|余り|あまり)?"
KEY_NUMBER = re.compile(rf"({_KM_PRE})({_KM_CORE})(\s*{_KM_QUAL})")


def key_number(h: str):
    """図の案の大きな数字の所（「60〜90%程度以上」「ほぼ0〜0.9%」「8割以上」「3人に1人」）→ (全体, 数字＋単位)。読めなければ None。
    範囲（〜）・単位・前の限定（約・ほぼ）・後ろの限定（程度以上・以下・未満）まで載せる。数字＋単位は、全体が大きな数字の場所に入らないときに
    大きく出す形（zemi の key_message の short。全体は説明の頭に回る）。地震の比べで「60〜90%程度以上」が「60」、「ほぼ0〜0.9%」が「0」、
    「8割以上」が「8割」だけになった。"""
    m = KEY_NUMBER.search(h or "")
    return (m.group(0).strip(), m.group(2).strip()) if m else None


def key_message_code(fig: str):
    """図の案「…：大きな数字：17%（説明の一言）」から s.key_message の行（帯の下に置き、本文はその下へ）。読めなければ None。"""
    h, inner = _head_inner(_fig_body(fig))
    got = key_number(h)
    if not got:
        return None
    full, short = got
    sub = f', sub="{q(_fold(inner, 9.0, 22))}"' if inner else ""
    alt = f', short="{q(short)}"' if short != full else ""
    return f's.cur_y = s.key_message("{q(full)}"{sub}{alt}, y=deck.area["top"] + 0.1).bottom + 0.45'


def table_code(fig: str, beside: bool = True):
    """図の案「…：表：列1×列2（行1＝セル／行2＝セル）」（セルが2つ以上なら「｜」で区切る）から s.table の行。
    行の中身が無ければ None（担当が中身を考えることになるので、設計メモに書く）。"""
    h, inner = _head_inner(_fig_body(fig))
    rows = [tuple(x.strip() for x in it.split("＝", 1)) for it in _top_split(inner, "／/") if "＝" in it] if inner else []
    if len(rows) < 2:
        return None
    header = [x.strip() for x in re.split(r"[×xX]", h) if x.strip()] or ["", ""]
    ncell = max(len(c.split("｜")) for _, c in rows)
    total = 5.4 if beside else 11.5
    label_w = 1.5 if beside else 1.8
    col_w = round((total - label_w) / ncell, 2)
    cells = [(lab, [_fold(c, col_w - 0.2, 16) for c in cell.split("｜")]) for lab, cell in rows[:7]]
    nl = max(c.count("\n") + 1 for _, cs in cells for c in cs)   # 行の高さは、いちばん行の多いセルに合わせる（固定だと2行のセルが重なった）
    row_h = round(0.2 + 0.28 * nl, 2)
    rr = ", ".join('("' + q(lab) + '", [' + qs(cs) + "])" for lab, cs in cells)
    x, y = ('deck.area["fig_x"] - 0.7', 'deck.area["top"]') if beside else ('deck.area["x"]', "s.cur_y + 0.3")
    return f"s.table({x}, {y}, {col_w}, {row_h}, [{qs(header[:ncell + 1])}], [{rr}], label_w={label_w}, size=16)"


PART_CODE = {"s.compare": compare_code, "s.flow": flow_code, "s.decision": decision_code,
             "s.before_after": before_after_code, "s.cards": cards_code, "s.key_message": key_message_code, "s.table": table_code}
PART_FORMS = {   # スクリプトが読める書き方（check_memo が、読めない図の案を ✘ にするときに出す）
    "s.compare": "違い：比較：A（a、b）と B（c、d）",
    "s.flow": "流れ：流れ図：A → B → C（3〜5段）",
    "s.decision": "判定：判定の流れ図：問い1？→ はい：結論1／いいえ：問い2？→ はい：結論2／いいえ：最後",
    "s.before_after": "違い：前後：A（a、b）→ B（c、d）",
    "s.cards": "並び：カード：題（見出し1＝説明1／見出し2＝説明2／見出し3＝説明3）",
    "s.key_message": "印象：大きな数字：17%（説明の一言）",
    "s.table": "観点：表：列1×列2（行1＝セル／行2＝セル。セルが2つ以上なら「｜」で区切る）",
}


def part_name(fig: str):
    import figplan
    ppt = figplan.pptx_part(fig) if fig not in EMPTY else None
    return ppt.split("（")[0].strip() if ppt else None


def unbuildable(rows) -> list:
    """[(枚, 部品, 書き方)]：PowerPoint の部品で組む図の案のうち、スクリプトが読めない物（担当が手で組むことになる）。"""
    out = []
    for r in rows:
        fig = col(r, "図で見せるもの", "図")
        name = part_name(fig)
        if name in PART_CODE and PART_CODE[name](fig) is None:
            out.append((r["#"], name, PART_FORMS[name]))
    return out


def quiz_slices(text: str, rows):
    """{枚: [(番号, 文)]}：設計メモ6節の問題と解答を、確認問題・解答の枚に順に割り振る（〔…〕の印は外す）。"""
    import structures
    try:
        qi = structures.quiz_items(text) or {}
    except Exception:
        qi = {}
    if not qi:
        return {}
    ids = list(qi)
    out = {}
    for role, k in (("確認問題", 0), ("解答", 3)):
        slides = [r["#"] for r in rows if col(r, "役割") == role]
        if not slides:
            continue
        per = -(-len(ids) // len(slides))
        for j, n in enumerate(slides):
            out[n] = [(i, TAG.sub("", qi[i][k]).strip()) for i in ids[j * per:(j + 1) * per]]
    return out


def quiz_wrapped(qz: dict) -> dict:
    """確認問題・解答のスライド用：1行32字前後で改行（原稿は改行しない quiz_slices のまま）。"""
    return {n: [(k, wrap_jp(t, 32)) for k, t in items] for n, items in qz.items()}


def short_source(src: str) -> str:
    """出典の欄 → 図の下の短い出典（「Walters ほか 2023」の形）。"""
    m = re.match(r"\s*([A-Za-z][\w'-]+)", src or "")
    y = re.search(r"(19|20)\d{2}", src or "")
    if m:
        who = m.group(1) + (" ほか" if re.search(r"&|et al|ほか|,\s*[A-Z]\.", src) else "")
    else:
        who = re.split(r"[「（(、,]", src or "")[0].strip()[:16]
    return f"（{who} {y.group(0)}）" if who and y else ""


def figs_py(work: Path, rows, text: str) -> str:
    """軽量の回の figs.py の出発点：データの棒グラフ（2列の表）は描き上げ、ほかの図は TODO の関数（下書きの雛形を埋めて描く）。"""
    import data as datamod
    import figplan
    try:
        rel = os.path.relpath(SKILL / "scripts", work).replace("\\", "/")
    except ValueError:
        rel = (SKILL / "scripts").as_posix()
    ds = datamod.datasets(text)
    place = placements(rows)
    L = ['"""図。python figs.py [名前 ...]（名前は f_ を除いた部分）。データの棒グラフは scaffold.py が設計メモの3b節から描いた。TODO の図を描く"""',
         "import sys", "from pathlib import Path", "",
         "HERE = Path(__file__).resolve().parent",
         f'sys.path.insert(0, str((HERE / "{rel}").resolve()))',
         "from figkit import COL, LW, arrow, blank, box, fig, noticks, save  # noqa: E402,F401",
         "import figlib  # noqa: E402,F401",
         "import figschema  # noqa: E402,F401", "",
         'OUT = HERE / "figs"', "OUT.mkdir(exist_ok=True)", ""]
    for r in rows:
        if (col(r, "役割") or "本文") != "本文":
            continue
        n, fig = r["#"], col(r, "図で見せるもの", "図")
        if fig in EMPTY or figplan.pptx_part(fig):
            continue
        refs = datamod.refs(fig)
        d = ds.get(refs[0]) if refs else None
        vals = None
        if d and len(d.get("head") or []) == 2:
            try:
                vals = [(r_[0], float(str(r_[1]).replace(",", "").replace("％", "").replace("%", ""))) for r_ in d["rows"]]
            except ValueError:
                vals = None
        L.append("")
        if vals:
            unit = d["fields"].get("単位", "")
            unit = "%" if unit in ("％", "%") else ("" if len(unit) > 3 else unit)
            tail = d["fields"].get("驚き", "").split("実際")[-1]   # 驚きの文で「実際」のあとに先に出る値の棒を強調（ラベルは前半にも出る）
            pos = sorted((tail.find(f"{v:g}"), i) for i, (_, v) in enumerate(vals) if tail.find(f"{v:g}") >= 0)
            hi = pos[0][1] if pos else next((i for i, (lab, _) in enumerate(vals) if lab and lab in tail), None)
            L += [f"def f_s{n:02d}():",
                  f'    """{q(fig[:80])}（データ{refs[0]}：{q(d["title"][:40])}。scaffold.py が3b節の表から描いた。強調する棒は highlight）"""',
                  "    f, ax = fig(5.6, 0.7 + 0.55 * " + str(len(vals)) + ")",
                  "    figlib.bars(ax, [" + qs([v[0] for v in vals]) + "], [" + ", ".join(f"{v[1]:g}" for v in vals) + "]"
                  + (f", highlight={hi}" if hi is not None else "") + (f', unit="{q(unit)}"' if unit else "") + ")",
                  f'    save(f, OUT / "s{n:02d}.png")', ""]
        else:
            # 描いた大きさのまま置かれるので、置き場所に入る大きさを渡す（試しで、制作の担当が zemi.py・figkit.py を読みに行っていた）
            mk = "fig" if re.search(r"グラフ|棒|推移|分布|散布", fig) else "blank"
            size = (f"{mk}(7.0, 4.6)・図が主役（左に図・右に細い列の文）" if place.get(n) == "main"
                    else f"{mk}(5.6, 4.0)・左文右図（右の列。本文の右端しだいで幅 5.0〜5.8）")
            if d and d.get("rows"):   # 2列でない表（組の棒など）は描かないが、値はここに（data_N.md を開かずに描ける）
                hd = d.get("head") or []
                size += f"。データ{refs[0]}" + "の値（" + q("｜".join(hd)) + "）：" + q("／".join("｜".join(str(c) for c in r_) for r_ in d["rows"])[:300])
            import figschema
            h = figschema.hint(fig)
            L += [f"def f_s{n:02d}():",
                  f'    """TODO 図の案：{q(fig[:100])}（大きさ：{size}）',
                  *([f"    {q(h)}"] if h else []),
                  '    （figdraft.py の下書きの雛形を埋めて、ここに書き、描く）"""',
                  f'    raise NotImplementedError("s{n:02d} の図はまだ（図の案のとおりに描く）")', ""]
    L += ["", 'if __name__ == "__main__":',
          '    names = sys.argv[1:] or [n[2:] for n in list(globals()) if n.startswith("f_")]',
          "    for n in names:",
          '        globals()["f_" + n]()']
    return "\n".join(L) + "\n"


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
    plan = work / {"memo": "memo.md", "answers": "answers.md"}.get(kind, "outline.md")
    foreign = False   # 日本語でないデッキか（設定の「言語」）
    if plan.exists():
        import language as LG
        from slide_profile import read_options
        foreign = not LG.is_japanese(read_options(plan.read_text(encoding="utf-8")).get("言語"))
        if foreign:
            title = re.sub(r"^第(\d+)回\s*", r"Lecture \1: ", title)   # 日本語でない講座：スライドの上の題も（英語の試しで「第1回」が残った）
    if kind == "memo":
        course = re.sub(r"_\d{2}$", "", work.name)
        num = re.search(r"_(\d{2})$", work.name)
        nn = num.group(1) if num else "01"
        short_title = q(re.sub(r"^(第\d+回|Lecture \d+:)\s*", "", title))
        out_line = f'OUT = HERE.parents[1] / "{q(course)}" / "{nn}_{short_title}{"_slides" if foreign else "_スライド"}.pptx"'
    elif kind == "answers":
        out_line = ('OUT = HERE / "TODO_answers_slides.pptx"   # same folder as the original deck: "<name>_answers_slides.pptx".' if foreign else
                    'OUT = HERE / "TODO_質問回答_スライド.pptx"   # 元のデッキと同じフォルダ・「<資料名>_質問回答_スライド.pptx」に')
    else:
        out_line = f'OUT = HERE.parents[1] / "{q(work.name)}" / "{q(work.name)}{"_slides" if foreign else "_スライド"}.pptx"   # 発表フォルダ（資料置き場と同じ）。一覧の「出力先」があれば合わせる'
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
              "def qa(s, items, size=22, gap=0.45):",
              '    """確認問題・解答の本文。items = [(番号, 本文)]。番号は「1-1」の形（原稿HTMLの「1-1 に答える」ボタンになる）"""',
              "    s.at(1.0, 2.0)",
              "    for j, (k, txt) in enumerate(items):",
              '        s.p("{b:" + k + "}' + ("  " if foreign else "　") + '" + txt, size=size, gap=gap if j < len(items) - 1 else 0.2)',
              ""]
    qa_slices = qa_split(work, kind, rows)
    place = placements(rows)
    ptext = plan.read_text(encoding="utf-8") if plan.exists() else ""
    quiz = quiz_slices(ptext, rows) if kind == "memo" else {}
    import data as datamod
    dsets = datamod.datasets(ptext) if ptext else {}
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
            L.append('s.heading("Expected Questions")' if foreign else 's.heading("想定質問")')
            pairs = [(k, qq, re.sub(r"\s*〔[^〕]*〕", "", a)) for k, qq, a, _ in qa_slices.get(n, [])]   # 〔出どころ〕はスライドに出さない
            L.append("s.at(1.0, 1.9)")
            L.append("s.qa_pairs([" + ", ".join(f'("{q(k)}", "{q(qq)}", "{q(a)}")' for k, qq, a in pairs)
                     + "])   # 1行25字までに \\n を入れて折る（回答は2〜3行）。戻る枚は原稿に")
        elif role == "まとめ":
            import story
            st = story.story_table(plan.read_text(encoding="utf-8")) if plan.exists() else None
            st = st or {}
            ans = (st.get("答え") or ("",))[0] or "TODO 筋の表の答えの一文"
            opn = (st.get("問い") or ("",))[0] or "TODO 最初の本文の枚の前振り（問い・見方・問題）"
            summ = q(summary) if summary not in EMPTY else q(ans)
            L.append(f's = deck.slide(T, summary="{summ}")   # まとめ：結論の一文はこの回の答え')
            L.append('s.heading("Summary")' if foreign else 's.heading("まとめ")')
            kind_ = story.recap_kind(plan.read_text(encoding="utf-8")) if plan.exists() else "問い→答え"
            pl = ", ".join(f'"{q(p)}"' for p in pts[:3]) if pts else '"TODO 持ち帰る一言1", "TODO 一言2"'
            sit = (st.get("状況") or ("",))[0] or "TODO 状況"
            comp = (st.get("複雑化") or ("",))[0] or "TODO しかし"
            note = f"   # まとめの形「{kind_}」（話の型から。合わなければ kind を変える。新しい事実は入れない。references/story.md 3節）"
            # 前と後・選び方：設計メモのまとめの行の要点に「A → B」で書いた対を、そのまま組む（無ければ筋の表の状況→答えと TODO）
            prs = [tuple(x.strip() for x in re.split(r"\s*(?:→|⇒)\s*", p, maxsplit=1)) for p in pts if re.search(r"→|⇒", p)][:3]
            pair_code = ", ".join(f'("{q(a)}", "{q(b)}")' for a, b in prs)
            if kind_ == "前と後":
                pair_code = pair_code or f'("{q(sit)}", "{q(ans)}"), ("TODO 聞く前の見方2", "TODO 今わかったこと2")'
                L.append(f's.recap(kind="前と後", pairs=[{pair_code}])' + note)
            elif kind_ == "筋":
                L.append(f's.recap(kind="筋", steps=["{q(sit)}", "{q(comp)}", "TODO だから（手段・理由）", "{q(ans)}"], points=[{pl}])' + note)
            elif kind_ == "次の一歩":
                L.append(f's.recap(kind="次の一歩", answer="{q(ans)}", actions=[{pl if pts else chr(34) + "TODO 明日からやること1" + chr(34) + ", " + chr(34) + "TODO 2" + chr(34)}])' + note)
            elif kind_ == "選び方":
                pair_code = pair_code or '("TODO こんなとき1", "TODO 選ぶもの1"), ("TODO こんなとき2", "TODO 選ぶもの2")'
                L.append(f's.recap(kind="選び方", pairs=[{pair_code}])' + note)
            else:
                L.append(f's.recap("{q(opn)}", "{q(ans)}", [{pl}])' + note)
        elif role in ("確認問題", "解答"):
            L.append("s = deck.slide(T)   # summary なし：帯も●も無い枚になる")
            if foreign and re.search(r"[ぁ-んァ-ヶ一-龥]", head or role):   # 日本語の見出しのままなら、その言語の決まった見出しに
                ids = re.findall(r"\d+-\d+", head or "")
                rng = f" ({ids[0]} to {ids[-1]})" if len(ids) >= 2 else f" ({ids[0]})" if ids else ""
                head = ("Review Questions" if role == "確認問題" else "Answers") + rng
            L.append(f's.heading("{q(head or role)}")')
            if quiz.get(n):   # 設計メモの6節から scaffold.py が入れた（長ければ短く。くわしい説明は原稿へ）
                L.append("qa(s, [" + ", ".join(f'("{q(k)}", "{q(t)}")' for k, t in quiz_wrapped(quiz)[n]) + "])")
            else:
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
            import figplan
            ppt = figplan.pptx_part(fig) if fig not in EMPTY else None
            refs = datamod.refs(fig) if fig not in EMPTY else []
            cap = short_source(dsets[refs[0]]["fields"].get("出典", "")) if refs and refs[0] in dsets else ""
            cap_arg = f', caption="{q(cap)}"' if cap else ""
            if place.get(n) == "main":   # 図が主役：図を先に置き、文は右の細い列（1行13字前後。補足は図の読み方と言えること）
                L.append(f'if (FIG / "s{n:02d}.png").exists(): s.figure_main(FIG / "s{n:02d}.png"{cap_arg})   # 図：{fig[:60]}（図が主役の型。scaffold.py が左文右図を半分までにするため選んだ）')
            lim = 13 if place.get(n) == "main" else 13 if ppt and ppt.startswith("s.decision") else 16 if ppt and ppt.startswith("s.compare") else 19
            pname = ppt.split("（")[0].strip() if ppt else None
            if pname == "s.table":
                cc = table_code(fig, beside=len(pts) >= 2)
            else:
                cc = PART_CODE.get(pname, lambda _f: None)(fig) if ppt else None
            first_part = pname in ("s.key_message", "s.before_after")   # 帯のすぐ下に置き、本文はその下へ
            if cc and first_part:
                L.append(cc + "   # 図の案から scaffold.py が組んだ（言い方を確かめる）")
            L += form_code(col(r, "本文の形"), pts, lim)
            if ppt and not first_part or (ppt and not cc):
                L.append(cc + "   # 図の案から scaffold.py が組んだ（言い方を確かめる）" if cc else f'# TODO {fig[:60]}（画像ではなく {ppt} で組む）')
            elif fig not in EMPTY and place.get(n) != "main":
                L.append(f'if (FIG / "s{n:02d}.png").exists(): s.figure_beside(FIG / "s{n:02d}.png"{cap_arg})   # 図：{fig[:60]}（図は figs/s{n:02d}.png）')
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


# 出典の列に、作り手の確かめのメモ（「検索の抜粋で確認」「強さは原稿で…と断る」「本文は未読」など）が括弧で入ることがある。
# 原稿の ※ の行は講師が読む所なので、書名・URL・頁や図の場所だけを残す（試しで、採点者に「読み上げにくい・作り手のメモが混ざる」と言われた）
MAKER_NOTE = re.compile(r"確認|確か|未読|未開封|未取得|未参照|取得|検索|担当|メイン側|原稿|断る|断定|スライド|載せ|載る|書く|本文で|頁は|ページは|一致|資料外|記載|割れる|写した")


def clean_source(src: str) -> str:
    """出典の文から、作り手のメモの括弧と「検索で確かめた」の前置きを外す。"""
    t = re.sub(r"[（(]([^（）()]*)[）)]", lambda m: "" if MAKER_NOTE.search(m.group(1)) else m.group(0), src)
    t = re.sub(r"^(?:ウェブ|Web|web)?(?:検索で|で)?確かめた", "", t.strip())
    head, *rest = re.split(r"(?<=。)", t)   # 2文目からの作り手のメモ（「一次資料は未確認」など）も外す
    t = head + "".join(x for x in rest if not MAKER_NOTE.search(x))
    return re.sub(r"\s{2,}", " ", t).strip(" 、，,。")


def note_sources(text: str, cells: str) -> list:
    """本文の要点・図の案の〔事実N〕〔データN〕から、3節・3b節の出典の「※ 出典：…」の行（スクリプトが原稿に入れる）。"""
    out = []
    try:
        import facts
        _, fh, frows = facts.memo_facts(text)
        i_src = next((k for k, h in enumerate(fh) if "出典" in h), 2)
    except BaseException:
        frows, i_src = [], 2
    import data as datamod
    ds = datamod.datasets(text)
    refs = []
    for tag in re.findall(r"〔([^〕]*)〕", cells):   # 〔事実3・11〕〔データ1〕
        for kind_, nums in re.findall(r"(事実|データ)\s*([0-9・、,\s]+)", tag):
            refs += [(kind_, int(x)) for x in re.findall(r"\d+", nums)]
    for kind_, n in refs:
        if kind_ == "事実" and 1 <= n <= len(frows) and len(frows[n - 1]) > i_src:
            src = frows[n - 1][i_src]
        elif kind_ == "データ" and n in ds:
            src = ds[n]["fields"].get("出典", "")
        else:
            continue
        src = clean_source(src)
        line = f"※ 出典：{src}"
        if src and line not in out:
            out.append(line)
    return out


def notes_md(kind, rows, care, minutes=None, text: str = "") -> str:
    """原稿の骨組み。確認問題・解答の枚は設計メモの6節から原稿を書き、本文の枚には出典の行（※）を入れる（スクリプトで書ける所は書く）。"""
    body = [r for r in rows if (col(r, "役割") or "本文") == "本文"]
    quiz = quiz_slices(text, rows) if text and kind == "memo" else {}
    try:
        import structures
        qi = structures.quiz_items(text) if text and kind == "memo" else {}
    except Exception:
        qi = {}
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
        if role == "確認問題" and quiz.get(n):
            text_ = "確認問題です。まず自分で答えを考えてから、次の枚の解答と比べてください。\n\n" + "\n\n".join(f"{k}。{t}" for k, t in quiz[n])
            L += [f"## {n}", "", text_, ""]
            continue
        if role == "解答" and quiz.get(n):
            parts = []
            for k, t in quiz[n]:
                it = qi.get(k, ("", "", "", "", []))
                el = [TAG.sub("", e).strip() for e in (it[4] or []) if e.strip()]
                basis = (re.findall(r"(\d+)\s*枚", it[2] or "") if isinstance(it[2], str) else [str(it[2])] if isinstance(it[2], int)
                         else [str(x) for x in (it[2] or [])])
                back = f"{'・'.join(basis)}枚目で見たことを思い出してください。" if basis else ""
                need = ("、".join(f"「{e}」" for e in el[:-1]) + f"、それに「{el[-1]}」" if len(el) >= 2 else f"「{el[0]}」" if el else "")
                parts.append(f"{k} です。{back}答えは、{t.rstrip('。')}。"
                             + (f"\n\n{need}{'の' + str(len(el)) + 'つ' if len(el) >= 2 else ''}が入っていれば正解です。" if el else ""))
            L += [f"## {n}", "", "\n\n".join(parts), ""]
            continue
        src = note_sources(text, col(r, "本文の要点") + " " + col(r, "図で見せるもの", "図")) if text and role == "本文" else []
        L += [f"## {n}", "<!-- " + " ／ ".join(hint).replace("--", "—") + " -->", "", "TODO"] + ([""] + src if src else []) + [""]
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


def geometry_marks(prs, check_layout):
    """描かなくても枠の位置で分かること（--try 用）：文の塊の数と、右・下のはみ出し。
    比べの試しで、仕上げ役の最初の make_deck に、図を右に置きすぎたはみ出しと塊の多さの ERROR が並び、直しの往復が増えた。
    文字の実際の高さは描かないと分からないので、文字の箱の下のはみ出しは △（枠で測った目安）にする。"""
    EMU = 12700   # → pt（check_layout と同じ単位）
    sl = prs.slides[0]
    W, H = prs.slide_width / EMU, prs.slide_height / EMU
    items, pn_top = [], None
    for sh in sl.shapes:
        size = None
        if sh.has_text_frame:
            size = next((r.font.size.pt for p in sh.text_frame.paragraphs for r in p.runs if r.font.size), None)
        ph = sh.placeholder_format.type if sh.is_placeholder else None
        d = {"name": sh.name, "type": int(sh.shape_type) if sh.shape_type is not None else None,
             "left": sh.left / EMU, "top": sh.top / EMU, "width": sh.width / EMU, "height": sh.height / EMU,
             "ph": int(ph) if ph is not None else None, "text": sh.text_frame.text if sh.has_text_frame else "", "size": size}
        if (sh.is_placeholder and sh.placeholder_format.idx == 12) or "Slide Number" in sh.name:
            pn_top = d["top"]
        items.append(d)
    out = []
    n = 0 if check_layout.is_qa_slide(items) or check_layout.is_cover_slide(items) else check_layout.text_units(items)   # 確認問題・解答・表紙は数えない（描画の検査と同じ）
    if n >= check_layout.UNITS_MAX:
        out.append(("✘", "文の塊", f"{n} つ（2つまで、多くて3つ）。結論に要る塊だけ残し、ほかは原稿へ"))
    elif n >= check_layout.UNITS_WARN:
        out.append(("△", "文の塊", f"{n} つ（目安は2つまで）。3つ目は結論に要るか"))
    right = W - check_layout.PAGE_MARGIN + 0.2 * 72   # 0.2 in の遊び（描画の検査は図の描いた範囲で測るので、枠だけで少し越えるのは通る）
    bottom = (pn_top if pn_top is not None else H - 0.48 * 72) + 1
    shown = [d for d in items if d["ph"] is None and not d["name"].endswith("の地")]   # 区切りの枚の全面の地は除く
    wide = [d for d in shown if d["left"] + d["width"] > right]
    if wide:
        hard = [d for d in wide if d["type"] != 17]   # 文字の箱（17）は、折り返さないと枠が文字より広い
        out.append(("✘" if hard else "△", "右のはみ出し", "・".join(f"{d['name'][:12]}（右端 {(d['left'] + d['width']) / 72:.2f} in）" for d in wide[:3])
                    + f" → 右の余白 0.4 in（{(W - check_layout.PAGE_MARGIN) / 72:.2f} in まで）に収める。図は fig_x から描いた幅のまま置く"))
    low = [d for d in shown if d["top"] + d["height"] > bottom]
    if low:
        hard = [d for d in low if not d["text"]]
        out.append(("✘" if hard else "△", "下のはみ出し", "・".join(f"{d['name'][:12]}（下端 {(d['top'] + d['height']) / 72:.2f} in）" for d in low[:3])
                    + " → ページ番号より上に" + ("" if hard else "（文字の箱は枠で測った目安。描くと収まることもある）")))
    return out


FIT_FIG = {"beside": (5.2, 3.8), "main": (7.0, 4.6)}   # 見積もりで置く図の大きさ（in）：figs_py が渡す大きさの中ほど（左文右図は 5.0〜5.8 in 幅）
FIT_BIG = 0.3   # これより大きい超え（in）を先に出す（zemi が自分で詰めるのは 0.3 in まで）


def fit_estimate(work: Path) -> list:
    """設計メモ（memo.md）・構成案（outline.md）の各枚を、骨組み（build_py）と同じ部品・同じ幅・同じ折り返しで組んでみて
    （描かない。図はまだ無いので、figs_py が渡す大きさの白い画像を置く）、zemi.py が組む時点に出す知らせを集める。
    戻り値 [(枚, 超え in, 文)]：本文の場所に入らない枚（超えの大きい順）と、列・図の横に入らず折り返した要点（超え 0）。
    見積もり：要点の言い方は制作の担当が変えるので、外れることがある（check_memo は △ で出す）。"""
    import contextlib
    import io
    import tempfile
    import figplan
    from PIL import Image
    kind, title, rows, _ = plan(work)
    code = build_py(work, kind, title, rows)
    place = placements(rows)
    out = []
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        (td / "figs").mkdir()
        for r in rows:
            fig = col(r, "図で見せるもの", "図")
            if (col(r, "役割") or "本文") == "本文" and fig not in EMPTY and not figplan.pptx_part(fig):
                w, h = FIT_FIG["main" if place.get(r["#"]) == "main" else "beside"]
                Image.new("RGB", (int(w * 220), int(h * 220)), "white").save(td / "figs" / f"s{r['#']:02d}.png", dpi=(220, 220))
        code = code.replace('FIG = HERE / "figs"', f'FIG = Path(r"{td / "figs"}")')
        code = code.replace('deck = Deck(workdir=HERE / "build"', f'deck = Deck(workdir=Path(r"{td / "build"}")')
        code = code[:code.index('NOTES = load_notes(')]
        g = {"__file__": str(work / "build.py"), "__name__": "__fit__"}
        with contextlib.redirect_stdout(io.StringIO()):
            exec(compile(code, str(work / "build.py"), "exec"), g)   # noqa: S102  骨組みのコード（scaffold が設計メモから作ったもの）
            deck = g["deck"]
            report = deck.fit_report()
    nums = [r["#"] for r in rows]
    row_of = lambda i: nums[i - 1] if 0 < i <= len(nums) else i   # noqa: E731  枚の順 → 表の番号（1行が1枚）
    lim = {r["#"]: (13 if place.get(r["#"]) == "main" else 13 if (figplan.pptx_part(col(r, "図で見せるもの", "図") or "") or "").startswith("s.decision")
                    else 16 if (figplan.pptx_part(col(r, "図で見せるもの", "図") or "") or "").startswith("s.compare") else 19) for r in rows}
    import re as _re
    for i, msg in report:
        n = row_of(i)
        r_ = _re.search(r"^(.+?)の右端 [\d.]+ in、限り [\d.]+ in（([\d.]+) in 超え", msg)
        g_ = _re.search(r"と(.+?)の間 (-?[\d.]+) in < ([\d.]+) in", msg)
        if r_:
            out.append((n, float(r_.group(2)), f"{n}枚目：右に {float(r_.group(2)):.1f} in 入らない見込み（{r_.group(1)[:8]}）→ 文・箱を短く"))
        elif g_:   # 図との間（0.4 in）だけの不足は出さない（図の幅は図の担当が本文に合わせて 5.0〜5.8 in で描く）
            pass
        elif "に重なる（文の右端" in msg:
            o_ = _re.search(r"文の右端 ([\d.]+) in、図の左端 ([\d.]+) in", msg)
            ov = float(o_.group(1)) - float(o_.group(2)) if o_ else 0.5
            out.append((n, ov, f"{n}枚目：文が図に {ov:.1f} in 重なる見込み → 図の横の要点を短く（展開は左右とも短く）か、図を下に置く型に"))
        m = _re.search(r"^(.+?)の下端 [\d.]+ in、限り [\d.]+ in（([\d.]+) in 超え", msg)
        if not m:
            continue
        over = float(m.group(2))
        part = m.group(1)
        k = max(1, int(-(-over // (22 * 1.2 / 72))))
        what = {"比較": f"比較の各列は1行{lim.get(n, 16)}字まで・各列3行のまま", "カード": "カードの説明は短く・カードの数はそのまま",
                "表": "表のセルは短く", "図": "図の高さ"}.get(part, f"本文は1行{lim.get(n, 19)}字まで")
        out.append((n, over, f"{n}枚目：要点が {over:.1f} in 入らない見込み（{what}。あと{k}行ほど多い）→ 要点を1つ減らすか短く"))
    # 列・図の横の1行に入らない要点は、組むときに zemi が折り返す（それで高さが足りなくなった枚は上の「入らない見込み」に出る）ので、ここでは出さない
    out.sort(key=lambda x: (-x[1], x[0]))
    return out


def fit_marks(work: Path) -> list:
    """check_memo・check_outline の △ の行（入りの見込み）。見積もれなければ空。"""
    try:
        est = fit_estimate(work)
    except Exception:   # noqa: BLE001  骨組みが組めない設計（読めない図の案など）は、ほかの確認が ✘ で出す
        return []
    if not est:
        return [("✔", "入りの見込み", "骨組みと同じ部品・幅で組むと、どの枚も本文の場所に入る")]
    big = [m for _, o, m in est if o > FIT_BIG]
    rest = [m for _, o, m in est if o <= FIT_BIG]
    shown = (big + rest)[:6]
    return [("△", "入りの見込み", "；".join(shown) + (f"；ほか {len(est) - len(shown)} 件" if len(est) > len(shown) else "")
             + "（骨組みと同じ部品・幅で、塊の間を詰めたうえで組んだ見積もり。要点の言い方が変わると外れることもある）")]


TRY_TYPES = {}   # --try all：枚 → (スライドの型, 本文の枚か)。左文右図が本文の半分を超えないかを、組む前に見る


def try_part(work: Path, n: int) -> int:
    """parts/NN.py の1枚だけを組んで、構成案どおりか（本文の形・図・結論）と字数を短く出す。描かない。
    書き手が部品のソースや検査のスクリプトを読みに行かずに、自分の1枚を確かめるための道具。"""
    import subprocess
    part = work / "parts" / f"{n:02d}.py"
    b = (work / "build.py").read_text(encoding="utf-8")
    bl = blocks(b)
    if not bl:
        print("✘ build.py に枚の印（# ---- N）が無い")
        return 1
    if not part.exists() and n not in bl:
        print(f"✘ {part} が無い")
        return 1
    head = b[:min(a for a, _ in bl.values())]
    if part.exists():
        code = MARK.sub("", part.read_text(encoding="utf-8")).strip("\n")
    else:   # parts を使わない回（軽量）：build.py のその枚
        x0, y0 = bl[n]
        code = MARK.sub("", b[x0:y0]).strip("\n")
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
    rows_ += geometry_marks(prs, check_layout)
    for ln in (r.stdout or "").splitlines():   # 組む時点の知らせ（zemi.py：本文の場所に入るか・図との間・構造の決まり）
        if "[WARN]" in ln and "1枚目：" in ln:
            rows_.append(("△", "組む時点", ln.split("1枚目：", 1)[1].strip()))
    TRY_TYPES[n] = (figplan.slide_type(prs.slides[0], prs.slide_width, prs.slide_height), roles.get(n) == "本文")
    lines = []
    for sh in prs.slides[0].shapes:
        tx = sh.has_text_frame and sh.text_frame.text.strip()
        if tx and not sh.is_placeholder and sh.name != "見出し":   # 上の帯・ページ番号・青帯は数えない
            lines += [l.strip() for l in sh.text_frame.text.splitlines() if l.strip()]
    import language as LG
    from slide_profile import read_options
    lang = read_options(text).get("言語")
    size = (lambda l: len(_flat(l))) if LG.is_japanese(lang) else (lambda l: round(LG.measure(_flat(l), lang)))   # 日本語でなければ全角に直した幅
    chars = sum(size(l) for l in lines)
    long_ = [l for l in lines if size(l) > 20]
    rows_.append(("△" if long_ else "✔", "1行20字", "超える行：" + "／".join(l[:24] for l in long_[:3]) if long_ else "すべて20字まで"))
    if tm.get("notes"):
        rows_.append(("△", "出どころの断り", "／".join(x[:28] for x in tm["notes"][:3]) + " → スライドから外し、原稿の ※ 行へ"
                      "（残してよいのは図の「（概略）」と「（講師の解釈）」〔発表は「（発表者の解釈）」〕だけ）"))
    if tm.get("subs"):
        rows_.append(("△", "下付き", "・".join(dict.fromkeys(tm["subs"])) + " → 下付きは `_{p}` で書く（例 \"x²_{n}\"）"))
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


NOTE_SEC = re.compile(r"^## (\d+)\s*\n(.*?)(?=^## \d+|\Z)", re.S | re.M)
TODO_LINE = re.compile(r"^TODO[ \t]*$", re.M)


def notes_todo(work: Path) -> list:
    """notes.md の TODO の枚：「[N] 目安…」（枚の頭のコメントを1行に縮めて）。"""
    f = work / "notes.md"
    if not f.exists():
        return []
    out, seen = [], []
    for m in NOTE_SEC.finditer(f.read_text(encoding="utf-8")):
        if TODO_LINE.search(m.group(2)):
            c = re.search(r"<!--(.*?)-->", m.group(2), re.S)
            parts = [x.strip() for x in re.sub(r"\s+", " ", c.group(1) if c else "").split("／") if x.strip()]
            keep = []
            for x in parts:   # どの枚にも同じ言い方（目安・「1文目で…」）は最初の1回だけ出す
                x2 = x.replace("（1文目でこの語のつながりを言う）", "")
                if x2.startswith("目安"):
                    if x2 in seen:
                        continue
                    seen.append(x2)
                keep.append(x2)
            out.append(f"[{m.group(1)}] " + " ／ ".join(keep)[:220])
    if out:
        out.append("（前の枚から：1文目でこの語のつながりを言う。目安が書かれていない枚は、上の枚と同じ目安）")
    return out


def figs_todo(work: Path) -> list:
    """figs.py の TODO の図：「f_s02（14行目）：図の案…」。"""
    f = work / "figs.py"
    if not f.exists():
        return []
    t = f.read_text(encoding="utf-8").splitlines()
    out = []
    for i, l in enumerate(t):
        m = re.match(r"def (f_\w+)\(", l)
        if m and i + 1 < len(t) and "TODO" in t[i + 1]:
            out.append(f"{m.group(1)}（{i + 1}行目）：" + t[i + 1].strip().strip('"').replace("TODO ", "", 1)[:520])
    return out


NOTE_TAG = re.compile(r"\s*〔事実\s*\d+[^〕]*〕")       # 設計メモの事実の印（原稿には要らない）
MEMO_LINE = re.compile(r"^\s*※\s*[（(]メモ[)）].*$\n?", re.M)   # 作り手のメモの行（読み上げない）


def spoken(text: str) -> str:
    """script.md の1枚の原稿から、読み上げない物を外す：〔事実N〕の印と「※（メモ）」の行。
    地震の試しで、推論距離の担当が足した〔事実16〕などの印と作業のメモが原稿に残り、採点者2人が「読み上げられない」と減点した。"""
    return NOTE_TAG.sub("", MEMO_LINE.sub("", text)).strip()


def fill_notes(work: Path, src: Path):
    """「## N」ごとの原稿を、notes.md のその枚の TODO の行に入れる（ほかの行はそのまま）。入れた枚と、まだ TODO の枚を返す。"""
    f = work / "notes.md"
    text = f.read_text(encoding="utf-8")
    new = {int(m.group(1)): spoken(m.group(2)) for m in NOTE_SEC.finditer(src.read_text(encoding="utf-8")) if spoken(m.group(2))}
    done = []

    def put(m):
        n, body = int(m.group(1)), m.group(2)
        if n in new and TODO_LINE.search(body):
            done.append(n)
            body = TODO_LINE.sub(lambda _: new[n], body, count=1)
        return f"## {m.group(1)}\n" + body
    text = NOTE_SEC.sub(put, text)
    f.write_text(text, encoding="utf-8")
    left = [int(m.group(1)) for m in NOTE_SEC.finditer(text) if TODO_LINE.search(m.group(2))]
    return done, left


def terms_to_readme(work: Path):
    """設計メモの4節（用語・記号の決め事）を、講座の README の「決め事」に写す（references/course.md 4節「スライドを作る前に
    README の決め事に写す」）。標準の流れでは写す担当がおらず、比べの4本とも README の決め事が下書きのままだった。
    担当にさせず、組む前にスクリプトが写す。同じ回の行は置き換える。戻り値は知らせの1行（写さなかったら None）。"""
    memo, m = work / "memo.md", re.search(r"_(\d{2})$", work.name)
    readme = work.parent.parent / re.sub(r"_\d{2}$", "", work.name) / "00_README.md"
    if not (memo.exists() and readme.exists() and m):
        return None
    sec = re.search(r"^## 4\..*?$(.*?)(?=^## |\Z)", memo.read_text(encoding="utf-8"), re.S | re.M)
    terms = [l.strip()[2:].strip() for l in (sec.group(1).splitlines() if sec else []) if l.strip().startswith("- ")]
    terms = [t for t in terms if t and t not in ("なし", "—")]
    if not terms:
        return None
    n = int(m.group(1))
    tag = f"（第{n}回）"
    with open(readme, encoding="utf-8", newline="") as f:   # 改行をそのまま読む（CRLF の README を LF にしない）
        raw = f.read()
    eol ="\r\n" if "\r\n" in raw else "\n"
    lines = raw.splitlines()
    head = next((i for i, l in enumerate(lines) if l.startswith("## 決め事")), None)
    if head is None:
        return None
    end = next((i for i in range(head + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    body = [l for l in lines[head + 1:end] if not l.startswith(f"- {tag}") and "<回を作るたびに足す>" not in l]
    while body and not body[-1].strip():
        body.pop()
    body += [f"- {tag}{t}" for t in terms] + [""]
    tail = eol if raw.endswith(("\n", "\r")) else ""
    readme.write_text(eol.join(lines[:head + 1] + body + lines[end:]) + tail, encoding="utf-8", newline="")
    return f"README の決め事に用語・記号を写した（第{n}回・{len(terms)}行）"



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
        nums = sorted(int(f.stem) for f in (work / "parts").glob("[0-9][0-9].py"))
        if not nums and (work / "build.py").exists():   # parts を使わない回（軽量）：build.py の本文の枚
            nums = [k for k in sorted(blocks((work / "build.py").read_text(encoding="utf-8"))) if k > 1]
        for k in nums:   # 全部の枚：直す所がある枚だけ中身を出す
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                code = try_part(work, k)
            rows = [l for l in buf.getvalue().splitlines() if l[:1] in ("✘", "△")]
            bad += code
            print(f"[{k:02d}] " + ("✔" if not rows else "\n  " + "\n  ".join(rows)))
        import figplan
        body = [t for t, is_body in TRY_TYPES.values() if is_body]
        side = sum(t == "左文右図" for t in body)
        if body and side > figplan.MAX_SHARE * len(body):   # 渡す前の確認の「左に文・右に図の数」と同じ基準（試しで、軽量の回が10枚中9枚になった）
            print(f"[型] ✘ 左に文・右に図が本文 {len(body)} 枚のうち {side} 枚（半分まで）。図そのものを読ませる枚は s.figure_main、"
                  "横長の図は下に、並べる中身はカード、比べるなら比較にする（組む前に直す。渡す前の確認が ✘ にする）")
            bad += 1
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
    if "--light" in argv:   # 軽量の制作の担当の準備を1回の呼び出しで（呼ぶたびに会話を読み直すので、続けてよいものはまとめる）
        import subprocess
        py = [sys.executable, "-X", "utf8"]
        if not (work / "build.py").exists():
            code = main([str(work)])
            if code:
                return code
        main([str(work), "--figs"])
        for title, cmd in (("図の下書きの雛形", py + [str(HERE / "figdraft.py"), str(work)]),
                           ("設計メモの話の順番・事実と出典", py + [str(HERE / "guide.py"), str(work / "memo.md"), "2", "3"])):   # 確認問題（6節）はもう build.py・notes.md に入れた
            if title.startswith("設計メモ") and not (work / "memo.md").exists():
                cmd = py + [str(HERE / "guide.py"), str(work / "outline.md"), "2"]
            r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
            print(f"\n===== {title}\n" + (r.stdout or r.stderr).strip())
        btxt = (work / "build.py").read_text(encoding="utf-8")
        b = btxt.splitlines()
        todo = [f"{i}: {l.strip()[:120]}" for i, l in enumerate(b, 1) if "TODO" in l and not l.startswith('"""')]
        print("\n===== build.py に残った TODO\n" + ("\n".join(todo) or "なし"))
        # notes.md・figs.py の TODO も、ここに並べる（担当がファイルを全文で開かなくて済むように。コミュニケーション講座の試しで、
        # 制作の担当が build.py・figs.py・notes.md を cat して、その約4万字を以後の毎回読み直していた）
        print("\n===== notes.md の TODO の枚（原稿を書く枚と、その枚の目安）\n" + ("\n".join(notes_todo(work)) or "なし")
              + f"\n→ 原稿は「## N」の見出しごとに1つのファイルに書き、`python \"{HERE.as_posix()}/scaffold.py\" {work.as_posix()} --fill-notes <そのファイル>` で"
              "入れる（notes.md は開かない。TODO の所だけ置き換わり、※ の行・確認問題の原稿は残る）")
        print("\n===== figs.py の TODO の図\n" + ("\n".join(figs_todo(work)) or "なし"))
        common = work / "cards" / "00_共通.md"
        if common.exists():
            print("\n===== 書き方の共通の決まり（cards/00_共通.md）\n" + common.read_text(encoding="utf-8").strip())
        # TODO の枚の部品の書き方（カードの節）を、同じ行は1回だけにまとめて出す（枚ごとに出すと s.block などが7回並んだ）
        uses, seen, ks = [], set(), []
        for k, (x0, y0) in sorted(blocks(btxt).items()):
            card = work / "cards" / f"{k:02d}.md"
            if "TODO" in btxt[x0:y0] and card.exists():
                m = re.search(r"^## 使う部品の書き方.*?(?=^## |\Z)", card.read_text(encoding="utf-8"), re.S | re.M)
                if m:
                    ks.append(k)
                    for line in m.group(0).strip().splitlines()[1:]:
                        if line.strip() and line not in seen:
                            seen.add(line)
                            uses.append(line)
        if uses:
            print(f"\n===== TODO の枚（{'・'.join(map(str, ks))}）で使う部品の書き方（これ以上の説明は要るときだけ `guide.py structures`）\n"
                  + "\n".join(uses))
        return 0
    if "--fill-notes" in argv:
        k = argv.index("--fill-notes")
        if k + 1 >= len(argv):
            print("✘ --fill-notes <「## N」ごとに原稿を書いたファイル>")
            return 1
        done, left = fill_notes(work, Path(argv[k + 1]))
        print(f"入れた：{'・'.join(map(str, done)) or 'なし'}" + (f"。まだ TODO の枚：{'・'.join(map(str, left))}" if left else "。notes.md の TODO は無い"))
        return 0
    if "--figs" in argv:   # 軽量の回：figs.py の出発点（データの棒グラフは描き上げ、ほかは TODO）。もうあれば書かない
        fp = work / "figs.py"
        if fp.exists():
            print("figs.py はもうある（書き換えない）")
            return 0
        _, _, rows_, _ = plan(work)
        kind_ = "memo" if (work / "memo.md").exists() else "outline"
        fp.write_text(figs_py(work, rows_, (work / f"{kind_}.md").read_text(encoding="utf-8")), encoding="utf-8")
        t = fp.read_text(encoding="utf-8")
        print(f"figs.py を作った：描き上げた図 {t.count('scaffold.py が3b節の表から描いた')}・TODO の図 {t.count('raise NotImplementedError')}")
        return 0
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
                         else build_py(work, kind, title, rows)), ("notes.md", notes_md(kind, rows, care, minutes, (work / {"memo": "memo.md", "answers": "answers.md"}.get(kind, "outline.md")).read_text(encoding="utf-8") if (work / {"memo": "memo.md", "answers": "answers.md"}.get(kind, "outline.md")).exists() else ""))):
        p = work / name
        if p.exists() and not force:
            print(f"・{name} はもうある（作らなかった。作り直すなら --force）")
            continue
        p.write_text(text, encoding="utf-8")
        made.append(name)
    script = work / "script.md"   # 設計の担当が書いた原稿（標準の回）：notes.md の TODO の枚に入れる（制作の担当は書き直さない）
    if "notes.md" in made and script.exists():
        done, left = fill_notes(work, script)
        made.append(f"原稿を script.md から {len(done)} 枚入れた" + (f"（まだ TODO：{'・'.join(map(str, left))}）" if left else ""))
    if "build.py" in made and kind == "memo":
        note = terms_to_readme(work)
        if note:
            made.append(note)
    if made:
        print(f"作った：{'・'.join(made)}（{len(rows)}枚）。確認問題・解答・図の置き方・比較は設計メモから入れた。残った TODO を書き換えてから make_deck.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
