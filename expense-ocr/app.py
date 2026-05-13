import streamlit as st
import google.generativeai as genai
import json
import os
import re
import subprocess
import sys
import csv
import io
import requests
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

_SHEET_ID = "1IR_H2bNfG0EBfsQdiSfFMFSJ2TjTcl2BZsh0FHsfyfU"
_SHEET_TABS = {"賽事部": "0", "數位服務部": "916187796"}

COST_CATEGORIES = [
    {"code": "A01", "name": "租金"},
    {"code": "A02", "name": "租金(IFRS 16)"},
    {"code": "A03", "name": "文具"},
    {"code": "A04", "name": "印刷費"},
    {"code": "A05", "name": "旅費"},
    {"code": "A06", "name": "運費"},
    {"code": "A07", "name": "郵資"},
    {"code": "A08", "name": "電話費"},
    {"code": "A09", "name": "網路服務費"},
    {"code": "A10", "name": "修繕費"},
    {"code": "A11", "name": "廣告費"},
    {"code": "A12", "name": "水電瓦斯費"},
    {"code": "A13", "name": "勞保費"},
    {"code": "A14", "name": "健保費"},
    {"code": "A15", "name": "團保費"},
    {"code": "A16", "name": "其他保險"},
    {"code": "A17", "name": "交際費"},
    {"code": "A18", "name": "捐贈"},
    {"code": "A19", "name": "稅捐"},
    {"code": "A20", "name": "職工福利"},
    {"code": "A21", "name": "佣金支出"},
    {"code": "A22", "name": "訓練費"},
    {"code": "A23", "name": "勞務費"},
    {"code": "A24", "name": "會計師公費"},
    {"code": "A25", "name": "書報雜誌"},
    {"code": "A26", "name": "雜項購置"},
    {"code": "A27", "name": "匯款手續費"},
    {"code": "A28", "name": "刷卡手續費"},
    {"code": "A29", "name": "其他手續費"},
    {"code": "A30", "name": "清潔費"},
    {"code": "A31", "name": "管理費"},
    {"code": "A32", "name": "規費"},
    {"code": "A33", "name": "會議餐費"},
    {"code": "A34", "name": "其他費用"},
    {"code": "A35", "name": "兼職薪資"},
    {"code": "A36", "name": "員工健檢"},
    {"code": "A37", "name": "付費照片成本"},
    {"code": "A38", "name": "雜誌成本"},
    {"code": "A39", "name": "廣告成本"},
    {"code": "A40", "name": "其他勞務成本"},
    {"code": "A41", "name": "銷貨折讓"},
    {"code": "A42", "name": "勞務折讓"},
    {"code": "A43", "name": "佣金收入"},
    {"code": "A44", "name": "銷貨收入"},
    {"code": "A45", "name": "其他所得"},
    {"code": "A46", "name": "銷貨成本-其他"},
    {"code": "A47", "name": "佣金收入-Pano"},
    {"code": "B01", "name": "代扣所得稅"},
    {"code": "B02", "name": "代扣補充保費"},
    {"code": "B03", "name": "代扣勞保費"},
    {"code": "B04", "name": "代扣健保費"},
    {"code": "B05", "name": "代扣勞退金"},
    {"code": "B06", "name": "其他代扣款"},
    {"code": "B07", "name": "其他代收款"},
    {"code": "B08", "name": "存入保證金"},
    {"code": "B09", "name": "其他應收款-關係人"},
    {"code": "B10", "name": "暫收款-賽事報名"},
    {"code": "C01", "name": "預付租金"},
    {"code": "C02", "name": "預付費用-其他"},
    {"code": "C03", "name": "代付款"},
    {"code": "C04", "name": "預付設備款"},
    {"code": "C05", "name": "存出保證金"},
    {"code": "D01", "name": "銀行借款"},
    {"code": "D02", "name": "預付投資款"},
]

