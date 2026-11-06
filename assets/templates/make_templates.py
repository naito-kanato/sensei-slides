"""同梱のテンプレート「テンプレート1〜8」（構造。番号は見やすさの順）と配色（配色.json）を、python-pptx の白紙から作る（スキルの作者用）。

    python assets/templates/make_templates.py              # assets/templates/ に テンプレート1〜8.pptx・.json と 配色.json を作る
    python assets/templates/make_templates.py <出力先>     # 試しに別の場所へ

テンプレートは「構造」（タイトルの置き方・結論の置き場・本文の場所と割合）で分け、色は「配色」で変える。
どの構造にも標準の配色があり、`deck_options(P, color="深緑")` か設定の一覧の「色」で別の配色にできる。
マスター・レイアウトの飾りの図形は名前に役割（{main} {accent} {tint} {band_bg}）を付けてあり、zemi.py が配色を差し替える。
構造は、研究発表のデッキと公開されているフリーのテンプレート（研究発表用・論文発表用）の形から、研究発表に合うものを選んで白紙から作った。
どれも白地で、研究発表のデザインの手引きの目安に合わせた：本文 20 pt、文字と背景の明暗差 4.5:1 以上、四辺の余白 0.4 in 以上。
ライセンスはこのリポジトリと同じ（MIT）。作り直したら tests/update_manifest.py で部品の指紋も作り直す。
"""
import json
import sys
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.oxml.ns import qn
from pptx.util import Inches

W, H = Inches(13.333), Inches(7.5)
BAND_TOP = Inches(6.76)       # 下のまとめの帯（zemi.py の BAND_TOP と同じ）
NS = 'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"'

# ---- 配色（役割 → 色）。main：主色（見出し・帯）、accent：差し色（●・線）、ink：本文、emph：強調、pale：薄い主色の塗り、
#      light：薄い灰の塗り、arrow：矢印、tint：淡い地（上の帯・柱）、band_bg／band_text：下の帯、conclude：結論の囲み
PALETTES = {
    "青":       dict(main="215F99", accent="4E95D9", bullet="005AFF", ink="545455", emph="FF0000", pale="DCE9F7", light="F2F2F2",
                    arrow="4E95D9", tint="EAF1FA", band_bg="215F99", band_text="FFFFFF", conclude="FBE3D6"),
    "紺とオレンジ": dict(main="1F3A5F", accent="E8772E", bullet="E8772E", ink="3C3C3C", emph="C8102E", pale="FBE7D8", light="F4F2EF",
                    arrow="F0A46E", tint="F5EFE6", band_bg="F5EFE6", band_text="1F3A5F", conclude="FBE7D8"),
    "生成りと山吹": dict(main="2F4B66", accent="D9A21B", bullet="D9A21B", ink="333333", emph="D62D20", pale="E3ECF5", light="F3F3F3",
                    arrow="9AAFC4", tint="FFF4D6", band_bg="FFF4D6", band_text="2F4B66", conclude="FBE3D6"),
    "藍":       dict(main="1F4E79", accent="2E75B6", bullet="2E75B6", ink="333333", emph="C00000", pale="DEEBF7", light="F2F2F2",
                    arrow="8FB4D9", tint="EAF1FA", band_bg="1F4E79", band_text="FFFFFF", conclude="FBE3D6"),
    "青緑":     dict(main="0B4F6C", accent="0B7A75", bullet="0B7A75", ink="333333", emph="C62828", pale="DDEFEE", light="F2F5F5",
                    arrow="5FA8A3", tint="E6F2F1", band_bg="E6F2F1", band_text="0B4F6C", conclude="FCE4D6"),
    "珊瑚":     dict(main="5A2E28", accent="E8604C", bullet="E8604C", ink="3A3A3A", emph="B42318", pale="FCE3DD", light="F6F1EF",
                    arrow="EE9A8C", tint="FBE7E1", band_bg="FBE7E1", band_text="5A2E28", conclude="FCE3DD"),
    "墨と山吹": dict(main="2B2B2B", accent="F2A900", bullet="F2A900", ink="333333", emph="C0392B", pale="FCEFC7", light="F3F3F3",
                    arrow="F2C14E", tint="F5F5F5", band_bg="2B2B2B", band_text="FFFFFF", conclude="FCEFC7"),
    "深緑":     dict(main="2E5E4E", accent="2E5E4E", bullet="2E5E4E", ink="333333", emph="B23A48", pale="DCE8E2", light="F2F4F3",
                    arrow="7FA898", tint="EEF3F0", band_bg="EEF3F0", band_text="2E5E4E", conclude="F6E0E2"),
    "グレーと赤": dict(main="333333", accent="C0392B", bullet="C0392B", ink="333333", emph="C0392B", pale="F6E1DE", light="F2F2F2",
                    arrow="D98880", tint="EFEFEF", band_bg="EFEFEF", band_text="333333", conclude="F6E1DE"),
    "墨と藍":   dict(main="1F3864", accent="2F75B5", bullet="2F75B5", ink="262626", emph="C00000", pale="DEEAF6", light="F2F2F2",
                    arrow="9DB9D8", tint="EEF3F9", band_bg="1F3864", band_text="FFFFFF", conclude="FBE3D6"),
}
# 強調（emph）は本文の地で明暗差 4.5:1 以上、差し色（●・札）と色相を離す。紺とオレンジ（D9480F）と珊瑚（D1392A）は
# 差し色のオレンジ・珊瑚と見分けにくく、赤字の結論が飾りに埋もれていた（紺とオレンジは 4.3:1）ので、深い赤に
for _p in PALETTES.values():
    _p.setdefault("rule", "D0D0D0")   # 本文と見出しを分ける細い線

