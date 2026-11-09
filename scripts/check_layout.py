"""render_check.ps1 が書いた shapes.json（PowerPoint実描画の座標）を検査する。

    python check_layout.py render/shapes.json [deck.pptx] [--template 自分のテンプレート.pptx]

検出するもの（ERROR は必ず直す、WARN は画像を見て判断）:
  ERROR  スライド外へのはみ出し / 青帯への侵入 / 要素どうしの重なり / タイトル・青帯まとめの折り返し
         本文と図・表の間隔が狭い（横に並ぶ本文の右端と図の左端が 0.4 in 未満）
  WARN   要素の間隔が詰まりすぎ / 左右の余白不足 / 図形内テキストの自動折り返し
         本文の文字量が目安を超えている（180字超 または 10行超。目安は 100〜150字。210字超・12行超は「多すぎる」）
         1行が長い（図・表の横では全角22字超（目安18〜20字）、図がなければ25字超）
         ※ 確認問題・解答・やり取り・添削のスライド（●見出しで判定）と、表紙・区切り（●見出しが無い）には文字量と行長の目安を当てない
         図を縮小して置いている（描いた幅より置いた幅が 5% 以上小さい → 図の文字が目安より小さくなる）
         下が空いている（本文の最下端が y 4.5 in より上で、図も表もない → 2枚を1枚にまとめるか、行間を広げて縦に配分）
         図が無い（●見出しのある本文のスライドに、図・表・大きな数字・比較のどれも無い）
         図が小さい（図の描いてある範囲＝画像の白でない部分の外枠と図形の合計が、スライドの 8% 未満）
         図の下が空いている（横に置いた図の下端（注記を含む）から帯までが 2.5 in より空いている）
         ※ 枠を大きく置いても、中の絵が小さい・まばらなら小さいと数える（過去の講座で、幅5inの枠に細い線1本の図が続き、
           どの検査も通ったのに下半分が空いて見えた反省）

構造（テンプレート）の形に合わせた検査（デッキの pptx のレイアウトから構造を見分ける。下の「テンプレートの形」の節）:
  ERROR  本文・図が本文の場所からはみ出す（左は本文・見出しの左端、右はページの余白 0.4 in、下は area.bottom。図は描いてある範囲で測る）
         上の見出しの領域（タイトルの枠・上の線や帯・結論の一文の行）にかかる / 飾り（左の細い帯・下の帯の線や地）に重なる
         柱からはみ出す文（柱の中で始まり text_right を越える） / 図が柱の縁をまたぐ / 表紙の題が柱の縁をまたぐ
         タイトルが枠に収まらない / 結論の一文が2行・右にはみ出す / 柱の結論の線が●見出しにかかる / 上の見出しの領域が本文の上端を越える
         ページ番号に重なる / テンプレートそのものの寸法の食い違い（タイトルの枠の高さ・結論の一文の行と線・帯と本文の下端など）
  WARN   図が柱の中にある / ページ番号の文字が下の帯の色に埋もれる（明暗差 3:1 未満）

最後に、スライドごとの一覧（字数・行数・最長行・図との間隔・図の縮尺）を必ず出す。
**ERROR 0 は「収まっている」という意味でしかない。** 一覧の値を目安（100〜150字・図の横は1行20字・間隔 0.4 in 以上・縮尺 1.0）に
寄せるところまでが描画確認（過去の質問回答デッキで、文章調・1行23〜26字のまま上限に収まるのを合格扱いにした反省）。

図の注目点に重ねる輪（zemi.py の s.oval、名前「注目の輪」）は図と重なるのが役目なので、重なり検査から外す。

文字量は「本文のテキストボックス」（18pt以上。●見出し・タイトル・青帯・表のセル・小さな注記は除く）で数える。
図の縮尺は pptx を python-pptx で開き、画像のピクセル数と dpi から「描いた幅」を出して「置いた幅」と比べる
（dpi が 100 未満の画像＝教科書の切り出しなどは比べない）。
"""
import json
import re
import sys
from itertools import combinations
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):  # cp932 の端末でも 𝑑 などの数式文字で落ちないように
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PT = 72.0
BAND_TOP = 487.0        # 青帯の上端 (pt)
MARGIN = 0.25 * PT
TEXT_TARGET_CHARS = 180  # これを超えたら「目安超え」（目安は100〜150字。輪読・論文紹介の実際のデッキの実測：中央値 120字前後、多い1割が170字超）
TEXT_TARGET_LINES = 10   # これを超えたら「目安超え」
TEXT_MAX_CHARS = 210     # 本文の字数の上限（実測の最大 約210字）
TEXT_MIN_CHARS = 70      # 本文の枚で、これより少なければ「本文が少ない」（見本の中央値は 90〜100字。1行だけの枚が出た）
TEXT_MIN_CHARS_FIG = 50  # 図が面積の2割以上の枚（図が主役）の下限
TEXT_FULL_CHARS = 100    # 目安（100〜150字）の下端。これより少ない枚には、行数だけで「目安超え」を出さない（短い行が並ぶと行数で削らせていた）
TEXT_MEDIAN_MIN = 100    # 本文の枚の中身の字数の中央値の下限（実際のデッキは 120字前後。Codex の試作は 66字で、全体に薄かった）
LO_GAP_SHIFT = 4.0      # LibreOffice の描画で、縦に並ぶ文字どうしの間隔に足す分（pt）。PowerPoint との差の実測の最小
BRIEF = False            # --brief：直す所（ERROR・WARN と「←」の行）だけを出す。make_deck.py が使う（会話を短く保つ）
TEXT_MAX_LINES = 12      # 本文の行数の上限
LINE_MAX_BESIDE_FIG = 22  # 図・表の横にある本文の1行の長さ（全角。目安は18〜20字、これを超えたら WARN）
LINE_MAX = 25            # 図がないときの1行の長さ
FIG_GAP_MIN = 0.4 * PT   # 本文の右端と図の左端の間隔の下限
FIG_GAP_MIN_LO = 0.25 * PT  # LibreOffice で描いたとき。文字の範囲を PowerPoint より広く測る（同じ2つのデッキを両方で描いて、
                             # 文字の幅は中央値で +8〜17pt、最大 +65pt。以前は「狭く測る」として 0.5 in にしていて、PowerPoint で通るデッキに ERROR が出ていた）
LO_BOTTOM_TOL = 6.0       # LibreOffice は文字の高さを PowerPoint より約6pt 高く測る（同じ実測。中央値 +6pt）。下端の判定に足す分（pt）
FIG_GAP_BELOW_MIN = 0.3 * PT  # 本文の下端と、その下に置いた図・表の上端の間隔の下限
PIC_SCALE_MIN = 0.95     # 置いた幅／描いた幅 がこれ未満なら「縮小して置いている」
EMPTY_BOTTOM = 4.5 * PT  # 本文の最下端がここより上で図も表もなければ「下が空いている」
FIG_MIN_H = 1.0 * PT     # これより低い画像は数式の画像とみなし、図に数えない
UNDERLINE_MAX = 2         # 1枚の下線の数の上限（下線は聞き手に指してほしい語だけ。ラベルと問いの見出しは太字）
FIG_AREA_MIN = 0.08      # 図の描いてある範囲がスライドの面積のこの割合より小さければ「図が小さい」（見本は 8〜25%）
FIG_EMPTY_BELOW = 2.5 * PT  # 横に置いた図の下端から帯の上端までがこれより空いていれば「図の下が空いている」
INK_WHITE = 235          # 画像の明るさ（0〜255）がこれ未満の画素を「描いてある」とみなす
MSO_AUTOSHAPE, MSO_GROUP, MSO_PICTURE, MSO_TEXTBOX, MSO_TABLE = 1, 6, 13, 17, 19
PH_TITLE, PH_BODY, PH_SLDNUM, PH_CENTER_TITLE = 1, 2, 13, 3


def rect_of(s):
    if s.get("text") and s.get("tw") is not None and s["tw"] > 0:
        return (s["tl"], s["tt"], s["tl"] + s["tw"], s["tt"] + s["th"])
    return (s["left"], s["top"], s["left"] + s["width"], s["top"] + s["height"])


CONTENT_SKIP = ("見出し", "結論の一文", "結論の線", "章のナビ", "青帯",
                "表の見出し", "表の行ラベル", "表のセル")   # 表の文字は数えない（短い語が並ぶだけで字数が増え、薄い枚が通っていた）


def content_chars(items):
    """本文・囲み・箱など、中身の文字（16pt 以上。タイトル・結論の一文・表・図の注記・ページ番号は除く）の字数。"""
    return sum(len(re.sub(r"\s", "", s.get("text") or "")) for s in items
               if s.get("ph") is None and s.get("text") and s.get("name") not in CONTENT_SKIP and (s.get("size") or 0) >= 16)


def rect_area(s):
    r = rect_of(s)
    return max(0.0, r[2] - r[0]) * max(0.0, r[3] - r[1])


def inter(a, b):
    w = min(a[2], b[2]) - max(a[0], b[0])
    h = min(a[3], b[3]) - max(a[1], b[1])
    return (w, h) if w > 0 and h > 0 else (0, 0)


def label(s):
    t = (s.get("text") or "").replace("\r", " ").replace("\n", " ").strip()
    return f"{s['name']}「{t[:18]}」" if t else s["name"]


def is_ring(s):
    """図の上に重ねる注目の輪（s.oval）。重なりは意図したものなので検査しない。"""
    return "注目" in s["name"] or s["name"].startswith(("Oval", "楕円"))


