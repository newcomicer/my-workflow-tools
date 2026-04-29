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

*最後更新：2026-04-28（KM-008、009、010 新增）*
