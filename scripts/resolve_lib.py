"""Funções para montar o vídeo no DaVinci Resolve Studio pela scripting API.

Uso típico (python3 com as variáveis de ambiente do Resolve, ver ambiente()):
    from resolve_lib import *
    p, mp = criar_projeto("Assunto - Empresa", 1080, 1920, 30)
    t = criar_timeline(p, mp, "Reels 60s")
    colocar_narracao(t, mp, ".../narracoes/narracao.wav", db=5)
    colocar_musica(t, mp, ".../musica/faixa.wav", inicio_faixa=64.0, dur=48.4, db=-10, fade=2.5)
    montar_takes(t, mp, [(".../brolls/take_01.mp4", 0.0), (".../brolls/take_02.mp4", 5.1), ...], fim=48.4)
    colocar_legendas(t, mp, ".../legendas/legendas_v1.srt")
    lettering(t, "@gabrielxreis_ Cinematic", "TEXTO DO GANCHO", inicio=0.0, dur=2.5)
    renderizar(p, ".../videos", "Assunto - Empresa", 1080, 1920)
"""
import math, os, subprocess, sys, time

RESOLVE_API = "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting"
RESOLVE_LIB = "/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/fusionscript.so"


def ambiente():
    os.environ.setdefault("RESOLVE_SCRIPT_API", RESOLVE_API)
    os.environ.setdefault("RESOLVE_SCRIPT_LIB", RESOLVE_LIB)
    sys.path.append(os.path.join(RESOLVE_API, "Modules"))


def conectar(abrir=True, espera=120):
    """Conecta no Resolve (abre o app se precisar). Precisa de Preferences > System > General > External scripting = Local."""
    ambiente()
    import DaVinciResolveScript as dvr
    r = dvr.scriptapp("Resolve")
    if not r and abrir:
        subprocess.run(["open", "-a", "DaVinci Resolve"])
        t0 = time.time()
        while not r and time.time() - t0 < espera:
            time.sleep(3); r = dvr.scriptapp("Resolve")
        time.sleep(8)
    if not r:
        raise SystemExit("Resolve não respondeu. Confira External scripting = Local.")
    return r


def criar_projeto(nome, w=1080, h=1920, fps=30):
    """Cria (ou abre) o projeto 'Assunto - Empresa'. IMPORTANTE: fps de timeline E de playback
    são gravados ANTES de qualquer timeline; depois a API não muda o playback (áudio engasga)."""
    r = conectar(); pm = r.GetProjectManager()
    p = pm.CreateProject(nome)
    if p:
        for k, v in (("timelineFrameRate", str(fps)), ("timelinePlaybackFrameRate", str(fps)),
                     ("timelineResolutionWidth", str(w)), ("timelineResolutionHeight", str(h))):
            p.SetSetting(k, v)
    else:
        p = pm.LoadProject(nome)
    mp = p.GetMediaPool()
    root = mp.GetRootFolder()
    existentes = {f.GetName() for f in root.GetSubFolderList()}
    for b in ("NARRACAO", "MUSICA", "SFX", "BROLLS", "LEGENDAS"):
        if b not in existentes: mp.AddSubFolder(root, b)
    return p, mp



def checar_playback(p):
    """True se o playback fps == timeline fps. Se False o áudio picota; a API não corrige depois que há timeline:
    Project Settings > Master Settings > Playback frame rate (interface) + Playback > Render Cache > Smart."""
    pb, tl = p.GetSetting("timelinePlaybackFrameRate"), p.GetSetting("timelineFrameRate")
    ok = float(pb or 0) == float(tl or 0)
    if not ok: print(f"AVISO: playback {pb} fps != timeline {tl} fps (áudio vai picotar)")
    return ok

def _bin(mp, nome):
    for f in mp.GetRootFolder().GetSubFolderList():
        if f.GetName() == nome:
            mp.SetCurrentFolder(f); return f
    return mp.SetCurrentFolder(mp.AddSubFolder(mp.GetRootFolder(), nome))


