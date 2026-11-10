"""発表（ゼミ）の構成案の確認：中身を作る前（構成案を書いた段階）に、outline.md の本文の枚数を発表時間と比べる（SKILL.md 手順2）。

    python <skill>/scripts/check_outline.py _work/<資料名>/outline.md

確かめること（✘ が1つでもあれば終了コード 1。△ は終了コードに入れない）
  本文の枚数：「## 構成」の表で、表紙と区切り（論文の表紙など、●見出しが「—」の行）を除いた行の数を、
  「## オプション」の表の発表時間と比べる。
    - 下限：発表時間÷2分（20分なら10枚）。下回ったら △。抜けている話（前提・図の読み方・結果の論理・
      聞き手が引っかかる所の説明）が無いか見直す。枚数合わせの水増しはしない
    - 上限はゆるめ：発表時間÷1.2分（20分なら16枚）。超えたら △。範囲を絞るか、1枚にまとめられる所をまとめる
    - どうしても外れるなら、outline.md に「枚数の理由：…」と書く。書いてあれば ✔
  発表時間が書いていない（ひとりゼミなど）ときは数えない。
  前提と丁寧さ：必須の「聞き手のテーマへの詳しさ（初学者／多少知っている／かなり知っている）」と「聞き手の前提知識（知っている＝…／知らない＝…）」が
    書いてある。無ければ ✘（小さな依頼でも。聞いて書くまで先へ進まない）。丁寧さは、書いていなければ詳しさから（0・1・2）
    （構成案のレビューの推論距離の監査が、これを前提にする。references/outline-review.md）
  推論距離の手当て：構成案のレビューの結果（outline.md と同じフォルダの outline_review.md）の
    穴の行（「[番号] 「A ⇒ B」｜種類｜要否｜…」、穴1つに1行。要否は 要1〜要4・深 のうち当たるもの全部）で、要1・要2・要4があるスライドと、要3が丁寧さより多いスライドが、
    outline.md の「## 引っかかりへの手当て」に [番号] で全部載っている（採らなかったものも理由つきで載せる）。「深」と、要と深の両方の行（迷い）は数えない（迷いは一覧に出す）。
    載っていなければ ✘。レビューの前（outline_review.md が無い）なら数えない
  照合できるのは、数えた結果と手当てが食い違っていないかまで。穴の数そのものはレビュー担当の判断。
  話の筋・前の枚から：筋の表（状況・複雑化・問い・答え）と、構成の表の「前の枚から」（そして・しかし・だから）。story.py
"""
import math
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_memo import table_rows  # noqa: E402

MIN_PER_SLIDE = 2.0      # 下限：1枚 2分（これより少ないと、抜けている話がある）
LOOSE_PER_SLIDE = 1.2    # 上限：1枚 1.2分（目安の 1.5分よりゆるめ）


def minutes(text: str):
    """「## オプション」の表の発表時間（分）。無ければ None。"""
    rows = table_rows(text, "オプション")
    for r in (rows or [])[1:]:
        if r and "発表時間" in r[0] and len(r) > 1:
            m = re.search(r"(\d+(?:\.\d+)?)", r[1])
            if m:
                return float(m.group(1))
    return None


def body_rows(text: str):
    """「## 構成」の表で、本文のスライドの見出し。表が無ければ None。"""
    rows = table_rows(text, "構成")
    if rows is None:
        return None
    head = rows[0]
    i_h = next((k for k, h in enumerate(head) if "見出し" in h), None)
    i_t = next((k for k, h in enumerate(head) if "タイトル" in h), None)
    i_r = next((k for k, h in enumerate(head) if h.strip() == "役割"), None)
    out = []
    for r in rows[1:]:
        h = r[i_h] if i_h is not None and len(r) > i_h else ""
        t = r[i_t] if i_t is not None and len(r) > i_t else ""
        role = r[i_r].strip() if i_r is not None and len(r) > i_r else ""
        if "表紙" in t or "表紙" in h or h.strip() in ("", "—", "-", "－"):
            continue
        if role and role != "本文":      # 想定質問・確認問題・質問待機などは本文の枚に数えない
            continue
        out.append(h)
    return out


REVIEW = "outline_review.md"
KINDS = ("用語", "出どころ", "論拠", "比較", "範囲", "根拠")
HOLE = re.compile(r"^\s*[-*]?\s*\[\s*(\d+)\s*\]\s*「(.+?)」\s*｜\s*(" + "|".join(KINDS) + r")\s*(?:[（(][^）)]*[）)])?\s*｜\s*((?:要[1-4]?|深)(?:\s*[・／/、,]\s*(?:要[1-4]?|深))*)\s*｜", re.M)
HOLE_FORM = "「[番号] 「A ⇒ B」｜種類｜要否（要1・要2・要3・要4・深 のうち当たるもの全部。例：要1・要4）｜補う前提：…｜使う所：…｜架け方：…」"


