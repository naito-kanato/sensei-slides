#!/bin/sh
# sensei-slides の準備：仮想環境 .venv を作って、スライド作りの部品を入れる（Mac・Linux）。
#   ターミナルでこのフォルダに移って  sh 準備.sh
cd "$(dirname "$0")" || exit 1
# uv が入っていれば uv で作る（速い。Python が無くても 3.12 を取ってくる）。無ければ下の python と pip で
if command -v uv >/dev/null 2>&1; then
  { [ -x .venv/bin/python ] || uv venv --seed --python 3.12 .venv; } &&
  uv pip install --python .venv/bin/python -q -r .agents/skills/sensei-slides/requirements.txt || {
    echo "部品を入れられませんでした。上のメッセージを確かめてください。"; exit 1; }
else
PY=$(command -v python3 || command -v python)
if [ -z "$PY" ] || ! "$PY" -c 'import sys; sys.exit(sys.version_info < (3, 10))' 2>/dev/null; then
  echo "Python 3.10 以上が見つかりませんでした（入っていないか、版が古い）。"
  if [ "$(uname)" = "Darwin" ] && command -v brew >/dev/null 2>&1; then
    printf "Homebrew で入れられます：brew install python@3.12。いま入れますか？ [y/N] "
    read -r ANS
    if [ "$ANS" = "y" ] || [ "$ANS" = "Y" ]; then brew install python@3.12 && echo "入れ終わったら、もう一度 sh 準備.sh を実行してください。"; exit 1; fi
  fi
  echo "https://www.python.org/downloads/ から入れて（Linux は sudo apt install python3 python3-venv など）、もう一度実行してください。"
  exit 1
fi
[ -x .venv/bin/python ] || "$PY" -m venv .venv || exit 1
.venv/bin/python -m pip install --disable-pip-version-check -q -r .agents/skills/sensei-slides/requirements.txt || {
  echo "部品を入れられませんでした。上のメッセージを確かめてください。"; exit 1; }
fi
echo
.venv/bin/python .agents/skills/sensei-slides/scripts/check_env.py
echo
echo "準備ができました。使い方は スキルの使い方.html（ブラウザで開く）。このフォルダを Codex・Claude Code・Antigravity・VS Code などで開いて、"
if [ "$(uname)" = "Darwin" ]; then open "スキルの使い方.html"; elif command -v xdg-open >/dev/null 2>&1; then xdg-open "スキルの使い方.html" >/dev/null 2>&1 & fi
echo "「〇〇の講座を作って」「〇〇.pdf のスライドを作って」と頼みます（くわしくは はじめに.md）。"