def criar_timeline(p, mp, nome, w=None, h=None, fps=None):
    t = mp.CreateEmptyTimeline(nome); p.SetCurrentTimeline(t)
    if w and h:
        t.SetSetting("useCustomSettings", "1")
        if fps: t.SetSetting("timelineFrameRate", str(fps))
        t.SetSetting("timelineResolutionWidth", str(w)); t.SetSetting("timelineResolutionHeight", str(h))
    while t.GetTrackCount("audio") < 3: t.AddTrack("audio")   # A1 narração, A2 música, A3 efeitos
    # Já na criação: playback fps tem que ser igual ao da timeline (senão o áudio picota).
    if not checar_playback(p):
        p.SetSetting("timelinePlaybackFrameRate", str(fps or p.GetSetting("timelineFrameRate")))
        if not checar_playback(p):
            print("AJUSTAR AGORA PELA INTERFACE: File > Project Settings > Master Settings > Playback frame rate "
                  "= fps da timeline > Save; e Playback > Render Cache > Smart")
    return t


def importar(mp, caminho, bin_nome):
    _bin(mp, bin_nome)
    itens = mp.ImportMedia([caminho])
    if not itens: raise RuntimeError(f"não importou {caminho}")
    return itens[0]


def fps_tl(t):
    return float(t.GetSetting("timelineFrameRate"))


def colocar_narracao(t, mp, wav, db=5):
    it = importar(mp, wav, "NARRACAO")
    x = mp.AppendToTimeline([{"mediaPoolItem": it, "mediaType": 2, "trackIndex": 1, "recordFrame": t.GetStartFrame()}])[0]
    x.SetProperty("AudioVolume", db)   # a chave "Volume" não funciona; "AudioVolume" sim
    return it, x


def preparar_musica(origem, destino, inicio_faixa, dur, fade=2.5, hz=48000):
    """Corta o trecho usado, já com fade in curto e fade out no fim, em 48 kHz (a API não faz fade)."""
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", str(inicio_faixa), "-t", str(dur), "-i", origem,
                    "-af", f"afade=t=in:d=0.5,afade=t=out:st={max(0, dur - fade)}:d={fade}", "-ar", str(hz), destino], check=True)
    return destino


def colocar_musica(t, mp, wav_pronto, db=-10):
    it = importar(mp, wav_pronto, "MUSICA")
    x = mp.AppendToTimeline([{"mediaPoolItem": it, "mediaType": 2, "trackIndex": 2, "recordFrame": t.GetStartFrame()}])[0]
    x.SetProperty("AudioVolume", db)
    return x


def colocar_sfx(t, mp, lista, db=-6):
    """lista = [(arquivo, segundo_na_timeline), ...] na A3."""
    S, F = t.GetStartFrame(), fps_tl(t); out = []
    for arq, seg in lista:
        it = importar(mp, arq, "SFX")
        x = mp.AppendToTimeline([{"mediaPoolItem": it, "mediaType": 2, "trackIndex": 3, "recordFrame": S + round(seg * F)}])
        if x: x[0].SetProperty("AudioVolume", db); out.append(x[0])
    return out


def montar_takes(t, mp, takes, fim, zoom=1.0):
    """takes = [(arquivo, inicio_s), ...] em ordem. Cada take vai até o início do próximo, sem buraco:
    encadeia pelo GetEnd() real e usa ceil (fontes 24/25 fps numa timeline 30 deixariam 1-2 quadros pretos)."""
    S, F = t.GetStartFrame(), fps_tl(t)
    cur = S + round(takes[0][1] * F); fim_f = S + round(fim * F); itens = []
    for k, (arq, ini) in enumerate(takes):
        nxt = S + round(takes[k + 1][1] * F) if k + 1 < len(takes) else fim_f
        it = importar(mp, arq, "BROLLS")
        sf = float(it.GetClipProperty("FPS")); mx = int(float(it.GetClipProperty("Frames")))
        n = min(mx, math.ceil((nxt - cur) * sf / F) + 1)
        x = mp.AppendToTimeline([{"mediaPoolItem": it, "startFrame": 0, "endFrame": n - 1, "mediaType": 1,
                                  "trackIndex": 1, "recordFrame": cur}])[0]
        if zoom != 1.0: x.SetProperty("ZoomX", zoom); x.SetProperty("ZoomY", zoom)
        itens.append(x); cur = x.GetEnd()
        if x.GetEnd() < nxt: print(f"AVISO: {os.path.basename(arq)} é curto, sobra {nxt - x.GetEnd()} quadros")
    return itens


