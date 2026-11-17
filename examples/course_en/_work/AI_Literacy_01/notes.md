## 1
<!-- 表紙の枚 ／ ノートへ：この回のゴール3つ -->

Welcome. In this lecture, we look at what a chat AI actually computes when it writes a reply to you.

By the end, you should be able to do three things. First, explain how the model writes: one token at a time, it gives every possible next token a probability and draws one. Second, explain why fluent but wrong answers, such as made-up facts, sources and numbers, are a natural result of that process, not a rare accident. Third, check an answer yourself: open the cited source, re-ask in a new chat, and recompute the numbers.

Our theme today: fluent is not the same as true.

You only need to have used a chat AI before. Let's start with what happens when it reads your question.

## 2
You have probably typed a question into a chatbot and got a smooth, confident answer back. So what is actually going on inside?

Look at the chart on the right. It shows what the model sees after the words "The capital of Australia is". Each bar is one candidate for the next token, and its height is the probability the model gives it. Canberra, in blue, is tall. Sydney, in red, is shorter, but it is clearly there. The numbers on this chart are only an example.

The model does this for every token in its vocabulary. GPT-2, for instance, has 50,257 of them. Then it draws one, weighted by those probabilities, appends it to the text, and does the whole thing again.

Think of the next-word suggestions on your phone keyboard, scaled up until it writes the whole reply. And here is a trap: Sydney is Australia's largest city, but it is not the capital, and it still gets a real share of the probability.

Before we go on, make a guess. When it answered, did it look the answer up somewhere? Keep that guess in mind. First, let's see what a token actually is.

## 3
Let's look more closely at the candidates from the last slide. The unit the model chose from was not a word. It was a token.

Below, the same sentence, "The capital of Australia is", is cut into boxes. Each box is one token. Short, common words often get a box of their own, and longer or rarer words can be split into pieces. The 27 characters of this sentence became 5 tokens. At the bottom, a rare place name, Dubbo, is cut into two pieces. The split shown here is just an example, because each model has its own way of cutting text.

So how long is a token? OpenAI gives a rule of thumb for English: one token is about 4 characters, or about three quarters of a word. In other words, 100 tokens is roughly 75 words.

Here is where people slip. That ratio is for English. OpenAI notes that other languages have different ratios, so do not carry the 4-character rule over to every language.

Tokens also set the length limit. What the model can read at once is counted in tokens, not in words or pages. For GPT-3 in 2020, that limit was 2,048 tokens.

Next, how does the model learn which token should come next?

## 4
The answer is training.

Follow the flow chart on the right from the top. Take some real text and hide the next token. The model guesses it. The guess is compared with the real token, and the numbers inside the model are nudged a little toward the right answer. Then it all repeats, again and again.

Those numbers are called parameters. They are values inside the model that training sets. GPT-3 has 175 billion of them. During training, GPT-3 read about 300 billion tokens drawn from web pages, books and Wikipedia.

Be careful with that number. 300 billion is how many tokens it saw during training, not the size of the data itself.
※ The mix of filtered Common Crawl, WebText2, Books and Wikipedia adds up to about 499 billion tokens. Training sampled from it with weights.

Now look at what the loop actually checks: only whether the guess matched the real text. So what it learns is how text continues, not a list of facts. Hold on to that; we will need it later.

So what happens when you actually chat with a model like this?

## 5
Look at the picture on the right. The whole chat is laid out as one long document: the instructions, then your message, its reply, your next message, and finally an empty slot where the reply's next token goes. Every time you send a message, all of this is sent to the model in full. OpenAI's documentation describes each request as independent and stateless. So the model's "memory" of the chat is really just this document, handed over again each turn, and the reply is its likely continuation.

But there is a catch. A model that only predicts how text continues will not necessarily continue in the form of an answer to your question. That is why tuning comes in. Plain GPT-3 just continues text. InstructGPT was tuned on example replies written by people, and on people's rankings of its own replies, so that preferred replies became more likely.

The result is striking. People preferred answers from the 1.3 billion parameter InstructGPT over the 175 billion parameter GPT-3. That is about one hundredth of the parameters.

But even a tuned model still draws its tokens, so let's see what that does.

## 6
But that does not mean the model always says the most likely thing. Each token is a draw.

