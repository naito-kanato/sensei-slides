# 構成案：Observation of Gravitational Waves from a Binary Black Hole Merger

## オプション

| 項目 | 値 |
|---|---|
| 発表の種類 | 論文紹介（水曜ゼミ） |
| 資料 | B. P. Abbott et al., PRL 116, 061102 (2016)（CC BY 3.0。図は出典つきで切り出す） |
| 言語 | 英語（スライド・原稿とも） |
| 発表時間 | 20分 |
| 発表者名 | なし（表紙に名前を出さない） |
| 範囲 | II〜VI節（天体物理的な意味・合体率・背景重力波はノートか省略） |
| 順 | 論文の順（方法から始めて、結論を最後に回収） |
| ねらい | 論文を紹介する（方法から） |
| 答えの位置 | 後 |
| テンプレート | テンプレート1 |
| 聞き手のテーマへの詳しさ | 多少知っている（学部の物理まで。重力波の検出の小分野は知らない） |
| 前提知識 | 知っている＝波と干渉・周波数・光速・一般相対論の名前・太陽質量・中性子星とブラックホールの名前・正規分布とσ／知らない＝重力波の検出のしかた・ひずみ h・マイケルソン干渉計の腕の共振器とリサイクリング・ショットノイズ・SNR とマッチドフィルタ・チャープ質量・シュワルツシルト半径の大きさの感覚・タイムスライドの背景・誤警報率 |
| 丁寧さ | 1枚に許すあと 1つまで |
| 構成案の確認 | 任せる |
| 原稿のモード | 発表（ゼミの聞き手全体に話す） |

- 道筋：Background（何が足りなかったか）→ Detector（10⁻²¹ のひずみをどう読むか）→ Observation（何が見えたか）→ Significance（雑音の偶然ではないか）→ Source（何が出したか）

## 話の筋

| 筋 | 型 | 一文 | 枚 |
|---|---|---|---|
| 状況 | — | Gravitational waves were predicted in 1916, and a binary pulsar showed their effect only indirectly | 2 |
| 複雑化 | 壁 | But a strain of 10⁻²¹ moves a 4-km mirror by only about 4×10⁻¹⁸ m, and every detector shakes with its own noise | 3 |
| 問い | どうやって | How can such a tiny stretch be caught, and shown not to be a chance coincidence of noise? | 3 |
| 対立 | — | Is the matching wiggle in the two detectors a gravitational wave, or noise bursts that lined up by chance? | 10 |
| それで | — | Noise alone fakes it less than once per 203,000 years, so the chance-coincidence explanation falls away: a first direct detection | 12 |
| 答え | — | Seen at two sites beyond chance: two black holes | 13 |
| 語り手 | — | The LIGO team: building an instrument for a 10⁻²¹ strain, then proving the first event is not noise | — |

話の型：論文紹介（方法から）

## 3b. データ（data.py merge が data_N.md から入れる。図の案から「データN」で指す。値・単位・注記はこのとおりに描く。驚きの事実は、使うなら3節の事実の行に写す）

### データ1：How rarely noise alone fakes GW150914, by search
- 驚き：A single 0.2-s event in 16 days of data is judged against tens of thousands to hundreds of thousands of years of noise, and noise still never reaches it in the matched-filter search
- 問いの候補：Could a chance coincidence of noise in two detectors make GW150914?
- 単位：years per one false alarm (inverse false alarm rate; for the binary search an upper bound)
- 分母：—
- 時点：16 days of coincident data, 12 Sep – 20 Oct 2015
- 出典：Abbott et al., PRL 116, 061102 (2016), V-A, V-B, Fig. 4
- 確認：○
- 別の読み方：The binary search value is only a bound set by the length of the background (608,000 years); the model-free search, with fewer assumptions, gives a smaller number
| 区分 | 値 |
|---|---|
| Binary coalescence search (matched filter) | 203000 |
| Generic transient search, class C3 | 22500 |
| Generic transient search, classes C2+C3 | 8400 |

