"""Gab no Premiere Pro 2018 a 25.x (CEP + ExtendScript), sem olhar a tela: o mesmo papel do premiere_lib.py (UXP, 26+).

Como funciona: a extensão invisível "Gab Ponte PPro" (plugin/, instalada por instalar.ps1) sobe um servidor HTTP em
127.0.0.1:8767 dentro do Premiere. Cada função daqui manda ExtendScript em POST /jsx; o Premiere roda no motor dele
(evalScript) e devolve JSON. As funções de apoio ficam em jsx/gab_ppro.jsx (carregado uma vez, recarrega se mudar).

    import premiere2019_lib as P
    P.versao()                                  # "13.1.5"
    P.jsx("return app.project.name")            # qualquer ExtendScript; `args` chega como objeto
    P.retrato()                                 # trilhas e clipes da sequência ativa
Trilhas: índice 0 = V1/A1. Tempo em segundos.
"""
import json, os, sys, urllib.request, urllib.error

PORTA = int(os.environ.get("OGAB_PREMIERE_CEP_PORTA", "8767"))
AQUI = os.path.dirname(os.path.abspath(__file__))
JSX = os.path.join(AQUI, "jsx", "gab_ppro.jsx").replace("\\", "/")
PASTAS = ["Timelines", "Footages", "BRoll", "SFX", "Musicas", "Motions", "Legendas"]


def _post(script, espera=600):
    req = urllib.request.Request(f"http://127.0.0.1:{PORTA}/jsx", data=script.encode("utf-8"), method="POST")
    try:
        with urllib.request.urlopen(req, timeout=espera) as r:
            return r.read().decode("utf-8")
    except urllib.error.URLError as e:
        raise SystemExit("O Premiere não respondeu em 127.0.0.1:%d (%s). Abra o Premiere; se continuar, abra "
                         "Window > Extensions > Gab Ponte." % (PORTA, e.reason))


def conectado():
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{PORTA}/ping", timeout=3) as r:
            return r.read() == b"ok"
    except Exception:
        return False


# Envelope de toda chamada. Erro de SINTAXE no topo de um evalScript abre a janela modal "Run Script Error" e trava o
# motor até alguém clicar OK; dentro de eval() ele vira exceção comum. Por isso o apoio e o código vão em eval(), e o
# envelope em si é só ASCII fixo (testado). Resposta sem JSON (não deveria acontecer) vira texto cru com o prefixo !.
_ENVELOPE = (
    '(function () { var J = function (o) { return (typeof GAB !== "undefined" && GAB.json) ? GAB.json(o) : "!" + o.erro; };'
    ' try {'
    ' if (typeof GAB === "undefined" || GAB.__v !== %(v)s) {'
    ' var f = new File(%(arq)s); f.encoding = "UTF-8"; if (!f.open("r")) throw new Error("nao abriu " + f.fsName);'
    ' var fonte = f.read(); f.close(); eval(fonte); GAB.__v = %(v)s; }'
    ' var args = %(args)s;'
    ' var r = eval("(function () {\\n" + %(codigo)s + "\\n})")();'
    ' return J({ ok: true, resultado: r === undefined ? null : r });'
    ' } catch (e) { return J({ ok: false, erro: String(e) + (e.line ? " (linha " + e.line + ")" : "") }); } })();'
)


def jsx(codigo, rotulo="", espera=600, **args):
    """Roda ExtendScript (corpo de função: use `return`) com GAB.* carregado. args chega como `args`."""
    versao_jsx = str(os.path.getmtime(JSX))
    # ensure_ascii: o corpo vai como literal de string ASCII (o ExtendScript lê \\uXXXX sem problema de codificação)
    script = _ENVELOPE % dict(v=json.dumps(versao_jsx), arq=json.dumps(JSX), args=json.dumps(args), codigo=json.dumps(codigo))
    bruto = _post(script, espera)
    if bruto.startswith("!"):
        raise RuntimeError(f"Premiere ({rotulo or 'jsx'}): {bruto[1:]}")
    try:
        r = json.loads(bruto)
    except ValueError:
        raise RuntimeError(f"Premiere ({rotulo or 'jsx'}): resposta inesperada: {bruto[:300]!r}")
    if not r.get("ok"):
        raise RuntimeError(f"Premiere ({rotulo or 'jsx'}): {r.get('erro')}")
    return r.get("resultado")