# ---- 構造。title：タイトルの位置・大きさ・色の役割、deco：マスターの飾り、band：下の帯（無ければ None）、
#      conclusion：結論の置き場（zemi.py）、area：本文の場所（in）。番号は下の ORDER（見やすさの順。1 が既定）
STRUCTURES = [
    dict(label="下の帯", palette="青", mark="●",
         desc="左上の縦棒とタイトル、下の帯に結論の1行（ゼミの基本の形）",
         title=dict(x=0.6, y=0.12, w=12.2, h=0.8, sz=3600, color="ink"),
         deco=[("タイトルの左の縦棒", 0.32, 0.24, 0.13, 0.66, "main")],
         band="solid", conclusion="band",
         area=dict(x=1.0, top=1.9, right=12.33, bottom=6.62, heading=(0.55, 1.14), fig_x=7.6),
         cover=[("表紙の左の縦棒", 0.32, 0.24, 0.13, 0.66, "main")]),
    dict(label="上の帯", palette="紺とオレンジ", mark="●",
         desc="上の濃い帯にタイトル、下に「まとめ」の札つきの淡い帯",
         title=dict(x=0.45, y=0.1, w=12.4, h=0.8, sz=3000, color="white"),
         deco=[("タイトルの帯", 0, 0, 13.333, 0.98, "main"), ("タイトルの下の線", 0, 0.98, 13.333, 0.06, "accent")],
         band="tag", conclusion="band",
         area=dict(x=1.0, top=1.9, right=12.33, bottom=6.62, heading=(0.55, 1.14), fig_x=7.6),
         cover=[("表紙の帯", 0, 6.68, 13.333, 0.82, "main"), ("表紙の線", 0, 6.6, 13.333, 0.08, "accent")]),
    dict(label="結論の囲み", palette="生成りと山吹", mark="●",
         desc="上に淡い帯（タイトルは中央）、下の帯は無く、結論は淡い色の囲みに（学会発表）",
         title=dict(x=0.45, y=0.1, w=12.4, h=0.8, sz=3200, color="main", align="ctr"),
         deco=[("タイトルの地", 0, 0, 13.333, 0.98, "tint")],
         band=None, conclusion="box",
         # 本文の下端は結論の囲み（zemi.BOX_TOP 6.25 in）の上 0.15 in。囲みが 6.05 in で下に 0.8 in 空き、本文が狭くて下の図が小さくなっていた
         area=dict(x=1.0, top=1.9, right=12.33, bottom=6.1, heading=(0.55, 1.14), fig_x=7.6),
         cover=[("表紙の帯", 0, 6.68, 13.333, 0.82, "tint"), ("表紙の線", 0, 6.6, 13.333, 0.08, "accent")]),
    dict(label="結論タイトル", palette="藍", mark="●", arrow="thin",
         desc="上に小さく話題、その下に大きく結論の一文。下の帯は無し（結論を見出しにする形）",
         # 話題の行の灰色は 6B6B6B（5.3:1）。8C8C8C では 3.4:1 で、16pt の細字には薄すぎた
         title=dict(x=0.6, y=0.12, w=12.2, h=0.45, sz=1600, color="gray", bold=False),
         deco=[], band=None, conclusion="title",
         area=dict(x=1.0, top=1.6, right=12.33, bottom=6.9, heading=(0.6, 0.62), fig_x=7.6),
         cover=[("表紙の帯", 0, 6.68, 13.333, 0.82, "main"), ("表紙の線", 0, 6.6, 13.333, 0.08, "accent")]),
    dict(label="細い左帯と副題", palette="青緑", mark="■",
         desc="左端に主色の細い帯、大きなタイトルの下に結論の副題の1行。下の帯は無し",
         # タイトル 28pt・副題（結論）24pt。32pt と 22pt では、「／ 見出し」を足したタイトルが結論より大きく目を引き、上下が逆だった。
         # 左の帯は 0.3 in（0.42 in では全高の濃い面が重かった）。副題はタイトルと同じ左端に
         title=dict(x=0.75, y=0.18, w=12.0, h=0.7, sz=2800, color="main"),
         deco=[("左の細い帯", 0, 0, 0.3, 7.5, "main")],
         band=None, conclusion="lead",
         area=dict(x=1.15, top=1.75, right=12.6, bottom=6.95, heading=(0.75, 0.98), fig_x=7.7, lead=(0.75, 0.98)),
         cover=[("表紙の左の帯", 0, 0, 1.2, 7.5, "main")]),
    dict(label="左の淡い柱", palette="珊瑚", mark="●",
         desc="左の 34% の淡い柱にタイトル・結論・短い要点、右に図を大きく（図が主役の枚）",
         title=dict(x=0.45, y=0.3, w=3.9, h=0.75, sz=2800, color="main"),
         deco=[("左の柱", 0, 0, 4.5, 7.5, "tint")],
         band=None, conclusion="column",
         area=dict(x=0.5, top=2.75, right=12.9, bottom=6.95, heading=(0.45, 2.2), fig_x=4.95, text_right=4.2,
                   column=(0.45, 1.05, 3.8)),
         cover=[("表紙の柱", 0, 0, 4.5, 7.5, "tint")]),
    dict(label="章のナビ", palette="墨と山吹", mark="■",
         desc="上に章の並び（今の章を主色に）、その下にタイトル、下に線で挟んだ結論の1行（長い発表）",
         title=dict(x=0.55, y=0.6, w=12.2, h=0.7, sz=2800, color="main"),
         deco=[], band="rules", conclusion="band", nav=True,
         area=dict(x=1.0, top=2.05, right=12.33, bottom=6.62, heading=(0.55, 1.42), fig_x=7.6),
         cover=[("表紙の線", 0, 6.6, 13.333, 0.08, "accent"), ("表紙の帯", 0, 6.68, 13.333, 0.82, "main")]),
]
STRUCTURES.append(
    # 見やすさを優先して、ここまでの構造の良い所を合わせたもの：結論を先に（結論の一文を見出しに）、本文を最大に、
    # 飾りは主色の短い縦棒と細い線だけ、本文は濃い墨（明暗差を高く）、見出しは小さな話題の行にまとめて上を2段に
    dict(label="結論ヘッダー", palette="墨と藍", mark="●", arrow="thin",
         desc="上に小さく話題と見出し、その下に大きく結論の一文（左に主色の短い縦棒）、細い線で本文と分ける。下の帯は無く、本文が一番広い",
         # 話題の行・結論の一文・結論の無い枚の●見出しの左端をそろえる（話題の行が 0.09 in 右にずれていた）
         title=dict(x=0.66, y=0.16, w=12.09, h=0.4, sz=1500, color="main"),
         deco=[("結論の左の縦棒", 0.45, 0.66, 0.1, 0.48, "main"), ("見出しの下の線", 0.45, 1.4, 12.43, 0.02, "rule")],
         band=None, conclusion="header",
         area=dict(x=0.9, top=1.72, right=12.43, bottom=6.95, heading=(0.66, 0.58), fig_x=7.5, message=(0.66, 0.56)),
         cover=[("表紙の下の線", 0, 7.36, 13.333, 0.14, "main")]))