### データ2：Masses before and after the merger (source frame)
- 驚き：The final black hole is lighter than the two it came from: about 3 solar masses are missing, carried away as gravitational waves
- 問いの候補：Where did 3 solar masses go?
- 単位：M☉ (source frame, median of the 90% credible interval)
- 分母：—
- 時点：GW150914, 14 Sep 2015
- 出典：Abbott et al., PRL 116, 061102 (2016), Table I, VI
- 確認：○
- 別の読み方：Each mass has an uncertainty of about ±4 M☉, larger than the 3 M☉ gap; the radiated energy (3.0 ± 0.5 M☉c²) is estimated separately from fits to numerical simulations
| 区分 | 値 |
|---|---|
| Primary black hole | 36 |
| Secondary black hole | 29 |
| Sum of the two | 65 |
| Final black hole | 62 |
| Radiated as gravitational waves | 3.0 |

## 構成

| 番号 | 範囲 | タイトル | ●見出し | 前の枚から | 青帯（結論） | 図で見せるもの | 本文の要点 | 本文の形 | ノートへ | 役割 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | — | — | — | — | — | — | — | — | — | 表紙 |
| 2 | I | Background | A century of waiting | — | Predicted in 1916, gravitational waves were seen only indirectly until 2015 | 時期：年表：1916 Einstein predicts gravitational waves〔I〕／1957 Chapel Hill conference ends the debate on their reality〔I〕／1960s Weber's resonant bars〔I〕／1975 Hulse–Taylor binary pulsar〔I〕／2002–2011 initial interferometers observe jointly〔I〕／2015 Advanced LIGO starts〔I〕（主役は 2015 だけ赤） | Prediction：strain waves at light speed〔I〕 / Indirect proof：binary pulsar loses energy〔I〕 / Direct search：bars, then interferometers〔I〕 | ラベル | — | 本文 |
| 3 | I, III | Background | How small is the signal? | しかし（壁） | A strain of 10⁻²¹ moves a 4-km arm by only about 4×10⁻¹⁸ m | 印象：大きな数字：4×10⁻¹⁸ m（arm change at h = 1.0×10⁻²¹, L = 4 km） | Strain h = ΔL/L：1.0×10⁻²¹ at peak〔III〕〔要旨〕 / ★Question：catch it, prove not noise? | ラベル | — | 本文 |
| 4 | III, Fig. 3 | Detector | Michelson interferometer | だから（手段） | A Michelson interferometer turns the arm difference ΔL = hL into a light signal | 仕組み：模式図：Fig. 3 main diagram redrawn（laser at left, beam splitter at centre, 4-km arms to the right and up, photodetector at bottom）（読み方：one arm stretches while the other shrinks） | ΔL = δLx − δLy = hL〔III〕 / h：strain projected onto the detector〔III〕 / ΔL：shifts the phase of the two returning beams〔III〕 | 式の注釈 | — | 本文 |
| 5 | III | Detector | Cavities and recycling | そして（詳しく） | Arm cavities multiply the phase shift 300-fold, with 100 kW stored per arm | 流れ：流れ図：Laser 20 W → Power-recycling mirror → 700 W on the beam splitter → 100 kW in each arm cavity | Arm cavity：phase effect ×300 over a plain arm〔III〕 / Power recycling：sends light back, 20 W → 700 W〔III〕 | ラベル | — | 本文 |
| 6 | III, IV, Fig. 3(b) | Detector | Noise remains | しかし（壁） | One detector alone cannot tell a wave from its own bursts of noise | 仕組み：資料の図：Fig. 3(b) strain noise vs frequency（H1 red, L1 blue; lowest near 100–300 Hz; sharp lines are calibration and power-grid lines）（読み方：lower curve = quieter detector） | Above 150 Hz：photon shot noise〔Fig. 3〕 / Below 150 Hz：thermal and ground noise〔III〕 / Any band：non-Gaussian noise bursts〔IV〕 | 場合分け | — | 本文 |
| 7 | III, V, Fig. 3(a) | Detector | Two distant sites | だから（手段） | A real wave must reach Hanford and Livingston within 10 ms | 実物：資料の図：Fig. 3(a) map（H1 at upper left in red, L1 at lower right in blue, dashed line "10 ms light travel time"） | Local noise? ⇒ seen at one site only〔III〕 / Real wave? ⇒ both sites within 10 ms〔Fig. 3〕〔V〕 | 問い | — | 本文 |
| 8 | II, Fig. 1 | Observation | GW150914 | そして（次へ） | On 14 Sep 2015 both detectors recorded the same signal 6.9 ms apart | 実物：資料の図：Fig. 1 top row, right panel（L1 strain in blue with H1 shifted by 6.9 ms and inverted in orange on top） | When：14 Sep 2015, 09:50:45 UTC〔II〕 / Timing：L1 first, H1 6.9 ms later〔Fig. 1〕 / Size：peak h 1.0×10⁻²¹, combined SNR 24〔要旨〕〔II〕 | ラベル | — | 本文 |
| 9 | II, Fig. 1, Fig. 2 | Observation | A rising chirp | そして（詳しく） | In 0.2 s the signal rose from 35 to 150 Hz in about 8 cycles | 実物：資料の図：Fig. 1 bottom row, left panel（H1 time–frequency map; a bright track rising to the right near 0.40–0.43 s） | 35 Hz〔II〕 → 150 Hz, loudest〔II〕 / Chirp：frequency and amplitude rise together〔II〕 / GR fit：residuals look like noise〔Fig. 1〕 | 展開・ラベル | — | 本文 |
| 10 | IV, V | Significance | Is it just noise? | しかし（疑い） | Noise bursts in two detectors can also line up by chance within 10 ms | 違い：比較：Gravitational wave（same shape at both sites、within 10 ms、frequency rising）と Chance coincidence（independent at each site、random timing、many shapes） | Environmental disturbance? ⇒ under 6% of the strain〔IV〕 / Glitch shared by both sites? ⇒ none found〔IV〕 | 問い | — | 本文 |
| 11 | V, V-B | Significance | Time-slide background | だから（手段） | Shifting one detector's data in time gave 608,000 years of noise-only pairs | 仕組み：模式図：two time lines H1 (red) above and L1 (blue) below; L1 slid sideways by an offset much larger than 10 ms; pairs that still coincide are counted as noise（読み方：each shift is one fake experiment with no real wave in common） | 1. Shift one site's time stamps ≫ 10 ms 2. Count coincidences again 3. Repeat ~10⁷ times〔V-B〕 / Conservative：a real wave can enter the background〔V〕 | 手順・ラベル | — | 本文 |
| 12 | V-A, V-B, Fig. 4 | Significance | Above all background | だから（帰結） | No background event reached GW150914: under 1 false alarm per 203,000 years | 実物：資料の図：Fig. 4 right（binary coalescence search; black background line falls off below ρ̂c ≈ 21, orange square marked GW150914 alone at 23.6 on the right） | Matched filter：data vs ~250,000 GR waveforms〔V-B〕 / Can noise reach 23.6? ⇒ ★< 1 per 203,000 yr, > 5.1σ〔V-B〕 / Model-free search：4.6σ, 1 per 22,500 yr〔V-A〕 | ラベル・問い | — | 本文 |
| 13 | II | Source | What can orbit at 75 Hz? | だから（問い） | A chirp mass of 30 M☉ at a 75-Hz orbit leaves only black holes | 判定：判定の流れ図：Two neutron stars?→ はい：ruled out, too light／いいえ：Black hole + neutron star?→ はい：ruled out, would merge at lower frequency／いいえ：Two black holes | Chirp mass ≈ 30 M☉〔II〕 → total ≳ 70 M☉〔II〕 / Size：Schwarzschild radii sum ≳ 210 km〔II〕 / 75-Hz orbit：only ≈ 350 km apart〔II〕 | 展開・ラベル | — | 本文 |
| 14 | VI, Table I | Source | Masses of the pair | そして（詳しく） | Black holes of 36 and 29 M☉ became 62 M☉, radiating 3 M☉ as waves | 比べる：棒グラフ：データ2（上から Primary 36、Secondary 29、Sum 65、Final 62、Radiated 3.0。Radiated だけ青） | Before → after：36 + 29 → 62 M☉〔Table I〕 / ★Radiated：3.0 M☉c² as waves〔VI〕 / Source：410 Mpc away, spin 0.67〔Table I〕 | ラベル | — | 本文 |
| 15 | II, VI, VII | Source | What is not yet known | しかし（限り） | Matches GR in strong gravity, but two detectors place it only within 600 deg² | 観点：表：Check×Result（Remnant mass and spin, early vs late＝consistent／Inspiral phase coefficients＝no deviation from GR／Graviton mass＝< 1.2×10⁻²² eV/c²／Sky position, 90% region＝about 600 deg²） | Does GR hold in strong gravity? ⇒ three tests, no deviation〔VI〕 / Where is the source? ⇒ only within ~600 deg²〔II〕 | 問い | — | 本文 |
| 16 | VIII | Summary | Caught, and not noise | だから（帰結） | Two distant interferometers caught a black-hole merger far beyond chance | 流れ：流れ図：Cavities read h ≈ 10⁻²¹ → Same chirp at two sites 6.9 ms apart → Noise fakes it < 1 per 203,000 years → Only two black holes fit | How? ⇒ ★amplify, coincide, count noise〔講師のまとめ〕 / What? ⇒ ★first black-hole merger〔VIII〕 | 問い | — | まとめ |
| 17 | — | — | — | — | — | — | — | — | — | 想定質問 |
| 18 | — | — | — | — | — | — | — | — | — | 想定質問 |

