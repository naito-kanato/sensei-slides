# 完成後のレビュー（Lecture 1: What a Chat AI Computes）

- 判定: 直してから渡す
- 総評: 筋（2枚目で素朴な見方→7枚目で崩して問い→10枚目で答え→11・12枚目で手段）は青帯だけで通り、数値（Walters & Wilder・PersonQA・SimpleQA・Kandpal・Magesh）も設計メモと合う。前半と後半の書きぶり（ラベル＋字下げ・赤字1〜2か所・原稿の長さと呼びかけ）もそろっている（F2 問題なし）。英語に日本語の残りは無い。直すのは、原稿が図に無い棒を指す所、青帯の英語の読み違い、図のラベルの重なりの3点。
- plan_changes.md の3件（6・11・12枚目）は文字量・はみ出しの手当てで、外した内容は原稿に残っており、伝えたいことは弱くなっていない。

## 必ず直す点

1. [7] B2 図と文の食い違い：原稿の「And the second pair of bars shows that even among the real references, 43% and 24% had major errors...」— 図の棒は GPT-3.5（55%）と GPT-4（18%）の1組だけで、「2組目の棒」は無い。
   → 原稿をこう直す：「The same study also found that even among the real references, 43% from GPT-3.5 and 24% from GPT-4 had major errors, such as the wrong authors, year or pages. That part is not on the chart.」（設計メモ3節 データ2）

2. [4] 英語の読み違い（D5・C3）：青帯「Training set GPT-3's 175 billion numbers to predict text」は、"Training set"（学習データ）という名詞句として読まれ、文の動詞が見えない。
   → 青帯を「Training tunes GPT-3's 175 billion numbers to predict text」に（構成案2節の4行目の青帯も同じ文に）。

3. [10] B3 図の見え方：赤い点のラベル「≈25%」の「≈」が縦軸の線に重なっている（slide-10.png）。
   → ラベルを点の右下（点と「Rare facts」の箱の間の右側）へ移し、縦軸から離す。

## 直すとよい点

1. [7] A1・A4 定義の言い換え：本文「Hallucination: fluent text that is nonsensical or unfaithful to the source」— 出典（Ji et al. 2023, Sec. 2）の定義は "generated content that is nonsensical or unfaithful to the provided source content" で、"fluent" は無い。
   → 「generated text that is nonsensical or unfaithful to the source」に。

2. [7] A4・A5 出どころの無い言い切り：原稿「That is one study and one task, and newer models or tools with search do better.」— 設計メモ3節に裏づけの行が無く、11枚目（検索つきでも 17〜33%）とも響き方がずれる。
   → 「That is one study and one task. Newer models and tools with search may do better, but as slide 11 shows, not perfectly.」に。

3. [6→7] A3 理由の取り違え：6枚目の原稿の最後「So how often does this drawing go wrong? Let's look at the evidence.」は、作り話の原因が「引くこと（揺らぎ）」だと聞こえ、10枚目の答え（事実を確かめる仕組みが無い・学習データに少ない事実）とずれる。
   → 「But does what it draws match the facts? Let's look at the evidence.」に。

4. [10] D4 縮めて開いた穴・E2：本文「Step 2 checks nothing:」は、何の Step 2 かが本文から消えている（構成案は「Step 2 (the next-token probability, slide 2)」）。
   → 本文を「Step 2 (slide 2) checks nothing:」に。あわせて原稿「From here on, the first line is my own summary.」を「The first line on the slide is my own summary.」に、Rare facts の段落（"Now look at the graph..."）の頭に「First, rare facts.」を足す（後の "Second," "Third," と対にする）。

5. [10] A5 図の出どころ：図は Kandpal Fig. 1 から目で読んだ2点を直線で結んだもので、元の図の曲線ではない。出典の注「Data: Kandpal et al., ICML 2023, Fig. 1」だけだと、元のデータの線に見える。
   → 注を「Two points read from Kandpal et al., ICML 2023, Fig. 1 (approx.)」に。原稿にも「I read two points off their figure」を1文足す。

6. [8] B3：破線のラベル「o1 level」の末尾が o3 の棒の左端に接している（slide-08.png）。
   → ラベルを破線の右端（o4-mini の棒の右）へ移す。

7. [5] 英語の読み違い：本文 Tuning の「plain GPT-3 just continues text / tuned on human example replies and human rankings of its replies」は、"tuned on..." の主語が GPT-3 に読める（InstructGPT の名前は最後の ⇒ 行まで出ない）。
   → 2行目以降を「InstructGPT: tuned on human example replies and rankings」に（字数はほぼ同じ）。

