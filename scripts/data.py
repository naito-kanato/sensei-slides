"""講座の「数字を探す」段のデータ：数字を探す担当が data_N.md に書いた、比べられる数字の組を扱う。

    python <skill>/scripts/data.py merge <work>    # data_*.md を設計メモ（発表は構成案）の「3b. データ」節に入れる（データ1・データ2…と番号を振る）
    python <skill>/scripts/data.py check <work>    # data_*.md（か設計メモの3b節）の書き方を確かめる

数字は「話の裏付け」ではなく、筋の「しかし」（思い込みが崩れる所）を作る材料として扱う。だから設計の前に探す。
講座は数字を探す担当2人が Web から、発表は設計の担当が資料の表・図から（出典は「Table 2」「Fig. 3」「p.12」、確認は資料で○）。
1組の書き方（data_N.md に、組ごとに1つ。3組まで）：

    ## データ：<題>
    - 驚き：<思い込みとどう違うか・何が意外か>
    - 問いの候補：<…か？>
    - 単位：<％・件・床…>／分母：<何に対する割合か（割合でなければ —）>／時点：<2026年3月31日現在 など>
    - 出典：<「題名」発行者 年 URL 頁>
    - 確認：○（出典で確かめた）／△（出典どうしで違う。値の欄に両方）
    - 別の読み方：<この数字が驚きに見えない読み方（極端な条件だけ・分母が違う・資料が選んだ項目だけ・古い時点 など）>
    | 区分 | 値 |
    |---|---|
    | <区分1> | <数> |
    | <区分2> | <数> |

列は増やしてよい（| 区分 | 2017 | 2019 | のように、時点ごとの列）。値は数（％や単位は「単位」の行に書く）。
比べられる組が無いとき（理論の導入・手順の習得・定義から応用へ、のような回）は、無理に出さずに次を書く。これも正規の結果：

    ## 見つからなかった：<理由（統計の対象でない・比べられる区分が無い など）>
    - 調べたこと：<立てた問いの候補と、検索の回数>

図の案は、このデータを「目的：種類：データN」で指す（例「比べる：棒グラフ：データ2」）。カードが、その枚の書き手にデータの表を写す。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SECTION = "## 3b. データ"
FIELDS = ("驚き", "問いの候補", "単位", "分母", "時点", "出典", "確認", "別の読み方")
REQUIRED = ("驚き", "単位", "時点", "出典", "確認", "別の読み方")
NOT_FOUND = re.compile(r"^##+\s*見つからなかった\s*[：:]\s*(.*?)\s*$(.*?)(?=^##+\s|\Z)", re.M | re.S)
NF_LINE = "- 見つからなかった："
REF = re.compile(r"データ\s*(\d+)")
NUM = re.compile(r"^[−\-+]?[\d,]+(\.\d+)?$|^約?[\d,.]+[〜~][\d,.]+$")


def parse(text: str) -> list[dict]:
    """「## データ」の見出しごとに1組。{title, fields{...}, head[...], rows[[...]]}。"""
    out = []
    for m in re.finditer(r"^##+\s*データ\s*\d*\s*[：:]\s*(.+?)\s*$(.*?)(?=^##+\s|\Z)", text, re.M | re.S):
        body = m.group(2)
        f = {}
        for line in body.splitlines():
            line = line.strip()
            if not line.startswith("-"):
                continue
            for part in re.split(r"[／/](?=\s*(?:" + "|".join(FIELDS) + r")\s*[：:])", line.lstrip("- ")):
                mm = re.match(r"\s*(" + "|".join(FIELDS) + r")\s*[：:]\s*(.*)$", part)
                if mm:
                    f[mm.group(1)] = mm.group(2).strip()
        rows = [[c.strip() for c in l.strip().strip("|").split("|")] for l in body.splitlines()
                if l.strip().startswith("|") and not re.match(r"^\|\s*:?-", l.strip())]
        out.append({"title": m.group(1), "fields": f, "head": rows[0] if rows else [], "rows": rows[1:]})
    return out


def problems(d: dict) -> list[str]:
    """1組の書き方の抜け（✘ にするもの）。"""
    p = [f"「{k}」が無い" for k in REQUIRED if not d["fields"].get(k) or d["fields"][k] in ("—", "-")]
    if len(d["rows"]) < 2:
        p.append("比べる区分が2つ未満（表に2行以上）")
    bad = [c for r in d["rows"] for c in r[1:] if c and not NUM.match(c.replace("％", "").replace("%", "").strip())]
    if bad:
        p.append(f"値が数でない：{'・'.join(bad[:3])}（単位は「単位」の行に。値の欄は数だけ）")
    return p


def not_found(text: str) -> list[tuple[str, str]]:
    """data_N.md の「## 見つからなかった：理由」：[(理由, 調べたこと)]。"""
    out = []
    for m in NOT_FOUND.finditer(text):
        tried = re.search(r"^\s*-\s*調べたこと\s*[：:]\s*(.*)$", m.group(2), re.M)
        out.append((m.group(1).strip(), tried.group(1).strip() if tried else ""))
    return out


