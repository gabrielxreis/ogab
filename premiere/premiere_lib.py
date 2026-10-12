"""Funções para montar o vídeo no Adobe Premiere Pro (2026+) pela API UXP, no lugar do resolve_lib.py.

Como funciona: o plugin "Gab Ponte" (premiere/plugin, instalado pelo premiere/instalar) fica aberto no Premiere e
se conecta a este módulo por WebSocket (127.0.0.1:8765). Cada função manda um trecho de JavaScript que roda na API
do Premiere (require("premierepro")) e devolve JSON. Sem dependência extra: o WebSocket é da biblioteca padrão.

Uso típico (mesma ordem do fluxo do DaVinci):
    import premiere_lib as P
    P.abrir_projeto("~/Desktop/Empresa/Assunto - Empresa/Assunto - Empresa.prproj")   # cria se não existir
    s = P.criar_sequencia("Reels 60s", ".../gravacao/bruto.mov", 1080, 1920, 30)
    P.transcrever(".../gravacao/bruto.mov", ".../legendas/transcricao.json")          # Speech to Text do Premiere
    P.colocar(s, ".../narracoes/narracao.wav", 0, video=None, audio=0, db=5)
    P.colocar_musica(s, ".../musica/faixa.wav", inicio_faixa=64.0, dur=48.4, db=-10)
    P.montar_takes(s, [(".../brolls/take_01.mp4", 0.0), (".../brolls/take_02.mp4", 5.1)], fim=48.4, trilha=1)
    P.aplicar_lut([".../brolls/take_01.mp4"], "LUT DO GAB")
    P.lettering(s, "Cinematic", "TEXTO DO GANCHO", inicio=0.0, dur=2.5, trilha=3)
    P.exportar(s, ".../videos/Assunto - Empresa.mp4")
Trilhas: índice 0 = V1/A1 (a API do Premiere conta do zero).
"""
import base64, hashlib, json, os, socket, struct, sys, time

PORTA = int(os.environ.get("OGAB_PREMIERE_PORTA", "8765"))
AQUI = os.path.dirname(os.path.abspath(__file__))
PASTAS = ["Timelines", "Footages", "BRoll", "SFX", "Musicas", "Motions", "Legendas"]

# ---------------------------------------------------------------- WebSocket mínimo (servidor, 1 cliente)

