// Headless check of the viewer's decoder + compare mode against two real saves (no browser needed):
// node viewer/test_compare.js viewer/index.html <save dir> <save A> <save B>   -> prints the text report
const fs = require("fs"), path = require("path");
const html = fs.readFileSync(process.argv[2], "utf8");
const data = html.match(/<script type="application\/json" id="data">([\s\S]*?)<\/script>/)[1];
const code = html.match(/<script>\s*([\s\S]*?)<\/script>/)[1];
const els = {};
const mk = (id) => els[id] || (els[id] = { id, innerHTML: "", textContent: id === "data" ? data : "", value: "", hidden: false, dataset: {},
  setAttribute() {}, addEventListener() {}, classList: { add() {}, remove() {} }, scrollIntoView() {} });
global.document = { getElementById: mk, addEventListener() {} };
let T; global.__plTest = (t) => (T = t);
eval(code);
const dir = process.argv[3], files = process.argv.slice(4);
const saves = files.map((f) => T.decodeSave(fs.readFileSync(path.join(dir, f)).buffer, f));
saves.forEach((s) => console.log(s.name, (s.playtime / 3600).toFixed(3), "h", s.missions.length, "missions", s.sec.size, "sections"));
saves.sort((a, b) => a.playtime - b.playtime);
T.load(saves[1], saves[0]);
const d = T.diffSaves(saves[0], saves[1]);
console.log(T.changeReport());
const h = T.renderChanges();
console.log("renderChanges html bytes", h.length, "tab view len", els.view.innerHTML.length, "changes tab hidden", els["tab-changes"].hidden);
