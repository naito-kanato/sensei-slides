# 構成案（論文紹介）：Observation of Gravitational Waves from a Binary Black Hole Merger（表紙＋論文の表紙＋本文14枚＋想定質問2枚）

論文：B. P. Abbott et al. (LIGO Scientific Collaboration and Virgo Collaboration), "Observation of Gravitational Waves from a Binary Black Hole Merger", Phys. Rev. Lett. **116**, 061102 (2016), DOI 10.1103/PhysRevLett.116.061102。CC BY 3.0（図を切り出すときは書誌と DOI を出典に）。資料：作業ディレクトリの `Abbott2016_PRL116_061102.pdf`（16頁、本文は p.1〜8）。

テンプレート1（結論ヘッダー）なので、本文の最後に赤字の結論を繰り返す帰結の形は使わず、根拠を見せる形（ラベル・式の注釈・場合分け・展開・問い・手順）で組む。★＝赤字（根拠の要の数値・語）。
スライドに載る列（タイトル・●見出し・青帯・本文の要点）と図の中身・ノートは英語。

## オプション

| オプション | 今の値 |
|---|---|
| 軽さ | 標準 |
| 言語 | 英語 |
| 原稿のモード | 発表 |
| 発表時間 | 20分 |
| 聞き手 | 研究室のゼミ（学部の物理を習った人） |
| 聞き手の前提知識 | 知っている＝波と干渉・周波数・光速・一般相対論の名前・太陽質量・中性子星とブラックホールの名前・正規分布と σ／知らない＝重力波の検出の方法・ひずみ h・マイケルソン干渉計の腕の共振器とリサイクリング・ショット雑音・SN 比とマッチドフィルター・チャープ質量・シュヴァルツシルト半径の値の目安・時刻ずらしの背景・誤報率 |
| 聞き手のテーマへの詳しさ | 初学者・多少知っている |
| 丁寧さ | 1 |
| 範囲 | 主要な結果に絞る（II〜VI 節。VI 節の天体物理の含意・合体率・背景重力波はノートか省略） |
| 答えの位置 | 後（論文の順に方法から入り、結論を最後に回収） |
| ねらい | 論文を紹介する（方法から） |
| テンプレート | テンプレート1（結論ヘッダー） |
| 構成案の確認 | 任せる |
| 発表者名 | なし |

## 話の筋

入口は2枚目の予想（「4 km の物差しはどれだけ伸びるか」）。5枚目で答え（4×10⁻¹⁸ m）が予想と食い違い、問いを立てる（スライドに赤字で1行）。光と振り子で越え（6・7枚目）、信号を見て正体を詰め（8〜11枚目）、疑い（12枚目：雑音の偶然）を時刻ずらしで晴らし（13枚目）、14枚目で答える。16枚目のまとめで冒頭の問いに戻って言い直す。

| 筋 | 型 | 一文 | 枚 |
|---|---|---|---|
| 状況 | — | Gravitational waves were predicted in 1916 and seen only indirectly, through the energy loss of the binary pulsar PSR B1913+16 | 2 |
| 複雑化 | 壁 | A strain of 10⁻²¹ changes the length difference of 4 km arms by only about 4×10⁻¹⁸ m, about 1/400 of a proton | 5 |
| 問い | どうやって | How can a stretch this tiny be caught on Earth, and told apart from noise? | 5 |
| 答え | — | Same chirp at two sites, not noise | 14 |
| 対立 | — | Is the signal seen at both sites a gravitational wave, or glitches and noise lining up by chance? | 12 |
| それで | — | Sensors rule out local disturbances, and time-shifted background puts chance noise below once in 203,000 years (5.1σ): the noise explanation is gone, so the wave was caught directly | 14 |
| 語り手 | — | The LIGO team: they read a stretch smaller than a proton, then cleared the doubt of chance noise with 608,000 years of time-shifted background | — |

話の型：論文紹介（方法から）

拍の割り当て：だから（手段：方法・装置）＝4、しかし（壁：越えるべき難しさ）＝5、そして（次へ：結果）＝8、しかし（疑い：別の説明・偶然では）＝12、だから（帰結：確かめた結果）＝14。拍のあいだの肉付け：6・7（壁の越え方）、9〜11（波形から波源へ）、13（背景の作り方）、15（波源の値）。

