# 踩過的坑（2026-11 實戰紀錄）

## 使用者端

| 症狀 | 原因 | 解法 |
|---|---|---|
| `'irm' 不是內部或外部命令` | 在 CMD 打了 PowerShell 指令 | 不只是視窗開錯，系統本身也太舊：說明裝不了 Claude Code，改走遠端 |
| `'Get-NetConnectionProfile' 不是內部或外部命令` | 開的是 CMD，提示字元沒有 `PS` | 在同一個視窗打 `powershell` |
| `FINDSTR: 無法開啟 diskdrive` 之類 | 兩行指令貼上後黏成一行 | 一次只給一行；長的改成 `systeminfo` 整段貼回來或截圖 |
| 中文的 findstr 條件沒有輸出 | CMD 的中文編碼不一致 | 改用不篩選的整段輸出 |

## 網路

| 症狀 | 原因 | 解法 |
|---|---|---|
| 兩台 IP 前三段不同、ping 不到 | 目標連到另一台路由器的 Wi-Fi（NAT 隔開） | 改連主控機所在的同一個 Wi-Fi |
| 使用者說插了網路線，但有線網卡是 `169.254.x.x` | 線沒接好，或那個孔沒有 DHCP；實際上走的是 Wi-Fi | 用 `Get-NetIPAddress` 看清楚是哪張網卡拿到 IP |
| 重開機後、沒人登入時連不到，登入後才連得到 | 開機時先自動連上另一個已存的 Wi-Fi（另一網段、公用網路），登入後才換回 | 正確的 Wi-Fi 設第一優先，搶先的那個改 `connectionmode=manual`；可查 `Microsoft-Windows-NetworkProfile/Operational` 事件 10000 看開機後依序連了哪些網路 |
| 開機後 4、5 分鐘才連得到 | WinRM 預設延遲啟動 | `DelayedAutostart=0` |
| 連得到但 5985 不通 | 目標 IP 變了（DHCP），或主控機 IP 變了被防火牆擋 | 主控機掃網段：對 1–254 平行 ping，再用 `arp -a` 比對 MAC |

## 程式與編碼