_COST_OPTS = [f"{c['code']}　{c['name']}" for c in COST_CATEGORIES]
_COST_DEFAULT_IDX = next(i for i, c in enumerate(COST_CATEGORIES) if c["code"] == "A05")


@st.cache_data(ttl=300)
def fetch_projects() -> list:
    """從 Google Sheet 抓取兩個分頁的在建專案清單（5 分鐘快取）"""
    projects = []
    for dept, gid in _SHEET_TABS.items():
        url = f"https://docs.google.com/spreadsheets/d/{_SHEET_ID}/export?format=csv&gid={gid}"
        try:
            resp = requests.get(url, timeout=8)
            text = resp.content.decode("utf-8")
            if resp.status_code == 200 and "<!DOCTYPE" not in text:
                reader = csv.reader(io.StringIO(text))
                next(reader, None)  # 跳過標題列
                for row in reader:
                    code = row[1].strip() if len(row) > 1 else ""
                    name = row[2].strip() if len(row) > 2 else ""
                    closed = row[6].strip() if len(row) > 6 else ""
                    if code and name and not closed:
                        projects.append({"code": code, "name": name, "dept": dept})
        except Exception:
            pass
    projects.sort(key=lambda p: p["code"], reverse=True)
    return projects


st.set_page_config(page_title="報帳助手", page_icon="🧾", layout="wide")
st.title("🧾 報帳助手")
st.caption("上傳發票照片或 PDF，自動辨識後一鍵複製到 EasyFlow")

# ── EasyFlow 設定（側邊欄）────────────────────────────────────────────────────

# ── API Key 設定（側邊欄）────────────────────────────────────────────────────

with st.sidebar:
    st.header("🔑 Gemini API Key")
    st.caption("從 [Google AI Studio](https://aistudio.google.com/apikey) 免費取得")
    _effective_key = st.text_input(
        "API Key",
        type="password",
        key="gemini_api_key",
        placeholder="AIza...",
    ).strip()
    if _effective_key:
        genai.configure(api_key=_effective_key)
    else:
        st.warning("請輸入 API Key 才能辨識")

    st.divider()
    st.header("⚙️ EasyFlow 登入")
    ef_username = st.text_input("工號", key="ef_username", placeholder="H2U23082")
    ef_password = st.text_input("密碼", type="password", key="ef_password")

ef_ready = bool(ef_username and ef_password)

# ── OCR prompt ───────────────────────────────────────────────────────────────

OCR_PROMPT = """
請辨識這份文件中的所有台灣消費憑證（統一發票、電子發票、收據、車票等）。
如果是 PDF，請掃描所有頁面，每頁可能有多張憑證，全部都要辨識。

回傳 JSON 陣列（即使只有一筆，也用陣列格式），每筆憑證一個物件：
[
  {
    "date": "消費日期，格式 YYYY/MM/DD",
    "taxId": "統一編號（8位數字，沒有則填空字串）",
    "invoiceNumber": "發票號碼（2英文字母+8數字，共10碼，無橫線，沒有則填空字串）",
    "amount": "含稅總金額（純數字，不含逗號）",
    "vendor": "店家或供應商名稱",
    "description": "消費摘要（簡短描述，不含日期）",
    "invoiceType": "EasyFlow 憑證類型代號，從以下選一：T223（二聯式收銀機統一發票）/ T251（三聯式收銀機統一發票）/ T254（電子發票）/ T211（手開或電子計算機統一發票）/ T222（有起迄票：高鐵、台鐵、客運）/ TXXX（收據、免用統一發票；停車費 200 元以內也使用 TXXX）",
    "pageNumber": "員工手寫在憑證上的編號（純整數），若無則填 null",
    "confidence": "辨識信心（高/中/低）"
  }
]

注意：
- invoiceNumber 去掉橫線或空格，例如 AB-12345678 → AB12345678
- amount 只填數字，例如 1,050 → 1050
- 如果某欄無法辨識，填空字串
- 每張憑證分開列，不要合併成一筆
- 只回傳 JSON，不要其他文字
"""