def _abs(c):
    return os.path.abspath(os.path.expanduser(c)).replace("\\", "/")


# ---------------------------------------------------------------- projeto e sequência

def versao():
    return jsx("return app.version;", "versão")


def abrir_projeto(caminho):
    """Abre o .prproj (ou cria, se não existir) e cria a árvore de bins (regra 1b)."""
    caminho = _abs(caminho)
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    return jsx("""
      var alvo = GAB.norm(args.caminho);
      if (!(app.isDocumentOpen() && GAB.norm(app.project.path) === alvo)) {
        // 13.x não tem app.newProject. qe.newProject só cria o arquivo (não abre): abre em seguida.
        if (!args.existe) { app.enableQE(); qe.newProject(args.caminho); }
        app.openDocument(args.caminho, true, true, true);
        if (!app.isDocumentOpen()) throw new Error("não abriu/criou " + args.caminho);
      }
      for (var i = 0; i < args.pastas.length; i++) GAB.bin(args.pastas[i]);
      app.project.save();
      return { nome: app.project.name, caminho: app.project.path };
    """, "abrir projeto", caminho=caminho, existe=os.path.exists(caminho), pastas=PASTAS)


def projeto():
    return jsx("var p = GAB.proj(); return { nome: p.name, caminho: p.path, "
               "sequencias: (function(){ var l=[]; for (var i=0;i<p.sequences.numSequences;i++) l.push(p.sequences[i].name); return l; })(), "
               "ativa: p.activeSequence ? p.activeSequence.name : null };", "projeto")


def retrato(seq=None):
    """Trilhas e clipes (nome, início, fim) da sequência: a regra 1g (retrato antes de mexer)."""
    return jsx("return GAB.retrato(GAB.seq(args.seq));", "retrato", seq=seq)


def descrever(expr):
    """Engenharia reversa: métodos (com argumentos) e propriedades de qualquer objeto ExtendScript."""
    return jsx("return GAB.descrever(%s);" % expr, "descrever " + expr)


def salvar():
    return jsx("GAB.proj().save(); return true;", "salvar")


def criar_sequencia(nome, w=1080, h=1920, fps=30, preset=None):
    """Sequência nova sem diálogo (qe.project.newSequence + preset), forçada para w x h e fps exatos.
    O createNewSequence do DOM abre a janela de preset; createNewSequenceFromClips não existe no 13.x."""
    return jsx("""
      var p = GAB.proj();
      try { var s0 = GAB.seq(args.nome); p.activeSequence = s0; return s0.name; } catch (e) {}
      var pre = args.preset || GAB.instalacao("Settings/SequencePresets/Digital SLR/1080p/DSLR 1080p30.sqpreset");
      app.enableQE();
      if (!qe.project.newSequence(args.nome, pre)) throw new Error("newSequence falhou com o preset " + pre);
      var s = GAB.seq(args.nome), st = s.getSettings();
      st.videoFrameWidth = args.w; st.videoFrameHeight = args.h;
      var fr = new Time(); fr.ticks = String(Math.round(GAB.TICKS / args.fps)); st.videoFrameRate = fr;   // DSLR 1080p30 é 29,97
      s.setSettings(st);
      var b = GAB.bin("Timelines"); try { s.projectItem.moveBin(b); } catch (e2) {}
      p.activeSequence = s;
      return s.name;
    """, "criar sequência", nome=nome, w=w, h=h, fps=fps, preset=preset.replace("/", "\\") if preset else None)


# ---------------------------------------------------------------- colocar mídia

def _bin_de(caminho):
    ext = os.path.splitext(caminho)[1].lower()
    pasta = os.path.basename(os.path.dirname(caminho)).lower()
    for prefixo, b in (("broll", "BRoll"), ("sfx", "SFX"), ("musica", "Musicas"), ("motion", "Motions"), ("legenda", "Legendas")):
        if pasta.startswith(prefixo): return b
    return "Legendas" if ext == ".srt" else "Footages"