8. [6] C3 強調：赤字は Low (0.5) の「84%」だけで、青帯（replies can vary）の要である「高い温度で間違いの Sydney が増える」が灰色。
   → 赤を「84%」から外し、High (2) の「Sydney 28%」を赤に（赤は1か所のまま）。

9. [3→4・4→5・11→12] E2 つなぎの二重：前の枚の最後の文と次の枚の1文目が同じ問いを2回言っている。
   - 3枚目末「Next, how does the model learn which token should come next?」＋4枚目頭「Next, where do those probabilities come from? The answer is training.」→ 4枚目頭を「The answer is training.」だけに。
   - 4枚目末「So what happens when you actually chat with a model like this?」＋5枚目頭「Next, after training, what actually happens when you chat with the model?」→ 5枚目頭の文を削り「Look at the picture on the right.」から始める。
   - 11枚目末「Another check is to re-ask, and we turn to that next.」＋12枚目頭「Another check is to re-ask: answers that disagree flag likely errors.」→ 12枚目頭を「Here is the key idea: answers that disagree flag likely errors.」に。

10. [1] D3 要点の抜け：構成案の表紙の要点「— Fluent is not the same as true」が表紙に無い（副題の場所は「AI Literacy (1 lecture)」）。
   → テンプレートで足せるなら、副題に「Fluent is not the same as true」を足す（講座名の行は残す）。足せないなら原稿1の1文目の後に「Our theme today: fluent is not the same as true.」を足す。

## 採否と直した点

- 必ず直す点1（7枚目 原稿の「2組目の棒」）：採る。原稿をレビューの文どおりに直した（43%・24% は図に無いと断る）。
- 必ず直す点2（4枚目 青帯）：採る。「Training tunes GPT-3's 175 billion numbers to predict text」に。memo.md の構成案の4行目と「青帯だけを上から読む」も同じ文に。
- 必ず直す点3（10枚目「≈25%」が縦軸に重なる）：採る。ただし置き場所は点の右下ではなく点の左上（右下は「Rare facts」の引き出し線と重なるため）。縦軸からも青い線からも離れたことを slide-10.png で確認。
- 直すとよい点1（7枚目 定義）：採る。「generated text that is nonsensical / or unfaithful to the source」に。memo.md の構成案の7行目も同じ文に。
- 直すとよい点2（7枚目 原稿の言い切り）：採る。レビューの文どおり。
- 直すとよい点3（6枚目 原稿の最後の文）：採る。「But does what it draws match the facts? ...」に。
- 直すとよい点4（10枚目 Step 2）：採る。本文を「Step 2 (slide 2) checks nothing:」に、原稿の断りの文を直し、Rare facts の段落の頭に「First, rare facts.」を足した。
- 直すとよい点5（10枚目 図の出どころ）：採る。注を「Two points read from Kandpal et al., ICML 2023, Fig. 1 (approx.)」に、原稿に「I read two points off a figure ... so the values are approximate.」を足した。
- 直すとよい点6（8枚目「o1 level」）：採る。破線を右へ延ばし、ラベルを o4-mini の棒の右に移した。
- 直すとよい点7（5枚目 Tuning）：採る。「InstructGPT: tuned on human / example replies and rankings」に。
- 直すとよい点8（6枚目 赤字）：採る。赤を「84%」から外し「Sydney 28%」に（赤は1か所のまま）。
- 直すとよい点9（つなぎの二重 3→4・4→5・11→12）：採る。4・5・12枚目の原稿の頭をレビューの文どおりに。
- 直すとよい点10（表紙の要点）：採る（原稿で）。表紙の副題の欄は講座名に使われているため、原稿1の「You only need ...」の前に「Our theme today: fluent is not the same as true.」を足した。
- make_deck 2回（ERROR 0・WARN 0）。残る △「5〜10枚目が左文右図」は前の版からのもので、今回の直しの範囲外として残した。原稿HTMLを作り直した。
- テンプレート2で組み直した：memo.md の1節に「- テンプレート：テンプレート2」を足し（README・memo 冒頭の指定どおり。前の版は1節に行が無く既定のテンプレート1で組まれていた）、make_deck で組み直した。テンプレートが変わってずれた所を直した：5・8枚目の結論の一文が右にはみ出したので削った（5「The whole chat is resent each turn; the reply continues it」、8「o3 made up answers to 33% of PersonQA questions (o1: 16%)」。memo.md の構成案と「青帯だけを上から読む」も同じ文に。8枚目の年は本文の「Apr 2025」に残る）、9枚目の展開の右と図の間隔が狭かったので矢印を細くし字を17ptに、11枚目の判定の結論の箱の幅を 1.45→1.38 in に。make_deck は上限のあと --over で2回（ERROR 0・WARN 0）。△「5〜10枚目が左文右図」は前の版から残る。原稿HTMLを作り直した。
