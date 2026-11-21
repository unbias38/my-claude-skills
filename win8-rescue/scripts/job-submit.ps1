# 把主控機上的一個資料夾（程式＋資料）傳到目標電腦的 <Workdir>\jobs\<名稱>_<時間>\，並在背景啟動
# 傳檔走 SMB 管理分享（\\IP\D$），大檔也可以；啟動用排程器以登入使用者身分隱藏執行，WinRM 斷線也會繼續跑
# 用法：job-submit.ps1 -Target OLDPC -LocalDir C:\work\myjob -Command 'python main.py' [-Name pi] [-NoSpeak]
param(
  [Parameter(Mandatory)][string]$Target,
  [Parameter(Mandatory)][string]$LocalDir,
  [Parameter(Mandatory)][string]$Command,
  [string]$Name,
  [switch]$NoSpeak
)
$cfg = (Get-Content (Join-Path $env:USERPROFILE '.win8-rescue\targets.json') -Raw -Encoding UTF8 | ConvertFrom-Json).$Target
if (-not (Test-Path $LocalDir)) { throw "找不到 $LocalDir" }
if (-not $Name) { $Name = Split-Path $LocalDir -Leaf }
$jobName = '{0}_{1:yyyyMMdd_HHmmss}' -f ($Name -replace '[^\w\-]', '_'), (Get-Date)
$remoteDir = "$($cfg.workdir)\jobs\$jobName"
$unc = '\\' + $cfg.ip + '\' + $remoteDir.Substring(0, 1) + '$' + $remoteDir.Substring(2)

# 用 SMB 傳檔（以目標帳密連管理分享）
$drv = 'W8R' + (Get-Random -Maximum 9999)
New-PSDrive -Name $drv -PSProvider FileSystem -Root ('\\' + $cfg.ip + '\' + $remoteDir.Substring(0, 1) + '$') -Credential (Import-Clixml $cfg.cred) | Out-Null
try {
  $dst = "${drv}:" + $remoteDir.Substring(2)
  New-Item -ItemType Directory -Force $dst | Out-Null
  Copy-Item -Path (Join-Path $LocalDir '*') -Destination $dst -Recurse -Force
  $n = @(Get-ChildItem $dst -Recurse -File).Count
  $mb = (Get-ChildItem $dst -Recurse -File | Measure-Object Length -Sum).Sum / 1MB
  "已傳送 {0} 個檔案（{1:N1} MB）到 {2}" -f $n, $mb, $remoteDir
} finally { Remove-PSDrive $drv -Force }

$b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($Command))
& (Join-Path $PSScriptRoot 'desktop-run.ps1') -Target $Target -Script 'run-job.ps1' -Arguments @{ JobDir = $remoteDir; CommandB64 = $b64; Speak = $(if ($NoSpeak) { '0' } else { '1' }) } -Title "啟動工作 $jobName：$Command"
"JOB=$jobName"
