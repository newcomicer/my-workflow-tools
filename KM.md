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

### KM-022 🟡 多頁面 CSS 統一：font-smoothing + zoom + font-scale 三者缺一不可
- **問題**：settlement topbar 字體看起來比 budget-tracker 粗，字級也不同
- **根因**：三個獨立原因疊加 — ① body 缺少 `-webkit-font-smoothing: antialiased`（字粗）② CSS `zoom` 套在 body 而非內容區（topbar 被放大）③ topbar 字級沒用 `--font-scale` CSS 變數（字大小不隨系統設定縮放）
- **解法**：① body 加 `antialiased` ② zoom 改套在 `#settlement-content` ③ brand-name/sub-title 改用 `calc(var(--font-scale,1) * px)` 並在 JS 設定 `--font-scale`
- **影響範圍**：`settlement.html` CSS + JS
- **未來注意**：新增頁面時，checklist — body 要有 antialiased、zoom 不能影響 topbar、topbar 文字要用 --font-scale

### KM-020 🟡 「已到款」計數硬綁 key='l5'，自訂標籤不被計入
- **問題**：在設定頁「標籤設定」點「＋ 新增」新增 L5 標籤（如「L5已到款(內扣)」），指派給活動後，主頁「已到款 X 場」計數仍為 0
- **根因**：計數邏輯 `r.bizStatus === 'l5'` 硬寫死 key，但自訂標籤的 key 是自動產生的 `custom_xxx`，不是 `l5`
- **解法**：改為查 `labelSettings.bizStatus` 找到對應 label，若 label 開頭是 `'L5'` 就計入（同時保留 key=`l5` 的快速比對）
- **影響範圍**：`index.html` → `updateMainPanel()` 裡的 l5 計數那行
- **未來注意**：所有「用 key 做語意判斷」的邏輯，都有此風險；若允許自訂標籤，就不能靠固定 key 做判斷，要改靠 label 內容或另設「標記欄位」

### KM-019 🟡 overflow-x:auto 容器裁切 position:absolute 子元素
- **問題**：topbar 加 `overflow-x:auto` 後，user-dropdown（position:absolute）點開被裁切看不到
- **根因**：`overflow-x:auto` 會建立新的 stacking/clipping context，absolute 子元素超出邊界即被裁切
- **解法**：手機版 dropdown 改 `position:fixed`，定位基準換成 viewport，脫離 overflow 容器
- **影響範圍**：所有在 `overflow:hidden/auto` 容器內的 absolute popup/dropdown
- **未來注意**：在 scroll 容器內放 floating UI 一律用 `position:fixed` + 手動定位（參考 KM-004）

### KM-018 🟡 RWD 手機版四個常見坑（一次整理）
- **問題 A**：view-mode-pill 在手機上重複出現（mobileMonthBar 和 month-header 各一顆）
- **根因 A**：新增手機版 pill 時，沒有同步隱藏桌機版的
- **解法 A**：`@media(max-width:767px){ .month-header .view-mode-pill{display:none} }`

- **問題 B**：卡片內 at-actual/at-target 並排，target 數字被 `overflow:hidden` 截掉
- **根因 B**：`.at-card-main` 用 `justify-content:space-between`，卡片寬度不足時數字溢出被裁
- **解法 B**：手機改 `flex-direction:column;align-items:flex-start`

- **問題 C**：year-badge 文字（「2026 年度」/「全年」）在手機 topbar 斷行
- **根因 C**：`.year-badge` 沒有 `white-space:nowrap`
- **解法 C**：加 `white-space:nowrap` 到 `.year-badge`

- **問題 D**：橫向捲動篩選列中，「活動清單 65場」被壓縮換行
- **根因 D**：flex 容器設 `flex-wrap:nowrap` 後，子元素預設 `flex-shrink:1` 會被壓縮
- **解法 D**：不應縮的標題區加 `flex-shrink:0`

- **影響範圍**：所有 RWD 改版
- **未來注意**：新增手機版元件時，同時確認桌機版對應元件是否需要隱藏；橫向捲動列內的標題元素一律加 `flex-shrink:0`

### KM-014 🟡 切換費用輸入模式（非勞務→勞務）按鈕殘留 disabled 狀態
- **問題**：點「人工費用」後彈出勞務表單，「＋新增這筆」按鈕無法點擊
- **根因**：先前點非勞務費用時，`checkExpFormReady()` 把按鈕設為 disabled；切換成勞務表單時 innerHTML 整個重建，但沒有明確重設按鈕狀態；新的表單有自己的 `checkLaborFormReady()`，但初始狀態需要顯式設定
- **解法**：勞務表單 innerHTML 設定完後立即執行 `btn.disabled=true`，再由 `checkLaborFormReady()` 在填完姓名+工時後啟用
- **影響範圍**：所有「表單 innerHTML 整個換掉，但共用同一個提交按鈕」的 pattern
- **未來注意**：共用按鈕在表單切換時，必須明確重設為 disabled，由新表單的 validator 接管控制權，不能依賴舊 validator 的殘留狀態

### KM-013 🟡 登出後 loginOverlay 按鈕卡在「登入中...」disabled 狀態
- **問題**：登入成功進入系統後，點登出，loginOverlay 再次出現時登入按鈕文字是「登入中...」且無法點擊
- **根因**：`signInWithGoogle()` 把按鈕改成 disabled + 「登入中...」，登入成功後沒有重設；登出時 loginOverlay 重新顯示，但按鈕狀態殘留
- **解法**：`handleAuthUser(null)` 分支（user 為 null 時）補上 `btn.disabled=false; btn.textContent='使用 Google 帳號登入'`
- **影響範圍**：所有「登入按鈕改狀態後靠 overlay hide/show 切換畫面」的 pattern
- **未來注意**：畫面用 overlay 切換時，重新顯示前要確認所有 UI 狀態已重設

