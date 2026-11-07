/**
 * Hermes (the Android RN runtime) provides no WebCrypto, so
 * crypto.randomUUID() crashes on-device. Request/message IDs are
 * correlation IDs (backend stores x-request-id as String(100), audit.py),
 * not secrets, so Math.random-based generation with RFC v4 formatting is
 * sufficient. If a cryptographic ID ever becomes necessary, use
 * expo-crypto instead of re-enabling this.
 */

const HEX = '0123456789abcdef';

/** UUID v4-formatted ID. NOT cryptographically random. */
export function makeId(): string {
  let out = '';
  for (let i = 0; i < 36; i++) {
    if (i === 8 || i === 13 || i === 18 || i === 23) {
      out += '-';
    } else if (i === 14) {
      out += '4';
    } else if (i === 19) {
      out += HEX[8 + Math.floor(Math.random() * 4)];
    } else {
      out += HEX[Math.floor(Math.random() * 16)];
    }
  }
  return out;
}
