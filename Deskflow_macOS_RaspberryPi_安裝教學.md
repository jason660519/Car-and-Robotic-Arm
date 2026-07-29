# Deskflow 安裝教學：macOS (Apple Silicon) + Raspberry Pi (Wayland/labwc)

> 適用情境：一台 macOS（M 系列 Apple Silicon）作為 **Server**（提供鍵盤滑鼠），
> 一台 Raspberry Pi 5（Raspberry Pi OS，桌面環境為 **labwc / wlroots**，Wayland session）作為 **Client**。
>
> 本文件根據實際安裝過程整理，記錄了會遇到的坑與對應解法。

---

## 環境資訊

| 項目 | 內容 |
|---|---|
| Server | macOS，M 系列 Apple Silicon |
| Client | Raspberry Pi 5，Raspberry Pi OS |
| Client 桌面環境 | `labwc:wlroots`（可用 `echo $XDG_CURRENT_DESKTOP` 確認） |
| Client session 類型 | `wayland`（可用 `echo $XDG_SESSION_TYPE` 確認） |
| 軟體 | [Deskflow](https://github.com/deskflow/deskflow) v1.26.0 |
| Client 安裝方式 | Flatpak（因 Raspberry Pi OS 內建的 Qt/libei 版本通常過舊，無法直接跑原生 Deskflow GUI） |

---

## Part 1：macOS（Server 端）安裝

### 1.1 用 Homebrew 安裝

```bash
brew tap deskflow/tap
brew install deskflow
```

**踩雷點：** 如果出現以下錯誤：
```
Error: Refusing to load cask deskflow/tap/deskflow from untrusted tap deskflow/tap.
```
代表你的 Homebrew 環境是客製化／包裝過的版本（標準 Homebrew 沒有這個機制）。解法：
```bash
brew trust deskflow/tap
brew install deskflow
```

### 1.2 排除「已損毀」的警告

Deskflow 沒有經過 Apple 憑證公證（notarization），第一次開啟會顯示「已損毀」：
```bash
xattr -c /Applications/Deskflow.app
```

### 1.3 授予權限

打開 Deskflow.app 後，前往 **系統設定 → 隱私權與安全性**：
- 開啟 **輔助使用（Accessibility）** 權限（給 Deskflow app 與 deskflow process）
- macOS Sequoia 以上：另外在 **本機網路（Local Network）** 設定中允許 Deskflow

### 1.4 設定為 Server

- 開啟 Deskflow → 選 **「Use this computer's keyboard and mouse (make this computer the server)」**
- App 上方會顯示 `Suggested IP`，記下這組 IP（例如 `192.168.1.246`），等下 Client 端要用
- 點 **Configure Server → Computers** 分頁，把 Client（樹莓派）的螢幕名稱加進來，並拖曳到符合實體擺放位置的方向（左／右／上／下）

---

## Part 2：Raspberry Pi（Client 端）安裝

### 2.1 用 SSH 連線

先在樹莓派本機（或已知連線方式）確認使用者名稱與 IP：
```bash
whoami          # 確認使用者名稱
hostname -I     # 注意是大寫 I，取得實際網路 IP（不要用小寫 -i，那只會回傳 127.0.1.1）
```

從 Mac 連線：
```bash
ssh <使用者名稱>@<樹莓派IP>
# 或先試主機名稱（不一定每個網路都支援）：
ssh <使用者名稱>@raspberrypi.local
```

### 2.2 安裝 Flatpak 與 Deskflow

```bash
sudo apt update
sudo apt install flatpak
flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
flatpak search deskflow      # 確認搜尋得到 org.deskflow.deskflow
flatpak install --user flathub org.deskflow.deskflow
```

**踩雷點 1：** `flatpak remote-add` 用舊網址（`flathub.org/repo/...`）有時會加入失敗但不報錯，
導致後續 `flatpak search` 和 `flatpak install` 都找不到。用 `flatpak remotes` 確認 remote 是否真的存在；
若沒有，改用 `https://dl.flathub.org/repo/flathub.flatpakrepo` 這個網址重新加入。

**踩雷點 2：** 若用預設的 `flatpak install flathub ...`（system-wide 系統層級安裝），
每個相依套件都會跳出密碼驗證（polkit）。改用 `--user` 參數安裝在使用者層級，就不會一直要密碼。

### 2.3 啟動 Deskflow（需要在樹莓派的實體桌面/螢幕上執行，不能只靠 SSH）

在樹莓派接的螢幕上打開終端機：
```bash
flatpak run org.deskflow.deskflow
```

> ⚠️ Deskflow client 會開啟 GUI 視窗，純 SSH 文字介面無法顯示，一定要有實體螢幕或 VNC。

### 2.4 設定為 Client

- 選 **「Use another computer's mouse and keyboard (make this computer the client)」**
- 「Connect to」欄位輸入 Mac 的 IP（Part 1.4 記下的那組）
- 點 **Connect**

---

## Part 3：連線失敗排解（本次實際踩到的坑）

### 症狀
Client 端一直顯示：
```
Failed to connect to the server 'x.x.x.x'.
Please check your TLS and firewall settings.
```
Server 端 log 一直重複：
```
WARNING: client connection may not be secure
ERROR: failed to accept secure socket
```

看起來像 TLS／防火牆問題，**但實際上不是**。真正原因藏在 Client 端更早的 log 裡：
```
WARNING: can't open xkb display during reading languages
ERROR: failed to initialize remote desktop session: GDBus
```

### 真正原因

Raspberry Pi 的 Wayland compositor 是 `labwc`（屬於 wlroots 系列）。Deskflow 在 Linux/Wayland 上需要透過
`xdg-desktop-portal` 取得螢幕擷取／遠端輸入（`ScreenCast` / `RemoteDesktop`）的權限，而這兩個介面**只有
`xdg-desktop-portal-wlr` 有實作**，`xdg-desktop-portal-gtk` 並沒有。

系統雖然兩個 portal 套件都有裝，但沒有設定檔告訴 `xdg-desktop-portal` 主服務：「`ScreenCast` 和
`RemoteDesktop` 這兩個介面要繞去用 `wlr` 而不是預設的 `gtk`」，所以請求根本找不到能處理的後端，
於是 client 端連 TLS 握手都還沒真正走到就先失敗了 —— 但因為連線在 Server 端看起來像是「未完成的
不安全連線」，才誤導成看起來是 TLS／防火牆問題。

### 解法

在樹莓派上執行：

```bash
mkdir -p ~/.config/xdg-desktop-portal
cat > ~/.config/xdg-desktop-portal/labwc-portals.conf << 'EOF'
[preferred]
default=gtk
org.freedesktop.impl.portal.ScreenCast=wlr
org.freedesktop.impl.portal.RemoteDesktop=wlr
EOF

systemctl --user restart xdg-desktop-portal xdg-desktop-portal-wlr
```

然後重新啟動 Deskflow client：
```bash
flatpak run org.deskflow.deskflow
```

再次點 Connect，此時 log 應該不再出現 `GDBus` / `failed to initialize remote desktop session` 錯誤，
連線即可成功建立。

---

## 常見診斷指令備忘

| 目的 | 指令 |
|---|---|
| 確認 Wayland/桌面環境 | `echo $XDG_SESSION_TYPE` / `echo $XDG_CURRENT_DESKTOP` |
| 確認 Pi 的實際 IP | `hostname -I`（大寫 I） |
| 確認 Flatpak remote 是否存在 | `flatpak remotes` |
| 確認 Deskflow 是否有支援的架構版本 | `flatpak search deskflow` |
| 確認 portal 套件是否已安裝 | `dpkg -l \| grep xdg-desktop-portal` |
| 確認 wlr portal 服務是否運作中 | `systemctl --user status xdg-desktop-portal-wlr` |
| 查看 wlr portal 啟動記錄 | `journalctl --user -u xdg-desktop-portal-wlr -n 50 --no-pager` |
| 確認 Flatpak App 的權限設定 | `flatpak info --show-permissions org.deskflow.deskflow` |

---

## 重點總結（給趕時間的人）

1. macOS：Homebrew 安裝 → `brew trust` 解決 untrusted tap → `xattr -c` 解決損毀警告 → 開輔助使用權限 → 設為 Server。
2. 樹莓派：用 **Flatpak（`--user` 安裝）** 而非原生套件 → 記得用 `dl.flathub.org` 網址加 remote → 需要實體螢幕（GUI 應用程式）→ 設為 Client。
3. 若出現「TLS/firewall」錯誤，**先別急著懷疑 TLS**，去看 client 端 log 有沒有 `GDBus` / `remote desktop session` 相關錯誤 —— 那通常代表 Wayland portal 沒有正確路由到 `xdg-desktop-portal-wlr`，照 Part 3 建立設定檔並重啟服務即可解決。
