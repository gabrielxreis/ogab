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
import base64, hashlib, json, os, socket, struct, subprocess, sys, time

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
const clip = (it) => P.ClipProjectItem.cast(it);
// Remove itens da timeline com uma seleção própria (nunca a do usuário). A seleção só vale dentro do callback.
const remover = (p, ed, itens, tipo) => { let ok = false; p.lockedAccess(() => { P.TrackItemSelection.createEmptySelection((sel) => {
  for (const x of itens) sel.addItem(x, true);
  ok = p.executeTransaction((c) => c.addAction(ed.createRemoveItemsAction(sel, false, tipo === undefined ? P.Constants.MediaType.ANY : tipo)), "Gab: remover"); }); }); return ok; };
// Subclipe só de vídeo do take (criado uma vez, no mesmo bin): o overwrite dele não leva áudio.
async function soVideo(p, it) {
  const nome = it.name + " (video)";
  const pai = it.getParentBin ? it.getParentBin() : await p.getRootItem();
  for (const x of await pai.getItems()) if (x.name === nome) return x;
  const c = clip(it);
  if (typeof c.createSubClipAction !== "function") throw new Error("este Premiere não tem createSubClipAction (26.0): atualize para 26.5+. MOV de motion sem áudio pode ir com createOverwriteItemAction(item, t, trilha, -1) direto");
  const fim = await c.getOutPoint(P.Constants.MediaType.VIDEO);
  await tx(p, "Gab: subclipe só vídeo", () => [c.createSubClipAction(nome, P.TickTime.TIME_ZERO, fim, false, { takeVideo: true, takeAudio: false })]);
  for (const x of await pai.getItems()) if (x.name === nome) return x;
  for (const x of await itens(await p.getRootItem())) if (x.name === nome) return x;
  throw new Error("não criou o subclipe só de vídeo de " + it.name);
}
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
    try { if (c && norm(await c.getMediaFilePath()) === alvo) return it; } catch (e) {}   // item CRU: o createOverwriteItemAction recusa o cast
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
    return js("return uxp.host.version;", "versão")


def abrir_projeto(caminho=None):
    """Usa o projeto aberto (caminho=None) ou abre/cria o .prproj. Cria a árvore de bins (regra 1b) e salva."""
    if caminho:
        caminho = _abs(caminho)
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
    return js("""
      let p = await P.Project.getActiveProject();
      const c = args.caminho;
      if (c && (!p || norm(p.path) !== norm(c))) {
        p = args.existe ? await P.Project.open(c) : await P.Project.createProject(c);   // isProject() diz true para qualquer .prproj, mesmo inexistente
      }
      if (!p) throw new Error("abra ou crie um projeto no Premiere");
      for (const n of args.pastas) await bin(p, n);
      await p.save();
      return { nome: p.name, caminho: p.path };
    """, "abrir projeto", caminho=caminho, existe=bool(caminho and os.path.exists(caminho)), pastas=PASTAS)


