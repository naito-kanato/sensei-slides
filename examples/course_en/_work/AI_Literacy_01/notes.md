## 1
<!-- 表紙の枚 -->

Welcome. Today you will find out what a chatbot actually computes when it writes a reply, and why that same computation sometimes produces confident mistakes. By the end, you should be able to say in one sentence what generative AI computes, explain why a fluent answer can still be wrong, and name what to check before you rely on one. We start with a real court case from 2023. Keep one question in mind: what does generative AI actually compute?

## 2
<!-- 目安 400字前後（導入・図の読み方・根拠・例か間違いやすい所・次へのつなぎ） ／ 手当て：[2] 本文の Belief の主がない → 本文を「a lawyer thought it "could not" fabricate」にし、原稿に「One lawyer testified he thought ChatGPT could not possibly make up cases.」（事実2）。経験の問いは3枚目にあるので、2枚目の原稿の同じ問いは外した -->

In 2023, in a New York case, Mata versus Avianca, lawyers cited six court cases. Under "What the lawyers assumed": ChatGPT looked them up, and they were real. Under "What actually happened": ChatGPT wrote them, none existed, and the judge fined the lawyers 5,000 dollars. One lawyer testified he thought ChatGPT could not possibly make up cases. So how can a citation look real and not be? Start with your phone keyboard, which already predicts your next word.

※ Source: ABA Journal "Lawyers who 'doubled down' and defended ChatGPT's fake cases must pay $5K, judge says" (2023) https://abajournal.com/web/article/lawyers-who-doubled-down-and-defended-chatgpts-fake-cases-must-pay-5k-judge-says ; Bloomberg Law "Phony ChatGPT Brief Leads to $5,000 Fine for NY Lawyers" (2023) https://news.bloomberglaw.com/litigation/chatgpt-phony-legal-filing-case-gets-lawyers-a-5-000-fine
※ Source: ABA Journal (2023), same article as row 1

## 3
<!-- 目安 400字前後（導入・図の読み方・根拠・例か間違いやすい所・次へのつなぎ） ／ 前の枚から：だから（手段）（1文目でこの語のつながりを言う） -->

So, start with something you use every day. Type "See you", and your keyboard offers "soon", "later" or "tomorrow"; you tap one. It is not looking up your plans; it guesses which word usually comes next. Have you trusted a reply just because it sounded sure? Then today's question matters: what does generative AI actually compute? A guess to test: maybe a chatbot is a far bigger keyboard. The first step comes before any guessing: text is cut into tokens, and 100 tokens are about 75 words.

※ Source: Apple "iPhone User Guide: Use predictive text on iPhone" https://support.apple.com/guide/iphone/use-predictive-text-iphd4ea90231/ios ; Apple Support "How to use Auto-Correction and predictive text" https://support.apple.com/104995

## 4
<!-- 目安 400字前後（導入・図の読み方・根拠・例か間違いやすい所・次へのつなぎ） ／ 前の枚から：そして（詳しく）（1文目でこの語のつながりを言う） -->

Let's look closely at that first step. A model cuts text into tokens. In the figure, "Chatbots predict text." becomes boxes, one per token; the splits are only an illustration. OpenAI says a token can be a word, part of a word, or a punctuation mark. In English one token is about four characters, or three quarters of a word, so 100 tokens are about 75 words. Think of building blocks, except the blocks do not always match whole words. Next: each possible next token gets a probability.

※ Source: OpenAI Help Center "What are tokens and how to count them" (article 4936856) https://help.openai.com/en/articles/4936856-what-are-tokens-and-how-to-count-them
※ Source: OpenAI Help Center "What are tokens and how to count them" https://help.openai.com/en/articles/4936856-what-are-tokens-and-how-to-count-them

## 5
<!-- 目安 400字前後（導入・図の読み方・根拠・例か間違いやすい所・次へのつなぎ） ／ 前の枚から：そして（詳しく）（1文目でこの語のつながりを言う） ／ 手当て：[5] training の中身・確率の出どころ → 原稿に「Training: the model reads huge amounts of text, and its settings are adjusted until the token that actually came next gets a high probability.」（事実7の言い換え） -->

