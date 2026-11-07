"""型の辞書：本文の形（文字の塊の組み方）と、図解のスライドの型。zemi.py の部品・check_outline・check_memo・check_done・analyze_structure が使う。

本文の形は「1つの塊の中の書き方」と「塊どうしのつなぎ方」。どの AI で作っても同じ組み方になるように、
構成案・設計メモの表の「本文の形」の列で枚ごとに決め、部品（zemi.py）で組み、渡す前の確認で突き合わせる。
型は、研究発表のデッキ（ゼミの輪読・論文紹介・学会発表）を1枚ずつ見て取り出したものと、
研究発表のデザインの手引き・公開されたスライドの型の一覧から、研究発表に合うものを足したもの（references/structures.md）。
"""
from __future__ import annotations

import re
from pathlib import Path

# ---- 本文の形（文字の塊の組み方）。shapes：部品が付ける図形の名前（渡す前の確認がこれで見分ける）
TEXT_FORMS = [
    dict(key="帰結", name="前提 ⇒ 帰結", part="s.lead(lines, then)",
         when="2〜3行の説明のあと、その結果・意味を「⇒ 赤字の一言」で", shapes=("帰結",)),
    dict(key="ラベル", name="ラベル＋説明", part="s.block(head, lines, then=None)",
         when="効果・手法・用語の名前を小見出しにして、下に1〜2行を字下げ。定義を並べる", shapes=("塊の見出し",)),
    dict(key="展開", name="横の矢印で展開", part="s.develop(left, right)",
         when="左に条件・前の状態、右に結果・次の状態", shapes=("展開の左", "展開の右")),
    dict(key="縦の結論", name="縦の矢印で結論へ", part="s.lead_down(premise, conclusion)",
         when="背景・問題から、目的・結論を導く（学会発表の導入・まとめ）", shapes=("縦の前提",)),
    dict(key="場合分け", name="条件の場合分け", part="s.cases([(条件, 説明), ...])",
         when="温度域・符号・条件ごとに振る舞いが変わる", shapes=("場合分け",)),
    dict(key="問い", name="問い → 答え", part="s.ask(question, answer)",
         when="考えられる別の説明を1つずつ確かめる・否定する（検証の筋）", shapes=("問い",)),
    dict(key="手順", name="番号の手順", part="s.numbered(items)",
         when="解析・試料作成・測定の手順", shapes=("手順",)),
    dict(key="式の注釈", name="式の項への注釈", part="s.peq(...) と s.defs(...)",
         when="式の各項・記号の意味を式の右に", shapes=("定義",)),
    dict(key="箇条", name="短い箇条", part="s.p(...)",
         when="上のどれにも当たらない短い並び（多用しない）", shapes=()),
]
FORM_KEYS = [f["key"] for f in TEXT_FORMS]
NONE_FORM = ("—", "-", "－", "なし", "")   # 本文の形が無い枚（全面の図・大きな数字だけ・区切り）

# ---- 図解のスライドの型（figplan.slide_type が名前で見分ける）
DIAGRAM_TYPES = [
    dict(key="並列カード", part='s.cards(items, layout="row")', when="手法の要素・条件・候補を同格に2〜4個", shape="カード_並列"),
    dict(key="格子のカード", part='s.cards(items, layout="grid")', when="同格の要素が4〜6個", shape="カード_格子"),
    dict(key="段違いの順序", part='s.cards(items, layout="steps")', when="段階のある手順（3〜4段）", shape="カード_段違い"),
    dict(key="循環", part='s.cards(items, layout="cycle")', when="測定→解析→モデル→次の測定のような繰り返し（4つ）", shape="カード_循環"),
    dict(key="ツリー", part="s.tree(root, children)", when="分類・階層（大分類から小分類）", shape="ツリー"),
    dict(key="前後", part="s.before_after(before, after, value)", when="従来と改善を並べ、差を1つの数で", shape="前後"),
    dict(key="2つ並べた図", part="s.pair(left, right, labels, values)", when="条件の違う2つの図を並べ、下に数値", shape="並べた図"),
]
SKELETONS = [   # テンプレート1〜8（構造。番号は見やすさの順）。色は配色で変える（assets/templates/配色.json）
    dict(key="結論ヘッダー", when="上に小さく話題と見出し、その下に大きく結論の一文（左に主色の短い縦棒）、細い線で本文と分ける。下の帯は無く、本文が一番広い（テンプレート1）", style="header"),
    dict(key="結論タイトル", when="上に小さく話題、その下に大きく結論の一文。下の帯は無し（結論を見出しにする形）（テンプレート2）", style="title"),
    dict(key="細い左帯と副題", when="左端に主色の細い帯、大きなタイトルの下に結論の副題の1行。下の帯は無し（テンプレート3）", style="lead"),
    dict(key="下の帯", when="左上の縦棒とタイトル、下の帯に結論の1行（ゼミの基本の形）（テンプレート4）", style="band"),
    dict(key="上の帯", when="上の濃い帯にタイトル、下に「まとめ」の札つきの淡い帯（テンプレート5）", style="band"),
    dict(key="章のナビ", when="上に章の並び（今の章を主色に）、その下にタイトル、下に線で挟んだ結論の1行（長い発表）（テンプレート6）", style="band"),
    dict(key="結論の囲み", when="上に淡い帯（タイトルは中央）、下の帯は無く、結論は淡い色の囲みに（学会発表）（テンプレート7）", style="box"),
    dict(key="左の淡い柱", when="左の 34% の淡い柱にタイトル・結論・短い要点、右に図を大きく（図が主役の枚）（テンプレート8）", style="column"),
]