def movimento(item, tipo="zoom_in", intensidade=0.08):
    """Movimento leve no take (só se o usuário pediu). A API não cria keyframes; aplica zoom estático
    como base e deixa anotado para animar no Inspector, ou use o preset de lettering/efeito no Edit."""
    z = 1.0 + intensidade
    item.SetProperty("ZoomX", z); item.SetProperty("ZoomY", z)
    return z


def aplicar_grade(r, t, drx, drx_iphone=None, trilha=1):
    """Aplica o PowerGrade (.drx) em todos os takes da trilha. Takes de iPhone recebem `drx_iphone`
    (PowerGrade combinado: conversor do iPhone ANTES + LUT/look depois), se configurado.
    Notas da API: Timeline.ApplyGradeFromDRX não funciona; usar TimelineItem.GetNodeGraph().ApplyGradeFromDRX(path, 0).
    Os grafos de grupo (pre/post-clip) NÃO aceitam .drx (só SetLUT), por isso a ordem conversor -> LUT
    precisa vir pronta num único PowerGrade combinado. Sempre pegar o grafo de novo a cada chamada (grafo velho derruba o Resolve)."""
    from midia import eh_iphone
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    absol = lambda p: p if (not p or os.path.isabs(p)) else os.path.join(base, p)
    drx, drx_iphone = absol(drx), absol(drx_iphone)
    r.OpenPage("color"); res = []
    for x in t.GetItemListInTrack("video", trilha) or []:
        arq = x.GetMediaPoolItem().GetClipProperty("File Path")
        iph = bool(arq and os.path.exists(arq) and eh_iphone(arq))
        usar = drx_iphone if (iph and drx_iphone and os.path.exists(drx_iphone)) else drx
        if iph and usar == drx: print(f"AVISO: {x.GetName()} é de iPhone mas não há PowerGrade combinado (cor.drx_iphone); aplicado só o LUT")
        res.append((x.GetName(), "iphone" if iph else "padrao", bool(x.GetNodeGraph().ApplyGradeFromDRX(usar, 0))))
    r.OpenPage("edit")
    return res


def colocar_legendas(t, mp, srt, trocar=True):
    """Importa o SRT na trilha de legenda. Se a trilha já existe, troca só os itens (mantém o preset de estilo)."""
    if t.GetTrackCount("subtitle") == 0: t.AddTrack("subtitle")
    elif trocar:
        antigos = t.GetItemListInTrack("subtitle", 1) or []
        if antigos: t.DeleteClips(antigos, False)
    it = importar(mp, srt, "LEGENDAS")   # nome de arquivo único por versão (v1, v2...)
    mp.AppendToTimeline([it])
    return len(t.GetItemListInTrack("subtitle", 1) or [])


def _tc(t, f):
    F = int(round(fps_tl(t))); h, rem = divmod(f, F * 3600); m, rem = divmod(rem, F * 60); s, q = divmod(rem, F)
    return f"{h:02d}:{m:02d}:{s:02d}:{q:02d}"


def tamanho_lettering(texto, base=0.19, largura=0.85):
    """Tamanho do texto para caber na largura do quadro vertical (medido: largura ~ caracteres x size x 0.39)."""
    maior = max(len(l) for l in texto.split("\n"))
    return round(min(base, largura / (0.39 * max(maior, 1))), 4)


def _textos(comp):
    """Todas as ferramentas de texto (Text+) do título. O nome muda por animação (Template, Template_1, Text1...)
    e algumas têm duas (Corte: o texto é duplicado e cortado por máscara), então o texto vai em todas."""
    return [x for x in comp.GetToolList(False).values() if x.ID == "TextPlus"]


