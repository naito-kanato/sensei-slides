"""講座の設計メモの確認：スライドを作る前（構成を決めた段階）に、設計メモ（memo.md）を機械的に確かめる（references/course.md 手順4）。

    python <skill>/scripts/check_memo.py _work/<講座フォルダ名>_<回の番号>/memo.md

確かめること（✘ が1つでもあれば終了コード 1。△ は終了コードに入れない）
  1. 本文の枚数：2節「話の順番」の表で、表紙・確認問題・解答を除いた行（＝本文のスライド）が、既定の10〜15枚に入っているか。
     外れたら △。話を足す（前提の説明・具体例・数値の例・つまずきやすい所・前後の回とのつながり）か回をまとめる（多ければ回を分ける）。
     テーマが狭いなど、どうしても外れるなら2節に「枚数の理由：…」と書く。書いてあれば ✔
  2. 出典：3節「事実と出典」の表で、確認が「○」の行の出典に、資料を特定できる手がかり
     （URL・DOI・「題名」・著者と年・条番号・頁や図の番号）がある。「厚生労働省」「薬機法」だけ、のような行は ✘
     （渡す前の確認 check_done.py も同じことを見る）
  3. 前提と丁寧さ：1節に必須の「聞き手のテーマへの詳しさ：…」（初学者・多少知っている／かなり知っている）と「聞き手の前提知識（知っている＝…／知らない＝…）」。
     無ければ ✘。丁寧さは書いていなければ詳しさから（初学者・多少知っている 0・かなり知っている 1）
  4. 推論距離の手当て：設計メモのレビューの結果（memo.md と同じフォルダの memo_review.md）の
     穴の行（「[番号] 「A ⇒ B」｜種類｜要否｜…」）で、「要」の用語があるスライドと、丁寧さを超える「要」があるスライドが、
     「## 9. 引っかかりへの手当て」に [番号] で全部載っている。レビューの前（memo_review.md が無い）なら数えない
     （ゼミの構成案と同じ照合。check_outline.py の reasoning）
  5. 話の筋・前の枚から：1節の筋の表（状況・複雑化・問い・答え）と、2節の表の「前の枚から」（そして・しかし・だから）。story.py
"""
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_done import vague_sources  # noqa: E402

BODY_MIN, BODY_MAX = 10, 15                  # 講座の1回の本文の枚数（references/course.md の既定）


def table_rows(text: str, section: str):
    """「## <番号>. <section>」の節にある最初の表を [ヘッダ, 行, ...]（セルのリスト）で返す。無ければ None。"""
    m = re.search(rf"^##\s*\d*\.?\s*{section}.*?$(.*?)(?=^##\s|\Z)", text, re.S | re.M)
    if not m:
        return None
    rows = [l for l in m.group(1).splitlines() if l.strip().startswith("|")]
    if len(rows) < 2:
        return None
    cells = [[c.strip() for c in l.strip().strip("|").split("|")] for l in rows]
    return [cells[0]] + cells[2:]            # 区切り行（|---|）を除く


def body_rows(text: str):
    """2節の表から本文のスライドの見出しのリスト。表が無ければ None。"""
    rows = table_rows(text, "話の順番")
    if rows is None:
        return None
    head = rows[0]
    i = next((k for k, h in enumerate(head) if "見出し" in h), 1)
    out = []
    for r in rows[1:]:
        h = r[i] if len(r) > i else ""
        if h and not not_body_heading(h):
            out.append(h)
    return out


def not_body_heading(h: str) -> bool:
    """表紙・確認問題・解答（・区切り）の行の●見出しか。日本語でない見出し（"Review Questions (1-1 to 1-3)"・"Answers"）も見る。
    英語の試しで、英語の確認問題の見出しを本文に数え、設計の担当が見出しを日本語に戻して逃げた。"""
    import language as LG
    return (any(w in h for w in ("表紙", "問題", "解答")) or LG.is_qa_heading(h) or bool(re.match(r"\s*(title|cover)\b", h, re.I))
            or h.strip() in ("まとめ", "Summary"))   # まとめの枚（役割「まとめ」）は本文の枚数に数えない


SCRIPT_MIN, SCRIPT_MAX = 280, 420   # 標準の回の script.md：本文の枚の読み上げの字数（目安は300〜400字。少しの外れは知らせない）
SCRIPT_MEMO = re.compile(r"私の概算|概算です|開いていません|開いていない|開けていない|原資料|検索で|検索した|確かめていません|確かめられていません|未確認です|抜粋で")   # 原稿に残った作業の言い方
SCRIPT_POS = re.compile(r"右端|左端|一番上|一番下|いちばん上|いちばん下|[上下左右]から[1-9１-９一二三四五]番目")   # 図の中の位置で指す言い方
RECAP_MIN_BODY = 6   # 本文がこの枚数以上の講座は、最後にまとめの枚（輪読の型は、最後の拍が節のまとめなので要らない）