def knowledge(text: str) -> bool:
    """聞き手の前提知識（知っている＝…／知らない＝…）が書いてあるか。"""
    return bool(re.search(r"知っている\s*[＝=]\s*\S", text) and re.search(r"知らない\s*[＝=]\s*\S", text))


def familiarity(text: str):
    """聞き手のテーマへの詳しさ（初学者・多少知っている・かなり知っている）。オプションの表か「聞き手のテーマへの詳しさ：…」の行から。無ければ None。"""
    from slide_profile import FAMILIARITY, read_options, FAMILIARITY_KEY
    v = read_options(text).get(FAMILIARITY_KEY, "")
    if not v:
        m = re.search(FAMILIARITY_KEY + r"\s*[：:|]\s*([^\n|]+)", text)
        v = m.group(1) if m else ""
    return next((k for k in FAMILIARITY if k in v), None)


def politeness(text: str):
    """丁寧さ（0・1・2）。オプションの表か「丁寧さ：1」の行から。無ければ None。"""
    for r in (table_rows(text, "オプション") or [])[1:]:
        if r and "丁寧さ" in r[0] and len(r) > 1:
            m = re.search(r"\d", r[1])
            if m:
                return int(m.group(0))
    m = re.search(r"丁寧さ\s*[：:]\s*(\d)", text)
    return int(m.group(1)) if m else None


def holes(review_text: str):
    """レビュー結果の推論距離の行（穴1つに1行）：{スライド番号: [(つなぎ目, 種類, 要否)]}。"""
    out = {}
    for n, joint, kind, need in HOLE.findall(review_text):
        out.setdefault(int(n), []).append((joint.strip(), kind, need))
    return out


HOLE_ANY = re.compile(r"^\s*[-*]?\s*\[\s*(\d+)\s*\]\s*「(.+?)」\s*｜\s*([^｜\r\n]+?)\s*｜\s*([^｜\r\n]+?)\s*｜([^\r\n]*)$", re.M)


def hole_form(review_text: str):
    """推論距離の行の形の [(印, 項目, 説明)]：種類が6つでない・要否が読めない行（数えていない）は ✘、
    要4 の補う前提が「像：」で始まらない行と、全部の枚がちょうど1穴にそろった形は △。"""
    rows = HOLE_ANY.findall(review_text)
    res = []
    bad = [(int(n), kind) for n, _, kind, need, _ in rows if re.sub(r"[（(][^）)]*[）)]$", "", kind).strip() not in KINDS or not labels(need)]
    if bad:
        res.append(("✘", "推論距離の行の形", f"種類か要否が決まりの形でない行が {len(bad)} 行（" + "・".join(f"[{n}] {k}" for n, k in bad[:6])
                    + ("…" if len(bad) > 6 else "") + "）。この行は数えていない。レビュー担当に推論距離の節だけやり直させる（`brief.py レビュー担当 <work>` に「推論距離の節だけ」と添える。種類は " + "・".join(KINDS) + " から1つ、要否は 要1〜要4・深 のうち当たるもの全部）。メインが書き直さない"))
    y4 = [int(n) for n, _, kind, need, rest in rows if "要4" in labels(need) and not re.search(r"補う前提\s*[：:]\s*像", rest)]
    if y4:
        res.append(("△", "推論距離の要4", "要4 なのに補う前提が「像：〇〇と思い浮かべる → 実際は△△」の形でない行：" + "・".join(f"[{n}]" for n in y4)
                    + "（要4 は動作の語の像のずれだけ。当たらないなら 要1〜要3 に付け直す）"))
    per = {}
    for n, *_ in rows:
        per[int(n)] = per.get(int(n), 0) + 1
    if len(per) >= 6 and set(per.values()) == {1}:
        res.append(("△", "推論距離の数", f"{len(per)} 枚が全部ちょうど1穴にそろっている。枚ごとの数はそろえない（穴の無い枚は書かず、つなぎ目ごとに穴があれば何行でも）。つなぎ目を試し直す"))
    return res


def cared(text: str):
    """「## 引っかかりへの手当て」に [番号] で載っているスライド。節が無ければ空。"""
    m = re.search(r"^##\s*\d*\.?\s*引っかかりへの手当て.*?$(.*?)(?=^##\s|\Z)", text, re.S | re.M)
    return {int(x) for x in re.findall(r"\[\s*(\d+)\s*\]", m.group(1))} if m else set()


def labels(need: str) -> set:
    """要否の欄（「要1・要4」「要3・深」など、当たるもの全部）を {"要1", "要4"} のような集合に。"""
    return set(re.findall(r"要[1-4]?|深", need))


