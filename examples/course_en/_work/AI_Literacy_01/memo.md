# 設計メモ：第1回 What a Chat AI Computes（AI_Literacy）

作業用（ユーザーは読まない）。スライドを作るときは、このメモを講義録の代わりに使う。2節の表は構成案（outline.md）を兼ねる。
スライドは テンプレート2（結論タイトル）で組む。結論（青帯の列）は上の大きな一文に出るので、本文の最後に「⇒ 赤字の結論」を繰り返す帰結の形は使わず、根拠を見せる形（手順・ラベル・場合分け・問い・展開）にする。赤字は結論の言い換えではなく、根拠の要の語・数値に。

## 1. この回のゴールと前提

- ねらい：仕組みが分かる
- 言えるようになること（3つまで）：
  1. The model computes, one token at a time, a probability for every possible next token and draws one; the chat itself is one document it keeps continuing, and the draw is why answers vary
  2. Why fluent-but-wrong answers (made-up facts, sources, numbers) are natural rather than rare
  3. How to check an answer: open the cited source, re-ask in a new chat, and recompute numbers yourself
- 前提にする回と、その回の何を使うか：なし（チャットの AI を使ったことがある）
- 予告する回：なし（全1回）
- 聞き手の前提知識：知っている＝チャットの AI に質問して答えをもらうこと・スマホのキーボードの次の語の候補・割合（％）・検索エンジン／知らない＝言語モデル・トークン・確率の分布・パラメータ・学習と調整・サンプリング・温度・ハルシネーション・一次資料・知識の締め切り
- 聞き手のテーマへの詳しさ：初学者
- 丁寧さ：0

- 言語：英語（README の「学習者とゴール」から。表のタイトル・●見出し・青帯・本文の要点の列と6節の問題・解答は英語）
- 答えの位置：後
- テンプレート：テンプレート2

話の筋（references/story.md。素朴な見方は2枚目で立て、7枚目の意外で崩して問いを立て、10枚目で答える）

| 筋 | 型 | 一文 | 枚 |
|---|---|---|---|
| 状況 | — | You type a question into a chat AI and it replies in fluent sentences, as if it had looked the answer up | 2 |
| 複雑化 | 意外 | But 55% of the references GPT-3.5 gave did not exist, and 18% of GPT-4's (2023) | 7 |
| 問い | なぜ | If it reads so fluently, why does it make things up so confidently? | 7 |
| 答え | — | Nothing in it checks facts: it draws likely continuations of its training text, so facts rare in that text, facts after its cutoff, and guesses that tests reward come out fluent but wrong | 10 |
| 語り手 | — | 学習者自身の疑問：すらすら答えるのに、なぜときどき堂々と間違うのか | — |

話の型：素朴な見方を崩す

## 2. 話の順番（構成案を兼ねる。表紙＋本文11＋問題2＋解答2＝16枚）

