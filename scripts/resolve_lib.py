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


def aplicar_grade(r, t, drx, trilha=1):
    """Aplica o PowerGrade (.drx) em todos os takes da trilha de vídeo (via node graph de cada item).
    Timeline.ApplyGradeFromDRX não funciona pela API; usar TimelineItem.GetNodeGraph().ApplyGradeFromDRX(path, 0)."""
    if not os.path.isabs(drx): drx = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), drx)
    r.OpenPage("color"); res = []
    for x in t.GetItemListInTrack("video", trilha) or []:
        g = x.GetNodeGraph(); res.append(bool(g and g.ApplyGradeFromDRX(drx, 0)))
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


def lettering(t, template, texto, inicio=0.0, dur=None, faixa_video=2):
    """Insere um título animado do pacote (Fusion Title) no playhead e troca o texto (ferramenta 'Template')."""
    S, F = t.GetStartFrame(), fps_tl(t)
    while t.GetTrackCount("video") < faixa_video: t.AddTrack("video")
    f = S + round(inicio * F)
    h, rem = divmod(f, int(F) * 3600); m, rem = divmod(rem, int(F) * 60); s, q = divmod(rem, int(F))
    t.SetCurrentTimecode(f"{h:02d}:{m:02d}:{s:02d}:{q:02d}")
    it = t.InsertFusionTitleIntoTimeline(template)
    if not it: raise RuntimeError(f"template '{template}' não encontrado (pacote instalado? Resolve reiniciado?)")
    comp = it.GetFusionCompByIndex(1)
    tool = comp.FindTool("Template") if comp else None
    if tool: tool.SetInput("StyledText", texto)
    return it


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
