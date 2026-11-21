# 磁碟大檔案與重複檔案分析（只讀，PowerShell 4.0 相容）。由 scripts\scan-bigfiles.ps1 在開頭補上 $Drive、$MinMB、$OutDir 後送出
# 1) 第一層資料夾大小  2) 最大的檔案  3) 疑似重複：大小相同 → 比對「開頭 1MB + 結尾 1MB」的 MD5
# 跳過資料夾捷徑（junction），避免重複計算；完整清單存成 CSV 到 $OutDir
$RP = [IO.FileAttributes]::ReparsePoint
$min = [int64]$MinMB * 1MB
$skip = '\\System Volume Information$|\\\$RECYCLE\.BIN$|\\\$Recycle\.Bin$'
$t0 = Get-Date
$top = @{}; $big = New-Object System.Collections.Generic.List[object]; $nFiles = 0L; $total = 0L
foreach ($first in ([IO.DirectoryInfo]$Drive).EnumerateFileSystemInfos()) {
  if ($first.Attributes -band $RP) { continue }
  if ($first -isnot [IO.DirectoryInfo]) { $total += $first.Length; $top['(根目錄檔案)'] += $first.Length; if ($first.Length -ge $min) { $big.Add($first) }; continue }
  if ($first.FullName -match $skip) { continue }
  $sum = 0L; $stack = New-Object System.Collections.Stack; $stack.Push($first.FullName)
  while ($stack.Count) {
    $d = $stack.Pop()
    try { foreach ($i in ([IO.DirectoryInfo]$d).EnumerateFileSystemInfos()) {
      if ($i.Attributes -band $RP) { continue }
      if ($i -is [IO.DirectoryInfo]) { $stack.Push($i.FullName) }
      else { $nFiles++; $sum += $i.Length; if ($i.Length -ge $min) { $big.Add($i) } } } } catch {}
  }
  $top[$first.Name] = $sum; $total += $sum
}
"掃描 {0}：{1:N0} 個檔案，{2:N1} GB，花了 {3:N1} 分鐘" -f $Drive, $nFiles, ($total/1GB), ((Get-Date) - $t0).TotalMinutes
""
"=== 第一層資料夾（前 15 名）==="
$top.GetEnumerator() | Sort-Object Value -Descending | Select-Object -First 15 | ForEach-Object { "{0,8:N1} GB  {1}" -f ($_.Value/1GB), $_.Key }
""
"=== 最大的 30 個檔案 ==="
$big | Sort-Object Length -Descending | Select-Object -First 30 | ForEach-Object { "{0,8:N2} GB  {1:yyyy-MM-dd}  {2}" -f ($_.Length/1GB), $_.LastWriteTime, $_.FullName }

# 疑似重複
$t1 = Get-Date
function PartHash([string]$path, [int64]$len) {
  $fs = [IO.File]::Open($path, 'Open', 'Read', 'ReadWrite')
  try {
    $n = [int][Math]::Min(1MB, $len); $buf = New-Object byte[] ($n * 2)
    [void]$fs.Read($buf, 0, $n)
    if ($len -gt $n) { [void]$fs.Seek(-$n, 'End'); [void]$fs.Read($buf, $n, $n) }
    $md5 = [Security.Cryptography.MD5]::Create(); [BitConverter]::ToString($md5.ComputeHash($buf)) -replace '-', ''
  } finally { $fs.Dispose() }
}
$groups = @()
foreach ($g in ($big | Group-Object Length | Where-Object { $_.Count -gt 1 })) {
  foreach ($h in ($g.Group | ForEach-Object { $f = $_; try { [pscustomobject]@{ F = $f; H = (PartHash $f.FullName $f.Length) } } catch {} } | Group-Object H | Where-Object { $_.Count -gt 1 })) {
    $files = @($h.Group | ForEach-Object { $_.F } | Sort-Object LastWriteTime)
    $groups += [pscustomobject]@{ Size = $files[0].Length; Count = $files.Count; Waste = $files[0].Length * ($files.Count - 1); Files = $files }
  }
}
""
"=== 疑似重複（大小相同、開頭與結尾內容相同）==="
"共 {0} 組，若每組只留一份可省 {1:N1} GB（比對花了 {2:N1} 分鐘）" -f $groups.Count, (($groups | Measure-Object Waste -Sum).Sum/1GB), ((Get-Date) - $t1).TotalMinutes
$k = 0
foreach ($g in ($groups | Sort-Object Waste -Descending | Select-Object -First 15)) {
  $k++; "[{0}] 每份 {1:N2} GB × {2} 份，可省 {3:N2} GB" -f $k, ($g.Size/1GB), $g.Count, ($g.Waste/1GB)
  $g.Files | ForEach-Object { "     {0:yyyy-MM-dd}  {1}" -f $_.LastWriteTime, $_.FullName }
}

# 完整清單
New-Item -ItemType Directory -Force $OutDir | Out-Null
$stamp = '{0:yyyyMMdd_HHmm}' -f (Get-Date)
$big | Sort-Object Length -Descending | Select-Object @{n='GB';e={[Math]::Round($_.Length/1GB,3)}}, LastWriteTime, FullName | Export-Csv "$OutDir\bigfiles_$stamp.csv" -NoTypeInformation -Encoding UTF8
$k = 0; $groups | Sort-Object Waste -Descending | ForEach-Object { $k++; $grp = $k; $_.Files | Select-Object @{n='組';e={$grp}}, @{n='GB';e={[Math]::Round($_.Length/1GB,3)}}, LastWriteTime, FullName } | Export-Csv "$OutDir\duplicates_$stamp.csv" -NoTypeInformation -Encoding UTF8
""
"完整清單：$OutDir\bigfiles_$stamp.csv、duplicates_$stamp.csv"