def unsure(need: str) -> bool:
    """迷い：要と深の両方が付いた行。手当ての検査には数えず、一覧に出してメイン側が決める。"""
    ls = labels(need)
    return "深" in ls and any(x.startswith("要") for x in ls)


def need_care(hs: dict, care_level: int):
    """手当てが要るスライド：要1（この枚の結論のなぜ）・要2（名前の付いた知らない語）・要4（動作の語の像のずれ）がある枚（丁寧さによらず）と、
    要3（あとで使う前提）が1枚に丁寧さより多い枚。「深」と迷い（要と深の両方）は数えない。番号の無い「要」は要1と同じに扱う（厳しいほうに倒す）。"""
    out = []
    for i, hl in hs.items():
        rows = [(kind, labels(need)) for _, kind, need in hl if not unsure(need)]
        strict = any(ls & {"要", "要1", "要2", "要4"} or (kind == "用語" and any(x.startswith("要") for x in ls)) for kind, ls in rows)
        later = sum("要3" in ls and kind != "用語" for kind, ls in rows)
        if strict or later > care_level:
            out.append(i)
    return sorted(out)


def reasoning(outline: Path, text: str, require_review: bool = False, small: bool = False,
              review: str = REVIEW, default_level=None, what: str = "構成案"):
    """前提と丁寧さ・推論距離の手当ての [(印, 項目, 説明)]。require_review＝レビュー結果が無ければ ✘（渡す前の確認）。
    講座の設計メモでも使う（review="memo_review.md"、what="設計メモ"）。"""
    REVIEW = review  # noqa: N806（この関数の中だけ、講座の memo_review.md に読み替える）
    res = []
    from slide_profile import FAMILIARITY
    fam = familiarity(text)
    lv = politeness(text)
    if lv is None and fam is not None:
        lv = FAMILIARITY[fam]          # 丁寧さは、書いていなければ詳しさから（初学者 0・多少知っている 1・かなり知っている 2）
    miss = [w for w, ok in (("聞き手のテーマへの詳しさ（初学者／多少知っている／かなり知っている）", fam is not None),
                            ("聞き手の前提知識（知っている＝…／知らない＝…）", knowledge(text))) if not ok]
    res.append(("✘" if miss else "✔", "前提と丁寧さ",
                f"必須の {'・'.join(miss)} が無い。聞いて書くまで先へ進まない（推論距離の監査の前提。オプションの表か設計メモの1節に書く）" if miss
                else f"詳しさ {fam}・前提知識あり・丁寧さ {lv}"))
    rv = outline.with_name(REVIEW)
    if not rv.exists():
        res.append(("✘" if require_review else "・", "推論距離の手当て",
                    f"{REVIEW} が無い（{what}のレビューの結果をそのまま残す）" if require_review else
                    f"まだレビュー前（レビューのあと、結果を {REVIEW} に残してもう一度走らせる）"))
        return res
    rv_text = rv.read_text(encoding="utf-8")
    hs = holes(rv_text)
    res += hole_form(rv_text)
    if not hs:
        res.append(("✘", "推論距離の手当て", f"{REVIEW} に推論距離の行が無い（穴1つを1行で、{HOLE_FORM} の形。references/outline-review.md の8）"))
        return res
    need = need_care(hs, lv if lv is not None else (default_level if default_level is not None else 1))
    missing = [i for i in need if i not in cared(text)]
    if missing:
        res.append(("✘", "推論距離の手当て", "「## 引っかかりへの手当て」に載っていないスライド：" + "・".join(f"[{i}]" for i in missing)
                    + f"（要1・要2・要4がある、または要3が丁寧さ {lv} より多い。採るなら架け方を、採らないなら理由を書く。「深」は書かなくてよい）"))
    else:
        res.append(("✔", "推論距離の手当て", f"手当ての要る {len(need)} 枚（{'・'.join(f'[{i}]' for i in need) or 'なし'}）が全部載っている"))
    doubt = sorted({i for i, hl in hs.items() if any(unsure(need) for _, _, need in hl)} - set(need) - cared(text))
    if doubt:
        res.append(("・", "推論距離の迷い", "要と深の両方が付いた穴のある枚：" + "・".join(f"[{i}]" for i in doubt)
                    + "（数えていない。その枚の結論に要るなら手当てに載せ、要らなければ原稿の ※ の候補）"))
    return res


def bounds(t: float):
    return math.floor(t / MIN_PER_SLIDE), math.floor(t / LOOSE_PER_SLIDE)


