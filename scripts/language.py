"""出力の言語（スライド・原稿・原稿のページの言語）。設定の「言語」（既定は日本語）。

考え方：
  - 構成案・設計メモ・担当への依頼・検査の言葉は日本語のまま。スライドと原稿に載る文字だけを、その言語で書く。
  - 字数の目安は「全角に直した幅」で数える。日本語は今までどおり1字＝1（空白は数えない）。
    ほかの言語は、全角の字（漢字・かな・ハングル）を1、半角の字（ラテン文字・数字・空白）を0.5として数える。
    英語の文は日本語より横に長いが、スライドの上の広さは同じなので、同じ目安（1枚80〜120・1行20前後）がそのまま使える
    （見本の2本を英語にしたデッキで、本文の量の中央値が日本語版 110字 に対して 115〜130 になった）。
  - 体言止め・動詞で終わる行の検査は日本語だけ。ほかの言語は、文の終わりの記号（. 。 ! ？）で終わる行を「文章調」として見る。
  - 原稿の長さは、日本語は字数（1分300字）、空白で語を区切る言語は語数（1分150語。日本語の字数の約半分）で見る。

    from language import lang_name, lang_code, is_japanese, width, measure, words
"""
from __future__ import annotations

import re
import unicodedata

KEY = "言語"
DEFAULT = "日本語"

# 呼び名 → 正式な名前（小文字にして引く）。無い名前は、書いてあるまま使う（目安は英語と同じ、空白で語を区切る言語として扱う）
ALIASES = {
    "日本語": "日本語", "japanese": "日本語", "ja": "日本語", "ja-jp": "日本語", "jp": "日本語",
    "英語": "英語", "english": "英語", "en": "英語", "en-us": "英語", "en-gb": "英語", "えいご": "英語",
    "中国語": "中国語", "chinese": "中国語", "zh": "中国語", "zh-cn": "中国語", "簡体字": "中国語", "繁体字": "中国語（繁体字）",
    "中国語（繁体字）": "中国語（繁体字）", "zh-tw": "中国語（繁体字）",
    "韓国語": "韓国語", "korean": "韓国語", "ko": "韓国語", "ko-kr": "韓国語", "ハングル": "韓国語",
    "フランス語": "フランス語", "french": "フランス語", "fr": "フランス語",
    "ドイツ語": "ドイツ語", "german": "ドイツ語", "de": "ドイツ語",
    "スペイン語": "スペイン語", "spanish": "スペイン語", "es": "スペイン語",
    "ポルトガル語": "ポルトガル語", "portuguese": "ポルトガル語", "pt": "ポルトガル語",
    "イタリア語": "イタリア語", "italian": "イタリア語", "it": "イタリア語",
    "ベトナム語": "ベトナム語", "vietnamese": "ベトナム語", "vi": "ベトナム語",
    "インドネシア語": "インドネシア語", "indonesian": "インドネシア語", "id": "インドネシア語",
}
CODES = {"日本語": "ja-JP", "英語": "en-US", "中国語": "zh-CN", "中国語（繁体字）": "zh-TW", "韓国語": "ko-KR",
         "フランス語": "fr-FR", "ドイツ語": "de-DE", "スペイン語": "es-ES", "ポルトガル語": "pt-BR", "イタリア語": "it-IT",
         "ベトナム語": "vi-VN", "インドネシア語": "id-ID"}
# 語を空白で区切らない言語（原稿の長さを字数で見る）
NO_SPACE = {"日本語", "中国語", "中国語（繁体字）"}
# 原稿の速さの目安：字数で見る言語は 字／分、ほかは 語／分
CHARS_PER_MIN = {"日本語": 300, "中国語": 250, "中国語（繁体字）": 250}
WORDS_PER_MIN = 150   # 日本語の原稿1字は英語の約0.5語（見本の講座の1回を英語にした原稿で 507字→263語）


def lang_name(v) -> str:
    """設定の値 → 正式な名前（「英語」「English」「en」→「英語」）。空なら日本語。知らない言語は書いてあるまま。"""
    v = (v or "").strip()
    if not v:
        return DEFAULT
    head = re.split(r"[（(。、,;；:：\s]", v, maxsplit=1)[0].strip()   # 先頭の語（「日本語（スライド…）。16:9」の「日本語」）
    for u in (v, re.sub(r"\s*[（(].*?[)）]\s*$", "", v).strip(), head):   # 「英語（スライドと原稿）」のような注記を外して引き直す
        if u.lower() in ALIASES:
            return ALIASES[u.lower()]
    # 注記のあとに別の文が続いても先頭の語で読む（地図の担当が「言語：日本語（スライド・原稿・確認問題）。16:9」と書き、
    # 読めずに日本語のデッキが英語の名前（_slides.pptx）・英語の部品で組まれ、制作の担当が全部の枚を直していた）
    return re.sub(r"\s*[（(].*?[)）]\s*$", "", v).strip() or DEFAULT


