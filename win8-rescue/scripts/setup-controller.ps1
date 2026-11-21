# 主控機設定（請使用者以「系統管理員」身分執行）
# 1. 把目標加入 WinRM 信任清單  2. 讓使用者輸入目標帳號密碼，加密存檔  3. 登記到 ~/.win8-rescue/targets.json
param(
  [Parameter(Mandatory)][string]$Name,     # 例：OLDPC
  [Parameter(Mandatory)][string]$Ip,       # 例：192.168.0.50
  [Parameter(Mandatory)][string]$User,     # 例：OLDPC\user
  [Parameter(Mandatory)][string]$Workdir   # 目標電腦上放紀錄、儀表板、筆記的資料夾，例：D:\Claude\rescue
)
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) { Write-Host '請用「以系統管理員身分執行」打開 PowerShell 再跑一次。' -ForegroundColor Red; return }

# 信任清單（設定時需要 WinRM 服務在執行，設完恢復原狀）
$svc = Get-Service WinRM; $wasStopped = $svc.Status -ne 'Running'
if ($wasStopped) { Start-Service WinRM }
$cur = (Get-Item WSMan:\localhost\Client\TrustedHosts).Value
if (($cur -split ',') -notcontains $Ip) { Set-Item WSMan:\localhost\Client\TrustedHosts -Value $Ip -Concatenate -Force }
if ($wasStopped) { Stop-Service WinRM }
Write-Host "已加入信任清單：$Ip" -ForegroundColor Green

# 密碼由使用者自己輸入；只有這台電腦、這個 Windows 帳號解得開
$dir = Join-Path $env:USERPROFILE '.win8-rescue'
New-Item -ItemType Directory -Force $dir | Out-Null
$credPath = Join-Path $dir "$Name.cred.xml"
$c = Get-Credential -UserName $User -Message "$Name 的密碼"
if (-not $c) { Write-Host '沒有輸入密碼，已取消。' -ForegroundColor Yellow; return }
$c | Export-Clixml $credPath
Write-Host "密碼已加密存到 $credPath" -ForegroundColor Green

# 登記
$cfgPath = Join-Path $dir 'targets.json'
$cfg = @{}
if (Test-Path $cfgPath) { (Get-Content $cfgPath -Raw -Encoding UTF8 | ConvertFrom-Json).PSObject.Properties | ForEach-Object { $cfg[$_.Name] = $_.Value } }
$cfg[$Name] = [pscustomobject]@{ ip = $Ip; user = $User; cred = $credPath; workdir = $Workdir }
[IO.File]::WriteAllText($cfgPath, ([pscustomobject]$cfg | ConvertTo-Json -Depth 4), (New-Object Text.UTF8Encoding $false))
Write-Host "已登記到 $cfgPath" -ForegroundColor Green

# 測試
try {
  $r = Invoke-Command -ComputerName $Ip -Credential $c -ErrorAction Stop -ScriptBlock { "{0} / {1} / PowerShell {2}" -f (whoami), $env:COMPUTERNAME, $PSVersionTable.PSVersion }
  Write-Host "連線成功：$r" -ForegroundColor Green
} catch { Write-Host ("連線失敗：" + $_.Exception.Message) -ForegroundColor Red }
