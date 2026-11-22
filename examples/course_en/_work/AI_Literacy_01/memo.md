# 設計メモ：第1回 What Generative AI Actually Computes（AI_Literacy）

作業用（ユーザーは読まない）。スライドを作るときは、このメモを講義録の代わりに使う。2節の表は構成案（outline.md）を兼ねる。

## 1. この回のゴールと前提

- ねらい：仕組みが分かる（既定の型「素朴な見方を崩す」）
- 言えるようになること（3つまで）：
  1. 生成AIは答えを調べて返すのではなく、次のトークンの確率を計算し、1つ選んで付け足すことを繰り返している、と言える
  2. 流暢さと正しさが別物で、存在しない出典・数値・人名が出る理由を説明できる
  3. 使うときに確かめる所（人名・数値・出典）と確かめ方（原典を開いて主張を探す）を挙げられる
- 道筋：Tokens → Token odds → Pick, repeat → What to check
- 前提にする回と、その回の何を使うか：なし（全1回）
- 予告する回：なし
- 聞き手の前提知識：知っている＝チャットAIを使ったこと、スマホの予測変換／知らない＝トークン、確率の計算、学習、temperature
- 聞き手のテーマへの詳しさ：初学者
- 丁寧さ：0
- 言語：英語（表のタイトル・●見出し・青帯・本文の要点の列と6節の問題・解答は英語）
- 答えの位置：後

話の筋

| 筋 | 型 | 一文 | 枚 |
|---|---|---|---|
| 状況 | — | You ask a chatbot and get a fluent answer, often with sources, in seconds | 2 |
| 複雑化 | 意外 | In 2023, lawyers cited six court cases that ChatGPT had made up | 2 |
| 問い | 何が | What does generative AI actually compute, if it can write a source that does not exist? | 3 |
| 答え | — | It computes how likely each next token is, picks one, appends it and repeats, so it scores what is likely, not what is true | 10 |
| たとえ | — | It is your phone's next-word suggestion tapped over and over to the end of a reply: it finishes sentences, it never checks them | 10 |
| 対立 | — | Is a fake source a search that slipped, or a likely continuation that never searched? | 8 |
| それで | — | One fact got three different dates and fake papers exist nowhere to find, so the slipped-search view goes: fluency is no sign of truth, and you check names, numbers and sources | 13 |

話の型：素朴な見方を崩す

## 2. 話の順番（構成案を兼ねる。表紙＋本文13＋問題2＋解答2＝18枚）

