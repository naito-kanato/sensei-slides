## 1
Welcome to Lecture 1. Today we look at what the chat AI you use every day is actually doing inside.

By the end, there are three things I'd like you to be able to explain. What generative AI computes. Why plausible-sounding mistakes happen. And how to check AI's answers, how to ask it things, and what you should not put into it.

## 2
A chat AI answers your questions smoothly, in natural sentences. So what is it doing inside, and how far can you trust its answers? This lecture answers those questions.

At the heart of a chat AI is something called a large language model, or LLM. It is given a vast amount of text to read, and from it picks up, as probabilities, which words tend to follow which. This is called training. When it writes a sentence, it follows steps 1 to 3 on the left: it reads the preceding context, then computes how likely each word is to come next.

The figure on the right shows example candidates for the word after "Tomorrow's weather is." The probabilities are just an example, but "sunny" is the highest, followed by "rainy" and "cloudy." The model picks one according to these probabilities, appends it, and builds the sentence that way.

A common misconception is that the AI looks up the answer in some database and shows it to you. The model itself does not search anything; it builds the text one word at a time from these probabilities. Services that search while answering are covered on slide 8.

These probabilities come from how often words follow each other in a vast amount of text; they do not directly check whether something is true. So the key point is that what it computes is "plausibility," not whether something is a fact.

Now, do you think it always picks the most likely word? We'll answer that on slide 6.

* (Source) Brown et al., NeurIPS 2020 (GPT-3).

## 3
I said "word" just now, but strictly speaking, the unit a model handles is a token: a word or part of a word. The figure on the right splits "Tomorrow's weather is sunny" into five tokens, but the actual split differs from model to model. In some languages, such as Japanese, a single character can even become two or more tokens.

How much a model can read at once is also set in tokens. For example, GPT-3, a large language model from 2020, could handle up to 2048 tokens. Today's models can read much more, but there is still a limit.

So if you hand it a long document, it may not all fit in at once. One way around this is to give it the document chapter by chapter.

