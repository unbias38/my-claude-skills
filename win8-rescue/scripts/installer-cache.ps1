# 分析 C:\Windows\Installer（只讀）：哪些檔案仍被登記使用、哪些是孤兒、各產品佔多少
$base = 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Installer\UserData'
$reg = New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase)
$map = @{}
foreach ($sid in Get-ChildItem $base -ErrorAction SilentlyContinue) {
  $patchPkg = @{}
  Get-ChildItem "$($sid.PSPath)\Patches" -ErrorAction SilentlyContinue | ForEach-Object {
    $lp = (Get-ItemProperty $_.PSPath -ErrorAction SilentlyContinue).LocalPackage
    if ($lp) { $patchPkg[$_.PSChildName] = $lp; [void]$reg.Add($lp) } }
  foreach ($p in Get-ChildItem "$($sid.PSPath)\Products" -ErrorAction SilentlyContinue) {
    $ip = Get-ItemProperty "$($p.PSPath)\InstallProperties" -ErrorAction SilentlyContinue
    $name = if ($ip.DisplayName) { $ip.DisplayName } else { $p.PSChildName }
    $fam = $name -replace ' \(.*\)$', '' -replace ' - .*$', ''
    if ($fam -match '^Microsoft Office') { $fam = 'Microsoft Office（各元件合計，更新檔會重複計算）' }
    $pk = @(); if ($ip.LocalPackage) { $pk += $ip.LocalPackage; [void]$reg.Add($ip.LocalPackage) }
    Get-ChildItem "$($p.PSPath)\Patches" -ErrorAction SilentlyContinue | ForEach-Object { if ($patchPkg[$_.PSChildName]) { $pk += $patchPkg[$_.PSChildName] } }
    foreach ($f in $pk) { if (Test-Path -LiteralPath $f) {
      if (-not $map[$fam]) { $map[$fam] = [pscustomobject]@{ N = $fam; B = 0L; C = 0 } }
      $map[$fam].B += (Get-Item -LiteralPath $f -Force).Length; $map[$fam].C++ } }
  }
}
$files = @(Get-ChildItem C:\Windows\Installer -File -Force -ErrorAction SilentlyContinue | Where-Object { $_.Extension -in '.msi', '.msp' })
$used = @($files | Where-Object { $reg.Contains($_.FullName) })
$orph = @($files | Where-Object { -not $reg.Contains($_.FullName) })
"msi/msp 共 {0} 個，{1:N2} GB" -f $files.Count, (($files | Measure-Object Length -Sum).Sum/1GB)
"仍在使用 {0} 個，{1:N2} GB（不能刪）" -f $used.Count, (($used | Measure-Object Length -Sum).Sum/1GB)
"孤兒 {0} 個，{1:N2} GB（可以搬到別的磁碟，不要直接刪）" -f $orph.Count, (($orph | Measure-Object Length -Sum).Sum/1GB)
"--- 孤兒前 10 大 ---"
$orph | Sort-Object Length -Descending | Select-Object -First 10 | ForEach-Object { "{0,7:N0} MB  {1:yyyy-MM-dd}  {2}" -f ($_.Length/1MB), $_.LastWriteTime, $_.Name }
"--- 依產品（前 12 名）---"
$map.Values | Sort-Object B -Descending | Select-Object -First 12 | ForEach-Object { "{0,7:N2} GB {1,5} 檔  {2}" -f ($_.B/1GB), $_.C, $_.N }