try:
    from structures import TEXT_SHAPE_NAMES
except ImportError:   # 単体で写して使うとき
    TEXT_SHAPE_NAMES = set()
LABEL_NAMES = {"並べた図のラベル", "並べた図の値", "前後の値", "区切り", "結論の一文", "章のナビ"}   # 結論の副題・柱の結論・章のナビも本文に数えない   # 図に付くラベル・数値（本文の字数に数えない）
BODY_SHAPE_NAMES = {"場合分け"}                                    # 図形の中の文字だが本文に数えるもの


def is_figure(s):
    """図・表に数える図形（画像は高さ1in以上、グループ、表、矢印と輪以外の図形）。本文の形の部品の囲み（場合分け・結論の囲み）は数えない。"""
    if s.get("ph") is not None or s.get("name") in TEXT_SHAPE_NAMES or s.get("name") in ("区切りの地", "章のナビ"):
        return False
    if s["type"] == MSO_PICTURE:
        return s["height"] >= FIG_MIN_H
    if s["type"] == MSO_AUTOSHAPE:
        return not (is_ring(s) or "矢印" in s["name"] or "Arrow" in s["name"])
    return s["type"] in (MSO_GROUP, MSO_TABLE)


def is_body(s):
    """本文のテキストボックス（18pt以上。注記・表のセル・プレースホルダは除く）。"""
    return ((s.get("type") == MSO_TEXTBOX or s.get("name") in BODY_SHAPE_NAMES) and s.get("ph") is None and bool(s.get("text"))
            and s.get("name") not in ("見出し",) and s.get("name") not in LABEL_NAMES
            and (s.get("size") or 20) >= 17.5 and not is_ring(s))   # 図に重ねる注記（s.note）は本文に数えない


def paragraphs(s):
    for para in s["text"].replace("\n", "\r").split("\r"):
        t = para.replace(" ", "").replace("　", "").replace("\t", "")
        if t and not t.startswith("●"):
            yield t


def is_qa_slide(items):
    """確認問題・解答・実際のやり取りのスライド（●見出しで判定）。文字量と行の長さの目安は当てない（要素を削らない）。"""
    for s in items:
        t = (s.get("text") or "").strip()
        if (s.get("name") == "見出し" or t.startswith("●")) and any(k in t for k in ("問題", "解答", "やり取り", "添削", "想定質問")):
            return True
    return False


def is_cover_slide(items):
    """表紙・区切り（論文の表紙など）のスライド：●見出しが無い。題名・著者・書誌は本文ではないので、文字量・行長・文体の目安を当てない
    （論文の図を CC BY で使うときは、表紙に雑誌・DOI を書く必要があり、本文として数えると WARN になっていた）。"""
    return not any(s.get("name") == "見出し" or (s.get("text") or "").strip().startswith("●") for s in items)


def body_amount(items):
    """本文テキストボックスの字数（空白を除く）、行数（空でない段落）、最長の行の字数。"""
    chars = lines = longest = 0
    for s in items:
        if not is_body(s):
            continue
        for t in paragraphs(s):
            chars += len(t)
            lines += 1
            longest = max(longest, len(t))
    return chars, lines, longest


SENTENCE_END = re.compile(r"(ます|です|する|しない|できる|できない|ない|いる|ある|れる|られる|なる|える|める|った|だ|。)$")


def sentence_lines(items):
    """文章調の行（文末が動詞・助動詞・「。」で終わる本文の行）。スライドの本文は体言止め・短い言い切りにする（style-guide 2節）。
    過去の質問回答デッキが「〜できない」「〜でいられる」の文章調で書かれ、読みにくいと指摘された反省。"""
    out = []
    for s in items:
        if not is_body(s):
            continue
        for t in paragraphs(s):
            u = t.rstrip("）」』)]")
            if SENTENCE_END.search(u):
                out.append(t)
    return out


# 動詞の終止形・「〜にくい／〜やすい」で終わる行（SENTENCE_END に当たらないもの）。文章調ほど強くはないが、名詞句にできることが多い。
# 過去の論文紹介で「進む」「伸びる」「ずれる」「抜ける」「上げる」「当たりにくい」の8行を見逃し、完成後のレビューで指摘された
VERB_END = re.compile(r"(にくい|やすい|[ぁ-んァ-ヶ一-龥][うくぐすつぬぶむる])$")


def verb_lines(items):
    out = []
    for s in items:
        if not is_body(s):
            continue
        for t in paragraphs(s):
            u = t.rstrip("）」』)]")
            if not SENTENCE_END.search(u) and VERB_END.search(u):
                out.append(t)
    return out


def shape_rect(s):
    """図形そのものの枠（表のセルや箱は、中の文字の枠ではなく箱で測る）。"""
    return (s["left"], s["top"], s["left"] + s["width"], s["top"] + s["height"])


def below_gap(text, fig):
    """fig が text の下にあり、横に重なる範囲があるか。あれば縦の間隔 (pt) を返す。"""
    rt, rf = rect_of(text), shape_rect(fig)
    if rf[1] < rt[3] - 2 or min(rt[2], rf[2]) - max(rt[0], rf[0]) <= 0:
        return None
    return rf[1] - rt[3]


def beside(text, fig):
    """fig が text の右にあり、縦に重なる範囲があるか。あれば横の間隔 (pt) を返す（負は重なり）。
    fig は箱で測る（表のセルを文字の枠で測ると、セルの左端より内側・文字の高さだけになり、
    質問の要旨の行がセルに接していても見逃した。過去の質問回答デッキ）。"""
    rt, rf = rect_of(text), shape_rect(fig)
    if rf[0] <= rt[0]:
        return None
    if min(rt[3], rf[3]) - max(rt[1], rf[1]) <= 0:
        return None
    return rf[0] - rt[2]


def picture_scales(pptx_path, shapes):
    """スライド番号 → {図形名: (置いた幅in, 描いた幅in, 縮尺)}。python-pptx か pptx が無ければ空。"""
    out = {}
    try:
        from pptx import Presentation
        from pptx.util import Emu
    except ImportError:
        return out
    if not pptx_path or not Path(pptx_path).exists():
        return out
    try:
        prs = Presentation(pptx_path)
    except Exception:
        return out
    for i, slide in enumerate(prs.slides, 1):
        for sh in slide.shapes:
            if sh.shape_type != MSO_PICTURE or not hasattr(sh, "image"):
                continue
            try:
                px_w = sh.image.size[0]
                dpi = (sh.image.dpi or (72, 72))[0]
            except Exception:
                continue
            if not dpi or dpi < 100:      # 教科書の切り出しなど、描いた大きさの決まっていない画像は比べない
                continue
            placed = Emu(sh.width).inches
            drawn = px_w / dpi
            out.setdefault(i, {})[sh.name] = (placed, drawn, placed / drawn if drawn else 1.0)
    return out


def underlines(pptx_path):
    """スライド番号 → [下線の付いた文字（続いている下線の文字はまとめて1か所）]。pptx が読めなければ空。"""
    out = {}
    try:
        from pptx import Presentation
        prs = Presentation(str(pptx_path))
    except Exception:
        return out
    for i, sl in enumerate(prs.slides, 1):
        found = []
        for sh in sl.shapes:
            if not getattr(sh, "has_text_frame", False) or not sh.has_text_frame:
                continue
            for para in sh.text_frame.paragraphs:
                cur = ""
                for r in para.runs:
                    if r.font.underline:
                        cur += r.text
                    elif cur.strip():
                        found.append(cur.strip())
                        cur = ""
                if cur.strip():
                    found.append(cur.strip())
        if found:
            out[i] = found
    return out


def quiz_problems(shapes, n_slides):
    """確認問題・解答の枚の決まり（講座：6問を3問ずつ、確認問題2枚・解答2枚）から外れた所。確認問題の枚が無いデッキ（発表）は見ない。"""
    try:
        from structures import QUIZ_PER_SLIDE, QUIZ_SLIDES, QUIZ_TOTAL, quiz_ids
    except ImportError:
        return []
    q, a = {}, {}
    for i in range(1, n_slides + 1):
        items = [s for s in shapes if s["slide"] == i]
        head = " ".join((s.get("text") or "") for s in items if s.get("name") == "見出し" or (s.get("text") or "").strip().startswith("●"))
        if "確認問題" not in head and "解答" not in head:
            continue
        lines = [t for s in items if s.get("ph") is None and s.get("name") != "見出し" and s.get("text")
                 for t in s["text"].replace("\n", "\r").split("\r")]
        (q if "確認問題" in head else a)[i] = quiz_ids(lines)
    if not q:
        return []
    out = []
    for what, d in (("確認問題", q), ("解答", a)):
        if len(d) != QUIZ_SLIDES:
            out.append(f"{what}の枚が {len(d)}枚（{'・'.join(map(str, d)) or 'なし'}枚目）。{QUIZ_TOTAL}問を {QUIZ_PER_SLIDE}問ずつ、{what} {QUIZ_SLIDES}枚にまとめる")
        bad = [f"{i}枚目 {len(ids)}問" for i, ids in d.items() if len(ids) != QUIZ_PER_SLIDE]
        if bad:
            out.append(f"{what}の枚の問題の数が {QUIZ_PER_SLIDE}問でない：{'・'.join(bad)}（番号「N-1」を行の頭に置いて1枚に {QUIZ_PER_SLIDE}問）")
        n = len({x for ids in d.values() for x in ids})
        if n != QUIZ_TOTAL:
            out.append(f"{what}の問題が合計 {n}問（{QUIZ_TOTAL}問ちょうどにする）")
    return out