def _fade_saida(comp, dur_f, fade_f, fim):
    """Fade out na IMAGEM FINAL do título (nó ColorGain 'FadeSaida' logo antes do MediaOut, ganho em R, G, B e alfa):
    some tudo junto (texto, sombra, barras, linhas, brilho), em qualquer animação. SetKeyFrames(..., True)
    substitui a curva inteira (somar keyframes por SetInput deixava o texto voltar depois do fade)."""
    mo = comp.FindTool("MediaOut1")
    g = comp.FindTool("FadeSaida")
    if not g:
        src = mo.Input.GetConnectedOutput()
        comp.Lock(); g = comp.AddTool("ColorGain", -32768, -32768); g.SetAttrs({"TOOLS_Name": "FadeSaida"})
        g.Input = src; mo.Input = g.Output; comp.Unlock()
    kf = {0.0: {1: 1.0}, float(dur_f): {1: 1.0}, float(dur_f + fade_f): {1: 0.0}, float(fim + 1): {1: 0.0}}
    for ent in ("GainRed", "GainGreen", "GainBlue", "GainAlpha"):
        inp = getattr(g, ent); out = inp.GetConnectedOutput()
        if not out:
            comp.Lock(); setattr(g, ent, comp.BezierSpline({})); comp.Unlock(); out = getattr(g, ent).GetConnectedOutput()
        out.GetTool().SetKeyFrames(kf, True)
    if round(g.GetInput("GainAlpha", dur_f + fade_f), 2) != 0.0 or round(g.GetInput("GainAlpha", 0), 2) != 1.0:
        raise RuntimeError("fade de saída não ficou certo")


VEL_ENTRADA = 0.7   # animação do pacote a 70%: na velocidade original a entrada leva ~20 quadros e o texto "pula" na tela
SEGURA_F = 10       # quadros a mais com o texto inteiro antes do fade (compensa a entrada mais lenta)


def ajustar_titulo(item, texto, size=None, dur_f=None, fade_f=18, entrelinha=0.8, cor=(1.0, 1.0, 1.0), velocidade=VEL_ENTRADA):
    """Padrão do usuário para os letterings: Shading Element = SOLID (o template vem com gradiente, Type1=2),
    cor sólida, entrelinha mais junta com quebra de linha, tamanho que cabe na largura, animação na velocidade
    um pouco MAIS LENTA (velocidade 0.7: entrada suave; nunca acima de 1.0, acelerar pede quadros além do fim
    do título: "frame not available") e, se dur_f for
    menor que o título, FADE OUT médio (fade_f quadros) na imagem inteira do título (_fade_saida)."""
    comp = item.GetFusionCompByIndex(1); txts = _textos(comp)
    if not txts: raise RuntimeError(f"título sem Text+: {item.GetName()}")
    for tool in txts:
        tool.SetInput("StyledText", texto); tool.SetInput("Size", size or tamanho_lettering(texto))
        tool.SetInput("ShadingElements", 1); tool.SetInput("Type1", 0)          # 0 = Solid
        tool.SetInput("Red1", cor[0]); tool.SetInput("Green1", cor[1]); tool.SetInput("Blue1", cor[2]); tool.SetInput("Alpha1", 1.0)
        if "\n" in texto: tool.SetInput("LineSpacing", entrelinha)
    for ts in comp.GetToolList(False, "TimeSpeed").values(): ts.SetInput("Speed", min(1.0, velocidade))
    fim = int(comp.GetAttrs().get("COMPN_RenderEnd", item.GetDuration() - 1))
    if dur_f: dur_f = min(dur_f + SEGURA_F, fim - fade_f - 1)
    if dur_f and dur_f + fade_f < fim: _fade_saida(comp, dur_f, fade_f, fim)


def checar_fades(t):
    """Confere se TODO lettering (título Fusion acima da V1) termina com fade (nó FadeSaida): cai para 0 e não volta."""
    ruins = []
    for v in range(2, t.GetTrackCount("video") + 1):
        for it in t.GetItemListInTrack("video", v) or []:
            if not it.GetFusionCompCount(): continue
            c = it.GetFusionCompByIndex(1); g = c.FindTool("FadeSaida"); txt = (_textos(c) or [None])[0]
            nome = txt.GetInput("StyledText") if txt else it.GetName()
            if not g: ruins.append(nome); continue
            vals = [g.GetInput("GainAlpha", f) or 0 for f in range(0, it.GetDuration(), 3)]
            caiu = next((i for i, x in enumerate(vals) if x < 0.01), None)
            if caiu is None or any(x > 0.01 for x in vals[caiu:]): ruins.append(nome)
    print("fades OK" if not ruins else f"SEM FADE LIMPO: {ruins}")
    return ruins


def _ir(t, f, tentativas=20):
    """Move o playhead e espera ele chegar (SetCurrentTimecode é assíncrono; sem esperar, o título cai no lugar errado)."""
    alvo = _tc(t, f)
    for _ in range(tentativas):
        t.SetCurrentTimecode(alvo); time.sleep(0.25)
        if t.GetCurrentTimecode() == alvo: return True
    raise RuntimeError(f"playhead não foi para {alvo} (está em {t.GetCurrentTimecode()})")