# 構造（json の "conclusion"）と本文の形の相性。本文の広さと結論の置き場が違うので、合わない形がある。
# 割合で決めるのではなく（形は中身で選ぶもの）、合わない組み合わせだけを △ にする
TOP_CONCLUSION = "結論を上の一文（見出しの下・副題）で言うので、本文の最後の「⇒ 赤字の帰結」が結論と重なりやすい。根拠を見せる形（ラベル・展開・問い）にする"
COMPAT = {
    "header": dict(avoid=("帰結",), good="ラベル・展開・問い・手順", why=TOP_CONCLUSION),
    "title": dict(avoid=("帰結",), good="ラベル・展開・問い・手順", why=TOP_CONCLUSION),
    "lead": dict(avoid=("帰結",), good="ラベル・展開・問い・手順", why=TOP_CONCLUSION),
    "band": dict(good="どれでも（帰結が一番合う）"),
    "box": dict(max_forms=1, good="塊1つ（帰結・ラベル・問いのどれか1つ）",
                why="本文が 48% と狭く、下に結論の囲みがある。重い組み方（3行の帰結を2つ など）は入りきらないので、塊は1つに絞る"),
    "column": dict(avoid=("展開", "場合分け", "式の注釈"), good="ラベル・帰結・箇条（柱の中の短い要点）",
                   why="文は左の柱の短い要点だけ（1行14字まで）。横に広がる形は柱に入らない"),
}


def template_of(folder, text: str = ""):
    """作業フォルダで使うテンプレートの {name, label, conclusion}。わからなければ None。
    名前は、構成案の「## オプション」の表の「テンプレート」の行 → build.py の deck_options(..., name=/place_name=) の順で見る。
    書いていなければ（build.py が deck_options(P) だけなら）既定（テンプレート1）で決まる。"""
    import json
    import slide_profile as sp
    name = place = None
    found = False
    m = re.search(r"^\|\s*テンプレート\s*\|\s*([^|]+?)\s*\|", text or "", re.M)
    if m:
        name, found = re.sub(r"（.*?）|\(.*?\)", "", m.group(1)).strip(), True
    b = Path(folder) / "build.py" if folder else None
    if not found and b and b.exists():
        src = b.read_text(encoding="utf-8", errors="replace")
        d = re.search(r"deck_options\(([^)]*)\)", src)
        if d:
            found = True
            n = re.search(r"name\s*=\s*[\"']([^\"']+)", d.group(1))
            p = re.search(r"place_name\s*=\s*[\"']([^\"']+)", d.group(1))
            name, place = (n.group(1) if n else None), (p.group(1) if p else None)
    if not found:
        return None
    prof = sp.load_profile(folder) if folder else {}
    n = sp.template_name(prof, name, place) if (name or place) else None
    pptx = sp.template(prof, n, _resolved=True)
    j = Path(pptx).with_suffix(".json")
    try:
        st = json.loads(j.read_text(encoding="utf-8"))
    except Exception:
        return None
    return dict(name=Path(pptx).stem, label=st.get("label", Path(pptx).stem), conclusion=st.get("conclusion", "band"))


def compat(plan: dict, body_no: list, tpl):
    """[(印, 項目, 説明)]：テンプレートに合わない本文の形の枚（△）。テンプレートがわからない・相性の決まりが無ければ []。"""
    rule = COMPAT.get((tpl or {}).get("conclusion"))
    if not rule or not plan:
        return []
    bad = []
    for i in body_no:
        keys = [k for k in plan.get(i, []) if isinstance(k, str)]
        hit = [k for k in keys if k in rule.get("avoid", ())]
        if hit:
            bad.append(f"[{i}] {'・'.join(hit)}")
        elif rule.get("max_forms") and len([k for k in keys if k != "箇条"]) > rule["max_forms"]:
            bad.append(f"[{i}] {'＋'.join(keys)}")
    if not bad:
        return [("✔", "テンプレートとの相性", f"{tpl['label']}（{tpl['name']}）に合わない形は無い")]
    return [("△", "テンプレートとの相性", f"{tpl['label']}（{tpl['name']}）に合いにくい形：{'、'.join(bad[:6])}。"
             f"{rule['why']}（合う形：{rule['good']}。references/structures.md の3節）")]