# 番号は見やすさの順。8つを同じ中身で描き、構造の名前を伏せて別のエージェントに採点させた結果（2026-11-06、3回目：
# 帯も●も無い枚のレイアウトと「本文の枚には結論の一文」の決まりを入れ、空の帯が出なくなったあと）。
# 読む順・結論の見つけやすさ・使える面積・文字の明暗差・飾りの少なさ・いろいろな枚での崩れにくさ、各5点の30点満点。
# 結論ヘッダー 28、結論タイトル 27、細い左帯と副題 23、下の帯 21、上の帯 20、章のナビ 19、結論の囲み 18、左の淡い柱 17
ORDER = ["結論ヘッダー", "結論タイトル", "細い左帯と副題", "下の帯", "上の帯", "章のナビ", "結論の囲み", "左の淡い柱"]
STRUCTURES.sort(key=lambda st: ORDER.index(st["label"]))
ROLE_COLOR = {"white": "FFFFFF", "gray": "6B6B6B"}


def inch(v):
    return int(Inches(v))


def rect(id_, name, x, y, w, h, color, geom="rect"):
    return etree.fromstring(
        f'<p:sp {NS}><p:nvSpPr><p:cNvPr id="{id_}" name="{name}"/><p:cNvSpPr/><p:nvPr userDrawn="1"/></p:nvSpPr>'
        f'<p:spPr><a:xfrm><a:off x="{int(x)}" y="{int(y)}"/><a:ext cx="{int(w)}" cy="{int(h)}"/></a:xfrm>'
        f'<a:prstGeom prst="{geom}"><a:avLst/></a:prstGeom><a:solidFill><a:srgbClr val="{color}"/></a:solidFill><a:ln><a:noFill/></a:ln></p:spPr>'
        f'<p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:endParaRPr lang="ja-JP"/></a:p></p:txBody></p:sp>')