def criar_sequencia(nome, midia_base, w=1080, h=1920, fps=30, pasta=None, sem_menu=None):
    """Cria a sequência a partir da gravação (herda áudio e cor) e força o quadro w x h e o fps do vídeo.
    Portão do menu (23/10/2026): exige o menu_escolha.json da `pasta` do vídeo ou sem_menu="motivo"."""
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
    import portao_menu; portao_menu.checar(pasta or os.path.dirname(os.path.abspath(midia_base)), sem_menu)
    return js("""
      const p = await proj();
      for (const s of await p.getSequences()) if (s.name === args.nome) { await p.setActiveSequence(s); return s.name; }
      const [base] = await importar(p, [args.midia], "Footages");
      const s = await p.createSequenceFromMedia(args.nome, [clip(base)], await bin(p, "Timelines"));
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
      const b = c.ate !== null ? tt(c.ate) : await clip(it).getOutPoint(P.Constants.MediaType.ANY);
      await tx(p, "Gab: in/out", () => [clip(it).createSetInOutPointsAction(a, b)]);
    }
    const v = c.video === null ? -1 : c.video, au = c.audio === null ? -1 : c.audio;
    let fonte = it;
    // com -1 o Premiere põe o áudio do take na A1 mesmo assim, por isso o subclipe só de vídeo. Arquivo SEM áudio
    // (motion MOV ProRes 4444) entra direto: o subclipe dele falha no 26.5 ("startTime must be less than endTime").
    if (c.audio === null && c.video !== null && c.tem_audio !== false) {
      try { fonte = await soVideo(p, it); }
      catch (e) { if (c.tem_audio === null && /startTime must be less than endTime/i.test(String(e))) fonte = it; else throw e; }  // sem ffprobe: mesmo sintoma = sem áudio
    }
    // Overwrite do ITEM com in point (sem subclipe) cai em tempo + in (relato 3f81261bd5, 20/10/2026: música com
    // de=40 entrou em 40 s): compensa a posição; o subclipe (soVideo) já começa no zero e não precisa.
    const desloc = (fonte === it && c.de) ? c.de : 0;
    const pos = Math.max(0, c.tempo - desloc);
    await tx(p, "Gab: colocar " + it.name, () => [ed.createOverwriteItemAction(fonte, tt(pos), v, au)]);
    if (c.de !== null || c.ate !== null) await tx(p, "Gab: limpa in/out", () => [clip(it).createClearInOutPointsAction()]);
    let caiu = null;   // confere onde o clipe entrou (trilha de áudio, ou de vídeo se não tem áudio)
    try {
      const tr = au >= 0 ? await s.getAudioTrack(au) : await s.getVideoTrack(v);
      for (const x of tr.getTrackItems(CLIPE, false)) {
        const st = (await x.getStartTime()).seconds;
        if (Math.abs(st - c.tempo) < 0.05) { caiu = st; break; }
        if (Math.abs(st - c.tempo - desloc) < 0.05 || Math.abs(st - c.tempo - (c.de || 0)) < 0.05) caiu = st;
      }
    } catch (e) {}
    saida.push({ nome: it.name, pedido: c.tempo, caiu });
  }
  return saida;
"""


def _tem_audio(arquivo):
    """O arquivo tem trilha de áudio? True/False pelo ffprobe; None se não deu para saber (sem ffprobe).
    Motion MOV não tem áudio: entra sem subclipe (relato 002bf235ae, 19/10/2026)."""
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index",
                            "-of", "csv=p=0", arquivo], capture_output=True, text=True, timeout=30)
        return bool(r.stdout.strip()) if r.returncode == 0 else None
    except Exception:
        return None


def colocar(seq, arquivo, tempo, video=0, audio=0, de=None, ate=None, db=None, fade_in=0, fade_out=0):
    """Overwrite do arquivo em `tempo` (s). video/audio = índice da trilha (0 = V1/A1) ou None para não usar.
    de/ate cortam a fonte (s). db/fades ajustam o volume do clipe de áudio colocado."""
    arquivo = _abs(arquivo)
    r = js(_JS_COLOCAR, "colocar", seq=seq, clipes=[dict(arquivo=arquivo, tempo=tempo, video=video, audio=audio,
                                                           de=de, ate=ate, bin=_bin_de(arquivo), tem_audio=_tem_audio(arquivo))])
    for x in (r or []):
        if isinstance(x, dict) and x.get("caiu") is not None and abs(x["caiu"] - tempo) > 0.05:
            raise RuntimeError(f"{x['nome']} entrou em {x['caiu']:.2f} s, não em {tempo:.2f} s (ponto de entrada de={de}): "
                               "conferir createOverwriteItemAction nesta versão do Premiere")
    if audio is not None and (db is not None or fade_in or fade_out):
        volume(seq, audio, tempo, db or 0, fade_in, fade_out)
    return r