def check(outline: Path, require_review: bool = False):
    text = outline.read_text(encoding="utf-8")
    body = body_rows(text)
    if body is None:
        return [("✘", "本文の枚数", "「## 構成」の表が無い（examples/zemi/outline.md の形で書く）")]
    # 小さな依頼（本文5枚以下）は構成案のレビューを省いてよい（SKILL.md）ので、レビュー結果を求めない
    small = len(body) <= 5
    from check_memo import table_rows, thin_points, untagged_numbers
    rows = table_rows(text, "構成")
    tp = thin_points(rows, "構成案「## 構成」") if rows else None
    ut = untagged_numbers(rows, "構成案「## 構成」") if rows else None
    import story
    return (count(text, body) + ([tp] if tp else []) + ([ut] if ut else []) + story.check(text, "outline", story.body_numbers(text, "outline"), "構成案")
            + flows(text, outline.parent) + reasoning(outline, text, require_review and not small, small))


def flows(text: str, folder=None):
    """流れ図の案（「図で見せるもの」の列）が上限（本文4枚に1枚、最低2枚）を超えたら △。"""
    import figplan
    plan = figplan.plan_from_text(text, "outline")
    if not plan:
        return []
    rows = table_rows(text, "構成") or []
    i_h = next((k for k, h in enumerate(rows[0]) if "見出し" in h), 3) if rows else 3
    body_no = [int(r[0]) for r in rows[1:] if r and r[0].strip().isdigit() and len(r) > i_h and r[i_h].strip() not in ("", "—", "-")]
    import structures as _st
    _roles = _st.plan_roles(text, "outline") or {}
    body_no = [n for n in body_no if _roles.get(n, "本文") == "本文"]   # 想定質問・確認問題などは本文の枚に数えない
    mark, msg = figplan.flow_check(figplan.flow_count(plan, body_no), len(body_no), text, "構成案")
    nf = figplan.no_figure(plan, body_no)
    import structures
    roles = structures.check_roles(text, "outline", "構成案")
    if roles is None:
        roles = [("✘", "役割", "構成案の" + f"表に「役割」の列が無い。枚ごとに {'・'.join(structures.ROLES)} から選んで書く（結論の一文を置くのは本文だけ）")]
    return structures.check_plan(text, "outline", body_no, "構成案", folder) + roles + structures.check_expected_qa(text, "outline") + [(mark or "△", "流れ図の数", msg),
            ("✘" if nf else "✔", "図の無いスライド",
             f"「図で見せるもの」が「なし」・無い本文のスライド：{'・'.join(map(str, nf))}。{figplan.NO_FIGURE_HINT}" if nf
             else "本文のスライドすべてに図で見せるものがある")] + _data(text, folder, body_no)


def _data(text, folder, body_no):
    """資料の数字の組（data_N.md → 構成案の3b節）。発表では任意：無ければ何も出さない。"""
    import check_memo
    return check_memo.data_rows(text, Path(folder), body_no, "outline") if folder else []


def count(text: str, body):
    n = len(body)
    t = minutes(text)
    if t is None:
        return [("✔", "本文の枚数", f"{n}枚（発表時間が書いていないので数えない）")]
    lo, hi = bounds(t)
    aim = f"{math.floor(t / 2)}〜{math.floor(t / 1.5)}枚"
    if lo <= n <= hi:
        return [("✔", "本文の枚数", f"{n}枚（発表 {t:g}分。目安 {aim}、上限はゆるめに {hi}枚まで）")]
    if re.search(r"枚数の理由[：:]\s*\S", text):
        return [("✔", "本文の枚数", f"{n}枚（発表 {t:g}分の目安 {aim} から外れるが、理由が書いてある）")]
    if n < lo:
        hint = (f"下限 {lo}枚を下回る。抜けている話（前提・図の読み方・結果の論理・聞き手が引っかかる所の説明）が無いか見直す。"
                "枚数合わせの水増しはしない")
    else:
        hint = f"上限 {hi}枚を超える。範囲を絞るか、まとめられる所をまとめる"
    return [("△", "本文の枚数", f"{n}枚（発表 {t:g}分。目安 {aim}）。{hint}。どうしても外れるなら outline.md に「枚数の理由：…」を書く")]


def main(argv=None):
    import report
    argv, full = report.take_all(sys.argv[1:] if argv is None else argv)
    if len(argv) != 1:
        print(__doc__)
        return 2
    p = Path(argv[0]).resolve()
    if not p.exists():
        print(f"[ERROR] {p} が無い")
        return 1
    res = check(p)
    report.show(res, full)
    bad = sum(m == "✘" for m, _, _ in res)
    warn = sum(m == "△" for m, _, _ in res)
    reviewed = p.with_name(REVIEW).exists()
    nxt = "中身（図・ビルド）に進んでよい" if reviewed else "レビューに回してよい"
    print("\n" + (f"✘ が {bad} 件。直してから先へ" if bad else
                  f"△ が {warn} 件。直すか理由を書いてから先へ" if warn else nxt) + f"（{p.name}）")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
