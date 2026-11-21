---
name: win8-rescue
description: 拯救舊 Windows 一條龍：目標電腦是 Windows 7／8／8.1（或 1809 以前的 Win10），裝不了 Claude Code，就讓 Claude Code 待在同一個區網的另一台電腦（主控機），用 PowerShell 遠端管理（WinRM）連進去健檢、修問題、部署「病床邊監視器」儀表板，並讓它重開機、沒人登入時也連得到，也能在它的桌面上開網址、Google 搜尋、播 YouTube、開程式、關分頁、用記事本顯示文字、截圖看它的畫面、用語音念出文字，最後寫筆記。只要使用者提到 Win8、Win8.1、Win7、舊電腦、舊筆電要健檢或整理、安裝 Claude 時出現 'irm' 不是內部或外部命令、版本號 6.3.9600 或 6.1.7601、想從另一台電腦遠端管理或監看舊電腦、想替舊電腦做儀表板，或說「連 <已登記的電腦名稱>」「在那台舊電腦開 YouTube」「幫我在舊電腦打開漫畫瀏覽器」之類要接續操作已設定好的舊電腦，即使沒說「拯救」兩個字也要用本 skill。不適用：目標本身是 Win10 1809 以上或 Win11（直接在那台裝 Claude Code）、只想把舊電腦重灌成 Linux、純遠端桌面看畫面（AnyDesk、RustDesk）的設定問題。
---

# 拯救舊 Windows 一條龍

舊 Windows 裝不了 Claude Code（需要 Win10 1809 以上），WSL 也沒有。解法是**遠距看診**：Claude Code 跑在同一個區網裡的主控機（Win10／11），透過 Windows 內建的 PowerShell 遠端管理（WinRM）對目標電腦下指令。目標電腦不用安裝任何東西。

全程用繁體中文、口語跟使用者說明。使用者通常不是工程師，給他在目標電腦上操作的指令時，**一次只給一行**（貼上時換行常會消失，兩行黏成一行就會出錯），並說明這行在做什麼。

## 工具（都在本 skill 資料夾）

