"""講座の設計メモの裏取りを分ける・まとめる（references/course.md 手順4）。

設計の担当が、筋 → 青帯の並び → 事実の表の行（値は空でよい、確認は「未確認」）の順に書いたあと、
まだ確かめていない行を裏取りの担当に分けて渡し、戻ったものを設計メモに戻す。

    python <skill>/scripts/facts.py split <work> [--n 2]   # まだの行を n 人分に分け、<work>/facts_1.md … を作る
    python <skill>/scripts/facts.py merge <work>           # facts_*.md の行を memo.md の3節に戻し、要点と違った行を facts_diff.md に

split：3節「事実と出典」の表で、確認が空か「未確認」の行を、表の順のまま n 個に分ける（表の順＝枚の順に近いので、話題が近い行が同じ人に行く）。
       各ファイルの先頭に裏取りのやり方を書くので、裏取りの担当への依頼は「<work>/facts_N.md の先頭のとおりに」だけでよい。
merge：facts_N.md の表の「番号」の行で、memo.md の同じ番号の行（主張・値・出典・確認）を置き換える。番号が「+」の行は表の最後に足す。
       「要点と合うか」が「違う」の行は facts_diff.md にまとめる（直しの担当が、その枝の青帯と筋を直す）。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))

SECTION = re.compile(r"(^##\s*3\.\s*事実と出典[^\n]*\n)(.*?)(?=^##\s|\Z)", re.S | re.M)
HEAD = ["番号", "主張", "値・式", "出典（書名・URL）", "確認", "使う枚", "要点と合うか", "検索（回数：2回目からの理由）"]
SEARCH_MAX = 5   # 1行の検索の上限。ソネットの試しで、1人の裏取りの担当が1行を何度も調べ直し、呼び出し62回・キャッシュの読み680万になった

HOWTO = """# 裏取り（{name}・{k}/{n}）

あなたは裏取りの担当です。ユーザーには質問しません。下の表の行を、上から1行ずつ確かめて、**1行終えるごとに、このファイルのその行だけを書き換える**
（ファイル全体を書き直さない。全体を書くと、そのたびに表の全文が会話に積み上がる。途中で止まっても、確かめた行は残る）。ほかのファイルは書かない。設計メモ（memo.md）は、行の意味が分からないときだけ2節を読む。

1行ごとに：
- **値・式**を確かめて書く。**出典**は、ほかの人があとで同じ資料を開ける形で（URL・「題名」・発行者と年・頁や条番号）。「厚生労働省」だけ、は不可
- **時とともに変わる事実**（制度の版・統計・法令・料金・数）は、最新の版を先に探す（検索語に今年の年と「最新」「改定」を入れ、
  公式のページで版と改定日を確かめてから値を拾う）。出典に版か年（「Ver.3.0（2023年4月）」「2026年3月31日現在」）を書く
- **確認**：○＝出典で確かめた／△＝出典どうしで値が違う・諸説あり（違いを値の欄に）／×＝確かめられなかった
- **要点と合うか**：設計の担当が置いた値・言い方（主張と値の欄の今の中身）と、使う枚の青帯（表の下）が言っていることに合うか。「合う」か「違う：〈何がどう違うか〉」。
  違うときは、表の値は確かめた値に直す（直しの担当が、その行を使う枚の青帯と筋を直す）
- 行に無いが、使う枚の話に要る新しい事実（新しい版がある、など）を見つけたら、番号を「+」にして表の最後に足す
- PDF は要る頁だけ読む。検索の結果を全部覚えておかない（表に要る所だけ拾う）
- **検索は1行につき、1回目は自由、2回目からは、検索する前に「検索」の欄に理由を書く**（何が足りなかったか：一次資料が無い・版が古い・値が出典どうしで違う など）。
  欄の書き方は「3：2 一次資料が無い／3 最新版が要る」（回数：何回目と理由を ／ で）。1回だけなら「1」
- **5回まで**。5回で確かめられなければ、6回目はせずに、確認を「×（5回で確かめられず）」にして次の行へ進む（その行のために長く調べ続けない）

終えたら「○ n・△ n・× n、違う n 行」と、違う行の番号と一言だけを、10行までで返す。

