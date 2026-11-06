# PowerPoint 本体で .pptx を PDF に書き出す（見た目はスライドと同じ、フォント埋め込み・文字検索可）。
# 手順の最後、render_check.ps1 / check_layout.py で ERROR 0 を確認してから実行する。
#
#   powershell -ExecutionPolicy Bypass -File export_pdf.ps1 -Pptx deck.pptx            # 同じ場所に deck.pdf
#   powershell -ExecutionPolicy Bypass -File export_pdf.ps1 -Pptx deck.pptx -Pdf out.pdf
param(
  [Parameter(Mandatory = $true)][string]$Pptx,
  [string]$Pdf = ""
)
$ErrorActionPreference = "Stop"
$Pptx = (Resolve-Path $Pptx).Path
if ($Pdf -eq "") { $Pdf = [System.IO.Path]::ChangeExtension($Pptx, ".pdf") }
$Pdf = [System.IO.Path]::GetFullPath($Pdf)

# OneDrive 上の pptx は PowerPoint がクラウドの古い版を開くことがあるので、一時フォルダの複製から書き出す（render_check.ps1 と同じ）
$Copy = Join-Path ([System.IO.Path]::GetTempPath()) ("export_" + [guid]::NewGuid().ToString("N") + ".pptx")
Copy-Item -LiteralPath $Pptx -Destination $Copy -Force

$app = New-Object -ComObject PowerPoint.Application
$pres = $null
try {
  $pres = $app.Presentations.Open($Copy, $true, $false, $false)  # ReadOnly, Untitled=false, WithWindow=false
  $pres.SaveAs($Pdf, 32)  # 32 = ppSaveAsPDF
  $n = $pres.Slides.Count
  Write-Output "saved $Pdf ($n pages)"
} finally {
  # Close が失敗しても（ダイアログ表示中など）Quit と複製の削除まで進める。開いたままの PowerPoint が残ると、次の実行が失敗する
  try { if ($pres -ne $null) { $pres.Close() } } catch { Write-Warning "Close に失敗: $($_.Exception.Message)" }
  try { if ($app.Presentations.Count -eq 0) { $app.Quit() } } catch {}
  [System.Runtime.InteropServices.Marshal]::ReleaseComObject($app) | Out-Null
  Remove-Item -LiteralPath $Copy -Force -ErrorAction SilentlyContinue
}
