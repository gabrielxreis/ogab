// Gab Ponte: liga o Premiere ao /ogab. O Python da skill (premiere/premiere_lib.py) abre um WebSocket em
// 127.0.0.1:8765 e manda trechos de JavaScript; este plugin roda cada trecho com a API do Premiere e devolve o
// resultado. Fica de propósito sem lógica de edição: tudo o que a skill faz vive no Python, então melhorar o Gab
// é só "git pull", sem reinstalar o plugin.
const ppro = require("premierepro");
const uxp = require("uxp");
const PORTA = 8765;

function mostrar(estado, ultimo) {
  const e = document.getElementById("estado");
  if (e) e.textContent = estado;
  if (ultimo !== undefined) {
    const u = document.getElementById("ultimo");
    if (u) u.textContent = ultimo;
  }
}

async function executar(msg) {
  const corpo = "return (async () => {\n" + msg.js + "\n})();";
  const fn = new Function("ppro", "uxp", "args", corpo);
  return await fn(ppro, uxp, msg.args || {});
}

function conectar() {
  let ws;
  try {
    ws = new WebSocket("ws://127.0.0.1:" + PORTA);
  } catch (e) {
    console.log("[Gab Ponte] WebSocket recusado: " + e);
    setTimeout(conectar, 700);
    return;
  }
  ws.onopen = () => { conectar.avisou = false; console.log("[Gab Ponte] conectado"); mostrar("conectado"); };
  ws.onmessage = async (ev) => {
    let msg;
    try { msg = JSON.parse(ev.data); } catch (e) { return; }
    mostrar("executando", msg.rotulo || "");
    try {
      const r = await executar(msg);
      ws.send(JSON.stringify({ id: msg.id, ok: true, resultado: r === undefined ? null : r }));
    } catch (e) {
      ws.send(JSON.stringify({ id: msg.id, ok: false, erro: String((e && e.stack) || e) }));
    }
    mostrar("conectado");
  };
  ws.onclose = () => { mostrar("aguardando"); setTimeout(conectar, 500); };
  ws.onerror = (e) => { if (!conectar.avisou) { console.log("[Gab Ponte] erro de conexão: " + (e && (e.message || e.type))); conectar.avisou = true; } };
}

console.log("[Gab Ponte] carregado");
conectar();