def over_target(chars: int, lines: int) -> bool:
    """文字量が目安を超えたか（180字超か10行超）。目安の下端（100字）より少ない枚は、行数だけでは超えにしない。"""
    return chars > TEXT_TARGET_CHARS or (lines > TEXT_TARGET_LINES and chars >= TEXT_FULL_CHARS)


def is_red(hexs: str) -> bool:
    """赤字の色か（同梱の配色の強調色 FF0000・C00000・C8102E・B23A48 などはどれも当たる。青・灰・本文の色は当たらない）。"""
    try:
        r, g, b = int(hexs[0:2], 16), int(hexs[2:4], 16), int(hexs[4:6], 16)
    except (TypeError, ValueError):
        return False
    return r >= 0x90 and r - max(g, b) >= 0x60


def red_counts(pptx_path):
    """スライド番号 → 赤字の箇所の数（文字のある赤い run。グループの中も数える）。pptx が読めなければ None。"""
    try:
        from pptx import Presentation
        prs = Presentation(str(pptx_path))
    except Exception:
        return None

    def shapes_of(shs):
        for sh in shs:
            yield sh
            if getattr(sh, "shape_type", None) == 6:   # グループ
                yield from shapes_of(sh.shapes)

    out = {}
    for i, sl in enumerate(prs.slides, 1):
        n = 0
        for sh in shapes_of(sl.shapes):
            if not getattr(sh, "has_text_frame", False) or not sh.has_text_frame:
                continue
            for para in sh.text_frame.paragraphs:
                for r in para.runs:
                    try:
                        rgb = r.font.color.rgb if r.font.color and r.font.color.type is not None else None
                    except AttributeError:
                        rgb = None
                    n += bool(rgb is not None and r.text.strip() and is_red(str(rgb)))
        out[i] = n
    return out


def plain_slides(pptx_path):
    """帯も●も無い枚（結論の無い役割の枚：確認問題・解答・目次など）の番号。本文の量の目安を当てない。"""
    try:
        from pptx import Presentation
        from zemi import PLAIN_LAYOUT_NAME, PLAIN_MARK
        prs = Presentation(str(pptx_path))
    except Exception:
        return set()
    return {i for i, sl in enumerate(prs.slides, 1) if sl.name == PLAIN_MARK or sl.slide_layout.name == PLAIN_LAYOUT_NAME}


def picture_ink(pptx_path):
    """スライド番号 → [(図形名, 左pt, 上pt, 描いてある範囲の上pt, 下pt, 面積pt², 左pt, 右pt)]。画像の白でない画素の外枠を、置いた大きさで測る。
    python-pptx・Pillow・pptx が無ければ空（そのときは枠の大きさで測る）。"""
    out = {}
    try:
        import io
        from PIL import Image
        from pptx import Presentation
    except ImportError:
        return out
    if not pptx_path or not Path(pptx_path).exists():
        return out
    try:
        prs = Presentation(pptx_path)
    except Exception:
        return out
    emu = 12700.0   # 1pt
    for i, slide in enumerate(prs.slides, 1):
        for sh in slide.shapes:
            if sh.shape_type != MSO_PICTURE or not hasattr(sh, "image") or sh.height / emu < FIG_MIN_H:
                continue
            try:
                im = Image.open(io.BytesIO(sh.image.blob))
                if im.mode in ("RGBA", "LA", "P"):
                    im = im.convert("RGBA")
                    bg = Image.new("RGBA", im.size, "white")
                    bg.alpha_composite(im)
                    im = bg
                im = im.convert("L")
                bb = im.point(lambda v: 255 if v < INK_WHITE else 0).getbbox()
            except Exception:
                continue
            w, h = im.size
            left, top, pw, ph = sh.left / emu, sh.top / emu, sh.width / emu, sh.height / emu
            if not bb:
                out.setdefault(i, []).append((sh.name, left, top, top, top, 0.0, left, left))
                continue
            it, ib = top + bb[1] / h * ph, top + bb[3] / h * ph
            il, ir = left + bb[0] / w * pw, left + bb[2] / w * pw
            area = (bb[2] - bb[0]) / w * pw * (bb[3] - bb[1]) / h * ph
            out.setdefault(i, []).append((sh.name, left, top, it, ib, area, il, ir))
    return out


def ink_of(s, inks):
    """shapes.json の画像 s に当たる描いてある範囲 (上pt, 下pt, 面積pt²)。見つからなければ枠で。"""
    for name, left, top, it, ib, area, *_ in inks:
        if name == s["name"] and abs(left - s["left"]) < 3 and abs(top - s["top"]) < 3:
            return it, ib, area
    return s["top"], s["top"] + s["height"], s["width"] * s["height"]


def visible_rect(s, inks):
    """見えている範囲：画像は描いてある範囲（白い余白を除く）、文字は文字の範囲、ほかは枠。
    図の PNG は周りに白い余白を持つので、枠で測ると、描いた線は余白の内側なのにページの余白に出たと数えていた（講座の見本の第8枚）。"""
    if s.get("type") == MSO_PICTURE:
        for name, left, top, it, ib, area, il, ir in inks:
            if name == s["name"] and abs(left - s["left"]) < 3 and abs(top - s["top"]) < 3:
                return (il, it, ir, ib) if ir > il and ib > it else rect_of(s)
    return rect_of(s)


NOBAND_BOTTOM = 7.5 * PT - 0.45 * PT   # 下の帯の無い構造で、本文・図の下端の限り（ページ番号の上）
EMPTY_BELOW_NOBAND = 1.6 * PT          # 帯の無い枚で、本文の下端からその限りまでがこれより空いていたら「下が空いている」


def band_slides(pptx_path):
    """下の帯のある枚の番号の集合（レイアウトに下の帯の枠がある枚）。pptx が読めなければ None（全部の枚に帯があるとみなす）。
    帯の無い構造（結論ヘッダー・結論タイトルなど）の枚では、帯にかかる検査の代わりに、ページの下の余白で見る。"""
    try:
        from pptx import Presentation
        from zemi import band_placeholder_idx
        prs = Presentation(pptx_path)
    except Exception:
        return None
    out = set()
    for i, sl in enumerate(prs.slides, 1):
        if band_placeholder_idx(sl.slide_layout, prs.slide_height) is not None or any(sh.name == "青帯" for sh in sl.shapes):
            out.add(i)
    return out


def stale_slides(pptx_path, data, shapes):
    """描画結果（shapes.json）が今の pptx と食い違うスライド番号の一覧。pptx の文字が shapes.json に無ければ古い描画。
    OneDrive 上の pptx を PowerPoint がクラウドの古い版で開き、直したはずの指摘が残って見えた反省（過去の論文紹介）。"""
    try:
        from pptx import Presentation
        prs = Presentation(pptx_path)
    except Exception:
        return []
    norm = lambda t: re.sub(r"\s+", "", t or "")  # noqa: E731
    if len(prs.slides) != data["slides"]:
        return list(range(1, max(len(prs.slides), data["slides"]) + 1))
    out = []
    for i, slide in enumerate(prs.slides, 1):
        drawn = {norm(s.get("text")) for s in shapes if s["slide"] == i}
        mine = {norm(sh.text_frame.text) for sh in slide.shapes if sh.has_text_frame}
        if any(len(t) >= 4 and t not in drawn for t in mine):
            out.append(i)
    return out


# ---- テンプレートの形（構造）に合わせた検査 ------------------------------------------------------------
# テンプレートの寸法は、デッキの pptx のレイアウト・マスターから読む（飾りの図形＝名前に {main} などの役割の付いた図形の位置、
# タイトルの枠、ページ番号の枠、下の帯の枠）。shapes.json はスライドの図形しか持たないので、飾りとの重なりはここで初めて見える。
# 本文の場所（area：本文の左右・上下、図の x、柱の文の右端など）はレイアウトに無いので、テンプレートの .json から読む。
# デッキの pptx にはどのテンプレートから作ったかが残らない（保存の題名で上書きされる）ので、同梱のテンプレート
# （assets/templates/テンプレートN.pptx）のレイアウトと、飾りの名前・位置とタイトルの枠を突き合わせて見つける。
# 配色を変えても（recolor）形と位置は変わらないので当たる。自分で足したテンプレートは --template で渡す。
# どれにも当たらなければ、レイアウトから読める飾り・枠だけで検査する（本文の場所の検査は省き、その旨を出す）。
EMU_PT = 12700.0
TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "assets" / "templates"
EDGE_TOL = 0.1 * PT          # 本文の場所の左・下からの許し（部品の内側の余白・描画の誤差の分）
RIGHT_TOL = 0.03 * PT        # 右の許し（右はページの余白 0.4 in そのもので見るので、描画の誤差の分だけ）
PAGE_MARGIN = 0.4 * PT       # 四辺の余白の目安（make_templates.py の構造はこれに合わせてある）
TOUCH = 2.0                  # 飾り・見出しの領域との重なりを数える下限 (pt)。接しているだけは数えない
NUM_CONTRAST_MIN = 3.0       # ページ番号（12pt の灰色）と下の地の明暗差の下限
HEADER_SHAPES = ("見出し", "結論の一文", "結論の線", "章のナビ")   # zemi.py が上の見出しの領域に置く図形（Deck.HEADER_NAMES と同じ）
NAV_BOTTOM = 0.46 * PT       # 章のナビの行の下端（zemi.py の _draw_nav：y 0.08 + 高さ 0.38 in）
try:
    from zemi import BOX_TOP as _BOX_TOP, MESSAGE_POS as _MESSAGE_POS