## 引っかかりへの手当て

- [2] Weber's resonant bars の中身 → 2の原稿に「large metal bars meant to ring when a wave passes」
- [2] 連星パルサーで何が見えたか → 2の原稿に「a neutron star whose radio pulses act as a clock」と「its orbit slowly shrinks」（13で思い出させる）
- [2] LIGO の略語 → 2の原稿に「the upgraded Laser Interferometer Gravitational-Wave Observatory」
- [3] 10⁻²¹ がまだ出ていない事象の値 → 3の原稿に予告「for the event we will see on slide eight」
- [3] arm が何の腕か → 3の原稿に「mirrors at the ends of two arms」と予告「the next slide shows how」
- [3] 像：strain＝力で材料が伸びる → 3の原稿に「Nothing pushes or pulls on the arm」「the mirrors hang freely」
- [4] projected の意味 → 4の原稿に「the part of the wave's stretching that lies along the arms」
- [5] 光を増やすとなぜ良いか → 5の原稿に「the signal grows in proportion to the light」と、6への予告「This randomness is the shot noise on the next slide」
- [5] Signal recycling が帯域を広げる理由は事実の置き場に無く、答えにつながらない細部 → 本文の要点と原稿から外した
- [6] H1/L1＝Hanford/Livingston → 6の原稿に「LIGO has two detectors, H1 at Hanford and L1 at Livingston」
- [6] 非ガウスがなぜ困るか → 6の原稿に「we could compute the chance of a fake; here we cannot」、10の原稿で「this rate must be measured from the data, not computed from sigma」と思い出させて11の time slide へつなぐ
- [6] calibration lines → 6の原稿に「signals injected on purpose to calibrate」
- [8] GW150914 の名前 → 8の原稿に「GW for gravitational wave, followed by the date」
- [9] GR fit が何の波形で、何が言えるか → 9の原稿に「for two compact objects orbiting and merging」と「one predicted shape explains the whole signal」
- [12] false alarm の意味 → 12の原稿に「A false alarm is a noise-only event with a score this high or higher」
- [12] 横軸の点数と8の SNR 24 → 12の原稿に「this search's version of the signal-to-noise ratio of slide eight」
- [12] 5.1σ への換算 → 12の原稿に「a normal-distribution tail beyond five point one sigma」
- [12] 608,000 年の背景から上限が 203,000 年になる理由 → 12の原稿に「the paper divides by this trials factor of three: six hundred eight thousand over three is about two hundred three thousand」（論文 V：試行の割り引き＝探した区分の数、V-B：区分は3つ、上限は3区分を通して 1/203,000 年）
- [13] 周波数の上がり方がなぜ質量を決めるか → 13の原稿に「the pair loses energy to the waves, so it spirals inward and orbits faster」
- [13] chirp mass と総質量 70 以上 → 13の原稿に「at most about 0.44 times the total mass」
- [13] detector frame と z → 13の原稿に「read directly from the wave as it arrives」、14の原稿に「where z is the source's redshift」
- [13] BH＋NS がなぜ低い周波数で合体するか → 13の原稿に「the star would reach it at a wider, slower orbit」
- [13] 350 km と 210 km の比べ → 13の原稿に「less than twice the two hundred ten kilometres」
- [14] spin 0.67・410 Mpc → 14の原稿に「the fastest spin a black hole can have」「roughly 1.3 billion light-years」
- [15] inspiral・phase coefficients → 15の原稿に「the stage when the two orbit inward before merging」
- [15] 重力子の質量の上限がなぜ付くか → 15の原稿に「the chirp would arrive distorted」
- [15] 2台でなぜ 600 deg² か → 15の原稿に「anywhere on a ring across the sky」