def volume(seq, trilha_audio, tempo, db=0.0, fade_in=0.0, fade_out=0.0):
    """Volume do clipe de áudio que começa em `tempo` na trilha (0 = A1): nível em dB e fades por keyframe.
    O parâmetro Level/Nível do Premiere vai de 0 a 1.0 = +15 dB: 0 dB vale 0.17782794 (10^(-15/20)), o padrão de todo
    clipe. Por isso a conversão é 10^((dB - 15)/20), com teto em +15 dB. (Antes era 10^(dB/20) e todo ganho entrava
    15 dB alto: música pedida a -9,5 dB tocou a +5,5 dB. Relato 2d6c34e0f1, 19/10/2026.)"""
    return js("""
      const p = await proj(); const s = await seqPorNome(p, args.seq);
      const tr = await s.getAudioTrack(args.trilha);
      let alvo = null;
      for (const it of tr.getTrackItems(CLIPE, false))
        if (Math.abs((await it.getStartTime()).seconds - args.tempo) < 0.05) alvo = it;
      if (!alvo) throw new Error("clipe de áudio não encontrado em " + args.tempo + " s");
      const cadeia = await alvo.getComponentChain();
      const lin = Math.min(1, Math.pow(10, (args.db - 15) / 20));   // escala do Premiere: 0.1778 = 0 dB, 1.0 = +15 dB (máximo)
      const ini = (await alvo.getStartTime()).seconds, fim = (await alvo.getEndTime()).seconds;
      // Componentes e parâmetros só valem DENTRO do lockedAccess e sem await no meio (senão "script object is no longer valid").
      let ok = false, achou = false;
      p.lockedAccess(() => {
        let nivel = null;
        for (let i = 0; i < cadeia.getComponentCount() && !nivel; i++) {
          const comp = cadeia.getComponentAtIndex(i);
          for (let j = 0; j < comp.getParamCount(); j++) { const pr = comp.getParam(j); if (/^(level|nível|nivel)$/i.test(pr.displayName)) { nivel = pr; break; } }
        }
        if (!nivel) return;
        achou = true;
        const k = (t, v) => { const kf = nivel.createKeyframe(v); kf.position = tt(t); return nivel.createAddKeyframeAction(kf); };
        ok = p.executeTransaction((c) => {
          if (args.fade_in || args.fade_out) {
            c.addAction(nivel.createSetTimeVaryingAction(true));
            if (args.fade_in) { c.addAction(k(0, 0)); c.addAction(k(args.fade_in, lin)); } else c.addAction(k(0, lin));
            if (args.fade_out) { c.addAction(k(fim - ini - args.fade_out, lin)); c.addAction(k(fim - ini, 0)); }
          } else {
            c.addAction(nivel.createSetValueAction(nivel.createKeyframe(lin), true));
          }
        }, "Gab: volume");
      });
      if (!achou) throw new Error("parâmetro Level do Volume não encontrado");
      return { db: args.db, linear: lin, ok };
    """, "volume", seq=seq, trilha=trilha_audio, tempo=tempo, db=db, fade_in=fade_in, fade_out=fade_out)


def envelope_volume(seq, trilha_audio, tempo, pontos):
    """Curva de volume no clipe de áudio que começa em `tempo` (s) na trilha (0 = A1): pontos = [(t_na_sequencia, dB), ...].
    Serve para ducking (música abaixando sob uma fala) sem cortar o clipe. Mesma escala do volume(): 0 dB = 0.1778.
    (Relato e5ee2c7e86, 19/10/2026: a função tinha ficado de fora do commit dde8d8b.)"""
    return js("""
      const p = await proj(); const s = await seqPorNome(p, args.seq);
      const tr = await s.getAudioTrack(args.trilha);
      let alvo = null;
      for (const it of tr.getTrackItems(CLIPE, false))
        if (Math.abs((await it.getStartTime()).seconds - args.tempo) < 0.05) alvo = it;
      if (!alvo) throw new Error("clipe de áudio não encontrado em " + args.tempo + " s");
      const ini = (await alvo.getStartTime()).seconds, entrada = (await alvo.getInPoint()).seconds;
      const cadeia = await alvo.getComponentChain();
      let ok = false, achou = false;
      p.lockedAccess(() => {
        let nivel = null;
        for (let i = 0; i < cadeia.getComponentCount() && !nivel; i++) {
          const comp = cadeia.getComponentAtIndex(i);
          for (let j = 0; j < comp.getParamCount(); j++) { const pr = comp.getParam(j); if (/^(level|nível|nivel)$/i.test(pr.displayName)) { nivel = pr; break; } }
        }
        if (!nivel) return;
        achou = true;
        ok = p.executeTransaction((c) => {
          c.addAction(nivel.createSetTimeVaryingAction(true));
          for (const [t, db] of args.pontos) {
            const kf = nivel.createKeyframe(Math.min(1, Math.pow(10, (db - 15) / 20))); kf.position = tt(t - ini + entrada);
            c.addAction(nivel.createAddKeyframeAction(kf));
          }
        }, "Gab: envelope de volume");
      });
      if (!achou) throw new Error("parâmetro Level do Volume não encontrado");
      return { pontos: args.pontos.length, ok };
    """, "envelope", seq=seq, trilha=trilha_audio, tempo=tempo, pontos=[[float(a), float(b)] for a, b in pontos])


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
                           de=0.0, ate=(None if t1 is None else t1 - t0), bin=_bin_de(arq), tem_audio=_tem_audio(arq)))
    return js(_JS_COLOCAR, "montar takes", seq=seq, clipes=clipes)