except ImportError:   # 単体で写して使うとき
    _BOX_TOP, _MESSAGE_POS = 6.25, (0.6, 0.62)
BOX_TOP_PT = _BOX_TOP * PT


def _emu_rect(sh):
    try:
        l, t, w, h = sh.left, sh.top, sh.width, sh.height
    except Exception:
        return None
    if None in (l, t, w, h):
        return None
    return (l / EMU_PT, t / EMU_PT, (l + w) / EMU_PT, (t + h) / EMU_PT)


def _fill_rgb(sh):
    try:
        if sh.fill.type == 1:   # MSO_FILL.SOLID
            return str(sh.fill.fore_color.rgb)
    except Exception:
        pass
    return None


def _decorations(part):
    """マスター・レイアウトの飾りの図形（プレースホルダ以外）。名前の {role} は外して、役割として持つ。"""
    out = []
    for sh in part.shapes:
        if sh.is_placeholder:
            continue
        r = _emu_rect(sh)
        if r is None:
            continue
        m = re.search(r"\{(\w+)\}", sh.name or "")
        out.append({"name": re.sub(r"\s*\{\w+\}", "", sh.name or "").strip() or "飾り",
                    "role": m.group(1) if m else None, "rect": r, "fill": _fill_rgb(sh)})
    return out


def _srgb(el, path):
    try:
        v = el.xpath(path)
    except Exception:
        return None
    return str(v[0]) if v else None


def layout_geometry(layout, slide_h):
    """レイアウト（と、表示するならマスター）の形：飾り・タイトルの枠・ページ番号の枠と文字色・下の帯の枠・表紙かどうか（pt）。"""
    decos = _decorations(layout)
    if layout._element.get("showMasterSp") != "0":
        decos = _decorations(layout.slide_master) + decos
    g = {"decos": decos, "title": None, "title_size": None, "sldnum": None, "sldnum_color": None, "band": None, "cover": False}
    color_path = "./p:txBody/a:lstStyle/a:lvl1pPr/a:defRPr/a:solidFill/a:srgbClr/@val"
    for ph in layout.placeholders:
        t = int(ph.placeholder_format.type)
        r = _emu_rect(ph)
        if t == PH_TITLE:
            g["title"] = r
        elif t == PH_CENTER_TITLE:
            g["cover"] = True
        elif t == PH_SLDNUM:
            g["sldnum"] = r
            g["sldnum_color"] = _srgb(ph._element, color_path)
        elif t == PH_BODY and r and r[1] * EMU_PT > 0.8 * slide_h:
            g["band"] = r
    if g["sldnum"] and not g["sldnum_color"]:   # レイアウトで色を決めていなければマスターの枠から
        for ph in layout.slide_master.placeholders:
            if int(ph.placeholder_format.type) == PH_SLDNUM:
                g["sldnum_color"] = _srgb(ph._element, color_path)
    sz = _srgb(layout.slide_master._element, "./p:txStyles/p:titleStyle/a:lvl1pPr/a:defRPr/@sz")
    g["title_size"] = int(sz) / 100 if sz and sz.isdigit() else None
    return g


def _signature(g):
    """テンプレートを見分ける指紋：飾りの名前と位置、タイトルの枠（pt に丸める）。色は入れない（配色を変えても当たるように）。"""
    rr = lambda r: tuple(round(v) for v in r) if r else None  # noqa: E731
    return (tuple(sorted((d["name"], rr(d["rect"])) for d in g["decos"])), rr(g["title"]))


_SIGNATURES = {}


def _template_signatures():
    out = []
    for p in sorted(TEMPLATE_DIR.glob("テンプレート*.pptx")):
        if p not in _SIGNATURES:
            try:
                from pptx import Presentation
                prs = Presentation(str(p))
                _SIGNATURES[p] = [_signature(layout_geometry(l, prs.slide_height)) for l in prs.slide_layouts]
            except Exception:
                _SIGNATURES[p] = []
        out.append((p, _SIGNATURES[p]))
    return out


def area_pt(style):
    """テンプレートの .json の本文の場所（in）を pt に。既定の補い方は zemi.body_area と同じ。"""
    try:
        from zemi import body_area
        a = body_area(style)
    except ImportError:
        a = dict(style.get("area", {}))
    out = {}
    for k, v in a.items():
        out[k] = tuple(x * PT for x in v) if isinstance(v, (list, tuple)) else v * PT
    return out


def template_geometry(pptx_path, template=None):
    """デッキの形。{"slides": {番号: レイアウトの形}, "style": テンプレートの .json か None, "name": テンプレートの名前か None,
    "area": 本文の場所 (pt) か None, "content": 本文のレイアウトの形}。pptx が読めなければ None。"""
    try:
        from pptx import Presentation
        prs = Presentation(pptx_path)
    except Exception:
        return None
    geoms, by_layout = {}, {}
    for i, sl in enumerate(prs.slides, 1):
        lay = sl.slide_layout
        key = str(lay.part.partname)
        if key not in by_layout:
            by_layout[key] = layout_geometry(lay, prs.slide_height)
        geoms[i] = by_layout[key]
    content = next((g for g in geoms.values() if g["title"] and not g["cover"]), None)
    style = name = None
    if template:
        side = Path(template).with_suffix(".json")
        name = Path(template).stem
        style = json.loads(side.read_text(encoding="utf-8")) if side.exists() else None
    elif content:
        sig = _signature(content)
        for p, sigs in _template_signatures():
            if sig in sigs and p.with_suffix(".json").exists():
                style, name = json.loads(p.with_suffix(".json").read_text(encoding="utf-8")), p.stem
                break
    return {"slides": geoms, "style": style, "name": name, "content": content,
            "area": area_pt(style) if style is not None else None}


def is_region(d, W, H):
    """中に文を置く大きな地（左の柱）。中に置くのはよく、縁をまたぐのがいけない。"""
    w, h = d["rect"][2] - d["rect"][0], d["rect"][3] - d["rect"][1]
    return "柱" in d["name"] or (h >= 0.9 * H and w >= 0.2 * W)


def deco_kinds(g, area, W, H):
    """飾りを 柱（region）・横の帯（side：全高の細い帯）・上（top：本文の上端より上）・下（bottom）に分ける。"""
    top_lim = area["top"] if area else 0.3 * H
    regions, sides, tops, bottoms = [], [], [], []
    for d in g["decos"]:
        r = d["rect"]
        if is_region(d, W, H):
            regions.append(d)
        elif r[3] - r[1] >= 0.5 * H:
            sides.append(d)
        elif r[3] <= top_lim + TOUCH:
            tops.append(d)
        else:
            bottoms.append(d)
    return regions, sides, tops, bottoms


def frame_of(g, area, W):
    """本文の場所の左右 (pt)。左は本文・見出し・結論の左端の一番左。右は本文の右端・タイトルの枠や横に長い線の右端・
    ページの右の余白 0.4 in（研究発表のデザインの手引き）の一番右。同梱の構造は、図を fig_x から描いた幅のまま置くと
    本文の右端 area.right を少し越え、タイトルの枠・線の右端（12.75〜12.9 in）のあたりで終わる作りなので、右は余白で見る。"""
    left = min([area["x"], area["heading"][0]] + [area[k][0] for k in ("message", "lead", "column") if k in area])
    rights = [area["right"], W - PAGE_MARGIN]
    if g["title"] and g["title"][0] < W / 2:
        rights.append(g["title"][2])
    rights += [d["rect"][2] for d in g["decos"] if d["rect"][2] - d["rect"][0] > W / 2 and d["rect"][2] < W - 1]
    return left, max(rights)


def contrast(c1, c2):
    """2色（"RRGGBB"）の明暗差（WCAG の比）。"""
    def lum(c):
        vals = []
        for k in (0, 2, 4):
            v = int(c[k:k + 2], 16) / 255
            vals.append(v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4)
        return 0.2126 * vals[0] + 0.7152 * vals[1] + 0.0722 * vals[2]
    a, b = sorted((lum(c1), lum(c2)), reverse=True)
    return (a + 0.05) / (b + 0.05)


def _is_mark_heading(s):
    return s.get("name") == "見出し" and (s.get("text") or "").lstrip().startswith(("●", "■"))


def is_message(s):
    """結論の一文（結論ヘッダー・結論タイトル・副題の「見出し」、柱の「結論の一文」）。●見出しは含めない。"""
    return s.get("name") == "結論の一文" or (s.get("name") == "見出し" and not _is_mark_heading(s))