| # | ●見出し | 前の枚から | 青帯（結論） | 図で見せるもの | 本文の要点 | ノートへ・橋渡し | 本文の形 | 役割 |
|---|---|---|---|---|---|---|---|---|
| 1 | 表紙 | — | — | — | Lecture 1: What Generative AI Actually Computes／——From next-word guesses to plausible mistakes／For chat AI users | — | — | 表紙 |
| 2 | Six cases that never existed | — | In 2023, lawyers cited six cases ChatGPT made up | 違い：比較：What the lawyers assumed（looked up by ChatGPT、real court rulings、safe to cite）と What actually happened（text written by ChatGPT、six cases that never existed、a $5,000 fine） | Case：Mata v. Avianca, New York, 2023〔事実1〕 / Case：six fake cases, a $5,000 fine〔事実1〕 / Belief：a lawyer thought it "could not" fabricate〔事実2〕 ⇒ ★Fluent, yet invented | — | ラベル | 本文 |
| 3 | Today's question | だから（手段） | Your phone keyboard already predicts your next word | 流れ：流れ図：You type "See you" → The keyboard offers soon, later, tomorrow → You tap one | You tap its next-word guesses daily〔事実3〕 / Have you trusted a sure-sounding reply? / ⇒ ★What does generative AI actually compute? | — | 帰結 | 本文 |
| 4 | Step 1: tokens | そして（詳しく） | Text is cut into tokens: 100 tokens ≈ 75 words | 仕組み：模式図：the sentence "Chatbots predict text." cut into four boxes Chatbots / predict / text / . ；読み方：1 box = 1 token (splits shown are an illustration) | Token：a word, part of a word, or a mark〔事実4〕 / Size：about 4 letters of English text〔事実5〕 / Size：other languages split differently〔事実5〕 | — | ラベル | 本文 |
| 5 | Step 2: probabilities | そして（詳しく） | Each possible next token gets a probability | 仕組み：模式図：after "The capital of France is", candidate next tokens Paris, a, the, located with bars of different lengths and no numbers；読み方：longer bar = rated more likely to come next | Trained on 300 billion tokens〔事実6〕 / Tuned to predict the next token〔事実7〕 / ⇒ ★A table of likely next tokens | — | 帰結 | 本文 |
| 6 | Step 3: pick and repeat | そして（次へ） | It picks one token, appends it, and repeats | 流れ：流れ図：Text so far → Probabilities for each next token → Pick one, with some chance → Append it and go again | Each pick involves chance〔事実8〕 / Higher temperature = more random〔事実8〕 / ⇒ ★Same question, a different reply | — | 帰結 | 本文 |
| 7 | Plausible but fake | しかし（意外） | GPT-3.5 invented 55% of citations, GPT-4 18% | 比べる：棒グラフ：データ1 | Short literature reviews, 2023〔データ1〕 / Newer model: fewer, not zero〔データ1〕 / ⇒ ★Fluent reference ≠ real reference | — | 帰結 | 本文 |
| 8 | A search that slipped? | しかし（疑い） | Asked 3 times, a model gave 3 different wrong dates | 違い：比較：A failed lookup（finds a real source、same answer each time、wrong in places）と A likely continuation（may name a source that never existed、a new answer each try、fluent either way） | Test：Kalai's birthday, to DeepSeek-V3〔事実9〕 / Test：told to answer only if known〔事実9〕 / Reading：a lookup gives 1 answer〔講師のまとめ〕 ⇒ ★Not a search that slipped | — | ラベル | 本文 |
| 9 | Why it guesses | だから（帰結） | Tests reward a 1-in-365 guess over "I don't know" | 印象：大きな数字：1/365（chance that a guessed birthday is right） | Rare facts：seen once in training text〔事実11〕 / Rare facts：no pattern to learn from〔事実11〕 / Grading："I don't know" scores zero〔事実10〕 ⇒ ★So guessing pays | — | ラベル | 本文 |
| 10 | The answer | だから（問い） | It computes what is likely next, not what is true | 仕組み：模式図：the pick-and-repeat loop (text so far → probabilities → pick → append) with a dashed, crossed-out box "Check: is it true?" that the loop never passes through；読み方：dashed box = a step the loop does not have | Answer：next-token odds, pick, repeat〔講師のまとめ〕 / Answer：no step checks the world〔講師のまとめ〕 / Like：your keyboard, tapped to the end〔講師のまとめ〕 ⇒ ★Likely ≠ true | — | ラベル | 本文 |
| 11 | Where to check | だから（手段） | Check the names, numbers and sources you rely on | 判定：判定の流れ図：Only wording or ideas?→ はい：Use it as a draft／いいえ：Will you rely on a name, number or source?→ はい：Check it in the original／いいえ：Use it, marked unchecked | Risky：names, dates, numbers, sources〔事実11〕 / Risky：facts you will repeat〔講師のまとめ〕 / Safer：wording, structure, ideas〔講師のまとめ〕 | — | ラベル | 本文 |
| 12 | How to check | そして（次へ） | Only 7% of 115 references were real and accurate | 内訳：帯グラフ：データ2 | 1. Search the exact title 2. Match authors, year, journal 3. Find the claim inside〔事実12〕 / GPT-3.5 (ChatGPT), medical papers, 2023〔データ2〕 / ⇒ ★A real paper may not say it | — | 手順・帰結 | 本文 |
| 13 | Back to the lawyers | だから（帰結） | The fake cases were likely text, not failed searches | 流れ：流れ図：Ask for supporting cases → Likely tokens: names, courts, years → A fluent citation → Not in any court record | Computed：likely next tokens〔講師のまとめ〕 / Missed step：opening the cases〔事実1〕 / Missed step：none of the six existed〔事実1〕 ⇒ ★Fluent says nothing about true | — | ラベル | 本文 |
| 14 | Summary | — | Likely next token, not the truth | — | Looks it up → Guesses tokens / Fluent = true → Fluent = likely / Cited = real → Open the source | — | — | まとめ |
| 15 | Check questions (1-1 to 1-3) | — | — | — | 1-1〜1-3 | 解答は17枚目 | — | 確認問題 |
| 16 | Check questions (1-4 to 1-6) | — | — | — | 1-4〜1-6 | 解答は18枚目 | — | 確認問題 |
| 17 | Answers (1-1 to 1-3) | — | — | — | 要素を削らない | 全文 | — | 解答 |
| 18 | Answers (1-4 to 1-6) | — | — | — | 要素を削らない | 全文 | — | 解答 |

