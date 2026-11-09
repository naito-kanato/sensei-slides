# 道具とモデルの対応表（どのエージェントでも使えるように）

手順書（SKILL.md と references/）は、特定のエージェントに頼らない**中立の言葉**（【】で囲んだ言葉）で書いてある。
使っているエージェントの列を見て、それぞれの言葉を実際の道具・モデルに読み替えてから手順を進める。手順そのもの
（構成案 → 図 → ビルド → 描画確認 → レビュー → 原稿HTML → 渡す前の確認）は、どのエージェントでも変えない。

**ユーザーが使うモデル・道具を言ったときは（「レビューは〇〇で」「別のエージェントは使わない」）、そちらを、この表より優先する。**

## 道具

| 中立の言葉 | 何をするか | Codex | Claude Code | Antigravity | GitHub Copilot（CLI） |
|---|---|---|---|---|---|
| 【質問】 | 選択肢をボタンで示して、ユーザーに1回だけ聞く（**1回に3問・各3択まで**。「その他」の自由記入はどの道具でも付く） | request_user_input（Plan モードだけ。ふつうのモードは request_user_input_async：答えは次のメッセージで届く） | AskUserQuestion | ask_question（1問ずつなら、続けて聞く） | ask_user |
| 【別のエージェント】 | 構成案・設計メモ・完成品のレビューと、スライドの制作（手順3〜6）を、別のエージェントにさせる。**空の会話から始め**、渡すのはファイルの場所と頼むことだけ | spawn_agent（**`fork_turns: "none"`**。省くと親の会話をまるごと写して始まり、その分ずっと重くなる。モデルを指定できる。終わりは wait_agent で待つ。**`timeout_ms` は長く（600000 など）し、時間切れなら待ち直す**。短い待ちを数回で切り上げて応答を終えない） | Agent ツール（新しい会話で始まる。モデルを指定。レビューはバックグラウンドで） | invoke_subagent（`Model` でモデルを指定。既定は親と同じ） | task（`mode` を background に。結果は read_agent で読む） |
| 【続けて頼む】 | 先読みさせたレビュー担当に続けてレビューを、講座の設計の担当に続けて直しを頼む | followup_task（起動したときの名前に送る） | SendMessage（起動したときの ID に送る） | send_message | write_agent（起動したときの ID に送る） |
| 【画像を見る】 | 描画したスライドの PNG・資料のページ画像を目で確かめる | view_image | Read | read_file（PNG も読める） | view（PNG も読める） |
| 【ファイルを書き換える】 | 改行や `\` を含む文字列を、ファイルの中で正確に置き換える | apply_patch | Edit ツール | edit_file（新しく作るなら write_file） | apply_patch |
| （シェル） | コマンドを実行する | exec_command | Bash / PowerShell | run_command | powershell |

表の道具の名前は、それぞれのツールでこのスキルを試したときの記録から取った。道具の名前はツールの版で変わることがある。名前が違っても、同じ働きの道具を使う。
どのエージェントでも、モデルが分からなければユーザーに聞く。`render_check.ps1`・`export_pdf.ps1` は、どのエージェントでも Windows の PowerShell で動かす。

**PowerPoint を使うスクリプト（`render_check.ps1`・`export_pdf.ps1`・`notes_html.py`・`make_deck.py`）は、サンドボックスの中では止められることがある**（PowerPoint が無い PC では、代わりに LibreOffice 版の `render_check_lo.py` を使う。references/tools.md「PowerPoint の決まり」）（Codex では「Retrieving the COM class factory … 80070005 Access is denied」）。Codex なら exec_command に `sandbox_permissions: "require_escalated"` を付けて、ユーザーの許可を得てサンドボックスの外で動かす（試験ではこれで通った）。毎回の許可を省くには、同梱の `assets/codex/sensei-slides.rules` を、スライドを作るフォルダの `.codex/rules/` に置いてもらう（Codex がそのフォルダを信頼しているときに読む。この3つのスクリプトだけを、確認なしでサンドボックスの外で動かす決まり）。止められても、自作の HTML や別の描き方で代えない（SKILL.md）。また、画面操作の機能（Codex の Computer Use など）で PowerPoint を開かない。サンドボックスの外での実行は、画面は変わらず、コマンドの許可を求める確認が出るだけ。

**表にないツール（VS Code の Copilot など）**では、同じ働きの道具を探して使う。無いときは次のようにする。
- 【質問】：チャットに問いと選択肢を番号つきで並べて（「1-a, 2-c のように答えてください」）、答えを待つ
- 【別のエージェント】：下の「別のエージェントが無いとき」
- 【続けて頼む】：レビューのたびに資料と観点を渡し直す（先読みは省く）
- 【画像を見る】：画像を読めないなら、ユーザーに `render/` の画像を見てもらい、気になる所を言ってもらう
- 【ファイルを書き換える】：ファイルを書き換える道具を使う。シェルのヒアドキュメントで置換しない（改行と日本語が壊れやすい。references/tools.md「コマンドの書き方」）

## モデル

決まりは SKILL.md「必ず守る」（メインのモデルで全部。【別のエージェント】にモデルを指定しない）。ここには道具ごとの注意だけを置く。
- **軽量モデル（例：Codex・GitHub Copilot の GPT-6 Luna）は非推奨（使うことはできる）。** 試したところ、手順は最後まで進められたが、図の中身が薄く、
  資料にない仕組みを簡単にしすぎることがあった。軽いモデルで作るときは、ユーザーに図と事実の確認を頼む

## 別のエージェントが無いとき

制作役と仕上げ役（手順3〜6）は、空の会話から始められないなら、段階ごとに会話を分ける（SKILL.md「1人で回すとき」）。
Codex の Web 検索（web__run）は、`response_length` を短くして、要る所だけ開く。

レビューは、作った本人とは別の目で見ることに意味がある（作った本人は自分の粗が見えない）。【別のエージェント】が使えないときは、次のどちらかにする。

1. **別の会話でレビューする（おすすめ）**：ユーザーに新しい会話を開いてもらい、`references/outline-review.md` か `references/final-review.md` のプロンプトの雛形と、
   見てほしいファイルの場所を貼ってもらう。返ってきた指摘を、この会話に貼ってもらって直す
2. **自分で見直す**：作業の区切りで、雛形の観点を1つずつ当てて読み直す。構成案なら「青帯だけを上から読む」、完成品なら全スライドの画像を順に見る。
   別の目ほど確かではないので、ユーザーに渡すときに「レビューは自分で見直した」と伝える

## スキルを書き換えさせない（任意）

エージェントはスキルの部品を書き換えない決まり（SKILL.md）で、渡す前の確認（`check_done.py`）が部品の指紋（`scripts/MANIFEST.txt`）と照合する。書き換えをはじめから止めたいときは、次のどちらかをする。

- **ファイルを読み取り専用にする**（どのエージェントでも効く）：Windows なら、スキルのフォルダで `attrib +R /S *`。スキルを入れ替えるときは `attrib -R /S *` で戻してから入れ替える
- **Claude Code**：`.claude/settings.json` の `permissions.deny` に `"Edit(.claude/skills/sensei-slides/**)"` と `"Write(.claude/skills/sensei-slides/**)"` を足す

## 許可リスト（コマンドを確認なしで動かしたいとき）

エージェントの設定でコマンドの許可リスト（Allow list）を使うときは、次の頭の部分を登録する。スキルを `.agents/skills/sensei-slides/` に置いた場合の書き方で、
ほかの場所に置いたときは `<skill>` の部分をその場所に変える。手順書はコマンドをこの形にそろえるよう指示している（references/tools.md「コマンドの書き方」）。

```
.venv/Scripts/python .agents/skills/sensei-slides/scripts/
../../.venv/Scripts/python figs.py
../../.venv/Scripts/python build.py
python .agents/skills/sensei-slides/scripts/
powershell -ExecutionPolicy Bypass -File .agents/skills/sensei-slides/scripts/render_check.ps1
powershell -ExecutionPolicy Bypass -File .agents/skills/sensei-slides/scripts/export_pdf.ps1
python figs.py
python build.py
python -X utf8 figs.py
python -X utf8 build.py
```

- 上の3行は、作業フォルダに `.venv` があるとき（配布の一式）の形。Mac・Linux は `Scripts` を `bin` に。`.venv` が無いときは `python` で始まる行が当たる
- `.../scripts/` で終わる行で、スキルの Python の部品（`check_layout.py`・`notes_html.py`・`pdf_pages.py` など）がまとめて通る
- `python` だけ・`powershell` だけは登録しない（どんなプログラムでも確認なしで動くようになる）。`pip install` も、最初の1回だけなので毎回確かめる
- Codex の決まり（`.codex/rules/sensei-slides.rules`）は、`python` で始まる形と `.venv` の Python で始まる形の両方を許す
- 描画の検査と原稿のページづくりは、一時フォルダ（Windows の `%TEMP%`）に pptx の複製と PDF を書く。作業フォルダの外のファイルへのアクセスを確かめる設定があるツールでは、そこでも確認が出る
- エージェントが書き方を変えて（フルパス、`\` の区切りなど）確認が出たときは、内容がこのスキルの作業なら許可してよい

## 置き場所

スキルは「フォルダの中に SKILL.md」という形（Agent Skills）なので、ツールごとの場所にこのフォルダを `sensei-slides` という名前で置く。
フォルダ名と SKILL.md の `name` が違うと読み込まれないツールがある。

| ツール | プロジェクトの場所 | 個人の場所 |
|---|---|---|
| Codex | `.agents/skills/sensei-slides/` | `~/.agents/skills/sensei-slides/` |
| Claude Code | `.claude/skills/sensei-slides/` | `~/.claude/skills/sensei-slides/` |
| Antigravity | `.agents/skills/sensei-slides/`（これで試した） | — |
| GitHub Copilot | `.github/skills/sensei-slides/`（CLI はこれで試した。VS Code なら `.agents/skills/`・`.claude/skills/` も可） | `~/.copilot/skills/sensei-slides/` |

`.agents/skills/` に置くと、Codex・Antigravity と、VS Code の Copilot（ローカルのエージェント）から読める。
Copilot CLI やクラウドのエージェントで使うなら `.github/skills/` に置く。

## 会話の記録（レビューの担当の確かめ）

渡す前の確認（`check_done.py`）は、レビューを別の担当がしたかを、道具が残す会話の記録で確かめる（`scripts/review_record.py`）。記録の形は公開された仕様ではないので、変わったら「記録なし」（△）になる。

| エージェント | 読む記録 | 担当の見分け方 |
|---|---|---|
| Claude Code | `~/.claude/projects/<始めたフォルダ>/`（`CLAUDE_CONFIG_DIR` があればその下） | `<会話>/subagents/agent-*.jsonl` が担当 |
| Codex | `~/.codex/sessions/`（`CODEX_HOME` があればその下） | 冒頭の `thread_source` が `subagent`（許可の審査 `guardian_review` は数えない） |
| Antigravity・GitHub Copilot | 読まない | △（確かめられない）。review.md の冒頭に担当とモデルを書く |
