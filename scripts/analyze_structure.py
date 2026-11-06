"""手持ちのデッキの「本文の形」（文字の塊の組み方）を数える。見た目を数える analyze_template.py の、組み方版。

    python analyze_structure.py <デッキ.pptx> [<デッキ2.pptx> ...] [--skip 1,5-7]   # 結果の表と、設定の一覧に書く1行
    python analyze_structure.py スライドテンプレート/                                  # フォルダの pptx を全部

数えるもの（本文のスライドのうち、その形を使った枚の割合。1枚に複数の形があってよい）
  帰結（「⇒」で始まる行・赤字の結論）、ラベル（「〇〇：」で終わる行・下線の小見出し）、展開（横の太矢印）、
  縦の結論（下向きの太矢印）、場合分け（「〇〇以下：／以上：」・①②③の条件）、問い（「？」）、手順（1. 2. 3.・①②③）、
  箇条（行頭の中黒）、結論の置き場（下の帯・塗りの囲み・上の結論の一文）、赤字の枚の割合、1枚の文字の塊の数（中央値）
各デッキの1枚目は表紙として数えない。見にくい枚・古い枚は数えないほうがよい（--skip で外す。番号は全デッキ共通）。割合は、構成案の「本文の形」を選ぶときの目安にする
（設定の一覧の「本文の形の割合」。references/structures.md）。AI の印象ではなく部品が数えるので、どの AI でも同じ結果になる。
"""
from __future__ import annotations

import re
import statistics as st
import sys
from collections import Counter
from pathlib import Path

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from structures import FORM_KEYS, detect_forms  # noqa: E402

RED = {"FF0000", "C00000", "E60012", "D62D20", "D9480F", "C62828", "C0392B", "C8102E", "B42318"}


def walk(shapes):
    for sh in shapes:
        if sh.shape_type == MSO_SHAPE_TYPE.GROUP:
            yield from walk(sh.shapes)
        else:
            yield sh


def _rgb(run):
    try:
        return str(run.font.color.rgb) if run.font.color and run.font.color.type is not None else ""
    except Exception:
        return ""


def slide_forms(slide, W, H):
    """1枚の本文の形の集合、結論の置き場、赤字の有無、文字の塊の数。本文でない枚（表紙・図だけ）は None。"""
    sh = list(walk(slide.shapes))
    texts = [s for s in sh if getattr(s, "has_text_frame", False) and s.has_text_frame and s.text_frame.text.strip()
             and s.top is not None and s.top < 0.86 * H
             and not (s.is_placeholder and "TITLE" in str(s.placeholder_format.type))]
    body = "\n".join(s.text_frame.text for s in texts)
    if len(re.sub(r"\s", "", body)) < 15:
        return None
    paras = [p for s in texts for p in s.text_frame.paragraphs if p.text.strip()]
    found = set(detect_forms(slide))          # zemi.py の部品で作ったデッキ（部品の名前）
    if any(p.text.strip().startswith(("⇒", "→", "⇨")) for p in paras):
        found.add("帰結")
    if any(re.search(r"[：:]\s*$", p.text.strip()) for p in paras) or any(
            r.font.underline and len(r.text.strip()) >= 2 for p in paras for r in p.runs):
        found.add("ラベル")
    kinds = set()
    for s in sh:
        try:
            if s.shape_type == MSO_SHAPE_TYPE.AUTO_SHAPE:
                kinds.add(s.auto_shape_type.name)
        except Exception:
            pass
    if any("RIGHT" in k and "ARROW" in k for k in kinds):
        found.add("展開")
    if any("DOWN" in k and "ARROW" in k for k in kinds):
        found.add("縦の結論")
    if re.search(r"(以下|以上|を上回る|を超え|[<＜>＞]).{0,15}[：:]", body) or re.search(r"[①②③].{0,20}[<＜>＞]", body):
        found.add("場合分け")
    if re.search(r"[？?]", body):
        found.add("問い")
    if any(re.match(r"\s*([①②③④⑤]|[1-9][\.．)]\s)", p.text) for p in paras):
        found.add("手順")
    if any(p.text.strip().startswith(("・", "•")) for p in paras):
        found.add("箇条")
    red = any(_rgb(r) in RED for p in paras for r in p.runs)
    # 結論の置き場：下の帯（下 15% の全幅の塗り）・塗りの囲み（本文の下半分の淡い塗りの箱に文字）・上の結論の一文
    place = "なし"
    for s in sh:
        try:
            filled = s.fill.type == 1
        except Exception:
            filled = False
        if s.top is not None and s.top >= 0.86 * H and s.width and s.width > 0.6 * W and (filled or s.is_placeholder) and (filled or s.has_text_frame and s.text_frame.text.strip()):
            place = "下の帯"
    if place == "なし":
        for s in texts:
            try:
                if s.fill.type == 1 and s.top > 0.5 * H and s.width < 0.9 * W:
                    place = "塗りの囲み"
            except Exception:
                pass
    return found, place, red, len(texts)


def analyze(paths, skip=()):
    c, places, blocks = Counter(), Counter(), []
    n = red = 0
    for p in paths:
        prs = Presentation(p)
        W, H = prs.slide_width, prs.slide_height
        for i, sl in enumerate(prs.slides, 1):
            if i == 1 or i in skip:   # 1枚目は表紙として数えない
                continue
            r = slide_forms(sl, W, H)
            if r is None:
                continue
            found, place, is_red, nb = r
            n += 1
            c.update(found)
            places[place] += 1
            red += is_red
            blocks.append(nb)
    return dict(n=n, forms=c, places=places, red=red, blocks=st.median(blocks) if blocks else 0)


def parse_skip(s):
    out = set()
    for part in (s or "").split(","):
        if "-" in part:
            a, b = part.split("-")
            out |= set(range(int(a), int(b) + 1))
        elif part.strip():
            out.add(int(part))
    return out


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    skip = set()
    if "--skip" in argv:
        k = argv.index("--skip")
        skip = parse_skip(argv[k + 1])
        argv = argv[:k] + argv[k + 2:]
    paths = []
    for a in argv:
        q = Path(a)
        paths += sorted(q.glob("*.pptx")) if q.is_dir() else [q]
    paths = [p for p in paths if not p.name.startswith("~$")]
    if not paths:
        print(__doc__)
        return 2
    r = analyze(paths, skip)
    if not r["n"]:
        print("本文のスライドが見つからない")
        return 1
    print(f"本文のスライド {r['n']}枚（{len(paths)}本のデッキ）")
    print("| 本文の形 | 枚 | 割合 |")
    print("|---|---|---|")
    order = sorted(FORM_KEYS, key=lambda k: -r["forms"][k])
    for k in order:
        if r["forms"][k]:
            print(f"| {k} | {r['forms'][k]} | {r['forms'][k] / r['n'] * 100:.0f}% |")
    print(f"\n赤字のある枚：{r['red'] / r['n'] * 100:.0f}%　1枚の文字の塊：中央値 {r['blocks']:.0f}個")
    print("結論の置き場：" + "、".join(f"{k} {v / r['n'] * 100:.0f}%" for k, v in r["places"].most_common()))
    top = [f"{k} {r['forms'][k] / r['n'] * 100:.0f}%" for k in order if r["forms"][k] / r["n"] >= 0.1]
    print("\n設定の一覧（outline.md の ## オプション）に書く行：")
    print(f"- 本文の形の割合: {'、'.join(top)}（{r['n']}枚から。analyze_structure.py）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
