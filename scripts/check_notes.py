"""読み上げ原稿（notes.md）の確認。渡す前の確認（check_done.py）が呼ぶ。単独でも走らせられる。

    python <skill>/scripts/check_notes.py <work>          # <work>/notes.md と、構成案（outline.md）か設計メモ（memo.md）

確かめること
  ✘ 手当ての抜け：構成案・設計メモの「引っかかりへの手当て」で、原稿に回すと書いた枚（行に「原稿」とある [番号]）について、
     notes.md のその枚に、手当ての中身が入っているか。中身は行の中のかぎかっこで見る：
       - 「原稿で「…」」「原稿で〇〇を「…」と言う」の「…」：その言い回し（7割以上が続けて一致）が原稿にある
       - 「用語「…」」（「用語の穴「…」」も可）の語：その語が原稿にある（本文で手当てした語は、スライドに書いてあればよい）
     かぎかっこの無い行は数えない（何を言うかを書いていないので確かめられない。手当ては「…」で書く）
  △ 書き方の目安（読み上げやすさ。決めるのは人）
       - 1文が 90字を超える（読み上げで息が続かない。2文に分ける）
       - 中身の無いつなぎだけの文（「では次に。」「次のスライドです。」など。次の枚で何を見るかを言う）
       - 原稿全体の長さが、発表時間（構成案の ## オプション の「発表時間」）に比べて多すぎる・少なすぎる（1分 300字の目安で ±40%）
       - 1枚あたりの原稿が少ない本文の枚（ゼミは 発表時間×300字÷本文の枚数 の半分、講座は 240字に届かない。字数は句読点・空白を除いて数える）
"""
from __future__ import annotations

import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))

SENT_MAX = 90            # 1文の長さの目安（字）
CHARS_PER_MIN = 300      # 読み上げの速さの目安（字／分）
LEN_TOL = 0.4            # 発表時間との釣り合いの幅
NOTE_PER_SLIDE = 380     # 講座の本文の枚の原稿の目安（句読点・空白を除いた字数）
NOTE_MIN_COURSE = 240    # 講座で、これより少ない枚は △（見本の講座は 250〜450字）
EMPTY_LINK = re.compile(r"^(では|それでは|続いて|次に|次は)?[、,]?\s*(次の(スライド|ページ)(です|に(進みます|行きます|移ります))|次に(進みます|行きます|移ります)|"
                        r"次のスライドをご覧ください|では次に|それでは次に)[。．]?$")
QUOTE = re.compile(r"「([^「」]{2,})」")
# 読み上げる原稿に残った作業のメモ（書き手が迷った所は返答に書く。※の行も聞き手に見える）
WORK_MEMO = re.compile(r"TODO|ノートへ[:：]|抜き出し|出典を確かめ|確かめてから話して|確認できていません|仕上げ(役|段階)|書き手|カードの|手元の資料に(は)?(ありません|ない|無い)")


def _norm(s: str) -> str:
    return re.sub(r"[\s、。，．,.・「」『』（）()\-－—]", "", s or "")


def _care_section(text: str):
    m = re.search(r"^##\s*\d*\.?\s*引っかかりへの手当て.*?$(.*?)(?=^##\s|\Z)", text, re.S | re.M)
    return m.group(1) if m else ""


def care_items(text: str):
    """[(スライド番号, [原稿で言う言い回し], [用語の穴の語], 行)]：手当ての節の、原稿に回すと書いた行。"""
    out = []
    for line in _care_section(text).splitlines():
        m = re.match(r"\s*[-*]\s*\[\s*(\d+)\s*\](.*)", line)
        if not m or "原稿" not in m.group(2):
            continue
        body = m.group(2)
        say = []
        for part in re.split(r"(?=原稿)", body)[1:]:        # 「原稿」より後ろのかぎかっこ（次の「本文」までの間）
            part = re.split(r"本文[にでの]", part)[0]
            say += QUOTE.findall(part)
        terms = []
        for t in re.findall(r"用語(?:の穴)?((?:「[^「」]+」)+)", body):
            terms += QUOTE.findall(t)
        out.append((int(m.group(1)), say, terms, line.strip()))
    return out


WORD = re.compile(r"[一-龥々]{2,}|[ァ-ヶー]{2,}|[A-Za-z]{2,}|\d+(?:\.\d+)?")
WORD_SHARE = 0.6         # 言い回しの中身の語のうち、原稿にあればよい割合（言い方を変えてよい）


def _contains(hay: str, needle: str) -> bool:
    """needle の中身が hay にあるか：そのまま入っているか、中身の語（漢字・カタカナの2字以上の語、英字、数）の6割以上が入っている。"""
    h, n = _norm(hay), _norm(needle)
    if not n or n in h:
        return True
    words = set(WORD.findall(needle))
    if not words:
        m = SequenceMatcher(None, h, n, autojunk=False).find_longest_match(0, len(h), 0, len(n))
        return m.size >= 0.7 * len(n)
    return sum(w in hay for w in words) >= WORD_SHARE * len(words)


