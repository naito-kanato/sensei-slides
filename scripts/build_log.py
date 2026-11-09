"""組みの記録：make_deck を回すたびに、枚ごとの指紋を <work>/build_log.jsonl に1行足す。

    python <skill>/scripts/build_log.py <work>     # 何回組んで、何枚に手を入れたか

指紋は枚ごとの図形の文字・位置（約1mm単位）・画像の中身から作る（発表者ノートは含めない）。
数えるもの
  - 組んだ回数（make_deck の回数）
  - 初回の組みから手を入れた枚
  - 検査が通ってから（ERROR 0・原稿と構成案どおりか ✘ 0 になった最初の回のあと。ふつうは完成後のレビューの後）手を入れた枚
check_done.py（渡す前の確認）が最後に1行で出す。作り方の手戻りを振り返るための記録で、合否には使わない。
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LOG = "build_log.jsonl"
GRID = 36000   # 約1mm（EMU）。これより小さい位置のずれは同じとみなす


def _shape_sig(sh) -> str:
    parts = [sh.name or "", str(round((sh.left or 0) / GRID)), str(round((sh.top or 0) / GRID)),
             str(round((sh.width or 0) / GRID)), str(round((sh.height or 0) / GRID))]
    if getattr(sh, "has_text_frame", False) and sh.has_text_frame:
        parts.append(sh.text_frame.text)
    if getattr(sh, "has_table", False) and sh.has_table:
        parts.append("|".join(c.text for r in sh.table.rows for c in r.cells))
    try:
        parts.append(sh.image.sha1)
    except Exception:
        pass
    if getattr(sh, "shapes", None) is not None and sh.shape_type == 6:   # グループ
        parts.extend(_shape_sig(s) for s in sh.shapes)
    return "\x1f".join(parts)


def signatures(pptx) -> list[str]:
    from pptx import Presentation
    prs = Presentation(str(pptx))
    return [hashlib.md5("\x1e".join(_shape_sig(sh) for sh in s.shapes).encode("utf-8")).hexdigest()[:12]
            for s in prs.slides]


def same_as_before(recs: list, i: int) -> bool:
    """i 番目の記録が、1つ前の記録とスライドの中身（枚ごとの指紋）がまったく同じか（何も直さずにもう一度回した）。"""
    return i > 0 and bool(recs[i].get("sig")) and recs[i].get("sig") == recs[i - 1].get("sig")


def append(work: Path, pptx: Path, err=None, warn=None, x=None, final: bool = False) -> int:
    """1回分を足し、何回目かを返す。記録できなくても組みは止めない（0 を返す）。final＝上限のあとの最後の確かめ（回数に数えない）。"""
    try:
        rec = {"t": time.strftime("%Y-%m-%d %H:%M:%S"), "pptx": Path(pptx).name, "sig": signatures(pptx),
               "error": err, "warn": warn, "x": x}
        if final:
            rec["final"] = True
        p = Path(work) / LOG
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return sum(1 for _ in p.open(encoding="utf-8"))
    except Exception:
        return 0


def load(work: Path) -> list[dict]:
    p = Path(work) / LOG
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except ValueError:
            pass
    return out


def _changed(a: list[str], b: list[str]) -> list[int]:
    """a から b で変わった枚の番号（b の番号。増えた枚も入れる。減った枚は数だけ末尾に足す）。"""
    out = [i for i in range(1, len(b) + 1) if i > len(a) or a[i - 1] != b[i - 1]]
    return out + [0] * max(0, len(a) - len(b))


def summary(work: Path) -> dict | None:
    recs = load(work)
    if not recs:
        return None
    first, last = recs[0]["sig"], recs[-1]["sig"]
    clean = next((k for k, r in enumerate(recs) if r.get("error") == 0 and r.get("x") == 0), None)
    return {"runs": len(recs), "slides": len(last), "since_first": _changed(first, last),
            "clean_run": None if clean is None else clean + 1,
            "after_clean": None if clean is None else _changed(recs[clean]["sig"], last)}


def _nums(xs: list[int]) -> str:
    named = [str(i) for i in xs if i]
    gone = sum(1 for i in xs if not i)
    return "・".join(named) + (f"（ほか {gone}枚を外した）" if gone else "")


def line(work: Path) -> str | None:
    s = summary(work)
    if not s:
        return None
    a = f"make_deck {s['runs']}回。初回の組みから手を入れた枚 {len(s['since_first'])}/{s['slides']}"
    if s["since_first"]:
        a += f"（{_nums(s['since_first'])}）"
    if s["clean_run"] is None:
        a += "。検査が通った回はまだ無い"
    else:
        b = s["after_clean"]
        a += f"。検査が通った {s['clean_run']}回目のあとに手を入れた枚 {len(b)}" + (f"（{_nums(b)}）" if b else "")
    return a


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print(__doc__)
        return 1
    t = line(Path(argv[0]))
    print(t or f"{Path(argv[0]) / LOG} が無い（make_deck.py を回すと記録が始まる）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