Look at the chart on the left. It shows the same capital candidates at three temperatures. Temperature is a dial applied just before the draw. At temperature 1 we have the original numbers: Canberra 62%, Sydney 25%, Melbourne 8%, and everything else 5%. Think of a lottery where 62 of 100 tickets say Canberra. At a low temperature, 0.5, the tall bar gets taller: Canberra 84%, Sydney 14%. At a high temperature, 2, the bars flatten out: Canberra 44%, Sydney 28%, Melbourne 16%.
※ (Lecturer's calculation) The values at 0.5 and 2 are computed from the example probabilities, with "other" counted as one candidate.

So why not just always pick the top token? Researchers found that doing that makes text bland and strangely repetitive, so models draw instead.

A common mistake is to think you control this dial. ※ (Not from the source) In chat apps, you usually cannot change the temperature; the provider picks the value. That is why the same question in a new chat can get a different answer.

But does what it draws match the facts? Let's look at the evidence.

## 7
Before I show you the chart, make a guess. When an AI lists references for a paper, what share of them do you think do not exist? Well, the result was 55% for ChatGPT running GPT-3.5.

Look first at the GPT-3.5 bar for made-up references: more than half. The newer GPT-4 did better, at 18%, but that is still about one in five. The same study also found that even among the real references, 43% from GPT-3.5 and 24% from GPT-4 had major errors, such as the wrong authors, year or pages. That part is not on the chart. The study checked 636 references from 84 short papers on 42 topics, in 2023. That is one study and one task. Newer models and tools with search may do better, but, as we will see when we open the source, not perfectly.

At the start, you guessed it looked the answer up. It did not. Asking it to check itself does not help either. In Mata v. Avianca in 2023, a lawyer asked ChatGPT whether a case was real. It said yes. The case did not exist, and the lawyers were fined 5,000 dollars.

This is called hallucination. The survey defines it as text that is nonsensical or unfaithful to the provided source. In this course we also use it for content that does not match the facts.

So here is today's question. If it reads so fluently, why does it make things up so confidently?

## 8
Another surprise is that newer models are not free of this problem.

Look first at the made-up bars on the right. The older o1 made up answers to 16% of the questions. The newer o3 made up answers to 33%, about twice as many. And o4-mini reached 48%, about three times as many.

These numbers come from PersonQA, a test that asks about published facts on real people. Each rate is a share of all the PersonQA questions. OpenAI reported them in its system card in April 2025.

Now, here is where it is easy to misread the chart. o3 is not simply worse. Its accuracy also went up, to 59% compared with 47% for o1. It makes more claims overall, so it gets more answers right and also more answers wrong. And this is one company's result on one test, so we should not stretch it further.

Still, the lesson is clear enough. You cannot skip checking just because a model is newer.

So is there a pattern in when models guess instead of holding back? The next result looks at exactly that.

## 9
Another pattern shows up in how often a model is willing to say "I don't know".

Look first at the right answers on the chart. They are almost the same: 22% for gpt-5-thinking-mini and 24% for o4-mini. Now look at the wrong answers. gpt-5-thinking-mini got 26% wrong, but o4-mini got 75% wrong, nearly three times as many.

The difference is in the first number. gpt-5-thinking-mini said "I don't know" to 52% of the questions. o4-mini said it to just 1%. Each figure is a share of all the SimpleQA questions, which are short fact questions. So guessing on almost everything added only a couple of right answers, but a huge number of wrong ones.

A word of caution. This comes from OpenAI's own announcement in September 2025. It compares two models from the same company on one test, and the test only has short fact questions. So we should not read more into it than that.

Here is the part to remember. A confident tone is not a sign that the answer is right. The model that sounded sure about everything was wrong most of the time.

So why do models guess instead of saying "I don't know"? That is the next slide.

## 10
So why does it make things up so confidently? The last three charts showed fake references, wrong answers, and a model that almost never said "I don't know." The answer to our question is this: nothing in it checks facts. It draws likely continuations of its training text, so rare facts, facts after its cutoff, and guesses that tests reward all come out fluent but wrong.

The first block on the slide is my own summary: no step checks facts. The next-token probability we started with comes from how text usually continues, not from a list of facts.

First, rare facts. Now look at the chart on the right. I read two points off a figure in Kandpal and colleagues' 2023 paper, so the values are approximate. Each bar is the answers of BLOOM-176B to TriviaQA questions: blue is right, red is not right. On the left is a rare fact, with only about 10 pretraining documents about it. Accuracy is about 25%, so about three answers in four are not right. On the right is a common fact, with about 10,000 documents. Accuracy is over 55%. A fact the model has rarely seen never gets a high probability for the right continuation.

Two more reasons are not on the slide. Second, every model has a cutoff, the date its training text ends. For GPT-4 in 2023, that was September 2021, so later events are simply not in the data.

Third, tests usually rate a guess above "I don't know", and training follows the score.

So how should we use it? On the next slide, we open the source ourselves.

## 11
So we use one simple habit: open the source and find the sentence yourself. These three steps are my own recommendation.

First, ask the AI for the source. Second, open it yourself. Search by the title, the authors, and the DOI, which is the paper's ID. Third, find the actual sentence that supports the claim.

Now follow the flow chart on the right, from the top. Is a source given? If not, go right and mark the claim "unverified". Can you open it? If not, the same. Does it actually say this claim? Only when all three answers are yes do you reach the bottom and use it. If you cannot find the sentence, write "unverified" and leave the claim out.

Why go this far? Even legal research AIs that search a database first and then write made things up on 17 to 33% of test questions in a 2024 study. Some of these tools, such as Lexis+ AI, were advertised as hallucination-free. The writing step is still next-token prediction. Even real papers can come with wrong authors or years. And asking the AI "Is this real?" is not a check, as we saw with the Mata case.

Another check is to re-ask, and we turn to that next.

## 12
Here is the key idea: answers that disagree flag likely errors. Earlier we saw that each token is a new draw. Here we use that draw as a test.

Ask the same question again in a new chat. Do not use the same chat, because the whole chat, including the old answer, is sent again as one document, and the model tends to continue what it already wrote.

Now compare the two sides. On the left, two new chats both say Canberra. On the right, one says Canberra and the other says Sydney. The study behind this idea found that when a model knows a fact, sampled answers tend to agree. When it is guessing, they tend to diverge and contradict each other. So disagreement is a warning sign.

But be careful: agreement is not proof. If a wrong token is the most likely one, it can win every draw, and you get the same wrong answer twice.

For numbers, recompute the sums and percentages yourself, and find the original figure. You will try this in question 1-6.

So, back to our question: why does it make things up so confidently? Nothing in it checks facts, so the checking is our job: open the source, re-ask, and recompute. Now let's review with some questions.

## 13
Let's check what you have learned so far with three questions.

Question 1-1 asks what a chat AI computes at each step of a reply, and what it does with the result. If you are not sure, look back at the next-token chart.

Question 1-2 asks why two new chats can give two different answers to the same question. Answer it using how each token is chosen. The temperature chart will help.

Question 1-3 is about a friend who thinks the AI must have looked up a paper, because it gave the authors and the journal. What is wrong with that reasoning? The fake-references chart will help.

Take a few minutes and write your answers in your own words before moving on.

## 14
Here are three more questions, this time about why errors happen and how to check them.

Question 1-4 asks which birth year a chat AI is more likely to get wrong: a world-famous scientist's, or a little-known local politician's. Explain your choice. The rare-facts chart will help.

Question 1-5 gives you a claim backed by "Smith (2021), Journal of Learning". Before you put that claim in a report, what steps do you take? Look back at the open-the-source steps.

Question 1-6 gives you a sentence about students who use the library. Check the number yourself, and name one more check you would do. The re-ask slide will help.

Write down your answers before we go to the answer slides.

## 15
Let's go through the answers.

Question 1-1. At each step, the model computes a probability for every possible next token, given all the text so far, which means the whole chat. It then draws one token, appends it, and repeats until the reply is done. A reply is built one token at a time in this loop.

Question 1-2. Each token is a weighted random draw from those probabilities, not always the top token. So a less likely token, even a wrong one, is sometimes picked, and the rest of the reply follows from it. How much the answers vary depends on the temperature. Every draw is a new chance, so two chats can split early and end up far apart.

Question 1-3. Authors and a journal name are just likely-looking text. Nothing in the model checks that the paper exists. In a 2023 study, 55% of the references from GPT-3.5 and 18% from GPT-4 did not exist. So open the paper yourself. A reference can look complete and still be made up, because the format is easy to predict.

## 16
Here are the answers to the last three questions.

Question 1-4. The local politician. A fact like that appears in few training documents, so the right year never gets a high probability, and a plausible wrong year is more likely to be drawn. Accuracy rises with the number of documents about a fact, from about 25% to over 55% in that graph.

Question 1-5. Search for the paper by its title, authors and year, or its DOI, and open the original. Then find the sentence that supports the claim. If you cannot find it, or it says something else, mark the claim "unverified" and do not use it. Asking the AI "is it real?" does not count. Even search-based tools made things up, so only the original text settles it.

Question 1-6. Thirty percent of 1,200 is 0.30 times 1,200, which is 360, not 390. The two numbers do not match, since 390 would be 32.5%, so at least one of them is wrong. One more check is to find the original survey. Re-asking in a new chat is weaker, because agreement is not proof. Recomputing and finding the original figure come first.

