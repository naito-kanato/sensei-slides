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
import unicodedata
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


# ---- 文字の大きさの計算 ---------------------------------------------------------------------------
# 描画の検査（render_check_py.py：PowerPoint の文字の範囲・行数に合わせた計算。ラン・書体・太字の広がり・kern・禁則・ぶら下げ・
# 余白・1行の高さ）と同じ関数で測る。部品が置く瞬間に、検査と同じ幅・行数で入るかを見られる（前は PIL で字の幅を足すだけの
# 見積もりで、検査の幅と食い違い、はみ出しが描いてから見つかっていた）。render_check_py が使えない（fontTools が無い）ときは、
# 前の見積もり（_pil_width）で測る。書体が無い環境の代わりの書体は、render_check_py も下の _FONT_FILES を使う。
try:
    import render_check_py as _RC
except Exception:   # noqa: BLE001
    _RC = None

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
                # 幅を測るだけなので、文字の配置は簡単な方式で（Linux の Pillow の raqm は文字によって raqm_layout() で止まる）
                _FONTS[kind] = ImageFont.truetype(str(path), 100, index=index, layout_engine=ImageFont.Layout.BASIC)
                break
            except OSError:
                continue
    return _FONTS[kind]


def _is_ea(ch: str) -> bool:
    o = ord(ch)
    return o >= 0x2E80 or 0x2190 <= o <= 0x2BFF or 0x0370 <= o <= 0x03FF or 0x2010 <= o <= 0x2027


def _pil_width(runs: list[Run], size: float, bold: bool = False) -> float:
    """前の見積もり（render_check_py が使えないときだけ）：字の送り幅を PIL で足す。"""
    w = 0.0
    for r in runs:
        scale = 0.7 if r.baseline else 1.0
        for ch in r.text:
            kind = "ea" if _is_ea(ch) else ("latin_i" if r.i else ("latin_b" if (r.b or bold) else "latin"))
            f = _font(kind)
            try:
                cw = f.getlength(ch) / 100.0 if f else (1.0 if kind == "ea" else 0.55)
            except (RuntimeError, OSError):     # 測れない文字は、全角 1・半角 0.55 の目安で
                cw = 1.0 if kind == "ea" else 0.55
            w += cw * size * scale
    return w


INSET_X, INSET_Y = ((_RC.DEFAULT_INS[0] / 914400, _RC.DEFAULT_INS[1] / 914400) if _RC else (0.1, 0.05))   # 文字の枠の余白（in）
LINE_FACTOR = _RC.LINE_FACTOR if _RC else 1.2   # 1行の高さ ＝ 字の大きさ × 1.2（行間 100%）


def line_height_in(size: float) -> float:
    return size * LINE_FACTOR / 72.0


def fill_runs(paragraph, runs: list[Run], size: float, color: str | None, bold: bool, lang: str, alt: str):
    """段落にランを入れる（スライドの文字の枠と、測るための枠が同じ書式になるように1か所で）。"""
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
        rPr.set("lang", lang)
        rPr.set("altLang", alt)
        if r.baseline:
            rPr.set("baseline", str(r.baseline))


class Meter:
    """文字を測る。render_check_py.layout_text（描画の検査と同じ計算）を、スライドに置かない文字の枠で呼ぶ。
    Deck ごとに1つ（そのテンプレートのテーマの書体・デッキの言語で測る）。"""

    def __init__(self, prs, lang: str = "ja-JP", alt: str = "en-US"):
        self.rd = _RC.Deck(prs)
        self.master = prs.slide_masters[0]
        self.lang, self.alt = lang, alt
        self._cache: dict = {}

    @staticmethod
    def _key(lines):
        return tuple(tuple((r.text, r.b, r.i, r.baseline) for r in l) for l in lines)

    def layout(self, lines: list, size: float, bold: bool = False, wrap_w: float | None = None):
        """lines（段落ごとのラン）を置いたときの配置（render_check_py.layout_text の戻り値）。wrap_w（in）を渡すと、その幅で折り返す。"""
        key = (self._key(lines), size, bool(bold), wrap_w)
        hit = self._cache.get(key)
        if hit is not None:
            return hit
        from pptx.oxml.shapes.autoshape import CT_Shape
        from pptx.shapes.autoshape import Shape
        w_emu = int((wrap_w + 2 * INSET_X if wrap_w else 40.0) * 914400)
        sh = Shape(CT_Shape.new_textbox_sp(1, "measure", 0, 0, w_emu, 914400), None)
        tf = sh.text_frame
        tf.word_wrap = bool(wrap_w)
        for j, line in enumerate(lines or [[]]):
            p = tf.paragraphs[0] if j == 0 else tf.add_paragraph()
            if line:
                fill_runs(p, line, size, None, bold, self.lang, self.alt)
            else:
                p.add_run().text = ""
        lay = _RC.layout_text(_RC.TextCtx(self.rd, sh, self.master), (0.0, 0.0, w_emu / 12700.0, 100000.0))
        if len(self._cache) > 20000:
            self._cache.clear()
        self._cache[key] = lay
        return lay

    def widths(self, lines, size, bold=False) -> list:
        """段落ごとの [(字の幅, 行末の分)]（pt。折り返さない）。字の幅は描画の検査の行の幅、行末の分は検査の範囲に入る段落記号の幅。"""
        lay = self.layout(lines, size, bold)
        out = [(0.0, 0.0)] * len(lines)
        for ln in lay["lines"]:
            if ln.para < len(out):
                out[ln.para] = (ln.width, ln.end_extra)
        return out

    def chars(self, line: list, size, bold=False) -> list:
        """1行の字ごとの (字, 幅 pt)。"""
        lay = self.layout([line], size, bold)
        return [(c.c, c.w) for ln in lay["lines"] for c in ln.chars if c.c != "\v"]

    def nlines(self, lines, size, bold=False, wrap_w: float | None = None) -> int:
        return self.layout(lines, size, bold, wrap_w)["nlines"] if lines else 0


_METER = None        # いま組んでいるデッキの Meter（Deck が作る。部品の外の text_width_pt・wrap_to も同じ計算で測る）
_METER_DEFAULT = []  # デッキを作る前に測るとき（scaffold.py の折り返し）の、既定のテンプレートの Meter


def _meter():
    if _RC is None:
        return None
    if _METER is not None:
        return _METER
    if not _METER_DEFAULT:
        try:
            _METER_DEFAULT.append(Meter(Presentation(str(TEMPLATE))))
        except Exception:   # noqa: BLE001
            _METER_DEFAULT.append(None)
    return _METER_DEFAULT[0]


def text_width_pt(runs: list[Run], size: float, bold: bool = False) -> float:
    """1行の字の幅（pt）。描画の検査（render_check_py）と同じ計算。"""
    m = _meter()
    if m is not None and runs:
        try:
            return m.widths([runs], size, bold)[0][0]
        except Exception:   # noqa: BLE001  測れない字の並び（壊れたフォントなど）は前の見積もりで
            pass
    return _pil_width(runs, size, bold)


def line_extent_pt(runs: list[Run], size: float, bold: bool = False) -> float:
    """1行の文字の範囲の幅（pt）：字の幅＋行末の段落記号の幅。描画の検査が本文の右端・図との間隔に使う幅。"""
    m = _meter()
    if m is not None and runs:
        try:
            w, extra = m.widths([runs], size, bold)[0]
            return w + extra
        except Exception:   # noqa: BLE001
            pass
    return _pil_width(runs, size, bold) + 0.27 * size


# ---- 折り返し（右の限りを超える行だけ。描画の検査と同じ字の幅で） -----------------------------------------------
_BREAK_AFTER = set("、。，,・）」』】：:；;!！?？")
_PARTICLES = ("では", "には", "とは", "から", "まで", "より", "ので", "のに", "が", "を", "に", "は", "で", "と", "も", "へ", "や")
_NO_START = set(_RC.NO_START) if _RC else set("、。，．,.・：；？！?!:;)）]］}｝」』】ー")
_NO_END = set(_RC.NO_END) if _RC else set("([｛〔〈《「『【（［{")
_MARKS = ("⇒", "→", "・", "□", "☐", "•")


def _split_runs(line: list, k: int):
    """ランの並びを、字の位置 k で2つに分ける。"""
    a, b, pos = [], [], 0
    for r in line:
        n = len(r.text)
        if pos + n <= k:
            a.append(r)
        elif pos >= k:
            b.append(r)
        else:
            cut = k - pos
            a.append(Run(r.text[:cut], r.color, r.u, r.b, r.i, r.baseline))
            b.append(Run(r.text[cut:], r.color, r.u, r.b, r.i, r.baseline))
        pos += n
    return a, b


def _strip_runs(line: list, left: bool = False, right: bool = False):
    out = [Run(r.text, r.color, r.u, r.b, r.i, r.baseline) for r in line]
    if left:
        while out and not out[0].text.lstrip(" "):
            out.pop(0)
        if out:
            out[0].text = out[0].text.lstrip(" ")
    if right:
        while out and not out[-1].text.rstrip(" "):
            out.pop()
        if out:
            out[-1].text = out[-1].text.rstrip(" ")
    return out


def _latin(ch: str) -> bool:
    return ch.isascii() and (ch.isalnum() or ch in ".,'%+-_/()^")


def wrap_runs(line: list, width_pt: float, size: float, bold: bool = False, indent: str = "") -> list:
    """1行（ラン）を幅 width_pt（字の幅＋行末の分）に入るように折る。折る所は「、」「。」・空白・助詞の後ろ（禁則と英単語の途中は避ける）。
    2行目からは indent を頭に付ける（字下げ・「⇒」「・」の後ろにそろえる）。入る行はそのまま [line]。"""
    m = _meter()
    out, cur = [], line
    for _ in range(8):
        text = "".join(r.text for r in cur)
        ext = line_extent_pt(cur, size, bold) if text else 0.0
        if not text or ext <= width_pt:
            break
        cw = []
        if m is not None:
            try:
                cw = m.chars(cur, size, bold)
            except Exception:   # noqa: BLE001
                cw = []
        if len(cw) != len(text):
            cw = [(c, text_width_pt([Run(c)], size, bold)) for c in text]
        extra = max(0.0, ext - sum(w for _, w in cw))
        acc, imax = 0.0, 0
        for i, (_, w) in enumerate(cw):
            if acc + w + extra > width_pt and i > 0:
                break
            acc += w
            imax = i + 1
        if imax >= len(text):
            break
        best, rank_best = None, -1
        for i in range(max(1, int(imax * 0.5)), imax + 1):
            prev, nxt = text[i - 1], text[i] if i < len(text) else ""
            if nxt in _NO_START or prev in _NO_END or (_latin(prev) and _latin(nxt)) or not text[i:].strip():
                continue
            if prev in _BREAK_AFTER or prev == " " or nxt == " ":
                rank = 3
            elif any(text[:i].endswith(p) for p in _PARTICLES):
                rank = 2
            else:
                rank = 1
            if rank >= rank_best:
                best, rank_best = i, rank
        if best is None:   # 折れる所が無い（長い英単語など）：入る所で切る
            best = max(1, imax)
        a, b = _split_runs(cur, best)
        out.append(_strip_runs(a, right=True))
        b = _strip_runs(b, left=True)
        cur = ([Run(indent)] if indent else []) + b
    out.append(cur)
    return out


