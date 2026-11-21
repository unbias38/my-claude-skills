# 查目標電腦上某個工作的狀態與輸出最後幾行；不給 -Job 就列出所有工作
# 用法：job-status.ps1 -Target OLDPC [-Job pi_20261121_231500] [-Tail 15]
param([Parameter(Mandatory)][string]$Target, [string]$Job, [int]$Tail = 15)
$cfg = (Get-Content (Join-Path $env:USERPROFILE '.win8-rescue\targets.json') -Raw -Encoding UTF8 | ConvertFrom-Json).$Target
Invoke-Command -ComputerName $cfg.ip -Credential (Import-Clixml $cfg.cred) -ArgumentList "$($cfg.workdir)\jobs", $Job, $Tail -ScriptBlock {
  param($root, $job, $tail)
  if (-not $job) {
    Get-ChildItem $root -Directory -ErrorAction SilentlyContinue | Sort-Object Name | ForEach-Object {
      $s = Get-Content (Join-Path $_.FullName 'status.txt') -Encoding UTF8 -ErrorAction SilentlyContinue
      "{0}  {1}" -f $_.Name, (($s | Where-Object { $_ -match '^(state|minutes|exit)=' }) -join '  ') }
    return
  }
  $d = Join-Path $root $job
  "=== 狀態 ==="; Get-Content (Join-Path $d 'status.txt') -Encoding UTF8 -ErrorAction SilentlyContinue
  $cpu = (Get-WmiObject Win32_Processor | Measure-Object LoadPercentage -Average).Average; "目前 CPU: $cpu%"
  "=== stdout 最後 $tail 行 ==="; Get-Content (Join-Path $d 'stdout.txt') -Encoding UTF8 -Tail $tail -ErrorAction SilentlyContinue
  $e = Get-Content (Join-Path $d 'stderr.txt') -Encoding UTF8 -Tail $tail -ErrorAction SilentlyContinue
  if ($e) { "=== stderr 最後 $tail 行 ==="; $e }
}