| 檔案 | 在哪跑 | 用途 |
|---|---|---|
| `scripts/setup-controller.ps1` | 主控機，**使用者**以系統管理員身分執行 | 加信任清單、讓使用者輸入目標電腦的密碼並加密存檔、登記到 `~/.win8-rescue/targets.json` |
| `scripts/run.ps1` | 主控機，Claude 用 | 對目標電腦送指令。**所有遠端操作都經過它**，才會留下紀錄並出現在儀表板 |
| `scripts/healthcheck.ps1` | 透過 `run.ps1 -CmdFile` 送去 | 第一輪健檢，只讀 |
| `scripts/scan-cdrive.ps1` | 同上 | C 槽空間分析（會跳過資料夾捷徑，不會重複計算） |
| `scripts/installer-cache.ps1` | 同上 | 分析 `C:\Windows\Installer`：孤兒檔數量、各產品佔多少 |
| `scripts/scan-bigfiles.ps1` | 主控機，Claude 用（放背景） | 資料碟的大檔案、疑似重複檔案分析（只讀），完整清單存成 CSV。處理方式見 `fixes.md` |
| `scripts/deploy-dashboard.ps1` | 主控機，Claude 用 | 部署儀表板、桌面捷徑，並可設定每次登入自動啟動 |
| `scripts/wait-reboot.ps1` | 主控機，放背景跑 | 等目標重開機後重新上線，回報登入狀態和 Wi-Fi |
| `scripts/open-on-desktop.ps1` | 主控機，Claude 用 | 在使用者看得到的桌面打開網址、Google 搜尋或程式 |
| `scripts/desktop-run.ps1` | 主控機，Claude 用 | 在使用者桌面執行 `assets/desktop/` 裡的小程式（WinRM 碰不到桌面，改用排程器代為執行） |
| `assets/desktop/window.ps1` | 透過 `desktop-run.ps1` 執行 | 對視窗做動作：`close-tab`、`maximize`、`minimize`、`front`，帶到前景時不改變大小 |
| `scripts/screenshot.ps1` | 主控機，Claude 用 | 拍目標的螢幕傳回主控機（`~/.win8-rescue/shots/`），再用 Read 看圖；傳回後會刪掉目標上的檔案 |
| `scripts/speak.ps1` | 主控機，Claude 用 | 讓目標用內建語音念出文字（預設台灣中文 Hanhan），會回報用了哪個語音、念了多久 |
| `scripts/job-submit.ps1` | 主控機，Claude 用 | 把一個資料夾（程式＋資料）用 SMB 傳到 `<Workdir>\jobs\<名稱>_<時間>\`，在背景執行，跑完用語音通知 |
| `scripts/job-status.ps1` | 主控機，Claude 用 | 查工作狀態（running／done、結束碼、花費時間）、CPU、輸出最後幾行；不給 `-Job` 就列出全部工作 |
| `scripts/job-fetch.ps1` | 主控機，Claude 用 | 把工作資料夾整個取回主控機（預設 `~/.win8-rescue/jobs/<工作>`） |
| `scripts/close-tab.ps1` | 主控機，Claude 用 | `window.ps1 close-tab` 的捷徑：關掉目前分頁標題含某個字的 Chrome 分頁，標題不符就不動作 |
| `assets/dashboard/` | 被部署到目標電腦 | 儀表板網頁＋每 2 秒寫數值的收集程式 |
| `references/target-setup.md` | 給使用者照著做 | 目標電腦開啟遠端管理的步驟 |
| `references/fixes.md` | Claude 參考 | 健檢結果怎麼判讀、每種修復的指令與注意事項 |
| `references/pitfalls.md` | Claude 參考 | 實際踩過的坑與解法，卡住時先查這裡 |

送指令的寫法（Windows PowerShell 工具）：

```powershell
& "$HOME\.claude\skills\win8-rescue\scripts\run.ps1" -Target OLDPC -Title '查瀏覽器' -Cmd @'
...要在目標電腦執行的 PowerShell 4.0 指令...
'@
& "$HOME\.claude\skills\win8-rescue\scripts\run.ps1" -Target OLDPC -Title '第一輪健檢' -CmdFile "$HOME\.claude\skills\win8-rescue\scripts\healthcheck.ps1"
```

`-Title` 用中文寫一句「在做什麼」，它會成為儀表板上那筆紀錄的標題。目標電腦是 PowerShell 4.0（Win8.1）或 2.0（Win7），送過去的指令不能用 5.0 以後的語法，例如 `Get-LocalUser`、`::new()`、`-AsHashtable`。

## 流程

已經設定過的電腦（`targets.json` 裡有）直接跳到第 5 階段。先用 `run.ps1` 送一個 `whoami` 確認連得上；連不上就查 `references/pitfalls.md` 的「連不上」。

### 1. 確認狀況、盤點硬體

- 從使用者貼的錯誤訊息或 `ver` 判斷版本：`6.1` 是 Win7，`6.2` 是 Win8，`6.3` 是 Win8.1。告訴他為什麼裝不了 Claude Code，以及為什麼改走遠端。
- 請他在目標電腦分兩次執行 `systeminfo` 和 `wmic diskdrive get model,size`，看機型、CPU、記憶體、硬碟（SSD 還是傳統硬碟）。
- 如果使用者真正想要的是「在這台用 Claude」而不是「管理這台」，先提另外兩條路：改裝 Linux，或把它當遠端終端機。讓他選，不要預設。
- **Win7 要先升級 PowerShell**：Win7 內建的是 PowerShell 2.0，本 skill 的程式需要 4.0 以上。請使用者先安裝 .NET Framework 4.5.2 和 WMF 5.1（微軟官方下載），重開機後再繼續。Win8.1 內建 4.0，不用另外安裝。

### 2. 讓兩台在同一個網段

- 主控機：`Get-NetIPAddress -AddressFamily IPv4` 查 IP 和閘道。目標電腦：請使用者打 `ipconfig`。
- IP 前三段相同（例如都是 `192.168.0.x`）才算同一區。不同的話，多半是目標連到另一台路由器的 Wi-Fi，請使用者改連主控機所在的那個 Wi-Fi，或插網路線接同一台設備。
- 確認：從主控機 ping 目標 IP，並用 `nbtstat -A <IP>` 核對電腦名稱。

### 3. 目標電腦開啟遠端管理（使用者操作）

照 `references/target-setup.md` 一步一步帶。重點：

- Win8.1 的 Win+X 給的是 CMD，要在視窗裡打 `powershell` 切換，提示字元變成 `PS` 開頭才對。
- 防火牆**只開給主控機那一個 IP**。這台沒有安全更新，入口越小越好。
- 帳號一定要有密碼（Windows 遠端不接受空密碼）。用 Ctrl+Alt+Del →「變更密碼」設定，舊密碼留空。密碼由使用者自己輸入，Claude 不經手。
- 最後請他打 `whoami`，拿到正確的帳號名稱（例如 `oldpc\user`）。

### 4. 主控機設定並測試連線

請使用者在主控機用**系統管理員** PowerShell 執行（Claude 通常沒有系統管理員權限，改不了信任清單）：

```powershell
& "$HOME\.claude\skills\win8-rescue\scripts\setup-controller.ps1" -Name OLDPC -Ip 192.168.0.50 -User 'OLDPC\user' -Workdir 'D:\Claude\rescue'
```

`-Workdir` 是目標電腦上存放紀錄、儀表板、筆記的資料夾，選一個不在 C 槽的位置。設定好之後，Claude 送 `whoami` 和系統管理員權限檢查。拿到 `IsAdmin: True` 就成功了。

### 5. 第一輪健檢（只讀）

`run.ps1 -CmdFile scripts/healthcheck.ps1`。判讀方法見 `references/fixes.md` 的「判讀」，有幾個常見的假警報（例如 Kernel-General 11、Schannel 36887）不要當成問題報出去。

回報格式：先列「健康的部分」，再列「需要處理的問題」表格（# / 問題 / 白話說明），**依嚴重度排序**，最後給可以遠端處理的選項（A、B、C⋯）和需要使用者親自處理的事。問他要做哪些。

### 6. 修復（每一項都要使用者同意）

使用者挑好之後才動手。做法見 `references/fixes.md`。每一項都要：

1. 先記錄改前狀態。
2. 會刪東西的先備份（登錄檔用 `reg export`，存到目標的 `Workdir`）。
3. 執行。
4. 列出改前／改後對照表。

空間不夠時，先跑 `scan-cdrive.ps1` 看實際分布，再決定。`C:\Windows\Installer` 很大時，跑 `installer-cache.ps1`：只有孤兒檔可以搬走；仍在使用的檔案不能刪，只能透過移除對應的軟體來釋放。

### 7. 儀表板與即時紀錄

```powershell
& "$HOME\.claude\skills\win8-rescue\scripts\deploy-dashboard.ps1" -Target OLDPC -AutoStart
```

- 部署到 `<Workdir>\dashboard\`，並在桌面和 `Workdir` 各放一份 `Claude儀表板.bat`。`-AutoStart` 會讓它每次登入都自動啟動（縮到最小）。
- 畫面是病床邊監視器的風格：CPU 和記憶體畫成心電圖掃描線，旁邊是磁碟、溫度、電池，右邊列出 Claude 的每個指令和回應，上方燈號在 Claude 連線時變綠。
- 部署後請使用者雙擊 bat，然後送 2 到 3 個測試指令（打招呼、檢查網路、10 秒 CPU 負載），讓他看到紀錄跳出來、燈號變綠、曲線起伏。
- 溫度需要系統管理員權限才讀得到，一般執行會顯示「—」，這是正常的。
- 想要純文字視窗的話，請使用者執行 `Get-Content <Workdir>\remote_log.txt -Wait -Encoding UTF8`。

### 8. 重開機也連得到

逐項說明後再做：

- **Wi-Fi**：開機時可能先連到別的已存 Wi-Fi（另一個網段、公用網路），登入後才換回正確的那個。把正確的設成第一優先並自動連線，會搶先的那幾個改成手動連線（`netsh wlan set profileparameter ... connectionmode=manual`）。
- **WinRM 立即啟動**：預設是延遲啟動，開機後要等約 5 分鐘才連得到。把登錄檔的 `DelayedAutostart` 改成 0，可以縮短到 1 到 2 分鐘。
- **自動登入**（使用者想讓儀表板開機就出現時才做）：請他自己執行 `netplwiz`，取消勾選「必須輸入使用者名稱和密碼」。這樣密碼會用 LSA 加密存放。事後確認 Winlogon 裡**沒有** `DefaultPassword` 明文欄位。說清楚代價：任何人實際碰到這台電腦都能直接進去。
- **重開測試**：用 `shutdown.exe /r /t 60 /c "<提示>"` 給 60 秒倒數，同時在背景跑 `wait-reboot.ps1 -Target <名稱>`。請使用者**停在登入畫面不要登入**，用來驗證沒人登入時也連得到。

### 9. 依使用者需要

- **電池**：`powercfg /batteryreport /output <Workdir>\battery-report.html`，解析設計容量、滿充容量、容量歷史。如果容量歷史「越來越高」，多半是換過電池或電量計重新校正過。提醒膨脹的徵兆。要找替換電池時，用料號上網搜尋，台灣通路優先（PChome、蝦皮、露天），附上來源連結。
- **遠端開機**：查 `Get-NetAdapterPowerManagement` 和 `powercfg /devicequery wake_programmable`。Wi-Fi 網卡幾乎都不支援從關機狀態喚醒；有線網卡才有機會，還要 BIOS 支援。誠實說明可不可行，再給替代方案（插電時永不睡眠只關螢幕、定時喚醒、無線轉有線橋接器）。

- **在桌面開網址或程式**：WinRM 在背景工作階段執行，直接 `Start-Process` 開的視窗使用者看不到。改用 `open-on-desktop.ps1 -Target <名稱> -Url <網址>`（或 `-Search '<關鍵字>'`、`-Exe <程式> -Arguments <參數>`），它會用排程器以登入使用者的身分開啟，開完再自動把視窗帶到前景（加 `-Maximize` 則放大）。需要有人登入才行。使用者說的程式名稱找不到時，多半是免安裝版：先在使用者放軟體的資料夾，用中英文關鍵字比對資料夾和 exe 名稱，找到後說出完整路徑再開。Chrome 已經開著時，新的程序會把網址交給舊視窗後立刻結束，所以從遠端找不到那個程序是正常的，要請使用者看螢幕確認。
- **播放影片**：YouTube 要直接開影片頁（`watch?v=<ID>&autoplay=1`），開搜尋頁還要有人點選。影片 ID 可以在主控機抓 `youtube.com/results?search_query=...` 的頁面，用正規表示式取出 `"videoRenderer":{"videoId":"..."` 和標題，選官方版本。廣告的「略過」按鈕必須由使用者自己點。
- **截圖看畫面**：`screenshot.ps1 -Target <名稱>` 會印出 `LOCAL=<路徑>`，再用 Read 讀那張圖。截圖會拍到螢幕上所有內容，所以只在使用者要求，或為了確認自己剛做的桌面操作時才拍，並告訴他拍了。**做完桌面操作後拍一張來驗證**，不要只相信程式回報「已開啟」：實戰中就是靠截圖才發現記事本沒有換行、舊視窗擋在新視窗前面。
- **讓電腦說話**：`speak.ps1 -Target <名稱> -Text '<要念的話>'`。先用 `System.Speech` 的 `GetInstalledVoices()` 查有哪些語音（Win8.1 繁中版通常有 zh-TW 的 Hanhan；Win7 通常只有英文語音，念中文會跳過或念錯）。數字用中文寫，例如「十八度」，比「18°C」念得自然。一段控制在 15 秒以內，比較長的內容拆成幾段。念完請使用者確認有沒有聽到：沒聲音多半是系統靜音或喇叭音量太小，這些 Claude 看不到。
- **在對方螢幕上顯示一段文字**（例如天氣、提醒、說明）：不要用模擬鍵盤打字，中文和換行很容易打錯。先用 `run.ps1` 把內容寫成 `<Workdir>\<主題>.txt`，**存成 UTF-8 with BOM，而且換行一定要是 CRLF**（Win8.1 的記事本沒有 BOM 會把中文判斷成 ANSI，只有 LF 的話整篇會擠成一段；寫檔前先做 `-replace "\`r?\`n", "\`r\`n"`），再用 `open-on-desktop.ps1 -Exe notepad.exe -Arguments '"<檔案路徑>"'` 打開，路徑要加雙引號。內容要註明資料時間和來源；使用者沒指定地點等條件時，說出你選了什麼、為什麼這樣選。
- **查天氣**：在主控機抓 `https://wttr.in/<英文城市名>?format=j1`，用 `Invoke-WebRequest -UseBasicParsing` 取 `.Content`，再 `ConvertFrom-Json`。不要加 `lang=` 參數，加了之後 `Invoke-RestMethod` 解析出來會是空的。天氣描述是英文，自己翻成中文。
- **關分頁**：`close-tab.ps1 -Target <名稱> -Match <標題關鍵字>`。Chrome 只露出每個視窗「目前顯示的分頁」的標題，所以只能關到正在顯示的那一個；不符合就不動作，以免關錯。關掉整個 Chrome 會一併關掉儀表板，不要這樣做。
- **能操作到什麼程度要說清楚**：搜尋用搜尋結果網址就能做到；點按鈕、填表單需要 Chrome 的遠端除錯埠（在沒有更新的舊系統上開一個無保護的控制埠，風險太高）或盲打鍵盤（看不到畫面），都不建議。**登入一律請使用者自己來**，密碼不經過 Claude，也不能進紀錄檔。需要看畫面操作時，建議用 AnyDesk 或 RustDesk。

- **當背景運算機**：舊電腦常裝有 Python、R、Stata、EViews、SAS 等。先盤點版本（舊版 Python 3.9、R 4.1 這類，新套件可能裝不上）。流程是 `job-submit.ps1 -Target <名稱> -LocalDir <資料夾> -Command '<指令>'` → `job-status.ps1` 查進度 → `job-fetch.ps1` 取回結果。程式在工作資料夾裡執行，指令用相對路徑。提醒使用者：舊 CPU 比新電腦慢，好處是不佔用主力電腦；長時間滿載會很熱，要搭配儀表板看溫度；含個資或 IRB 管控的資料不要放在沒有安全更新的電腦上。

### 10. 收尾

- **筆記**：使用者要的話，用 `learn-notes` 的格式，在目標的 `Workdir` 和主控機上的對應資料夾各寫一份（`LEARN.md`＋`learns/YYYYMMDD_<電腦名稱>遠端健檢.md`）。筆記不寫任何密碼。
- **記憶**：在專案記憶留一則 reference，記下這台的 IP、帳號、`Workdir`、做過哪些修改、使用者做了哪些決定，下次說「連 <電腦名稱>」才能直接接上。
- **結案報告**：列出處理結果表、尚未處理而需要使用者自己來的事（清灰塵、更新停在哪一年、電池，以及刪掉重複檔後**只剩一份、還沒備份**的資料夾），以及之後怎麼再連線、怎麼關閉遠端管理（`Disable-PSRemoting -Force`）。

## 原則

- **改東西前問，讀東西不用問。** 健檢、掃描、報告都是只讀的，可以直接做。分享、服務、登錄檔、開機項目、電源設定、Wi-Fi、重開機，都要使用者明確同意，而且同意只適用於他點名的那幾項。
- **使用者看得到 Claude 在做什麼。** 所有遠端操作都經過 `run.ps1`，紀錄會留在 `remote_log.txt` 和儀表板上。不要繞過它直接用 `Invoke-Command`，部署大檔案時例外，例如 `deploy-dashboard.ps1` 會在部署完後補一筆紀錄。
- **密碼只由使用者輸入。** 用 `Get-Credential` 加密存檔、`netplwiz`、Ctrl+Alt+Del 變更密碼。Claude 不要求使用者在對話裡告訴他密碼，也不把密碼寫進任何檔案或筆記。
- **含中文的 .ps1 一定要存成 UTF-8 with BOM。** 主控機的 Windows PowerShell 5.1 和目標的 4.0 都會把沒有 BOM 的檔案當成 ANSI 讀，中文就會變亂碼。
- **舊系統的極限要說清楚。** 停在多年前的 Windows 更新補不回來，建議使用者不要在這台登入網路銀行或重要帳號。
