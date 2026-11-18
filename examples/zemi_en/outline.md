# 構成案（論文紹介）：Observation of Gravitational Waves from a Binary Black Hole Merger（表紙＋論文の表紙＋本文13枚＋想定質問2枚）

論文：B. P. Abbott et al. (LIGO Scientific Collaboration and Virgo Collaboration), "Observation of Gravitational Waves from a Binary Black Hole Merger",
Phys. Rev. Lett. **116**, 061102 (2016), DOI 10.1103/PhysRevLett.116.061102。CC BY 3.0（図を使うときは書誌と DOI を表示）。資料：`Gravitational_Waves/資料/その他/1602.03837.pdf`（arXiv 版、16頁。本文は p.1〜8）。

依頼文（request.txt）：Make slides for a paper review at my lab seminar from 1602.03837.pdf (the first observation of gravitational waves). The audience knows some physics but not this field.

テンプレート1（結論ヘッダー）なので、本文の最後に赤字の結論を繰り返す帰結の形は使わず、根拠を見せる形（ラベル・式の注釈・場合分け・展開・問い・手順）で組む。★＝赤字（根拠の要の数値・語）。
スライドに載る列（タイトル・●見出し・青帯・本文の要点）は英語。図の案の中身・ノートも英語で書く。

## オプション

| オプション | 今の値 |
|---|---|
| 軽さ | 念入り |
| 言語 | 英語 |
| 原稿のモード | 発表 |
| 発表時間 | 20分 |
| 聞き手 | 研究室のゼミ（学部の物理を習った人） |
| 聞き手の前提知識 | 知っている＝波と干渉・周波数・光速・一般相対論の名前・太陽質量・中性子星とブラックホールの名前・正規分布と σ／知らない＝重力波の検出の方法・ひずみ h・マイケルソン干渉計の腕の共振器とリサイクリング・ショット雑音・SN 比とマッチドフィルター・チャープ質量・シュヴァルツシルト半径の値の目安・時刻ずらしの背景・誤報率 |
| 聞き手のテーマへの詳しさ | 多少知っている |
| 丁寧さ | 1 |
| 範囲 | 主要な結果に絞る（II〜VI 節。VI 節の天体物理の含意・合体の頻度・背景放射はノートか省略） |
| 答えの位置 | 後 |
| ねらい | 論文を紹介する（方法から） |
| テンプレート | テンプレート1（結論ヘッダー） |
| 構成案の確認 | 任せる |
| 発表者名 | なし |

## 話の筋

問いは3枚目で立て（スライドにも赤字で1行）、壁（6枚目：2本の腕の長さの差は陽子の約400分の1）を光と振り子で越え（7・8枚目）、信号を見て（9〜12枚目）、疑い（13枚目：雑音の偶然の一致）を時刻ずらしで晴らして、14枚目で答える。

| 筋 | 型 | 一文 | 枚 |
|---|---|---|---|
| 状況 | — | Gravitational waves were predicted in 1916 and shown only indirectly, by the energy loss of the binary pulsar PSR B1913+16 | 2 |
| 複雑化 | 壁 | A wave of strain 10⁻²¹ changes the arm-length difference of 4 km arms by only ~4×10⁻¹⁸ m, about 1/400 of a proton | 6 |
| 問い | どうやって | How can a stretch this tiny be caught on Earth, and told apart from noise? | 3 |
| 答え | — | The two LIGO detectors recorded the same chirp 6.9 ms apart, and noise alone would mimic it less than once in 203,000 years (5.1σ) | 14 |
| 対立 | — | Is the signal both detectors saw a gravitational wave, or a chance coincidence of noise? | 12 |
| それで | — | Time-shifted comparisons put chance noise at less than once in 203,000 years, so the noise explanation is ruled out: the wave was caught directly | 14 |
| 語り手 | — | The LIGO team: they read a stretch smaller than a proton with 100 kW of light and four-stage pendulums, then cleared the doubt of chance noise with 608,000 years of time-shifted background | — |

話の型：論文紹介（方法から）