def _cont_indent(text: str, sp: str) -> str:
    """折った2行目の頭に付ける字下げ：元の行の頭の空白、行が「⇒」「・」「1.」などで始まるなら、その後ろにそろえる分。"""
    lead = text[:len(text) - len(text.lstrip(" 　"))]
    rest = text[len(lead):]
    if rest.startswith(_MARKS) or re.match(r"^\d+[.．]\s", rest):
        return lead + sp
    return lead


BODY_PT = 22   # 本文の字の大きさ（2026-11-13 に 20 → 22。本文の目安を 80〜120字に狭めたのに合わせ、少し大きく）


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


_RULES: dict = {}


def _rule(name: str):
    """描画の検査（check_layout.py）の基準の値（下端の許し・図との間隔・箱の決まりなど）。二重に持たないように、検査のものを読む。"""
    if name not in _RULES:
        import check_layout
        _RULES[name] = getattr(check_layout, name)
    return _RULES[name]


# ---- スライド ------------------------------------------------------------------
class Slide:
    def __init__(self, deck: "Deck", slide):
        self.deck = deck
        self.slide = slide
        self.cur_x = deck.area["x"] if hasattr(deck, "area") else BODY_X
        self.cur_y = deck.area["top"] if hasattr(deck, "area") else 1.9
        self.boxes: list[tuple[str, Box]] = []
        self._texts: list[dict] = []   # 置いた文字の枠（折り返し直し・ずらしに使う）：{shape, box, lines, size, bold, color, align, name, fit}
        self._shape_box: dict = {}     # 図形の要素 → その Box（ずらすとき、記録の位置も合わせる）

    def _forms(self, items, what: str, steps: bool = False):
        """並べる項目の形がそろっているか（英語だけ。style-guide 7節）。組んだ pptx では折り返しと次の項目が区別できないので、ここで見る。"""
        if not isinstance(items, (list, tuple)):
            return
        import language
        bad = language.mixed_forms(items, self.deck.lang, steps)
        if bad:
            main, odd = bad
            n = self.deck.prs.slides.index(self.slide) + 1
            print(f"[WARN] {n}枚目の{what}：並べる項目の形がそろっていない（多いのは{main}）："
                  + " / ".join(f"「{t[:30]}」（{f}）" for f, t in odd[:3])
                  + f" → 全部を{main}にそろえる（名詞句・命令形・-ing・文を混ぜない。style-guide 7節）")

    # -- 低レベル: テキストボックス
    def _add_runs(self, paragraph, runs: list[Run], size: float, color: str | None, bold: bool):
        fill_runs(paragraph, runs, size, color, bold, self.deck.lang_code, self.deck.alt_code)

    # -- 置く瞬間に測る：本文の場所の右端・下端、図の左端（描画の検査と同じ値。check_layout から1か所で読む）
    FIT_NAMES = ("塊の見出し", "塊の本文", "帰結", "展開の左", "展開の右", "問い", "答え", "手順", "想定質問", "回答",
                 "漸進表示", "定義")   # 右の限りを超えたら折り返す本文の文字の枠（名前の無い本文 s.p も）

    def _no(self) -> int:
        return self.deck.prs.slides.index(self.slide) + 1

    def _reg(self, kind: str, box: Box, sh=None):
        self.boxes.append((kind, box))
        if sh is not None:
            self._shape_box[id(sh._element)] = (sh._element, box, kind)   # 要素も持つ（持たないと id が使い回される）

    def _right_limit(self, x: float, y0: float, y1: float) -> float:
        """x から始まる文の右の限り（in）：本文の場所の右（描画の検査の本文の場所の右と同じ。柱の中の文は柱の右）、
        右に図・表・箱が縦に重なって置いてあれば、その左端から図との間隔（0.4 in）を引いた所。"""
        a = self.deck.area
        lim = max(a["right"], SLIDE_W - _rule("PAGE_MARGIN") / 72.0) + _rule("RIGHT_TOL") / 72.0
        if "text_right" in a and x < a["text_right"]:
            lim = a["text_right"]
        for kind, b in self.boxes:
            if kind in ("image", "shape") and b.x - x >= 1.0 and b.y < y1 - 0.02 and y0 + 0.02 < b.bottom:
                lim = min(lim, b.x - _rule("FIG_GAP_MIN") / 72.0)
        return lim

    def _bottom_limit(self) -> float:
        """本文・図の下端の限り（in）：本文の場所の下端（deck.content_bottom）＋描画の検査の許し（EDGE_TOL）と、
        帯の上端（帯の無い枚はページ番号の上）から描画の誤差 2pt を引いた所の、上の方（描画の検査と同じ値）。"""
        if getattr(self, "_blim", None) is None:
            banded = (band_placeholder_idx(self.slide.slide_layout, self.deck.prs.slide_height) is not None
                      or any(sh.name == "青帯" for sh in self.slide.shapes))
            band = (_rule("BAND_TOP") if banded else _rule("NOBAND_BOTTOM")) - 2.0
            self._blim = min(self.deck.content_bottom + _rule("EDGE_TOL") / 72.0, band / 72.0) - 0.01   # 0.01 in は丸めの分（ちょうど限りで ERROR になった）
        return self._blim

    def _fits(self, name, size) -> bool:
        return hasattr(self, "section") and (name in self.FIT_NAMES or (name is None and size >= 17.5))

    def _wrap_to_limit(self, lines, x, y, size, bold, width=None):
        """右の限り（width を渡せばその幅）を超える行だけ折る。(新しい行, 折ったか)。"""
        out, changed = lines, False
        for _ in range(2):   # 折ると高さが増え、下にある図にかかることがあるので、もう1回見る
            h = len(out) * line_height_in(size) + 2 * INSET_Y
            lim_pt = (width * 72.0) if width is not None else (self._right_limit(x, y, y + h) - x - INSET_X) * 72.0
            if lim_pt < 6 * size:   # 6字も入らない所では折らない（細切れになる。右のはみ出しとして知らせる）
                break
            new = []
            for line in out:
                if line and line_extent_pt(line, size, bold) > lim_pt:
                    text = "".join(r.text for r in line)
                    new += wrap_runs(line, lim_pt, size, bold, _cont_indent(text, self.deck.sp))
                else:
                    new.append(line)
            if len(new) == len(out):
                break
            out, changed = new, True
        return out, changed

    def _fill_frame(self, tf, lines, size, color, bold, align):
        for j, line in enumerate(lines):
            p = tf.paragraphs[0] if j == 0 else tf.add_paragraph()
            p.alignment = {"l": PP_ALIGN.LEFT, "c": PP_ALIGN.CENTER, "r": PP_ALIGN.RIGHT}[align]
            if line:
                self._add_runs(p, line, size, color, bold)
            else:
                p.add_run().text = ""

    def _text_size(self, lines, size, bold):
        """文字の枠の幅・高さ（in）：一番長い行の字の幅＋余白、行数 × 1行の高さ＋余白（描画の検査と同じ計算）。"""
        m = self.deck.meter
        tw = None
        if m is not None:
            try:
                tw = max((w for w, _ in m.widths(lines, size, bold)), default=0) / 72.0
            except Exception:   # noqa: BLE001
                tw = None
        if tw is None:
            tw = max((_pil_width(l, size, bold) for l in lines), default=0) / 72.0
        return tw + 2 * INSET_X + 0.05, len(lines) * line_height_in(size) + 2 * INSET_Y

    def text(self, x: float, y: float, text: str, size: float = BODY_PT, color: str | None = None,
             align: str = "l", bold: bool = False, w: float | None = None, name: str | None = None,
             fit: bool | None = None, wrap_w: float | None = None) -> Box:
        """本文テキストを置く。改行は \\n で明示。本文の文字の枠（FIT_NAMES・名前の無い本文）は、行が右の限り（本文の場所の右・
        右にある図の左端から 0.4 in）を超えるときだけ、その幅で折る（fit=False で折らない。wrap_w（in）でその幅に）。戻り値は外枠。"""
        lines = split_lines(parse_markup(text))
        fit = self._fits(name, size) if fit is None else fit
        if (fit or wrap_w) and align == "l":
            before = lines
            lines, changed = self._wrap_to_limit(lines, x, y, size, bold, wrap_w)
            if changed:
                self._wrapped(before, lines, size, name)
        tw, bh = self._text_size(lines, size, bold)
        bw = tw if w is None else max(w, tw) if wrap_w is not None else w
        tb = self.slide.shapes.add_textbox(Inches(x), Inches(y), Inches(bw), Inches(bh))
        if name:
            tb.name = name
        tf = tb.text_frame
        tf.word_wrap = False
        tf.auto_size = MSO_AUTO_SIZE.SHAPE_TO_FIT_TEXT
        self._fill_frame(tf, lines, size, color, bold, align)
        box = Box(x, y, bw, bh)
        self._reg("text", box, tb)
        self._texts.append(dict(shape=tb, box=box, lines=lines, size=size, bold=bold, color=color, align=align,
                                name=name, fit=fit, w=w))
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
                    add = ("　／　" if self.deck.lang == "日本語" else "  /  ") + text
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
        self._reg("text", box, tb)
        return box

    # -- 数式
    def eq(self, latex: str, x: float, y: float, size: float = BODY_PT, color: str | None = None,
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
        self._reg("eq", box, pic)
        return box

    def row(self, x: float, y: float, parts: list, size: float = BODY_PT, gap: float = 0.07) -> Box:
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
                b = self.text(cx - INSET_X, cy - line_h / 2, part, size=size, fit=False)   # 数式と並ぶ1行は折らない
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
        self._reg("image", box, pic)
        self._fig_font(pic, path, w)
        return box

    def arrow(self, x: float, y: float, w: float = 0.6, h: float = 0.55, direction: str = "right") -> Box:
        """元デッキと同じ水色のブロック矢印（テーマ色 tx2 50%）。direction: right/down/left/up/both"""
        if w <= 0 or h <= 0:   # マイナスの大きさの図形があると、PowerPoint はファイルごと開けない
            raise ValueError(f"矢印の大きさが0以下（w={w:.2f}, h={h:.2f} in）。flow の gap は 0.35 in 以上にする")
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
        self._reg("arrow", box, sh)
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
        self._reg("shape", box, sh)
        return box

    def caption(self, box: Box, text: str, right: bool = True, size: float = 14) -> Box:
        """図のすぐ下に小さな灰色の注記（「（概略）」「温度は代表値」などの断り書き）。box は image() の戻り値。
        図より長い注記が図の左へ伸びて、そこに本文があるときは、図の左端から置く（左文右図で、右寄せの出典が左の本文にかぶっていた）。
        図の左端から右の余白までに入らなければ2行に折り、それでも入らなければ12ptにする。"""
        def width(t, sz):
            return max(text_width_pt(l, sz) for l in split_lines(parse_markup(t))) / 72.0 + 2 * INSET_X + 0.05
        y = box.bottom + 0.02
        w = width(text, size)
        x = box.right - w if right else box.x
        h = line_height_in(size) + 2 * INSET_Y
        if x < box.x - 0.01 and any(kind in ("text", "eq", "shape") and b.x < box.x and x < b.right and b.y < y + h and y < b.bottom
                                    for kind, b in self.boxes):
            area = getattr(self.deck, "area", None) or {}
            room = max(box.w, area.get("right", SLIDE_W - 0.5) - box.x)
            if w > room:
                text = wrap_to(text, room, size)
                if width(text, size) > room:
                    size = 12
            x = box.x
        return self.text(x, y, text, size=size, color=C.GRAY, fit=False)

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
        # 右の限りを越える幅なら、列の幅を同じ割合で縮める（手で決めた表の幅が右にはみ出す、が1回目の ERROR にあった）
        room = self._right_limit(x, y, y + 1) - x - label_w - 0.08 * (ncols - 1)
        if sum(ws) > room + 0.01 and room > 0.5 * sum(ws):
            ws = [w_ * room / sum(ws) for w_ in ws]
        lim = self._bottom_limit()
        gap = 0.08
        for sz, gp in ((size, 0.08), (size, 0.04), (min(size, 15), 0.04), (min(size, _rule("TABLE_FONT_MIN")), 0.04)):
            # 行の高さは、その行のいちばん行の多いセルに合わせる（折り返した行も数える。足りないとセルの文字が下の行に重なった）
            hs = [max([row_h] + [self._box_text_h(c, w_, sz) for c, w_ in zip(cells, ws)]
                      + ([self._box_text_h(lab, label_w - 0.08, sz, bold=True)] if label_w else [])) for lab, cells in rows]
            size, gap = sz, gp
            if y + 0.5 + gp + sum(hs) + gp * (len(hs) - 1) <= lim:
                break
        xs = [x + label_w + sum(ws[:j]) + 0.08 * j for j in range(len(ws))]
        if corner is not None:
            self.rect(x, y, label_w - 0.08, 0.5, fill=C.PALE, text=corner, size=17, color=C.BAND, bold=True, name=TABLE_NAMES[0])
        for j, h in enumerate(header):
            self.rect(xs[j], y, ws[j], 0.5, fill=C.PALE, text=h, size=17, color=C.BAND, bold=True, name=TABLE_NAMES[0])
        yy = y + 0.5 + gap
        for (lab, cells), rh in zip(rows, hs):
            if label_w:
                self.rect(x, yy, label_w - 0.08, rh, fill=C.PALE, text=lab, size=size, color=C.BAND, bold=True, name=TABLE_NAMES[1])
            for j, cell in enumerate(cells):
                self.rect(xs[j], yy, ws[j], rh, fill=C.LIGHT, text=cell, size=size, align="l", name=TABLE_NAMES[2])
            yy += rh + gap
        return yy

    def _box_text_h(self, text: str, w: float, size: float, bold: bool = False) -> float:
        """箱（rect。左右の余白 0.12 in・上下 0.05 in・角丸）の中の文字の高さ（in）：箱の幅で折り返した行数 × 1行の高さ＋余白。"""
        lines = split_lines(parse_markup(text or ""))
        m = self.deck.meter
        inner = max(0.3, w - 0.24 - 0.05)
        try:
            n = m.nlines(lines, size, bold, inner) if m is not None else len(lines)
        except Exception:   # noqa: BLE001
            n = len(lines)
        return n * line_height_in(size) + 0.1 + 0.06

    def flow(self, items: list, x: float, y: float, w: float, h: float = 0.9, gap: float = 0.75,
             direction: str = "down", size: float = 18, arrow_labels: list | None = None,
             last_fill: str | None = None) -> Box:
        """箱と水色のブロック矢印でつないだ流れ図（PowerPointの図形なので後で編集できる）。
        items = ["資料を読む\\n（PDF・講義メモ）", "構成案", "スライド"]。
        direction="down" は縦に、"right" は横に並べる。arrow_labels で矢印の横に注記（例 ["較正", None]）。
        最後の箱だけ薄灰（結果・行き先）、ほかは薄青。"""
        n = len(items)
        lim_b, lim_r = self._bottom_limit(), self._right_limit(x, y, y + h)
        need = lambda w_: max(self._box_text_h(tx, w_, size) for tx in items)   # noqa: E731  箱の文字が入る高さ
        if direction == "right" and x + n * w + (n - 1) * gap > lim_r + 0.01:   # 右に入らなければ、間 → 箱の幅の順に詰める
            gap = max(0.35, min(gap, (lim_r - x - n * w) / max(1, n - 1)))
            w = min(w, (lim_r - x - (n - 1) * gap) / n)
        h = max(h, need(w))   # 箱の文字が箱より高ければ、箱を高く（文字が箱の外に出ていた）
        if direction == "down" and y + n * h + (n - 1) * gap > lim_b:   # 下に入らなければ、間 → 箱の高さの順に詰める
            gap = max(0.35, min(gap, (lim_b - y - n * h) / max(1, n - 1)))
            h = max(need(w), min(h, (lim_b - y - (n - 1) * gap) / n))
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
        self._reg("line", Box(min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1)), ln)
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
        self._reg("ring", box, sh)
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

    def defs(self, x: float, y: float, items: list, size: float = 18, sep: str | None = None) -> Box:
        """数式の右に変数の定義を縦に並べる（過去の輪読のデッキの「γ：表面張力」「ρ：液体の密度」）。
        items = [("γ", "表面張力"), ("ρ", "液体の密度")]。記号は自動でイタリック（{i:}）、全角「：」で区切る。
        記号に上下付きを含めてよい（("m_{4}", "^{4}Heの質量")）。元デッキは20pt。18pt は「定義の補足」として許される下限。
        置き方: e = s.peq(...) のあと s.defs(e.right + 0.4, e.y, [...]) のように数式の右・同じ高さに。"""
        sep = sep if sep is not None else "：" if self.deck.lang == "日本語" else ": "   # 日本語でないデッキは半角の「: 」
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

    RECAP_KINDS = ("問い→答え", "前と後", "筋", "次の一歩", "選び方")

    def recap(self, opening: str | None = None, answer: str = "", points=(), kind: str = "問い→答え", pairs=None,
              steps=None, actions=None, labels=None, size: float = 22, big: float = 26, panel: bool = False) -> Box:
        """まとめの枚（役割「まとめ」）。kind で5つの形（references/story.md 3節。話の型から既定が決まる）：
          問い→答え：左「最初の問い」（灰の箱）→ 右「答え」（薄い主色の箱）、下に持ち帰ること（余白をあけて、白い地の文字）
          前と後　　：pairs=[(聞く前の見方, 今わかったこと), …]（2〜3組）。左の列は灰、右の列は薄い主色の地1つずつ。行は白い線で区切る
          筋　　　　：steps=[状況, しかし, だから, 答え]（3〜4個）を1段ずつ小さな箱（灰、答えだけ薄い主色）にして細い矢印でつなぐ。答えは赤の太字。
                    panel=True で流れ全体を1つの地にまとめる。下に持ち帰ること
          次の一歩　：上に答え（薄い主色の箱）、下に actions=[明日からやること, …]（余白をあけて文字、□の印）
          選び方　　：pairs=[(こんなとき, 選ぶもの), …]（2〜3組）。前と後と同じ並べ方
        決まり：箱（地）は1枚に2つまで。同じ段の中は作りをそろえる（左右とも箱か、全部文字）。箱の外の文字は、箱の中の文字と左端・高さをそろえる。
        どの形も、新しい事実は入れない（前の枚の言い直しだけ）。要の語は {r:…} で赤に。1行は日本語12〜14字・英語25字ほどまでに \n を入れる。"""
        if kind not in self.RECAP_KINDS:
            raise ValueError(f"まとめの形は {'・'.join(self.RECAP_KINDS)} から（今は {kind}）")
        ja = self.deck.lang == "日本語"
        a = self.deck.area
        x0, x1 = self.deck.wide
        W = x1 - x0
        y = max(self.cur_y, a["top"])
        lh = line_height_in
        n0 = len(self.slide.shapes)
        PAD = 0.12          # 箱の中の文字の余白（rect の margin）。箱の外の文字も、これに合わせて置く
        DX = PAD - INSET_X  # 文字の箱（text）の余白との差

        def nlines(t):
            return len(split_lines(parse_markup(t)))

        def label(x, yy, t, sz=size):
            return self.text(x + DX, yy, "{b:" + t + "}", size=sz, color=C.BAND, name="まとめの見出し")

        def words(x, yy, t, sz, name):
            return self.text(x + DX, yy, t, size=sz, name=name)

        def take_home(yy, items, head=None, mark="・"):
            items = [p for p in list(items)[:3] if p]
            if not items:
                return yy
            head = head or ("持ち帰ること" if ja else "Take home")   # 線も箱も無い、白い地の文字の塊（区切りは余白）
            hb = label(x0, yy + 0.15, head)
            b = words(x0, hb.bottom + 0.02, "\n".join(mark + wrap_to(p, W - 1.0, size) for p in items), size, "まとめの要点")
            return b.bottom

        def two_boxes(lt, rt, sz, names):
            gap = 0.9
            bw = (W - gap) / 2
            bh = max(1.8, max(nlines(lt), nlines(rt)) * lh(sz) + 0.55)
            for k, (t, fill) in enumerate(((lt, C.LIGHT), (rt, C.PALE))):
                self.rect(x0 + k * (bw + gap), y, bw, bh, fill=fill, text=t, size=sz, color=C.TEXT, align="l", anchor="t", name=names[k])
            self.thin_arrow(x0 + bw + 0.12, y + bh / 2, x0 + bw + gap - 0.12, y + bh / 2)
            return y + bh

        def paired(rows, la, lb):
            gap = 0.9
            bw = (W - gap) / 2
            rx = x0 + bw + gap
            label(x0, y, la)
            label(rx, y, lb)
            top = y + lh(size) + 0.35   # 見出しと地の間（0.25 だと描画の検査の「縦の間隔が狭い」0.30 in を割った）
            cells, yy = [], top
            for left, right in list(rows)[:3]:
                lt, rt = wrap_to(left, bw - 0.4, size), wrap_to(right, bw - 0.4, size)
                h = max(1.0, max(nlines(lt), nlines(rt)) * lh(size) + 0.45)
                cells.append((yy, h, lt, rt))
                yy += h
            self.rect(x0, top, bw, yy - top, fill=C.LIGHT, name="まとめの地")   # 左右とも1つの地（作りをそろえる。箱は2つ）
            self.rect(rx, top, bw, yy - top, fill=C.PALE, name="まとめの地")
            for k, (cy, h, lt, rt) in enumerate(cells):
                if k:
                    for xx in (x0, rx):
                        self.line(xx + 0.15, cy, xx + bw - 0.15, cy, color="FFFFFF", width=1.5)
                mid = cy + h / 2
                words(x0 + 0.13, mid - nlines(lt) * lh(size) / 2 - INSET_Y, lt, size, "まとめの前")
                words(rx + 0.13, mid - nlines(rt) * lh(size) / 2 - INSET_Y, rt, size, "まとめの後")
                self.thin_arrow(x0 + bw + 0.12, mid, rx - 0.12, mid)
            return yy

        if kind == "問い→答え":
            la, lb = labels or (("最初の問い", "答え") if ja else ("We asked", "Answer"))
            bw = (W - 0.9) / 2
            bottom = two_boxes("{ab:" + la + "}\n" + wrap_to(opening or "", bw - 0.4, big),
                               "{ab:" + lb + "}\n" + wrap_to(answer, bw - 0.4, big), big, ("まとめの問い", "まとめの答え"))
            if points:
                bottom = take_home(bottom + 0.55, points)
        elif kind in ("前と後", "選び方"):
            if not pairs:
                raise ValueError(f"まとめ（{kind}）は pairs=[(左, 右), …] を2〜3組")
            la, lb = labels or ({"前と後": ("聞く前", "今わかったこと"), "選び方": ("こんなとき", "選ぶもの")}[kind] if ja else
                                {"前と後": ("Before", "Now we know"), "選び方": ("When", "Choose")}[kind])
            bottom = paired(pairs, la, lb)
            if points:
                bottom = take_home(bottom + 0.55, points)
        elif kind == "筋":
            st = list(steps or [])[:4]
            if len(st) < 3:
                raise ValueError("まとめ（筋）は steps に3〜4個（状況・しかし・だから・答え）")
            heads = labels or ((("状況", "しかし", "答え") if ja else ("Setting", "But", "Answer")) if len(st) == 3
                               else (("状況", "しかし", "だから", "答え") if ja else ("Setting", "But", "So", "Answer")))
            fs = size
            pad = 0.35                       # 流れ全体を1つの地にまとめる（1つの流れとして見える。箱は1つだけ）
            gap = 0.6 if panel else 0.85   # 箱を分けるときは、箱と箱の間に矢印が入る幅を
            px = pad if panel else 0.15    # 文字の左右の余白（地の内側。箱を分けるときは箱の内側）
            bw = (W - 2 * px - gap * (len(st) - 1)) / len(st)
            texts = ["\n".join(wrap_to(ln, bw + 0.15, fs) for ln in t.split("\n")) for t in st]   # 行ごとに箱の幅で折る（英語は1行が長く、矢印にかかった）
            last = texts[-1]
            texts[-1] = "{b:" + last + "}" if "{r:" in last else "{r:{b:" + last + "}}"   # 答えは赤の太字
            hh = lh(fs)
            th = max(nlines(t) for t in texts) * lh(fs)
            ph = hh + 0.05 + th + pad + pad * 1.4   # 下の余白を少し広めに（文字の下が詰まって見えた）
            if panel:   # 流れ全体を1つの地に
                self.rect(x0, y, W, ph, fill=C.PALE, name="まとめの地")
            ty = y + pad
            for k, (h, t) in enumerate(zip(heads, texts)):
                xx = x0 + px + k * (bw + gap)
                if not panel:   # 1段ずつ小さな箱（答えだけ薄い主色）。矢印でつながった小さな段は5個まで
                    self.rect(xx - px, y, bw + 2 * px, ph, fill=C.PALE if k == len(texts) - 1 else C.LIGHT, name="まとめの地")
                label(xx, ty, h, fs)
                words(xx, ty + hh + 0.05, t, fs, "まとめの答え" if k == len(texts) - 1 else "まとめの筋")
                if k < len(texts) - 1:
                    ax0 = xx + bw + (px if not panel else -0.1)
                    ax1 = xx + bw + gap - (px if not panel else 0.15)
                    self.thin_arrow(ax0 + 0.05, ty + hh + 0.05 + th / 2, ax1 - 0.05, ty + hh + 0.05 + th / 2)
            bottom = y + ph
            if points:
                bottom = take_home(bottom + 0.55, points)
        else:   # 次の一歩
            t = wrap_to(answer, W - 0.8, big)
            bh = max(1.4, nlines(t) * lh(big) + 0.55)
            self.rect(x0, y, W, bh, fill=C.PALE, text=t, size=big, color=C.TEXT, align="l", anchor="m", name="まとめの答え")
            bottom = take_home(y + bh + 0.55, actions or points, head=(labels[0] if labels else ("明日からやること" if ja else "Next steps")),
                               mark="□ " if ja else "☐ ")
        # まとめの塊を、本文の場所の上下の真ん中へ（上寄せの構造で、下が大きく空いた）
        dy = (self.deck.content_bottom - bottom - (y - a["top"])) / 2
        if dy > 0.15:
            for sh in list(self.slide.shapes)[n0:]:
                sh.top = sh.top + Emu(int(dy * 914400))
            y, bottom = y + dy, bottom + dy
        self.cur_x, self.cur_y = x0, bottom + 0.35
        return Box(x0, y, W, bottom - y)

    def figure_main(self, path, caption: str | None = None, w: float | None = None, gap: float = 0.5,
                    name: str = "左の図") -> Box:
        """図が主役の型：左に図を大きく、右の細い列（幅 4 in 前後）に補足の文。図そのものを読ませたい枚に
        （結果のグラフ・装置の写真・構造の図）。呼んだあと、s.block・s.lead・s.ask などは右の列に置かれる。
        右の列は1行が短い（20pt で全角13字・英語で28字前後）。補足は図の説明として2〜3塊・6〜8行（日本語で60〜100字、英語で35〜50語）：
        何の図か（軸・何と何）、どこを見るか、そこから言えること（赤字1か所）。短すぎると図の読み方が伝わらない。言うことの残りは原稿へ。
        w を省けば、図の描いた幅（8 in まで）。右の列が 4.2 in より狭くなるなら縮める。
        柱のある構造（本文が左の柱）では、図を右の白い所いっぱいに置き、文は柱のまま。"""
        with Image.open(path) as im:
            pw, ph_ = im.size
            dpi = (im.info.get("dpi") or (0, 0))[0]
        a = self.deck.area
        top = a["top"]
        if "text_right" in a:                       # 柱のある構造：図は右の白い所に、文は柱に
            fx = a["fig_x"]
            fw = a["right"] - fx
        else:
            fx = a["x"]
            fw = w or (pw / dpi if dpi and dpi >= 100 else 7.6)
            fw = min(fw, 8.0, a["right"] - fx - gap - 4.2)
        room = self.deck.content_bottom - top - (0.4 if caption else 0)
        fh = fw * ph_ / pw
        if fh > room:                                # 縦に入らなければ高さに合わせる
            fw, fh = room * pw / ph_, room
        b = self.image(path, fx, top, w=fw, h=fh, name=name)
        if caption:
            self.caption(b, caption, right=False)
        if "text_right" not in a:
            self.cur_x, self.cur_y = b.right + gap, top
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
        fy = a["top"] if y is None else y
        fh = w * ph_ / pw

        def place_x():
            texts = [b for kind, b in self.boxes if kind in ("text", "eq", "shape", "arrow") and b.y > a["top"] - 0.3]
            tr = max((b.right for b in texts), default=a.get("fig_x", right - w) - gap)
            x = min(tr + max(gap, (right - w - tr) / 2), right - w)
            return max(x, a["fig_x"]) if "text_right" in a else x
        x = place_x()
        # 図の左に入らない文（右端＋図との間隔 0.4 in が図の左端を越える行）は、図の左端までの幅で折り直す
        # （1行が長くて図に重なる・図との間隔が狭い、が1回目の ERROR の2割近くあった）
        if self._reflow_left_of(x, fy, fy + fh):
            x = place_x()
        b = self.image(path, x, fy, name=name)
        if caption:
            self.caption(b, caption)
        return b

    def _reflow_left_of(self, fx: float, y0: float, y1: float) -> bool:
        """図の左端 fx の左にあり、縦に重なる本文の文字の枠のうち、図との間隔（0.4 in）に入らない行を折り直す。折ったら True。"""
        lim = fx - _rule("FIG_GAP_MIN") / 72.0 - 0.01   # 描画の検査は 0.40 in ちょうどでも小数の切り捨てで ERROR にするので、少し内側に
        done = False
        for t in list(self._texts):
            b = t["box"]
            if not t["fit"] or t["align"] != "l" or fx - b.x < 1.0 or not (b.y < y1 and y0 < b.bottom):
                continue
            width = (lim - b.x - INSET_X) * 72.0
            if width < 6 * t["size"]:   # 6字も入らない所は折らない（細切れになる。図を小さく描き直すほうがよい。組む時点に知らせる）
                continue
            new = []
            for line in t["lines"]:
                if line and line_extent_pt(line, t["size"], t["bold"]) > width:
                    new += wrap_runs(line, width, t["size"], t["bold"], _cont_indent("".join(r.text for r in line), self.deck.sp))
                else:
                    new.append(line)
            if len(new) != len(t["lines"]):
                self._wrapped(t["lines"], new, t["size"], "図の横の文")
                self._retext(t, new)
                done = True
        return done

    def _wrapped(self, before, after, size, name):
        """折り返した行の記録（設計メモの確認 check_memo.py の見積もりが、列に入らない要点として出す）：(枚, 元の行, 1行の字数, 部品)。"""
        n = self._no()
        cpl = max((len("".join(r.text for r in l).strip()) for l in after), default=0)
        for l in before:
            tx = "".join(r.text for r in l).strip()
            if tx and not any("".join(r.text for r in a).strip() == tx for a in after):
                self.deck._wraps.append((n, tx, cpl, name or "本文"))

    def _retext(self, t: dict, lines):
        """置いた文字の枠の行を入れ替え、大きさを合わせる。高くなった分、その下に後から置いた図形を下へずらす（重ならない分だけ）。"""
        sh, b = t["shape"], t["box"]
        old_bottom = b.bottom
        tf = sh.text_frame
        tf.clear()
        self._fill_frame(tf, lines, t["size"], t["color"], t["bold"], t["align"])
        tw, th = self._text_size(lines, t["size"], t["bold"])
        b.w = tw if t["w"] is None else max(t["w"], tw)
        b.h = th
        sh.width, sh.height = Inches(b.w), Inches(b.h)
        t["lines"] = lines
        self._push_below(sh, old_bottom, b.bottom)

    def _push_below(self, sh, old_bottom: float, new_bottom: float):
        """sh より後に置いた、old_bottom より下の図形を、new_bottom に重ならない分だけ下へ。カーソルも。"""
        els = list(self.slide.shapes._spTree.iterchildren())
        k = els.index(sh._element)
        sb = self._shape_box
        after = [e for e in els[k + 1:] if id(e) in sb and sb[id(e)][1].y >= old_bottom - 0.02]
        if not after:
            return
        skip = {id(sh._element)} | {id(x) for x in after}
        others = [bx for key, (_, bx, _k) in sb.items() if key not in skip and bx.y < old_bottom and bx.y > self.deck.area["top"] - 0.3]
        floor = max([old_bottom] + [bx.bottom for bx in others if bx.bottom > old_bottom - 0.02])
        dy = new_bottom - floor
        if dy <= 0.005:
            return
        for e in after:
            bx = sb[id(e)][1]
            bx.y += dy
            e_sh = next(s for s in self.slide.shapes if s._element is e)
            e_sh.top = Inches(bx.y)
        if self.cur_y >= old_bottom - 0.02:
            self.cur_y += dy

    def _body_above(self, x0: float, x1: float) -> float:
        """先に置いた、x0〜x1 に横に重なる本文の図形の下端の一番下（無ければ 0）。上の見出しの領域の図形は数えない。"""
        top = self.deck.area["top"] - 0.3
        return max([0.0] + [b.bottom for kind, b in self.boxes if kind in ("text", "eq", "shape", "arrow", "image")
                            and b.y > top and b.x < x1 and x0 < b.right])

    def compare(self, left: tuple, right: tuple, y: float | None = None, size: float = BODY_PT, gap: float = 0.6) -> list:
        """2つを並べて比べる型（手法の比較・前と後・長所と短所）。left/right = ("小見出し", ["要点", ...])。
        左右同じ幅で、上に小見出しの帯、間に縦の区切り線。戻り値は左右の下端。置いたあと、カーソルを下端（の大きい方）の下へ進める
        （続けて s.block・s.p を置ける）。y を省くと、上に置いた塊の下（無ければ本文の上端）。渡した y が上の塊に重なるなら、塊の下へずらす。
        要点は列の幅で折り返す。"""
        wx0, wx1 = self.deck.wide
        col_w = (wx1 - wx0 - gap) / 2
        top0 = self.deck.area["top"] + 0.1
        above = self._body_above(wx0, wx1)   # 先に置いた本文の図形の下端（横に重なるもの）
        if y is None:
            y = max(top0, above + 0.3) if above else top0
        elif above > y - 0.05:   # 先に置いた塊に重なる（手で決めた y が上の文と重なる、が1回目の ERROR に多かった）
            y = above + 0.3
        # 下に入りきらないときは、行の間を詰め、それでも入らなければ字を 18pt まで小さく
        # （ベンチプレス講座の試しで、塊2つ＋3行ずつの比較がページ番号にかかり、制作の担当の直しが上限を越えた）。
        # 行は減らさない（各列の行を削ると、描画の検査の「箱が小さい（比較の列が短い）」になる）
        inner = col_w - 0.3 - 2 * INSET_X
        lim = self._bottom_limit()
        lh = line_height_in

        def nl(tx, sz):
            return len(self._wrap_to_limit(split_lines(parse_markup(tx)), 0, 0, sz, False, inner)[0])

        def low(sz, sp, to):
            return y + to + max(sum(nl(tx, sz) * lh(sz) + 2 * INSET_Y for tx in its) + sp * max(0, len(its) - 1)
                                for its in (left[1], right[1])) - INSET_Y
        top_off, step = 0.8, 0.2
        for sz, sp, to in ((size, 0.2, 0.8), (size, 0.08, 0.7), (min(size, 20), 0.08, 0.7), (min(size, 18), 0.06, 0.68)):
            size, step, top_off = sz, sp, to
            if low(sz, sp, to) <= lim:
                break
        bottoms, lows = [], []
        for k, (head, items) in enumerate((left, right)):
            x = wx0 + k * (col_w + gap)
            self.rect(x, y, col_w, 0.55, fill=C.PALE, text=head, size=20, color=C.BAND, bold=True)
            yy, b = y + top_off, None
            for it in items:
                # 列の幅いっぱいの枠に（列が1つの箱に見える。渡す前の検査は、箱の大きさを各列の行数で見る）
                b = self.text(x + 0.15, yy, it, size=size, w=col_w - 0.3, wrap_w=inner,
                              name="比較の" + ("左" if k == 0 else "右"))
                yy = b.bottom + step
            bottoms.append(yy)
            lows.append(b.bottom if b else y + 0.55)
        self.line(wx0 + col_w + gap / 2, y, wx0 + col_w + gap / 2, max(lows) - INSET_Y, color=C.GRAY, width=1.0)
        self.cur_y = max(lows) + 0.35
        return bottoms

    def key_message(self, big: str, sub: str | None = None, size: float = 54, y: float = 2.5, short: str | None = None) -> Box:
        """大きな数字・結論を1つだけ見せる型（一番伝えたい値・結論）。中央に大きく、下に短い説明。1回のデッキで1〜2枚まで。
        short：big（「60〜90%程度以上」のような範囲・限定つき）が横の場所に入らないときに大きく出す、数字＋単位だけの形（「60〜90%」）。
        そのときは big の全体を説明の頭に回す（限定を落とさない）。"""
        if short and short != big:
            wide = self.deck.wide[1] - self.deck.wide[0] - 0.2
            if max(text_width_pt(l, size, bold=True) for l in split_lines(parse_markup(big))) / 72.0 + 2 * INSET_X + 0.1 > wide:
                sub = f"{big}：{sub}" if sub else big
                big = short
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
              size: float = BODY_PT, indent: float = 0.35, gap: float = 0.35, name: str | None = None) -> Box:
        """ラベル＋説明の塊：小見出し（下線）の下に、説明を字下げして1〜3行。then で最後に「⇒ 赤字の帰結」。
        head=None なら字下げせずに説明だけ（= s.lead）。"""
        x, y = self._xy(x, y)
        self._forms(lines, "塊" + (f"「{head}」" if head else ""))
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
            size: float = BODY_PT, indent: float = 0.35, gap: float = 0.35) -> Box:
        """問い → 答え：「〜ではないのか？」（ラベルと同じ太字）の下に「⇒ 確かめた結果」。別の説明を1つずつ確かめる検証の筋に。"""
        x, y = self._xy(x, y)
        q = self.text(x, y, self._label(question), size=size, name="問い")
        a = self.text(x + indent, q.bottom + 0.05, "⇒ " + re.sub(r"^\s*[⇒→]+\s*", "", answer), size=size, name="答え")   # 書き手が ⇒ を付けても二重にしない
        self.cur_x, self.cur_y = x, a.bottom + gap
        return Box(x, y, max(q.right, a.right) - x, a.bottom - y)

    def qa_pairs(self, pairs, x: float | None = None, y: float | None = None, size: float = BODY_PT,
                 indent: float = 0.35, gap: float = 0.7) -> Box:
        """想定質問の枚：1枚に質問と回答を2組。pairs = [(番号, 質問, 回答), …]（2組まで。改行は文字列の中の \\n）。
        質問は太字のラベル（「Q1　…」）、回答はその下に字下げして「⇒ …」。2組の間は gap（in）あけて細い線を引く（帯なしの枚は、全体を上下の中ほどに寄せる）。
        答えが前の枚の図につながる組は、4つ目に図を添える：(番号, 質問, 回答, (図のパス, 注記))。図は話す所だけを切り出したもの
        （pdf_pages.py crop・PIL の crop。描き足さない）。質問と回答は左の列に、図はその組の高さから右に置き、注記の頭に番号が付く
        （「Q1: Slide 9, Fig. 1 …」。どの質問の図か・何枚目の図かが分かる）。図の無い組は文字だけ。
        戻るとよい枚はスライドに書かず、原稿に書く（図を添えた組は、注記に枚の番号を書く）。"""
        x, y = self._xy(x, y)
        pairs = list(pairs)[:2]
        sep = "：" if self.deck.lang == "日本語" else ": "
        top, bottom, rows = y, y, []
        for j, pr in enumerate(pairs):
            k, q, a = pr[:3]
            yy = top if j == 0 else bottom + gap
            qb = self.text(x, yy, self._label(f"{k}{self.deck.sp}{q}"), size=size, name="想定質問")
            head, *rest = a.split("\n")
            head = re.sub(r"^\s*[⇒→]+\s*", "", head)
            ab = self.text(x + indent, qb.bottom + 0.05, "⇒ " + head + "".join("\n" + self.deck.sp + " " + t for t in rest),
                           size=size, name="回答")   # 2行目からは矢印の後ろにそろえる
            rows.append((k, yy, max(qb.right, ab.right), pr[3] if len(pr) > 3 else None))
            bottom = ab.bottom
        figs = [r for r in rows if r[3]]
        a_ = self.deck.area
        fx = max(r[2] for r in rows) + 0.5 if figs else None   # 図の左端：一番長い文の右から 0.5 in（本文との間隔 0.4 in 以上）
        line_r = (fx - 0.3) if figs else SLIDE_W - x
        if len(rows) > 1:
            self.line(x, rows[1][1] - gap / 2, line_r, rows[1][1] - gap / 2, color="BFBFBF", width=0.75)
        low = 0.0   # 前の図の下端（2つの組の両方に図があれば、2つ目は1つ目の下から）
        for k, yy, _, fig in figs:
            path, cap = fig if isinstance(fig, tuple) else (fig, None)
            fw = a_["right"] - fx
            with Image.open(path) as im:
                ratio = im.height / im.width
            fy = max(yy + 0.05, low + 0.2)
            room = self.deck.content_bottom - fy - (0.4 if cap else 0)
            if fw * ratio > room:            # 縦に入らなければ高さに合わせる（文字が小さくなるので WARN が出る）
                fw = room / ratio
            b = self.image(path, fx, fy, w=fw, name="想定質問の図")
            c = self.caption(b, f"{k}{sep}{cap}" if cap else k)
            low = max(low, c.bottom)
        self.cur_x, self.cur_y = x, bottom + 0.35
        return Box(x, top, SLIDE_W - 2 * x, max(bottom, low) - top)

    def develop(self, left, right, x: float | None = None, y: float | None = None, size: float = BODY_PT,
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
                  w: float | None = None, size: float = BODY_PT, gap: float = 0.2) -> Box:
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
              size: float = BODY_PT, boxed: bool = True) -> Box:
        """条件の場合分け：items = [("T > T_λ", "純粋液体の ^{4}He と同様"), ...]。条件は太字、説明は字下げ。
        boxed=True で全体を薄い灰の囲みに（灰色の角丸箱。過去の輪読のデッキの形）。"""
        x, y = self._xy(x, y)
        self._forms([c for c, _ in items], "場合分けの条件")
        rows = []
        for k, (cond, desc) in enumerate(items):
            if k:
                rows.append("")
            rows.append("{b:" + cond + "}")
            rows += [self.deck.sp + l for l in self._lines(desc).split("\n")]
        text = "\n".join(rows)
        w = w or (self._text_w(text, size) + 0.4)
        h = len(rows) * line_height_in(size) + 0.35
        if boxed:
            b = self.rect(x, y, w, h, fill=C.LIGHT, text=text, size=size, color=C.TEXT, align="l", anchor="t", name="場合分け")
        else:
            b = self.text(x, y, text, size=size, name="場合分け")
        self.cur_x, self.cur_y = x, b.bottom + 0.35
        return b

    def numbered(self, items: list, x: float | None = None, y: float | None = None, size: float = BODY_PT,
                 gap: float = 0.35) -> Box:
        """番号の手順：1. 2. 3.（項目の2行目は字下げ）。解析・試料作成・測定の手順に。"""
        x, y = self._xy(x, y)
        self._forms(items, "手順", steps=True)
        rows = []
        for k, it in enumerate(items, 1):
            first, *rest = self._lines(it).split("\n")
            rows.append(f"{k}. {first}")
            rows += [self.deck.sp + " " + r for r in rest]
        b = self.text(x, y, "\n".join(rows), size=size, name="手順")
        self.cur_x, self.cur_y = x, b.bottom + gap
        return b

    # -- 図解の型（references/structures.md）。カードは薄い灰の塗りだけ（線なし）、見出しは主色の太字
    VALUE_SIZE = 28   # カードの値（3つ目）の文字の大きさ

    def _card_h(self, items, size, pad=0.45, cw=None):
        """カードの中身（見出し1行＋説明の行数、値があればその1行）の一番多いものに合わせた高さ。
        cw（カードの幅）を渡すと、カードの幅で折り返した行も数える（描画の検査と同じ計算）。"""
        def nl(it):
            if cw is not None:
                return round((self._box_text_h(self._card_text(it), cw, size) - 0.16) / line_height_in(size))
            return 1 + (len(self._lines(it[1]).split("\n")) if isinstance(it, tuple) and len(it) > 1 and it[1] else 0)
        n = max(nl(it) for it in items)
        val = any(isinstance(it, tuple) and len(it) > 2 and it[2] for it in items)
        return n * line_height_in(size) + pad + (line_height_in(self.VALUE_SIZE) + 0.1 if val else 0)

    def _card_text(self, item) -> str:
        item = item if isinstance(item, tuple) else (item,)
        head, body = (tuple(item) + ("", ""))[:2]
        return "{ab:" + head + "}" + ("\n" + "\n".join(self.deck.sp + l for l in self._lines(body).split("\n")) if body else "")

    def _card(self, x, y, w, h, item, kind, size):
        item = item if isinstance(item, tuple) else (item,)
        value = (tuple(item) + ("", ""))[2]   # 説明は全角1字下げ（見出しとの階層の差。場合分けの部品と同じ）
        text = self._card_text(item)
        b = self.rect(x, y, w, h, fill=C.LIGHT, text=text, size=size, color=C.TEXT, align="l", anchor="t", name=f"カード_{kind}")
        if value:   # 値（大きな赤い数字）はカードの下に。並べるだけの箱が小さく寂しく見えるのを、言いたい値で埋める
            vh = line_height_in(self.VALUE_SIZE) + 0.1
            self.text(x + 0.12, y + h - vh - 0.08, "{r:" + value + "}", size=self.VALUE_SIZE, bold=True, name=f"カードの値_{kind}")
        return b

    def cards(self, items: list, layout: str = "row", x: float | None = None, y: float | None = None,
              w: float | None = None, h: float | None = None, size: float = BODY_PT, gap: float = 0.3) -> Box:
        """カードの図解。items = [("見出し", "説明1行\\n説明2行"), ...]。3つ目に値を書くと、カードの下に大きな赤い数字で
        （("質量", "合体の前と後", "36+29 → 62")。並べるだけでは箱が小さく寂しいときに、言いたい値で埋める）。layout:
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
            ch = h or max(1.3, self._card_h(items, size, pad=0.6, cw=cw))
            if not h and y + ch > self._bottom_limit():   # 下に入らなければ、余白を詰める（文字が入る高さまで）
                ch = max(self._card_h(items, size, pad=0.3, cw=cw), self._bottom_limit() - y)
            for k, it in enumerate(items):
                self._card(x + k * (cw + gap), y, cw, ch, it, kind, size)
            box = Box(x, y, w, ch)
        elif layout == "grid":
            cols = 2 if n <= 4 else 3
            nrow = (n + cols - 1) // cols
            cw = (w - gap * (cols - 1)) / cols
            ch = h or max(self._card_h(items, size, pad=0.3, cw=cw),
                          min(max(1.1, self._card_h(items, size, cw=cw)), (bottom - y - gap * (nrow - 1)) / nrow))
            for k, it in enumerate(items):
                r, c = divmod(k, cols)
                self._card(x + c * (cw + gap), y + r * (ch + gap), cw, ch, it, kind, size)
            box = Box(x, y, w, nrow * ch + (nrow - 1) * gap)
        elif layout == "steps":
            cw = w * (0.46 if n <= 3 else 0.4)
            ch = h or self._card_h(items, size, pad=0.35, cw=cw)
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
            ch = h or max(self._card_h(items, size, pad=0.3, cw=cw), min(max(1.1, self._card_h(items, size, cw=cw)), (bottom - y - g2) / 2))
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
            text = ch if isinstance(ch, str) else "{b:" + ch[0] + "}" + self.deck.sp + ch[1]
            self.rect(cx, cy, child_w, h, fill=C.LIGHT, text=text, size=size, color=C.TEXT, align="l", name="ツリー")
            self.line(jx, cy + h / 2, cx, cy + h / 2, color=C.GRAY, width=1.5)
        self.cur_x, self.cur_y = x, y + total + 0.35
        return Box(x, y, cx + child_w - x, total)

    def decision(self, steps: list, last: str, x: float | None = None, y: float | None = None,
                 q_w: float = 4.8, out_w: float = 3.8, h: float = 0.7, gap: float = 0.5, size: float = 18,
                 yes: str | None = None, no: str | None = None) -> Box:
        """判定の流れ図：問いを上から順に確かめ、「はい」なら右の結論へ、「いいえ」なら下の次の問いへ。全部「いいえ」なら last。
        steps = [("享受が目的か？", "許諾が要る"), ("権利者の利益を不当に害するか？", "許諾が要る")]、last = "許諾なしで使える"。
        要件・例外・場合分けのように、条件で結論が分かれる所に（表に並べるより、どの順に何を確かめるかが見える）。
        問いは2〜3つまで（4つ以上は縦に入らない。2枚に分けるか、問いをまとめる）。
        yes・no を省くと、デッキの言語の「はい／いいえ」（英語は Yes／No。language.YES_NO）。"""
        import language
        dy, dn = language.YES_NO.get(self.deck.lang, ("Yes", "No"))
        yes, no = yes or dy, no or dn
        if not steps or len(steps) > 3:
            raise ValueError(f"判定の流れ図の問いは1〜3つ（今は {len(steps)} つ）。多ければ2枚に分ける")
        x = self.deck.wide[0] if x is None else x
        y = self.cur_y if y is None else y
        n = len(steps)
        lim_r = self._right_limit(x, y, y + 1)
        if x + q_w + 1.3 + out_w > lim_r + 0.01:   # 右に入らなければ、問いと結論の箱の幅を同じ割合で（手で決めた幅が右にはみ出していた）
            k_ = max(0.6, (lim_r - x - 1.3) / (q_w + out_w))
            q_w, out_w = q_w * k_, out_w * k_
        h = max([h, self._box_text_h(last, q_w, size)]
                + [self._box_text_h(tx, w_, size) for (q_, o_) in steps for tx, w_ in ((q_, q_w), (o_, out_w))])
        total = n * (h + gap) + h
        lim = self._bottom_limit()
        if y + total > lim:   # 下に入らなければ、間を詰める（それでも入らなければ Deck.save が知らせる）
            gap = max(0.36, min(gap, (lim - y - (n + 1) * h) / n))
            total = n * (h + gap) + h
        ox = x + q_w + 1.3
        for k, (q, out) in enumerate(steps):
            qy = y + k * (h + gap)
            self.rect(x, qy, q_w, h, fill=C.PALE, text=q, size=size, name="判定の問い")
            self.arrow(x + q_w + 0.15, qy + h / 2 - 0.2, w=1.0, h=0.4, direction="right")
            self.text(x + q_w + 0.32, qy + h / 2 - 0.62, yes, size=16, color=C.BAND, bold=True, name="判定の枝")   # 問いの箱から 0.4 in（描画の検査の図との間隔）
            self.rect(ox, qy, out_w, h, fill=C.LIGHT, text=out, size=size, name="判定の結論")
            self.arrow(x + q_w / 2 - 0.2, qy + h + 0.06, w=0.4, h=gap - 0.12, direction="down")
            self.text(x + q_w / 2 + 0.3, qy + h + 0.02, no, size=16, color=C.BAND, bold=True, name="判定の枝")
        self.rect(x, y + n * (h + gap), q_w, h, fill=C.LIGHT, text=last, size=size, name="判定の結論")
        self.cur_x, self.cur_y = x, y + total + 0.35
        return Box(x, y, ox + out_w - x, total)

    def before_after(self, before: tuple, after: tuple, value: str | None = None, y: float | None = None,
                     h: float | None = None, size: float = BODY_PT) -> Box:
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
            cb = self.text(out[-1].right - cw_, bottom, caption, size=14, color=C.GRAY, fit=False)
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

    # -- 組む時点の検査（Deck.save が枚ごとに呼ぶ）：本文の場所に入るか。小さな超え（SQUEEZE_MAX まで）は、塊の間を詰めて直す
    SQUEEZE_MAX = 0.3      # in。これまでの超えは、塊・部品の間を詰めて直す（見た目を大きく変えないように、これより大きい超えは知らせるだけ）
    GAP_MIN = 0.15         # 詰めたあとの文の塊どうしの間（in）
    PART_HINTS = (         # 下にはみ出した図形の名前 → (部品, 直し方)。箱の決まり（箱が小さい）を破らない直し方を先に書く
        ("比較の", "比較", "上の塊を1つ減らすか、比較の各列の字を短く（各列は{cmp}行以上のまま：{cmp}行より削ると描画の検査の「箱が小さい」）"),
        ("カード", "カード", "上の文を1つ減らすか、カードの説明を短く（カードの数と大きさはそのまま：小さくすると「箱が小さい」）"),
        ("表の", "表", "表の行を減らすか、セルの言葉を短く（字は {tab:g}pt まで小さくしてある）"),
        ("判定の", "判定の流れ図", "問いを1つ減らすか、上の文を減らす"),
        ("前後_", "前後", "上の文を減らすか、前後の行を短く"),
        ("ツリー", "ツリー", "上の文を減らすか、小分類を減らす"),
        ("まとめの", "まとめ", "持ち帰ることを1つ減らすか、短く"),
    )

    def _fig_font(self, pic, path, w):
        """置いた図の中のいちばん小さい字（figkit.save が画像に書いた MinFontPt × 縮尺）が、描画の検査の下限より小さければ知らせる。"""
        try:
            with Image.open(path) as im:
                mf = float(im.info.get("MinFontPt") or im.text.get("MinFontPt"))
                px, dpi = im.size[0], (im.info.get("dpi") or (0, 0))[0]
        except Exception:   # noqa: BLE001  記録の無い画像（資料の切り出し・写真）は描画の検査が画像から測る
            return
        drawn = px / dpi if dpi and dpi >= 100 else None
        eff = mf * (w / drawn if drawn else 1.0)
        lim = _rule("FIG_FONT_MIN")
        if eff < lim - 0.25:
            self.deck._notes.append((self._no(), f"図の文字が小さい（{pic.name}：いちばん小さい字が置いた大きさで {eff:.1f}pt < {lim:g}pt）"
                                                  " → 置く幅で描き直す（fig() の幅を置く幅に、目盛り・注記は 14pt 以上）"))

    def _body(self):
        """本文の図形：[(要素, Box, 種類, 名前)]。上の見出しの領域・結論の置き場・図に重ねる注目の印は除く。"""
        top = self.deck.area["top"] - 0.3
        out = []
        for el, b, kind in self._shape_box.values():
            nm = el.find(".//" + qn("p:cNvPr")).get("name", "")
            if (b.y < top or nm in Deck.HEADER_NAMES or nm == "青帯" or nm.startswith("注目の") or kind == "ring"
                    or (nm == "結論の囲み" and b.y >= BOX_TOP - 0.1)):
                continue
            out.append((el, b, kind, nm))
        return out

    @staticmethod
    def _vis_bottom(b, kind):
        return b.bottom - INSET_Y if kind == "text" else b.bottom   # 文字の枠は、文字の範囲（描画の検査が測る所）

    def _squeeze(self, need: float, items) -> bool:
        """縦に並ぶ塊（縦に重なる図形のまとまり）の間を詰めて、下端を need（in）上げる。入れば True（図形を動かす）。
        間は文どうし GAP_MIN、下が図・表・箱なら描画の検査の「本文の直下の図・表との間隔」（0.3 in）まで。"""
        items = sorted(items, key=lambda it: it[1].y)
        groups = []
        for it in items:
            if groups and it[1].y < max(self._vis_bottom(g[1], g[2]) for g in groups[-1]) - 0.01:
                groups[-1].append(it)
            else:
                groups.append([it])
        if len(groups) < 2:
            return False
        below_min = _rule("FIG_GAP_BELOW_MIN") / 72.0
        red = []
        for a_, b_ in zip(groups, groups[1:]):
            gap = min(it[1].y for it in b_) - max(self._vis_bottom(it[1], it[2]) for it in a_)
            boxy = any(k in ("image", "shape") for _, _, k, _ in b_)
            red.append(max(0.0, gap - (below_min if boxy else self.GAP_MIN)))
        if sum(red) + 1e-6 < need:
            return False
        shapes = {id(s._element): s for s in self.slide.shapes}
        shift = 0.0
        for k, g in enumerate(groups[1:]):
            shift += need * red[k] / sum(red)
            for el, b, _, _ in g:
                b.y -= shift
                sh = shapes.get(id(el))
                if sh is not None:
                    sh.top = Inches(b.y)
        return True

    def _fit_check(self, squeeze: bool = True) -> list:
        """[(枚, 文)]：本文の場所の下端・右端と、図との間隔。小さな下の超えは詰めて直す（直せたものは出さない）。"""
        if not hasattr(self, "section"):
            return []
        n, out = self._no(), []
        full = self._body()
        if not full:
            return out
        lim = self._bottom_limit()
        body = [it for it in full if it[2] != "line"] or full   # 線（比較の区切り線など）は部品の文字に合わせて動くので、部品の名前で言う
        low = max(body, key=lambda it: self._vis_bottom(it[1], it[2]))
        over = self._vis_bottom(low[1], low[2]) - lim
        if over > 0.005 and squeeze and over <= self.SQUEEZE_MAX:
            moved = self._squeeze(over, full)
            if not moved:   # 右に図が縦いっぱいにある枚：左の列だけを詰める
                figs = [it for it in body if it[2] == "image" and it[1].x > self.deck.area["x"] + 1.0]
                if figs:
                    fx = min(it[1].x for it in figs)
                    left = [it for it in full if it[1].right <= fx + 0.05]
                    if low in left:
                        moved = self._squeeze(over, left)
            if moved:
                low = max(body, key=lambda it: self._vis_bottom(it[1], it[2]))
                over = self._vis_bottom(low[1], low[2]) - lim
        if over > 0.005:
            part, hint = "文", None
            for pre, nm, h in self.PART_HINTS:
                if low[3].startswith(pre):
                    part, hint = nm, h.format(cmp=_rule("COMPARE_MIN_LINES"), tab=_rule("TABLE_FONT_MIN"))
                    break
            if hint is None and low[2] == "image":
                part, hint = "図", "図を低く描き直す（描いた大きさのまま置くので、fig() の高さを本文の場所に合わせる）か、図の上の文を減らす"
            if hint is None:
                t_ = next((t for t in self._texts if t["box"] is low[1]), None)
                sz = t_["size"] if t_ else BODY_PT
                cut = max(1, -(-over // line_height_in(sz)))
                hint = f"要点を1つ減らすか短く（あと {int(cut)} 行ほど減らす）"
            out.append((n, f"{part}の下端 {self._vis_bottom(low[1], low[2]):.2f} in、限り {lim:.2f} in（{over:.2f} in 超え"
                           + ("。小さな超えは間を詰めて直すが、それでも入らない" if over <= self.SQUEEZE_MAX else "") + f"）→ {hint}"))
        # 右の限り（本文の場所の右）・図との間隔
        a = self.deck.area
        rlim = max(a["right"], SLIDE_W - _rule("PAGE_MARGIN") / 72.0) + _rule("RIGHT_TOL") / 72.0
        ext = {}
        for t_ in self._texts:
            if t_["lines"]:
                ext[id(t_["box"])] = t_["box"].x + INSET_X + max(line_extent_pt(l, t_["size"], t_["bold"]) for l in t_["lines"]) / 72.0
        wide = [(it, ext.get(id(it[1]), it[1].right)) for it in body if it[2] != "line"]
        wide = [(it, r) for it, r in wide if r > rlim + 0.01]
        if wide:
            it, r = max(wide, key=lambda x: x[1])
            out.append((n, f"{it[3] or '図形'}の右端 {r:.2f} in、限り {rlim:.2f} in（{r - rlim:.2f} in 超え）→ 幅を狭く（図は fig_x から描いた幅のまま。"
                           "箱・表は幅を減らす）"))
        gap_min = _rule("FIG_GAP_MIN") / 72.0
        figs = [it for it in body if it[2] == "image"]
        for t_ in self._texts:   # 本文が図に重なる（図の左端の近くから始まる文は、折り返しでは直らない）
            b = t_["box"]
            if not t_["fit"] or id(b) not in ext:
                continue
            for el, f, kind, nm in figs:
                ox = min(ext[id(b)], f.right) - max(b.x + INSET_X, f.x)
                oy = min(b.bottom - INSET_Y, f.bottom) - max(b.y + INSET_Y, f.y)
                if ox > 0.03 and oy > 0.03 and f.x > b.x:
                    out.append((n, f"文「{''.join(r.text for r in t_['lines'][0])[:12]}」が{nm or '図'}に重なる（文の右端 {ext[id(b)]:.2f} in、"
                                   f"図の左端 {f.x:.2f} in）→ 文を図の左に収める（展開の左右を短く・図を小さく描き直す）か、図を下に置く型（figure_below）に"))
                    break
            else:
                continue
            break
        for t_ in self._texts:
            b = t_["box"]
            if not t_["fit"] or id(b) not in ext:
                continue
            for el, f, kind, nm in body:
                if kind in ("image", "shape") and f.x - b.x >= 1.0 and f.y < b.bottom - INSET_Y and b.y + INSET_Y < f.bottom:
                    g = f.x - ext[id(b)]
                    if g < gap_min - 0.005 and not (kind == "image" and g < 0):   # 図に重なるものは上で出した
                        cpl = int((f.x - gap_min - b.x - INSET_X) * 72 / t_["size"])
                        head = f"文「{''.join(r.text for r in t_['lines'][0])[:12]}」と{nm or '図'}の間 {g:.2f} in < {gap_min:.1f} in"
                        out.append((n, head + (f" → 文の行を短く（ここは1行 {cpl}字まで）" if cpl >= 6 else
                                               f"（文の左端 {b.x:.2f} in、図の左端 {f.x:.2f} in）→ 文を図の左に収める"
                                               "（展開の左右を短く・図を小さく描き直す）か、図を下に置く型（figure_below）に")))
                        break
        return out

    # -- 流し込みレイアウト（上から順に置く）
    def at(self, x: float, y: float):
        self.cur_x, self.cur_y = x, y
        return self

    def skip(self, dy: float):
        self.cur_y += dy
        return self

    def p(self, text: str, dx: float = 0.0, gap: float = 0.3, size: float = BODY_PT, **kw) -> Box:
        """カーソル位置にテキストを置き、下へ進める。dx はカーソルxからの字下げ。"""
        b = self.text(self.cur_x + dx, self.cur_y, text, size=size, **kw)
        self.cur_y = b.bottom + gap
        return b

    def peq(self, latex: str, dx: float = 0.4, gap: float = 0.3, size: float = BODY_PT, color: str | None = None) -> Box:
        b = self.eq(latex, self.cur_x + dx + INSET_X, self.cur_y + 0.03, size=size, color=color)
        self.cur_y = b.bottom + gap
        return b

    def prow(self, parts: list, dx: float = 0.0, gap: float = 0.3, size: float = BODY_PT) -> Box:
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
                 sections: list | None = None, valign: str | None = None, lang: str | None = None):
        """template：構造（テンプレート1〜8 か追加したもの）。color：配色の名前（assets/templates/配色.json。省けば構造の標準の色）。
        sections：章のナビの構造で上に並べる章の名前（省けば、本文の枚のタイトルを出てきた順に）。
        lang：スライドの言語（設定の「言語」。省けば日本語）。文字の言語の印と pptx の言語の印に書き、検査がそれで目安を変える。"""
        import language
        self.lang = language.lang_name(lang)
        self.lang_code = language.lang_code(self.lang)
        self.alt_code = "en-US" if self.lang_code.startswith("ja") else "ja-JP"
        # 部品が入れる字下げ・区切りの空白。日本語は全角の空白、ほかの言語は半角2つ（英語の試しで、全角の空白が英字の間に残った）
        self.sp = "　" if self.lang == "日本語" else "  "
        self.prs = Presentation(str(template))
        global _METER
        try:   # 文字を測る道具（描画の検査と同じ計算。テンプレートのテーマの書体・デッキの言語で）
            self.meter = Meter(self.prs, self.lang_code, self.alt_code) if _RC else None
        except Exception:   # noqa: BLE001
            self.meter = None
        _METER = self.meter
        self._notes: list = []   # 組む時点の知らせ [(枚, 文)]（save で WARN にして出す）
        self._wraps: list = []   # 右の限りで折り返した行 [(枚, 元の行, 1行の字数, 部品)]
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
                rpr = fld.makeelement(qn("a:rPr"), {"lang": self.lang_code, "altLang": self.alt_code})
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
                rPr.set("lang", self.lang_code); rPr.set("altLang", self.alt_code)
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
                    size: float = 44, bold: bool = True, roadmap: list[str] | None = None) -> Slide:
        """表紙／区切りスライド（左上の縦棒だけのレイアウト）。lines は節番号付きの題目を1行ずつ。
        論文の表紙（過去の論文紹介のデッキの形）は lines に英題（2行まで）、subtitle に和訳（28pt）、author に著者名（20pt、\\n で2行）。
        元デッキの英題は太字でないので bold=False にする。
        roadmap（講座）は、問いから答えまでの段 ["A", "B", "C"]。題の下に「今日の道筋：A → B → C」を1行（入らなければ2行）で置く。"""
        slide = self.prs.slides.add_slide(self.layout_title)
        for ph in list(slide.placeholders):  # 空のタイトル枠は使わない（元デッキ同様テキストボックスで置く）
            ph._element.getparent().remove(ph._element)
        s = Slide(self, slide)
        text = "\n".join(lines)
        runs = split_lines(parse_markup(text))
        x0, x1 = self._cover_span(self.layout_title)
        size0 = size
        while True:   # 題が表紙の幅に入らなければ 2pt ずつ小さく（32pt まで。それでも入らない1行の題は2行に折ってやり直す）
            tw = max(text_width_pt(l, size, bold) for l in runs) / 72.0 + 2 * INSET_X + 0.1
            if tw <= x1 - x0 - 0.4:
                break
            if size <= 32:
                if len(runs) == 1:
                    text = wrap_to(text, x1 - x0 - 0.6, size0)
                    runs = split_lines(parse_markup(text))
                    if len(runs) > 1:
                        size = size0
                        continue
                break
            size -= 2
        if tw > x1 - x0 - 0.4:
            self._notes.append((len(self.prs.slides), f"表紙の題が幅に入らない（{size}pt でも {tw:.1f} in > {x1 - x0 - 0.4:.1f} in）："
                                                       f"「{text[:16]}」 → \\n で行を分ける"))
        th = len(runs) * line_height_in(size) * 0.95 + 2 * INSET_Y
        top = 2.44 if len(runs) >= 2 else 2.75
        cx = (x0 + x1) / 2
        s.text(cx - tw / 2, top, text, size=size, bold=bold, align="c", w=tw)
        y = top + th + 0.25
        if subtitle:
            sw = max(text_width_pt(l, 28) for l in split_lines(parse_markup(subtitle))) / 72.0 + 0.3
            b = s.text(cx - sw / 2, y, subtitle, size=28, align="c", w=sw)
            y = b.bottom + 0.3
        if roadmap:
            head = "今日の道筋：" if self.lang == "日本語" else "Today: "
            line = head + " → ".join(roadmap)
            span = x1 - x0 - 0.8
            if text_width_pt(parse_markup(line), 20) / 72.0 + 0.3 > span:   # 入らなければ段の区切りで2行に
                k = -(-len(roadmap) // 2)
                line = head + " → ".join(roadmap[:k]) + " →\n" + " → ".join(roadmap[k:])
            rw = min(span, max(text_width_pt(l, 20) for l in split_lines(parse_markup(line))) / 72.0 + 0.3)
            b = s.text(cx - rw / 2, y, line, size=20, color=C.TEXT, align="c", w=rw, name="道筋")
            y = b.bottom + 0.1
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
        s.text(1.6, 2.9, f"{number}{self.sp}{title}", size=40, bold=True, color="FFFFFF", name="区切り")
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

    def fit_report(self, squeeze: bool = True) -> list:
        """組む時点の知らせ [(枚, 文)]：本文の場所に入るか（0.3 in までの超えは塊の間を詰めて直し、出さない）・右の限り・図との間隔・
        図の文字の大きさと、描画の検査の構造の決まり（文の塊の数・箱が小さい・箱のまわりが空いている。check_layout の同じ関数で）。
        1回だけ計算する（save と、設計メモの確認 check_memo.py の見積もりが使う）。"""
        if getattr(self, "_report", None) is not None:
            return self._report
        out = list(self._notes)
        for s in self.slides:
            out += s._fit_check(squeeze)
        out += self._structure_notes()
        self._report = sorted(out, key=lambda x: x[0])
        return self._report

    def _structure_notes(self) -> list:
        """描画の検査の構造の決まり（check_layout.unit_msgs・box_msgs）を、組んだ枚に同じ基準で当てる。"""
        if self.meter is None:
            return []
        try:
            import check_layout as CL
        except Exception:   # noqa: BLE001
            return []
        out = []
        W = self.prs.slide_width / 12700.0
        for s in self.slides:
            if not hasattr(s, "section"):
                continue
            n = s._no()
            try:
                items = _RC.shape_rows(self.meter.rd, s.slide, n)
            except Exception:   # noqa: BLE001
                continue
            if CL.is_qa_slide(items) or CL.is_cover_slide(items):
                continue
            banded = (band_placeholder_idx(s.slide.slide_layout, self.prs.slide_height) is not None
                      or any(sh.name == "青帯" for sh in s.slide.shapes))
            for level, msg in CL.unit_msgs(items) + CL.box_msgs(items, W, CL.BAND_TOP if banded else CL.NOBAND_BOTTOM):
                if level == "ERROR":   # 描画の検査で ERROR になるものだけ（WARN は検査の出力に任せる）
                    out.append((n, msg.split(" → ")[0] + "（描画の検査と同じ基準）"))
        return out

    def save(self, path: str | Path, title: str | None = None, author: str | None = None):
        if not getattr(self, "_reported_once", False):
            for n, msg in self.fit_report():
                print(f"[WARN] {n}枚目：{msg}")
            self._reported_once = True
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
        self.prs.core_properties.language = self.lang_code   # check_layout・notes_html がこれで言語を知る
        self.prs.save(str(path))
        print(f"saved {path} ({len(self.prs.slides)} slides)")


def wrap_to(text: str, width: float, size: float) -> str:
    """幅 width (in) に入らない1行を、真ん中に近い「、」か助詞の後ろで2行に分ける（柱の中の結論など、幅の決まった所に）。"""
    if "\n" in text or text_width_pt(parse_markup(text), size) / 72.0 + 2 * INSET_X <= width:
        return text
    mid = len(text) / 2
    if " " in text.strip() and not any(unicodedata.east_asian_width(c) in "WF" for c in text):   # 空白で語を区切る言語：真ん中に近い空白で
        cands = [i for i, ch in enumerate(text) if ch == " " and 0 < i < len(text) - 1]
        k = min(cands, key=lambda i: abs(i - mid))
        return text[:k].rstrip() + "\n" + text[k:].lstrip()
    cands = [i + 1 for i, ch in enumerate(text[:-1]) if ch in "、，,・" or text[i:i + 1] in "でとがはをにの"]
    k = min(cands, key=lambda i: abs(i - mid)) if cands else int(mid)
    return text[:k] + "\n" + text[k:]