# ── 工具函數 ──────────────────────────────────────────────────────────────────

def parse_response(text: str) -> list:
    text = text.strip()
    text = re.sub(r'^```[a-z]*\n?', '', text)
    text = re.sub(r'\n?```$', '', text)
    result = json.loads(text)
    if isinstance(result, dict):
        result = [result]
    return result


def clean_invoice_number(raw: str) -> str:
    return re.sub(r'[-\s]', '', raw).upper()


def compose_description(date_str: str, desc: str, proj_code: str = "", proj_label: str = "") -> str:
    """組合最終費用說明：YYYY.MM.DD - 描述 / 專案名稱(代號)"""
    m = re.match(r'(\d{4})/(\d{2})/(\d{2})', date_str or "")
    date_fmt = f"{m.group(1)}.{m.group(2)}.{m.group(3)}" if m else ""
    base = f"{date_fmt} - {desc}" if (date_fmt and desc) else (date_fmt or desc)
    if proj_code and proj_label:
        return f"{base} / {proj_label}({proj_code})"
    return base


def check_compliance(r: dict) -> list:
    """依財會 SOP 檢查憑證合規性，回傳問題清單"""
    issues = []
    inv_type = r.get("invoiceType", "")
    # 停車費 200 元以內視同 TXXX，免填統編及發票號碼
    is_parking_under_200 = (
        "停車" in r.get("description", "") and
        r.get("amount", "0").isdigit() and int(r.get("amount", "0")) <= 200
    )
    is_receipt_type = inv_type in ["TXXX", "T222"] or is_parking_under_200

    if not is_receipt_type:
        if not r.get("taxId", "").strip():
            issues.append("統一編號未填（統一發票 / 電子發票須填寫）")
        inv_clean = clean_invoice_number(r.get("invoiceNumber", ""))
        if not inv_clean:
            issues.append("發票號碼未填（統一發票 / 電子發票須填寫）")

    try:
        if int(r.get("amount", "0") or "0") > 20000:
            issues.append("金額超過 2 萬元，員工墊款單筆上限為 2 萬（國外差旅不在此限）")
    except ValueError:
        pass

    return issues


_PARKING_KEYWORDS = ("停車", "parking")

def apply_parking_rule(r: dict) -> None:
    """停車費金額 < 200 → 強制改成 TXXX（帳務規定；電子發票外觀仍免用統編）"""
    text = (r.get("description", "") + r.get("vendor", "")).lower()
    amount_str = r.get("amount", "0") or "0"
    if not amount_str.isdigit():
        return
    if any(kw in text for kw in _PARKING_KEYWORDS) and int(amount_str) < 200:
        r["invoiceType"] = "TXXX"
        r["taxId"] = ""
        r["invoiceNumber"] = ""


# ── OCR 辨識函數 ─────────────────────────────────────────────────────────────

def _ocr_error_desc(e: Exception) -> str:
    msg = str(e)
    if "429" in msg or "quota" in msg.lower() or "RESOURCE_EXHAUSTED" in msg:
        return "API 配額已用完（免費版每日 20 次），請明天再試，或至 Google AI Studio 開啟付費方案"
    return msg


def _error_result(e: Exception) -> list:
    return [{"date": "", "taxId": "", "invoiceNumber": "", "amount": "",
             "vendor": "辨識失敗", "description": _ocr_error_desc(e),
             "invoiceType": "", "confidence": "低"}]


def recognize_image(image: Image.Image) -> list:
    model = genai.GenerativeModel("gemini-2.5-flash")
    try:
        response = model.generate_content([OCR_PROMPT, image])
        return parse_response(response.text)
    except Exception as e:
        return _error_result(e)


def recognize_pdf(pdf_bytes: bytes) -> list:
    model = genai.GenerativeModel("gemini-2.5-flash")
    try:
        part = {"mime_type": "application/pdf", "data": pdf_bytes}
        response = model.generate_content([OCR_PROMPT, part])
        return parse_response(response.text)
    except Exception as e:
        return _error_result(e)