def missing_care(plan_text: str, notes: dict, slide_texts: dict | None = None):
    """[(番号, 足りないもの)]：手当てで原稿に回すと書いたのに、原稿（とスライド）に中身が無い。"""
    out = []
    for n, say, terms, line in care_items(plan_text):
        note = notes.get(n, "")
        lack = [f"「{s}」" for s in say if not _contains(note, s)]
        lack += [f"用語「{t}」" for t in terms if not (_contains(note, t) or _contains((slide_texts or {}).get(n, ""), t))]
        if lack:
            out.append((n, "・".join(lack)))
    return out


def sentences(text: str):
    body = "\n".join(l for l in text.splitlines() if not l.lstrip().startswith("※"))   # 出典・補足の行は除く
    return [s.strip() for s in re.split(r"(?<=[。！？])|\n", body) if s.strip()]


def talk_minutes(plan_text: str):
    m = re.search(r"\|\s*発表時間\s*\|\s*(\d+(?:\.\d+)?)\s*分", plan_text or "")
    return float(m.group(1)) if m else None


def check(work: Path, plan_text: str | None = None, slide_texts: dict | None = None):
    """[(印, 項目, 説明)]。"""
    from set_notes import load_notes
    work = Path(work)
    nf = work / "notes.md"
    if not nf.exists():
        return [("✘", "原稿の手当て", "notes.md が無い")]
    notes = load_notes(nf)
    if plan_text is None:
        src = work / "memo.md" if (work / "memo.md").exists() else work / "outline.md"
        plan_text = src.read_text(encoding="utf-8") if src.exists() else ""
    res = []
    items = care_items(plan_text)
    lack = missing_care(plan_text, notes, slide_texts)
    if lack:
        res.append(("✘", "原稿の手当て", "手当てで原稿に回すと書いたのに、原稿に無い：" + "、".join(f"[{n}] {w}" for n, w in lack[:6])
                    + "（notes.md のその枚に、その言い回し・用語の説明を入れる。言い方を変えたなら、手当ての行も直す）"))
    elif items:
        res.append(("✔", "原稿の手当て", f"原稿に回した手当て {len(items)}件が、原稿に入っている"))
    memo = [(n, m.group(0)) for n, t in notes.items() for m in [WORK_MEMO.search(t)] if m]
    if memo:
        res.append(("✘", "原稿の作業メモ", "読み上げる原稿に作業のメモが残っている：" + "、".join(f"[{n}] 「{w}」" for n, w in memo[:6])
                    + "（迷った所・確かめたい所は原稿から消し、返答に書く。資料にあるかは資料を開いて確かめる）"))
    long = [(n, len(s)) for n, t in notes.items() for s in sentences(t) if len(s) > SENT_MAX]
    if long:
        res.append(("△", "原稿の1文の長さ", f"{SENT_MAX}字を超える文：" + "、".join(f"[{n}] {k}字" for n, k in long[:6]) + "（読み上げで息が続かない。2文に分ける）"))
    empty = [n for n, t in notes.items() for s in sentences(t) if EMPTY_LINK.match(s)]
    if empty:
        res.append(("△", "原稿のつなぎ", "中身の無いつなぎだけの文：" + "・".join(map(str, sorted(set(empty))))
                    + "（「では次に」で済ませず、次の枚で何を見るか・なぜそこへ進むかを1文で）"))
    mins = talk_minutes(plan_text)
    if mins:
        total = sum(len(_norm("\n".join(sentences(t)))) for t in notes.values())
        want = mins * CHARS_PER_MIN
        if abs(total - want) > LEN_TOL * want:
            res.append(("△", "原稿の長さ", f"原稿 {total}字（読み上げ約 {total / CHARS_PER_MIN:.0f}分）、発表時間 {mins:g}分"
                        f"（目安 {want:.0f}字 ±{LEN_TOL:.0%}）。{'削る（細部はスライドに無い補足から）' if total > want else '図の読み方・つなぎを足す'}"))
        else:
            res.append(("✔", "原稿の長さ", f"原稿 {total}字（約 {total / CHARS_PER_MIN:.0f}分）、発表時間 {mins:g}分"))
    # 1枚あたりの原稿：本文の役割の枚で、目安の半分（講座は 300字）に届かない枚
    import structures
    kind = "memo" if "話の順番" in plan_text else "outline"
    roles = structures.plan_roles(plan_text, kind) or {}
    body = [n for n, r in roles.items() if r == "本文"]
    if body:
        if mins:
            per, low = mins * CHARS_PER_MIN / len(body), 0.5 * mins * CHARS_PER_MIN / len(body)
        else:   # 講座（AI講義モード）：見本の中央値は 1枚 420字前後
            per, low = NOTE_PER_SLIDE, NOTE_MIN_COURSE
        short = [(n, len(_norm("\n".join(sentences(notes.get(n, "")))))) for n in body]
        short = [(n, k) for n, k in short if k < low]
        if short:
            res.append(("△", "1枚あたりの原稿", f"目安 {per:.0f}字前後に対して少ない枚：" + "、".join(f"[{n}] {k}字" for n, k in short[:8])
                        + "（図のどこを見て何が読めるか・具体例・よくある間違い・次の枚へのつなぎを足す）"))
    return res


def main(argv=None):
    argv = argv or sys.argv[1:]
    if not argv:
        print(__doc__)
        return 1
    res = check(Path(argv[0]))
    for mark, item, msg in res:
        print(f"{mark} {item}：{msg}")
    return 1 if any(m == "✘" for m, _, _ in res) else 0


if __name__ == "__main__":
    sys.exit(main())
