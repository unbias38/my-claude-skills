# 健檢判讀與修復手冊

所有修復都要使用者同意後才做，並列出改前／改後對照。指令都要能在 PowerShell 4.0 上執行。

## 判讀 healthcheck.ps1 的輸出

| 項目 | 怎麼看 | 嚴重度 |
|---|---|---|
| 分享資料夾 | 除了 `ADMIN$`、`C$`、`D$`、`IPC$`、`print$` 這些預設分享以外的，都要查權限。`Everyone Full` 最嚴重 | 🔴 |
| SMB1 server = True | WannaCry 利用的就是它 | 🔴 |
| 最近一次更新的日期 | 停在多年前就照實說，Win8.1 在 2023-01 停止支援，Win7 在 2020-01 | 🟠（無解，只能提醒） |
| C 槽剩餘 < 10% | 系統會變慢、更新會失敗 | 🟠 |
| SMART PredictFailure = True | 硬碟可能快壞了，**最優先**請使用者備份 | 🔴 |
| 真正的硬碟錯誤事件（disk 7/11/51/153、Ntfs 55） | 有的話同樣先備份 | 🔴 |
| Kernel-Power 41（不正常關機） | 一年內幾次屬於正常；很頻繁才查電源或過熱 | 🟡 |
| 溫度：閒置時某個感應器 ≥ 80°C | 灰塵或散熱膏老化，需要使用者自己處理 | 🟡 |
| 電池滿充／設計 < 60% | 老化；提醒膨脹的徵兆 | 🟡 |
| 開機項目很多、有重複 | 系統帳號（S-1-5-18／19／20、.DEFAULT）底下的 Run 項目不會執行，只是殘留 | 🟡 |
| Schannel 36887 數千筆 | 舊的 TLS 連線失敗，大多是雜訊；可以順便說明有些網站可能打不開 | 不列為問題 |
| DistributedCOM 10010 | 雜訊 | 不列為問題 |
| sptd 錯誤 | Daemon Tools 這類光碟模擬軟體留下的舊驅動 | 🟡（可以建議移除） |
| AnyDesk、TeamViewer 開機自動啟動並允許控制 | 使用者沒在用的話，就是多一個入口 | 🟡（問使用者） |

## 修復：分享與 SMB1

```powershell
Get-SmbShare -Name <名稱>; Get-SmbShareAccess -Name <名稱>    # 改前
Remove-SmbShare -Name <名稱> -Force
Set-SmbServerConfiguration -EnableSMB1Protocol $false -Force   # SMB2 保持開啟
```

不要動 SMB1 的 client 端，有些舊 NAS 還需要它。

## 修復：C 槽空間

依效果和風險排列：

1. **關閉休眠** `powercfg -h off`：釋放的空間約等於記憶體的 75%。代價是「休眠」選項和快速啟動都會消失，睡眠照常可用。
2. **暫存檔**：`C:\Windows\Temp`、`%LOCALAPPDATA%\Temp`、`C:\Windows\SoftwareDistribution\Download`、資源回收筒。刪之前先列出大小。
3. **DISM**：`Dism /Online /Cleanup-Image /StartComponentCleanup`，放背景跑。之前或之後用 `/AnalyzeComponentStore` 看可回收量。不要加 `/ResetBase`，除非使用者明白之後就無法移除已安裝的更新。
4. **Installer 孤兒檔**：只有 `installer-cache.ps1` 判定為孤兒的檔案，才可以**搬**到 D 槽（不要刪）。不建議把整個 Installer 資料夾改成指向 D 槽的連結，因為 D 槽硬碟一出問題，軟體就無法修復或更新。
5. **移除大型軟體**：例如 Office 2013 的更新檔可能佔幾十 GB，只有使用者確定不用了才移除。

## 修復：大檔案與重複檔案（D 槽等資料碟）

