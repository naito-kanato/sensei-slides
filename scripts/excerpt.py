"""資料の、構成案の「範囲」に当たる所を抜き出す（scaffold.py のカードに入れる。書き手が資料全体を探さずに済ませる）。

    python <skill>/scripts/excerpt.py <資料.pdf|資料.txt> "III. Detectors, Fig. 3"   # 抜き出しを出す（確かめ用）

範囲の書き方（構成案の「範囲」の列。「,」「、」で区切って並べてよい）
  論文の節     「III. Detectors」「Sec. V」 → その見出しの行から、次の同じ形の見出しの前まで
  図・表       「Fig. 3」「Fig. 1 上段」「Table I」 → 図・表の説明文（FIG. 3. …）から
  頁           「p.12」「pp.12-13」「12頁」 → PDF の頁（1から数える）
  節の番号     「3.2」「§3.2」「3.2節」 → 「3.2 」で始まる行から、次の同じ形の見出しの前まで
抜き出せなかった範囲は、書き手が資料を開いて読む（カードにそう書く）。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PART_MAX = 12000     # 1つの範囲から抜き出す字数の上限（論文の1節がおおよそ入る）
CARD_MAX = 15000     # 1枚のカードに入れる字数の上限
CAPTION_MAX = 3000    # 図・表の説明文の上限
ABSTRACT_MAX = 3000   # 要旨（最初の節の見出しより前）の上限
ROMAN = r"(?=[IVX])(?:X{0,3}(?:IX|IV|V?I{0,3}))"   # 空にならない（空だと「. 」で始まる行を見出しと取り違える）
SUFFIXES = (".pdf", ".txt", ".md")


def load(path: Path) -> str:
    """資料の文字（頁は \\f で区切る）。PDF は PyMuPDF で。"""
    if path.suffix.lower() == ".pdf":
        import fitz
        with fitz.open(path) as doc:
            return "\f".join(page.get_text() for page in doc)
    return path.read_text(encoding="utf-8", errors="replace")


def find_source(work: Path):
    """作業フォルダか発表フォルダの 資料/ に、PDF・テキストが1つだけあればそれ。無い・2つ以上なら None。"""
    cands = []
    for d in (work / "資料", work.parents[1] / work.name / "資料", work.parents[1] / work.name / "資料" / "その他"):
        if d.is_dir():
            cands += [p for p in d.iterdir() if p.suffix.lower() in SUFFIXES and p.is_file()]
    return cands[0] if len(cands) == 1 else None


def _cut(text: str, start: int, end_pat, limit: int = PART_MAX) -> str:
    m = end_pat.search(text, start + 1) if end_pat is not None else None
    end = m.start() if m else len(text)
    return text[start:min(end, start + limit)].strip()


def one(text: str, token: str) -> str | None:
    t = token.strip()
    if not t or t in ("—", "-"):
        return None
    m = re.match(rf"^(?:Sec\.?\s*)?({ROMAN})\.?(?:\s|$)", t)
    if m and m.group(1):
        r = m.group(1)
        h = re.search(rf"^\s*{r}\.\s+[A-Z]", text, re.M)
        if h:
            return _cut(text, h.start(), re.compile(rf"^\s*(?!{r}\.){ROMAN}\.\s+[A-Z]", re.M))
    m = re.match(r"^(Fig\.?|FIG\.?|図)\s*(\d+)", t)
    if m:
        # 説明文（FIG. 1. ／ 図1：）を先に探す。本文中の「shown in Fig. 1.」から始めない
        h = (re.search(rf"FIG\.\s*{m.group(2)}\.", text) or re.search(rf"^\s*図\s*{m.group(2)}[.．:：\s]", text, re.M)
             or re.search(rf"(Fig\.|図)\s*{m.group(2)}[.．:：\s]", text))
        if h:   # 説明文の終わり（次の図の説明・節の見出し）まで。上段・下段の説明が後ろにあっても切らない
            return _cut(text, h.start(), re.compile(rf"(FIG\.|図)\s*\d+[.．:：]|^\s*{ROMAN}\.\s+[A-Z]", re.M), CAPTION_MAX)
    m = re.match(r"^(Table|TABLE|表)\s*([IVX\d]+)", t)
    if m:
        h = (re.search(rf"TABLE\s*{m.group(2)}\.", text) or re.search(rf"^\s*表\s*{m.group(2)}[.．:：\s]", text, re.M)
             or re.search(rf"(Table|表)\s*{m.group(2)}[.．:：\s]", text))
        if h:
            return text[h.start():h.start() + CAPTION_MAX].strip()
    m = re.match(r"^(?:pp?\.?\s*)?(\d+)\s*(?:[-–〜~]\s*(\d+))?\s*頁?$", t) if re.search(r"p\.|pp\.|頁", t) else None
    if m:
        pages = text.split("\f")
        a, b = int(m.group(1)), int(m.group(2) or m.group(1))
        return "\n".join(pages[i - 1] for i in range(a, b + 1) if 0 < i <= len(pages))[:PART_MAX].strip() or None
    m = re.match(r"^§?\s*(\d+(?:\.\d+)+)\s*節?$", t)
    if m:
        h = re.search(rf"^\s*§?{re.escape(m.group(1))}\s+\S", text, re.M)
        if h:
            return _cut(text, h.start(), re.compile(rf"^\s*§?(?!{re.escape(m.group(1))}\s)\d+(?:\.\d+)+\s+\S", re.M))
    return None


def abstract(text: str) -> str:
    """要旨：最初の節の見出し（I. … か 1 …）より前の所。数値の要約が入っていることが多いので、どの枚のカードからも指す。"""
    h = re.search(rf"^\s*I\.\s+[A-Z]|^\s*1\.?\s+\S", text, re.M)
    head = text[:h.start()] if h else text[:ABSTRACT_MAX]
    return head.strip()[:ABSTRACT_MAX]


def pieces(text: str, rng: str):
    """([(範囲の語, 抜き出した文)], 抜き出せなかった範囲のリスト)。同じ所は1回だけ。"""
    out, miss, seen = [], [], set()
    for tok in re.split(r"[,，、;；]", rng or ""):
        tok = re.sub(r"[（(].*?[)）]", "", tok).strip()
        if not tok:
            continue
        got = one(text, tok)
        if got and got[:200] not in seen:
            seen.add(got[:200])
            out.append((tok, got))
        elif not got:
            miss.append(tok)
    return out, miss


def excerpt(text: str, rng: str):
    """(抜き出した文, 抜き出せなかった範囲のリスト)。"""
    out, miss, seen = [], [], set()
    for tok in re.split(r"[,，、;；]", rng or ""):
        tok = re.sub(r"[（(].*?[)）]", "", tok).strip()
        if not tok:
            continue
        got = one(text, tok)
        if got and got[:200] not in seen:
            seen.add(got[:200])
            out.append(f"〔{tok}〕\n{got}")
        elif not got:
            miss.append(tok)
    body = "\n\n".join(out)
    if len(body) > CARD_MAX:
        body = body[:CARD_MAX] + "\n…（ここまで。続きが要るときだけ資料を開く）"
    return body, miss


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2:
        print(__doc__)
        return 2
    body, miss = excerpt(load(Path(argv[0])), argv[1])
    print(body or "（抜き出せなかった）")
    if miss:
        print("\n抜き出せなかった範囲：" + "・".join(miss))
    return 0


if __name__ == "__main__":
    sys.exit(main())
