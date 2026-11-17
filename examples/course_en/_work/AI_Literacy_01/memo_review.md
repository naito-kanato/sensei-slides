# 設計メモのレビュー：第1回 What a Chat AI Computes

- 判定: 直してから進める
- 総評: 事実と数値は出典どおりで、データ3組の使い方もよい。ただし筋の「問い」（何を計算しているか）が2枚目の青帯ですぐ答えられてしまい、7枚目の意外から出る問いになっていない。10枚目の答えも青帯が「少ない事実ほど誤る」だけで問いに答えていない。
  5枚目の青帯がゴール1の「チャット＝1つの文書」を出しておらず、11枚目の青帯は手段の枚なのに7〜9枚目と同じ「作り話が多い」の繰り返しになっている。
  6枚目は例の確率から計算した値と本文の言い方が合っていない。英語の青帯は「何の何%か」が曖昧なものがある（8・9・11枚目）。

## 必ず直す点

1. [2・7・10・1節の筋] 問い「What is a chat AI actually computing when it answers you?」は、同じ2枚目の青帯「It scores every possible next token, then picks one」ですぐ答えられている。「答えの位置：後」と合わず、型の しかし（意外）（7枚目の55%）から出てくる問いにもなっていない → 問いを語り手の疑問の形にする。例：2枚目の本文に素朴な見方「It sounds like it looked the answer up. Did it?」を載せ（予想を立てさせる）、7枚目の意外のあとに問い「If it reads so fluently, why does it make things up so confidently?」をスライドに載せる。1節の表の問いの枚を7、一文を差し替える（根拠：1節の語り手の行、story.md 2節）
2. [10] 答えの枚の青帯「Facts rare in its training text are answered worst」は答えの一部で、筋の表の答え（no step checks facts → fluent errors are built in）も9枚目の当てずっぽう（採点）も回収していない → 青帯を「Nothing checks facts, so rare facts come out fluent but wrong」などにし、rare facts・cutoff・scoring を本文の3つの理由として並べる（根拠：事実1・11・12・13、1節の答えの行）
3. [5] 青帯「A tuned 1.3B model beat 175B GPT-3 in human ratings」は●見出し「A chat is one document」とも、ゴール1の「the chat itself is one document it keeps continuing」とも違うことを言っている。次の6枚目への しかし（限り）も、この青帯からはつながらない → 青帯を「The whole chat is resent each turn, and the reply is its likely continuation」にし、1.3B vs 175B は本文の Tuning の行に残す（根拠：事実5・事実6、1節のゴール1）
4. [6] 例の確率（0.62／0.25／0.08／0.05）から計算すると、温度0.5で Canberra 84%・Sydney 14%、温度2で Canberra 44%・Sydney 28%・Melbourne 16%・other 12%。「the top token almost every time」は84%に対して言い過ぎで、「Sydney is drawn more often」は25%→28%しか動かず、増えるのは主に Melbourne と other。さらに「always-the-top text turns dull」は Holtzman の greedy（常に1位を取る）の話で、温度0.5の話ではない → 本文を計算した数で書く（Low (0.5)：Canberra 84%／High (2)：Canberra 44%, Sydney 28%, Melbourne 16%）。dull の行は「Always taking the top token makes text dull, so chat AIs draw instead」と greedy の話として分ける。図の注に「other」を1つの候補として計算したことを書く（根拠：事実7・事実16）
5. [11] 青帯「Even search-based legal AIs made things up 17–33%」は、7〜9枚目と同じ「作り話が多い」という教訓の4つ目で、手段の枚（だから（手段））の結論になっていない。ゴール3と確認問題1-5が確かめる手順が青帯に出ない → 青帯を「Open the source and find the sentence yourself」などの手順にし、17–33% は本文に「Why: even search-based tools…」として移す（根拠：事実14、6節 1-5）
6. [6節 1-6 の解答] 「30% of 1,200 is 360, not 390, so the AI's number is wrong」は言い過ぎ。2つの数が食い違っていることまでしか言えず、390人のほうが正しくて30%が誤り（390/1,200＝32.5%）かもしれない → 「360, not 390: the two numbers do not match (390 would be 32.5%), so at least one is wrong」とし、要素も「the numbers do not match」にする。もう1つの確かめ方は「find the original survey」を先に書く（新しいチャットで聞き直しても、数が一致しただけでは正しいとは言えないと12枚目で教えているため）

