#!/usr/bin/env python3
"""
EasyFlow 自動填表 - Playwright 版
使用 Playwright 內建 Chromium（穩定、不依賴真實 Chrome）
持久化 Profile 保留登入狀態。
"""

import json
import os
import sys
import time

from playwright.sync_api import sync_playwright

EASYFLOW_LOGIN = "https://efgp.h2u.com.tw:20103/NaNaWeb/GP/Authentication"
PROFILE_DIR    = os.path.expanduser("~/.easyflow-pw-profile")
PID_FILE       = "/tmp/easyflow_filler.pid"
RUNNING_FILE   = "/tmp/easyflow_filler.running"   # 存在代表瀏覽器視窗開著

INVOICE_TYPE_MAP = {
    "T223": "二聯式收銀機統一發票",
    "T251": "三聯式收銀機統一發票",
    "T254": "電子發票(應稅)",
    "T211": "手開三聯式統一發票",
    "T222": "有起迄票",
    "TXXX": "免用統一發票收據",
}


def _check_single_instance():
    """PID 檔防止同時執行多個填表視窗"""
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE) as f:
                old_pid = int(f.read().strip())
            os.kill(old_pid, 0)          # 還活著
            print(f"⚠️ 已有一個填表視窗正在執行（PID {old_pid}），請關閉後再試")
            sys.exit(0)
        except (OSError, ValueError):
            pass                         # 舊 PID 已不存在，繼續
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))


def _cleanup():
    for path in [PID_FILE, RUNNING_FILE]:
        try:
            os.remove(path)
        except Exception:
            pass


# ── 瀏覽器內狀態提示 ──────────────────────────────────────────────────────────

def _set_browser_status(page, msg: str, color: str = "#2196F3"):
    try:
        page.evaluate(f"""
            (function() {{
                var d = document.getElementById('__pw_status');
                if (!d) {{
                    d = document.createElement('div');
                    d.id = '__pw_status';
                    d.style.cssText = 'position:fixed;top:12px;right:12px;z-index:2147483647;'
                        + 'padding:10px 16px;border-radius:8px;font-size:14px;'
                        + 'color:#fff;box-shadow:0 2px 8px rgba(0,0,0,.3);';
                    document.body.appendChild(d);
                }}
                d.style.background = {json.dumps(color)};
                d.textContent = {json.dumps(msg)};
            }})()
        """)
    except Exception:
        pass


# ── 登入偵測（輪詢 URL，比 wait_for_url 更可靠）────────────────────────────

def wait_for_login(page, timeout: int = 180) -> bool:
    print("  等待登入中", end="", flush=True)
    for _ in range(timeout * 2):
        try:
            if EASYFLOW_LOGIN not in page.url:
                print(" ✓")
                return True
        except Exception:
            pass
        time.sleep(0.5)
        print(".", end="", flush=True)
    print(" ✗（逾時）")
    return False


# ── iframe 內 JS ──────────────────────────────────────────────────────────────

def js(page, code: str):
    return page.evaluate(f"""
        (function() {{
            var l1 = document.getElementById('ifmFucntionLocation');
            var l2 = l1.contentDocument.getElementById('ifmAppLocation');
            var doc = l2.contentDocument;
            {code}
        }})()
    """)


def js_safe(page, code: str, label: str = ""):
    try:
        return js(page, code)
    except Exception as e:
        print(f"  ⚠️ [{label}] JS 失敗（繼續）：{e}")
        return None


def wait_for_form(page, timeout: int = 30) -> bool:
    print("  等待表單就緒", end="", flush=True)
    for _ in range(timeout * 2):
        try:
            if js(page, "return doc.getElementById('uniNumber') ? 'ok' : 'wait';") == "ok":
                print(" ✓")
                return True
        except Exception:
            pass
        time.sleep(0.5)
        print(".", end="", flush=True)
    print(" ✗")
    return False


def wait_for_invoice_count(page, expected: int, timeout: int = 15) -> bool:
    for _ in range(timeout * 2):
        try:
            if js(page, "return doc.getElementById('drpInvoceNumber').options.length;") >= expected:
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


# ── 主流程 ────────────────────────────────────────────────────────────────────

