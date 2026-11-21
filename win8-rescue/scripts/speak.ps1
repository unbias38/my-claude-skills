# 讓目標電腦用內建語音念出一段文字（預設台灣中文 Hanhan）
# 用法：speak.ps1 -Target OLDPC -Text '今天台中晴天，最高二十二度' [-Voice zh-TW] [-Rate 0]
# 念的時間超過 15 秒時，desktop-run 可能先回報「沒有回報結果」，但聲音會繼續念完；長文請拆段
param([Parameter(Mandatory)][string]$Target, [Parameter(Mandatory)][string]$Text, [string]$Voice = 'zh-TW', [int]$Rate = 0)
$b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($Text))
$short = if ($Text.Length -gt 30) { $Text.Substring(0, 30) + '…' } else { $Text }
& (Join-Path $PSScriptRoot 'desktop-run.ps1') -Target $Target -Script 'speak.ps1' -Arguments @{ TextB64 = $b64; Voice = $Voice; Rate = "$Rate" } -Title "讓電腦說話：$short"
