# 構成案レビュー：Observation of Gravitational Waves from a Binary Black Hole Merger

- 判定: 直してから進める
- 総評: 筋（壁→光と振り子→信号→疑い→時刻ずらし）と枚数（本文13枚／20分）は釣り合っている。直す必要があるのは3種類。1つ目は、3枚目の問いの一文が筋の表とずれていて、後半の答え（13・14枚目）の「雑音と見分ける」を問いの側で立てていない点。2つ目は、6・8・12枚目の青帯の正確さと、青帯と図の食い違い。3つ目は、11→15枚目の質量の系（70 vs 36＋29）と、9→14枚目の SNR・ρ̂c の呼び名のずれが聞き手に説明されていない点。

## 必ず直す点

1. [3] スライドに載る問い「How can the wave itself be caught on Earth?」が、筋の表の問い「How can such a tiny stretch be caught on Earth and told apart from noise?」と違う。「雑音と見分ける」の半分が抜けていて、答えの枚（14：誤報率）がその問いに答える形になっていない → スライドの問いを筋の表と同じにする。例：「★How can a stretch this tiny be caught, and told apart from noise?」。2枚目の「tiny」とつながるように、問いの行の直前に「Amplitude: remarkably small」を受ける語（such a tiny…）を残す（根拠：p.1 I. Introduction／p.5 V. Searches）
2. [6] 青帯「h ≈ 10⁻²¹ moves a 4 km arm only ~4×10⁻¹⁸ m」と筋の表の「changes a 4 km arm by…」は不正確。hL は2本の腕の長さの**差** ΔL = δLx − δLy で、1本の腕の動きではない → 青帯を「h ≈ 10⁻²¹ changes the arm-length difference by only ~4×10⁻¹⁸ m」にし、筋の表の複雑化の一文も同じに直す（根拠：p.3 III. Detectors「ΔL(t) = δLx − δLy = h(t)L」）
3. [8] 図は Fig. 3(b)（雑音スペクトル）なのに、青帯「Isolation cuts ground motion >10 orders above 10 Hz」は図に写っていない（地面の揺れの遮断は本文だけの数値）。図が青帯を支えていない → (a) 図に合わせて青帯を「Most sensitive at 100–300 Hz, 3–5× better than initial LIGO」にし、10枚目の信号の帯域（35–250 Hz）がこの谷に入ることを図の注記で示す。または (b) 青帯はそのままで、図を4段振り子と防振台の模式図に替える。(a) を勧める（根拠：p.4 Fig. 3(b) キャプション、p.4 III、p.5 冒頭「100–300 Hz … 3 to 5 times」）
4. [12] 青帯「Of known objects, only black holes orbit at 75 Hz」は言い過ぎ。中性子星の対でも 75 Hz で回ることはあり、論文の論点は「必要な質量を持ちつつ、**触れずに** 75 Hz まで回れるほど compact なのはブラックホールだけ」 → 「Of known objects, only black holes are heavy and compact enough to orbit at 75 Hz」。本文の Two neutron stars の行も「compact, but not enough mass」のまま、この論理に合わせる（根拠：p.3「the only known objects compact enough to reach an orbital frequency of 75 Hz without contact」）
5. [11→15] 11枚目の「total ≳ 70 M⊙ (detector frame)」のあと、15枚目で「36 and 29 M⊙」（合計 65、source frame）が出る。聞き手には矛盾に見える（70以上と言ったのに65）。系の違いは11枚目のノートにしか無い → 15枚目の Masses の行に「(source frame; ×(1+z) = 1.09 ⇒ ≈ 71 in the detector frame)」を添える。11枚目の本文にも「detector frame = masses seen ×(1+z)」の一言を入れる（根拠：p.7 Table I のキャプション「to convert to the detector frame multiply by (1+z)」、p.3）
6. [9→14] 14枚目の ρ̂c = 23.6 が定義なしで出る。しかも9枚目の「combined SNR 24」との関係が書かれていない（呼び名の揺れ）。聞き手は「背景のどれより大きい」の軸の量が分からない → 14枚目の Reading の行に「x: ρ̂c = combined matched-filter SNR of both sites, down-weighted for glitch-like data (cf. SNR 24, slide 9)」を足す。χ² による重みの詳細はノートへ（根拠：p.7 V.B「ρ̂ = ρ/{[1+(χ²r)^{3/2}]/2}^{1/6} … quadrature sum ρ̂c」、p.3「combined SNR of 24 [45]」）

## 直すとよい点