def colocar(seq, arquivo, tempo, video=0, audio=0, de=None, ate=None, db=None, fade_in=0, fade_out=0, preencher=False):
    """Overwrite do arquivo em `tempo` (s). video/audio = trilha (0 = V1/A1) ou None para não usar.
    de/ate cortam a fonte (s). Só vídeo: subclipe sem áudio. Só áudio: Track.overwriteClip na trilha de áudio.
    preencher=True escala o vídeo para cobrir o quadro (take horizontal em sequência vertical)."""
    arquivo = _abs(arquivo)
    r = jsx("""
      var s = GAB.seq(args.seq);
      GAB.garantirTrilhas(s, args.video === null ? 0 : args.video + 1, args.audio === null ? 0 : args.audio + 1);
      var it = GAB.importar([args.arquivo], args.bin)[0];
      var fonte = (args.audio === null && args.video !== null) ? GAB.soVideo(it) : it;
      GAB.marcarInOut(fonte, args.de, args.ate);
      try {
        if (args.video !== null && args.audio !== null) s.overwriteClip(fonte, GAB.tempo(args.tempo), args.video, args.audio);
        else if (args.video !== null) s.videoTracks[args.video].overwriteClip(fonte, GAB.tempo(args.tempo));
        else s.audioTracks[args.audio].overwriteClip(fonte, GAB.tempo(args.tempo));
      } finally { fonte.clearInPoint(4); fonte.clearOutPoint(4); }
      var tr = args.video !== null ? s.videoTracks[args.video] : s.audioTracks[args.audio];
      var c = GAB.clipeEm(tr, args.tempo);
      if (!c) throw new Error("o clipe não apareceu em " + args.tempo + " s na trilha pedida");
      if (args.preencher && args.video !== null) GAB.preencher(s, c);
      return { nome: c.name, inicio: c.start.seconds, fim: c.end.seconds };
    """, "colocar", seq=seq, arquivo=arquivo, tempo=float(tempo), video=video, audio=audio, de=de, ate=ate,
            bin=_bin_de(arquivo), preencher=preencher)
    if audio is not None and (db is not None or fade_in or fade_out):
        volume(seq, audio, tempo, db or 0, fade_in, fade_out)
    return r


def volume(seq, trilha_audio, tempo, db=0.0, fade_in=0.0, fade_out=0.0):
    """Volume do clipe que começa em `tempo` na trilha de áudio. ESCALA DO 13.x (medida com render + ffmpeg):
    Level = 0,5 * 10^(dB/20); 0,5 = 0 dB (padrão do clipe), teto 1,0 = +6 dB. Diferente do UXP 26 (0,1778 = 0 dB)."""
    return jsx("""
      var s = GAB.seq(args.seq), c = GAB.clipeEm(s.audioTracks[args.trilha], args.tempo);
      if (!c) throw new Error("clipe de áudio não encontrado em " + args.tempo + " s");
      var nivel = GAB.nivel(c), lin = GAB.lin(args.db);
      if (!args.fade_in && !args.fade_out) { nivel.setValue(lin, true); return { linear: lin }; }
      var ini = c.inPoint.seconds, dur = c.end.seconds - c.start.seconds;   // chaves em tempo da FONTE
      nivel.setTimeVarying(true);
      var pts = [];
      if (args.fade_in) pts.push([ini, 0], [ini + args.fade_in, lin]); else pts.push([ini, lin]);
      if (args.fade_out) pts.push([ini + dur - args.fade_out, lin], [ini + dur, 0]);
      for (var i = 0; i < pts.length; i++) { nivel.addKey(pts[i][0]); nivel.setValueAtKey(pts[i][0], pts[i][1], true); }
      return { linear: lin, chaves: pts.length };
    """, "volume", seq=seq, trilha=trilha_audio, tempo=float(tempo), db=db, fade_in=fade_in, fade_out=fade_out)


def colocar_musica(seq, wav, inicio_faixa=0.0, dur=None, db=-10.0, trilha=1, fade_in=0.5, fade_out=2.5):
    ate = None if dur is None else inicio_faixa + dur
    return colocar(seq, wav, 0.0, video=None, audio=trilha, de=inicio_faixa, ate=ate, db=db, fade_in=fade_in, fade_out=fade_out)