# 部品が付ける、本文の形の図形の名前（check_layout は図に数えず本文に数える、figplan は図の種類に数えない）
TEXT_SHAPE_NAMES = {n for f in TEXT_FORMS for n in f["shapes"]} | {"塊の本文", "答え", "縦の結論", "結論の囲み"}


def form_key(cell: str):
    """構成案の「本文の形」の1セルを、型の key（いくつか）に。分からない語は ("?", 語)。"""
    cell = (cell or "").strip()
    if cell in NONE_FORM:
        return []
    out = []
    for part in re.split(r"[／/・、,＋+]\s*", cell):
        part = part.strip()
        if not part:
            continue
        hit = next((f["key"] for f in TEXT_FORMS if part == f["key"] or part == f["name"] or f["key"] in part), None)
        out.append(hit or ("?", part))
    return out


def plan_forms(text: str, kind: str):
    """{スライド番号: [key, ...]}。kind="memo"（設計メモ2節）か "outline"（構成案の「## 構成」）。列が無ければ None。"""
    from check_memo import table_rows
    rows = table_rows(text, "話の順番") if kind == "memo" else table_rows(text, "構成")
    if not rows:
        return None
    head = rows[0]
    i_f = next((k for k, h in enumerate(head) if "本文の形" in h), None)
    if i_f is None:
        return None
    out = {}
    for r in rows[1:]:
        if r and r[0].strip().isdigit() and len(r) > i_f:
            out[int(r[0])] = form_key(r[i_f])
    return out


def detect_forms(slide) -> set:
    """スライドで使われた本文の形（部品の図形の名前と、「⇒」で始まる行）。"""
    names = set()
    has_arrow_down = False
    for sh in slide.shapes:
        names.add(sh.name)
        if sh.name == "矢印":
            try:
                has_arrow_down |= "DOWN" in sh.auto_shape_type.name
            except Exception:
                pass
    found = {f["key"] for f in TEXT_FORMS if any(n in names for n in f["shapes"])}
    for sh in slide.shapes:
        if getattr(sh, "has_text_frame", False) and sh.has_text_frame and sh.name not in ("見出し",):
            if any(p.text.strip().startswith("⇒") for p in sh.text_frame.paragraphs):
                found.add("帰結")
    return found


# ---- 本文の形の「入れる所」（スロット）。構成案・設計メモの「本文の要点」は、形の入れる所の書き方で書く。
# 形を選ぶと、要点を入れる所が決まる（展開なら左と右の2か所）。1か所に入る事実は0個のことも、2個以上のこともある。
# 要点は「 / 」で区切り、各要点の後ろに出どころ〔…〕。scaffold.py がこの書き方から部品の呼び出しを組む。
SLOTS = {
    "帰結":     dict(slots="前提（1〜3）／帰結（1）", write="「前提 / 前提 / ⇒ 帰結」（帰結は ⇒ の後ろ）", pat=r"⇒", need=1),
    "縦の結論": dict(slots="前提（1〜3）／結論（1）", write="「前提 / 前提 / ⇒ 結論」", pat=r"⇒", need=1),
    "ラベル":   dict(slots="見出し＋説明（1〜4組。最後に帰結を付けてよい）", write="「見出し：説明」（説明の後ろに「⇒ 帰結」も可）", pat=r"^[^：→⇒]{1,24}：", need=1),
    "場合分け": dict(slots="条件＋説明（2〜3組）", write="「条件：説明」を2つ以上", pat=r"^[^：→⇒]{1,24}：", need=2),
    "展開":     dict(slots="左（条件・前の状態）／右（結果・次の状態）", write="「左 → 右」", pat=r"→", need=1),
    "問い":     dict(slots="問い／確かめた結果（1〜3組）", write="「〜ではないか？⇒ 確かめた結果」", pat=r"[？?]\s*⇒", need=1),
    "手順":     dict(slots="段（2〜5）", write="「1. 段 2. 段 3. 段」（1つの要点に番号で並べる）", pat=r"[1１][.．](?![0-9])\s*\S.*[2２][.．](?![0-9])", need=1),
    "式の注釈": dict(slots="式／記号と意味", write="「式（＝を含む）」と「記号：意味」", pat=r"[=＝]", need=1),
    "箇条":     dict(slots="項目（2〜4）", write="短い項目を並べる", pat=None, need=0),
}
COLON_FORMS = ("ラベル", "場合分け")   # 「：」の要点を分け合う形


