# my-workflow-tools — 我的工作流總專案

## 對話開始時請先讀
進度與最近更動都在 Obsidian：`secondbrain/my-workflow-tools/工作筆記.md`

## 工作模式
- **加新工具**：對 Claude 說「我想做一個 XXX 工具」→ Claude 會：
  1. 建 `tools/<工具名>/` 子資料夾
  2. 在 Obsidian `my-workflow-tools/<工具名>/` 建立 `專案工作流程.md`（含專案簡介、技術架構、改版紀錄、待辦項目）
  3. 引導我跟著開發
- **結束工作**：對 Claude 說「**收工**」→ 自動 commit + push + 更新 Obsidian 工作筆記
- **接續工作**：對 Claude 說「讀工作筆記、告訴我上次做到哪」→ 若有指定工具，同時讀該工具的 `my-workflow-tools/<工具名>/專案工作流程.md`

## 工作桌 + 三個家
- 📋 BeeStation 工作桌：`/Users/johnny.chang/Library/CloudStorage/BeeStation-MyBeeStationPlus/Johnny-Agent/my-workflow-tools/`（自動跨電腦同步）
- 🐙 GitHub repo：`newcomicer/my-workflow-tools`（公開，網頁的家）
- 📘 Obsidian 筆記本：`secondbrain/my-workflow-tools/工作筆記.md`（想法的家）
- 🔥 Firebase 專案：`my-workflow-tools`（資料的家）

## 工具清單
（之後加新工具時會自動更新）
- **settlement-app** (`tools/settlement-app/`)：iRunner Excel 匯入 → 自動計算結算金額 → 匯出 PDF 費用申請單

## 工作注意事項
- commit 訊息要寫清楚做了什麼 + 為什麼
- 收工前說「收工」讓 Claude 同步三方
