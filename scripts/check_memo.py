"""講座の設計メモの確認：スライドを作る前（構成を決めた段階）に、設計メモ（memo.md）を機械的に確かめる（references/course.md 手順4）。

    python <skill>/scripts/check_memo.py _work/<講座フォルダ名>_<回の番号>/memo.md

確かめること（✘ が1つでもあれば終了コード 1。△ は終了コードに入れない）
  1. 本文の枚数：2節「話の順番」の表で、表紙・確認問題・解答を除いた行（＝本文のスライド）が、既定の10〜15枚に入っているか。
     外れたら △。話を足す（前提の説明・具体例・数値の例・つまずきやすい所・前後の回とのつながり）か回をまとめる（多ければ回を分ける）。
     テーマが狭いなど、どうしても外れるなら2節に「枚数の理由：…」と書く。書いてあれば ✔
  2. 出典：3節「事実と出典」の表で、確認が「○」の行の出典に、資料を特定できる手がかり
     （URL・DOI・「題名」・著者と年・条番号・頁や図の番号）がある。「厚生労働省」「薬機法」だけ、のような行は ✘
     （渡す前の確認 check_done.py も同じことを見る）
  3. 前提と丁寧さ：1節に必須の「聞き手のテーマへの詳しさ：…」（初学者／多少知っている／かなり知っている）と「聞き手の前提知識（知っている＝…／知らない＝…）」。
     無ければ ✘。丁寧さは書いていなければ詳しさから（初学者 0・多少知っている 1・かなり知っている 2）
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
        if h and "表紙" not in h and "問題" not in h and "解答" not in h:
            out.append(h)
    return out


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
        if not h or any(w in h for w in ("表紙", "問題", "解答")):
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
    自分の計算なら〔発表者の概算〕）。"""
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
                f"（講座は〔事実3〕＝3節の表の行）、自分の計算なら〔発表者の概算〕と書く（{what}。カードが、その所を書き手に渡す）")
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
        if (role and role != "本文") or (not role and any(w in h for w in ("表紙", "問題", "解答", "区切り"))):
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
        res.append(("△", "データ", "3b節にデータがあるのに、描く図が無い。強い組なら、図の案を「目的：種類：データN」（棒グラフ・折れ線・帯など）にして見せる。"
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
            res.append(("△", "本文の枚数", f"{n}枚（既定 {BODY_MIN}〜{BODY_MAX}枚）。{hint}。どうしても外れるなら2節に「枚数の理由：…」を書く"))
    import figplan
    plan = figplan.plan_from_text(text, "memo")
    rows = table_rows(text, "話の順番") or []
    body_no = [int(r[0]) for r in rows[1:] if r and r[0].strip().isdigit() and r[1:2] and
               not any(w in r[1] for w in ("表紙", "問題", "解答"))]
    if plan:
        mark, msg = figplan.flow_check(figplan.flow_count(plan, body_no), len(body_no), text, "設計メモ")
        res.append((mark or "△", "流れ図の数", msg))
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
        res.append(("✘", "出典", f"○ なのに資料を特定できない行が {len(bad)} 件（書名・URL・頁などを足すか、確認を × にする）："
                    + " / ".join(f"「{a[:14]}」→{b[:20]}" for a, b in bad[:4])))
    else:
        res.append(("✔", "出典", "○ の行はすべて資料を特定できる"))
    import check_outline  # 関数の中で読む（check_outline → check_memo の循環を避ける）
    res += check_outline.reasoning(memo, text, require_review, review=MEMO_REVIEW, default_level=0, what="設計メモ")
    return res


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
    res = check(memo)
    report.show(res, full)
    bad = sum(m == "✘" for m, _, _ in res)
    warn = sum(m == "△" for m, _, _ in res)
    if bad:
        print(f"\n✘ が {bad} 件。直してからレビューに回す（{memo.name}）")
    elif warn:
        print(f"\n△ が {warn} 件。直すか理由を書いてから、レビューに回す（{memo.name}）")
    else:
        print(f"\nレビューに回してよい（{memo.name}）")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
