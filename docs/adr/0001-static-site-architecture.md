# ADR 0001：專案報告網站的前端架構

- **狀態**：提案中（待決定）
- **日期**：2026-07-30

## 背景

專案要產出一份**專案報告**，用靜態網頁呈現，發布到 GitHub Pages。

目前 `site/` 已經有三個手寫的單檔 HTML：

| 頁面 | 行數 | 內容 |
|---|---|---|
| `site/inventory/index.html` | ~1800 | 零件庫存瀏覽器（繁中），26 個模組、搜尋、分類、modal、lightbox |
| `site/inventory/index.en.html` | ~1770 | 同上英文版 |
| `site/assembly-guide/index.en.html` | ~1490 | 組裝指南，50 頁掃描圖 |

### 現況的三個問題

1. **CSS 完全重複** —— 每個檔案各自帶一份 700 行的 `<style>`，改配色要改三個地方
2. **資料寫死在 JS 裡** —— `MODULES_DATA` 陣列直接嵌在 HTML 中，中英文各維護一份，
   已經出現不同步（`stat-count` 硬寫 90，實際資料只有 26 筆）
3. **沒有共用 layout** —— 新增第四頁等於再複製貼上一次

整理過程中還發現三個因為「單檔手寫」而長期沒被發現的 bug：中文版缺整段 lightbox
markup、英文版 `<script>` 沒收尾、gallery 沒接上 lightbox。三頁都無法正常顯示，
但因為沒有建置流程與檢查，沒人發現。

### 限制條件

- GitHub Pages 發布體積上限 **1GB**；`assets/` 壓縮後 45MB，還有成長空間
- 內容是雙語（繁中／英文）
- `docs/` 底下已經有 Markdown 文件，報告內容應該直接沿用，不要再抄一份
- 團隊工具偏好：npm（不用 yarn / pnpm）

## 選項

### A. 維持 vanilla HTML，只做重構

抽出共用 `site/assets/style.css`、把 `MODULES_DATA` 移到 `site/data/modules.json`。

- ✅ 零建置、零依賴，`python3 -m http.server` 直接跑
- ✅ 改動最小
- ❌ 沒有 layout 繼承，新頁面還是要複製貼上
- ❌ 圖片優化要自己寫腳本
- ❌ Markdown 文件無法直接變成頁面，報告內容得手動搬

### B. Astro（建議）

- ✅ **Content collections 直接吃 `docs/*.md`** —— 文件就是網站內容，不會分家，
  這點跟 `CONVENTIONS.md` 的「單一真實來源」原則一致
- ✅ **`astro:assets` 自動產生 WebP 與多尺寸 responsive** —— 直接解掉圖片體積問題
- ✅ 預設輸出零 JS；現有的 vanilla JS 互動可以原樣包成 island，不用重寫
- ✅ 內建 i18n routing，符合雙語需求
- ✅ GitHub Pages 有官方 `withastro/action`
- ❌ 多一層建置步驟與 npm 依賴
- ❌ 三個頁面要拆成 component，是實質工作量

### C. VitePress

- ✅ Markdown-first，做「文件型報告」最快
- ❌ 庫存瀏覽器那種客製化互動要塞進 VitePress 的框架裡比較彆扭
- ❌ 版面高度綁定它的預設主題

## 決策

**建議選 B（Astro）**，但分階段導入，每個階段都能獨立驗收：

| 階段 | 內容 | 產出 |
|---|---|---|
| 0 | ~~修好既有頁面、統一資產路徑~~ | ✅ 已完成 |
| 1 | 資料抽出到 `site/data/modules.json`，中英共用一份 | 去掉 zh/en 資料不同步 |
| 2 | 導入 Astro，三頁改成 layout + component | 新增頁面不用再複製貼上 |
| 3 | GitHub Actions 部署 + `astro:assets` 圖片優化 | 自動發布，體積再降一個量級 |

階段 1 即使之後不走 Astro 也不會白做 —— 資料與呈現分離在任何方案下都是對的。

## 影響

- `site/` 之後會有 `package.json` 與 `node_modules/`（已列入 `.gitignore`）
- 建置輸出到 `_site/`（已列入 `.gitignore`）
- 本機預覽從 `python3 -m http.server` 改成 `npm run dev`
- `CONVENTIONS.md` 的資產命名規則不受影響
