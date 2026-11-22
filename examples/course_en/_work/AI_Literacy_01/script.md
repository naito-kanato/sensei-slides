# Script: Lecture 1 What Generative AI Actually Computes

## 1
Welcome. Today you will find out what a chatbot actually computes when it writes a reply, and why that same computation sometimes produces confident mistakes. By the end, you should be able to say in one sentence what generative AI computes, explain why a fluent answer can still be wrong, and name what to check before you rely on one. We start with a real court case from 2023. Keep one question in mind: what does generative AI actually compute?

## 2
In 2023, in a New York case, Mata versus Avianca, lawyers cited six court cases. Under "What the lawyers assumed": ChatGPT looked them up, and they were real. Under "What actually happened": ChatGPT wrote them, none existed, and the judge fined the lawyers 5,000 dollars. One lawyer testified he thought ChatGPT could not possibly make up cases. So how can a citation look real and not be? Start with your phone keyboard, which already predicts your next word.

## 3
So, start with something you use every day. Type "See you", and your keyboard offers "soon", "later" or "tomorrow"; you tap one. It is not looking up your plans; it guesses which word usually comes next. Have you trusted a reply just because it sounded sure? Then today's question matters: what does generative AI actually compute? A guess to test: maybe a chatbot is a far bigger keyboard. The first step comes before any guessing: text is cut into tokens, and 100 tokens are about 75 words.

## 4
Let's look closely at that first step. A model cuts text into tokens. In the figure, "Chatbots predict text." becomes boxes, one per token; the splits are only an illustration. OpenAI says a token can be a word, part of a word, or a punctuation mark. In English one token is about four characters, or three quarters of a word, so 100 tokens are about 75 words. Think of building blocks, except the blocks do not always match whole words. Next: each possible next token gets a probability.

## 5
After "The capital of France is", the model rates every token by how likely it is to come next. A longer bar means more likely: "Paris" long, "located" short. Where do the odds come from? Training: the model reads huge amounts of text, and its settings are adjusted until the token that actually came next gets a high probability. GPT-3, an earlier OpenAI model, was trained on 300 billion tokens. It is like a chance-of-rain forecast, but about which text usually follows, not about the world. Next: it picks one token, appends it, and repeats.

## 6
Follow the flow chart: text so far, probabilities for each next token, pick one with some chance, append it, and go again. Likely tokens are picked most often, unlikely ones now and then; it is not an even draw. A setting called temperature, nothing to do with heat, controls how much chance there is: higher means more random, lower means more focused. That is why the same question can get two different replies. But what about real facts, like references? In a 2023 study, GPT-3.5 invented 55 percent of its citations, GPT-4 18 percent.

## 7
But here is the surprise. In a 2023 study in Scientific Reports, researchers asked ChatGPT for short literature reviews, summaries of research with a reference list, and checked every citation. The bars show the share that did not exist: 55 percent for GPT-3.5 and 18 percent for GPT-4, two versions of the model behind ChatGPT. Newer was better, but not zero. A limit: two 2023 models on a hard task; today's tools may do better. You might think the AI searched and slipped. Let's test that: asked 3 times, a model gave 3 different wrong dates.

## 8
Here a doubt comes up: is this a search that slipped? A failed lookup finds a real source, and since it reads the same stored record, it repeats the same answer. A likely continuation may name a source that never existed, with a new answer each try. In a 2025 paper, Adam Kalai's team asked DeepSeek-V3, another company's chat model, for Kalai's birthday, only if it knew. Three tries, three different wrong dates. A lookup would not do that; the loop would, because each pick involves chance, as in step 3. So why guess? Partly because tests reward a 1-in-365 guess over "I don't know".

## 9
First, rare facts: Training learns from what repeats, and a birthday seen once in the training text has no pattern to learn from. Second, grading: the tests used to score models count only right answers, and 1 in 365 is the chance a guessed birthday is right. Small, but if "I don't know" scores zero, a guess still earns more on average, like an exam with no penalty for wrong answers. So such tests reward guessing over admitting it does not know, and the guessing shows most on rare facts. Then what does generative AI actually compute? It computes what is likely next, not what is true.

## 10
So, why do plausible mistakes appear? This is my summary. Generative AI computes how likely each next token is, picks one, appends it, and repeats. The figure shows the same loop, plus a crossed-out box, "Check: is it true?": a step the loop does not have. The analogy: your keyboard's guess, tapped to the end. It finishes sentences; it never checks them. Where it breaks: it learned from far more text, so it guesses better, but still guesses. So, check the names, numbers and sources you rely on.

## 11
So, here is how to use this. Follow the decision chart. Is the reply only wording or ideas, like rephrasing an email? Then use it as a draft. If not, will you rely on a name, a number or a source? Then check it in the original; otherwise, use it marked unchecked. Why these? Exact names, dates, numbers and sources are often rare facts, seen once in training text, where the model guesses. Wording has no single fact to get wrong. But checking that a source exists is not enough: only 7 percent of 115 references were real and accurate.

## 12
The bar shows 115 references ChatGPT wrote with GPT-3.5, the older model from slide 7, for medical papers in 2023: 47 percent fabricated, 46 percent real but inaccurate, only 7 percent real and accurate. Look at "Real but inaccurate": almost half existed but had wrong details. A real source may still not say what the reply claims. So the steps go further: search the exact title, match authors, year and journal, then open it and find the claim. A limit: one older model, one field. Now, back to the lawyers: the fake cases were likely text, not failed searches.

## 13
So, back to the case we started with. The flow chart replays it. The lawyers asked for supporting cases. The model produced likely tokens, names, courts and years, shaped like a citation. The result was fluent, and in no court record. My summary: the model computed likely next tokens, and the missed step was opening the cases; none of the six existed. It was not a search that slipped; it was the loop at work. Fluent says nothing about true. In one line: likely next token, not the truth.

## 14
Let's check the opening question: what does generative AI actually compute? Before, you might have said it looks answers up; now you can say it guesses the next token, again and again. You might have thought fluent means true; now you know fluent means likely. And you might have trusted a cited source; now you know to open it yourself. Next come six questions. Try each in your own words before looking at the answers.
