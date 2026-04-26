# KM — 踩坑知識庫

> **規則**：任何 bug 解決、坑踩過，當下立刻寫進來。新 session 開始前必讀。
> **格式**：每條記錄包含「問題 / 根因 / 解法 / 影響範圍 / 未來注意」五欄。

---

## 使用說明

- **新增記錄**：直接在對應工具區段下方新增，最新的放最上面
- **標籤**：`[settlement-app]` / `[budget-tracker]` / `[共用]`
- **嚴重度**：🔴 嚴重（功能壞掉）/ 🟡 中等（行為不符預期）/ 🟢 輕微（小細節）

---

## settlement-app

### KM-001 🟡 Excel 欄位偵測失敗（無「報名資料」工作表）
- **問題**：上傳 Excel 後解析失敗，頁面無回應或報錯
- **根因**：iRunner 匯出格式有時工作表命名不一致（例如「報名名單」vs「報名資料」）
- **解法**：`parse_excel()` 的工作表偵測改為模糊比對（contains「報名」），不要精確比對名稱
- **影響範圍**：`app.py` → `parse_excel()`
- **未來注意**：拿到新版 iRunner Excel 時，先確認工作表名稱是否改變

---

### KM-002 🟡 PDF 產生失敗（Playwright 找不到 Chromium）
- **問題**：點「匯出 PDF」後後端報錯，找不到執行檔
- **根因**：新環境未執行 `playwright install chromium`
- **解法**：`requirements.txt` 安裝完後，執行 `python -m playwright install chromium`
- **影響範圍**：PDF 匯出功能
- **未來注意**：換電腦或新環境部署時必做這一步，`啟動.command` 可考慮加入檢查

---

## budget-tracker

### KM-007 🟡 用 style.display='none' 關 modal，下次 classList.add('open') 無效
- **問題**：儲存設定後再次點齒輪按鈕，設定視窗完全不出現
- **根因**：關閉時用 `element.style.display='none'`（inline style）；重開時用 `element.classList.add('open')`（class CSS 設 display:flex）。Inline style 優先級高於 class，所以 class 的 display:flex 被蓋掉，視窗永遠隱藏
- **解法**：關閉 modal 統一呼叫同一個 `closeSettings()` 函數（用 `classList.remove('open')`），不要直接操作 inline style
- **影響範圍**：所有「用 class 控制顯示/隱藏的 modal」都有此風險
- **未來注意**：modal 開關邏輯只用一種方式，class-based 就全部 class，inline style 就全部 inline；混用必踩

---

### KM-004 🟡 icon picker popup 被 overflow:hidden 裁切不顯示
- **問題**：點 icon 按鈕後選擇器 popup 建立了但畫面上看不到
- **根因**：`.cat-edit-card` 有 `overflow:hidden`，`position:absolute` 的 popup 被裁切
- **解法**：popup 改 `position:fixed`，用 `btn.getBoundingClientRect()` 計算 top/left，`document.body.appendChild(popup)`
- **影響範圍**：任何在 `overflow:hidden` 容器內的 absolute popup 都有此問題
- **未來注意**：設計 floating UI 時優先考慮 `position:fixed` + 手動定位，避免被父層 overflow 夾死

---

### KM-005 🟡 設定頁 label 文字輸入 focus 跳掉
- **問題**：在標籤設定頁輸入文字，每按一個鍵 input 就失去焦點
- **根因**：`oninput` 事件呼叫 `renderLabelSettings()` 整體重渲 DOM，原本的 input 元素被銷毀重建
- **解法**：`oninput` 只更新對應的 badge span（`document.getElementById('label-badge-xxx').textContent`），不再呼叫整體重渲
- **影響範圍**：所有「編輯後即時重渲整個區塊」的 pattern 都有此問題
- **未來注意**：即時更新 UI 時優先選擇「更新最小 DOM 範圍」，避免重渲整個 list

---

### KM-006 🟡 detail panel 下拉選單未同步設定頁
- **問題**：在設定頁新增業務人員或修改狀態後，點進活動明細的下拉選單沒有更新
- **根因**：detail panel 的 `<select>` 全部是硬碼靜態 HTML，且「儲存設定」按鈕沒有 `onclick`
- **解法**：(1) 加 JS 變數 `settingsBizPeople`、`settingsPMPeople`、`settingsClients` 存設定資料；(2) 加 `populateDetailSelects(race)` 在 `openDetail` / `openNewRace` 時動態填入；(3) `saveSettings()` 讀 DOM tag → 更新 JS 變數 → 重填 selects → 關視窗
- **影響範圍**：業務、PM、客戶、業務狀態、執行狀態、活動類型等所有 detail panel 下拉
- **未來注意**：任何「設定頁編輯 → 主介面生效」的流程，都要明確定義資料的 single source of truth；DOM tag 不是可靠的資料源

---

## 共用

### KM-003 🟢 BeeStation 同步延遲導致舊檔案被覆蓋
- **問題**：兩台電腦同時開啟同一檔案，存檔時有機率互蓋
- **根因**：BeeStation 同步不是即時的，若兩端同時修改會衝突
- **解法**：確認另一台電腦已關閉檔案後再開始編輯；衝突發生時查看「衝突副本」
- **影響範圍**：所有工具原始碼
- **未來注意**：重要修改前先確認 BeeStation 已同步完成（檔案圖示無同步中標記）

---

*最後更新：2026-04-26（KM-007 新增）*
