# 在使用者桌面的工作階段執行（由 desktop-run.ps1 透過排程器啟動）
# 對「目前分頁標題含 $Match」的 Chrome 視窗（或任何程式視窗，見 $Process）做動作：
#   close-tab：帶到前景後送 Ctrl+W（只關目前顯示的分頁）
#   maximize／minimize／front：放大、縮到工作列、只帶到前景
# 帶到前景時不改變視窗大小：只有被縮到工作列時才還原（SW_RESTORE 會把最大化的視窗變回一般大小）
param([string]$Action = 'front', [string]$Match = '', [string]$Process = 'chrome', [string]$Out, [string]$Recent = '')
Add-Type -Namespace U -Name W -MemberDefinition @'
[DllImport("user32.dll")] public static extern bool SetForegroundWindow(System.IntPtr h);
[DllImport("user32.dll")] public static extern bool ShowWindow(System.IntPtr h, int c);
[DllImport("user32.dll")] public static extern bool IsIconic(System.IntPtr h);
[DllImport("user32.dll")] public static extern bool IsZoomed(System.IntPtr h);
[DllImport("user32.dll")] public static extern void keybd_event(byte vk, byte scan, uint flags, System.UIntPtr extra);
'@
# Windows 不讓背景程式搶前景（只會在工作列閃）；先模擬按放一次 Alt，SetForegroundWindow 才會生效
function Unlock { [U.W]::keybd_event(0x12, 0, 0, [UIntPtr]::Zero); [U.W]::keybd_event(0x12, 0, 2, [UIntPtr]::Zero) }
function Titles { (Get-Process $Process -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle } | ForEach-Object { $_.MainWindowTitle }) -join ' | ' }
# 剛啟動的程式視窗可能還沒出現，最多等 10 秒。
# 找不到同名程式時（例如免安裝版的啟動器 XxxPortable.exe 另外開了 Xxx.exe），改抓 60 秒內新出現、有視窗的程式
$p = $null
for ($i = 0; $i -lt 20 -and -not $p; $i++) {
  $p = Get-Process $Process -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -and $_.MainWindowTitle -like "*$Match*" } | Select-Object -First 1
  if (-not $p -and $Recent) { $p = Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -and $_.StartTime -gt (Get-Date).AddSeconds(-60) } | Sort-Object StartTime -Descending | Select-Object -First 1 }
  if (-not $p) { Start-Sleep -Milliseconds 500 }
}
if (-not $p) { "沒有動作：找不到標題含「$Match」的 $Process 視窗。目前視窗: " + (Titles) | Out-File $Out -Encoding UTF8; return }
$h = $p.MainWindowHandle; $t = $p.MainWindowTitle
function Front { if ([U.W]::IsIconic($h)) { [void][U.W]::ShowWindow($h, 9) }; Unlock; [void][U.W]::SetForegroundWindow($h); Start-Sleep -Milliseconds 400 }
switch ($Action) {
  'close-tab' { Front; (New-Object -ComObject WScript.Shell).SendKeys('^w'); Start-Sleep -Milliseconds 800; $msg = "已關閉分頁: $t" }
  'maximize'  { [void][U.W]::ShowWindow($h, 3); Unlock; [void][U.W]::SetForegroundWindow($h); $msg = "已放大並帶到前景: $t" }
  'minimize'  { [void][U.W]::ShowWindow($h, 6); $msg = "已縮到工作列: $t" }
  default     { Front; $msg = "已帶到前景: $t" }
}
Start-Sleep -Milliseconds 300
$state = if ([U.W]::IsIconic($h)) { '縮在工作列' } elseif ([U.W]::IsZoomed($h)) { '最大化' } else { '一般大小' }
"$msg`r`n視窗狀態: $state`r`n現在視窗: " + (Titles) | Out-File $Out -Encoding UTF8