def point_texts(cell: str):
    """本文の要点のセル → 要点の文字列（出どころ〔…〕・★・下線の印を外す）。"""
    cell = re.sub(r"<br\s*/?>", "／", cell or "")
    parts = [p.strip() for p in re.split(r"\s+/\s+|／|；|;", cell) if p.strip()]
    return [re.sub(r"\s*〔[^〕]*〕", "", p).replace("★", "").strip() for p in parts]


def slot_kind(point: str, keys=None):
    """要点1つが、どの形の入れる所の書き方か（問い・展開・手順・式の注釈・コロン・帰結・None）。
    keys（その枚で選んだ形）があれば、その形の書き方だけを探す（見出しの中の「→」を展開と取り違えない）。"""
    keys = list(keys) if keys else list(SLOTS)
    for k in ("問い", "展開", "手順", "式の注釈"):
        if k in keys and re.search(SLOTS[k]["pat"], point):
            return k
    if any(k in keys for k in COLON_FORMS) and re.search(SLOTS["ラベル"]["pat"], point):
        return "コロン"
    if re.search(SLOTS["帰結"]["pat"], point):
        return "帰結"
    return None


def slot_problems(forms, points):
    """形の入れる所の書き方で書かれていない形の一覧 [(形, 書き方)]。"""
    keys = [k for k in forms if isinstance(k, str) and k in SLOTS]
    kinds = [slot_kind(p, keys) for p in points]
    out = []
    colon_need = sum(SLOTS[k]["need"] for k in keys if k in COLON_FORMS)
    for k in keys:
        if k in COLON_FORMS:
            if kinds.count("コロン") < colon_need:
                out.append((k, SLOTS[k]["write"]))
        elif k in ("帰結", "縦の結論"):
            if not any(re.search(r"⇒", p) and kinds[i] != "問い" for i, p in enumerate(points)):
                out.append((k, SLOTS[k]["write"]))
        elif SLOTS[k]["need"] and kinds.count(k) < SLOTS[k]["need"]:
            out.append((k, SLOTS[k]["write"]))
    return out


def check_slots(text: str, kind: str, body_no: list, where: str):
    """本文の要点が、選んだ本文の形の入れる所の書き方になっているか [(印, 項目, 説明)]。"""
    from check_memo import table_rows
    rows = table_rows(text, "話の順番") if kind == "memo" else table_rows(text, "構成")
    if not rows:
        return []
    head = rows[0]
    i_f = next((k for k, h in enumerate(head) if "本文の形" in h), None)
    i_p = next((k for k, h in enumerate(head) if "要点" in h), None)
    if i_f is None or i_p is None:
        return []
    bad = []
    for r in rows[1:]:
        if not (r and r[0].strip().isdigit()) or int(r[0]) not in body_no or len(r) <= max(i_f, i_p):
            continue
        for k, how in slot_problems(form_key(r[i_f]), point_texts(r[i_p])):
            bad.append(f"[{r[0]}] {k}なら{how}")
    if bad:
        return [("△", "本文の形の入れる所", "要点が形の入れる所の書き方になっていない：" + "；".join(bad[:6])
                 + "（形を選ぶと入れる所が決まる。事実はその所に入れる。references/structures.md 1節の「入れる所」）")]
    return [("✔", "本文の形の入れる所", "本文の要点が、選んだ形の入れる所の書き方になっている")]


def assign(forms, points):
    """[(形, [要点])]：要点を、書き方から形の入れる所に割り振る（scaffold.py が部品の呼び出しを組むのに使う）。
    どの形の入れる所の書き方でもない要点は、最後の ("余り", [...]) に（帰結・縦の結論・箇条があれば、その前提・項目に入れる）。"""
    keys = [k for k in forms if isinstance(k, str)] or ["箇条"]
    pool = {k: [] for k in keys}
    rest = []
    colon = [k for k in keys if k in COLON_FORMS]
    colon_pts = []
    for p in points:
        sk = slot_kind(p, keys)
        if sk == "コロン" and colon:
            colon_pts.append(p)
        elif sk in pool and sk != "帰結":
            pool[sk].append(p)
        elif sk == "帰結" and ("帰結" in pool or "縦の結論" in pool):
            pool["帰結" if "帰結" in pool else "縦の結論"].append(p)
        else:
            rest.append(p)
    if len(colon) == 2:   # ラベルと場合分け：後ろの2つ以上を場合分けに
        n = max(2, len(colon_pts) - 1) if len(colon_pts) > 2 else len(colon_pts)
        pool["場合分け"] += colon_pts[-n:]
        pool["ラベル"] += colon_pts[:-n]
    elif colon:
        pool[colon[0]] += colon_pts
    else:
        rest = colon_pts + rest
    tgt = next((k for k in ("帰結", "縦の結論", "箇条") if k in pool), None)
    if rest and tgt:   # どの書き方でもない要点：帰結・縦の結論があれば前提に（箇条ならそのまま）
        pool[tgt] = rest + pool[tgt]
        rest = []
    return [(k, pool[k]) for k in keys] + ([("余り", rest)] if rest else [])