def label(id_, name, x, y, w, h, color, text, text_color="FFFFFF", size=1600):
    return etree.fromstring(
        f'<p:sp {NS}><p:nvSpPr><p:cNvPr id="{id_}" name="{name}"/><p:cNvSpPr/><p:nvPr userDrawn="1"/></p:nvSpPr>'
        f'<p:spPr><a:xfrm><a:off x="{int(x)}" y="{int(y)}"/><a:ext cx="{int(w)}" cy="{int(h)}"/></a:xfrm>'
        f'<a:prstGeom prst="roundRect"><a:avLst/></a:prstGeom><a:solidFill><a:srgbClr val="{color}"/></a:solidFill><a:ln><a:noFill/></a:ln></p:spPr>'
        f'<p:txBody><a:bodyPr lIns="0" rIns="0" tIns="0" bIns="0" anchor="ctr"/><a:lstStyle/><a:p><a:pPr algn="ctr"/>'
        f'<a:r><a:rPr lang="ja-JP" sz="{size}" b="1"><a:solidFill><a:srgbClr val="{text_color}"/></a:solidFill></a:rPr><a:t>{text}</a:t></a:r></a:p></p:txBody></p:sp>')


def deco(tree, items, pal, start=90):
    """飾りの図形を、名前に役割を付けて後ろに置く（zemi.py が {role} を見て配色を差し替える）。"""
    for k, (name, x, y, w, h, role) in enumerate(items):
        behind(tree, rect(start + k, f"{name} {{{role}}}", inch(x), inch(y), inch(w), inch(h), pal[role]))


