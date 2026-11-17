# AI_Literacy — AI講座（sensei-slides の講座で作成）

What generative AI actually computes, taught by the AI lecturer for the requester (one lecture). 各回はスライド（`0N_<題>_スライド.pptx`）と
原稿HTML（`0N_<題>_原稿.html`：スライドと読み上げ原稿を横並びで読む）。読むのは原稿HTMLだけでよい。

## 学習者とゴール

- 軽さ：念入り
- テーマへの詳しさ：初学者
- 学習者のプロフィール（任意）：Has used chat AIs, but does not know how they work inside. No technical background assumed.
- ゴール：Be able to say what a generative AI is computing, and to spot plausible-looking mistakes and check them while using it.
- 言語：英語（the language of the request. Slides, script and quiz are all in English）
- 回数：全1回（1回ずつ作る。前の回のコメントと答えを読んでから次の回を作る）
- テンプレート：テンプレート2
- 資料：なし（テーマだけ）。Facts are checked in the design memo of each session; no local source to bridge to.
- 依頼文：`../request.txt`（英語）。読むのは依頼者本人

## 原稿HTMLのコメント

- 書き出しの保存先: このフォルダ（AI_Literacy）
- 講座ID: AI（コメントの書き出しファイル名の頭に付く。例 `AI01_<題>_コメント.json`。別の講座には別のIDを付ける）
- 原稿HTMLの「書き出し」でダウンロードフォルダに保存され、AI が読むときに講座ID「AI」のコメントだけをこのフォルダへ移す
- 質問への回答は別デッキ `0N_<題>_質問回答_スライド.pptx`・`_質問回答_原稿.html`。回答デッキへのコメントは同じ回答デッキの末尾に足す
- 確認問題への答え（「1-1 に答える」）は添削する。添削スライドには元の問題文も載せる

## 全体の地図

| 回 | 題 | ねらい | 言えるようになること | 前提 | 予告 |
|---|---|---|---|---|---|
| 1 | What a Chat AI Computes | 仕組みが分かる | You can say that the model computes, one token at a time, a probability for every possible next piece of text and picks from it; why that makes fluent-but-wrong answers (made-up facts, sources, numbers) natural rather than rare; and how to check an answer (ask for the source and open it, re-ask, verify numbers yourself). Topics: tokens; next-token probabilities; learning from large text by predicting the next word; the chat as a continued document (prompt + history = context); sampling and why answers vary; "plausible" ≠ "true"; a checking routine. 橋渡し：the phone keyboard's next-word suggestion, scaled up and made to write whole replies; the naive view "it looks things up / it knows" is the one this session breaks | — | — |

## 決め事（全回共通）

- 原稿は **AI講義モード**：話し手＝講師のAI、聞き手＝学習者（「あなた」と呼ぶ。英語では "you"）。問いかけ、学習者の背景への橋渡しを入れる。
  確認問題は「あなたならどう答えますか」、答えの添削は「あなたは〜と答えました。〜」（英語で書く）
- タイトルは全スライド「第N回 <題>」（英語では "Lecture N: <title>"）。構成：表紙＋本文（10〜15枚目安）＋確認問題（3問/枚）→解答（同じ区切り）
- 伏線は本文に青字「→ 第N回：…」。全1回なので伏線は置かない
- 出典は原稿の ※（出典）行、確かめられなかったものは ※（要確認）行
- PDF は作らない（原稿HTMLがあるため）
- 記号・図の向き・色：例文「The capital of Australia is」を回をまたいで使い回す（Canberra＝正しい続き・青、Sydney＝もっともらしい誤り・赤）／<回を作るたびに足す>

## つまずき一覧（質問回答のたびに足す。次の回の設計メモで読む）

| 回・問題 | 取り違えたこと・抜けていたこと | 補った場所 |
|---|---|---|
