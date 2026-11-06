"""手持ちのスライド（.pptx）を分析して、テンプレートの見た目の特徴を表にする（make_template.py が使う。単独でも動く）。

    python <skill>/scripts/analyze_template.py <元のスライド.pptx> [--json 出力.json]

AI の判断を入れずに、毎回同じ結果になるように、python-pptx で数えた値だけを出す（どのモデルで動かしても同じ表になる）。
値は「実際のスライドで一番多いもの」を基本にし、スライドに無いものはマスター・レイアウト・テーマから取る。
「目安」の列は、研究発表・スライドデザインの手引きの値（下の出典）。外れていても直さずに、元のスライドの好みとして扱う
（ユーザーに伝えるだけ。直すかはユーザーが決める）。
表のあとに、zemi.py に渡す見た目の設定（テンプレートの横に置く .json：色・見出しの印・まとめの帯の寄せ）を出す。

目安の出典（2026-11 に読んだもの）：
  伝わるデザイン（tsutawarudesign.com：レイアウト・文字組み・配色・フォント・箇条書き）
  見やすいパワポの作り方・学会発表スライドの作り方（felo.ai）、卒論発表パワポの作り方（smallppt.com）
  Zoho Show「25 presentation design tips」、deckary「slide types guide」、WCAG 2.1 1.4.3（コントラスト）
"""
import argparse
import colorsys
import json
import statistics
import sys
from collections import Counter
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor  # noqa: F401
from pptx.enum.dml import MSO_COLOR_TYPE, MSO_FILL_TYPE, MSO_THEME_COLOR
from pptx.enum.shapes import MSO_SHAPE_TYPE, PP_PLACEHOLDER
from pptx.enum.text import PP_ALIGN
from pptx.oxml.ns import qn

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

EMU_IN = 914400
MARKS = "●■◆▶▷►○□◇◎・▪▸•"
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
THEME_KEYS = {MSO_THEME_COLOR.TEXT_1: "dk1", MSO_THEME_COLOR.BACKGROUND_1: "lt1", MSO_THEME_COLOR.TEXT_2: "dk2",
              MSO_THEME_COLOR.BACKGROUND_2: "lt2", MSO_THEME_COLOR.DARK_1: "dk1", MSO_THEME_COLOR.LIGHT_1: "lt1",
              MSO_THEME_COLOR.DARK_2: "dk2", MSO_THEME_COLOR.LIGHT_2: "lt2",
              **{getattr(MSO_THEME_COLOR, f"ACCENT_{i}"): f"accent{i}" for i in range(1, 7)}}
ALIGN = {PP_ALIGN.LEFT: "左", PP_ALIGN.CENTER: "中央", PP_ALIGN.RIGHT: "右", PP_ALIGN.JUSTIFY: "両端"}


def inch(v):
    return round((v or 0) / EMU_IN, 2)


def mode(xs, default=None):
    xs = [x for x in xs if x is not None]
    return Counter(xs).most_common(1)[0][0] if xs else default


# ---------------------------------------------------------------- テーマ
def theme_of(prs):
    master = prs.slide_master
    part = next(r.target_part for r in master.part.rels.values() if r.reltype.endswith("/theme"))
    t = etree.fromstring(part.blob)
    colors = {}
    for c in t.find(f".//{A}clrScheme"):
        name = etree.QName(c).localname
        v = c.find(f"{A}srgbClr")
        s = c.find(f"{A}sysClr")
        colors[name] = (v.get("val") if v is not None else s.get("lastClr") if s is not None else None)
    fonts = {}
    for kind in ("majorFont", "minorFont"):
        f = t.find(f".//{A}{kind}")
        if f is not None:
            fonts[kind] = {k: (f.find(f"{A}{k}").get("typeface") if f.find(f"{A}{k}") is not None else "") for k in ("latin", "ea")}
    return colors, fonts