def not_found_problems(reason: str, tried: str) -> list[str]:
    return ([] if reason else ["理由が無い"]) + ([] if tried else ["「調べたこと」（問いの候補と検索の回数）が無い"])


def memo_not_found(text: str) -> list[str]:
    """設計メモの3b節に merge が書いた「見つからなかった」の行。"""
    return [l[len(NF_LINE):].strip() for l in (section(text) or "").splitlines() if l.startswith(NF_LINE)]


def files(work: Path) -> list[Path]:
    return sorted(Path(work).glob("data_[0-9]*.md"))


def section(text: str) -> str | None:
    m = re.search(r"^" + re.escape(SECTION) + r"[^\n]*\n.*?(?=^##\s|\Z)", text, re.M | re.S)   # 次の「## 」見出しまで（### データN は中身）
    return m.group(0) if m else None


def datasets(text: str) -> dict[int, dict]:
    """設計メモの3b節の {番号: 組}（見出しの「データN：」の N）。"""
    sec = section(text) or ""
    out = {}
    parts = re.split(r"(?m)^###\s*データ\s*(\d+)\s*[：:]\s*(.*)$", sec)   # [前, 番号, 題, 中身, 番号, 題, 中身, …]
    for i in range(1, len(parts) - 2, 3):
        one = parse(f"## データ：{parts[i + 1]}\n{parts[i + 2]}")
        if one:
            out[int(parts[i])] = one[0]
    return out


def render(n: int, d: dict) -> str:
    f = d["fields"]
    lines = [f"### データ{n}：{d['title']}"]
    for k in FIELDS:
        if f.get(k):
            lines.append(f"- {k}：{f[k]}")
    if d["head"]:
        lines.append("| " + " | ".join(d["head"]) + " |")
        lines.append("|" + "---|" * len(d["head"]))
        lines += ["| " + " | ".join(r) + " |" for r in d["rows"]]
    return "\n".join(lines)


def merge(work: Path) -> int:
    """data_*.md の組を、設計メモの3b節に番号つきで入れる（前の3b節は置き換える）。入れた組の数。"""
    work = Path(work)
    memo = work / "memo.md" if (work / "memo.md").exists() or not (work / "outline.md").exists() else work / "outline.md"
    if not memo.exists():
        raise SystemExit(f"✘ {memo} が無い（先に設計メモ・構成案の骨を書く）")
    texts = [f.read_text(encoding="utf-8") for f in files(work)]
    sets = [d for t in texts for d in parse(t)]
    nfs = [x for t in texts for x in not_found(t)]
    body = (SECTION + "（data.py merge が data_N.md から入れる。図の案から「データN」で指す。値・単位・注記はこのとおりに描く）\n\n"
            + "\n\n".join(render(i, d) for i, d in enumerate(sets, 1))
            + ("\n\n" if sets and nfs else "")
            + "\n".join(f"{NF_LINE}{r}（調べたこと：{t}）" for r, t in nfs) + "\n\n")
    raw = memo.read_text(encoding="utf-8")
    old = section(raw)
    if old:
        raw = raw.replace(old, body)
    else:
        m = re.search(r"^##\s*4[.．]", raw, re.M) or re.search(r"^##\s*構成\s*$", raw, re.M)   # 設計メモは4節の前、構成案は構成の表の前
        raw = raw[:m.start()] + body + raw[m.start():] if m else raw.rstrip() + "\n\n" + body
    memo.write_text(raw, encoding="utf-8")
    return len(sets)


def refs(cell: str) -> list[int]:
    return [int(x) for x in REF.findall(cell or "")]


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) < 2 or argv[0] not in ("merge", "check"):
        print(__doc__)
        return 2
    work = Path(argv[1])
    if argv[0] == "merge":
        n = merge(work)
        nf = sum(len(not_found(f.read_text(encoding="utf-8"))) for f in files(work))
        print(f"設計メモの3b節に {n} 組を入れた（データ1〜{n}）。強い組だけ、図の案から「目的：種類：データN」で指す" if n else
              "比べられる数字の組は見つからなかった（理由を3b節に書いた）。筋の しかし は、データ無しの意外・疑い・限りで組む" if nf else
              "data_N.md に組が無い（数字を探す担当の結果を待つ）")
        return 0
    bad = 0
    for f in files(work):
        for r, t in not_found(f.read_text(encoding="utf-8")):
            p = not_found_problems(r, t)
            bad += bool(p)
            print(("✘ " if p else "・ ") + f"{f.name}：見つからなかった（{r or '理由なし'}）" + ("：" + "・".join(p) if p else ""))
        for d in parse(f.read_text(encoding="utf-8")):
            p = problems(d)
            bad += bool(p)
            print(("✘ " if p else "✔ ") + f"{f.name}「{d['title']}」" + ("：" + "・".join(p) if p else ""))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
