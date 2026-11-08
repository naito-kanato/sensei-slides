# 道具とコマンド（SKILL.md から分けた、担当と1人で回すとき向けの節）

今要る節だけを `python <skill>/scripts/guide.py tools <見出しの語>` で読む。

## 道具

検査の部品は、何を見るか・直し方を自分の出力（とファイル冒頭の説明）に書いてある。✘・ERROR・△・WARN が出たら、その文を読んで直す。

| ファイル | いつ使うか |
|---|---|
| `scripts/next_step.py` | 今どこまで済み、次に何をするか。迷ったとき・再開するときに最初に |
| `scripts/guide.py` | 手順書・references の今要る節だけを出す |
| `scripts/check_env.py` | 初めて使うとき・「環境を確かめて」（手順0） |
| `scripts/materials.py` | 資料を発表フォルダの `資料/` に写し、足りないもの（研究発表の方針.md・図）を確かめる |
| `scripts/slide_profile.py` | 設定の一覧（手順0）。build.py からも `load_profile`・`author`・`deck_options` |
| `scripts/pdf_pages.py` | PDF のページ画像化（`extract`）と図の切り出し（`crop`） |
| `scripts/check_outline.py`・`check_memo.py` | 構成案・講座の設計メモの確認（話の筋・前の枚から・要点の出どころ・推論距離の手当て・確認問題のひもづけまで） |
| `scripts/scaffold.py`・`cards.py`・`excerpt.py` | 骨組みと枚ごとのカード、資料の抜き出し、書き手の parts を戻す `--merge` |
| `scripts/figkit.py`・`figlib.py`・`figgrid.py`・`catalog.py` | 図の共通設定と小道具・よく使う図の型・図の一覧画像・これまでの図のカタログ |
| `scripts/zemi.py` | build.py で使う `Deck`・`Slide`・`Eq`（部品の一覧はファイル冒頭） |
| `scripts/make_deck.py` | 図→組む→描く→検査を1回で（render_check.ps1・render_check_lo.py・check_layout.py・grid.py・check_notes.py をまとめて呼ぶ） |
| `scripts/notes_html.py`・`set_notes.py` | 原稿HTML・notes.md を発表者ノートに入れる |
| `scripts/budget.py` | 回数の予算：担当の起動と make_deck の回数、上限（オプション「回数の上限」「使用量の上限」） |
| `scripts/check_done.py` | 渡す前の確認（手順7）。最後に作った記録も残す（`build_log.py`：make_deck の回数と作り直した枚、`run_record.py`：会話ごとのモデル・思考の強さ・トークン → `<work>/run_record.md`） |
| `scripts/comments_read.py` | 原稿HTMLのコメントを読む（手順8） |
| `scripts/make_template.py`・`analyze_template.py`・`analyze_structure.py` | テンプレートを作る（`references/templates.md`） |
| `references/steps.md` | 手順0〜8の中身 |
| `references/story.md`・`structures.md`・`figures.md`・`style-guide.md` | 話の筋／本文の形と図解の型／図の作り方／書式と文章 |
| `references/outline-review.md`・`final-review.md` | 構成案のレビュー（推論距離）・完成後のレビュー（指摘の型） |
| `references/course.md`・`answer-deck.md`・`series.md`・`templates.md`・`agents.md` | 講座／質問回答／続きもの／テンプレート／道具の対応表と許可リスト |

依存：`<skill>/requirements.txt`。`No module named 'pptx'` などと出たら、`.venv` の Python でなく `python` のまま動かした可能性が高い。
`.venv` が無く部品が足りなければ、手順0のとおり聞いてから `.venv` を作って入れる（配布の一式なら、ユーザーが `.setup/準備.bat`・`.setup/準備.sh` を走らせても入る）。

## PowerPoint の決まり

- Windows 版 PowerPoint を使うのは `render_check.ps1`・`export_pdf.ps1`（と内部でそれを使う `notes_html.py`）だけ。画面に出さずに裏で使う。画面操作で開かない
- **PowerPoint が開けない（アクセス拒否 0x80070005 など）ときに、描画の検査や原稿HTMLを別の方法（自作の HTML・PIL の画像）で代えない。**
  サンドボックスで止められているなら、ユーザーの許可を得てサンドボックスの外で同じスクリプトを動かす（`references/agents.md`）。動かせないなら止めて伝える
- PowerPoint が無いとき（Mac・Linux など）だけ LibreOffice で代える（`render_check_lo.py`、原稿のページは `notes_html.py` が自動で）。最後は画像を目で見る
- PowerPoint も LibreOffice も無いときは、聞かずに `make_deck.py <work> --no-render` で pptx だけを作る（作る前に一言伝える）。
  渡すときに「描画の検査・原稿のページ・完成後の画像のレビューはしていない。LibreOffice（無料）を入れれば、あとから検査できる」とはっきり書く（このときだけ、check_done の描画・原稿のページ・レビューの ✘ は残ったままでよい。ほかの ✘ は直す）

## コマンドの書き方

エージェントの許可リストに当たるように、いつもこの形にそろえる（`references/agents.md`「許可リスト」）。
- スキルの部品は、作業ディレクトリ（スライドを作るフォルダの一番上）から `python <skill>/scripts/<名前>.py ...` で呼ぶ。
  `<skill>` は作業ディレクトリからの相対パス（例 `.agents/skills/sensei-slides`）で、区切りは `/`。フルパスにしない
- デッキごとの `figs.py`・`build.py` は、その作業フォルダ（`_work/<資料名>/`）に移ってから `python figs.py`・`python build.py` で動かす
- PowerShell の部品は `powershell -ExecutionPolicy Bypass -File <skill>/scripts/render_check.ps1 ...`（`export_pdf.ps1` も同じ形）
- **作業ディレクトリに `.venv` があれば、いつもその Python をパスで書く**（仮想環境が有効かどうかは確かめない）：Windows は `.venv/Scripts/python <skill>/scripts/<名前>.py ...`、
  Mac・Linux は `.venv/bin/python ...`。デッキの作業フォルダに移ったときは `../../.venv/Scripts/python figs.py`（Mac・Linux は `../../.venv/bin/python`）。`.venv` が無ければ `python` のまま
- 日本語を含む使い捨てのスクリプトは、ファイルに書いて `python -X utf8 <ファイル>` で動かす。ヒアドキュメント（`python - <<EOF`）で流さない
  （Windows では標準入力が cp932 で読まれて文字化けし、`\\n` も改行に化けて置換が当たらない）。改行や `\` を含む置換は【ファイルを書き換える】で行う

## 依頼の大きさで読む量を変える

| 依頼 | 読むもの | 省けるもの |
|---|---|---|
| **小さな依頼**：本文5枚以下、既存デッキの一部修正、図を1枚描き直すだけ | style-guide.md の 2・3節、figures.md の 1・2節だけ | 構成案のレビュー（手順2のチェックリストを自分で当てる）・話の筋の表・見本 |
| **大きな依頼**：節1つ分、論文1本分、それ以上 | 手順0〜8のそれぞれの節 | なし |

小さな依頼でも、**描画確認（手順5）、完成後のレビュー（手順5b）、原稿HTML（手順6）は省略しない**。

