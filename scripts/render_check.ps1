# PowerPoint 本体で .pptx を開き、各スライドを PNG に書き出すと同時に、
# 全図形の位置と「実際に描画された文字の範囲」を shapes.json に保存する。
# check_layout.py がこの JSON を読んで、はみ出し・重なり・青帯への侵入・タイトルの折り返しを検出する。
#
#   powershell -ExecutionPolicy Bypass -File render_check.ps1 -Pptx deck.pptx -OutDir render
#   （-NoImages で PNG を省略、-Width で画像幅px）
param(
  [Parameter(Mandatory = $true)][string]$Pptx,
  [Parameter(Mandatory = $true)][string]$OutDir,
  [int]$Width = 1600,
  [switch]$NoImages
)
$ErrorActionPreference = "Stop"
$Pptx = (Resolve-Path $Pptx).Path
New-Item -ItemType Directory -Force $OutDir | Out-Null
$OutDir = (Resolve-Path $OutDir).Path
Get-ChildItem $OutDir -Filter "slide-*.png" -ErrorAction SilentlyContinue | Remove-Item -Force

# OneDrive / SharePoint 上の pptx をそのまま開くと、PowerPoint がクラウドのキャッシュ（作り直す前の古い版）を
# 開くことがある（過去の論文紹介で、描画結果と原稿HTMLの画像が1つ前の build のままだった）。
# 毎回、一時フォルダに別名で複製してから開く。
$Copy = Join-Path ([System.IO.Path]::GetTempPath()) ("render_" + [guid]::NewGuid().ToString("N") + ".pptx")
Copy-Item -LiteralPath $Pptx -Destination $Copy -Force

$app = New-Object -ComObject PowerPoint.Application
$pres = $null
try {
  # ReadOnly, Untitled=false, WithWindow=false
  $pres = $app.Presentations.Open($Copy, $true, $false, $false)
  $W = $pres.PageSetup.SlideWidth
  $H = $pres.PageSetup.SlideHeight
  $rows = New-Object System.Collections.ArrayList
  $i = 0
  foreach ($s in $pres.Slides) {
    $i++
    if (-not $NoImages) {
      $s.Export((Join-Path $OutDir ("slide-{0:D2}.png" -f $i)), "PNG", $Width, [int]($Width * $H / $W))
    }
    foreach ($sh in $s.Shapes) {
      $o = [ordered]@{
        slide = $i; name = $sh.Name; type = [int]$sh.Type
        left = [double]$sh.Left; top = [double]$sh.Top; width = [double]$sh.Width; height = [double]$sh.Height
        ph = $null; text = ""; tl = $null; tt = $null; tw = $null; th = $null; lines = 0; paras = 0; size = $null
      }
      try { if ($sh.Type -eq 14) { $o.ph = [int]$sh.PlaceholderFormat.Type } } catch {}
      try {
        if ($sh.HasTextFrame -and $sh.TextFrame.HasText) {
          $tr = $sh.TextFrame.TextRange
          $o.text = [string]$tr.Text
          $o.tl = [double]$tr.BoundLeft; $o.tt = [double]$tr.BoundTop
          $o.tw = [double]$tr.BoundWidth; $o.th = [double]$tr.BoundHeight
          $o.lines = [int]$tr.Lines().Count
          $o.paras = [int]$tr.Paragraphs().Count
          try { $o.size = [double]$tr.Runs(1).Font.Size } catch {}
        }
      } catch {}
      [void]$rows.Add((New-Object PSObject -Property $o))
    }
  }
  $json = [ordered]@{ pptx = $Pptx; slideWidth = $W; slideHeight = $H; slides = $i; shapes = $rows } | ConvertTo-Json -Depth 4
  [System.IO.File]::WriteAllText((Join-Path $OutDir "shapes.json"), $json, (New-Object System.Text.UTF8Encoding $false))
  Write-Output "rendered $i slides -> $OutDir"
} finally {
  # Close が失敗しても（ダイアログ表示中など）Quit と複製の削除まで進める。開いたままの PowerPoint が残ると、次の実行が失敗する
  try { if ($pres -ne $null) { $pres.Close() } } catch { Write-Warning "Close に失敗: $($_.Exception.Message)" }
  try { if ($app.Presentations.Count -eq 0) { $app.Quit() } } catch {}
  [System.Runtime.InteropServices.Marshal]::ReleaseComObject($app) | Out-Null
  Remove-Item -LiteralPath $Copy -Force -ErrorAction SilentlyContinue
}
