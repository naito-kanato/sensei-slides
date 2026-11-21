"""PowerPoint を使わない描画の検査（pptx だけから、文字の配置を計算して描く）。

render_check.ps1 と同じ形の shapes.json と slide-NN.png を作る。shapes.json には "engine": "python" が入り、
check_layout.py は PowerPoint と同じ基準で見る（LibreOffice 用のゆるめの補正は当てない）。

    python render_check_py.py -Pptx deck.pptx -OutDir <work>/render [-Width 1600] [-NoImages]

文字の範囲（tl/tt/tw/th）と行数（lines）は、PowerPoint の TextRange の BoundLeft/Top/Width/Height と Lines() に合わせて計算する。
  - 文字の大きさ・書体・揃え・段落の前後の間隔・行間は、ラン → 段落 → 図形の lstStyle → （プレースホルダなら）レイアウト → マスター
    の文字の書式 → presentation.xml の既定、の順に受け継ぐ
  - 書体：ランの書体 → テーマの書体（+mn-lt など）。和文の枠は、ランの言語の書体（テーマの <a:font script="Jpan">）を先に使う
    （PowerPoint の描画と比べて、テーマの ea が Meiryo でも日本語のランは ＭＳ Ｐゴシック で描かれていた）。
    フォントのファイルは OS のフォントのフォルダから名前で探し、無ければ zemi と同じ代わりのフォント
  - 1行の高さは 大きさ × 1.2 × 行間（PowerPoint の実測。書体によらない）、幅は書体の送り幅の和 ＋ 行末の空白1つ分
    （PowerPoint の BoundWidth は、行末の段落記号の幅を含む）
  - 折り返す枠（wrap="square"）は、日本語の行頭・行末の禁則と、英単語の途中で切らないことを入れて行を割る
  - 余白（bodyPr の lIns/tIns/rIns/bIns。既定 0.1 in・0.05 in）と縦の位置（anchor）から、文字の塊の位置を決める
画像は PIL で、背景・マスターとレイアウトの飾りの図形・スライドの図形（画像・四角・角丸・楕円・線と矢印・表・文字）を重なりの順に描く。
グラフ・SmartArt・3D などは描けない（灰色の枠で場所だけ示す）。数式の入った文字の枠（mc:AlternateContent）は、文字の範囲と行数は
数式の字を横に並べて数え（分数・添え字の組みはおおよそ。幅は PowerPoint より少し狭く出る）、絵は Fallback の画像で描く。最後の確認は、描いた画像を目で見て行う。
"""
from __future__ import annotations

import argparse
import io
import json
import math
import os
import platform
import re
import sys
import tempfile
import logging
from functools import lru_cache
from pathlib import Path

logging.getLogger("fontTools").setLevel(logging.ERROR)   # 古いフォントの作成日の警告（無害）を出さない
EMU_PT = 12700.0
NS = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main",
      "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
A = "{%s}" % NS["a"]
P = "{%s}" % NS["p"]
R = "{%s}" % NS["r"]
LINE_FACTOR = 1.2      # 行間 100% の1行の高さ ＝ 文字の大きさ × 1.2（PowerPoint の実測。MS PGothic・Yu Gothic・Segoe UI で同じ）
DEFAULT_INS = (91440, 45720, 91440, 45720)   # bodyPr の lIns・tIns・rIns・bIns の既定（EMU）
KERN = True           # 字の組の詰め（kern 表）を入れる
SUPER_SCALE = 2 / 3    # 上付き・下付き（baseline）の文字の大きさの縮み（PowerPoint の既定の上付きと同じ程度）