def recap_check(text: str, srows, col):
    """講座の最後のまとめの枚（役割「まとめ」）。本文6枚以上で無ければ ✘。睡眠の比べで、まとめの枚が無いと採点者2人が減点した
    （部品 s.recap と scaffold の組みはあったが、標準の回の設計の担当に知らせる所も検査も無く、作られなかった）。"""
    import story
    role = lambda r: col(r, "役割") or "本文"   # noqa: E731
    body = [r["#"] for r in srows if role(r) == "本文"]
    name, _ = story.arc_of(text)
    if len(body) < RECAP_MIN_BODY or (name or "").startswith("輪読"):
        return []
    rec = [r["#"] for r in srows if role(r) == "まとめ"]
    if not rec:
        return [("✘", "まとめの枚", f"本文 {len(body)} 枚の講座に、最後のまとめの枚が無い。2節の表の最後の本文の枚のあと（確認問題の前）に、"
                 f"●見出し「まとめ」・役割「まとめ」の行を1つ足す（形は話の型の既定「{story.recap_kind(text)}」。青帯は筋の表の「答え」の一文。"
                 "新しい事実は入れない。references/story.md 3節）。scaffold が s.recap で組む")]
    after = [n for n in body if n > rec[0]]
    if after:
        return [("✘", "まとめの枚", f"まとめの枚（{rec[0]}枚目）のあとに本文の枚がある（{after[0]}枚目）。まとめは最後の本文の枚のあと・確認問題の前に")]
    r = next(x for x in srows if x["#"] == rec[0])
    band = re.sub(r"\s", "", col(r, "青帯（結論）", "青帯") or "")
    kind_ = story.recap_kind(text)
    pts = [p.strip() for p in re.split(r"\s*/\s*", col(r, "本文の要点") or "") if p.strip() and p.strip() not in ("—", "-")]
    bad = []
    if len(band) > 36:
        bad.append(f"青帯が {len(band)} 字（36字まで。答えの一文を縮める）")
    if kind_ in ("前と後", "選び方"):
        pairs = [p for p in pts if re.search(r"→|⇒", p)]
        if not 2 <= len(pairs) <= 3:
            bad.append(f"本文の要点に「{'聞く前の見方 → 今わかったこと' if kind_ == '前と後' else 'こんなとき → 選ぶもの'}」の対を「 / 」で区切って2〜3組（今 {len(pairs)} 組）")
        long_ = [s for p in pairs for s in re.split(r"\s*(?:→|⇒)\s*", p) if len(re.sub(r"\s", "", s)) > 14]
        if long_:
            bad.append("対の片側は14字まで（箱の中で1行）：" + "・".join(f"「{s[:16]}」" for s in long_[:3]))
    if bad:
        return [("✘", "まとめの枚", f"{rec[0]}枚目（形「{kind_}」）：" + "。".join(bad))]
    return [("✔", "まとめの枚", f"{rec[0]}枚目（形「{kind_}」）")]


CONCRETE = re.compile(r"[0-9０-９]|「[^」]+」|例[：:）)]|たとえば|例えば")
CONCRETE_MIN = 0.5    # 本文のスライドのうち、具体的なもの（数値・具体例）がある枚の割合の下限


def concreteness(rows):
    """2節の表で、本文の各行（図で見せるもの・本文の要点・青帯）に数値か具体例（「…」・例：）があるか。半分に満たなければ △。
    以前の試験で、本文が「〜を確認」「〜を考慮」の言い換えばかりで、数値の出てくる枚が11枚中2枚だった。"""
    head = rows[0]
    i_h = next((k for k, h in enumerate(head) if "見出し" in h), 1)
    cols = [k for k, h in enumerate(head) if any(w in h for w in ("図で見せる", "本文", "青帯"))]
    body, plain = 0, []
    for r in rows[1:]:
        h = r[i_h] if len(r) > i_h else ""
        if not h or not_body_heading(h):
            continue
        body += 1
        t = re.sub(r"第[0-9０-９]+回", "", " ".join(r[k] for k in cols if k < len(r)))   # 「第1回の〜」は数値に数えない
        if not CONCRETE.search(t):
            plain.append(r[0])
    if not body:
        return ("✔", "中身の具体さ", "本文のスライドが無い")
    n = body - len(plain)
    if n >= CONCRETE_MIN * body:
        return ("✔", "中身の具体さ", f"本文 {body}枚のうち {n}枚に数値か具体例がある")
    return ("△", "中身の具体さ", f"本文 {body}枚のうち、数値か具体例（「…」・例：）がある枚が {n}枚（半分以上に）。無い枚：{'・'.join(plain)}。"
            "「〜を確認」「〜に注意」の言い換えで終わらせず、各枚に、出典つきの数値・実際の場面の例・よくある間違いの例を1つ足す")


POINTS_MIN = 3        # 本文の要点の数の下限（SKILL.md の書き方は 3〜4個）
THIN_ROWS_MAX = 0.5   # 要点が POINTS_MIN に満たない本文の行の割合の上限（見本：講座 1/10・ゼミ 0/12、Codex の試作 7/10）


def point_count(cell: str) -> int:
    """本文の要点のセルの項目の数（／ / ； ・ 改行で分ける）。"""
    cell = re.sub(r"<br\s*/?>", "／", cell or "")
    return len([p for p in re.split(r"\s*(?:／|/|・|；|;)\s*", cell) if p.strip(" ★")])


TAG = re.compile(r"〔[^〕]+〕")
NUMERIC = re.compile(r"[0-9０-９]")


def untagged_numbers(rows, what="設計メモ2節"):
    """本文の要点のうち、数値があるのに出どころ〔…〕が無い項目のある枚 → △。書き手（軽いモデル）が材料を探さずに書けるように、
    構成を決めるときに「どこから引くか」まで決めておく（論文なら〔II. Observation〕〔Fig. 2〕〔要旨〕、講座なら〔事実3〕＝3節の表の3行目、
    自分の計算なら〔発表者の概算〕、講座は〔講師の概算〕）。"""
    head = [h.strip() for h in rows[0]]
    k = next((i for i, h in enumerate(head) if "本文の要点" in h), None)
    kr = next((i for i, h in enumerate(head) if "役割" in h), None)
    if k is None:
        return None
    bad, n_num = [], 0
    for r in rows[1:]:
        if not r or not r[0].strip().isdigit() or (kr is not None and kr < len(r) and r[kr].strip() not in ("", "本文")):
            continue
        items = [x for x in re.split(r"\s*(?:／|/|；|;)\s*", r[k] if k < len(r) else "") if x.strip()]
        nums = [x for x in items if NUMERIC.search(TAG.sub("", x))]
        n_num += len(nums)
        if any(not TAG.search(x) for x in nums):
            bad.append(r[0].strip())
    if not n_num:
        return None
    if bad:
        return ("△", "要点の出どころ", f"数値のある要点に出どころ〔…〕が無い枚：{'・'.join(bad)}。要点の後ろに〔II. Observation〕〔Fig. 2〕〔要旨〕"
                f"（講座は〔事実3〕＝3節の表の行）、自分の計算なら〔発表者の概算〕（講座は〔講師の概算〕）と書く（{what}。カードが、その所を書き手に渡す）")
    return ("✔", "要点の出どころ", f"数値のある要点 {n_num}個すべてに出どころ")


