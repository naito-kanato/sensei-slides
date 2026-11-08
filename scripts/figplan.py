"""図の案とスライドの図を突き合わせる（check_done.py・check_memo.py・check_outline.py が使う）。

図の案：講座は設計メモ（memo.md）の「## 5. 図の案」の表（スライド｜…｜何をどう描くか）、
        発表は構成案（outline.md）の「## 構成」の表の「図で見せるもの」の列。
図の種類：流れ図（箱と矢印。s.flow）・表（s.table）・図（figs.py で描いた画像・論文の図）。数式の画像は図に数えない。

以前の試験で、図の案に「経路図」「ミラーと死角の位置関係」と書いたのに、スライドでは本文を言い換えただけの3つの箱の流れ図になり、
本文11枚のうち8枚が流れ図だった。流れ図は、手順・因果・分類のように順番や枝分かれに意味があるときだけにする（references/figures.md）。
"""
import re

from pptx.enum.shapes import MSO_SHAPE_TYPE

FLOW_WORDS = re.compile(r"流れ図|フロー|ブロック図|手順の図|段違い|循環")
DIAGRAM_WORDS = re.compile(r"カード|ツリー|前後|ビフォー|並べた図|2つ並べ")   # 図解の型（structures.py）。図として扱う
DIAGRAM_PREFIX = ("カード_", "ツリー", "前後_", "並べた図")
TABLE_WORDS = re.compile(r"^表[：:\s]|比較表|の表")
REASON = re.compile(r"流れ図の理由[：:]\s*\S")


# ---- 図の種類の選択肢（構成案・設計メモの「図で見せるもの」は、この名前のどれかを書いてから中身を書く。例「棒グラフ：…」）
# 目的から選ぶ。名前ごとに描く部品が決まっているので、文字の箱を並べただけの図になりにくい。
FIG_MENU = [
    # (名前, 目的, 部品, 別の書き方)
    ("棒グラフ", "2〜8個の値を比べる・順位", "figlib.bars", ("棒",)),
    ("折れ線", "時間・条件で値が変わる（数値あり）", "fig() に plot（figlib.data_fit）", ("推移のグラフ",)),
    ("概略グラフ", "関数形・傾向（数値なし）", "fig() ＋ noticks（figlib.compare など）", ("概略図", "傾向の図")),
    ("帯グラフ", "全体の内訳・割合", "figlib.share_bar", ("割合の帯", "内訳の帯")),
    ("年表", "いつ何が起きたか・時代の区切り", "figlib.timeline", ("時間軸",)),
    ("模式図", "仕組み・構造・配置・縮尺", "blank() に box・arrow など（figkit）", ("仕組みの図", "断面図", "縮尺図", "作図", "装置図")),
    ("流れ図", "手順・因果・分類（順番や枝分かれに意味がある）", "s.flow（PowerPoint の図形）", ("フロー", "ブロック図")),
    ("表", "項目×観点（2つ以上の比較を、数や語で）", "s.table", ("比較表",)),
    ("比較", "2つを左右に並べて違いを見せる", "s.compare", ("並べて比べ",)),
    ("前後", "変える前と後", "s.before_after", ("ビフォー",)),
    ("カード", "同格の要素を2〜6個", "s.cards", ("箱",)),
    ("ツリー", "階層・分類の木", "s.tree", ()),
    ("大きな数字", "1つの値・結論を印象づける（1回に1〜2枚）", "s.key_message", ()),
    ("資料の図", "教科書・論文の図をそのまま（出典を付ける）", "pdf_pages.py crop", ("論文 Fig", "論文の図", "教科書の図", "論文 Table", "Fig.")),
    ("写真", "実物（自作しない。ユーザーに用意してもらう）", "s.figure_beside", ()),
]


def menu_name(desc: str):
    """図の案の一文に出てくる、図の種類の選択肢の名前（無ければ None）。"""
    d = desc or ""
    for name, _, _, alias in FIG_MENU:
        if name in d or any(a in d for a in alias):
            return name
    return None