青帯だけを上から読む：In 2023, lawyers cited six cases ChatGPT made up → Your phone keyboard already predicts your next word → Text is cut into tokens: 100 tokens ≈ 75 words → Each possible next token gets a probability → It picks one token, appends it, and repeats → GPT-3.5 invented 55% of citations, GPT-4 18% → Asked 3 times, a model gave 3 different wrong dates → Tests reward a 1-in-365 guess over "I don't know" → It computes what is likely next, not what is true → Check the names, numbers and sources you rely on → Only 7% of 115 references were real and accurate → The fake cases were likely text, not failed searches → Likely next token, not the truth

## 3. 事実と出典

| 主張 | 値・式 | 出典（書名・URL） | 確認 |
|---|---|---|---|
| 1. Mata v. Avianca: lawyers filed a brief citing six court cases that ChatGPT made up; the court (Judge P. Kevin Castel, S.D.N.Y.) fined them | six fictitious cases; $5,000 sanction, June 2023; the court found the lawyers ignored signs the citations were fake (why it happened: they did not open the cases) | ABA Journal "Lawyers who 'doubled down' and defended ChatGPT's fake cases must pay $5K, judge says" (2023) https://abajournal.com/web/article/lawyers-who-doubled-down-and-defended-chatgpts-fake-cases-must-pay-5k-judge-says ; Bloomberg Law "Phony ChatGPT Brief Leads to $5,000 Fine for NY Lawyers" (2023) https://news.bloomberglaw.com/litigation/chatgpt-phony-legal-filing-case-gets-lawyers-a-5-000-fine | ○ |
| 2. A lawyer's belief about ChatGPT | testified he was "operating under the false perception that [ChatGPT] could not possibly be fabricating cases on its own" | ABA Journal (2023), same article as row 1 | ○ |
| 3. A phone keyboard's predictive text suggests next words from what you typed | iPhone: "As you type text on the iPhone keyboard, Siri predicts your next word"; tap a suggested word to accept it | Apple "iPhone User Guide: Use predictive text on iPhone" https://support.apple.com/guide/iphone/use-predictive-text-iphd4ea90231/ios ; Apple Support "How to use Auto-Correction and predictive text" https://support.apple.com/104995 | ○ |
| 4. What a token is | a character, part of a word, a whole word, or punctuation; spaces affect how text is split | OpenAI Help Center "What are tokens and how to count them" (article 4936856) https://help.openai.com/en/articles/4936856-what-are-tokens-and-how-to-count-them | ○ |
| 5. Token size in English (rule of thumb, not exact; other languages differ) | 1 token ≈ 4 characters ≈ 3/4 word; 100 tokens ≈ 75 words | OpenAI Help Center "What are tokens and how to count them" https://help.openai.com/en/articles/4936856-what-are-tokens-and-how-to-count-them | ○（言い換え：3/4 word per token × 100 tokens = 75 words。出典も両方を書いている） |
| 6. GPT-3 size and training data | 175 billion parameters; trained on a total of 300 billion tokens | Brown T. et al. "Language Models are Few-Shot Learners" arXiv:2005.14165 (2020), abstract; Table 2.1 caption ("All models were trained for a total of 300 billion tokens") https://arxiv.org/abs/2005.14165 | ○ |
| 7. A model like GPT-3 is autoregressive: it predicts each next token from the tokens before it, and a reply is built by repeating that | why: training adjusts the parameters so that the actual next token in the training text gets a high probability (pretraining = next-word prediction) | Brown et al. 2020 abstract ("an autoregressive language model"); Kalai A.T. et al. "Why Language Models Hallucinate" arXiv:2509.04664 (2025) https://arxiv.org/abs/2509.04664 | ○ |
| 8. Temperature setting | higher values (e.g. 0.8) make output more random; lower values (e.g. 0.2) more focused and deterministic. why: each token is drawn by chance from the probabilities, so picks differ between runs | OpenAI API reference wording, quoted in OpenAI Developer Community "Temperature docs for 1 max vs 2 max" (2023) https://community.openai.com/t/temperature-docs-for-1-max-vs-2-max/309112 | ○（公式の API リファレンスの頁そのものは開いていない。範囲 0〜2 か 0〜1 かは出典で違うので数値の範囲は載せない） |
| 9. Birthday test in Kalai et al. 2025 | asked DeepSeek-V3 for Kalai's birthday ("answer only if known"); 3 attempts gave 3 different wrong dates | Kalai A.T., Nachum O., Vempala S., Zhang E. "Why Language Models Hallucinate" arXiv:2509.04664 (2025-09-04) https://arxiv.org/abs/2509.04664 | ○ |
| 10. Grading rewards guessing | a guessed birthday has a 1-in-365 chance of being right; "I don't know" earns zero points, so accuracy-only tests reward guessing over admitting uncertainty | OpenAI "Why language models hallucinate" (2025-09) https://openai.com/index/why-language-models-hallucinate/ | ○（言い換え：1/365 ≈ 0.27% > 0 → 当て推量の期待点は「わからない」の0点より高い） |
| 11. Rare, arbitrary facts have no learnable pattern | facts like birthdays that appear once in training data: if 20% of birthday facts appear exactly once, base models are expected to hallucinate on at least 20% of birthday facts. why: next-token prediction learns patterns, and a fact seen once has no pattern to generalize from | Kalai et al. 2025, arXiv:2509.04664 (same as row 9) | ○ |
| 12. How to verify an AI-given citation | search the title in a library catalog, a database or Google Scholar; verify title, author, journal, volume, dates, DOI; verify the content the AI claimed is actually in the source | Centre College Library "Evaluating AI" https://library.centre.edu/AI/evaluate (2026-11 閲覧) | ○ |