def thin_points(rows, what="設計メモ2節"):
    """本文の行のうち、要点が POINTS_MIN 個に満たない行が半分を超えたら ✘（スライドの中身が薄くなる。Codex の試作は要点2個の行ばかりで、
    スライドの本文も中身の無い字数合わせの行で埋まった）。役割の列があれば本文の行だけを見る。"""
    head = [h.strip() for h in rows[0]]
    k = next((i for i, h in enumerate(head) if "本文の要点" in h), None)
    if k is None:
        return None
    kr = next((i for i, h in enumerate(head) if "役割" in h), None)
    kh = next((i for i, h in enumerate(head) if "見出し" in h), 1)
    body, thin = 0, []
    for r in rows[1:]:
        if not r or not r[0].strip().isdigit():
            continue
        role = r[kr].strip() if kr is not None and kr < len(r) else ""
        h = r[kh] if kh < len(r) else ""
        if (role and role != "本文") or (not role and (not_body_heading(h) or "区切り" in h)):
            continue
        body += 1
        if point_count(r[k] if k < len(r) else "") < POINTS_MIN:
            thin.append(r[0].strip())
    if not body:
        return None
    if len(thin) > THIN_ROWS_MAX * body:
        return ("✘", "本文の要点の数", f"本文 {body}枚のうち {len(thin)}枚で、本文の要点が {POINTS_MIN}個に満たない（{'・'.join(thin)}）。"
                f"{what}の「本文の要点」を枚ごとに 3〜4個にする：結論の根拠・数値・具体例・よくある間違い。言い換えや「〜の見方」のような中身の無い要点は数えない")
    return ("✔", "本文の要点の数", f"本文 {body}枚のうち、要点が {POINTS_MIN}個に満たない枚は {len(thin)}枚")


# 事実の行の限定（言い切りを弱める言葉）。「または」は並べるときにも使うので、事実の側では見ない（枚の側で残っていれば通す）
# 英語などの語も見る（英語の試しで、設計の担当が英語の要点に「(ことがある)」と日本語の印を付けて通していた）
HEDGE_FACT = re.compile(r"とされ|考慮|望ましい|努力義務|場合が?ある|ことがある|可能性|一部|原則"
                        r"|(?i:\b(?:may|might|can|could|often|usually|typically|generally|some|likely|is considered|are considered"
                        r"|is thought|are thought|in principle|recommended|should)\b)")
HEDGE = re.compile(HEDGE_FACT.pattern + r"|または|あるいは|いずれか|選択肢|例[：:）)]|の例|目安|など"
                   r"|(?i:\b(?:or|either|e\.g\.|for example|such as|about|around|approximately|up to|at least|roughly)\b|~|≈)")


def hedged_facts(text: str, rows):
    """事実の行（3節）の限定（または・一部・〜とされる・考慮・望ましい など）が、その〔事実N〕を使う枚の青帯・本文の要点で
    外れていないか（その枚の文に限定の言葉が1つも無ければ △）。試しの回で、「〜とされる」の事実が、設計メモで言い切り、スライドの表で「必須」と強まった。"""
    try:
        import facts
        _, fh, frows = facts.memo_facts(text)
    except (SystemExit, Exception):
        return None
    head = [h.strip() for h in rows[0]]
    cols = [i for i, h in enumerate(head) if "青帯" in h or "結論" in h or "本文の要点" in h]
    if not cols:
        return None
    hits = []
    for r in rows[1:]:
        if not r or not r[0].strip().isdigit():
            continue
        line = " ".join(r)
        said = " ".join(r[i] for i in cols if i < len(r))
        for k in sorted({int(x) for x in re.findall(r"事実\s*(\d+)", line)}):
            if not 1 <= k <= len(frows):
                continue
            words = sorted(set(HEDGE_FACT.findall(" ".join(frows[k - 1][:2]))))
            if words and not HEDGE.search(said):
                hits.append(f"[{r[0].strip()}] 事実{k}の「{'・'.join(words[:2])}」")
    if not hits:
        return None
    return ("△", "事実の限定", "事実の行の限定が、その事実を使う枚の青帯・本文の要点で外れている：" + "、".join(hits[:6])
            + ("…" if len(hits) > 6 else "") + "。限定を残す（「〜とされる」を言い切りに、「一部」を全体に、「考慮する」を「必須」にしない）")


WHEN = re.compile(r"\d{4}\s*年|年度|\d+\s*月|時点|現在|\d{4}[-/.]\d|\b(?:19|20)\d{2}\b|(?i:\bas of\b)")   # 英語の年・as of も
DENOM = re.compile(r"分母|÷|／|うち|中\s*\d|中の|に対し|あたり|当たり|全国|全体|のなかで|に占める"
                   r"|(?i:\b(?:out of|of all|per|among|share of)\b)")


def data_slides(rows, what="設計メモ2節"):
    """データN を使う枚（図の案か本文の要点で指す）の青帯・本文の要点に、時点（年・年度・月・時点）が無い、
    割合（%・割）なのに分母（〜のうち・全国の・÷）が無い → △。試しの回で、時点の違う値が1枚に混ざり（7年前の平均と今年の値）、
    よかった回は「分子：〇〇の数（各年3月末）／分母：全国の〇〇の数（各前年3月末）」まで書いていた。"""
    head = [h.strip() for h in rows[0]]
    cols = [i for i, h in enumerate(head) if "青帯" in h or "結論" in h or "本文の要点" in h]
    if not cols:
        return None
    no_when, no_denom = [], []
    for r in rows[1:]:
        if not r or not r[0].strip().isdigit() or not re.search(r"データ\s*\d", " ".join(r)):
            continue
        said = " ".join(r[i] for i in cols if i < len(r))
        if not WHEN.search(said):
            no_when.append(f"[{r[0].strip()}]")
        if re.search(r"%|％|割", said) and not DENOM.search(said):
            no_denom.append(f"[{r[0].strip()}]")
    notes = []
    if no_when:
        notes.append("時点が無い：" + "・".join(no_when[:8]) + "（いつの値か。「〇年〇月末」「〇年度」）")
    if no_denom:
        notes.append("割合なのに分母が無い：" + "・".join(no_denom[:8]) + "（何のうちの割合か。「全国の〇〇のうち」「÷ 全体の数」）")
    if not notes:
        return None
    return ("△", "データの枚の時点と分母", f"{what}でデータを使う枚の青帯・本文の要点に、" + "。".join(notes) + "。1枚に違う時点の値を混ぜるなら、それぞれに時点を書く")


FULLWIDTH = re.compile(r"[０-９Ａ-Ｚａ-ｚ．％]+")


