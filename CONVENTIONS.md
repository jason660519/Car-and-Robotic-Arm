# 專案歸檔與命名規範

> 這份文件是本專案檔案擺放與命名的**單一真實來源（single source of truth）**。
> 任何時候不確定「這個檔案該放哪、該叫什麼」，以本文件為準。
> 與現況衝突時，是現況要改，不是本文件要改。

最後更新：2026-07-30

---

## 1. 資料夾結構

```
Car-and-Robotic-Arm/
├── README.md              專案入口
├── CONVENTIONS.md         ← 本文件
├── CLAUDE.md              AI agent 工作規則
├── pyproject.toml         Python 專案定義（uv 管理）
│
├── docs/                  我們寫的文件（Markdown）
│   ├── hardware/          硬體規格、通訊協定、接線
│   ├── setup/             環境建置步驟
│   └── adr/               架構決策紀錄
│
├── src/carbot/            Python package（實際會被 import 的程式）
├── tests/                 測試
├── examples/              可直接執行的示範腳本
├── scripts/               一次性工具、產生器
│
├── assets/                二進位資產
│   ├── inventory/         零件庫存照（編號序列）
│   ├── assembly/          組裝過程照（編號序列）
│   ├── reference/         參考圖：接線圖、規格表、截圖
│   └── assembly-guide/    組裝說明書的頁面圖與抽取文字
│
├── site/                  Astro 網站原始碼
│   ├── src/data/          頁面共用的資料檔 —— 中英文只有這一份
│   ├── src/pages/         路由（zh 在根、en 在 /en/）
│   ├── src/components/    元件
│   ├── src/layouts/       版型
│   ├── src/styles/        tokens.css + 各頁樣式
│   └── public/            直接複製到輸出的靜態檔
│
├── astro.config.mjs       建置設定（輸出到 _site/，不進版控）
├── package.json
│
└── vendor/                原廠資料，唯讀
    ├── yourfun-nezha/         有方機器人 NeZha 驅動板
    ├── keyes-37in1-sensor-kit/  37 合 1 感測器套件
    └── raspberry-pi/          Raspberry Pi 官方文件
```

## 2. 判斷檔案該放哪：只問一個問題

**「這個檔案是誰寫的？」**

| 誰寫的 | 放哪 | 可否修改 |
|---|---|---|
| 我們寫的文件 | `docs/` | 可改 |
| 我們寫的程式 | `src/` `tests/` `examples/` `scripts/` | 可改 |
| 我們拍的照片 | `assets/` | **只增不改**（改了會讓編號失去意義） |
| 網頁前端 | `site/` | 可改 |
| 原廠給的 | `vendor/` | **唯讀**，改了就失去對照價值 |
| 程式產生的暫存 | `scratch/` | 不進版控 |

`vendor/` 是硬規則。要基於原廠程式碼改寫，複製一份到 `src/` 或 `scripts/` 再改，
原始檔留在 `vendor/` 當對照組。

## 3. 命名規則

### 3.1 程式與文件 — `lower-kebab-case`

```
docs/hardware/nezha-i2c-protocol.md
scripts/build-assembly-html.py
site/inventory/index.html
```

**唯一例外**：Python 模組因為要被 `import`，用 `snake_case` —
`src/carbot/nezha.py`、`scripts/build_assembly_html.py`。

### 3.2 雙語文件 — 主檔 + `.en` 後綴

```
raspberry-pi-5-pinout.md      繁體中文（主檔）
raspberry-pi-5-pinout.en.md   English
```

不用 `_EN.md`。`.en.md` 是 i18n 慣例，建置工具認得。
只有單一語言版本時，直接用 `name.md`，語言在文件開頭標示。

### 3.3 資產照片 — `NNN_Title_Case_Description.ext`

```
assets/inventory/027_Waveshare_PanTilt_HAT_Front.jpg
assets/assembly/003_Car_Chassis_Bottom_Wiring.jpg
```

- `NNN` 是**入庫流水號，三位數補零**
- **編號一旦分配就不重用、不重排、不回收**。零件退掉了，編號也留著空著。
- 編號是**跨資料夾全域唯一**的：`assets/inventory/` 和 `assets/assembly/` 共用同一個序列
- 目前用到 `091`，已知空號 `048`（從未使用）。**下一個新照片從 092 開始**

這裡刻意不用 kebab-case。編號是有意義的識別碼、且 `site/inventory/` 的網頁有硬編引用，
維持 Title_Case 讓檔名在檔案總管裡好讀。**這是全專案唯一的例外軌道。**

### 3.4 參考圖 — `lower-kebab-case`，日期相關加 ISO 前綴

```
assets/reference/raspberry-pi-5/gpio-pinout-diagram.png
assets/reference/nezha/2026-07-30-stm32-car-wiring-diagram.png
```

`assets/reference/` 放**沒有入庫編號**的東西：規格圖、接線圖、截圖。
按來源分子資料夾（`raspberry-pi-5/`、`nezha/`）。

### 3.5 硬性禁止

進 repo 前一定要改掉：