def recognize_file(uploaded_file) -> list:
    name = uploaded_file.name.lower()
    if name.endswith(".pdf"):
        return recognize_pdf(uploaded_file.read())
    else:
        return recognize_image(Image.open(uploaded_file))


# ── 初始化 session state ──────────────────────────────────────────────────────

if "results" not in st.session_state:
    st.session_state.results = []
if "filler_proc" not in st.session_state:
    st.session_state.filler_proc = None

# 清理孤兒 running file（Playwright 異常崩潰後的殘留）
_RF = "/tmp/easyflow_filler.running"
if os.path.exists(_RF):
    try:
        with open(_RF) as _f:
            _old_pid = int(_f.read().strip())
        os.kill(_old_pid, 0)   # 還活著 → 保留
    except (OSError, ValueError):
        os.remove(_RF)         # 程序已不存在 → 刪除孤兒 flag


# ── 上傳區 ───────────────────────────────────────────────────────────────────

with st.container():
    uploaded_files = st.file_uploader(
        "選擇發票照片或 PDF（可一次多張）",
        type=["jpg", "jpeg", "png", "webp", "pdf"],
        accept_multiple_files=True,
        help="支援統一發票、電子發票、收據、車票等；圖片或 PDF 皆可"
    )

    if uploaded_files:
        col_btn, col_clear = st.columns([2, 1])
        with col_btn:
            run_ocr = st.button("🔍 開始辨識", type="primary", use_container_width=True,
                                disabled=not _effective_key)
        with col_clear:
            if st.button("清除全部", use_container_width=True):
                st.session_state.results = []
                st.rerun()

        if run_ocr:
            existing_names = {r["file_name"] for r in st.session_state.results}
            to_process = [f for f in uploaded_files if f.name not in existing_names]

            if not to_process:
                st.info("這些檔案已辨識過，若要重新辨識請先點「清除全部」")
            else:
                n = len(to_process)
                progress = st.progress(0, text="準備辨識...")
                total_found = 0
                for i, file in enumerate(to_process):
                    progress.progress(i / n, text=f"辨識中（{i + 1}/{n}）：{file.name}")
                    results_list = recognize_file(file)
                    for result in results_list:
                        result["file_name"] = file.name
                        result["invoiceNumber"] = clean_invoice_number(result.get("invoiceNumber", ""))
                        apply_parking_rule(result)
                        if "cost_code" not in result:
                            result["cost_code"] = "A05"
                            result["cost_label"] = "旅費"
                        if "project_code" not in result:
                            result["project_code"] = ""
                            result["project_label"] = ""
                    # 依手寫編號排序（無編號的排後面）
                    results_list.sort(key=lambda x: x.get("pageNumber") or 9999)
                    st.session_state.results.extend(results_list)
                    total_found += len(results_list)
                progress.progress(1.0, text=f"完成！共辨識 {total_found} 份")
                progress.empty()
                st.success(f"完成！共辨識 {total_found} 份憑證（來自 {n} 個檔案）")


# ── 結果確認與複製區 ──────────────────────────────────────────────────────────