def fullwidth_alnum(rows, what="設計メモ2節"):
    """青帯（結論）と本文の要点にある全角の英数字（「第２版」「Ｖｅｒ２．０」）を △。スライドにそのまま出て、半角の数字と混ざる。"""
    head = [h.strip() for h in rows[0]]
    cols = [i for i, h in enumerate(head) if "青帯" in h or "結論" in h or "本文の要点" in h]
    if not cols:
        return None
    hits = []
    for r in rows[1:]:
        if not r or not r[0].strip().isdigit():
            continue
        found = sorted({m for i in cols if i < len(r) for m in FULLWIDTH.findall(r[i])})
        if found:
            hits.append(f"[{r[0].strip()}] {'・'.join(found[:3])}")
    if not hits:
        return None
    return ("△", "全角の英数字", f"{what}の青帯・本文の要点に全角の英数字：{'、'.join(hits[:6])}{'…' if len(hits) > 6 else ''}。"
            "半角に直す（「第2版」「Ver.2.0」「50項目」）。スライドにそのまま出て、半角の数字と混ざる")


MEMO_REVIEW = "memo_review.md"


def data_rows(text: str, work: Path, body_no, kind: str = "memo") -> list:
    """3b節「データ」：組の書き方、図の案が指すデータNがあるか、データを描く図があるか。kind="outline" は発表の構成案（3b節は任意）。"""
    import data
    import figplan
    import structures
    if data.section(text) is None:
        if data.files(work):
            return [("✘", "データ", "data_N.md があるのに3b節が無い（python <skill>/scripts/data.py merge <work>）")]
        if kind == "outline":   # 発表も、探したかどうかは必ず残す（組が無ければ「見つからなかった：理由」でよい）
            return [("✘", "データ", "data_1.md が無い。資料の表・図から比べられる数字の組を2組まで書く。無ければ「## 見つからなかった：理由」と"
                     "「- 調べたこと：」。書いたら python <skill>/scripts/data.py merge <work>")]
        return [("・", "データ", "3b節が無い（講座は、設計の前に数字を探す担当が比べられる数字の組を探す。references/course.md 手順4⓪）")]
    ds = data.datasets(text)
    nf = data.memo_not_found(text)
    res = []
    texts = [f.read_text(encoding="utf-8") for f in data.files(work)]
    n_sets, n_nf = sum(len(data.parse(t)) for t in texts), sum(len(data.not_found(t)) for t in texts)
    if texts and (n_sets, n_nf) != (len(ds), len(nf)):   # 雛形の3b節の見出しだけ残っている・data_N.md を書き足した あとに merge していない
        res.append(("✘", "データ", f"data_N.md（組 {n_sets}・見つからなかった {n_nf}）と3b節（組 {len(ds)}・見つからなかった {len(nf)}）がずれている。"
                    "python <skill>/scripts/data.py merge <work> で入れ直す"))
    bad = [f"データ{n}：{'・'.join(p)}" for n, d in ds.items() if (p := data.problems(d))]
    if bad:
        res.append(("✘", "データ", "；".join(bad[:4])))
    cells = {n: " ".join(v) for n, v in figplan.fig_cells(text, kind).items()}   # 構成の表と図の案の表の両方
    used = {n for c in cells.values() for n in data.refs(c)}
    missing = sorted(used - set(ds))
    if missing:
        res.append(("✘", "データ", f"図の案が指すデータが3b節に無い：{'・'.join(f'データ{n}' for n in missing)}"))
    if not ds:
        res.append(("・", "データ", f"比べられる数字の組は見つからなかった（{'／'.join(nf)}）。しかし はデータ無しで組む" if nf else "3b節に組が無い"))
    elif not used and not re.search(r"データを使わない理由[：:]\s*\S", text):
        res.append(("✘", "データ", "3b節にデータがあるのに、描く図が無い。強い組なら、図の案を「目的：種類：データN」（棒グラフ・折れ線・帯など）にして見せる。"
                    "弱い組（別の読み方で驚きが消える）なら使わずに、1節に「データを使わない理由：…」と書く"))
    elif not bad and not missing:
        res.append(("✔", "データ", f"{len(ds)}組。図で使うもの：{'・'.join(f'データ{n}' for n in sorted(used)) or 'なし'}"))
    return res


def fact_count(text: str):
    """3節「事実と出典」の表の行の数（空の行は数えない）。表が無ければ None。"""
    m = re.search(r"^##\s*3[.．]?\s*事実と出典.*?(?=^##\s)", text + "\n## ", re.M | re.S)
    if not m:
        return None
    rows = [l for l in m.group(0).splitlines() if l.startswith("|") and not re.match(r"^\|\s*-", l)]
    rows = rows[1:]   # 見出しの行
    return sum(1 for l in rows if any(c.strip() for c in l.strip("|").split("|")))


LATIN_NAME = re.compile(r"(?<![A-Za-z0-9])(?=[A-Za-z0-9.-]*[A-Za-z]{2})[A-Za-z][A-Za-z0-9.-]*[A-Za-z0-9]|[A-Za-z]+-?\d[\w.-]*")


def _heads_and_bands(text: str, kind: str):
    """話の順番・構成の表の本文の枚の (●見出し, 青帯) のリスト（記号・数字を外して比べやすく）。"""
    import structures
    rows = structures._plan_table(text, kind) or []
    if not rows:
        return []
    head = rows[0]
    i_h = next((k for k, h in enumerate(head) if "見出し" in h), None)
    i_b = next((k for k, h in enumerate(head) if "青帯" in h or "結論" in h), None)
    norm = lambda s: re.sub(r"[\s、。・,.「」（）()〔〕\[\]0-9０-９%％]", "", s or "")   # noqa: E731
    out = []
    for r in rows[1:]:
        if not (r and r[0].strip().isdigit()):
            continue
        h = norm(r[i_h]) if i_h is not None and len(r) > i_h else ""
        b = norm(r[i_b]) if i_b is not None and len(r) > i_b else ""
        if (h or b) and b not in ("—", "-", ""):
            out.append((h, b))
    return out