"""


def rows_of(table_text: str):
    lines = [l for l in table_text.splitlines() if l.strip().startswith("|")]
    if len(lines) < 2:
        return None, []
    cells = [[c.strip() for c in l.strip().strip("|").split("|")] for l in lines]
    return cells[0], [r for r in cells[2:] if any(c for c in r)]


def memo_facts(memo: str):
    m = SECTION.search(memo)
    if not m:
        raise SystemExit("memo.md に「## 3. 事実と出典」の節が無い")
    head, rows = rows_of(m.group(2))
    if head is None:
        raise SystemExit("3節に表が無い（| 主張 | 値・式 | 出典（書名・URL） | 確認 |）")
    return m, head, rows


def uses(memo: str) -> dict:
    """{事実の番号: [枚の番号]}：2節の表の〔事実N〕から。"""
    out = {}
    sec = re.search(r"^##\s*2\.[^\n]*\n(.*?)(?=^##\s|\Z)", memo, re.S | re.M)
    for line in (sec.group(1).splitlines() if sec else []):
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if not line.strip().startswith("|") or not c or not c[0].isdigit():
            continue
        for k in re.findall(r"事実\s*(\d+)", line):
            if int(c[0]) not in out.setdefault(int(k), []):
                out[int(k)].append(int(c[0]))
    return out


# 「一般」の行でも、これがあれば確かめる（数値・年・版・制度・統計・記録は、知っているつもりで外しやすい）
RISKY = re.compile(r"[0-9０-９]|[一二三四五六七八九十百千万億]+(?:年|人|件|種|頭|個|倍|割|%|％)|年|％|%|円|版|法|条|制度|基準|統計|最新|記録|世界一|最大|最小|初め|最初")
PER_CHECKER = 6   # 1人に渡す行の目安。これ以下なら1人


def unchecked(row, i_ok) -> bool:
    """まだ確かめていない行（確認が空か「未確認」）。○・△・× や「図に（例）と書く」などは、決まった行として扱う。
    「一般」（設計の担当が付ける：教科書に必ず載る、数値も年も無い定性的な事実）は確かめない。ただし数値・年・制度などを含めば確かめる。"""
    v = row[i_ok].strip() if len(row) > i_ok else ""
    if "一般" in v:
        return bool(RISKY.search(" ".join(row[:i_ok])))
    return v in ("", "-", "—") or "未確認" in v


def headlines(memo: str) -> dict:
    """{枚の番号: 青帯}：2節の表から。"""
    import structures
    rows = structures._plan_table(memo, "memo") or []
    return {k: c for k, c in (structures._conclusion_cells(rows) or {}).items() if c and c not in ("—", "-")}


def split(work: Path, n: int):
    memo = (work / "memo.md").read_text(encoding="utf-8")
    _, head, rows = memo_facts(memo)
    i_ok = next((k for k, h in enumerate(head) if "確認" in h), 3)
    use = uses(memo)
    todo = [(k + 1, r) for k, r in enumerate(rows) if unchecked(r, i_ok)]
    general = [k + 1 for k, r in enumerate(rows) if len(r) > i_ok and "一般" in r[i_ok]]
    forced = [no for no, r in todo if len(r) > i_ok and "一般" in r[i_ok]]
    if general:
        print(f"「一般」の行 {len(general) - len(forced)} 件は確かめない" +
              (f"（事実 {'・'.join(map(str, forced))} は「一般」でも数値・年・制度などを含むので確かめる）" if forced else ""))
    if not todo:
        print("確かめる行が無い（確認が空・未確認の行が無い）。裏取りの担当は要らない")
        return []
    n = min(n, -(-len(todo) // PER_CHECKER))   # 行が少なければ1人（会話の始めの読み込みを2人分しない）
    for old in work.glob("facts_*.md"):
        if old.name != "facts_diff.md":
            old.unlink()
    n = max(1, min(n, len(todo)))
    size = -(-len(todo) // n)
    out = []
    for k in range(n):
        part = todo[k * size:(k + 1) * size]
        if not part:
            continue
        p = work / f"facts_{k + 1}.md"
        lines = [HOWTO.format(name=work.name, k=k + 1, n=n), "| " + " | ".join(HEAD) + " |", "|" + "---|" * len(HEAD)]
        for no, r in part:
            r = (r + [""] * 4)[:4]
            lines.append("| " + " | ".join([str(no), *r, "・".join(map(str, use.get(no, []))) or "—", "", ""]) + " |")
        used = sorted({s for no, _ in part for s in use.get(no, [])})
        if used:
            heads = headlines(memo)
            lines += ["", "## 使う枚の青帯（その事実で何を言うか。合うかを決める手がかり）", ""]
            lines += [f"- {s}枚目：{heads.get(s, '（青帯なし）')}" for s in used]
        p.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
        out.append(p)
        print(f"{p.name}：{len(part)} 行（事実 {part[0][0]}〜{part[-1][0]}）")
    print(f"裏取りの担当を {len(out)} 人、同時に起動する。依頼は「<work>/facts_N.md の先頭のとおりに裏を取る」。"
          f"全員が戻ったら `facts.py merge {work.as_posix()}`")
    return out


def search_problem(cell: str) -> str | None:
    """「検索」の欄（「3：2 一次資料が無い／3 最新版」）：回数が上限を超えた・2回目からの理由が足りない、なら説明の文。空・1回は None。"""
    cell = (cell or "").strip()
    m = re.match(r"(\d+)", cell)
    if not m:
        return None
    n = int(m.group(1))
    if n > SEARCH_MAX:
        return f"{n}回（{SEARCH_MAX}回を超えた）"
    reasons = [x for x in re.split(r"[／/]", cell[m.end():].lstrip("：: ")) if x.strip()]
    if n >= 2 and len(reasons) < n - 1:
        return f"{n}回なのに、2回目からの理由が {len(reasons)} 個"
    return None


def merge(work: Path):
    memo_p = work / "memo.md"
    memo = memo_p.read_text(encoding="utf-8")
    m, head, rows = memo_facts(memo)
    files = sorted(p for p in work.glob("facts_*.md") if p.name != "facts_diff.md")
    if not files:
        raise SystemExit("facts_*.md が無い（先に facts.py split）")
    width = len(head)
    rows = [(r + [""] * width)[:width] for r in rows]
    diffs, added, replaced, search_bad = [], 0, 0, []
    for f in files:
        h, rs = rows_of(f.read_text(encoding="utf-8"))
        if h is None:
            continue
        col = {name: next((k for k, x in enumerate(h) if x.startswith(name)), None) for name in ("番号", "主張", "値", "出典", "確認", "使う枚", "要点", "検索")}
        for r in rs:
            get = (lambda key: r[col[key]].strip() if col[key] is not None and col[key] < len(r) else "")
            new = [get("主張"), get("値"), get("出典"), get("確認")] + [""] * max(0, width - 4)
            no = get("番号")
            if no.isdigit() and 1 <= int(no) <= len(rows):
                rows[int(no) - 1] = new[:width]
                replaced += 1
                label = no
            else:
                rows.append(new[:width])
                added += 1
                label = str(len(rows))
            sp = search_problem(get("検索"))
            if sp:
                search_bad.append(f"事実{get('番号') or '?'}：{sp}")
            fit = get("要点")
            if fit.startswith("違") or (no and not no.isdigit()):
                diffs.append(f"- 事実{label}（使う枚：{get('使う枚') or '—'}）：{get('主張')}｜{get('値')}｜{fit or '新しく足した行'}")
    table = ["| " + " | ".join(head) + " |", "|" + "---|" * width] + ["| " + " | ".join(r) + " |" for r in rows]
    body = m.group(2)
    lines = body.splitlines()
    first = next(k for k, l in enumerate(lines) if l.strip().startswith("|"))
    last = first
    while last + 1 < len(lines) and lines[last + 1].strip().startswith("|"):
        last += 1
    new_body = "\n".join(lines[:first] + table + lines[last + 1:]) + ("\n" if body.endswith("\n") else "")
    memo_p.write_text(memo[:m.start(2)] + new_body + memo[m.end(2):], encoding="utf-8", newline="\n")
    i_ok = next((k for k, x in enumerate(head) if "確認" in x), 3)
    cnt = {s: sum(r[i_ok].startswith(s) for r in rows) for s in ("○", "△", "×")}
    rest = sum(unchecked(r, i_ok) for r in rows)
    dp = work / "facts_diff.md"
    if diffs:
        dp.write_text("# 裏取りで、設計の担当の値・言い方と違った行と、新しく足した行\n\n"
                      "直しの担当は、行ごとに、使う枚の青帯・本文の要点と、話の筋（1節）を確かめた値に合わせて直す。\n\n"
                      + "\n".join(diffs) + "\n", encoding="utf-8", newline="\n")
    elif dp.exists():
        dp.unlink()
    print(f"memo.md の3節に戻した：置き換え {replaced} 行・足した {added} 行（○ {cnt['○']}・△ {cnt['△']}・× {cnt['×']}"
          + (f"・まだ {rest}" if rest else "") + "）")
    print(f"違った行・足した行：{len(diffs)} 件" + ("（facts_diff.md。直しの担当に渡す）" if diffs else ""))
    if search_bad:   # 検索の決まり（2回目からは理由、5回まで）を守っていない行
        over = [x for x in search_bad if "回を超えた" in x]
        print(("✘ " if over else "△ ") + "検索の決まりを守っていない行：" + "；".join(search_bad[:6])
              + "（1行の検索は、2回目からは理由を書いてから、5回まで。超えた行は確かめ方を見直す）")
    return diffs


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    if len(a) < 2 or a[0] not in ("split", "merge"):
        print(__doc__)
        return 2
    work = Path(a[1])
    if work.name == "memo.md":
        work = work.parent
    if a[0] == "split":
        n = int(a[a.index("--n") + 1]) if "--n" in a else 2
        split(work, n)
    else:
        merge(work)
    return 0


if __name__ == "__main__":
    sys.exit(main())