# ---------------------------------------------------------------- transcrição (Speech to Text do Premiere)

def transcrever(arquivo, saida, idioma="pt-br"):
    """Transcreve com o próprio Premiere e salva no formato da skill (segundos, como o motor whisper do
    transcrever.py): {"motor": "premiere", "language", "segments": [{start, end, text, words: [{text, start, end}]}]}."""
    arquivo = _abs(arquivo)
    bruto = js("""
      const p = await proj();
      const [cru] = await importar(p, [args.arquivo], "Footages"); const it = clip(cru);
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


_JS_LUMETRI = """
// Garante um Lumetri no clipe de vídeo e põe o parâmetro Aparência (Look) no índice pedido.
async function lumetriLook(p, item, indice) {
  const cadeia = await item.getComponentChain();
  let tem = false;
  p.lockedAccess(() => { for (let i = 0; i < cadeia.getComponentCount(); i++) { const c = cadeia.getComponentAtIndex(i); for (let j = 0; j < c.getParamCount(); j++) if (/^(look|aparência)$/i.test(c.getParam(j).displayName)) tem = true; } });
  if (!tem) { const comp = await P.VideoFilterFactory.createComponent("AE.ADBE Lumetri"); await tx(p, "Gab: Lumetri", () => [cadeia.createAppendComponentAction(comp)]); }
  let ok = false;
  p.lockedAccess(() => {
    for (let i = cadeia.getComponentCount() - 1; i >= 0 && !ok; i--) {
      const c = cadeia.getComponentAtIndex(i);
      for (let j = 0; j < c.getParamCount(); j++) {
        const pr = c.getParam(j);
        if (/^(look|aparência)$/i.test(pr.displayName)) { ok = p.executeTransaction((cc) => cc.addAction(pr.createSetValueAction(pr.createKeyframe(indice), true)), "Gab: LUT"); break; }
      }
    }
  });
  return ok;
}
async function clipesDe(s, nomes) {
  const r = [];
  for (let i = 0; i < await s.getVideoTrackCount(); i++)
    for (const it of (await s.getVideoTrack(i)).getTrackItems(CLIPE, false)) { const n = await it.getName(); if (nomes.some((x) => n === x || n === x + " (video)")) r.push(it); }
  return r;
}
"""


def _indice_lut(seq, lut, amostra):
    """A API não aceita o LUT por nome: o Look do Lumetri é um índice do menu, que muda conforme os LUTs da máquina.
    Calibra uma vez: aplica o .cube com ffmpeg num quadro da sequência (referência) e testa os índices até bater.
    Guarda em assets/lut/indice.json (local)."""
    cache = os.path.join(AQUI, "assets", "lut", "indice.json")
    dados = json.load(open(cache)) if os.path.exists(cache) else {}
    if lut in dados:
        return dados[lut]
    cubo = luts_instalados().get(lut)
    if not cubo:
        raise SystemExit(f"LUT '{lut}' não instalado nas pastas do Premiere (rode premiere/instalar).")
    from PIL import Image, ImageChops, ImageStat
    d = os.path.join(AQUI, "assets", "lut", "_calibracao"); os.makedirs(d, exist_ok=True)   # o Premiere não grava na pasta temporária do sistema
    for f in os.listdir(d): os.remove(os.path.join(d, f))
    t = amostra["tempo"]
    def quadro(nome):
        js("const p = await proj(); const s = await seqPorNome(p, args.seq); return await P.Exporter.exportSequenceFrame(s, tt(args.t), args.n, args.d + '/', 540, 960);",
           "quadro", seq=seq, t=t, n=nome, d=d)
        f = os.path.join(d, nome)
        for _ in range(60):
            if os.path.exists(f) and os.path.getsize(f) > 0:
                time.sleep(0.3); return Image.open(f).convert("RGB")
            time.sleep(0.25)
        raise RuntimeError("o Premiere não exportou o quadro de calibração")
    def por(i):
        js(_JS_LUMETRI + "const p = await proj(); const s = await seqPorNome(p, args.seq); const [it] = await clipesDe(s, [args.nome]); return await lumetriLook(p, it, args.i);",
           "LUT", seq=seq, nome=amostra["nome"], i=i)
    por(0)
    base = quadro("base.png")
    import subprocess
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(d, "base.png"), "-vf", f"lut3d=file='{cubo}'", os.path.join(d, "ref.png")], check=True)
    ref = Image.open(os.path.join(d, "ref.png")).convert("RGB")
    dif = lambda im: sum(ImageStat.Stat(ImageChops.difference(im, ref)).mean) / 3
    melhor, ant, rep = (dif(base), 0), None, 0
    for i in range(1, 200):
        por(i); dv = round(dif(quadro(f"i{i}.png")), 2)
        if dv < melhor[0]: melhor = (dv, i)
        rep = rep + 1 if dv == ant else 0; ant = dv
        if rep >= 6: break                      # passou do fim da lista
    if melhor[1] == 0 or melhor[0] > 10:
        raise SystemExit(f"não achei o '{lut}' no menu Look do Lumetri (melhor diferença {melhor[0]}). Reinicie o Premiere depois de instalar o LUT.")
    dados[lut] = melhor[1]; json.dump(dados, open(cache, "w"), indent=1)
    return melhor[1]


def aplicar_lut(seq, arquivos, lut="LUT DO GAB"):
    """Cor (regra 7b, no lugar do PowerGrade do DaVinci): Lumetri com o LUT do Gab como Look em cada take da timeline.
    Na 1ª vez por máquina calibra o índice do LUT no menu (ver _indice_lut)."""
    nomes = [os.path.basename(a) for a in arquivos]
    ini = js(_JS_LUMETRI + "const s = await seqPorNome(await proj(), args.seq); const c = await clipesDe(s, args.nomes); return c.length ? [await c[0].getName(), (await c[0].getStartTime()).seconds + 0.5] : null;",
             "LUT", seq=seq, nomes=nomes)
    if not ini:
        raise SystemExit("nenhum dos takes está na sequência")
    indice = _indice_lut(seq, lut, {"nome": ini[0], "tempo": ini[1]})
    return js(_JS_LUMETRI + """
      const p = await proj(); const s = await seqPorNome(p, args.seq); let n = 0;
      for (const it of await clipesDe(s, args.nomes)) if (await lumetriLook(p, it, args.i)) n++;
      return { lut: args.lut, indice: args.i, clipes: n };
    """, "LUT", seq=seq, nomes=nomes, i=indice, lut=lut)


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
      let inseridos = [];     // (não chamar de "itens": é uma função do prelúdio)
      p.lockedAccess(() => { inseridos = ed.insertMogrtFromPath(args.mogrt, tt(args.inicio), args.trilha, -1); });
      const v = inseridos.find(i => i.getComponentChain && i.createSetEndAction);
      if (!v) throw new Error("o Premiere não inseriu o MOGRT");
      await tx(p, "Gab: duração do lettering", () => [v.createSetEndAction(tt(args.inicio + args.dur))]);
      // Campos do MOGRT: componente depois de Opacidade e Movimento. Os de texto são os que não começam com "Cor".
      // Texto com quebra de linha preenche os campos de texto em ordem (LINHA 1, LINHA 2...). Valor: texto puro; se o
      // Premiere não aceitar, tenta o formato JSON de texto (textEditValue).
      // logo depois de inserir, o componente com os campos do MOGRT ainda não existe: reler o clipe na trilha
      let real = v;
      for (let tentativa = 0; tentativa < 10; tentativa++) {
        await new Promise((r) => setTimeout(r, 300));
        for (const x of (await s.getVideoTrack(args.trilha)).getTrackItems(CLIPE, false))
          if (Math.abs((await x.getStartTime()).seconds - args.inicio) < 0.05) real = x;
        const ch = await real.getComponentChain(); let n = 0; p.lockedAccess(() => { n = ch.getComponentCount(); });
        if (n > 2) break;
      }
      const cadeia = await real.getComponentChain(); const campos = [];
      p.lockedAccess(() => { for (let i = 2; i < cadeia.getComponentCount(); i++) { const c = cadeia.getComponentAtIndex(i);
        for (let j = 0; j < c.getParamCount(); j++) campos.push(c.getParam(j)); } });
      const deTexto = campos.filter((pr) => pr.displayName && !/^(cor|color)/i.test(pr.displayName.trim()));
      const linhas = args.texto ? String(args.texto).split("\\n") : [];
      const params = campos.map((pr) => pr.displayName); let trocado = 0;
      for (let k = 0; k < Math.min(linhas.length, deTexto.length); k++) {
        const pr = deTexto[k];
        for (const valor of [linhas[k], JSON.stringify({ textEditValue: linhas[k] })]) {
          try { p.lockedAccess(() => { p.executeTransaction((cc) => cc.addAction(pr.createSetValueAction(pr.createKeyframe(valor), true)), "Gab: texto do lettering"); }); } catch (e) { continue; }
          let agora = null; try { agora = String(await pr.getValueAtTime(tt(0))); } catch (e) {}
          if (agora === null || agora.indexOf(linhas[k]) >= 0) { trocado++; break; }
        }
      }
      return { mogrt: args.mogrt, texto_trocado: trocado, campos_texto: deTexto.map((x) => x.displayName), parametros: params };
    """, "lettering", seq=seq, mogrt=_abs(mogrt), texto=texto, inicio=inicio, dur=dur, trilha=trilha)