## 直すとよい点

1. [4] 青帯「GPT-3 set 175 billion numbers to predict text」は、英語として主語が不自然（数を決めたのは学習）→「Training set GPT-3's 175 billion numbers to predict text」など。10枚目の答えに要る「覚えたのは文の続き方で、事実の一覧ではない」がノートにしかないので、本文の1行にする（根拠：事実1）
2. [4] 「about 300 billion tokens of web pages, books and Wikipedia」は、裏取りの差分（事実2）どおり「学習で読んだトークン数」と分かる言い方に →「It read about 300 billion tokens drawn from web pages, books and Wikipedia」（根拠：facts_diff 事実2、Brown et al. 2020 Table 2.1 の注）
3. [3] トークンの分け方の図が「説明のための例」で、例文「The capital of Australia is」はふつう語ごとに1トークンになり、「a piece of a word」の例にならない → 実際のトークナイザーで分けた結果を使い、語の途中で切れる語（長い語や珍しい語）を1つ入れる。推測の図を避ける（根拠：事実3）
4. [7] 青帯の「GPT-3.5」は聞き手の知らない名前で、同じ枚の Mata v. Avianca は「ChatGPT」と呼ぶ →「GPT-3.5 (the 2023 free ChatGPT)」と1句添える。Hallucination の定義「not true to the facts or the source」は、Ji et al. の定義（nonsensical or unfaithful to the provided source content）より広い → 「出典の定義を広げた言い方」と原稿で断るか、Ji の言い方に寄せる。1枚の量も3項目とも長いので、Mata の行を短くする（根拠：事実9・データ2）
5. [8] 青帯「o3 made up 33% on PersonQA」は何の33%かが読めない →「o3 made up answers to 33% of PersonQA questions, vs 16% for o1 (2025)」（根拠：データ3）
6. [9] 青帯「was 75% wrong」は「1つの答えが75%間違い」とも読める →「o4-mini rarely said "I don't know" (1%) and got 75% wrong」。22 と 24 で正解がほぼ同じなのに間違いが3倍、の読みを「⇒」の1行で本文に（根拠：データ1）
7. [10] 図が「shape only, no numbers」の概略グラフ。事実11 に BLOOM-176B・TriviaQA の値（関連文書 約10件→約1万件で 約25%→55%超）があるので、この2点を目盛りつきで描く（根拠：事実11・事実19、Kandpal Figure 1）
8. [10] 「GPT-4 knew little after September 2021」は初代 GPT-4 の値で、今のモデルは締め切りが後 →「Every model has a cutoff; for GPT-4 (2023) it was September 2021」と、一般の話に年つきの例として添える（根拠：事実12）
9. [10・11] 出典の付け方：10枚目の「Step 2 checks nothing」に〔事実1・事実9〕、11枚目の手順に〔事実14〕〔事実10〕を付けているが、どの出典も「事実を確かめる段が無い」「この手順で確かめよ」とは書いていない → 講師の推論・おすすめの手順として出典の印を外すか、原稿で「ここからは講師のまとめ」と断る
10. [6] チャットのアプリでは利用者は温度を変えられない（提供側が決めている）ことを原稿で一言。温度は「確率を尖らせる・ならす目盛り」と本文に定義を1句（推論距離の [6] を参照）
11. [README] 4節の色の決め事（Canberra＝青、Sydney＝赤）と例文の使い回しを、README の「記号・図の向き・色」に足す

## 資料にあるのに構成案から抜けている内容