def _inserir_titulo_v1(t, template, texto, ini_f, dur_f):
    """Insere o Fusion Title na V1 em ini_f (a API sempre usa a V1, com ripple). NÃO corta o título:
    cortar um Fusion Title no meio derruba o Resolve. A duração visível vem de um fade out na opacidade
    do texto: o título fica com o tamanho padrão, mas o texto some (com fade médio) depois de dur_f quadros."""
    _ir(t, ini_f)
    it = t.InsertFusionTitleIntoTimeline(template)
    if not it: raise RuntimeError(f"template '{template}' não encontrado (pacote instalado? Resolve reiniciado?)")
    achados = [x for x in (t.GetItemListInTrack("video", 1) or []) if x.GetStart() == ini_f]
    if not achados: raise RuntimeError(f"título não caiu em {ini_f}")
    alvo = achados[0]
    ajustar_titulo(alvo, texto, dur_f=dur_f)
    return alvo


def _assinatura(t):
    """Posição de todos os itens de áudio e legenda (para provar que o ripple dos títulos não mexeu neles)."""
    return [(k, i, x.GetStart(), x.GetDuration()) for k in ("audio", "subtitle")
            for i in range(1, t.GetTrackCount(k) + 1) for x in (t.GetItemListInTrack(k, i) or [])]


def camada_letterings(t, mp, lista, template):
    """Coloca letterings [(TEXTO, inicio_s, dur_s[, template]), ...] em camadas logo ACIMA dos takes (sem compound).
    A API só insere título na V1 e com ripple, então: guarda os takes da V1 e tira; distribui os letterings em
    camadas sem sobreposição (cada título ocupa o tamanho padrão do template); para cada camada, insere na V1
    vazia em ordem cronológica (com áudio, legenda e outras trilhas TRAVADAS para o ripple não mexer) e cria
    uma trilha nova na posição 1 (a camada sobe). No fim recoloca os takes na V1. Reaplicar a cor depois.
    Devolve os intervalos ocupados (para sem_legenda)."""
    F = fps_tl(t); S = t.GetStartFrame()
    # GetLeftOffset/GetDuration vêm em quadros da TIMELINE, mas AppendToTimeline (startFrame/endFrame) pede quadros
    # da FONTE: em take 24/25 fps numa timeline 30, usar direto desloca o início e estica o take a cada refação.
    takes = []
    for x in (t.GetItemListInTrack("video", 1) or []):
        m = x.GetMediaPoolItem()
        if not m: continue
        r_ = float(m.GetClipProperty("FPS")) / F
        takes.append((m, x.GetStart(), round(x.GetLeftOffset() * r_), x.GetDuration(), x.GetProperty("ZoomX"), r_))
    velhos = t.GetItemListInTrack("video", 1) or []
    if velhos: t.DeleteClips(velhos, False)
    padrao = 150  # duração padrão dos Fusion Titles do pacote (5 s a 30 fps); conferido ao inserir
    camadas = []
    for item in sorted(lista, key=lambda x: x[1]):
        ini_f = S + round(item[1] * F)
        for c in camadas:
            if ini_f >= c[-1][4] + 1: c.append((*item[:3], item[3] if len(item) > 3 else template, ini_f + padrao)); break
        else: camadas.append([(*item[:3], item[3] if len(item) > 3 else template, ini_f + padrao)])
    ocup = [(x[1], x[1] + x[2] + (SEGURA_F + 18) / F) for x in lista]   # inclui a folga e o fade out
    for c in reversed(camadas):           # a primeira camada termina mais perto dos takes
        travar = [(k, i) for k in ("audio", "subtitle") for i in range(1, t.GetTrackCount(k) + 1)] + \
                 [("video", i) for i in range(2, t.GetTrackCount("video") + 1)]
        for k, i in travar: t.SetTrackLock(k, i, True)
        soltas = [(k, i) for k, i in travar if not t.GetIsTrackLocked(k, i)]
        if soltas: raise RuntimeError(f"trilhas não travaram {soltas}: o ripple do título ia empurrar áudio/legenda")
        antes = _assinatura(t)
        try:
            for texto, ini, dur, tpl, _ in c:
                _inserir_titulo_v1(t, tpl, texto, S + round(ini * F), round(dur * F))
        finally:
            for k, i in travar: t.SetTrackLock(k, i, False)
        if _assinatura(t) != antes: raise RuntimeError("áudio/legenda mudaram ao inserir título (ripple): desfazer e refazer")
        t.AddTrack("video", {"index": 1})
    for mpi, st, lo, dur, zoom, r_ in takes:
        x = mp.AppendToTimeline([{"mediaPoolItem": mpi, "startFrame": lo, "endFrame": lo + math.ceil(dur * r_) - 1, "mediaType": 1,
                                  "trackIndex": 1, "recordFrame": st}])
        if x and zoom and zoom != 1.0: x[0].SetProperty("ZoomX", zoom); x[0].SetProperty("ZoomY", zoom)
    return ocup


