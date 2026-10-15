// Gab Lettering (OGraf para DaVinci Resolve): determinístico, tudo calculado a partir do tempo (goToTime).
const PADRAO = { texto: "ESSA É A FRASE DE EFEITO", destaque: "EFEITO", cor: "#ffffff", corDestaque: "#ffb300",
  fonte: "Montserrat", tamanho: 1.0, posY: 0.5, sombra: true };
const ENTRADA = 0.9, SAIDA = 0.4, ATRASO = 0.08;
const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
const saidaCubica = t => 1 - Math.pow(1 - t, 3);
const voltaSuave = t => { const c = 1.70158; return 1 + (c + 1) * Math.pow(t - 1, 3) + c * Math.pow(t - 1, 2); };
const norm = s => (s || "").normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^\w]/g, "").toLowerCase();

class GabLettering extends HTMLElement {
  constructor() {
    super();
    this._state = { ...PADRAO }; this._initialData = {}; this._passo = 0; this._schedule = [];
    const raiz = this.attachShadow({ mode: "open" });
    const css = document.createElement("style");
    css.textContent = `
      :host { position: fixed; top: 0; left: 0; right: 0; bottom: 0; display: block; pointer-events: none; }
      .cena { position: absolute; inset: 0; opacity: 0; display: flex; align-items: center; justify-content: center; }
      .cena.dbg { outline: 12px solid red; } :host(.dbg) { outline: 12px solid lime; }
      .linha { position: relative; width: 88%; text-align: center;
               font-weight: 900; line-height: 1.02; letter-spacing: -0.01em; text-transform: uppercase; }
      .p { display: inline-block; margin: 0 0.12em; will-change: transform, opacity; }`;
    this._cena = document.createElement("div"); this._cena.className = "cena";
    this._linha = document.createElement("div"); this._linha.className = "linha";
    this._cena.append(this._linha); raiz.append(css, this._cena); this._palavras = [];
  }
  async load(p) { this._rc = p.renderCharacteristics || null; this._initialData = p.data || {}; this._state = { ...PADRAO, ...this._initialData }; this._schedule = [];
    this._applyState(); this._quadro(0); return { statusCode: 200 }; }
  async dispose() { this._cena.remove(); return { statusCode: 200 }; }
  async playAction() { this._passo = 1; this._quadro(ENTRADA); return { statusCode: 200, currentStep: 1 }; }
  async stopAction() { this._passo = 0; this._quadro(-SAIDA); return { statusCode: 200 }; }
  async customAction() { return { statusCode: 200 }; }
  async updateAction(params) {
    this._state = { ...this._state, ...(params.data || {}) }; this._applyState();
    if (!this._schedule.some(e => e.action?.type === "updateAction")) this._initialData = { ...this._initialData, ...(params.data || {}) };
    return { statusCode: 200 };
  }
  async setActionsSchedule(payload) { this._schedule = (payload?.schedule || []).slice().sort((a, b) => a.timestamp - b.timestamp); return { statusCode: 200 }; }
  async goToTime(payload) {
    const timestamp = payload?.timestamp ?? 0; const ts = timestamp;
    this._state = { ...PADRAO, ...this._initialData }; this._applyState();
    let play = null, stop = null;
    for (const event of this._schedule) { const e = event;
      if (e.timestamp > ts) break;
      const { type, params } = e.action; // replay do schedule
      if (type === "updateAction") { this._state = { ...this._state, ...(params?.data || {}) }; this._applyState(); }
      else if (type === "playAction") { play = e.timestamp; stop = null; this._passo = 1; }
      else if (type === "stopAction") { stop = e.timestamp; play = null; this._passo = 0; }
    }
    if (stop !== null) this._quadro(-Math.min((ts - stop) / 1000, SAIDA) - Number.EPSILON);
    else if (play !== null) this._quadro((ts - play) / 1000);
    else { this._passo = 1; this._quadro(ts / 1000); }
    return { statusCode: 200 };
  }
  _applyState() {
    const s = this._state, alvo = norm(s.destaque);
    // o DaVinci carrega a página com outro tamanho e só depois ajusta ao quadro: medir a tela a cada quadro, em px
    const res = this._rc?.resolution || {}, W = res.width || window.innerWidth || 1080, H = res.height || window.innerHeight || 1920;
    // o loader do DaVinci prende o elemento em 16:9 (1080x608 num quadro vertical): forçar o tamanho real do quadro
    // e ainda ENCOLHE a página (monta em 1920 de largura e reduz 0,5625 no vertical): medir a escala e compensar
    this.style.setProperty("width", `${W}px`, "important"); this.style.setProperty("height", `${H}px`, "important");
    const k = (this.getBoundingClientRect().width / (this.offsetWidth || W)) || 1;
    this._k = k;
    this.style.setProperty("width", `${(W / k).toFixed(1)}px`, "important"); this.style.setProperty("height", `${(H / k).toFixed(1)}px`, "important");
    const chave = [s.texto, s.destaque, s.cor, s.corDestaque, s.fonte, s.tamanho, s.posY, s.sombra, W, H, k.toFixed(4)].join("|");
    if (chave === this._chave) return; this._chave = chave;
    this._linha.style.top = `${((clamp(Number(s.posY), 0, 1) - 0.5) * 100).toFixed(2)}%`;
    const dbg = s.texto === "DEBUG"; this._cena.classList.toggle("dbg", dbg); this.classList.toggle("dbg", dbg);
    this._linha.style.fontFamily = `"${s.fonte}", "Montserrat", "Inter", "Helvetica Neue", Arial, sans-serif`;
    this._linha.style.fontSize = `${(100 * Number(s.tamanho) / k).toFixed(1)}px`;   // 100 px do QUADRO no tamanho 1
    this._linha.style.textShadow = s.sombra ? "0 0.04em 0.12em rgba(0,0,0,0.55)" : "none";
    this._linha.textContent = "";
    if (s.texto === "DEBUG") { const r = this.getBoundingClientRect();
      s.texto = `RC ${JSON.stringify(this._rc?.resolution||null)} DOC ${document.documentElement.clientWidth}x${document.documentElement.clientHeight} HOST ${Math.round(r.width)}x${Math.round(r.height)}`; }
    this._palavras = String(s.texto || "").split(/\s+/).filter(Boolean).map(w => {
      const el = document.createElement("span"); el.className = "p"; el.textContent = w;
      el.style.color = alvo && norm(w) === alvo ? s.corDestaque : s.cor; this._linha.append(el); return el;
    });
  }
  _quadro(seg) {
    this._applyState();   // reavalia o tamanho da tela (só refaz o DOM se algo mudou)
    if (this._passo === 0) {   // saída: tudo some junto
      const k = seg < 0 ? Math.min(-seg / SAIDA, 1) : 1;
      this._cena.style.opacity = String(1 - k);
      this._palavras.forEach(el => { el.style.transform = `translateY(${(-20 * k).toFixed(1)}%)`; });
      return;
    }
    if (seg < 0) { this._cena.style.opacity = "0"; return; }
    this._cena.style.opacity = "1";
    this._palavras.forEach((el, i) => {   // cada palavra entra de baixo, com leve "voltinha", uma depois da outra
      const t = clamp((seg - i * ATRASO) / (ENTRADA * 0.6), 0, 1);
      el.style.opacity = String(saidaCubica(t));
      el.style.transform = `translateY(${(60 * (1 - voltaSuave(t))).toFixed(1)}%) scale(${(0.92 + 0.08 * saidaCubica(t)).toFixed(3)})`;
    });
  }
}
export default GabLettering;
