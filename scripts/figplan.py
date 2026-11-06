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


def flow_limit(n_body: int) -> int:
    """1回のデッキで使ってよい流れ図の枚数：本文4枚に1枚、最低2枚（本文10枚なら2枚、12枚なら3枚、16枚なら4枚）。"""
    return max(2, n_body // 4)


def planned_kind(desc: str):
    """図の案の一文から、描くつもりの図の種類。描かないなら None。"""
    d = (desc or "").strip()
    if d in ("", "—", "-", "－", "なし"):
        return None
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