1. [2・3] 2枚目の「never seen directly」と3枚目の「showed GWs only indirectly」が同じこと（直接は見えていない）を2回言っている → 2枚目の青帯は波の性質と小ささにする。例：「Einstein's 1916 waves stretch and squeeze space itself at light speed」。「直接は未観測」は3枚目に任せる（根拠：p.1 I）
2. [5] 要点が5個（Michelson／式／h／L／Two sites）で4個を超える。また「Two sites ⇒ local noise is not shared」は9枚目（2か所で同じ波形）で使う前提なのに、4枚前にしか無い → h と L は式の注釈にまとめ、Two sites の行は9枚目へ移す（根拠：p.3 III 冒頭）
3. [6] 「★1/400 of a proton」は発表者の概算（陽子の大きさは資料外）なのに、赤字で資料の事実のように載る → その行に「(presenter's estimate)」を添える。また「Weber's resonant bars (1960s) … ⇒ upper limits only」は、論文が upper limits と言っているのは 2002–2011 の初期の干渉計の共同観測だけ → upper limits は初期の検出器の行だけに付ける（根拠：p.1 I）
4. [7] 青帯（100 kW に増やす）から、6枚目の壁（4×10⁻¹⁸ m）を越えられる理由へのつながりが「less impact of photon shot noise」の語だけ → Purpose の行を「more photons ⇒ smaller relative shot noise ⇒ smaller ΔL readable」にする。図は自作の光路図より、Fig. 3 の本体（20 W・100 kW の表記がある）を使い、700 W を注記するほうが資料に忠実（根拠：p.3–4 III、p.4 Fig. 3）
5. [10] Meaning の行「two orbiting masses spiraling in」から、論文の限定「the most plausible explanation」が外れている → 「most plausible: two orbiting masses spiraling in」（根拠：p.3）
6. [11] 図の Fig. 2 は、Sec. VI の GR 解析で得たパラメータで計算した波形。この枚の青帯（f と ḟ から合計 ≥70 M⊙）を支えていない → 10枚目と同じ Fig. 1 下段を同じ位置に置き、f と ḟ を読む箇所に注記する。Fig. 2 は12枚目へ移して補助にする（下段の分離が数 R_S まで縮む・v/c > 0.5 ＝ ブラックホールの近さ）か、ノートへ回す（根拠：p.3 Fig. 2 キャプション「using the resulting source parameters」）
7. [13] 青帯が疑い（雑音が偶然そろう）だけで、本文の中身（時刻ずらしで背景を作る）と青帯が別のことを言っている → 疑いと答えの数値を1文にする。例：「Chance noise could line up, so one site was time-shifted to build 608,000 years of noise-only background」。拍の「しかし（疑い）」は青帯の前半に残る（根拠：p.5 V、p.7 V.B）
8. [14] 答えの位置は「後」で14枚目だが、答えの一文の前半（2か所で 6.9 ms 差の同じチャープ）は9枚目にしか無い。14枚目では3枚目の問いへの回収が見えない → 本文の最後に「Answer: same chirp at two sites (slide 9) + time-shifted background ⇒ not chance noise」を1行足すか、原稿の締めで問いを読み返す
9. [15] 棒グラフが3本並び（36・29・62）だけだと、「合わせて65 → 62」の比べが目で追えない → 「before」を 36＋29 の積み上げ1本にし、「after」の 62 と並べる。差の所には引き算ではなく論文の推定値「3.0 ± 0.5 M⊙c² radiated (paper's estimate)」を書き、±4–5 の誤差棒を付ける（データ1の別の読み方どおり）。「GR tests: 3 checks, no deviation ⇒ graviton…」の「⇒」は、重力子の制限が3つ目の検査そのものなので「one of them: graviton Compton wavelength > 10¹³ km」にする。距離は 410 (+160/−180) Mpc と幅も添える（根拠：p.7 Table I、p.7–8 VI）
10. 英語：8枚目「>10 orders」→「by >10 orders of magnitude」。14枚目「under once per」→「less than once per」。7枚目「20 W of laser」→「20 W of laser light … in each arm」。「GWs」の略は2枚目で「gravitational waves (GWs)」と初出を示す。12枚目「point masses only ≃350 km apart」→「equal point masses would be only ≃350 km apart」
11. [9 または 11] 要旨の柱「matches the waveform predicted by general relativity」の直接の根拠である Fig. 1 の2段目（数値相対論の波形と、モデルを使わない再構成の 94% の重なり）が、どの枚にも無い → 9枚目のノートか11枚目の Waveform の行に、「NR waveform and model-free reconstruction overlap 94% (Fig. 1, 2nd row)」を足す（根拠：p.2 Fig. 1 キャプション）

## 資料にあるのに構成案から抜けている内容

- p.2 Fig. 1 の2段目・3段目：数値相対論の波形との一致（99.9% の独立計算）、2つの再構成の 94% の重なり、残差
- p.4–5 III：較正の不確かさ（振幅 10%・位相 10°）、GPS の時刻合わせ（10 μs 以内）、60 Hz 以下で10倍超の感度向上、観測した時空の体積が従来の10倍
- p.5 IV：環境センサーの網、環境の揺らぎは強さの 6% 以下、2か所に相関した外乱なし（Q1 だけにある。13枚目のノートに1文あるとよい）
- p.6 V.A：汎用探索の ηc = 20.0、クラス C3、67,400 年分の背景、試行の補正 3、C2+C3 での 1/8,400 年・4.4σ
- p.7 V.B：約250,000個のテンプレート、χ² による重み、15 ms の窓（ρ̂c の定義の材料）。2番目に強い事象（1/2.3年、確率 0.02）
- p.7 Table I・VI：最終ブラックホールのスピン 0.67、主星のスピン < 0.7
- p.8 VI（範囲外として省略可）：25 M⊙ を超える恒星質量ブラックホールの存在、低金属量、合体率 2–400 Gpc⁻³ yr⁻¹、背景放射
- p.8 VII：設計感度に達すると SNR が3倍

## 推論距離

[5] 「4 km arms ⇒ ΔL = hL」｜用語｜語・あと｜補う前提：ひずみ h＝長さの相対変化 ΔL/L（無次元）｜使う所：5・6・9｜架け方：本文の h の行に「(fractional stretch ΔL/L)」を括弧で添える
[5] 「a wave stretches one arm ⇒ test-mass mirrors」｜出どころ｜像｜補う前提：像：重力波が鏡を押して動かすと思い浮かべる → 実際は、自由に吊った鏡のあいだの距離（空間そのもの）が伸び縮みし、鏡は目印にすぎない｜使う所：5｜架け方：図の鏡に「free-hanging test mass」の注記、原稿1文
[6] 「4 km arms read ΔL ⇒ h ≈ 10⁻²¹」｜出どころ｜筋｜補う前提：10⁻²¹ は、のちに測られたピークのひずみ（要旨）を、狙う大きさとして先に使ったもの｜使う所：6｜架け方：本文に「(peak value later measured)」を括弧で
[7] 「the arm difference is only 4×10⁻¹⁸ m ⇒ build the light up to 100 kW」｜論拠｜筋・語・あと｜補う前提：ショット雑音＝光子の数の揺らぎ。光子数 N に対して相対的な揺らぎ ∝ 1/√N なので、光を強くすると小さな位相差が雑音に埋もれにくい（1/√N は資料外）｜使う所：7・8（Above 150 Hz: shot noise）｜架け方：Purpose の行を「more photons ⇒ smaller relative shot noise」にし、原稿に ※（資料外の補足）で1文
[7] 「20 W input ⇒ 700 W at the beam splitter」｜用語｜語｜補う前提：パワーリサイクリング＝入口の半透鏡で、戻ってきた光を干渉計へ送り返して溜める仕組み｜使う所：7｜架け方：本文に括弧で一言
[7] 「Signal recycling ⇒ broadens the bandwidth」｜用語｜深｜補う前提：腕の共振器の帯域＝応答できる信号の周波数の幅｜使う所：なし｜架け方：行ごとノートへ移す
[8] 「Fig. 3(b) ⇒ most sensitive at 100–300 Hz」｜用語｜筋・語・あと｜補う前提：縦軸＝雑音の振幅スペクトル密度を h に換算したもの（Hz⁻¹ᐟ²）。低いほど小さな h が見える｜使う所：8・10（信号の 35–250 Hz が谷に入る）｜架け方：図に「lower = quieter」の注記、原稿で軸を読む
[8] 「ground motion ⇒ quadruple pendulum」｜出どころ｜像｜補う前提：像：振り子は揺れるもの・揺れを生むものと思い浮かべる → 実際は、吊った段ごとに、共振より高い周波数の地面の揺れを弱める濾過器になる（資料外）｜使う所：8｜架け方：原稿に ※（資料外の補足）で1文
[9] 「same waveform 6.9 ms apart ⇒ a real common source」｜論拠｜筋・あと｜補う前提：遠い（4枚前）局所の雑音は2か所に同時には出ないので、伝播時間 10 ms 以内に同じ形なら共通の源｜使う所：9・13｜架け方：5枚目の Two sites の行を9枚目へ移す
[9] 「combined SNR 24 ⇒ ρ̂c = 23.6」｜用語｜あと｜補う前提：呼び名の揺れ：9枚目の combined SNR と14枚目の ρ̂c は同じ系統の量（2か所の matched-filter SNR を合わせ、雑音らしい形の分だけ下げた値）｜使う所：14｜架け方：14枚目の Reading の行に「ρ̂c ≈ combined SNR (slide 9)」
[10] 「35 → 150 Hz in 0.2 s ⇒ two orbiting masses spiraling in」｜論拠｜筋・あと｜補う前提：重力波の周波数は公転の2倍。エネルギーを失うと軌道が縮み、公転が速くなる｜使う所：10・12（75 Hz＝150 Hz の半分）｜架け方：Meaning の行に「(GW frequency = 2 × orbital; shrinking orbit ⇒ faster)」
[11] 「the frequency rises ⇒ chirp mass ℳ」｜用語｜語｜補う前提：チャープ質量＝周波数の上がり方（f と ḟ）だけで決まる m₁, m₂ の組み合わせ｜使う所：11｜架け方：ノートの一言を式の上の本文に上げる
[11] 「ℳ ≃ 30 M⊙ ⇒ total ≳ 70 M⊙」｜論拠｜筋｜補う前提：ℳ を固定すると、合計 M は m₁ = m₂ のとき最小で M = 4^(3/5)ℳ ≈ 2.3ℳ ≈ 70（発表者の補足）｜使う所：11｜架け方：本文に「(smallest when m₁ = m₂)」を括弧で、原稿に ※
[11] 「total ≳ 70 M⊙ ⇒ (detector frame)」｜用語｜あと｜補う前提：detector frame＝赤方偏移で (1+z) 倍重く見える質量、source frame＝波源での本来の質量｜使う所：15｜架け方：本文に括弧で一言
[12] 「orbit at 75 Hz ⇒ summed Schwarzschild radii ≳ 210 km」｜用語｜筋・語｜補う前提：シュヴァルツシルト半径 R_S = 2GM/c²＝その質量がブラックホールになる大きさ（1 M⊙ あたり約3 km。論文の 70 M⊙ → 210 km から）｜使う所：12｜架け方：本文に「(horizon size, ≈3 km per M⊙)」を括弧で
[12] 「≃350 km apart vs ≳210 km ⇒ very compact」｜論拠｜筋｜補う前提：70 M⊙ が 350 km の間隔で触れずに回る＝各天体はシュヴァルツシルト半径に近い大きさまで詰まっている｜使う所：12｜架け方：縮尺図の注記に「bodies must fit inside 350 km」
[12] 「Two neutron stars? ⇒ not enough mass」｜根拠｜筋｜補う前提：中性子星の質量の上限はおよそ2〜3 M⊙（資料外）で、2つ合わせても 70 M⊙ に届かない｜使う所：12｜架け方：原稿に ※（資料外の補足）で1文
[12] 「NS + BH ⇒ would merge at a much lower frequency」｜論拠｜深｜補う前提：同じチャープ質量で片方が軽いと合計が大きくなり、重い系ほど低い周波数で合体する｜使う所：なし｜架け方：原稿1文
[13] 「noise is non-Gaussian ⇒ the background must be measured」｜論拠｜筋・あと｜補う前提：正規分布なら σ から確率を計算できるが、裾の重い雑音ではできないので、実際のデータから数える｜使う所：13・14｜架け方：Problem の行に「⇒ cannot compute from σ; count from data」
[13] 「16 days, ~10⁷ shifts ⇒ 608,000 years」｜論拠｜筋｜補う前提：ずらすたびに雑音だけの16日分が新しくでき、それを約10⁷回重ねた長さ｜使う所：13・14｜架け方：手順3に「each shift = a new noise-only 16 days」
[14] 「above every background event ⇒ < 1 per 203,000 years」｜用語｜語｜補う前提：誤報率＝雑音だけでこれ以上強い事象が出る頻度。背景に上回る事象が無いので上限だけが言える｜使う所：14｜架け方：ノートの定義を Reading の行に上げる
[14] 「probability < 2×10⁻⁷ ⇒ 5.1σ」｜範囲｜像｜補う前提：像：σ を雑音の正規分布の幅と思い浮かべる → 実際は、時刻ずらしで数えた確率を正規分布の片側の裾に換算した目盛りで、雑音が正規分布だという意味ではない｜使う所：14｜架け方：本文に「(Gaussian-equivalent)」を括弧で、Q3 の答えを原稿に前出し
[15] 「total ≳ 70 M⊙ ⇒ 36 + 29 M⊙」｜比較｜筋・あと｜補う前提：遠い（4枚前）11枚目は detector frame、15枚目は source frame。(1+z) = 1.09 倍で 65 → 約71｜使う所：15｜架け方：Masses の行に「(source frame; ×1.09 in detector frame)」
[15] 「the waveform ⇒ 36, 29, 62 M⊙」｜出どころ｜筋｜補う前提：個々の質量は、GR の波形モデルをデータに当てたベイズ推定から（11枚目のチャープ質量だけでは決まらない）｜使う所：15｜架け方：本文に「(GR waveform fits, Sec. VI)」を括弧で
[15] 「GR tests ⇒ graviton Compton wavelength > 10¹³ km」｜用語｜深｜補う前提：重力子のコンプトン波長の下限＝重力子の質量の上限｜使う所：なし｜架け方：ノートへ移す
