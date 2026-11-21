# 部署「病床邊監視器」儀表板到目標電腦 <Workdir>\dashboard\，在桌面和 Workdir 各放一份 Claude儀表板.bat
# -AutoStart：每次登入自動啟動（HKCU Run，視窗縮到最小）
param([Parameter(Mandatory)][string]$Target, [switch]$AutoStart)
$cfg = (Get-Content (Join-Path $env:USERPROFILE '.win8-rescue\targets.json') -Raw -Encoding UTF8 | ConvertFrom-Json).$Target
if (-not $cfg) { throw "targets.json 裡沒有 $Target" }
$assets = Join-Path (Split-Path $PSScriptRoot) 'assets\dashboard'
$html = [IO.File]::ReadAllText((Join-Path $assets 'index.html'), [Text.Encoding]::UTF8)
$loop = [IO.File]::ReadAllText((Join-Path $assets 'stats-loop.ps1'), [Text.Encoding]::UTF8)
$cred = Import-Clixml $cfg.cred
$autoFlag = [bool]$AutoStart   # 不能在 -ArgumentList 裡直接寫 [bool]$AutoStart：指令模式會把它當成字串 '[bool]False'，永遠是真

Invoke-Command -ComputerName $cfg.ip -Credential $cred -ArgumentList $html, $loop, $cfg.workdir, $autoFlag -ScriptBlock {
  param($html, $loop, $root, $auto)
  $dd = Join-Path $root 'dashboard'
  New-Item -ItemType Directory -Force $dd | Out-Null
  $noBom = New-Object Text.UTF8Encoding $false; $bom = New-Object Text.UTF8Encoding $true
  [IO.File]::WriteAllText("$dd\index.html", $html, $noBom)
  [IO.File]::WriteAllText("$dd\stats-loop.ps1", $loop, $bom)   # PowerShell 4.0 需要 BOM 才讀得懂中文

  # 已有 remote_log.txt 但還沒有 log.js：把舊紀錄轉過來
  $txt = Join-Path $root 'remote_log.txt'
  if (-not (Test-Path "$dd\log.js")) {
    $lines = New-Object System.Collections.Generic.List[string]
    if (Test-Path $txt) {
      $all = [IO.File]::ReadAllText($txt, [Text.Encoding]::UTF8)
      $parts = [regex]::Split($all, '(?m)^===== (\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)  Claude 送來的指令 =====\r?$')
      for ($i = 1; $i -lt $parts.Count; $i += 2) {
        $body = $parts[$i+1]; $k = $body.IndexOf('----- 回應 -----'); if ($k -lt 0) { continue }
        $e = @{ t = ($parts[$i] -replace ' ', 'T'); title = ''; cmd = $body.Substring(0, $k).Trim(); out = $body.Substring($k + 14).Trim(); ok = $true }
        $lines.Add('LOG.push(' + ($e | ConvertTo-Json -Compress) + ');') }
    }
    [IO.File]::WriteAllText("$dd\log.js", (($lines -join "`r`n") + "`r`n"), $noBom)
    "轉入舊紀錄 $($lines.Count) 筆"
  }

  # 啟動用 bat：用系統預設編碼（中文 Windows 是 Big5），路徑有中文也能用
  $bat = "@echo off`r`ntitle Claude dashboard`r`nstart `"`" `"$dd\index.html`"`r`npowershell -NoProfile -ExecutionPolicy Bypass -File `"$dd\stats-loop.ps1`"`r`n"
  $desk = [Environment]::GetFolderPath('Desktop')
  foreach ($p in (Join-Path $desk 'Claude儀表板.bat'), (Join-Path $root 'Claude儀表板.bat')) { [IO.File]::WriteAllText($p, $bat, [Text.Encoding]::Default); "已建立 $p" }

  if ($auto) {
    Set-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' -Name 'ClaudeDashboard' -Value ('cmd.exe /c start "Claude dashboard" /min "' + (Join-Path $root 'Claude儀表板.bat') + '"')
    "已設定每次登入自動啟動"
  }
  $b = Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.html\UserChoice' -ErrorAction SilentlyContinue
  "預設瀏覽器: " + $(if ($b) { $b.ProgId } else { '未知' }) + "（需要 Chrome／Edge 80 以上，IE 開不了）"
}
& (Join-Path $PSScriptRoot 'run.ps1') -Target $Target -Title '部署儀表板' -Cmd ('"儀表板已部署到 ' + $cfg.workdir + '\dashboard"')
