// Prévia de um Lottie: toca no Chrome com lottie-web e salva os quadros (fNNNN.png) numa taxa fixa.
//   node previa.mjs <arquivo.json> <pasta> <fundo #hex> <fps_da_previa>
import { chromium } from "playwright-core";
import fs from "node:fs";
import path from "node:path";

const [arq, pasta, fundo = "#0B0B0D", fpsPrev = "15"] = process.argv.slice(2);
const anim = JSON.parse(fs.readFileSync(arq, "utf8"));
const nav = await chromium.launch({ channel: "chrome", headless: true });
const pag = await nav.newPage({ viewport: { width: anim.w, height: anim.h } });
await pag.setContent(`<html><body style="margin:0;background:${fundo}"><div id="a" style="width:${anim.w}px;height:${anim.h}px"></div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/lottie-web/5.12.2/lottie.min.js"></script></body></html>`, { waitUntil: "networkidle" });
await pag.evaluate(d => { window.A = lottie.loadAnimation({ container: document.getElementById("a"), renderer: "svg", loop: false, autoplay: false, animationData: d }); }, anim);
const total = anim.op - anim.ip, passo = anim.fr / +fpsPrev;
let i = 0;
for (let q = 0; q < total; q += passo) {
  await pag.evaluate(q => window.A.goToAndStop(q, true), q);
  await pag.screenshot({ path: path.join(pasta, `f${String(i++).padStart(4, "0")}.png`) });
}
for (let k = 0; k < 8; k++) await pag.screenshot({ path: path.join(pasta, `f${String(i++).padStart(4, "0")}.png`) });   // segura o fim
await nav.close();
console.log(i);
