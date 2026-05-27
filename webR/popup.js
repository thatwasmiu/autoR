const LOG = '[autoR]';
const log = (...args) => console.log(LOG, ...args);
const warn = (...args) => console.warn(LOG, ...args);
const error = (...args) => console.error(LOG, ...args);

const DEFAULT_INVOICE = '4601609273';

const runBtn = document.getElementById('run');
const statusEl = document.getElementById('status');
const birthdayEl = document.getElementById('birthday');
const invoiceInput = document.getElementById('invoice');

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

async function loadSavedInvoice() {
  const { invoiceNo } = await chrome.storage.local.get({
    invoiceNo: DEFAULT_INVOICE,
  });
  invoiceInput.value = invoiceNo;
  log('Loaded saved invoice:', invoiceNo);
}

loadSavedInvoice();
showBirthdayIfToday();

runBtn.addEventListener('click', async () => {
  const invoiceNo = resolvedInvoice();
  invoiceInput.value = invoiceNo;

  runBtn.disabled = true;
  setStatus('Running…');
  log('Run clicked', { invoiceNo });

  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    log('Active tab', { id: tab.id, url: tab.url });

    await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: (config) => {
        window.__autoRConfig = config;
        console.log('[autoR]', 'Config set on page', config);
      },
      args: [{ invoiceNo }],
    });
    log('Config injected');

    const [{ result }] = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      files: ['script.js'],
    });
    log('Script result:', result);

    if (result === false) {
      setStatus('Form elements not found.', true);
    } else {
      await chrome.storage.local.set({ invoiceNo });
      log('Saved invoice to storage:', invoiceNo);
      setStatus('Done.');
    }
  } catch (err) {
    error('Run failed:', err);
    setStatus(err.message || 'Failed to run.', true);
  } finally {
    runBtn.disabled = false;
  }
});
