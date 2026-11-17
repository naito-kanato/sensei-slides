# 完成後のレビュー（Gravitational_Waves・発表・英語）

- 判定: 直してから渡す
- 総評: 筋（3枚目の問い → 6枚目の壁 → 13枚目の疑い → 14枚目の答え）は青帯だけでつながり、数値はほぼ論文どおり。英語も自然で、日本語の残りは無い。
  ただ、資料より強く言っている所が2か所（9・12枚目）、図の読み方の抜けが1か所（14枚目の紫の線）、切り抜きの残りが1か所（10枚目）ある。
  前半（2〜8）と後半（9〜15）の書きぶり（ラベル＋字下げの形・赤字1〜3か所・原稿の長さと話し方）はそろっている（F2 は単位の表記1点だけ）。

## 必ず直す点

1. [9] A4 言い過ぎ・D5：本文「local noise never at both sites」と赤字「⇒ same shape = common source」は、論文の「widely separated detectors to *distinguish* gravitational waves from local instrumental and environmental noise」〔III. Detectors, p.3〕より強い。「never」と書くと、13枚目の「Chance?（雑音が偶然そろったのでは）」と食い違う（偶然の一致は否定できていない段階）。
   → 本文を「local noise: not shared between sites」、赤字を「⇒ same shape points to a common source」に（原稿はすでに "points to a common source" なので、スライドを原稿に合わせる）。
2. [12] A4 言い過ぎ・A6：青帯「Only black holes are heavy and compact enough to orbit at 75 Hz」は、論文の「the only **known** objects compact enough to reach an orbital frequency of 75 Hz without contact」〔II. Observation, p.2〕から「known」が落ちた（構成案の青帯 "Of known objects, …" からも縮んだ）。
   → 青帯を「Of known objects, only black holes are compact enough to orbit at 75 Hz」に。原稿の「That leaves black holes.」も「That leaves black holes as the only known objects compact enough.」に。
3. [14] A1 数値の写し違い（原稿）：「The generic search … also finds it, at 1 in 22,500 years, or 4.6 sigma.」の 1 in 22,500 は上限（論文「its false alarm rate is **lower than** 1 in 22 500 years」〔V. Searches, p.5〕）。
   → 「… also finds it, at less than 1 in 22,500 years, or 4.6 sigma.」
4. [14] B1 図にしか無い前提：図の紫の線（Background excluding GW150914）と、黒の背景が 13〜22 まで右へ伸びている理由が、本文にも原稿にも無い。13枚目の「real signal may enter background ⇒ conservative」が、ここで目に見える所なのに使われていない。
   → 原稿の Look at the histogram … の段に1文足す：「The purple line is the background with GW150914 removed. The long black tail to the right is GW150914 itself leaking into the background, the conservative bias from the last slide.」
5. [10] B3 図の見え方：Fig. 1 の切り抜きに、隣のパネルの残り（x 目盛り「0.45」の右の欠けた「5」と、カラーバーの左の細い青い縦線）が出ている。
   → figs.py の切り抜き範囲を右端で数 px 詰めて、欠けた目盛りと青い縦線を外す（11枚目も同じ図なので、カラーバー無しの切り方で問題ないか合わせて確かめる）。
6. [6]・[15]（[12]も） A5 出どころの印：原稿で「presenter's own calculation／my own rough estimates」と断った数値に、スライドの行では印が無い。構成案の6枚目には「(presenter's estimate)」があったが縮めて消えた（D4）。
   → 6枚目「⇒ ΔL ≈ 1/400 of a proton」を「⇒ ΔL ≈ 1/400 of a proton (my estimate)」、15枚目「(36 + 29) × 1.09 ≈ 71, detector frame」を「(36 + 29) × 1.09 ≈ 71, detector frame (my estimate)」に。12枚目の「(≈3 km per M⊙)」も原稿で presenter's own calculation と断っているので「(≈3 km per M⊙, my estimate)」に（幅が足りなければ12枚目は原稿だけでよい）。

## 直すとよい点

1. [7] B3：Fig. 3(a) の中の文字（Test Mass・Power Recycling・20 W・100 kW Circulating Power など）が 6pt 前後で、投影すると読めない。原稿は「Follow the light from the 20 W laser to the 100 kW in the arms」と図を追わせている。
   → 図を中央（レーザー〜ビームスプリッタ〜x 腕）に切り詰めて大きくする。それが難しければ、原稿を「the numbers are small, so follow the body text: 20 W, 700 W, 100 kW」と本文に目を向ける言い方に。
2. [9] B1・B3：Fig. 1 上段が下に小さく置かれ、凡例（H1 observed / L1 observed / H1 observed (shifted, inverted)）が読めない。縦軸の名前も切れていて、原稿でも縦軸が strain（単位 10⁻²¹）と言っていない。
   → 本文と図の間の空き（約0.4 in 余る）を使って図を縦に大きくする。原稿の「The left panel is the strain at Hanford」の後に「The vertical axis is strain in units of 10 to the minus 21. In the right panel, blue is L1 and orange is the shifted, inverted H1.」を足す。
3. [8] B1：原稿で H1・L1 の2本と言うが、どちらが赤でどちらが青か言っていない。
   → 「The two curves are H1 at Hanford, in red, and L1 at Livingston, in blue.」
4. [12] B2 図と文の食い違い：原稿「The two dots are equal masses … The circles around them show how big their horizons would be」とあるが、図には点は無く、塗りつぶした円（Horizon）が2つだけ。上の矢印（Sum of radii ≳210 km）にも触れていない。
   → 「The two filled circles are the horizons of two equal masses. The red arrow between their centers is about 350 kilometers, and the arrow on top is the sum of their radii, at least 210 kilometers.」
