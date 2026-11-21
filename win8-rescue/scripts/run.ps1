# 對目標電腦送指令：指令與回應同時寫入 <Workdir>\remote_log.txt 與儀表板 <Workdir>\dashboard\log.js
# 用法：run.ps1 -Target OLDPC -Title '中文標題' -Cmd '...'   或   -CmdFile <檔案>
param(
  [Parameter(Mandatory)][string]$Target,
  [string]$Cmd,
  [string]$CmdFile,
  [string]$Title = ''
)
$cfgPath = Join-Path $env:USERPROFILE '.win8-rescue\targets.json'
if (-not (Test-Path $cfgPath)) { throw "找不到 $cfgPath，請先執行 setup-controller.ps1" }
$cfg = (Get-Content $cfgPath -Raw -Encoding UTF8 | ConvertFrom-Json).$Target
if (-not $cfg) { throw "targets.json 裡沒有 $Target" }
if ($CmdFile) { $Cmd = [IO.File]::ReadAllText($CmdFile, [Text.Encoding]::UTF8) }
if (-not $Cmd) { throw '請提供 -Cmd 或 -CmdFile' }
$cred = Import-Clixml $cfg.cred

Invoke-Command -ComputerName $cfg.ip -Credential $cred -ArgumentList $Cmd, $Title, $cfg.workdir -ScriptBlock {
  param($text, $title, $dir)
  if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  $log = Join-Path $dir 'remote_log.txt'; $js = Join-Path $dir 'dashboard\log.js'
  $t0 = Get-Date
  Add-Content -LiteralPath $log -Encoding UTF8 -Value ("`r`n===== {0:yyyy-MM-dd HH:mm:ss}  Claude 送來的指令 =====`r`n{1}`r`n----- 回應 -----" -f $t0, $text.Trim())
  $ok = $true
  try { $out = & ([scriptblock]::Create($text)) 2>&1 | Out-String -Width 200 } catch { $ok = $false; $out = $_ | Out-String }
  $out = $out.TrimEnd()
  Add-Content -LiteralPath $log -Encoding UTF8 -Value $out
  if (Test-Path -LiteralPath (Split-Path $js)) {
    $e = @{ t = $t0.ToString('yyyy-MM-ddTHH:mm:ss'); title = $title; cmd = $text.Trim(); out = $out; ok = $ok; ms = [int]((Get-Date) - $t0).TotalMilliseconds }
    Add-Content -LiteralPath $js -Encoding UTF8 -Value ('LOG.push(' + ($e | ConvertTo-Json -Compress) + ');')
  }
  $out
}
