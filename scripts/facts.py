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
HEAD = ["番号", "主張", "値・式", "出典（書名・URL）", "確認", "使う枚", "要点と合うか"]

HOWTO = """# 裏取り（{name}・{k}/{n}）

あなたは裏取りの担当です。ユーザーには質問しません。下の表の行を、上から1行ずつ確かめて、**1行終えるごとにこのファイルを書き直す**
（途中で止まっても、確かめた行は残る）。ほかのファイルは書かない。設計メモ（memo.md）は、行の意味が分からないときだけ2節を読む。

1行ごとに：
- **値・式**を確かめて書く。**出典**は、ほかの人があとで同じ資料を開ける形で（URL・「題名」・発行者と年・頁や条番号）。「厚生労働省」だけ、は不可
- **時とともに変わる事実**（制度の版・統計・法令・料金・数）は、最新の版を先に探す（検索語に今年の年と「最新」「改定」を入れ、
  公式のページで版と改定日を確かめてから値を拾う）。出典に版か年（「Ver.3.0（2023年4月）」「2026年3月31日現在」）を書く
- **確認**：○＝出典で確かめた／△＝出典どうしで値が違う・諸説あり（違いを値の欄に）／×＝確かめられなかった
- **要点と合うか**：設計の担当が置いた値・言い方（主張と値の欄の今の中身）と合うか。「合う」か「違う：〈何がどう違うか〉」。
  違うときは、表の値は確かめた値に直す（直しの担当が、その行を使う枚の青帯と筋を直す）
- 行に無いが、使う枚の話に要る新しい事実（新しい版がある、など）を見つけたら、番号を「+」にして表の最後に足す
- PDF は要る頁だけ読む。検索の結果を全部覚えておかない（表に要る所だけ拾う）

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


def unchecked(row, i_ok) -> bool:
    """まだ確かめていない行（確認が空か「未確認」）。○・△・× や「図に（例）と書く」などは、決まった行として扱う。"""
    v = row[i_ok].strip() if len(row) > i_ok else ""
    return v in ("", "-", "—") or "未確認" in v


def split(work: Path, n: int):
    memo = (work / "memo.md").read_text(encoding="utf-8")
    _, head, rows = memo_facts(memo)
    i_ok = next((k for k, h in enumerate(head) if "確認" in h), 3)
    use = uses(memo)
    todo = [(k + 1, r) for k, r in enumerate(rows) if unchecked(r, i_ok)]
    if not todo:
        print("確かめる行が無い（確認が空・未確認の行が無い）。裏取りの担当は要らない")
        return []
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
            lines.append("| " + " | ".join([str(no), *r, "・".join(map(str, use.get(no, []))) or "—", ""]) + " |")
        p.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
        out.append(p)
        print(f"{p.name}：{len(part)} 行（事実 {part[0][0]}〜{part[-1][0]}）")
    print(f"裏取りの担当を {len(out)} 人、同時に起動する。依頼は「<work>/facts_N.md の先頭のとおりに裏を取る」。"
          f"全員が戻ったら `facts.py merge {work.as_posix()}`")
    return out


def merge(work: Path):
    memo_p = work / "memo.md"
    memo = memo_p.read_text(encoding="utf-8")
    m, head, rows = memo_facts(memo)
    files = sorted(p for p in work.glob("facts_*.md") if p.name != "facts_diff.md")
    if not files:
        raise SystemExit("facts_*.md が無い（先に facts.py split）")
    width = len(head)
    rows = [(r + [""] * width)[:width] for r in rows]
    diffs, added, replaced = [], 0, 0
    for f in files:
        h, rs = rows_of(f.read_text(encoding="utf-8"))
        if h is None:
            continue
        col = {name: next((k for k, x in enumerate(h) if x.startswith(name)), None) for name in ("番号", "主張", "値", "出典", "確認", "使う枚", "要点")}
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