def template_problems(g, style, area, W, H):
    """テンプレートそのものの寸法の食い違い（どの枚にも出るので、描画の前に分かる）。文字の一覧で返す。"""
    out = []
    if not g or not g["title"]:
        return out
    t = g["title"]
    size = g.get("title_size") or 32
    need = size * 1.2 + 0.1 * PT
    if t[3] - t[1] < need - 1:
        out.append(f"タイトルの枠の高さ {(t[3] - t[1]) / PT:.2f} in が {size:.0f}pt の1行（{need / PT:.2f} in）より低い"
                   " → make_templates.py の title の h を上げるか sz を下げる")
    regions, sides, tops, bottoms = deco_kinds(g, area, W, H)
    for d in regions:
        if t[0] < d["rect"][2] - TOUCH < t[2] - TOUCH:
            out.append(f"タイトルの枠が「{d['name']}」の縁をまたぐ → 枠の幅を柱の中に収める")
    for d in sides:
        w, h = inter(t, d["rect"])
        if w > TOUCH and h > TOUCH:
            out.append(f"タイトルの枠が「{d['name']}」に重なる → 枠の x を飾りの右へ")
    if not area:
        return out
    conc = style.get("conclusion", "band")
    top = area["top"]
    slot = {"header": ("message", 28), "title": ("message", 28), "lead": ("lead", 24)}.get(conc)
    if slot:
        pos = area.get(slot[0]) or tuple(v * PT for v in _MESSAGE_POS)
        mb = pos[1] + slot[1] * 1.2 + 0.1 * PT
        below = [d for d in tops if d["rect"][1] >= pos[1] + slot[1] * 0.6 and d["rect"][2] > pos[0]]
        nxt = min([d["rect"][1] for d in below] + [top])
        if mb > nxt + 1:
            what = f"「{min(below, key=lambda d: d['rect'][1])['name']}」" if below and nxt < top else "本文の上端"
            out.append(f"結論の一文の行（y {pos[1] / PT:.2f} in・{slot[1]}pt）の下端 {mb / PT:.2f} in が{what}（{nxt / PT:.2f} in）を超える"
                       " → area の message／lead の y か top を直す")
        if pos[1] < t[3] - 1:
            out.append(f"タイトルの枠（下端 {t[3] / PT:.2f} in）と結論の一文の行（y {pos[1] / PT:.2f} in）が重なる → 枠を低くするか、行を下げる")
    else:
        hb = area["heading"][1] + 24 * 1.2 + 0.1 * PT
        if hb > top + 1:
            out.append(f"●見出しの行の下端 {hb / PT:.2f} in が本文の上端 {top / PT:.2f} in を超える → area の heading の y か top を直す")
        if conc != "column" and area["heading"][1] < t[3] - 1:
            out.append(f"●見出しの行（y {area['heading'][1] / PT:.2f} in）がタイトルの枠（下端 {t[3] / PT:.2f} in）に重なる → heading の y を下げる")
    if conc == "column" and "column" in area:
        cx, cy, cw = area["column"]
        cb = cy + 2 * 20 * 1.2 + 0.1 * PT + 0.1 * PT   # 柱の結論は2行まで（wrap_to）、その下に差し色の線
        if cb > area["heading"][1] + 1:
            out.append(f"柱の結論（2行）と下の線の下端 {cb / PT:.2f} in が●見出しの行（y {area['heading'][1] / PT:.2f} in）を超える"
                       " → area の heading の y を下げる")
    if g["band"]:
        if area["bottom"] > g["band"][1] - 0.05 * PT:
            out.append(f"本文の下端 {area['bottom'] / PT:.2f} in が下の帯（{g['band'][1] / PT:.2f} in）に近すぎる → area の bottom を上げる")
    elif conc == "box":
        if area["bottom"] > BOX_TOP_PT - 0.1 * PT:
            out.append(f"本文の下端 {area['bottom'] / PT:.2f} in が結論の囲み（{BOX_TOP_PT / PT:.2f} in）に近すぎる")
    elif g["sldnum"] and area["bottom"] > g["sldnum"][1] + 1 and area["right"] > g["sldnum"][0]:
        out.append(f"本文の場所（下端 {area['bottom'] / PT:.2f} in・右端 {area['right'] / PT:.2f} in）がページ番号の枠にかかる → bottom を上げる")
    for d in sides:
        if d["rect"][0] < W / 2 and area["x"] < d["rect"][2] + 0.3 * PT:
            out.append(f"本文の左端 {area['x'] / PT:.2f} in が「{d['name']}」（右端 {d['rect'][2] / PT:.2f} in）に近すぎる → area の x を右へ")
    if area["x"] < PAGE_MARGIN or area["right"] > W - PAGE_MARGIN:
        out.append("本文の場所がページの端から 0.4 in の余白に入る（研究発表のデザインの手引き） → area の x・right を内側へ")
    low = max([d["rect"][3] for d in tops] + [0])
    if low > top - 0.1 * PT:
        out.append(f"上の飾りの下端 {low / PT:.2f} in が本文の上端 {top / PT:.2f} in に近すぎる → area の top を下げる")
    if style.get("nav") and t[1] < NAV_BOTTOM:
        out.append(f"タイトルの枠（上端 {t[1] / PT:.2f} in）が章のナビの行（下端 {NAV_BOTTOM / PT:.2f} in）に重なる")
    return out