def lang_code(v) -> str:
    """PowerPoint の文字の言語（ja-JP・en-US など）。知らない言語は en-US（つづりの検査が少なくとも英語の綴りで動く）。"""
    name = lang_name(v)
    if name in CODES:
        return CODES[name]
    if re.fullmatch(r"[a-z]{2,3}(-[A-Za-z]{2,4})?", (v or "").strip()):
        return v.strip()
    return "en-US"


def name_of_code(code) -> str:
    """ja-JP → 日本語（pptx の言語の印から戻すとき）。知らない印は日本語（今までのデッキは印が無い）。"""
    c = (code or "").strip().lower()
    for name, cd in CODES.items():
        if cd.lower() == c:
            return name
    if c and c.split("-")[0] in ALIASES:
        return ALIASES[c.split("-")[0]]
    return DEFAULT


def is_japanese(v) -> bool:
    return lang_name(v) == DEFAULT


def spaced(v) -> bool:
    """語を空白で区切る言語か（英語・韓国語・フランス語など）。原稿の長さを語数で見る。"""
    return lang_name(v) not in NO_SPACE


def width(t: str) -> float:
    """全角に直した幅：全角の字は1、半角の字（空白を含む）は0.5。"""
    return sum(1.0 if unicodedata.east_asian_width(c) in "WF" else 0.5 for c in t or "" if c not in "\r\n\t")


def measure(t: str, lang=None) -> float:
    """スライドの文字の量（字数の目安と比べる値）。日本語は空白を除いた字数（今までどおり）、ほかは全角に直した幅。"""
    if is_japanese(lang):
        return len(re.sub(r"\s", "", t or ""))
    return width(re.sub(r"\s+", " ", (t or "").strip()))


def words(t: str) -> int:
    return len(re.findall(r"\S+", t or ""))


def script_unit(lang=None) -> str:
    return "語" if spaced(lang) else "字"


def per_min(lang=None) -> int:
    return WORDS_PER_MIN if spaced(lang) else CHARS_PER_MIN.get(lang_name(lang), 300)


# 文の終わりの記号で終わる行（日本語以外の「文章調」）。略語（etc. e.g. i.e. et al. vs.）は除く。
# 問い（?）は数えない（本文の形「問い → 答え」の問いの行。日本語の検査も「？」は数えない）
SENTENCE_END = re.compile(r"[.!。！]$")
NOT_SENTENCE = re.compile(r"(\betc|\be\.g|\bi\.e|\bal|\bvs|\bcf|\bNo|\bFig|\bEq|\bRef|\bp|\bpp|\.\.)\.$", re.I)


def is_sentence(t: str, lang=None) -> bool:
    """日本語以外の本文の行が文の形か（文の終わりの記号で終わる。空白で語を区切る言語は3語以上）。"""
    u = (t or "").rstrip(")]}\"'”’）」 ")
    return bool(SENTENCE_END.search(u)) and not NOT_SENTENCE.search(u) and (words(u) >= 3 or not spaced(lang))


# 確認問題・解答・やり取りの枚を●見出しで見分ける言葉（言語を問わずまとめて見る。解答を先に見る）。
# 漢字・かな・ハングルの言葉は見出しのどこにあってもよい。ラテン文字の言葉は見出しの頭だけ
# （"Even big models ... so answers vary" のような結論の見出しを解答の枚と取り違えた）
ANSWER_WORDS = ("解答", "answer", "solution", "答案", "解答", "정답", "해답", "réponse", "antwort", "lösung", "respuesta", "resposta", "risposta")
QUIZ_WORDS = ("確認問題", "review question", "check question", "quiz", "check your understanding", "exercise", "练习", "復習", "复习", "확인 문제", "문제",
              "question de révision", "kontrollfrage", "pregunta", "pergunta", "domanda")
