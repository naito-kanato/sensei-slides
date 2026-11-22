"""講座の設計メモの「## 3. 事実と出典」の表を読む（check_memo・next_step・scaffold が使う）。

設計の担当は、事実の行を設計メモの3節に書き、その場で確かめて確認の欄（○・△・×・一般）を埋める（references/course.md 手順4）。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

SECTION = re.compile(r"(^##\s*3\.\s*事実と出典[^\n]*\n)(.*?)(?=^##\s|\Z)", re.S | re.M)


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


# 「一般」の行でも、これがあれば確かめる（数値・年・版・制度・統計・記録は、知っているつもりで外しやすい）
RISKY = re.compile(r"[0-9０-９]|[一二三四五六七八九十百千万億]+(?:年|人|件|種|頭|個|倍|割|%|％)|年|％|%|円|版|法|条|制度|基準|統計|最新|記録|世界一|最大|最小|初め|最初")


def unchecked(row, i_ok) -> bool:
    """まだ確かめていない行（確認が空か「未確認」）。○・△・× や「図に（例）と書く」などは、決まった行として扱う。
    「一般」（設計の担当が付ける：教科書に必ず載る、数値も年も無い定性的な事実）は確かめない。ただし数値・年・制度などを含めば確かめる。"""
    v = row[i_ok].strip() if len(row) > i_ok else ""
    if "一般" in v:
        return bool(RISKY.search(" ".join(row[:i_ok])))
    return v in ("", "-", "—") or "未確認" in v