def fill_easyflow(config: dict):
    _check_single_instance()
    invoices = config["invoices"]
    username = config["username"]
    password = config["password"]
    defaults = config.get("defaults", {})

    try:
        _run(invoices, username, password, defaults)
    finally:
        _cleanup()


def _run(invoices, username, password, defaults):
    with sync_playwright() as p:
        print(f"▶ 啟動 Playwright Chromium  Profile: {PROFILE_DIR}")

        context = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            headless=False,
            args=[
                "--start-maximized",
                "--disable-blink-features=AutomationControlled",
            ],
            ignore_https_errors=True,
        )
        # 隱藏自動化特徵
        context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        page = context.new_page()

        # 標記視窗已開啟（讓 Streamlit 知道瀏覽器還活著）
        with open(RUNNING_FILE, "w") as f:
            f.write(str(os.getpid()))

        # ── 1. 登入 ──────────────────────────────────────────────────
        print("▶ 開啟 EasyFlow...")
        page.goto(EASYFLOW_LOGIN)
        page.wait_for_load_state("networkidle")

        if EASYFLOW_LOGIN in page.url:
            # 嘗試自動填入帳號密碼
            try:
                user_input = page.locator("input[type='text']").first
                user_input.click()
                user_input.fill(username)
                page.locator("input[type='password']").fill(password)
                page.wait_for_timeout(500)
                page.locator(
                    "input[type='submit'], button[type='submit'], button:has-text('登入')"
                ).first.click()
                page.wait_for_load_state("networkidle")
                page.wait_for_timeout(2000)
                print("  已送出登入表單")
            except Exception as e:
                print(f"  ⚠️ 自動填入失敗（{e}），請手動登入")

            # 若仍在登入頁，等待使用者手動操作
            if EASYFLOW_LOGIN in page.url:
                _set_browser_status(page, "⏳ 請輸入帳號密碼並登入，登入後自動繼續...", "#FF9800")
                print("  仍在登入頁，等待手動登入（最多 3 分鐘）...")
                if not wait_for_login(page, timeout=180):
                    print("❌ 等待登入逾時，請關閉視窗後重試")
                    return
        else:
            print("  Cookie 有效，略過登入 ✓")

        _set_browser_status(page, "✅ 已登入，正在導航到申請單...", "#4CAF50")
        page.wait_for_timeout(1500)

        # ── 2. 導航到申請單 ───────────────────────────────────────────
        print("▶ 導航到請款_預支費用申請單...")
        nav_ok = False
        try:
            page.locator("text=發起流程").first.click()
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(1200)

            search = page.locator(
                "input[placeholder*='查詢'], input[placeholder*='流程']"
            ).first
            search.fill("請款_預支費用申請單")
            search.press("Enter")
            page.wait_for_timeout(1500)

            page.locator("text=請款_預支費用申請單(YH)").first.click()
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(2000)
            nav_ok = True
        except Exception as e:
            print(f"  ⚠️ 自動導航失敗（{e}）")
            _set_browser_status(
                page,
                "⚠️ 自動導航失敗，請手動開啟「請款_預支費用申請單(YH)」，開啟後程式自動繼續...",
                "#FF5722",
            )
            print("  請手動開啟「請款_預支費用申請單(YH)」，程式持續等待...")

        # ── 3. 等表單就緒 ─────────────────────────────────────────────
        if not nav_ok:
            _set_browser_status(page, "⏳ 等待表單載入...", "#FF9800")

        print("▶ 等待表單載入...")
        if not wait_for_form(page, timeout=60):
            print("  繼續等待（最多 5 分鐘）...")
            _set_browser_status(page, "⏳ 等待表單載入（最多 5 分鐘）...", "#FF9800")
            if not wait_for_form(page, timeout=300):
                print("❌ 表單逾時，請關閉視窗後重試")
                return

        _set_browser_status(page, "✅ 表單已就緒，開始填入資料...", "#4CAF50")

        # ── 4. 填基本欄位 ─────────────────────────────────────────────
        print("▶ 填入基本欄位...")

        js_safe(page, "var r = doc.getElementById('apa00_0'); if (r) r.click();", "申請類別")
        time.sleep(0.5)

        js_safe(page, """
            var t = doc.getElementById('diaApa36_txt');
            var l = doc.getElementById('diaApa36_lbl');
            if (t) t.value = '6';
            if (l) l.value = '其他應付費用-員工';
        """, "帳款類別")

        js_safe(page, "var r = doc.getElementById('PayTargetType_rad_1'); if (r) r.click();", "受款人性質")
        time.sleep(1.5)

        # ── 5. 逐張發票填入 ───────────────────────────────────────────
        total = len(invoices)
        print(f"▶ 開始填入 {total} 張發票明細\n")

        for i, inv in enumerate(invoices):
            vendor = inv.get("vendor", "")
            amount = inv.get("amount", "")
            print(f"▶ 第 {i+1}/{total} 張：{vendor}　{amount} 元")
            _set_browser_status(page, f"填入第 {i+1}/{total} 張：{vendor} {amount} 元")

            inv_type_code  = inv.get("invoiceType", "")
            inv_type_label = INVOICE_TYPE_MAP.get(inv_type_code, inv_type_code)
            date_val       = inv.get("date", "")
            tax_id         = inv.get("taxId", "")
            inv_number     = inv.get("invoiceNumber", "")
            description    = inv.get("description", "")

            js_safe(page, f"""
                doc.getElementById('InvoceCate_txt').value = {json.dumps(inv_type_code)};
                doc.getElementById('InvoceCate_lbl').value = {json.dumps(inv_type_label)};
            """, "憑證類型")

            js_safe(page, f"""
                var el = doc.getElementById('invoceDate_txt');
                if (el) {{
                    el.removeAttribute('readonly');
                    el.value = {json.dumps(date_val)};
                    el.setAttribute('readonly', 'readonly');
                }}
            """, "發票日期")

            js_safe(page, f"""
                doc.getElementById('uniNumber').value       = {json.dumps(tax_id)};
                doc.getElementById('invoceNumber').value    = {json.dumps(inv_number)};
                doc.getElementById('invoceOriTaxSum').value = {json.dumps(amount)};
            """, "金額/發票號")

            print(f"  日期={date_val}  統編={tax_id}  發票={inv_number}  金額={amount}")

            js_safe(page, "doc.getElementById('Invoce_add').click();", "Invoce_add")
            if not wait_for_invoice_count(page, i + 2):
                print(f"  ⚠️ 第 {i+1} 張：等待憑證新增逾時，繼續...")
                time.sleep(1)

            js_safe(page, """
                var drp = doc.getElementById('drpInvoceNumber');
                if (drp && drp.options.length > 1)
                    drp.value = drp.options[drp.options.length - 1].value;
            """, "選憑證項次")

            _cost_code  = inv.get("cost_code")  or defaults.get("cost_code", "")
            _cost_label = inv.get("cost_label") or defaults.get("cost_label", "")
            js_safe(page, f"""
                doc.getElementById('cost_txt').value = {json.dumps(_cost_code)};
                doc.getElementById('cost_lbl').value = {json.dumps(_cost_label)};
            """, "費用類別")

            js_safe(page, f"doc.getElementById('Memo_txt').value = {json.dumps(description)};", "費用說明")
            print(f"  說明={description}")

            js_safe(page, "doc.getElementById('Fee_add').click();", "Fee_add")
            time.sleep(2.5)

        # ── 6. 完成 ───────────────────────────────────────────────────
        print(f"\n{'='*50}")
        print(f"✅ 完成！共填入 {total} 張憑證")
        print("請確認資料無誤後點「發起」")
        print(f"{'='*50}")

        _set_browser_status(
            page,
            f"✅ 完成！共填入 {total} 張憑證，請確認後點「發起」",
            "#4CAF50",
        )

        try:
            page.evaluate("window.scrollTo(0, 0)")
        except Exception:
            pass

        # 等使用者關閉視窗（最多 30 分鐘）
        try:
            page.wait_for_event("close", timeout=1_800_000)
        except Exception:
            pass


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法：python playwright_filler.py '<config_json>'")
        sys.exit(1)
    config = json.loads(sys.argv[1])
    fill_easyflow(config)