拍の割り当て：だから（手段：方法・装置）＝5、しかし（壁：越えるべき難しさ）＝6、そして（次へ：結果）＝9、しかし（疑い：別の説明・偶然では）＝13、だから（帰結：確かめた結果）＝14。拍のあいだの肉付け：7・8（壁の越え方）、10〜12（波形から波源へ）、15（波源の考察）。

## 3b. データ（data.py merge が data_N.md から入れる。図の案から「データN」で指す。値・単位・注記はこのとおりに描く。驚きの事実は、使うなら3節の事実の行に写す）

### データ1：Black hole masses before and after the merger
- 驚き：合体後のブラックホール（62 M⊙）は、合体前の2つ（36＋29 M⊙）の和より軽い。差は重力波として出たエネルギー（論文の推定 3.0 ± 0.5 M⊙c²）
- 問いの候補：消えた質量はどこへ行ったのか？
- 単位：太陽質量 M⊙（波源の系）
- 分母：—
- 時点：GW150914（2015年9月14日 09:50:45 UTC の観測）
- 出典：Table I（Abbott et al., Phys. Rev. Lett. 116, 061102, 2016）
- 確認：○
- 別の読み方：どの値も中央値で、90% の範囲は ±4〜5 M⊙。引き算の差 3 は範囲と同じくらいなので、放出エネルギーは引き算ではなく論文の推定値 3.0 ± 0.5 M⊙c²〔VI〕で言う。検出器の系では (1+z) = 1.09 倍
| 区分 | 値 |
|---|---|
| Primary (before) | 36 |
| Secondary (before) | 29 |
| Final black hole | 62 |

## 構成