## 3b. データ（data.py merge が data_N.md から入れる。図の案から「データN」で指す。値・単位・注記はこのとおりに描く。驚きの事実は、使うなら3節の事実の行に写す）

### データ1：False alarm rate of GW150914 in each search
- 驚き：波形の形の条件を外した探索でも、雑音が同じ強さを出すのは 8,400 年に1回。一番強い探索では背景のどの事象も超えたので、上限（20万3千年に1回未満）しか言えない
- 問いの候補：雑音の偶然の一致で、この信号が出ることはあるのか？
- 単位：年（雑音が同じ強さ以上の事象を1回出すまでの年数。大きいほど偶然らしくない）
- 分母：—
- 時点：2015年9月12日〜10月20日の16日分の同時観測
- 出典：V. Searches（A. Generic transient search・B. Binary coalescence search）、Fig. 4（Abbott et al., Phys. Rev. Lett. 116, 061102, 2016）
- 確認：○
- 別の読み方：連星合体の探索の値は「背景の長さ（60万8千年分）で決まる上限」で、測った頻度ではない。探索ごとに背景の長さ（汎用は6万7400年分）と分類の数が違うので、差は探索のよし悪しの比べではない
| 区分 | 値 | σ |
|---|---|---|
| Binary coalescence search（上限） | 203000 | 5.1 |
| Generic transient search（C3 class） | 22500 | 4.6 |
| Generic, any shape（C2+C3 class） | 8400 | 4.4 |

### データ2：Black hole masses before and after the merger
- 驚き：合体後のブラックホール（62 M⊙）は、合体前の2つ（36＋29 M⊙）の和より軽い。差は重力波で出たエネルギー（論文の推定 3.0 ± 0.5 M⊙c²）
- 問いの候補：消えた質量はどこへ行ったのか？
- 単位：太陽質量 M⊙（波源の系）
- 分母：—
- 時点：GW150914（2015年9月14日 09:50:45 UTC）
- 出典：Table I（Abbott et al., Phys. Rev. Lett. 116, 061102, 2016）
- 確認：○
- 別の読み方：どれも中央値で、90% の範囲は ±4〜5 M⊙。引き算の差 3 は範囲と同じくらいなので、放出エネルギーは論文の推定値 3.0 ± 0.5 M⊙c²〔VI〕で言う
| 区分 | 値 |
|---|---|
| Primary (before) | 36 |
| Secondary (before) | 29 |
| Final (after) | 62 |

## 構成