def lettering_ae(seq, modelo, valores, inicio, trilha=1, pasta=None, cores=None, nome=None):
    """Lettering com o TEXTO DO VÍDEO no Premiere 26.x: a API só troca texto de MOGRT a partir do Premiere 27
    (MogrtText). Então o Gab monta o modelo da biblioteca no After Effects com os valores do vídeo, exporta um
    .mogrt só deste vídeo (texto e cores continuam editáveis no Essential Graphics) e insere na trilha.
    valores = campos do modelo (ex.: {"linha1": "SEM ATALHO.", "linha2": "COM PROCESSO."}). pasta = <vídeo>/motions."""
    raiz = os.path.dirname(AQUI)
    sys.path.insert(0, os.path.join(raiz, "scripts")); sys.path.insert(0, os.path.join(raiz, "aftereffects"))
    import biblioteca_motions as B, ae_lib as AE
    nome = nome or f"{modelo} {int(inicio * 100):06d}"
    spec = B.aplicar(modelo, valores, cores, nome_comp=nome)
    spec["elementos"] = [e for e in spec["elementos"] if e.get("tipo") not in ("fundo", "fundo_rico")]
    pasta = _abs(pasta or os.path.join(os.path.expanduser("~"), "Desktop", "ogab_mogrts"))
    AE.abrir_projeto(os.path.join(pasta, "letterings.aep"))
    AE.motion(spec)
    arq = AE.mogrt(nome, os.path.join(pasta, "mogrt"))
    r = lettering(seq, arq, None, inicio, spec["dur"], trilha=trilha)
    r["mogrt"] = arq
    return r


