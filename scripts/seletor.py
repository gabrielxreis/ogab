"""Seletor visual de presets: página local com o GIF de cada preset para a pessoa escolher pelas miniaturas.

  python3 seletor.py [sugestao.json] [--saida escolha_presets.json] [--formato vertical|horizontal] [--porta 0]
                     [--sem-abrir] [--timeout 1800]

- Com sugestao.json (de escolher_preset.py sugerir ... --saida): mostra o vídeo trecho a trecho com o preset que o Gab
  sugeriu; a pessoa clica num trecho e depois na miniatura para trocar (ou troca a linguagem do vídeo inteiro).
- Sem sugestão: galeria para escolher o preset do vídeo (um ou mais).
Ao clicar em "Confirmar", a escolha é gravada em --saida (padrão: ao lado da sugestão, ou na pasta temporária; antes caía na raiz da skill),
a página avisa que pode voltar ao Gab e o script termina (rodar em segundo plano: o Gab é avisado quando acabar).
Só serve arquivos de presets/ e só em 127.0.0.1.
"""
import json, os, socket, sys, tempfile, threading, time, webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote

AQUI = os.path.dirname(os.path.abspath(__file__)); SKILL = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
from escolher_preset import catalogo  # noqa: E402

TIPOS = {".gif": "image/gif", ".png": "image/png", ".jpg": "image/jpeg", ".mp4": "video/mp4", ".webp": "image/webp"}

