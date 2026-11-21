# 把目標電腦上某個工作的整個資料夾（含 output、stdout、stderr、status）拿回主控機
# 用法：job-fetch.ps1 -Target OLDPC -Job pi_20261121_231500 [-Dest C:\work\results]
param([Parameter(Mandatory)][string]$Target, [Parameter(Mandatory)][string]$Job, [string]$Dest)
$cfg = (Get-Content (Join-Path $env:USERPROFILE '.win8-rescue\targets.json') -Raw -Encoding UTF8 | ConvertFrom-Json).$Target
if (-not $Dest) { $Dest = Join-Path $env:USERPROFILE ".win8-rescue\jobs\$Job" }
$remoteDir = "$($cfg.workdir)\jobs\$Job"
$drv = 'W8R' + (Get-Random -Maximum 9999)
New-PSDrive -Name $drv -PSProvider FileSystem -Root ('\\' + $cfg.ip + '\' + $remoteDir.Substring(0, 1) + '$') -Credential (Import-Clixml $cfg.cred) | Out-Null
try {
  $src = "${drv}:" + $remoteDir.Substring(2)
  if (-not (Test-Path $src)) { throw "目標上找不到 $remoteDir" }
  New-Item -ItemType Directory -Force $Dest | Out-Null
  Copy-Item -Path (Join-Path $src '*') -Destination $Dest -Recurse -Force
  "已取回 {0} 個檔案到 {1}" -f @(Get-ChildItem $Dest -Recurse -File).Count, $Dest
} finally { Remove-PSDrive $drv -Force }