| 番号 | 範囲（論文） | タイトル | ●見出し | 前の枚から | 青帯（結論） | 図で見せるもの | 本文の要点 | ノートへ | 本文の形 | 役割 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | — | — | — | — | — | — | Paper review: Observation of Gravitational Waves from a Binary Black Hole Merger | — | — | 表紙 |
| 2 | I. Introduction | Background | A century-old prediction | — | Before 2015, the only evidence was one pulsar's energy loss | 仕組み：模式図：a ring of free particles stretched one way, then the other, over one wave cycle (self-drawn. 読み方：dots = freely floating masses, ring shape = the stretch at that moment) | Prediction (1916)：transverse waves of spatial strain (space itself stretches and squeezes) moving at the speed of light〔I. Introduction〕 / Indirect evidence：binary pulsar PSR B1913+16, orbital ★energy loss (the orbit shrinks as GWs carry energy away)〔I. Introduction〕 / Your guess：how far would a 4 km ruler stretch?〔III. Detectors〕 | Einstein knew the amplitude would be tiny; the reality of GWs was debated until 1957; pulsar = neutron star sending regular radio pulses; quadrupole moment = how the mass distribution changes | ラベル | 本文 |
| 3 | — | — | — | — | — | — | Paper title / B. P. Abbott et al. (LIGO Scientific Collaboration and Virgo Collaboration) / Phys. Rev. Lett. 116, 061102 (2016) / CC BY 3.0, DOI 10.1103/PhysRevLett.116.061102 | — | — | 表紙 |
| 4 | III. Detectors, Fig. 3 | Detector | Interferometer as a ruler | だから（手段） | Two perpendicular 4 km arms turn a stretch of space into a phase shift | 仕組み：模式図：Michelson interferometer drawn after Fig. 3 (laser, beam splitter, two 4 km arms with test-mass mirrors, photodetector; not to scale. 読み方：red line = light path, one arm stretches while the other shrinks) | ΔL(t) = δLx − δLy = h(t)L〔III. Detectors〕 / h：strain, the fractional stretch (no unit)〔III. Detectors〕 / L：arm length, ★4 km〔III. Detectors〕 / Readout：ΔL shifts the phase of the returning light → photodetector〔III. Detectors〕 | Test masses are free-hanging mirrors; the wave changes the distance between them; like the ring on slide 2, when the x arm stretches the y arm shrinks, so the difference of the two arms catches it; two sites: Hanford (H1) and Livingston (L1) | 式の注釈 | 本文 |
| 5 | Abstract, III. Detectors | Detector | The size of the target | しかし（壁） | The target stretch, 4×10⁻¹⁸ m, is about 1/400 of a proton | 印象：大きな数字：4×10⁻¹⁸ m（about 1/400 of a proton, 1.7 fm wide; presenter's estimate, proton size from CODATA 2018） | 10⁻²¹ (peak strain of the signal we will see)〔要旨〕 × 4 km〔III. Detectors〕 → ★4×10⁻¹⁸ m〔発表者の概算〕 / Question：how can we catch it? | Answer to the slide-2 guess; 10⁻²¹ is the peak strain later measured (1.0×10⁻²¹); proton size (charge radius 0.84 fm) is outside the paper; earlier resonant bars (1960s) and initial interferometers (2002–2011) gave only upper limits | 展開・ラベル | 本文 |
| 6 | III. Detectors | Detector | More light, sharper ruler | だから（手段） | Recycled light reaches 100 kW per arm, 5,000 times the 20 W input | 流れ：流れ図：Laser 20 W → Beam splitter 700 W → Each arm cavity 100 kW | Arm cavity：light bounces between the two test masses, each trip adds the shift again ⇒ phase effect ★×300〔III. Detectors〕 / Power recycling：a partly transmitting input mirror sends light heading back to the laser into the arms again, 20 W → 700 W → ★100 kW〔III. Detectors〕 | 5,000 = 100 kW / 20 W (presenter's arithmetic); purpose: more light ⇒ smaller relative shot noise; shot noise = the fluctuation in the number of photons, about √N for N photons, so the relative fluctuation falls as the light grows; 1064 nm laser | ラベル | 本文 |
| 7 | III. Detectors, Fig. 3(b) | Detector | Noise by frequency band | そして（並べる） | Above 10 Hz, ground motion is cut by over 10 orders of magnitude | 実物：資料の図：Fig. 3(b), noise spectrum of H1 and L1 (figure first: large on the left, cases on the right) | Above 150 Hz：photon shot noise ⇒ more light (previous slide)〔III. Detectors・Fig. 3〕 / Middle：thermal noise ⇒ heavy 40 kg fused-silica mirrors, less thermal jiggle〔III. Detectors〕 / Low：seismic noise ⇒ ★quadruple pendulum on an active isolation platform〔III. Detectors〕 | Reading Fig. 3(b): vertical axis = noise in each frequency band, as strain (unit 1/√Hz); lower = smaller stretches can be read; a pendulum barely follows ground shaking faster than its own swing, and four stages multiply the effect; most sensitive band 100–300 Hz, 3–5× better than initial LIGO; arm tubes below 1 μPa; calibration within 10% in amplitude | 場合分け | 本文 |
| 8 | II. Observation, Fig. 1 top row | Result 1 | GW150914 | そして（次へ） | On 14 Sep 2015, Livingston saw it 6.9 ms before Hanford | 実物：資料の図：Fig. 1 top row, H1 and L1 strain, with H1 shifted and inverted over L1 (wide, below the text) | L1 first → H1 ★6.9 ms later (light needs up to 10 ms between the sites ⇒ one wave could pass both)〔II. Observation・Fig. 1〕 / When：09:50:45 UTC, Hanford (H1) and Livingston (L1)〔II. Observation〕 / Strength：peak strain 1.0×10⁻²¹, combined SNR 24 (signal 24 times the typical noise)〔要旨・II. Observation〕 | H1 is inverted because the two detectors face differently; 35–350 Hz bandpass for display; only the two LIGO detectors were observing | 展開・ラベル | 本文 |
| 9 | II. Observation, Fig. 1 bottom row | Result 1 | Frequency and amplitude grow | そして（詳しく） | Eight cycles in 0.2 s, rising to 150 Hz at peak amplitude | 実物：資料の図：Fig. 1 bottom row, time–frequency map (wide, below the text) | Track：35 → 150 Hz in about 8 cycles over 0.2 s, amplitude peaks at ★150 Hz〔II. Observation〕 / Both sites：the same rising track in H1 and L1〔Fig. 1〕 / Reading：a 'chirp': two masses spiral in as they lose energy to GWs and orbit faster, so frequency and amplitude rise〔II. Observation〕 | Reading the map: horizontal = time, vertical = frequency, brightness = signal strength; 'chirp': this rising sweep sounds like a bird's chirp as audio; the whole signal spans 35–250 Hz (abstract) | ラベル | 本文 |
| 10 | II. Observation, Fig. 2 | Result 2 | Weighing by the chirp | だから（帰結） | The rate of the rise weighs the pair at 70 M⊙ or more in total | 実物：資料の図：Fig. 2 top panel, full-band waveform with the horizon insets (figure first: large on the left) | ℳ = (m₁m₂)^(3⁄5) ⁄ (m₁+m₂)^(1⁄5) = (c³⁄G)[(5⁄96)π^(−8⁄3) f^(−11⁄3) ḟ]^(3⁄5)〔II. Observation〕 / f, ḟ：observed frequency and its rate of change, read from the data〔II. Observation・Fig. 1〕 / ℳ ≃ 30 M⊙〔II. Observation〕 ⇒ total ★≳ 70 M⊙〔II. Observation〕 | Chirp mass = the one mass combination that sets how fast the chirp rises: heavier pairs radiate more strongly and sweep faster; for a given total M, ℳ is largest at m₁ = m₂ (ℳ ≈ 0.435M), so ℳ ≃ 30 M⊙ needs M ≈ 70 M⊙ or more (presenter's arithmetic); Fig. 2 bottom: R_S = Schwarzschild radius 2GM/c² (horizon size); speed above 0.5c near merger | 式の注釈 | 本文 |
| 11 | II. Observation | Result 2 | Ruling out neutron stars | だから（問い） | At about 350 km apart, only black holes can hold 70 M⊙ | 仕組み：模式図：scale drawing of two equal masses ≃350 km apart, with summed Schwarzschild radii ≳210 km (to scale. 読み方：circles = horizon size, gap = separation at 75 Hz) | Two neutron stars？⇒ ★each ≲ 2 M⊙〔II. Observation・Fonseca+ 2021〕 / Neutron star + black hole？⇒ merges at a much lower frequency〔II. Observation〕 / Two black holes？⇒ ★350 km apart (Kepler, 75 Hz orbit), radii sum ≳210 km (3 km per M⊙)〔II. Observation〕 | Heaviest well-measured neutron star: PSR J0740+6620, 2.08 ± 0.07 M⊙ (Fonseca et al., ApJL 915, L12, 2021; outside the paper), so two cannot reach 70 M⊙; orbit 75 Hz = half the 150 Hz GW frequency; equal point masses; R_S = 2GM/c² (slide 10), so 70 M⊙ gives about 210 km, and 350 km is under twice that: only black holes are that compact; NS + BH with this chirp mass would need a very large total mass, and a bigger pair touches at a wider, slower orbit, so it would merge at a lower frequency | 問い | 本文 |
| 12 | IV. Detector validation, V. Searches | Result 3 | Glitches and disturbances | しかし（疑い） | Non-Gaussian glitches in the data could fake a coincidence | 違い：比較：Gravitational wave（same shape at both、≤10 ms apart、sensors quiet）と Noise（shapes differ、any offset、sensors see it） | Local disturbance？⇒ under ★6% of the signal's strain, too small to make it〔IV. Detector validation〕 / Chance coincidence？⇒ must be counted (next)〔V. Searches〕 | Glitch = a short burst of noise from the instrument; non-Gaussian = big bursts come far more often than a normal distribution predicts, so σ cannot be computed from a formula and chance must be counted; no correlated transients between sites; sensors: seismometers, microphones, magnetometers, radio receivers, cosmic-ray detector; ~10⁵ channels; detectors cannot be shielded from GWs | 問い | 本文 |
| 13 | V. Searches | Result 3 | Manufacturing background | だから（手段） | Sliding one site's 16 days by ≫10 ms gave 608,000 years of noise | 仕組み：模式図：time shift: H1 and L1 noise traces, L1 slid by an offset much larger than 10 ms, coincidences counted (schematic. 読み方：rows = two detectors, after the shift a real signal no longer lines up) | 1. Shift one site by ≫10 ms (beyond the light time, so no real wave lines up) 2. Re-count coincidences 3. Repeat ~10⁷ times ⇒ ★608,000 years〔V. Searches〕 / Bias：conservative, a real signal left in makes noise look stronger〔V. Searches〕 | Nothing is invented: real noise is re-paired in time; each shift adds another 16 days of noise-only coincidences, so ~10⁷ shifts × 16 days add up to 608,000 years; 16 days: 12 Sep – 20 Oct 2015; numbers are for the binary coalescence search; a real signal in the background makes the false alarm rate an overestimate | 手順・ラベル | 本文 |
| 14 | V. Searches, Fig. 4 right | Result 3 | Beyond every background event | だから（帰結） | No background event beat it: under 1 false alarm per 203,000 years | 実物：資料の図：Fig. 4 right, binary coalescence search histogram (GW150914 circled in red by the presenter; figure first: large on the left) | Binary coalescence search：templates, ρ̂c = 23.6 (loudness) ⇒ < 1 per 203,000 years, ★5.1σ〔V. Searches〕 / Generic transient search：no waveform model, ηc = 20.0 ⇒ < 1 per 22,500 years, 4.6σ〔V. Searches〕 / Two searches：independent, both detect it〔V. Searches〕 | Reading Fig. 4: horizontal = loudness score, vertical = number of events, lines = time-shifted background, red circle = GW150914; false alarm rate = how often noise alone makes an event this strong; 203,000 is an upper bound set by the background length; it is below 608,000 because the search sorts events into classes, and counting the chance in any class (trials factor) lowers the bound; 16 days ÷ 203,000 years ≈ 2×10⁻⁷ = chance that noise did it during the run ↔ 5.1σ Gaussian tail; values in データ1 | ラベル | 本文 |
| 15 | VI. Source discussion, Table I | Discussion | Masses from the full waveform | そして（次へ） | Bayesian fits give 36 and 29 M⊙ before, 62 M⊙ after | 比べる：棒グラフ：データ2 | 36 + 29 M⊙ → ★62 M⊙〔Table I〕 / Radiated：the missing 3.0 ± 0.5 M⊙c² as GWs〔VI. Source discussion〕 / GR tests：three checks, ★no deviation〔VI. Source discussion〕 | Masses as at the source; read at Earth, cosmic expansion (z = 0.09) stretches the wave and masses look about 1.09× heavier, so slide 10's ≳70 M⊙ is about 65 = 36 + 29 here; 90% intervals ±4–5 M⊙; distance 410 Mpc (z = 0.09); peak luminosity 3.6×10⁵⁶ erg/s; graviton mass < 1.2×10⁻²² eV/c²; final spin 0.67; sky area ~600 deg² | 展開・ラベル | 本文 |
| 16 | VIII. Conclusion | Conclusion | Back to the question | だから（帰結） | A sub-proton stretch, caught at two sites and not by chance | — | Catch it？⇒ strong light, quiet mirrors〔III. Detectors〕 / Noise？⇒ < 1 per 203,000 yr〔V. Searches〕 / Source？⇒ ★merging black holes〔II. Observation・VI. Source discussion〕 | Full answer: first direct GW detection and first binary black hole merger〔VIII. Conclusion〕; outlook: design sensitivity gives 3× SNR; Virgo, KAGRA, LIGO-India improve sky position〔VII. Outlook〕 | 問い | まとめ |
| 17 | — | Q&A | Anticipated questions | — | — | — | — | — | — | 想定質問 |
| 18 | — | Q&A | Anticipated questions | — | — | 実物：資料の図：for Q3, Fig. 1 top row, right panel (H1 shifted and inverted over L1) | — | — | — | 想定質問 |

## 引っかかりへの手当て

- [2] strain が定義前に出る → 2枚目の本文に括弧で「space itself stretches and squeezes」（定義は4枚目の h）
- [2] エネルギー損失がなぜ証拠か → 本文の括弧に「the orbit shrinks as GWs carry energy away」
- [4] 直交する腕の差で読む理由 → ノートで2枚目の輪に戻し、x が伸びると y が縮むので差に出ると一言
- [4] 7枚目で H1・L1 が先に出る → 4枚目のノートで Hanford (H1)・Livingston (L1) と略号を添えた
- [5] 10⁻²¹ の出どころ → 本文の括弧に「peak strain of the signal we will see」（8枚目の 1.0×10⁻²¹ へ）
- [6] 光を増やす理由とショット雑音 → ノートに、光子の数の揺らぎ √N で相対の揺らぎが下がると1文
- [6] 往復で ×300 になる理由 → 本文の括弧に「each trip adds the shift again」
- [6] recycling の像 → Power recycling の項を、レーザー側へ戻る光を腕へ送り返すと言い換え
- [6] Signal recycling の帯域の主張 → 理由が置き場に無い細部なので本文から外した
- [6] homodyne readout・Nd:YAG → ノートから外した（筋に要らない名前）
- [7] Fig. 3(b) の読み方 → ノートの頭に縦軸（各帯域の雑音、ひずみ換算 1/√Hz、低いほど細かく読める）
- [7] 低損失ファイバーで熱雑音が減る理由 → 置き場に理由が無いので low-loss を外し、「heavy 40 kg mirrors, less thermal jiggle」に言い換え
- [7] 振り子で地面の揺れが切れる理由（青帯のなぜ） → ノートに、振り子は自分の揺れより速い揺れについていかず、4段で掛け算になると1文
- [8] 6.9 ms の意味 → 本文の括弧に「⇒ one wave could pass both」
- [8] SNR 24 → 本文の括弧を「signal 24 times the typical noise」に言い換え
- [9] 時間周波数図の読み方 → ノートの頭に横・縦・明るさ
- [9] 周波数が上がる ⇒ 近づく、の理由・chirp の語 → 本文の Reading を「a 'chirp': … orbit faster, so frequency and amplitude rise」に（chirp はここが初出）
- [10] 掃引の速さで重さが分かる理由・チャープ質量 → ノートの頭に一言（重いほど強く放射して速く掃引）
- [10] ℳ ≃ 30 ⇒ ≳70 → ノートに、同じ総質量なら m₁ = m₂ で ℳ が最大（≈0.435M）と1文
- [10] detector frame → 10枚目は新しい名前が3つになるので本文から外し、中身は15枚目のノートへ（下の [15]）
- [10] 図の R_S が11枚目の定義より先に出る → R_S = 2GM/c² の定義を10枚目のノートへ移した
- [11] 350 km の出どころ → 本文の括弧に「Kepler at a 75 Hz orbit」
- [11] 半径の和 210 km とブラックホールの結びつき → 本文に「about 3 km per M⊙」、ノートに 350 km は半径の和の2倍弱なので BH だけが詰まれると1文
- [11] NS + BH が低い周波数で合体する理由 → ノートに、大きい組ほど広く遅い軌道で接すると1文
- [11] ringdown・Kerr（ノート） → 語の中身が無い細部なので外した
- [11] 中性子星2つでは質量が足りない理由 → 採らない：中性子星の質量の上限が置き場に無い。設計に戻す
- [12] glitch・non-Gaussian → ノートの頭に、短い雑音の突発・正規分布より大きな揺れが多いので σ を式で出せず数えるしかない（13枚目へ）
- [12] 6% 未満の意味 → 本文の括弧を「of the signal's strain, too small to make it」に
- [13] ずらすと雑音だけになる理由 → 本文の手順1に括弧で「beyond the light time, so no real wave lines up」
- [13] 16日が 608,000 年になる理由 → ノートに、1回ずらすごとに16日分、約10⁷回と1文
- [13] Manufacturing の像 → ノートの頭に「Nothing is invented: real noise is re-paired in time」
- [13] conservative の向き → 本文を「a real signal left in makes noise look stronger」に言い換え
- [13] classes and trials factor（ノート） → 14枚目のノートへ中身つきで移した
- [14] 608,000 年と 203,000 年の食い違い → ノートに、分類ごとの偶然を数える分（trials factor）で上限が下がると1文
- [14] ρ̂c・ηc と、連星合体の探索が何をするか → 本文に「fits merger waveforms」「(loudness)」、ノートに横軸＝強さの点数
- [14] ヒストグラムの読み方 → ノートの頭に横・縦・線・丸
- [14] 203,000 年 ⇒ 5.1σ → ノートに、16日 ÷ 203,000 年 ≈ 2×10⁻⁷ が観測中の偶然の確率と1文
- [14] 2つ目の事象（1 per 2.3 years） → 説明の無い細部なのでノートから外した
- [15] Bayesian fits → 本文の括弧に「GR waveform fit」
- [15] 10枚目の ≳70 と 36 + 29 = 65 → ノートに、地球で読むと z = 0.09 の膨張で約1.09倍重く見えるので、10枚目の ≳70 はここでの約65と1文
- [15] 36 + 29 → 62 と放出エネルギーのつながり → 本文を「the missing 3.0 ± 0.5 M⊙c² left as GWs」に

## 想定質問

| 番号 | 型 | 質問 | 回答の要点 | 戻る枚 |
|---|---|---|---|---|
| Q1 | 疑い | Could noise in the two detectors have lined up by chance? | Time-shifted background (608,000 years): noise this strong less than once in 203,000 years, 5.1σ〔V. Searches〕 | 14 |
| Q2 | 疑い | Could an earthquake or a power-line disturbance have caused it? | Site sensors: all fluctuations under 6% of the strain amplitude; no correlated disturbance at both sites〔IV. Detector validation〕 | 12 |
| Q3 | 数値の意味 | What does the 6.9 ms delay mean? | Shorter than the 10 ms light travel time between the sites, so one wave could have passed both〔II. Observation〕 | 8 |
| Q4 | 限界 | Where in the sky was the source? | Only two detectors: about 600 deg² (90% region), set mainly by arrival time; Virgo and KAGRA will narrow it〔II. Observation・VII. Outlook〕 | 15 |

## 迷った所

- 5枚目の図を「大きな数字」にした（陽子との比は論文の外の値。CODATA 2018 の陽子の荷電半径 0.84 fm から幅 1.7 fm として概算）。対数の物差しの模式図にする手もある
- 14枚目は Fig. 4 右（実物）を主役にし、データ1（3つの探索の誤報率）は本文とノートに回した。棒グラフにするなら対数軸が要る
- 12枚目の IV 節（検出器の確かめ）は1枚の問いの形に2行でまとめ（相関した雑音が無いことはノートへ）、雑音の偶然の数え方は13・14枚目に分けた
- 15枚目の距離 410 Mpc はノートへ回した（入りの見込みのため）。範囲が「主要な結果」なので、波源の値は質量と放出エネルギー・GR の検証だけを本文に
- 論文の節の順は II（観測）→ III（検出器）だが、依頼の「方法から入る」に合わせて III を先（4〜7枚目）、II を後（8〜11枚目）にした。論文どおり II を先にするなら 8〜11 を 4 の前へ
- 筋の答えは、まとめの枚の入りの見込みのため短い一文（Same chirp at two sites, not noise）にした。数値（203,000 年に1回未満・5.1σ）は14枚目の青帯、初の直接検出の言い切りは16枚目のノートに
- 2枚目の「Your guess」の答え合わせは5枚目（4×10⁻¹⁸ m）。陽子の幅 1.7 fm は論文の外（CODATA 2018 の荷電半径 0.84 fm の2倍）で、5枚目の大きな数字の注記にだけ置いた
