# 目標電腦開啟遠端管理（帶使用者一步一步做）

每一步都只給一行指令，等使用者回報結果再給下一行。

## 1. 開系統管理員 PowerShell

- Win8／8.1：按 **Win + X** →「命令提示字元 (系統管理員)」→ 按「是」→ 在視窗裡打 `powershell` 按 Enter。
- Win7：開始 → 搜尋 `powershell` → 按右鍵 →「以系統管理員身分執行」。
- 確認提示字元是 `PS C:\Windows\system32>`，開頭要有 **PS**。

## 2. 網路設成「私人」

網路類型是公用時，Enable-PSRemoting 會失敗，防火牆也會擋。

```powershell
Get-NetConnectionProfile | Set-NetConnectionProfile -NetworkCategory Private
```

Win7 沒有這個指令。改請使用者到「網路和共用中心」，點目前網路下方的「公用網路」，改成「家用網路」或「工作場所網路」。

## 3. 開啟遠端管理

```powershell
Enable-PSRemoting -Force
```

這一行會啟動 WinRM 服務並設成自動啟動、建立防火牆規則，並設定讓本機管理員帳號從遠端連入時取得完整權限（LocalAccountTokenFilterPolicy）。

## 4. 防火牆只允許主控機

把 `<主控機IP>` 換成主控機的實際 IP：

```powershell
Get-NetFirewallRule -Name 'WINRM-HTTP-In-TCP*' | Set-NetFirewallRule -RemoteAddress <主控機IP>
```

確認（應該看到 `RemoteAddress : <主控機IP>`）：

```powershell
Get-NetFirewallRule -Name 'WINRM-HTTP-In-TCP*' | Get-NetFirewallAddressFilter
```

Win7 沒有 NetSecurity 模組，改用：

```
netsh advfirewall firewall set rule name="Windows 遠端管理 (HTTP-In)" new remoteip=<主控機IP>
```

規則名稱可能是英文的 `Windows Remote Management (HTTP-In)`，可以先用 `netsh advfirewall firewall show rule name=all | findstr /i "5985 遠端管理 Remote"` 找出來。

## 5. 確認帳號有密碼

教使用者按 **Win + L** 鎖定，再試著解鎖：

- 要輸入密碼才能進去：有密碼。
- 點一下就進去：沒有密碼，要設一個。按 **Ctrl + Alt + Delete** →「變更密碼」→ 舊密碼**留空**，輸入兩次新密碼。

這個方法比「開機會不會問密碼」準，因為開了自動登入的電腦，即使有密碼，開機也不會問。

## 6. 取得帳號名稱

```powershell
whoami
```

結果像 `oldpc\user`。如果出現電子郵件地址，表示用的是微軟帳號，主控機輸入帳號時要用 `MicrosoftAccount\<email>`。

## 完成後

請使用者到主控機執行 `setup-controller.ps1`（見 SKILL.md 第 4 階段）。主控機的 IP 也要用 DHCP 保留或固定，不然它的 IP 一變，防火牆就會把它擋在外面。
