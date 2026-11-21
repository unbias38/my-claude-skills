# C 槽空間分析（只讀）。跳過資料夾捷徑（junction／symlink），避免重複計算
$RP = [IO.FileAttributes]::ReparsePoint
function DirSize([string]$root) {
  $sum = 0L; $stack = New-Object System.Collections.Stack; $stack.Push($root)
  while ($stack.Count) {
    $d = $stack.Pop()
    try { foreach ($i in ([IO.DirectoryInfo]$d).EnumerateFileSystemInfos()) {
      if ($i.Attributes -band $RP) { continue }
      if ($i -is [IO.DirectoryInfo]) { $stack.Push($i.FullName) } else { $sum += $i.Length } } } catch {}
  }
  [math]::Round($sum/1GB, 2)
}
function Top([string]$p, [int]$n) {
  Get-ChildItem -LiteralPath $p -Force -ErrorAction SilentlyContinue | Where-Object { -not ($_.Attributes -band $RP) } | ForEach-Object {
    $g = if ($_.PSIsContainer) { DirSize $_.FullName } else { [math]::Round($_.Length/1GB, 2) }
    [pscustomobject]@{ N = $_.Name; G = $g } } | Sort-Object G -Descending | Select-Object -First $n | ForEach-Object { "{0,8} GB  {1}" -f $_.G, $_.N }
}
$me = $env:USERPROFILE
"C 槽剩餘: {0:N1} GB" -f ((Get-WmiObject Win32_LogicalDisk -Filter "DeviceID='C:'").FreeSpace/1GB)
"=== C:\ 第一層 ==="; Top 'C:\' 10
"=== C:\Users ==="; Top 'C:\Users' 5
"=== $me ==="; Top $me 8
"=== AppData\Local ==="; Top "$me\AppData\Local" 10
"=== AppData\Roaming ==="; Top "$me\AppData\Roaming" 6
"=== ProgramData ==="; Top 'C:\ProgramData' 8
"=== 可清理候選 ==="
foreach ($p in 'C:\Windows\Temp', "$me\AppData\Local\Temp", 'C:\Windows\SoftwareDistribution\Download', 'C:\$Recycle.Bin', 'C:\Windows.old', 'C:\ProgramData\Microsoft\Windows\WER', 'C:\Windows\Installer', 'C:\Windows\WinSxS') {
  if (Test-Path -LiteralPath $p) { "{0,8} GB  {1}" -f (DirSize $p), $p } else { "     ---    {0}（不存在）" -f $p } }
"hiberfil.sys: " + $(if (Test-Path 'C:\hiberfil.sys') { "{0:N2} GB" -f ((Get-Item 'C:\hiberfil.sys' -Force).Length/1GB) } else { '無' })
"pagefile.sys: " + $(if (Test-Path 'C:\pagefile.sys') { "{0:N2} GB" -f ((Get-Item 'C:\pagefile.sys' -Force).Length/1GB) } else { '不在 C 槽' })
"=== 使用者資料夾實際位置（遠端看到的是登入帳號本身的設定）==="
$sf = Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders' -ErrorAction SilentlyContinue
"桌面={0} | 文件={1} | 下載={2}" -f $sf.Desktop, $sf.Personal, $sf.'{374DE290-123F-4565-9164-39C4925E467B}'
"=== 系統還原點佔用 ==="
vssadmin list shadowstorage 2>&1 | Select-String '已使用|Used|最大|Maximum' | ForEach-Object { $_.Line.Trim() }
