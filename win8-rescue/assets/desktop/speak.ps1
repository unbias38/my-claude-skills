# 在使用者桌面的工作階段執行（由 speak.ps1 包裝器透過 desktop-run 啟動）
# 用 Windows 內建語音念出文字。背景工作階段（session 0）沒有音訊裝置，所以一定要在桌面這邊念
# 文字用 base64 傳進來，避免中文經過排程器參數時變成亂碼
param([string]$TextB64, [string]$Voice = 'zh-TW', [string]$Rate = '0', [string]$Out)
Add-Type -AssemblyName System.Speech
$text = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($TextB64))
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$v = $s.GetInstalledVoices() | Where-Object { $_.Enabled -and ($_.VoiceInfo.Culture.Name -eq $Voice -or $_.VoiceInfo.Name -like "*$Voice*") } | Select-Object -First 1
if ($v) { $s.SelectVoice($v.VoiceInfo.Name) }
$s.Rate = [int]$Rate   # -10（慢）到 10（快）
$s.Volume = 100
# 系統靜音或音量為 0 時念了也聽不到：一併回報，讓 Claude 提醒使用者
$mute = ''
try {
  Add-Type -Namespace U -Name A -MemberDefinition '[DllImport("winmm.dll")] public static extern int waveOutGetVolume(System.IntPtr h, out uint v);'
  $vol = [uint32]0; [void][U.A]::waveOutGetVolume([IntPtr]::Zero, [ref]$vol); $mute = "，此程式的音量通道 {0}%" -f [int](($vol -band 0xFFFF) * 100 / 0xFFFF)
} catch {}
$t0 = Get-Date
$used = $s.Voice.Name
$s.Speak($text)
$s.Dispose()
"已用「$used」念完 {0} 個字，花了 {1:N1} 秒$mute" -f $text.Length, ((Get-Date) - $t0).TotalSeconds | Out-File $Out -Encoding UTF8