if st.session_state.results:
    st.divider()
    st.subheader("📋 辨識結果")
    st.caption("請確認每張發票的資料，有誤可直接修改，再複製到 EasyFlow")

    # ── 批次操作區 ────────────────────────────────────────────────────────────
    all_payloads = [
        {
            "date": r.get("date", ""),
            "taxId": r.get("taxId", ""),
            "invoiceNumber": clean_invoice_number(r.get("invoiceNumber", "")),
            "amount": r.get("amount", ""),
            "description": compose_description(
                r.get("date", ""), r.get("description", ""),
                r.get("project_code", ""), r.get("project_label", ""),
            ),
            "invoiceType": r.get("invoiceType", ""),
            "vendor": r.get("vendor", ""),
            "cost_code": r.get("cost_code", "A05"),
            "cost_label": r.get("cost_label", "旅費"),
        }
        for r in st.session_state.results
    ]

    col_pw, col_bm = st.columns([1, 1])

    with col_pw:
        _RUNNING_FILE = "/tmp/easyflow_filler.running"
        _proc = st.session_state.filler_proc
        # 瀏覽器視窗開著（running file 存在）OR 子程序仍在跑
        _filling = os.path.exists(_RUNNING_FILE) or (
            _proc is not None and _proc.poll() is None
        )

        if _filling:
            st.button("⏳ 填表進行中，請查看彈出的瀏覽器...", disabled=True, use_container_width=True)
        elif ef_ready:
            if st.button("🚀 送入 EasyFlow（自動填表）", type="primary", use_container_width=True):
                config = {
                    "invoices": all_payloads,
                    "username": ef_username,
                    "password": ef_password,
                    "defaults": {}
                }
                filler_path = os.path.join(os.path.dirname(__file__), "playwright_filler.py")
                proc = subprocess.Popen([sys.executable, filler_path, json.dumps(config)])
                st.session_state.filler_proc = proc
                st.rerun()
        else:
            st.button("🚀 送入 EasyFlow（自動填表）", disabled=True, use_container_width=True,
                      help="請先在左側填入工號與密碼")

    with col_bm:
        if len(st.session_state.results) > 1:
            st.code(json.dumps(all_payloads, ensure_ascii=False), language="json")
            st.caption("👆 手動模式：複製 JSON → 切到 EasyFlow → 點書籤貼上")

    st.divider()

    _projects = fetch_projects()
    _proj_opts = ["（不選）"] + [f"{p['code']}　{p['name']}" for p in _projects]

    for i, r in enumerate(st.session_state.results):
        confidence_color = {"高": "🟢", "中": "🟡", "低": "🔴"}.get(r.get("confidence", "低"), "🔴")
        inv_type = r.get("invoiceType", "")
        compliance_issues = check_compliance(r)
        compliance_icon = "🔴" if compliance_issues else "🟢"
        page_num = r.get("pageNumber")
        num_label = f"#{page_num}　" if page_num else ""
        label = f"{compliance_icon} {confidence_color} {num_label}{r['file_name']}　{r.get('vendor', '')}　{r.get('amount', '')} 元"

        with st.expander(label, expanded=(i == 0)):

            # ── 合規性警示 ────────────────────────────────────────────────
            if compliance_issues:
                for issue in compliance_issues:
                    st.warning(f"⚠️ {issue}")

            col1, col2 = st.columns(2)

            with col1:
                r["date"] = st.text_input("發票日期（YYYY/MM/DD）", r.get("date", ""), key=f"date_{i}")
                r["taxId"] = st.text_input("統一編號（8碼）", r.get("taxId", ""), key=f"tax_{i}",
                                            max_chars=8)
                r["invoiceNumber"] = st.text_input(
                    "發票號碼（2英文+8數字，共10碼）",
                    clean_invoice_number(r.get("invoiceNumber", "")),
                    key=f"inv_{i}", max_chars=10
                )
                r["amount"] = st.text_input("含稅金額", r.get("amount", ""), key=f"amt_{i}")

            with col2:
                st.text_input("店家名稱（參考用）", r.get("vendor", ""), key=f"vendor_{i}", disabled=True)
                st.text_input("EasyFlow 憑證類型代號", inv_type, key=f"type_{i}", disabled=True,
                              help="T223 二聯收銀機｜T251 三聯收銀機｜T254 電子發票｜T211 手開/電計｜T222 高鐵/台鐵/客運｜TXXX 收據")
                confidence = r.get("confidence", "低")
                st.metric("辨識信心", f"{confidence_color} {confidence}")

            # ── 費用類別（每張獨立選擇）────────────────────────────────
            _cur_code = r.get("cost_code", "A05")
            _cur_idx = next((j for j, c in enumerate(COST_CATEGORIES) if c["code"] == _cur_code), _COST_DEFAULT_IDX)
            _cost_sel = st.selectbox("費用類別", _COST_OPTS, index=_cur_idx, key=f"cost_{i}")
            _sel_code = _cost_sel.split("　")[0]
            r["cost_code"] = _sel_code
            r["cost_label"] = next(c["name"] for c in COST_CATEGORIES if c["code"] == _sel_code)

            # ── 活動描述 ───────────────────────────────────────────────
            r["description"] = st.text_input(
                "活動描述",
                r.get("description", ""),
                key=f"desc_{i}",
                placeholder="例：晶片計時服務執行-交通費(自車停車)",
            )

            # ── 專案（每張獨立選擇）───────────────────────────────────
            _cur_proj = r.get("project_code", "")
            _proj_idx = next((j + 1 for j, p in enumerate(_projects) if p["code"] == _cur_proj), 0)
            _proj_sel = st.selectbox("專案", _proj_opts, index=_proj_idx, key=f"proj_{i}")
            if _proj_sel != "（不選）":
                _pi = _proj_opts.index(_proj_sel) - 1
                r["project_code"]  = _projects[_pi]["code"]
                r["project_label"] = _projects[_pi]["name"]
            else:
                r["project_code"]  = ""
                r["project_label"] = ""

            # ── 費用說明預覽 ───────────────────────────────────────────
            _composed = compose_description(
                r.get("date", ""), r.get("description", ""),
                r.get("project_code", ""), r.get("project_label", ""),
            )
            st.info(f"**費用說明（送入 EasyFlow）：** {_composed}")

            # 發票號碼格式驗證
            inv_clean = clean_invoice_number(r.get("invoiceNumber", ""))
            if inv_clean and not re.match(r'^[A-Z]{2}\d{8}$', inv_clean):
                st.warning(f"⚠️ 發票號碼格式不符，應為 2 英文 + 8 數字（例如 AB12345678），目前：{inv_clean}")

            # ── JSON payload ──────────────────────────────────────────────
            payload = {
                "date": r.get("date", ""),
                "taxId": r.get("taxId", ""),
                "invoiceNumber": clean_invoice_number(r.get("invoiceNumber", "")),
                "amount": r.get("amount", ""),
                "description": compose_description(
                    r.get("date", ""), r.get("description", ""),
                    r.get("project_code", ""), r.get("project_label", ""),
                ),
            }
            payload_json = json.dumps(payload, ensure_ascii=False)

            st.code(payload_json, language="json")
            st.caption("👆 複製上方 JSON → 切到 EasyFlow → 點書籤「EasyFlow 自動填表」→ 貼上")

    st.divider()

    # ── 書籤安裝說明 ──────────────────────────────────────────────────────────
    with st.expander("📌 首次使用：如何安裝書籤？", expanded=False):
        st.markdown("""
**只需設定一次，之後每次用書籤一鍵填表。**

1. 在 Chrome 書籤列空白處按右鍵 → 「新增書籤...」
2. 名稱填：`EasyFlow 自動填表`
3. 網址欄位貼入以下程式碼：
""")

        bookmarklet_path = os.path.join(os.path.dirname(__file__), "bookmarklet_min.js")
        if os.path.exists(bookmarklet_path):
            with open(bookmarklet_path, "r", encoding="utf-8") as f:
                bookmarklet_code = f.read().strip()
            st.code(bookmarklet_code, language="javascript")
        else:
            st.error("找不到 bookmarklet_min.js 檔案")

        st.markdown("""
4. 儲存後，書籤列就會出現「EasyFlow 自動填表」按鈕
5. **每次使用流程**：
   - 在本頁複製發票的 JSON 資料
   - 打開 EasyFlow 報帳表單
   - 點「EasyFlow 自動填表」書籤
   - 貼上 JSON → 確認填入
   - 手動選「憑證類型」→ 點「新增」
""")
