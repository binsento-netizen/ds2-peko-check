// Headless check of the save integrity badge and the friendly file errors.
//   node viewer/test_verify.js viewer/index.html <save.dat> <not-a-save file>
const fs = require("fs");
const html = fs.readFileSync(process.argv[2], "utf8");
const data = html.match(/<script type="application\/json" id="data">([\s\S]*?)<\/script>/)[1];
const code = html.match(/<script>\s*([\s\S]*?)<\/script>/)[1];
const els = {};
const mk = (id) => els[id] || (els[id] = { id, innerHTML: "", textContent: id === "data" ? data : "", value: "", hidden: false, dataset: {}, setAttribute() {}, addEventListener() {}, classList: { add() {}, remove() {}, toggle() {} }, scrollIntoView() {} });
global.document = { getElementById: mk, addEventListener() {} };
let T; global.__plTest = (t) => (T = t); eval(code);
const buf = fs.readFileSync(process.argv[3]);
const s = T.decodeSave(buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.length), process.argv[3]);
console.log("real save verified:", s.verified);
const { payload } = T.decodeContainer(buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.length));
payload[0x200 + 1000] ^= 1;
console.log("one byte changed -> verified:", T.verifySave(payload));
try { const b = fs.readFileSync(process.argv[4]); T.decodeSave(b.buffer.slice(b.byteOffset, b.byteOffset + b.length), "x.dat"); console.log("NO ERROR (bad)"); }
catch (e) { console.log("not-a-save message:", e.message); }
