# 第一輪健檢（只讀，PowerShell 4.0 相容）。用 run.ps1 -CmdFile 送到目標執行
$os = Get-WmiObject Win32_OperatingSystem
$cs = Get-WmiObject Win32_ComputerSystem
"=== 系統 ==="
"{0} | {1} {2} | 組建 {3}" -f $cs.Model, $os.Caption, $os.OSArchitecture, $os.BuildNumber
"上次開機: {0:yyyy-MM-dd HH:mm}" -f $os.ConvertToDateTime($os.LastBootUpTime)
"記憶體: 可用 {0:N0} MB / 共 {1:N0} MB" -f ($os.FreePhysicalMemory/1KB), ($os.TotalVisibleMemorySize/1KB)

"=== 實體硬碟 ==="
Get-WmiObject Win32_DiskDrive | ForEach-Object { "{0} | {1:N0} GB | 狀態 {2}" -f $_.Model, ($_.Size/1GB), $_.Status }
try { Get-WmiObject -Namespace root\wmi MSStorageDriver_FailurePredictStatus -ErrorAction Stop | ForEach-Object { "SMART 預測故障: {0}  ({1})" -f $_.PredictFailure, ($_.InstanceName -replace '^.*Prod_','' -replace '\\.*$','') } } catch { "SMART: 讀不到" }

"=== 磁碟空間 ==="
Get-WmiObject Win32_LogicalDisk -Filter "DriveType=3" | ForEach-Object { "{0} {1}  共 {2:N0} GB  剩 {3:N1} GB ({4:P0})" -f $_.DeviceID, $_.VolumeName, ($_.Size/1GB), ($_.FreeSpace/1GB), ($_.FreeSpace/$_.Size) }

"=== 系統錯誤事件（近 90 天，前 10 名）==="
$ev = Get-WinEvent -FilterHashtable @{LogName='System'; StartTime=(Get-Date).AddDays(-90); Level=1,2} -ErrorAction SilentlyContinue
"嚴重+錯誤 共 " + @($ev).Count + " 筆"
$ev | Group-Object ProviderName, Id | Sort-Object Count -Descending | Select-Object -First 10 | ForEach-Object { "{0,5} 次  {1}" -f $_.Count, $_.Name }

"=== 硬碟錯誤（一年內，disk 7/11/51/153、Ntfs 55）==="
$since = (Get-Date).AddDays(-365)
$d1 = Get-WinEvent -FilterHashtable @{LogName='System'; StartTime=$since; ProviderName='disk'; Id=7,11,51,153} -ErrorAction SilentlyContinue
$d2 = Get-WinEvent -FilterHashtable @{LogName='System'; StartTime=$since; ProviderName='Ntfs','Microsoft-Windows-Ntfs'; Id=55} -ErrorAction SilentlyContinue
"共 " + (@($d1).Count + @($d2).Count) + " 筆"
@($d1) + @($d2) | Where-Object { $_ } | Group-Object ProviderName, Id | ForEach-Object { "   {0} 次  {1}" -f $_.Count, $_.Name }
$kp = Get-WinEvent -FilterHashtable @{LogName='System'; StartTime=$since; ProviderName='Microsoft-Windows-Kernel-Power'; Id=41} -ErrorAction SilentlyContinue
"一年內不正常關機（Kernel-Power 41）: " + @($kp).Count

"=== 防毒 ==="
try { Get-WmiObject -Namespace root\SecurityCenter2 AntiVirusProduct -ErrorAction Stop | ForEach-Object { "{0}  productState=0x{1:X}" -f $_.displayName, $_.productState } } catch { "讀不到（Server 版或 Win7 以前的系統沒有 SecurityCenter2）" }

"=== 最近安裝的 Windows 更新 ==="
Get-HotFix | Where-Object InstalledOn | Sort-Object InstalledOn -Descending | Select-Object -First 3 | ForEach-Object { "{0}  {1:yyyy-MM-dd}" -f $_.HotFixID, $_.InstalledOn }

"=== 開機自動啟動 ==="
Get-WmiObject Win32_StartupCommand | Where-Object Name | ForEach-Object { "{0}  |  {1}  |  {2}" -f $_.Name, $_.User, $_.Command }

"=== 記憶體用量前 10 名 ==="
Get-Process | Sort-Object WorkingSet -Descending | Select-Object -First 10 | ForEach-Object { "{0,-30} {1,6:N0} MB" -f $_.ProcessName, ($_.WorkingSet/1MB) }

"=== 電池 ==="
$b = Get-WmiObject Win32_Battery
if ($b) {
  "剩餘 {0}%  狀態碼 {1}（2=插電）" -f $b.EstimatedChargeRemaining, $b.BatteryStatus
  try { $full = (Get-WmiObject -Namespace root\wmi BatteryFullChargedCapacity -ErrorAction Stop | Select-Object -First 1).FullChargedCapacity; $design = (Get-WmiObject -Namespace root\wmi BatteryStaticData -ErrorAction Stop | Select-Object -First 1).DesignedCapacity; "滿充 {0:N0} / 設計 {1:N0} mWh（{2:P0}）" -f $full, $design, ($full/$design) } catch { "容量: 讀不到" }
} else { "沒有電池（桌機）" }

"=== 溫度 ==="
try { Get-WmiObject -Namespace root\wmi MSAcpi_ThermalZoneTemperature -ErrorAction Stop | ForEach-Object { "{0}: {1:N0} °C" -f ($_.InstanceName -replace '^.*\\',''), ($_.CurrentTemperature/10 - 273.15) } } catch { "讀不到" }

"=== 安全設定 ==="
try { "SMB1 server: " + (Get-SmbServerConfiguration).EnableSMB1Protocol } catch { "SMB1: 讀不到（Win7 請查 HKLM\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters 的 SMB1）" }
try { Get-NetFirewallProfile | ForEach-Object { "防火牆 {0}: {1}" -f $_.Name, $_.Enabled } } catch { netsh advfirewall show allprofiles state }
"分享資料夾:"
Get-WmiObject Win32_Share | ForEach-Object { "   {0} -> {1}" -f $_.Name, $_.Path }
try { Get-SmbShare | Where-Object { $_.Name -notmatch '\$$' } | ForEach-Object { $n = $_.Name; Get-SmbShareAccess -Name $n | ForEach-Object { "   權限 {0}: {1} {2}" -f $n, $_.AccountName, $_.AccessRight } } } catch {}
"遠端控制軟體（開機啟動或服務）:"
Get-Service | Where-Object { $_.Name -match 'AnyDesk|TeamViewer|RustDesk|UltraVNC|tvnserver' } | ForEach-Object { "   服務 {0}: {1}" -f $_.Name, $_.Status }

"=== 已安裝程式數 ==="
@(Get-ItemProperty 'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*','HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*' -ErrorAction SilentlyContinue | Where-Object DisplayName).Count
