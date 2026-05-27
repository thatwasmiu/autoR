(async () => {
  const LOG = '[autoR]';
  const log = (...args) => console.log(LOG, ...args);
  const warn = (...args) => console.warn(LOG, ...args);

  const DEFAULT_INVOICE = '4601609273';
  const DELAY_AFTER_CLICK_MS = 1000;
  const invoiceNo = window.__autoRConfig?.invoiceNo?.trim() || DEFAULT_INVOICE;

  log('Starting', { invoiceNo, config: window.__autoRConfig });

  const SELECTORS = {
    btn: '#pt1\\:b1',
    targetSelect: '#pt1\\:soc1\\:\\:content',
    input: '#pt1\\:it5\\:\\:content',
    typeSelect: '#pt1\\:soc2\\:\\:content',
  };

  function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  function queryBtn() {
    return document.querySelector(SELECTORS.btn);
  }

  function fillForm() {
    const targetSelect = document.querySelector(SELECTORS.targetSelect);
    const input = document.querySelector(SELECTORS.input);
    const typeSelect = document.querySelector(SELECTORS.typeSelect);

    const missing = Object.entries({ targetSelect, input, typeSelect })
      .filter(([, el]) => !el)
      .map(([name]) => name);

    if (missing.length) {
      log('Form elements not ready:', missing);
      return false;
    }

    log('Filling form');
    targetSelect.value = '0';
    input.value = invoiceNo;
    typeSelect.value = '0';

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

  function waitForBtn(maxMs = 15000, intervalMs = 300) {
    const btn = queryBtn();
    if (btn) {
      return Promise.resolve(btn);
    }

    warn(`Waiting for button (max ${maxMs}ms)`);

    return new Promise((resolve) => {
      const start = Date.now();
      let attempts = 0;

      const timer = setInterval(() => {
        attempts += 1;
        const elapsed = Date.now() - start;
        const found = queryBtn();

        if (found) {
          clearInterval(timer);
          log(`Button found after ${attempts} attempt(s), ${elapsed}ms`);
          resolve(found);
        } else if (elapsed > maxMs) {
          clearInterval(timer);
          warn(`Button not found after ${attempts} attempt(s), ${elapsed}ms`);
          resolve(null);
        } else if (attempts === 1 || attempts % 10 === 0) {
          log(`Still waiting for button… attempt ${attempts}, ${elapsed}ms`);
        }
      }, intervalMs);
    });
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

  async function waitAndRun(maxMs = 15000, intervalMs = 300) {
    const btn = await waitForBtn(maxMs, intervalMs);
    if (!btn) {
      return false;
    }

    log('Clicking button');
    btn.click();

    log(`Waiting ${DELAY_AFTER_CLICK_MS}ms after click`);
    await sleep(DELAY_AFTER_CLICK_MS);

    return waitForForm(maxMs, intervalMs);
  }

  const ok = await waitAndRun();
  log(ok ? 'Run finished successfully' : 'Run failed');
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
