"""Lecture 1: What Generative AI Actually Computes（設計メモ memo.md の表から scaffold.py が作った骨組み。TODO を書き換える）。

    python <skill>/scripts/make_deck.py <この作業フォルダ>   # 図→組む→描く→検査を1回で
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parents[3]   # 見本はリポジトリの scripts/ を使う
sys.path.insert(0, str(SKILL / "scripts"))
from set_notes import load_notes  # noqa: E402
from slide_profile import author, deck_options, load_profile  # noqa: E402
from zemi import Deck  # noqa: E402

T = "Lecture 1: What Generative AI Actually Computes"
FIG = HERE / "figs"
OUT = HERE.parents[1] / "AI_Literacy" / "01_What Generative AI Actually Computes_slides.pptx"

P = load_profile(HERE)
AUTHOR = author(P)   # 表紙の名前（発表は一覧の「発表者名」、無ければ空。講座は「講座名（全N回）」。仮の名前を入れない）
deck = Deck(workdir=HERE / "build", **deck_options(P))   # テンプレートを選ぶなら deck_options(P, name="テンプレート2") など


def qa(s, items, size=22, gap=0.45):
    """確認問題・解答の本文。items = [(番号, 本文)]。番号は「1-1」の形（原稿HTMLの「1-1 に答える」ボタンになる）"""
    s.at(1.0, 2.0)
    for j, (k, txt) in enumerate(items):
        s.p("{b:" + k + "}  " + txt, size=size, gap=gap if j < len(items) - 1 else 0.2)

# ---------------------------------------------------------------- 1 表紙
deck.title_slide([T], author=AUTHOR, roadmap=["Tokens", "Token odds", "Pick, repeat", "What to check"])

# ---------------------------------------------------------------- 2 Six cases that never existed
s = deck.slide(T, summary="In 2023, lawyers cited six cases ChatGPT made up")
s.heading("Six cases that never existed")
s.block("Case:", ["Mata v. Avianca, New York, 2023", "belief: it \"could not\" fabricate"], then="{r:Fluent}, yet invented")
s.compare(("What the lawyers assumed", ["looked up by ChatGPT", "real court rulings", "safe to cite"]), ("What actually happened", ["text written by ChatGPT", "{r:six cases that never existed}", "a $5,000 fine"]), size=18)

# ---------------------------------------------------------------- 3 Today's question
s = deck.slide(T, summary="Your phone keyboard already predicts your next word")
s.heading("Today's question")
s.lead(["You tap its next-word guesses daily", "Have you trusted a sure-sounding\nreply?"], "{r:What does generative AI actually compute?}")
s.flow(["You type \"See you\"", "Keyboard offers\nsoon, later, tomorrow", "You tap one"], x=deck.area["fig_x"], y=deck.area["top"] + 0.1, w=5.0, size=18)

# ---------------------------------------------------------------- 4 Step 1: tokens
s = deck.slide(T, summary="Text is cut into tokens: 100 tokens ≈ 75 words")
s.heading("Step 1: tokens")
s.block("Token:", ["a word, part of a word, or a mark"])
s.block("Size:", ["about {r:4 letters} of English text", "other languages split differently"])
if (FIG / "s04.png").exists(): s.figure_beside(FIG / "s04.png")   # 図：仕組み：模式図：the sentence "Chatbots predict text." cut into four （図は figs/s04.png）

# ---------------------------------------------------------------- 5 Step 2: probabilities
s = deck.slide(T, summary="Each possible next token gets a probability")
s.heading("Step 2: probabilities")
s.lead(["Trained on 300 billion tokens", "Tuned to predict the next token"], "{r:A table of likely next tokens}")
if (FIG / "s05.png").exists(): s.figure_beside(FIG / "s05.png")   # 図：仕組み：模式図：after "The capital of France is", candidate next tok（図は figs/s05.png）

# ---------------------------------------------------------------- 6 Step 3: pick and repeat
s = deck.slide(T, summary="It picks one token, appends it, and repeats")
s.heading("Step 3: pick and repeat")
s.lead(["Each pick involves chance", "Higher temperature = more random"], "{r:Same question}, a different reply")
s.flow(["Text so far", "Probabilities for\neach next token", "Pick one,\nwith some chance", "Append it and\ngo again"], h=0.85, gap=0.45, x=deck.area["fig_x"], y=deck.area["top"] + 0.1, w=5.0, size=18)

# ---------------------------------------------------------------- 7 Plausible but fake
s = deck.slide(T, summary="GPT-3.5 invented 55% of citations, GPT-4 18%")
s.heading("Plausible but fake")
s.lead(["Short literature reviews, 2023", "Newer model: fewer, not zero"], "{r:Fluent reference ≠ real reference}")
if (FIG / "s07.png").exists(): s.figure_beside(FIG / "s07.png", caption="(Walters et al. 2023)")   # 図：比べる：棒グラフ：データ1（図は figs/s07.png）

# ---------------------------------------------------------------- 8 A search that slipped?
s = deck.slide(T, summary="Asked 3 times, a model gave 3 different wrong dates")
s.heading("A search that slipped?")
s.block("Test:", ["Kalai's birthday, to DeepSeek-V3", "told to answer only if known"])
s.block("Reading:", ["a lookup gives 1 answer"], then="{r:Not a search that slipped}")
s.compare(("A failed lookup", ["finds a real source", "same answer each time", "wrong in places"]), ("A likely continuation", ["may name a source\nthat never existed", "a new answer each try", "fluent either way"]), size=18)

# ---------------------------------------------------------------- 9 Why it guesses
s = deck.slide(T, summary="Tests reward a 1-in-365 guess over \"I don't know\"")
s.heading("Why it guesses")
s.cur_y = s.key_message("1/365", sub="chance that a guessed birthday is right", y=deck.area["top"] + 0.1).bottom + 0.45   # 図の案から scaffold.py が組んだ（言い方を確かめる）
s.block("Rare facts:", ["seen once in training text", "no pattern to learn from"])
s.block("Grading:", ["\"I don't know\" scores zero"], then="{r:So guessing pays}")
if (FIG / "s09.png").exists(): s.figure_beside(FIG / "s09.png")   # 図：印象：大きな数字：1/365（chance that a guessed birthday is right）（図は figs/s09.png）

# ---------------------------------------------------------------- 10 The answer
s = deck.slide(T, summary="It computes what is likely next, not what is true")
s.heading("The answer")
s.block("Answer:", ["next-token odds, pick, repeat", "no step checks the world"])
s.block("Like:", ["your keyboard, tapped to the end"], then="{r:Likely ≠ true}")
if (FIG / "s10.png").exists(): s.figure_beside(FIG / "s10.png")   # 図：仕組み：模式図：the pick-and-repeat loop (text so far → probabilitie（図は figs/s10.png）

# ---------------------------------------------------------------- 11 Where to check
s = deck.slide(T, summary="Check the names, numbers and sources you rely on")
s.heading("Where to check")
s.block("Risky:", ["names, dates, numbers,\nsources", "facts you will repeat"])
s.block("Safer:", ["wording, structure, ideas"])
s.decision([("Only wording or ideas?", "Use it as a draft"), ("Will you rely on a name,\nnumber or source?", "Check it in\nthe original")], "Use it, marked\nunchecked", x=deck.area["fig_x"] - 1.3, y=deck.area["top"], q_w=3.0, out_w=2.2)   # 図の案から scaffold.py が組んだ（言い方を確かめる）

# ---------------------------------------------------------------- 12 How to check
s = deck.slide(T, summary="Only 7% of 115 references were real and accurate")
s.heading("How to check")
s.numbered(["Search the exact title", "Match authors, year, journal", "Find the claim inside"])
s.lead(["GPT-3.5 (ChatGPT),\nmedical papers, 2023"], "{r:A real paper may not say it}")
if (FIG / "s12.png").exists(): s.figure_beside(FIG / "s12.png", caption="(Bhattacharyya et al. 2023)")   # 図：内訳：帯グラフ：データ2（図は figs/s12.png）

# ---------------------------------------------------------------- 13 Back to the lawyers
s = deck.slide(T, summary="The fake cases were likely text, not failed searches")
s.heading("Back to the lawyers")
s.block("Computed:", ["likely next tokens"])
s.block("Missed step:", ["opening the cases", "none of the six existed"], then="{r:Fluent says nothing about true}")
s.flow(["Ask for\nsupporting cases", "Likely tokens:\nnames, courts, years", "A fluent citation", "Not in any\ncourt record"], h=0.85, gap=0.45, x=deck.area["fig_x"], y=deck.area["top"] + 0.1, w=5.0, size=18)

# ---------------------------------------------------------------- 14 Summary
s = deck.slide(T, summary="Likely next token, not the truth")   # まとめ：結論の一文はこの回の答え
s.heading("Summary")
s.recap(kind="前と後", pairs=[("Looks it up", "Guesses tokens"), ("Fluent = true", "Fluent = likely"), ("Cited = real", "Open the source")])   # まとめの形「前と後」（話の型から。合わなければ kind を変える。新しい事実は入れない。references/story.md 3節）

# ---------------------------------------------------------------- 15 Check questions (1-1 to 1-3)
s = deck.slide(T)   # summary なし：帯も●も無い枚になる
s.heading("Check questions (1-1 to 1-3)")
qa(s, [("1-1", "What is a token, and about how many English words do 100 tokens\nmake?"), ("1-2", "You ask a chatbot the same question twice and get two different\nreplies. Using the loop, explain why."), ("1-3", "A friend says: \"The chatbot cited a paper that does not exist,\nso its search must have failed.\" What is wrong?")])

# ---------------------------------------------------------------- 16 Check questions (1-4 to 1-6)
s = deck.slide(T)   # summary なし：帯も●も無い枚になる
s.heading("Check questions (1-4 to 1-6)")
qa(s, [("1-4", "Compare the 2023 study's fake-citation rates for GPT-3.5 and\nGPT-4. What do they tell you about newer models?"), ("1-5", "A chatbot says \"a 2021 study found 62% of students...\" and you\nwill quote it in a report. What do you check, and how?"), ("1-6", "What does generative AI actually compute? Answer with the\none-line answer and the analogy.")])

# ---------------------------------------------------------------- 17 Answers (1-1 to 1-3)
s = deck.slide(T)   # summary なし：帯も●も無い枚になる
s.heading("Answers (1-1 to 1-3)")
qa(s, [("1-1", "A piece of text (word, part of a word, mark). 100 tokens ≈ 75\nwords, because 1 token ≈ 3/4 word. (slide 4)"), ("1-2", "Each pick is drawn by chance from the probabilities, and because\neach pick changes what follows, replies differ. (slide 6)"), ("1-3", "It wrote likely tokens, not a search, because asked one birthday\n3 times, a model gave 3 different dates; a lookup would not.\n(slide 8)")])

# ---------------------------------------------------------------- 18 Answers (1-4 to 1-6)
s = deck.slide(T)   # summary なし：帯も●も無い枚になる
s.heading("Answers (1-4 to 1-6)")
qa(s, [("1-4", "55% vs 18% fake: newer models invent fewer but not zero, so you\nstill check, because fluency is no proof. (slide 7)"), ("1-5", "The study, year and 62%, because names and numbers are where it\nguesses: search the title, open it, find the claim. (slide 12)"), ("1-6", "Next-token odds: it picks one, appends, repeats, so it scores\nlikely, not true. Like your keyboard's guess tapped to the end.\n(slide 10)")])

NOTES = load_notes(HERE / "notes.md")
for i, sl in enumerate(deck.slides, 1):
    if i in NOTES:
        sl.notes(NOTES[i])
OUT.parent.mkdir(parents=True, exist_ok=True)
deck.save(OUT, title=T, author=AUTHOR)