def example_copy(text: str, kind: str, path):
    """同梱の見本（examples/ の設計メモ・構成案）の写し：本文の枚の●見出しか青帯が、見本のどれかの枚とほぼ同じ
    （似ている度合い 0.8 以上）枚が3枚以上か本文の3割以上なら ✘。見本と同じテーマの依頼で、Antigravity の設計が
    見本の見出し・つなぎ・青帯をほぼそのまま写した。"""
    import difflib
    import os
    root = Path(__file__).resolve().parents[1]
    if "examples" in Path(path).resolve().parts or os.environ.get("SENSEI_SKIP_EXAMPLE_COPY"):   # テストは見本を写して使うので切る
        return []
    mine = _heads_and_bands(text, kind)
    if len(mine) < 4:
        return []
    sim = lambda a, b: difflib.SequenceMatcher(None, a, b).ratio()   # noqa: E731
    worst = (0, None)
    for ex in sorted((root / "examples").glob("*/_work/*/memo.md")) + sorted((root / "examples").glob("*/outline.md")):
        theirs = _heads_and_bands(ex.read_text(encoding="utf-8"), "memo" if ex.name == "memo.md" else "outline")
        same = sum(1 for h, b in mine if any((len(h) >= 4 and h2 and sim(h, h2) >= 0.8) or (len(b) >= 8 and b2 and sim(b, b2) >= 0.8)
                                             for h2, b2 in theirs))
        if same > worst[0]:
            worst = (same, ex)
    n, ex = worst
    if n >= 3 or (ex and n / len(mine) >= 0.3):
        name = ex.parent.name if ex.name == "memo.md" else ex.parent.name + "/outline.md"
        return [("✘", "見本の写し", f"本文 {len(mine)} 枚のうち {n} 枚の●見出しか青帯が、同梱の見本（{name}）とほぼ同じ。"
                 "見本は形（表の列・書き方）だけを見る。話の順番・見出し・青帯は、この依頼の聞き手・ゴール・集めた事実から組み直す")]
    return []


EVERYDAY_NAMES = ("PowerPoint", "Word", "Excel", "Google", "Windows", "Mac", "iPhone", "Android", "YouTube", "LINE", "ChatGPT", "Wikipedia", "PDF", "URL", "Web")   # 説明の要らない身近な名前


def term_order(text: str, rows, scaffold):
    """用語の初出（推論距離の網。スクリプトで安く見られる所だけ。深い監査は推論距離の担当・レビュー担当がする）：
    4節の用語が、本文の枚の青帯・要点に初めて出る枚で説明されているか（「語：」「語（」「語＝」が無く、あとの枚にあれば △）と、
    青帯・要点の英字の名前（3字以上か数字入り）が4節にも前提知識の「知っている」にも無い（△）。
    試しで、3枚目で「2048トークン」と使ってから4枚目でトークンを説明し、「BLOOM」は説明が無かった。"""
    sec4 = re.search(r"^##\s*4\..*?(?=^##\s|\Z)", text, re.S | re.M)
    gloss = sec4.group(0) if sec4 else ""
    known = re.search(r"知っている\s*[＝=]\s*([^／\n]*)", text)
    known = known.group(1) if known else ""
    terms = [t.strip() for t in re.findall(r"(?:^-\s*|、)\s*([^\s、（(：:]{2,12})（", gloss, re.M)]
    body = [(r["#"], scaffold.TAG.sub("", " / ".join(scaffold.col(r, *c) or "" for c in (("青帯（結論）", "青帯"), ("本文の要点",), ("図で見せるもの", "図")))))
            for r in rows if (scaffold.col(r, "役割") or "本文") == "本文"]
    late = []
    for t in terms:
        hits = [n for n, s in body if t in s]
        if len(hits) < 2:
            continue
        defs = [n for n, s in body if re.search(r"(?:^|[/／]\s*|[（(])★?" + re.escape(t) + r"\s*[：:＝=（(]", s)]   # 要点の頭の「語：…」「語（…」
        if defs and hits[0] not in defs and defs[0] > hits[0]:
            late.append(f"{t}（{hits[0]}枚目で使い、{defs[0]}枚目で説明）")
    names = []
    for n, s in body:
        for m in LATIN_NAME.findall(s):
            if len(m) >= 3 or any(c.isdigit() for c in m):
                if m not in gloss and m not in known and m not in EVERYDAY_NAMES and m not in [x for x, _ in names]:
                    names.append((m, n))
    out = []
    if late:
        out.append(("△", "用語の初出", "説明より前の枚で使っている：" + "・".join(late[:5]) + "（初めて出る枚で一言説明するか、言い方を変える。推論距離の担当も見る）"))
    if names:
        out.append(("△", "説明の無い英字の名前", "4節にも前提知識にも無い：" + "・".join(f"{m}（{n}枚目）" for m, n in names[:8])
                    + "（4節に一言の説明を足し、初めて出る枚でも言う。知っている側の名前なら前提知識に足す）"))
    return out