### KM-011 🔴 `<label>` 包 `<input>` 導致 onclick 觸發兩次，操作看似無效
- **問題**：角色勾選點一下完全沒反應（加了又馬上移掉）
- **根因**：`<label onclick="fn()"><input type="checkbox">文字</label>` — 點 label 會先觸發 onclick，再對 checkbox 發一次合成 click，合成 click 冒泡回 label 又觸發一次 onclick；兩次抵銷
- **解法**：onclick 改為接收 event 參數，函式內第一行呼叫 `e.preventDefault()` 阻止合成 click
- **影響範圍**：所有「label 包 input，且 onclick 做開關邏輯」的 pattern 都有此問題
- **未來注意**：toggle UI 優先用 `<div onclick>` + CSS class 控制，避免用 label 包 input 觸發雙重事件

### KM-012 🟡 新用戶登入白名單後，成員管理表格不顯示該人員
- **問題**：把 email 加入白名單 → 該用戶登入成功 → 成員管理表格卻看不到他
- **根因**：`buildMergedMembers` 只把有 Firestore profile 記錄的人加進 `currentMembers`；白名單簡化後 `addToWhitelist` 不再自動建 profile，導致新用戶登入後沒有 profile 記錄
- **解法**：在 `handleAuthUser` 登入成功後，檢查當前用戶是否在 `currentMembers`，不在的話自動建立基本 profile（名字抓 Google displayName，角色預設唯讀）
- **影響範圍**：白名單新增流程 + 首次登入流程
- **未來注意**：白名單控制「誰能登入」，profile 控制「誰出現在成員表格」；兩者要同步

### KM-008 🔴 Firebase signInWithRedirect 跨域導致 getRedirectResult 失敗
- **問題**：登入後被導回 app，但 `getRedirectResult()` 拿不到 user，停在登入頁
- **根因**：`authDomain` 用 `firebaseapp.com`，但 app 在 `web.app`，兩個不同 origin，session storage 無法跨域共享
- **解法**：`authDomain` 改為與 Hosting 相同的 `web.app` 網域（例如 `h2u-budget-tracker.web.app`），並在 Google Cloud Console → 憑證 → OAuth 2.0 用戶端 → 已授權的重新導向 URI 加上 `https://<site>.web.app/__/auth/handler`
- **影響範圍**：所有用非預設 Hosting site（非 project ID 預設網址）部署的 Firebase Auth redirect 流程
- **未來注意**：Firebase Hosting 有多個 site 時，`authDomain` 要對應使用的 site 網址，不能沿用預設的 `firebaseapp.com`

### KM-009 🟡 Firebase Hosting 部署到非預設 site 需設定 firebase.json
- **問題**：`firebase deploy` 部署到 `budget-tracker-cfee4.web.app`（專案預設），而非預期的 `h2u-budget-tracker.web.app`
- **根因**：`firebase.json` 沒有指定 `site`，CLI 預設部署到與 project ID 同名的 site
- **解法**：在 `firebase.json` 的 `hosting` 區塊加上 `"site": "h2u-budget-tracker"`
- **影響範圍**：有自訂 Hosting site ID 的所有專案
- **未來注意**：建立非預設 site 時，`firebase.json` 必須明確指定 `site`

### KM-010 🟡 Google 登入每次自動選上次帳號，無法切換
- **問題**：登出後再登入，自動用上次的 Google 帳號，看不到帳號選擇器
- **根因**：`GoogleAuthProvider` 預設沿用 Google session
- **解法**：`provider.setCustomParameters({ prompt: 'select_account' })`
- **影響範圍**：所有 Google Sign-in 流程
- **未來注意**：多帳號環境（個人 + 公司）一定要加這個參數

---


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

### KM-019：iRunner 免費名單工作表名稱不固定
- **問題**：解析器只找「免費名單」sheet，但有些 Excel 叫「公關名單」，導致公關人數全靠 fee=null 推斷
- **根因**：iRunner 匯出的 sheet 名稱因賽事設定不同而異
- **解法**：用陣列 `['免費名單', '公關名單']` 做模糊比對
- **影響範圍**：`web/js/excel-parser.js` 免費名單偵測邏輯
- **未來注意**：遇到新的 sheet 名稱變體就加進陣列

### KM-020：親子組公關偵測容易雙重計算
- **問題**：親子組每組 2 人但只有 1 筆費用，第 2 人 fee=null 會被誤判為公關；且免費名單的人可能跟 fee=null 的人重疊
- **根因**：免費名單用訂單 ID 排除會失敗（同一訂單可能同時在免費名單和報名資料中）
- **解法**：改用「每組別計數扣減法」— 先計算免費名單各組別人數，fee=null 的人先扣免費名單配額，扣完才算新公關
- **影響範圍**：`web/js/excel-parser.js` 公關偵測區段
- **未來注意**：測試公關人數時一定要用有親子組 + 免費名單的 Excel 交叉驗證

### KM-021：報名費不能用 (人數-公關)×單價 計算
- **問題**：親子組 2 人共用 1 筆報名費，用人數×單價會多算
- **根因**：iRunner 的「報名項目費用」欄是每人一列，親子組第 2 人費用為 null
- **解法**：直接從 Excel「報名項目費用」欄逐列加總（`reg_fee_by_group`），不再用人數公式
- **影響範圍**：`web/js/excel-parser.js` + `web/index.html` 報名費計算
- **未來注意**：所有涉及「人數×單價」的計算都可能被親子組破壞，優先用 Excel 原始數值

---

*最後更新：2026-05-08（KM-022 新增）*
