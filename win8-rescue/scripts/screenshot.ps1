# 拍目標電腦的螢幕，傳回主控機，印出本機圖檔路徑（Claude 再用 Read 讀圖）
# 截圖會拍到螢幕上的所有東西：只在使用者要求、或為了排解他提到的畫面問題時才拍，並告訴他拍了
# 用法：screenshot.ps1 -Target OLDPC [-MaxWidth 1600]
param([Parameter(Mandatory)][string]$Target, [int]$MaxWidth = 1600)
$r = & (Join-Path $PSScriptRoot 'desktop-run.ps1') -Target $Target -Script 'screenshot.ps1' -Arguments @{ MaxWidth = "$MaxWidth" } -Title '拍螢幕截圖給 Claude 看'
$r
# 結果檔第一行可能帶 BOM（﻿），所以不用 ^ 錨定，整段一起比對
$m = [regex]::Match(($r -join "`n"), 'FILE=([^\r\n]+)')
$remote = if ($m.Success) { $m.Groups[1].Value.Trim() } else { $null }
if (-not $remote) { Write-Host '沒有拿到截圖檔' -ForegroundColor Red; return }
$cfg = (Get-Content (Join-Path $env:USERPROFILE '.win8-rescue\targets.json') -Raw -Encoding UTF8 | ConvertFrom-Json).$Target
$b64 = Invoke-Command -ComputerName $cfg.ip -Credential (Import-Clixml $cfg.cred) -ArgumentList $remote -ScriptBlock {
  param($f) $s = [Convert]::ToBase64String([IO.File]::ReadAllBytes($f)); Remove-Item $f -Force; $s }   # 傳回後刪除，不在目標留下截圖
$dir = Join-Path $env:USERPROFILE ".win8-rescue\shots"; New-Item -ItemType Directory -Force $dir | Out-Null
$local = Join-Path $dir ("{0}_{1:yyyyMMdd_HHmmss}.jpg" -f $Target, (Get-Date))
[IO.File]::WriteAllBytes($local, [Convert]::FromBase64String($b64))
"LOCAL=$local"
