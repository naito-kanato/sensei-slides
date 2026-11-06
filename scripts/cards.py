"""カード：上の段（構成案・設計メモ）で決めたことのうち、1件の仕事に要るものだけを1つのファイルにまとめる（SKILL.md「使用量を抑える進め方」）。
書き手（軽いモデルでも）は、カードと、カードが指す資料の抜き出しだけを読んで1件ずつ仕上げる。補う前提（書き手の推論距離）を先に埋めておくための部品。


カードの種類（どれも「やること・変えないもの・材料・書き方の型・出力するファイル」の順）
  quiz（writer の中）：講座の確認問題・解答の枚。設計メモ 6節の〔ゴールN・M枚目〕〔要素：…〕から
  answers（writer の中）：質問回答の枚。answers.md の表のコメント・元の枚から。差は小さく（2勝1敗）使用量は +14% なので、
                         軽いモデルに書かせるときだけ使う（標準以上のモデルなら、表と骨組みから直接書く）
  ※試して入れなかったもの（軽いモデルの Haiku と、伏せた Opus の判定で比べた。2026-11-06）
    - 描画の崩れを直すカード：仕上げ役1人が描画を見ながら直すほうが、使用量が少なく（約14万 対 23万）結果も同じ。カードの直し役は原稿を消した
    - 図のカード：図の担当1人が figures.md を読んで描くほうが良く（4勝1敗1分）、使用量も少ない。図は資料を探すより仕組みを正しく描くのが難しい
    - 完成後のレビューに渡す材料（枚ごとの構成案・スライドの文字・原稿）：使用量が同じ（約14万）で、指摘の数も同じくらい。拾う所が違うだけ
  どれも各方式1回ずつの比べ。効いたのは「資料から探して、決まった形に書く」仕事（本文・原稿）で、見ながら直す・仕組みを理解して描く仕事には効かなかった
  writer（scaffold.py が作る cards/NN.md）：本文と原稿を1枚ずつ書く
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

# カードに入れる量の上限（字）。資料の抜き出しや見本をまるごと入れると、書き手の数だけ読む量が増える
CARD_SRC_MAX = 16000     # 1枚のカードが指す資料の抜き出しの合計（要旨を含む）。超えた範囲は「資料で読む」に回す
INLINE_MAX = 1200        # カードの中に直接写す文（元の枚の原稿・今の原稿など）


def clip(text: str, limit: int, rest: str) -> str:
    """limit 字までに切り、切ったときは「…（rest）」を付ける。"""
    return text if len(text) <= limit else text[:limit].rstrip() + f"\n…（ここまで。{rest}）"


FORM_METHODS = {"帰結": ["lead"], "ラベル": ["block"], "展開": ["develop"], "縦の結論": ["lead_down"], "場合分け": ["cases"],
                "問い": ["ask"], "手順": ["numbered"], "式の注釈": ["peq", "defs"], "箇条": ["p"]}


def api_lines(forms: str, figure: bool, table: bool):
    """カードに入れる、この枚で使う部品の書き方（zemi.py の引数と説明の1〜2行）。書き手が部品の説明を探しに行かずに済む。"""
    import inspect
    try:
        import zemi
    except Exception:
        return []
    names = []
    for k in [f.strip() for f in re.split(r"[・、,＋+]", forms or "") if f.strip()] or ["箇条"]:
        names += FORM_METHODS.get(k, [])
    names += (["figure_beside"] if figure else []) + (["table"] if table else [])
    out = ["- 文字の書式：{r:赤字} {u:下線} {b:太字} {i:変数}。改行は文字列の中の \\n（1行20字まで）"]
    for n in dict.fromkeys(names):
        f = getattr(zemi.Slide, n, None)
        if f is None:
            continue
        sig = re.sub(r":\s*'[^']*'", "", str(inspect.signature(f))).replace("(self, ", "(").replace(" -> 'Box'", "").replace(" -> 'float'", "")
        doc = " ".join((inspect.getdoc(f) or "").splitlines()[:2])
        out.append(f"- `s.{n}{sig}`：{doc}")
    return out


def writer(work: Path, kind, rows, care, minutes=None, source=None):
    """{番号: カードの文}（本文の枚だけ）。source（資料の PDF・テキスト）があれば、範囲の所を抜き出して入れる。"""
    import excerpt
    import story
    from scaffold import EMPTY, blocks, build_py, col
    src_text = excerpt.load(source) if source else ""
    shared = {}     # 抜き出しの先頭 → ファイル名（同じ節を枚ごとに写さない）
    out = {}
    head = excerpt.abstract(src_text) if src_text else ""
    if head:        # 要旨は数値の要約が入っていることが多いので、どの枚のカードからも指す（書き手ごとに1回だけ読む）
        out["資料0.md"] = f"# 資料の抜き出し：要旨（{source.name} の最初の節より前）\n\n```text\n{head}\n```\n"
    text = (work / {"memo": "memo.md", "answers": "answers.md"}.get(kind, "outline.md")).read_text(encoding="utf-8")
    st = story.story_table(text) or {}
    body = [r for r in rows if (col(r, "役割") or "本文") == "本文"]
    per = f"{minutes * 300 / max(len(body), 1):.0f}字" if minutes else ("380字" if kind == "memo" else "400字")
    skel = build_py(work, kind, "T", rows)
    code = blocks(skel)
    terms = ""
    if kind == "memo":
        m = re.search(r"^##\s*4\.[^\n]*\n(.*?)(?=^##\s)", text, re.S | re.M)
        terms = re.sub(r"\n{2,}", "\n", m.group(1)).strip() if m else ""
        terms = "" if terms in ("-", "") else terms
    facts = []
    if kind == "memo":
        from check_memo import table_rows
        ft = table_rows(text, "事実と出典") or []
        facts = [[c for c in r[:3]] for r in ft[1:] if r and any(c.strip() for c in r)]
    for k, r in enumerate(body):
        n = r["#"]
        prev, nxt = (body[k - 1] if k else None), (body[k + 1] if k + 1 < len(body) else None)
        w, kd = story.split_link(col(r, "前の枚から"))
        g = story.GUIDE.get((w, kd))
        a, b = code.get(n, (0, 0))
        q_, a_ = st.get("問い", ("", None)), st.get("答え", ("", None))
        fig_cell = col(r, "図で見せるもの", "図") or "なし"
        not_image = fig_cell in EMPTY or bool(re.match(r"\s*(表|大きな数字)", fig_cell))
        L = [f"# {n}枚目のカード（{work.name}）",
             "",
             "このカードと、下の「資料」の所だけを見て、この1枚を書く。ほかの枚・SKILL.md 全体は読まない。",
             f"書くもの：`parts/{n:02d}.py`（下の骨組みの TODO を埋めた、この枚のコード）と `parts/{n:02d}.md`（この枚の原稿。「## {n}」の見出しは書かない）。",
             "青帯（結論）と●見出しは変えない。変えたくなったら書かずに、理由を1行で返す。",
             "",
             "## 話の中の位置"]
        if st:
            L += [f"- 筋の問い（{q_[1] or '?'}枚目）：{q_[0]}", f"- 筋の答え（{a_[1] or '?'}枚目）：{a_[0]}"]
            if n == q_[1]:
                L.append("- **この枚が問いの枚**：原稿の終わりで、筋の問いをそのまま聞き手に投げかける（あとの枚の「最初の問い」はここを指す）")
            if n == a_[1]:
                L.append("- **この枚が答えの枚**：原稿で「問いへの答えは〜です」と、筋の問いに答える形で言う")
        L += [f"- 前の枚（{prev['#']}）の青帯：{col(prev, '青帯', '結論')}" if prev else "- 前の枚：なし（本文の最初の枚。筋の状況から入る）",
              f"- **この枚の青帯：{col(r, '青帯', '結論')}**",
              f"- 次の枚（{nxt['#']}）の青帯：{col(nxt, '青帯', '結論')}" if nxt else "- 次の枚：なし（本文の最後の枚。筋の問いに戻って締める）"]
        if g:
            L.append(f"- 前の枚から：{w}（{kd}）→ 原稿の1文目は {g[0]} の形。{g[1]}")
        if kind == "answers":
            L += answer_lines(work, r)
        L += ["", "## この枚の中身",
              f"- ●見出し：{col(r, '●見出し')}",
              f"- 本文の形：{col(r, '本文の形') or '—'}（部品の使い方：`python <skill>/scripts/guide.py structures` の、その形の節）",
              f"- 本文の要点（★は赤字。〔…〕は出どころ＝その数値・例を引く所。スライドには書かない）：{col(r, '本文の要点')}",
              (f"- 図で見せるもの：{fig_cell}（画像は使わない。表は s.table、大きな数字は本文の部品で組む）" if not_image else
               f"- 図で見せるもの：{fig_cell}（図のファイルは figs/s{n:02d}.png。描くのは図の担当なので、名前だけ使う）"),
              f"- ノートへ（原稿で言う細部）：{col(r, 'ノートへ', 'ノート') or 'なし'}"]
        for c in care.get(n, []):
            L.append(f"- 手当て（必ず原稿か本文に入れる）：{c}")
        src = col(r, "範囲")
        # 要点の出どころ〔…〕が範囲の外の節・図を指していれば、それも抜き出す（要旨・事実N・自分の計算は除く）
        tags = [t.strip() for g in re.findall(r"〔([^〕]+)〕", col(r, "本文の要点")) for t in g.split("・")]
        tags = [t for t in tags if t and not re.match(r"(要旨|事実|発表者|資料外|例|一般)", t)]
        if (src not in EMPTY or tags) and src_text:
            got, miss = excerpt.pieces(src_text, ", ".join(([src] if src not in EMPTY else []) + tags))
            src = src if src not in EMPTY else "（要点の出どころから）"
            names = ["`cards/資料0.md`（要旨）"] if head else []
            budget = CARD_SRC_MAX - len(head)
            for tok, piece in got:
                if len(piece) > budget:      # 1枚が指す抜き出しの合計に上限（書き手の数だけ読む量が増えるため）
                    miss.append(f"{tok}（抜き出しの上限を超えるので省いた）")
                    continue
                budget -= len(piece)
                key = piece[:200]
                if key not in shared:
                    shared[key] = f"資料{len(shared) + 1}.md"
                    out[shared[key]] = f"# 資料の抜き出し：{tok}（{source.name} から excerpt.py で）\n\n```text\n{piece}\n```\n"
                names.append(f"`cards/{shared[key]}`（{tok}）")
            L += ["", "## 資料",
                  f"- 範囲：{src}。抜き出し：{'・'.join(names) or 'なし'}。**前の枚で同じ抜き出しを読んだなら、読み直さない**",
                  f"- 数値・式・固有名詞は抜き出しのとおりに写す。資料のファイル {source.name} は、抜き出しに無いことが要るときだけ開く"]
            if miss:
                L.append(f"- 抜き出せなかった範囲：{'・'.join(miss)}（{source.name} でその所だけを読む）")
        elif src not in EMPTY:
            L += ["", "## 資料", f"- 範囲：{src}（構成案の冒頭に書いた資料（発表フォルダの 資料/）の、この所だけを読む。数値・式・固有名詞は資料のとおりに写す）"]
        elif kind == "memo":
            L += ["", "## 資料", "- 設計メモ 3節「事実と出典」の表から、この枚の要点に当たる行だけを使う（表に無い事実は足さない）"]
        else:
            L += ["", "## 資料", "- 構成案の要点に当たる資料の所だけを読む"]
        if kind == "memo" and facts:
            used = sorted({int(x) for x in re.findall(r"事実\s*(\d+)", col(r, "本文の要点"))})
            rowsf = [f"  - 事実{i}：" + "｜".join(facts[i - 1]) for i in used if 0 < i <= len(facts)]
            if rowsf:
                L += ["- この枚の要点が使う事実（設計メモ 3節の表の行）："] + rowsf
        if terms:
            L += ["- 用語・記号の決め事（設計メモ 4節）：", terms]
        api = api_lines(col(r, "本文の形"), not not_image, bool(re.match(r"\s*表", fig_cell)))
        if api:
            L += ["", "## 使う部品の書き方（これ以上の説明は要るときだけ `guide.py structures`）"] + api
        L += ["", "## 目安",
              ("- 本文：80〜100字（質問の行が上にあるので、ふつうの枚より短く）・体言止め。赤字は答えの要の語・数値に1〜2か所" if kind == "answers"
               else "- 本文：100〜150字（表は数えない）・体言止め。赤字は根拠の要の語・数値に1〜2か所"),
              "- **1行は20字まで**：長い項目は、文字列の中に \\n を入れて意味の切れ目で折る（例：\"片方の時刻を 10 ms より\\n大きくずらした組合せ\"）。"
              "1項目は2行まで。それより長いなら原稿へ回す。図の横の本文は特に短く",
              "- 本文に入れるもの：要点ごとに、数値か具体例を1つ（〔…〕の所から引く）。言い換えや中身の無い行で字数を埋めない",
              f"- 原稿：{per}前後。話し言葉（です・ます）。次の順で書く：①導入（前の枚からの語で1〜2文）②図の読み方（どこを見て、何が読めるか）"
              "③根拠（要点の数値・例を〔…〕の所から）④例か、間違いやすい所 "
              + ("⑤元の枚に戻ってどう読めばよいか（1文）" if kind == "answers" else "⑤次の枚へのつなぎ（1文）")
              + "。資料に無いことは「※（資料外の補足）」",
              "- **構成案の数値・不等号（以上・未満・≳・約）・固有名詞は変えない**。資料と違って見えたら、そこは書かずに理由を1行で返す",
              "", f"## 骨組み（parts/{n:02d}.py の出発点。TODO を書き換える）", "```python", skel[a:b].rstrip(), "```", ""]
        out[n] = "\n".join(L)
    if kind == "memo":
        out.update(quiz_cards(work, rows, text, blocks(skel), skel))
    return out


def answer_lines(work: Path, r) -> list:
    """質問回答の枚のカードに足す所：答えるコメント・元の枚の青帯と原稿・回答の書き方（references/answer-deck.md の3・4）。"""
    from scaffold import EMPTY, col, note_sections, plan
    src_n = re.search(r"\d+", col(r, "元の枚") or "")
    n0 = int(src_n.group(0)) if src_n else None
    orig = work.parent
    L = ["", "## 答えるコメント", f"- {col(r, 'コメント') or '（answers.md のコメントの列が空）'}"]
    if n0:
        try:
            _, _, rows0, _ = plan(orig)
            band = next((col(x, '青帯', '結論') for x in rows0 if x["#"] == n0), "")
        except SystemExit:
            band = ""
        notes = (orig / "notes.md").read_text(encoding="utf-8") if (orig / "notes.md").exists() else ""
        sec = note_sections(notes).get(n0)
        L += [f"- 元の枚：{n0}枚目" + (f"（青帯「{band}」）" if band not in EMPTY else "")]
        if sec:
            L += ["- 元の枚の原稿：", "", clip(notes[slice(*sec)].strip(), INLINE_MAX, f"続きは元の notes.md の「## {n0}」"), ""]
    L += ["## 回答の書き方",
          f"- 本文の1行目は `{{c:← {n0 or 'N'}枚目「選んだ部分」}}`（範囲のコメントなら `{{c:← {n0 or 'N'}枚目の図の○○}}`）とコメントの要旨。続けて答えの要点2〜4個",
          "- 本文は80〜100字・体言止め（会話文にしない：「合っています。正確には〜」→「合っている：〜」）。会話調の答えは原稿に",
          "- 原稿の1文目は「あなたは N枚目の『…』について、…と聞きましたね」（発表のモードなら「N枚目の『…』への質問です」）。※行にコメント番号と元の枚を残す",
          "- 元のスライドや原稿の誤りを突くコメントなら、答えにそれを書き、迷った所として返す（元のデッキを直すのはメイン）"]
    return L


def quiz_cards(work: Path, rows, text: str, code: dict, skel: str):
    """確認問題・解答の枚のカード（設計メモ 6節の問題・解答と、〔ゴールN・M枚目〕〔要素：…〕から）。"""
    import structures
    from scaffold import col
    items = structures.quiz_items(text)
    out = {}
    for r in rows:
        role = col(r, "役割")
        if role not in ("確認問題", "解答"):
            continue
        n = r["#"]
        ids = re.findall(r"\d+-\d+", col(r, "●見出し") + " " + col(r, "本文の要点"))
        lo_hi = [x for x in ids]
        if len(lo_hi) == 2 and lo_hi[0].split("-")[0] == lo_hi[1].split("-")[0]:
            a0, b0 = int(lo_hi[0].split("-")[1]), int(lo_hi[1].split("-")[1])
            ids = [f"{lo_hi[0].split('-')[0]}-{i}" for i in range(a0, b0 + 1)]
        L = [f"# {n}枚目のカード（{role}、{work.name}）", "",
             f"書くもの：`parts/{n:02d}.py`（下の骨組みの qa(...) に問題か解答を入れる）と `parts/{n:02d}.md`（この枚の原稿）。", ""]
        for k in ids:
            if k not in items:
                continue
            qtext, goal, slide, atext, els = items[k]
            qclean = structures.QUIZ_Q_TAG.sub("", qtext).strip()
            aclean = structures.QUIZ_A_TAG.sub("", atext).strip()
            L.append(f"## {k}")
            L.append(f"- 問題：{qclean}（確かめるゴール {goal}、根拠の枚 {slide}枚目）")
            if role == "解答":
                L.append(f"- 解答：{aclean}")
                L.append(f"- **削ってはいけない要素**：{'／'.join(els) or '（6節に無い）'}。スライドの解答にも原稿にも、全部を入れる")
                L.append(f"- 原稿：解答を言ったあと、「{slide}枚目で見たとおり」と根拠の枚に戻って1〜2文で理由を言う")
            L.append("")
        if role == "確認問題":
            L.append("- 原稿：解き方のヒントは言わない。どの枚を見返せばよいかだけを言う（根拠の枚）")
        a, b = code.get(n, (0, 0))
        L += ["", "## 骨組み", "```python", skel[a:b].rstrip(), "```", ""]
        out[n] = "\n".join(L)
    return out


def main(argv=None):
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