# ---- フォント ------------------------------------------------------------------------------------------
def font_dirs():
    s = platform.system()
    if s == "Windows":
        ds = [Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"]
        if os.environ.get("LOCALAPPDATA"):
            ds.append(Path(os.environ["LOCALAPPDATA"]) / "Microsoft" / "Windows" / "Fonts")
    elif s == "Darwin":
        ds = [Path("/System/Library/Fonts"), Path("/System/Library/Fonts/Supplemental"), Path("/Library/Fonts"),
              Path.home() / "Library" / "Fonts"]
    else:
        ds = [Path("/usr/share/fonts"), Path("/usr/local/share/fonts"), Path.home() / ".fonts",
              Path.home() / ".local" / "share" / "fonts"]
    return [d for d in ds if d.is_dir()]


def _font_files():
    out = []
    for d in font_dirs():
        for root, _, files in os.walk(d):
            for f in files:
                if f.lower().endswith((".ttf", ".ttc", ".otf", ".otc")):
                    out.append(Path(root) / f)
    return out


def _scan(files):
    """フォントのファイルを読み、{書体の名前（小文字）: [[ファイル, 番号, 太字, 斜体, 字の太さ], ...]}。"""
    from fontTools.ttLib import TTCollection, TTFont
    idx = {}
    for p in files:
        try:
            fonts = TTCollection(str(p), lazy=True).fonts if p.suffix.lower() in (".ttc", ".otc") else [TTFont(str(p), lazy=True)]
        except Exception:
            continue
        for i, ft in enumerate(fonts):
            try:
                names = ft["name"].names
                os2 = ft["OS/2"] if "OS/2" in ft else None
                sel = os2.fsSelection if os2 is not None else 0
                weight = os2.usWeightClass if os2 is not None else 400
                mac = ft["head"].macStyle
            except Exception:
                continue
            bold = bool(sel & 0x20 or mac & 1)
            ital = bool(sel & 0x01 or mac & 2)
            fam1, fam16 = set(), set()
            for r in names:
                if r.nameID in (1, 16):
                    try:
                        t = r.toUnicode().strip().lower()
                    except Exception:
                        continue
                    (fam1 if r.nameID == 1 else fam16).add(t)
            for t in fam1:
                idx.setdefault(t, []).append([str(p), i, bold, ital, weight, 1])
            for t in fam16 - fam1:
                idx.setdefault(t, []).append([str(p), i, bold, ital, weight, 16])
    return idx


_INDEX = None


def font_index():
    """書体の名前からファイルを引く表。一時フォルダに覚えておき、フォントのフォルダが変わったら作り直す。"""
    global _INDEX
    if _INDEX is not None:
        return _INDEX
    files = _font_files()
    sig = f"{len(files)}:{sum(int(f.stat().st_mtime) for f in files[:4000]) if files else 0}"
    cache = Path(tempfile.gettempdir()) / "sensei_slides_font_index_v1.json"
    try:
        d = json.loads(cache.read_text(encoding="utf-8"))
        if d.get("sig") == sig:
            _INDEX = d["index"]
            return _INDEX
    except Exception:
        pass
    _INDEX = _scan(files)
    try:
        cache.write_text(json.dumps({"sig": sig, "index": _INDEX}, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass
    return _INDEX


# 名前で見つからないときの代わり（zemi.py の文字幅の見積もりと同じ考え方：Windows のテーマのフォントに近いものを Mac・Linux でも探す）
FALLBACK_FAMILIES = {
    "ea": ["ms pgothic", "yu gothic", "meiryo", "hiragino sans", "hiragino kaku gothic pron", "ヒラギノ角ゴシック",
           "noto sans cjk jp", "noto sans jp", "ipaexgothic", "ipaexゴシック", "takaoexgothic"],
    "latin": ["arial", "segoe ui", "helvetica", "helvetica neue", "liberation sans", "dejavu sans", "noto sans"],
    "serif": ["times new roman", "times", "liberation serif", "dejavu serif", "noto serif"],
}
CHECK_FONTS = ["MS PGothic", "Segoe UI", "Arial"]   # 同梱のテンプレートのテーマの書体（check_env.py が、あるか確かめる）
# 字が書体に無いときに探す書体（PowerPoint・Windows の代わりの字の探し方に近いもの）
GLYPH_FALLBACK = ["segoe ui symbol", "cambria math", "segoe ui", "ms gothic", "yu gothic", "arial unicode ms",
                  "segoe ui emoji", "apple symbols", "stix two math", "dejavu sans", "noto sans symbols",
                  "noto sans symbols2", "noto sans math"]
SERIF_HINT = re.compile(r"times|mincho|明朝|serif|cambria|georgia|century|garamond|palatino", re.I)


class Face:
    """1つのフォントのファイル（ttc なら番号も）。送り幅と字の有無を fontTools で読む。"""
    _cache = {}

    def __init__(self, path, index, synth_bold=False, synth_italic=False):
        self.path, self.index = path, index
        self.synth_bold, self.synth_italic = synth_bold, synth_italic
        self._cmap = self._hmtx = None
        self.upem = 1000
        self._wcache = {}

    @classmethod
    def get(cls, path, index, synth_bold=False, synth_italic=False):
        k = (path, index, synth_bold, synth_italic)
        if k not in cls._cache:
            cls._cache[k] = Face(path, index, synth_bold, synth_italic)
        return cls._cache[k]

    def _load(self):
        if self._cmap is not None:
            return
        from fontTools.ttLib import TTFont
        self._kern = {}
        try:
            ft = TTFont(self.path, fontNumber=self.index, lazy=True)
            self._cmap = ft.getBestCmap() or {}
            self._hmtx = ft["hmtx"].metrics
            self.upem = ft["head"].unitsPerEm
            if "kern" in ft:   # 字の組の詰め（kern 表。GPOS の詰めは読まない：読んでも PowerPoint の幅に近づかなかった）
                for t in ft["kern"].kernTables:
                    kt = getattr(t, "kernTable", None)
                    if kt:
                        self._kern.update(kt)
        except Exception:
            self._cmap, self._hmtx = {}, {}

    def kern(self, a, b):
        """a と b の間の詰め（em。負なら詰める）。"""
        self._load()
        if not self._kern:
            return 0.0
        ga, gb = self._cmap.get(ord(a)), self._cmap.get(ord(b))
        if ga is None or gb is None:
            return 0.0
        return self._kern.get((ga, gb), 0) / self.upem

    def has(self, ch):
        self._load()
        return ord(ch) in self._cmap

    def advance(self, ch):
        """1文字の送り幅（em）。"""
        w = self._wcache.get(ch)
        if w is None:
            self._load()
            g = self._cmap.get(ord(ch))
            m = self._hmtx.get(g) if g else self._hmtx.get(".notdef")
            w = (m[0] / self.upem) if m else (1.0 if is_ea(ch) else 0.55)
            self._wcache[ch] = w
        return w


@lru_cache(maxsize=None)
def find_face(family: str, bold: bool, italic: bool):
    """書体の名前・太字・斜体から Face。見つからなければ None。"""
    if not family:
        return None
    idx = font_index()
    cands = idx.get(family.strip().lower())
    if not cands:
        return None
    best = None
    for path, i, b, it, wt, src in cands:
        score = (0 if b == bold else 2) + (0 if it == italic else 1) + (0 if src == 1 else 0.5) + abs(wt - (700 if bold else 400)) / 1000
        if best is None or score < best[0]:
            best = (score, path, i, b, it)
    _, path, i, b, it = best
    return Face.get(path, i, synth_bold=bold and not b, synth_italic=italic and not it)


@lru_cache(maxsize=None)
def fallback_face(kind: str, bold: bool, italic: bool):
    for fam in FALLBACK_FAMILIES[kind]:
        f = find_face(fam, bold, italic)
        if f:
            return f
    try:   # zemi.py の代わりのフォントの候補（フォントの索引が作れない環境でも）
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import zemi
        key = "ea" if kind == "ea" else ("latin_i" if kind == "serif" else ("latin_b" if bold else "latin"))
        for path, index in zemi._FONT_FILES.get(key, []):
            if Path(path).exists():
                return Face.get(str(path), index)
    except Exception:
        pass
    return None


@lru_cache(maxsize=None)
def glyph_fallback(ch: str, bold: bool):
    o = ord(ch)
    order = GLYPH_FALLBACK
    if 0x2200 <= o <= 0x22FF or 0x27C0 <= o <= 0x27EF or 0x2980 <= o <= 0x2AFF or 0x1D400 <= o <= 0x1D7FF:
        order = ["cambria math"] + GLYPH_FALLBACK   # 数学の記号
    for fam in order:
        f = find_face(fam, bold, False)
        if f and f.has(ch):
            return f
    return None


def is_ea(ch: str) -> bool:
    """和文の書体（ea）で描く字か。CJK・かな・全角の字と、日本語の文の中で全角で描かれる記号。"""
    o = ord(ch)
    return (0x2E80 <= o <= 0x9FFF or 0xF900 <= o <= 0xFAFF or 0xFE30 <= o <= 0xFE4F or 0xFF00 <= o <= 0xFFEF
            or 0x3000 <= o <= 0x30FF or 0x20000 <= o <= 0x2FFFF or o in EA_SYMBOLS)


# 日本語のランで和文の書体になる記号（PowerPoint の描画と幅を比べて決めた）
# （⇒・≪・≫・∝ などの数学の記号と矢印は、和文の書体に字があっても欧文の側で描かれ、欧文の書体に無ければ代わりの書体（Cambria Math など）になる）
# 矢印（→ など）は欧文の書体で描かれた（Segoe UI のテーマで → が 0.86 字分の幅）。● と × は英語のラン（altLang が ja-JP）でも和文の書体
# ↔ は日本語のランで和文の書体（MS PGothic の幅）だった
EA_SYMBOLS = set(map(ord, "・…‥―‐“”‘’※○●◎◇◆□■△▲▽▼☆★♪↔"
                          "§¨°±´¶×÷"))
SYNTH_BOLD_PT = 0.12   # 太字の字が無い書体（MS PGothic など）を太字にしたとき、1字ごとに広がる幅（pt。16〜44pt で大きさによらない。実測）
SYNTH_BOLD_MIN = 15.5  # これより小さい字は広がらない（15pt のタイトルでは広がらなかった）


# ---- 色 ----------------------------------------------------------------------------------------------
PRESET_COLORS = {"black": "000000", "white": "FFFFFF", "red": "FF0000", "green": "008000", "blue": "0000FF",
                 "yellow": "FFFF00", "gray": "808080", "grey": "808080", "darkGray": "A9A9A9", "lightGray": "D3D3D3",
                 "orange": "FFA500", "navy": "000080"}


def _hex(h):
    h = (h or "000000").strip()
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _rgb_to_hsl(r, g, b):
    r, g, b = r / 255, g / 255, b / 255
    mx, mn = max(r, g, b), min(r, g, b)
    l = (mx + mn) / 2
    if mx == mn:
        return 0.0, 0.0, l
    d = mx - mn
    s = d / (2 - mx - mn) if l > 0.5 else d / (mx + mn)
    if mx == r:
        h = (g - b) / d + (6 if g < b else 0)
    elif mx == g:
        h = (b - r) / d + 2
    else:
        h = (r - g) / d + 4
    return h / 6, s, l


def _hsl_to_rgb(h, s, l):
    def f(p, q, t):
        t %= 1
        if t < 1 / 6:
            return p + (q - p) * 6 * t
        if t < 1 / 2:
            return q
        if t < 2 / 3:
            return p + (q - p) * (2 / 3 - t) * 6
        return p
    if s == 0:
        v = l
        return (round(v * 255),) * 3
    q = l * (1 + s) if l < 0.5 else l + s - l * s
    p = 2 * l - q
    return tuple(round(255 * f(p, q, h + d)) for d in (1 / 3, 0, -1 / 3))


class Colors:
    """テーマの色とマスターの色の割り当て（clrMap）。"""

    def __init__(self, scheme: dict, cmap: dict):
        self.scheme, self.cmap = scheme, cmap

    def scheme_rgb(self, name):
        name = self.cmap.get(name, name)
        return _hex(self.scheme.get(name, "000000"))

    def of(self, el, ph=None):
        """色の要素（srgbClr などを子に持つ要素か、色の要素そのもの）→ (r, g, b, a)。無ければ None。"""
        if el is None:
            return None
        c = el if el.tag in (A + "srgbClr", A + "schemeClr", A + "sysClr", A + "prstClr", A + "scrgbClr", A + "hslClr") else None
        if c is None:
            for t in ("srgbClr", "schemeClr", "sysClr", "prstClr", "scrgbClr", "hslClr"):
                c = el.find(A + t)
                if c is not None:
                    break
        if c is None:
            return None
        tag = c.tag[len(A):]
        if tag == "srgbClr":
            rgb = _hex(c.get("val"))
        elif tag == "schemeClr":
            v = c.get("val")
            rgb = ph if (v == "phClr" and ph) else self.scheme_rgb(v)
            rgb = rgb[:3]
        elif tag == "sysClr":
            rgb = _hex(c.get("lastClr") or ("FFFFFF" if c.get("val") == "window" else "000000"))
        elif tag == "prstClr":
            rgb = _hex(PRESET_COLORS.get(c.get("val"), "000000"))
        elif tag == "scrgbClr":
            rgb = tuple(round(255 * min(1, int(c.get(k, "0")) / 100000) ** (1 / 2.2)) for k in ("r", "g", "b"))
        else:
            rgb = _hsl_to_rgb(int(c.get("hue", "0")) / 21600000, int(c.get("sat", "0")) / 100000, int(c.get("lum", "0")) / 100000)
        alpha = 1.0
        for m in c:
            k, v = m.tag[len(A):], int(m.get("val", "0")) / 100000
            if k == "alpha":
                alpha = v
            elif k in ("lumMod", "lumOff"):
                h, s, l = _rgb_to_hsl(*rgb)
                l = l * v if k == "lumMod" else min(1, l + v)
                rgb = _hsl_to_rgb(h, s, l)
            elif k == "tint":
                rgb = tuple(round(x + (255 - x) * (1 - v)) for x in rgb)
            elif k == "shade":
                rgb = tuple(round(x * v) for x in rgb)
        return (*rgb, alpha)


# ---- 文字の書式の受け継ぎ ----------------------------------------------------------------------------------
TITLE_TYPES = {"title", "ctrTitle"}
BODY_TYPES = {"body", "subTitle", "obj", None}


def _lvl(lst, n):
    """lstStyle などから lvl{n}pPr。"""
    if lst is None:
        return None
    return lst.find(f"{A}lvl{n}pPr")


class Deck:
    """pptx 全体の情報（テーマ・既定の文字の書式）。"""

    def __init__(self, prs):
        self.prs = prs
        self.W = prs.slide_width / EMU_PT
        self.H = prs.slide_height / EMU_PT
        pres = prs.part._element
        self.default_style = pres.find(P + "defaultTextStyle")
        self._themes = {}

    def theme(self, master):
        key = id(master)
        if key not in self._themes:
            from lxml import etree
            th = None
            for rel in master.part.rels.values():
                if rel.reltype.endswith("/theme"):
                    th = etree.fromstring(rel.target_part.blob)
            fonts = {"major": {}, "minor": {}}
            scheme = {}
            fill_styles, line_styles = [], []
            if th is not None:
                for kind in ("major", "minor"):
                    f = th.find(f".//{A}{kind}Font")
                    if f is not None:
                        for t in ("latin", "ea", "cs"):
                            e = f.find(A + t)
                            fonts[kind][t] = e.get("typeface", "") if e is not None else ""
                        for e in f.findall(A + "font"):
                            fonts[kind][e.get("script")] = e.get("typeface", "")
                cs = th.find(f".//{A}clrScheme")
                if cs is not None:
                    for e in cs:
                        n = e.tag[len(A):]
                        c = e.find(A + "srgbClr")
                        if c is not None:
                            scheme[n] = c.get("val")
                        else:
                            c = e.find(A + "sysClr")
                            if c is not None:
                                scheme[n] = c.get("lastClr") or ("FFFFFF" if c.get("val") == "window" else "000000")
                fl = th.find(f".//{A}fillStyleLst")
                fill_styles = list(fl) if fl is not None else []
                ll = th.find(f".//{A}lnStyleLst")
                line_styles = list(ll) if ll is not None else []
            cm = master._element.find(P + "clrMap")
            cmap = dict(cm.attrib) if cm is not None else {}
            self._themes[key] = dict(fonts=fonts, colors=Colors(scheme, cmap), fill_styles=fill_styles, line_styles=line_styles)
        return self._themes[key]


def placeholder_chain(sh):
    """プレースホルダの受け継ぎ元 [レイアウトの図形, マスターの図形]（あるものだけ）。"""
    out = []
    cur = sh
    for _ in range(2):
        try:
            base = cur._base_placeholder
        except Exception:
            base = None
        if base is None:
            break
        out.append(base)
        cur = base
    return out


def ph_type(sh):
    try:
        ph = sh._element.ph
        if ph is None:
            return None
        return ph.get("type", "obj")
    except Exception:
        return None


class TextCtx:
    """1つの図形の文字の書式の受け継ぎの鎖。"""

    def __init__(self, deck, sh, master, txbody=None, table_cell=False, style_font_color=None):
        self.deck, self.sh = deck, sh
        self.th = deck.theme(master)
        self.txbody = txbody if txbody is not None else sh._element.find(".//" + P + "txBody")
        self.ptype = ph_type(sh) if not table_cell else None
        self.is_ph = self.ptype is not None and not table_cell
        self.bases = placeholder_chain(sh) if self.is_ph else []
        lst = []   # 低い方（既定）から高い方（図形）へ
        if deck.default_style is not None:
            lst.append(deck.default_style)
        if self.is_ph:
            txs = master._element.find(f"{P}txStyles")
            if txs is not None:
                key = "titleStyle" if self.ptype in TITLE_TYPES else ("bodyStyle" if self.ptype in BODY_TYPES else "otherStyle")
                st = txs.find(P + key)
                if st is not None:
                    lst.append(st)
            for b in reversed(self.bases):
                tb = b._element.find(".//" + P + "txBody")
                if tb is not None and tb.find(A + "lstStyle") is not None:
                    lst.append(tb.find(A + "lstStyle"))
        if table_cell:
            lst = [deck.default_style] if deck.default_style is not None else []
        if self.txbody is not None and self.txbody.find(A + "lstStyle") is not None:
            lst.append(self.txbody.find(A + "lstStyle"))
        self.lst = lst
        self.style_font_color = style_font_color
        sppr = sh._element.find(P + "spPr") if not table_cell else None
        geom = sppr.find(A + "prstGeom") if sppr is not None else None
        self.geom = geom
        self.prst = geom.get("prst") if geom is not None else None
        # bodyPr：図形 → レイアウト → マスター
        bps = []
        if self.txbody is not None and self.txbody.find(A + "bodyPr") is not None:
            bps.append(self.txbody.find(A + "bodyPr"))
        for b in self.bases:
            tb = b._element.find(".//" + P + "txBody")
            if tb is not None and tb.find(A + "bodyPr") is not None:
                bps.append(tb.find(A + "bodyPr"))
        self.bodyprs = bps

    def body_attr(self, name, default=None):
        for bp in self.bodyprs:
            v = bp.get(name)
            if v is not None:
                return v
        return default

    def ppr_chain(self, lvl, ppr):
        """段落の書式の要素を、低い方から高い方へ。"""
        ch = []
        for l in self.lst:
            e = _lvl(l, lvl + 1)
            if e is not None:
                ch.append(e)
        if ppr is not None:
            ch.append(ppr)
        return ch

    def para_props(self, p):
        ppr = p.find(A + "pPr")
        lvl = int(ppr.get("lvl", "0")) if ppr is not None else 0
        chain = self.ppr_chain(lvl, ppr)
        d = dict(algn="l", marL=0, indent=0, lnSpc=None, spcBef=None, spcAft=None, bullet=None, defTab=914400,
                 buFont=None, buSz=None, buClr=None, hang=True)
        for e in chain:
            if e.get("hangingPunct") is not None:
                d["hang"] = e.get("hangingPunct") in ("1", "true")
            for k in ("algn", "marL", "indent"):
                if e.get(k) is not None:
                    d[k] = e.get(k) if k == "algn" else int(e.get(k))
            if e.get("defTabSz") is not None:
                d["defTab"] = int(e.get("defTabSz"))
            for k in ("lnSpc", "spcBef", "spcAft"):
                s = e.find(A + k)
                if s is not None:
                    pc, pt = s.find(A + "spcPct"), s.find(A + "spcPts")
                    if pc is not None:
                        d[k] = ("pct", int(pc.get("val", "100000")) / 100000)
                    elif pt is not None:
                        d[k] = ("pts", int(pt.get("val", "0")) / 100)
            if e.find(A + "buNone") is not None:
                d["bullet"] = None
            elif e.find(A + "buChar") is not None:
                d["bullet"] = e.find(A + "buChar").get("char", "•")
            elif e.find(A + "buAutoNum") is not None:
                d["bullet"] = ("auto", e.find(A + "buAutoNum").get("type", "arabicPeriod"),
                               int(e.find(A + "buAutoNum").get("startAt", "1")))
            if e.find(A + "buFont") is not None:
                d["buFont"] = e.find(A + "buFont").get("typeface")
            if e.find(A + "buSzPct") is not None:
                d["buSz"] = int(e.find(A + "buSzPct").get("val")) / 100000
            if e.find(A + "buClr") is not None:
                d["buClr"] = e.find(A + "buClr")
        d["lvl"] = lvl
        d["chain"] = chain
        return d

    def run_props(self, pp, rpr):
        """ランの書式（受け継ぎを解いたもの）。"""
        d = dict(sz=18.0, b=False, i=False, u=False, strike=False, baseline=0.0, spc=0.0, cap=None, kern=None,
                 latin="+mn-lt", ea="+mn-ea", sym=None, lang=None, alt=None, color=None)
        for e in [c.find(A + "defRPr") for c in pp["chain"]] + [rpr]:
            if e is None:
                continue
            if e.get("sz") is not None:
                d["sz"] = int(e.get("sz")) / 100
            for k in ("b", "i"):
                if e.get(k) is not None:
                    d[k] = e.get(k) in ("1", "true")
            if e.get("u") is not None:
                d["u"] = e.get("u") != "none"
            if e.get("strike") is not None:
                d["strike"] = e.get("strike") != "noStrike"
            if e.get("baseline") is not None:
                d["baseline"] = int(e.get("baseline")) / 100000
            if e.get("spc") is not None:
                d["spc"] = int(e.get("spc")) / 100
            if e.get("kern") is not None:
                d["kern"] = int(e.get("kern")) / 100   # この大きさ（pt）以上で字の組を詰める
            if e.get("cap") is not None:
                d["cap"] = e.get("cap")
            if e.get("lang") is not None:
                d["lang"] = e.get("lang")
            if e.get("altLang") is not None:
                d["alt"] = e.get("altLang")
            for t in ("latin", "ea", "sym"):
                f = e.find(A + t)
                if f is not None and f.get("typeface") is not None:
                    d[t] = f.get("typeface")
            for t in ("solidFill",):
                f = e.find(A + t)
                if f is not None:
                    d["color"] = f
            if e.find(A + "noFill") is not None:
                d["color"] = "none"
        return d

    def default_lang(self):
        ds = self.deck.default_style
        if ds is not None:
            e = ds.find(f"{A}defPPr/{A}defRPr")
            if e is not None:
                return e.get("lang")
        return None

    # 書体の名前（+mn-lt などを解く）
    def typeface(self, slot, rp):
        tf = rp[slot]
        fonts = self.th["fonts"]
        if tf and tf.startswith("+"):
            kind = "major" if tf[1:3] == "mj" else "minor"
            part = {"lt": "latin", "ea": "ea", "cs": "cs"}.get(tf[4:], "latin")
            f = fonts[kind]
            if part == "ea":
                lang = rp["lang"] or self.default_lang() or ""
                script = {"ja": "Jpan", "ko": "Hang", "zh-CN": "Hans", "zh-TW": "Hant", "zh-HK": "Hant"}
                sc = script.get(lang) or script.get(lang[:2])
                if sc and f.get(sc):
                    return f[sc]
                return f.get("ea") or ""
            return f.get(part, "")
        return tf or ""


def _face_for(name, bold, italic, kind):
    f = find_face(name, bold, italic) if name else None
    if f is None:
        f = fallback_face("serif" if (name and SERIF_HINT.search(name) and kind != "ea") else kind, bold, italic)
    return f


class RunFonts:
    """ランの書体の組（和文・欧文）。字ごとに選ぶ。"""

    def __init__(self, ctx, rp):
        self.rp = rp
        lat = ctx.typeface("latin", rp)
        ea = ctx.typeface("ea", rp)
        if not ea:
            # テーマに和文の書体が無いとき（Calibri だけのテーマなど）：言語の書体、無ければ OS の和文の書体
            ea = ""
        self.latin = _face_for(lat, rp["b"], rp["i"], "latin")
        if ea:
            self.ea = _face_for(ea, rp["b"], rp["i"], "ea")
        elif self.latin is not None and self.latin.has("あ"):
            self.ea = self.latin   # 和文の書体が決まらないとき、欧文の書体に和文の字があればそれで描く（Yu Gothic を欧文に指定したデッキ）
        else:
            self.ea = fallback_face("ea", rp["b"], rp["i"])
        # 和文の記号（● など）を和文の書体で描くのは、ランの言語か第2の言語（altLang）が日本語・中国語・韓国語のとき
        self.ea_lang = any((x or "")[:2] in ("ja", "zh", "ko") for x in (rp["lang"] or ctx.default_lang(), rp["alt"]))

    def face(self, ch):
        ea = is_ea(ch) if (self.ea_lang or ord(ch) >= 0x2E80) else (ord(ch) >= 0x2E80 or 0xFF00 <= ord(ch) <= 0xFFEF)
        f = self.ea if ea else self.latin
        if f is None or not f.has(ch):
            # 和文の字が和文の書体に無ければ欧文の書体、欧文の字が欧文の書体に無ければ代わりの記号の書体（Segoe UI Symbol・
            # Cambria Math）を先に探す（⇒ は MS PGothic にあるが、PowerPoint は Segoe UI Symbol の幅で描いていた）
            o = self.latin if ea else self.ea
            if ea and o is not None and o.has(ch):
                return o
            g = glyph_fallback(ch, self.rp["b"])
            if g is not None:
                return g
            if o is not None and o.has(ch):
                return o
        return f


# ---- 文字の配置 ------------------------------------------------------------------------------------------
# 行頭に来ない字・行末に来ない字（PowerPoint の既定の禁則に近いもの）
NO_START = set("、。，．,.・：；？！?!:;)）]］}｝〕〉》」』】〙〗〟’”｠»ゝゞーァィゥェォッャュョヮヵヶぁぃぅぇぉっゃゅょゎゕゖㇰㇱㇲㇳㇴㇵㇶㇷㇸㇹㇺㇻㇼㇽㇾㇿ々〻‐゠–〜～%％‰℃°′″")
HANG = set("、。，．")   # ぶら下げる字（hangingPunct="1" のとき）
NO_END = set("([｛〔〈《「『【〘〖〝‘“｟«（［{")


class Ch:
    __slots__ = ("c", "w", "face", "size", "rp", "run", "x")

    def __init__(self, c, w, face, size, rp, run):
        self.c, self.w, self.face, self.size, self.rp, self.run = c, w, face, size, rp, run
        self.x = 0.0


def _break_ok(a: Ch, b: Ch) -> bool:
    """a と b の間で行を割ってよいか。"""
    ca, cb = a.c, b.c
    if ca == "\t":
        return True
    if cb in " \t":
        return False        # 空白は前の行の末に付ける
    if ca == " ":
        return True
    if (cb in NO_START or ca in NO_END) and (a.run.ea_lang or b.run.ea_lang):
        return False   # 禁則は、言語が日本語などのランだけ（英語のランでは、PowerPoint は「）」も行頭に送った）
    if is_ea(ca) or is_ea(cb):
        return True
    if ca in "-–—" and cb.isalnum():
        return True    # ハイフン・ダッシュの後（PowerPoint は「Blonder–」で割った）
    return False


class Line:
    def __init__(self):
        self.chars = []
        self.width = 0.0       # 行末の空白を除いた幅
        self.height = 0.0
        self.top = 0.0
        self.x = 0.0
        self.maxsize = 0.0
        self.bullet = None     # [文字, Face, 大きさ, 幅, 色]
        self.bullet_rel = self.bullet_x = 0.0
        self.soft = False      # 折り返した行（段落の末・改行で終わる行でない）
        self.trail = 0.0       # 折り返した行の末の空白の幅
        self.abs_x = 0.0
        self.end_extra = 0.0


M = "{http://schemas.openxmlformats.org/officeDocument/2006/math}"
A14_M = "{http://schemas.microsoft.com/office/drawing/2010/main}m"
MC = "{http://schemas.openxmlformats.org/markup-compatibility/2006}"


def _runs_of_para(p):
    """段落の中の (要素, 上付き・下付きか) を順に。数式（a14:m の中の m:r）も1つずつ出す。
    数式の組み（分数・根号・アクセント）は組まず、字を横に並べるだけ（おおよそ。m:sub・m:sup の中は上付きの大きさ）。"""
    for el in p:
        if el.tag == A14_M:
            for r in el.iter(M + "r"):
                small = False
                anc = r.getparent()
                while anc is not None and anc is not el:
                    if anc.tag in (M + "sub", M + "sup", M + "deg"):
                        small = True
                        break
                    anc = anc.getparent()
                yield r, small
        else:
            yield el, False


def para_text(p, slide_no=None):
    """段落の文字（PowerPoint の TextRange.Text に近い形。数式の字も入れる）。"""
    out = []
    for el, _ in _runs_of_para(p):
        if el.tag == M + "r":
            out.append("".join(x.text or "" for x in el.iter(M + "t")))
        elif el.tag == A + "fld" and slide_no is not None and (el.get("type") or "").startswith("slidenum"):
            out.append(str(slide_no))
        elif el.tag in (A + "r", A + "fld"):
            out.append(el.findtext(A + "t") or "")
        elif el.tag == A + "br":
            out.append("\v")
    return "".join(out)


def slide_shapes(slide):
    """スライドの一番上の図形を、XML の順に（python-pptx が飛ばす mc:AlternateContent（数式の入った文字の枠など）も、
    Choice の側の図形を入れる。PowerPoint も Choice の側を図形として数える）。"""
    from pptx.shapes.shapetree import SlideShapeFactory
    tree = slide.shapes._spTree
    out = []
    for el in tree.iterchildren():
        if el.tag == MC + "AlternateContent":
            ch = el.find(MC + "Choice")
            kid = next((k for k in (ch if ch is not None else []) if k.tag.startswith(P)), None)
            if kid is None:
                fb = el.find(MC + "Fallback")
                kid = next((k for k in (fb if fb is not None else []) if k.tag.startswith(P)), None)
            if kid is not None:
                out.append(SlideShapeFactory(kid, slide.shapes))
        elif el.tag in (P + "sp", P + "pic", P + "cxnSp", P + "grpSp", P + "graphicFrame", P + "contentPart"):
            out.append(SlideShapeFactory(el, slide.shapes))
    return out


def _chars_of_para(ctx, p, pp, slide_no, scale, prev_rpr=None):
    """段落の字を Ch の並びに。a:br は '\\v'。"""
    out = []
    end_rp = None
    for el, small in _runs_of_para(p):
        tag = el.tag[len(A):] if el.tag.startswith(A) else ("m" if el.tag == M + "r" else "")
        if tag in ("r", "fld", "m"):
            rpr = el.find(A + "rPr")
            rp = ctx.run_props(pp, rpr)
            if small:   # 数式の上付き・下付き
                rp = dict(rp, baseline=1)
            t = el.findtext(A + "t") if tag != "m" else "".join(x.text or "" for x in el.iter(M + "t"))
            t = t or ""
            if tag == "fld" and (el.get("type") or "").startswith("slidenum"):
                t = str(slide_no)
            if rp["cap"] == "all":
                t = t.upper()
            fonts = RunFonts(ctx, rp)
            size = rp["sz"] * scale
            eff = size * (SUPER_SCALE if rp["baseline"] else 1.0)
            kern_on = KERN and rp["kern"] is not None and rp["kern"] > 0 and eff >= rp["kern"]
            for c in t:
                if c in "\r\n":
                    c = " "
                f = fonts.face(c)
                w = (f.advance(c) if f else (1.0 if is_ea(c) else 0.55)) * eff + rp["spc"]
                if f is not None and f.synth_bold and c != " " and eff >= SYNTH_BOLD_MIN:
                    w += SYNTH_BOLD_PT
                if kern_on and out and out[-1].face is f and out[-1].rp is rp and f is not None:
                    out[-1].w += f.kern(out[-1].c, c) * eff   # 詰めは前の字の幅に入れる
                out.append(Ch(c, w, f, size, rp, fonts))
            end_rp = (rp, fonts)
        elif tag == "br":
            rpr = el.find(A + "rPr")
            rp = ctx.run_props(pp, rpr)
            out.append(Ch("\v", 0.0, None, rp["sz"] * scale, rp, RunFonts(ctx, rp)))
    epr = p.find(A + "endParaRPr")
    if not out or end_rp is None:
        if epr is None and prev_rpr is not None:
            # 空の段落に endParaRPr が無いとき、PowerPoint は前の段落の最後のランの書式で行の高さを取る（実測）
            rp = ctx.run_props(pp, prev_rpr)
        else:
            rp = ctx.run_props(pp, epr)
        end_rp = (rp, RunFonts(ctx, rp))
    return out, end_rp


def _space_w(fonts, size):
    f = fonts.latin or fonts.ea
    return (f.advance(" ") if f else 0.27) * size


def layout_text(ctx, box, slide_no=1):
    """図形の文字を配置する。戻り値 dict(lines=[Line], paras, bound=(l, t, w, h) or None, nlines)。
    box = (left, top, width, height) pt。"""
    tb = ctx.txbody
    if tb is None:
        return None
    left, top, width, height = box
    ins = [int(ctx.body_attr(k, str(d))) / EMU_PT for k, d in zip(("lIns", "tIns", "rIns", "bIns"), DEFAULT_INS)]
    wrap = ctx.body_attr("wrap", "square") != "none"
    anchor = ctx.body_attr("anchor", "t")
    vert = ctx.body_attr("vert", "horz")
    # 自動調整で縮めた文字（normAutofit の fontScale・lnSpcReduction。図形の bodyPr に書かれた値を使う）
    bp = tb.find(A + "bodyPr")
    na = bp.find(A + "normAutofit") if bp is not None else None
    scale = int(na.get("fontScale", "100000")) / 100000 if na is not None else 1.0
    lnred = int(na.get("lnSpcReduction", "0")) / 100000 if na is not None else 0.0
    if vert in ("vert", "vert270", "eaVert", "wordArtVert", "mongolianVert", "wordArtVertRtl"):
        # 縦書きは、幅と高さを入れ替えて横書きとして並べる（範囲はおおよそ）
        width, height = height, width
    # 図形の形の中の文字の場所（角丸・楕円・矢印などは、外形より内側。プリセットの図形の定義の text rect）
    tr = text_rect(ctx.prst, width, height, ctx.geom) if ctx.prst else (0.0, 0.0, 0.0, 0.0)
    left, top = left + tr[0], top + tr[1]
    width, height = width - tr[0] - tr[2], height - tr[1] - tr[3]
    inner_w = width - ins[0] - ins[2]
    lines_all = []
    paras = tb.findall(A + "p")
    y = 0.0
    first_line_of_box = True
    auto_counters = {}
    prev_rpr = None
    for pi, p in enumerate(paras):
        pp = ctx.para_props(p)
        chars, (end_rp, end_fonts) = _chars_of_para(ctx, p, pp, slide_no, scale, prev_rpr)
        runs_here = [e for e in p if e.tag in (A + "r", A + "fld")]
        if runs_here:
            prev_rpr = runs_here[-1].find(A + "rPr")
        marL, indent = pp["marL"] / EMU_PT, pp["indent"] / EMU_PT
        # 箇条書きの記号
        bullet = None
        visible = [c for c in chars if c.c != "\v"]
        if pp["bullet"] is not None and visible:
            rp0 = chars[0].rp
            bsz = (rp0["sz"] * scale) * (pp["buSz"] or 1.0)
            if isinstance(pp["bullet"], tuple):
                key = (pp["lvl"], pp["bullet"][1])
                n = auto_counters.get(key, pp["bullet"][2] - 1) + 1
                auto_counters[key] = n
                btxt = _autonum(pp["bullet"][1], n)
            else:
                btxt = pp["bullet"]
            bf = find_face(pp["buFont"], False, False) if pp["buFont"] and not pp["buFont"].startswith("+") else None
            if bf is None or not all(bf.has(c) for c in btxt):
                bf = chars[0].run.face(btxt[0])
            bw = sum((bf.advance(c) if bf else 0.6) * bsz for c in btxt)
            bullet = [btxt, bf, bsz, bw, pp["buClr"]]
        elif pp["bullet"] is None:
            auto_counters.clear()
        # 行を割る
        plines = []
        cur = Line()
        avail_first = inner_w - marL - indent if not bullet else inner_w - marL
        avail = inner_w - marL
        first_x = marL + indent if not bullet else max(marL, marL + indent + bullet[3])
        if bullet:   # 記号は marL + indent に置き、文字は marL から（記号が入らなければ記号の後ろから）
            avail_first = inner_w - first_x
        x0 = first_x
        lim = avail_first
        hang = pp["hang"]

        def finish(line, x_start, soft=False):
            line.soft = soft
            # 折り返した行の末の空白は幅に数えない（段落の末・改行の前の空白は、PowerPoint の範囲に入る）
            k = len(line.chars)
            while k > 0 and (line.chars[k - 1].c == "\v" or (soft and line.chars[k - 1].c in " \t")):
                k -= 1
            line.width = sum(c.w for c in line.chars[:k]) if k else 0.0
            # 折り返した行の末の空白は、揃えと「入るか」には数えないが、範囲（BoundWidth）には入る（PowerPoint の実測）
            line.trail = sum(c.w for c in line.chars[k:] if c.c != "\v") if soft else 0.0
            line.x = x_start
            plines.append(line)

        i = 0
        n = len(chars)
        pos = 0.0
        while i < n:
            c = chars[i]
            if c.c == "\v":
                cur.chars.append(c)
                finish(cur, x0)
                cur = Line()
                x0, lim, pos = marL, avail, 0.0
                i += 1
                continue
            if c.c == "\t":
                tab = pp["defTab"] / EMU_PT or 72.0
                absx = x0 + pos
                nxt = (math.floor(absx / tab + 1e-6) + 1) * tab
                c.w = max(0.0, nxt - absx)
            if not wrap:
                cur.chars.append(c)
                pos += c.w
                i += 1
                continue
            # 次に割れる所までのまとまり（単語）
            j = i + 1
            while j < n and chars[j].c != "\v" and not _break_ok(chars[j - 1], chars[j]):
                j += 1
            unit = chars[i:j]
            uw = sum(u.w for u in unit)
            uw_vis = sum(u.w for u in unit[:len(unit) - _trail_spaces(unit)])
            if hang:   # ぶら下げ：行末の「、」「。」は右の端の外に出てよい
                k = len(unit) - _trail_spaces(unit)
                while k > 0 and unit[k - 1].c in HANG and unit[k - 1].run.ea_lang:   # 英語のランではぶら下げない（行頭に「、」が来た）
                    uw_vis -= unit[k - 1].w
                    k -= 1
            if cur.chars and pos + uw_vis > lim + 0.01:
                finish(cur, x0, soft=True)
                cur = Line()
                x0, lim, pos = marL, avail, 0.0
                continue
            if not cur.chars and uw_vis > lim + 0.01 and len(unit) > 1:
                # 1語が行より長い：字の途中で割る
                k = 0
                acc = 0.0
                while k < len(unit) and (acc + unit[k].w <= lim + 0.01 or k == 0):
                    acc += unit[k].w
                    k += 1
                cur.chars.extend(unit[:k])
                finish(cur, x0, soft=True)
                cur = Line()
                x0, lim, pos = marL, avail, 0.0
                i += k
                continue
            cur.chars.extend(unit)
            pos += uw
            i = j
        finish(cur, x0)
        if bullet:
            plines[0].bullet = bullet
            plines[0].bullet_rel = marL + indent
        # 行の高さ
        for li, ln in enumerate(plines):
            sizes = [c.size for c in ln.chars if c.c not in "\v"] or [end_rp["sz"] * scale]
            if not [c for c in ln.chars if c.c not in "\v"] and ln.chars:
                sizes = [ln.chars[0].size]
            ms = max(sizes)
            ln.maxsize = ms
            ls = pp["lnSpc"]
            if ls is None:
                h = ms * LINE_FACTOR * (1 - lnred)
            elif ls[0] == "pct":
                h = ms * LINE_FACTOR * max(0.0, ls[1] - lnred)
            else:
                h = ls[1]
            ln.height = h
            last = ln.chars[-1] if ln.chars else None
            fonts = last.run if last is not None else end_fonts
            esz = last.size if last is not None else end_rp["sz"] * scale
            # 段落の末・改行の行は、範囲に段落記号の幅（空白1つ分）が入る。折り返した行には入らない
            ln.end_extra = 0.0 if ln.soft else _space_w(fonts, esz)
        # 段落の前後の間隔
        bef = _spacing(pp["spcBef"], plines[0].maxsize if plines else 18)
        aft = _spacing(pp["spcAft"], plines[-1].maxsize if plines else 18)
        if not first_line_of_box:
            y += bef
        for ln in plines:
            ln.top = y
            y += ln.height
            ln.algn = pp["algn"]
            ln.marL = marL
            ln.para = pi
        if pi < len(paras) - 1:
            y += aft
        first_line_of_box = False
        lines_all.extend(plines)
    total_h = y
    inner_h = height - ins[1] - ins[3]
    if anchor == "ctr":
        y0 = top + ins[1] + (inner_h - total_h) / 2
    elif anchor == "b":
        y0 = top + ins[1] + inner_h - total_h
    else:
        y0 = top + ins[1]
    x_in = left + ins[0]
    boxes = []
    for ln in lines_all:
        ln.top += y0
        # 中央・右揃えは、行末の空白の分を除いた幅で揃える（範囲は行末の空白の分だけ右へ出る。PowerPoint の実測）
        if ln.algn in ("ctr", "dist"):
            lx = x_in + ln.x + (inner_w - ln.x - ln.width) / 2
        elif ln.algn == "r":
            lx = x_in + inner_w - ln.width
        else:
            lx = x_in + ln.x
        ln.abs_x = lx
        bl = lx
        if ln.bullet:   # 箇条書きの記号の位置（marL + indent）。範囲は記号から
            ln.bullet_x = x_in + ln.bullet_rel
            bl = min(bl, ln.bullet_x)
        boxes.append((bl, ln.top, lx + ln.width + ln.end_extra + ln.trail, ln.top + ln.height))
    has_text = any(c.c.strip() for ln in lines_all for c in ln.chars)
    bound = None
    if boxes and has_text:
        l = min(b[0] for b in boxes)
        t = min(b[1] for b in boxes)
        r = max(b[2] for b in boxes)
        bt = max(b[3] for b in boxes)
        bound = (l, t, r - l, bt - t)
    return dict(lines=lines_all, bound=bound, nlines=len(lines_all), ins=ins, wrap=wrap, total_h=total_h)


def text_rect(prst, w, h, geom):
    """プリセットの図形の文字の場所の、外形からの内側への幅 (左, 上, 右, 下) pt（ECMA-376 の presetShapeDefinitions の rect）。"""
    ss = min(w, h)
    if prst in ("roundRect", "flowChartAlternateProcess"):
        r = ss * _adj(geom, "adj", 16667) / 100000 * 0.29289
        return (r, r, r, r)
    if prst in ("ellipse", "flowChartConnector"):
        k = (1 - math.sqrt(0.5)) / 2
        return (w * k, h * k, w * k, h * k)
    if prst == "rightArrow" or prst == "leftArrow":
        a1 = _adj(geom, "adj1", 50000)
        a2 = _adj(geom, "adj2", 50000)
        dy1 = h * a1 / 200000
        dx1 = ss * a2 / 100000
        y1 = h / 2 - dy1
        dx2 = y1 * dx1 / (h / 2) if h else 0
        if prst == "rightArrow":
            return (0.0, y1, dx1 - dx2, y1)
        return (dx1 - dx2, y1, 0.0, y1)
    if prst in ("downArrow", "upArrow"):
        a1 = _adj(geom, "adj1", 50000)
        a2 = _adj(geom, "adj2", 50000)
        dx1 = w * a1 / 200000
        dy1 = ss * a2 / 100000
        x1 = w / 2 - dx1
        dy2 = x1 * dy1 / (w / 2) if w else 0
        if prst == "downArrow":
            return (x1, 0.0, x1, dy1 - dy2)
        return (x1, dy1 - dy2, x1, 0.0)
    if prst in ("triangle", "flowChartExtract"):
        a = _adj(geom, "adj", 50000)
        x1 = w * a / 200000
        return (x1, h / 2, w - (x1 + w / 2), 0.0)
    if prst in ("diamond", "flowChartDecision"):
        return (w / 4, h / 4, w / 4, h / 4)
    if prst in ("homePlate", "pentagon"):
        dx1 = ss * _adj(geom, "adj", 50000) / 100000
        return (0.0, 0.0, dx1 / 2, 0.0)
    if prst == "chevron":
        x1 = ss * _adj(geom, "adj", 50000) / 100000
        return (x1, 0.0, x1, 0.0)
    if prst == "hexagon":
        x1 = ss * _adj(geom, "adj", 25000) / 100000
        return (x1 / 2, h * 0.08, x1 / 2, h * 0.08)
    if prst == "flowChartTerminator":
        return (w * 1018 / 21600, h * 3163 / 21600, w * 1018 / 21600, h * 3163 / 21600)
    return (0.0, 0.0, 0.0, 0.0)


def _trail_spaces(unit):
    k = 0
    for u in reversed(unit):
        if u.c in " \t":
            k += 1
        else:
            break
    return k


def _spacing(sp, size):
    if sp is None:
        return 0.0
    if sp[0] == "pct":
        return sp[1] * size * LINE_FACTOR
    return sp[1]


def _autonum(kind, n):
    if kind.startswith("alphaLc"):
        s = chr(ord("a") + (n - 1) % 26)
    elif kind.startswith("alphaUc"):
        s = chr(ord("A") + (n - 1) % 26)
    elif kind.startswith("romanLc") or kind.startswith("romanUc"):
        vals = [(10, "x"), (9, "ix"), (5, "v"), (4, "iv"), (1, "i")]
        s, m = "", n
        for v, r in vals:
            while m >= v:
                s += r
                m -= v
        s = s.upper() if kind.startswith("romanUc") else s
    elif kind.startswith("circleNum"):
        s = chr(0x2460 + n - 1) if n <= 20 else str(n)
        return s
    else:
        s = str(n)
    if kind.endswith("ParenBoth"):
        return f"({s})"
    if kind.endswith("ParenR"):
        return f"{s})"
    if kind.endswith("Period"):
        return f"{s}."
    return s


# ---- 図形の一覧（shapes.json） ------------------------------------------------------------------------------
def shape_rows(deck, slide, idx):
    """render_check.ps1 と同じ形の行（スライドの一番上の図形ごと）。"""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import render_check_lo
    shapes = slide_shapes(slide)
    rows = render_check_lo.shape_info(slide, idx, shapes)
    master = slide.slide_layout.slide_master
    for sh, row in zip(shapes, rows):
        if getattr(sh, "has_text_frame", False) and sh.text_frame._txBody.find(".//" + A14_M) is not None:
            paras = sh.text_frame._txBody.findall(A + "p")   # 数式の字も文字に入れる（python-pptx の text は数式を落とす）
            t = "\r".join(para_text(p_, idx) for p_ in paras)
            row["text"], row["paras"] = (t, len(paras)) if t.strip() else ("", 0)
        if not row["text"]:
            continue
        try:
            ctx = TextCtx(deck, sh, master, style_font_color=None)
            lay = layout_text(ctx, (row["left"], row["top"], row["width"], row["height"]), idx)
        except Exception as e:   # 1つの図形で落ちても、ほかは出す
            print(f"注意: スライド {idx} の「{sh.name}」の文字を配置できなかった（{type(e).__name__}: {e}）", file=sys.stderr)
            continue
        if not lay or not lay["bound"]:
            continue
        l, t, w, h = lay["bound"]
        row.update(tl=l, tt=t, tw=w, th=h, lines=lay["nlines"])
        first = next((c for ln in lay["lines"] for c in ln.chars if c.c.strip()), None)
        if first is not None:
            row["size"] = round(first.rp["sz"], 2)
    return rows


# ---- 描画 ------------------------------------------------------------------------------------------------
class Painter:
    """1枚の画像を描く（2倍の大きさで描いてから縮める）。"""
    SS = 2

    def __init__(self, deck, width_px):
        from PIL import Image, ImageDraw
        self.deck = deck
        self.k = width_px / deck.W * self.SS
        self.size = (round(deck.W * self.k), round(deck.H * self.k))
        self.width_px = width_px
        self.Image, self.ImageDraw = Image, ImageDraw
        self.img = Image.new("RGB", self.size, (255, 255, 255))
        self.dr = ImageDraw.Draw(self.img, "RGBA")
        self._pil_fonts = {}

    def px(self, v):
        return v * self.k

    def result(self):
        w = self.width_px
        h = round(self.deck.H * w / self.deck.W)
        return self.img.resize((w, h), self.Image.LANCZOS)

    def pil_font(self, face, px):
        from PIL import ImageFont
        key = (face.path, face.index, max(1, round(px)))
        f = self._pil_fonts.get(key)
        if f is None:
            try:
                f = ImageFont.truetype(face.path, key[2], index=face.index, layout_engine=ImageFont.Layout.BASIC)
            except OSError:
                f = ImageFont.load_default()
            self._pil_fonts[key] = f
        return f


def _rgba(c):
    if c is None:
        return None
    r, g, b, a = c
    return (r, g, b, round(255 * a))


def _xfrm(el):
    """要素の a:xfrm → (x, y, w, h, rot, flipH, flipV) pt。無ければ None。"""
    x = el.find(f"{P}spPr/{A}xfrm")
    if x is None:
        x = el.find(f"{P}grpSpPr/{A}xfrm")
    if x is None:
        x = el.find(f"{P}xfrm")
    if x is None:
        return None
    off, ext = x.find(A + "off"), x.find(A + "ext")
    if off is None or ext is None:
        return None
    return (int(off.get("x")) / EMU_PT, int(off.get("y")) / EMU_PT, int(ext.get("cx")) / EMU_PT, int(ext.get("cy")) / EMU_PT,
            int(x.get("rot", "0")) / 60000, x.get("flipH") == "1", x.get("flipV") == "1")


def _adj(geom, name="adj", default=50000):
    if geom is None:
        return default
    for gd in geom.findall(f"{A}avLst/{A}gd"):
        if gd.get("name") == name:
            m = re.search(r"val\s+(-?\d+)", gd.get("fmla", ""))
            if m:
                return int(m.group(1))
    return default


def preset_polygon(prst, w, h, geom):
    """プリセットの図形の外形（図形の中の座標の点の並び）。楕円は None（別に描く）。"""
    ss = min(w, h)
    if prst in ("rect", "flowChartProcess", "textBox", None, ""):
        return [(0, 0), (w, 0), (w, h), (0, h)]
    if prst in ("triangle", "flowChartExtract"):
        a = _adj(geom, "adj", 50000) / 100000
        return [(w * a, 0), (w, h), (0, h)]
    if prst == "rtTriangle":
        return [(0, 0), (w, h), (0, h)]
    if prst in ("diamond", "flowChartDecision"):
        return [(w / 2, 0), (w, h / 2), (w / 2, h), (0, h / 2)]
    if prst == "parallelogram":
        a = _adj(geom, "adj", 25000) / 100000 * ss
        return [(a, 0), (w, 0), (w - a, h), (0, h)]
    if prst == "trapezoid":
        a = _adj(geom, "adj", 25000) / 100000 * ss
        return [(a, 0), (w - a, 0), (w, h), (0, h)]
    if prst in ("homePlate", "pentagon"):
        a = _adj(geom, "adj", 50000) / 100000 * ss
        return [(0, 0), (w - a, 0), (w, h / 2), (w - a, h), (0, h)]
    if prst == "chevron":
        a = _adj(geom, "adj", 50000) / 100000 * ss
        return [(0, 0), (w - a, 0), (w, h / 2), (w - a, h), (0, h), (a, h / 2)]
    if prst == "hexagon":
        a = _adj(geom, "adj", 25000) / 100000 * ss
        return [(a, 0), (w - a, 0), (w, h / 2), (w - a, h), (a, h), (0, h / 2)]
    if prst == "octagon":
        a = _adj(geom, "adj", 29289) / 100000 * ss
        return [(a, 0), (w - a, 0), (w, a), (w, h - a), (w - a, h), (a, h), (0, h - a), (0, a)]
    if prst in ("rightArrow", "leftArrow"):
        a1 = _adj(geom, "adj1", 50000) / 100000
        hl = min(_adj(geom, "adj2", 50000) / 100000 * ss, w)
        t0, t1 = h * (1 - a1) / 2, h * (1 + a1) / 2
        pts = [(0, t0), (w - hl, t0), (w - hl, 0), (w, h / 2), (w - hl, h), (w - hl, t1), (0, t1)]
        return pts if prst == "rightArrow" else [(w - x, y) for x, y in pts]
    if prst in ("downArrow", "upArrow"):
        a1 = _adj(geom, "adj1", 50000) / 100000
        hl = min(_adj(geom, "adj2", 50000) / 100000 * ss, h)
        t0, t1 = w * (1 - a1) / 2, w * (1 + a1) / 2
        pts = [(t0, 0), (t1, 0), (t1, h - hl), (w, h - hl), (w / 2, h), (0, h - hl), (t0, h - hl)]
        return pts if prst == "downArrow" else [(x, h - y) for x, y in pts]
    if prst == "leftRightArrow":
        a1 = _adj(geom, "adj1", 50000) / 100000
        hl = min(_adj(geom, "adj2", 50000) / 100000 * ss, w / 2)
        t0, t1 = h * (1 - a1) / 2, h * (1 + a1) / 2
        return [(0, h / 2), (hl, 0), (hl, t0), (w - hl, t0), (w - hl, 0), (w, h / 2), (w - hl, h), (w - hl, t1),
                (hl, t1), (hl, h)]
    if prst == "plus":
        a = _adj(geom, "adj", 25000) / 100000 * ss
        return [(a, 0), (w - a, 0), (w - a, a), (w, a), (w, h - a), (w - a, h - a), (w - a, h), (a, h), (a, h - a),
                (0, h - a), (0, a), (a, a)]
    if prst in ("star5", "star4", "star6"):
        n = int(prst[-1])
        pts = []
        for k in range(2 * n):
            r = 0.5 if k % 2 == 0 else 0.2
            ang = -math.pi / 2 + k * math.pi / n
            pts.append((w / 2 + r * w * math.cos(ang), h / 2 + r * h * math.sin(ang)))
        return pts
    if prst in ("wedgeRectCallout", "wedgeRoundRectCallout"):
        return [(0, 0), (w, 0), (w, h), (0, h)]
    return [(0, 0), (w, 0), (w, h), (0, h)]


def custom_paths(geom, w, h):
    """a:custGeom の線の並び（点の並びのリスト、閉じるか）。曲線は細かい直線で近似。"""
    out = []
    pl = geom.find(A + "pathLst")
    if pl is None:
        return out
    for path in pl.findall(A + "path"):
        pw = int(path.get("w", "0")) or 1
        phh = int(path.get("h", "0")) or 1
        sx, sy = w / pw, h / phh
        pts, closed, cur = [], False, (0, 0)
        for c in path:
            tag = c.tag[len(A):]
            ps = [(int(pt.get("x", "0")) * sx, int(pt.get("y", "0")) * sy) for pt in c.findall(A + "pt")]
            if tag == "moveTo" and ps:
                if len(pts) > 1:
                    out.append((pts, closed))
                pts, closed = [ps[0]], False
                cur = ps[0]
            elif tag == "lnTo" and ps:
                pts.append(ps[0])
                cur = ps[0]
            elif tag == "cubicBezTo" and len(ps) == 3:
                p0 = cur
                for k in range(1, 13):
                    t = k / 12
                    x = (1 - t) ** 3 * p0[0] + 3 * (1 - t) ** 2 * t * ps[0][0] + 3 * (1 - t) * t * t * ps[1][0] + t ** 3 * ps[2][0]
                    y = (1 - t) ** 3 * p0[1] + 3 * (1 - t) ** 2 * t * ps[0][1] + 3 * (1 - t) * t * t * ps[1][1] + t ** 3 * ps[2][1]
                    pts.append((x, y))
                cur = ps[2]
            elif tag == "quadBezTo" and len(ps) == 2:
                p0 = cur
                for k in range(1, 9):
                    t = k / 8
                    x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * ps[0][0] + t * t * ps[1][0]
                    y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * ps[0][1] + t * t * ps[1][1]
                    pts.append((x, y))
                cur = ps[1]
            elif tag == "close":
                closed = True
        if len(pts) > 1:
            out.append((pts, closed))
    return out


class SlideRenderer:
    def __init__(self, deck, slide, idx, width_px):
        self.deck, self.slide, self.idx = deck, slide, idx
        self.layout = slide.slide_layout
        self.master = self.layout.slide_master
        self.th = deck.theme(self.master)
        self.colors = self.th["colors"]
        self.pt = Painter(deck, width_px)

    # 背景
    def background(self):
        for owner in (self.slide, self.layout, self.master):
            bg = owner._element.find(f"{P}cSld/{P}bg")
            if bg is None:
                continue
            bp = bg.find(P + "bgPr")
            if bp is not None:
                self._fill_rect(bp, (0, 0, self.deck.W, self.deck.H), owner)
                return
            br = bg.find(P + "bgRef")
            if br is not None:
                c = self.colors.of(br)
                if c:
                    self.pt.dr.rectangle([0, 0, *self.pt.size], fill=_rgba(c))
                return

    def _fill_rect(self, holder, rect, owner):
        f = holder.find(A + "solidFill")
        x, y, w, h = rect
        box = [self.pt.px(x), self.pt.px(y), self.pt.px(x + w), self.pt.px(y + h)]
        if f is not None:
            self.pt.dr.rectangle(box, fill=_rgba(self.colors.of(f)))
            return
        g = holder.find(A + "gradFill")
        if g is not None:
            stops = g.findall(f"{A}gsLst/{A}gs")
            if stops:
                c = self.colors.of(stops[0])
                self.pt.dr.rectangle(box, fill=_rgba(c))
            return
        b = holder.find(A + "blipFill")
        if b is not None:
            im = self._blip_image(b, owner)
            if im is not None:
                self._paste(im, rect, 0)

    def _blip_image(self, blipfill, owner):
        from PIL import Image
        blip = blipfill.find(A + "blip")
        if blip is None:
            return None
        rid = blip.get(R + "embed")
        if not rid:
            return None
        try:
            part = owner.part.related_part(rid)
            im = Image.open(io.BytesIO(part.blob))
            im.load()
        except Exception:
            return None
        im = im.convert("RGBA")
        src = blipfill.find(A + "srcRect")
        if src is not None:
            W, H = im.size
            l, t = int(src.get("l", "0")) / 100000, int(src.get("t", "0")) / 100000
            r, b = int(src.get("r", "0")) / 100000, int(src.get("b", "0")) / 100000
            box = (round(W * l), round(H * t), round(W * (1 - r)), round(H * (1 - b)))
            if box[2] > box[0] and box[3] > box[1]:
                im = im.crop(box)
        am = blip.find(A + "alphaModFix")
        if am is not None:
            a = int(am.get("amt", "100000")) / 100000
            im.putalpha(im.getchannel("A").point(lambda v: round(v * a)))
        return im

    def _paste(self, im, rect, rot, flipH=False, flipV=False):
        from PIL import Image
        x, y, w, h = rect
        W, H = max(1, round(self.pt.px(w))), max(1, round(self.pt.px(h)))
        im = im.resize((W, H), Image.LANCZOS)
        if flipH:
            im = im.transpose(Image.FLIP_LEFT_RIGHT)
        if flipV:
            im = im.transpose(Image.FLIP_TOP_BOTTOM)
        X, Y = self.pt.px(x), self.pt.px(y)
        if rot:
            im = im.rotate(-rot, expand=True, resample=Image.BICUBIC)
            X += (W - im.size[0]) / 2
            Y += (H - im.size[1]) / 2
        self.pt.img.paste(im, (round(X), round(Y)), im)

    def run(self):
        self.background()
        show_master = self.slide._element.get("showMasterSp") != "0" and self.layout._element.get("showMasterSp") != "0"
        if show_master:
            self.draw_tree(self.master._element.find(f"{P}cSld/{P}spTree"), self.master, None, deco=True)
        if self.slide._element.get("showMasterSp") != "0":
            self.draw_tree(self.layout._element.find(f"{P}cSld/{P}spTree"), self.layout, None, deco=True)
        self.draw_tree(self.slide._element.find(f"{P}cSld/{P}spTree"), self.slide, None, deco=False)
        return self.pt.result()

    def draw_tree(self, tree, owner, tf, deco):
        """spTree・grpSp の子を順に描く。tf はグループの座標の変換 (ox, oy, sx, sy, cx, cy)。"""
        if tree is None:
            return
        # 要素 → python-pptx の図形（プレースホルダは、受け継いだ位置・大きさを読むため）
        shmap = {}
        if not deco:
            try:
                for s_ in owner.shapes:
                    shmap[id(s_._element)] = s_
            except Exception:
                pass
        for el in tree:
            tag = el.tag[len(P):] if el.tag.startswith(P) else ""
            if tag not in ("sp", "pic", "cxnSp", "grpSp", "graphicFrame"):
                if el.tag.endswith("}AlternateContent"):
                    fb = el.find("{http://schemas.openxmlformats.org/markup-compatibility/2006}Fallback")
                    if fb is not None:
                        self.draw_tree(fb, owner, tf, deco)
                continue
            if deco and el.find(f".//{P}nvPr/{P}ph") is not None:
                continue   # マスター・レイアウトのプレースホルダ（入力の枠）は描かない
            sh = shmap.get(id(el))
            try:
                if tag == "grpSp":
                    self.draw_group(el, owner, tf, deco)
                elif tag == "pic":
                    self.draw_pic(el, owner, tf)
                elif tag == "graphicFrame":
                    self.draw_frame(el, owner, tf, sh)
                else:
                    self.draw_sp(el, owner, tf, sh)
            except Exception as e:
                print(f"注意: スライド {self.idx} の図形を描けなかった（{type(e).__name__}: {e}）", file=sys.stderr)

    def _map(self, rect, tf):
        x, y, w, h = rect
        if tf is None:
            return rect
        ox, oy, sx, sy, cx, cy = tf
        return (ox + (x - cx) * sx, oy + (y - cy) * sy, w * sx, h * sy)

    def _geom_of(self, el, sh):
        xf = _xfrm(el)
        if xf is None and sh is not None:
            try:
                return ((sh.left or 0) / EMU_PT, (sh.top or 0) / EMU_PT, (sh.width or 0) / EMU_PT, (sh.height or 0) / EMU_PT,
                        (getattr(sh, "rotation", 0) or 0), False, False)
            except Exception:
                return None
        return xf

    def draw_group(self, el, owner, tf, deco):
        x = el.find(f"{P}grpSpPr/{A}xfrm")
        if x is None:
            self.draw_tree(el, owner, tf, deco)
            return
        off, ext, choff, chext = (x.find(A + n) for n in ("off", "ext", "chOff", "chExt"))
        gx, gy = int(off.get("x")) / EMU_PT, int(off.get("y")) / EMU_PT
        gw, gh = int(ext.get("cx")) / EMU_PT, int(ext.get("cy")) / EMU_PT
        cx, cy = (int(choff.get("x")) / EMU_PT, int(choff.get("y")) / EMU_PT) if choff is not None else (gx, gy)
        cw, ch = (int(chext.get("cx")) / EMU_PT, int(chext.get("cy")) / EMU_PT) if chext is not None else (gw, gh)
        sx = gw / cw if cw else 1.0
        sy = gh / ch if ch else 1.0
        if tf is not None:   # 入れ子のグループ
            ox, oy, psx, psy, pcx, pcy = tf
            gx, gy = ox + (gx - pcx) * psx, oy + (gy - pcy) * psy
            sx, sy = sx * psx, sy * psy
        self.draw_tree(el, owner, (gx, gy, sx, sy, cx, cy), deco)

    def draw_pic(self, el, owner, tf):
        xf = _xfrm(el)
        if xf is None:
            return
        x, y, w, h, rot, fh, fv = xf
        rect = self._map((x, y, w, h), tf)
        bf = el.find(P + "blipFill")
        im = self._blip_image(bf, owner) if bf is not None else None
        if im is None:
            self._placeholder_box(rect, "画像")
            return
        self._paste(im, rect, rot, fh, fv)
        ln = el.find(f"{P}spPr/{A}ln")
        if ln is not None:
            stroke = self._line_style(ln, None)
            if stroke:
                self._outline(preset_polygon("rect", rect[2], rect[3], None), rect, stroke, closed=True)

    def _placeholder_box(self, rect, label):
        x, y, w, h = rect
        box = [self.pt.px(x), self.pt.px(y), self.pt.px(x + w), self.pt.px(y + h)]
        self.pt.dr.rectangle(box, fill=(235, 235, 235, 255), outline=(160, 160, 160, 255), width=2)
        f = fallback_face("ea", False, False)
        if f:
            self.pt.dr.text(((box[0] + box[2]) / 2, (box[1] + box[3]) / 2), label, fill=(120, 120, 120, 255),
                            font=self.pt.pil_font(f, self.pt.px(12)), anchor="mm")

    # 塗りと線
    def _style_color(self, el, ref):
        st = el.find(P + "style")
        if st is None:
            return None, 0
        r = st.find(A + ref)
        if r is None:
            return None, 0
        idx = r.get("idx", "0")
        return self.colors.of(r), (int(idx) if idx.lstrip("-").isdigit() else 0)   # fontRef の idx は "minor" など

    def _fill(self, sppr, el):
        """図形の塗り → (r, g, b, a) か None。"""
        if sppr is not None:
            if sppr.find(A + "noFill") is not None:
                return None
            f = sppr.find(A + "solidFill")
            if f is not None:
                return self.colors.of(f)
            g = sppr.find(A + "gradFill")
            if g is not None:
                stops = g.findall(f"{A}gsLst/{A}gs")
                if stops:
                    cs = [self.colors.of(s) for s in stops]
                    cs = [c for c in cs if c]
                    if cs:
                        return tuple(round(sum(c[k] for c in cs) / len(cs)) if k < 3 else cs[0][3] for k in range(4))
                return None
            if sppr.find(A + "pattFill") is not None:
                fg = sppr.find(f"{A}pattFill/{A}fgClr")
                return self.colors.of(fg) if fg is not None else None
        c, idx = self._style_color(el, "fillRef")
        if c and idx > 0:
            return c
        return None

    def _line_style(self, ln, el):
        """線 → dict(color, width, dash, head, tail) か None。"""
        style_c, style_idx = self._style_color(el, "lnRef") if el is not None else (None, 0)
        if ln is None:
            if style_c and style_idx > 0:
                w = 0.75
                ls = self.th["line_styles"]
                if 0 < style_idx <= len(ls):
                    w = int(ls[style_idx - 1].get("w", "9525")) / EMU_PT
                return dict(color=style_c, width=w, dash=None, head=None, tail=None)
            return None
        if ln.find(A + "noFill") is not None:
            return None
        f = ln.find(A + "solidFill")
        c = self.colors.of(f) if f is not None else None
        if c is None:
            g = ln.find(A + "gradFill")
            if g is not None:
                st = g.find(f"{A}gsLst/{A}gs")
                c = self.colors.of(st) if st is not None else None
        if c is None:
            c = style_c
        if c is None:
            return None
        w = int(ln.get("w", "0")) / EMU_PT
        if not w:
            w = 0.75
            ls = self.th["line_styles"]
            if 0 < style_idx <= len(ls):
                w = int(ls[style_idx - 1].get("w", "9525")) / EMU_PT
        d = ln.find(A + "prstDash")
        dash = d.get("val") if d is not None and d.get("val") != "solid" else None
        head = ln.find(A + "headEnd")
        tail = ln.find(A + "tailEnd")
        return dict(color=c, width=w, dash=dash,
                    head=(head.get("type"), head.get("w", "med"), head.get("len", "med")) if head is not None and head.get("type", "none") != "none" else None,
                    tail=(tail.get("type"), tail.get("w", "med"), tail.get("len", "med")) if tail is not None and tail.get("type", "none") != "none" else None)

    def _abs_points(self, pts, rect, rot, fh=False, fv=False):
        x, y, w, h = rect
        out = []
        cx, cy = x + w / 2, y + h / 2
        ca, sa = math.cos(math.radians(rot)), math.sin(math.radians(rot))
        for px_, py_ in pts:
            if fh:
                px_ = w - px_
            if fv:
                py_ = h - py_
            X, Y = x + px_, y + py_
            if rot:
                dx, dy = X - cx, Y - cy
                X, Y = cx + dx * ca - dy * sa, cy + dx * sa + dy * ca
            out.append((self.pt.px(X), self.pt.px(Y)))
        return out

    def _poly_line(self, P_, stroke, closed):
        if not stroke or len(P_) < 2:
            return
        col = _rgba(stroke["color"])
        wpx = max(1, round(self.pt.px(stroke["width"])))
        seq = P_ + [P_[0]] if closed else P_
        if stroke["dash"]:
            dash_len = {"dot": 1, "sysDot": 1, "sysDash": 3, "dash": 4, "lgDash": 8, "dashDot": 4, "lgDashDot": 8,
                        "lgDashDotDot": 8, "sysDashDot": 3, "sysDashDotDot": 3}.get(stroke["dash"], 4) * wpx
            gap = (1 if stroke["dash"].startswith("sys") else 3) * wpx
            for a, b in zip(seq, seq[1:]):
                L = math.hypot(b[0] - a[0], b[1] - a[1])
                if L == 0:
                    continue
                t = 0.0
                while t < L:
                    t1 = min(L, t + dash_len)
                    self.pt.dr.line([(a[0] + (b[0] - a[0]) * t / L, a[1] + (b[1] - a[1]) * t / L),
                                     (a[0] + (b[0] - a[0]) * t1 / L, a[1] + (b[1] - a[1]) * t1 / L)], fill=col, width=wpx)
                    t = t1 + gap
        else:
            self.pt.dr.line(seq, fill=col, width=wpx, joint="curve")

    def _outline(self, pts, rect, stroke, closed, rot=0, fh=False, fv=False):
        self._poly_line(self._abs_points(pts, rect, rot, fh, fv), stroke, closed)

    def _arrow_head(self, tip, frm, end, stroke):
        typ, wsz, lsz = end
        lw = max(stroke["width"], 0.75)
        k = {"sm": 2.0, "med": 3.0, "lg": 5.0}
        W, L = self.pt.px(lw * k.get(wsz, 3.0)), self.pt.px(lw * k.get(lsz, 3.0))
        dx, dy = tip[0] - frm[0], tip[1] - frm[1]
        d = math.hypot(dx, dy) or 1
        ux, uy = dx / d, dy / d
        bx, by = tip[0] - ux * L, tip[1] - uy * L
        col = _rgba(stroke["color"])
        if typ == "oval":
            r = W / 2
            self.pt.dr.ellipse([tip[0] - r, tip[1] - r, tip[0] + r, tip[1] + r], fill=col)
            return
        pts = [tip, (bx - uy * W / 2, by + ux * W / 2), (bx + uy * W / 2, by - ux * W / 2)]
        if typ in ("arrow", "open"):
            self.pt.dr.line([pts[1], tip, pts[2]], fill=col, width=max(1, round(self.pt.px(stroke["width"]))))
        else:
            if typ == "stealth":
                pts = [tip, pts[1], (tip[0] - ux * L * 0.6, tip[1] - uy * L * 0.6), pts[2]]
            self.pt.dr.polygon(pts, fill=col)

    def draw_sp(self, el, owner, tf, sh):
        xf = self._geom_of(el, sh)
        if xf is None:
            return
        x, y, w, h, rot, fh, fv = xf
        rect = self._map((x, y, w, h), tf)
        sppr = el.find(P + "spPr")
        # プレースホルダは、受け継いだ spPr（塗り・線）も見る
        base_sppr = []
        if sh is not None and getattr(sh, "is_placeholder", False):
            for b in placeholder_chain(sh):
                bs = b._element.find(P + "spPr")
                if bs is not None:
                    base_sppr.append(bs)
        geom = sppr.find(A + "prstGeom") if sppr is not None else None
        cust = sppr.find(A + "custGeom") if sppr is not None else None
        prst = geom.get("prst") if geom is not None else ("rect" if cust is None else None)
        fill = self._fill(sppr, el)
        if fill is None and (sppr is None or (sppr.find(A + "noFill") is None and sppr.find(A + "solidFill") is None)):
            for bs in base_sppr:
                f2 = self._fill(bs, el)
                if f2:
                    fill = f2
                    break
        ln = sppr.find(A + "ln") if sppr is not None else None
        stroke = self._line_style(ln, el)
        is_line = prst in ("line", "straightConnector1", "bentConnector2", "bentConnector3", "curvedConnector3") or el.tag == P + "cxnSp"
        if is_line:
            if stroke is None and el.tag == P + "cxnSp":
                stroke = dict(color=(0, 0, 0, 1.0), width=0.75, dash=None, head=None, tail=None)
            if stroke:
                X0, Y0 = (rect[0] + rect[2], rect[1]) if fh else (rect[0], rect[1])
                X1, Y1 = (rect[0], rect[1] + rect[3]) if fh else (rect[0] + rect[2], rect[1] + rect[3])
                if fv:
                    Y0, Y1 = Y1, Y0
                a, b = (self.pt.px(X0), self.pt.px(Y0)), (self.pt.px(X1), self.pt.px(Y1))
                if prst in ("bentConnector3", "bentConnector2"):
                    mid = (b[0], a[1]) if prst == "bentConnector2" else None
                    seq = [a, mid, b] if mid else [a, ((a[0] + b[0]) / 2, a[1]), ((a[0] + b[0]) / 2, b[1]), b]
                else:
                    seq = [a, b]
                self._poly_line(seq, stroke, False)
                if stroke["tail"]:
                    self._arrow_head(seq[-1], seq[-2], stroke["tail"], stroke)
                if stroke["head"]:
                    self._arrow_head(seq[0], seq[1], stroke["head"], stroke)
        elif cust is not None:
            for pts, closed in custom_paths(cust, rect[2], rect[3]):
                P_ = self._abs_points(pts, rect, rot, fh, fv)
                if fill and closed and len(P_) > 2:
                    self.pt.dr.polygon(P_, fill=_rgba(fill))
                if stroke:
                    self._poly_line(P_, stroke, closed)
        elif prst in ("ellipse", "flowChartConnector", "donut", "arc", "pie", "chord", "blockArc"):
            if rot:
                pts = [(rect[2] / 2 + rect[2] / 2 * math.cos(t * math.pi / 36), rect[3] / 2 + rect[3] / 2 * math.sin(t * math.pi / 36)) for t in range(72)]
                P_ = self._abs_points(pts, rect, rot)
                if fill:
                    self.pt.dr.polygon(P_, fill=_rgba(fill))
                self._poly_line(P_, stroke, True)
            else:
                box = [self.pt.px(rect[0]), self.pt.px(rect[1]), self.pt.px(rect[0] + rect[2]), self.pt.px(rect[1] + rect[3])]
                if box[2] > box[0] and box[3] > box[1]:
                    self.pt.dr.ellipse(box, fill=_rgba(fill) if fill else None,
                                       outline=_rgba(stroke["color"]) if stroke else None,
                                       width=max(1, round(self.pt.px(stroke["width"]))) if stroke else 0)
        elif prst in ("roundRect", "flowChartAlternateProcess", "flowChartTerminator", "snipRoundRect", "round2SameRect", "round1Rect") and not rot:
            a = _adj(geom, "adj", 16667) / 100000 if prst != "flowChartTerminator" else 0.5
            r = self.pt.px(a * min(rect[2], rect[3]))
            box = [self.pt.px(rect[0]), self.pt.px(rect[1]), self.pt.px(rect[0] + rect[2]), self.pt.px(rect[1] + rect[3])]
            if box[2] > box[0] and box[3] > box[1]:
                self.pt.dr.rounded_rectangle(box, radius=r, fill=_rgba(fill) if fill else None,
                                             outline=_rgba(stroke["color"]) if stroke and not stroke["dash"] else None,
                                             width=max(1, round(self.pt.px(stroke["width"]))) if stroke else 0)
                if stroke and stroke["dash"]:
                    self._outline(preset_polygon("rect", rect[2], rect[3], None), rect, stroke, True)
        else:
            pts = preset_polygon(prst, rect[2], rect[3], geom)
            P_ = self._abs_points(pts, rect, rot, fh, fv)
            if fill and len(P_) > 2:
                self.pt.dr.polygon(P_, fill=_rgba(fill))
            if stroke:
                self._poly_line(P_, stroke, True)
        # 文字
        tb = el.find(P + "txBody")
        if tb is not None and sh is not None:
            fc, _ = self._style_color(el, "fontRef")
            ctx = TextCtx(self.deck, sh, self.master, style_font_color=fc)
            self.draw_text(ctx, rect, rot)
        elif tb is not None and (tb.findtext(f".//{A}t") or "").strip():
            # マスター・レイアウトの飾りの文字（プレースホルダでないもの）
            fc, _ = self._style_color(el, "fontRef")
            ctx = TextCtx(self.deck, _Bare(el), self.master, txbody=tb, style_font_color=fc)
            self.draw_text(ctx, rect, rot)

    def draw_text(self, ctx, rect, rot=0, slide_no=None):
        lay = layout_text(ctx, rect, slide_no or self.idx)
        if not lay:
            return
        dr = self.pt.dr
        for ln in lay["lines"]:
            x = ln.abs_x
            base = ln.top + ln.height * 0.8 if ln.height <= ln.maxsize * LINE_FACTOR * 1.05 else ln.top + ln.maxsize * 1.0
            if ln.bullet:
                btxt, bf, bsz, bw, bclr = ln.bullet
                col = self._text_color(ln.chars[0].rp, ctx) if ln.chars else (0, 0, 0, 255)
                if bclr is not None:
                    col = _rgba(self.colors.of(bclr))
                if bf and col:
                    dr.text((self.pt.px(ln.bullet_x), self.pt.px(base)), btxt, fill=col, font=self.pt.pil_font(bf, self.pt.px(bsz)), anchor="ls")
            for c in ln.chars:
                if c.c in "\v\t ":
                    c.x = x
                    x += c.w
                    continue
                col = self._text_color(c.rp, ctx)
                if col is None:
                    x += c.w
                    continue
                sz = c.size * (SUPER_SCALE if c.rp["baseline"] else 1.0)
                yb = base - c.rp["baseline"] * c.size
                if c.face is not None:
                    f = self.pt.pil_font(c.face, self.pt.px(sz))
                    sw = round(self.pt.px(sz) / 70) if c.face.synth_bold else 0   # 太字の字の無い書体は、縁取りで少し太く
                    dr.text((self.pt.px(x), self.pt.px(yb)), c.c, fill=col, font=f, anchor="ls", stroke_width=sw, stroke_fill=col if sw else None)
                if c.rp["u"]:
                    uy = self.pt.px(yb + sz * 0.12)
                    dr.line([(self.pt.px(x), uy), (self.pt.px(x + c.w), uy)], fill=col, width=max(1, round(self.pt.px(sz / 18))))
                if c.rp["strike"]:
                    sy_ = self.pt.px(yb - sz * 0.3)
                    dr.line([(self.pt.px(x), sy_), (self.pt.px(x + c.w), sy_)], fill=col, width=max(1, round(self.pt.px(sz / 18))))
                x += c.w

    def _text_color(self, rp, ctx):
        c = rp["color"]
        if c == "none":
            return None
        if c is not None:
            v = self.colors.of(c)
            if v:
                return _rgba(v)
        if ctx.style_font_color:
            return _rgba(ctx.style_font_color)
        return _rgba((*self.colors.scheme_rgb("tx1"), 1.0))

    def draw_frame(self, el, owner, tf, sh):
        xf = _xfrm(el)
        if xf is None:
            return
        x, y, w, h, rot, fh, fv = xf
        rect = self._map((x, y, w, h), tf)
        tbl = el.find(f".//{A}tbl")
        if tbl is None:
            uri = el.find(f".//{A}graphicData")
            kind = (uri.get("uri") if uri is not None else "") or ""
            self._placeholder_box(rect, "グラフ" if "chart" in kind else ("図表" if "diagram" in kind else "オブジェクト"))
            return
        grid = [int(g.get("w")) / EMU_PT for g in tbl.findall(f"{A}tblGrid/{A}gridCol")]
        rows = table_rows(self.deck, sh, self.master, tbl, grid)
        X0, Y = rect[0], rect[1]
        dr = self.pt.dr
        for tr, rh in rows:
            X = X0
            for ci, tc in enumerate(tr.findall(A + "tc")):
                if tc.get("hMerge") == "1" or tc.get("vMerge") == "1":
                    X += grid[ci] if ci < len(grid) else 0
                    continue
                span = int(tc.get("gridSpan", "1"))
                cw = sum(grid[ci:ci + span])
                tcpr = tc.find(A + "tcPr")
                fill = self._fill(tcpr, el) if tcpr is not None else None
                box = [self.pt.px(X), self.pt.px(Y), self.pt.px(X + cw), self.pt.px(Y + rh)]
                if fill:
                    dr.rectangle(box, fill=_rgba(fill))
                # 罫線（指定があればその色、無ければ薄い灰色）
                drawn = False
                if tcpr is not None:
                    for side, seg in (("lnL", [(box[0], box[1]), (box[0], box[3])]), ("lnR", [(box[2], box[1]), (box[2], box[3])]),
                                      ("lnT", [(box[0], box[1]), (box[2], box[1])]), ("lnB", [(box[0], box[3]), (box[2], box[3])])):
                        l_ = tcpr.find(A + side)
                        if l_ is not None:
                            stv = self._line_style(l_, None)
                            if stv:
                                self._poly_line(seg, stv, False)
                            drawn = True
                if not drawn:
                    dr.rectangle(box, outline=(191, 191, 191, 255), width=1)
                ctx = TextCtx(self.deck, sh, self.master, txbody=tc.find(A + "txBody"), table_cell=True)
                ctx.bodyprs = [_cell_bodypr(tcpr)]
                self.draw_text(ctx, (X, Y, cw, rh))
                X += grid[ci] if ci < len(grid) else cw
            Y += rh


class _Bare:
    """マスター・レイアウトの飾りの図形（python-pptx の図形にしないもの）を TextCtx に渡すための薄い入れ物。"""

    def __init__(self, el):
        self._element = el
        self.name = ""


def _cell_bodypr(tcpr):
    """表のセルの余白（tcPr の marL など）を bodyPr の形に。"""
    from lxml import etree
    bp = etree.Element(A + "bodyPr")
    m = {"marL": "lIns", "marR": "rIns", "marT": "tIns", "marB": "bIns"}
    if tcpr is not None:
        for k, v in m.items():
            if tcpr.get(k) is not None:
                bp.set(v, tcpr.get(k))
        if tcpr.get("anchor"):
            bp.set("anchor", tcpr.get("anchor"))
    return bp


def table_rows(deck, sh, master, tbl, grid):
    """表の行と、文字に合わせて広げた行の高さ（PowerPoint は文字が行の高さに入らなければ行を広げる）。"""
    out = []
    for tr in tbl.findall(A + "tr"):
        h = int(tr.get("h", "0")) / EMU_PT
        for ci, tc in enumerate(tr.findall(A + "tc")):
            if tc.get("hMerge") == "1" or tc.get("vMerge") == "1" or int(tc.get("rowSpan", "1")) > 1:
                continue
            span = int(tc.get("gridSpan", "1"))
            cw = sum(grid[ci:ci + span])
            tb = tc.find(A + "txBody")
            if tb is None:
                continue
            ctx = TextCtx(deck, sh, master, txbody=tb, table_cell=True)
            ctx.bodyprs = [_cell_bodypr(tc.find(A + "tcPr"))]
            lay = layout_text(ctx, (0, 0, cw, h))
            if lay:
                need = lay["total_h"] + lay["ins"][1] + lay["ins"][3]
                h = max(h, need)
        out.append((tr, h))
    return out


def table_height(deck, sh, master):
    tbl = sh._element.find(f".//{A}tbl")
    if tbl is None:
        return None
    grid = [int(g.get("w")) / EMU_PT for g in tbl.findall(f"{A}tblGrid/{A}gridCol")]
    return sum(h for _, h in table_rows(deck, sh, master, tbl, grid))


def _f32(v):
    import struct
    return struct.unpack("f", struct.pack("f", float(v)))[0]


# ---- 入口 ------------------------------------------------------------------------------------------------
def render(pptx, out, width=1600, images=True):
    """pptx を描く。shapes.json と slide-NN.png を out に書き、shapes.json の中身を返す。"""
    from pptx import Presentation
    pptx = Path(pptx).resolve()
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    for f in out.glob("slide-*.png"):
        f.unlink()
    prs = Presentation(str(pptx))
    deck = Deck(prs)
    allrows = []
    n = 0
    for i, slide in enumerate(prs.slides, 1):
        n = i
        rows = shape_rows(deck, slide, i)
        master = slide.slide_layout.slide_master
        for sh, row in zip(slide.shapes, rows):
            if row["type"] == 19:   # 表：文字が入らない行は PowerPoint が広げるので、その高さにする
                try:
                    th = table_height(deck, sh, master)
                    if th and th > row["height"] + 0.5:
                        row["height"] = round(th, 3)
                except Exception:
                    pass
        for row in rows:   # PowerPoint の COM は位置を単精度（float32）で返す。境目ちょうどの比べ（0.30 in など）を同じにするため、そろえる
            for k in ("left", "top", "width", "height", "tl", "tt", "tw", "th"):
                if row.get(k) is not None:
                    row[k] = _f32(row[k])
        allrows.extend(rows)
        if images:
            try:
                SlideRenderer(deck, slide, i, width).run().save(out / f"slide-{i:02d}.png")
            except Exception as e:
                print(f"注意: スライド {i} の画像を描けなかった（{type(e).__name__}: {e}）", file=sys.stderr)
    js = dict(pptx=str(pptx), engine="python", slideWidth=deck.W, slideHeight=deck.H, slides=n, shapes=allrows)
    (out / "shapes.json").write_text(json.dumps(js, ensure_ascii=False, indent=1), encoding="utf-8")
    return js


def main(argv=None):
    ap = argparse.ArgumentParser(description="pptx だけから shapes.json と slide-NN.png を作る（PowerPoint を使わない）")
    ap.add_argument("-Pptx", "--pptx", required=True)
    ap.add_argument("-OutDir", "--outdir", required=True)
    ap.add_argument("-Width", "--width", type=int, default=1600)
    ap.add_argument("-NoImages", "--noimages", action="store_true")
    a = ap.parse_args(argv)
    js = render(a.pptx, a.outdir, a.width, not a.noimages)
    print(f"rendered {js['slides']} slides -> {a.outdir}（PowerPoint を使わない描画。最後は画像を目で見て確かめる）")
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):   # パイプで走らせると日本語の Windows では cp932 になり、珍しい字で落ちる
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
