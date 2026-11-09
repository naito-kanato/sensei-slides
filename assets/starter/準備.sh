#!/bin/sh
# sensei-slides の準備：仮想環境 .venv を作って、スライド作りの部品を入れる（Mac・Linux）。
#   ターミナルで一式のフォルダに移って  sh .setup/準備.sh
cd "$(dirname "$0")/.." || exit 1
REQ=.agents/skills/sensei-slides/requirements.txt
ok_py() { "$1" -c 'import sys; sys.exit(sys.version_info < (3, 10))' 2>/dev/null; }

# 前に作った .venv が古い Python（3.10 未満）なら作り直す
if [ -x .venv/bin/python ] && ! ok_py .venv/bin/python; then
  echo "前に作った .venv の Python が古いので、作り直します。"
  rm -rf .venv
fi

# uv が入っていれば uv で作る（速い。Python が無くても 3.12 を取ってくる）。うまくいかなければ下の python と pip で
DONE=
if command -v uv >/dev/null 2>&1; then
  { [ -x .venv/bin/python ] || uv venv --seed --python 3.12 .venv; } &&
    uv pip install --python .venv/bin/python -q -r "$REQ" && DONE=1
fi

if [ -z "$DONE" ]; then
  # 新しい版から探す（Mac は /usr/bin/python3 が古い 3.9 のことがあり、Homebrew の python3.12 などを先に使う）
  PY=
  for c in python3.13 python3.12 python3.11 python3.10 python3 python; do
    p=$(command -v "$c" 2>/dev/null) || continue
    if ok_py "$p"; then PY=$p; break; fi
  done
  if [ -z "$PY" ]; then
    echo "Python 3.10 以上が見つかりませんでした（入っていないか、版が古い）。"
    if [ "$(uname)" = "Darwin" ] && command -v brew >/dev/null 2>&1; then
      printf "Homebrew で入れられます：brew install python@3.12。いま入れますか？ [y/N] "
      read -r ANS
      if [ "$ANS" = "y" ] || [ "$ANS" = "Y" ]; then
        brew install python@3.12 && echo "入れ終わりました。もう一度 sh .setup/準備.sh を実行してください。"
        exit 1
      fi
    fi
    echo "https://www.python.org/downloads/ から入れて（Linux は sudo apt install python3 python3-venv など）、もう一度実行してください。"
    exit 1
  fi
  if [ ! -x .venv/bin/python ]; then
    "$PY" -m venv .venv || {
      echo "仮想環境を作れませんでした。Linux（Debian・Ubuntu）なら sudo apt install python3-venv を入れてから、もう一度実行してください。"
      rm -rf .venv; exit 1; }
  fi
  .venv/bin/python -m pip install --disable-pip-version-check -q -r "$REQ" || {
    echo "部品を入れられませんでした。上のメッセージを確かめて、ネットにつながっているかを見てから、もう一度実行してください。"; exit 1; }
fi
echo
.venv/bin/python .agents/skills/sensei-slides/scripts/check_env.py
echo
echo "準備ができました。使い方は スキルの使い方.html（ブラウザで開く）。このフォルダを Codex・Claude Code・Antigravity・VS Code などで開いて、"
if [ "$(uname)" = "Darwin" ]; then open "スキルの使い方.html"; elif command -v xdg-open >/dev/null 2>&1; then xdg-open "スキルの使い方.html" >/dev/null 2>&1 & fi
echo "「〇〇の講座を作って」「〇〇.pdf のスライドを作って」と頼みます（くわしくは スキルの使い方.html）。"
