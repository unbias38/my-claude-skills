# 關掉目標電腦桌面上，「目前顯示的分頁」標題含某個字的 Chrome 分頁（例如 YouTube）。標題不符時不動作，視窗大小不變
# 用法：close-tab.ps1 -Target OLDPC -Match YouTube
param([Parameter(Mandatory)][string]$Target, [string]$Match = 'YouTube')
& (Join-Path $PSScriptRoot 'desktop-run.ps1') -Target $Target -Script 'window.ps1' -Arguments @{ Action = 'close-tab'; Match = $Match } -Title "關掉 Chrome 分頁：$Match"
