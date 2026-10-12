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
import math, os, re, subprocess, sys, time

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
    garantir_pastas(mp)   # árvore do Media Pool logo ao criar/abrir (regra 1b)
    return p, mp


def abrir_projeto(nome=None):
    """Abre o projeto (ou usa o atual) e JÁ cria a árvore de pastas do Media Pool (regra 1b). Usar no início
    de toda edição de projeto existente, antes de importar qualquer coisa."""
    r = conectar(); pm = r.GetProjectManager()
    p = pm.LoadProject(nome) if nome else pm.GetCurrentProject()
    mp = p.GetMediaPool(); garantir_pastas(mp)
    return p, mp


def garantir_pastas(mp):
    """Cria na raiz do Media Pool as pastas Timelines, Footages, BRoll, SFX, Musicas, Motions, Legendas (as que faltarem).
    Não move nada; para arrumar o que já existe, `organizar(...)`."""
    root = mp.GetRootFolder(); tem = {f.GetName() for f in root.GetSubFolderList() or []}
    for n in PASTAS_PROJETO:
        if n not in tem: mp.AddSubFolder(root, n)
    mp.SetCurrentFolder(root)



def checar_playback(p):
    """True se o playback fps == timeline fps. Se False o áudio picota; a API não corrige depois que há timeline:
    Project Settings > Master Settings > Playback frame rate (interface). Não ligar Render Cache (fica em None)."""
    pb, tl = p.GetSetting("timelinePlaybackFrameRate"), p.GetSetting("timelineFrameRate")
    ok = float(pb or 0) == float(tl or 0)
    if not ok: print(f"AVISO: playback {pb} fps != timeline {tl} fps (áudio vai picotar)")
    return ok

# nomes antigos/variações caem na pasta certa da árvore (regra 1b)
ALIAS_PASTA = {"NARRACAO": "Footages", "GRAVACOES": "Footages", "FOOTAGE": "Footages", "FOTOS": "Footages",
               "MUSICA": "Musicas", "MUSICAS": "Musicas", "BROLLS": "BRoll", "BROLL": "BRoll", "TAKES": "BRoll",
               "LEGENDAS": "Legendas", "LEGENDA": "Legendas", "MOTIONS": "Motions", "SFX": "SFX", "TIMELINES": "Timelines"}


def _bin(mp, nome):
    nome = ALIAS_PASTA.get(nome.upper(), nome)
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
                  "= fps da timeline > Save (Render Cache fica em None)")
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
    """OBSOLETO para a timeline (o usuário quer a música bruta, cortada no DaVinci: use colocar_musica com inicio_faixa). Só para prévia/export fora do DaVinci. Corta o trecho usado, já com fade in curto e fade out no fim, em 48 kHz (a API não faz fade)."""
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", str(inicio_faixa), "-t", str(dur), "-i", origem,
                    "-af", f"afade=t=in:d=0.5,afade=t=out:st={max(0, dur - fade)}:d={fade}", "-ar", str(hz), destino], check=True)
    return destino


def garantir_trilhas_audio(t, n):
    """Cria trilhas de áudio estéreo até ter n (timeline de gravação vem só com A1; sem isso o append some calado)."""
    while t.GetTrackCount("audio") < n:
        t.AddTrack("audio", "stereo")


def colocar_musica(t, mp, wav_bruto, inicio_faixa=0.0, dur=None, db=-10, fade_in=0.5, fade_out=2.5):
    """Música BRUTA na A2 (regra do usuário, 11/10/2026): o WAV original entra inteiro no Media Pool e o corte
    é feito no DaVinci (ponto de entrada = inicio_faixa, duração = dur ou a timeline toda), com fade no clipe.
    Nada de cortar/renderizar o áudio antes: assim o usuário consegue arrastar e reajustar na timeline."""
    garantir_trilhas_audio(t, 2)
    it = importar(mp, wav_bruto, "MUSICA")
    fps_c = float(it.GetClipProperty("FPS") or fps_tl(t))
    if dur is None:
        dur = (t.GetEndFrame() - t.GetStartFrame()) / fps_tl(t)
    ini = int(round(inicio_faixa * fps_c))
    res = mp.AppendToTimeline([{"mediaPoolItem": it, "mediaType": 2, "trackIndex": 2, "recordFrame": t.GetStartFrame(),
                                "startFrame": ini, "endFrame": ini + int(round(dur * fps_c)) - 1}])
    if not res:
        raise RuntimeError("a música não entrou na A2 (timeline atual é outra?)")
    x = res[0]
    x.SetProperty("AudioVolume", db)
    F = fps_tl(t)
    try:
        x.SetFades({"FadeIn": int(round(fade_in * F)), "FadeOut": int(round(fade_out * F))})
    except Exception:
        pass
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