RUN_LIMIT = 4   # 同じ本文の形だけの枚が続いてよい枚数（スライドの型の MAX_RUN と同じ）


def form_runs(seq, limit: int = RUN_LIMIT):
    """[(番号, [key, ...])] から、同じ形の組だけの枚が limit 枚を超えて続いた所 [(始め, 終わり, "帰結・ラベル")]。形の無い枚で切れる。"""
    out, run = [], []
    for i, keys in list(seq) + [(None, None)]:
        k = tuple(sorted(x for x in (keys or []) if isinstance(x, str)))
        if run and (k != run[0][1] or not k or i is None):
            if len(run) > limit:
                out.append((run[0][0], run[-1][0], "・".join(run[0][1])))
            run = []
        if k:
            run.append((i, k))
    return out


def check_plan(text: str, kind: str, body_no: list, where: str, folder=None):
    """構成案・設計メモの「本文の形」の列の確認 [(印, 項目, 説明)]。列が無い・分からない語は △、同じ形が5枚以上続いても △。
    folder（作業フォルダ）を渡すと、使うテンプレートに合わない形も △（compat）。"""
    plan = plan_forms(text, kind)
    if plan is None:
        return [("△", "本文の形", f"{where}の表に「本文の形」の列が無い。枚ごとに文字の組み方を決める（{'・'.join(FORM_KEYS)}。"
                 "references/structures.md）。決めないと、組み方が AI まかせになる")]
    res = []
    unknown = [(i, k[1]) for i in body_no for k in plan.get(i, []) if isinstance(k, tuple)]
    if unknown:
        res.append(("△", "本文の形", "分からない語：" + "・".join(f"[{i}]「{w}」" for i, w in unknown[:6])
                    + f"（使える名前：{'・'.join(FORM_KEYS)}）"))
    runs = form_runs([(i, plan.get(i, [])) for i in body_no])
    if runs:
        res.append(("△", "本文の形の続き方", "同じ形が続いている：" + "、".join(f"{a}〜{b}枚目が「{t}」" for a, b, t in runs)
                    + f"（{RUN_LIMIT}枚まで。内容に合う別の形にできないか見直す）"))
    if not res:
        used = sorted({k for i in body_no for k in plan.get(i, []) if isinstance(k, str)}, key=FORM_KEYS.index)
        res.append(("✔", "本文の形", f"本文 {len(body_no)}枚に形がある（使う形：{'・'.join(used) or 'なし'}）"))
    res += check_slots(text, kind, body_no, where)
    if folder is not None:
        res += compat(plan, body_no, template_of(folder, text))
    return res


# ---- 枚の役割（構成案・設計メモの「役割」の列。AI はこの語から選ぶ。スクリプトが結論の列とスライドに突き合わせる）
# 質問待機：発表の最後に、質問を待つあいだ映す枚（「質疑応答」「ご清聴ありがとうございました」）。
# 聞かれそうな質問に答える予備の枚は、中身があるので「本文」（結論の一文あり）
# 想定質問：発表の最後（質問待機のあと）に、聞かれそうな質問と回答案を1枚に2組ずつ載せる枚（構成案の「## 想定質問」の表から）
ROLES = ("表紙", "本文", "区切り", "目次", "確認問題", "解答", "参考文献", "謝辞", "質問待機", "想定質問")
NO_CONCLUSION_ROLES = tuple(r for r in ROLES if r != "本文")   # 結論の一文を置かない枚（組むときに帯も●も無い枚になる）


def _plan_table(text: str, kind: str):
    from check_memo import table_rows
    return table_rows(text, "話の順番") if kind == "memo" else table_rows(text, "構成")


def plan_roles(text: str, kind: str):
    """{スライド番号: 役割}。表に「役割」の列が無ければ None。"""
    rows = _plan_table(text, kind)
    if not rows:
        return None
    i = next((k for k, h in enumerate(rows[0]) if h.strip() == "役割"), None)
    if i is None:
        return None
    return {int(r[0]): (r[i].strip() if len(r) > i else "") for r in rows[1:] if r and r[0].strip().isdigit()}


