#!/bin/sh
# sensei-slides の準備：仮想環境 .venv を作って、スライド作りの部品を入れる（Mac・Linux）。
#   ターミナルでこのフォルダに移って  sh はじめに.sh
cd "$(dirname "$0")" || exit 1
PY=$(command -v python3 || command -v python)
if [ -z "$PY" ]; then
  echo "Python 3.10 以上が見つかりませんでした。https://www.python.org/downloads/ から入れて、もう一度実行してください。"
  exit 1
fi
[ -x .venv/bin/python ] || "$PY" -m venv .venv || exit 1
.venv/bin/python -m pip install --disable-pip-version-check -q -r .agents/skills/sensei-slides/requirements.txt || {
  echo "部品を入れられませんでした。上のメッセージを確かめてください。"; exit 1; }
echo
.venv/bin/python .agents/skills/sensei-slides/scripts/check_env.py
echo
echo "準備ができました。このフォルダを Codex・Claude Code・Antigravity・VS Code などで開いて、"
echo "「〇〇の講座を作って」「〇〇.pdf のスライドを作って」と頼みます（くわしくは はじめに.md）。"