def montar_takes(seq, takes, fim=None, trilha=1, preencher=True):
    """takes = [(arquivo, tempo_inicio), ...]; cada take vai até o próximo (o último até `fim`), só vídeo, na V2."""
    r = []
    for i, (arq, t0) in enumerate(takes):
        t1 = takes[i + 1][1] if i + 1 < len(takes) else fim
        r.append(colocar(seq, arq, t0, video=trilha, audio=None, de=0.0, ate=None if t1 is None else t1 - t0, preencher=preencher))
    return r


def legenda(seq, srt, trilha=3):
    """SRT como item de legenda numa trilha de VÍDEO (o 13.x não tem trilha de legenda pela API).
    O item começa na 1ª fala: colocar no início da 1ª legenda, senão todas adiantam."""
    srt = _abs(srt)
    with open(srt, encoding="utf-8-sig") as f:
        import re
        m = re.search(r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->", f.read())
    inicio = int(m[1]) * 3600 + int(m[2]) * 60 + int(m[3]) + int(m[4]) / 1000 if m else 0.0
    return colocar(seq, srt, inicio, video=trilha, audio=None)


def marcador(seq, tempo, nome, comentario=""):
    return jsx("var m = GAB.seq(args.seq).markers.createMarker(args.t); m.name = args.n; m.comments = args.c; return true;",
               "marcador", seq=seq, t=float(tempo), n=nome, c=comentario)


def remover(seq, trilha_video, tempo):
    return jsx("var c = GAB.clipeEm(GAB.seq(args.seq).videoTracks[args.v], args.t); if (!c) return false; c.remove(false, false); return true;",
               "remover", seq=seq, v=trilha_video, t=float(tempo))


# ---------------------------------------------------------------- QE: corte, efeitos, transições, velocidade

def cortar(seq, trilha_video, tempo):
    """Razor da QE só na trilha de vídeo pedida (não corta o áudio). Timecode da sequência (30 fps sem drop)."""
    return jsx("GAB.qeSeq(GAB.seq(args.seq)).getVideoTrackAt(args.v).razor(GAB.tc(GAB.seq(args.seq), args.t)); return true;",
               "cortar", seq=seq, v=trilha_video, t=float(tempo))


def efeito(seq, trilha_video, tempo, nome="Lumetri Color"):
    """Efeito de vídeo pelo nome (lista: efeitos()). Devolve os componentes do clipe depois."""
    return jsx("""
      GAB.qeClipe(GAB.seq(args.seq), args.v, args.t).addVideoEffect(qe.project.getVideoEffectByName(args.n));
      var c = GAB.clipeEm(GAB.seq(args.seq).videoTracks[args.v], args.t), l = [];
      for (var i = 0; i < c.components.numItems; i++) l.push(c.components[i].displayName);
      return l;
    """, "efeito", seq=seq, v=trilha_video, t=float(tempo), n=nome)


def efeitos():
    return jsx("app.enableQE(); return { video: qe.project.getVideoEffectList(), transicoes: qe.project.getVideoTransitionList() };")


def transicao(seq, trilha_video, tempo, nome="Cross Dissolve", quadros=15, no_inicio=False):
    return jsx("""
      GAB.qeClipe(GAB.seq(args.seq), args.v, args.t).addTransition(qe.project.getVideoTransitionByName(args.n), args.ini, "00;00;00;" + (args.q < 10 ? "0" : "") + args.q);
      return GAB.seq(args.seq).videoTracks[args.v].transitions.numItems;
    """, "transição", seq=seq, v=trilha_video, t=float(tempo), n=nome, q=int(quadros), ini=no_inicio)


def velocidade(seq, trilha_video, tempo, fator):
    """fator 2 = 200%. ATENÇÃO: a QE recebe multiplicador, não porcentagem (200 vira 1 quadro)."""
    return jsx("GAB.qeClipe(GAB.seq(args.seq), args.v, args.t).setSpeed(args.f, '', false, false, false); "
               "return GAB.clipeEm(GAB.seq(args.seq).videoTracks[args.v], args.t).getSpeed();",
               "velocidade", seq=seq, v=trilha_video, t=float(tempo), f=float(fator))


# ---------------------------------------------------------------- lettering

def titulo(seq, texto, inicio, dur, trilha=3, fonte="Poppins-Bold", tamanho=90, cor=0xFFFFFF, y=None, alinhamento=2):
    """Texto editável no 13.x: o título nativo (Essential Graphics > Basic Title.mogrt) com o Source Text reescrito.
    O valor do Source Text é 4 caracteres de prefixo (o 1º = 2 x tamanho do JSON) + JSON `mTextParam`.
    cor = 0xRRGGBB. y em px da sequência (centro do texto); None = posição do modelo.
    Os MOGRTs do Gab (feitos no AE novo) travam o importMGT do 13.x: para lettering animado usar lettering_ae."""
    import glob
    modelo = (glob.glob(os.path.join(r, "Essential Graphics", "Basic Title.mogrt")) for r in _instalacoes())
    modelo = next((m[0] for m in modelo if m), None)
    if not modelo:
        raise SystemExit("Basic Title.mogrt não encontrado na instalação do Premiere")
    bruto = jsx("""
      var s = GAB.seq(args.seq);
      GAB.garantirTrilhas(s, args.v + 1, 1);
      var ti = s.importMGT(args.m, GAB.ticks(args.ini), args.v, 0);
      if (!ti) throw new Error("importMGT não devolveu o clipe");
      return GAB.textoDe(GAB.clipeEm(s.videoTracks[args.v], args.ini)).properties[0].getValue().substr(4);
    """, "título", seq=seq, m=modelo.replace("/", "\\"), v=trilha, ini=float(inicio))
    j = json.loads(bruto)
    tp = j["mTextParam"]; ss = tp["mStyleSheet"]
    ss["mText"] = texto
    ss["mFontName"]["mParamValues"][0][1] = fonte
    ss["mFontSize"]["mParamValues"][0][1] = tamanho
    ss["mFillColor"]["mParamValues"][0][1] = int(cor)
    tp["mAlignment"] = alinhamento
    return jsx("""
      var s = GAB.seq(args.seq), c = GAB.clipeEm(s.videoTracks[args.v], args.ini), txt = GAB.textoDe(c);
      txt.properties[0].setValue(String.fromCharCode(args.json.length * 2) + String.fromCharCode(0, 0, 0) + args.json, true);
      if (args.y !== null) { var pos = txt.properties[2], p = pos.getValue(); pos.setValue([p[0], args.y / s.frameSizeVertical], true); }
      var fim = GAB.tempo(args.ini + args.dur); c.end = fim;
      return { nome: c.name, inicio: c.start.seconds, fim: c.end.seconds, ok: txt.properties[0].getValue().indexOf(args.amostra) >= 0 };
    """, "título", seq=seq, v=trilha, ini=float(inicio), dur=float(dur), y=y,
               json=json.dumps(j, ensure_ascii=True, separators=(",", ":")), amostra=texto[:8].encode("ascii", "ignore").decode())


def _ler_srt(srt):
    import re
    blocos = re.split(r"\r?\n\r?\n", open(srt, encoding="utf-8-sig").read().strip())
    seg = lambda h, m, s, ms: int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000
    out = []
    for b in blocos:
        m = re.search(r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)\s*\r?\n(.*)", b, re.S)
        if m:
            out.append((seg(*m.groups()[:4]), seg(*m.groups()[4:8]), m[9].strip()))
    return out


# GAB USA (DaVinci) medido no render: Poppins Bold, caixa alta, branca, sombra leve, "NÃO FOI O MOVIMENTO" com 414 px
# de largura no 1080x1920, centro do texto em Y 724 contado de baixo. No título nativo do 13.1.5 isso é fontSize 63,53
# (calibrado em teste/t13_legenda.py); o Position do título é a LINHA DE BASE, por isso a base desce 0,26 x tamanho.
GAB_USA = dict(fonte="Poppins-Bold", tamanho=63.53, cor=0xFFFFFF, y=724, sombra=27)


def legenda_gab(seq, srt, trilha=3, y=None, estilo=None):
    """Legenda no estilo GAB USA no 13.x: um título nativo por fala do SRT (as Open Captions do 13.x não deixam trocar
    fonte nem tamanho pela API). y = altura do CENTRO do texto contada de baixo (724 do GAB USA; 390 = legenda baixa).
    Duas chamadas no total: importa todos os títulos, depois escreve texto/estilo/posição/duração de todos."""
    e = dict(GAB_USA, **(estilo or {}))
    if y is not None: e["y"] = y
    falas = _ler_srt(_abs(srt))
    if not falas:
        raise SystemExit("SRT vazio ou ilegível: " + srt)
    import glob
    modelo = next((m[0] for m in (glob.glob(os.path.join(r, "Essential Graphics", "Basic Title.mogrt")) for r in _instalacoes()) if m), None)
    bruto = jsx("""
      var s = GAB.seq(args.seq);
      GAB.garantirTrilhas(s, args.v + 1, 1);
      for (var i = 0; i < args.inicios.length; i++) s.importMGT(args.m, GAB.ticks(args.inicios[i]), args.v, 0);
      return GAB.textoDe(GAB.clipeEm(s.videoTracks[args.v], args.inicios[0])).properties[0].getValue().substr(4);
    """, "legenda (importar)", seq=seq, m=modelo.replace("/", "\\"), v=trilha, inicios=[a for a, _, _ in falas])
    base = json.loads(bruto)
    blobs = []
    for _, _, texto in falas:
        j = json.loads(json.dumps(base)); tp = j["mTextParam"]; ss = tp["mStyleSheet"]
        ss["mText"] = texto.upper().replace("\r\n", "\r").replace("\n", "\r")
        ss["mFontName"]["mParamValues"][0][1] = e["fonte"]
        ss["mFontSize"]["mParamValues"][0][1] = e["tamanho"]
        ss["mFillColor"]["mParamValues"][0][1] = int(e["cor"])
        tp["mAlignment"] = 2
        tp["mShadowVisible"] = bool(e["sombra"]); tp["mShadowOpacity"] = e["sombra"]; tp["mShadowColor"] = 0
        tp["mShadowOffset"] = 2; tp["mShadowBlur"] = 0; tp["mShadowAngle"] = 135
        js_ = json.dumps(j, ensure_ascii=True, separators=(",", ":"))
        blobs.append(chr(len(js_) * 2) + "\x00\x00\x00" + js_)
    # linha de base da 1ª linha; com N linhas o bloco cresce para baixo (entrelinha medida: 0,614 x tamanho)
    bases = [(1920 - e["y"]) + 0.26 * e["tamanho"] - t.count("\n") * 0.614 * e["tamanho"] / 2 for _, _, t in falas]
    return jsx("""
      var s = GAB.seq(args.seq), n = 0, H = s.frameSizeVertical;
      for (var i = 0; i < args.falas.length; i++) {
        var f = args.falas[i], c = GAB.clipeEm(s.videoTracks[args.v], f[0]);
        if (!c) continue;
        var txt = GAB.textoDe(c);
        txt.properties[0].setValue(args.blobs[i], true);
        var pos = txt.properties[2], p = pos.getValue(); pos.setValue([p[0], args.bases[i] / H], true);
        c.end = GAB.tempo(f[1]); n++;
      }
      return { falas: args.falas.length, colocadas: n };
    """, "legenda (estilo)", seq=seq, v=trilha, falas=[[a, b] for a, b, _ in falas], blobs=blobs, bases=bases)


def lettering_ae(seq, modelo, valores, inicio, trilha=2, pasta=None, cores=None, nome=None):
    """Lettering ANIMADO da biblioteca do Gab no 13.x: monta o modelo no After Effects (ponte do AE), renderiza em
    MOV com alfa (ae_lib.renderizar) e coloca como motion. Diferença do 26: não vira MOGRT (o importMGT do 13.x não
    aceita MOGRT do AE novo), então o texto se muda no .aep e renderiza de novo.
    valores = campos do modelo (ex.: {"linha1": "SEM ATALHO.", "linha2": "COM PROCESSO."}). pasta = <vídeo>/motions."""
    raiz = os.path.expanduser(os.path.join("~", ".claude", "skills", "ogab"))
    sys.path.insert(0, os.path.join(raiz, "scripts")); sys.path.insert(0, os.path.join(raiz, "aftereffects"))
    import biblioteca_motions as B, ae_lib as AE
    nome = nome or f"{modelo} {int(inicio * 100):06d}"
    spec = B.aplicar(modelo, valores, cores, nome_comp=nome)
    spec["elementos"] = [e for e in spec["elementos"] if e.get("tipo") not in ("fundo", "fundo_rico")]
    pasta = _abs(pasta or os.path.join(os.path.expanduser("~"), "Desktop", "ogab_letterings"))
    AE.conectar()
    AE.abrir_projeto(os.path.join(pasta, "letterings.aep"))
    AE.motion(spec)
    mov = AE.renderizar(nome, os.path.join(pasta, "mov", nome + ".mov"))
    r = colocar(seq, mov, inicio, video=trilha, audio=None)
    r["mov"] = mov
    return r


# ---------------------------------------------------------------- cor: LUT do Gab no Lumetri

def luts_instalados():
    """Os .cube que o Lumetri do 13.x pode listar: pasta da instalação (Lumetri\\LUTs) e a de usuário que o
    premiere/instalar.ps1 usa (%APPDATA%\\Adobe\\Common\\LUTs)."""
    bases = [os.path.join(os.environ.get("APPDATA", ""), "Adobe", "Common", "LUTs")]
    bases += [os.path.join(r, "Lumetri", "LUTs") for r in _instalacoes()]
    achados = {}
    for b in bases:
        for raiz, _, arqs in os.walk(b):
            for a in arqs:
                if a.lower().endswith(".cube"):
                    achados.setdefault(os.path.splitext(a)[0], os.path.join(raiz, a))
    return achados


def _instalacoes():
    import glob
    return glob.glob(os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "Adobe", "Adobe Premiere Pro*"))