## 想定質問

| 番号 | 型 | 質問 | 回答の要点 | 戻る枚 |
|---|---|---|---|---|
| Q1 | 疑い | Could a disturbance common to both sites, not noise at each site, fake the signal? | Sensors found no such disturbance; environment explains under 6% of the strain | 10 |
| Q2 | 数値の意味 | Why are there two significances, 5.1σ and 4.6σ? | Matched filter uses GR waveforms (5.1σ); the model-free search assumes less (4.6σ) | 12 |
| Q3 | なぜ | Why is the time-slide background conservative? | A real wave in one detector can pair with shifted noise and enter the background | 11 |
| Q4 | 今後 | How will the sky position improve? | Advanced Virgo, KAGRA and a LIGO detector in India will extend the network | 15 |

## 迷った所

- 12枚目の 1/203,000 年は、背景 608,000 年を3区分の試行の割り引き（trials factor 3）で割った値（論文 V・V-B。608,000÷3≈202,700 を論文は 203,000 と書く）。原稿に1文で入れた

- 16枚目（まとめ）の入りの見込みの △ は、英語の文字幅の見積もりで出ている見込み。答えの行と要点は縮めたが、残れば制作の段で流れ図の箱を短くする

- 原稿の字数の △（目安 429字）は日本語の 300字/分 の目安で、英語の文字数には合わない。英語は 1枚 約130〜150語（700〜850文字、約1分）にそろえ、本文15枚で約20分になるようにしたので、このままにした

- 論文の順は II Observation → III Detectors だが、依頼の「方法から始める」に合わせ、Detector（III）を Observation（II）より先に置いた
- 3枚目の「4×10⁻¹⁸ m」は h = 1.0×10⁻²¹ と L = 4 km を掛けた発表者の概算（論文に ΔL の値そのものは無い）
- 13枚目のチャープ質量 30 M☉・総質量 70 M☉ は検出器系の値、14枚目の 36・29・62 M☉ は源の系の値（(1+z) 倍の違い）。原稿で一言断る