# 図の目的の選択肢と、目的ごとのおすすめの図（先頭がいちばんのおすすめ）。図の案は「目的：種類：中身」で書く
FIG_PURPOSES = [
    # (目的, 何をしたいとき, おすすめの種類)
    ("比べる", "2〜8個の値を比べる・順位", ("棒グラフ", "比較", "表")),
    ("推移", "時間・条件で値が変わる", ("折れ線", "概略グラフ")),
    ("傾向", "関数形・傾向を見せる（数値なし）", ("概略グラフ",)),
    ("内訳", "全体の中の割合", ("帯グラフ", "大きな数字")),
    ("時期", "いつ何が起きたか・時代の区切り", ("年表",)),
    ("仕組み", "仕組み・構造・配置・縮尺", ("模式図", "資料の図")),
    ("流れ", "手順・因果・分類の枝分かれ", ("流れ図",)),
    ("観点", "項目×観点で整理する", ("表",)),
    ("違い", "2つの状態・方法の違い", ("前後", "比較")),
    ("並び", "同格の要素を並べる", ("カード",)),
    ("階層", "上下関係・分類の木", ("ツリー",)),
    ("印象", "1つの値・結論を印象づける（1回に1〜2枚）", ("大きな数字",)),
    ("柱", "答えを支える柱の一覧（答えの位置「先」の答えの枚）", ("カード", "ツリー")),
    ("実物", "資料の図・実物をそのまま見せる", ("資料の図", "写真")),
]
PURPOSE_NAMES = [p for p, _, _ in FIG_PURPOSES]
REASON_WORDS = re.compile(r"外す理由[：:]|おすすめ外の理由[：:]")


def parse_fig(cell: str):
    """図の案のセル → (目的 or None, 種類 or None)。「目的：種類：中身」の形なら、種類は2つ目の区切りの中だけで探す
    （中身の文の「発表」の「表」などを種類と取り違えない）。目的が無い古い書き方は、文全体から種類を探す。"""
    d = (cell or "").strip()
    parts = [x.strip() for x in d.split("：")]
    if len(parts) >= 2 and parts[0] in PURPOSE_NAMES:
        return parts[0], menu_name(parts[1])
    return None, menu_name(d)


PPT_KINDS = ("表", "大きな数字", "流れ図", "比較", "前後", "カード", "ツリー")   # 画像でなく PowerPoint の部品で組む種類


def pptx_part(cell: str):
    """図の案が PowerPoint の部品で組む種類なら、その部品（s.table など）。画像（figs/sNN.png）なら None。"""
    _, k = parse_fig(cell)
    if k is None:
        k = "表" if re.match(r"\s*表", cell or "") else "大きな数字" if re.match(r"\s*大きな数字", cell or "") else None
    return next((x[2] for x in FIG_MENU if x[0] == k), None) if k in PPT_KINDS else None


def check_menu(text: str, kind: str, body_no: list):
    """本文の枚の「図で見せるもの」が「目的：種類：中身」で書かれ、種類がその目的のおすすめか [(印, 項目, 説明)]。
    おすすめ以外の種類にするなら、中身に「外す理由：…」を書く。"""
    import structures
    rows = structures._plan_table(text, kind)
    if not rows:
        return []
    head = rows[0]
    i = next((k for k, h in enumerate(head) if "図で見せる" in h), None)
    if i is None:
        return []
    nopurpose, nokind, offmenu = [], [], []
    for r in rows[1:]:
        if not (r and r[0].strip().isdigit() and int(r[0]) in body_no and len(r) > i):
            continue
        d = r[i].strip()
        if d in ("", "—", "-", "－", "なし"):
            continue
        purpose, k = parse_fig(d)
        if purpose is None:
            nopurpose.append(f"[{r[0]}]「{d[:14]}」")
        elif k is None:
            nokind.append(f"[{r[0]}]「{d[:14]}」")
        else:
            rec = next(x[2] for x in FIG_PURPOSES if x[0] == purpose)
            if k not in rec and not REASON_WORDS.search(d):
                offmenu.append(f"[{r[0]}] {purpose}に{k}（おすすめ：{'・'.join(rec)}）")
    notes = []
    if nopurpose:
        notes.append("目的が無い：" + "・".join(nopurpose[:6]) + "（先頭に目的：" + "・".join(PURPOSE_NAMES) + "）")
    if nokind:
        notes.append("種類が選択肢に無い：" + "・".join(nokind[:6]) + "（" + "・".join(n for n, *_ in FIG_MENU) + "）")
    if offmenu:
        notes.append("目的のおすすめでない図：" + "；".join(offmenu[:6]) + "（おすすめにするか、中身に「外す理由：…」）")
    if notes:
        return [("△", "図の目的と種類", "。".join(notes) + "。書き方は「目的：種類：中身」（references/figures.md 1b）")]
    return [("✔", "図の目的と種類", "本文の図の案は、どれも目的と、そのおすすめの種類で書いてある")]