## 3b. データ（data.py merge が data_N.md から入れる。図の案から「データN」で指す。値・単位・注記はこのとおりに描く。驚きの事実は、使うなら3節の事実の行に写す）

### データ1：Share of ChatGPT-generated citations that do not exist (GPT-3.5 vs GPT-4)
- 驚き：AI が付けた参考文献は「調べて持ってきた本物」だと思われがちだが、GPT-3.5 では半分以上、GPT-4 でも約5件に1件が存在しない文献だった
- 問いの候補：なぜ AI は、存在しない文献をもっともらしく書けるのか？
- 単位：％
- 分母：各モデルが短い文献レビュー（42の学術テーマ）に付けた参考文献
- 時点：2023年3〜4月に生成、2023年9月発表
- 出典：Walters W.H. & Wilder E.I. "Fabrication and errors in the bibliographic citations generated by ChatGPT" Scientific Reports 13, 14045 (2023) https://www.nature.com/articles/s41598-023-41032-5
- 確認：○
- 別の読み方：2023年の2モデル・学術文献という特に難しい依頼での値で、今のモデルやWeb検索つきの使い方では低いかもしれない（新しいモデルで下がっても0ではない、が読める範囲）
| 区分 | 値 |
|---|---|
| GPT-3.5 | 55 |
| GPT-4 | 18 |