QA_WORDS = ("問題", "解答", "やり取り", "添削", "想定質問", "question", "answer", "q&a", "quiz", "exercise", "feedback",
            "review question", "check question", "expected question", "anticipated question", "solution", "check your understanding",
            "问题", "答案", "문제", "정답", "질문")


def _hit(heading: str, words) -> bool:
    h = re.sub(r"^[\s●■◆▶▷►○□◇◎・▪▸•]+", "", (heading or "").lower())
    for w in words:
        if any(unicodedata.east_asian_width(c) in "WF" for c in w):
            if w in h:
                return True
        elif re.match(re.escape(w) + r"(?![a-zà-ÿ])|" + re.escape(w) + r"s\b", h):
            return True
    return False


def quiz_kind(heading: str):
    """●見出しから：解答の枚 →「解答」、確認問題の枚 →「確認問題」、どちらでもない → None。"""
    if _hit(heading, ANSWER_WORDS):
        return "解答"
    if _hit(heading, QUIZ_WORDS):
        return "確認問題"
    return None


def is_qa_heading(heading: str) -> bool:
    """確認問題・解答・やり取り・添削・想定質問の枚の●見出しか（文字量の目安を当てない枚）。"""
    return _hit(heading, QA_WORDS)


# 作るファイルの名前の終わり（日本語・それ以外）。読む側はどちらも受け取る（今までの日本語の名前のデッキも読める）
# 英語の見本の作り直しで、英語のデッキの名前が「_スライド.pptx」「_原稿.html」と日本語になった
SUFFIXES = {"slides": ("_スライド", "_slides"), "script": ("_原稿", "_script"), "comments": ("_コメント", "_comments"),
            "answers": ("_質問回答", "_answers")}


def suffix(kind: str, lang=None) -> str:
    """ファイルの名前の終わり：suffix("slides", "英語") → "_slides"。"""
    ja, other = SUFFIXES[kind]
    return ja if is_japanese(lang) else other


def strip_suffix(stem: str, kind: str) -> str:
    """名前の終わり（日本語・英語のどちらでも）を外す。"""
    for s in SUFFIXES[kind]:
        if stem.endswith(s):
            return stem[:-len(s)]
    return stem


def sibling(path, src_kind: str, dst_kind: str):
    """「X_スライド.pptx」→「X_原稿.html」のように、同じ言語の名前の終わりで隣のファイルの場所を作る。"""
    from pathlib import Path as _P
    p = _P(path)
    stem = p.stem
    for i, s in enumerate(SUFFIXES[src_kind]):
        if stem.endswith(s):
            return p.with_name(stem[:-len(s)] + SUFFIXES[dst_kind][i] + {"slides": ".pptx", "script": ".html", "comments": ".json"}.get(dst_kind, ""))
    return p.with_name(stem + SUFFIXES[dst_kind][0] + {"slides": ".pptx", "script": ".html", "comments": ".json"}.get(dst_kind, ""))


KANA = re.compile(r"[ぁ-んァ-ヶー]")
KANJI = re.compile(r"[一-龥々]")

def japanese_left(t: str, lang=None) -> bool:
    """日本語でないデッキの文字に、日本語が残っているか。かなは中国語でも残り、漢字は中国語のデッキでは数えない。
    全角の空白（　）も数えない（部品の字下げ）。英語の試しで、表紙の「第1回」「全1回」がどの検査にも出なかった。"""
    if is_japanese(lang) or not t:
        return False
    if KANA.search(t):
        return True
    return lang_name(lang) not in NO_SPACE and bool(KANJI.search(t))


def deck_language(pptx_path=None, start=None) -> str:
    """デッキの言語：pptx の言語の印（zemi.Deck が書く）→ 作業フォルダの設定（構成案・設計メモの「言語」）→ 日本語。"""
    if pptx_path:
        try:
            from pptx import Presentation
            code = Presentation(str(pptx_path)).core_properties.language
            if code:
                return name_of_code(code)
        except Exception:
            pass
    if start:
        try:
            from pathlib import Path
            from slide_profile import load_profile, option
            for d in (Path(start), *Path(start).parents[:2]):
                p = load_profile(d)
                if p.get("オプション"):
                    return lang_name(option(p, KEY))
        except Exception:
            pass
    return DEFAULT


