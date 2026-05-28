(async () => {
  const LOG = '[autoR]';
  const log = (...args) => console.log(LOG, ...args);
  const warn = (...args) => console.warn(LOG, ...args);

  const DEFAULT_INVOICE = '4601609273';
  const DELAY_AFTER_CLICK_MS = 1200;
  const DELAY_AFTER_NAV_MS = 1200;
  const DELAY_AFTER_FORM_FILL_MS = 500;
  const DELAY_AFTER_AFTER_FILL_MS = 500;
  const DELAY_AFTER_CLOSE_MS = 1000;
  const invoiceNo =
    (typeof localStorage !== 'undefined' && localStorage.getItem('autoR_invoiceNo')?.trim()) ||
    window.__autoRConfig?.invoiceNo?.trim() ||
    DEFAULT_INVOICE;

  log('Starting', { invoiceNo, config: window.__autoRConfig });

  const TARGET_PATHNAME = '/faces/SoDinhDanh';

  const SELECTORS = {
    navToSoDinhDanh: '#pt1\\:dc7\\:dinhDanhhangHoa > div > table > tbody > tr > td.x18i > a',
    btn: '#pt1\\:b1',
    afterFillClick: '#pt1\\:cb3 > a',
    closePrimary: '#pt1\\:b4',
    closeAlt: '#pt1\\:d3\\:\\:close',
    soDinhDanhInput: '#pt1\\:it11\\:\\:content',
    qrImage: '#pt1\\:i1',
    targetSelect: '#pt1\\:soc1\\:\\:content',
    input: '#pt1\\:it5\\:\\:content',
    typeSelect: '#pt1\\:soc2\\:\\:content',
  };

  const FALLBACK_SELECTORS = {
    // ADF ids can be re-prefixed; match by suffix when exact ids aren't present.
    targetSelect: '[id$="soc1::content"]',
    input: '[id$="it5::content"]',
    typeSelect: '[id$="soc2::content"]',
  };

  function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  function parseSoDinhDanhFromPartialResponse(text) {
    try {
      const xmlDoc = new DOMParser().parseFromString(text, 'text/xml');
      const update = xmlDoc.querySelector('update[id="pt1:pc1:t2"]');
      const html = update?.textContent || '';
      if (!html) return null;

      const doc = new DOMParser().parseFromString(html, 'text/html');
      const cell =
        doc.querySelector('td[id$=":0:c2"] span') ||
        doc.querySelector('td[id*=":t2:0:c2"] span') ||
        doc.querySelector('#pt1\\:pc1\\:t2\\:0\\:c2 span');

      const value = (cell?.textContent || '').trim();
      return value || null;
    } catch (e) {
      warn('Failed to parse partial-response', e);
      return null;
    }
  }

  function captureRenderedValues() {
    const soEl = document.querySelector(SELECTORS.soDinhDanhInput);
    const qrEl = document.querySelector(SELECTORS.qrImage);

    const soDinhDanh = (soEl?.value || soEl?.textContent || '').trim();
    const qrBase64 = (qrEl?.getAttribute?.('src') || '').trim();

    return {
      soDinhDanh: soDinhDanh || null,
      qrBase64: qrBase64 || null,
    };
  }

  async function waitForRenderedValues(maxMs = 20000, intervalMs = 250, previousSoDinhDanh = null) {
    const start = Date.now();
    let attempts = 0;

    while (Date.now() - start <= maxMs) {
      attempts += 1;
      const { soDinhDanh, qrBase64 } = captureRenderedValues();
      const hasValues = Boolean(soDinhDanh) && Boolean(qrBase64);
      const isNew = !previousSoDinhDanh || soDinhDanh !== previousSoDinhDanh;

      if (hasValues && isNew) {
        log(`Captured rendered values after ${attempts} check(s), ${Date.now() - start}ms`, {
          soDinhDanh,
          qrLen: qrBase64.length,
          previousSoDinhDanh: previousSoDinhDanh || '(none)',
        });
        return { soDinhDanh, qrBase64 };
      }

      if (attempts === 1 || attempts % 10 === 0) {
        log(`Waiting for rendered values… check ${attempts}, ${Date.now() - start}ms`, {
          soDinhDanh: soDinhDanh ? (isNew ? 'present' : 'stale') : 'missing',
          qrBase64: qrBase64 ? 'present' : 'missing',
          previousSoDinhDanh: previousSoDinhDanh || '(none)',
        });
      }

      await sleep(intervalMs);
    }

    warn('Timed out waiting for rendered values', { previousSoDinhDanh });
    return { soDinhDanh: null, qrBase64: null };
  }

  function isOnTargetPage() {
    return window.location?.pathname === TARGET_PATHNAME;
  }

  function maybeNavigateToTarget() {
    if (isOnTargetPage()) {
      return { status: 'already_on_target' };
    }

    const link = document.querySelector(SELECTORS.navToSoDinhDanh);
    if (!link) {
      warn('Navigation link not found:', SELECTORS.navToSoDinhDanh);
      return { status: 'nav_link_missing' };
    }

    log('Not on target page, clicking navigation link…', {
      current: window.location?.pathname,
      target: TARGET_PATHNAME,
    });
    link.click();
    return { status: 'navigating' };
  }

  function queryBtn() {
    return document.querySelector(SELECTORS.btn);
  }

  function fillForm() {
    const targetSelect =
      document.querySelector(SELECTORS.targetSelect) ||
      document.querySelector(FALLBACK_SELECTORS.targetSelect);
    const input =
      document.querySelector(SELECTORS.input) || document.querySelector(FALLBACK_SELECTORS.input);
    const typeSelect =
      document.querySelector(SELECTORS.typeSelect) ||
      document.querySelector(FALLBACK_SELECTORS.typeSelect);

    const missing = Object.entries({ targetSelect, input, typeSelect })
      .filter(([, el]) => !el)
      .map(([name]) => name);

    if (missing.length) {
      log('Form elements not ready:', missing);
      // helpful when ADF changes ids
      if (missing.includes('targetSelect')) {
        log('Debug targetSelect selectors:', {
          exact: SELECTORS.targetSelect,
          fallback: FALLBACK_SELECTORS.targetSelect,
        });
      }
      return false;
    }

    const formValues = window.__autoRConfig?.formValues || { target: '0', type: '0' };
    const targetVal = String(formValues.target ?? '0');
    const typeVal = String(formValues.type ?? '0');

    log('Filling form', { target: targetVal, type: typeVal, invoiceNo });
    targetSelect.value = targetVal;
    input.value = invoiceNo;
    typeSelect.value = typeVal;

    [targetSelect, input, typeSelect].forEach((el) => {
      el.dispatchEvent(new Event('change', { bubbles: true }));
      el.dispatchEvent(new Event('input', { bubbles: true }));
    });

    log('Form filled', {
      invoiceNo,
      target: targetSelect.value,
      type: typeSelect.value,
    });

    return true;
  }

  function waitForForm(maxMs = 15000, intervalMs = 300) {
    if (fillForm()) {
      return Promise.resolve(true);
    }

    warn(`Waiting for form fields (max ${maxMs}ms)`);

    return new Promise((resolve) => {
      const start = Date.now();
      let attempts = 0;

      const timer = setInterval(() => {
        attempts += 1;
        const elapsed = Date.now() - start;

        if (fillForm()) {
          clearInterval(timer);
          log(`Form filled after ${attempts} attempt(s), ${elapsed}ms`);
          resolve(true);
        } else if (elapsed > maxMs) {
          clearInterval(timer);
          warn(`Form timeout after ${attempts} attempt(s), ${elapsed}ms`);
          resolve(false);
        } else if (attempts === 1 || attempts % 10 === 0) {
          log(`Still waiting for form… attempt ${attempts}, ${elapsed}ms`);
        }
      }, intervalMs);
    });
  }

  function clickAfterFill() {
    const el = document.querySelector(SELECTORS.afterFillClick);
    if (!el) {
      return false;
    }
    el.click();
    return true;
  }

  function waitForAfterFillClick(maxMs = 15000, intervalMs = 300) {
    if (clickAfterFill()) {
      log('Clicked after-fill link');
      return Promise.resolve(true);
    }

    warn(`Waiting for after-fill link (max ${maxMs}ms)`);
    return new Promise((resolve) => {
      const start = Date.now();
      let attempts = 0;

      const timer = setInterval(() => {
        attempts += 1;
        const elapsed = Date.now() - start;

        if (clickAfterFill()) {
          clearInterval(timer);
          log(`After-fill link clicked after ${attempts} attempt(s), ${elapsed}ms`);
          resolve(true);
        } else if (elapsed > maxMs) {
          clearInterval(timer);
          warn(`After-fill link timeout after ${attempts} attempt(s), ${elapsed}ms`);
          resolve(false);
        } else if (attempts === 1 || attempts % 10 === 0) {
          log(`Still waiting for after-fill link… attempt ${attempts}, ${elapsed}ms`);
        }
      }, intervalMs);
    });
  }

  function clickClose() {
    const el =
      document.querySelector(SELECTORS.closePrimary) || document.querySelector(SELECTORS.closeAlt);
    if (!el) return false;
    try {
      el.focus?.();
    } catch {}

    // Some ADF elements ignore .click(); dispatch a real mouse click too.
    try {
      el.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true }));
      el.dispatchEvent(new MouseEvent('mouseup', { bubbles: true, cancelable: true }));
      el.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
    } catch {
      el.click();
    }
    return true;
  }

  function isPopupClosed() {
    // Heuristic: when popup closes, these rendered result elements typically disappear or clear.
    const soEl = document.querySelector('#pt1\\:p1\\:\\:popup-container');
    return !soEl;
  }

  function isMaskingFrameHidden() {
    // ADF masking frame used during popup/modal interactions.
    const iframe = document.querySelector('#f1\\:\\:__af_Z_maskingframe > iframe');
    if (!iframe) return false;

    const style = window.getComputedStyle(iframe);
    // Hidden/none indicates the mask is gone => close completed.
    if (style.visibility === 'hidden' || style.display === 'none') return true;
    if (Number(style.opacity) === 0) return true;
    return false;
  }

  function waitForClose(maxMs = 15000, intervalMs = 250) {
    if (clickClose()) {
      log('Clicked close');
      // If close didn't actually close, we'll detect below.
    }

    warn(`Waiting for close button (max ${maxMs}ms)`);
    return new Promise((resolve) => {
      const start = Date.now();
      let attempts = 0;
      const timer = setInterval(() => {
        attempts += 1;
        const elapsed = Date.now() - start;
        if (isMaskingFrameHidden() || isPopupClosed()) {
          clearInterval(timer);
          log(`Popup closed after ${attempts} check(s), ${elapsed}ms`);
          resolve(true);
        } else if (clickClose()) {
          clearInterval(timer);
          log(`Close clicked after ${attempts} attempt(s), ${elapsed}ms`);
          // Wait a moment for DOM to update; if still not closed, keep polling.
          setTimeout(() => {
            if (isMaskingFrameHidden() || isPopupClosed()) {
              log('Popup closed after click');
              resolve(true);
            } else {
              warn('Close click did not close popup; will reload');
              try {
                window.location.reload();
              } catch {}
              resolve(true);
            }
          }, 800);
        } else if (elapsed > maxMs) {
          clearInterval(timer);
          warn(`Close timeout after ${attempts} attempt(s), ${elapsed}ms`);
          // Fallback: reload page to reset state.
          try {
            window.location.reload();
            log('Reloaded page after close timeout');
            resolve(true);
            return;
          } catch {}
          resolve(false);
        } else if (attempts === 1 || attempts % 10 === 0) {
          log(`Still waiting for close… attempt ${attempts}, ${elapsed}ms`);
        }
      }, intervalMs);
    });
  }

  async function runOnce(maxMs = 20000, intervalMs = 300, previousSoDinhDanh = null) {
    const btn = queryBtn();
    if (!btn) {
      return { status: 'btn_missing' };
    }

    log('Clicking button');
    btn.click();

    log(`Waiting ${DELAY_AFTER_CLICK_MS}ms after click`);
    await sleep(DELAY_AFTER_CLICK_MS);

    const okForm = await waitForForm(maxMs, intervalMs);
    if (!okForm) {
      return { status: 'form_timeout' };
    }

    log(`Waiting ${DELAY_AFTER_FORM_FILL_MS}ms after form fill`);
    await sleep(DELAY_AFTER_FORM_FILL_MS);

    const clicked = await waitForAfterFillClick(maxMs, intervalMs);
    if (!clicked) {
      return { status: 'after_fill_click_timeout' };
    }

    log(`Waiting ${DELAY_AFTER_AFTER_FILL_MS}ms for server render`);
    await sleep(DELAY_AFTER_AFTER_FILL_MS);

    const { soDinhDanh, qrBase64 } = await waitForRenderedValues(
      maxMs,
      intervalMs,
      previousSoDinhDanh
    );
    if (!soDinhDanh || !qrBase64) {
      return { status: 'render_value_timeout', soDinhDanh, qrBase64 };
    }

    const closed = await waitForClose(maxMs, intervalMs);
    if (!closed) {
      return { status: 'close_timeout', soDinhDanh, qrBase64 };
    }

    log(`Waiting ${DELAY_AFTER_CLOSE_MS}ms after close`);
    await sleep(DELAY_AFTER_CLOSE_MS);

    return { status: 'ok', soDinhDanh, qrBase64 };
  }

  async function main() {
    const config = window.__autoRConfig || {};

    if (config.ensurePageOnly) {
      const nav = maybeNavigateToTarget();
      if (nav.status === 'navigating' || nav.status === 'nav_link_missing') {
        return nav;
      }
      log('On target page', window.location?.pathname);
      log(`Waiting ${DELAY_AFTER_NAV_MS}ms for render`);
      await sleep(DELAY_AFTER_NAV_MS);
      return { status: 'ready' };
    }

    if (config.singleRun) {
      if (!isOnTargetPage()) {
        const nav = maybeNavigateToTarget();
        if (nav.status === 'navigating' || nav.status === 'nav_link_missing') {
          return nav;
        }
        await sleep(DELAY_AFTER_NAV_MS);
      }

      log('Single run starting', { lastSoDinhDanh: config.lastSoDinhDanh || '(none)' });
      return runOnce(20000, 300, config.lastSoDinhDanh || null);
    }

    warn('Unknown config mode');
    return { status: 'unknown_config' };
  }

  const ok = await main();
  log('Run finished:', ok);
  return ok;

// node -e "
// const key = 'xR9m';
// const msg = 'Chúc mừng sinh nhật nhé :>';
// const utf8 = [...new TextEncoder().encode(msg)];
// const enc = utf8.map((b, i) => b ^ key.charCodeAt(i % key.length));
// const dec = new TextDecoder().decode(Uint8Array.from(enc.map((b, i) => b ^ key.charCodeAt(i % key.length))));
// console.log(JSON.stringify(enc));
// console.log('verify:', dec);
// console.log('len', enc.length);
// "

})();
