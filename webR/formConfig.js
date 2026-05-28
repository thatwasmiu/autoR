/** Default form configs: target (soc1), type (soc2), runs */
const AUTO_R_DEFAULT_FORM_CONFIGS = [
  { target: '0', type: '0', runs: 10 },
  { target: '0', type: '1', runs: 10 },
  { target: '0', type: '2', runs: 10 },
];

function parseFormConfigsJson(text) {
  const parsed = JSON.parse(text);
  if (!Array.isArray(parsed) || parsed.length === 0) {
    throw new Error('Config must be a non-empty array');
  }
  return parsed.map((row, i) => {
    const target = String(row.target ?? '0');
    const type = String(row.type ?? '0');
    // Allow runs=0 to mean "skip this config entry"
    const runsRaw = Number(row.runs);
    const runs = Math.max(0, Math.min(50, Number.isFinite(runsRaw) ? runsRaw : 1));
    return { target, type, runs, _index: i };
  });
}