def colocar_legendas(t, mp, srt, trocar=True, p=None):
    """Importa o SRT na trilha de legenda. Se a trilha já existe, troca só os itens (mantém o preset de estilo)."""
    # DeleteClips/AppendToTimeline só valem na timeline ATUAL: abrir `t` antes de tudo
    if p: p.SetCurrentTimeline(t); import time; time.sleep(0.5)
    if t.GetTrackCount("subtitle") == 0: t.AddTrack("subtitle")
    elif trocar:
        antigos = t.GetItemListInTrack("subtitle", 1) or []
        if antigos and not t.DeleteClips(antigos, False):
            raise RuntimeError(f"não apagou as legendas antigas de '{t.GetName()}' (timeline atual?)")
    # O Media Pool reaproveita item pelo NOME do arquivo: SRT com mesmo nome em vídeos diferentes faz um vídeo
    # receber a legenda do outro. Sempre importar com nome único (pasta do vídeo + nome).
    pasta_video = os.path.basename(os.path.dirname(os.path.dirname(os.path.abspath(srt))))
    unico = os.path.join(os.path.dirname(srt), f"{pasta_video.split(' - ')[0].replace(' ', '_')}__{os.path.basename(srt)}")
    if not os.path.exists(unico): import shutil; shutil.copy(srt, unico)
    it = importar(mp, unico, "LEGENDAS")
    # AppendToTimeline usa a timeline ABERTA (já aberta acima; sem p= a legenda pode cair em outro vídeo)
    # trilha de legenda DESABILITADA recusa o SRT em silêncio (render sem legenda pode deixá-la desligada)
    t.SetTrackEnable("subtitle", 1, True)
    n0 = len(t.GetItemListInTrack("subtitle", 1) or [])
    mp.AppendToTimeline([it])
    if len(t.GetItemListInTrack("subtitle", 1) or []) == n0:
        raise RuntimeError(f"a legenda não entrou em '{t.GetName()}': passe p= para abrir a timeline certa")
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


SEGURA_F = 0   # quadros extras com o texto inteiro antes do fade
FADE_LETTERING = 31   # fade de saída no bloco (o usuário ajustou assim no 'NÃO ABANDONE SUA CARREIRA')


def ajustar_titulo(item, texto, size=None, dur_f=None, fade_f=31, entrelinha=0.8, cor=(1.0, 1.0, 1.0), centro_y=None):
    """Padrão do usuário para os letterings: troca SÓ o que não é animado no template: texto, tamanho que cabe na
    largura, Shading Element = SOLID (Type1=0), entrelinha 0.8 com quebra de linha e, se pedido, a altura (centro_y,
    0 = base, 1 = topo do quadro). NUNCA sobrescrever entrada que tenha animação (GetConnectedOutput) nem o TimeSpeed:
    o pacote já tem animação de ENTRADA e ela tem que aparecer. A saída é um FADE NO BLOCO da timeline
    (TimelineItem.SetFades FadeOut), não um nó dentro da composição. dur_f fica só por compatibilidade (o bloco
    tem a duração padrão do template, 5 s; a API não apara título)."""
    comp = item.GetFusionCompByIndex(1); txts = _textos(comp)
    if not txts: raise RuntimeError(f"título sem Text+: {item.GetName()}")
    def por(tool, nome, valor):
        inp = tool.GetInputList(); ent = next((i for i in inp.values() if i.GetAttrs()["INPS_ID"] == nome), None)
        if ent is not None and ent.GetConnectedOutput(): return       # animado pelo template: não mexer
        tool.SetInput(nome, valor)
    for tool in txts:
        tool.SetInput("StyledText", texto)
        por(tool, "Size", size or tamanho_lettering(texto))
        por(tool, "ShadingElements", 1); por(tool, "Type1", 0)            # 0 = Solid
        por(tool, "Red1", cor[0]); por(tool, "Green1", cor[1]); por(tool, "Blue1", cor[2])
        if "\n" in texto: por(tool, "LineSpacing", entrelinha)
        if centro_y is not None: por(tool, "Center", {1: 0.5, 2: centro_y})
    item.SetFades({"FadeOut": fade_f or FADE_LETTERING})


def checar_fades(t):
    """Confere se TODO lettering (título, item sem MediaPoolItem acima da V1) tem fade out no bloco. NÃO abre a
    composição do Fusion (abrir congela a animação no render)."""
    ruins = [it.GetName() for v in range(2, t.GetTrackCount("video") + 1) for it in (t.GetItemListInTrack("video", v) or [])
             if it.GetMediaPoolItem() is None and not (it.GetFades() or {}).get("FadeOut")]
    print("fades OK" if not ruins else f"SEM FADE NO BLOCO: {ruins}")
    return ruins


def _ir(t, f, tentativas=20):
    """Move o playhead e espera ele chegar (SetCurrentTimecode é assíncrono; sem esperar, o título cai no lugar errado)."""
    alvo = _tc(t, f)
    for _ in range(tentativas):
        t.SetCurrentTimecode(alvo); time.sleep(0.25)
        if t.GetCurrentTimecode() == alvo: return True
    raise RuntimeError(f"playhead não foi para {alvo} (está em {t.GetCurrentTimecode()})")


def _inserir_titulo_v1(t, template, texto, ini_f, dur_f, centro_y=None):
    """Insere o Fusion Title na V1 em ini_f (a API sempre usa a V1, com ripple). NÃO corta o título:
    cortar um Fusion Title no meio derruba o Resolve. A duração visível vem de um fade out na opacidade
    do texto: o título fica com o tamanho padrão, mas o texto some (com fade médio) depois de dur_f quadros."""
    _ir(t, ini_f); time.sleep(0.6); _ir(t, ini_f)          # a interface demora a assentar o playhead
    it = t.InsertFusionTitleIntoTimeline(template)
    if not it: raise RuntimeError(f"template '{template}' não encontrado (pacote instalado? Resolve reiniciado?)")
    achados = [x for x in (t.GetItemListInTrack("video", 1) or []) if x.GetStart() == ini_f]
    if not achados: raise RuntimeError(f"título não caiu em {ini_f}")
    alvo = achados[0]
    ajustar_titulo(alvo, texto, dur_f=dur_f, centro_y=centro_y)
    return alvo


