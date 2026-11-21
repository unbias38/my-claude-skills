# 掃描目標電腦某顆磁碟的大檔案、疑似重複檔案（只讀）。傳統硬碟幾百 GB 可能要十幾分鐘，請放背景執行
# 用法：scan-bigfiles.ps1 -Target OLDPC [-Drive 'D:\'] [-MinMB 50]
param([Parameter(Mandatory)][string]$Target, [string]$Drive = 'D:\', [int]$MinMB = 50)
$cfg = (Get-Content (Join-Path $env:USERPROFILE '.win8-rescue\targets.json') -Raw -Encoding UTF8 | ConvertFrom-Json).$Target
$body = [IO.File]::ReadAllText((Join-Path (Split-Path $PSScriptRoot) 'assets\remote\bigfiles.ps1'), [Text.Encoding]::UTF8)
$q = { param($s) "'" + ($s -replace "'", "''") + "'" }
$cmd = "`$Drive = $(& $q $Drive); `$MinMB = $MinMB; `$OutDir = $(& $q ($cfg.workdir + '\reports'))`r`n" + $body
& (Join-Path $PSScriptRoot 'run.ps1') -Target $Target -Title "掃描 $Drive 大檔案與重複檔案（$MinMB MB 以上）" -Cmd $cmd
