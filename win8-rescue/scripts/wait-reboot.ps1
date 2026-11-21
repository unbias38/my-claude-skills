# 在主控機背景執行：等目標關機、再重新上線（5985 埠可連），然後回報登入狀態、Wi-Fi、網路類型
param([Parameter(Mandatory)][string]$Target, [int]$Minutes = 15)
$cfg = (Get-Content (Join-Path $env:USERPROFILE '.win8-rescue\targets.json') -Raw -Encoding UTF8 | ConvertFrom-Json).$Target
$deadline = (Get-Date).AddMinutes($Minutes); $down = $false; $up = $false
while ((Get-Date) -lt $deadline) {
  $up = (New-Object Net.Sockets.TcpClient).ConnectAsync($cfg.ip, 5985).Wait(1500)
  if (-not $up -and -not $down) { $down = $true; "{0:HH:mm:ss} 已關機，重開中" -f (Get-Date) }
  if ($up -and $down) { "{0:HH:mm:ss} 重新上線" -f (Get-Date); break }
  Start-Sleep 5
}
if (-not ($up -and $down)) { "{0} 分鐘內沒有等到重新上線（曾關機: {1}）。到 references/pitfalls.md 查「網路」那一段。" -f $Minutes, $down; return }
& (Join-Path $PSScriptRoot 'run.ps1') -Target $Target -Title '重開機後上線狀態' -Cmd @'
$os = Get-WmiObject Win32_OperatingSystem
"開機時間: {0:HH:mm:ss}" -f $os.ConvertToDateTime($os.LastBootUpTime)
$u = (Get-WmiObject Win32_ComputerSystem).UserName
"目前登入: " + $(if ($u) { $u } else { '沒有人登入（停在登入畫面）' })
$s = netsh wlan show interfaces | Select-String '^\s*SSID' | Select-Object -First 1
if ($s) { $s.Line.Trim() } else { 'Wi-Fi: 沒有連線（可能走有線）' }
try { Get-NetConnectionProfile | ForEach-Object { "網路 {0}: {1}" -f $_.Name, $_.NetworkCategory } } catch {}
'@
