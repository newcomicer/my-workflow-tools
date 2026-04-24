# budget-tracker — 年度賽事預算追蹤系統

## 這個工具是做什麼的
年度賽事財務總覽：月份 × 賽事矩陣、收支明細、AOP 比對、小幫手費用計算器。

使用者是 Johnny（路跑賽事規劃與計時服務業務主管），用於追蹤全年度各場賽事的實際收支與目標達成狀況。

## 技術架構（目前）

| 層 | 技術 |
|---|---|
| 前端 | 單頁 `index.html`（無前端框架，Tailwind CDN） |
| 資料 | 目前為 JS 常數（races 陣列），未來接 Firebase |
| 預覽伺服器 | Python http.server，port 5002 |

## 啟動方式
```bash
python3 -m http.server 5002 --directory tools/budget-tracker
# 開啟 http://127.0.0.1:5002
```
或透過 Claude Code launch.json 的 budget-tracker 設定啟動。

## 核心資料結構

### race 物件欄位
```js
{
  year: 2026,          // 年度（切換器用）
  name: '賽事名稱',
  code: 'TIR260101',   // iRunner 代碼
  date: '01/04',       // MM/DD
  client, biz, pm,     // 客戶、業務、PM
  type,                // both / report / timer
  bizStatus,           // l5~l2
  execStatus,          // 完成/進行中/規劃中…
  income, expense,     // 實際收支
  targetIncome, targetExpense, targetGPPct,  // AOP 目標
  estIncome, estExpense,  // 預估值
  regCount, timerCount
}
```

## 已完成功能
- 頂欄年度切換器（▼ 下拉，自動偵測 races 中的年份）
- 月份側邊欄（1~12 月點擊切換）
- 賽事清單 14 欄（可勾選顯示/隱藏、拖拉排序、自訂凍結欄）
- Detail Panel（基本資訊 / 收入明細 / 支出明細 / AOP / 預估 五 Tab）
- 收入明細：三類別（報名服務/計時服務/客製化），單價×數量
- 支出明細：多筆明細（日期+備註+金額），小幫手費率計算器
- AOP Tab：目標 vs 實際對比
- 設定頁（密碼 1234）：人員/客戶/收支項目/費率/標籤設定

## 下一步
- 支出備註欄提示文字 → 整合進設定頁
- 轉為正式 Flask + Firebase app

## 檔案結構
```
budget-tracker/
├── index.html    # 單頁前端原型
└── CLAUDE.md     # 本說明檔
```