5. [6] D1 手当ての抜け：手当て「10⁻²¹ が後で測った値 → 本文に (peak value later measured)」が本文から消え、「peak h ≈ 10⁻²¹」だけになっている（原稿にはある）。まだ観測の前の枚なので、聞き手は「何のピーク？」となる。
   → 「peak h ≈ 10⁻²¹ (GW150914)」。
6. [11] D4・E3：「detector frame: ×(1+z)」は何に何を掛けるのか本文から読めず、z（赤方偏移）が出てくるのは15枚目。
   → 本文を「detector frame (masses as observed)」にし、原稿の該当文を「… Table I says to multiply source-frame masses by one plus z, where z is the redshift, to convert.」に。
7. [13]・[14] F2 書き手のぶれ（表記）：13枚目と青帯は「years」、14枚目の本文は「203,000 yr」。14枚目の「(Gaussian equiv)」も省略が目立つ。
   → 14枚目を「noise this loud: < 1 per 203,000 years」「p < 2×10⁻⁷ = 5.1σ (Gaussian-equivalent)」に（幅が足りなければ前者だけ）。
8. [15] B2：原稿は「Each mass is a median with a 90% range of about plus or minus 4 to 5」と言うが、図の誤差棒は合体後の 62 にだけある。
   → 合体前の 36・29 にも誤差棒（+5/−4、±4）を付けるか、原稿に「The error bar on the right bar shows the 90% range of the final mass; the two masses before have similar ranges.」と足す。

## 確かめたこと（指摘なし）

- plan_changes.md の4件（8枚目の図の注記を本文へ、10・11枚目を H1 の1枚に、Sweep をノートへ）は、どれも伝えたいことが弱くなっていない。L1 も同じ形であること・35–250 Hz は原稿で言えている。
- 主要な数値（6.9 ms・SNR 24・35→150 Hz／0.2 s／8 cycles・ℳ≃30・≳70・≃350 km・≳210 km・608,000 years・~10⁷・ρ̂c=23.6・1 in 203,000・2×10⁻⁷・5.1σ・36/29/62・3.0±0.5・3.6×10⁵⁶・410 Mpc・z=0.09・6%・600 deg²・3× SNR）は論文と一致。8枚目の low = seismic・intermediate = thermal も論文〔III, p.3〕どおり。
- 原稿に TODO・ノートへ・コメントの残りは無い（pptx のノートでも確認）。日本語の残りも無い。

## 採否と直した点

### 必ず直す点（全部採用）

1. [9] 採用。本文「local noise: not shared between sites」、赤字「⇒ same shape points to a common source」。行が長くなったので右の塊を x=7.8→6.5 に。outline.md の9枚目の本文の欄と手当ての行も同じ言い方に直した。
2. [12] 採用。青帯「Of known objects, only black holes are compact enough to orbit at 75 Hz」（構成案の青帯どおり）。原稿「That leaves black holes as the only known objects compact enough.」。
3. [14] 採用。原稿「at less than 1 in 22,500 years」。outline.md の14枚目も「< 1 per 22,500 years」に。
4. [14] 採用。原稿の図の段に紫の線と右へ伸びる黒の尾（GW150914 自身が背景に入る＝前の枚の保守的な偏り）の2文を足した。
5. [10] 採用。s10.png の H1 の地図とカラーバーの間に重複して貼られていた右端の帯（欠けた「5」と青い縦線）を白で消した（列 1415–1459 px）。dpi の情報を保ち直し、図の大きさは元どおり。11枚目はカラーバー無しの別の切り抜きで、問題なし。
6. [6]・[15]・[12] 採用。6枚目「⇒ ΔL ≈ 1/400 of a proton (my estimate)」。15枚目は幅と下の余白が足りず「detector frame ≈ 71 (my estimate)」に縮めた（65 × 1.09 の計算は原稿にある）。12枚目は「Schwarzschild radii: sum ≳210 km」「(≈3 km per M⊙, my estimate)」の2行に。

### 直すとよい点

1. [7] 一部採用。図の切り詰めはせず、原稿を「The labels in the figure are small, so follow the numbers in the text on the left: 20 W, then 700 W, then 100 kW.」に。
2. [9] 採用。図の下との間を gap=0.1 にし、s09.png の dpi を 300 にして図を約 1.2 倍に（凡例が少し読みやすく）。原稿に縦軸（strain, 10⁻²¹ 単位）と右の枠の色（青 L1・橙 H1 shifted, inverted）の2文を足した。
3. [8] 採用。原稿「H1 at Hanford, in red, and L1 at Livingston, in blue」。
4. [12] 採用。原稿の図の説明を、塗りつぶした円＝地平線・赤い矢印＝中心間 約350 km・上の矢印＝半径の和 ≳210 km に直した。
5. [6] 採用。展開の左を「peak h ≈ 10⁻²¹ / (GW150914) / L = 4 km」の3行に（1行にすると右の式が図に重なったため）。文字量の目安に収めるため「resonant bars since the 1960s」→「resonant bars (1960s–)」。
6. [11] 採用。本文「detector frame (masses as observed)」、原稿「… by one plus z, where z is the redshift, to convert.」。
7. [14] 前者だけ採用（「203,000 years」）。「(Gaussian-equivalent)」は図との間隔が 0.4 in を切ったので「(Gaussian equiv)」のまま。
8. [15] 原稿で採用（「The error bar on the right bar shows the 90% range of the final mass; the two masses before have similar ranges.」）。図は変えていない。

### 結果

- make_deck 2回目で ERROR 0・WARN 0・✘ 0。残る △ は「10〜15枚目が左文右図で続く」（直す前からの型の並び。型を組み替えると直しの回数を超えるので残した）。
- 原稿HTMLを作り直した。
