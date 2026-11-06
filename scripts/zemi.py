"""ゼミスライド生成ライブラリ（python-pptx）

テンプレート（既定は同梱の assets/templates/テンプレート1.pptx）のマスターをそのまま使い、
同じ見た目の部品（●見出し・本文・赤字強調・数式・矢印・図・下部の青帯まとめ）を置いていく。

最小例:
    import sys; sys.path.insert(0, r"<skill>/scripts")
    from zemi import Deck, Eq

    deck = Deck(workdir="build")                     # 数式PNGなどの中間ファイル置き場
    deck.title_slide(["3.2 熱力学温度"], author="発表者名")

    s = deck.slide("3.2 熱力学温度", summary="熱力学温度はカルノー・サイクルの熱量比で定義")
    s.heading("熱力学温度（ケルビン目盛）")
    s.at(1.0, 1.95)                                   # ここから下へ流し込み
    s.p("理想熱機関（カルノー・サイクル）で出入りする熱量に基づく")
    s.peq(r"\\frac{T_1}{T_2}=\\frac{Q_1}{Q_2}")
    s.p("{r:作業物質によらない}温度目盛")
    s.image("figs/carnot.png", x=7.6, y=1.3, w=5.0)
    s.notes("話す内容…")
    deck.save("out.pptx")

テキストの簡易マークアップ（入れ子可）:
    {r:赤字}  {u:下線}  {b:太字}  {i:イタリック(変数用, Times)}  {c:青字}  {ru:赤＋下線}
    ^{上付き}  _{下付き}      例: "^{3}He-^{4}He混合液", "pH_{2}", "{i:T}_{c}"
    改行 \\n で段落を分ける（元スライドと同じく1行=1段落、折り返しは自分で入れる）
    リテラルの { } ^ _ は \\{ \\} \\^ \\_ で書く

そのほかの部品:
    s.oval(x, y, w, h)                       図の注目点に重ねる赤い輪（塗りなし。過去の輪読のデッキの形）
    s.defs(x, y, [("γ", "表面張力"), ("ρ", "液体の密度")])   数式の右に変数の定義を縦に（過去の輪読のデッキの形）
    deck.title_slide([英題1行目, 英題2行目], subtitle="和訳", author="著者名", bold=False)   論文の表紙（過去の論文紹介のデッキの形）

本文の形の部品（references/structures.md。構成案の「本文の形」の列で枚ごとに選ぶ）:
    s.lead(["前提1", "前提2"], "帰結")            前提 ⇒ 帰結（最後の行が「⇒ 赤字」）
    s.block("アトキンス効果：", ["説明1", "説明2"], then=None)   ラベル＋字下げの説明
    s.develop("臨界速度以下：\\n抵抗なし", "{r:輸送率は一定}")    横の太矢印で展開（左＝条件・前、右＝結果・次）
    s.lead_down("背景・問題", "目的・結論")         縦の矢印で結論へ（結論は淡い橙の囲み）
    s.cases([("T > T_λ", "説明"), ("T < T_λ", "説明")])  条件の場合分け（灰色の囲み）
    s.ask("〜ではないのか？", "〜により否定")       問い → 答え
    s.numbered(["手順1", "手順2"])                 番号の手順
図解の型の部品:
    s.cards([("見出し", "説明"), ...], layout="row"|"grid"|"steps"|"cycle")   並列カード・格子・段違いの順序・循環
    s.tree("大分類", ["小分類1", "小分類2"])        ツリー（分類・階層）
    s.before_after(("従来", [...]), ("この研究", [...]), value="誤差 1/3")   前後を並べ、差を1つの数で
    s.pair("figs/a.png", "figs/b.png", labels=["条件 A", "条件 B"], values=["誤差 2.0", "誤差 6.8"])
    s.callout((点のx, 点のy), (箱のx, 箱のy), "解釈")   図の注目点への吹き出し
    deck.section(2, "結果")                         区切りの枚（全面の色）
    deck.build_up(title, heading, items)            項目を1つずつ足していく枚（漸進表示）
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageFont
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.dml import MSO_THEME_COLOR
from pptx.enum.shapes import MSO_SHAPE, PP_PLACEHOLDER
from pptx.enum.text import MSO_AUTO_SIZE, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATE = SKILL_DIR / "assets" / "templates" / "テンプレート1.pptx"   # 名前を言わないときのテンプレート

# ---- 寸法（インチ）: 元デッキから実測 -------------------------------------------
SLIDE_W, SLIDE_H = 13.333, 7.5
BAND_TOP = 6.76            # 下部の青帯の上端
CONTENT_BOTTOM = 6.62      # 本文・図はここより上に収める
HEADING_POS = (0.55, 1.14) # ●見出しの位置
BODY_X = 1.0               # 本文ブロックの標準x
BOX_TOP = 6.25             # 帯の無い骨格（conclusion: box）の、結論の囲みの上端（6.05 では囲みの下に 0.8 in 空き、本文が狭かった）
MESSAGE_POS = (0.6, 0.62)  # 結論タイトルの骨格（conclusion: title）の、結論の一文の位置（上の小さな話題の下）

TABLE_NAMES = ("表の見出し", "表の行ラベル", "表のセル")   # s.table の図形の名前（check_layout が本文の字数から外す）

# ---- 色 -----------------------------------------------------------------------
class C:
    TEXT = "545455"    # テーマ tx1（本文の灰色）
    RED = "FF0000"     # 強調
    BULLET = "005AFF"  # 見出しの●
    BLUE = "213CFF"    # 補助の青字（まれに使用）
    BAND = "215F99"    # 青帯・タイトル左の縦棒（tx2 75%）。この濃い青の「面」は青帯専用で、表や箱の塗りには使わない
    ARROW = "4E95D9"   # ブロック矢印（tx2 50%）
    GRAY = "8C8C8C"
    PALE = "DCE9F7"    # 薄い青の塗り（表の見出し・流れ図の箱）
    LIGHT = "F2F2F2"   # 薄い灰の塗り（表の本文セル）
    CONCLUDE = "FBE3D6"  # 結論の囲みの塗り（淡い橙。帯の無い骨格で、下の帯の代わり）
    ACCENT = "215F99"    # 差し色（章のナビの今の章・線）
    TINT = "EAF1FA"      # 淡い地（柱・上の帯）


_C_DEFAULTS = {k: v for k, v in vars(C).items() if k.isupper()}


def template_style(template) -> dict:
    """テンプレートの横の同じ名前の .json（例 assets/templates/テンプレート2.json）。無ければ {}。
    {"colors": {"BULLET": "E8772E", ...}, "band_align": "l"} の形で、色（C の名前）とまとめの帯の寄せ（c／l）を変える。"""
    side = Path(template).with_suffix(".json")
    return json.loads(side.read_text(encoding="utf-8")) if side.exists() else {}


PALETTE_FILE = SKILL_DIR / "assets" / "templates" / "配色.json"


def palettes() -> dict:
    """同梱の配色 {名前: {役割: 色, colors: {C の名前: 色}}}（assets/templates/配色.json）。"""
    return json.loads(PALETTE_FILE.read_text(encoding="utf-8")) if PALETTE_FILE.exists() else {}


def recolor(prs, style: dict, pal: dict):
    """テンプレートの飾りの図形（名前に {main} などの役割）・タイトルの文字・まとめの帯の文字・テーマの色を、配色 pal に差し替える。
    構造（形と位置）はそのまま、色だけが変わる。"""
    import re
    from lxml import etree
    master = prs.slide_master
    parts = [master] + list(master.slide_layouts)
    for part in parts:
        for sh in part.shapes:
            m = re.search(r"\{(\w+)\}", sh.name or "")
            if m and m.group(1) in pal:
                sh.fill.solid()
                sh.fill.fore_color.rgb = RGBColor.from_string(pal[m.group(1)])
                if "札" in sh.name:   # 札の文字は、白と主色のうち差し色の地で明暗差の大きいほう（make_templates.tag_text と同じ）
                    tc = max(("FFFFFF", pal["main"]), key=lambda c: contrast(c, pal[m.group(1)]))
                    for r in sh._element.iter(qn("a:rPr")):
                        for f in r.findall(qn("a:solidFill")):
                            r.remove(f)
                        fill = etree.Element(qn("a:solidFill"))
                        etree.SubElement(fill, qn("a:srgbClr"), val=tc)
                        r.insert(0, fill)
            if sh.name == "まとめの帯":
                for d in sh._element.iter(qn("a:defRPr")):
                    for f in d.findall(qn("a:solidFill")):
                        d.remove(f)
                    fill = etree.SubElement(d, qn("a:solidFill"))
                    etree.SubElement(fill, qn("a:srgbClr"), val=pal["ink"] if style.get("band_rules") else pal["band_text"])
                    d.insert(0, fill)
    for lay in master.slide_layouts:   # ページ番号の色を、下にある飾りの色に合わせる（配色を変えると帯の濃淡が逆になる）
        _recolor_slide_number(lay, pal)
    role = style.get("title_color", "ink")
    tcol = {"white": "FFFFFF", "gray": "6B6B6B"}.get(role) or pal.get(role, pal["ink"])
    title = master._element.find(qn("p:txStyles")).find(qn("p:titleStyle")).find(qn("a:lvl1pPr"))
    rpr = title.find(qn("a:defRPr"))
    for f in rpr.findall(qn("a:solidFill")):
        rpr.remove(f)
    fill = etree.SubElement(rpr, qn("a:solidFill"))
    etree.SubElement(fill, qn("a:srgbClr"), val=tcol)
    rpr.insert(0, fill)
    theme_part = next(r.target_part for r in master.part.rels.values() if r.reltype.endswith("/theme"))
    theme = etree.fromstring(theme_part.blob)
    a = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
    for key, val in (("dk1", pal["ink"]), ("dk2", pal["main"]), ("accent1", pal["accent"]), ("accent2", pal["emph"])):
        el = theme.find(f".//{a}clrScheme/{a}{key}")
        if el is not None:
            for c in list(el):
                el.remove(c)
            etree.SubElement(el, a + "srgbClr", val=val)
    theme_part._blob = etree.tostring(theme, xml_declaration=True, encoding="UTF-8", standalone=True)


def contrast(c1: str, c2: str) -> float:
    """2色（"RRGGBB"）の明暗差（WCAG の比）。"""
    def lum(c):
        v = [int(c[k:k + 2], 16) / 255 for k in (0, 2, 4)]
        v = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in v]
        return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]
    a, b = sorted((lum(c1), lum(c2)), reverse=True)
    return (a + 0.05) / (b + 0.05)


def _recolor_slide_number(layout, pal: dict):
    """レイアウトのページ番号の文字色を、その下の飾りの役割で決め直す：下の帯の地（band_bg）なら帯の文字の色、主色の帯（main）なら白。
    飾りが下に無ければそのまま（灰色）。例：下の帯の構造（濃い青の帯に白い番号）を淡い帯の配色にすると、白い番号が見えなくなっていた。"""
    import re
    from lxml import etree
    num = next((ph for ph in layout.placeholders if ph.placeholder_format.type == PP_PLACEHOLDER.SLIDE_NUMBER), None)
    if num is None or num.left is None or num.width is None:
        return
    parts = ([] if layout._element.get("showMasterSp") == "0" else [layout.slide_master]) + [layout]
    under = None
    for part in parts:   # マスターが下、レイアウトが上に描かれるので、後に見つかったものが番号のすぐ下
        for sh in part.shapes:
            m = re.search(r"\{(\w+)\}", sh.name or "")
            if (m and not sh.is_placeholder and sh.left is not None and sh.left < num.left + num.width
                    and sh.left + sh.width > num.left and sh.top < num.top + num.height and sh.top + sh.height > num.top):
                under = m.group(1)
    color = {"band_bg": pal.get("band_text"), "main": "FFFFFF"}.get(under)
    if not color:
        return
    txBody = num._element.find(qn("p:txBody"))
    lst = txBody.find(qn("a:lstStyle"))
    if lst is None:
        lst = etree.SubElement(txBody, qn("a:lstStyle"))
        txBody.insert(1, lst)
    lvl = lst.find(qn("a:lvl1pPr"))
    if lvl is None:
        lvl = etree.SubElement(lst, qn("a:lvl1pPr"), algn="r")
    rpr = lvl.find(qn("a:defRPr"))
    if rpr is None:
        rpr = etree.SubElement(lvl, qn("a:defRPr"), sz="1200")
    for f in rpr.findall(qn("a:solidFill")):
        rpr.remove(f)
    fill = etree.Element(qn("a:solidFill"))
    etree.SubElement(fill, qn("a:srgbClr"), val=color)
    rpr.insert(0, fill)


def body_area(style: dict) -> dict:
    """構造の本文の場所（in）：テンプレートの .json の area に既定を補ったもの。結論の囲みの構造（box）では囲みの上で切る。
    Deck と check_layout.py（構造に合わせた検査）が同じ値を使うように、ここで1か所にまとめる。"""
    area = {"x": BODY_X, "top": 1.9, "right": SLIDE_W - BODY_X, "bottom": CONTENT_BOTTOM,
            "heading": HEADING_POS, "fig_x": 7.6, **style.get("area", {})}
    if style.get("conclusion", "band") == "box":
        area["bottom"] = min(area["bottom"], BOX_TOP - 0.15)
    return area


def apply_template_colors(style: dict):
    """C の色を既定に戻してから、テンプレートの色で上書きする（1つのプロセスで別のテンプレートのデッキを続けて作っても混ざらない）。"""
    for k, v in _C_DEFAULTS.items():
        setattr(C, k, v)
    for k, v in style.get("colors", {}).items():
        if k in _C_DEFAULTS:
            setattr(C, k, v)


# 色は C の名前で持ち、読むときに引く（テンプレートの色 apply_template_colors が {r:} にも効くように）。{a:} は主色（見出し・カードの見出し）
FLAG_STYLES = {"r": ("color", "RED"), "c": ("color", "BLUE"), "u": ("u", True),
               "b": ("b", True), "i": ("i", True), "g": ("color", "GRAY"), "a": ("color", "BAND")}


# ---- マークアップ解析 ------------------------------------------------------------
@dataclass
class Run:
    text: str
    color: str | None = None
    u: bool = False
    b: bool = False
    i: bool = False
    baseline: int = 0  # 30000=上付き, -25000=下付き


def parse_markup(s: str, base: Run | None = None) -> list[Run]:
    """'{r:赤}^{3}He' のような文字列を Run のリストにする（入れ子可）。"""
    base = base or Run("")
    out: list[Run] = []
    buf = []

    def flush(style):
        if buf:
            out.append(Run("".join(buf), style.color, style.u, style.b, style.i, style.baseline))
            buf.clear()

    def find_close(k):
        depth = 0
        while k < len(s):
            ch = s[k]
            if ch == "\\":
                k += 2
                continue
            if ch == "{":
                depth += 1
            elif ch == "}":
                if depth == 0:
                    return k
                depth -= 1
            k += 1
        raise ValueError(f"閉じ括弧 }} が足りません: {s!r}")

    k = 0
    while k < len(s):
        ch = s[k]
        if ch == "\\" and k + 1 < len(s):
            buf.append(s[k + 1]); k += 2; continue
        if ch in "^_" and k + 1 < len(s) and s[k + 1] == "{":
            end = find_close(k + 2)
            flush(base)
            st = Run("", base.color, base.u, base.b, base.i, 30000 if ch == "^" else -25000)
            out.extend(parse_markup(s[k + 2:end], st))
            k = end + 1; continue
        if ch == "{":
            colon = s.find(":", k)
            flags = s[k + 1:colon] if colon > 0 else ""
            if colon > 0 and flags and all(f in FLAG_STYLES for f in flags):
                end = find_close(colon + 1)
                flush(base)
                st = Run("", base.color, base.u, base.b, base.i, base.baseline)
                for f in flags:
                    attr, val = FLAG_STYLES[f]
                    setattr(st, attr, getattr(C, val) if attr == "color" else val)
                out.extend(parse_markup(s[colon + 1:end], st))
                k = end + 1; continue
        buf.append(ch); k += 1
    flush(base)
    return out


def split_lines(runs: list[Run]) -> list[list[Run]]:
    lines: list[list[Run]] = [[]]
    for r in runs:
        parts = r.text.split("\n")
        for j, part in enumerate(parts):
            if j > 0:
                lines.append([])
            if part:
                lines[-1].append(Run(part, r.color, r.u, r.b, r.i, r.baseline))
    return lines


# ---- 文字幅の見積もり（PILのフォント計測。最終確認は PowerPoint 実描画で行う） -----
_FONTS: dict = {}
_WIN = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
# 文字幅を見積もるフォントの候補（上から順に、あるものを使う）。Windows のテーマのフォントに近いものを、Mac・Linux でも探す。
# (ファイル, ttc の番号)。どれも無ければ、和文 1.0・欧文 0.55 文字分の幅で見積もる（最終確認は PowerPoint の実描画）
_FONT_FILES = {
    "latin": [(_WIN / "arial.ttf", 0), (Path("/System/Library/Fonts/Supplemental/Arial.ttf"), 0),
              (Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"), 0)],
    "latin_b": [(_WIN / "arialbd.ttf", 0), (Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"), 0),
                (Path("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"), 0)],
    "latin_i": [(_WIN / "timesi.ttf", 0), (Path("/System/Library/Fonts/Supplemental/Times New Roman Italic.ttf"), 0),
                (Path("/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf"), 0)],
    "ea": [(_WIN / "msgothic.ttc", 2),          # MS PGothic（テーマの和文フォント）
           (Path("/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc"), 0),
           (Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"), 0),
           (Path("/usr/share/fonts/opentype/ipaexfont-gothic/ipaexg.ttf"), 0)],
}


def _font(kind: str):
    if kind not in _FONTS:
        _FONTS[kind] = None
        for path, index in _FONT_FILES["ea" if kind not in _FONT_FILES else kind]:
            try:
                _FONTS[kind] = ImageFont.truetype(str(path), 100, index=index)
                break
            except OSError:
                continue
    return _FONTS[kind]


def _is_ea(ch: str) -> bool:
    o = ord(ch)
    return o >= 0x2E80 or 0x2190 <= o <= 0x2BFF or 0x0370 <= o <= 0x03FF or 0x2010 <= o <= 0x2027


def text_width_pt(runs: list[Run], size: float) -> float:
    w = 0.0
    for r in runs:
        scale = 0.7 if r.baseline else 1.0
        for ch in r.text:
            kind = "ea" if _is_ea(ch) else ("latin_i" if r.i else ("latin_b" if r.b else "latin"))
            f = _font(kind)
            cw = f.getlength(ch) / 100.0 if f else (1.0 if kind == "ea" else 0.55)
            w += cw * size * scale
    return w


def line_height_in(size: float) -> float:
    return size * 1.2 / 72.0


INSET_X, INSET_Y = 0.1, 0.05


@dataclass
class Box:
    x: float
    y: float
    w: float
    h: float

    @property
    def right(self): return self.x + self.w
    @property
    def bottom(self): return self.y + self.h
    @property
    def cy(self): return self.y + self.h / 2


# ---- 数式（matplotlib mathtext, Computer Modern で PNG 化） -------------------------
@dataclass
class Eq:
    latex: str
    color: str | None = None
    size: float | None = None


EQ_SCALE = 1.1  # 同じptでもCMはArialより小さく見えるので少し大きめに


def render_eq(latex: str, size: float, color: str, outdir: Path, dpi: int = 600):
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import mathtext, rcParams
    from matplotlib.font_manager import FontProperties
    # Computer Modern（LaTeX風）。ただし cm の \oint は崩れるので STIX に切り替える
    rcParams["mathtext.fontset"] = "stix" if r"\oint" in latex else "cm"
    outdir.mkdir(parents=True, exist_ok=True)
    key = hashlib.md5(f"{latex}|{size}|{color}|{dpi}|{rcParams['mathtext.fontset']}".encode()).hexdigest()[:12]
    path = outdir / f"eq_{key}.png"
    if not path.exists():
        mathtext.math_to_image(f"${latex}$", str(path), prop=FontProperties(size=size),
                               dpi=dpi, format="png", color="#" + color)
    with Image.open(path) as im:
        w, h = im.size
    return path, w / dpi, h / dpi




def slide_texts(slide):
    return [sh.text_frame.text for sh in slide.shapes if getattr(sh, "has_text_frame", False) and sh.has_text_frame]


def has_conclusion(slide, slide_height) -> bool:
    """この枚に結論の一文があるか：下の帯の枠・帯・結論の囲み・柱の結論の一文、上の結論の一文（●■で始まらない「見出し」）。
    帯なしの枚（summary の無い枚）には結論の置き場が無い（見出しに●が付かないので、上の結論の一文と取り違えない）。"""
    if getattr(slide, "name", "") == PLAIN_MARK or slide.slide_layout.name == PLAIN_LAYOUT_NAME:
        return False
    idx = band_placeholder_idx(slide.slide_layout, slide_height)
    for sh in slide.shapes:
        if not getattr(sh, "has_text_frame", False) or not sh.has_text_frame or not sh.text_frame.text.strip():
            continue
        if sh.is_placeholder and idx is not None and sh.placeholder_format.idx == idx:
            return True
        if sh.name in ("青帯", "結論の一文"):
            return True
        if sh.name == "結論の囲み" and sh.top is not None and sh.top / 914400 >= BOX_TOP - 0.1:   # 下の結論の置き場の囲み（本文の中の s.lead_down の囲みは数えない）
            return True
        if sh.name == "見出し" and not sh.text_frame.text.lstrip().startswith(("●", "■")):
            return True
    return False


# ---- スライド ------------------------------------------------------------------
class Slide:
    def __init__(self, deck: "Deck", slide):
        self.deck = deck
        self.slide = slide
        self.cur_x = deck.area["x"] if hasattr(deck, "area") else BODY_X
        self.cur_y = deck.area["top"] if hasattr(deck, "area") else 1.9
        self.boxes: list[tuple[str, Box]] = []

    # -- 低レベル: テキストボックス
    def _add_runs(self, paragraph, runs: list[Run], size: float, color: str | None, bold: bool):
        for r in runs:
            run = paragraph.add_run()
            run.text = r.text
            f = run.font
            f.size = Pt(size)
            c = r.color or color
            if c:
                f.color.rgb = RGBColor.from_string(c)
            if r.u:
                f.underline = True
            if r.b or bold:
                f.bold = True
            if r.i:
                f.italic = True
                f.name = "Times New Roman"
            rPr = run._r.get_or_add_rPr()
            rPr.set("lang", "ja-JP")
            rPr.set("altLang", "en-US")
            if r.baseline:
                rPr.set("baseline", str(r.baseline))

    def text(self, x: float, y: float, text: str, size: float = 20, color: str | None = None,
             align: str = "l", bold: bool = False, w: float | None = None, name: str | None = None) -> Box:
        """本文テキストを置く。折り返しなし（改行は \\n で明示）。戻り値は推定の外枠。"""
        lines = split_lines(parse_markup(text))
        tw = max((text_width_pt(l, size) for l in lines), default=0) / 72.0
        bw = w if w is not None else tw + 2 * INSET_X + 0.05
        bh = len(lines) * line_height_in(size) + 2 * INSET_Y
        tb = self.slide.shapes.add_textbox(Inches(x), Inches(y), Inches(bw), Inches(bh))
        if name:
            tb.name = name
        tf = tb.text_frame
        tf.word_wrap = False
        tf.auto_size = MSO_AUTO_SIZE.SHAPE_TO_FIT_TEXT
        for j, line in enumerate(lines):
            p = tf.paragraphs[0] if j == 0 else tf.add_paragraph()
            p.alignment = {"l": PP_ALIGN.LEFT, "c": PP_ALIGN.CENTER, "r": PP_ALIGN.RIGHT}[align]
            if line:
                self._add_runs(p, line, size, color, bold)
            else:
                p.add_run().text = ""
        box = Box(x, y, bw, bh)
        self.boxes.append(("text", box))
        tr = self.deck.area.get("text_right") if hasattr(self.deck, "area") else None
        if tr and hasattr(self, "section") and box.x < tr < box.right - 0.05 and box.x < self.deck.area["fig_x"]:   # 本文の枚だけ
            print(f"[WARN] 柱からはみ出す文（右端 {box.right:.2f} in > 柱の右 {tr:.2f} in）：「{text[:16]}」"
                  " → 柱の中は1行14字前後（20pt）までに \\n で折るか、文を右の白い所に置く")
        return box

    def heading(self, text: str, x: float | None = None, y: float | None = None, size: float = 24) -> Box:
        """「● 見出し」（●は青 005AFF、文字は24pt）。1スライド1つが基本。
        結論の一文・副題が上にある構造（conclusion: title・lead）でその枚に結論があるときは、見出しを別の行にせず、
        タイトルの行の後ろに「／ 見出し」と足す（上が3段に重ならないように）。結論の無い枚では、結論の一文の場所に置く。"""
        if getattr(self, "_message", False) and x is None and y is None:
            for ph in self.slide.placeholders:
                if ph.placeholder_format.type == PP_PLACEHOLDER.TITLE:
                    add = "　／　" + text
                    d = self.deck
                    # タイトルの大きい構造（細い左帯と副題は 32pt）では、足した見出しでタイトルの枠を越えて折り返し、
                    # 下の副題の行に重なっていた（check_layout の構造の検査で見つけた）。入らなければ足す部分だけ小さく（14pt まで）。
                    # 文字幅の見積もりは MS PGothic で、描画のメイリオより 1 割ほど狭いので 1.1 倍で見る
                    base = text_width_pt(parse_markup(ph.text_frame.text), d.title_size) * 1.1 / 72.0
                    unit = text_width_pt(parse_markup(add), 1.0) * 1.1 / 72.0
                    room = d.title_w - 2 * INSET_X - 0.1 - base
                    size = None if base + unit * d.title_size <= d.title_w - 2 * INSET_X - 0.1 else max(14, min(d.title_size, int(room / unit)))
                    self.deck._set_placeholder_text(ph, add, append=True, size=size)
                    return Box(0.6, 0.12, 0, 0)
        hx, hy = self.deck.area["heading"]
        x = hx if x is None else x
        y = hy if y is None else y
        lines = [([] if getattr(self, "_plain", False) else [Run(self.deck.style.get("heading_mark", "●"), C.BULLET), Run(" ")])
                 + parse_markup(text)]   # 帯なしの枚は●を付けない
        tr = self.deck.area.get("text_right")
        if tr and x < tr:   # 柱の中の見出しは、柱の文の右端に入るまで小さく（20pt まで）。見積もりは描画より狭いので 1.1 倍で
            # 柱では 22pt から（24pt の●見出しが、その上の 20pt の結論より大きく見え、上下が逆だった）
            size = min(size, 22)
            while size > 20 and x + text_width_pt(lines[0], size) * 1.1 / 72.0 + 2 * INSET_X > tr:
                size -= 1
        tw = text_width_pt(lines[0], size) / 72.0
        bw, bh = tw + 2 * INSET_X + 0.05, line_height_in(size) + 2 * INSET_Y
        tb = self.slide.shapes.add_textbox(Inches(x), Inches(y), Inches(bw), Inches(bh))
        tb.name = "見出し"
        tf = tb.text_frame
        tf.word_wrap = False
        tf.auto_size = MSO_AUTO_SIZE.SHAPE_TO_FIT_TEXT
        self._add_runs(tf.paragraphs[0], lines[0], size, None, False)
        box = Box(x, y, bw, bh)
        self.boxes.append(("text", box))
        return box

    # -- 数式
    def eq(self, latex: str, x: float, y: float, size: float = 20, color: str | None = None,
           h: float | None = None, center_y: float | None = None) -> Box:
        """LaTeX(mathtext)の数式をPNGにして置く。size は本文のpt（自動で少し拡大）。
        center_y を与えると数式の上下中心をそこに合わせる。"""
        path, w_in, h_in = render_eq(latex, size * EQ_SCALE, color or C.TEXT, self.deck.workdir / "eq")
        if h is not None:
            w_in, h_in = w_in * h / h_in, h
        if center_y is not None:
            y = center_y - h_in / 2
        pic = self.slide.shapes.add_picture(str(path), Inches(x), Inches(y), Inches(w_in), Inches(h_in))
        pic.name = "数式"                     # 図と見分ける（figplan.py が図の種類を数えるとき）
        box = Box(x, y, w_in, h_in)
        self.boxes.append(("eq", box))
        return box

    def row(self, x: float, y: float, parts: list, size: float = 20, gap: float = 0.07) -> Box:
        """文章と数式を1行に並べる: s.row(1, 3, ["巨視的波動関数から", Eq(r"v_s=\\frac{\\hbar}{m}\\nabla S"), "を用いて"])"""
        line_h = line_height_in(size) + 2 * INSET_Y
        eq_items = []
        for part in parts:
            if isinstance(part, Eq):
                p, w_in, h_in = render_eq(part.latex, (part.size or size) * EQ_SCALE,
                                          part.color or C.TEXT, self.deck.workdir / "eq")
                eq_items.append(h_in)
        row_h = max([line_h] + eq_items)
        cy = y + row_h / 2
        cx = x + INSET_X  # 文字（グリフ）の左端を追うカーソル
        for part in parts:
            if isinstance(part, Eq):
                b = self.eq(part.latex, cx + gap, 0, size=part.size or size, color=part.color, center_y=cy)
                cx = b.right + gap
            else:
                b = self.text(cx - INSET_X, cy - line_h / 2, part, size=size)
                cx = b.right - INSET_X - 0.05
        return Box(x, y, cx - x + INSET_X, row_h)

    # -- 図・図形
    def image(self, path, x: float, y: float, w: float | None = None, h: float | None = None,
              name: str | None = None) -> Box:
        with Image.open(path) as im:
            pw, ph = im.size
            dpi = (im.info.get("dpi") or (0, 0))[0]
        if w is None and h is None:
            # 幅を指定しなければ「描いた幅のまま」置く（figkit.save は 220 dpi で保存するので px/dpi が描いた幅）。
            # 幅を指定して拡大・縮小すると図の文字が本文と釣り合わなくなる（過去の質問回答デッキ、2026-10-21）
            w = pw / dpi if dpi and dpi >= 100 else 4.5
        if w is None:
            w = h * pw / ph
        if h is None:
            h = w * ph / pw
        pic = self.slide.shapes.add_picture(str(path), Inches(x), Inches(y), Inches(w), Inches(h))
        pic.name = name or "図"
        box = Box(x, y, w, h)
        self.boxes.append(("image", box))
        return box

    def arrow(self, x: float, y: float, w: float = 0.6, h: float = 0.55, direction: str = "right") -> Box:
        """元デッキと同じ水色のブロック矢印（テーマ色 tx2 50%）。direction: right/down/left/up/both"""
        kind = {"right": MSO_SHAPE.RIGHT_ARROW, "down": MSO_SHAPE.DOWN_ARROW, "left": MSO_SHAPE.LEFT_ARROW,
                "up": MSO_SHAPE.UP_ARROW, "both": MSO_SHAPE.LEFT_RIGHT_ARROW}[direction]
        sh = self.slide.shapes.add_shape(kind, Inches(x), Inches(y), Inches(w), Inches(h))
        sh.name = "矢印"
        sh.fill.solid()
        sh.fill.fore_color.theme_color = MSO_THEME_COLOR.TEXT_2
        sh.fill.fore_color.brightness = 0.5
        sh.line.fill.background()
        style = sh._element.find(qn("p:style"))
        if style is not None:
            sh._element.remove(style)
        box = Box(x, y, w, h)
        self.boxes.append(("shape", box))
        return box

    def rect(self, x, y, w, h, fill: str | None = "F2F2F2", line: str | None = None, rounded=True,
             text: str | None = None, size: float = 18, color: str | None = None,
             align: str = "c", bold: bool = False, name: str | None = None, anchor: str = "m") -> Box:
        """囲み（比較表のセルや定義のまとめなどに）。装飾目的の帯や縦線には使わない。
        濃い青（C.BAND）で塗ると下部の青帯と同じ重みになって結論の帯と競合するので、塗りは C.PALE / C.LIGHT にする。
        塗りと線の両方に色を付けない（どちらか一方。研究発表のデザインの手引き）。anchor は文字の縦の寄せ（t／m）。"""
        sh = self.slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE,
                                         Inches(x), Inches(y), Inches(w), Inches(h))
        if name:
            sh.name = name
        if rounded:
            sh.adjustments[0] = 0.08
        if fill:
            sh.fill.solid(); sh.fill.fore_color.rgb = RGBColor.from_string(fill)
        else:
            sh.fill.background()
        if line:
            sh.line.color.rgb = RGBColor.from_string(line); sh.line.width = Pt(1.25)
        else:
            sh.line.fill.background()
        style = sh._element.find(qn("p:style"))
        if style is not None:
            sh._element.remove(style)
        if text:
            tf = sh.text_frame
            tf.word_wrap = True
            tf.margin_left = tf.margin_right = Inches(0.12)
            if anchor == "t":
                from pptx.enum.text import MSO_ANCHOR
                tf.vertical_anchor = MSO_ANCHOR.TOP
                tf.margin_top = Inches(0.12)
            for j, line_runs in enumerate(split_lines(parse_markup(text))):
                p = tf.paragraphs[0] if j == 0 else tf.add_paragraph()
                p.alignment = {"l": PP_ALIGN.LEFT, "c": PP_ALIGN.CENTER, "r": PP_ALIGN.RIGHT}[align]
                self._add_runs(p, line_runs, size, color or C.TEXT, bold)
        box = Box(x, y, w, h)
        self.boxes.append(("shape", box))
        return box

    def caption(self, box: Box, text: str, right: bool = True, size: float = 14) -> Box:
        """図のすぐ下に小さな灰色の注記（「（概略）」「温度は代表値」などの断り書き）。box は image() の戻り値。"""
        w = text_width_pt(parse_markup(text), size) / 72.0 + 2 * INSET_X + 0.05
        x = box.right - w if right else box.x
        return self.text(x, box.bottom + 0.02, text, size=size, color=C.GRAY)

    def table(self, x: float, y: float, col_w, row_h: float, header: list[str], rows: list,
              label_w: float = 0.0, size: float = 16) -> float:
        """薄青の見出し行（青字）＋薄灰のセルの比較表。rows = [(行ラベル, [セル, ...]), ...]。
        label_w>0 で左端に行ラベル列（薄青）を付ける。セル内は \\n で改行。戻り値は表の下端y。
        col_w は全列共通の幅、または列ごとの幅のリスト（例: [1.45, 2.95]）。
        header はセルの列の見出し。行ラベル列があって header が1つ多いときは、最初の1つを行ラベル列の上に置く（例 ["年齢", "推奨時間"]）。"""
        header = list(header)
        ncols = max((len(cells) for _, cells in rows), default=len(header))
        corner = None
        if label_w and len(header) == ncols + 1:
            corner, header = header[0], header[1:]
        if len(header) != ncols or any(len(cells) != ncols for _, cells in rows):
            raise ValueError(f"s.table：見出し {len(header) + (corner is not None)} 個とセルの列 {ncols} 個が合わない"
                             f"（各行のセル数 {[len(c) for _, c in rows]}）。header はセルの列の数だけ"
                             "（行ラベル列 label_w があるときは、その見出しを先頭に1つ足してもよい）。各行のセルの数もそろえる")
        ws = list(col_w) if isinstance(col_w, (list, tuple)) else [col_w] * ncols
        if len(ws) != ncols:
            raise ValueError(f"s.table：col_w の幅 {len(ws)} 個とセルの列 {ncols} 個が合わない（行ラベル列の幅は label_w で渡す）")
        xs = [x + label_w + sum(ws[:j]) + 0.08 * j for j in range(len(ws))]
        if corner is not None:
            self.rect(x, y, label_w - 0.08, 0.5, fill=C.PALE, text=corner, size=17, color=C.BAND, bold=True, name=TABLE_NAMES[0])
        for j, h in enumerate(header):
            self.rect(xs[j], y, ws[j], 0.5, fill=C.PALE, text=h, size=17, color=C.BAND, bold=True, name=TABLE_NAMES[0])
        yy = y + 0.58
        for lab, cells in rows:
            if label_w:
                self.rect(x, yy, label_w - 0.08, row_h, fill=C.PALE, text=lab, size=size, color=C.BAND, bold=True, name=TABLE_NAMES[1])
            for j, cell in enumerate(cells):
                self.rect(xs[j], yy, ws[j], row_h, fill=C.LIGHT, text=cell, size=size, align="l", name=TABLE_NAMES[2])
            yy += row_h + 0.08
        return yy

    def flow(self, items: list, x: float, y: float, w: float, h: float = 0.9, gap: float = 0.75,
             direction: str = "down", size: float = 18, arrow_labels: list | None = None,
             last_fill: str | None = None) -> Box:
        """箱と水色のブロック矢印でつないだ流れ図（PowerPointの図形なので後で編集できる）。
        items = ["資料を読む\\n（PDF・講義メモ）", "構成案", "スライド"]。
        direction="down" は縦に、"right" は横に並べる。arrow_labels で矢印の横に注記（例 ["較正", None]）。
        最後の箱だけ薄灰（結果・行き先）、ほかは薄青。"""
        n = len(items)
        aw, ah = (0.6, gap - 0.15) if direction == "down" else (gap - 0.15, 0.6)
        for k, text in enumerate(items):
            if direction == "down":
                bx, by = x, y + k * (h + gap)
            else:
                bx, by = x + k * (w + gap), y
            self.rect(bx, by, w, h, fill=(last_fill or C.LIGHT) if k == n - 1 else C.PALE, text=text, size=size)
            if k < n - 1:
                if direction == "down":
                    ax_, ay_ = bx + w / 2 - aw / 2, by + h + 0.075
                    self.arrow(ax_, ay_, w=aw, h=ah, direction="down")
                    lab_xy = (ax_ + aw + 0.1, ay_ + ah / 2 - 0.2)
                else:
                    ax_, ay_ = bx + w + 0.075, by + h / 2 - ah / 2
                    self.arrow(ax_, ay_, w=aw, h=ah, direction="right")
                    lab_xy = (ax_ - 0.05, ay_ - 0.45)
                if arrow_labels and k < len(arrow_labels) and arrow_labels[k]:
                    self.text(lab_xy[0], lab_xy[1], arrow_labels[k], size=16)
        if direction == "down":
            return Box(x, y, w, n * h + (n - 1) * gap)
        return Box(x, y, n * w + (n - 1) * gap, h)

    def line(self, x1, y1, x2, y2, color: str = C.TEXT, width: float = 1.5, dash: bool = False):
        ln = self.slide.shapes.add_connector(1, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
        ln.line.color.rgb = RGBColor.from_string(color)
        ln.line.width = Pt(width)
        if dash:
            ln.line.dash_style = 4
        return ln

    def oval(self, x: float, y: float, w: float, h: float, color: str = C.RED, width: float = 2.75) -> Box:
        """塗りなしの輪。教科書の図の注目点（はい上がりの縁など）に重ねて「ここ」を示す。
        過去の輪読のデッキの形（赤 FF0000、0.57×0.49 in、線 2.75pt）。図の上に重ねるものなので、
        名前を「注目の輪」にして check_layout の重なり検査から外している。"""
        sh = self.slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x), Inches(y), Inches(w), Inches(h))
        sh.name = "注目の輪"
        sh.fill.background()
        sh.line.color.rgb = RGBColor.from_string(color)
        sh.line.width = Pt(width)
        style = sh._element.find(qn("p:style"))
        if style is not None:
            sh._element.remove(style)
        box = Box(x, y, w, h)
        self.boxes.append(("shape", box))
        return box

    def note(self, x: float, y: float, text: str, size: float = 16, color: str | None = None,
             align: str = "l", bg: bool = True) -> Box:
        """論文・教科書の図の上に重ねる注記（読み方のラベル「立方晶の位置」「[012]：増加」など）。
        bg=True で白く塗って下の図から浮かせる。名前を「注目の注記」にして重なり検査・本文の字数から外す。
        ラベルは名詞だけ、16pt 前後、赤は結論に関わる1〜2か所（figures.md 2節）。"""
        b = self.text(x, y, text, size=size, color=color, align=align, name="注目の注記")
        if bg:
            sh = self.slide.shapes[-1]
            sh.fill.solid()
            sh.fill.fore_color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        return b

    def pointer(self, x1, y1, x2, y2, color: str = C.RED, width: float = 2.0, head: bool = True, dash: bool = False):
        """図の注目点を指す線（(x2, y2) の側に矢じり）。補助線は head=False, dash=True。
        名前を「注目の矢印」にして重なり検査から外す。"""
        ln = self.line(x1, y1, x2, y2, color=color, width=width, dash=dash)
        ln.name = "注目の矢印"
        if head:
            from pptx.oxml.ns import qn as _qn
            from lxml import etree
            a_ln = ln.line._get_or_add_ln()
            tail = etree.SubElement(a_ln, _qn("a:tailEnd"))
            tail.set("type", "triangle")
            tail.set("w", "med")
            tail.set("len", "med")
        return ln

    def defs(self, x: float, y: float, items: list, size: float = 18, sep: str = "：") -> Box:
        """数式の右に変数の定義を縦に並べる（過去の輪読のデッキの「γ：表面張力」「ρ：液体の密度」）。
        items = [("γ", "表面張力"), ("ρ", "液体の密度")]。記号は自動でイタリック（{i:}）、全角「：」で区切る。
        記号に上下付きを含めてよい（("m_{4}", "^{4}Heの質量")）。元デッキは20pt。18pt は「定義の補足」として許される下限。
        置き方: e = s.peq(...) のあと s.defs(e.right + 0.4, e.y, [...]) のように数式の右・同じ高さに。"""
        text = "\n".join(f"{{i:{sym}}}{sep}{desc}" for sym, desc in items)
        return self.text(x, y, text, size=size, name="定義")

    def notes(self, text: str):
        """発表者ノート（話す内容のメモ）。スライド上には出ない。"""
        self.slide.notes_slide.notes_text_frame.text = text

    # -- スライドの型（references/figures.md「スライドの型」）。「左に文・右に図」だけが続かないように、内容で選ぶ
    def figure_below(self, path, gap: float = 0.35, caption: str | None = None, name: str = "下の図") -> Box:
        """上に文・下に横長の図の型（横長のグラフ・時系列・2枚並べた図）。本文のカーソルの下に、図を中央に置く（描いた幅のまま）。"""
        with Image.open(path) as im:
            pw, ph_ = im.size
            dpi = (im.info.get("dpi") or (0, 0))[0]
        w = pw / dpi if dpi and dpi >= 100 else 8.0
        wx0, wx1 = self.deck.wide
        # 柱のある構造では、本文は柱の中にあるので、図は右の白い所の上（本文の上端）から置く。カーソルの下に置くと、
        # 柱の文の下まで図が下がって右の上が空き、幅 8 in の図は柱にかかっていた（check_layout の構造の検査で見つけた）
        col = "text_right" in self.deck.area and self.cur_x < self.deck.area["text_right"]
        top = self.deck.area["top"] if col else self.cur_y + gap
        w = min(w, wx1 - wx0)                          # 横いっぱいの範囲（deck.wide）に収める
        h = w * ph_ / pw
        room = self.deck.content_bottom - top - (0.35 if caption else 0)
        if h > room:                                   # 入らなければ高さに合わせて縮める（文字が小さくなるので WARN が出る）
            w, h = w * room / h, room
        b = self.image(path, (wx0 + wx1 - w) / 2, top, w=w, h=h, name=name)
        if caption:
            self.caption(b, caption)
        if not col:
            self.cur_y = b.bottom
        return b

    def figure_beside(self, path, y: float | None = None, caption: str | None = None, gap: float = 0.75,
                      name: str = "右の図") -> Box:
        """左に文・右に図の型。図は描いた幅のまま、本文の右に置く（本文の右端から gap 以上空け、空きが大きければ
        本文と図の間と図の右を半分ずつに）。柱のある構造では右の白い所（fig_x）から。y を省けば本文の上端。"""
        with Image.open(path) as im:
            pw, ph_ = im.size
            dpi = (im.info.get("dpi") or (0, 0))[0]
        w = pw / dpi if dpi and dpi >= 100 else 5.0
        a = self.deck.area
        right = a["right"]
        texts = [b for kind, b in self.boxes if kind != "image" and b.y > a["top"] - 0.3]
        tr = max((b.right for b in texts), default=a.get("fig_x", right - w) - gap)
        x = min(tr + max(gap, (right - w - tr) / 2), right - w)
        if "text_right" in a:
            x = max(x, a["fig_x"])
        b = self.image(path, x, a["top"] if y is None else y, name=name)
        if caption:
            self.caption(b, caption)
        return b

    def compare(self, left: tuple, right: tuple, y: float | None = None, size: float = 20, gap: float = 0.6) -> list:
        """2つを並べて比べる型（手法の比較・前と後・長所と短所）。left/right = ("小見出し", ["要点", ...])。
        左右同じ幅で、上に小見出しの帯、間に縦の区切り線。戻り値は左右の下端。"""
        y = self.deck.area["top"] + 0.1 if y is None else y
        wx0, wx1 = self.deck.wide
        col_w = (wx1 - wx0 - gap) / 2
        bottoms = []
        for k, (head, items) in enumerate((left, right)):
            x = wx0 + k * (col_w + gap)
            self.rect(x, y, col_w, 0.55, fill=C.PALE, text=head, size=20, color=C.BAND, bold=True)
            yy = y + 0.8
            for it in items:
                b = self.text(x + 0.15, yy, it, size=size, name="比較の" + ("左" if k == 0 else "右"))
                yy = b.bottom + 0.2
            bottoms.append(yy)
        self.line(wx0 + col_w + gap / 2, y, wx0 + col_w + gap / 2, max(bottoms), color=C.GRAY, width=1.0)
        return bottoms

    def key_message(self, big: str, sub: str | None = None, size: float = 54, y: float = 2.5) -> Box:
        """大きな数字・結論を1つだけ見せる型（一番伝えたい値・結論）。中央に大きく、下に短い説明。1回のデッキで1〜2枚まで。"""
        lines = split_lines(parse_markup(big))
        tw = max(text_width_pt(l, size) for l in lines) / 72.0 + 2 * INSET_X + 0.1
        cx = sum(self.deck.wide) / 2
        b = self.text(cx - tw / 2, y, big, size=size, bold=True, align="c", w=tw, color=C.BAND, name="大きな数字")
        if sub:
            sl = split_lines(parse_markup(sub))
            sw = max(text_width_pt(l, 22) for l in sl) / 72.0 + 2 * INSET_X + 0.1
            b = self.text(cx - sw / 2, b.bottom + 0.35, sub, size=22, align="c", w=sw, name="大きな数字の説明")
        return b

    def full_figure(self, path, caption: str | None = None, top: float | None = None, name: str = "全面の図") -> Box:
        """全面の図の型（図そのものが主張のとき）。見出しの下いっぱいに、図を中央に置く。本文は書かず、言うことはノートに。"""
        top = self.deck.area["top"] - 0.15 if top is None else top
        with Image.open(path) as im:
            pw, ph_ = im.size
        room_h = self.deck.content_bottom - top - (0.35 if caption else 0)
        wx0, wx1 = self.deck.wide
        room_w = min(wx1 - wx0, SLIDE_W - 2 * 0.8)
        w = min(room_w, room_h * pw / ph_)
        h = w * ph_ / pw
        b = self.image(path, (wx0 + wx1 - w) / 2, top, w=w, h=h, name=name)
        if caption:
            self.caption(b, caption)
        return b

    # -- 本文の形（文字の塊の組み方。scripts/structures.py・references/structures.md）
    # 位置 x, y を省くとカーソル（s.at）から置く。置いたあとはカーソルを塊の下へ進める（続けて s.p や次の塊を置ける）。
    # 図形の名前（塊の見出し・帰結・展開の左…）で、渡す前の確認が構成案の「本文の形」と突き合わせる
    def _xy(self, x, y):
        return (self.cur_x if x is None else x), (self.cur_y if y is None else y)

    def _label(self, head: str) -> str:
        """ラベル（小見出し）と問いの書き方。テンプレートの .json の label_style（b＝太字〔既定〕／u＝下線／r＝赤／a＝主色／plain）。
        既定は太字：下線を付けると1枚に3〜4か所並び、指してほしい語の下線が埋もれた（下線は1枚2か所まで。check_layout）。"""
        st = self.deck.style.get("label_style", "b")
        return head if st == "plain" else "{%s:%s}" % (st if st in FLAG_STYLES else "b", head)

    @staticmethod
    def _lines(lines) -> str:
        return lines if isinstance(lines, str) else "\n".join(lines)

    def _text_w(self, text: str, size: float) -> float:
        return max((text_width_pt(l, size) for l in split_lines(parse_markup(text))), default=0) / 72.0 + 2 * INSET_X + 0.05

    def thin_arrow(self, x1, y1, x2, y2, color: str | None = None, width: float = 2.25, head: bool = True):
        """細い矢印（線＋矢じり）。カードの順序・循環に。矢印は主役ではないので、太いブロック矢印より目立たせない。"""
        ln = self.line(x1, y1, x2, y2, color=color or C.ARROW, width=width)
        ln.name = "矢印"
        if not head:
            return ln
        from lxml import etree
        tail = etree.SubElement(ln.line._get_or_add_ln(), qn("a:tailEnd"))
        tail.set("type", "triangle"); tail.set("w", "med"); tail.set("len", "med")
        return ln

    def _flow_arrow(self, x, y, w, h, direction):
        """塊をつなぐ矢印。テンプレートの .json で "arrow": "thin" なら細い矢印、既定はブロック矢印。"""
        if self.deck.style.get("arrow") == "thin":
            if direction == "down":
                self.thin_arrow(x + w / 2, y, x + w / 2, y + h)
            else:
                self.thin_arrow(x, y + h / 2, x + w, y + h / 2)
            return Box(x, y, w, h)
        return self.arrow(x, y, w=w, h=h, direction=direction)

    def block(self, head: str | None, lines=(), then: str | None = None, x: float | None = None, y: float | None = None,
              size: float = 20, indent: float = 0.35, gap: float = 0.35, name: str | None = None) -> Box:
        """ラベル＋説明の塊：小見出し（下線）の下に、説明を字下げして1〜3行。then で最後に「⇒ 赤字の帰結」。
        head=None なら字下げせずに説明だけ（= s.lead）。"""
        x, y = self._xy(x, y)
        parts, yy = [], y
        dx = indent if head else 0.0
        if head:
            b = self.text(x, yy, self._label(head), size=size, name=name or "塊の見出し")
            parts.append(b); yy = b.bottom
        if lines:
            b = self.text(x + dx, yy, self._lines(lines), size=size, name=name or "塊の本文")
            parts.append(b); yy = b.bottom
        if then:
            b = self.text(x + dx, yy + 0.05, "⇒ {r:" + then + "}", size=size, name=name or "帰結")
            parts.append(b); yy = b.bottom
        box = Box(x, y, max(p.right for p in parts) - x, yy - y)
        self.cur_x, self.cur_y = x, yy + gap
        return box

    def lead(self, lines, then: str, **kw) -> Box:
        """前提 ⇒ 帰結：2〜3行の説明のあと「⇒ 赤字の一言」（その塊の結論）。"""
        return self.block(None, lines, then=then, **kw)

    def ask(self, question: str, answer: str, x: float | None = None, y: float | None = None,
            size: float = 20, indent: float = 0.35, gap: float = 0.35) -> Box:
        """問い → 答え：「〜ではないのか？」（ラベルと同じ太字）の下に「⇒ 確かめた結果」。別の説明を1つずつ確かめる検証の筋に。"""
        x, y = self._xy(x, y)
        q = self.text(x, y, self._label(question), size=size, name="問い")
        a = self.text(x + indent, q.bottom + 0.05, "⇒ " + answer, size=size, name="答え")
        self.cur_x, self.cur_y = x, a.bottom + gap
        return Box(x, y, max(q.right, a.right) - x, a.bottom - y)

    def develop(self, left, right, x: float | None = None, y: float | None = None, size: float = 20,
                gap: float = 0.35, arrow_w: float = 0.6, after: float = 0.35) -> Box:
        """横の矢印で展開：左に条件・前の状態、右に結果・次の状態。left/right は文字列か (ラベル, [行])。
        右を赤字にするなら "{r:…}" で。左右の塊の高さの中ほどに矢印を置く。"""
        x, y = self._xy(x, y)

        def put(item, xx, nm):
            if isinstance(item, tuple):
                return self.block(item[0], item[1], x=xx, y=y, size=size, name=nm, gap=0)
            return self.text(xx, y, self._lines(item), size=size, name=nm)

        L = put(left, x, "展開の左")
        ax = L.right + gap
        R = put(right, ax + arrow_w + gap, "展開の右")
        bottom = max(L.bottom, R.bottom)
        self._flow_arrow(ax, (y + bottom) / 2 - 0.27, arrow_w, 0.55, "right")
        self.cur_x, self.cur_y = x, bottom + after
        return Box(x, y, R.right - x, bottom - y)

    def conclude_box(self, text: str, x: float | None = None, y: float | None = None, w: float | None = None,
                     cx: float | None = None, size: float = 22, name: str = "結論の囲み", outline: bool = False) -> Box:
        """結論の囲み：淡い橙（C.CONCLUDE）の塗りだけの箱に1〜2行。帯の無い骨格では、下の帯の代わりにスライドの結論を入れる。
        outline=True なら塗らずに細い濃い色（C.BAND）の線だけ（本文の中の結論。s.lead_down が使う）。
        塗りの囲みはスライドの結論の置き場（下の囲み）だけにして、本文の囲みと見分けられるようにする。"""
        lines = split_lines(parse_markup(text))
        w = w or (max(text_width_pt(l, size) for l in lines) / 72.0 + 0.7)
        h = len(lines) * line_height_in(size) + 0.3
        x, y = self._xy(x, y)
        if cx is not None:
            x = cx - w / 2
        if outline:
            b = self.rect(x, y, w, h, fill=None, line=C.BAND, text=text, size=size, color=C.TEXT, bold=True, name=name)
        else:
            b = self.rect(x, y, w, h, fill=C.CONCLUDE, text=text, size=size, color=C.TEXT, bold=True, name=name)
        self.cur_y = b.bottom + 0.35
        return b

    def lead_down(self, premise, conclusion: str, boxed: bool = True, x: float | None = None, y: float | None = None,
                  w: float | None = None, size: float = 20, gap: float = 0.2) -> Box:
        """縦の矢印で結論へ：前提の段（中央ぞろえ）↓ 結論（線だけの囲み。boxed=False なら赤字）。
        囲みは塗らない（塗りの囲みは結論の囲みの構造でスライドの結論の置き場なので、それと見分けるため）。
        学会発表の導入（背景 → 目的）やまとめに。w は中央ぞろえにする幅（既定は x からスライドの右の余白まで）。"""
        x, y = self._xy(x, y)
        w = w or (self.deck.x1 - x)
        cx = x + w / 2
        pt = self._lines(premise)
        tw = self._text_w(pt, size)
        p = self.text(cx - tw / 2, y, pt, size=size, align="c", w=tw, name="縦の前提")
        a = self._flow_arrow(cx - 0.3, p.bottom + gap, 0.6, 0.45, "down")
        if boxed:
            c = self.conclude_box(wrap_to(conclusion, w - 0.7, size + 2), y=a.bottom + gap, cx=cx, size=size + 2,
                                  outline=True)   # 幅 w に入るように。線だけ（下の結論の囲みと見分ける）
        else:
            ct = "{r:" + conclusion + "}"
            cw = self._text_w(ct, size + 2)
            c = self.text(cx - cw / 2, a.bottom + gap, ct, size=size + 2, align="c", w=cw, bold=True, name="縦の結論")
        self.cur_x, self.cur_y = x, c.bottom + 0.35
        return Box(x, y, w, c.bottom - y)

    def cases(self, items: list, x: float | None = None, y: float | None = None, w: float | None = None,
              size: float = 20, boxed: bool = True) -> Box:
        """条件の場合分け：items = [("T > T_λ", "純粋液体の ^{4}He と同様"), ...]。条件は太字、説明は字下げ。
        boxed=True で全体を薄い灰の囲みに（灰色の角丸箱。過去の輪読のデッキの形）。"""
        x, y = self._xy(x, y)
        rows = []
        for k, (cond, desc) in enumerate(items):
            if k:
                rows.append("")
            rows.append("{b:" + cond + "}")
            rows += ["　" + l for l in self._lines(desc).split("\n")]
        text = "\n".join(rows)
        w = w or (self._text_w(text, size) + 0.4)
        h = len(rows) * line_height_in(size) + 0.35
        if boxed:
            b = self.rect(x, y, w, h, fill=C.LIGHT, text=text, size=size, color=C.TEXT, align="l", anchor="t", name="場合分け")
        else:
            b = self.text(x, y, text, size=size, name="場合分け")
        self.cur_x, self.cur_y = x, b.bottom + 0.35
        return b

    def numbered(self, items: list, x: float | None = None, y: float | None = None, size: float = 20,
                 gap: float = 0.35) -> Box:
        """番号の手順：1. 2. 3.（項目の2行目は字下げ）。解析・試料作成・測定の手順に。"""
        x, y = self._xy(x, y)
        rows = []
        for k, it in enumerate(items, 1):
            first, *rest = self._lines(it).split("\n")
            rows.append(f"{k}. {first}")
            rows += ["　 " + r for r in rest]
        b = self.text(x, y, "\n".join(rows), size=size, name="手順")
        self.cur_x, self.cur_y = x, b.bottom + gap
        return b

    # -- 図解の型（references/structures.md）。カードは薄い灰の塗りだけ（線なし）、見出しは主色の太字
    def _card_h(self, items, size, pad=0.45):
        """カードの中身（見出し1行＋説明の行数）の一番多いものに合わせた高さ。"""
        n = max(1 + (len(self._lines(it[1]).split("\n")) if isinstance(it, tuple) and it[1] else 0) for it in items)
        return n * line_height_in(size) + pad

    def _card(self, x, y, w, h, item, kind, size):
        head, body = item if isinstance(item, tuple) else (item, "")
        text = "{ab:" + head + "}" + ("\n" + self._lines(body) if body else "")
        return self.rect(x, y, w, h, fill=C.LIGHT, text=text, size=size, color=C.TEXT, align="l", anchor="t",
                         name=f"カード_{kind}")

    def cards(self, items: list, layout: str = "row", x: float | None = None, y: float | None = None,
              w: float | None = None, h: float | None = None, size: float = 18, gap: float = 0.3) -> Box:
        """カードの図解。items = [("見出し", "説明1行\\n説明2行"), ...]。layout:
        row＝横に並べる並列（2〜4枚）、grid＝2列の格子（4〜6枚）、steps＝段違いの順序（3〜4枚、細い矢印）、
        cycle＝循環（4枚を2×2に、時計回りの細い矢印）。"""
        kind = {"row": "並列", "grid": "格子", "steps": "段違い", "cycle": "循環"}[layout]
        x = self.deck.wide[0] if x is None else x
        y = self.cur_y if y is None else y
        w = w or (self.deck.x1 - x)
        n = len(items)
        bottom = self.deck.content_bottom
        if layout == "row":
            cw = (w - gap * (n - 1)) / n
            ch = h or max(1.3, self._card_h(items, size, pad=0.6))
            for k, it in enumerate(items):
                self._card(x + k * (cw + gap), y, cw, ch, it, kind, size)
            box = Box(x, y, w, ch)
        elif layout == "grid":
            cols = 2 if n <= 4 else 3
            nrow = (n + cols - 1) // cols
            cw = (w - gap * (cols - 1)) / cols
            ch = h or min(max(1.1, self._card_h(items, size)), (bottom - y - gap * (nrow - 1)) / nrow)
            for k, it in enumerate(items):
                r, c = divmod(k, cols)
                self._card(x + c * (cw + gap), y + r * (ch + gap), cw, ch, it, kind, size)
            box = Box(x, y, w, nrow * ch + (nrow - 1) * gap)
        elif layout == "steps":
            cw = w * (0.46 if n <= 3 else 0.4)
            ch = h or self._card_h(items, size, pad=0.35)
            dx = (w - cw) / (n - 1)
            dy = min(ch + 0.3, (bottom - y - ch) / (n - 1))
            for k, it in enumerate(items):
                self._card(x + k * dx, y + k * dy, cw, ch, it, kind, size)
                if k < n - 1:   # 前のカードの下から、次のカードの左へ折れる細い矢印
                    ax = x + k * dx + min(0.45, dx * 0.3)
                    ny = y + (k + 1) * dy + ch / 2
                    self.thin_arrow(ax, y + k * dy + ch + 0.04, ax, ny, head=False)
                    self.thin_arrow(ax, ny, x + (k + 1) * dx - 0.06, ny)
            box = Box(x, y, w, (n - 1) * dy + ch)
        else:   # cycle
            if n != 4:
                raise ValueError("cycle は4枚（2×2）で使う")
            g2 = 0.7
            cw = (w - g2) / 2
            ch = h or min(max(1.1, self._card_h(items, size)), (bottom - y - g2) / 2)
            pos = [(x, y), (x + cw + g2, y), (x + cw + g2, y + ch + g2), (x, y + ch + g2)]
            for k, (px, py) in enumerate(pos):
                self._card(px, py, cw, ch, items[k], kind, size)
            m = 0.1
            self.thin_arrow(x + cw + m, y + ch / 2, x + cw + g2 - m, y + ch / 2)
            self.thin_arrow(x + cw + g2 + cw / 2, y + ch + m, x + cw + g2 + cw / 2, y + ch + g2 - m)
            self.thin_arrow(x + cw + g2 - m, y + ch + g2 + ch / 2, x + cw + m, y + ch + g2 + ch / 2)
            self.thin_arrow(x + cw / 2, y + ch + g2 - m, x + cw / 2, y + ch + m)
            box = Box(x, y, w, 2 * ch + g2)
        self.cur_x, self.cur_y = x, box.bottom + 0.35
        return box

    def tree(self, root: str, children: list, x: float | None = None, y: float | None = None,
             root_w: float = 2.6, child_w: float = 4.2, h: float = 0.62, gap: float = 0.22, size: float = 18) -> Box:
        """ツリー：左に大分類、右に小分類を縦に並べ、折れ線でつなぐ（分類・階層）。children は文字列か (見出し, 説明)。"""
        x = self.deck.wide[0] if x is None else x
        y = self.cur_y if y is None else y
        n = len(children)
        total = n * h + (n - 1) * gap
        ry = y + total / 2 - h / 2
        self.rect(x, ry, root_w, h, fill=C.PALE, text="{b:" + root + "}", size=size, color=C.TEXT, name="ツリー")
        cx = x + root_w + 0.9
        jx = x + root_w + 0.45
        self.line(x + root_w, ry + h / 2, jx, ry + h / 2, color=C.GRAY, width=1.5)
        self.line(jx, y + h / 2, jx, y + total - h / 2, color=C.GRAY, width=1.5)
        for k, ch in enumerate(children):
            cy = y + k * (h + gap)
            text = ch if isinstance(ch, str) else "{b:" + ch[0] + "}　" + ch[1]
            self.rect(cx, cy, child_w, h, fill=C.LIGHT, text=text, size=size, color=C.TEXT, align="l", name="ツリー")
            self.line(jx, cy + h / 2, cx, cy + h / 2, color=C.GRAY, width=1.5)
        self.cur_x, self.cur_y = x, y + total + 0.35
        return Box(x, y, cx + child_w - x, total)

    def before_after(self, before: tuple, after: tuple, value: str | None = None, y: float | None = None,
                     h: float | None = None, size: float = 20) -> Box:
        """前後（ビフォーアフター）：左に従来（灰）、右にこの研究・改善（薄い主色）、間に矢印、右の下に差を赤い数値1つで。
        before/after = ("見出し", ["要点", ...])。"""
        y = self.cur_y if y is None else y
        gap = 1.0
        wx0, wx1 = self.deck.wide
        cw = (wx1 - wx0 - gap) / 2
        nl = max(1 + len(self._lines(side[1]).split("\n")) for side in (before, after))
        h = h or min(max(1.6, nl * line_height_in(size) + 0.6), self.deck.content_bottom - y - (0.7 if value else 0))
        for k, (head, lines) in enumerate((before, after)):
            px = wx0 + k * (cw + gap)
            text = "{ab:" + head + "}\n" + self._lines(lines)
            self.rect(px, y, cw, h, fill=C.LIGHT if k == 0 else C.PALE, text=text, size=size, color=C.TEXT,
                      align="l", anchor="t", name="前後_" + ("前" if k == 0 else "後"))
        self._flow_arrow(wx0 + cw + 0.2, y + h / 2 - 0.27, gap - 0.4, 0.55, "right")
        bottom = y + h
        if value:
            vt = "{r:" + value + "}"
            vw = self._text_w(vt, 26)
            b = self.text(wx0 + cw + gap + (cw - vw) / 2, y + h + 0.1, vt, size=26, bold=True, align="c", w=vw, name="前後の値")
            bottom = b.bottom
        self.cur_y = bottom + 0.35
        return Box(wx0, y, wx1 - wx0, bottom - y)

    def pair(self, left, right, labels: list | None = None, values: list | None = None, y: float | None = None,
             caption: str | None = None, gap: float = 0.6) -> Box:
        """2つ並べた図：条件の違う2つの図を左右に（描いた幅のまま。入らなければ縮める）、上にラベル、下に赤い数値。
        条件の違う2つの図を並べ、下に比べる数値を置く形。"""
        y = self.cur_y if y is None else y
        top = y + (0.5 if labels else 0)
        sizes = []
        for p in (left, right):
            with Image.open(p) as im:
                pw, ph_ = im.size
                dpi = (im.info.get("dpi") or (0, 0))[0]
            w = pw / dpi if dpi and dpi >= 100 else 5.0
            sizes.append((w, w * ph_ / pw))
        wx0, wx1 = self.deck.wide
        room_w = (wx1 - wx0 - gap) / 2
        room_h = self.deck.content_bottom - top - (0.55 if values else 0) - (0.35 if caption else 0)
        out = []
        for k, (p, (w, h)) in enumerate(zip((left, right), sizes)):
            s = min(1.0, room_w / w, room_h / h)
            w, h = w * s, h * s
            px = wx0 + k * (room_w + gap) + (room_w - w) / 2
            b = self.image(p, px, top, w=w, h=h, name="並べた図")
            out.append(b)
            if labels and labels[k]:
                lw = self._text_w(labels[k], 20)
                self.text(b.x + (w - lw) / 2, y, labels[k], size=20, align="c", w=lw, name="並べた図のラベル")
            if values and values[k]:
                vt = "{r:" + values[k] + "}"
                vw = self._text_w(vt, 20)
                self.text(b.x + (w - vw) / 2, b.bottom + 0.08, vt, size=20, bold=True, align="c", w=vw, name="並べた図の値")
        bottom = max(b.bottom for b in out) + (0.55 if values else 0)
        if caption:   # 数値の行の下、右の図の右端にそろえる
            cw_ = self._text_w(caption, 14)
            cb = self.text(out[-1].right - cw_, bottom, caption, size=14, color=C.GRAY)
            bottom = cb.bottom
        self.cur_y = bottom + 0.3
        return Box(wx0, y, wx1 - wx0, bottom - y)

    def callout(self, target: tuple, at: tuple, text: str, size: float = 18) -> Box:
        """図の注目点への吹き出し：at=(x, y) に薄い主色の箱で解釈を書き、target=(x, y)（図の中の点）へ細い線を引く。
        図に重ねてよい部品なので、名前を「注目の吹き出し」「注目の矢印」にして重なり検査から外す。1枚に1〜2個まで。"""
        w = self._text_w(text, size) + 0.2
        h = len(split_lines(parse_markup(text))) * line_height_in(size) + 0.22
        b = self.rect(at[0], at[1], w, h, fill=C.PALE, text=text, size=size, color=C.TEXT, align="l", name="注目の吹き出し")
        ex = b.x if target[0] < b.x else b.right
        self.pointer(ex, b.cy, target[0], target[1], color=C.BAND, width=1.5)
        return b

    # -- 流し込みレイアウト（上から順に置く）
    def at(self, x: float, y: float):
        self.cur_x, self.cur_y = x, y
        return self

    def skip(self, dy: float):
        self.cur_y += dy
        return self

    def p(self, text: str, dx: float = 0.0, gap: float = 0.3, size: float = 20, **kw) -> Box:
        """カーソル位置にテキストを置き、下へ進める。dx はカーソルxからの字下げ。"""
        b = self.text(self.cur_x + dx, self.cur_y, text, size=size, **kw)
        self.cur_y = b.bottom + gap
        return b

    def peq(self, latex: str, dx: float = 0.4, gap: float = 0.3, size: float = 20, color: str | None = None) -> Box:
        b = self.eq(latex, self.cur_x + dx + INSET_X, self.cur_y + 0.03, size=size, color=color)
        self.cur_y = b.bottom + gap
        return b

    def prow(self, parts: list, dx: float = 0.0, gap: float = 0.3, size: float = 20) -> Box:
        b = self.row(self.cur_x + dx, self.cur_y, parts, size=size)
        self.cur_y = b.bottom + gap
        return b


CONTENT_LAYOUT_NAMES = ("本文", "タイトルのみ", "Title Only")
TITLE_LAYOUT_NAMES = ("表紙", "1_タイトルのみ", "タイトル スライド", "Title Slide")
PLAIN_LAYOUT_NAME = "本文（帯なし）"   # 帯も●も無い枚のレイアウト（同梱のテンプレートにある。無ければ本文のレイアウトで帯を消す）
PLAIN_MARK = "帯なし"                  # その枚の名前（slide.name）。結論の一文の決まりの例外の印
_PH_MINOR = (PP_PLACEHOLDER.SLIDE_NUMBER, PP_PLACEHOLDER.DATE, PP_PLACEHOLDER.FOOTER)


def band_placeholder_idx(layout, slide_h):
    """レイアウトの下部の青帯のまとめ文の枠（下 2割にある本文プレースホルダ）の idx。無ければ None。"""
    for ph in layout.placeholders:
        if ph.placeholder_format.type == PP_PLACEHOLDER.BODY and ph.top > 0.8 * slide_h:
            return ph.placeholder_format.idx
    return None


def pick_layouts(prs, content=None, title=None):
    """本文用と表紙用のレイアウトを選ぶ。名前の指定（テンプレート一覧の「本文のレイアウト」など）が最優先、
    次に既定の名前（同梱テンプレートの「タイトルのみ」「1_タイトルのみ」、英語版の Title Only / Title Slide）、
    無ければ形で選ぶ：本文用＝タイトル枠があり他の枠が一番少ないもの、表紙用＝中央タイトル枠のあるもの。
    ユーザーが自分のデッキから作ったテンプレート（make_template.py）でも動くように。"""
    layouts = list(prs.slide_layouts)

    def by_name(names):
        for n in names:
            for l in layouts:
                if l.name == n:
                    return l
        return None

    def n_main(l):
        h = prs.slide_height
        return sum(ph.placeholder_format.type not in _PH_MINOR + (PP_PLACEHOLDER.TITLE,)
                   and ph.placeholder_format.idx != band_placeholder_idx(l, h) for ph in l.placeholders)

    if content:
        lc = by_name([content])
        if lc is None:
            raise KeyError(f"レイアウト {content!r} がテンプレートにありません: {[l.name for l in layouts]}")
    else:
        lc = by_name(CONTENT_LAYOUT_NAMES) or min(
            (l for l in layouts if any(p.placeholder_format.type == PP_PLACEHOLDER.TITLE for p in l.placeholders)),
            key=n_main, default=layouts[0])
    if title:
        lt = by_name([title])
        if lt is None:
            raise KeyError(f"レイアウト {title!r} がテンプレートにありません: {[l.name for l in layouts]}")
    else:
        lt = by_name(TITLE_LAYOUT_NAMES) or next(
            (l for l in layouts if any(p.placeholder_format.type == PP_PLACEHOLDER.CENTER_TITLE for p in l.placeholders)), lc)
    return lc, lt


class Deck:
    def __init__(self, template: str | Path = TEMPLATE, workdir: str | Path = "build",
                 content_layout: str | None = None, title_layout: str | None = None, color: str | None = None,
                 sections: list | None = None, valign: str | None = None):
        """template：構造（テンプレート1〜8 か追加したもの）。color：配色の名前（assets/templates/配色.json。省けば構造の標準の色）。
        sections：章のナビの構造で上に並べる章の名前（省けば、本文の枚のタイトルを出てきた順に）。"""
        self.prs = Presentation(str(template))
        self.workdir = Path(workdir)
        self.workdir.mkdir(parents=True, exist_ok=True)
        w, h = self.prs.slide_width / 914400, self.prs.slide_height / 914400
        if abs(w - SLIDE_W) > 0.05 or abs(h - SLIDE_H) > 0.05:
            print(f"[WARN] テンプレートの大きさ {w:.2f}×{h:.2f} in が 16:9（{SLIDE_W}×{SLIDE_H} in）でない。"
                  "部品の位置は 16:9 で決めてあるので、ずれる")
        self.style = template_style(template)
        if color and color != self.style.get("palette"):
            pal = palettes().get(color)
            if pal is None:
                raise KeyError(f"配色 {color!r} がない。使える配色: {list(palettes())}")
            self.style = dict(self.style, colors={**self.style.get("colors", {}), **pal["colors"]}, palette=color,
                              band_rules=self.style.get("nav", False))
            recolor(self.prs, self.style, pal)
        apply_template_colors(self.style)
        self.band_align = PP_ALIGN.LEFT if self.style.get("band_align") == "l" else PP_ALIGN.CENTER
        self.layout_content, self.layout_title = pick_layouts(self.prs, content_layout, title_layout)
        self.band_idx = band_placeholder_idx(self.layout_content, self.prs.slide_height)
        self.layout_plain = next((l for l in self.prs.slide_layouts if l.name == PLAIN_LAYOUT_NAME), None)
        # タイトルの枠の幅 (in) と文字の大きさ (pt)。見出しをタイトルの後ろに足すとき、枠に入るかを見る
        tph = next((ph for ph in self.layout_content.placeholders if ph.placeholder_format.type == PP_PLACEHOLDER.TITLE), None)
        self.title_w = tph.width / 914400 if tph is not None and tph.width else SLIDE_W - 1.2
        sz = self.prs.slide_master._element.xpath("./p:txStyles/p:titleStyle/a:lvl1pPr/a:defRPr/@sz")
        self.title_size = int(sz[0]) / 100 if sz and str(sz[0]).isdigit() else 32.0
        # 結論の置き場（骨格）：band＝下の帯（既定）、box＝下の帯の代わりに淡い橙の結論の囲み、
        # title＝上に小さく話題（タイトルの枠）、その下に大きく結論の一文（帯は無し）。テンプレートの .json の "conclusion"
        # lead＝タイトルの下の副題の1行、column＝左の柱の下。本文の場所はテンプレートの .json の "area"（構造ごとの割合）
        self.conclusion = self.style.get("conclusion", "band")
        self.area = body_area(self.style)
        self.x0, self.x1 = self.area["x"], self.area["right"]
        # 横いっぱいの部品（比べる・前後・2つ並べた図・大きな数字）の範囲。柱のある構造では右の白い所
        self.wide = (self.area["fig_x"], self.x1) if "text_right" in self.area else (self.x0, self.x1)
        self.content_bottom = self.area["bottom"]
        # 上の見出しの領域の下端：図を見出しの横まで上げてよい高さ（結論の一文が上にある構造では、本文の上端の少し上まで）。
        # ほかの構造ではタイトルの枠の下（+0.1 in）か 1.1 in の低くない方。章のナビの構造はタイトルが 0.6〜1.3 in と低く、
        # 1.1 in 固定のままだと、図を header_bottom に置くとタイトルの枠に食い込んでいた（check_layout の構造の検査で見つけた）
        title_bottom = max(((ph.top + ph.height) / 914400 for ph in self.layout_content.placeholders
                            if ph.placeholder_format.type == PP_PLACEHOLDER.TITLE and ph.top is not None and ph.height is not None),
                           default=0.9)
        self.header_bottom = (self.area["top"] - 0.15 if self.conclusion in ("title", "header", "lead")
                              else max(1.1, round(title_bottom + 0.1, 2)))
        self.sections = sections
        # 本文の縦の寄せ：下の帯の無い構造では、上寄せのままだと下が大きく空く（下の帯が下の重しになっていた見本を、
        # 帯の無い構造で組んだら下が空いた反省）。center＝本文の塊を、上の見出しの線から本文の下端までの間で縦の中央に
        self.valign = valign or self.style.get("valign") or ("center" if self.conclusion in ("title", "header", "lead", "box") else "top")
        self.slides: list[Slide] = []

    def _draw_band(self, slide, summary):
        """テンプレートに青帯の枠が無いとき、同じ位置に青帯（C.BAND の面）と白い太字のまとめ文を描く。名前は「青帯」。"""
        sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(BAND_TOP), Inches(SLIDE_W), Inches(SLIDE_H - BAND_TOP))
        sh.name = "青帯"
        sh.fill.solid(); sh.fill.fore_color.rgb = RGBColor.from_string(C.BAND)
        sh.line.fill.background()
        style = sh._element.find(qn("p:style"))
        if style is not None:
            sh._element.remove(style)
        tf = sh.text_frame
        tf.word_wrap = False
        self._set_placeholder_text(sh, summary, align=PP_ALIGN.CENTER)
        for p in tf.paragraphs:
            for r in p.runs:
                r.font.size = Pt(24); r.font.bold = True
                if not r.font.color or r.font.color.type is None:
                    r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    def _add_slide_number(self, slide, layout):
        for ph in layout.placeholders:
            if ph.placeholder_format.type == PP_PLACEHOLDER.SLIDE_NUMBER:
                slide.shapes.clone_placeholder(ph)
                sp = slide.shapes[-1]
                txBody = sp.text_frame._txBody
                p = txBody.find(qn("a:p"))
                for child in list(p):
                    p.remove(child)
                fld = p.makeelement(qn("a:fld"), {"id": "{189DD758-679A-0341-A1B9-815B1BDB6AE1}", "type": "slidenum"})
                rpr = fld.makeelement(qn("a:rPr"), {"lang": "ja-JP", "altLang": "en-US"})
                t = fld.makeelement(qn("a:t"), {})
                t.text = str(len(self.prs.slides))
                fld.append(rpr); fld.append(t); p.append(fld)
                return

    def _set_placeholder_text(self, ph, text: str, align=None, append: bool = False, size: float | None = None):
        tf = ph.text_frame
        lines = split_lines(parse_markup(text))
        for j, line in enumerate(lines):
            p = tf.paragraphs[-1] if append else tf.paragraphs[0] if j == 0 else tf.add_paragraph()
            if align is not None:
                p.alignment = align
            for r in line:
                run = p.add_run()
                run.text = r.text
                if size:
                    run.font.size = Pt(size)
                rPr = run._r.get_or_add_rPr()
                rPr.set("lang", "ja-JP"); rPr.set("altLang", "en-US")
                if r.baseline:
                    rPr.set("baseline", str(r.baseline))
                if r.color:
                    run.font.color.rgb = RGBColor.from_string(r.color)
                if r.i:
                    run.font.italic = True; run.font.name = "Times New Roman"

    def _cover_span(self, layout) -> tuple:
        """表紙の横の範囲 (in)：左右の端から全面の高さで伸びる飾り（柱・左の帯）を除いた所。題・著者をこの中央に置く。
        ページの中央に置くと、左の淡い柱の構造で題が柱の縁をまたいでいた（check_layout の構造の検査で見つけた）。"""
        x0, x1 = 0.0, SLIDE_W
        parts = ([] if layout._element.get("showMasterSp") == "0" else [layout.slide_master]) + [layout]
        for part in parts:
            for sh in part.shapes:
                if sh.is_placeholder or sh.height is None or sh.height < 0.9 * self.prs.slide_height:
                    continue
                left, right = sh.left / 914400, (sh.left + sh.width) / 914400
                if left <= 0.05:
                    x0 = max(x0, right)
                elif right >= SLIDE_W - 0.05:
                    x1 = min(x1, left)
        return x0, x1

    def title_slide(self, lines: list[str], author: str | None = None, subtitle: str | None = None,
                    size: float = 44, bold: bool = True) -> Slide:
        """表紙／区切りスライド（左上の縦棒だけのレイアウト）。lines は節番号付きの題目を1行ずつ。
        論文の表紙（過去の論文紹介のデッキの形）は lines に英題（2行まで）、subtitle に和訳（28pt）、author に著者名（20pt、\\n で2行）。
        元デッキの英題は太字でないので bold=False にする。"""
        slide = self.prs.slides.add_slide(self.layout_title)
        for ph in list(slide.placeholders):  # 空のタイトル枠は使わない（元デッキ同様テキストボックスで置く）
            ph._element.getparent().remove(ph._element)
        s = Slide(self, slide)
        text = "\n".join(lines)
        runs = split_lines(parse_markup(text))
        tw = max(text_width_pt(l, size) for l in runs) / 72.0 + 2 * INSET_X + 0.1
        th = len(runs) * line_height_in(size) * 0.95 + 2 * INSET_Y
        top = 2.44 if len(runs) >= 2 else 2.75
        x0, x1 = self._cover_span(self.layout_title)
        cx = (x0 + x1) / 2
        s.text(cx - tw / 2, top, text, size=size, bold=bold, align="c", w=tw)
        y = top + th + 0.25
        if subtitle:
            sw = max(text_width_pt(l, 28) for l in split_lines(parse_markup(subtitle))) / 72.0 + 0.3
            b = s.text(cx - sw / 2, y, subtitle, size=28, align="c", w=sw)
            y = b.bottom + 0.3
        if author:
            aw = text_width_pt(parse_markup(author), 20) / 72.0 + 0.3
            s.text(cx - aw / 2, max(y + 0.6, 4.98), author, size=20, align="c", w=aw)
        self._add_slide_number(slide, self.layout_title)
        self.slides.append(s)
        return s

    def slide(self, title: str, summary: str | None = None, section: str | None = None, plain: bool | None = None) -> Slide:
        """本文スライド（タイトル＋結論の置き場）。summary は「このスライドの結論」1文（下の帯・囲み・結論の一文・副題・柱の下。構造による）。
        section は章のナビの構造での今の章（省けば title）。
        summary の無い枚は、自動で帯も●も無い枚になる（「本文（帯なし）」のレイアウト。空の帯を出さない。plain で明示もできる）。
        結論が要るかは、構成案・設計メモの「役割」の列で決まる（本文だけが要る。渡す前の確認が structures.role_mismatches で突き合わせる）。"""
        if plain is None:
            plain = not summary
        if plain and summary:
            print(f"[WARN] 帯なしの枚「{title}」に summary がある → 帯なしの枚には結論を置かない（結論があるなら plain を外す）")
            summary = None
        slide = self.prs.slides.add_slide(self.layout_plain if plain and self.layout_plain is not None else self.layout_content)
        if plain:
            slide.name = PLAIN_MARK
        for ph in list(slide.placeholders):
            t = ph.placeholder_format.type
            if t == PP_PLACEHOLDER.TITLE:
                self._set_placeholder_text(ph, title)
            elif self.band_idx is not None and ph.placeholder_format.idx == self.band_idx:
                if summary:
                    self._set_placeholder_text(ph, summary, align=self.band_align)
                else:
                    ph._element.getparent().remove(ph._element)
            elif ph.placeholder_format.type not in _PH_MINOR:
                ph._element.getparent().remove(ph._element)   # 使わない空の枠（他のテンプレートの本文枠など）は消す
        s = Slide(self, slide)
        s._plain = plain
        if summary and self.band_idx is None:
            if self.conclusion == "box":
                s.conclude_box(summary, y=BOX_TOP, cx=SLIDE_W / 2)
            elif self.conclusion == "title":
                # 結論の一文がこの枚の見出し（名前「見出し」。●見出しは s.heading で、この下に小さく置ける）
                s.text(MESSAGE_POS[0], MESSAGE_POS[1], summary, size=28, bold=True, color=C.BAND, name="見出し")
                s._message = True
            elif self.conclusion == "header":   # 小さな話題の行の下に、大きく結論の一文（濃い墨。入らなければ少し小さく）
                mx, my = self.area.get("message", (0.66, 0.56))
                size = 28 if text_width_pt(parse_markup(summary), 28) / 72.0 < self.area["right"] - mx else 24
                s.text(mx, my + (0.04 if size == 24 else 0), summary, size=size, bold=True, color=C.TEXT, name="見出し")
                s._message = True
            elif self.conclusion == "lead":   # タイトルの下の副題の1行（差し色の太字、24pt）
                lx, ly = self.area.get("lead", (0.75, 0.98))
                # 差し色が白地で 4.5:1 に届かない配色（山吹・オレンジ・珊瑚）では主色で（山吹の副題は 2.0:1 で読めなかった）
                col = C.BULLET if contrast(C.BULLET, "FFFFFF") >= 4.5 else C.BAND
                s.text(lx, ly, summary, size=24, bold=True, color=col, name="見出し")   # この枚の見出しを兼ねる
                s._message = True
            elif self.conclusion == "column":  # 左の柱の、タイトルのすぐ下に結論（柱の幅で折り返す）、その下に差し色の線
                cx, cy, cw = self.area.get("column", (0.45, 1.05, 3.8))
                b = s.text(cx, cy, wrap_to(summary, cw, 20), size=20, bold=True, color=C.BAND, name="結論の一文")
                s.line(cx + 0.08, b.bottom + 0.1, cx + 1.2, b.bottom + 0.1, color=C.BULLET, width=3.0).name = "結論の線"
            else:
                self._draw_band(slide, summary)
        self._add_slide_number(slide, self.layout_content)
        s.cur_x, s.cur_y = self.area["x"], self.area["top"]
        s.section = section or title
        self.slides.append(s)
        return s

    def _draw_nav(self):
        """章のナビの構造：本文の枚の上に、章の名前を並べ、今の章を主色に（保存の前に、全部の章がそろってから描く）。"""
        body = [s for s in self.slides if getattr(s, "section", None)]
        names = self.sections or list(dict.fromkeys(s.section for s in body))
        if not names:
            return
        x0, x1, y, h, gap = 0.45, SLIDE_W - 0.45, 0.08, 0.38, 0.06
        w = (x1 - x0 - gap * (len(names) - 1)) / len(names)
        for s in body:
            for k, n in enumerate(names):
                cur = n == s.section
                s.rect(x0 + k * (w + gap), y, w, h, fill=C.BAND if cur else C.LIGHT, text=n, size=14,
                       color="FFFFFF" if cur else C.TEXT, bold=cur, name="章のナビ")

    def section(self, number, title: str, lead: str | None = None) -> Slide:
        """区切りの枚：全面を主色で塗り、章の番号と題（白）。独立した話が4つ以上の長い発表で、章の頭に。"""
        slide = self.prs.slides.add_slide(self.layout_title)
        for ph in list(slide.placeholders):
            ph._element.getparent().remove(ph._element)
        s = Slide(self, slide)
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, self.prs.slide_width, self.prs.slide_height)
        bg.name = "区切りの地"
        bg.fill.solid(); bg.fill.fore_color.rgb = RGBColor.from_string(C.BAND)
        bg.line.fill.background()
        style = bg._element.find(qn("p:style"))
        if style is not None:
            bg._element.remove(style)
        s.text(1.6, 2.9, f"{number}　{title}", size=40, bold=True, color="FFFFFF", name="区切り")
        if lead:
            s.text(1.6, 3.85, lead, size=22, color="FFFFFF", name="区切り")
        self.slides.append(s)
        return s

    def build_up(self, title: str, heading: str, items: list, summary: str | None = None,
                 size: float = 22, gap: float = 0.35, figure=None, fig_x: float = 7.6) -> list:
        """項目を1つずつ足していく枚（漸進表示）：items の数だけ枚を作り、k 枚目は k 個目までを出す。
        前の項目は灰色、今の項目だけ濃く。研究の要約・手順を1項目ずつ話すときに。figure で毎枚の右に同じ図。
        戻り値は作った Slide のリスト。"""
        out = []
        for k in range(1, len(items) + 1):
            s = self.slide(title, summary=summary if k == len(items) else None, plain=False)   # 途中の枚も本文のまま（帯が出たり消えたりしない）
            s.heading(heading)
            s.at(self.area["x"], s.cur_y)
            for j, it in enumerate(items[:k]):
                text = it if j == k - 1 else "{g:" + it + "}"
                s.p(text, size=size, gap=gap, name="漸進表示")
            if figure:
                s.image(figure, x=fig_x, y=1.9)
            out.append(s)
        return out

    HEADER_NAMES = ("見出し", "結論の一文", "結論の線", "章のナビ")

    def _distribute(self):
        """本文の枚ごとに、本文の塊（見出し・結論・ページ番号を除く図形）を、本文の上端から下端までの間で縦の中央に寄せる。
        空きが 0.5 in に満たない枚は動かさない。動かすのは 1 in まで（上に浮きすぎないように）。"""
        top, bottom = self.area["top"], self.area["bottom"]
        for s in self.slides:
            if not hasattr(s, "section"):
                continue
            body = [sh for sh in s.slide.shapes if not sh.is_placeholder and sh.name not in self.HEADER_NAMES
                    and sh.top is not None and sh.height is not None and sh.top / 914400 < bottom
                    and not (sh.name == "結論の囲み" and sh.top / 914400 >= BOX_TOP - 0.05)]   # 下の結論の囲みは動かさない
            if not body:
                continue
            y0 = min(sh.top for sh in body) / 914400
            y1 = max(sh.top + sh.height for sh in body) / 914400
            free = bottom - y1
            gap_top = max(0.0, y0 - top)
            dy = min(1.0, (free - gap_top) / 2)
            if free < 0.5 or dy < 0.15:
                continue
            for sh in body:
                sh.top = sh.top + Emu(int(dy * 914400))

    def save(self, path: str | Path, title: str | None = None, author: str | None = None):
        if self.valign == "center" and not getattr(self, "_distributed", False):
            self._distribute()
            self._distributed = True
        if self.style.get("nav") and not getattr(self, "_nav_drawn", False):
            self._draw_nav()
            self._nav_drawn = True
        if title:
            self.prs.core_properties.title = title
        if author:
            self.prs.core_properties.author = author
        self.prs.save(str(path))
        print(f"saved {path} ({len(self.prs.slides)} slides)")


def wrap_to(text: str, width: float, size: float) -> str:
    """幅 width (in) に入らない1行を、真ん中に近い「、」か助詞の後ろで2行に分ける（柱の中の結論など、幅の決まった所に）。"""
    if "\n" in text or text_width_pt(parse_markup(text), size) / 72.0 + 2 * INSET_X <= width:
        return text
    mid = len(text) / 2
    cands = [i + 1 for i, ch in enumerate(text[:-1]) if ch in "、，,・" or text[i:i + 1] in "でとがはをにの"]
    k = min(cands, key=lambda i: abs(i - mid)) if cands else int(mid)
    return text[:k] + "\n" + text[k:]


def title_right_edge(title: str, size: float = 44) -> float:
    """タイトル文字列の右端x（インチ）。図をタイトルの右に上詰めで置けるかの判断に使う。"""
    return 0.63 + INSET_X + text_width_pt(parse_markup(title), size) / 72.0
