# 続きもの（同じシリーズの次の回・次の節）を作るとき

発表の続きもの用。講座の次の回は `references/course.md` の手順4・6 に従う（講座には outline.md がなく、伏線は README の地図の「予告」から取る）。

前の回のデッキがあるなら、同梱の見本より**前の回の作業フォルダを雛形にする**。書式の決め事も図の部品もそこに揃っていて、
読み直し・描き直しが減る。オプション表は貼るだけで質問は省く（値は前の回の outline.md と同じ。SKILL.md 手順0）。

1. **雛形**：`_work/<前の回>/outline.md`（冒頭の決め事：タイトルの形・伏線の書き方・問題スライドの形）と `build.py` を読み、
   `build.py` をコピーして中身を差し替える。`examples/zemi/` は読まなくてよい
2. **図の部品を流用**：汎用の部品は `figkit` にある（`disordered_disks`・`tri_lattice`・`draw_disks`・`random_network` は
   液体・ガラス・結晶・網目の模式図用。配置は `cache=` で .npy に保存して使い回す）。前の回の図は `catalog.py` の一覧で探す。
   前の回だけにある関数は、同じ名前の `figs.py` どうしがぶつからないよう importlib で別名にして読み込む：
   ```python
   import importlib.util
   spec = importlib.util.spec_from_file_location("prev_figs", HERE.parent / "<前の回>" / "figs.py")
   prev = importlib.util.module_from_spec(spec); spec.loader.exec_module(prev)   # prev.f_vt_rate などを流用
   ```
   2回以上使った関数は、作業フォルダの figs.py の中で共通の関数にまとめる。スキルの部品（figkit・figlib）へ移すのはスキルの作者の仕事で、
   エージェントは部品を書き換えない（SKILL.md 手順7）。移したほうがよい関数は、渡すときにユーザーへ伝える
3. **レビュー担当は続投**：同じセッション内なら、前の回の担当に 【続けて頼む】で「次の資料の先読み」→「レビュー」を頼む
   （書式ガイドと前の回の決め事を覚えているので、読み直しが大きく減る）。新しいセッションでは担当がいないので新しく起動する。
   起動は【標準モデル】（構成案のレビュー担当。SKILL.md「モデルの確認」）。資料が短い（Markdown の講義録など）なら
   読ませるのは資料と style-guide 3・5節、figures.md 1節に絞る
4. **前の回からの伏線**：前の回の outline.md の「伏線」節を見て、「→第N回」で予告されていた内容をこの回のどこで回収するか決める
5. **決め事を残す**：この回で新しく決めたこと（ラベルの呼び方、色の割り当てなど）は outline.md の冒頭に書いておく。次の回の雛形になる
