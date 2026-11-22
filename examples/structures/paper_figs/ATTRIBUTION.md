# このフォルダの図の出典

このフォルダの画像は、次の論文の図の一部を切り出したものです（切り出しのほかの変更は、下の表に書いたもののみ）。
型の見本（`../build.py`・`../build_en.py`）と、テンプレートの見本（`../../template/build.py`）が使います。

- B. P. Abbott et al. (LIGO Scientific Collaboration and Virgo Collaboration),
  "Observation of Gravitational Waves from a Binary Black Hole Merger",
  *Physical Review Letters* **116**, 061102 (2016). DOI: [10.1103/PhysRevLett.116.061102](https://doi.org/10.1103/PhysRevLett.116.061102)
- ライセンス：[Creative Commons Attribution 3.0（CC BY 3.0）](https://creativecommons.org/licenses/by/3.0/)。
  論文には「著者・題名・雑誌・DOI を示せば、論文とその一部を許可なく再利用できる」と書かれています。

| ファイル | 元の図 | 変更 |
|---|---|---|
| `fig1_strain.png` | Fig. 1 の上段（ハンフォード H1 とリビングストン L1 で観測したひずみ。時間軸なし） | 切り出しのみ |
| `fig2_waveform_lower.png` | Fig. 2 の下2段（推定した重力波の波形と、ブラックホールの間隔・相対速度） | 上の Inspiral・Merger・Ring-down の絵を切り落とした |
| `fig1_timefreq_H1.png` | Fig. 1 の最下段の H1 のパネル（時間–周波数の図）と色の目盛り | 右端の重なった細い帯を白く塗った |
| `fig4_search.png` | Fig. 4 の右（連星の合体を探す解析の結果と、雑音の背景。縦軸の名前「Number of events」まで） | GW150914 に赤い丸を足した |

論文の図は、論文の PDF のページを 400 dpi で画像にして切り出しました。軸・目盛りの数字・軸の名前・凡例を残しています。

`../figs.py` が描く図（重力波によるひずみ、干渉計の模式図、光のパワー、連星の大きさ、時刻ずらし、Advanced LIGO の光の通り道）は、論文をもとにこのリポジトリで描いたものです（以前のゼミの見本の図）。