def check(memo: Path, require_review: bool = False):
    """[(✔/✘/△, 項目, 説明)] を返す。require_review＝レビュー結果が無ければ ✘（渡す前の確認）。"""
    text = memo.read_text(encoding="utf-8")
    res = []
    body = body_rows(text)
    if body is None:
        res.append(("✘", "本文の枚数", "2節「話の順番」の表が無い（assets/course/memo.md の形で書く）"))
    else:
        n = len(body)
        reason = re.search(r"枚数の理由[：:]\s*\S", text)
        if BODY_MIN <= n <= BODY_MAX:
            res.append(("✔", "本文の枚数", f"{n}枚（既定 {BODY_MIN}〜{BODY_MAX}枚）"))
        elif reason:
            res.append(("✔", "本文の枚数", f"{n}枚（既定 {BODY_MIN}〜{BODY_MAX}枚から外れるが、理由が書いてある）"))
        else:
            hint = "話を足す（前提・具体例・数値の例・つまずきやすい所・前後の回とのつながり）か、回をまとめる" if n < BODY_MIN else "回を分ける"
            res.append(("✘", "本文の枚数", f"{n}枚（既定 {BODY_MIN}〜{BODY_MAX}枚）。{hint}。どうしても外れるなら2節に「枚数の理由：…」を書く"))
    import figplan
    plan = figplan.plan_from_text(text, "memo")
    rows = table_rows(text, "話の順番") or []
    body_no = [int(r[0]) for r in rows[1:] if r and r[0].strip().isdigit() and r[1:2] and
               not not_body_heading(r[1])]
    if plan:
        mark, msg = figplan.flow_check(figplan.flow_count(plan, body_no), len(body_no), text, "設計メモ")
        res.append((mark or "✘", "流れ図の数", msg))
        nf = figplan.no_figure(plan, body_no)
        res.append(("✘" if nf else "✔", "図の無いスライド",
                    f"5節「図の案」が「なし」・無い本文のスライド：{'・'.join(map(str, nf))}。{figplan.NO_FIGURE_HINT}" if nf
                    else "本文のスライドすべてに図の案がある"))
    if rows:
        res.append(concreteness(rows))
        tp = thin_points(rows)
        if tp:
            res.append(tp)
        ut = untagged_numbers(rows)
        if ut:
            res.append(ut)
        for extra in (fullwidth_alnum(rows), hedged_facts(text, rows), data_slides(rows)):
            if extra:
                res.append(extra)
        import structures
        roles = structures.check_roles(text, "memo", "設計メモ2節")
        res += roles if roles is not None else [("✘", "役割", "設計メモ2節の" + f"表に「役割」の列が無い。枚ごとに {'・'.join(structures.ROLES)} から選んで書く（結論の一文を置くのは本文だけ）")]
        import structures
        res += structures.check_plan(text, "memo", body_no, "設計メモ2節", memo.parent)
        res += structures.check_quiz_plan(text, "memo")
        import story
        res += story.check(text, "memo", story.body_numbers(text, "memo"), "設計メモ2節")
    res += data_rows(text, memo.parent, body_no)
    nfacts = fact_count(text)
    if nfacts is not None and body_no and nfacts < len(body_no):
        res.append(("△", "事実の数", f"3節の事実の行が {nfacts} 行で、本文の {len(body_no)} 枚より少ない。"
                    "1枚に1つ以上、そのテーマの具体（数値・年・固有の名前・実際の例）を事実の行にして本文の要点に〔事実N〕で付ける。"
                    "一般論（見方・比べ方）だけの枚が続くと、どのテーマでも言える講座になる"))
    bad = vague_sources(memo)
    if bad is None:
        res.append(("✘", "出典", "3節「事実と出典」の表が無い"))
    elif bad:
        res.append(("✘", "出典", f"○ なのに資料を特定できない行が {len(bad)} 件（書名・URL・頁などを足すか、確認を × にする。裏取りした行は facts_N.md の同じ行も直す：memo.md だけ直すと facts.py merge で戻る）："
                    + " / ".join(f"「{a[:14]}」→{b[:20]}" for a, b in bad[:4])))
    else:
        res.append(("✔", "出典", "○ の行はすべて資料を特定できる"))
    try:
        import budget as _b
        res += design_content(text, _b.light(memo.parent))
    except Exception:
        pass
    try:   # PowerPoint の部品で組む図の案を、スクリプトが読める書き方か（読めないと、制作の担当が中身を考えて手で組む。
        # コミュニケーション講座の試しで、表の中身・判定の書き方が読めず、制作の担当が本文12枚を丸ごと書き直した）
        import scaffold
        _, _, srows, _ = scaffold.plan(memo.parent)
        many = []   # 1枚の文の塊（見出しの違う要点＋比較・前後・カード）が3つを超える枚。描画の検査は4つで ERROR
        for r in srows:
            if (scaffold.col(r, "役割") or "本文") != "本文":
                continue
            pts = scaffold.items_of(scaffold.col(r, "本文の要点"))
            heads = {p.partition("：")[0].strip("★ ") for p in pts if "：" in p and "→" not in p.partition("：")[0]}
            loose = sum(1 for p in pts if "：" not in p or "→" in p.partition("：")[0])   # 展開（A → B）・見出しの無い文は1つずつ
            fig = scaffold.col(r, "図で見せるもの", "図")
            pname = scaffold.part_name(fig)
            part = pname == "s.compare"   # 描画の検査（check_layout.text_units）と同じ数え方：比較は1つ、前後・カード・表の中の文字は数えない
            if len(heads) + loose + part > 3:
                many.append(f"[{r['#']}] 見出し{len(heads)}つ" + (f"＋見出しの無い要点{loose}つ" if loose else "") + ("＋部品" if part else ""))
            if pname == "s.compare":   # 比較の各列は3行以上（描画の検査）。図の案に各列3つ書いてあれば、スクリプトがそのまま組める
                m = re.search(r"（([^（）]{2,80})）\s*と\s*[^（）：。、]{1,16}（([^（）]{2,80})）", fig)
                if m and min(len([x for x in re.split(r"[、／/]", g) if x.strip()]) for g in m.groups()) < 3:
                    many.append(f"[{r['#']}] 比較の列が3つ未満（各列3つ：根拠の数値・例・よくある間違い）")
        if many:
            res.append(("✘", "文の塊の数", "塊が3つを超える枚：" + "・".join(many[:6]) + "。要点（行）は3〜4個のまま、見出しは2〜3つに："
                        "同じ見出しの下に2行まとめる（「例：a」「例：b」）か、補足の要点は原稿へ（描画の検査は塊4つで ERROR。制作の担当が全部の枚を組み直していた）"))
        res += term_order(text, srows, scaffold)
        res += scaffold.fit_marks(memo.parent)   # 骨組みと同じ部品・幅で組んだときに、本文の場所に入らない枚・列に入らない要点
        import os as _os2
        if "examples" not in Path(memo).resolve().parts and not _os2.environ.get("SENSEI_SKIP_EXAMPLE_COPY"):   # 見本はまとめの枚より前に作った（作り直すときに入れる）
            res += recap_check(text, srows, scaffold.col)
        res += example_copy(text, "memo", memo)
        import budget as _bud   # 標準の回：原稿は設計の担当が script.md に書く（制作の担当は書き直さない）
        import os as _os
        if _bud.light(memo.parent) and "examples" not in Path(memo).resolve().parts and not _os.environ.get("SENSEI_SKIP_EXAMPLE_COPY"):
            sp = memo.parent / "script.md"
            body_n = [r["#"] for r in srows if (scaffold.col(r, "役割") or "本文") in ("本文", "まとめ")]
            if not sp.exists():
                res.append(("△", "原稿", "script.md が無い（本文の枚ごとに「## N」と読み上げる原稿。設計の担当が書き、scaffold が notes.md に入れる）"))
            else:
                secs = {int(m.group(1)): m.group(2) for m in scaffold.NOTE_SEC.finditer(sp.read_text(encoding="utf-8"))}
                # 読み上げる字数（※ の出典・要確認の行は数えない）
                got = {n: len(re.sub(r"\s", "", "\n".join(l for l in t.splitlines() if not l.strip().startswith("※")))) for n, t in secs.items()}
                short = [n for n in body_n if got.get(n, 0) < 150]
                if short:
                    res.append(("△", "原稿", "script.md に原稿が無いか短い枚（150字未満）：" + "・".join(map(str, short[:8]))
                                + "（本文の枚は300〜400字。1文目で前の枚からつなぎ、図の読み方・根拠・橋渡し・次への予告）"))
                # 本文の枚の字数の幅（比べの4本で、300〜400字に入ったのは 3〜10 枚/10 とばらつき、最大 501 字の枚があった。少しの外れは許す）
                body_only = [r["#"] for r in srows if (scaffold.col(r, "役割") or "本文") == "本文"]
                off = [f"{n}（{got[n]}字）" for n in body_only if got.get(n, 0) >= 150 and not SCRIPT_MIN <= got[n] <= SCRIPT_MAX]
                if off:
                    res.append(("△", "原稿の字数", "本文の枚の原稿が300〜400字から外れた枚：" + "・".join(off[:8])
                                + "（長い枚は1文を短くして補足を削る。短い枚は根拠の数字・例か、学習者の経験への橋渡しを足す）"))
                # 作業の経緯の言い方（※ の行は出典・要確認の行なので見ない）。断りは設計メモ（3節の確認の列・8節）へ、原稿は聞き手に言う言い方だけ
                memo_hits = [f"{n}「{m.group(0)}」" for n, t in secs.items()
                             for m in [SCRIPT_MEMO.search("\n".join(l for l in t.splitlines() if not l.strip().startswith("※")))] if m]
                if memo_hits:
                    res.append(("△", "原稿の作業メモ", "原稿に作り手の作業の言い方が残っている枚：" + "・".join(memo_hits[:6])
                                + "（確かさの断り・作業の経緯は設計メモの3節の確認の列か8節へ。原稿は「〜とされます」のように聞き手に言う形だけ）"))
                # 図の中の位置で指す言い方（図の向き・並びは制作の担当があとで決めるので、原稿と食い違う。比べで「右端の〜」が横棒の一番下だった）
                pos = [f"{n}「{m.group(0)}」" for n, t in secs.items() for m in [SCRIPT_POS.search(t)] if m]
                if pos:
                    res.append(("△", "原稿の図の指し方", "図の中の位置で指している枚：" + "・".join(pos[:6])
                                + "（図の向き・並びは組むときに決まる。位置ではなく中身で指す：「右端の棒」→「南海トラフの棒」）"))
        import language as _LG   # 図の案を読むスクリプトは日本語の書き方だけ（ほかの言語の回は、読めない所を担当が組む）
        bad = scaffold.unbuildable(srows) if _LG.is_japanese(_LG.deck_language(start=memo.parent)) else []
        if bad:
            res.append(("✘", "部品の図の書き方", "スクリプトが組めない図の案：" + "；".join(f"[{n}] {name} は「{form}」の形で" for n, name, form in bad[:5])
                        + "（中身まで設計メモに書く。表なら行ごとのセル、判定なら はい・いいえ の行き先）"))
    except Exception:
        pass
    try:   # 軽量の回（裏取りの担当がいない）：確認がまだの事実を残さない（試しで、「一般」にした数値の行が2回とも残り、往復が増えた）
        import budget
        import facts
        if budget.light(memo.parent):
            _, fh, frows = facts.memo_facts(text)
            i_ok = next((k for k, h in enumerate(fh) if "確認" in h), 3)
            todo = [r for r in frows if facts.unchecked(r, i_ok)]
            if todo:
                res.append(("✘", "事実の確かめ", f"確認がまだの行が {len(todo)} 行（軽量の回は設計の担当が確かめる）："
                            + " / ".join(f"「{r[0][:16]}」" for r in todo[:5])
                            + "。数値・年・固有の名前を含む行は「一般」にできない。確かめて ○・△ にするか、確かめきれなければ ×（確かめられず）"))
    except Exception:
        pass
    import check_outline  # 関数の中で読む（check_outline → check_memo の循環を避ける）
    res += check_outline.reasoning(memo, text, require_review, review=MEMO_REVIEW, default_level=0, what="設計メモ")
    return res


