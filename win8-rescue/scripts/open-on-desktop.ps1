# 在目標電腦「使用者看得到的桌面」打開網址、程式或檔案
# WinRM 在背景工作階段（session 0）執行，直接 Start-Process 開的視窗使用者看不到，
# 所以借用工作排程器，以登入使用者的身分、互動模式執行一次，執行完就刪掉排程。
# 用法：
#   open-on-desktop.ps1 -Target OLDPC -Url 'https://www.google.com.tw'
#   open-on-desktop.ps1 -Target OLDPC -Search '台北 天氣'          # 用 Google 搜尋結果網址
#   open-on-desktop.ps1 -Target OLDPC -Exe 'notepad.exe' -Arguments 'D:\a.txt'
param(
  [Parameter(Mandatory)][string]$Target,
  [string]$Url,
  [string]$Search,
  [string]$Exe,
  [string]$Arguments = '',
  [switch]$Maximize
)
if ($Search) { $Url = 'https://www.google.com.tw/search?q=' + [Uri]::EscapeDataString($Search) }
if (-not $Url -and -not $Exe) { throw '請提供 -Url、-Search 或 -Exe' }
$title = if ($Exe) { "在桌面開啟 $Exe $Arguments" } elseif ($Search) { "在桌面用 Chrome 搜尋：$Search" } else { "在桌面用 Chrome 打開 $Url" }
# 把參數放進指令開頭（單引號跳脫），讓 run.ps1 照常記錄
function Q($s) { "'" + ($s -replace "'", "''") + "'" }
$cmd = "`$url = $(Q $Url); `$exe = $(Q $Exe); `$arg = $(Q $Arguments)`r`n" + @'
if (-not $exe) {
  $exe = (Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe' -ErrorAction SilentlyContinue).'(default)'
  if (-not $exe) { $exe = (Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe' -ErrorAction SilentlyContinue).'(default)' }
  if (-not $exe) { "找不到 Chrome 或 Edge"; return }
  $arg = $url
}
$user = (Get-WmiObject Win32_ComputerSystem).UserName
if (-not $user) { "沒有人登入，桌面還不存在，無法開視窗"; return }
$tn = 'ClaudeOpenOnDesktop'
$a = if ($arg) { New-ScheduledTaskAction -Execute $exe -Argument $arg } else { New-ScheduledTaskAction -Execute $exe }
$p = New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive
Register-ScheduledTask -TaskName $tn -Action $a -Principal $p -Force | Out-Null
Start-ScheduledTask -TaskName $tn
Start-Sleep 3
$i = Get-ScheduledTaskInfo -TaskName $tn
Unregister-ScheduledTask -TaskName $tn -Confirm:$false
# 0 = 已執行完（例如 Chrome 把網址交給已開的視窗後就結束）；267009 (0x41301) = 程式還開著，也是成功
# 刪除排程不會關掉已經開啟的程式
if ($i.LastTaskResult -eq 0 -or $i.LastTaskResult -eq 267009) { "已在 $user 的桌面開啟：$exe $arg" } else { "執行失敗，結果碼 $($i.LastTaskResult)" }
'@
$r = & (Join-Path $PSScriptRoot 'run.ps1') -Target $Target -Title $title -Cmd $cmd
$r
# 背景啟動的程式只會在工作列閃，不會自己跳到前面：再用 window.ps1 帶到前景（-Maximize 則放大）
if ($r -match '^已在') {
  $proc = if ($Exe) { ([IO.Path]::GetFileNameWithoutExtension($Exe) -replace 'Portable$', '') + '*' } else { 'chrome' }
  $act = if ($Maximize) { 'maximize' } else { 'front' }
  $wargs = @{ Action = $act; Process = $proc }
  if ($Exe) { $wargs.Recent = '1' }
  & (Join-Path $PSScriptRoot 'desktop-run.ps1') -Target $Target -Script 'window.ps1' -Arguments $wargs -Title '把剛開的視窗帶到前景'
}