def color_of(cf, theme):
    """python-pptx の ColorFormat から RRGGBB。テーマの色は、明るさの調整を近似して足す。読めなければ None。"""
    try:
        if cf is None or cf.type is None:
            return None
        if cf.type == MSO_COLOR_TYPE.RGB:
            rgb = str(cf.rgb)
        elif cf.type == MSO_COLOR_TYPE.SCHEME:
            rgb = theme.get(THEME_KEYS.get(cf.theme_color, ""), None)
            if rgb is None:
                return None
        else:
            return None
        br = cf.brightness or 0
        if br:
            r, g, b = (int(rgb[i:i + 2], 16) / 255 for i in (0, 2, 4))
            h, l, s = colorsys.rgb_to_hls(r, g, b)
            l = l + (1 - l) * br if br > 0 else l * (1 + br)
            r, g, b = colorsys.hls_to_rgb(h, l, s)
            rgb = "".join(f"{round(x * 255):02X}" for x in (r, g, b))
        return rgb.upper()
    except Exception:
        return None


def fill_of(shape, theme):
    try:
        if shape.fill.type == MSO_FILL_TYPE.SOLID:
            return color_of(shape.fill.fore_color, theme)
    except Exception:
        pass
    return None


def luminance(rgb):
    def ch(v):
        v = int(v, 16) / 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(rgb[i:i + 2]) for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def hls(rgb):
    r, g, b = (int(rgb[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return colorsys.rgb_to_hls(r, g, b)


def is_grayish(rgb):
    h, l, s = hls(rgb)
    return s < 0.18 or l < 0.12 or l > 0.97


# ---------------------------------------------------------------- 図形の見分け
def is_title(sh):
    return sh.is_placeholder and sh.placeholder_format.type in (PP_PLACEHOLDER.TITLE, PP_PLACEHOLDER.CENTER_TITLE)


def runs(sh):
    if not sh.has_text_frame:
        return []
    return [(p, r) for p in sh.text_frame.paragraphs for r in p.runs if r.text.strip()]


def first_text(sh):
    return sh.text_frame.text.strip() if sh.has_text_frame else ""


def minor_ph(sh):
    """スライド番号・日付・フッターの枠（余白の計算から外す）。"""
    return sh.is_placeholder and sh.placeholder_format.type in (PP_PLACEHOLDER.SLIDE_NUMBER, PP_PLACEHOLDER.DATE, PP_PLACEHOLDER.FOOTER)


def band_like(sh, W, H):
    """下の2割にあって、幅が6割以上の帯（塗りか、塗りのある本文の枠）。"""
    return sh.top is not None and sh.top > 0.78 * H and (sh.width or 0) > 0.6 * W


def bar_like(sh, W, H):
    """タイトルの飾り：上の全幅の帯・左の縦棒・下線。"""
    if sh.top is None or sh.top > 0.25 * H:
        return None
    w, h = sh.width or 0, sh.height or 0
    if w > 0.8 * W and h < 0.25 * H:
        return "上の全幅の帯" if h > 0.04 * H else "全幅の線"
    if w < 0.03 * W and h < 0.2 * H:
        return "左の縦棒"
    if h < 0.012 * H and w > 0.2 * W:
        return "下線"
    return None


# ---------------------------------------------------------------- 分析
def analyze(path):
    prs = Presentation(str(path))
    W, H = prs.slide_width, prs.slide_height
    theme, fonts = theme_of(prs)
    slides = list(prs.slides)
    content = [s for s in slides[1:] if any(is_title(sh) for sh in s.placeholders)] or slides[1:] or slides
    rep, style = [], {"colors": {}}

    def row(group, item, value, how, aim=""):
        rep.append({"分類": group, "項目": item, "値": value, "目安": aim, "測り方": how})

    # 大きさ・枚数・レイアウト
    w, h = W / EMU_IN, H / EMU_IN
    row("全体", "大きさ", f"{w:.2f}×{h:.2f} in（{'16:9' if abs(w / h - 16 / 9) < 0.02 else '4:3' if abs(w / h - 4 / 3) < 0.02 else 'その他'}）", "プレゼンテーションの幅と高さ")
    row("全体", "スライドの枚数", len(slides), "")
    used = Counter(s.slide_layout.name for s in slides)
    row("全体", "使われたレイアウト", "、".join(f"{k}（{v}枚）" for k, v in used.most_common()), "各スライドのレイアウトの名前を数えた")
    lc = mode([s.slide_layout.name for s in content])
    lt = slides[0].slide_layout.name if slides else None
    row("全体", "本文に使うレイアウト", lc, "2枚目以降でタイトルの枠があるスライドの、一番多いレイアウト")
    row("全体", "表紙に使うレイアウト", lt, "1枚目のレイアウト")
    divider = [i + 1 for i, s in enumerate(slides[1:], 1)
               if any(is_title(sh) for sh in s.placeholders) and sum(1 for sh in s.shapes if first_text(sh)) <= 2 and not s.shapes._spTree.xpath(".//p:pic")]
    row("全体", "区切りのスライド", "、".join(map(str, divider[:8])) or "なし", "タイトルのほかに文字が1つまでで、画像の無いスライド")

    # テーマ
    row("テーマ", "テーマの色", "、".join(f"{k}={v}" for k, v in theme.items() if v), "テーマの配色（dk1=本文の文字、lt1=背景、accent=強調の候補）")
    row("テーマ", "テーマのフォント", "、".join(f"{'見出し' if k == 'majorFont' else '本文'}：{v.get('latin') or '—'}／{v.get('ea') or '—'}" for k, v in fonts.items()), "テーマのフォント（欧文／和文）")
    bg = prs.slide_master.background.fill if hasattr(prs.slide_master, "background") else None
    bgc = None
    try:
        bgc = color_of(bg.fore_color, theme) if bg is not None and bg.type == MSO_FILL_TYPE.SOLID else None
    except Exception:
        pass
    pics_master = len(prs.slide_master.shapes._spTree.xpath(".//p:pic")) + sum(len(l.shapes._spTree.xpath(".//p:pic")) for l in prs.slide_layouts)
    row("テーマ", "背景", (f"単色 {bgc}" if bgc else "白（テーマの背景）") + (f"、マスターとレイアウトに画像 {pics_master} 個（ロゴ・飾り）" if pics_master else ""), "マスターの背景と、マスター・レイアウトの画像")

    # タイトル
    tsz, tcol, tb, tal, tfont, tpos = [], [], [], [], [], []
    for s in content:
        for sh in s.placeholders:
            if is_title(sh):
                tpos.append((inch(sh.left), inch(sh.top), inch(sh.width), inch(sh.height)))
                for p, r in runs(sh):
                    tsz.append(r.font.size.pt if r.font.size else None)
                    tcol.append(color_of(r.font.color, theme))
                    tb.append(r.font.bold)
                    tfont.append(r.font.name)
                    tal.append(ALIGN.get(p.alignment))
    # マスターのタイトルの書式（スライドに無いとき）
    ts = prs.slide_master._element.find(qn("p:txStyles"))
    mrpr = ts.find(qn("p:titleStyle")).find(qn("a:lvl1pPr")).find(qn("a:defRPr")) if ts is not None else None
    msz = int(mrpr.get("sz")) / 100 if mrpr is not None and mrpr.get("sz") else None
    mcol = None
    if mrpr is not None and mrpr.find(f"{A}solidFill/{A}srgbClr") is not None:
        mcol = mrpr.find(f"{A}solidFill/{A}srgbClr").get("val")
    tp = mode(tpos)
    row("タイトル", "位置と大きさ", f"左 {tp[0]}・上 {tp[1]}・幅 {tp[2]}・高さ {tp[3]} in" if tp else "—", "本文のスライドのタイトルの枠の、一番多い位置")
    row("タイトル", "文字の大きさ", f"{mode(tsz) or msz or '—'} pt", "タイトルの文字の一番多い大きさ（無ければマスター）")
    title_color = mode(tcol) or mcol or theme.get("dk1")
    row("タイトル", "文字の色", title_color or "—", "タイトルの文字の一番多い色（無ければマスター・テーマ）")
    row("タイトル", "太字・揃え・フォント", f"{'太字' if mode(tb) else '太字でない'}・{mode(tal) or 'マスターどおり'}・{mode(tfont) or fonts.get('majorFont', {}).get('ea') or 'テーマどおり'}", "タイトルの文字の一番多い値")
    deco = Counter()
    deco_col = {}
    for container in [prs.slide_master] + list(prs.slide_layouts):
        for sh in container.shapes:
            if sh.is_placeholder:
                continue
            k = bar_like(sh, W, H)
            if k:
                deco[k] += 1
                deco_col.setdefault(k, fill_of(sh, theme))
    for s in content:
        for sh in s.shapes:
            if not sh.is_placeholder:
                k = bar_like(sh, W, H)
                if k:
                    deco[k] += 1
                    deco_col.setdefault(k, fill_of(sh, theme))
    row("タイトル", "タイトルの飾り", "、".join(f"{k}（{deco_col.get(k) or '色不明'}）" for k, _ in deco.most_common()) or "なし",
        "マスター・レイアウト・本文のスライドの、上の2.5割にある帯・縦棒・線")

    # 見出しの印・本文・強調
    marks, mark_col, mark_slides = Counter(), [], set()
    bsz, bcol, bfont, bspace, bal, bleft, chars, nlines = [], [], [], [], [], [], [], []
    emph, bold_runs, all_runs = [], 0, 0
    text_colors, font_names = Counter(), Counter()
    for i, s in enumerate(content):
        cnt_chars, cnt_lines = 0, 0
        for sh in s.shapes:
            if not sh.has_text_frame or is_title(sh) or band_like(sh, W, H):
                continue
            t = first_text(sh)
            if not t:
                continue
            if t[0] in MARKS and (sh.top or 0) < 0.35 * H:
                marks[t[0]] += 1
                mark_slides.add(i)
                rr = runs(sh)
                if rr:
                    mark_col.append(color_of(rr[0][1].font.color, theme))
                continue
            if sh.is_placeholder and sh.placeholder_format.type in (PP_PLACEHOLDER.SLIDE_NUMBER, PP_PLACEHOLDER.FOOTER, PP_PLACEHOLDER.DATE):
                continue
            bleft.append(inch(sh.left))
            for p in sh.text_frame.paragraphs:
                if p.text.strip():
                    cnt_lines += 1
                    cnt_chars += len(p.text.replace(" ", ""))
                    if p.line_spacing:
                        bspace.append(round(p.line_spacing, 2) if isinstance(p.line_spacing, float) else f"{p.line_spacing.pt:.0f}pt")
                    bal.append(ALIGN.get(p.alignment))
            for p, r in runs(sh):
                all_runs += 1
                sz = r.font.size.pt if r.font.size else None
                c = color_of(r.font.color, theme)
                bsz.append(sz if sz and sz >= 12 else None)
                bcol.append(c)
                bfont.append(r.font.name or "（テーマのフォント）")
                if c:
                    text_colors[c] += 1
                if r.font.name:
                    font_names[r.font.name] += 1
                if r.font.bold:
                    bold_runs += 1
        chars.append(cnt_chars)
        nlines.append(cnt_lines)
    body_color = mode(bcol) or theme.get("dk1")
    for c in bcol:
        if c and c != body_color and not is_grayish(c):
            emph.append(c)
    mark = marks.most_common(1)[0][0] if marks else None
    row("見出し", "見出しの印", f"「{mark}」（本文のスライドの {len(mark_slides)}/{len(content)} 枚）" if mark else "なし",
        "本文のスライドの上の3.5割で、記号（●■◆▶ など）から始まる文字の枠")
    row("見出し", "見出しの印の色", mode(mark_col) or "—", "その記号の文字の色")
    row("本文", "文字の大きさ", f"{mode(bsz) or '—'} pt（中央値 {statistics.median([x for x in bsz if x]) if any(bsz) else '—'}）", "本文の文字（12pt 以上）の一番多い大きさ")
    row("本文", "文字の色", body_color or "—", "本文の文字の一番多い色")
    bf = mode(bfont)
    row("本文", "フォント", f"テーマどおり（{fonts.get('minorFont', {}).get('latin') or '—'}／{fonts.get('minorFont', {}).get('ea') or '—'}）" if bf in (None, "（テーマのフォント）") else bf,
        "本文の文字の一番多いフォント（名前の指定が無ければテーマのフォント）")
    row("本文", "行間・揃え", f"{mode(bspace) or 'テーマどおり'}・{mode(bal) or 'マスターどおり'}", "本文の段落の一番多い行間と揃え")
    row("本文", "左端の位置", f"{mode(bleft) or '—'} in", "本文の文字の枠の左端の、一番多い位置")
    row("本文", "1枚の量", f"中央値 {statistics.median(chars) if chars else 0:.0f} 字・{statistics.median(nlines) if nlines else 0:.0f} 段落", "本文のスライドの、文字の数と段落の数")
    emph_color = mode(emph)
    row("強調", "強調の色", emph_color or "なし", "本文の文字の色のうち、本文の色と灰色以外で一番多いもの")
    row("強調", "太字の割合", f"{bold_runs}/{all_runs}" if all_runs else "—", "本文の文字のうち太字のもの")
    row("強調", "文字の色の数", f"{len(text_colors)} 色（" + "、".join(f"{k}:{v}" for k, v in text_colors.most_common(5)) + "）", "本文の文字に使われた色（多い順に5つ）")
    row("強調", "フォントの数", f"{len(font_names)} 種類（" + "、".join(k for k, _ in font_names.most_common(4)) + "）" if font_names else "テーマのフォントだけ", "本文の文字に名前で指定されたフォント")

    # まとめの帯
    band_cols, band_txt, band_al, band_h, band_slides = [], [], [], [], 0
    for s in content:
        hit = False
        for sh in s.shapes:
            if band_like(sh, W, H) and (fill_of(sh, theme) or first_text(sh)):
                if sh.is_placeholder and sh.placeholder_format.type == PP_PLACEHOLDER.SLIDE_NUMBER:
                    continue
                hit = True
                band_cols.append(fill_of(sh, theme))
                band_h.append(inch(sh.height))
                for p, r in runs(sh):
                    band_txt.append(color_of(r.font.color, theme))
                    band_al.append(ALIGN.get(p.alignment))
        band_slides += hit
    layout_band = None
    lay = next((l for l in prs.slide_layouts if l.name == lc), None)
    if lay is not None:
        for ph in lay.placeholders:
            if ph.placeholder_format.type == PP_PLACEHOLDER.BODY and ph.top > 0.8 * H:
                layout_band = ph.placeholder_format.idx
    if lay is not None and layout_band is not None:          # 帯の色・文字の色は、レイアウトの枠から受け継いでいることが多い
        ph = next(x for x in lay.placeholders if x.placeholder_format.idx == layout_band)
        band_cols.append(fill_of(ph, theme))
        lv = ph._element.find(f".//{A}lstStyle/{A}lvl1pPr")
        if lv is not None:
            c = lv.find(f"{A}defRPr/{A}solidFill/{A}srgbClr")
            if c is not None:
                band_txt.append(c.get("val"))
            if lv.get("algn"):
                band_al.append({"l": "左", "ctr": "中央", "r": "右"}.get(lv.get("algn")))
    for container in ([lay] if lay is not None else []) + [prs.slide_master]:   # レイアウト・マスターに描いてある帯の地
        for sh in container.shapes:
            if not sh.is_placeholder and band_like(sh, W, H) and fill_of(sh, theme):
                band_cols.append(fill_of(sh, theme))
    band_col = mode([c for c in band_cols if c]) or None
    row("まとめの帯", "有無", f"本文のスライドの {band_slides}/{len(content)} 枚" + (f"・レイアウトに枠あり（idx {layout_band}）" if layout_band else "・レイアウトに枠なし"),
        "下の2割にある、幅6割以上の塗りか文字の帯")
    row("まとめの帯", "色・文字の色・寄せ・高さ", f"{band_col or '塗りなし'}・{mode(band_txt) or '—'}・{mode(band_al) or '—'}・{mode(band_h) or '—'} in", "その帯の一番多い値")

    # 塗り・線・ページ番号・余白・図
    fills, lines_c = Counter(), Counter()
    pic_pos = Counter()
    lefts, rights = [], []
    for s in content:
        for sh in s.shapes:
            if is_title(sh) or band_like(sh, W, H) or bar_like(sh, W, H):
                continue
            if sh.shape_type == MSO_SHAPE_TYPE.AUTO_SHAPE:
                f = fill_of(sh, theme)
                if f:
                    fills[f] += 1
            try:
                if sh.shape_type in (MSO_SHAPE_TYPE.LINE, MSO_SHAPE_TYPE.FREEFORM) or getattr(sh, "begin_x", None) is not None:
                    c = color_of(sh.line.color, theme)
                    if c:
                        lines_c[c] += 1
            except Exception:
                pass
            if sh.shape_type == MSO_SHAPE_TYPE.PICTURE and (sh.width or 0) > 0.15 * W:
                cx = (sh.left + sh.width / 2) / W
                pic_pos["全幅" if sh.width > 0.7 * W else "右" if cx > 0.55 else "左" if cx < 0.45 else "中央"] += 1
            if sh.left is not None and sh.width and sh.width < 0.95 * W and not minor_ph(sh):
                lefts.append(inch(sh.left))
                rights.append(round(w - inch(sh.left + sh.width), 2))
    pale = [c for c, _ in fills.most_common() if hls(c)[1] > 0.8]
    strong = [c for c, _ in fills.most_common() if hls(c)[1] <= 0.8 and not is_grayish(c)]
    row("塗りと線", "表・箱の塗り", "、".join(f"{c}:{n}" for c, n in fills.most_common(6)) or "なし", "本文のスライドの図形の塗りの色（多い順）")
    row("塗りと線", "薄い塗り・濃い塗り", f"薄い {pale[0] if pale else '—'}・濃い {strong[0] if strong else '—'}", "塗りの色を明るさで分けた、それぞれ一番多いもの")
    row("塗りと線", "線・矢印の色", "、".join(f"{c}:{n}" for c, n in lines_c.most_common(3)) or "なし", "線・コネクタの色")
    num_pos = "—"
    if lay is not None:
        for ph in lay.placeholders:
            if ph.placeholder_format.type == PP_PLACEHOLDER.SLIDE_NUMBER:
                num_pos = ("右" if ph.left > W / 2 else "左") + ("下" if ph.top > H / 2 else "上")
    row("配置", "ページ番号", num_pos, "本文のレイアウトのスライド番号の枠の位置")
    row("配置", "左右の余白", f"左 {min(lefts) if lefts else '—'} in・右 {min(rights) if rights else '—'} in（いちばん外側）", "本文のスライドの図形の、いちばん左・いちばん右")
    row("配置", "図の置き方", "、".join(f"{k}:{v}" for k, v in pic_pos.most_common()) or "図なし", "幅1.5割以上の画像の置き場所（右・左・中央・全幅）")

    # 手引きの目安と比べる特徴（余白・比・字間・行間・揃え・色の明暗差など）
    tops, bottoms, spc, after, blank_paras, aligns, left_set, sizes_per, margins, tables, pic_area = [], [], [], [], 0, Counter(), [], [], [], [], []
    for s in content:
        sz_here = set()
        area = 0
        for sh in s.shapes:
            if sh.left is None or not sh.width:
                continue
            if not is_title(sh) and not band_like(sh, W, H) and not bar_like(sh, W, H) and sh.width < 0.95 * W and not minor_ph(sh):
                tops.append(inch(sh.top))
                bottoms.append(round(h - inch(sh.top + sh.height), 2))
            if sh.shape_type == MSO_SHAPE_TYPE.PICTURE:
                area += sh.width * sh.height
            if sh.has_table:
                tables.append((len(sh.table.rows), len(sh.table.columns)))
            if not sh.has_text_frame or is_title(sh) or band_like(sh, W, H) or not first_text(sh):
                continue
            left_set.append(round(inch(sh.left), 1))
            tf = sh.text_frame
            margins.append(tuple(inch(getattr(tf, k)) if getattr(tf, k) is not None else None for k in ("margin_left", "margin_top")))
            for para in tf.paragraphs:
                if not para.text.strip():
                    blank_paras += 1
                    continue
                aligns[ALIGN.get(para.alignment) or "マスターどおり"] += 1
                if para.space_after is not None:
                    after.append(round(para.space_after.pt, 1))
                for r in para.runs:
                    v = r._r.find(qn("a:rPr"))
                    if v is not None and v.get("spc"):
                        spc.append(int(v.get("spc")) / 100)
                    if r.font.size:
                        sz_here.add(r.font.size.pt)
        sizes_per.append(len(sz_here))
        pic_area.append(area / (W * H))
    tsize = mode(tsz) or msz
    bsize = mode(bsz)
    row("手引きと比べる", "余白（四辺）", f"左 {min(lefts) if lefts else '—'}・上 {min(tops) if tops else '—'}・右 {min(rights) if rights else '—'}・下 {min(bottoms) if bottoms else '—'} in",
        "タイトル・帯を除いた図形の、いちばん外側", "四辺とも 0.5 in（15 mm）以上")
    row("手引きと比べる", "タイトルと本文の大きさの比", f"{tsize / bsize:.1f} 倍（{tsize}／{bsize} pt）" if tsize and bsize else "—",
        "タイトルの大きさ ÷ 本文の大きさ（ジャンプ率）", "本文 18〜24 pt、タイトル 32〜40 pt")
    row("手引きと比べる", "1枚の文字の大きさの種類", f"中央値 {statistics.median(sizes_per):.0f} 種類" if sizes_per else "—",
        "本文のスライドごとに、使われた文字の大きさの数", "1枚に 2〜3 種類")
    row("手引きと比べる", "字間", f"{mode(spc)} pt" if spc else "指定なし（0）", "文字の run の spc（1/100 pt）", "文字の大きさの約5%（20 pt なら 1 pt）")
    row("手引きと比べる", "段落のあとの間隔・空の段落", f"{mode(after) if after else '指定なし'} pt・空の段落 {blank_paras} 個", "段落の space_after と、文字の無い段落",
        "空の段落で間を空けず、段落のあとの間隔で空ける")
    al_mix = "・".join(f"{k}:{v}" for k, v in aligns.most_common())
    row("手引きと比べる", "揃えの混在", al_mix or "—", "本文の段落の揃え", "左揃えが基本。左と中央を混ぜない")
    clusters = sorted(Counter(left_set).items(), key=lambda x: -x[1])
    row("手引きと比べる", "左端の揃い", f"{len(clusters)} か所（多い順：" + "、".join(f"{k} in" for k, _ in clusters[:4]) + "）" if clusters else "—",
        "文字の枠の左端（0.1 in で丸めた）の種類", "左端を少ない位置にそろえる")
    mg = mode(margins)
    row("手引きと比べる", "枠の内側の余白", f"左 {mg[0]}・上 {mg[1]} in" if mg and mg[0] is not None else "既定（左右 0.1・上下 0.05 in）", "文字の枠の margin_left・margin_top", "枠の中の上下に1文字分ほど")
    row("手引きと比べる", "表の大きさ", "、".join(f"{r}行×{c}列" for r, c in tables[:4]) or "表なし", "表の行と列の数", "5列×7行まで")
    row("手引きと比べる", "図の面積", f"中央値 {statistics.median(pic_area) * 100:.0f}%（最大 {max(pic_area) * 100:.0f}%）" if pic_area else "—",
        "本文のスライドで、画像が占める面積の割合", "図はできるだけ大きく。文と図は 4:6 ほど")
    bgcol = bgc or theme.get("lt1") or "FFFFFF"
    if body_color:
        ratio = contrast(body_color, bgcol)
        row("手引きと比べる", "文字と背景の明暗差", f"{ratio:.1f} : 1（本文 {body_color} と背景 {bgcol}）", "WCAG の相対輝度の比", "4.5 : 1 以上（大きな文字は 3 : 1）")
    if band_col and mode(band_txt):
        row("手引きと比べる", "まとめの帯の明暗差", f"{contrast(mode(band_txt), band_col):.1f} : 1", "帯の文字の色と帯の色の相対輝度の比", "4.5 : 1 以上")
    ncol = len([c for c, n in text_colors.items() if n >= 2])
    row("手引きと比べる", "色の数", f"文字 {ncol} 色・塗り {len(fills)} 色", "2回以上使われた文字の色と、塗りの色の数", "背景・文字・主色・強調の 3〜4 色")

    # zemi.py に渡す見た目の設定
    accent = theme.get("accent1")
    if body_color:
        style["colors"]["TEXT"] = body_color
    if emph_color:
        style["colors"]["RED"] = emph_color
    if mark and mode(mark_col):
        style["colors"]["BULLET"] = mode(mark_col)
    if mark and mark != "●":
        style["heading_mark"] = mark
    band_or_bar = band_col or deco_col.get("上の全幅の帯") or deco_col.get("左の縦棒") or theme.get("dk2")
    if band_or_bar:
        style["colors"]["BAND"] = band_or_bar
    if pale:   # 薄い主色（表の見出し・流れ図の箱）。灰色の囲み（場合分けなど）より色味のある塗りを選ぶ
        tinted = [c for c in pale if not is_grayish(c)]
        style["colors"]["PALE"] = (tinted or pale)[0]
    if accent:
        style["colors"]["ARROW"] = accent
    if mode(band_al) == "左":
        style["band_align"] = "l"
    return {"source": str(path), "rows": rep, "style": style,
            "layouts": {"本文": lc, "表紙": lt}, "band_in_layout": layout_band is not None}


def print_report(res):
    print(f"分析したスライド：{res['source']}\n")
    print("| 分類 | 項目 | 値 | 目安 | 測り方 |\n|---|---|---|---|---|")
    for r in res["rows"]:
        print(f"| {r['分類']} | {r['項目']} | {r['値']} | {r.get('目安', '')} | {r['測り方']} |")
    print("\nzemi.py に渡す見た目の設定（テンプレートの横の .json）：")
    print(json.dumps(res["style"], ensure_ascii=False, indent=2))


def main():
    ap = argparse.ArgumentParser(description="手持ちのスライドを分析して、テンプレートの見た目の特徴を表にする")
    ap.add_argument("pptx")
    ap.add_argument("--json", help="見た目の設定（style）を書き出す先")
    a = ap.parse_args()
    res = analyze(a.pptx)
    print_report(res)
    if a.json:
        Path(a.json).write_text(json.dumps(res["style"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"\nwrote {a.json}")


if __name__ == "__main__":
    main()