HOOK_BODY = 2   # 本文の最初の何枚までに、問いか意外な事実を置くか（試しで、仕組みの説明が3枚続いてから問いが出て「引き込みが遅い」と減点された）


def _fig_src(text: str, n: int) -> list:
    """5節「図の案」の表の、その枚の行の全部のセル（値の出どころの列も）。"""
    rows = table_rows(text, "図の案") or []
    return [" ".join(r) for r in rows[1:] if r and r[0].strip() == str(n)]


def design_content(text: str, light: bool):
    """[(印, 項目, 説明)]：設計の中身で、外から見た採点で毎回減点された所。軽量の回は ✘（レビュー担当がいない）、標準の回は △。
    ・冒頭：本文の最初の HOOK_BODY 枚に、問い（？）か意外な事実（しかし・データN・数字の青帯）が無い
    ・くり返し：同じデータN を、本文の2枚以上の図で見せている（4枚目と9枚目で同じ表、と減点された）"""
    rows = table_rows(text, "話の順番")
    if not rows:
        return []
    head = rows[0]
    ix = lambda *names: next((k for k, h in enumerate(head) if any(n in h for n in names)), None)   # noqa: E731
    i_role, i_fig, i_pts, i_sum, i_link = ix("役割"), ix("図で見せる"), ix("本文の要点"), ix("青帯", "結論"), ix("前の枚から")
    get = lambda r, i: (r[i] if i is not None and i < len(r) else "")   # noqa: E731
    body = [r for r in rows[1:] if r and r[0].strip().isdigit() and (get(r, i_role) or "本文").strip() == "本文"]
    if not body:
        return []
    mark = "✘" if light else "△"
    out = []
    first = body[:HOOK_BODY]
    asks = lambda r: "？" in get(r, i_pts) + get(r, i_sum) or "?" in get(r, i_pts) + get(r, i_sum)   # noqa: E731
    data_ref = lambda r: re.search(r"データ\s*\d", get(r, i_fig) + get(r, i_pts) + get(r, i_sum))   # noqa: E731
    sec3b = re.search(r"^##\s*3b\..*?(?=^##\s|\Z)", text, re.S | re.M)
    surprise = bool(sec3b and re.search(r"^-\s*驚き\s*[:：]", sec3b.group(0), re.M))
    if surprise:
        # 3b節に驚きがあれば、最初の枚でそのデータを指す（冒頭の謎）。「しかし（壁）」のつなぎや筋の表の問いの枚だけでは通さない
        # （研究発表からの講座の試しで、2・3枚目が背景と「未検証」の説明だけのまま通り、驚きの数字2つが9・13枚目に回った）
        hooked = any(data_ref(r) for r in first)
    else:   # 驚きが無い回は前のまま：問い（？）・データN・しかし・筋の表の問いを置いた枚
        hooked = any(asks(r) or data_ref(r) or "しかし" in get(r, i_link) for r in first)
        try:
            import story
            qn = ((story.story_table(text) or {}).get("問い") or ("", None))[1]
            hooked = hooked or (qn is not None and str(qn) in {r[0].strip() for r in first})
        except Exception:
            pass
    if not hooked:
        out.append((mark, "冒頭の問い", f"本文の最初の {len(first)} 枚（{'・'.join(r[0] for r in first)}枚目）に、"
                    + (("3b節の驚きのデータ（データN）を指す枚が無い（「しかし（壁）」のつなぎや背景の説明だけでは引き込めない）。"
                        "冒頭の謎：3b節の驚きのうち一番強いものを、本文の1〜2枚目の青帯か要点で「〜のはずが、実際は〜。なぜ？」と見せ、"
                        "要点に「（データN）」と書く（数字は一言で。グラフと理由はあとの枚で1回だけ）。型の拍の順は変えない") if surprise else
                       ("問い（？）も意外な事実（しかし・データN）も無い。1枚目の本文で、学習者の思い込みを問う一文か、驚きのある数字を出す"
                        "（筋の表の問いを前へ。仕組みの説明はそのあと）"))
                    + "。references/story.md 3節"))
    last = body[-1]
    if re.search(r"[？?]\s*$", get(last, i_sum)) or re.search(r"[？?]\s*$", get(last, i_pts).split("/")[-1].split("／")[-1]):
        out.append(("△", "結びの答え", f"本文の最後の枚（{last[0].strip()}枚目）が問い（？）で終わる。冒頭の謎に戻り、"
                    "この回で言えたことを1行で答える（言えない所は「〜までは言える」と限りを付けて）"))
    import figplan
    cells = {n: " ".join(v) for n, v in figplan.fig_cells(text, "memo").items()}   # 2節の図の列と5節の図の案（値の出どころも）
    body_no = {r[0].strip() for r in body}
    seen = {}
    teaser = {r[0].strip() for r in first if asks(r)}   # 冒頭の謎（数字を一言で見せて問う枚）は くり返しに数えない
    for n, c in cells.items():
        if str(n) in body_no and str(n) not in teaser:
            for d in dict.fromkeys(re.findall(r"データ\s*(\d+)", c + " " + " ".join(r for r in _fig_src(text, n)))):
                seen.setdefault(f"データ{d}", []).append(str(n))
    for r in body:   # 青帯に同じ数字（2桁以上・%・〜の幅）をくり返す枚（試しで「誤り17〜33%」を4枚目と9枚目の青帯に）
        if r[0].strip() in teaser:
            continue
        for v in dict.fromkeys(re.findall(r"\d{2,}(?:[〜~-]\d+)?\s*[%％]|\d+[〜~-]\d+\s*[%％]", get(r, i_sum))):
            seen.setdefault(v.replace(" ", ""), []).append(r[0].strip())
    dup = {n: v for n, v in seen.items() if len(set(v)) >= 2}
    if dup:
        out.append((mark, "同じデータのくり返し", "；".join(f"{n} を {'・'.join(dict.fromkeys(v))}枚目で" for n, v in dup.items())
                    + "。同じ表・数字を2回見せない（あとの枚は、前の枚を指して言葉で振り返るか、別の数字・例にする。まとめの枚での振り返りは数えない）"))
    if not out:
        out.append(("✔", "冒頭とくり返し", f"本文の最初の {len(first)} 枚に問いか驚きの数字があり、同じデータを2回見せていない"))
    return out


