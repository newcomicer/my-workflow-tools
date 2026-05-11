# my-workflow-tools — 我的工作流總專案

## 對話開始時請先讀
1. **KM.md**（踩坑知識庫）：`my-workflow-tools/KM.md` — 必讀，避免重蹈覆轍
2. **專案工作流程**（進度 + 待辦）：Obsidian `2ndbrain/my-workflow-tools/<專案名>/專案工作流程.md`
   - 只讀本次要動的專案，不用同時讀兩個
   - 工具清單索引：`2ndbrain/my-workflow-tools/工作筆記.md`（輕量，只看清單用）

## 工作模式

### Sprint 節奏（每次開發新功能 / 修 bug / 加新工具都走這條）

**① 開工確認（DOR）**
Johnny 說清楚：「我想要 [做什麼]，完成後應該要能 [看到什麼行為]」
→ Claude 確認理解正確再繼續，有疑問先問清楚

**② 探索（Explore）**
Claude 先盤點所有可能解法，列出優缺點與推薦方向
→ 不直接動手，等 Johnny 確認方向後才進入下一步

**③ 完工條件（DOD）**
Claude 更新該工具的 `TEST.md`，新增本次功能的驗收條目，包含：
- Happy path × 1（正常流程走完是什麼樣子）
- 最容易出問題的情境 × 3（邊界條件、異常輸入、環境差異）
→ Johnny 確認 TEST.md 內容後才開始寫程式

**④ 開發（Code）**
實際執行，過程中若遇到預期外的坑 → 解決後立刻更新 KM.md

**⑤ 收工回顧（Retro）**
Johnny 說「**收工**」時，Claude 依序執行：
1. 對照 `TEST.md` 驗收清單逐條確認，全部通過才繼續
2. 本次有踩新坑？→ 確認已寫進 `KM.md`
3. `CLAUDE.md` 需要新增或刪除規則？→ 當場更新
4. commit + push（訊息寫清楚做了什麼 + 為什麼）
5. 更新 Obsidian `<專案名>/專案工作流程.md`（上次做到哪 + 待辦）

---

### 快速指令
- **加新工具**：說「我想做一個 XXX 工具」→ 進入 Sprint ①，Claude 同步建立 `tools/<工具名>/` 和 Obsidian `專案工作流程.md`
- **加新功能 / 修 bug**：說「我想在 XXX 加一個 YYY」或「XXX 有個 bug 是 ZZZ」→ 進入 Sprint ①
- **接續工作**：說「接續 XXX，告訴我上次做到哪」→ Claude 讀 KM.md + Obsidian `XXX/專案工作流程.md` 後回報

## 工作桌 + 三個家
- 📋 BeeStation 工作桌：`/Users/johnny.chang/Library/CloudStorage/BeeStation-MyBeeStationPlus/Johnny-Agent/my-workflow-tools/`（自動跨電腦同步）
- 🐙 GitHub repo：`newcomicer/my-workflow-tools`（公開，網頁的家）
- 📘 Obsidian 筆記本：`2ndbrain/my-workflow-tools/工作筆記.md`（想法的家）
- 🔥 Firebase 專案：`my-workflow-tools`（資料的家）

## 工具清單
（之後加新工具時會自動更新）
- **settlement-app** (`tools/settlement-app/`)：iRunner Excel 匯入 → 自動計算結算金額 → 匯出 PDF 費用申請單

## 工作注意事項
- commit 訊息要寫清楚做了什麼 + 為什麼
- 收工前說「收工」讓 Claude 同步三方
- **踩到 bug 解決後，當下立刻寫進 `KM.md`**，不要等到收工才補