class _Ponte:
    def __init__(self, espera=60):
        self.srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.srv.bind(("127.0.0.1", PORTA)); self.srv.listen(1); self.srv.settimeout(espera)
        try:
            self.c, _ = self.srv.accept()
        except socket.timeout:
            self.srv.close()
            raise SystemExit("O Premiere não conectou. Abra o Premiere com o painel Window > UXP Plugins > Gab Ponte "
                             "(ele mostra 'conectado' quando o Gab fala com ele).")
        self.c.settimeout(None)
        req = b""
        while b"\r\n\r\n" not in req:
            req += self.c.recv(4096)
        chave = [l.split(b":", 1)[1].strip() for l in req.split(b"\r\n") if l.lower().startswith(b"sec-websocket-key")][0]
        aceite = base64.b64encode(hashlib.sha1(chave + b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11").digest())
        self.c.sendall(b"HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                       b"Sec-WebSocket-Accept: " + aceite + b"\r\n\r\n")
        self.n = 0

    def _ler(self, n):
        b = b""
        while len(b) < n:
            p = self.c.recv(n - len(b))
            if not p:
                raise SystemExit("O Premiere fechou a conexão (painel Gab Ponte fechado ou Premiere travou).")
            b += p
        return b

    def _quadro(self):
        msg, op0 = b"", None
        while True:
            b1, b2 = self._ler(2)
            fim, op = b1 & 0x80, b1 & 0x0F
            n = b2 & 0x7F
            if n == 126: n = struct.unpack(">H", self._ler(2))[0]
            elif n == 127: n = struct.unpack(">Q", self._ler(8))[0]
            masc = self._ler(4) if b2 & 0x80 else None
            dados = self._ler(n)
            if masc:
                dados = bytes(x ^ masc[i % 4] for i, x in enumerate(dados))
            if op == 9:      # ping -> pong
                self._enviar(dados, 10); continue
            if op == 8:
                raise SystemExit("O Premiere fechou a conexão.")
            if op in (1, 2): op0 = op
            msg += dados
            if fim:
                return msg.decode("utf-8")

    def _enviar(self, dados, op=1):
        n = len(dados)
        cab = bytes([0x80 | op])
        cab += bytes([n]) if n < 126 else (bytes([126]) + struct.pack(">H", n) if n < 65536 else bytes([127]) + struct.pack(">Q", n))
        self.c.sendall(cab + dados)

    def rodar(self, js, args=None, rotulo=""):
        self.n += 1
        self._enviar(json.dumps({"id": self.n, "js": js, "args": args or {}, "rotulo": rotulo}).encode("utf-8"))
        r = json.loads(self._quadro())
        if not r.get("ok"):
            raise RuntimeError(f"Premiere ({rotulo or 'js'}): {r.get('erro')}")
        return r.get("resultado")

    def fechar(self):
        try:
            self._enviar(b"", 8); self.c.close()
        finally:
            self.srv.close()


_ponte = None

def conectar(espera=60):
    """Espera o painel Gab Ponte conectar (ele tenta a cada 0,5 s). Uma conexão por processo Python."""
    global _ponte
    if _ponte is None:
        _ponte = _Ponte(espera)
        import atexit; atexit.register(_ponte.fechar)
    return _ponte


# Funções auxiliares que vão junto em todo trecho de JS (o plugin não guarda lógica nenhuma).
_PRELUDIO = r"""
const P = ppro;
const tt = (s) => P.TickTime.createWithSeconds(Number(s));
const proj = async () => { const p = await P.Project.getActiveProject(); if (!p) throw new Error("nenhum projeto aberto no Premiere"); return p; };
const tx = async (p, rotulo, fazer) => { let ok = false; p.lockedAccess(() => { ok = p.executeTransaction((c) => { for (const a of fazer()) if (a) c.addAction(a); }, rotulo); }); return ok; };
const norm = (s) => String(s || "").replace(/\\/g, "/").toLowerCase();
async function itens(pasta, saida = []) {
  for (const it of await pasta.getItems()) {
    if (P.ClipProjectItem.cast(it)) { saida.push(it); continue; }
    const f = P.FolderItem.cast(it); if (f) await itens(f, saida);
  }
  return saida;
}
async function itemPorCaminho(p, caminho) {
  const alvo = norm(caminho);
  for (const it of await itens(await p.getRootItem())) {
    const c = P.ClipProjectItem.cast(it);
    try { if (c && norm(await c.getMediaFilePath()) === alvo) return c; } catch (e) {}
  }
  return null;
}
async function binFilho(raiz, nome) {
  for (const it of await raiz.getItems()) if (it.name === nome && !P.ClipProjectItem.cast(it)) { const f = P.FolderItem.cast(it); if (f) return f; }
  return null;
}
async function bin(p, nome) {
  const raiz = await p.getRootItem();
  if (!nome) return raiz;
  let b = await binFilho(raiz, nome);
  if (!b) { await tx(p, "Gab: bin " + nome, () => [raiz.createBinAction(nome, false)]); b = await binFilho(raiz, nome); }
  return b || raiz;
}
const CLIPE = (P.Constants.TrackItemType && P.Constants.TrackItemType.CLIP !== undefined) ? P.Constants.TrackItemType.CLIP : 1;
async function seqPorNome(p, nome) {
  if (!nome) return await p.getActiveSequence();
  for (const s of await p.getSequences()) if (s.name === nome) return s;
  throw new Error("sequência não encontrada: " + nome);
}
async function importar(p, arquivos, nomeBin) {
  const faltam = [];
  for (const a of arquivos) if (!(await itemPorCaminho(p, a))) faltam.push(a);
  if (faltam.length) await p.importFiles(faltam, true, await bin(p, nomeBin), false);
  const r = [];
  for (const a of arquivos) { const it = await itemPorCaminho(p, a); if (!it) throw new Error("não importou: " + a); r.push(it); }
  return r;
}
"""


def js(codigo, rotulo="", **args):
    """Roda um trecho de JS no Premiere (com o prelúdio) e devolve o resultado. args chega como `args` no JS."""
    return conectar().rodar(_PRELUDIO + "\n" + codigo, args, rotulo)


def _abs(c):
    return os.path.abspath(os.path.expanduser(c))


def _bin_de(caminho):
    ext = os.path.splitext(caminho)[1].lower()
    pasta = os.path.basename(os.path.dirname(caminho)).lower()
    if pasta.startswith("broll"): return "BRoll"
    if pasta.startswith("sfx"): return "SFX"
    if pasta.startswith("musica"): return "Musicas"
    if pasta.startswith("motion"): return "Motions"
    if pasta.startswith("legenda") or ext == ".srt": return "Legendas"
    return "Footages"


# ---------------------------------------------------------------- projeto e sequência

def versao():
    return js("return await P.Application.version;", "versão")


def abrir_projeto(caminho=None):
    """Usa o projeto aberto (caminho=None) ou abre/cria o .prproj. Cria a árvore de bins (regra 1b) e salva."""
    if caminho:
        caminho = _abs(caminho)
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
    return js("""
      let p = await P.Project.getActiveProject();
      const c = args.caminho;
      if (c && (!p || norm(p.path) !== norm(c))) {
        p = P.Project.isProject(c) ? await P.Project.open(c) : await P.Project.createProject(c);
      }
      if (!p) throw new Error("abra ou crie um projeto no Premiere");
      for (const n of args.pastas) await bin(p, n);
      await p.save();
      return { nome: p.name, caminho: p.path };
    """, "abrir projeto", caminho=caminho, pastas=PASTAS)


def criar_sequencia(nome, midia_base, w=1080, h=1920, fps=30):
    """Cria a sequência a partir da gravação (herda áudio e cor) e força o quadro w x h e o fps do vídeo."""
    return js("""
      const p = await proj();
      for (const s of await p.getSequences()) if (s.name === args.nome) { await p.setActiveSequence(s); return s.name; }
      const [base] = await importar(p, [args.midia], "Footages");
      const s = await p.createSequenceFromMedia(args.nome, [base], await bin(p, "Timelines"));
      const st = await s.getSettings();
      const r = await st.getVideoFrameRect(); r.width = args.w; r.height = args.h;
      await st.setVideoFrameRect(r);
      st.setVideoFrameRate(P.FrameRate.createWithValue(args.fps));
      await tx(p, "Gab: ajustes da sequência", () => [s.createSetSettingsAction(st)]);
      await p.setActiveSequence(s); await p.save();
      return s.name;
    """, "criar sequência", nome=nome, midia=_abs(midia_base), w=w, h=h, fps=fps)


def sequencias():
    return js("const p = await proj(); return (await p.getSequences()).map(s => s.name);", "sequências")


def salvar():
    return js("return await (await proj()).save();", "salvar")


# ---------------------------------------------------------------- colocar mídia

_JS_COLOCAR = """
  const p = await proj(); const s = await seqPorNome(p, args.seq);
  const ed = P.SequenceEditor.getEditor(s);
  const saida = [];
  for (const c of args.clipes) {
    const [it] = await importar(p, [c.arquivo], c.bin);
    if (c.de !== null || c.ate !== null) {
      const a = c.de !== null ? tt(c.de) : P.TickTime.TIME_ZERO;
      const b = c.ate !== null ? tt(c.ate) : await it.getOutPoint(P.Constants.MediaType.ANY);
      await tx(p, "Gab: in/out", () => [it.createSetInOutPointsAction(a, b)]);
    }
    const v = c.video === null ? -1 : c.video, au = c.audio === null ? -1 : c.audio;
    await tx(p, "Gab: colocar " + it.name, () => [ed.createOverwriteItemAction(it, tt(c.tempo), v, au)]);
    if (c.de !== null || c.ate !== null) await tx(p, "Gab: limpa in/out", () => [it.createClearInOutPointsAction()]);
    saida.push(it.name);
  }
  return saida;
"""


def colocar(seq, arquivo, tempo, video=0, audio=0, de=None, ate=None, db=None, fade_in=0, fade_out=0):
    """Overwrite do arquivo em `tempo` (s). video/audio = índice da trilha (0 = V1/A1) ou None para não usar.
    de/ate cortam a fonte (s). db/fades ajustam o volume do clipe de áudio colocado."""
    arquivo = _abs(arquivo)
    r = js(_JS_COLOCAR, "colocar", seq=seq, clipes=[dict(arquivo=arquivo, tempo=tempo, video=video, audio=audio,
                                                           de=de, ate=ate, bin=_bin_de(arquivo))])
    if audio is not None and (db is not None or fade_in or fade_out):
        volume(seq, audio, tempo, db or 0, fade_in, fade_out)
    return r


def volume(seq, trilha_audio, tempo, db=0.0, fade_in=0.0, fade_out=0.0):
    """Volume do clipe de áudio que começa em `tempo` na trilha (0 = A1): nível em dB e fades por keyframe.
    O parâmetro Level do Premiere é linear (1.0 = 0 dB), por isso a conversão 10^(dB/20)."""
    return js("""
      const p = await proj(); const s = await seqPorNome(p, args.seq);
      const tr = await s.getAudioTrack(args.trilha);
      let alvo = null;
      for (const it of tr.getTrackItems(CLIPE, false))
        if (Math.abs((await it.getStartTime()).seconds - args.tempo) < 0.05) alvo = it;
      if (!alvo) throw new Error("clipe de áudio não encontrado em " + args.tempo + " s");
      const cadeia = await alvo.getComponentChain();
      let nivel = null;
      for (let i = 0; i < cadeia.getComponentCount(); i++) {
        const comp = cadeia.getComponentAtIndex(i);
        if ((await comp.getMatchName()).toLowerCase().includes("volume")) {
          for (let j = 0; j < comp.getParamCount(); j++) { const pr = comp.getParam(j); if (/level|nível|nivel/i.test(pr.displayName)) nivel = pr; }
        }
      }
      if (!nivel) throw new Error("parâmetro Level do Volume não encontrado");
      const lin = Math.pow(10, args.db / 20);
      const ini = (await alvo.getStartTime()).seconds, fim = (await alvo.getEndTime()).seconds;
      const acoes = [];
      if (args.fade_in || args.fade_out) {
        acoes.push(nivel.createSetTimeVaryingAction(true));
        const k = (t, v) => { const kf = nivel.createKeyframe(v); kf.position = tt(t); return nivel.createAddKeyframeAction(kf); };
        if (args.fade_in) { acoes.push(k(0, 0)); acoes.push(k(args.fade_in, lin)); } else acoes.push(k(0, lin));
        if (args.fade_out) { acoes.push(k(fim - ini - args.fade_out, lin)); acoes.push(k(fim - ini, 0)); }
      } else {
        acoes.push(nivel.createSetValueAction(nivel.createKeyframe(lin), true));
      }
      await tx(p, "Gab: volume", () => acoes);
      return { db: args.db, linear: lin };
    """, "volume", seq=seq, trilha=trilha_audio, tempo=tempo, db=db, fade_in=fade_in, fade_out=fade_out)


def colocar_narracao(seq, wav, db=0.0, tempo=0.0, trilha=0):
    return colocar(seq, wav, tempo, video=None, audio=trilha, db=db)


def colocar_musica(seq, wav, inicio_faixa=0.0, dur=None, db=-10.0, trilha=1, fade_in=0.5, fade_out=2.5):
    """Música bruta (regra do usuário): o WAV original, com ponto de entrada no trecho e fades no próprio clipe.
    Para o clímax cair no CTA: inicio_faixa = hookStartSeconds - tempo_do_CTA."""
    ate = None if dur is None else inicio_faixa + dur
    return colocar(seq, wav, 0.0, video=None, audio=trilha, de=inicio_faixa, ate=ate, db=db,
                   fade_in=fade_in, fade_out=fade_out)


def montar_takes(seq, takes, fim=None, trilha=1, com_audio=False):
    """takes = [(arquivo, tempo_inicio), ...]; cada take vai até o início do próximo (o último até `fim`).
    trilha 1 = V2 (b-roll acima da V1, que é intocável)."""
    clipes = []
    for i, (arq, t0) in enumerate(takes):
        t1 = takes[i + 1][1] if i + 1 < len(takes) else fim
        arq = _abs(arq)
        clipes.append(dict(arquivo=arq, tempo=t0, video=trilha, audio=(trilha if com_audio else None),
                           de=0.0, ate=(None if t1 is None else t1 - t0), bin=_bin_de(arq)))
    return js(_JS_COLOCAR, "montar takes", seq=seq, clipes=clipes)


# ---------------------------------------------------------------- transcrição (Speech to Text do Premiere)

def transcrever(arquivo, saida, idioma="pt-br"):
    """Transcreve com o próprio Premiere e salva no formato da skill (segundos, como o motor whisper do
    transcrever.py): {"motor": "premiere", "language", "segments": [{start, end, text, words: [{text, start, end}]}]}."""
    arquivo = _abs(arquivo)
    bruto = js("""
      const p = await proj();
      const [it] = await importar(p, [args.arquivo], "Footages");
      if (!P.Transcript.hasTranscript(it)) {
        const ok = await P.Transcript.transcribeClipProjectItem(it, { languageCode: args.idioma });
        if (!ok) throw new Error("o Premiere não transcreveu (pacote de idioma " + args.idioma + " instalado?)");
      }
      for (let i = 0; i < 600 && !P.Transcript.hasTranscript(it); i++) await new Promise(r => setTimeout(r, 1000));
      return await P.Transcript.exportToJSON(it);
    """, "transcrever", arquivo=arquivo, idioma=idioma)
    tr = json.loads(bruto) if isinstance(bruto, str) else bruto
    segs = []
    for s in tr.get("segments", []):
        ws = []
        for w in s.get("words", []):
            txt = w.get("text", "").strip()
            if not txt:
                continue
            if w.get("type") == "punctuation":   # pontuação vem separada: cola na palavra anterior
                if ws:
                    ws[-1]["text"] += txt
                continue
            ws.append({"text": txt, "start": round(w["start"], 3), "end": round(w["start"] + w["duration"], 3)})
        if ws:
            segs.append({"start": ws[0]["start"], "end": ws[-1]["end"], "text": " ".join(w["text"] for w in ws), "words": ws})
    r = {"motor": "premiere", "language": tr.get("language", idioma), "segments": segs}
    os.makedirs(os.path.dirname(_abs(saida)), exist_ok=True)
    json.dump(r, open(_abs(saida), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{saida}: {len(segs)} trechos, {sum(len(s['words']) for s in segs)} palavras (premiere)")
    return r


# ---------------------------------------------------------------- legenda, cor, lettering, áudio

def importar_legenda(seq, srt):
    """Importa o .srt no bin Legendas e tenta colocar na trilha de legenda da sequência. Se a API não aceitar
    (depende da versão), o arquivo fica no bin e o usuário arrasta para a timeline (1 movimento)."""
    srt = _abs(srt)
    return js("""
      const p = await proj(); const s = await seqPorNome(p, args.seq);
      const [it] = await importar(p, [args.srt], "Legendas");
      try {
        const ed = P.SequenceEditor.getEditor(s);
        const ok = await tx(p, "Gab: legenda", () => [ed.createOverwriteItemAction(it, P.TickTime.TIME_ZERO, -1, -1)]);
        return { no_bin: it.name, na_timeline: ok, trilhas_legenda: await s.getCaptionTrackCount() };
      } catch (e) { return { no_bin: it.name, na_timeline: false, erro: String(e) }; }
    """, "legenda", seq=seq, srt=srt)


def luts_instalados():
    """Pastas de LUT do Premiere (Technical = Input LUT, Creative = Look) com os .cube instalados."""
    if sys.platform == "darwin":
        bases = [os.path.expanduser("~/Library/Application Support/Adobe/Common/LUTs"), "/Library/Application Support/Adobe/Common/LUTs"]
    else:
        bases = [os.path.join(os.environ.get("APPDATA", ""), "Adobe", "Common", "LUTs"),
                 os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "Adobe", "Common", "LUTs")]
    achados = {}
    for b in bases:
        for raiz, _, arqs in os.walk(b):
            for a in arqs:
                if a.lower().endswith(".cube"):
                    achados.setdefault(os.path.splitext(a)[0], os.path.join(raiz, a))
    return achados


def aplicar_lut(arquivos, lut="LUT DO GAB"):
    """Aplica o LUT como Input LUT de cada clipe no projeto (todas as instâncias na timeline recebem). Equivale ao
    PowerGrade do DaVinci (regra 7b). Confere lendo de volta; devolve o que ficou com o LUT."""
    caminho = luts_instalados().get(lut, lut)
    return js("""
      const p = await proj(); const r = {};
      for (const a of args.arquivos) {
        const it = await itemPorCaminho(p, a);
        if (!it) { r[a] = "não está no projeto"; continue; }
        for (const id of [args.lut, args.caminho]) {
          await tx(p, "Gab: LUT", () => [it.createSetInputLUTIDAction(id)]);
          const atual = await it.getInputLUTID();
          if (atual) { r[a] = atual; break; }
        }
        if (!r[a]) r[a] = "não aplicou";
      }
      return r;
    """, "LUT", arquivos=[_abs(a) for a in arquivos], lut=lut, caminho=caminho)


def mogrts():
    """MOGRTs de lettering instalados (pasta de templates do Premiere)."""
    pasta = js("return await P.SequenceEditor.getInstalledMogrtPath();", "mogrts")
    lst = []
    for raiz, _, arqs in os.walk(pasta or ""):
        lst += [os.path.join(raiz, a) for a in arqs if a.lower().endswith(".mogrt")]
    return lst


def lettering(seq, mogrt, texto, inicio, dur, trilha=2):
    """Insere um MOGRT de lettering (nome ou caminho do .mogrt) e troca o texto do 1º parâmetro de texto.
    Devolve os parâmetros do template para conferir. trilha 2 = V3."""
    if not os.path.isfile(mogrt):
        cands = [m for m in mogrts() if mogrt.lower() in os.path.basename(m).lower()]
        if not cands:
            raise SystemExit(f"MOGRT '{mogrt}' não instalado (rode premiere/instalar de novo).")
        mogrt = cands[0]
    return js("""
      const p = await proj(); const s = await seqPorNome(p, args.seq);
      const ed = P.SequenceEditor.getEditor(s);
      let itens = [];
      p.lockedAccess(() => { itens = ed.insertMogrtFromPath(args.mogrt, tt(args.inicio), args.trilha, -1); });
      const v = itens.find(i => i.getComponentChain && i.createSetEndAction);
      if (!v) throw new Error("o Premiere não inseriu o MOGRT");
      await tx(p, "Gab: duração do lettering", () => [v.createSetEndAction(tt(args.inicio + args.dur))]);
      const cadeia = await v.getComponentChain(); const params = []; let trocado = false;
      for (let i = 0; i < cadeia.getComponentCount(); i++) {
        const comp = cadeia.getComponentAtIndex(i);
        for (let j = 0; j < comp.getParamCount(); j++) {
          const pr = comp.getParam(j); let val = null;
          try { val = (await pr.getStartValue()).value.value; } catch (e) {}
          params.push([await comp.getDisplayName(), pr.displayName, typeof val === "string" ? val.slice(0, 60) : val]);
          if (!trocado && typeof val === "string" && args.texto) {
            let novo = args.texto;
            try { const o = JSON.parse(val); if (o && typeof o === "object" && "textEditValue" in o) { o.textEditValue = args.texto; novo = JSON.stringify(o); } } catch (e) {}
            await tx(p, "Gab: texto do lettering", () => [pr.createSetValueAction(pr.createKeyframe(novo), true)]);
            trocado = true;
          }
        }
      }
      return { mogrt: args.mogrt, texto_trocado: trocado, parametros: params };
    """, "lettering", seq=seq, mogrt=_abs(mogrt), texto=texto, inicio=inicio, dur=dur, trilha=trilha)


def efeitos_audio():
    """Nomes dos efeitos de áudio que a API enxerga (para achar o Enhance Speech / Aprimorar fala nesta versão)."""
    return js("return await P.AudioFilterFactory.getDisplayNames();", "efeitos de áudio")


def isolar_voz(seq, trilha_audio=0):
    """Voice isolation (regra 1d) com o Enhance Speech do Premiere. Se esta versão não expõe o efeito pela API,
    devolve {"manual": true}: aí o Gab pede ao usuário para selecionar os clipes da A1 e clicar em
    Essential Sound > Dialogue > Enhance (uma vez para todos)."""
    return js("""
      const nomes = await P.AudioFilterFactory.getDisplayNames();
      const nome = nomes.find(n => /enhance speech|aprimorar fala|melhorar fala|voice isol/i.test(n));
      if (!nome) return { manual: true, motivo: "Enhance Speech não aparece entre os efeitos da API" };
      const p = await proj(); const s = await seqPorNome(p, args.seq);
      const tr = await s.getAudioTrack(args.trilha); let n = 0;
      for (const it of tr.getTrackItems(CLIPE, false)) {
        const comp = await P.AudioFilterFactory.createComponentByDisplayName(nome, it);
        const cadeia = await it.getComponentChain();
        await tx(p, "Gab: " + nome, () => [cadeia.createAppendComponentAction(comp)]); n++;
      }
      return { efeito: nome, clipes: n };
    """, "isolar voz", seq=seq, trilha=trilha_audio)


def marcador(seq, tempo, nome, comentario=""):
    return js("""
      const p = await proj(); const s = await seqPorNome(p, args.seq);
      const m = await P.Markers.getMarkers(s);
      return await tx(p, "Gab: marcador", () => [m.createAddMarkerAction(args.nome, "Comment", tt(args.tempo), P.TickTime.TIME_ZERO, args.comentario)]);
    """, "marcador", seq=seq, tempo=tempo, nome=nome, comentario=comentario)


# ---------------------------------------------------------------- export

def preset_padrao():
    """Preset de export H.264 'Match Source - High bitrate' que vem com o Premiere."""
    if sys.platform == "darwin":
        raizes = ["/Applications"]
    else:
        raizes = [os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "Adobe")]
    for r in raizes:
        for d in os.listdir(r):
            if "Premiere Pro" not in d:
                continue
            for raiz, _, arqs in os.walk(os.path.join(r, d)):
                for a in arqs:
                    if a.lower().endswith(".epr") and "match source" in a.lower() and "high" in a.lower():
                        return os.path.join(raiz, a)
    return None


def exportar(seq, saida, preset=None, esperar=True):
    """Exporta a sequência direto pelo Premiere (sem o Media Encoder). Só quando o usuário pedir (etapa 9)."""
    preset = preset or preset_padrao()
    if not preset:
        raise SystemExit("preset .epr não encontrado; passe preset=<arquivo .epr>")
    saida = _abs(saida); os.makedirs(os.path.dirname(saida), exist_ok=True)
    r = js("""
      const p = await proj(); const s = await seqPorNome(p, args.seq);
      return await P.EncoderManager.getManager().exportSequence(s, P.Constants.ExportType.IMMEDIATELY, args.saida, args.preset, true);
    """, "exportar", seq=seq, saida=saida, preset=preset)
    if esperar:
        t0, ant = time.time(), -1
        while time.time() - t0 < 3600:
            if os.path.exists(saida):
                tam = os.path.getsize(saida)
                if tam == ant and tam > 0:
                    break
                ant = tam
            time.sleep(3)
    return r


if __name__ == "__main__":
    # Teste rápido: python3 premiere/premiere_lib.py  (com o Premiere aberto e o painel Gab Ponte visível)
    print("Premiere", versao())
    print("sequências:", sequencias())