def set_xfrm(sp, x, y, w, h):
    spPr = sp.find(qn("p:spPr"))
    old = spPr.find(qn("a:xfrm"))
    if old is not None:
        spPr.remove(old)
    xfrm = etree.Element(qn("a:xfrm"))
    spPr.insert(0, xfrm)
    etree.SubElement(xfrm, qn("a:off"), x=str(int(x)), y=str(int(y)))
    etree.SubElement(xfrm, qn("a:ext"), cx=str(int(w)), cy=str(int(h)))


def ph_type(sp):
    ph = sp.find(".//" + qn("p:ph"))
    return None if ph is None else (ph.get("type") or "body", ph.get("idx"))


def behind(tree, el):
    tree.insert(2, el)


def solid(parent, color):
    for f in parent.findall(qn("a:solidFill")):
        parent.remove(f)
    fill = etree.Element(qn("a:solidFill"))
    etree.SubElement(fill, qn("a:srgbClr"), val=color)
    parent.insert(0, fill)


def role_color(pal, role):
    return ROLE_COLOR.get(role) or pal[role]


def build(st, out):
    pal = PALETTES[st["palette"]]
    prs = Presentation()
    prs.slide_width, prs.slide_height = W, H
    master = prs.slide_master
    tree = master.shapes._spTree
    deco(tree, st["deco"], pal)
    t = st["title"]
    for sp in list(tree.iterchildren(qn("p:sp"))):
        typ = ph_type(sp)
        if typ is None:
            continue
        if typ[0] == "title":
            set_xfrm(sp, inch(t["x"]), inch(t["y"]), inch(t["w"]), inch(t["h"]))
        elif typ[0] == "sldNum":
            set_xfrm(sp, Inches(12.2), Inches(6.98), Inches(0.95), Inches(0.36))
        elif typ[0] in ("dt", "ftr"):
            tree.remove(sp)
        elif typ[0] == "body":
            set_xfrm(sp, Inches(0.55), Inches(1.6), Inches(12.2), Inches(5.0))
    title = master._element.find(qn("p:txStyles")).find(qn("p:titleStyle")).find(qn("a:lvl1pPr"))
    title.set("algn", t.get("align", "l"))
    rpr = title.find(qn("a:defRPr"))
    rpr.set("sz", str(t["sz"]))
    rpr.set("b", "1" if t.get("bold", True) else "0")
    solid(rpr, role_color(pal, t["color"]))
    # ---- テーマ：和文はメイリオ、欧文は Segoe UI、本文の文字色
    theme_part = next(r.target_part for r in master.part.rels.values() if r.reltype.endswith("/theme"))
    theme = etree.fromstring(theme_part.blob)
    a = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
    for font in theme.iter(a + "majorFont", a + "minorFont"):
        font.find(a + "latin").set("typeface", "Segoe UI")
        font.find(a + "ea").set("typeface", "Meiryo")
    for key, val in (("dk1", pal["ink"]), ("dk2", pal["main"]), ("accent1", pal["accent"]), ("accent2", pal["emph"])):
        el = theme.find(f".//{a}clrScheme/{a}{key}")
        for c in list(el):
            el.remove(c)
        etree.SubElement(el, a + "srgbClr", val=val)
    theme_part._blob = etree.tostring(theme, xml_declaration=True, encoding="UTF-8", standalone=True)
    # ---- レイアウト：本文用・表紙用と、帯も●も無い本文用（目次・確認問題・解答・図だけの枚など。「Title and Content」の本文の枠を消して使う）
    lst = master._element.find(qn("p:sldLayoutIdLst"))
    for lay, entry in zip(list(master.slide_layouts), list(lst)):
        if lay.name not in ("Title Only", "Title Slide", "Title and Content"):
            master.part.drop_rel(entry.get(qn("r:id")))
            lst.remove(entry)
    for lay in master.slide_layouts:
        ltree = lay.shapes._spTree
        for sp in list(ltree.iterchildren(qn("p:sp"))):
            typ = ph_type(sp)
            if typ and typ[0] in ("dt", "ftr"):
                ltree.remove(sp)
            elif typ and lay.name == "Title and Content" and typ[0] not in ("title", "sldNum"):
                ltree.remove(sp)   # 帯なしの本文：本文の枠（obj）は使わない
                continue
            elif typ and typ[0] in ("title", "sldNum"):
                x = sp.find(qn("p:spPr")).find(qn("a:xfrm"))
                if x is not None:
                    x.getparent().remove(x)
        if lay.name == "Title Only":
            lay.name = "本文"
            content_layout(lay, st, pal)
        elif lay.name == "Title and Content":
            lay.name = "本文（帯なし）"
            content_layout(lay, dict(st, band=None), pal)   # 下の帯・まとめの札・線を描かない（上の飾りはマスターのまま）
        else:
            lay.name = "表紙"
            cover_layout(lay, st, pal)
    core = prs.core_properties
    core.title, core.author, core.last_modified_by = f"{st['label']}（sensei-slides）", "", ""
    prs.save(out)
    style = {"label": st["label"], "structure": st["label"], "palette": st["palette"], "desc": st["desc"],
             "colors": colors_of(pal), "band_align": "l" if st["band"] == "tag" else "c",
             "conclusion": st["conclusion"], "area": st["area"], "title_color": t["color"]}
    if st["mark"] != "●":
        style["heading_mark"] = st["mark"]
    if st.get("arrow"):
        style["arrow"] = st["arrow"]
    if st.get("nav"):
        style["nav"] = True
    Path(out).with_suffix(".json").write_text(json.dumps(style, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def contrast(c1, c2):
    """2色（"RRGGBB"）の明暗差（WCAG の比）。"""
    def lum(c):
        v = [int(c[k:k + 2], 16) / 255 for k in (0, 2, 4)]
        v = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in v]
        return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]
    a, b = sorted((lum(c1), lum(c2)), reverse=True)
    return (a + 0.05) / (b + 0.05)