def template_checks(items, g, area, conclusion, W, H, band_top, inks=(), right_tol=RIGHT_TOL):
    """1枚を、テンプレートの形（飾り・枠・本文の場所）と突き合わせる。(msgs, 左右の ERROR を出した図形の id) を返す。"""
    msgs, edge = [], set()
    if g is None or any(s["name"] == "区切りの地" for s in items):   # 区切りの枚は全面の地なので見ない
        return msgs, edge
    content = bool(g["title"]) and not g["cover"]
    regions, sides, tops, bottoms = deco_kinds(g, area if content else None, W, H)
    shapes = [s for s in items if s.get("ph") is None]
    header = [s for s in shapes if s["name"] in HEADER_SHAPES]
    body = [s for s in shapes if s["name"] not in HEADER_SHAPES and s["name"] != "青帯"
            and not (s["name"] == "結論の囲み" and conclusion == "box" and s["top"] >= BOX_TOP_PT - 4)]   # 下の結論の囲みは結論の置き場
    frame = frame_of(g, area, W) if content and area else None
    title = next((s for s in items if s.get("ph") == PH_TITLE), None)

    def hit(a, b):
        w, h = inter(a, b)
        # 細い飾り（見出しの下の線は 0.02 in = 1.4pt）は、少しでも縦に重なれば数える（2pt の下限では線にかからなかった）
        thin = min(b[2] - b[0], b[3] - b[1]) < 2 * TOUCH
        return w > TOUCH and (h > 0 if thin else h > TOUCH)

    # 1. 本文の場所（左右・下）
    if frame:
        left, right = frame
        for s in body:
            r = visible_rect(s, inks)
            if r[0] < left - EDGE_TOL:
                msgs.append(("ERROR", f"本文の場所より左にはみ出す（左端 {r[0] / PT:.2f} in < {left / PT:.2f} in）: {label(s)}"
                                      f" → 左端を本文の x（{area['x'] / PT:.2f} in。deck.area['x']）にそろえる"))
                edge.add(id(s))
            if r[2] > right + right_tol:
                msgs.append(("ERROR", f"本文の場所より右にはみ出す（右端 {r[2] / PT:.2f} in > {right / PT:.2f} in）: {label(s)}"
                                      f" → 図は x = fig_x（{area['fig_x'] / PT:.2f} in）から描いた幅のまま置き、入らなければ図の幅を描き直す"
                                      "（右の余白 0.4 in を残す）"))
                edge.add(id(s))
            if area["bottom"] + EDGE_TOL < r[3] <= band_top - 2:   # 帯・ページ番号にかかるものは下の検査が出す
                small = s.get("text") and (s.get("size") or 20) < 17.5
                msgs.append(("ERROR", f"本文の場所の下端を超える（下端 {r[3] / PT:.2f} in > {area['bottom'] / PT:.2f} in"
                                      f"{'。結論の囲みの上' if conclusion == 'box' else ''}）: {label(s)}"
                                      + (" → 図の注記なら、図を縦に縮めて注記の分（0.35 in）を空ける（figure_below・full_figure・pair は caption を渡せば空ける）"
                                         if small else " → 行を削るか図を縮める（本文・図の下端は deck.content_bottom）")))

    # 2. 上の見出しの領域：タイトルの枠・上の飾り（線・帯・縦棒）・結論の一文の行に、本文がかからない
    if content:
        zones = []
        if g["title"] and area:   # 構造の分からないテンプレートでは、短いタイトルの右に図を上詰めで置く使い方（title_right_edge）があるので見ない
            zones.append(("タイトルの枠", g["title"], rect_of(title) if title else None))
        zones += [(f"「{d['name']}」", d["rect"], None) for d in tops]
        for s in header:
            if is_message(s) and conclusion in ("title", "header", "lead"):
                r = rect_of(s)
                zones.append(("結論の一文の行", (r[0], r[1], frame[1] if frame else W - MARGIN, r[3]), r))
        for s in body:
            r = visible_rect(s, inks)
            for zname, z, own in zones:
                if hit(r, z) and not (own and hit(r, own)):   # 文字そのものとの重なりは「重なり」の検査が出す
                    low = max(zz[3] for _, zz, _ in zones if zz[2] > r[0] and zz[0] < r[2])
                    msgs.append(("ERROR", f"上の見出しの領域（{zname}）にかかる: {label(s)}"
                                          f" → 上端を {low / PT:.2f} in より下へ（図を上げるのは deck.header_bottom まで）"))
                    break

    # 3. 飾り（左の細い帯・下の帯の線や地）に重ならない。柱は縁をまたがない
    for s in shapes:
        r = rect_of(s)
        for d in sides + bottoms + (tops if s in header else []):
            if hit(r, d["rect"]) and not (d in bottoms and r[3] > band_top - 2):   # 帯にかかるものは下の検査が出す
                what = ("結論の一文が2行になったか大きすぎる → 1行に収まるよう短くする" if is_message(s)
                        else "飾りの外へ移す（本文の場所は deck.area）")
                msgs.append(("ERROR", f"テンプレートの飾り「{d['name']}」に重なる: {label(s)} → {what}"))
                break
    for d in regions if content else []:   # 表紙は下でまとめて見る
        if d["rect"][0] > 1:       # 左端から始まる柱だけ（右の柱の構造は無い）
            continue
        edge_x = d["rect"][2]
        tr = area["text_right"] if content and area and "text_right" in area else edge_x - 0.3 * PT
        fx = area["fig_x"] if content and area else edge_x + 0.45 * PT
        for s in shapes + [s for s in items if s.get("ph") == PH_BODY]:
            r = rect_of(s)
            if r[2] - r[0] <= 0 or r[0] >= edge_x - TOUCH:
                continue
            textual = (bool(s.get("text")) and not is_figure(s)) or (s["type"] == MSO_PICTURE and not is_figure(s))
            if textual:
                if r[2] > tr + 0.05 * PT and r[0] < fx:
                    msgs.append(("ERROR", f"柱からはみ出す文（右端 {r[2] / PT:.2f} in > 柱の文の右端 {tr / PT:.2f} in）: {label(s)}"
                                          f" → 柱の中は1行14字前後（20pt）までに \\n で折るか、文を右の白い所（x {fx / PT:.2f} in から）に置く"))
                    edge.add(id(s))
            elif is_figure(s) or s["type"] == MSO_PICTURE:
                if r[2] > edge_x + TOUCH:
                    msgs.append(("ERROR", f"図が柱の縁（{edge_x / PT:.2f} in）をまたぐ: {label(s)}"
                                          f" → 図は柱の外、x {fx / PT:.2f} in（fig_x）から置く"))
                    edge.add(id(s))
                else:
                    msgs.append(("WARN", f"図が柱の中にある: {label(s)}"
                                         f" → 柱はタイトル・結論・短い要点の場所。図は右の白い所（x {fx / PT:.2f} in から）に大きく"))
    if not content:   # 表紙：題・著者が柱をまたがない（柱の構造の表紙で、中央に置いた題が柱の縁にかかっていた）
        for d in regions:
            if d["rect"][0] > 1:
                continue
            for s in shapes:
                r = rect_of(s)
                if s.get("text") and r[0] < d["rect"][2] - TOUCH < r[2] - TOUCH:
                    msgs.append(("ERROR", f"表紙の文が「{d['name']}」の縁をまたぐ: {label(s)}"
                                          " → 題は柱の右の白い所の中央に（zemi.py の title_slide は柱を避けて置く）"))

    # 4. 高さ：タイトル・結論の一文がそれぞれの場所に収まり、上の見出しの領域が本文の上端より上で終わる
    if content and title and g["title"] and title.get("text") and title["lines"] <= title["paras"]:   # 折り返しは上の検査が出す
        r, slot = rect_of(title), g["title"]
        if r[3] > slot[3] + TOUCH or r[1] < slot[1] - TOUCH:
            msgs.append(("ERROR", f"タイトルが枠（高さ {(slot[3] - slot[1]) / PT:.2f} in）に収まらない（{title['paras']}段落・"
                                  f"{title.get('size') or 0:.0f}pt）: {label(title)} → タイトルを1行に短くする（詳しい内容は結論・見出しへ）"))
    if content:
        for s in header:
            if not is_message(s) or not s.get("text"):
                continue
            r = rect_of(s)
            size = s.get("size") or 28
            if conclusion in ("title", "header", "lead"):
                limit = frame[1] if frame else W - MARGIN
                n = int((limit - r[0]) / size)
                if s["lines"] > 1 or s["paras"] > 1:
                    msgs.append(("ERROR", f"結論の一文が {max(s['lines'], s['paras'])} 行になっている（1行の場所）: {label(s)}"
                                          f" → 全角 {n} 字以内（{size:.0f}pt）に削る。言い足りない分は本文・ノートへ"))
                elif r[2] > limit + EDGE_TOL:
                    msgs.append(("ERROR", f"結論の一文が右にはみ出す（右端 {r[2] / PT:.2f} in > {limit / PT:.2f} in）: {label(s)}"
                                          f" → 全角 {n} 字以内（{size:.0f}pt）に削る"))
        heads = [s for s in header if _is_mark_heading(s)]
        lines_ = [s for s in header if s["name"] == "結論の線"]
        for ln in lines_:
            for h in heads:
                if ln["top"] > h["top"] - TOUCH and ln["left"] < h["left"] + h["width"]:
                    msgs.append(("ERROR", f"柱の結論が長く、下の線が●見出しにかかる: {label(h)}"
                                          " → 結論を柱の幅で2行以内（1行14字前後×2行、20pt）に削る"))
        if area:
            stack = [rect_of(s)[3] for s in header if s["name"] != "章のナビ" and s["top"] < area["top"]]
            if title and title.get("text"):
                stack.append(rect_of(title)[3])
            if stack and max(stack) > area["top"] + TOUCH:
                msgs.append(("ERROR", f"上の見出しの領域が本文の上端を超える（下端 {max(stack) / PT:.2f} in > {area['top'] / PT:.2f} in）"
                                      " → タイトル・結論の一文・見出しを1行ずつに。構造の高さは変えない（本文が下に押される）"))

    # 5. ページ番号：本文・図が重ならない。下の地（帯）の上でも読める色か
    num = next((s for s in items if s.get("ph") == PH_SLDNUM), None)
    if num:
        nr = shape_rect(num)
        for s in shapes + [s for s in items if s.get("ph") == PH_BODY]:
            if hit(rect_of(s), nr):
                msgs.append(("ERROR", f"ページ番号に重なる: {label(s)} → 右下（x {nr[0] / PT:.1f} in・y {nr[1] / PT:.1f} in より先）を空ける"))
        col = g.get("sldnum_color")
        under = [d for d in g["decos"] if d.get("fill") and hit(d["rect"], nr)]
        if col and under:
            d = under[-1]   # 後ろに置いた（上に描かれる）飾り
            c = contrast(col, d["fill"])
            if c < NUM_CONTRAST_MIN:
                msgs.append(("WARN", f"ページ番号の文字（#{col}）が下の「{d['name']}」（#{d['fill']}）に埋もれる（明暗差 {c:.1f}:1）"
                                     " → テンプレートのページ番号の色を地に合わせる（make_templates.py の sldnum_style・zemi.py の recolor）"))
    return msgs, edge


