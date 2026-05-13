# expense-ocr 驗收清單

## v0.1 — OCR 辨識 + Streamlit 確認介面

### Happy Path
- [ ] 上傳 1 張發票照片 → 辨識成功 → 日期、統編、發票號碼、金額、店家、摘要皆正確顯示
- [ ] 上傳 1 份多頁 PDF（含多張憑證）→ 每張憑證各自獨立一筆，可逐張編輯
- [ ] 選擇費用類別 + 專案 → 費用說明自動組合為 `YYYY.MM.DD - 描述 / 專案名(代號)`
- [ ] 點「送入 EasyFlow」→ Playwright 開啟 Chromium → 自動登入 → 導航到申請單 → 逐張填入 → 完成提示

### 容易出問題的情境
- [ ] 上傳模糊或歪斜的照片 → 辨識信心顯示「低」，不會 crash
- [ ] 停車費 < 200 元 → 自動轉 TXXX 類型，統編和發票號碼清空
- [ ] 發票號碼格式不符（例如只有數字沒有英文）→ 顯示黃色警告
- [ ] 金額超過 20,000 元 → 顯示紅色合規警告
- [ ] Gemini API Key 未填 → 「開始辨識」按鈕 disabled，顯示提示
- [ ] EasyFlow 工號密碼未填 → 「送入 EasyFlow」按鈕 disabled，顯示提示
- [ ] Playwright 填表中再按一次「送入 EasyFlow」→ 按鈕顯示「填表進行中」disabled，不會開第二個視窗

## v0.2 — EasyFlow 欄位驗證（待 e2e 測試後更新）
- [ ] 確認 `text=發起流程` 選擇器正確
- [ ] 確認搜尋框 placeholder 可定位
- [ ] 確認 `text=請款_預支費用申請單(YH)` 可點擊
- [ ] 確認 `apa00_0`（申請類別）可操作
- [ ] 確認 `diaApa36_txt/lbl`（帳款類別）可寫入
- [ ] 確認 `PayTargetType_rad_1`（受款人性質）可點擊
- [ ] 確認 `diaApa02_txt/lbl`（請款法人）欄位 ID