def efeitos_audio():
    """Nomes dos efeitos de áudio que a API enxerga (para achar o Enhance Speech / Aprimorar fala nesta versão)."""
    return js("return await P.AudioFilterFactory.getDisplayNames();", "efeitos de áudio")


def isolar_voz(seq, trilha_audio=0):
    """Voice isolation (regra 1d) com o Enhance Speech do Premiere. Se esta versão não expõe o efeito pela API,
    devolve {"manual": true}: aí o Gab pede ao usuário para selecionar os clipes da A1 e clicar em
    Essential Sound > Dialogue > Enhance (uma vez para todos)."""
    return js("""
      const nomes = await P.AudioFilterFactory.getDisplayNames();
      const nome = nomes.find(n => /enhance speech|speech enhancer|aprimorador de voz|aprimorar fala|melhorar fala|voice isol/i.test(n));
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


_JS_ANIMAR = """
// Keyframes no clipe da trilha `trilha` (0 = V1) que começa em `tempo`: Movimento (posição em fração do quadro,
// escala %, rotação °) e Opacidade (%). chaves = [[t, {x, y, escala, giro, opacidade}], ...] com t em segundos
// a partir do INÍCIO DO CLIPE na sequência.
const p = await proj(); const s = await seqPorNome(p, args.seq);
let alvo = null;
for (const it of (await s.getVideoTrack(args.trilha)).getTrackItems(CLIPE, false))
  if (Math.abs((await it.getStartTime()).seconds - args.tempo) < 0.05) alvo = it;
if (!alvo) throw new Error("clipe não encontrado na V" + (args.trilha + 1) + " em " + args.tempo + " s");
const entrada = (await alvo.getInPoint()).seconds;          // keyframe conta no tempo da mídia do clipe
const cadeia = await alvo.getComponentChain();
const prm = {};
p.lockedAccess(() => {
  for (let i = 0; i < cadeia.getComponentCount(); i++) {
    const c = cadeia.getComponentAtIndex(i);
    for (let j = 0; j < c.getParamCount(); j++) {
      const n = c.getParam(j).displayName;
      if (/^(posição|position)$/i.test(n)) prm.pos = c.getParam(j);
      else if (/^(escala|scale)$/i.test(n)) prm.esc = c.getParam(j);
      else if (/^(rotação|rotation)$/i.test(n)) prm.rot = c.getParam(j);
      else if (/^(opacidade|opacity)$/i.test(n) && !prm.op) prm.op = c.getParam(j);
    }
  }
});
const usar = { x: "pos", y: "pos", escala: "esc", giro: "rot", opacidade: "op" };
const usados = new Set(); for (const [, c] of args.chaves) for (const k in c) usados.add(usar[k]);
let ok = true, n = 0;
p.lockedAccess(() => {
  ok = p.executeTransaction((cc) => {
    for (const u of usados) if (prm[u]) cc.addAction(prm[u].createSetTimeVaryingAction(true));
    for (const [t, c] of args.chaves) {
      const quando = tt(entrada + t);
      const add = (pr, v) => { const kf = pr.createKeyframe(v); kf.position = quando; cc.addAction(pr.createAddKeyframeAction(kf)); n++; };
      if (("x" in c || "y" in c) && prm.pos) add(prm.pos, new P.PointF("x" in c ? c.x : 0.5, "y" in c ? c.y : 0.5));
      if ("escala" in c && prm.esc) add(prm.esc, c.escala);
      if ("giro" in c && prm.rot) add(prm.rot, c.giro);
      if ("opacidade" in c && prm.op) add(prm.op, c.opacidade);
    }
  }, "Gab: animar");
});
return { keyframes: n, ok: ok, entrada: entrada };
"""


def animar(seq, trilha, tempo, chaves):
    """Animação com keyframes num clipe/gráfico do Premiere (posição, escala, giro, opacidade).
    trilha: 0 = V1. tempo: onde o clipe começa na sequência (s). chaves: [(t_desde_o_inicio_do_clipe, {...}), ...]
    com x/y em fração do quadro (0.5, 0.5 = centro), escala em %, giro em graus, opacidade 0-100.
    Ex. punch-in: animar(s, 0, 9.6, [(1.0, {"escala": 100}), (1.6, {"escala": 112})])."""
    return js(_JS_ANIMAR, "animar", seq=seq, trilha=trilha, tempo=tempo,
              chaves=[[float(t), c] for t, c in chaves])


def animar_rastreado(seq, trilha, tempo, trilha_json, inicio_no_arquivo, deslocamento=(0.0, -0.10), margem=0.06):
    """Faz um gráfico/texto (MOGRT, título, PNG) na `trilha` acompanhar a trajetória de scripts/rastrear.py.
    inicio_no_arquivo: segundo do ARQUIVO rastreado que corresponde ao início do gráfico na sequência (em geral o
    ponto de entrada do take por baixo + o atraso do gráfico). deslocamento em fração do quadro (dy < 0 = acima)."""
    tr = json.load(open(trilha_json)) if isinstance(trilha_json, str) else trilha_json
    W, H = tr["w"], tr["h"]
    chaves = []
    for t, x, y, e in tr["pontos"]:
        rel = t - inicio_no_arquivo
        if rel < 0:
            continue
        cx = min(max(x / W + deslocamento[0], margem), 1 - margem)
        cy = min(max(y / H + deslocamento[1], margem), 1 - margem)
        chaves.append((round(rel, 4), {"x": round(cx, 4), "y": round(cy, 4)}))
    return animar(seq, trilha, tempo, chaves)


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