After "The capital of France is", the model rates every token by how likely it is to come next. A longer bar means more likely: "Paris" long, "located" short. Where do the odds come from? Training: the model reads huge amounts of text, and its settings are adjusted until the token that actually came next gets a high probability. GPT-3, an earlier OpenAI model, was trained on 300 billion tokens. It is like a chance-of-rain forecast, but about which text usually follows, not about the world. Next: it picks one token, appends it, and repeats.

※ Source: Brown T. et al. "Language Models are Few-Shot Learners" arXiv:2005.14165 (2020), abstract; Table 2.1 caption ("All models were trained for a total of 300 billion tokens") https://arxiv.org/abs/2005.14165
※ Source: Brown et al. 2020 abstract ("an autoregressive language model"); Kalai A.T. et al. "Why Language Models Hallucinate" arXiv:2509.04664 (2025) https://arxiv.org/abs/2509.04664

## 6
<!-- 目安 400字前後（導入・図の読み方・根拠・例か間違いやすい所・次へのつなぎ） ／ 前の枚から：そして（次へ）（1文目でこの語のつながりを言う） ／ 手当て：[6] pick の像（等しく引く） → 原稿に「Likely tokens are picked most often, unlikely ones now and then; it is not an even draw.」（事実8） ／ 手当て：[6] temperature の像（熱） → 原稿を「A setting called temperature, nothing to do with heat, controls how much chance there is: higher means more random, lower means more focused.」に（事実8） -->

Follow the flow chart: text so far, probabilities for each next token, pick one with some chance, append it, and go again. Likely tokens are picked most often, unlikely ones now and then; it is not an even draw. A setting called temperature, nothing to do with heat, controls how much chance there is: higher means more random, lower means more focused. That is why the same question can get two different replies. But what about real facts, like references? In a 2023 study, GPT-3.5 invented 55 percent of its citations, GPT-4 18 percent.

※ Source: OpenAI API reference wording, quoted in OpenAI Developer Community "Temperature docs for 1 max vs 2 max" (2023) https://community.openai.com/t/temperature-docs-for-1-max-vs-2-max/309112

## 7
<!-- 目安 400字前後（導入・図の読み方・根拠・例か間違いやすい所・次へのつなぎ） ／ 前の枚から：しかし（意外）（1文目でこの語のつながりを言う） ／ 手当て：[7] literature review・GPT-3.5/GPT-4 の中身 → 原稿に「summaries of research with a reference list」と「two versions of the model behind ChatGPT」 -->

But here is the surprise. In a 2023 study in Scientific Reports, researchers asked ChatGPT for short literature reviews, summaries of research with a reference list, and checked every citation. The bars show the share that did not exist: 55 percent for GPT-3.5 and 18 percent for GPT-4, two versions of the model behind ChatGPT. Newer was better, but not zero. A limit: two 2023 models on a hard task; today's tools may do better. You might think the AI searched and slipped. Let's test that: asked 3 times, a model gave 3 different wrong dates.

※ Source: Walters W.H. & Wilder E.I. "Fabrication and errors in the bibliographic citations generated by ChatGPT" Scientific Reports 13, 14045 (2023) https://www.nature.com/articles/s41598-023-41032-5

## 8
<!-- 目安 400字前後（導入・図の読み方・根拠・例か間違いやすい所・次へのつなぎ） ／ 前の枚から：しかし（疑い）（1文目でこの語のつながりを言う） ／ 手当て：[8] 検索なら同じ答えの理由・ループなら別の答えの理由（遠い：6枚目）・DeepSeek-V3 → 原稿に「since it reads the same stored record」「because each pick involves chance, as in step 3」「another company's chat model」 -->

Here a doubt comes up: is this a search that slipped? A failed lookup finds a real source, and since it reads the same stored record, it repeats the same answer. A likely continuation may name a source that never existed, with a new answer each try. In a 2025 paper, Adam Kalai's team asked DeepSeek-V3, another company's chat model, for Kalai's birthday, only if it knew. Three tries, three different wrong dates. A lookup would not do that; the loop would, because each pick involves chance, as in step 3. So why guess? Partly because tests reward a 1-in-365 guess over "I don't know".

