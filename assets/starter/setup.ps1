# sensei-slides の準備（Windows）：仮想環境 .venv を作って、スライド作りの部品を入れる。準備.bat がこれを呼ぶ。
# 日本語の表示は、このファイル（UTF-8・BOM 付き）で行う。bat に日本語を書くと、chcp 65001 のあと cmd が行を読み違えて動かなかった。
# 環境変数 SENSEI_SETUP_QUIET=1 なら、使い方のページを開かず、最後に Enter を待たない（試しのとき）。
$ErrorActionPreference = "Continue"
# Python（-X utf8）の出力を UTF-8 として読む（既定の cp932 だと、check_env の表示が化けた）
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
Set-Location (Split-Path -Parent $PSScriptRoot)
$req = ".agents\skills\sensei-slides\requirements.txt"
$venvPy = ".venv\Scripts\python.exe"
$quiet = $env:SENSEI_SETUP_QUIET -eq "1"

function Finish([int]$code) {
    if (-not $quiet) { Read-Host "Enter キーで閉じます" | Out-Null }
    exit $code
}

function Test-Py([string[]]$cmd) {
    # 3.10 以上の Python なら $true（Microsoft Store の入口だけの python.exe は、ここで落ちる）
    try {
        $exe = $cmd[0]; $rest = @(); if ($cmd.Count -gt 1) { $rest = $cmd[1..($cmd.Count - 1)] }
        & $exe @rest -c "import sys; sys.exit(sys.version_info < (3, 10))" 2>$null | Out-Null
        return ($LASTEXITCODE -eq 0)
    } catch { return $false }
}

Write-Host ""
Write-Host "sensei-slides の準備をします。仮想環境 .venv を作って、スライド作りの部品を入れます（数分かかります）。"
Write-Host ""

# 前に作った .venv の Python が古い（3.10 未満）なら作り直す
if ((Test-Path $venvPy) -and -not (Test-Py @($venvPy))) {
    Write-Host "前に作った .venv の Python が古いので、作り直します。"
    Remove-Item -Recurse -Force .venv
}

# uv が入っていれば uv で作る（速い。Python が無くても 3.12 を取ってくる）。うまくいかなければ下の python と pip で
$done = $false
if (Get-Command uv -ErrorAction SilentlyContinue) {
    if (-not (Test-Path $venvPy)) { & uv venv --seed --python 3.12 .venv }
    if (Test-Path $venvPy) {
        & uv pip install --python $venvPy -q -r $req
        if ($LASTEXITCODE -eq 0) { $done = $true }
    }
}

if (-not $done) {
    # py があれば 3.13・3.12・3.11・3.10 の順に探す（py -3 は一番新しい版になり、部品がまだ無い版のことがある）
    $py = $null
    if (Get-Command py -ErrorAction SilentlyContinue) {
        foreach ($v in "3.13", "3.12", "3.11", "3.10") {
            if (Test-Py @("py", "-$v")) { $py = @("py", "-$v"); break }
        }
        if (-not $py -and (Test-Py @("py", "-3"))) { $py = @("py", "-3") }
    }
    if (-not $py) {
        foreach ($n in "python", "python3") {
            if ((Get-Command $n -ErrorAction SilentlyContinue) -and (Test-Py @($n))) { $py = @($n); break }
        }
    }
    if (-not $py) {
        Write-Host "Python 3.10 以上が見つかりませんでした（入っていない・版が古い・Microsoft Store の入口だけ、のどれか）。"
        if (Get-Command winget -ErrorAction SilentlyContinue) {
            Write-Host ""
            Write-Host "winget で Python 3.12 を入れられます：winget install -e --id Python.Python.3.12"
            if (-not $quiet) {
                $ans = Read-Host "いま入れますか？ [y/N]"
                if ($ans -match "^[yY]") {
                    & winget install -e --id Python.Python.3.12
                    Write-Host ""
                    Write-Host "入れ終わったら、この窓を閉じて、もう一度 準備.bat をダブルクリックしてください。"
                    Finish 1
                }
            }
        }
        Write-Host "https://www.python.org/downloads/ から入れて（入れるときに「Add python.exe to PATH」に印を付ける）、もう一度 準備.bat をダブルクリックしてください。"
        Finish 1
    }
    if (-not (Test-Path $venvPy)) {
        $exe = $py[0]; $rest = @(); if ($py.Count -gt 1) { $rest = $py[1..($py.Count - 1)] }
        & $exe @rest -m venv .venv
        if (-not (Test-Path $venvPy)) {
            Write-Host "仮想環境 .venv を作れませんでした。上のメッセージを確かめてください。"
            Finish 1
        }
    }
    & $venvPy -m pip install --disable-pip-version-check -q -r $req
    if ($LASTEXITCODE -ne 0) {
        Write-Host "部品を入れられませんでした。上のメッセージを確かめて、ネットにつながっているかを見てから、もう一度ダブルクリックしてください。"
        Finish 1
    }
}

Write-Host ""
& $venvPy -X utf8 ".agents\skills\sensei-slides\scripts\check_env.py"
Write-Host ""
Write-Host "準備ができました。使い方のページ（スキルの使い方.html）をブラウザで開きます。"
if (-not $quiet) { Start-Process "スキルの使い方.html" }
Write-Host "このフォルダを Codex・Claude Code・Antigravity・VS Code などで開いて、"
Write-Host "「〇〇の講座を作って」「〇〇.pdf のスライドを作って」と頼みます（くわしくは スキルの使い方.html）。"
Write-Host ""
Finish 0