def flow_limit(n_body: int) -> int:
    """1回のデッキで使ってよい流れ図の枚数：本文4枚に1枚、最低2枚（本文10枚なら2枚、12枚なら3枚、16枚なら4枚）。"""
    return max(2, n_body // 4)


def planned_kind(desc: str):
    """図の案の一文から、描くつもりの図の種類。描かないなら None。"""
    d = (desc or "").strip()
    if d in ("", "—", "-", "－", "なし"):
        return None
    purpose, k = parse_fig(d)
    if purpose is not None and k is not None:
        return k if k in ("大きな数字", "比較", "流れ図", "表") else "図"
    if "大きな数字" in d:
        return "大きな数字"
    if re.search(r"並べて比べ|比較", d) and not TABLE_WORDS.search(d):
        return "比較"
    if FLOW_WORDS.search(d):
        return "流れ図"
    if DIAGRAM_WORDS.search(d):
        return "図"
    if TABLE_WORDS.search(d):
        return "表"
    return "図"


def slide_numbers(cell: str):
    """「8」「8–9」「8〜9」「8・9」のような番号の書き方を、番号のリストに。"""
    out = []
    for a, b in re.findall(r"(\d+)\s*(?:[–\-〜~～]\s*(\d+))?", cell or ""):
        out += list(range(int(a), int(b) + 1)) if b else [int(a)]
    return out


# 図の案の中身に残った、置き換え用の名前（「分類群A」「要素B」「〇〇」「XX」）。テーマの固有の名前で書く
GENERIC = re.compile(r"[一-龥ぁ-んァ-ヶー][A-ZＡ-Ｚ](?![A-Za-zＡ-Ｚａ-ｚ])|〇〇|○○|ＸＸ|XX|[A-ZＡ-Ｚ]・[A-ZＡ-Ｚ]|架空の|仮の(?:種|群|名前|例)")


def generic_names(plan: dict) -> list[int]:
    """図の案の中身に置き換え用の名前が残っている枚の番号。"""
    def body(cell):   # 「目的：種類：中身」の中身（無ければセル全体）
        parts = (cell or "").split("：")
        return "：".join(parts[2:]) if len(parts) >= 3 and parts[0].strip() in PURPOSE_NAMES else cell
    return sorted(n for n, cell in (plan or {}).items() if cell and GENERIC.search(body(cell)))


def plan_from_text(text: str, kind: str):
    """{スライド番号: 図の案の一文}。kind="memo"（講座の設計メモ）か "outline"（発表の構成案）。表が無ければ None。"""
    from check_memo import table_rows
    rows = table_rows(text, "図の案") if kind == "memo" else table_rows(text, "構成")
    if not rows:
        return None
    head = rows[0]
    i_no = next((k for k, h in enumerate(head) if "スライド" in h or "番号" in h or h.strip() == "#"), 0)
    i_desc = next((k for k, h in enumerate(head) if ("何をどう描く" in h if kind == "memo" else "図で見せる" in h)), None)
    if i_desc is None:
        return None
    plan = {}
    for r in rows[1:]:
        if len(r) > max(i_no, i_desc):
            for n in slide_numbers(r[i_no]):
                plan[n] = r[i_desc]
    return plan


def actual_kinds(slide):
    """スライドにある図の種類の集合（流れ図・表・図）。"""
    from structures import TEXT_SHAPE_NAMES
    shapes = list(slide.shapes)
    pics = [s for s in shapes if s.shape_type == MSO_SHAPE_TYPE.PICTURE and s.name != "数式"]
    names = [s.name for s in shapes]
    cards = [n for n in names if n.startswith(("カード_段違い", "カード_循環"))]
    diagram = any(n.startswith(DIAGRAM_PREFIX) for n in names)
    arrows = [s for s in shapes if s.name == "矢印"]
    boxes = [s for s in shapes if s.shape_type == MSO_SHAPE_TYPE.AUTO_SHAPE and s.has_text_frame and s.text_frame.text.strip()
             and s.name not in ("青帯", "注目の輪", "注目の吹き出し", "章のナビ") and s.name not in TEXT_SHAPE_NAMES
             and not s.name.startswith(DIAGRAM_PREFIX)]
    kinds = set()
    if pics or diagram:
        kinds.add("図")
    if cards:
        kinds.add("流れ図")      # 段違いの順序・循環のカードは、流れ図の数に入れる（言い換えの箱の並べすぎを防ぐ）
    if arrows and len(boxes) >= 2:
        kinds.add("流れ図")
    elif len(boxes) >= 4:
        kinds.add("表")
    return kinds


def slide_type(slide, W, H):
    """本文のスライドの型（左文右図・上文下図・全面の図・比較・大きな数字・流れ図・表・文のみ）。図形の名前と置き場所から。"""
    shapes = list(slide.shapes)
    names = {s.name for s in shapes}
    if "大きな数字" in names:
        return "大きな数字"
    if {"比較の左", "比較の右"} <= names:
        return "比較"
    if "区切りの地" in names:
        return "区切り"
    for prefix, kind in (("カード_並列", "並列カード"), ("カード_格子", "格子のカード"), ("カード_段違い", "段違いの順序"),
                         ("カード_循環", "循環"), ("ツリー", "ツリー"), ("前後_", "前後")):
        if any(n.startswith(prefix) for n in names):
            return kind
    if sum(n == "並べた図" for n in [s.name for s in shapes]) >= 2:
        return "2つ並べた図"
    pics = [s for s in shapes if s.shape_type == MSO_SHAPE_TYPE.PICTURE and s.name != "数式" and (s.width or 0) > 0.15 * W]
    kinds = actual_kinds(slide)
    if pics:
        big = max(pics, key=lambda s: s.width * s.height)
        if big.name == "全面の図" or big.width * big.height > 0.4 * W * H:
            return "全面の図"
        if big.name == "下の図" or (big.width > 0.5 * W and big.top > 0.4 * H):
            return "上文下図"
        return "左文右図" if big.left + big.width / 2 > 0.5 * W else "右文左図"
    if "流れ図" in kinds:
        return "流れ図"
    if "表" in kinds:
        return "表"
    return "文のみ"


MAX_RUN = 4   # 同じ型が続いてよい枚数（これを超えて続いたら △。「同じレイアウトが4枚続いたら1枚変える」Zoho の手引き）


def monotony(prs, skip=()):
    """[(始まりの番号, 終わりの番号, 型)]：同じ型が MAX_RUN 枚を超えて続いた所。"""
    W, H = prs.slide_width, prs.slide_height
    seq = [(i, slide_type(sl, W, H)) for i, sl in enumerate(prs.slides, 1) if i not in skip]
    out, start = [], 0
    for k in range(1, len(seq) + 1):
        if k == len(seq) or seq[k][1] != seq[start][1] or seq[k][0] != seq[k - 1][0] + 1:
            if k - start > MAX_RUN:
                out.append((seq[start][0], seq[k - 1][0], seq[start][1]))
            start = k
    return out


def mismatches(prs, plan: dict, skip=()):
    """[(スライド番号, 説明)]：図の案と違う図、案に無い流れ図。skip は見ないスライド（表紙・問題・解答）。"""
    out = []
    for i, sl in enumerate(prs.slides, 1):
        if i in skip:
            continue
        want = planned_kind(plan.get(i, ""))
        have = actual_kinds(sl)
        if want == "図" and "図" not in have:
            got = "・".join(sorted(have)) or "図なし"
            out.append((i, f"案は図（{plan[i][:24]}）なのに{got}"))
        elif want in ("大きな数字", "比較"):
            got = slide_type(sl, prs.slide_width, prs.slide_height)
            if got != want:
                out.append((i, f"案は{want}（{plan[i][:24]}）なのに{got}"))
        elif want in ("流れ図", "表") and not (have & {want, "図"}):
            out.append((i, f"案は{want}（{plan[i][:24]}）なのに{'・'.join(sorted(have)) or '図なし'}"))
        elif want is None and "流れ図" in have:
            out.append((i, "図の案に無い流れ図"))
    return out


def no_figure(plan: dict, body_slides):
    """本文のスライドのうち、図の案が無い（「なし」「—」・行が無い）番号。本文のスライドには必ず何かを見せる（図・表・大きな数字・比較・流れ図）。
    以前の試験で、図の案を「なし」にした枚が文だけのスライドになり、どの確認も通っていた。"""
    return [i for i in body_slides if planned_kind(plan.get(i, "")) is None]


NO_FIGURE_HINT = ("本文のスライドには、図・表・大きな数字・比較のどれかを必ず置く。文だけで言える話なら、"
                  "数値を大きな数字に、2つの違いを比較に、具体例を図にできないか考える（references/figures.md「スライドの型」）。"
                  "どれにもならない枚は、前後の枚にまとめる")


def flow_count(plan: dict, body_slides):
    """本文のスライドのうち、流れ図の案の枚数。"""
    return sum(planned_kind(plan.get(i, "")) == "流れ図" for i in body_slides)


def flow_check(n: int, n_body: int, text: str, where: str):
    """流れ図の枚数を上限と比べた (印, 説明)。上限を超えても「流れ図の理由：…」があれば ✔。"""
    lim = flow_limit(n_body)
    if n <= lim:
        return "✔", f"流れ図 {n}枚（上限 {lim}枚：本文 {n_body}枚の4枚に1枚）"
    if REASON.search(text):
        return "✔", f"流れ図 {n}枚（上限 {lim}枚を超えるが、{where}に理由がある）"
    return None, (f"流れ図 {n}枚（上限 {lim}枚：本文 {n_body}枚の4枚に1枚、最低2枚）。流れ図は手順・因果・分類で順番や枝分かれに意味があるときだけにし、"
                  f"ほかはテーマか難所を見せる図（模式図・グラフ・位置関係）にする。どうしても要るなら{where}に「流れ図の理由：…」を書く")