* (Source) Brown et al., NeurIPS 2020 (GPT-3's context length of 2048 tokens). How Japanese is split depends on the model; this is a general point.

## 4
Next, how is this model made? Training has two main stages.

The first is pretraining. The model reads a vast amount of text and practices predicting the next word. But on its own, this gives a model that "continues text," and it won't necessarily answer questions. Since all it does is predict the next word, after a question it might write a continuation of the question, or another question, instead of an answer.

The second stage is tuning. The model learns from example answers written by people, and is then adjusted with reinforcement learning based on how people ranked its answers. Reinforcement learning is training that nudges the model toward answers that get high ratings. This is the third box in the flow on the right: RLHF, reinforcement learning from human feedback.

This tuning makes a big difference. In one study, answers from a tuned model with 1.3 billion parameters were preferred over those from GPT-3, an untuned model with 175 billion parameters. A parameter is a number inside the model whose value is set by training. The study also reported more factual answers and fewer harmful outputs. As we'll see on slide 5, more parameters generally means the model can learn more. Yet a tuned model more than 100 times smaller won, which suggests that what mattered was less the amount of knowledge and more the way of answering. One view is that tuning mainly changes how the model answers.

* (Source) Ouyang et al., NeurIPS 2022 (InstructGPT).
* (Supplement beyond the sources) One view holds that most knowledge comes from pretraining and tuning mainly changes how the model answers (Zhou et al., "LIMA", NeurIPS 2023).

## 5
What exactly is "large" about a large language model? It is the number of parameters we met on slide 4, the numbers inside the model.

As the numbers on the slide show, GPT-2 in 2019 had 1.5 billion parameters, and GPT-3 in 2020 had 175 billion: more than a 100-fold jump in just over a year.

There was a reason for making models bigger. It has been reported that as you increase model size, amount of data, and compute, the error in predicting the next word falls steadily, following a power law. A power law here means that every time you make the model 10 times bigger, the error drops by a fixed ratio. Some of these trends held over a range of more than seven orders of magnitude. The better the predictions, the more natural the text. But becoming natural is not the same as becoming correct, and that is the topic of slide 7.

* (Source) Radford et al., OpenAI 2019 (GPT-2). Brown et al., NeurIPS 2020 (GPT-3). Kaplan et al., arXiv:2001.08361 (2020) (power law).

## 6
However, making the model bigger does not make its answers the same every time. Here is the answer to the question from slide 2. The model does not always pick the most likely word. It is known that always picking the most likely word tends to produce dull text that repeats the same phrases. So instead, it picks as if drawing lots weighted by probability. This is called sampling.

The setting that controls how much the choice varies is called temperature. The figure on the right takes the probabilities of the four candidates from slide 2, rescales them so they add up to 1, and then changes the temperature. That is why even at temperature 1 the values differ a little from slide 2. At a low temperature, the choice concentrates on "sunny," the most likely word. At a high temperature, unlikely words such as "snowy" become more likely to be picked. The number above each bar is the temperature.

So even if you ask the same question, the answer can change. At a low temperature, you get nearly the same answer. You have probably asked the same question again and received a different answer. That is because of this mechanism.

* (Source) Holtzman et al., ICLR 2020 (always picking the most probable word produces dull, repetitive text). The probabilities in the figure were calculated from the example on slide 2.

## 7
If answers merely changed each time, that would not be a big problem. But do you think that if a text is natural and coherent, its content must be correct too? In fact, not necessarily. Content that sounds plausible but is false or has no basis is called a hallucination.

You might think, "If it reads naturally, surely it's right?" That is the first question on the left. As we saw on slide 2, what the model computes is how likely words are to follow, so natural-sounding text and correct content are two different things. The answer to the second question is the example of citing references that do not exist. The figure on the right shows values from a study that had ChatGPT write short literature reviews; these are from the 2023 versions. Of the references it cited, 55% did not exist for GPT-3.5, and even for GPT-4, 18% did not.

So even when it sounds confident, you should not use its answer without checking.

* (Source) Ji et al., ACM Computing Surveys 55(12), 2023 (definition paraphrased for a general audience). Walters & Wilder, Sci. Rep. 13, 14045 (2023) (values from 42 topics and 636 references).

## 8
Why do such errors happen? Here are three main reasons.

First, as we have seen, the model itself only links words by probability; it does not check them against facts. Some services search while answering, but that is a search system added outside the model. Second, topics that are rare or absent in the training data. Even there, the model still produces plausible-sounding text. There are also reports that the fewer times a fact appears in the training data, the more likely the model is to get it wrong. Because the probabilities are set by how likely words are to follow in text, a fact that rarely appears does not get a high probability for the correct continuation, yet some word still gets picked. Rare personal names and detailed numbers are examples.

Third, the training data has a cutoff. As the figure on the right shows, the model does not know about events after the cutoff. For example, a 2023 report says GPT-4 generally lacks knowledge of events after September 2021. Current versions have later cutoffs, but there is still a cutoff.

So the newer the topic, or the more it involves rare names or detailed numbers, the more careful you need to be.

* (Source) Ji et al., ACM Computing Surveys 55(12), 2023 (overview of causes). Kandpal et al., ICML 2023 (facts with fewer related documents in the training data are answered less accurately). OpenAI, GPT-4 Technical Report, arXiv:2303.08774 (2023) (September 2021).

## 9
So how far can you trust AI's answers? The answer to our opening question is: check before you use them. As the flow on the right shows, ask the AI for its sources, then check those sources against primary documents: papers, official documents, or the original texts. If the source is a reference, search for it by title, author, and DOI, a unique ID given to each paper, and open the original. Slide 7 was about references that do not exist, but even when a reference does exist, the content the AI attributes to it may not be in it. A source that cannot be found, or whose content differs, is marked "needs checking," as the arrow on the left shows, and is not used as it is. It also matters not to feel reassured just because you found a different paper with a similar title.

Another approach is to give the AI materials and have it answer from them. The method of passing retrieved materials to the model and having it answer is called RAG, and it has been reported to produce more factual text than answering without materials. Since the materials you give it are read as context, it can answer even about events after the cutoff on slide 8, as long as they are in the materials.

* (Source) Lewis et al., NeurIPS 2020 (RAG).

## 10
How you ask also changes the answer. First, state your goal, conditions, and the form of the answer you want. For example, instead of just "summarize this," saying "for a seminar presentation, in three lines, with explanations for technical terms" gets you an answer closer to what you want. Your request is also part of the preceding context from slide 2, so the more clearly the goal and conditions are written, the more likely a matching continuation is to be picked. If there are materials you want it to use, give it those too.

The other technique is to have it write out its intermediate reasoning. The figure on the right shows results from math word problems solved after showing the model eight examples. When the examples showed only the answers, accuracy was 17.9%; when they showed the reasoning written out, it rose to 56.9%. Note, however, that this was with a 540-billion-parameter model, larger than the 175-billion GPT-3 on slide 5, and it did not help smaller models. This result alone can't tell us how well it applies to the AI you use today. One explanation for why it works is that the reasoning it writes out also becomes context when it picks the words of the answer.

There is also a report that simply adding "Let's think step by step" to your request, without showing any examples, raises accuracy.

And when you check its answer, having the reasoning written out makes it easier to spot where it went wrong.

* (Source) Wei et al., NeurIPS 2022, Table 2 (PaLM 540B, GSM8K; no effect in small models). Kojima et al., NeurIPS 2022 (adding "Let's think step by step" without examples).

## 11
Finally, information to check before you put it in. We'll go through the three questions on the left in order. First, is your input used for training? Some services are set up so that what you enter is used to train the model. If it is used for training, there is a risk that it could show up in answers to other people.

The three on the right, personal information, confidential documents, and unpublished research data, are things to stop and think about before entering. Japan's Personal Information Protection Commission has also warned general users that personal information they enter may be used for training and may appear in AI output, and urges them to check the terms of use and privacy policy. Confidential documents and unpublished data are not covered by that advisory, but they call for care for the same reason.

What you should check are the service's terms of use and settings, and the rules of your university, company, or other organization. If you can't confirm them, the safe choice is not to enter it.

* (Source) Personal Information Protection Commission (Japan), "Advisory on the Use of Generative AI Services" (June 2, 2023), item (3), cautions for general users. Confidential and unpublished data are a supplement beyond the source.

## 12
Now for the review questions. There are six, over two slides. How would you answer them? Use the "Answer 1-1" button at the bottom of the script page to write your answers.

* Answers are on slide 14.

## 13
Here are the last three. When you've finished writing, press "Export" and tell me "I commented." I'll mark your answers and send them back.

* Answers are on slide 15.

## 14
Here are the answers. For 1-1, it is the probability of the next token, given the preceding context. It picks tokens one by one according to that probability and joins them into text.

For 1-2, it is because the model picks by probability, that is, it samples, so unlikely words are sometimes chosen. Answers are not always different, though: at a low temperature you get nearly the same answer. The temperature setting changes how much the answers vary.

For 1-3, it is because pretraining alone gives a model that just continues text, and tuning makes it answer by following instructions. Also keep in mind that what changes most is mainly the way it answers.

## 15
For 1-4, it is producing content that sounds plausible but is false or has no basis. An example is citing references or numbers that don't exist. As slide 8 showed, it is also likely with new topics or detailed numbers, so naming one of those is also correct.

For 1-5, search by title, author, journal, and DOI, then open the original and check its content. If it can't be found, or the content differs, don't use it and mark it "needs checking." It is also important not to feel reassured just because you found a different paper with a similar title.

For 1-6, check the terms of use and settings to see whether your input is used for training. Also check your organization's rules, and if you can't confirm, don't enter it.

That's all for today. Thank you for your hard work.