def tag_text(pal):
    """「まとめ」の札（差し色の地）の文字色：白か主色の、明暗差の大きいほう。zemi.py の recolor も同じ決め方。"""
    return max(("FFFFFF", pal["main"]), key=lambda c: contrast(c, pal["accent"]))


def colors_of(pal):
    """zemi.py の C の名前へ。"""
    return {"TEXT": pal["ink"], "RED": pal["emph"], "BULLET": pal["bullet"], "BAND": pal["main"], "ARROW": pal["arrow"],
            "PALE": pal["pale"], "LIGHT": pal["light"], "CONCLUDE": pal["conclude"], "ACCENT": pal["accent"], "TINT": pal["tint"]}


def sldnum_style(ltree, color):
    for sp in list(ltree.iterchildren(qn("p:sp"))):
        typ = ph_type(sp)
        if typ and typ[0] == "sldNum":
            lst_style = sp.find(qn("p:txBody")).find(qn("a:lstStyle"))
            for c in list(lst_style):
                lst_style.remove(c)
            lvl = etree.SubElement(lst_style, qn("a:lvl1pPr"), algn="r")
            dr = etree.SubElement(lvl, qn("a:defRPr"), sz="1200")
            etree.SubElement(etree.SubElement(dr, qn("a:solidFill")), qn("a:srgbClr"), val=color)
            ltree.remove(sp)
            ltree.append(sp)


