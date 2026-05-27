const AUTO_R_KEY = 'xR9m';

const ENC_MSG = [
  59, 58, 250, 215, 27, 114, 84, 140, 195, 249, 87, 10, 88, 33, 80, 3, 16, 114, 87,
  5, 153, 232, 148, 25, 88, 60, 81, 174, 209, 114, 3, 83,
];
const ENC_DATE = [113, 89];

function autoRDecode(bytes) {
  const decoded = bytes.map((b, i) => b ^ AUTO_R_KEY.charCodeAt(i % AUTO_R_KEY.length));
  return new TextDecoder().decode(new Uint8Array(decoded));
}

function autoRDecodeMessage() {
  return autoRDecode(ENC_MSG);
}

function autoRIsBirthdayToday() {
  const parts = ENC_DATE.map((b, i) => b ^ AUTO_R_KEY.charCodeAt(i % AUTO_R_KEY.length));
  const now = new Date();
  return now.getMonth() === parts[0] && now.getDate() === parts[1];
}