def _assinatura(t):
    """Posição de todos os itens de áudio e legenda (para provar que o ripple dos títulos não mexeu neles)."""
    return [(k, i, x.GetStart(), x.GetDuration()) for k in ("audio", "subtitle")
            for i in range(1, t.GetTrackCount(k) + 1) for x in (t.GetItemListInTrack(k, i) or [])]


def camada_letterings(t, mp, lista, template, centro_y=None):
    """Coloca letterings [(TEXTO, inicio_s, dur_s[, template[, centro_y]]), ...] em camadas logo ACIMA dos takes (sem compound).
    centro_y por item: 0.5 = centro (lettering sobre b-roll, sem rosto); 1-1290/1920 = abaixo do queixo (sobre a pessoa).
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
        props = {k: x.GetProperty(k) for k in ("ZoomX", "ZoomY", "Pan", "Tilt")}   # reenquadramento do rosto
        takes.append((m, x.GetStart(), round(x.GetLeftOffset() * r_), x.GetDuration(), props, r_))
    velhos = t.GetItemListInTrack("video", 1) or []
    if velhos: t.DeleteClips(velhos, False)
    padrao = 150  # duração padrão dos Fusion Titles do pacote (5 s a 30 fps); conferido ao inserir
    camadas = []
    for item in sorted(lista, key=lambda x: x[1]):
        ini_f = S + round(item[1] * F)
        for c in camadas:
            if ini_f >= c[-1][4] + 1: c.append((*item[:3], item[3] if len(item) > 3 else template, ini_f + padrao, item[4] if len(item) > 4 else centro_y)); break
        else: camadas.append([(*item[:3], item[3] if len(item) > 3 else template, ini_f + padrao, item[4] if len(item) > 4 else centro_y)])
    ocup = [(x[1], x[1] + padrao / F) for x in lista]   # o bloco inteiro do título (fade no fim do bloco)
    for c in reversed(camadas):           # a primeira camada termina mais perto dos takes
        travar = [(k, i) for k in ("audio", "subtitle") for i in range(1, t.GetTrackCount(k) + 1)] + \
                 [("video", i) for i in range(2, t.GetTrackCount("video") + 1)]
        for k, i in travar: t.SetTrackLock(k, i, True)
        soltas = [(k, i) for k, i in travar if not t.GetIsTrackLocked(k, i)]
        if soltas: raise RuntimeError(f"trilhas não travaram {soltas}: o ripple do título ia empurrar áudio/legenda")
        antes = _assinatura(t)
        try:
            for texto, ini, dur, tpl, _, cy in c:
                _inserir_titulo_v1(t, tpl, texto, S + max(3, round(ini * F)), round(dur * F), cy)   # quadro 0 falha no fade
        finally:
            for k, i in travar: t.SetTrackLock(k, i, False)
        if _assinatura(t) != antes: raise RuntimeError("áudio/legenda mudaram ao inserir título (ripple): desfazer e refazer")
        t.AddTrack("video", {"index": 1})
    # endFrame do AppendToTimeline é EXCLUSIVO: com '- 1' cada take voltava 1 quadro menor (quadro preto entre takes).
    for mpi, st, lo, dur, props, r_ in takes:
        x = mp.AppendToTimeline([{"mediaPoolItem": mpi, "startFrame": lo, "endFrame": lo + math.ceil(dur * r_), "mediaType": 1,
                                  "trackIndex": 1, "recordFrame": st}])
        if x:
            for k, v in props.items():
                if v is not None: x[0].SetProperty(k, v)
    return ocup


def colocar_motions(p, t, mp, lista, nome_trilha="MOTIONS"):
    """Motions do HyperFrames (MOV ProRes 4444 com alfa, 1080x1920, fps da timeline) numa trilha PRÓPRIA acima de tudo.
    lista = [(arquivo, segundo_na_timeline), ...]. Antes duplica a timeline como backup."""
    t.DuplicateTimeline(f"{t.GetName()} (backup antes motions)"); p.SetCurrentTimeline(t)
    t.AddTrack("video"); v = t.GetTrackCount("video"); t.SetTrackName("video", v, nome_trilha)
    S, F = t.GetStartFrame(), fps_tl(t); out = []
    for arq, seg in lista:
        it = importar(mp, arq, "MOTIONS")
        x = mp.AppendToTimeline([{"mediaPoolItem": it, "mediaType": 1, "trackIndex": v, "recordFrame": S + round(seg * F)}])
        if not x: raise RuntimeError(f"motion não entrou: {arq}")
        out.append(x[0])
    return out


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


def masterizar(arq, lufs=-14, tp=-1.5, fade_s=0.4):
    """Áudio final do MP4: loudnorm em 2 passagens (-14 LUFS, pico -1.5 dBTP) + fade curto no fim; vídeo copiado.
    Talking head saiu do DaVinci com pico de +4,7 dBFS e loudness de -12,5 a -17,8: masterizar SEMPRE."""
    import json
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", arq],
                               capture_output=True, text=True).stdout)
    fade = f"afade=t=out:st={max(0, dur - fade_s):.3f}:d={fade_s}"
    med = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", arq, "-af", f"{fade},loudnorm=I={lufs}:TP={tp}:LRA=11:print_format=json",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    m = json.loads(med[med.rindex("{"):med.rindex("}") + 1])
    ln = (f"loudnorm=I={lufs}:TP={tp}:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
          f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    tmp = arq[:-4] + "_tmp.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", arq, "-c:v", "copy", "-af", f"{fade},{ln},aresample=48000", "-c:a", "aac", "-b:a", "320k",
                    "-movflags", "+faststart", tmp], check=True)
    os.replace(tmp, arq)
    a = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", arq, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    i = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", a)[-1]); pk = float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", a)[-1])
    return i, pk


def renderizar(p, pasta, nome, w=1080, h=1920, legenda_gravada=True, ate_fim_do_video=True, master=True):
    """ate_fim_do_video: corta no último quadro de vídeo (música que passa do fim dava quadros pretos no final).
    master: masteriza o áudio do MP4 (masterizar)."""
    for j in p.GetRenderJobList(): p.DeleteRenderJob(j["JobId"])
    p.SetCurrentRenderFormatAndCodec("mp4", "H264")
    # ExportVideo/ExportAudio SEMPRE explícitos: renders de quadro parado (capa, conferência) deixam ExportAudio=False
    # gravado no projeto e o MP4 sairia mudo.
    cfg = {"SelectAllFrames": True, "TargetDir": pasta, "CustomName": nome, "FormatWidth": w, "FormatHeight": h,
           "ExportVideo": True, "ExportAudio": True, "AudioCodec": "aac", "AudioSampleRate": 48000}
    if ate_fim_do_video:
        t = p.GetCurrentTimeline()
        fim = max((x.GetEnd() for k in range(1, t.GetTrackCount("video") + 1) for x in (t.GetItemListInTrack("video", k) or [])), default=None)
        if fim and fim < t.GetEndFrame():
            cfg.update({"SelectAllFrames": False, "MarkIn": t.GetStartFrame(), "MarkOut": fim - 1})
    if legenda_gravada: cfg.update({"ExportSubtitle": True, "SubtitleFormat": "BurnIn"})
    p.SetRenderSettings(cfg)
    jid = p.AddRenderJob(); p.StartRendering(jid)
    while p.IsRenderingInProgress(): time.sleep(2)
    st = p.GetRenderJobStatus(jid); arq = os.path.join(pasta, nome + ".mp4")
    tem_audio = "audio" in subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type", "-of", "csv=p=0", arq],
                                          capture_output=True, text=True).stdout
    if not tem_audio: raise RuntimeError(f"render saiu SEM ÁUDIO: {arq}")
    if master:
        i, pk = masterizar(arq)
        if abs(i + 14) > 0.5 or pk > -1.0: raise RuntimeError(f"master fora do alvo: {i} LUFS, pico {pk}")
    return arq, st.get("JobStatus")


def salvar(r=None):
    (r or conectar(False)).GetProjectManager().SaveProject()


# Organização do Media Pool (regra do usuário): pastas fixas na raiz e, com mais de um vídeo no mesmo
# projeto, uma subpasta por vídeo numerada (01 - Assunto, 02 - Assunto...) dentro de cada uma.
PASTAS_PROJETO = ("Timelines", "Footages", "BRoll", "SFX", "Musicas", "Motions", "Legendas")
TIPO_POR_SUBPASTA = {"gravacao": "Footages", "narracoes": "Footages", "brolls": "BRoll", "sfx": "SFX",
                     "musica": "Musicas", "motions": "Motions", "legendas": "Legendas"}


def _sub(mp, pai, nome):
    for f in pai.GetSubFolderList() or []:
        if f.GetName() == nome: return f
    return mp.AddSubFolder(pai, nome)


def _tipo_do_arquivo(arq):
    ext = os.path.splitext(arq)[1].lower(); partes = {x.lower() for x in arq.split(os.sep)}
    if "motions" in partes or "renders" in partes: return "Motions"
    if "sfx" in partes or "biblioteca_sfx" in partes: return "SFX"
    if "legendas" in partes or "legenda_baixa" in partes: return "Legendas"
    if partes & {"brolls", "ia_higgsfield", "ia_kling_bruto", "youtube_bruto"}: return "BRoll"
    if ext in (".srt", ".vtt"): return "Legendas"
    if ext in (".wav", ".mp3", ".aif", ".aiff", ".m4a"): return "Musicas"
    return "Footages"


def organizar(p, mp, videos):
    """Arruma o Media Pool em Timelines / Footages / BRoll / SFX / Musicas / Motions / Legendas.
    videos = [(pasta_do_video_no_disco, prefixo_das_timelines), ...] na ordem 01, 02, 03...
    Com 1 vídeo os itens ficam direto na pasta do tipo; com mais de um, em '<NN> - <Assunto>' dentro dela.
    O tipo vem da subpasta do arquivo no disco (gravacao, brolls, sfx, musica, motions, legendas);
    timelines pela pasta Timelines pelo prefixo do nome. Arquivo de fora das pastas dos vídeos vai para Footages/Originais."""
    root = mp.GetRootFolder(); tipos = {n: _sub(mp, root, n) for n in PASTAS_PROJETO}
    varios = len(videos) > 1
    rot = [f"{i + 1:02d} - {os.path.basename(os.path.normpath(d)).rsplit(' - ', 1)[0]}" for i, (d, _) in enumerate(videos)]
    destino = lambda tipo, k: _sub(mp, tipos[tipo], rot[k]) if (varios and k is not None) else tipos[tipo]
    def todas(f):
        for c in f.GetClipList() or []: yield c
        for s in f.GetSubFolderList() or []: yield from todas(s)
    mover = {}
    for c in list(todas(root)):
        if c.GetClipProperty("Type") == "Timeline":
            k = next((i for i, (_, pre) in enumerate(videos) if c.GetName().startswith(pre)), None)
            alvo = destino("Timelines", k)
        else:
            arq = c.GetClipProperty("File Path") or ""
            k = next((i for i, (d, _) in enumerate(videos) if arq.startswith(os.path.normpath(d) + os.sep)), None)
            if k is None:
                alvo = _sub(mp, tipos["Footages"], "Originais") if _tipo_do_arquivo(arq) == "Footages" else tipos[_tipo_do_arquivo(arq)]
            else:
                sub = os.path.relpath(arq, videos[k][0]).split(os.sep)[0]
                alvo = destino(TIPO_POR_SUBPASTA.get(sub, _tipo_do_arquivo(arq)), k)
        mover.setdefault(alvo.GetUniqueId(), (alvo, []))[1].append(c)
    for alvo, clips in mover.values(): mp.MoveClips(clips, alvo)
    # apaga as pastas antigas que ficaram vazias (NARRACAO, MUSICA, BROLLS, GRAVACOES...)
    vazias = [f for f in root.GetSubFolderList() if f.GetName() not in PASTAS_PROJETO and not list(todas(f))]
    if vazias: mp.DeleteFolders(vazias)
    mp.SetCurrentFolder(root)
    return {f.GetName(): sum(1 for _ in todas(f)) for f in root.GetSubFolderList()}


# Rosto (regras 1e e 1l do SKILL.md): medir onde está e reenquadrar com zoom + Pan/Tilt, sem nada por cima.
QUEIXO_MAX = 1140     # em 1080x1920: queixo acima da faixa da legenda


def medir_rosto(arquivo, passo_s=1.0, w=1080, h=1920):
    """Mediana do rosto (cx, cy, lado do quadrado do detector) em pixels do quadro w x h, sem zoom."""
    import cv2, statistics as st
    cas = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    cap = cv2.VideoCapture(arquivo); fps = cap.get(cv2.CAP_PROP_FPS) or 30; n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); bx = []
    for fr in range(0, n, max(1, int(fps * passo_s))):
        cap.set(cv2.CAP_PROP_POS_FRAMES, fr); ok, img = cap.read()
        if not ok: continue
        g = cv2.cvtColor(cv2.resize(img, (w, h)), cv2.COLOR_BGR2GRAY)
        fs = cas.detectMultiScale(g, 1.1, 8, minSize=(int(w * 0.2),) * 2)
        if len(fs): bx.append(max(fs, key=lambda b: b[2] * b[3]))
    if not bx: return None
    return {"cx": st.median(b[0] + b[2] / 2 for b in bx), "cy": st.median(b[1] + b[3] / 2 for b in bx), "lado": st.median(b[2] for b in bx)}


def enquadrar(face, w=1080, h=1920, tol_x=40):
    """(zoom, pan, tilt) com o MÍNIMO de zoom (regra do usuário): só sobe a imagem até o queixo ficar acima de
    QUEIXO_MAX e só centraliza na horizontal se o rosto estiver a mais de tol_x px do centro. Sem borda preta.
    Sem punch-in: o mesmo valor no vídeo todo. Tilt positivo sobe a imagem."""
    z = 1.0
    while True:
        fx = w / 2 + (face["cx"] - w / 2) * z; fy = h / 2 + (face["cy"] - h / 2) * z
        queixo = fy + 0.6 * face["lado"] * z
        dy = min(0.0, QUEIXO_MAX - queixo)                       # só sobe, e só o necessário
        pan = 0.0 if abs(w / 2 - fx) <= tol_x else (w / 2 - fx)
        if abs(pan) <= w / 2 * (z - 1) + 0.5 and abs(dy) <= h / 2 * (z - 1) + 0.5: break
        z += 0.005
    return round(z, 3), round(pan), round(-dy)


def aplicar_enquadramento(t, enq, trilha=1):
    """Mesmo enquadramento (zoom, pan, tilt) em todos os pedaços da trilha (sem punch-in)."""
    z, pan, tilt = enq
    for x in t.GetItemListInTrack("video", trilha) or []:
        for k, v in (("ZoomX", z), ("ZoomY", z), ("Pan", pan), ("Tilt", tilt)): x.SetProperty(k, v)


def trocar_pela_copia(p, mp, t):
    """RECEITA QUE FUNCIONA (12/10/2026) para o lettering editável entrar ANIMADO: título inserido/ajustado pela API
    congela (render seco) na timeline em que a composição do Fusion foi aberta (GetFusionCompByIndex). A CÓPIA anima,
    desde que: (1) a original FIQUE no projeto (apagar a original fazia a cópia travar) e (2) NINGUÉM abra a
    composição dos títulos na cópia (nada de GetFusionCompByIndex/_textos/ajustar_titulo/checar_fades antigo).
    A cópia já leva os fades do bloco (conferido). Devolve a cópia com o nome original."""
    nome, vi = t.GetName(), t.GetVoiceIsolationState(1)
    t.SetName(nome + " (titulos via API)"); d = t.DuplicateTimeline(nome); p.SetCurrentTimeline(d)
    if vi and vi.get("isEnabled") and not d.GetVoiceIsolationState(1).get("isEnabled"): d.SetVoiceIsolationState(1, vi)
    for j in range(2, d.GetTrackCount("video") + 1):          # título = item sem MediaPoolItem (não abre a composição)
        for x in d.GetItemListInTrack("video", j) or []:
            if x.GetMediaPoolItem() is None and not (x.GetFades() or {}).get("FadeOut"): x.SetFades({"FadeOut": FADE_LETTERING})
    return d


def inserir_letterings_na_trilha(t, trilha, lista, template, centro_y=None):
    """Insere letterings [(TEXTO, inicio_s, dur_s[, template[, centro_y]]), ...] direto na trilha `trilha` (acima da V1),
    SEM tocar na linha principal (regra 1j). PRÉ-REQUISITO: o destino da timeline (patch no cabeçalho) tem que estar
    nessa trilha (a API não muda o destino; fazer pela interface). Trava todas as outras trilhas durante a inserção
    (o InsertFusionTitleIntoTimeline faz ripple) e confere que nada mais andou. Ordem cronológica."""
    F = fps_tl(t); S = t.GetStartFrame()
    travar = [(k, i) for k in ("audio", "subtitle") for i in range(1, t.GetTrackCount(k) + 1)] + \
             [("video", i) for i in range(1, t.GetTrackCount("video") + 1) if i != trilha]
    for k, i in travar: t.SetTrackLock(k, i, True)
    t.SetTrackLock("video", trilha, False)
    antes = _assinatura(t) + [(k, i, x.GetStart()) for k, i in travar if k == "video" for x in (t.GetItemListInTrack(k, i) or [])]
    try:
        for item in sorted(lista, key=lambda x: x[1]):
            texto, ini, dur = item[:3]; tpl = item[3] if len(item) > 3 else template; cy = item[4] if len(item) > 4 else centro_y
            f = S + max(3, round(ini * F)); _ir(t, f); time.sleep(0.6); _ir(t, f)
            n0 = len(t.GetItemListInTrack("video", trilha) or [])
            if not t.InsertFusionTitleIntoTimeline(tpl): raise RuntimeError(f"título não entrou ({tpl}): o destino está na trilha {trilha}?")
            novos = [x for x in t.GetItemListInTrack("video", trilha) if x.GetStart() == f]
            if len(t.GetItemListInTrack("video", trilha)) != n0 + 1 or not novos:
                raise RuntimeError(f"título não caiu na trilha {trilha} em {f}: conferir o destino da timeline")
            ajustar_titulo(novos[0], texto, dur_f=round(dur * F), centro_y=cy)
    finally:
        for k, i in travar: t.SetTrackLock(k, i, False)
    depois = _assinatura(t) + [(k, i, x.GetStart()) for k, i in travar if k == "video" for x in (t.GetItemListInTrack(k, i) or [])]
    if depois != antes: raise RuntimeError("outra trilha mudou durante a inserção (ripple): conferir")

MODELO_LEGENDA = "MODELO GAB USA"
DRT_MODELO = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "davinci", "modelo_gab_usa.drt")


def timeline_do_modelo(p, mp, nome, w=None, h=None, fps=None, modelo=MODELO_LEGENDA, drt=DRT_MODELO):
    """Timeline nova JÁ com o estilo de legenda (preset GAB USA) sem clicar em nada: a API não aplica estilo de
    legenda, mas ele fica gravado na trilha e vai junto quando a timeline é duplicada ou importada (.drt).
    Usa a timeline-modelo do projeto; se não existir, importa assets/davinci/modelo_gab_usa.drt."""
    tls = {p.GetTimelineByIndex(i).GetName(): p.GetTimelineByIndex(i) for i in range(1, p.GetTimelineCount() + 1)}
    m = tls.get(modelo)
    if not m and os.path.exists(drt):
        m = mp.ImportTimelineFromFile(drt, {"timelineName": modelo})
        if m: m.SetName(modelo)
    if not m:
        return None
    p.SetCurrentTimeline(m)
    t = m.DuplicateTimeline(nome)
    if not t:
        return None
    p.SetCurrentTimeline(t)
    for k in ("video", "audio", "subtitle"):
        for n in range(1, t.GetTrackCount(k) + 1):
            its = t.GetItemListInTrack(k, n) or []
            if its: t.DeleteClips(its)
    t.SetSetting("useCustomSettings", "1")
    for k, v in (("timelineResolutionWidth", w), ("timelineResolutionHeight", h), ("timelineFrameRate", fps)):
        if v: t.SetSetting(k, str(v))
    return t


def mover_e_relinkar(mp, origem, destino):
    """Move/renomeia um arquivo e, se ele já estiver no Media Pool (o usuário pode ter usado direto de ~/Downloads),
    faz ReplaceClip para o caminho novo, sem ficar offline na timeline (bug de 12/10/2026)."""
    import shutil
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    shutil.move(origem, destino)
    alvo = os.path.realpath(origem); n = 0
    def walk(f):
        for c in f.GetClipList() or []: yield c
        for sub in f.GetSubFolderList() or []: yield from walk(sub)
    for c in walk(mp.GetRootFolder()):
        fp = c.GetClipProperty("File Path") or ""
        if fp and os.path.realpath(fp) == alvo:
            n += bool(c.ReplaceClip(destino))
    return n

def renderizar_trecho(p, pasta, nome, ini, fim, so_v1=True):
    """Exporta só um trecho (segundos da timeline), por padrão só a V1 (sem b-roll, motions e legenda), para mandar
    ao HyperFrames (legenda atrás da pessoa, pacote de entrevista). Religa tudo que desligou, mesmo se falhar."""
    t = p.GetCurrentTimeline(); F = fps_tl(t); S = t.GetStartFrame(); desligadas = []
    try:
        if so_v1:
            for tipo in ("video", "subtitle"):
                for k in range(1, t.GetTrackCount(tipo) + 1):
                    if (tipo, k) != ("video", 1) and t.GetIsTrackEnabled(tipo, k):
                        t.SetTrackEnable(tipo, k, False); desligadas.append((tipo, k))
        for j in p.GetRenderJobList(): p.DeleteRenderJob(j["JobId"])
        os.makedirs(pasta, exist_ok=True); p.SetCurrentRenderFormatAndCodec("mp4", "H264")
        p.SetRenderSettings({"SelectAllFrames": False, "MarkIn": S + round(ini * F), "MarkOut": S + round(fim * F) - 1,
                             "TargetDir": pasta, "CustomName": nome, "ExportVideo": True, "ExportAudio": True,
                             "FormatWidth": int(t.GetSetting("timelineResolutionWidth")), "FormatHeight": int(t.GetSetting("timelineResolutionHeight"))})
        jid = p.AddRenderJob(); p.StartRendering(jid)
        while p.IsRenderingInProgress(): time.sleep(1)
        return os.path.join(pasta, nome + ".mp4")
    finally:
        for tipo, k in desligadas: t.SetTrackEnable(tipo, k, True)


def timeline_com_letterings(p, mp, nome, lista, w=1080, h=1920, fps=30):
    """Timeline NOVA (do modelo GAB USA) com os letterings EDITÁVEIS (Fusion Title do pacote) já animados, sem UI.
    Por quê (12/10/2026): título inserido numa timeline que já tem mídia entra SECO (sem animação) e a API só insere na V1;
    numa timeline vazia ele anima. Então: insere os títulos primeiro na V1 vazia, em ordem, e cria uma trilha de vídeo na
    posição 1 (os títulos sobem para a V2 = LETTERING). Depois montar takes na V1, motions acima, áudio e legenda.
    lista = [(TEXTO, inicio_s, template[, centro_y]), ...]."""
    t = timeline_do_modelo(p, mp, nome, w, h, fps) or criar_timeline(p, mp, nome, w, h, fps)
    p.SetCurrentTimeline(t); S = t.GetStartFrame(); F = fps_tl(t)
    # o modelo traz uma V2 "BROLL" DESLIGADA (e a API não religa): apagar toda trilha de vídeo além da V1 antes
    for v in range(t.GetTrackCount("video"), 1, -1): t.DeleteTrack("video", v)
    for item in sorted(lista, key=lambda x: x[1]):
        texto, ini, tpl = item[:3]; cy = item[3] if len(item) > 3 else None
        f = S + max(0, round(ini * F)); _ir(t, f); time.sleep(0.6); _ir(t, f)
        it = t.InsertFusionTitleIntoTimeline(tpl)
        if not it or it.GetStart() != f: raise RuntimeError(f"título {texto!r} não caiu em {ini}s")
        ajustar_titulo(it, texto, centro_y=cy)
    t.AddTrack("video", {"index": 1}); t.SetTrackName("video", 2, "LETTERING")
    while t.GetTrackCount("audio") < 3: t.AddTrack("audio", "stereo")
    return t


def conferir_entrada_titulos(p, t, pasta="/tmp/ogab_titulos", quadro_ini=1, quadro_fim=45):
    """Prova que cada lettering (Fusion Title acima da V1) ENTRA ANIMADO: renderiza o começo de cada título e conta
    os pixels de texto (quase brancos, faixa central) no quadro 1 e no 45. Animado = quadro 1 com bem menos texto que
    o 45 (o preset começa invisível/borrado/parcial). Seco = os dois iguais. Devolve [(texto, inicio_s, razao, ok)]."""
    import numpy as np
    from PIL import Image
    os.makedirs(pasta, exist_ok=True); S, F = t.GetStartFrame(), fps_tl(t); out = []
    # só os títulos no render (fundo preto): desliga os outros clipes de vídeo e religa no fim (fundo claro enganava a conta)
    outros = [x for v in range(1, t.GetTrackCount("video") + 1) for x in (t.GetItemListInTrack("video", v) or [])
              if x.GetMediaPoolItem() is not None and x.GetClipEnabled()]
    for x in outros: x.SetClipEnabled(False)
    try:
        out = _conferir_titulos(p, t, pasta, quadro_ini, quadro_fim, S, F)
    finally:
        for x in outros: x.SetClipEnabled(True)
    if any(x.GetClipEnabled() is False for x in outros): raise RuntimeError("clipe não religou depois da conferência")
    return out


def _conferir_titulos(p, t, pasta, quadro_ini, quadro_fim, S, F):
    import numpy as np
    from PIL import Image
    out = []
    for v in range(2, t.GetTrackCount("video") + 1):
        for it in t.GetItemListInTrack("video", v) or []:
            if it.GetMediaPoolItem() is not None: continue      # só títulos; NÃO abrir a composição (congela)
            txt = it.GetName(); nome = f"tit_{it.GetStart()}"
            for j in p.GetRenderJobList(): p.DeleteRenderJob(j["JobId"])
            p.SetCurrentRenderFormatAndCodec("mp4", "H264")
            p.SetRenderSettings({"SelectAllFrames": False, "MarkIn": it.GetStart(), "MarkOut": it.GetStart() + quadro_fim + 2,
                                 "TargetDir": pasta, "CustomName": nome, "ExportVideo": True, "ExportAudio": False,
                                 "ExportSubtitle": False})
            jid = p.AddRenderJob(); p.StartRendering(jid)
            while p.IsRenderingInProgress(): time.sleep(0.5)
            conta = []
            for q in (quadro_ini, quadro_fim):
                png = os.path.join(pasta, f"{nome}_{q}.png")
                subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(pasta, nome + ".mp4"),
                                "-vf", f"select=eq(n\\,{q})", "-frames:v", "1", png], check=True)
                a = np.asarray(Image.open(png).convert("RGB")).astype(int); h = a.shape[0]
                faixa = a[int(h * 0.15):int(h * 0.85)]
                conta.append(int((faixa.max(axis=2) > 200).sum()))
            razao = conta[0] / max(conta[1], 1)
            out.append((txt, round((it.GetStart() - S) / F, 2), round(razao, 2), razao < 0.6))
    return out


def garantir_titulos_animados(p, mp, t, tentativas=3):
    """Regra do usuário (12/10/2026): lettering editável SEMPRE entra animado. Título inserido pela API sai seco na timeline
    onde foi inserido; a cópia (com a original mantida) anima. Faz a cópia, confere a entrada de cada título renderizando,
    e repete se algum continuar seco. Devolve a timeline final (a principal, com o nome original)."""
    for k in range(tentativas):
        t = trocar_pela_copia(p, mp, t)
        res = conferir_entrada_titulos(p, t)
        for r_ in res: print(("animado" if r_[3] else "SECO"), r_)
        if all(r_[3] for r_ in res):
            try: conectar(abrir=False).OpenPage("edit")
            except Exception: pass
            return t
    raise RuntimeError("títulos continuam secos depois de 3 cópias: conferir o pacote/preset")


SFX_DMAX = {"riser_hollow": 2.1, "hud_loading": 0.8, "whoosh_info": 1.1, "ui_select": 0.6, "swish": 0.6, "boom": 3.0,
            "air_swoosh": 1.9, "logo_impact": 6.0, "click": 0.4, "sparkle": 3.0, "pop": 0.3, "typing": 2.7, "stardust": 2.0}


def colocar_plano_sfx(t, mp, pasta_sfx, fim_s, trilhas=(3, 4, 5, 6)):
    """Coloca o desenho de som de `pasta_sfx/plano_sfx.txt` (linhas 'T.TTs Ax nome -NNdB: o que acompanha'), cada som
    na primeira trilha livre (A3..A6), cortado em SFX_DMAX, volume e fade no clipe. Apaga o que havia nessas trilhas."""
    import re as _re
    ev = [(m[2], float(m[1]), int(m[3])) for m in (_re.match(r"\s*([\d.]+)s A\d (\S+) (-?\d+)dB", l)
          for l in open(os.path.join(pasta_sfx, "plano_sfx.txt")).read().splitlines()) if m]
    garantir_trilhas_audio(t, max(trilhas))
    for k in trilhas:
        its = t.GetItemListInTrack("audio", k) or []
        if its: t.DeleteClips(its)
        t.SetTrackName("audio", k, "SFX" if k == trilhas[0] else f"SFX {k - trilhas[0] + 1}")
    S, F = t.GetStartFrame(), fps_tl(t); fim = {k: -1 for k in trilhas}; ok = 0
    for nome, ini, db in sorted(ev, key=lambda e: e[1]):
        it = importar(mp, os.path.join(pasta_sfx, nome + ".wav"), "SFX"); fc = float(it.GetClipProperty("FPS") or F)
        dur = min(SFX_DMAX.get(nome, 2.0), fim_s - ini); rf = S + round(ini * F)
        k = next(k for k in trilhas if fim[k] < rf)
        x = mp.AppendToTimeline([{"mediaPoolItem": it, "mediaType": 2, "trackIndex": k, "recordFrame": rf, "startFrame": 0, "endFrame": round(dur * fc)}])
        if not x: print("SFX falhou:", nome, ini); continue
        x[0].SetProperty("AudioVolume", db); x[0].SetFades({"FadeOut": min(8, round(dur * F / 4))}); fim[k] = x[0].GetEnd(); ok += 1
    return ok, len(ev)
