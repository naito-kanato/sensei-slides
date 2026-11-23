"""原稿が言う色が、その枚の図・図形にあるか（原稿と画面の食い違い）。渡す前の確認（check_done.py）と make_deck.py が呼ぶ。

    python <skill>/scripts/check_colors.py "<資料名>_スライド.pptx"          # 食い違った枚だけ出す
    python <skill>/scripts/check_colors.py "<資料名>_スライド.pptx" --all    # 原稿の色の語と、枚ごとの図の色をすべて出す

見本の発表で、原稿が「一番下の赤い棒が…」と言うのに、棒グラフの強調の棒は青かった。伏せた採点者2人とも
「原稿と画面の食い違い」と減点したのに、どの検査も拾っていなかった。
  1. 原稿（pptx の発表者ノート）から、色の語＋図の部品の語の組を拾う（赤い棒・青の線・橙の点・赤枠・赤で囲んだ所・
     red bar・blue line・orange square・the curve in red など）。黒・白・灰の無彩色は数えない（背景・軸・文字と見分けにくい）
  2. その枚の図の部分だけを描く（render_check_py の描き方で、文字・マスターとレイアウトの飾り・プレースホルダを除く）。
     見るのは、貼った画像（論文の切り出し・figkit の図）の画素と、図形の塗り・線の色。文字の色は数えない
     （強調の赤い文字があっても、棒が赤いことにはならない。ただし画像の中の文字は画像の画素として数える）
  3. 画素を色相で 赤・橙・黄・緑・青・紫 に分ける。無彩色は外す（最大と最小の差 CHROMA 未満）。ある色相の画素が
     MIN_PIXELS 以上あれば、その色が「ある」。figkit の色：red・dred（落ち着いた赤）・warm（うすい赤）は赤、
     blue・lblue・pale（うすい青）は青、orange は橙、green は緑、sand は橙
  4. 原稿の色がその枚に無ければ △（原稿の色を画面に合わせるか、図の色を直す）
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))

WIDTH = 800          # 図の部分を描く幅（px。描き方の中で2倍で描く）
CHROMA = 20          # 有彩色とみなす最大と最小の差（0〜255）。figkit の warm・pale（うすい塗り）は 26〜27
MIN_PIXELS = 30      # その色相の画素がこれ以上あれば「ある」（細い線・小さな丸の印でも数百 px）

# 色相の範囲（度）。隣どうしは少し重ねる（橙の点が赤寄りに、紫が赤寄りに描かれることがある）
HUES = {
    "赤": [(330, 360), (0, 22)],
    "橙": [(12, 50)],
    "黄": [(35, 72)],
    "緑": [(68, 175)],
    "青": [(170, 265)],
    "紫": [(255, 340)],
}
ORDER = list(HUES)

JA_COLOR = {"赤": "赤", "紅": "赤", "ピンク": "赤", "桃": "赤", "橙": "橙", "オレンジ": "橙", "茶": "橙", "黄": "黄",
            "緑": "緑", "青": "青", "水色": "青", "紺": "青", "紫": "紫"}
EN_COLOR = {"red": "赤", "crimson": "赤", "scarlet": "赤", "pink": "赤", "magenta": "紫", "orange": "橙", "brown": "橙",
            "yellow": "黄", "gold": "黄", "green": "緑", "blue": "青", "cyan": "青", "navy": "青", "teal": "緑",
            "purple": "紫", "violet": "紫"}
_JA_PART = (r"棒|線|点|丸|枠|帯|矢印|曲線|領域|面|円|四角|箱|印|網掛け|塗り|マーカー|記号|折れ線|囲み|破線|点線|実線|三角|星|"
            r"バー|カーブ|プロット|ゾーン|斜線|範囲|部分|箇所|所|ところ|玉|粒|球|柱|ブロック|カード|矩形|吹き出し|波形|"
            r"グラフ|ヒストグラム|ピーク|山|網|影|模様")
JA_PAIR = re.compile(
    r"(?:うすい|薄い|淡い|濃い|明るい|暗い)?(" + "|".join(sorted(JA_COLOR, key=len, reverse=True)) + r")"
    r"(?:色)?(?:"
    r"(?:い|の)?(?:太い|細い|太|細|破線の|点線の|実線の|縦の|横の|丸い|小さな|大きな|四角い|縦|横)?(?:" + _JA_PART + r")"
    r"|で(?:囲|塗|示|描|重ね|表し|ぬ|印))")
_EN_C = "|".join(EN_COLOR)
_EN_PART = (r"bars?|lines?|curves?|dots?|points?|circles?|box(?:es)?|frames?|bands?|arrows?|regions?|areas?|squares?|markers?|"
            r"outlines?|traces?|histograms?|shading|strips?|stripes?|rings?|ellipses?|triangles?|stars?|columns?|segments?|"
            r"patch(?:es)?|blocks?|rectangles?|shapes?|peaks?|spots?|blobs?|balls?|spheres?|disks?|discs?|crosses?|symbols?|"
            r"plots?|waveforms?|highlights?|bubbles?|cells?|tiles?|zones?|bins?|fills?|outline|borders?")
EN_PAIR = re.compile(r"\b(?:light|dark|pale|bright|deep)?[- ]?(" + _EN_C + r")(?:dish)?(?:[- ](?:dashed|dotted|solid|thick|thin|vertical|"
                     r"horizontal|shaded|filled|open|small|large|big|bold|round|wide|narrow))?[- ](?:" + _EN_PART + r")\b", re.I)
EN_IN = re.compile(r"\b(?:" + _EN_PART + r")\b(?:\s+(?:is|are|was|were))?(?:\s+(?:shown|drawn|plotted|marked|highlighted|circled|"
                   r"outlined|colou?red|shaded|filled))?\s+in\s+(?:light |dark |pale |bright )?(" + _EN_C + r")\b", re.I)
EN_CIRCLED = re.compile(r"\b(?:circled|outlined|boxed|highlighted|framed|shaded)\s+in\s+(?:light |dark |pale |bright )?(" + _EN_C + r")\b", re.I)

BAND = re.compile(r"帯|\bbands?\b|\bbanners?\b", re.I)


def color_mentions(text: str):
    """原稿の文から [(色相, 言い回し)]（出てきた順。同じ言い回しは1回）。"""
    out, seen = [], set()
    for m in JA_PAIR.finditer(text or ""):
        out.append((JA_COLOR[m.group(1)], m.group(0), m.start()))
    for rx in (EN_PAIR, EN_IN, EN_CIRCLED):
        for m in rx.finditer(text or ""):
            out.append((EN_COLOR[m.group(1).lower()], m.group(0).strip(), m.start()))
    res = []
    for hue, phrase, _ in sorted(out, key=lambda x: x[2]):
        if phrase not in seen:
            seen.add(phrase)
            res.append((hue, phrase))
    return res


def hue_counts(img) -> dict:
    """画像（PIL）の有彩色の画素を色相ごとに数える {色相: 画素数}。"""
    import numpy as np
    a = np.asarray(img.convert("RGB"), dtype=np.int16)
    mx, mn = a.max(axis=2), a.min(axis=2)
    d = mx - mn
    keep = d >= CHROMA
    if not keep.any():
        return {k: 0 for k in ORDER}
    r, g, b = (a[..., k][keep].astype(float) for k in range(3))
    mx_, d_ = mx[keep].astype(float), d[keep].astype(float)
    h = np.where(mx_ == r, ((g - b) / d_) % 6, np.where(mx_ == g, (b - r) / d_ + 2, (r - g) / d_ + 4)) * 60.0
    out = {}
    for k, ranges in HUES.items():
        sel = np.zeros(h.shape, dtype=bool)
        for lo, hi in ranges:
            sel |= (h >= lo) & (h < hi)
        out[k] = int(sel.sum())
    return out


def _figure_renderer(frame=False):
    import render_check_py as RC

    class FigureOnly(RC.SlideRenderer):
        """図の部分だけを描く：文字・背景・マスターとレイアウトの飾り・プレースホルダ（題名の帯・番号）を描かない。
        frame=True なら、文字のほかは全部（背景・飾り・プレースホルダの塗り）を描く（「青い帯」が結論の帯を指すとき）。"""

        def background(self):
            return super().background() if frame else None

        def draw_text(self, *a, **k):
            return None

        def draw_sp(self, el, owner, tf, sh):
            if not frame and ((sh is not None and getattr(sh, "is_placeholder", False)) or el.find(f".//{RC.P}nvPr/{RC.P}ph") is not None):
                return
            return super().draw_sp(el, owner, tf, sh)

        def run(self):
            if frame:
                super().run()
            else:
                self.draw_tree(self.slide._element.find(f"{RC.P}cSld/{RC.P}spTree"), self.slide, None, deco=False)
            return self.pt.img

    return RC, FigureOnly


def slide_hues(prs, numbers=None, frame=False) -> dict:
    """{枚: {色相: 画素数}}（図の部分だけ。frame=True なら文字のほかは全部）。numbers を渡すと、その枚だけ描く。"""
    import contextlib
    import io
    RC, FigureOnly = _figure_renderer(frame)
    deck = RC.Deck(prs)
    out = {}
    for i, slide in enumerate(prs.slides, 1):
        if numbers is not None and i not in numbers:
            continue
        with contextlib.redirect_stderr(io.StringIO()):
            img = FigureOnly(deck, slide, i, WIDTH).run()
        out[i] = hue_counts(img)
    return out


def notes_of(prs) -> dict:
    return {i: (s.notes_slide.notes_text_frame.text if s.has_notes_slide else "") for i, s in enumerate(prs.slides, 1)}


def present(counts: dict):
    return [k for k in ORDER if counts.get(k, 0) >= MIN_PIXELS]


def mismatches(prs, notes: dict | None = None):
    """[(枚, [言い回し], 無い色相, その枚にある色相)]：原稿が言う色が、その枚の図・図形に無い。"""
    notes = notes_of(prs) if notes is None else notes
    said = {i: color_mentions(t) for i, t in notes.items()}
    said = {i: m for i, m in said.items() if m}
    if not said:
        return []
    hues = slide_hues(prs, set(said))
    out = []
    for i, ms in sorted(said.items()):
        have = present(hues.get(i, {}))
        for hue in dict.fromkeys(h for h, _ in ms):
            if hue not in have:
                out.append((i, [p for h, p in ms if h == hue], hue, have))
    # 「青い帯」「the blue band」は、テンプレートの結論の帯（プレースホルダ・飾り）を指すことがある → 文字のほかを全部描いて見直す
    band = {i for i, ps, _, _ in out if all(BAND.search(p) for p in ps)}
    if band:
        whole = slide_hues(prs, band, frame=True)
        out = [(i, ps, hue, have) for i, ps, hue, have in out if not (i in band and hue in present(whole.get(i, {})))]
    return out


HINT = "原稿の色を画面に合わせるか、図の色を直す（figkit の図なら figs.py の色、論文の図なら原稿の言い方）"


def check(pptx, notes: dict | None = None):
    """[(印, 項目, 説明)]（check_done の行の形）。原稿に色の語＋図の部品の組が無ければ空。"""
    from pptx import Presentation
    prs = Presentation(str(pptx))
    notes = notes_of(prs) if notes is None else notes
    if not any(color_mentions(t) for t in notes.values()):
        return []
    bad = mismatches(prs, notes)
    if not bad:
        return [("✔", "原稿と図の色", "原稿が言う色は、どれもその枚の図・図形にある")]
    msg = "；".join(f"[{i}] 「{'」「'.join(ps[:2])}」→ この枚の図に{hue}が無い（あるのは {'・'.join(have) or '無彩色だけ'}）"
                   for i, ps, hue, have in bad[:6])
    return [("△", "原稿と図の色", f"{msg}（{HINT}）")]


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print(__doc__)
        return 1
    from pptx import Presentation
    pptx = Path(argv[0])
    if "--all" in argv:
        prs = Presentation(str(pptx))
        notes = notes_of(prs)
        hues = slide_hues(prs)
        for i in sorted(hues):
            ms = color_mentions(notes.get(i, ""))
            print(f"[{i}] 図の色 " + "・".join(f"{k}{v}" for k, v in hues[i].items() if v) + ("　原稿：" + "、".join(f"{p}（{h}）" for h, p in ms) if ms else ""))
    res = check(pptx)
    for mark, item, msg in res:
        print(f"{mark} {item}：{msg}")
    if not res:
        print("・ 原稿に、色の語と図の部品の語の組が無い")
    return 0


if __name__ == "__main__":
    sys.exit(main())