※ Source: Kalai A.T., Nachum O., Vempala S., Zhang E. "Why Language Models Hallucinate" arXiv:2509.04664 (2025-09-04) https://arxiv.org/abs/2509.04664

## 9
<!-- 目安 400字前後（導入・図の読み方・根拠・例か間違いやすい所・次へのつなぎ） ／ 前の枚から：だから（帰結）（1文目でこの語のつながりを言う） ／ 手当て：[9] 1度しか出ない事実に規則が無い理由・tests の中身 → 原稿に「Training learns from what repeats」と「the tests used to score models count only right answers」、結びを「So such tests reward guessing over admitting it does not know」に（事実10・11の言い換え） -->

First, rare facts: Training learns from what repeats, and a birthday seen once in the training text has no pattern to learn from. Second, grading: the tests used to score models count only right answers, and 1 in 365 is the chance a guessed birthday is right. Small, but if "I don't know" scores zero, a guess still earns more on average, like an exam with no penalty for wrong answers. So such tests reward guessing over admitting it does not know, and the guessing shows most on rare facts. Then what does generative AI actually compute? It computes what is likely next, not what is true.

※ Source: Kalai et al. 2025, arXiv:2509.04664 (same as row 9)
※ Source: OpenAI "Why language models hallucinate" (2025-09) https://openai.com/index/why-language-models-hallucinate/

## 10
<!-- 目安 400字前後（導入・図の読み方・根拠・例か間違いやすい所・次へのつなぎ） ／ 前の枚から：だから（問い）（1文目でこの語のつながりを言う） -->

So, why do plausible mistakes appear? This is my summary. Generative AI computes how likely each next token is, picks one, appends it, and repeats. The figure shows the same loop, plus a crossed-out box, "Check: is it true?": a step the loop does not have. The analogy: your keyboard's guess, tapped to the end. It finishes sentences; it never checks them. Where it breaks: it learned from far more text, so it guesses better, but still guesses. So, check the names, numbers and sources you rely on.

## 11
<!-- 目安 400字前後（導入・図の読み方・根拠・例か間違いやすい所・次へのつなぎ） ／ 前の枚から：だから（手段）（1文目でこの語のつながりを言う） ／ 手当て：[11] 名前・数はいつも珍しいわけではない（範囲） → 原稿を「Exact names, dates, numbers and sources are often rare facts, seen once in training text, where the model guesses.」に言い換え（事実11） -->

So, here is how to use this. Follow the decision chart. Is the reply only wording or ideas, like rephrasing an email? Then use it as a draft. If not, will you rely on a name, a number or a source? Then check it in the original; otherwise, use it marked unchecked. Why these? Exact names, dates, numbers and sources are often rare facts, seen once in training text, where the model guesses. Wording has no single fact to get wrong. But checking that a source exists is not enough: only 7 percent of 115 references were real and accurate.

※ Source: Kalai et al. 2025, arXiv:2509.04664 (same as row 9)

## 12
<!-- 目安 400字前後（導入・図の読み方・根拠・例か間違いやすい所・次へのつなぎ） ／ 前の枚から：そして（次へ）（1文目でこの語のつながりを言う） ／ 手当て：[12] 本物でも中身があるとは限らない・ChatGPT-3.5 の呼び名の揺れ → 本文の ⇒★ を「A real paper may not say it」、本文を「GPT-3.5 (ChatGPT)」に。原稿に「A real source may still not say what the reply claims.」と「the older model from slide 7」（事実12・データ2） -->

The bar shows 115 references ChatGPT wrote with GPT-3.5, the older model from slide 7, for medical papers in 2023: 47 percent fabricated, 46 percent real but inaccurate, only 7 percent real and accurate. Look at "Real but inaccurate": almost half existed but had wrong details. A real source may still not say what the reply claims. So the steps go further: search the exact title, match authors, year and journal, then open it and find the claim. A limit: one older model, one field. Now, back to the lawyers: the fake cases were likely text, not failed searches.

