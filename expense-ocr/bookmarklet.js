/**
 * EasyFlow 發票自動填表 Bookmarklet（批次版）
 *
 * 支援兩種輸入格式：
 * - 單筆：{"date":"...","taxId":"...","invoiceNumber":"...","amount":"...","description":"..."}
 * - 批次：[{...}, {...}, {...}]  ← 從報帳助手「複製全部」取得
 *
 * 每張憑證流程：
 *   【第一步 發票資訊】自動填入 → 員工手動選憑證類型 → 點「新增」→ 按確定繼續
 *   【第二步 費用明細】自動填入 → 員工手動選費用類別、歸屬部門 → 點「新增」→ 按確定繼續下一張
 */

(function () {
  // ── 1. 找到表單所在的第三層 iframe ──────────────────────────────
  var lvl1 = document.getElementById('ifmFucntionLocation');
  if (!lvl1) { alert('❌ 找不到 EasyFlow 表單框架\n請確認您在報帳申請單頁面'); return; }
  var lvl2 = lvl1.contentDocument.getElementById('ifmAppLocation');
  if (!lvl2) { alert('❌ 找不到表單內容，請重新整理後再試'); return; }
  var doc = lvl2.contentDocument;

  if (!doc.getElementById('uniNumber')) {
    alert('❌ 此頁面不是報帳申請單\n請先開啟「請款_預支費用申請單」');
    return;
  }

  // ── 2. 讀取並解析 JSON ───────────────────────────────────────────
  var dataStr = prompt('📋 請貼上發票資料（單筆物件或多筆陣列均可）');
  if (!dataStr || dataStr.trim() === '') return;

  var items;
  try {
    var parsed = JSON.parse(dataStr.trim());
    items = Array.isArray(parsed) ? parsed : [parsed];
  } catch (e) {
    alert('❌ 資料格式錯誤：' + e.message);
    return;
  }

  var total = items.length;

  // ── 3. 工具函數 ──────────────────────────────────────────────────
  function setField(id, value) {
    var el = doc.getElementById(id);
    if (el && value) el.value = value;
  }

  function scrollTo(id) {
    var el = doc.getElementById(id);
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  function cleanInvoice(raw) {
    return (raw || '').replace(/[-\s]/g, '').toUpperCase();
  }

  // ── 4. 逐張處理 ─────────────────────────────────────────────────
  for (var i = 0; i < total; i++) {
    var d = items[i];
    var seq = (i + 1) + '/' + total;
    var inv = cleanInvoice(d.invoiceNumber);

    // 驗證發票號碼格式
    if (inv && !/^[A-Z]{2}\d{8}$/.test(inv)) {
      if (!confirm('⚠️ 第' + seq + '張發票號碼格式可能不符\n值：' + inv + '\n\n仍要繼續？')) return;
    }

    // ── 第一步：填入發票資訊 ────────────────────────────────────
    var dateEl = doc.getElementById('invoceDate_txt');
    if (dateEl && d.date) {
      dateEl.removeAttribute('readonly');
      dateEl.value = d.date;
      dateEl.setAttribute('readonly', 'readonly');
    }
    setField('uniNumber', d.taxId || '');
    setField('invoceNumber', inv);
    setField('invoceOriTaxSum', d.amount || '');
    scrollTo('uniNumber');

    var msg1 = '🧾 【第' + seq + '張】發票資訊已填入\n';
    if (d.date)   msg1 += '✅ 發票日期：' + d.date + '\n';
    if (d.taxId)  msg1 += '✅ 統一編號：' + d.taxId + '\n';
    if (inv)      msg1 += '✅ 發票號碼：' + inv + '\n';
    if (d.amount) msg1 += '✅ 含稅金額：' + d.amount + '\n';
    msg1 += '\n📌 請完成：\n1. 點「憑證類型」旁 ... 選擇代號\n2. 確認資料正確\n3. 點「新增」\n\n完成後按「確定」繼續費用明細';

    if (!confirm(msg1)) {
      alert('已中止。已完成前 ' + i + ' 張，第 ' + (i + 1) + ' 張發票資訊尚未新增。');
      return;
    }

    // ── 第二步：填入費用明細 ────────────────────────────────────
    var drp = doc.getElementById('drpInvoceNumber');
    if (drp && drp.options.length > 1) {
      drp.value = drp.options[drp.options.length - 1].value;
    }
    setField('Memo_txt', d.description || '');
    scrollTo('Memo_txt');

    var msg2 = '📂 【第' + seq + '張】費用明細已填入\n';
    if (d.description) msg2 += '✅ 費用說明：' + d.description + '\n';
    msg2 += '✅ 憑證項次：已自動選取最新一筆\n';
    msg2 += '\n📌 請完成：\n1. 選「費用類別」\n2. 選「費用歸屬部門」\n3. 點「新增」\n\n完成後按「確定」';
    if (i < total - 1) msg2 += '繼續下一張（第 ' + (i + 2) + '/' + total + ' 張）';
    else msg2 += '完成全部';

    if (!confirm(msg2)) {
      alert('已中止。第 ' + (i + 1) + ' 張費用明細尚未新增。');
      return;
    }
  }

  alert('🎉 全部完成！共處理 ' + total + ' 張憑證。');
})();