### データ2：What 115 ChatGPT-3.5 references in medical papers turned out to be
- 驚き：本物に見える参考文献のうち、存在して中身も正しいものは7%だけだった
- 問いの候補：もっともらしい文献のうち、どれだけが本当に正しいか？
- 単位：％
- 分母：ChatGPT-3.5 が作った30本の短い医学論文の参考文献115件
- 時点：2023年4月12日に生成、2023年5月発表
- 出典：Bhattacharyya M. et al. "High Rates of Fabricated and Inaccurate References in ChatGPT-Generated Medical Content" Cureus 15(5): e39238 (2023) doi:10.7759/cureus.39238 https://pmc.ncbi.nlm.nih.gov/articles/PMC10277170/
- 確認：○
- 別の読み方：1つのモデル（GPT-3.5）・医学の題・115件だけの小さな調べで、今のモデルには当てはまらないかもしれない
| 区分 | 値 |
|---|---|
| Fabricated | 47 |
| Real but inaccurate | 46 |
| Real and accurate | 7 |

## 4. 用語・記号の決め事（README の決め事に足すもの）

- token（トークン）、next-token probability、temperature の呼び方をこの3つにそろえる。色：モデルの通常の流れは青、存在しない・作られたもの（fake）は赤
- 手当てで足した語の一言：training（学習：読ませた文で実際に次に来たトークンに高い確率が付くよう設定を直すこと）、temperature（熱とは無関係。引くときの偶然の大きさの設定）、literature review（研究のまとめに参考文献の一覧を付けた文）、tests（AI モデルを正答の数で採点する試験）。ChatGPT-3.5 と書かず GPT-3.5 (ChatGPT) にそろえる
- 固有の名前の一言：Mata v. Avianca（2023年の米国ニューヨークの裁判）、ChatGPT・GPT-3.5・GPT-4・GPT-3（OpenAI の言語モデル。GPT-3.5・GPT-4 は ChatGPT の中で動く版）、DeepSeek-V3（DeepSeek 社の言語モデル）、Kalai（2025年の論文の筆頭著者）、Google Scholar（論文を探す検索サービス）

## 5. 図の案（任意）

なし

## 6. 確認問題と模範解答

### 問題
1-1. What is a token, and about how many English words do 100 tokens make? 〔ゴール1・4枚目〕〔型：定義〕
1-2. You ask a chatbot the same question twice and get two different replies. Using the loop, explain why. 〔ゴール1・6枚目〕〔型：仕組み〕
1-3. A friend says: "The chatbot cited a paper that does not exist, so its search must have failed." What is wrong? 〔ゴール2・8枚目〕〔型：誤り指摘〕
1-4. Compare the 2023 study's fake-citation rates for GPT-3.5 and GPT-4. What do they tell you about newer models? 〔ゴール2・7枚目〕〔型：比べる〕
1-5. A chatbot says "a 2021 study found 62% of students..." and you will quote it in a report. What do you check, and how? 〔ゴール3・12枚目〕〔型：当てはめ〕
1-6. What does generative AI actually compute? Answer with the one-line answer and the analogy. 〔題の問い〕〔ゴール1・10枚目〕〔型：仕組み〕

### 解答
1-1. A piece of text (word, part of a word, mark). 100 tokens ≈ 75 words, because 1 token ≈ 3/4 word. 〔要素：a piece of text／about 75 words〕
1-2. Each pick is drawn by chance from the probabilities, and because each pick changes what follows, replies differ. 〔要素：picks involve chance／each pick changes what follows〕
1-3. It wrote likely tokens, not a search, because asked one birthday 3 times, a model gave 3 different dates; a lookup would not. 〔要素：no lookup, a likely continuation／3 different dates〕
1-4. 55% vs 18% fake: newer models invent fewer but not zero, so you still check, because fluency is no proof. 〔要素：55% vs 18%／fewer, not zero〕
1-5. The study, year and 62%, because names and numbers are where it guesses: search the title, open it, find the claim. 〔要素：name, number, source／open it and find the claim〕
1-6. Next-token odds: it picks one, appends, repeats, so it scores likely, not true. Like your keyboard's guess tapped to the end. 〔要素：next-token probabilities, pick and repeat／keyboard guess tapped to the end〕

