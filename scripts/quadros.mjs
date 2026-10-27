// Fotografa uma composição HyperFrames em tempos exatos, sem renderizar o vídeo (storyboard, revisor, prévias).
//   node quadros.mjs <index.html> <pasta_saida> <t1,t2,...> [largura] [altura]
// Abre no Google Chrome instalado (playwright-core), espera a timeline registrada em window.__timelines, pula para
// cada tempo (seek) e salva q_<t>.png. A timeline é pausada e determinística, então o quadro é igual ao do render.
// --allow-file-access-from-files: preset com <script type="module"> (colagem, gravura, mimic) por file:// tem origem
// "null" e o Chrome bloqueia o módulo por CORS; sem a flag a timeline nunca registra e o storyboard estoura o tempo.
import { chromium } from "playwright-core";
import path from "node:path";

const [arq, saida, tempos, w = "1080", h = "1920"] = process.argv.slice(2);
const nav = await chromium.launch({ channel: "chrome", headless: true, args: ["--allow-file-access-from-files"] });
const pag = await nav.newPage({ viewport: { width: +w, height: +h }, deviceScaleFactor: 1 });
const erros = [];
pag.on("pageerror", (e) => erros.push(e.message));
pag.on("console", (m) => { if (m.type() === "error") erros.push(m.text()); });
await pag.goto("file://" + path.resolve(arq), { waitUntil: "networkidle", timeout: 60000 }).catch(() => {});
await pag.waitForFunction(() => window.__timelines && Object.keys(window.__timelines).length > 0, null, { timeout: 30000 })
  .catch(async () => {
    await nav.close();
    console.error("a composição não registrou a timeline em window.__timelines em 30 s" +
                  (erros.length ? ". Erros da página:\n- " + [...new Set(erros)].slice(0, 5).map((e) => e.slice(0, 300)).join("\n- ") : ""));
    process.exit(1);
  });
await pag.evaluate(() => document.fonts.ready);
const id = await pag.evaluate(() => (document.querySelector("[data-composition-id]") || {}).dataset?.compositionId || Object.keys(window.__timelines)[0]);
for (const t of tempos.split(",").map(Number)) {
  await pag.evaluate(([id, t]) => { const tl = window.__timelines[id] || Object.values(window.__timelines)[0]; tl.pause(); tl.seek(t, false); }, [id, t]);
  await pag.waitForTimeout(250);   // imagens e canvas assentarem
  const nome = path.join(saida, `q_${t.toFixed(2)}.png`);
  await pag.screenshot({ path: nome });
  console.log(nome);
}
await nav.close();
