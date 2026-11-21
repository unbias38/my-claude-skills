# 在目標電腦執行一個「工作」（由 job-submit.ps1 透過排程器以登入使用者身分啟動，視窗隱藏）
# 在工作資料夾裡執行 $Command，stdout／stderr 分別寫進 stdout.txt、stderr.txt，狀態寫進 status.txt；跑完可語音通知
#
# 兩段式：排程器啟動的這一份（$Detached 空白）只負責「另開一個獨立的 PowerShell」來看管工作，然後立刻結束。
# 原因：desktop-run 拿到結果就會刪除排程，Windows 刪除排程時會終止排程啟動的那個程序；
#       另開的程序不屬於排程，刪除排程也不受影響，才能等工作跑完再寫狀態、念通知。
param([string]$JobDir, [string]$CommandB64, [string]$Speak = '1', [string]$Out, [string]$Detached = '')
if (-not $Detached) {
  $me = $MyInvocation.MyCommand.Path
  $a = '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "{0}" -JobDir "{1}" -CommandB64 "{2}" -Speak "{3}" -Out "{4}" -Detached 1' -f $me, $JobDir, $CommandB64, $Speak, $Out
  Start-Process powershell.exe -ArgumentList $a -WindowStyle Hidden
  return   # 結果檔由獨立程序寫，desktop-run 會等它
}

$cmd = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($CommandB64))
Set-Location -LiteralPath $JobDir
$status = Join-Path $JobDir 'status.txt'
$t0 = Get-Date
"state=running`r`nstart=$($t0.ToString('yyyy-MM-dd HH:mm:ss'))`r`npid=$PID`r`ncommand=$cmd" | Out-File $status -Encoding UTF8
"已啟動（看管程序 PID $PID）" | Out-File $Out -Encoding UTF8

# Python 3.9 把輸出導到檔案時，預設用系統舊編碼（台灣是 cp950），遇到 ≈、emoji 之類就當掉：強制用 UTF-8
$env:PYTHONIOENCODING = 'utf-8'; $env:PYTHONUTF8 = '1'
$p = Start-Process cmd.exe -ArgumentList "/c $cmd > stdout.txt 2> stderr.txt" -WorkingDirectory $JobDir -WindowStyle Hidden -Wait -PassThru
$t1 = Get-Date
$min = ($t1 - $t0).TotalMinutes
"state=done`r`nstart=$($t0.ToString('yyyy-MM-dd HH:mm:ss'))`r`nend=$($t1.ToString('yyyy-MM-dd HH:mm:ss'))`r`nminutes={0:N1}`r`nexit=$($p.ExitCode)`r`ncommand=$cmd" -f $min | Out-File $status -Encoding UTF8
if ($Speak -eq '1') {
  Add-Type -AssemblyName System.Speech
  $s = New-Object System.Speech.Synthesis.SpeechSynthesizer
  $v = $s.GetInstalledVoices() | Where-Object { $_.Enabled -and $_.VoiceInfo.Culture.Name -eq 'zh-TW' } | Select-Object -First 1
  if ($v) { $s.SelectVoice($v.VoiceInfo.Name) }
  $name = (Split-Path $JobDir -Leaf) -replace '_\d{8}_\d{6}$', ''
  $msg = if ($p.ExitCode -eq 0) { "工作 $name 已經完成，花了 {0:N0} 分鐘。" -f [Math]::Max(1, [Math]::Round($min)) } else { "工作 $name 執行失敗，請檢查錯誤訊息。" }
  $s.Speak($msg); $s.Dispose()
}