_CACHE_LUT = os.path.join(AQUI, "lut_indice.json")
_LOOK = 30   # Lumetri do 13.1.5: parâmetro 30 = "Look" (Creative), 6 = "Input LUT" (Basic Correction)


def _indice_lut(lut):
    """O Look do Lumetri é um índice do menu (muda por máquina e versão). Calibra uma vez numa sequência própria:
    quadro sem LUT -> ffmpeg aplica o .cube (referência) -> testa os índices até o quadro do Premiere bater.
    Guarda em lut_indice.json por versão do Premiere."""
    v = versao()
    dados = json.load(open(_CACHE_LUT)) if os.path.exists(_CACHE_LUT) else {}
    if lut in dados.get(v, {}):
        return dados[v][lut]
    cubo = luts_instalados().get(lut)
    if not cubo:
        raise SystemExit(f"LUT '{lut}' não está nas pastas do Lumetri (rode premiere/instalar.ps1 e reabra o Premiere).")
    import subprocess, time
    from PIL import Image, ImageChops, ImageStat
    d = os.path.join(AQUI, "_calibracao_lut"); os.makedirs(d, exist_ok=True)
    for f in os.listdir(d):
        if f.endswith(".png"): os.remove(os.path.join(d, f))
    amostra = os.path.join(d, "amostra_1080.mp4")   # barras + gradiente no quadro 1920x1080 INTEIRO (preto em volta dilui a diferença)
    if not os.path.exists(amostra):   # depois de importada, o Premiere trava o arquivo: reaproveitar
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "smptehdbars=s=1920x540:d=1:r=30", "-f", "lavfi", "-i",
                    "gradients=s=1920x540:d=1:r=30", "-filter_complex", "[0][1]vstack", "-pix_fmt", "yuv420p", amostra], check=True)
    jsx("""
      var nome = "_Calibracao LUT";
      try { GAB.seq(nome); } catch (e) { app.enableQE(); qe.project.newSequence(nome, GAB.instalacao("Settings/SequencePresets/Digital SLR/1080p/DSLR 1080p30.sqpreset")); }
      var s = GAB.seq(nome);
      var cs = s.videoTracks[0].clips;
      if (!cs.numItems || GAB.norm(cs[0].projectItem.getMediaPath()) !== GAB.norm(args.a))
        s.videoTracks[0].overwriteClip(GAB.importar([args.a], "Footages")[0], GAB.tempo(0));
      var c = s.videoTracks[0].clips[0];
      for (var i = 0; i < c.components.numItems; i++) if (c.components[i].matchName === "AE.ADBE Lumetri") return true;
      GAB.qeClipe(s, 0, 0).addVideoEffect(qe.project.getVideoEffectByName("Lumetri Color"));
      return true;
    """, "calibração LUT", a=_abs(amostra))

    def quadro(i):
        png = os.path.join(d, f"i{i}.png")
        jsx("""
          var s = GAB.seq("_Calibracao LUT"), c = s.videoTracks[0].clips[0];
          GAB.lumetri(c).properties[args.look].setValue(args.i, true);
          GAB.qeSeq(s).exportFramePNG("00;00;00;10", args.png); return true;
        """, "LUT", i=i, look=_LOOK, png=png)
        for _ in range(200):
            if os.path.exists(png) and os.path.getsize(png) > 0:
                try:
                    return Image.open(png).convert("RGB").resize((320, 180))
                except (PermissionError, OSError):   # o Premiere ainda está gravando o PNG
                    pass
            time.sleep(0.05)
        raise RuntimeError("o Premiere não exportou o quadro de calibração")

    base = quadro(0)
    base.save(os.path.join(d, "base.png"))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(d, "base.png"), "-vf",
                    "lut3d=file='%s'" % cubo.replace("\\", "/").replace(":", "\\:"), os.path.join(d, "ref.png")], check=True)
    ref = Image.open(os.path.join(d, "ref.png")).convert("RGB")
    dif = lambda im: sum(ImageStat.Stat(ImageChops.difference(im, ref)).mean) / 3
    melhor, ant, rep = (dif(base), 0), None, 0
    for i in range(1, 400):
        dv = round(dif(quadro(i)), 2)
        if dv < melhor[0]: melhor = (dv, i)
        rep = rep + 1 if dv == ant else 0; ant = dv
        if rep >= 6 or dv < 1.5: break        # passou do fim da lista, ou achou
    if melhor[1] == 0 or melhor[0] > 10:
        raise SystemExit(f"não achei o '{lut}' no menu Look do Lumetri (melhor diferença {melhor[0]} no índice {melhor[1]}).")
    dados.setdefault(v, {})[lut] = melhor[1]
    json.dump(dados, open(_CACHE_LUT, "w"), indent=1)
    return melhor[1]