PAGINA = r"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Seletor de presets</title><style>
:root{--bg:#0d0f14;--pn:#161a22;--pn2:#1d222c;--ln:#2a303c;--tx:#eef1f6;--mu:#9099ab;--ac:#5ee0b6;--ac2:#ffcf5c;--sel:#5ee0b622}
@media (prefers-color-scheme: light){:root:not([data-theme="dark"]){--bg:#f4f5f8;--pn:#fff;--pn2:#f0f2f6;--ln:#dde1e8;--tx:#141822;--mu:#5d6676;--ac:#0f9f78;--ac2:#b07a00;--sel:#0f9f7818}}
*{box-sizing:border-box;margin:0;padding:0}body{background:var(--bg);color:var(--tx);font:15px/1.45 -apple-system,BlinkMacSystemFont,"Inter",system-ui,sans-serif}
header{position:sticky;top:0;z-index:5;background:color-mix(in srgb,var(--bg) 88%,transparent);backdrop-filter:blur(12px);border-bottom:1px solid var(--ln);padding:14px 20px;display:flex;gap:14px;align-items:center;flex-wrap:wrap}
h1{font-size:18px;font-weight:700;letter-spacing:-.01em}header p{color:var(--mu);font-size:13px;flex:1;min-width:220px}
button{font:inherit;cursor:pointer;border-radius:10px;border:1px solid var(--ln);background:var(--pn2);color:var(--tx);padding:9px 14px}
button.pri{background:var(--ac);border-color:var(--ac);color:#06140f;font-weight:700}button:disabled{opacity:.5;cursor:default}
main{max-width:1280px;margin:0 auto;padding:18px 20px 80px}
section{margin-bottom:26px}#tGal{scroll-margin-top:80px}h2{font-size:14px;text-transform:uppercase;letter-spacing:.08em;color:var(--mu);margin-bottom:10px;font-weight:600}
.ling{display:flex;gap:14px;align-items:center;background:var(--pn);border:1px solid var(--ln);border-radius:14px;padding:12px;flex-wrap:wrap}
.ling img{width:64px;height:114px;object-fit:cover;border-radius:8px;background:#000}.ling b{font-size:17px}.ling small{display:block;color:var(--mu)}
.ling.alvo{outline:2px solid var(--ac2)}
.trechos{display:flex;flex-direction:column;gap:6px}
.tr{display:grid;grid-template-columns:34px 78px 1fr 250px;gap:12px;align-items:center;background:var(--pn);border:1px solid var(--ln);border-radius:12px;padding:8px 12px;cursor:pointer}
.tr.alvo{outline:2px solid var(--ac2);background:var(--sel)}.tr .n{color:var(--mu);font-weight:700}.tr .t{color:var(--mu);font-size:12px;font-variant-numeric:tabular-nums}
.tr .esc{display:flex;gap:8px;align-items:center}.tr .esc img{width:30px;height:52px;object-fit:cover;border-radius:5px;background:#000}
.tr .esc b{font-size:14px}.tr .esc small{display:block;color:var(--mu);font-size:12px}.tr select{margin-top:3px;font:inherit;font-size:12px;background:var(--pn2);color:var(--tx);border:1px solid var(--ln);border-radius:6px;padding:2px 4px;max-width:150px}
.mud{color:var(--ac2);font-size:11px;font-weight:700;margin-left:4px}
@media(max-width:760px){.tr{grid-template-columns:28px 1fr;}.tr .t{display:none}.tr .esc{grid-column:1/-1}}
.filtros{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px;align-items:center}.chip{padding:6px 12px;border-radius:99px;font-size:13px}
.chip.on{background:var(--tx);color:var(--bg);border-color:var(--tx)}input[type=search]{font:inherit;padding:8px 12px;border-radius:10px;border:1px solid var(--ln);background:var(--pn);color:var(--tx);min-width:200px;flex:1;max-width:320px}
.grade{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:14px}
.card{background:var(--pn);border:1px solid var(--ln);border-radius:14px;overflow:hidden;cursor:pointer;display:flex;flex-direction:column;transition:transform .15s,border-color .15s}
.card:hover{transform:translateY(-2px);border-color:var(--ac)}.card.esc{border-color:var(--ac);box-shadow:0 0 0 2px var(--ac)}.card.fora{opacity:.4}
.card .vis{aspect-ratio:9/12;background:#000;position:relative;overflow:hidden}.card .vis img{width:100%;height:100%;object-fit:cover;display:block}
.card .vis .sem{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;color:#778;font-size:13px;text-align:center;padding:10px}
.card .tag{position:absolute;left:8px;top:8px;background:var(--ac2);color:#1a1300;font-size:11px;font-weight:800;padding:3px 8px;border-radius:99px}
.card .cx{padding:10px 12px 12px}.card b{font-size:15px}.card p{color:var(--mu);font-size:12.5px;margin-top:4px}
.card .q{font-size:12px;margin-top:6px}.card .q i{color:var(--mu);font-style:normal}
.bd{display:flex;gap:5px;flex-wrap:wrap;margin-top:8px}.bd span{font-size:11px;padding:2px 7px;border-radius:6px;background:var(--pn2);color:var(--mu)}
.fim{position:fixed;inset:0;display:none;align-items:center;justify-content:center;background:color-mix(in srgb,var(--bg) 92%,transparent);z-index:9;text-align:center;padding:20px}
.fim div{max-width:420px}.fim b{font-size:22px;display:block;margin-bottom:8px}.fim p{color:var(--mu)}
.dica{color:var(--mu);font-size:13px;margin:-4px 0 10px}
.alvoTxt{background:var(--ac2);color:#1a1300;font-weight:700;font-size:13px;padding:6px 12px;border-radius:99px;max-width:420px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;cursor:pointer}
</style></head><body>
<header><h1>Seletor de presets</h1><p id="sub"></p><span id="alvoTxt" class="alvoTxt" hidden></span><button id="volta" hidden>Voltar para a sugestão</button><button class="pri" id="ok">Confirmar escolhas</button></header>
<main>
<section id="secVideo" hidden><h2>Linguagem do vídeo</h2><div class="ling" id="ling"></div>
<h2 style="margin-top:18px">Trecho a trecho</h2><p class="dica">Clique num trecho e depois numa miniatura para trocar o preset dele. Clique na linguagem para trocar o estilo do vídeo inteiro.</p><div class="trechos" id="trechos"></div></section>
<section><h2 id="tGal">Presets</h2><div class="filtros" id="filtros"></div><div class="grade" id="grade"></div></section>
</main><div class="fim" id="fim"><div><b>Escolha salva</b><p>Pode voltar para a conversa com o Gab. Ele já recebeu e segue a partir daqui.</p></div></div>
<script>
const D = __DADOS__; const P = Object.fromEntries(D.presets.map(p => [p.id, p])); const S = D.sugestao;
const $ = s => document.querySelector(s), mk = (t, c, h) => { const e = document.createElement(t); if (c) e.className = c; if (h != null) e.innerHTML = h; return e; };
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
let alvo = null, filtro = "todos", busca = "", soFormato = true, escolhidos = new Set();
let estado = S ? { linguagem: S.linguagem, trechos: S.trechos.map(t => ({...t, sug: t.preset, sugCena: t.cena})) } : null;
const gif = p => p && p.gif ? "/arquivo/" + p.gif : "";
function cenasDe(id) { return Object.keys((P[id] || {}).cenas || {}); }
function pinta() {
  $("#sub").textContent = S ? `Sugestão do Gab para o seu vídeo (${S.formato}). Troque o que quiser e confirme.` : "Escolha o preset do seu vídeo pelas miniaturas (pode marcar mais de um).";
  if (S) {
    $("#secVideo").hidden = false; $("#volta").hidden = false; const L = P[estado.linguagem] || {};
    $("#ling").className = "ling" + (alvo === "ling" ? " alvo" : "");
    $("#ling").innerHTML = `${gif(L) ? `<img src="${gif(L)}" alt="">` : ""}<div><b>${esc(L.nome || estado.linguagem)}</b>${estado.linguagem !== S.linguagem ? '<span class="mud">trocado</span>' : ""}<small>${esc(L.resumo || "")}</small><small>${S.linguagem_motivo ? "Por quê: " + esc(S.linguagem_motivo) : ""}</small></div>`;
    const box = $("#trechos"); box.innerHTML = "";
    estado.trechos.forEach((t, k) => {
      const p = P[t.preset] || {}; const r = mk("div", "tr" + (alvo === k ? " alvo" : ""));
      const tp = t.ini != null ? `${t.ini.toFixed(1)}-${t.fim.toFixed(1)} s` : "";
      const cs = cenasDe(t.preset);
      r.innerHTML = `<span class="n">${t.i}</span><span class="t">${tp}</span><span>${esc(t.texto)}</span><div class="esc">${gif(p) ? `<img src="${gif(p)}" alt="">` : ""}<div><b>${esc(p.nome || t.preset)}</b>${t.preset !== t.sug ? '<span class="mud">trocado</span>' : ""}<small>${esc(t.preset === t.sug ? (t.motivo || "") : "escolha sua")}</small>${cs.length ? `<select data-k="${k}"><option value="">o Gab escolhe a cena</option>${cs.map(c => `<option ${c === t.cena ? "selected" : ""}>${c}</option>`).join("")}</select>` : ""}</div></div>`;
      r.onclick = e => { if (e.target.tagName === "SELECT" || e.target.tagName === "OPTION") return; alvo = alvo === k ? null : k; pinta(); if (alvo != null) $("#tGal").scrollIntoView({behavior: "smooth", block: "start"}); };
      box.appendChild(r);
    });
    box.querySelectorAll("select").forEach(s => s.onchange = () => { estado.trechos[+s.dataset.k].cena = s.value; });
    $("#ling").onclick = () => { alvo = alvo === "ling" ? null : "ling"; pinta(); if (alvo) $("#tGal").scrollIntoView({behavior: "smooth", block: "start"}); };
    const at = $("#alvoTxt"); at.hidden = alvo == null; at.textContent = alvo === "ling" ? "Escolhendo: linguagem do vídeo (clique para cancelar)" : alvo != null ? `Escolhendo trecho ${estado.trechos[alvo].i}: ${estado.trechos[alvo].texto}` : ""; at.onclick = () => { alvo = null; pinta(); };
    $("#tGal").textContent = alvo === "ling" ? "Escolha a nova linguagem do vídeo" : alvo != null ? `Escolha o preset do trecho ${estado.trechos[alvo].i}` : "Presets";
  }
  galeria();
}
function galeria() {
  const f = $("#filtros"); f.innerHTML = "";
  [["todos", "Todos"], ...Object.entries(D.categorias)].forEach(([k, n]) => { const b = mk("button", "chip" + (filtro === k ? " on" : ""), esc(n)); b.onclick = () => { filtro = k; galeria(); }; f.appendChild(b); });
  const q = mk("input"); q.type = "search"; q.placeholder = "Buscar (ex.: número, bíblia, app)"; q.value = busca; q.oninput = () => { busca = q.value; desenha(); }; f.appendChild(q);
  const fb = mk("button", "chip" + (soFormato ? " on" : ""), "Só " + D.formato); fb.onclick = () => { soFormato = !soFormato; galeria(); }; f.appendChild(fb);
  desenha();
}
const semAc = s => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
function desenha() {
  const g = $("#grade"); g.innerHTML = ""; const b = semAc(busca);
  const sugeridos = new Set(S ? [S.linguagem, ...S.trechos.map(t => t.sug)] : []);
  D.presets.forEach(p => {
    if (filtro !== "todos" && p.categoria !== filtro) return;
    if (b && !semAc([p.nome, p.resumo, p.quando, ...(p.sinais || []), ...(p.nichos || [])].join(" ")).includes(b)) return;
    const fora = !p.formato.includes(D.formato); if (fora && soFormato) return;
    const atual = S ? (alvo === "ling" ? estado.linguagem === p.id : alvo != null ? estado.trechos[alvo].preset === p.id : false) : escolhidos.has(p.id);
    const c = mk("div", "card" + (atual ? " esc" : "") + (fora ? " fora" : ""));
    c.innerHTML = `<div class="vis">${p.gif ? `<img loading="lazy" src="${gif(p)}" alt="Prévia ${esc(p.nome)}">` : `<div class="sem">sem prévia ainda</div>`}${sugeridos.has(p.id) ? '<span class="tag">sugerido</span>' : ""}</div>
      <div class="cx"><b>${esc(p.nome)}</b><p>${esc(p.resumo)}</p><div class="q"><i>Quando:</i> ${esc(p.quando)}</div>
      <div class="bd"><span>${p.formato.join(" / ")}</span><span>${{precisa: "com apresentador", sem: "sem apresentador", tanto_faz: "com ou sem pessoa"}[p.apresentador]}</span><span>${{linguagem: "vídeo inteiro", trecho: "trecho", abertura: "abertura", entrega: "para site/app"}[p.papel] || p.papel}</span>${fora ? `<span>não é ${D.formato}</span>` : ""}</div></div>`;
    c.onclick = () => escolher(p.id); g.appendChild(c);
  });
  if (!g.children.length) g.innerHTML = '<p style="color:var(--mu)">Nada com esse filtro.</p>';
}
function escolher(id) {
  if (!S) { escolhidos.has(id) ? escolhidos.delete(id) : escolhidos.add(id); desenha(); return; }
  if (alvo === "ling") { const velho = estado.linguagem; estado.linguagem = id; estado.trechos.forEach(t => { if (t.preset === velho) { t.preset = id; t.cena = ""; } }); alvo = null; }
  else if (alvo != null) { const t = estado.trechos[alvo]; if (t.preset !== id) { t.preset = id; t.cena = id === t.sug ? t.sugCena : ""; } alvo = alvo + 1 < estado.trechos.length ? alvo + 1 : null; }
  else { alvo = "ling"; pinta(); window.scrollTo({top: 0, behavior: "smooth"}); return escolher(id); }
  pinta();
}
$("#volta").onclick = () => { estado = { linguagem: S.linguagem, trechos: S.trechos.map(t => ({...t, sug: t.preset, sugCena: t.cena})) }; alvo = null; pinta(); };
$("#ok").onclick = async () => {
  const corpo = S ? { modo: "trechos", linguagem: estado.linguagem, mudou_linguagem: estado.linguagem !== S.linguagem,
      trechos: estado.trechos.map(t => ({ i: t.i, ini: t.ini, fim: t.fim, texto: t.texto, preset: t.preset, cena: t.cena, sugerido: t.sug, trocado: t.preset !== t.sug })) }
    : { modo: "video", presets: [...escolhidos] };
  if (!S && !escolhidos.size) { alert("Marque pelo menos um preset."); return; }
  $("#ok").disabled = true;
  try { const r = await fetch("/escolha", { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(corpo) }); if (!r.ok) throw 0; $("#fim").style.display = "flex"; }
  catch (e) { $("#ok").disabled = false; alert("Não consegui salvar. O Gab ainda está com o seletor aberto?"); }
};
pinta();
</script></body></html>"""


def porta_livre(p):
    if p:
        return p
    s = socket.socket(); s.bind(("127.0.0.1", 0)); n = s.getsockname()[1]; s.close(); return n


def main(a):
    if a and a[0] in ("-h", "--help"):
        raise SystemExit(__doc__)
    def arg(k, d=None):
        return a[a.index(k) + 1] if k in a else d
    sug_arq = a[0] if a and not a[0].startswith("--") else None
    sug = json.load(open(sug_arq, encoding="utf-8")) if sug_arq else None
    formato = arg("--formato", (sug or {}).get("formato", "vertical"))
    saida = os.path.abspath(arg("--saida", os.path.join(os.path.dirname(os.path.abspath(sug_arq)) if sug_arq else tempfile.gettempdir(), "escolha_presets.json")))
    C = catalogo()
    dados = {"presets": C["presets"], "categorias": C["categorias"], "formato": formato, "sugestao": sug}
    html = PAGINA.replace("__DADOS__", json.dumps(dados, ensure_ascii=False).replace("</", "<\\/")).encode("utf-8")
    pronto = threading.Event()

    class H(BaseHTTPRequestHandler):
        def log_message(self, *x):
            pass

        def _envia(self, cod, corpo, tipo):
            self.send_response(cod); self.send_header("Content-Type", tipo); self.send_header("Content-Length", str(len(corpo)))
            self.send_header("Cache-Control", "no-store"); self.end_headers(); self.wfile.write(corpo)

        def do_GET(self):
            if self.path in ("/", "/index.html"):
                return self._envia(200, html, "text/html; charset=utf-8")
            if self.path.startswith("/arquivo/"):
                rel = unquote(self.path[len("/arquivo/"):].split("?")[0])
                arq = os.path.realpath(os.path.join(SKILL, rel)); base = os.path.realpath(os.path.join(SKILL, "presets"))
                ext = os.path.splitext(arq)[1].lower()
                if arq.startswith(base + os.sep) and ext in TIPOS and os.path.isfile(arq):
                    return self._envia(200, open(arq, "rb").read(), TIPOS[ext])
            self._envia(404, b"nao achei", "text/plain")

        def do_POST(self):
            if self.path != "/escolha":
                return self._envia(404, b"", "text/plain")
            try:
                d = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            except Exception:
                return self._envia(400, b"json invalido", "text/plain")
            d["salvo_em"] = time.strftime("%Y-%m-%d %H:%M")
            json.dump(d, open(saida, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            self._envia(200, b"ok", "text/plain"); pronto.set()

    porta = porta_livre(int(arg("--porta", 0)))
    srv = ThreadingHTTPServer(("127.0.0.1", porta), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{porta}/"
    print(f"seletor aberto: {url}\nesperando a escolha (salva em {saida})", flush=True)
    if "--sem-abrir" not in a:
        webbrowser.open(url)
    ok = pronto.wait(float(arg("--timeout", 1800)))
    time.sleep(.4); srv.shutdown()
    if not ok:
        raise SystemExit("tempo esgotado sem escolha")
    d = json.load(open(saida, encoding="utf-8"))
    nomes = {p["id"]: p["nome"] for p in C["presets"]}
    if d["modo"] == "video":
        print("escolhidos: " + ", ".join(nomes.get(x, x) for x in d["presets"]))
    else:
        print(f"linguagem: {nomes.get(d['linguagem'], d['linguagem'])}" + (" (trocada pela pessoa)" if d.get("mudou_linguagem") else ""))
        for t in d["trechos"]:
            print(f"  {t['i']}. {nomes.get(t['preset'], t['preset'])}{(' / ' + t['cena']) if t.get('cena') else ''}{'  <- trocado' if t.get('trocado') else ''}  | {t['texto'][:60]}")
    print(f"salvo: {saida}")


if __name__ == "__main__":
    main(sys.argv[1:])