※ Source: Centre College Library "Evaluating AI" https://library.centre.edu/AI/evaluate (accessed 2026-11)
※ Source: Bhattacharyya M. et al. "High Rates of Fabricated and Inaccurate References in ChatGPT-Generated Medical Content" Cureus 15(5): e39238 (2023) doi:10.7759/cureus.39238 https://pmc.ncbi.nlm.nih.gov/articles/PMC10277170/

## 13
<!-- 目安 400字前後（導入・図の読み方・根拠・例か間違いやすい所・次へのつなぎ） ／ 前の枚から：だから（帰結）（1文目でこの語のつながりを言う） -->

So, back to the case we started with. The flow chart replays it. The lawyers asked for supporting cases. The model produced likely tokens, names, courts and years, shaped like a citation. The result was fluent, and in no court record. My summary: the model computed likely next tokens, and the missed step was opening the cases; none of the six existed. It was not a search that slipped; it was the loop at work. Fluent says nothing about true. In one line: likely next token, not the truth.

※ Source: ABA Journal "Lawyers who 'doubled down' and defended ChatGPT's fake cases must pay $5K, judge says" (2023) https://abajournal.com/web/article/lawyers-who-doubled-down-and-defended-chatgpts-fake-cases-must-pay-5k-judge-says ; Bloomberg Law "Phony ChatGPT Brief Leads to $5,000 Fine for NY Lawyers" (2023) https://news.bloomberglaw.com/litigation/chatgpt-phony-legal-filing-case-gets-lawyers-a-5-000-fine

## 14
<!-- まとめの枚 -->

Let's check the opening question: what does generative AI actually compute? Before, you might have said it looks answers up; now you can say it guesses the next token, again and again. You might have thought fluent means true; now you know fluent means likely. And you might have trusted a cited source; now you know to open it yourself. Next come six questions. Try each in your own words before looking at the answers.

## 15
Review questions. Think of your own answer first, then compare it with the answers on the next slide.

1-1. What is a token, and about how many English words do 100 tokens make?

1-2. You ask a chatbot the same question twice and get two different replies. Using the loop, explain why.

1-3. A friend says: "The chatbot cited a paper that does not exist, so its search must have failed." What is wrong?

## 16
Review questions. Think of your own answer first, then compare it with the answers on the next slide.

1-4. Compare the 2023 study's fake-citation rates for GPT-3.5 and GPT-4. What do they tell you about newer models?

1-5. A chatbot says "a 2021 study found 62% of students..." and you will quote it in a report. What do you check, and how?

1-6. What does generative AI actually compute? Answer with the one-line answer and the analogy.

## 17
1-1. Recall what you saw on slide 4. The answer: A piece of text (word, part of a word, mark). 100 tokens ≈ 75 words, because 1 token ≈ 3/4 word.

Your answer is correct if it includes “a piece of text” and “about 75 words”.

1-2. Recall what you saw on slide 6. The answer: Each pick is drawn by chance from the probabilities, and because each pick changes what follows, replies differ.

Your answer is correct if it includes “picks involve chance” and “each pick changes what follows”.

1-3. Recall what you saw on slide 8. The answer: It wrote likely tokens, not a search, because asked one birthday 3 times, a model gave 3 different dates; a lookup would not.

Your answer is correct if it includes “no lookup, a likely continuation” and “3 different dates”.

## 18
1-4. Recall what you saw on slide 7. The answer: 55% vs 18% fake: newer models invent fewer but not zero, so you still check, because fluency is no proof.

Your answer is correct if it includes “55% vs 18%” and “fewer, not zero”.

1-5. Recall what you saw on slide 12. The answer: The study, year and 62%, because names and numbers are where it guesses: search the title, open it, find the claim.

Your answer is correct if it includes “name, number, source” and “open it and find the claim”.

1-6. Recall what you saw on slide 10. The answer: Next-token odds: it picks one, appends, repeats, so it scores likely, not true. Like your keyboard's guess tapped to the end.

Your answer is correct if it includes “next-token probabilities, pick and repeat” and “keyboard guess tapped to the end”.
