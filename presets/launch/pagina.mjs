// Preset LAUNCH: print da página inteira como uma pessoa veria, rolando até o fim antes de fotografar
// (sites com animação de entrada só mostram cada seção depois de rolar até ela).
//   node pagina.mjs <url> <saida.png> <largura> <altura> [celular]
// Usa o Google Chrome instalado (playwright-core, sem baixar outro navegador).
import { chromium } from "playwright-core";

const [url, saida, w, h, cel] = process.argv.slice(2);
const UA_IPHONE = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1";
const nav = await chromium.launch({ channel: "chrome", headless: true });
const ctx = await nav.newContext({
  viewport: { width: +w, height: +h }, deviceScaleFactor: 1,
  ...(cel ? { userAgent: UA_IPHONE, isMobile: true, hasTouch: true } : {}),
});
const pag = await ctx.newPage();
await pag.goto(url, { waitUntil: "networkidle", timeout: 60000 }).catch(() => {});
await pag.waitForTimeout(1500);
// Rola devagar até o fim (dispara as animações de entrada e o carregamento preguiçoso de imagens), volta ao topo.
await pag.evaluate(async () => {
  const passo = Math.max(300, innerHeight * 0.6);
  for (let y = 0; y < document.documentElement.scrollHeight; y += passo) { scrollTo(0, y); await new Promise(r => setTimeout(r, 220)); }
  scrollTo(0, document.documentElement.scrollHeight); await new Promise(r => setTimeout(r, 900));
  scrollTo(0, 0); await new Promise(r => setTimeout(r, 600));
});
// O que ainda estiver escondido esperando a rolagem (opacity 0 em seções de entrada) aparece de vez.
await pag.addStyleTag({ content: "[data-aos],[class*=reveal],[class*=fade],[class*=animate]{opacity:1!important;transform:none!important}" }).catch(() => {});
// Print da página inteira com cabeçalho fixo/sticky ou cartas sticky empilhadas saía com o cabeçalho no meio e as
// cartas uma por cima da outra (29/10/2026): tudo volta ao fluxo normal. Seção ainda apagada à espera da rolagem
// (opacity baixa com transição, ex.: classe .rv) aparece de vez.
await pag.evaluate(() => {
  for (const el of document.querySelectorAll("body *")) {
    const c = getComputedStyle(el);
    if (c.position === "sticky") el.style.setProperty("position", "relative", "important");
    else if (c.position === "fixed" && el.getBoundingClientRect().top < 200) el.style.setProperty("position", "absolute", "important");
    if (+c.opacity < 1 && c.transitionProperty !== "none" && c.transitionDuration !== "0s") {
      el.style.setProperty("opacity", "1", "important"); el.style.setProperty("transform", "none", "important");
    }
  }
  scrollTo(0, 0);
}).catch(() => {});
await pag.waitForTimeout(500);
await pag.screenshot({ path: saida, fullPage: true });
await nav.close();
console.log("ok", saida);