def main(argv=None):
    import report
    argv, full = report.take_all(sys.argv[1:] if argv is None else argv)
    if len(argv) != 1:
        print(__doc__)
        return 2
    memo = Path(argv[0]).resolve()
    if not memo.exists():
        print(f"[ERROR] {memo} が無い")
        return 1
    try:
        import budget
        import data as datamod
        if budget.light(memo.parent) and datamod.files(memo.parent):
            before = memo.read_text(encoding="utf-8")
            datamod.merge(memo.parent)
            if memo.read_text(encoding="utf-8") != before:
                print("（軽量の回：data_N.md を3b節に入れた。data.py merge を別に走らせなくてよい）")
    except SystemExit:
        pass
    except Exception:
        pass
    res = check(memo)
    report.show(res, full)
    bad = sum(m == "✘" for m, _, _ in res)
    warn = sum(m == "△" for m, _, _ in res)
    try:
        import budget
        then = "制作に回す" if budget.light(memo.parent) else "レビューに回す"   # 担当2人の回には、別のレビューが無い
    except Exception:
        then = "レビューに回す"
    if bad:
        print(f"\n✘ が {bad} 件。直してから{then}（{memo.name}）")
    elif warn:
        print(f"\n△ が {warn} 件。直すか理由を書いてから、{then}（{memo.name}）")
    else:
        print(f"\n{then.replace('回す', '回してよい')}（{memo.name}）")
    if not bad:
        try:   # 軽量の回：次の手順も続けて出す（設計の担当が next_step を別に呼ぶ1回を省く）
            import budget
            if budget.light(memo.parent):
                import next_step
                _, nxt = next_step.steps_for(memo.parent)
                print(f"次：{nxt}")
        except Exception:
            pass
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
