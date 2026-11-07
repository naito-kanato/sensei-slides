@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo.
echo sensei-slides の準備をします。仮想環境 .venv を作って、スライド作りの部品を入れます（数分かかります）。
echo.
rem uv が入っていれば uv で作る（速い。Python が無くても 3.12 を取ってくる）。無ければ下の python と pip で
where uv > nul 2> nul
if errorlevel 1 goto findpy
if not exist ".venv\Scripts\python.exe" uv venv --seed --python 3.12 .venv
if not exist ".venv\Scripts\python.exe" goto findpy
uv pip install --python ".venv\Scripts\python.exe" -q -r ".agents\skills\sensei-slides\requirements.txt"
if errorlevel 1 goto pipfail
goto ready
:findpy
set "PY="
where py > nul 2> nul
if %errorlevel%==0 set "PY=py -3"
if not defined PY (
  where python > nul 2> nul
  if not errorlevel 1 set "PY=python"
)
if not defined PY goto nopython
%PY% -c "import sys; sys.exit(sys.version_info < (3, 10))" > nul 2> nul
if errorlevel 1 goto nopython
if exist ".venv\Scripts\python.exe" goto install
%PY% -m venv .venv
if errorlevel 1 goto nopython
:install
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -q -r ".agents\skills\sensei-slides\requirements.txt"
if errorlevel 1 goto pipfail
:ready
echo.
".venv\Scripts\python.exe" ".agents\skills\sensei-slides\scripts\check_env.py"
echo.
echo 準備ができました。使い方のページ（スキルの使い方.html）をブラウザで開きます。
start "" "スキルの使い方.html"
echo このフォルダを Codex・Claude Code・Antigravity・VS Code などで開いて、
echo 「〇〇の講座を作って」「〇〇.pdf のスライドを作って」と頼みます（くわしくは はじめに.md）。
echo.
pause
exit /b 0
:nopython
echo Python 3.10 以上が見つかりませんでした（入っていない・版が古い・Microsoft Store の入口だけ、のどれか）。
where winget > nul 2> nul
if errorlevel 1 goto manualpy
echo.
echo winget で Python 3.12 を入れられます：winget install -e --id Python.Python.3.12
set /p ANS=いま入れますか？ [y/N] 
if /i not "%ANS%"=="y" goto manualpy
winget install -e --id Python.Python.3.12
echo.
echo 入れ終わったら、この窓を閉じて、もう一度 はじめに.bat をダブルクリックしてください。
pause
exit /b 1
:manualpy
echo https://www.python.org/downloads/ から入れて（入れるときに「Add python.exe to PATH」に印を付ける）、
echo もう一度 はじめに.bat をダブルクリックしてください。
pause
exit /b 1
:pipfail
echo 部品を入れられませんでした。上のメッセージを確かめて、ネットにつながっているかを見てから、もう一度ダブルクリックしてください。
pause
exit /b 1