def _conclusion_cells(rows):
    k = next((j for j, h in enumerate(rows[0]) if "青帯" in h or "結論" in h), None)
    if k is None:
        return None
    return {int(r[0]): (r[k].strip() if len(r) > k else "") for r in rows[1:] if r and r[0].strip().isdigit()}


EMPTY = ("", "—", "-", "－", "なし")


def check_roles(text: str, kind: str, where: str):
    """[(印, 項目, 説明)]：役割の列。列が無ければ None（呼ぶ側は、題の語で見分ける前の確認に戻す）。
    ✘：一覧に無い役割・役割が空／本文なのに結論の列が空／本文でないのに結論がある。"""
    roles = plan_roles(text, kind)
    if roles is None:
        return None
    rows = _plan_table(text, kind)
    cons = _conclusion_cells(rows) or {}
    res = []
    bad = [(n, r) for n, r in roles.items() if r not in ROLES]
    if bad:
        res.append(("✘", "役割", "一覧に無い役割：" + "・".join(f"[{n}]「{r or '空'}」" for n, r in bad[:8])
                    + f"（{'・'.join(ROLES)} から選ぶ）"))
    nocon = [n for n, r in roles.items() if r == "本文" and cons.get(n, "") in EMPTY]
    if nocon:
        res.append(("✘", "結論の一文", f"役割が本文なのに「青帯（結論）」が空の枚：{'・'.join(map(str, nocon))}。持ち帰ってほしい一文を書く。"
                    "言い切れない枚（目的・手順など）は、その枚の要約の一文"))
    extra = [n for n, r in roles.items() if r in NO_CONCLUSION_ROLES and cons.get(n, "") not in EMPTY]
    if extra:
        res.append(("✘", "役割と結論", f"役割が本文でないのに結論がある枚：{'・'.join(f'[{n}] {roles[n]}' for n in extra)}。"
                    "結論を言う枚なら役割を本文に、そうでなければ結論の列を「—」に"))
    if not res:
        n_body = sum(r == "本文" for r in roles.values())
        others = sorted({r for r in roles.values() if r != "本文"}, key=ROLES.index)
        res.append(("✔", "役割", f"本文 {n_body}枚すべてに結論の一文、ほかは {'・'.join(others) or 'なし'}"))
    return res


QUIZ_TOTAL = 6        # 講座の1回の確認問題の数（固定）
QUIZ_PER_SLIDE = 3    # 1枚に載せる問題の数（固定）。確認問題 2枚・解答 2枚になる
QUIZ_SLIDES = QUIZ_TOTAL // QUIZ_PER_SLIDE
QUIZ_ID = re.compile(r"^\s*(?:\{b:)?(\d+-\d+)")


def quiz_ids(lines):
    """行のリスト → 問題番号（「1-1」の形。行の頭にあるものだけ）のリスト。"""
    return [m.group(1) for t in lines if (m := QUIZ_ID.match(t))]


def check_quiz_plan(text: str, kind: str = "memo"):
    """[(印, 項目, 説明)]：講座の設計メモの確認問題が「1枚に3問・合計6問」（確認問題2枚・解答2枚）か。
    Codex の試作は、6問を1問ずつ6枚に分け、表の1行に「12〜17」とまとめて書いていた。"""
    rows = _plan_table(text, kind)
    res = []
    if rows:
        merged = [r[0].strip() for r in rows[1:] if r and r[0].strip() and not r[0].strip().isdigit() and re.search(r"\d", r[0])]
        if merged:
            res.append(("✘", "表の行", f"番号が1つでない行：{'・'.join(merged)}。1行＝スライド1枚で書く（確認問題・解答も1枚ずつ行に）"))
    roles = plan_roles(text, kind) or {}
    nq = sum(r == "確認問題" for r in roles.values())
    na = sum(r == "解答" for r in roles.values())
    if (nq, na) != (QUIZ_SLIDES, QUIZ_SLIDES):
        res.append(("✘", "確認問題の枚数", f"確認問題 {nq}枚・解答 {na}枚。確認問題は {QUIZ_TOTAL}問を {QUIZ_PER_SLIDE}問ずつ、"
                    f"確認問題 {QUIZ_SLIDES}枚（N-1〜N-3・N-4〜N-6）と解答 {QUIZ_SLIDES}枚にする"))
    sec = re.search(r"^##\s*6\.[^\n]*\n(.*?)(?=^##\s|\Z)", text, re.S | re.M)
    if sec:
        body = sec.group(1)
        q = re.search(r"^###\s*問題\s*\n(.*?)(?=^###|\Z)", body, re.S | re.M)
        a = re.search(r"^###\s*解答\s*\n(.*?)(?=^###|\Z)", body, re.S | re.M)
        nqs = len(set(quiz_ids(q.group(1).splitlines()))) if q else 0
        nas = len(set(quiz_ids(a.group(1).splitlines()))) if a else 0
        if (nqs, nas) != (QUIZ_TOTAL, QUIZ_TOTAL):
            res.append(("✘", "確認問題の数", f"6節の問題 {nqs}問・解答 {nas}問。ちょうど {QUIZ_TOTAL}問（N-1〜N-{QUIZ_TOTAL}）と、その解答を書く"))
    if not res:
        res.append(("✔", "確認問題", f"{QUIZ_TOTAL}問を {QUIZ_PER_SLIDE}問ずつ、確認問題 {QUIZ_SLIDES}枚・解答 {QUIZ_SLIDES}枚"))
    res += quiz_links(text, kind)
    return res


