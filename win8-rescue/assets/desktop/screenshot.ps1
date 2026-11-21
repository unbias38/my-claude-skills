# 在使用者桌面的工作階段執行（由 screenshot.ps1 包裝器透過 desktop-run 啟動）
# 拍下所有螢幕，縮到最寬 $MaxWidth 像素，存成 JPEG；結果（檔案路徑與尺寸）寫到 $Out
param([string]$Out, [string]$MaxWidth = '1600')
Add-Type -AssemblyName System.Windows.Forms, System.Drawing
# 不先宣告 DPI 感知的話，在有縮放的螢幕上只會拍到左上角一部分
Add-Type -Namespace U -Name D -MemberDefinition '[DllImport("user32.dll")] public static extern bool SetProcessDPIAware();'
[void][U.D]::SetProcessDPIAware()
$vs = [System.Windows.Forms.SystemInformation]::VirtualScreen
$bmp = New-Object System.Drawing.Bitmap $vs.Width, $vs.Height
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($vs.Left, $vs.Top, 0, 0, $bmp.Size)
$g.Dispose()
$w = [Math]::Min($vs.Width, [int]$MaxWidth); $h = [int]($vs.Height * $w / $vs.Width)
$small = New-Object System.Drawing.Bitmap $bmp, $w, $h
$bmp.Dispose()
$file = Join-Path (Split-Path $Out) ('screen_{0:yyyyMMdd_HHmmss}.jpg' -f (Get-Date))
$enc = [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | Where-Object { $_.MimeType -eq 'image/jpeg' }
$ep = New-Object System.Drawing.Imaging.EncoderParameters 1
$ep.Param[0] = New-Object System.Drawing.Imaging.EncoderParameter ([System.Drawing.Imaging.Encoder]::Quality), 80L
$small.Save($file, $enc, $ep)
$small.Dispose()
"FILE=$file`r`n原始解析度 $($vs.Width)x$($vs.Height)，存成 ${w}x${h}" | Out-File $Out -Encoding UTF8
