"""Lecture 1: What a Chat AI Computes（設計メモ memo.md の表から scaffold.py が作った骨組み。TODO を書き換える）。

    python <skill>/scripts/make_deck.py <この作業フォルダ>   # 図→組む→描く→検査を1回で
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parents[3]
sys.path.insert(0, str(SKILL / "scripts"))
from set_notes import load_notes  # noqa: E402
from slide_profile import author, deck_options, load_profile  # noqa: E402
from zemi import C, Deck, line_height_in  # noqa: E402

T = "Lecture 1: What a Chat AI Computes"
FIG = HERE / "figs"
OUT = HERE.parents[1] / "AI_Literacy" / "01_What a Chat AI Computes_slides.pptx"

P = load_profile(HERE)
AUTHOR = author(P)   # 表紙の名前（発表は一覧の「発表者名」、無ければ空。講座は「講座名（全N回）」。仮の名前を入れない）
deck = Deck(workdir=HERE / "build", **deck_options(P))   # テンプレートを選ぶなら deck_options(P, name="テンプレート2") など


def qa(s, heading, items, size=20, gap=0.3):
    """確認問題・解答の枚。見出しは本文の枚の結論の一文と同じ見た目（28pt の主色の太字）で、1問ずつ横いっぱいの薄い灰の箱に。
    items = [(番号, 本文)]。番号は「1-1」の形（原稿HTMLの「1-1 に答える」ボタンになる。箱の文字が「1-1  問題文」で始まる）。
    以前は文字だけを左半分に置き、見出しが細い灰色で、右と上が空いていた（外から見た採点の指摘）"""
    s.heading("{ab:" + heading + "}", size=28)
    x0, x1 = deck.wide
    y = deck.area["top"]
    for k, txt in items:
        h = max(1.0, (txt.count("\n") + 1) * line_height_in(size) + 0.45)
        s.rect(x0, y, x1 - x0, h, fill=C.LIGHT, text="{ab:" + k + "}  " + txt, size=size, align="l", name="確認問題の箱")
        y += h + gap


# ---------------------------------------------------------------- 1 表紙
deck.title_slide([T], author=AUTHOR)

# ---------------------------------------------------------------- 2 Predicting the next token
s = deck.slide(T, summary="It gives every possible next token a probability, then draws one")
s.heading("Predicting the next token")
s.numbered(["Read all the text so far",
            "Give every vocabulary token a\nprobability (GPT-2: {r:50,257} tokens)",
            "Draw one by its probability,\nappend it, repeat"])
s.block("Your guess:", ["it looked the answer up", "Did it?"])
s.figure_beside(FIG / "s02.png", caption="Example probabilities (schematic)")

# ---------------------------------------------------------------- 3 Tokens, not words
s = deck.slide(T, summary="One English token is about 4 characters of text")
s.heading("Tokens, not words")
# 上に文・下に図：2つのラベルを横に並べ、札の図（文と、まれな語が2つに割れる例）を下に横いっぱいに。
# 「Length limit」は原稿へ（文の塊は2つまで）
top = deck.area["top"]
b1 = s.block("Token:", ["a word or a piece of one", "rare words: split into pieces"], x=1.5, y=top, gap=0)
b2 = s.block("Rule of thumb:", ["1 token ≈ {r:4 characters}", "≈ ¾ of an English word"], x=7.3, y=top, gap=0)
s.at(1.0, max(b.bottom for b in (b1, b2)))
s.figure_below(FIG / "s03.png", gap=0.3, caption="Example split; differs by model (schematic)")

# ---------------------------------------------------------------- 4 Learning by guessing
s = deck.slide(T, summary="Training tunes GPT-3's 175 billion numbers to predict text")
s.heading("Learning by guessing")
# 手順は右の流れ図が見せるので、左は規模と学ぶものの2つの塊に（以前は同じ手順を本文の番号でも言い、塊が3つ）
s.at(1.0, deck.area["top"] + 0.3)
s.block("Scale:", ["175 billion numbers (parameters)", "about {r:300 billion tokens} read", "from web pages, books, Wikipedia"], gap=0.5)
s.block("What it learns:", ["how text continues,", "not a list of facts", "(the loop checks only the guess)"], gap=0)
s.flow(["Text, next token\nhidden", "Model guesses", "Compare with\nthe real token", "Adjust the numbers\n(parameters), repeat"],
       x=8.6, y=1.5, w=4.0, h=0.85, gap=0.45)

# ---------------------------------------------------------------- 5 A chat is one document
s = deck.slide(T, summary="The whole chat is resent each turn; the reply continues it")
s.heading("A chat is one document")
s.block("Each turn:", ["instructions + your messages", "+ its replies, {r:sent in full}"])
s.block("Tuning:", ["plain GPT-3 just continues text", "InstructGPT: tuned on human", "example replies and rankings"],
        then="1.3B InstructGPT preferred\nover 175B GPT-3")
s.figure_beside(FIG / "s05.png", caption="(schematic)")

# ---------------------------------------------------------------- 6 Why answers vary
s = deck.slide(T, summary="Each token is a weighted draw, so replies can vary")
s.heading("Why answers vary")
# 図が主役：温度ごとの棒そのものを読ませる（Canberra が下がり Sydney が上がる）。読み方を右の列に
s.figure_main(FIG / "s06.png", caption="The capital example, recomputed (schematic)")
s.block("Temperature:", ["a dial applied before the draw", "low sharpens, high flattens"], gap=0.3)
s.cases([("Low (0.5)", "Canberra 84%, Sydney 14%"),
         ("High (2)", "Canberra 44%, {r:Sydney 28%}")])

# ---------------------------------------------------------------- 7 Plausible is not true
s = deck.slide(T, summary="55% of the references ChatGPT (GPT-3.5) gave did not exist (2023)")
s.heading("Plausible is not true")
# 文の塊は2つ：問い（作り話の割合）と、名前と今日の問い。Mata v. Avianca は原稿へ
s.at(1.0, deck.area["top"] + 0.3)
s.ask("Did it look them up?", "Made up: GPT-3.5 {r:55%}, GPT-4 18%\n(636 references in 84 papers, 2023)", gap=0.5)
s.block("Hallucination:", ["generated text that is nonsensical", "or unfaithful to the source"],
        then="Fluent and sure, yet wrong: why?", gap=0)
s.figure_beside(FIG / "s07.png", caption="Walters & Wilder, Sci. Rep. 13, 14045 (2023)")

# ---------------------------------------------------------------- 8 Newer is not error-free
s = deck.slide(T, summary="o3 made up answers to 33% of PersonQA questions (o1: 16%)")
s.heading("Newer is not error-free")
s.at(1.0, deck.area["top"] + 0.3)
s.develop(("Older o1", ["made up 16%", "right 47%"]), ("Newer o3", ["made up {r:33%}", "right 59%"]), after=0.5)
s.block("PersonQA (Apr 2025):", ["questions about real people", "o4-mini: made up 48%", "one company, one test"], gap=0)
s.figure_beside(FIG / "s08.png", caption="OpenAI o3 and o4-mini System Card (Apr 2025)")

# ---------------------------------------------------------------- 9 Guessing beats "I don't know"
s = deck.slide(T, summary="o4-mini rarely said \"I don't know\" (1%) and got 75% wrong")
s.heading("Guessing beats \"I don't know\"")
s.figure_main(FIG / "s09.png", w=7.2, caption="OpenAI, Why language models hallucinate (Sep 2025)")
s.block("Reading:", ["SimpleQA: short fact", "questions (Sep 2025)", "gray: \"I don't know\""])
s.block("Compare:", ["right: 22% vs 24%", "wrong: 26% vs 75%"], then="guessing: few more right,\nmany more wrong")

# ---------------------------------------------------------------- 10 Why it goes wrong
s = deck.slide(T, summary="Nothing checks facts, so rare facts come out fluent but wrong")
s.heading("Why it goes wrong")
# 文の塊は2つ（確かめる段が無い・まれな事実）。締め切りと試験の採点は主題からずれるので原稿へ（外から見た採点の指摘）
s.at(1.0, deck.area["top"] + 0.3)
s.block("No step checks facts:", ["probabilities follow usual text,", "not a fact list"], gap=0.5)
s.block("Rare facts:", ["few documents → {r:low accuracy}", "≈10 documents: ≈25% right", "≈10,000 documents: >55% right"],
        then="right continuation stays unlikely", gap=0)
s.figure_beside(FIG / "s10.png", caption="Read from Kandpal et al., ICML 2023, Fig. 1 (approx.)")

# ---------------------------------------------------------------- 11 Open the source
s = deck.slide(T, summary="Open the source and find the sentence yourself")
s.heading("Open the source")
# 「If not found」は右の判定の流れ図の unverified が見せるので外す（文の塊は2つ）
s.at(1.0, deck.area["top"] + 0.3)
s.numbered(["Ask for the source", "Open it yourself (title,\nauthors, DOI: the paper's ID)", "Find the sentence\nthat supports the claim"], gap=0.5)
s.block("Why:", ["search-based legal AIs made", "things up on {r:17–33%} of questions (2024)",
                 "real references: major errors in 24–43%"], gap=0)
s.decision([("Is a source given?", "unverified"), ("Can you open it?", "unverified"), ("Does it say this claim?", "unverified")], "use it",
           x=deck.area["fig_x"], y=deck.area["top"], q_w=2.8, out_w=1.38, size=16, yes="No", no="Yes")

# ---------------------------------------------------------------- 12 Re-ask and recompute
s = deck.slide(T, summary="Re-asked answers that disagree flag likely errors")
s.heading("Re-ask and recompute")
# 比較の2列に3行ずつ（何が出たか・そこから言えること・どうするか）。枚の番号の参照は言葉に言い換えた
bot = s.compare(("Agree", ["{c:Canberra}, {c:Canberra}", "a known fact wins most draws", "not proof: a wrong token\ncan win every draw"]),
                ("Disagree", ["{c:Canberra}, {r:Sydney}", "a guess changes from draw to draw", "{r:warning sign}: open the source"]))
s.block("How:", ["re-ask in a new chat (no old answer resent)", "recompute numbers, find the original"], x=deck.area["x"], y=max(bot) + 0.3, gap=0)

# ---------------------------------------------------------------- 13 Quiz (1-1 to 1-3)
s = deck.slide(T)   # summary なし：帯も結論の一文も無い枚になる
qa(s, "Quiz (1-1 to 1-3)",
   [("1-1", "When a chat AI writes a reply, what does it compute at each step,\nand what does it do with the result?"),
    ("1-2", "You ask the same question in two new chats and get two different answers.\nExplain why, using how each token is chosen."),
    ("1-3", "A friend says: \"The AI gave the authors and the journal of a paper, so it must\nhave looked it up.\" What is wrong with this reasoning?")], gap=0.35)

# ---------------------------------------------------------------- 14 Quiz (1-4 to 1-6)
s = deck.slide(T)
qa(s, "Quiz (1-4 to 1-6)",
   [("1-4", "Which is a chat AI more likely to get wrong: the birth year of a world-famous\nscientist, or of a little-known local politician? Explain why."),
    ("1-5", "An AI answer supports a claim with \"Smith (2021), Journal of Learning\".\nYou want to use the claim in a report. Write the steps you take before using it."),
    ("1-6", "An AI says: \"30% of the 1,200 students, that is 390 students, use the library.\"\nCheck the number yourself, and name one more check you would do.")], gap=0.35)

# ---------------------------------------------------------------- 15 Answers (1-1 to 1-3)
s = deck.slide(T)
qa(s, "Answers (1-1 to 1-3)",
   [("1-1", "A probability for every possible next token, given all the text so far (the whole chat).\nIt draws one token, appends it, and repeats."),
    ("1-2", "Each token is a weighted random draw, not always the top token. A less likely (even\nwrong) token is sometimes picked, and the rest follows from it. The temperature sets how\nmuch answers vary."),
    ("1-3", "Authors and a journal are likely-looking text; the model does not check them. In 2023,\n55% of GPT-3.5's references and 18% of GPT-4's did not exist. Open the paper yourself.")], size=18, gap=0.3)

# ---------------------------------------------------------------- 16 Answers (1-4 to 1-6)
s = deck.slide(T)
qa(s, "Answers (1-4 to 1-6)",
   [("1-4", "The local politician. Few training documents mention the fact, so the right year stays\nunlikely and a wrong year can be drawn."),
    ("1-5", "Search by title, authors and year (or DOI), open the original, and find the supporting\nsentence. If it is not found or says something else, mark it \"unverified\" and do not use it.\nAsking the AI is not a check."),
    ("1-6", "0.30 × 1,200 = 360, not 390 (390 would be 32.5%). One more check: find the original\nsurvey. Re-asking is weaker, because agreement is not proof.")], size=18, gap=0.3)

NOTES = load_notes(HERE / "notes.md")
for i, sl in enumerate(deck.slides, 1):
    if i in NOTES:
        sl.notes(NOTES[i])
OUT.parent.mkdir(parents=True, exist_ok=True)
deck.save(OUT, title=T, author=AUTHOR)
