const LOG = '[autoR]';
const log = (...args) => console.log(LOG, ...args);
const warn = (...args) => console.warn(LOG, ...args);
const error = (...args) => console.error(LOG, ...args);

const DEFAULT_INVOICE = '4601609273';
const TARGET_PATH = '/faces/SoDinhDanh';
const DEFAULT_SCRIPT_URL =
  'https://script.google.com/macros/s/AKfycby_XxGnTT1NjgSS_rF27FIVZLSw9NHO2uihMrAqc-Kvoy-jBHSer-JEW0-HdlgXnR22Vg/exec';

const runBtn = document.getElementById('run');
const resetBtn = document.getElementById('reset');
const statusEl = document.getElementById('status');
const birthdayEl = document.getElementById('birthday');
const scriptUrlInput = document.getElementById('scriptUrl');
const invoiceInput = document.getElementById('invoice');
const formConfigsInput = document.getElementById('formConfigs');

function showBirthdayIfToday() {
  if (!autoRIsBirthdayToday()) {
    return;
  }
  birthdayEl.textContent = autoRDecodeMessage();
  birthdayEl.classList.add('visible');
  log('Birthday message shown');
}

function setStatus(text, isError = false) {
  statusEl.textContent = text;
  statusEl.classList.toggle('error', isError);
  log('Status:', text, isError ? '(error)' : '');
}

function resolvedInvoice() {
  const value = invoiceInput.value.trim();
  return value || DEFAULT_INVOICE;
}

function resolvedScriptUrl() {
  const value = (scriptUrlInput?.value || '').trim();
  return value || DEFAULT_SCRIPT_URL;
}

function resolvedFormConfigs() {
  const text = (formConfigsInput?.value || '').trim();
  if (!text) {
    return AUTO_R_DEFAULT_FORM_CONFIGS;
  }
  try {
    return parseFormConfigsJson(text);
  } catch (e) {
    warn('Invalid form configs JSON, using default', e);
    return AUTO_R_DEFAULT_FORM_CONFIGS;
  }
}

function totalRunsCount(formConfigs) {
  return formConfigs.reduce((sum, c) => sum + (Number(c.runs) || 0), 0);
}

async function loadSavedSettings() {
  const { invoiceNo, scriptUrl, formConfigsJson } = await chrome.storage.local.get({
    invoiceNo: DEFAULT_INVOICE,
    scriptUrl: DEFAULT_SCRIPT_URL,
    formConfigsJson: JSON.stringify(AUTO_R_DEFAULT_FORM_CONFIGS, null, 2),
  });
  invoiceInput.value = invoiceNo;
  if (scriptUrlInput) {
    scriptUrlInput.value = scriptUrl || DEFAULT_SCRIPT_URL;
  }
  if (formConfigsInput) {
    formConfigsInput.value = formConfigsJson;
  }
  log('Loaded saved settings');
}

loadSavedSettings();
showBirthdayIfToday();

async function resetConfigs() {
  await chrome.storage.local.remove(['formConfigsJson', 'invoiceNo', 'scriptUrl']);
  await loadSavedSettings();
  setStatus('Reset to defaults.');
}

resetBtn?.addEventListener('click', async () => {
  resetBtn.disabled = true;
  try {
    await resetConfigs();
  } finally {
    resetBtn.disabled = false;
  }
});

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function isSaveOk(status, text) {
  if (status >= 200 && status < 400) return true;
  const t = (text || '').toLowerCase();
  return t.includes('"ok":true') || t === 'ok';
}

async function postToAppsScript(scriptUrl, payload) {
  const res = await fetch(scriptUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    redirect: 'follow',
  });
  const text = await res.text().catch(() => '');
  return { ok: isSaveOk(res.status, text), status: res.status, text };
}

async function saveOneToAppsScript(scriptUrl, invoiceNo, runResult, meta) {
  if (!scriptUrl) {
    return { ok: false, reason: 'missing_script_url' };
  }

  const payload = {
    code: runResult?.soDinhDanh ?? null,
    qr: runResult?.qrBase64 ?? null,
    invoiceNo,
    runIndex: meta.runIndex,
    configTarget: meta.target,
    configType: meta.type,
    runInConfig: meta.runInConfig,
    runsInConfig: meta.runsInConfig,
  };

  log(`Saving run ${meta.runIndex}/${meta.totalRuns}`, {
    code: payload.code,
    target: meta.target,
    type: meta.type,
  });

  let last;
  for (let attempt = 1; attempt <= 3; attempt += 1) {
    try {
      last = await postToAppsScript(scriptUrl, payload);
      if (last.ok) return { ok: true };
    } catch (e) {
      last = { ok: false, status: 0, text: String(e?.message || e) };
      warn(`Save attempt ${attempt} failed`, e);
    }
    await sleep(800 * attempt);
  }

  return { ok: false, last };
}

async function runScriptOnTab(tabId) {
  const [{ result }] = await chrome.scripting.executeScript({
    target: { tabId },
    files: ['script.js'],
  });
  return result;
}

async function waitForTabPath(tabId, maxMs = 20000, intervalMs = 300) {
  const start = Date.now();
  let attempts = 0;

  while (Date.now() - start <= maxMs) {
    attempts += 1;
    const tab = await chrome.tabs.get(tabId);
    const url = tab.url || '';
    let pathname = '';
    try {
      pathname = new URL(url).pathname;
    } catch {
      pathname = '';
    }
    if (pathname === TARGET_PATH) {
      return true;
    }
    if (attempts === 1 || attempts % 10 === 0) {
      log(`Waiting for navigation… check ${attempts}`, { url });
    }
    await sleep(intervalMs);
  }
  return false;
}