## 7. 前の回から反映すること

なし

## 8. 迷った所とレビューの反映

- 迷った所：
  - 3枚目のつなぎを「だから（手段）」にした（冒頭の事件から「確かめるために身近な予測変換から入る」の意）。問いの一文はこの枚の赤字の要点に載せた
  - 4・5枚目の模式図のトークンの切れ目と候補の並びは説明のための例（実際のトークナイザーの出力ではない）。図の中に "illustration" と断る
  - 8枚目の比較の表の中身（failed lookup／likely continuation の3項目ずつ）は講師のまとめ。根拠は事実9（同じ問いに3つの違う日付）
  - 事実8（temperature）は公式の API リファレンスの頁そのものではなく、その文言を引いたフォーラムの頁で確かめた
  - 数字の組は2つとも2023年の古いモデル（GPT-3.5・GPT-4）。今のモデル・Web検索つきでは低い可能性を、7・12枚目の原稿で限りとして言う
- レビューの反映：
- 第N回に回す点：なし

## 9. 引っかかりへの手当て

- [2] 本文の Belief の主がない → 本文を「a lawyer thought it "could not" fabricate」にし、原稿に「One lawyer testified he thought ChatGPT could not possibly make up cases.」（事実2）。経験の問いは3枚目にあるので、2枚目の原稿の同じ問いは外した
- [5] training の中身・確率の出どころ → 原稿に「Training: the model reads huge amounts of text, and its settings are adjusted until the token that actually came next gets a high probability.」（事実7の言い換え）
- [6] pick の像（等しく引く） → 原稿に「Likely tokens are picked most often, unlikely ones now and then; it is not an even draw.」（事実8）
- [6] temperature の像（熱） → 原稿を「A setting called temperature, nothing to do with heat, controls how much chance there is: higher means more random, lower means more focused.」に（事実8）
- [7] literature review・GPT-3.5/GPT-4 の中身 → 原稿に「summaries of research with a reference list」と「two versions of the model behind ChatGPT」
- [8] 検索なら同じ答えの理由・ループなら別の答えの理由（遠い：6枚目）・DeepSeek-V3 → 原稿に「since it reads the same stored record」「because each pick involves chance, as in step 3」「another company's chat model」
- [9] 1度しか出ない事実に規則が無い理由・tests の中身 → 原稿に「Training learns from what repeats」と「the tests used to score models count only right answers」、結びを「So such tests reward guessing over admitting it does not know」に（事実10・11の言い換え）
- [11] 名前・数はいつも珍しいわけではない（範囲） → 原稿を「Exact names, dates, numbers and sources are often rare facts, seen once in training text, where the model guesses.」に言い換え（事実11）
- [12] 本物でも中身があるとは限らない・ChatGPT-3.5 の呼び名の揺れ → 本文の ⇒★ を「A real paper may not say it」、本文を「GPT-3.5 (ChatGPT)」に。原稿に「A real source may still not say what the reply claims.」と「the older model from slide 7」（事実12・データ2）
- 採らなかったもの：なし（深の行は書いていない）

- 残す△：原稿の字数（5〜9・11・12枚目が400字を少し超える。推論距離の手当て（training・temperature・検索とループの違いの理由など）を原稿に入れたためで、英語の原稿は1分あたりの語数で見ると収まる見込み）
- 残す△：冒頭の問い（冒頭の謎は学習者に近い実際の事件（事実1）で立て、データ1は7枚目のしかしで1回だけ見せる）
- 残す△：入口の経験（3枚目の要点に学習者の経験の問い「Have you trusted a sure-sounding reply?」と予測変換を置いた。英語の文のため検査が拾えていない）
- 残す△：説明の無い英字の名前（英語のデッキのため、普通の英単語まで拾われる。固有の名前は4節に足した）