def main(path, pptx_path=None, template=None):
    data = json.load(open(path, encoding="utf-8-sig"))
    W, H = data["slideWidth"], data["slideHeight"]
    shapes = data["shapes"]
    if isinstance(shapes, dict):
        shapes = [shapes]
    pptx_path = pptx_path or data.get("pptx")
    stale = stale_slides(pptx_path, data, shapes) if pptx_path and Path(pptx_path).exists() else []
    if stale:
        print(f"[ERROR] 描画結果が今の pptx と食い違う（スライド {', '.join(map(str, stale[:10]))}）: "
              "PowerPoint が古い版を開いた。render_check.ps1 をやり直す（一時フォルダの複製から開く版か確かめる）")
    scales = picture_scales(pptx_path, shapes)
    inks = picture_ink(pptx_path)
    unders = underlines(pptx_path) if pptx_path and Path(pptx_path).exists() else {}
    plains = plain_slides(pptx_path) if pptx_path and Path(pptx_path).exists() else set()
    thin_slides = set()
    reds = red_counts(pptx_path) if pptx_path and Path(pptx_path).exists() else None
    no_red = set()
    body_contents = []   # 本文の枚の中身の字数（デッキ全体の薄さを見る）
    banded = band_slides(pptx_path) if pptx_path and Path(pptx_path).exists() else None
    lo = data.get("engine") == "libreoffice"
    gap_min = FIG_GAP_MIN_LO if lo else FIG_GAP_MIN
    if lo:
        print("（LibreOffice で描いた結果。文字の範囲を PowerPoint より広く・高く測るので、本文と図の間隔は 0.25 in、下端は 6pt ゆるめて見る。"
              "折り返しの WARN は PowerPoint では出ないこともあるので画像で確かめる）")
    n_err = n_warn = 0
    n_err += bool(stale)
    geo = template_geometry(pptx_path, template) if pptx_path and Path(pptx_path).exists() else None
    t_area = t_conc = None
    if geo:
        t_area = geo["area"]
        t_conc = (geo["style"] or {}).get("conclusion", "band") if geo["style"] is not None else None
        if geo["style"] is not None:
            print(f"（構造：{geo['name']}「{geo['style'].get('label', '')}」の本文の場所・飾り・枠で検査）")
            for m in template_problems(geo["content"], geo["style"], t_area, W, H):
                print(f"[ERROR] テンプレート {geo['name']} の寸法: {m}")
                n_err += 1
        else:
            print("（テンプレートが同梱のどれとも合わない。飾り・枠との重なりだけ見る。本文の場所も見るには --template <テンプレート.pptx>）")
    amounts = []
    table = []
    for i in range(1, data["slides"] + 1):
        items = [s for s in shapes if s["slide"] == i]
        msgs = []
        band_top = BAND_TOP if banded is None or i in banded else NOBAND_BOTTOM
        chars, lines, longest = body_amount(items)
        figs = [s for s in items if is_figure(s)]
        bodies = [s for s in items if is_body(s)]
        qa = is_qa_slide(items)
        cover = is_cover_slide(items)
        if chars and not cover:
            amounts.append(chars)
        fig_ratio = sum(rect_area(f) for f in figs) / (W * H) if figs else 0.0
        big_fig = fig_ratio > 0.45
        min_chars = TEXT_MIN_CHARS_FIG if fig_ratio >= 0.20 else TEXT_MIN_CHARS   # 図が主役の枚（面積の2割以上）は少し少なくてよい
        content = content_chars(items)   # 囲み・箱の中の文字も入れた中身の字数（表は除く。「少なすぎ」はこちらで見る）
        body_slide = (not (qa or cover) and i not in plains and not big_fig
                      and any(s.get("ph") == PH_TITLE for s in items)
                      and not any(s.get("name") in ("区切りの地", "全面の図") for s in items))
        if body_slide:
            body_contents.append(content)
        # 比較の枚も見る（左右に1語ずつだけの枚が通っていた）。大きな数字の枚は数字が主役なので外す
        thin = body_slide and content < min_chars and not any(s.get("name") == "大きな数字" for s in items)
        if thin:
            thin_slides.add(i)
            msgs.append(("WARN", f"本文が少ない（{content}字。目安 100〜150字）→ 本文の要点を3〜4個にし、根拠の数値・具体例・よくある間違いを1つ足す"
                                 "（1行だけの枚にしない。言うことが無い枚なら前後の枚とまとめる。"
                                 "見出しの言い換えや「〜の見方」「別々の要因」のような中身の無い行で字数を埋めない）"))
        if body_slide and reds is not None and reds.get(i, 0) == 0:
            no_red.add(i)
            msgs.append(("WARN", "赤字が無い → その枚で一番言いたい語句（設計メモ・構成案の本文の要点で★の所）を1か所 {r:…} にする"))
        if qa or cover:
            pass  # 問題・解答（要素を削らない）と表紙・区切り（本文ではない）には、文字量・行長の目安を当てない
        elif chars > TEXT_MAX_CHARS or lines > TEXT_MAX_LINES:
            msgs.append(("WARN", f"本文の文字量が多すぎる（{chars}字・{lines}行。目安 100〜150字、上限{TEXT_MAX_CHARS}字・{TEXT_MAX_LINES}行）"
                                 " → 式の導出・長い説明などの細部を発表者ノートへ移すか、スライドを分ける"))
        elif over_target(chars, lines):
            msgs.append(("WARN", f"本文の文字量が目安を超えている（{chars}字・{lines}行。目安 100〜150字）"
                                 " → 式の導出・長い説明だけをノートへ。根拠の数値・具体例は残す。行が多いなら塊（ラベル＋説明）に分けて読みやすく"))
        # 1行の長さ（図・表が横にあるときは20字、なければ25字）
        any_beside = any(beside(t, f) is not None for t in bodies for f in figs)
        lim = LINE_MAX_BESIDE_FIG if any_beside else LINE_MAX
        if longest > lim and not (qa or cover):
            msgs.append(("WARN", f"1行が長い（最長{longest}字。目安 {'図・表の横は' if any_beside else ''}{lim}字）"
                                 " → \\n の位置を直すか、文を短くする（図を左に寄せて逃げない）"))
        # 文章調（体言止めになっていない行）
        sent = [] if (qa or cover) else sentence_lines(items)
        if sent:
            msgs.append(("WARN", f"文章調の行が {len(sent)} 行（本文は体言止め・短い言い切り。style-guide 2・3節）: "
                                 + " / ".join(f"「{t[:16]}」" for t in sent[:4])
                                 + " → 「〜できない」→「〜不可」「〜は無理」、「合っています。正確には〜」→「合っている：〜」のように名詞句で切る"))
        verb = [] if (qa or cover) else verb_lines(items)
        if verb:
            msgs.append(("WARN", f"動詞で終わる行が {len(verb)} 行: " + " / ".join(f"「{t[:16]}」" for t in verb[:4])
                                 + " → 名詞句にできないか確かめる（「進む」→「進行」、「伸びる」→「伸長」、「抜ける」→「脱離」、"
                                   "「当たりにくい」→「衝突がまれ」）。「〜を示す」程度の短い言い切りは残してよい"))
        # 本文と図・表の間隔（横に並ぶとき）
        min_gap = None
        for t in [s for s in items if s.get("type") == MSO_TEXTBOX and s.get("ph") is None and s.get("text")]:
            for f in figs:
                g = beside(t, f)
                if g is None or f["left"] - t["left"] < 1.0 * PT:   # 図の下の注記など、同じ列にあるものは除く
                    continue
                if min_gap is None or g < min_gap:
                    min_gap = g
                if 0 <= g < gap_min:
                    msgs.append(("ERROR", f"本文と図・表の間隔が狭い({g / PT:.2f}in < {gap_min / PT:.1f}in): {label(t)} → {label(f)}"
                                          " → 本文の行を短くする（図を右へずらすだけでは余白が偏る）"))
        # 本文の下に図・表を置いたときの縦の間隔（過去の質問回答デッキ：本文の直下に表が密着していた）
        for t in bodies:
            for f in figs:
                g = below_gap(t, f)
                if g is not None and lo:
                    g += LO_GAP_SHIFT   # LibreOffice は文字を高く測るので、縦の間隔を狭く測る
                if g is not None and g < FIG_GAP_BELOW_MIN:
                    msgs.append(("WARN", f"本文の直下の図・表との縦の間隔が狭い({g / PT:.2f}in < {FIG_GAP_BELOW_MIN / PT:.2f}in): {label(t)} ↓ {label(f)}"
                                         " → 表・図を右に移して本文を横に置くか、本文を削って間隔を空ける"))
        # 図の縮尺（描いた幅より小さく置くと図の文字が小さくなる）
        min_scale = None
        for name, (placed, drawn, sc) in scales.get(i, {}).items():
            if min_scale is None or sc < min_scale:
                min_scale = sc
            if sc < PIC_SCALE_MIN:
                msgs.append(("WARN", f"図を縮小して置いている（描いた幅 {drawn:.2f}in → 置いた幅 {placed:.2f}in、×{sc:.2f}）: {name}"
                                     " → 図の文字が目安より小さくなる。fig()/blank() の幅を置く幅に合わせて描き直す"))
        # 下が空いている: 本文スライド（タイトルあり）で、図も表もなく、本文の最下端が 4.5in より上
        designed = any(s.get("name") in ("大きな数字", "比較の左") for s in items)   # 大きな数字・比べる型は、下が空く形
        if chars and any(s.get("ph") == PH_TITLE for s in items) and not figs and not designed:
            bottom = max((s["top"] + s["height"] for s in items if s.get("ph") is None), default=0)
            if bottom < EMPTY_BOTTOM:
                msgs.append(("WARN", f"下が空いている（本文の最下端 {bottom / PT:.2f}in < {EMPTY_BOTTOM / PT:.1f}in、図・表なし）"
                                     " → 2枚を1枚にまとめるか、行間を広げて縦に配分する（本文は20ptのまま）"))
        if chars and not figs and not designed and not (qa or cover):
            msgs.append(("WARN", "図が無い（本文だけのスライド） → 図・表・大きな数字・比較のどれかを置く（渡す前の確認では ✘）"))
        if len(unders.get(i, [])) > UNDERLINE_MAX:
            u = unders[i]
            msgs.append(("WARN", f"下線が多い（{len(u)} か所：{'・'.join(x[:10] for x in u[:5])}） → 下線は聞き手に指してほしい語だけ、"
                                 f"1枚{UNDERLINE_MAX}か所まで。用語の小見出しは太字（s.block・s.ask の既定）、強調は赤字に"))
        if band_top != BAND_TOP and not (qa or cover or designed):   # 下の帯の無い枚：本文の下端からページの下までが大きく空いている
            low = max((rect_of(s)[3] for s in items if s.get("ph") is None and s.get("name") not in ("見出し", "章のナビ")), default=0)
            if low and band_top - low > EMPTY_BELOW_NOBAND:
                msgs.append(("WARN", f"下が空いている（本文の下端 {low / PT:.2f}in、ページの下まで {(band_top - low) / PT:.1f}in。帯の無い構造）"
                                     " → 図を縦に大きく描くか、本文の行間を広げる。zemi.py は帯の無い構造で本文を縦の中央に寄せるが、"
                                     "それでも空くなら中身が足りない（2枚を1枚にまとめるか、図・例を足す）"))
        # 図の大きさ：枠ではなく、描いてある範囲で測る（細い線1本・小さな箱2つの図を、大きな枠に置いて通していた反省）
        parts = [f for f in figs if f["top"] < band_top - 10 and f.get("name") != "青帯"]
        fig_area = None
        if parts and not (qa or cover or designed):
            fig_area = 0.0
            for f in parts:
                fig_area += ink_of(f, inks.get(i, []))[2] if f["type"] == MSO_PICTURE else f["width"] * f["height"]
            if fig_area < FIG_AREA_MIN * W * H:
                msgs.append(("WARN", f"図が小さい（描いてある範囲がスライドの {fig_area / (W * H) * 100:.0f}%、目安 {FIG_AREA_MIN * 100:.0f}% 以上）"
                                     " → 枠を広げるのではなく、絵そのものを大きく描き直す（右に置く図は幅4.5〜5in・高さ3〜4in を埋める）。"
                                     "描く物が少ないなら、値・具体例・名前を図に足すか、上に文・下に図の型・大きな数字の型にする"))
            # 横に置いた図の下が空いている（図とその注記の下端から帯まで）
            side = [f for f in parts if any(beside(t, f) is not None and f["left"] - t["left"] >= 1.0 * PT for t in bodies)]
            if side:
                col = min(f["left"] for f in side) - 0.3 * PT
                side = [f for f in parts if f["left"] >= col]   # 縦の流れ図の下の箱など、本文より下まで続く同じ列の図も含める
                top0 = min(f["top"] for f in side)
                low = max(ink_of(f, inks.get(i, []))[1] if f["type"] == MSO_PICTURE else f["top"] + f["height"] for f in side)
                for s in items:
                    if (s.get("ph") is None and s.get("type") == MSO_TEXTBOX and s.get("text") and s["left"] >= col
                            and s["top"] >= top0 and rect_of(s)[3] < band_top - 10):
                        low = max(low, rect_of(s)[3])
                if band_top - low > FIG_EMPTY_BELOW + (band_top - BAND_TOP):
                    msgs.append(("WARN", f"図の下が空いている（図と注記の下端 {low / PT:.2f}in、下まで {(band_top - low) / PT:.1f}in）"
                                         " → 図を縦に大きく描く（高さ3〜4in）か、図の下に値の表・例を足す。横長の図なら上に文・下に図の型（figure_below）"))
        # テンプレートの形（本文の場所・上の見出しの領域・飾り・柱・高さ・ページ番号）
        t_msgs, edge = template_checks(items, geo["slides"].get(i) if geo else None, t_area, t_conc, W, H, band_top, inks.get(i, []),
                                       right_tol=RIGHT_TOL + (0.1 * PT if lo else 0))   # LibreOffice の描画は字の幅が PowerPoint と違い、講座の見本の注記で 0.1 in ほど広く測れた
        msgs += t_msgs
        content = []
        for s in items:
            ph = s.get("ph")
            r = rect_of(s)
            if ph == PH_SLDNUM or s["name"] == "区切りの地":   # 区切りの枚の全面の地は、帯・余白・重なりの検査から外す
                continue
            if ph == PH_TITLE:
                if s["lines"] > s["paras"]:
                    msgs.append(("ERROR", f"タイトルが折り返している: {label(s)}"))
                content.append((s, r))
                continue
            if (ph == PH_BODY or s["name"] == "青帯") and r[1] >= BAND_TOP - 10:  # 青帯のまとめ文（テンプレートに枠が無いときは zemi が描いた「青帯」）
                if s["lines"] > s["paras"] or (s["tw"] or 0) > W - 20:
                    msgs.append(("ERROR", f"青帯のまとめ文が長すぎて折り返す/はみ出す: {label(s)}"))
                continue
            if r[0] < -1 or r[1] < -1 or r[2] > W + 1 or r[3] > H + 1:
                msgs.append(("ERROR", f"スライド外にはみ出し: {label(s)} rect={[round(v) for v in r]}"))
            limit = band_top - 2 + (LO_BOTTOM_TOL if lo else 0)   # 描画の誤差 2pt（LibreOffice はさらに高く測る分）
            if r[3] > limit and r[1] < H:
                what = "青帯にかかっている" if band_top == BAND_TOP else "下の余白が狭い（ページ番号にかかる）"
                msgs.append(("ERROR", f"{what}(下端 {r[3] / PT:.2f}in > {limit / PT:.2f}in): {label(s)}"))
            if (r[0] < MARGIN or r[2] > W - MARGIN) and id(s) not in edge:   # 本文の場所からはみ出す ERROR を出したものは重ねて言わない
                msgs.append(("WARN", f"左右の余白が狭い: {label(s)}"))
            if s.get("text") and s["lines"] > s["paras"]:
                msgs.append(("WARN", f"自動で折り返している（1文字だけ次行に落ちる等を画像で確認）: {label(s)}"))
            content.append((s, r))
        for (a, ra), (b, rb) in combinations(content, 2):
            if is_ring(a) or is_ring(b):
                continue
            w, h = inter(ra, rb)
            if w > 2 and h > 2 and w * h > 6:
                msgs.append(("ERROR", f"重なり: {label(a)} × {label(b)} ({w:.0f}x{h:.0f}pt)"))
            elif a.get("text") and b.get("text"):
                # 縦に並ぶテキストどうしの隙間が極端に狭い
                hov = min(ra[2], rb[2]) - max(ra[0], rb[0])
                gap = max(rb[1] - ra[3], ra[1] - rb[3])
                if lo:   # LibreOffice は縦の間隔を PowerPoint より約4〜6pt 狭く測る（2つのデッキで実測、最小 3.9pt）
                    gap += LO_GAP_SHIFT
                if hov > 0 and 0 <= gap < 3:
                    msgs.append(("WARN", f"間隔が狭い({gap:.1f}pt): {label(a)} / {label(b)}"))
        if msgs:
            print(f"--- slide {i}")
            for lvl, m in msgs:
                print(f"  [{lvl}] {m}")
                n_err += lvl == "ERROR"
                n_warn += lvl == "WARN"
        if chars or figs:
            table.append((i, chars, lines, longest, any_beside, min_gap, min_scale, qa or i in plains, len(sent), len(verb), cover,
                          None if fig_area is None else fig_area / (W * H)))

    # スライドごとの一覧（ERROR 0 でも必ず見る。目安から外れた値に ← を付ける）
    if table and BRIEF:
        rows_bad = []
        for i, chars, lines, longest, any_beside, min_gap, min_scale, qa, n_sent, n_verb, cover, area in table:
            skip = qa or cover
            f = [n for n, c in (("文字量", not skip and over_target(chars, lines)),
                                ("文字が少ない", i in thin_slides), ("赤字なし", i in no_red),
                                ("行長", not skip and longest > (LINE_MAX_BESIDE_FIG if any_beside else LINE_MAX)),
                                ("文章調", bool(n_sent)), ("動詞止め", bool(n_verb)), ("間隔", min_gap is not None and min_gap < gap_min),
                                ("縮尺", min_scale is not None and min_scale < PIC_SCALE_MIN), ("図が小さい", area is not None and area < FIG_AREA_MIN)) if c]
            if f:
                rows_bad.append(f"  [{i}] {chars}字・{lines}行・最長{longest}字 ← {'・'.join(f)}")
        if rows_bad:
            print("目安から外れた枚（直す）：\n" + "\n".join(rows_bad))
    elif table:
        print("\nスライドごとの一覧（目安：100〜150字、1行は図の横で20字・図なしで25字、文章調 0行、図との間隔 0.4in 以上、縮尺 1.0、"
              f"図の範囲 {FIG_AREA_MIN * 100:.0f}% 以上）")
        print("  枚  字数  行数  最長行  文章調  図との間隔  図の縮尺  図の範囲")
        for i, chars, lines, longest, any_beside, min_gap, min_scale, qa, n_sent, n_verb, cover, area in table:
            flags = []
            skip = qa or cover
            if not skip and over_target(chars, lines):
                flags.append("文字量")
            if i in thin_slides:
                flags.append("文字が少ない")
            if i in no_red:
                flags.append("赤字なし")
            if not skip and longest > (LINE_MAX_BESIDE_FIG if any_beside else LINE_MAX):
                flags.append("行長")
            if n_sent:
                flags.append("文章調")
            if n_verb:
                flags.append("動詞止め")
            if min_gap is not None and min_gap < gap_min:
                flags.append("間隔")
            if min_scale is not None and min_scale < PIC_SCALE_MIN:
                flags.append("縮尺")
            if area is not None and area < FIG_AREA_MIN:
                flags.append("図が小さい")
            gap_s = "   —   " if min_gap is None else f"{min_gap / PT:6.2f}in"
            sc_s = "  —  " if min_scale is None else f"×{min_scale:.2f}"
            sc_s += "   —  " if area is None else f"   {area * 100:4.0f}%"
            sent_s = "  — " if skip else f"{n_sent:3d}行" + (f"(+動詞{n_verb})" if n_verb else "")
            mark = ("  ← " + "・".join(flags)) if flags else ("  （問題・解答）" if qa else "  （表紙・区切り）" if cover else "")
            print(f"  {i:2d}  {chars:4d}  {lines:3d}   {longest:3d}字   {sent_s}   {gap_s}   {sc_s}{mark}")
    for m in quiz_problems(shapes, data["slides"]):
        n_err += 1
        print(f"[ERROR] 確認問題：{m}")
    if len(body_contents) >= 4:
        b = sorted(body_contents)
        med = b[len(b) // 2] if len(b) % 2 else (b[len(b) // 2 - 1] + b[len(b) // 2]) / 2
        if med < TEXT_MEDIAN_MIN:
            n_warn += 1
            print(f"[WARN] デッキ全体の本文が薄い（本文の枚の中身の字数の中央値 {med:.0f}字。下限 {TEXT_MEDIAN_MIN}字・実際のデッキは 120字前後）"
                  " → 少ない枚から順に、根拠の数値・具体例・よくある間違い・図の読み方を足す（字数合わせの行は足さない）")
    if amounts and not BRIEF:
        a = sorted(amounts)
        print(f"\n本文の字数: 中央値 {a[len(a) // 2]}字 / 最大 {a[-1]}字（目安 100〜150字、最大{TEXT_MAX_CHARS}字）")
    print(f"{data['slides']} slides: {n_err} errors, {n_warn} warnings")
    return 1 if n_err else 0


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--brief" in args:
        args.remove("--brief")
        BRIEF = True
    tmpl = None
    if "--template" in args:   # 自分で足したテンプレート（同梱のどれとも形が合わないもの）の本文の場所で見るとき
        k = args.index("--template")
        tmpl = args[k + 1]
        del args[k:k + 2]
    sys.exit(main(args[0], args[1] if len(args) > 1 else None, template=tmpl))