1. 先跑 `scan-bigfiles.ps1`（只讀）：第一層資料夾大小、最大 30 個檔案、疑似重複（大小相同，加上開頭 1MB 和結尾 1MB 的 MD5 相同），完整清單存成 CSV 放在 `<Workdir>\reports\`。
2. 重複集中在兩個資料夾之間時（例如手機備份 a、b），再比較「同路徑、同大小」的檔案數，確認一個是不是另一個的子集。
3. **家庭照片影片**：如果兩份都在同一顆老硬碟上，提醒使用者那份重複其實是唯一的第二份，建議先備份到別處再刪。使用者仍決定要刪的話，照做。**刪完之後**還要：(a) 在回報裡明講「現在只剩一份，放在哪個路徑」；(b) 把「備份這個資料夾」列進結案報告的待辦和筆記的「未來小提醒」；(c) 記進專案記憶，下次連到這台電腦時主動提起，直到使用者說已經備份好。
4. 刪除前一定要對**全部**檔案做完整 MD5 比對，全部相同才刪；有任何不一致或比對沒跑完，就停下不刪。`Remove-Item` 不會進資源回收筒，刪除前要告訴使用者。
5. **分頁檔**：系統自動管理時，分頁檔可能長到幾十 GB。改成固定大小（記憶體 16GB、平常用量不高的話，設 8GB 就夠）：關掉 `AutomaticManagedPagefile`，再設 `Win32_PageFileSetting` 的 InitialSize 和 MaximumSize。**關掉自動管理後，Windows 可能自己在 C 槽加一筆 0/0（系統管理大小）的設定，要刪掉**，再確認登錄檔的 `PagingFiles` 只剩你要的那一筆。需要重開機才會生效。
6. `D:\DUMP*.tmp` 這類記憶體傾印暫存檔可以直接刪除。

## 修復：開機項目

1. 用 `Get-WmiObject Win32_StartupCommand` 列出 `Name`、`Location`、`User`。
2. 分類給使用者勾選：🔴 建議停（已停止服務、重複、吃資源）、🟡 看你用不用、🟢 保留（音效、輸入法、銀行、防毒）。
3. 先 `reg export <該 Run 區段> <Workdir>\startup_backup\run_NN.reg /y` 備份。
4. `reg delete <區段> /v <名稱> /f`。32 位元的程式可能在 `WOW6432Node` 底下，兩個位置都要處理。
5. 啟動資料夾裡的捷徑，搬到 `<Workdir>\startup_backup\` 就好，不要刪除。
6. 告訴使用者要重開機才會生效，雙擊 `.reg` 可以還原。

## 修復：Wi-Fi 開機連錯

```powershell
netsh wlan show profiles                       # 是「所有使用者設定檔」才能在登入前連線
netsh wlan set profileorder name="<正確的>" interface="Wi-Fi" priority=1
netsh wlan set profileparameter name="<正確的>" connectionmode=auto
netsh wlan set profileparameter name="<搶先的>" connectionmode=manual
```

設定檔如果是「使用者設定檔」，要先匯出，再用 `user=all` 重新加入。匯出時加了 `key=clear` 的話，檔案裡會有明文密碼，用完要立刻刪掉。

## 修復：WinRM 立即啟動

```powershell
sc.exe config WinRM start= auto
Set-ItemProperty HKLM:\SYSTEM\CurrentControlSet\Services\WinRM -Name DelayedAutostart -Value 0 -Type DWord
```

## 自動登入與儀表板自動啟動

- 自動登入：請使用者自己執行 `netplwiz`。完成後檢查 `HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon`：`AutoAdminLogon=1`，而且**沒有** `DefaultPassword`。
- 每次登入都啟動儀表板：`deploy-dashboard.ps1 -AutoStart`，或手動在 HKCU Run 加 `cmd.exe /c start "dashboard" /min "<bat>"`。只想下次登入執行一次的話，改用 RunOnce。

## 遠端重開機

```powershell
shutdown.exe /r /t 60 /c "Claude 將在 60 秒後重新開機，請先儲存工作。"
```

使用者想取消，可以打 `shutdown /a`。同時在主控機背景跑 `wait-reboot.ps1`。

## 關閉遠端管理（使用者要收尾時）

```powershell
Disable-PSRemoting -Force
Stop-Service WinRM; Set-Service WinRM -StartupType Disabled
Get-NetFirewallRule -Name 'WINRM-HTTP-In-TCP*' | Disable-NetFirewallRule
```

主控機也要從信任清單移除，並刪掉加密帳密檔，以及 `targets.json` 裡那一台的資料。