QUIZ_Q_TAG = re.compile(r"〔\s*ゴール\s*(\d+)\s*[・、,]\s*(\d+)\s*枚目?\s*〕")
QUIZ_A_TAG = re.compile(r"〔\s*要素\s*[：:]\s*([^〕]+)〕")


QA_TOTAL = 4        # 発表の想定質問の数（固定）
QA_PER_SLIDE = 2    # 1枚に載せる組の数。想定質問の枚は 2枚


def expected_qa(text: str):
    """構成案の「## 想定質問」の表 → [(番号, 質問, 回答の要点, 戻る枚 int|None)]。表が無ければ None。"""
    from check_memo import table_rows
    rows = table_rows(text, "想定質問")
    if not rows:
        return None
    head = rows[0]

    def at(r, key, default):
        k = next((i for i, h in enumerate(head) if key in h), default)
        return r[k].strip() if k is not None and k < len(r) else ""
    out = []
    for r in rows[1:]:
        if not r or not any(c.strip() for c in r):
            continue
        back = re.search(r"\d+", at(r, "戻る", None))
        out.append((at(r, "番号", 0) or f"Q{len(out) + 1}", at(r, "質問", 1), at(r, "回答", 2), int(back.group(0)) if back else None))
    return out


def check_expected_qa(text: str, kind: str = "outline"):
    """[(印, 項目, 説明)]：発表の構成案の想定質問（4問、1枚に2組で2枚、各問に戻る枚）。講座の設計メモには当てない（確認問題がある）。"""
    if kind != "outline":
        return []
    items = expected_qa(text)
    roles = plan_roles(text, kind) or {}
    n_sl = sum(r == "想定質問" for r in roles.values())
    if items is None and not n_sl:
        return [("△", "想定質問", f"「## 想定質問」の表が無い。発表のあと聞かれそうな質問を {QA_TOTAL}問（番号｜質問｜回答の要点｜戻る枚）、"
                 f"表の最後に役割「想定質問」の行を {QA_TOTAL // QA_PER_SLIDE}枚（1枚に {QA_PER_SLIDE}組）")]
    bad = []
    if len(items or []) != QA_TOTAL:
        bad.append(f"質問が {len(items or [])}問（{QA_TOTAL}問にする）")
    if n_sl != QA_TOTAL // QA_PER_SLIDE:
        bad.append(f"役割「想定質問」の枚が {n_sl}枚（{QA_TOTAL // QA_PER_SLIDE}枚。1枚に {QA_PER_SLIDE}組）")
    body = {n for n, r in roles.items() if r == "本文"}
    noback = [k for k, _, _, b in (items or []) if b is None or (body and b not in body)]
    if noback:
        bad.append(f"戻る枚が無いか、本文の枚でない：{'・'.join(noback)}（答えるときに戻ると説明しやすい本文の枚の番号）")
    noans = [k for k, _, a, _ in (items or []) if not a]
    if noans:
        bad.append(f"回答の要点が空：{'・'.join(noans)}")
    if bad:
        return [("△", "想定質問", "。".join(bad))]
    return [("✔", "想定質問", f"{QA_TOTAL}問を {QA_PER_SLIDE}組ずつ {n_sl}枚、どれにも回答の要点と戻る枚")]


def quiz_items(text: str):
    """{問題番号: (問題の文, ゴール, 根拠の枚, 解答の文, [要素])}（設計メモ 6節）。"""
    sec = re.search(r"^##\s*6\..*?$(.*?)(?=^##\s|\Z)", text, re.S | re.M)
    if not sec:
        return {}
    q = re.search(r"^###\s*問題\s*\n(.*?)(?=^###|\Z)", sec.group(1), re.S | re.M)
    a = re.search(r"^###\s*解答\s*\n(.*?)(?=^###|\Z)", sec.group(1), re.S | re.M)
    out = {}
    for line in (q.group(1).splitlines() if q else []):
        m = re.match(r"^\s*(\d+-\d+)[.．]?\s*(.+)$", line)
        if m:
            t = QUIZ_Q_TAG.search(m.group(2))
            out[m.group(1)] = [m.group(2), int(t.group(1)) if t else None, int(t.group(2)) if t else None, "", []]
    for line in (a.group(1).splitlines() if a else []):
        m = re.match(r"^\s*(\d+-\d+)[.．]?\s*(.+)$", line)
        if m and m.group(1) in out:
            t = QUIZ_A_TAG.search(m.group(2))
            out[m.group(1)][3] = m.group(2)
            out[m.group(1)][4] = [x.strip() for x in re.split(r"[／/]", t.group(1)) if x.strip()] if t else []
    return {k: tuple(v) for k, v in out.items()}