# 判定の流れ図（zemi の s.decision）の枝の言葉。無い言語は英語
YES_NO = {"日本語": ("はい", "いいえ"), "英語": ("Yes", "No"), "中国語": ("是", "否"), "中国語（繁体字）": ("是", "否"),
          "韓国語": ("예", "아니요"), "フランス語": ("Oui", "Non"), "ドイツ語": ("Ja", "Nein"), "スペイン語": ("Sí", "No"),
          "ポルトガル語": ("Sim", "Não"), "イタリア語": ("Sì", "No"), "ベトナム語": ("Có", "Không"), "インドネシア語": ("Ya", "Tidak")}


# ---- 並べる項目の形（英語だけ）。日本語の体言止めに当たる、英語のスライドの決まり：並べる項目の形をそろえる
# （全部を名詞句に、手順なら全部を命令形に。名詞句と文、命令形と名詞句、-ing と名詞句を1つのリストに混ぜない）。
# 組んだ pptx では「1項目の折り返し」と「次の項目」が区別できないので、zemi.py が項目のリストを受け取った所で見る。
AUX = re.compile(r"\b(is|are|was|were|isn't|aren't|wasn't|weren't|can|cannot|can't|could|will|won't|would|should|must|"
                 r"has|have|had|hasn't|haven't|does|do|did|doesn't|don't|didn't|may|might)\b", re.I)
VERBS = set("""add adjust apply ask assume avoid build calculate choose cite collect combine compare compute confirm consider
convert decide define delete describe detect divide double-check explain find follow get give go hide identify ignore include keep
let make multiply nudge open pick predict prefer prepare read reduce remove repeat replace rerun reuse save see select send show
skip subtract summarize take tell think try use verify write""".split())
# 名詞にもなる動詞（"record low noise" "test results"）。同じリストにはっきりした命令形があるときだけ命令形と見る
VERBS_OR_NOUNS = set("""answer change check copy count cut draw drop estimate fit fix guess label list look mark measure move name
note place plot record report run search set shift sort split start stop test trace turn type update watch""".split())
ING_NOUNS = {"thing", "things", "string", "strings", "ring", "rings", "king", "nothing", "something", "everything", "anything",
             "morning", "evening", "spring", "ceiling", "during", "wing", "wings", "sibling", "siblings", "bring", "sing", "swing"}
_MARKUP = re.compile(r"\{[a-z]+:")
RELATIVE = re.compile(r"\b(?:that|which|who|whom|whose|when|where|if|whether|what|how|why|because|so)\b", re.I)


def _plain(item: str) -> str:
    return re.sub(r"\s+", " ", _MARKUP.sub("", str(item)).replace("{", "").replace("}", "").replace("^", "").replace("_", "")).strip()


def item_form(item: str, lang=None):
    """並べる項目1つの形：'文'（be動詞・助動詞を含む）・'命令形'・'-ing'・'名詞句'。
    見ないもの（None）：英語でない・数字や記号で始まる・問い（?）・「ラベル: 説明」の形。"""
    if lang_name(lang) != "英語":
        return None
    t = _plain(item)
    if not t or not t[0].isalpha() or t.endswith("?") or re.match(r"^[^:]{1,40}: ", t):
        return None
    if AUX.search(RELATIVE.split(t)[0]):   # "text that is nonsensical" は名詞句（関係詞のあとの be動詞は数えない）
        return "文"
    w = re.sub(r"[^a-z'-]", "", t.split()[0].lower())
    if len(t.split()) > 1 and w in VERBS:
        return "命令形"
    if len(t.split()) > 1 and w in VERBS_OR_NOUNS:
        return "命令形?"
    if w.endswith("ing") and len(w) > 4 and "-" not in w and w not in ING_NOUNS:
        return "-ing"
    return "名詞句"


def mixed_forms(items, lang=None, steps=False):
    """並べる項目の形がそろっていなければ、(多い形, [(形, 少ない方の項目), ...]) を返す。そろっていれば None。
    形を見られる項目が2つ未満なら見ない。steps=True（番号の手順）は、名詞にもなる動詞（Shift・Search）を命令形と見る。"""
    forms = [(item_form(it, lang), _plain(it)) for it in items]
    forms = [(f, t) for f, t in forms if f]
    clear = steps or any(f == "命令形" for f, _ in forms)
    forms = [(("命令形" if clear else "名詞句") if f == "命令形?" else f, t) for f, t in forms]
    kinds = {f for f, _ in forms}
    if len(forms) < 2 or len(kinds) < 2:
        return None
    count = {k: sum(f == k for f, _ in forms) for k in kinds}
    main = max(kinds, key=lambda k: (count[k], k == "名詞句"))
    return main, [(f, t) for f, t in forms if f != main]