| # | ●見出し | 前の枚から | 青帯（結論） | 図で見せるもの | 本文の要点 | ノートへ・橋渡し | 本文の形 | 役割 |
|---|---|---|---|---|---|---|---|---|
| 1 | 表紙 | — | — | — | Lecture 1: What a Chat AI Computes／— Fluent is not the same as true | この回のゴール3つ | — | 表紙 |
| 2 | Predicting the next token | — | It gives every possible next token a probability, then draws one | 比べる：棒グラフ：next-token candidates after "The capital of Australia is" (Canberra, Sydney, Melbourne, other; probabilities are an example)〔事実16〕 | 1. Read all the text so far 2. Give every token in its vocabulary a probability (a token is a word or a piece of one, next slide, and GPT-2 has ★50,257 of them) 3. Draw one, weighted by its probability, append it, repeat〔事実1・事実3〕 / Your guess：it looked the answer up. Did it? | 橋渡し：スマホのキーボードの次の語の候補〔事実17〕を大きくして、返事を丸ごと書かせたもの。素朴な見方「調べて・知っていて答える」を本文の最後の行で聞き手に立てさせる（7枚目で崩す）。Sydney は最大の都市で首都ではない〔事実18〕 | 手順・ラベル | 本文 |
| 3 | Tokens, not words | そして（詳しく） | One English token is about 4 characters of text | 仕組み：模式図："The capital of Australia is" split into token boxes, and below it a rare word (Dubbo) split into two pieces (the split is an example; it differs by model。横長の図なので上に文・下に図：2つのラベルを横に並べ、図を下に横いっぱいに) | Token：a word or a piece of one; rare words are split into pieces〔事実3〕 / Rule of thumb：1 token ≈ ★4 characters ≈ ¾ of an English word〔事実4〕 | 2枚目の「次の候補」の単位はトークンだと指す。Length limit（counted in tokens, GPT-3 (2020): 2,048〔事実1〕）は原稿で（文の塊は2つまで）。各モデルで分け方が違う | ラベル | 本文 |
| 4 | Learning by guessing | そして（次へ） | Training tunes GPT-3's 175 billion numbers to predict text | 流れ：流れ図：text with the next token hidden → model guesses → compare with the real token → adjust the numbers → repeat (PowerPoint shapes) | Scale：175 billion numbers (parameters); it read about ★300 billion tokens drawn from web pages, books and Wikipedia〔事実1・事実2〕 / What it learns：how text continues, not a list of facts〔事実1〕（当てて・比べて・数を直す手順は流れ図が見せる） | パラメータ＝学習で値を決める、モデルの中の数（175 billion は青帯）。300B は学習で読んだトークン数で、データの量そのものではない（※：Common Crawl・WebText2・Books・Wikipedia の合計 約 499B から重みづけして抜き出し〔事実2〕）。10枚目の答えの前提として「事実の一覧ではない」を本文に | ラベル | 本文 |
| 5 | A chat is one document | そして（次へ） | The whole chat is resent each turn; the reply continues it | 仕組み：模式図：the chat as one long document — [instructions][You: …][AI: …][You: …][AI: ▢ next token] | Each turn：instructions + your messages + its replies, ★sent in full〔事実6〕 / Tuning：plain GPT-3 just continues text, but after tuning with human example replies and human rankings of its replies, the 1.3B InstructGPT was preferred over the 175B GPT-3〔事実5〕 | 4枚目の次に調整が来る理由：文の続きを当てるだけのモデルは、質問に答える形で続けるとは限らない。調整＝人が返事に付けた順位を使い、好まれる返事が出やすいよう数を直す（RLHF の略語はスライドに出さない）。会話の記憶は、毎回まるごと渡し直す文書 | ラベル | 本文 |
| 6 | Why answers vary | しかし（限り） | Each token is a weighted draw, so replies can vary | 比べる：棒グラフ：the capital candidates at temperature 0.5, 1 and 2 (computed from the example probabilities, with "other" counted as one candidate; note: like a lottery, 62 of 100 tickets say Canberra。図が主役：左に大きく、右の列に読み方)〔事実16〕 | Temperature：a dial applied before the draw, where low sharpens the probabilities and high flattens them〔事実8〕 / Low (0.5)：Canberra 84%, Sydney 14%〔事実16〕〔講師の概算〕 / High (2)：Canberra 44%, ★Sydney 28%〔事実16〕〔講師の概算〕（Melbourne 16% と、Always the top token：text turns dull and repetitive, so models draw instead〔事実7〕は原稿へ） | 計算：T=0.5 で 84/14/1/0.5%、T=1 は元の 62/25/8/5%、T=2 で 44/28/16/12%。チャットのアプリでは利用者は温度を変えられず、提供側が決めた値で引いている（原稿の1文）。同じ質問でも新しいチャットで違う答え。12枚目の「聞き直し」の伏線 | ラベル・場合分け | 本文 |
| 7 | Plausible is not true | しかし（意外） | 55% of the references ChatGPT (GPT-3.5) gave did not exist (2023) | 比べる：棒グラフ：データ2 | Did it look them up?⇒ Made up: GPT-3.5 ★55%, GPT-4 18% of all references each gave (636 in all, 2023)〔データ2〕 / Hallucination：generated text that is nonsensical or unfaithful to the source〔事実9〕 ⇒ Fluent and sure, yet wrong: why? | 予想を先に：「AI が挙げた文献のうち、実在しないのは何割だと思いますか」。2枚目の「調べて答えた？」をここで崩し、最後の行で今日の問いを立てる。Mata v. Avianca（"is this case real?" に yes、$5,000 の制裁金〔事実10〕）は原稿で（文の塊は2つまで）。2023年の版で、今のモデルや検索つきでは下がる（限りは原稿で）。Hallucination の出典の定義は「与えた資料に忠実でない」で、この講座は事実に合わない内容にも広げて使う、と原稿で断る | 問い・ラベル | 本文 |
| 8 | Newer is not error-free | そして（並べる） | o3 made up answers to 33% of PersonQA questions (o1: 16%) | 比べる：棒グラフ：データ3 | Older o1 (made up 16%, right 47%) → newer o3 (made up ★33%, right 59%)〔データ3〕 / PersonQA (Apr 2025)：questions about real people; o4-mini made up 48%; one company, one test〔データ3〕 | 1社・1つの試験の結果。新しいから確かめなくてよい、とは言えない | 展開・ラベル | 本文 |
| 9 | Guessing beats "I don't know" | そして（並べる） | o4-mini rarely said "I don't know" (1%) and got 75% wrong | 比べる：棒グラフ：データ1 | Says "I don't know" 52% (gpt-5-thinking-mini) → right 22%, wrong 26%, out of all SimpleQA questions (short fact questions, Sep 2025)〔データ1〕 / Says "I don't know" 1% (o4-mini) → right 24%, ★wrong 75%, same questions〔データ1〕 / ⇒ Guessing adds few right answers but many wrong ones | 2025年9月の OpenAI の発表で、同じ会社の2モデル・答えの短い問いだけ（限り）。正解はほぼ同じ（22 と 24）なのに間違いは約3倍。自信のある言い方は確かさの印ではない。理由は次の10枚目で | 箇条 | 本文 |
| 10 | Why it goes wrong | だから（問い） | Nothing checks facts, so rare facts come out fluent but wrong | 比べる：積み上げ棒：BLOOM-176B on TriviaQA, a rare fact (about 10 relevant pretraining documents: right ≈25%, not right ≈75%) vs a common fact (about 10,000: right >55%) (read from Kandpal Figure 1。2点だけで、外れの割合は 100 から引いた値)〔事実11・事実19〕 | No step checks facts：probabilities come from how text usually continues, not from a fact list〔講師のまとめ〕 / Rare facts：few training documents → ★low accuracy (≈10 documents: ≈25% right; ≈10,000: >55% right) ⇒ the right continuation never gets a high probability〔事実11・事実19〕 | 原稿の1文目で7枚目の問い「なぜ堂々と間違うのか」に戻る（7〜9枚目の3つをまとめて）。1行目は講師のまとめ（出典の印なし。原稿で「ここからは講師のまとめ」と断る）。Cutoff（every model has one; GPT-4 (2023): September 2021〔事実12〕）と Test scores（tests rate a guess above "I don't know"〔事実13〕）は主題（まれな事実）からずれるので原稿で（文の塊は2つまで）。見たことの少ない事実は、正しい続きの確率が高くならない | ラベル | 本文 |
| 11 | Open the source | だから（手段） | Open the source and find the sentence yourself | 判定：判定の流れ図：Is a source given? → Can you open it? → Does it say this claim? → use it / mark "unverified" | 1. Ask for the source 2. Open it yourself (title, authors, DOI: the paper's ID) 3. Find the sentence that supports the claim〔講師のまとめ〕 / Why：even search-based legal AIs (they search a database first, then write) made things up on ★17–33% of all test questions (2024)〔事実14〕; real references: major errors in 24–43%〔データ2〕（If not found：mark it "unverified" and do not use it は判定の流れ図の unverified が見せる） | 講師のおすすめの手順（手順に出典の印は付けない）。検索つきでも書く段は次のトークンの予測。実在する文献でも著者・年などに大きな誤り（GPT-3.5 43%・GPT-4 24%〔データ2〕）があるので、開いて文を探すまでやる。AI に「本物か」と聞くのは確認にならない（7枚目、Mata〔事実10〕）。Lexis+ AI など「作り話なし」と宣伝された道具 | 手順・ラベル | 本文 |
| 12 | Re-ask and recompute | そして（並べる） | Re-asked answers that disagree flag likely errors | 違い：比較：two new-chat re-asks that agree (Canberra, Canberra) vs disagree (Canberra, Sydney)、各列3行（出た答え・言えること・どうするか） | Agree：Canberra, Canberra / a known fact wins most draws〔事実15〕 / not proof: a likely wrong token can win every draw / Disagree：Canberra, Sydney / a guess changes from draw to draw〔事実15〕 / ★warning sign: open the source / How：re-ask in a new chat (no old answer resent); recompute numbers, and find the original figure | 6枚目の「毎回の引き」を、確かめに使う。同じチャットで聞き直すと前の答えも文書に入って送られる（5枚目）ので、その続きを書いてしまう。数値は自分で計算（確認問題1-6） | ラベル | 本文 |
| 13 | Quiz (1-1 to 1-3) | — | — | — | 1-1〜1-3 | 解答は15枚目 | — | 確認問題 |
| 14 | Quiz (1-4 to 1-6) | — | — | — | 1-4〜1-6 | 解答は16枚目 | — | 確認問題 |
| 15 | Answers (1-1 to 1-3) | — | — | — | 要素を削らない | 全文 | — | 解答 |
| 16 | Answers (1-4 to 1-6) | — | — | — | 要素を削らない | 全文 | — | 解答 |

青帯だけを上から読む：It gives every possible next token a probability, then draws one →（そして（詳しく））One English token is about 4 characters of text →（そして（次へ））Training tunes GPT-3's 175 billion numbers to predict text →（そして（次へ））The whole chat is resent each turn; the reply continues it →（しかし（限り））Each token is a weighted draw, so replies can vary →（しかし（意外））55% of the references ChatGPT (GPT-3.5) gave did not exist (2023) →（そして（並べる））o3 made up answers to 33% of PersonQA questions (o1: 16%) →（そして（並べる））o4-mini rarely said "I don't know" (1%) and got 75% wrong →（だから（問い））Nothing checks facts, so rare facts come out fluent but wrong →（だから（手段））Open the source and find the sentence yourself →（そして（並べる））Re-asked answers that disagree flag likely errors

## 3. 事実と出典

確認：○＝出典で確かめた、△＝出典どうしで値が違う・諸説あり、×＝未確認（載せるなら ※（要確認））、一般＝教科書に必ず載る定性的な事実で、数値・年・制度を含まない（裏取りに回さない。数値などを含めば facts.py が回す）。
時とともに変わる値（制度の版・統計・法令・料金・数）は、最新の版を探してから書き、出典に版か年を入れる。

| 主張 | 値・式 | 出典（書名・URL） | 確認 |
|---|---|---|---|
| GPT-3 is an autoregressive language model trained to predict the next token; its parameter count and context length | 175 billion parameters; 2,048 tokens | T. Brown et al., "Language Models are Few-Shot Learners", NeurIPS 2020 (arXiv:2005.14165, https://arxiv.org/abs/2005.14165)：Abstract "an autoregressive language model with 175 billion parameters"／Section 2.1 "n_ctx = 2048 tokens"（全サイズ共通） | ○ |
| GPT-3's training data size and sources | trained on 300 billion tokens (seen in training); drawn from a mix of filtered Common Crawl 410B, WebText2 19B, Books1 12B, Books2 55B, Wikipedia 3B tokens (mix ≈ 499B tokens) | T. Brown et al. (2020), arXiv:2005.14165：300B は Table 2.1 の注（"trained for a total of 300 billion tokens"、Section 2.1）、データの内訳は Table 2.2（Section 2.2） | ○ |
| GPT-2's vocabulary size (byte-level BPE) | 50,257 tokens | A. Radford et al., "Language Models are Unsupervised Multitask Learners", OpenAI (2019), https://cdn.openai.com/better-language-models/language_models_are_unsupervised_multitask_learners.pdf, p.4 Section 2.3 "The vocabulary is expanded to 50,257."（byte-level BPE は Section 2.2） | ○ |
| Rule of thumb for English text: 1 token is about 4 characters, about 3/4 of a word | 1 token ≈ 4 characters ≈ 0.75 words | OpenAI Help Center, "What are tokens and how to count them?", https://help.openai.com/en/articles/4936856-what-are-tokens-and-how-to-count-them（2026-11-12 閲覧、更新日は版により異なる）："1 token ≈ 4 chars in English"、"1 token ≈ ¾ words"、"100 tokens ≈ 75 words"。英語以外は比が違うと注記あり | ○ |
| InstructGPT was tuned with human demonstrations and human rankings (RLHF); outputs of the 1.3B InstructGPT were preferred over the 175B GPT-3 | 1.3B vs 175B | L. Ouyang et al., "Training language models to follow instructions with human feedback", NeurIPS 2022 (arXiv:2203.02155, https://arxiv.org/abs/2203.02155)：Abstract — labeler demonstrations で教師ありの微調整→出力の順位づけで RLHF。"outputs from the 1.3B parameter InstructGPT model are preferred to outputs from the 175B GPT-3"（100分の1のパラメータ、OpenAI の API のプロンプトでの人の評価） | ○ |
| A chat model receives the whole conversation (instructions and all earlier messages) as input on each request; it keeps no memory between requests | — | OpenAI API documentation, "Conversation state" guide, https://developers.openai.com/api/docs/guides/conversation-state（2026-11-12 閲覧、更新日の記載なし）："each text generation request is independent and stateless"、続きの会話は前のメッセージを入力に足して送る。Responses API／Conversations API は会話をサーバー側に保存できる（既定 30 日） | ○ |
| Always choosing the most likely token (greedy/beam search) gives bland, repetitive text; sampling from the distribution is used instead | — （要旨："using likelihood as a decoding objective leads to text that is bland and strangely repetitive"。対策として Nucleus (top-p) Sampling を提案） | A. Holtzman, J. Buys, L. Du, M. Forbes, Y. Choi, "The Curious Case of Neural Text Degeneration", ICLR 2020, Abstract. https://arxiv.org/abs/1904.09751 ・ https://openreview.net/forum?id=rygGQyrFvH | ○ |
| Temperature reshapes the next-token probabilities: lower makes the top token dominate, higher spreads the choice to less likely tokens | — | 一般（教科書の定義） | 一般 |
| Definition of hallucination: generated content that is nonsensical or unfaithful to the provided source content | — （原文："the generated content that is nonsensical or unfaithful to the provided source content ... is the most inclusive and standard"） | Z. Ji et al., "Survey of Hallucination in Natural Language Generation", ACM Computing Surveys 55(12), Article 248, 2023, doi:10.1145/3571730. 文言は arXiv:2202.03629v6 の Sec. 2 "Definitions"（p.4）で確認 https://arxiv.org/abs/2202.03629 | ○ |
| AI に「本物か」と聞いても確認にならない：Mata v. Avianca で弁護士が ChatGPT に存在しない判例が本物かを尋ねると、本物で有名な法律データベースで見つかると答えた。弁護士はそのまま裁判所に出し、制裁金 5,000 ドルを科された（2023年の ChatGPT・検索なしでの1件） | $5,000 | Mata v. Avianca, Inc., No. 22-cv-1461 (PKC), Opinion and Order on Sanctions, U.S. District Court S.D.N.Y., 2023年6月22日（判決文の全文：https://reason.com/volokh/2023/06/22/sanctions-issued-in-case-where-lawyers-cited-chatgpt-hallucinated-precedents/printer/ ） | ○ |
| Models answer questions about a fact less accurately when fewer pretraining documents are relevant to it (long-tail knowledge) | — （例：BLOOM-176B の TriviaQA 正答率は、関連文書が約10件→約1万件で約25%→55%超。関連文書を除いて再学習すると正答率が大きく下がる） | N. Kandpal, H. Deng, A. Roberts, E. Wallace, C. Raffel, "Large Language Models Struggle to Learn Long-Tail Knowledge", ICML 2023, PMLR 202:15696–15707. https://proceedings.mlr.press/v202/kandpal23a.html （arXiv:2211.08411） | ○ |
| GPT-4 generally lacks knowledge of events after the vast majority of its pretraining data cut off | September 2021 （原文："lacks knowledge of events that have occurred after the vast majority of its pre-training data cuts off in September 2021"。初代 GPT-4 の値。GPT-4 Turbo などの後の版は別の日付） | OpenAI, "GPT-4 Technical Report", arXiv:2303.08774v6 (4 Mar 2024), Sec. 5 "Limitations". https://arxiv.org/abs/2303.08774 | ○ |
| Hallucinations persist partly because training and evaluation reward guessing over acknowledging uncertainty (accuracy-only scoring) | — （要旨："training and evaluation procedures reward guessing over acknowledging uncertainty"。0-1 採点では棄権が0点なので推測が得。対策は既存ベンチマークの採点の変更） | A. T. Kalai, O. Nachum, S. S. Vempala, E. Zhang, "Why Language Models Hallucinate", arXiv:2509.04664 (submitted 4 Sep 2025), Abstract. https://arxiv.org/abs/2509.04664 | ○ |
| 「調べてから答える」専門の AI でも作り話は残る：作り話が無いと宣伝された法律調査の AI（Lexis+ AI、Westlaw AI-Assisted Research、Ask Practical Law AI）も、問いの 17〜33％ で作り話をした（法律の問いに限った1つの研究。GPT-4 よりは少ない） | 17–33% | Magesh, V. ほか「Hallucination-Free? Assessing the Reliability of Leading AI Legal Research Tools」arXiv:2405.20362 (2024) https://arxiv.org/abs/2405.20362 （Abstract。のちに Journal of Empirical Legal Studies 2025） | ○ |
| Sampling several answers to the same prompt and checking whether they agree detects hallucinations: facts the model knows tend to come out consistent, made-up ones diverge | — （原文："if an LLM has knowledge of a given concept, sampled responses are likely to be similar and contain consistent facts. However, for hallucinated facts, stochastically sampled responses are likely to diverge and contradict one another."） | P. Manakul, A. Liusie, M. J. F. Gales, "SelfCheckGPT: Zero-Resource Black-Box Hallucination Detection for Generative Large Language Models", EMNLP 2023, Abstract. https://aclanthology.org/2023.emnlp-main.557/ （arXiv:2303.08896） | ○ |
| Next-token candidates after "The capital of Australia is" and their probabilities; the temperature bars are recomputed from these | Canberra 0.62, Sydney 0.25, Melbourne 0.08, other 0.05 | 説明のための例（実在のモデルの値ではない） | 図に（probabilities are an example）と書く |
| A phone keyboard's predictive text suggests the next word from what you have typed | — | 一般 | 一般 |
| Canberra is the capital of Australia; Sydney is its largest city | — | 一般 | 一般 |
| 10枚目「学習データに少ない事実ほど答えを誤る」の裏づけ（行1は次のトークンの予測を言うだけで、この主張は支えない）：事実の問いの正答率は、その問いの実体を含む事前学習の文書の数とともに上がる（相関と因果の両方、最大 176B のモデル） | 正答率 ∝ 関連する事前学習文書の数（定性的。数値はグラフのみ） | N. Kandpal et al., "Large Language Models Struggle to Learn Long-Tail Knowledge", ICML 2023, PMLR 202:15696–15707（arXiv:2211.08411, https://arxiv.org/abs/2211.08411）、Figure 1（BLOOM・TriviaQA） | ○ |

## 3b. データ（data.py merge が data_N.md から入れる。図の案から「データN」で指す。値・単位・注記はこのとおりに描く。驚きの事実は、使うなら3節の事実の行に写す）

### データ1：正解率の高いモデルほど、間違いも多い（SimpleQA）
- 驚き：正解率はほぼ同じ（22 と 24）なのに、「分からない」と言わない古いモデルは間違いが3倍近い。当てずっぽうで答えると正解率は上がるが、作り話も増える
- 問いの候補：なぜ AI は「分かりません」と言わずに、もっともらしく答えてしまうのか？
- 単位：％
- 分母：SimpleQA の問題の数（1モデルあたり全問）
- 時点：2025年9月公表
- 出典：「Why language models hallucinate」OpenAI 2025年9月5日 https://openai.com/index/why-language-models-hallucinate/ （SimpleQA の表。元の論文は Kalai ほか「Why Language Models Hallucinate」arXiv:2509.04664、表の値は GPT-5 System Card から）
- 確認：○
- 別の読み方：同じ会社の2モデルを1つの試験で比べただけ。SimpleQA は答えの短い事実の問いに限る。新しいモデルを持ち上げる会社自身の発表
| 区分 | 答えない | 正解 | 間違い |
|---|---|---|---|
| gpt-5-thinking-mini | 52 | 22 | 26 |
| o4-mini（古いモデル） | 1 | 24 | 75 |

### データ2：AI が書いた参考文献のうち、存在しない文献の割合
- 驚き：GPT-3.5 が挙げた参考文献の半分以上は存在しない。新しい GPT-4 でも約5件に1件。実在の文献でも、著者・年・頁などに大きな誤りがある割合が高い
- 問いの候補：本当に AI は文献を「調べて」挙げているのか？
- 単位：％
- 分母：各モデルが挙げた参考文献（作り話の割合）、そのうち実在した文献（誤りの割合）
- 時点：2023年（論文の公表は2023年9月）
- 出典：Walters, W. H. & Wilder, E. I.「Fabrication and errors in the bibliographic citations generated by ChatGPT」Scientific Reports 13, 14045 (2023) https://www.nature.com/articles/s41598-023-41032-5 （42の題で短い論文84本・参考文献636件を検証）
- 確認：○
- 別の読み方：2023年のモデルで、いまのモデルや検索つきの使い方では下がっている。1つの研究・1つの課題（短い論文に文献をつけさせる）だけ
| 区分 | 存在しない文献 | 実在の文献のうち大きな誤りあり |
|---|---|---|
| GPT-3.5 | 55 | 43 |
| GPT-4 | 18 | 24 |

### データ3：新しく賢いモデルの方が、人物の問いで作り話が多い（PersonQA）
- 驚き：新しいモデルほど作り話が減ると思いがちだが、o3 の作り話の率は前の o1 の約2倍、o4-mini は約3倍
- 問いの候補：新しいモデルなら、もう間違いを気にしなくてよいのか？
- 単位：割合（0〜1）
- 分母：PersonQA の問い（公開された人物の事実を尋ねる問い）
- 時点：2025年4月
- 出典：「OpenAI o3 and o4-mini System Card」OpenAI 2025年4月16日 https://cdn.openai.com/pdf/2221c875-02dc-4789-800b-e7758f3722c1/o3-and-o4-mini-system-card.pdf Table 4（Hallucination evaluations）
- 確認：○
- 別の読み方：o3 は主張の数そのものが多く、正解も増えている（正解率 0.59 は o1 より高い）。1社の1つの試験だけ
| 区分 | 正解率 | 作り話の率 |
|---|---|---|
| o1 | 0.47 | 0.16 |
| o3 | 0.59 | 0.33 |
| o4-mini | 0.36 | 0.48 |

### 驚きの事実1：AI に「本物か」と聞いても、確認にはならない
- 驚き：AI に「この判例は本物？」と聞き返せば確かめられると思われがちだが、実際の裁判（Mata v. Avianca）で弁護士が ChatGPT に存在しない判例が本物かを尋ねると、ChatGPT は本物で、有名な法律データベースで見つかると答えた。弁護士はそのまま裁判所に出し、制裁金 5,000 ドルを科された
- 問いの候補：AI 自身に聞き直せば、答えを確かめたことになるのか？
- 出典：Mata v. Avianca, Inc., No. 22-cv-1461 (PKC), Opinion and Order on Sanctions, U.S. District Court S.D.N.Y., 2023年6月22日（判決文の全文：https://reason.com/volokh/2023/06/22/sanctions-issued-in-case-where-lawyers-cited-chatgpt-hallucinated-precedents/printer/ ）
- 確認：○
- 別の読み方：2023年の ChatGPT（検索なし）での1件。いまは検索つきのものもある（ただし次の事実のとおり、検索つきでも作り話は残る）

### 驚きの事実2：「調べてから答える」専門の AI でも作り話は残る
- 驚き：データベースを検索してから答える AI なら作り話はしないと思われがちだが、作り話が無いと宣伝された法律調査の AI（Lexis+ AI、Westlaw AI-Assisted Research、Ask Practical Law AI）も、問いの 17〜33％ で作り話をした
- 問いの候補：本当に「調べて」答える AI なら、確かめなくてよいのか？
- 出典：Magesh, V. ほか「Hallucination-Free? Assessing the Reliability of Leading AI Legal Research Tools」arXiv:2405.20362 (2024) https://arxiv.org/abs/2405.20362 （Abstract。のちに Journal of Empirical Legal Studies 2025）
- 確認：○
- 別の読み方：法律の問い（わざと誤った前提を含む問いも入る）に限った1つの研究。汎用のチャット AI（GPT-4）よりは少ない

## 4. 用語・記号の決め事（README の決め事に足すもの）

- token, next-token probability, parameter, training (pretraining) and tuning, context, sampling, temperature, hallucination, source (original source), knowledge cutoff。初出で一度だけ平易に説明する
- 数は英語の書き方で：175 billion・1.3B（モデルの大きさは本文で "billion"、図の中は "B" でもよい）、％は "55%"
- 2枚目の例「The capital of Australia is」を 3・6・12枚目でも使い回す（Canberra＝正しい続き、Sydney＝もっともらしい誤り）。色は Canberra を青、Sydney を赤
- モデル名は出典の書き方のまま（GPT-3.5、GPT-4、o1、o3、o4-mini、gpt-5-thinking-mini）

## 5. 図の案

| スライド | テーマか難所か | 何をどう描くか | 値の出どころ |
|---|---|---|---|
| 2 | テーマ | 次のトークンの候補4つと確率の横棒（Canberra を主役） | 説明のための例 |
| 3 | 仕組み | 文をトークンの箱に分ける＋まれな語が2つに割れる例（横長。上に文・下に図） | 説明のための例 |
| 4 | 仕組み | 当てて・比べて・数を直す、のくり返しの流れ図 | Brown et al. (2020) |
| 5 | 仕組み | チャット全体を1枚の文書として描き、最後に次のトークンの空き | OpenAI API docs、Ouyang et al. (2022) |
| 6 | 難所 | 温度 0.5・1・2 ごとの候補の確率の棒（3色。図が主役の型で左に大きく） | 2枚目の例から計算 |
| 7 | テーマ | 実在しない文献の割合の棒（GPT-3.5・GPT-4） | データ2（Walters & Wilder 2023） |
| 8 | テーマ | PersonQA の作り話の率の棒（o1・o3・o4-mini） | データ3（OpenAI 2025） |
| 9 | テーマ | SimpleQA の答えない・正解・間違いの棒（2モデル） | データ1（OpenAI 2025） |
| 10 | 難所 | まれな事実と多い事実の答えの「正解・正解でない」の積み上げ棒（Figure 1 から読んだ2点） | Kandpal et al. (2023) |
| 11 | 位置づけ | 判定：判定の流れ図：出典を確かめる3つの問い（No なら unverified、全部 Yes なら use it） | — |
| 12 | 位置づけ | 聞き直しで一致する場合と割れる場合の比較 | 説明のための例 |

## 6. 確認問題と模範解答（6問ちょうど。スライドは1枚に3問ずつ、確認問題2枚・解答2枚）

### 問題
1-1. When a chat AI writes a reply, what does it compute at each step, and what does it do with the result? 〔ゴール1・2枚目〕〔型：仕組み〕
1-2. You ask the same question in two new chats and get two different answers. Explain why, using how each token is chosen. 〔ゴール1・6枚目〕〔型：仕組み〕
1-3. A friend says: "The AI gave the authors and the journal of a paper, so it must have looked it up." What is wrong with this reasoning? 〔ゴール2・7枚目〕〔型：誤り指摘〕
1-4. Which question is a chat AI more likely to get wrong: the birth year of a world-famous scientist, or the birth year of a little-known local politician? Explain why. 〔ゴール2・10枚目〕〔型：比べる〕
1-5. An AI answer supports a claim with "Smith (2021), Journal of Learning". You want to use the claim in a report. Write the steps you take before using it. 〔ゴール3・11枚目〕〔型：当てはめ〕
1-6. An AI says: "30% of the 1,200 students, that is 390 students, use the library." Check the number yourself, and name one more check you would do. 〔ゴール3・12枚目〕〔型：計算〕

### 解答
1-1. It computes a probability for every possible next token, given all the text so far (the whole chat). It draws one token, appends it, and repeats until the reply is done. 〔要素：a probability for every possible next token／given all the text so far／draws one, appends it and repeats〕
1-2. Each token is a weighted random draw from the probabilities, not always the top token, so a less likely token (even a wrong one) is sometimes picked, and the rest of the reply follows from it. How much answers vary depends on the temperature. 〔要素：a weighted random draw, not always the top token／a less likely token is sometimes picked／depends on the temperature〕
1-3. Authors and a journal are just likely-looking text; nothing in the model checks that the paper exists. In a 2023 study, 55% of the references from GPT-3.5 and 18% from GPT-4 did not exist. Open the paper yourself. 〔要素：likely-looking text, not checked／fake references are common (e.g. 18% for GPT-4)／open the paper yourself〕
1-4. The local politician. Facts that appear in few training documents get a low probability for the right continuation, so a plausible wrong year is more likely to be drawn. 〔要素：the local politician／few training documents about the fact／a low probability for the right answer, so a wrong year can be drawn〕
1-5. Search for the paper by title, authors and year (or DOI); open the original; find the sentence that supports the claim. If you cannot find it or it says something else, mark the claim "unverified" and do not use it. Asking the AI "is it real?" does not count. 〔要素：search by title, authors, DOI and open the original／find the supporting sentence／if not found, mark unverified and do not use〕
1-6. 30% of 1,200 is 0.30 × 1,200 = 360, not 390: the two numbers do not match (390 would be 32.5%), so at least one is wrong. One more check: find the original survey for the figures. (Re-asking in a new chat is weaker: agreement is not proof.) 〔要素：0.30 × 1,200 = 360, not 390, so the numbers do not match／find the original survey〕

## 7. 前の回から反映すること

- 前の回の質問回答デッキ・README のつまずき一覧から：第1回なのでなし
- 冒頭に「前回のつまずき」を置くか：置かない

## 8. 迷った所とレビューの反映

- 迷った所（設計の担当が書く。直しの担当が読む）：
  - データは3組とも使った（7枚目＝データ2を複雑化の しかし（意外）に、8枚目＝データ3、10枚目＝データ1）。驚きが一番素直なのは文献の作り話なので、それを筋の しかし に据えた。データ1（SimpleQA）は3つ目の驚き（9枚目）として だから（問い）（10枚目）の前に置いたが、2モデルの比べなので青帯は事実の言い方に留めた（「当てずっぽうで間違いが3倍」とは言わない）
  - 驚きの事実は2つとも使った（7枚目の Mata v. Avianca、11枚目の法律 AI の 17〜33%）。3節に写した
  - 地図の「chat as a continued document」は5枚目にまとめ、青帯は調整（InstructGPT）の比べにした。青帯をチャット＝文書にするか、調整の比べにするかで迷った
  - 6枚目（温度）の青帯に数が入らない。図の値は説明のための例なので、青帯に例の数を載せなかった
  - 12枚目の SelfCheckGPT は数を青帯に出していない（論文の数値を覚えていない）。裏取りで数が拾えれば青帯に入れてよい
  - 本文は11枚（そして が 3・4・5枚目で3つ続く）。表紙＋本文11＋問題2＋解答2＝16枚
- レビューの反映（直しの担当が書く。事実の確認を含む）：
  - 必ず直す点1〜6 は全部採った：筋の問いを7枚目の本文へ（型を「なぜ」、2枚目には素朴な見方の問い）、10枚目の青帯を答えに、5枚目の青帯をチャット＝文書に（迷った所の3はこれで決着）、6枚目を例の確率から計算した値に（greedy の dull は別の行）、11枚目の青帯を手順に（17–33% は本文の Why）、1-6 の解答を「食い違い」までに
  - 直すとよい点は 1・2・4〜11 を採った。3（実際のトークナイザーで3枚目を分ける）は、この環境にトークナイザー（tiktoken など）が無く確かめられないので採らず、図は「the split is an example」のまま
  - 事実の確認：facts_diff の事実2（300B＝学習で読んだトークン数）を4枚目の本文・原稿に、事実19 を10枚目の Rare facts の出典に。3節の行は足していない
  - 資料から抜けていた内容：データ2 の「実在の文献のうち大きな誤り」は11枚目の原稿に、事実2 の内訳は4枚目の ※ に
  - 12枚目の SelfCheckGPT は数値の行が無いので、青帯は数なしのまま
  - check_memo の △「問いの枚 7 が前のほうに無い」は残した：レビューの必ず直す点1（問いは7枚目の意外から出す、答えの位置：後）に従ったため。2枚目は素朴な見方（Your guess）で予想を立てさせる
  - 6枚目・10枚目・11枚目の講師の計算・まとめの行は〔講師の概算〕〔講師のまとめ〕にした（出典の行は付けない）
- 外から見た採点（83点）の反映：1枚の文の塊を2つまでに（7・10枚目は4つ→2つ、3・4・8・11枚目は3つ→2つ。外した塊（Length limit・Mata・Cutoff・Test scores・If not found）は原稿か図へ）、10枚目の図を2点を結んだ線から「正解・正解でない」の積み上げ棒に、本文の「(slide N)」の参照を言葉に言い換え（原稿も）、3枚目にまれな語が2トークンに割れる例、赤の棒・面を落ち着いた赤に、確認問題・解答は見出しを本文の枚の結論と同じ見た目にし、1問ずつ横いっぱいの箱に（答えは句読点のある文に）
- 第N回に回す点：

## 9. 引っかかりへの手当て（レビューの推論距離から。各行は [スライド番号] で始める）

レビューの結果は、そのまま memo_review.md に残す。「要」の穴のあるスライドを全部載せる（採らないものも理由つきで）。「深」は載せなくてよい（原稿の ※ に入れるなら書く）。

- [2] token の語（初出が2枚目）：手順2に括弧で「a token is a word or a piece of one, next slide」（定義は3枚目）
- [2] pick の像（最も確率の高いものを選ぶ）：手順3を「Draw one, weighted by its probability (slide 6)」に。くじ引きの中身は6枚目の図の注
- [2] scores／odds／probability の揺れ：2枚目の青帯・本文、10枚目、1-4 の解答を probability にそろえた（10枚目の採点は「Test scores」）
- [3] 長さの上限＝context の上限（深）：初学者なので採らない
- [4] learning の像（事実を覚え込む）：本文に「What it learns: how text continues, not a list of facts」をノートから上げた（10枚目の答えの前提）
- [5] 調整がなぜここに来るか：Tuning の行の頭に「plain GPT-3 just continues text」、原稿で「will not necessarily continue in the form of an answer」
- [5] RLHF：略語を外して「human rankings of its replies」に。人の順位で好まれる返事が出やすいよう数を直す、はノートに
- [6] temperature：本文の1行目に「Temperature: a dial applied before the draw; low sharpens…, high flattens…」
- [6] weighted draw：図の注に「like a lottery, 62 of 100 tickets say Canberra」
- [6] 利用者は温度を変えられない（深）：レビューの直すとよい点10 に合わせ、原稿の1文の候補としてノートに
- [7] 素朴な見方が遠い：2枚目の本文の最後に「It sounds like it looked the answer up. Did it?」を載せ、7枚目の1行目「Did it look them up?⇒」で崩す
- [7] GPT-3.5 の呼び名：青帯を「ChatGPT (GPT-3.5)」にし、Mata の ChatGPT とそろえた
- [8] PersonQA：本文に括弧で「questions about real people」
- [9] SimpleQA・abstain：括弧で「short fact questions」、abstain は青帯・本文とも「says "I don't know"」に言い換え
- [9] 22 vs 24・26 vs 75 の読み：本文の最後に「⇒ Guessing adds few right answers but many wrong ones」
- [10] Step 2 が遠い：ラベルを「No step checks facts」にし、枚の番号の参照をやめた（原稿で「the next-token probability we started with」）
- [10] 少ない文書→低い正答率の理由：Rare facts の行に「⇒ the right continuation never gets a high probability」
- [10] knowledge cutoff：「Cutoff (the date its training text ends)」。それより後の出来事は学習データに無い、はノートに
- [10] score の揺れ：2枚目を probability にし、10枚目は「Test scores」
- [11] search-based：括弧で「they search a database first, then write」。書く段は次のトークンの予測、はノートに
- [11] DOI：括弧で「DOI: the paper's ID」
- [12] 一致・不一致の理由が遠い：Re-ask の行に「a known fact wins most draws, a guess changes from draw to draw」
- [12] new chat の理由：括弧で「no old answer resent」。同じチャットだと前の答えの続きを書く（5枚目）、はノートに