def content_layout(lay, st, pal):
    tree = lay.shapes._spTree
    b = st["band"]
    if b is None:   # 帯の無い構造：まとめの帯の枠を作らない（結論は zemi.py が置く）
        sldnum_style(tree, "8C8C8C")
        return
    left = {"tag": Inches(1.75)}.get(b, Inches(0.4))
    right = Inches(1.2)
    algn = "l" if b == "tag" else "ctr"
    text_col = pal["band_text"] if b != "rules" else pal["ink"]
    band = etree.fromstring(
        f'<p:sp {NS}><p:nvSpPr><p:cNvPr id="20" name="まとめの帯"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>'
        f'<p:nvPr><p:ph type="body" sz="quarter" idx="13"/></p:nvPr></p:nvSpPr>'
        f'<p:spPr><a:xfrm><a:off x="{int(left)}" y="{int(BAND_TOP)}"/><a:ext cx="{int(W - left - right)}" cy="{int(H - BAND_TOP)}"/></a:xfrm>'
        f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr>'
        f'<p:txBody><a:bodyPr lIns="91440" rIns="91440" anchor="ctr"><a:normAutofit/></a:bodyPr><a:lstStyle>'
        f'<a:lvl1pPr marL="0" indent="0" algn="{algn}"><a:buNone/><a:defRPr sz="2200" b="1"><a:solidFill><a:srgbClr val="{text_col}"/></a:solidFill></a:defRPr></a:lvl1pPr>'
        f'</a:lstStyle><a:p><a:r><a:rPr lang="ja-JP"/><a:t>このスライドの結論</a:t></a:r></a:p></p:txBody></p:sp>')
    bt = BAND_TOP / 914400
    if b == "tag":
        deco(tree, [("まとめの地", 0, bt, 13.333, 7.5 - bt, "band_bg"), ("まとめの上の線", 0, bt, 13.333, 0.03, "accent")], pal, 22)
        # 札の文字は、白と主色のうち差し色の地で明暗差の大きいほう（山吹・オレンジの地に白では 2.0〜3.0:1 で読みにくかった）
        tree.append(label(30, "まとめの札 {accent}", Inches(0.45), BAND_TOP + Inches(0.17), Inches(1.2), Inches(0.42), pal["accent"], "まとめ",
                          text_color=tag_text(pal)))
    elif b == "rules":
        deco(tree, [("まとめの上の線", 0.45, bt, 12.43, 0.03, "accent"), ("まとめの下の線", 0.45, 7.4, 12.43, 0.03, "accent")], pal, 22)
    else:   # solid
        deco(tree, [("まとめの地", 0, bt, 13.333, 7.5 - bt, "band_bg")], pal, 22)
    tree.append(band)
    # ページ番号は帯の上にあるので、塗った帯（solid・tag）では帯の文字の色に。灰色のままだと淡い帯（上の帯の構造）で
    # 明暗差が 2.9:1 に落ちていた（check_layout の構造の検査で見つけた）。線だけの帯（rules）は白地なので灰色
    sldnum_style(tree, pal["band_text"] if b in ("solid", "tag") else "8C8C8C")


def cover_layout(lay, st, pal):
    lay._element.set("showMasterSp", "0")
    tree = lay.shapes._spTree
    deco(tree, st["cover"], pal, 30)
    # 表紙のページ番号（12.2〜13.15 in・6.98〜7.34 in）が濃い帯の上に来る構造では白に。テーマの既定の灰色のままだと、
    # 主色の帯の上で明暗差 2.6:1 になり読めなかった（結論タイトル・章のナビ・上の帯の表紙）
    under = [role for name, x, y, w, h, role in st["cover"] if x < 13.15 and x + w > 12.2 and y < 7.34 and y + h > 6.98]
    sldnum_style(tree, "FFFFFF" if under and under[-1] == "main" else "8C8C8C")
    for sp in list(tree.iterchildren(qn("p:sp"))):
        typ = ph_type(sp)
        if typ and typ[0] == "ctrTitle":
            set_xfrm(sp, Inches(1.0), Inches(2.3), Inches(11.33), Inches(1.6))
        elif typ and typ[0] == "subTitle":
            set_xfrm(sp, Inches(1.0), Inches(4.1), Inches(11.33), Inches(1.0))


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent
    out.mkdir(parents=True, exist_ok=True)
    for f in out.glob("テンプレート*.pptx"):
        n = f.stem[len("テンプレート"):]
        if not n.isdigit() or int(n) > len(STRUCTURES):
            f.unlink()
            f.with_suffix(".json").unlink(missing_ok=True)
    for k, st in enumerate(STRUCTURES, 1):
        build(st, out / f"テンプレート{k}.pptx")
        print(f"wrote テンプレート{k}.pptx（{st['label']}、標準の色 {st['palette']}）")
    (out / "配色.json").write_text(json.dumps({n: dict(p, colors=colors_of(p)) for n, p in PALETTES.items()},
                                              ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote 配色.json（{len(PALETTES)} 色）")


if __name__ == "__main__":
    main()