def quiz_links(text: str, kind: str = "memo"):
    """[(印, 項目, 説明)]：問題ごとに確かめるゴールと根拠の枚〔ゴールN・M枚目〕、解答に入れる要素〔要素：…／…〕（2つ以上）があるか。
    ゴールのどれかに問題が無いときも △。書き手（軽いモデル）が、解答の原稿でどの枚に戻ればよいか、何を削ってはいけないかが分かる。"""
    items = quiz_items(text)
    if not items:
        return []
    goals = len(re.findall(r"^\s*\d+\.\s+\S", (re.search(r"言えるようになること[^\n]*\n((?:\s+\d+\..*\n?)+)", text) or [None, ""])[1], re.M))
    roles = plan_roles(text, kind) or {}
    body = {n for n, r in roles.items() if r == "本文"}
    notag = [k for k, v in items.items() if v[1] is None]
    badslide = [k for k, v in items.items() if v[2] is not None and body and v[2] not in body]
    fewel = [k for k, v in items.items() if len(v[4]) < 2]
    missing_goal = [g for g in range(1, goals + 1) if not any(v[1] == g for v in items.values())] if goals else []
    notes = []
    if notag:
        notes.append(f"問題に〔ゴールN・M枚目〕が無い：{'・'.join(notag)}")
    if badslide:
        notes.append(f"根拠の枚が本文の枚でない：{'・'.join(badslide)}")
    if fewel:
        notes.append(f"解答に〔要素：…／…〕（2つ以上）が無い：{'・'.join(fewel)}")
    if missing_goal:
        notes.append(f"問題の無いゴール：{'・'.join(map(str, missing_goal))}")
    if notes:
        return [("△", "確認問題のひもづけ", "。".join(notes) + "（6節。問題の後ろに〔ゴール1・2枚目〕、解答の後ろに〔要素：…／…〕。"
                 "カードが、解答の原稿で戻る枚と、削ってはいけない要素を書き手に渡す）")]
    return [("✔", "確認問題のひもづけ", f"{len(items)}問すべてにゴール・根拠の枚・解答の要素")]


def role_mismatches(prs, roles: dict):
    """[(番号, 説明)]：構成案の役割と、できたスライドの食い違い（渡す前の確認）。
    本文なのに結論の一文が無い（漸進表示の途中の枚は除く）／本文でないのに結論がある／表紙が表紙のレイアウトでない／区切りが区切りでない。"""
    import zemi
    out = []
    slides = list(prs.slides)
    cover = slides[0].slide_layout if slides else None
    for i, sl in enumerate(slides, 1):
        r = roles.get(i)
        if not r or r not in ROLES:
            continue
        names = {sh.name for sh in sl.shapes}
        con = zemi.has_conclusion(sl, prs.slide_height)
        if r == "表紙":
            if sl.slide_layout != cover:
                out.append((i, "役割は表紙なのに、表紙のレイアウトでない（deck.title_slide で組む）"))
        elif r == "区切り":
            if "区切りの地" not in names:
                out.append((i, "役割は区切りなのに、区切りの枚でない（deck.section で組む）"))
        elif r == "本文":
            if not con and "漸進表示" not in names:
                out.append((i, "役割は本文なのに、結論の一文が無い（summary= に入れる）"))
        elif con:
            out.append((i, f"役割は{r}なのに、結論の一文がある（summary を外す。外すと帯も●も無い枚になる）"))
    return out


def mismatches(prs, plan: dict, skip=()):
    """[(番号, 説明)]：構成案の本文の形が、スライドで使われていない枚（部品の名前と「⇒」の行で見る。「箇条」は見ない）。"""
    out = []
    for i, sl in enumerate(prs.slides, 1):
        if i in skip or i not in plan:
            continue
        want = {k for k in plan[i] if isinstance(k, str) and k != "箇条"}
        miss = want - detect_forms(sl)
        if miss:
            out.append((i, "案は" + "・".join(sorted(miss, key=FORM_KEYS.index)) + "なのに、その部品が無い"))
    return out