- 事実2 の内訳（Common Crawl・WebText2・Books・Wikipedia の比）：本文に要らない。4枚目の原稿の ※ で足りる
- データ2 の「実在の文献のうち大きな誤りあり（GPT-3.5 43%・GPT-4 24%）」：7枚目のどこにも割り当たっていない。「実在しても著者・年に誤り」は11枚目の「Does it say this claim?」の根拠になるので、7枚目の原稿か11枚目の本文に1句

## 第2回以降に回す点

- なし（全1回）

## 推論距離

[2] 「Predicting the next token ⇒ Score every token in its vocabulary」｜用語｜語・あと｜補う前提：token＝語か語の一部（定義は3枚目）｜使う所：2・3・ゴール1｜架け方：本文の1句に括弧で「(a word or a piece of one; next slide)」と予告する
[2] 「Score every token ⇒ Pick one」｜用語｜あと・像｜補う前提：像：「pick」を最も確率の高いものを選ぶと思い浮かべる → 実際は確率の重みでくじを引く（6枚目）｜使う所：2・6・確認問題1-2｜架け方：手順3を「Draw one, weighted by its probability (slide 6)」にする
[2] 「scores（2枚目）⇒ odds（10枚目）⇒ probability（ゴール1・図）」｜用語｜あと｜補う前提：呼び名の揺れ：scores＝odds＝probability（同じものを3つの名前で呼ぶ）｜使う所：6・10・ゴール1｜架け方：全枚で「probability」にそろえる（青帯の scores も）
[3] 「Token ⇒ Length limit: 2,048 for GPT-3」｜範囲｜深｜補う前提：長さの上限は、入力と返事を合わせた1回に読める量（5枚目の context の上限）｜使う所：なし｜架け方：原稿の1文で「5枚目の context の上限」と添える
[4] 「Nudge the numbers ⇒ 175 billion numbers to predict text」｜範囲｜あと・像｜補う前提：像：「learning」から事実を覚え込む像を思い浮かべる → 実際は次のトークンを当てやすくなるよう数を少しずつ動かすだけで、事実の一覧は持たない｜使う所：10・ゴール2｜架け方：本文に「It learns how text continues, not a list of facts」の1行（ノートから上げる）
[5] 「175 billion numbers（4枚目）⇒ A tuned 1.3B model beat 175B GPT-3」｜論拠｜筋｜補う前提：なぜ4枚目の次に調整の話が来るか（文の続きを当てるだけのモデルは、質問に答える形で続けるとは限らない）｜使う所：5｜架け方：本文の Tuning の行の頭に「Plain GPT-3 just continues text;」と1句
[5] 「human rankings (RLHF) ⇒ 1.3B preferred」｜用語｜語｜補う前提：RLHF＝人が返事に付けた順位を使って、好まれる返事が出やすいよう数を直す調整｜使う所：5｜架け方：略語を外して「human rankings of its replies」だけにする
[6] 「Each token is a weighted draw ⇒ Low (0.5)／High (2)」｜用語｜筋・語・あと｜補う前提：temperature＝引く前に確率を尖らせる（低い）・ならす（高い）目盛り。0.5・2 はその値｜使う所：6・確認問題1-2の解答｜架け方：本文に「Temperature: a dial applied before the draw」の1行を足す
[6] 「probability ⇒ weighted draw」｜用語｜筋｜補う前提：weighted draw＝100枚のくじのうち62枚が Canberra、25枚が Sydney のようなくじ引き｜使う所：6・12｜架け方：図の注記に「like a lottery: 62 of 100 tickets say Canberra」
[6] 「Low／High temperature ⇒ replies can vary」｜範囲｜深｜補う前提：チャットのアプリでは利用者は温度を変えられず、提供側が決めた値で引いている｜使う所：なし｜架け方：原稿の1文
[7] 「It gave authors and a journal, so it looked them up? ⇒ Made up 55%」｜論拠｜あと｜補う前提：遠い（5枚前・ノートだけ）：素朴な見方「調べて答えている」は2枚目のノートでしか立っておらず、ここで崩す予想がスライドに無い｜使う所：7・話の筋（状況→意外）｜架け方：2枚目の本文に素朴な見方の1行を載せる（必ず直す点1）
[7] 「GPT-3.5 ⇒ Mata v. Avianca: ChatGPT」｜用語｜あと｜補う前提：呼び名の揺れ：GPT-3.5＝2023年の無料の ChatGPT の中身｜使う所：7｜架け方：青帯か本文に括弧で一言
[8] 「o3 made up 33% on PersonQA」｜用語｜筋・語｜補う前提：PersonQA＝実在の人物についての事実を尋ねる OpenAI の試験｜使う所：8｜架け方：本文の1句に括弧で「(questions about real people)」
[9] 「Abstains 52% → wrong 26%／Abstains 1% → wrong 75%」｜用語｜筋・語｜補う前提：SimpleQA＝答えが短い事実の問いの試験。abstain＝「分からない」と答えて答えないこと｜使う所：9・10｜架け方：本文に括弧で添え、abstain を「says "I don't know"」に言い換える
[9] 「right 22% vs 24%・wrong 26% vs 75% ⇒ guessing beats "I don't know"」｜論拠｜筋｜補う前提：正解はほぼ同じなのに間違いが3倍＝当てずっぽうで答えても正解はほとんど増えず、作り話だけが増える｜使う所：9・10｜架け方：本文の最後に「⇒ guessing adds few right answers but many wrong ones」の1行
[10] 「Step 2 checks nothing」｜論拠｜あと｜補う前提：遠い（8枚前）：Step 2＝2枚目の手順2「Score every token」｜使う所：10｜架け方：「Step 2 (scoring the next token, slide 2)」と思い出させる一言
[10] 「few training documents ⇒ low accuracy」｜論拠｜筋｜補う前提：見た例が少ない事実は、正しい続きの確率が高くならず、もっともらしい別の続きが引かれる｜使う所：10・確認問題1-4｜架け方：ノートの答えの1文を本文の「Rare facts」の行に「⇒」で載せる
[10] 「After the cutoff: GPT-4 knew little after September 2021」｜用語｜語｜補う前提：knowledge cutoff＝学習に使った文書の集め終わりの日。それより後の出来事は学習データに無い｜使う所：10｜架け方：本文の1句に括弧で「(the date its training text ends)」
[10] 「Scoring: tests rate a guess above "I don't know"」｜用語｜あと｜補う前提：呼び名の揺れ：2枚目の「score」は次のトークンの確率、10枚目の「score」は試験の採点で、別のもの｜使う所：10｜架け方：2枚目を probability にそろえ、10枚目は「test scores」とする
[11] 「Even search-based legal AIs made things up」｜用語｜筋｜補う前提：search-based＝答える前に資料を検索し、見つけた文書をもとに書く AI。それでも書く段は次のトークンの予測｜使う所：11｜架け方：本文の1句「(they search a database first, then write)」
[11] 「Open it yourself (title, authors, DOI)」｜用語｜語｜補う前提：DOI＝論文ごとに付く識別番号。検索すると原文に行ける｜使う所：11・確認問題1-5の解答｜架け方：括弧で「(DOI: the paper's ID)」
[12] 「Re-ask ⇒ disagreement is a warning sign」｜論拠｜筋｜補う前提：遠い（6枚前）：知っている事実は確率が高く毎回同じものが引かれ、作り話は引くたびに変わりやすい（6枚目のくじ引き）｜使う所：12・確認問題1-2｜架け方：本文に「a known fact wins most draws; a guess changes (slide 6)」の1句
[12] 「same question ⇒ in a new chat」｜論拠｜あと｜補う前提：遠い（7枚前）：同じチャットで聞き直すと前の答えも文書に入って送られるので（5枚目）、その続きを書いてしまう。だから新しいチャットで｜使う所：12・確認問題1-2・1-6｜架け方：Re-ask の行に「(a new chat does not resend the old answer)」