```
❌ Screenshot 2026-07-30 at 3.30.58 AM.png    有空格、格式不明
❌ IMG_0325.JPG                                無語意
❌ G SDA SCL 5V.JPG                            有空格
❌ 未命名.pdf                                  中文檔名

✅ assets/reference/nezha/2026-07-30-i2c-header-g-sda-scl-5v.jpg
✅ assets/inventory/091_HXS_18650_Battery_Pack_Label.jpg
```

- **禁止空格**、全形括號、中文檔名
- **副檔名一律小寫**（`.JPG` → `.jpg`）
- 日期一律 ISO `YYYY-MM-DD`

**唯一例外是 `vendor/`** — 原廠檔案保持原名（含中文），才能跟官方目錄、下載頁對照。

## 4. `vendor/` 匯入規則

每個 `vendor/<供應商>/` 底下**必須有 `README.md`**，記錄：

1. 供應商名稱與官方連結
2. 下載日期與版本
3. 原始壓縮檔／光碟的存放位置
4. 匯入時剔除了什麼

**匯入時一律剔除編譯產物**（`.o` `.crf` `.d` `.lst` `.dep` `.map` `.axf` `.uvoptx` 等，
完整清單見 `.gitignore`）。這些可以從原始碼重建，卻佔掉大部分體積 ——
本專案初次整理時光這一項就清掉 5,838 個檔案、約 1GB。

## 4.5 網頁資料

**頁面內容資料一律放 `site/data/`，不要寫死在 HTML 裡。**

中英文共用同一份資料檔，語言相關欄位放在 `i18n.zh` / `i18n.en` 底下：

```js
{ id, number, name, category, tags, images,
  i18n: { zh: { title, desc, specs, ... },
          en: { title, desc, specs, ... } } }
```

`images` 存**相對 repo 根目錄**的路徑（`assets/inventory/001_....jpg`），
頁面自己加前綴。這樣資料檔不會綁死在某個目錄深度。

資料檔位置：

| 檔案 | 內容 |
|---|---|
| `site/src/data/modules.json` | 零件庫存 26 個模組 |
| `site/src/data/assembly-guide.json` | 組裝指南 7 章節 25 個步驟 |
| `site/src/data/categories.ts` | 庫存分類標籤 |

改完資料跑一次驗證，它會檢查圖片存在、id 不重複、雙語欄位齊全、
檔名符合 §3.3：

```bash
uv run python scripts/check_inventory_data.py
```

### 本機預覽

```bash
npm run dev
```

網址是 <http://localhost:4321/Car-and-Robotic-Arm/>（`base` 要跟 GitHub Pages 的
repo 路徑一致，所以本機也帶前綴）。

> 這條規則的由來：庫存頁原本中英文各自嵌一份 `MODULES_DATA`，
> 已經漂移到頁首顯示「收錄模組 90 項」但實際只有 26 筆。

## 5. Git

### Commit message

Conventional Commits，scope 用頂層資料夾名：

```
docs: 補上 NeZha I2C 協定的暫存器對照表
src: 加入 NeZha 驅動板 Python 驅動
assets: 新增雙目相機模組照片 092-093
vendor: 匯入 37 合 1 感測器套件原廠資料
site: 修正庫存頁圖片路徑
chore: 建立 .gitignore
```

body 可中英混雜，重點寫**為什麼**，不寫做了什麼（diff 看得到）。

### 體積警戒線 ⚠️

這個 repo 的歷史裡有大量二進位檔，目前狀態：

| 項目 | 現況 | 上限 |
|---|---|---|
| 工作目錄 | ~195MB | — |
| `.git` 歷史 | ~83MB | GitHub 建議 < 1GB |
| 單一檔案 | 最大 2.4MB（原廠手冊 PDF） | GitHub 硬限制 100MB |
| `assets/` | 45MB | GitHub Pages 發布上限 **1GB** |

**規則：**

- 單張照片進 repo 前壓到 **1MB 以下**（1600px 長邊、JPEG q82 大約 500KB）
- PDF 等文件型檔案放寬到 **10MB**，超過先問
- 影片、韌體映像檔、壓縮包**不進 repo**，放外部儲存並在 README 記位置

`git rm` 不會縮小 `.git` 歷史 —— 舊 blob 還在。2026-07-30 已用 `git filter-repo`
改寫過一次歷史（616MB → 83MB）並 force push。這是 destructive 操作，會讓所有既有
clone 失效，再做之前必須先討論。

> 當時的教訓：`--strip-blobs-bigger-than 1M` 會連**工作目錄**裡的大檔一起清掉，
> 4 份原廠 PDF 因此消失，事後才從原始下載復原。跑之前先列出會被砍的清單。

## 6. 暫存檔

跑實驗、產生中間結果，一律放 repo 根目錄的 `scratch/`（已在 `.gitignore`）。
不要散在專案各處，也不要用 `test.py`、`tmp.json`、`未命名 2.py` 這種檔名佔住根目錄。

## 7. 新增檔案前的檢查清單

1. 這是誰寫的？→ 決定頂層資料夾（§2）
2. 檔名有沒有空格、中文、大寫副檔名？（§3.5）
3. 是照片嗎？→ 拿下一個流水號，**不要重用舊號**（§3.3）
4. 超過 1MB 嗎？→ 先壓縮（§5）
5. 是原廠資料嗎？→ 剔除編譯產物 + 寫 `README.md`（§4）