| 症狀 | 原因 | 解法 |
|---|---|---|
| 紀錄檔標題變成 `Claude ????隞?` | 含中文的 .ps1 存成無 BOM 的 UTF-8，PowerShell 5.1／4.0 當成 ANSI 讀 | 所有 .ps1 存成 UTF-8 with BOM |
| 自訂函式 `H` 卻跑去呼叫 `Get-History`，參數綁定錯誤 | PowerShell 的別名比函式優先，`h`、`r`、`gc`、`ls`、`cd` 這類短名稱都是內建別名 | 函式一律用「動詞-名詞」的完整名稱（例如 `Get-FileMd5Full`），不要取一兩個字母的名字 |
| `Get-Item D:\pagefile.sys -Force` 回報找不到檔案 | 系統正在使用中的分頁檔，從遠端讀不到它的屬性 | 改用 `Win32_PageFileUsage` 的 `AllocatedBaseSize`，或比較改前改後的磁碟剩餘空間 |
| 改登錄檔 `Windows Search\DataDirectory` 把搜尋索引搬到 D 槽，失敗 | 同時設了 `SetupCompletedSuccessfully=0` 時，重設會把位置改回預設；只改位置時，服務又報索引損毀、啟動不了（Win8.1 實測兩種都失敗） | 不要用登錄檔搬。請使用者自己用「索引選項 → 進階 → 新位置」（`control.exe srchadmin.dll`），Claude 開好視窗、用截圖帶他操作。失敗時要能還原：`DataDirectory` 改回 C 槽預設、`SetupCompletedSuccessfully=0`、啟動服務 |
| 背景工作一開始就停了，`status.txt` 卡在 running | `desktop-run` 拿到結果就刪除排程，**Windows 刪除排程時會終止排程啟動的程序**（TaskScheduler 事件 111）；它的子程序還在跑，但沒人負責收尾 | 排程啟動的程序先 `Start-Process` 另開一個獨立的看管程序，自己立刻結束（`run-job.ps1` 的兩段式寫法） |
| Python 輸出導到檔案時出現 `UnicodeEncodeError: 'cp950' codec can't encode` | Python 3.9 在台灣 Windows 上，輸出導向檔案時預設用 cp950，`≈`、emoji、簡體字等都會當掉 | 執行前設 `PYTHONIOENCODING=utf-8`、`PYTHONUTF8=1`；讀輸出時用 `Get-Content -Encoding UTF8` |
| `Get-ChildItem -Depth` 讓整段指令停下 | `-Depth` 是 PowerShell 5.0 才有的參數，4.0 會直接參數綁定錯誤 | 送去目標的指令只用 4.0 有的參數，例如改用 `-Recurse` 加篩選 |
| 沒加 `-AutoStart`，部署工具卻還是設了開機自動啟動 | `-ArgumentList ..., [bool]$AutoStart` 在指令模式下會被當成字串 `'[bool]False'`，非空字串永遠是真 | 先在外面算好 `$autoFlag = [bool]$AutoStart`，再傳 `$autoFlag` |
| 「比對後刪除」的腳本中途出錯 | 若沒防護，可能比對到一半就往下走到刪除 | 刪除前檢查「已比對數 = 總數」且不一致數為 0；腳本先在不刪除的模式下跑過 |
| Bash 跑多行 here-string（`@' '@`）出錯 | 那是 PowerShell 語法 | 對目標下指令一律用 PowerShell 工具，不要用 Bash |
| 掃 C 槽時 `Users` 顯示 346GB，比整顆硬碟還大 | `Get-ChildItem -Recurse` 跟著資料夾捷徑（junction，如 `Application Data`、`Documents and Settings`）重複計算 | 用 `scan-cdrive.ps1`，它會跳過帶 ReparsePoint 屬性的項目 |
| 健檢報出「一年內 326 筆硬碟錯誤」 | 只用事件 ID 篩選，抓到 Kernel-General 11 和 Kernel-Processor-Power 55（一般訊息） | 硬碟錯誤要同時對 ProviderName：disk 7/11/51/153、Ntfs 55 |
| 長時間掃描超過 10 分鐘被中斷 | 遠端遞迴列舉很慢，而且跟著捷徑繞圈 | 用 .NET 的 `EnumerateFileSystemInfos` 搭配堆疊、跳過捷徑；真的很久就放背景 |
| 儀表板在 file:// 讀不到資料 | Chrome 禁止 file:// 用 fetch | 資料寫成 `.js` 檔（`window.STATS=...`、`LOG.push(...)`），頁面用 script 標籤重新載入 |
| 遠端 `Start-Process chrome` 後，使用者螢幕上什麼都沒有 | WinRM 跑在 session 0（背景），不是使用者的桌面 | 用排程器以使用者身分、Interactive 模式執行（`open-on-desktop.ps1`） |
| `schtasks /create /tr "\"chrome.exe\" 網址"` 回報「錯誤的引數/選項」 | PowerShell 4.0 把含引號的原生指令參數拆壞了 | 改用 `Register-ScheduledTask` 和 `New-ScheduledTaskAction -Execute -Argument`，不要用 schtasks.exe |
| 開網址成功，但遠端查不到 Chrome 程序 | Chrome 已經開著時，新程序把網址交給舊視窗後就結束了 | 屬於正常；看排程的 LastTaskResult=0，再請使用者看螢幕確認 |
| 開程式回報「執行失敗，結果碼 267009」，但程式其實開了 | 267009＝0x41301＝SCHED_S_TASK_RUNNING，代表排程啟動的程式還開著（Chrome 交出網址後就結束，所以是 0） | 0 和 267009 都算成功；刪除排程不會關掉程式。用 `Win32_Process` 看 SessionId ≥ 1 確認 |
| 程式開了，但只在工作列閃，畫面還停在原本的視窗 | Windows 的前景鎖定：背景啟動的程式不能搶走前景 | `open-on-desktop.ps1` 開完會自動呼叫 `window.ps1 front`；裡面先用 `keybd_event` 模擬按放 Alt，再 `SetForegroundWindow` |
| 免安裝版開完後，用程式名稱找不到視窗 | 啟動器 `XxxPortable.exe` 會另外開 `Xxx.exe`，名字不同 | `window.ps1 -Recent 1`：同名找不到時，改抓 60 秒內新出現、有視窗的程式 |
| 記事本打開後整篇擠成一段，沒有換行 | 從主控機送過去的 here-string 換行是 LF；Win10 1809 以前的記事本只認 CRLF | 寫檔前 `-replace "\`r?\`n", "\`r\`n"`；之後拍截圖確認 |
| 想關掉舊視窗，用 `MainWindowTitle` 篩選卻什麼都沒找到 | 從 WinRM（session 0）看不到使用者桌面上視窗的標題，`MainWindowTitle` 都是空的 | 在背景時改用 `Win32_Process` 的 `CreationDate`、`CommandLine` 判斷；要用標題就透過 `desktop-run.ps1` 在桌面工作階段執行 |
| 截圖拍成功，但主控機拿不到檔名 | 結果檔是 UTF-8 with BOM，第一行開頭有 `﻿`，`^FILE=` 錨定比對不到 | 不要用 `^` 錨定，把整段接起來用 `FILE=([^\r\n]+)` 比對 |
| 從 WinRM 直接用 `SpeechSynthesizer` 念，使用者聽不到 | 背景工作階段（session 0）沒有音訊輸出 | 一定要透過 `desktop-run.ps1` 在桌面工作階段念（`speak.ps1`） |
| 中文文字傳到桌面後變成亂碼或被截斷 | 排程器的參數會經過引號處理和編碼轉換 | 把文字轉成 base64 再傳，桌面那端再解碼 |
| 想在記事本「打字」給使用者看 | 模擬鍵盤（SendKeys）打中文、換行、特殊符號都不可靠，而且看不到畫面，無法確認 | 先寫成 .txt 再用記事本打開；檔案要存成 UTF-8 with BOM，Win8.1 的記事本才不會顯示亂碼 |
| `Invoke-RestMethod "https://wttr.in/...?format=j1&lang=zh-tw"` 拿到空陣列（`Cannot index into a null array`） | 加了 `lang` 參數後，回應的解析出問題 | 不要加 `lang`，用 `Invoke-WebRequest -UseBasicParsing` 取 `.Content` 再 `ConvertFrom-Json` |
| 桌面上找不到使用者說的程式 | 很多是免安裝版（Portable），沒有登記在已安裝程式、也沒有捷徑 | 先問或先掃使用者放軟體的資料夾（例如 `D:\Software`、`D:\Games`），用中英文關鍵字比對資料夾名稱和 exe 名稱 |
| 關完分頁，整個 Chrome 視窗變小了 | 帶到前景時用了 `ShowWindow(h, 9)`（SW_RESTORE），會把最大化的視窗還原成一般大小 | 只有 `IsIconic`（縮在工作列）時才還原，其他情況只呼叫 `SetForegroundWindow`；已修正在 `window.ps1` |
| 指令還沒送出就出現 `Missing expression after unary operator` | 外層 `@' ... '@` 裡又有一行以 `'@` 開頭的內層 here-string，外層被提早截斷 | 要送去在使用者桌面跑的腳本，放在 `assets\desktop\`，用 base64 夾帶傳送（見 `close-tab.ps1`），不要巢狀 here-string |
| Chrome 109（Win8.1 最後版本）有些 CSS 不支援 | `color-mix()`、CSS 巢狀寫法要到 111、112 版以後 | 儀表板不使用這些語法 |

## 判斷上的坑

- Defender `productState=0x60100` 加上另一套防毒 `0x41000`：表示 Defender 已讓位、另一套在運作，屬於正常。
- `C:\Windows\Installer` 很大，不代表可以刪。先跑 `installer-cache.ps1`；全部都還被登記使用時，只能透過移除軟體來釋放空間。
- DISM 清理跑一分鐘就結束、空間沒變：用 `/AnalyzeComponentStore` 確認「可收回的套件數目」，如果是 0，代表已經是乾淨的，照實回報。
- 電池容量歷史「越來越高」：多半是換過電池或電量計重新校正，不是電池變好。
