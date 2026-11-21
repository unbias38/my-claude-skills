# OLDPC 儀表板：每 2 秒把系統數值寫進 stats.js，關閉這個視窗就停止
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
$out = Join-Path $dir 'stats.js'; $tmp = "$out.tmp"
$utf8 = New-Object Text.UTF8Encoding $false
$Host.UI.RawUI.WindowTitle = "$env:COMPUTERNAME 儀表板監看中"
Write-Host ''
Write-Host '  儀表板監看中，數值每 2 秒更新一次。' -ForegroundColor Cyan
Write-Host '  關閉這個視窗，儀表板就會停止更新。' -ForegroundColor DarkCyan
Write-Host ''
$os0 = Get-WmiObject Win32_OperatingSystem
$boot = $os0.ConvertToDateTime($os0.LastBootUpTime)
$cs0 = Get-WmiObject Win32_ComputerSystem; $model = ($cs0.Manufacturer + ' ' + $cs0.Model).Trim(); $osName = $os0.Caption -replace '^Microsoft ', ''
while ($true) {
  try {
    $os = Get-WmiObject Win32_OperatingSystem
    $cpu = (Get-WmiObject Win32_Processor | Measure-Object LoadPercentage -Average).Average
    $disks = @(Get-WmiObject Win32_LogicalDisk -Filter 'DriveType=3' | ForEach-Object { @{ id = $_.DeviceID; free = [math]::Round($_.FreeSpace/1GB, 2); total = [math]::Round($_.Size/1GB, 2) } })
    $b = Get-WmiObject Win32_Battery | Select-Object -First 1
    $temp = $null
    try { $z = Get-WmiObject -Namespace root\wmi MSAcpi_ThermalZoneTemperature -ErrorAction Stop | Sort-Object CurrentTemperature -Descending | Select-Object -First 1; if ($z) { $temp = [int][math]::Round($z.CurrentTemperature/10 - 273.15) } } catch {}
    $all = Get-Process
    $procs = @($all | Sort-Object WorkingSet -Descending | Select-Object -First 5 | ForEach-Object { @{ n = $_.ProcessName; mb = [int]($_.WorkingSet/1MB) } })
    $ip = (Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue | Where-Object { $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*' } | ForEach-Object { $_.IPAddress }) -join ', '
    $s = @{
      t = (Get-Date).ToString('yyyy-MM-ddTHH:mm:ss'); host = $env:COMPUTERNAME; model = $model; os = $osName; ip = $ip
      cpu = [int]$cpu
      ramTotal = [int]($os.TotalVisibleMemorySize/1KB); ramUsed = [int](($os.TotalVisibleMemorySize - $os.FreePhysicalMemory)/1KB)
      disks = $disks; temp = $temp
      batt = $(if ($b) { [int]$b.EstimatedChargeRemaining } else { $null }); charging = $(if ($b) { $b.BatteryStatus -eq 2 } else { $false })
      procs = $procs; pcount = $all.Count
      remote = (@($all | Where-Object { $_.ProcessName -eq 'wsmprovhost' }).Count -gt 0)
      uptimeH = [math]::Round(((Get-Date) - $boot).TotalHours, 1)
    }
    [IO.File]::WriteAllText($tmp, 'window.STATS=' + ($s | ConvertTo-Json -Compress -Depth 4) + ';', $utf8)
    Move-Item -Force -LiteralPath $tmp -Destination $out
  } catch { Write-Host ('  ' + $_.Exception.Message) -ForegroundColor DarkYellow }
  Start-Sleep -Seconds 2
}
