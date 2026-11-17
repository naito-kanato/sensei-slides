# このフォルダの図の出典

このフォルダの画像は、次の論文の図の一部を切り出したものです（切り出しのほかの変更は、下の表に書いたもののみ）。
切り出すときは、軸・目盛りの数字・軸の名前・凡例を残しています（`_axes` の付いたものは、論文の図では段どうしで共有している軸を、同じ図から並べ直して付けたもの）。

- B. P. Abbott et al. (LIGO Scientific Collaboration and Virgo Collaboration),
  "Observation of Gravitational Waves from a Binary Black Hole Merger",
  *Physical Review Letters* **116**, 061102 (2016). DOI: [10.1103/PhysRevLett.116.061102](https://doi.org/10.1103/PhysRevLett.116.061102)
- ライセンス：[Creative Commons Attribution 3.0（CC BY 3.0）](https://creativecommons.org/licenses/by/3.0/)。
  論文には「著者・題名・雑誌・DOI を示せば、論文とその一部を許可なく再利用できる」と書かれています。

| ファイル | 元の図 |
|---|---|
| `fig1_strain_axes.png` | Fig. 1 の上段（ハンフォード H1 とリビングストン L1 で観測したひずみ）に、同じ図の縦軸の名前「Strain (10⁻²¹)」（上の2段で共有）と、最下段の時間軸の目盛り・「Time (s)」を付けたもの。8枚目で使う |
| `fig1_strain_L1_axes.png` | Fig. 1 の上段の右のパネル（L1 と、ずらして反転した H1）に、左のパネルの縦軸の目盛り・縦軸の名前と、最下段の右の時間軸を付けたもの。16枚目（想定質問）で使う |
| `fig1_strain.png` | Fig. 1 の上段（時間軸なし）。`examples/structures` の見本が使う |
| `fig2_waveform_lower.png` | Fig. 2 の下2段（推定した重力波の波形と、ブラックホールの間隔・相対速度。上の Inspiral・Merger・Ring-down の絵は切り落とした） |
| `fig1_timefreq.png` | Fig. 1 の最下段（時間–周波数の図と色の凡例・その題「Normalized amplitude」。題の高さまで切り出したので、すぐ上の段の枠の下端だけ白く塗った）。スライドでは H1・L1 の注記（発表者が追加）を重ねている |
| `fig3b_noise.png` | Fig. 3 の右上のパネル (b)（検出器の雑音スペクトル。パネル記号「(b)」だけ白く塗った） |
| `fig4_search.png` | Fig. 4 の右（連星の合体を探す解析の結果と、雑音の背景。縦軸の名前「Number of events」まで）。スライドでは GW150914 に赤い丸と、黒線の注記（発表者が追加）を重ねている |

論文の図は、論文の PDF のページを 400 dpi で画像にして切り出しました。

`../figs.py` が描く図（重力波によるひずみ、干渉計の模式図、連星パルサー、光のパワー、連星の大きさ、時刻ずらし）は、論文をもとにこのリポジトリで描いたものです。