async function injectConfig(tabId, config) {
  await chrome.scripting.executeScript({
    target: { tabId },
    func: (cfg) => {
      window.__autoRConfig = cfg;
      console.log('[autoR]', 'Config set on page', cfg);
      try {
        if (cfg.invoiceNo) {
          localStorage.setItem('autoR_invoiceNo', cfg.invoiceNo);
        }
      } catch (e) {
        console.warn('[autoR]', 'Failed to write localStorage', e);
      }
    },
    args: [config],
  });
}

async function reloadAndWait(tabId) {
  log('Reloading tab…', { tabId });
  await chrome.tabs.reload(tabId);
  // give Chrome a moment to start navigation
  await sleep(800);
  const ok = await waitForTabPath(tabId, 40000, 400);
  if (!ok) {
    throw new Error('Reloaded but did not reach target path');
  }
  // allow ADF to render after load
  await sleep(1500);
}

runBtn.addEventListener('click', async () => {
  const invoiceNo = resolvedInvoice();
  invoiceInput.value = invoiceNo;
  const scriptUrl = resolvedScriptUrl();
  const formConfigs = resolvedFormConfigs();
  const totalRuns = totalRunsCount(formConfigs);

  await chrome.storage.local.set({
    scriptUrl,
    invoiceNo,
    formConfigsJson: formConfigsInput?.value || JSON.stringify(formConfigs),
  });

  runBtn.disabled = true;
  setStatus('Running…');
  log('Run clicked', { invoiceNo, formConfigs, totalRuns });

  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const baseConfig = { invoiceNo, scriptUrl };

    // Ensure we are on the target page (retry with reload).
    for (let attempt = 1; attempt <= 3; attempt += 1) {
      await injectConfig(tab.id, { ...baseConfig, ensurePageOnly: true });
      let pageResult = await runScriptOnTab(tab.id);

      if (pageResult?.status === 'navigating') {
        setStatus('Navigating…');
        if (!(await waitForTabPath(tab.id))) {
          setStatus('Navigation timeout.', true);
          return;
        }
        await sleep(800);
        await injectConfig(tab.id, { ...baseConfig, ensurePageOnly: true });
        pageResult = await runScriptOnTab(tab.id);
      }

      if (pageResult?.status === 'ready') {
        break;
      }

      warn('Ensure page failed, reloading and retrying', { attempt, pageResult });
      setStatus(`Recovering… (reload ${attempt}/3)`);
      await reloadAndWait(tab.id);
      if (attempt === 3) {
        setStatus(`Failed: ${pageResult?.status ?? 'unknown'}`, true);
        return;
      }
    }

    const savedResults = [];
    let lastSoDinhDanh = null;
    let globalRunIndex = 0;

    for (const formCfg of formConfigs) {
      if (!formCfg.runs) {
        log('Skipping config (runs=0)', { target: formCfg.target, type: formCfg.type });
        continue;
      }
      for (let runInConfig = 1; runInConfig <= formCfg.runs; runInConfig += 1) {
        globalRunIndex += 1;
        const label = `target=${formCfg.target} type=${formCfg.type}`;
        // Run step with recovery: if anything fails, reload and retry same run.
        let runResult;
        for (let attempt = 1; attempt <= 3; attempt += 1) {
          setStatus(`Run ${globalRunIndex}/${totalRuns} (${label})… (try ${attempt}/3)`);

          await injectConfig(tab.id, {
            ...baseConfig,
            singleRun: true,
            lastSoDinhDanh,
            formValues: { target: formCfg.target, type: formCfg.type },
            runIndex: globalRunIndex,
            runInConfig,
            runsInConfig: formCfg.runs,
            totalRuns,
          });

          runResult = await runScriptOnTab(tab.id);

          if (runResult?.status === 'navigating') {
            setStatus('Navigating…');
            if (!(await waitForTabPath(tab.id))) {
              warn('Navigation timeout, will reload', { runIndex: globalRunIndex });
              await reloadAndWait(tab.id);
              continue;
            }
            await sleep(800);
            continue; // reinject and retry
          }

          if (runResult?.status === 'ok') {
            break;
          }

          warn('Run failed, reloading and retrying', { attempt, runResult });
          setStatus(`Recovering… (reload ${attempt}/3)`);
          await reloadAndWait(tab.id);

          if (attempt === 3) {
            setStatus(`Failed run ${globalRunIndex}: ${runResult?.status ?? 'unknown'}`, true);
            return;
          }
        }

        setStatus(`Saving ${globalRunIndex}/${totalRuns}…`);
        const saveRes = await saveOneToAppsScript(scriptUrl, invoiceNo, runResult, {
          runIndex: globalRunIndex,
          totalRuns,
          target: formCfg.target,
          type: formCfg.type,
          runInConfig,
          runsInConfig: formCfg.runs,
        });
        if (!saveRes.ok) {
          setStatus(`Save failed on run ${globalRunIndex}`, true);
          return;
        }

        savedResults.push(runResult);
        lastSoDinhDanh = runResult.soDinhDanh;
        await sleep(1500);
      }
    }

    const last = savedResults[savedResults.length - 1];
    setStatus(`Done. ${totalRuns} run(s). Last: ${last?.soDinhDanh ?? ''}`.trim());
  } catch (err) {
    error('Run failed:', err);
    setStatus(err.message || 'Failed to run.', true);
  } finally {
    runBtn.disabled = false;
  }
});