def gerar_capa(r, p, mp, take, texto, template, pasta, nome="capa", seg_take=1.0, seg_quadro=3.3, w=1080, h=1920, drx=None):
    """Capa (thumbnail): quadro do take + lettering do gancho numa camada acima, PNG renderizado no DaVinci.
    Texto em 2-3 linhas curtas (\\n). seg_quadro = ponto da animação com o texto inteiro na tela."""
    ant = p.GetCurrentTimeline()
    t = mp.CreateEmptyTimeline(f"CAPA {nome} {int(time.time()) % 100000}"); p.SetCurrentTimeline(t)
    t.SetSetting("useCustomSettings", "1"); t.SetSetting("timelineResolutionWidth", str(w)); t.SetSetting("timelineResolutionHeight", str(h))
    F = fps_tl(t); S = t.GetStartFrame()
    it = importar(mp, take, "BROLLS"); sf = float(it.GetClipProperty("FPS")); mx = int(float(it.GetClipProperty("Frames")))
    ini = min(int(seg_take * sf), max(0, mx - int(4 * sf)))
    mp.AppendToTimeline([{"mediaPoolItem": it, "startFrame": ini, "endFrame": min(mx - 1, ini + int(4 * sf)), "mediaType": 1, "trackIndex": 1, "recordFrame": S}])
    camada_letterings(t, mp, [(texto, 0.0, 5.0)], template)
    if drx: t.GetItemListInTrack("video", 1)[0].GetNodeGraph().ApplyGradeFromDRX(drx, 0)
    q = S + round(seg_quadro * F)
    for j in p.GetRenderJobList(): p.DeleteRenderJob(j["JobId"])
    p.SetCurrentRenderFormatAndCodec("png", "RGB8")
    p.SetRenderSettings({"SelectAllFrames": False, "MarkIn": q, "MarkOut": q, "TargetDir": pasta, "CustomName": nome,
                         "FormatWidth": w, "FormatHeight": h, "ExportVideo": True, "ExportAudio": False})
    jid = p.AddRenderJob(); p.StartRendering(jid)
    while p.IsRenderingInProgress(): time.sleep(1)
    p.SetCurrentTimeline(ant)
    import glob
    gerados = sorted(glob.glob(os.path.join(pasta, nome + "*.png")), key=os.path.getmtime)
    if gerados and gerados[-1] != os.path.join(pasta, nome + ".png"): os.replace(gerados[-1], os.path.join(pasta, nome + ".png"))
    return os.path.join(pasta, nome + ".png")


def renderizar(p, pasta, nome, w=1080, h=1920, legenda_gravada=True):
    for j in p.GetRenderJobList(): p.DeleteRenderJob(j["JobId"])
    p.SetCurrentRenderFormatAndCodec("mp4", "H264")
    cfg = {"SelectAllFrames": True, "TargetDir": pasta, "CustomName": nome, "FormatWidth": w, "FormatHeight": h}
    if legenda_gravada: cfg.update({"ExportSubtitle": True, "SubtitleFormat": "BurnIn"})
    p.SetRenderSettings(cfg)
    jid = p.AddRenderJob(); p.StartRendering(jid)
    while p.IsRenderingInProgress(): time.sleep(2)
    st = p.GetRenderJobStatus(jid)
    return os.path.join(pasta, nome + ".mp4"), st.get("JobStatus")


def salvar(r=None):
    (r or conectar(False)).GetProjectManager().SaveProject()