def aplicar_lut(seq, trilha_video, tempos, lut="LUT DO GAB"):
    """Lumetri com o LUT do Gab como Look em cada clipe da trilha que começa num dos `tempos` (s).
    Na 1ª vez por máquina calibra o índice (_indice_lut)."""
    i = _indice_lut(lut)
    return jsx("""
      var s = GAB.seq(args.seq), n = 0;
      for (var k = 0; k < args.tempos.length; k++) {
        var c = GAB.clipeEm(s.videoTracks[args.v], args.tempos[k]);
        if (!c) continue;
        var lum = GAB.lumetri(c, true);
        lum.properties[args.look].setValue(args.i, true); n++;
      }
      return { lut: args.lut, indice: args.i, clipes: n };
    """, "LUT", seq=seq, v=trilha_video, tempos=[float(t) for t in tempos], i=i, look=_LOOK, lut=lut)


# ---------------------------------------------------------------- conferir e exportar (sem olhar a tela)

def quadro(seq, tempo, png):
    """PNG de um quadro da sequência (QE). O arquivo aparece logo depois de a chamada voltar."""
    png = os.path.abspath(png)
    os.makedirs(os.path.dirname(png), exist_ok=True)
    jsx("GAB.qeSeq(GAB.seq(args.seq)).exportFramePNG(GAB.tc(GAB.seq(args.seq), args.t), args.png); return true;",
        "quadro", seq=seq, t=float(tempo), png=png)
    import time
    for _ in range(100):
        if os.path.exists(png) and os.path.getsize(png) > 0:
            try:
                with open(png, "rb+"): return png   # o Premiere ainda grava (e às vezes recria) o PNG depois de voltar
            except OSError:
                pass
        time.sleep(0.1)
    raise RuntimeError("o Premiere não gravou o quadro " + png)


def exportar(seq, saida, preset=None):
    """Render síncrono pelo próprio Premiere (sem Media Encoder). Padrão: H.264 Match Source - High bitrate."""
    saida = os.path.abspath(saida)
    os.makedirs(os.path.dirname(saida), exist_ok=True)
    return jsx("""
      var pre = args.pre || GAB.instalacao("MediaIO/systempresets/4E49434B_48323634/01 - Match Source - High bitrate.epr");
      var r = GAB.seq(args.seq).exportAsMediaDirect(args.saida, pre, app.encoder.ENCODE_ENTIRE);
      return { r: r, saida: args.saida };
    """, "exportar", espera=3600, seq=seq, saida=saida, pre=preset)