| 番号 | 範囲（論文） | タイトル | ●見出し | 前の枚から | 青帯（結論） | 図で見せるもの | 本文の要点 | ノートへ | 本文の形 | 役割 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | — | — | — | — | — | — | Paper Review: The First Observation of Gravitational Waves | — | — | 表紙 |
| 2 | I. Introduction | Background | Gravitational waves | — | Einstein's 1916 waves stretch and squeeze space itself at light speed | 仕組み：模式図：a ring of test particles stretched horizontally and squeezed vertically by a passing wave, reversed each half-cycle (schematic; wide strip below the two labels) | Einstein's prediction, 1916：from the field equations of general relativity, a transverse strain wave at light speed, from a changing mass quadrupole〔I. Introduction〕 / Size：amplitude ★remarkably small, as Einstein himself knew; physical reality debated until 1957〔I. Introduction〕 | "Quadrupole moment" said first as "how the mass is distributed"; the ring sketch is not from the paper; "never seen directly" is left to slide 3 | ラベル | 本文 |
| 3 | I. Introduction | Background | Indirect evidence | そして（詳しく） | Binary pulsar energy loss showed GWs only indirectly | 仕組み：模式図：PSR B1913+16 orbit slowly shrinking (old orbit dashed, schematic, no numbers) | Binary pulsar PSR B1913+16：found by Hulse and Taylor (1975)〔I. Introduction・ref. 20〕; energy loss measured by Taylor and Weisberg (1982)〔I. Introduction・ref. 21〕 ⇒ GWs exist, but ★only indirectly / Next goal：direct amplitude and phase ⇒ tests of GR in strong fields〔I. Introduction〕 ⇒ ★how can a stretch this tiny be caught, and told apart from noise?〔I. Introduction・V. Searches〕 | Pulsar = neutron star with regular radio pulses; the question line is shown in red on the slide; "this tiny" picks up "remarkably small" from slide 2 | ラベル | 本文 |
| 4 | 論文の表紙 | — | — | — | — | — | Observation of Gravitational Waves / from a Binary Black Hole Merger / B. P. Abbott et al. (LIGO Scientific and Virgo Collaborations) / Phys. Rev. Lett. 116, 061102 (2016), CC BY 3.0, DOI 10.1103/PhysRevLett.116.061102 | Published 11 Feb 2016; over 1000 authors | — | 表紙 |
| 5 | III. Detectors, Fig. 3 | Detector | Advanced LIGO | だから（手段） | 4 km arms convert ΔL = hL into a light phase shift | 仕組み：模式図：Michelson interferometer with two 4 km arms, laser, beam splitter, mirrors labeled "free-hanging test mass" and photodetector (drawn after Fig. 3, not to scale) | Michelson interferometer：two perpendicular 4 km arms, a wave stretches one and ★shrinks the other, ΔL ⇒ phase shift of the returning light〔III. Detectors・Fig. 3〕 / ΔL(t) = δLx − δLy = h(t)L〔III. Detectors〕 (h = strain, the fractional stretch ΔL⁄L, no unit; L = arm length, 4 km)〔III. Detectors〕 | Phase difference at the beam splitter → photodetector signal proportional to h; test masses: free-hanging mirrors, only markers (labeled in the figure), the wave does not push the mirrors, it changes the distance between them | ラベル | 本文 |
| 6 | I. Introduction, III. Detectors | Detector | How small the signal is | しかし（壁） | h ≈ 10⁻²¹ changes the arm-length difference by only ~4×10⁻¹⁸ m | 仕組み：模式図：log-scale length ruler: 4 km arm, proton width 1.7×10⁻¹⁵ m, ΔL 4×10⁻¹⁸ m, 1/400 marked in red (wide, below the text) | Strain h ≈ 1.0×10⁻²¹ (peak value later measured), L = 4 km〔要旨・III. Detectors〕 → ΔL = hL ≈ 4×10⁻¹⁸ m ≈ ★1/400 of a proton (proton ≈ 1.7×10⁻¹⁵ m, presenter's estimate)〔発表者の概算・CODATA 2018〕 / Earlier：resonant bars since the 1960s〔I. Introduction〕; initial interferometers 2002–2011 ⇒ upper limits only〔I. Introduction〕 | 10⁻²¹ is the peak strain later measured; it is used here as the target size. Proton size is outside the paper | 展開・ラベル | 本文 |
| 7 | III. Detectors, Fig. 3 | Detector | Boosting the light | だから（手段） | Cavities build 20 W of laser light up to 100 kW in each arm | 仕組み：模式図：light path drawn after Fig. 3(a): laser 20 W → power recycling → 700 W at the beam splitter → 100 kW in each 4 km arm cavity, line width by power (figure first: large on the left, reading on the right) | Arm cavities：light bounces between two test-mass mirrors ⇒ phase effect ★×300〔III. Detectors〕 / Power recycling：light sent back in at the input (partially transmissive mirror), 20 W input → 700 W at the beam splitter → ★100 kW in each arm ⇒ less relative shot noise〔III. Detectors〕 | Purpose: more photons ⇒ smaller relative shot noise (photon-count fluctuation) ⇒ smaller ΔL readable; ※ relative fluctuation ∝ 1/√N for N photons (outside the paper); signal recycling broadens the arm-cavity bandwidth; 1064 nm Nd:YAG laser; homodyne readout | ラベル | 本文 |
| 8 | III. Detectors, Fig. 3(b) | Detector | Where the noise is lowest | そして（並べる） | Most sensitive at 100–300 Hz, 3–5× better than initial LIGO | 実物：資料の図：Fig. 3(b), instrument noise spectra of H1 and L1 (strain noise vs frequency); annotation added: shaded band for the signal 35–250 Hz (named in the caption) | Reading：strain noise vs frequency, lower = quieter〔Fig. 3〕 / Above 150 Hz：photon shot noise (slide 7)〔Fig. 3〕 / Low frequencies：ground motion ⇒ quadruple pendulum + active platform, cut by ★>10 orders of magnitude above 10 Hz〔III. Detectors〕 / Intermediate：thermal noise ⇒ 40 kg fused-silica mirrors on silica fibers〔III. Detectors〕 | ※ each pendulum stage filters out ground motion above its resonance (outside the paper); ultrahigh vacuum below 1 μPa; spikes = calibration lines, 60 Hz mains, fiber modes | 場合分け・ラベル | 本文 |
| 9 | II. Observation, Fig. 1 top row | Result 1 | Same signal at two sites | そして（次へ） | H1 and L1 saw the same waveform 6.9 ms apart | 実物：資料の図：Fig. 1 top row, H1 and L1 strain, with the strain axis label and the time axis taken from the same figure (full width below the text) | L1 first (14 Sep 2015)〔Fig. 1〕 → H1 ★6.9 ms later, within the 10 ms light travel time〔II. Observation・Fig. 1〕 / Size：peak strain 1.0×10⁻²¹, combined SNR (signal-to-noise ratio) 24〔要旨・II. Observation〕 | Two sites: local noise is not shared, so the same shape points to a common source〔III. Detectors〕; H1 shifted by 6.9 ms and inverted (detectors face differently) → overlaps L1 (named in the caption)〔Fig. 1〕; 09:50:45 UTC; found by a low-latency search within 3 minutes; Virgo was being upgraded | 展開・ラベル | 本文 |
| 10 | II. Observation, Fig. 1 bottom row | Result 1 | A rising chirp | そして（詳しく） | In 0.2 s the frequency rose from 35 to 150 Hz | 実物：資料の図：Fig. 1 bottom row, time–frequency map of H1 with the color bar; label "color: signal power" added in the figure (figure first: large on the left, reading on the right) | Track：from ★35 to 150 Hz in about 8 cycles over 0.2 s, amplitude peaking at 150 Hz, whole signal spans 35 to 250 Hz, same track in L1〔II. Observation・要旨・Fig. 1〕 / Meaning：most plausible, two orbiting masses spiraling in, energy lost to GWs (GW frequency = 2 × orbital, shrinking orbit ⇒ faster)〔II. Observation〕 | Called a "chirp" because it sounds like a bird's chirp when played as audio; losing energy to GWs shrinks the orbit, so the orbit speeds up | ラベル | 本文 |
| 11 | II. Observation, Fig. 1 bottom row | Result 2 | Chirp mass | だから（帰結） | Chirp rate implies a total mass of at least 70 M⊙ | 実物：資料の図：Fig. 1 bottom row, H1 panel (as slide 10), with the point f and the slope ḟ marked in white | Chirp mass ℳ：one combination of m₁, m₂, set by f and its rate of change ḟ (the track's slope), alone controls the chirp at low frequency〔II. Observation〕 / From Fig. 1：ℳ ≈ 30 M⊙ (detector frame = masses as observed), total smallest at m₁ = m₂ ⇒ ★total ≳ 70 M⊙〔II. Observation〕 | The general formula ℳ = (m₁m₂)^(3⁄5) ⁄ (m₁+m₂)^(1⁄5) = (c³⁄G)[(5⁄96) π^(−8⁄3) f^(−11⁄3) ḟ]^(3⁄5) is said in the notes, not shown (the fractions were unreadable at slide size); ※ fixing ℳ, the total M is smallest at m₁ = m₂: M = 4^(3⁄5)ℳ ≈ 2.3ℳ ≈ 70 (presenter's note); detector frame ×(1+z); NR waveform and model-free reconstruction overlap 94% (Fig. 1, 2nd row); Fig. 2: speed above 0.5c near merger | ラベル | 本文 |
| 12 | II. Observation | Result 2 | Why black holes | だから（問い） | Of known objects, only black holes are heavy and compact enough to orbit at 75 Hz | 仕組み：模式図：scale drawing of two equal masses ≃350 km apart, with summed Schwarzschild radii ≳210 km and arcs for the orbit at 75 Hz (schematic, to scale) | Orbit at 75 Hz：half of the 150 Hz GW peak, equal point masses would be only ≃350 km apart, summed Schwarzschild radii (horizon size, ≈3 km per M⊙) ≳210 km〔II. Observation〕 / Other candidates：two neutron stars ⇒ ★not enough mass, neutron star + black hole ⇒ total mass too large, would merge at a ★much lower frequency〔II. Observation〕 | Schwarzschild radius R_S = 2GM/c²; 70 M⊙ orbiting 350 km apart without touching ⇒ each body is close to its Schwarzschild size; ※ neutron stars are at most about 2–3 M⊙ (outside the paper), so two cannot reach 70 M⊙; ringdown fits a black hole settling to a Kerr state | ラベル | 本文 |
| 13 | V. Searches | Result 3 | Ruling out chance noise | しかし（疑い） | Chance coincidences? Time shifts built 608,000 years of noise-only background | 仕組み：模式図：time shift: H1 and L1 noise traces, L1 slid by an offset much larger than 10 ms, coincidences counted (schematic) | Problem：noise is non-Gaussian and nonstationary ⇒ cannot compute from σ, count from data; no detector can be shielded from GWs〔V. Searches〕 / 1. Shift one detector's data by ≫10 ms 2. Search for coincidences again (real signals no longer line up) 3. Each shift = a new noise-only 16 days, ~10⁷ shifts ⇒ ★608,000 years of background〔V. Searches〕 | Bias: a real signal can enter the background ⇒ overestimate, conservative〔V. Searches〕; 16 days: 12 Sep – 20 Oct 2015; numbers are for the binary coalescence search; environmental sensors found no disturbance correlated between the two sites (Sec. IV) | ラベル・手順 | 本文 |
| 14 | V. Searches, Fig. 4 right | Result 3 | False alarm rate | だから（帰結） | Noise would mimic it less than once per 203,000 years | 実物：資料の図：Fig. 4 right, binary coalescence search histogram (GW150914 circled in red by the presenter) | GW150914：ρ̂c = 23.6, ★above every background event, false alarm rate < 1 per 203,000 years (an upper bound: none louder) ⇒ probability < 2×10⁻⁷ = ★5.1σ (Gaussian-equivalent)〔V. Searches〕 / Generic search (no waveform model)：< 1 per 22,500 years, 4.6σ〔V. Searches〕 | Reading: x = ρ̂c, the combined SNR of both sites, down-weighted for glitch-like data (cf. SNR 24, slide 9), black = background, orange = candidates, top scale = σ (axis labels and legend in the figure)〔Fig. 4・V. Searches〕; 5.1σ only converts the counted probability to a Gaussian tail, the noise is not Gaussian (Q3); χ² weighting details; close by rereading the slide-3 question: same chirp at two sites (slide 9) + time-shifted background ⇒ not chance noise | ラベル | 本文 |
| 15 | VI. Source discussion, Table I | Discussion | The source | だから（帰結） | A 36 and 29 M⊙ pair merged, radiating 3.0 M⊙c² | 並び：カード：three parallel cards with a large value each: Masses 62 M⊙ (36 and 29 merged, source frame; データ1), Energy 3.0 M⊙c² (± 0.5), Distance 410 Mpc (z = 0.09); medians from Table I | Masses：36 and 29 M⊙ merged into ★62 M⊙ (source frame, ×(1+z) = 1.09 ⇒ ≈ 71 in the detector frame), from GR waveform fits〔Table I・VI. Source discussion〕 / Energy：3.0 ± 0.5 M⊙c² radiated, peak 3.6×10⁵⁶ erg s⁻¹〔VI. Source discussion〕 / Distance：410 (+160, −180) Mpc (z = 0.09)〔Table I〕 | GR tests: 3 checks, no deviation〔VI. Source discussion〕; one of them: graviton Compton wavelength > 10¹³ km, i.e. graviton mass < 1.2×10⁻²² eV/c²; 90% intervals ±4–5 M⊙; first direct GW detection and first binary black hole merger; at design sensitivity the SNR would be 3× higher; Virgo, KAGRA, LIGO-India next〔VII. Outlook〕 | 箇条 | 本文 |
| 16 | — | Q&A | Anticipated questions | — | — | 実物：資料の図：for Q1, Fig. 1 top row, right panel, with the strain axis and the time axis of the same figure | — | — | — | 想定質問 |
| 17 | — | Q&A | Anticipated questions | — | — | 実物：資料の図：for Q3, Fig. 4 right with all axes (as slide 14, GW150914 circled in red) | — | — | — | 想定質問 |

## 想定質問

| 番号 | 型 | 質問 | 回答の要点 | 戻る枚 |
|---|---|---|---|---|
| Q1 | 疑い | Could an earthquake or a local disturbance have caused it? | Environmental sensors saw nothing evolving like GW150914; fluctuations could explain at most 6% of its strain; no correlated disturbances between the two sites〔IV. Detector validation〕 | 9 |
| Q2 | なぜ | Why is the H1 trace inverted before it is overlaid on L1? | The two detectors have different orientations, so the same wave appears with opposite sign〔Fig. 1・Fig. 3(a)〕 | 9 |
| Q3 | 数値の意味 | What does 5.1σ mean here? | A false alarm probability < 2×10⁻⁷, expressed as the tail of a Gaussian beyond 5.1σ; the noise itself is not Gaussian, so the probability comes from time-shifted background〔V. Searches〕 | 14 |
| Q4 | 限界 | Where in the sky was the source? | With only two detectors, mainly from the arrival-time difference: about 600 deg² (90%); Virgo, KAGRA and LIGO-India will narrow it〔II. Observation・VII. Outlook〕 | 15 |

## 青帯だけを順に読む（括弧は前の枚から）

Einstein's 1916 waves stretch and squeeze space itself at light speed →（そして（詳しく））Binary pulsar energy loss showed GWs only indirectly →（論文の表紙）
→（だから（手段））4 km arms convert ΔL = hL into a light phase shift →（しかし（壁））h ≈ 10⁻²¹ changes the arm-length difference by only ~4×10⁻¹⁸ m
→（だから（手段））Cavities build 20 W of laser light up to 100 kW in each arm →（そして（並べる））Most sensitive at 100–300 Hz, 3–5× better than initial LIGO
→（そして（次へ））H1 and L1 saw the same waveform 6.9 ms apart →（そして（詳しく））In 0.2 s the frequency rose from 35 to 150 Hz
→（だから（帰結））Chirp rate implies a total mass of at least 70 M⊙ →（だから（問い））Of known objects, only black holes are heavy and compact enough to orbit at 75 Hz
→（しかし（疑い））Chance coincidences? Time shifts built 608,000 years of noise-only background →（だから（帰結））Noise would mimic it less than once per 203,000 years
→（だから（帰結））A 36 and 29 M⊙ pair merged, radiating 3.0 M⊙c²

## 迷った所

- 問い（3枚目）を壁（6枚目）より前に置いた。背景の終わりで問いを立て、装置を見せてから「どれだけ小さいか」を壁として出す順。6枚目を3枚目の直後に出す案（壁→装置）もありうる
- 6枚目の陽子の大きさ（直径 ≈ 1.7×10⁻¹⁵ m）は資料外（CODATA 2018 の陽子の荷電半径 0.84 fm から）。ΔL ≈ 4×10⁻¹⁸ m と「陽子の約1/400」は発表者の概算。原稿では ※（資料外の補足）にする
- 6枚目の h ≈ 10⁻²¹ は、あとで測られたピークの値（要旨）を「ねらう大きさ」として先に使っている。結果の先取りに見えるなら「~10⁻²¹」と丸めたままにする
- データは1組（Table I の質量）だけ。誤報率の3つの値（203,000・22,500・8,400 年）も比べられるが、検索の方式・クラスが違い、203,000 は上限なので、14枚目は Fig. 4 右をそのまま見せ、値は本文に置いた
- 15枚目の放出エネルギーは引き算（36＋29−62）ではなく論文の推定値 3.0 ± 0.5 M⊙c² を使う（データ1の別の読み方）
- 本文の要点の区切りは構成案の書き方どおり全角の「：」で書いた。スライドに載るときは英語の「: 」に直す（日本語でないデッキの決まり）
- 要点の中の「/」は区切りと読まれるので、式は分数の斜線「⁄」（U+2044）、単位は erg s⁻¹ と書いた。組むときに s.peq で普通の分数に直す
- 11枚目の「speed above 0.5c near merger」は Fig. 2 下段の読み取り（本文に数値なし）
- （直し）14枚目の答えの回収（2か所の同じチャープ＋時刻ずらし ⇒ 偶然ではない）は、本文の5行目にせずノートの締め（問いの読み返し）にした。本文に1行足すなら Generic search の行をノートへ回す
- （直し）15枚目の重力子のコンプトン波長はノートへ回した（推論距離で深・文字量）。11枚目の Fig. 2 はスライドから外し、v/c > 0.5 と 94% の重なりはノートへ
- （直し）15枚目の図は積み上げ棒（前＝36＋29、後＝62）。描画の部品が積み上げに対応しないなら、3本並びに戻し差の注記だけ残す

## 引っかかりへの手当て

- [5] h＝長さの相対変化 → 5枚目の式の注釈に「h = strain, the fractional stretch ΔL⁄L, no unit; L = 4 km」（h と L の行を式の注釈にまとめた）
- [5] 鏡を押すという像のずれ → 5枚目の図の鏡に「free-hanging test mass」、本文に Test masses の行（鏡は目印、間の空間が伸びる）、ノートに1文
- [6] 10⁻²¹ が後で測った値 → 6枚目の本文に「(peak value later measured)」。青帯も「腕の長さの差」に直した
- [7] ショット雑音で光を強くする理由 → 7枚目の Purpose を「more photons ⇒ smaller relative shot noise (photon-count fluctuation) ⇒ smaller ΔL readable」、1/√N はノートの ※（資料外）
- [7] パワーリサイクリング → 7枚目の本文に括弧で「a mirror sends returning light back in」
- [7] シグナルリサイクリングの帯域 → 採らない（深・聞き手は多少知っている）。行ごとノートへ移した
- [8] 雑音スペクトルの縦軸の読み方 → 8枚目の本文1行目「Reading：…lower = quieter」と図の注記。信号の帯域 35–250 Hz を谷に網掛けして10枚目へつなぐ
- [8] 振り子は揺れを濾す → 8枚目のノートに ※（資料外）で1文
- [9] 2か所の局所雑音は共有されない → 5枚目の Two sites の行を9枚目へ移し「local noise is not shared between sites, so the same shape points to a common source」
- [9] combined SNR と ρ̂c の関係 → 14枚目の Reading に「ρ̂c, the combined SNR of both sites, down-weighted for glitch-like data (cf. SNR 24, slide 9)」
- [10] 周波数の上昇＝軌道の縮み → 10枚目の Meaning に「(GW frequency = 2 × orbital; shrinking orbit ⇒ faster)」、エネルギーを失うと縮む理屈はノート
- [11] チャープ質量の意味 → 11枚目の本文1行目に「the m₁, m₂ combination fixed by f and its rate of change ḟ」
- [11] ℳ ≃ 30 → 合計 ≳ 70 → 11枚目の本文に「(smallest when m₁ = m₂)」、M = 4^(3⁄5)ℳ ≈ 2.3ℳ はノートの ※
- [11] detector frame → 11枚目の本文に「detector frame = masses as seen, ×(1+z)」
- [12] シュヴァルツシルト半径の目安 → 12枚目の本文に「(horizon size, ≈3 km per M⊙)」
- [12] 350 km と 210 km の比べ → 12枚目の図に「bodies must fit inside 350 km」、ノートに「触れずに回る＝各天体がシュヴァルツシルト半径に近い」
- [12] 中性子星の質量の上限 → 12枚目のノートに ※（資料外）で1文。青帯も「heavy and compact enough」に直した
- [12] NS+BH が低い周波数で合体する理由 → 採らない（深）。本文の行はそのまま
- [13] 非正規の雑音では σ から計算できない → 13枚目の Problem に「⇒ cannot compute from σ, count from data」
- [13] 608,000 年の作り方 → 13枚目の手順3に「Each shift = a new noise-only 16 days」
- [14] 誤報率の定義 → 14枚目の本文に「False alarm rate (how often noise alone is this loud)」、上限であることはノート
- [14] 5.1σ の像のずれ → 14枚目の本文に「(Gaussian-equivalent)」、Q3 の答えをノートに前出し
- [15] 70 と 36＋29 の系の違い → 15枚目の Masses に「(source frame; ×(1+z) = 1.09 ⇒ ≈ 71 in the detector frame)」
- [15] 個々の質量の出どころ → 15枚目の Masses に「from GR waveform fits」
- [15] 重力子のコンプトン波長 → 採らない（深）。行をノートへ移した
