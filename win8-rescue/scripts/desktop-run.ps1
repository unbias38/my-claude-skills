# 在目標電腦「使用者的桌面」執行 assets\desktop\ 裡的小程式（WinRM 本身碰不到桌面）
# 做法：把腳本用 base64 夾帶送到 <Workdir>\tools\，用排程器以登入使用者身分、互動模式執行，等它寫回結果檔
# 用法：desktop-run.ps1 -Target OLDPC -Script window.ps1 -Arguments @{ Action = 'maximize'; Match = 'Google' } -Title '放大 Chrome'
param(
  [Parameter(Mandatory)][string]$Target,
  [Parameter(Mandatory)][string]$Script,
  [hashtable]$Arguments = @{},
  [string]$Title = ''
)
$inner = [IO.File]::ReadAllText((Join-Path (Split-Path $PSScriptRoot) "assets\desktop\$Script"), [Text.Encoding]::UTF8)
$b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($inner))
$cfg = (Get-Content (Join-Path $env:USERPROFILE '.win8-rescue\targets.json') -Raw -Encoding UTF8 | ConvertFrom-Json).$Target
$argText = ($Arguments.GetEnumerator() | ForEach-Object { '-' + $_.Key + ' "' + ($_.Value -replace '"', '') + '"' }) -join ' '
$q = { param($s) "'" + ($s -replace "'", "''") + "'" }
$cmd = "`$name = $(& $q $Script); `$dir = $(& $q ($cfg.workdir + '\tools')); `$argText = $(& $q $argText)`r`n`$b64 = '$b64'`r`n" + @'
New-Item -ItemType Directory -Force $dir | Out-Null
$f = Join-Path $dir $name; $out = $f + '.result.txt'
[IO.File]::WriteAllText($f, [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($b64)), (New-Object Text.UTF8Encoding $true))
Remove-Item $out -ErrorAction SilentlyContinue
$user = (Get-WmiObject Win32_ComputerSystem).UserName
if (-not $user) { "沒有人登入，桌面不存在"; return }
$a = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument ('-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "' + $f + '" ' + $argText + ' -Out "' + $out + '"')
$p = New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive
Register-ScheduledTask -TaskName 'ClaudeDesktopRun' -Action $a -Principal $p -Force | Out-Null
Start-ScheduledTask -TaskName 'ClaudeDesktopRun'
$n = 0; while (-not (Test-Path $out) -and $n -lt 30) { Start-Sleep -Milliseconds 500; $n++ }
Unregister-ScheduledTask -TaskName 'ClaudeDesktopRun' -Confirm:$false
if (Test-Path $out) { Get-Content $out -Encoding UTF8 } else { "15 秒內沒有回報結果" }
'@
if (-not $Title) { $Title = "在桌面執行 $Script $argText" }
& (Join-Path $PSScriptRoot 'run.ps1') -Target $Target -Title $Title -Cmd $cmd
