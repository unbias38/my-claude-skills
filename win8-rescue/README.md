# win8-rescue｜拯救舊 Windows 一條龍

舊電腦（Windows 7／8／8.1）裝不了 Claude Code，那就讓 Claude Code 待在**同一個區網的另一台新電腦（主控機）**，透過 Windows 內建的 PowerShell 遠端管理（WinRM）隔空幫舊電腦健檢、整理、操作。**舊電腦不用安裝任何東西。**

> 舊電腦裝不了 AI，就讓 AI 待在新電腦上，遠端幫它健檢、整理、操作。

## 能做什麼

| 類別 | 功能 |
|---|---|
| **健檢** | 硬碟 SMART、磁碟空間、系統錯誤事件、防毒、更新停在哪年、開機項目、溫度、電池、危險分享與 SMB1 |
| **整理** | C 槽空間分析（不會被資料夾捷徑重複計算）、`C:\Windows\Installer` 分析、大檔案與重複檔案（完整比對後才刪）、分頁檔調整、開機項目整理（先備份） |
| **監看** | 「病床邊監視器」風格的儀表板：CPU／記憶體心電圖掃描線、磁碟、溫度、電池；右側即時列出 Claude 送的每個指令與回應；Claude 連線時燈號變綠 |
| **桌面操作** | 開網址、Google 搜尋、播 YouTube、開程式並帶到前景、關分頁、放大縮小視窗、用記事本顯示文字、**截圖給 Claude 看**、**用內建語音說話** |
| **背景運算** | 把程式資料夾丟過去在背景跑（Python、R、Stata⋯），查進度、跑完語音通知、取回結果 |
| **重開機也連得到** | Wi-Fi 開機連對網路、WinRM 立即啟動、自動登入、儀表板開機自動開；重開機後背景等待並回報 |

**做不到的：** 在網頁上點按鈕、填表單、**登入**（密碼一律由使用者自己輸入，不經過 Claude）。需要看著畫面操作時，請用 AnyDesk、RustDesk 這類遠端桌面。

## 需要什麼 ⚙️

| 條件 | 說明 |
|---|---|
| **主控機** | Windows 10 1809 以上或 Windows 11，裝好 Claude Code |
| **舊電腦** | Windows 8／8.1 直接可以；**Windows 7 要先裝 .NET Framework 4.5.2 和 WMF 5.1**（PowerShell 要 4.0 以上）；XP 以前不行 |
| **網路** | 兩台在**同一個區網**（IP 前三段相同，例如都是 `192.168.0.x`） |
| **帳號** | 舊電腦的登入帳號要**有密碼**（Windows 遠端不接受空密碼） |

## 安裝

照 repo 根目錄 README 的方式，把 `win8-rescue` 資料夾複製到主控機的 `~/.claude/skills/`，重開 Claude Code。

然後跟 Claude 說「我有一台 Win8 舊電腦想健檢」，它會一步一步帶你：

1. **舊電腦**（照 `references/target-setup.md`）：網路設成私人 → `Enable-PSRemoting -Force` → 防火牆只允許主控機的 IP → 確認帳號有密碼。
2. **主控機**（以系統管理員身分執行一次）：

   ```powershell
   & "$HOME\.claude\skills\win8-rescue\scripts\setup-controller.ps1" -Name OLDPC -Ip 192.168.0.50 -User 'OLDPC\user' -Workdir 'D:\Claude\rescue'
   ```

   它會把舊電腦加入信任清單、**讓你自己輸入密碼**並用 Windows 加密存成檔案（只有這台電腦、這個帳號解得開）、登記到 `~/.win8-rescue/targets.json`。

之後說「連 OLDPC」就能接著做。可以登記好幾台。

## 安全設計

- **改東西之前一定先問**，讀東西（健檢、掃描）不用問；會刪的東西先備份或先完整比對。
- 防火牆**只開給主控機一台**；密碼只由使用者輸入，用 Windows DPAPI 加密存在主控機，不進任何紀錄或筆記。
- **所有遠端指令都留紀錄**：寫進舊電腦的 `<Workdir>\remote_log.txt`，也即時顯示在儀表板上，使用者看得到 Claude 做了什麼。
- 截圖傳回主控機後，會立刻刪掉舊電腦上的那份。
- 舊系統沒有安全更新：建議不要在那台登入網路銀行、處理個資或研究受試者資料。

## 檔案

```
win8-rescue/
├── SKILL.md                    流程（10 個階段）與原則
├── scripts/                    在主控機上執行的工具
│   ├── setup-controller.ps1    新增一台舊電腦
│   ├── run.ps1                 送指令（所有遠端操作都經過它，自動留紀錄）
│   ├── healthcheck.ps1         第一輪健檢
│   ├── scan-cdrive.ps1         C 槽空間分析
│   ├── installer-cache.ps1     Installer 資料夾分析
│   ├── scan-bigfiles.ps1       大檔案與重複檔案
│   ├── deploy-dashboard.ps1    部署儀表板
│   ├── wait-reboot.ps1         等重開機並回報
│   ├── open-on-desktop.ps1     在桌面開網址、搜尋、開程式
│   ├── desktop-run.ps1         在使用者桌面執行小程式（通用）
│   ├── close-tab.ps1           關 Chrome 分頁
│   ├── screenshot.ps1          截圖
│   ├── speak.ps1               語音
│   └── job-submit／job-status／job-fetch.ps1   背景運算
├── assets/
│   ├── dashboard/              儀表板網頁＋數值收集程式
│   ├── desktop/                在使用者桌面執行的小程式（視窗、截圖、語音、工作看管）
│   └── remote/                 送到舊電腦執行的分析程式
└── references/
    ├── target-setup.md         舊電腦開啟遠端管理的步驟
    ├── fixes.md                健檢判讀與修復手冊
    └── pitfalls.md             實戰踩過的約 40 個坑與解法
```

所有含中文的 `.ps1` 都是 **UTF-8 with BOM**，請保持；改成沒有 BOM，Windows PowerShell 5.1／4.0 會把中文讀成亂碼。
