// Gab Letra (OGraf para DaVinci Resolve): letra de música para telão, determinístico (tudo a partir do tempo em goToTime).
// Cada palavra aparece no seu tempo (campo "tempos", segundos desde o início do clipe); sem tempos, uma a cada 0,12 s.
const PADRAO = { texto: "LETRA", tempos: "", cor: "#fff6e6", corBrilho: "#ffc46b", fonte: "Playfair Display",
  tamanho: 1.1, posY: 0.76, italico: true, maiusculas: false };
const ENTRADA = 0.55, SAIDA = 0.5, ATRASO = 0.12;
const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
const saidaCubica = t => 1 - Math.pow(1 - t, 3);

class GabLetra extends HTMLElement {
  constructor() {
    super();
    this._state = { ...PADRAO }; this._initialData = {}; this._passo = 0; this._schedule = [];
    const raiz = this.attachShadow({ mode: "open" });
    const css = document.createElement("style");
    css.textContent = `
      :host { position: fixed; top: 0; left: 0; right: 0; bottom: 0; display: block; pointer-events: none; }
      .cena { position: absolute; inset: 0; opacity: 0; display: flex; align-items: center; justify-content: center; }
      .linha { position: relative; width: 78%; text-align: center; font-weight: 500; line-height: 1.12; letter-spacing: -0.005em; }
      .p { display: inline-block; margin: 0 0.13em; will-change: transform, opacity, filter; }`;
    this._cena = document.createElement("div"); this._cena.className = "cena";
    this._linha = document.createElement("div"); this._linha.className = "linha";
    this._cena.append(this._linha); raiz.append(css, this._cena); this._palavras = []; this._t = [];
  }
  async load(p) { this._rc = p.renderCharacteristics || null; this._initialData = p.data || {}; this._state = { ...PADRAO, ...this._initialData }; this._schedule = [];
    this._applyState(); this._quadro(0); return { statusCode: 200 }; }
  async dispose() { this._cena.remove(); return { statusCode: 200 }; }
  async playAction() { this._passo = 1; this._quadro(99); return { statusCode: 200, currentStep: 1 }; }
  async stopAction() { this._passo = 0; this._quadro(-SAIDA); return { statusCode: 200 }; }
  async customAction() { return { statusCode: 200 }; }
  async updateAction(params) {
    this._state = { ...this._state, ...(params.data || {}) }; this._applyState();
    if (!this._schedule.some(e => e.action?.type === "updateAction")) this._initialData = { ...this._initialData, ...(params.data || {}) };
    return { statusCode: 200 };
  }
  async setActionsSchedule(payload) { this._schedule = (payload?.schedule || []).slice().sort((a, b) => a.timestamp - b.timestamp); return { statusCode: 200 }; }
  async goToTime(payload) {
    const ts = payload?.timestamp ?? 0;
    this._state = { ...PADRAO, ...this._initialData }; this._applyState();
    let play = null, stop = null;
    for (const e of this._schedule) {
      if (e.timestamp > ts) break;
      const { type, params } = e.action;
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
    const s = this._state;
    const res = this._rc?.resolution || {}, W = res.width || window.innerWidth || 1920, H = res.height || window.innerHeight || 1080;
    this.style.setProperty("width", `${W}px`, "important"); this.style.setProperty("height", `${H}px`, "important");
    const k = (this.getBoundingClientRect().width / (this.offsetWidth || W)) || 1;
    this._k = k;
    this.style.setProperty("width", `${(W / k).toFixed(1)}px`, "important"); this.style.setProperty("height", `${(H / k).toFixed(1)}px`, "important");
    const chave = [s.texto, s.tempos, s.cor, s.corBrilho, s.fonte, s.tamanho, s.posY, s.italico, s.maiusculas, W, H, k.toFixed(4)].join("|");
    if (chave === this._chave) return; this._chave = chave;
    this._linha.style.top = `${((clamp(Number(s.posY), 0, 1) - 0.5) * 100).toFixed(2)}%`;
    this._linha.style.fontFamily = `"${s.fonte}", "Playfair Display", Georgia, serif`;
    this._linha.style.fontStyle = s.italico ? "italic" : "normal";
    this._linha.style.textTransform = s.maiusculas ? "uppercase" : "none";
    this._linha.style.fontSize = `${(100 * Number(s.tamanho) / k).toFixed(1)}px`;   // 100 px do QUADRO no tamanho 1
    this._linha.textContent = "";
    const ps = String(s.texto || "").split(/\s+/).filter(Boolean);
    const ts = String(s.tempos || "").split(",").map(x => parseFloat(x)).filter(x => !isNaN(x));
    this._t = ps.map((_, i) => ts.length === ps.length ? ts[i] : i * ATRASO);
    this._palavras = ps.map(w => { const el = document.createElement("span"); el.className = "p"; el.textContent = w;
      el.style.color = s.cor; this._linha.append(el); return el; });
  }
  _quadro(seg) {
    this._applyState();
    const s = this._state, k = this._k || 1;
    const sombra = (g) => `0 ${(3 / k).toFixed(1)}px ${(14 / k).toFixed(1)}px rgba(0,0,0,0.75), 0 0 ${(30 / k).toFixed(1)}px rgba(0,0,0,0.45), 0 0 ${((22 + 60 * g) / k).toFixed(1)}px ${s.corBrilho}${Math.round(60 + 150 * g).toString(16).padStart(2, "0")}`;
    if (this._passo === 0) {   // saída: a linha inteira desfoca e sobe um pouco
      const q = seg < 0 ? Math.min(-seg / SAIDA, 1) : 1;
      this._cena.style.opacity = String(1 - q);
      this._palavras.forEach(el => { el.style.filter = `blur(${(10 * q / k).toFixed(1)}px)`; el.style.transform = `translateY(${(-14 * q).toFixed(1)}%)`; el.style.textShadow = sombra(0); });
      return;
    }
    if (seg < 0) { this._cena.style.opacity = "0"; return; }
    this._cena.style.opacity = "1";
    this._palavras.forEach((el, i) => {   // cada palavra nasce do desfoque, no seu tempo, com um brilho que assenta
      const t = clamp((seg - this._t[i]) / ENTRADA, 0, 1), e = saidaCubica(t);
      const brilho = clamp(1 - (seg - this._t[i]) / 1.2, 0, 1) * (t > 0 ? 1 : 0);
      el.style.opacity = String(e);
      el.style.filter = `blur(${(12 * (1 - e) / k).toFixed(1)}px)`;
      el.style.transform = `translateY(${(28 * (1 - e)).toFixed(1)}%) scale(${(0.96 + 0.04 * e).toFixed(3)})`;
      el.style.textShadow = sombra(brilho);
    });
  }
}
export default GabLetra;
