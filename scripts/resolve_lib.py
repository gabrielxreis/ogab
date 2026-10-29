"""Funções para montar o vídeo no DaVinci Resolve Studio pela scripting API.

Uso típico (python3 com as variáveis de ambiente do Resolve, ver ambiente()):
    from resolve_lib import *
    p, mp = criar_projeto("Assunto - Empresa", 1080, 1920, 30)
    t = criar_timeline(p, mp, "Reels 60s", pasta=".../Assunto - Empresa")   # exige o menu_escolha.json
    colocar_narracao(t, mp, ".../narracoes/narracao.wav", db=5)
    colocar_musica(t, mp, ".../musica/faixa.wav", inicio_faixa=64.0, dur=48.4, db=-10, fade=2.5)
    montar_takes(t, mp, [(".../brolls/take_01.mp4", 0.0), (".../brolls/take_02.mp4", 5.1), ...], fim=48.4)
    colocar_legendas(t, mp, ".../legendas/legendas_v1.srt")
    lettering(t, "@gabrielxreis_ Cinematic", "TEXTO DO GANCHO", inicio=0.0, dur=2.5)
    renderizar(p, ".../videos", "Assunto - Empresa", 1080, 1920)
"""
import json, math, os, re, subprocess, sys, time

RESOLVE_API = "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting"
RESOLVE_LIB = "/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/fusionscript.so"


def ambiente():
    os.environ.setdefault("RESOLVE_SCRIPT_API", RESOLVE_API)
    os.environ.setdefault("RESOLVE_SCRIPT_LIB", RESOLVE_LIB)
    sys.path.append(os.path.join(RESOLVE_API, "Modules"))


def set_fades(item, fades):
    """TimelineItem.SetFades só existe no DaVinci 21.1+ (relato 15/10/2026, Windows com 21.0): sem ele, avisa e segue."""
    f = getattr(item, "SetFades", None)
    if f is None:
        print("AVISO: DaVinci < 21.1 não tem SetFades pela API; fazer o fade à mão (ou atualizar o DaVinci)")
        return False
    return f(fades)


def get_fades(item):
    f = getattr(item, "GetFades", None)
    return (f() if f else None) or {}


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


def fps_padrao():
    """fps do usuário (config.regras.fps). Regra do usuário (29/10/2026): DaVinci SEMPRE em 24 fps."""
    try:
        cfg = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json"), encoding="utf-8"))
        return int(cfg.get("regras", {}).get("fps") or 24)
    except Exception:
        return 24


def criar_projeto(nome, w=1080, h=1920, fps=None):
    """Cria (ou abre) o projeto 'Assunto - Empresa'. IMPORTANTE: fps de timeline E de playback
    são gravados ANTES de qualquer timeline; depois a API não muda o playback (áudio engasga).
    fps padrão = config.regras.fps (24, regra do usuário de 29/10/2026)."""
    fps = fps or fps_padrao()
    r = conectar(); pm = r.GetProjectManager()
    salvar(r)   # CreateProject troca o projeto atual e DESCARTA o que não foi salvo (armadilha da API, MCP samuelgursky)
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


def criar_timeline(p, mp, nome, w=None, h=None, fps=None, pasta=None, sem_menu=None):
    """Timeline NOVA. Portão do menu (regra do usuário, 23/10/2026): exige o menu_escolha.json da `pasta` do vídeo,
    ou `sem_menu="motivo"` (pessoa não quer menu, variação de vídeo já aprovado). Ver scripts/portao_menu.py."""
    import portao_menu; portao_menu.checar(pasta, sem_menu)
    t = mp.CreateEmptyTimeline(nome); p.SetCurrentTimeline(t)
    if w and h:
        t.SetSetting("useCustomSettings", "1")
        if fps: t.SetSetting("timelineFrameRate", str(fps))
        t.SetSetting("timelineResolutionWidth", str(w)); t.SetSetting("timelineResolutionHeight", str(h))
    while t.GetTrackCount("audio") < 3: t.AddTrack("audio")   # A1 narração, A2 música, A3 efeitos
    # Já na criação: playback fps tem que ser igual ao da timeline (senão o áudio picota).
    if not checar_playback(p):
        p.SetSetting("timelinePlaybackFrameRate", str(fps or p.GetSetting("timelineFrameRate")))
        if not checar_playback(p):   # só avisar deixava seguir com o áudio picotando (relato Windows, 26/10/2026)
            raise RuntimeError("PLAYBACK_DIFERENTE: o DaVinci não aceitou o playback fps pela API. Pedir ao usuário: "
                               "File > Project Settings > Master Settings > Playback frame rate = fps da timeline > Save "
                               "(Render Cache fica em None); a timeline já foi criada, conferir com checar_playback(p) e seguir")
    return t


def _no_pool(mp, caminho):
    """Item do Media Pool que já aponta para este arquivo (procura em todas as pastas), ou None."""
    alvo = os.path.normcase(os.path.abspath(caminho)); pilha = [mp.GetRootFolder()]
    while pilha:
        f = pilha.pop()
        for c in f.GetClipList() or []:
            fp = c.GetClipProperty("File Path") or ""
            if fp and os.path.normcase(os.path.abspath(fp)) == alvo: return c
        pilha.extend(f.GetSubFolderList() or [])
    return None


def importar(mp, caminho, bin_nome, permitir_render=False):
    if _gerado_pelo_gab(caminho): proibido_render(f"mídia renderizada pelo Gab: {os.path.basename(caminho)}", permitir_render)
    if bin_nome.upper() in ("BROLLS", "BROLL", "FOOTAGES", "TAKES"): checar_take_original(caminho, permitir_render)
    ja = _no_pool(mp, caminho)   # ImportMedia sempre cria item novo: reimportar duplicava o clipe (relato 16/10/2026)
    if ja: return ja
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


def colar_motions(t, mp, max_vao=0.6):
    """Motions em sequência ficam COLADOS (regra do usuário, 12/10/2026: "muitos ficam com espaço pequeno entre um e outro
    e aí entra o frame debaixo sem necessidade"). Junta todos os itens de motion (File Path com /motions/) de todas as
    trilhas de vídeo acima da V1; se o próximo começa até `max_vao` s depois do fim do anterior, ele é recolocado no fim
    do anterior (mesma trilha), puxando o início e, se a mídia tiver sobra, o fim. Devolve [(nome, vão_s)] corrigidos.
    Complemento obrigatório: motion que entra logo depois de outro motion (ou por cima de um motion) é renderizado com
    bgfade=False, senão o fade de 0,25 s do fundo mostra o take de baixo."""
    pagina_edit()   # DeleteClips só funciona na página Edit
    S, F = t.GetStartFrame(), fps_tl(t); feitos = []
    while True:
        its = []
        for k in range(2, t.GetTrackCount("video") + 1):
            for x in t.GetItemListInTrack("video", k) or []:
                mpi = x.GetMediaPoolItem()
                if mpi and "/motions/" in (mpi.GetClipProperty("File Path") or ""): its.append((x.GetStart(), x.GetEnd(), k, x, mpi))
        its.sort(key=lambda e: e[0]); alvo = None
        for a, b in zip(its, its[1:]):
            vao = b[0] - a[1]
            if 0 < vao <= round(max_vao * F): alvo = (a, b, vao); break
        if not alvo: return feitos
        a, b, vao = alvo
        # 1º: esticar o ANTERIOR até o próximo (se a mídia dele tiver sobra): o próximo fica no tempo da fala.
        # Puxar o próximo para trás acumulava atraso (13/10/2026: 10 motions colados ficaram 5 quadros adiantados).
        xa, mpa, ka = a[3], a[4], a[2]
        la = xa.GetLeftOffset(); da = xa.GetDuration(); ta = int(float(mpa.GetClipProperty("Frames")))
        if la + da + vao <= ta:
            rec = xa.GetStart(); t.DeleteClips([xa], False)
            mp.AppendToTimeline([{"mediaPoolItem": mpa, "mediaType": 1, "trackIndex": ka, "recordFrame": rec,
                                  "startFrame": la, "endFrame": la + da + vao}])
            feitos.append((xa.GetName(), round(vao / F, 2))); continue
        x, mpi, k = b[3], b[4], b[2]
        left = x.GetLeftOffset(); dur = x.GetDuration(); total = int(float(mpi.GetClipProperty("Frames")))
        ini = max(0, left - vao); fim = min(total, ini + dur + vao)   # endFrame é exclusivo
        t.DeleteClips([x], False)
        mp.AppendToTimeline([{"mediaPoolItem": mpi, "mediaType": 1, "trackIndex": k, "recordFrame": a[1], "startFrame": ini, "endFrame": fim}])
        feitos.append((x.GetName(), round(vao / F, 2)))


def colocar_musica(t, mp, wav_bruto, inicio_faixa=0.0, dur=None, db=-10, fade_in=0.5, fade_out=2.5):
    """Música BRUTA na A2 (regra do usuário, 11/10/2026): o WAV original entra inteiro no Media Pool e o corte
    é feito no DaVinci (ponto de entrada = inicio_faixa, duração = dur ou a timeline toda), com fade no clipe.
    Nada de cortar/renderizar o áudio antes: assim o usuário consegue arrastar e reajustar na timeline."""
    garantir_trilhas_audio(t, 2)
    ocupado = t.GetItemListInTrack("audio", 2) or []
    if ocupado:   # AppendToTimeline não sobrescreve: com a A2 ocupada no mesmo ponto o clipe novo some sem erro
        raise RuntimeError(f"A2 já tem {len(ocupado)} clipe(s) ({ocupado[0].GetName()}): apagar/mover a música antiga antes")
    it = importar(mp, wav_bruto, "MUSICA")
    fps_c = float(it.GetClipProperty("FPS") or fps_tl(t))
    if dur is None:
        dur = (t.GetEndFrame() - t.GetStartFrame()) / fps_tl(t)
    ini = int(round(inicio_faixa * fps_c))
    res = mp.AppendToTimeline([{"mediaPoolItem": it, "mediaType": 2, "trackIndex": 2, "recordFrame": t.GetStartFrame(),
                                "startFrame": ini, "endFrame": ini + int(round(dur * fps_c))}])
    if not res:
        raise RuntimeError("a música não entrou na A2 (timeline atual é outra?)")
    x = res[0]
    F = fps_tl(t); fades = {"FadeIn": int(round(fade_in * F)), "FadeOut": int(round(fade_out * F))}
    # DaVinci 21.1: volume e fade do PRÓPRIO clipe pela API (o usuário arrasta as alças depois). Conferir lendo de volta.
    x.SetProperties({"AudioVolume": float(db)}) if hasattr(x, "SetProperties") else x.SetProperty("AudioVolume", db)
    set_fades(x, fades)
    lido, vol = get_fades(x) or {}, x.GetProperty("AudioVolume")
    if any(abs(float(lido.get(k, -1)) - v) > 0.5 for k, v in fades.items()) or vol is None or abs(float(vol) - db) > 0.1:
        print(f"AVISO: fade/volume da música não ficaram como pedido (fades {lido}, volume {vol}); ajustar à mão ou DaVinci < 21.1")
    return x


def colocar_sfx(t, mp, lista, db=-6):
    """lista = [(arquivo, segundo_na_timeline), ...] na A3."""
    S, F = t.GetStartFrame(), fps_tl(t); out = []
    for arq, seg in lista:
        it = importar(mp, arq, "SFX")
        x = mp.AppendToTimeline([{"mediaPoolItem": it, "mediaType": 2, "trackIndex": 3, "recordFrame": S + round(seg * F)}])
        if x: x[0].SetProperty("AudioVolume", db); out.append(x[0])
    return out


def _zoom_preencher(it, t):
    """Zoom para o take PREENCHER o quadro (ex.: 16:9 numa timeline 9:16 = 3,16x), no lugar de recortar antes."""
    try:
        ws, hs = [int(v) for v in str(it.GetClipProperty("Resolution")).lower().split("x")]
        wt, ht = int(t.GetSetting("timelineResolutionWidth")), int(t.GetSetting("timelineResolutionHeight"))
        return max(wt / ws, ht / hs) / min(wt / ws, ht / hs)
    except Exception:
        return 1.0



# ---- TRAVA: take nunca re-renderizado (regra do usuário, 13/10/2026: "apaga os takes que você renderizou e coloque
# os originais... garanta que isso nunca mais aconteça"). Vídeo que entra como take tem que ser o arquivo BAIXADO
# (Magnific, Higgsfield, banco, YouTube, câmera). Arquivo feito pelo ffmpeg DESTA máquina (cópia acelerada, cortada,
# re-encodada, foto virada vídeo) carrega no stream de vídeo a tag encoder da libavcodec local: é recusado (remux do yt-dlp passa). Motions (HyperFrames,
# pasta motions/) e áudio não passam por aqui. Só libera com permitir_render=True quando o USUÁRIO pedir.
_LAVF_LOCAL = None
def _lavf_local():
    global _LAVF_LOCAL
    if _LAVF_LOCAL is None:
        out = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True).stdout
        m = __import__("re").search(r"libavcodec\s+(\d+)\.\s*(\d+)\.\s*(\d+)", out)
        _LAVF_LOCAL = f"Lavc{m.group(1)}.{m.group(2)}.{m.group(3)}" if m else ""
    return _LAVF_LOCAL


def take_renderizado_aqui(arq):
    """True se o VÍDEO foi re-encodado pelo ffmpeg desta máquina (tag encoder do stream de vídeo começa com a libavcodec
    local, ex. 'Lavc62.28.102 libx264'). Remux sem re-encode (yt-dlp juntando áudio e vídeo) não tem essa tag e passa."""
    if not str(arq).lower().endswith((".mp4", ".mov", ".m4v", ".mkv", ".webm")): return False
    nota = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format_tags=comment", "-of", "default=nw=1:nk=1", arq],
                          capture_output=True, text=True).stdout.strip()
    if nota == "ogab:download-integral": return False   # baixar_video.py: vídeo inteiro normalizado, sem corte
    tag = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream_tags=encoder", "-of", "default=nw=1:nk=1", arq],
                         capture_output=True, text=True).stdout.strip()
    return bool(_lavf_local()) and tag.startswith(_lavf_local())


def checar_take_original(arq, permitir_render=False):
    if not permitir_render and take_renderizado_aqui(arq):
        raise RuntimeError(f"TAKE RE-RENDERIZADO RECUSADO: {arq}. Use o arquivo original baixado; velocidade/corte/zoom "
                           "se fazem no DaVinci, e só se o usuário pedir (permitir_render=True).")


FOTO_EXT = (".jpg", ".jpeg", ".png", ".webp", ".heic", ".tif", ".tiff")


def proibido_render(o_que, permitir=False):
    """PROIBIDO renderizar mídia para a timeline (regra do usuário, 23/10/2026: "você está renderizando movs em vez de
    encaixar eles na timeline e modificar lá; é proibido até que eu peça"). Foto, texto, legenda, zoom, duração: tudo
    entra como arquivo ORIGINAL e é ajustado NO EDITOR. Só com permitir=True, quando o usuário pediu com essas palavras."""
    if not permitir:
        raise RuntimeError(f"RENDER PROIBIDO ({o_que}): encaixar o arquivo original na timeline e ajustar lá. "
                           "Só renderizar se o usuário pedir explicitamente (permitir=True).")


def _gerado_pelo_gab(caminho):
    n = caminho.replace(os.sep, "/")
    return "/_fotos_mov/" in n or bool(re.search(r"/lb_\d{3}_[^/]*\.mov$", n))


def zoom_leve_foto(item, dur, intensidade=0.05, entrando=True):
    """Keyframes de zoom bem leve na foto inteira (1,00 -> 1,05 ou o contrário), nó Transform "AnimGab" no Fusion."""
    a, b = (1.0, 1.0 + intensidade) if entrando else (1.0 + intensidade, 1.0)
    try:
        animar_clipe(item, [(0.0, {"zoom": a}), (max(dur - 1 / 30, 0.1), {"zoom": b})], fps_arquivo=30)
    except Exception as e:
        print(f"AVISO: zoom leve não entrou em {item.GetName()} ({e}); fazer no Inspector")


def montar_takes(t, mp, takes, fim, zoom=1.0, respeitar_inicio=False, trilha=1, preencher=True, permitir_render=False, foto_zoom=0.05):
    """takes = [(arquivo, inicio_s), ...] ou [(arquivo, inicio_s, entrada_s), ...] em ordem. Cada take vai até o
    início do próximo, sem buraco: encadeia pelo GetEnd() real e usa ceil (fontes 24/25 fps numa timeline 30
    deixariam 1-2 quadros pretos).
    MATERIAL BRUTO (regra do usuário, 13/10/2026): `arquivo` é o vídeo ORIGINAL inteiro (nunca um trecho cortado ou
    renderizado antes) e `entrada_s` é o ponto do arquivo onde o take começa; o corte acontece NA TIMELINE, para o
    usuário conseguir puxar a borda e reajustar no DaVinci. preencher=True aplica o zoom que faz o take ocupar o
    quadro (16:9 em 9:16) em vez de recortar com ffmpeg.
    respeitar_inicio=True: cada take entra NO SEU TEMPO planejado mesmo que o anterior seja curto (o vão fica sob
    um motion de tela cheia). Sem isso, take curto ADIANTA todos os seguintes (bug do lote Calverstone 04-06)."""
    S, F = t.GetStartFrame(), fps_tl(t)
    cur = S + round(takes[0][1] * F); fim_f = S + round(fim * F); itens = []
    for k, tk in enumerate(takes):
        arq, ini = tk[0], tk[1]; entrada = tk[2] if len(tk) > 2 else 0.0
        if respeitar_inicio: cur = max(cur, S + round(ini * F))
        nxt = S + round(takes[k + 1][1] * F) if k + 1 < len(takes) else fim_f
        foto = os.path.splitext(arq)[1].lower() in FOTO_EXT
        if not foto: checar_take_original(arq, permitir_render)
        it = importar(mp, arq, "BROLLS", permitir_render or foto)
        if foto:   # foto ORIGINAL na timeline (sem MOV); a duração é a de still do DaVinci: ajustar NA timeline
            x = (mp.AppendToTimeline([{"mediaPoolItem": it, "mediaType": 1, "trackIndex": trilha, "recordFrame": cur}]) or [None])[0]
            if not x: raise RuntimeError(f"foto não entrou na timeline: {arq}")
            if abs(x.GetEnd() - nxt) > 1:
                print(f"AVISO: {os.path.basename(arq)} entrou com {(x.GetEnd() - x.GetStart()) / F:.1f} s (duração de still do "
                      f"DaVinci); o trecho pede {(nxt - cur) / F:.1f} s: ajustar a borda na timeline")
        else:
            sf = float(it.GetClipProperty("FPS")); mx = int(float(it.GetClipProperty("Frames")))
            e0 = min(int(round(entrada * sf)), mx - 1)
            n = min(mx - e0, math.ceil((nxt - cur) * sf / F))
            x = mp.AppendToTimeline([{"mediaPoolItem": it, "startFrame": e0, "endFrame": e0 + n, "mediaType": 1,
                                      "trackIndex": trilha, "recordFrame": cur}])[0]
        z = zoom * (_zoom_preencher(it, t) if preencher else 1.0)
        if z != 1.0: x.SetProperty("ZoomX", z); x.SetProperty("ZoomY", z)
        if foto and foto_zoom:   # foto nunca parada (regra do usuário, 23/10/2026): zoom leve por keyframe, editável no Fusion
            zoom_leve_foto(x, (x.GetEnd() - x.GetStart()) / F, foto_zoom, entrando=len(itens) % 2 == 0)
        itens.append(x); cur = x.GetEnd()
        if x.GetEnd() < nxt: print(f"AVISO: {os.path.basename(arq)} é curto, sobra {nxt - x.GetEnd()} quadros")
    return itens


def movimento(item, tipo="zoom_in", intensidade=0.08):
    """Movimento leve no take (só se o usuário pediu). A API não cria keyframes; aplica zoom estático
    como base e deixa anotado para animar no Inspector, ou use o preset de lettering/efeito no Edit."""
    z = 1.0 + intensidade
    item.SetProperty("ZoomX", z); item.SetProperty("ZoomY", z)
    return z


LUT_PASTA = ("/Library/Application Support/Blackmagic Design/DaVinci Resolve/LUT" if sys.platform == "darwin" else
             os.path.join(os.environ.get("PROGRAMDATA", r"C:\ProgramData"), "Blackmagic Design", "DaVinci Resolve", "Support", "LUT"))


def aplicar_grade(r, t, drx, drx_iphone=None, trilha=1, lut=None):
    """Aplica o PowerGrade (.drx) em todos os takes da trilha. Takes de iPhone recebem `drx_iphone`
    (PowerGrade combinado: conversor do iPhone ANTES + LUT/look depois), se configurado.
    Sem .drx (o PowerGrade é de cada um e não vai no git): aplica a LUT `lut` (padrão do instalador:
    "LUT DO GAB/LUT DO GAB.cube", relativo à pasta de LUTs do DaVinci) no nó 1 de cada take (Graph.SetLUT).
    Notas da API: Timeline.ApplyGradeFromDRX não funciona; usar TimelineItem.GetNodeGraph().ApplyGradeFromDRX(path, 0).
    Os grafos de grupo (pre/post-clip) NÃO aceitam .drx (só SetLUT), por isso a ordem conversor -> LUT
    precisa vir pronta num único PowerGrade combinado. Sempre pegar o grafo de novo a cada chamada (grafo velho derruba o Resolve)."""
    from midia import eh_iphone
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    absol = lambda p: p if (not p or os.path.isabs(p)) else os.path.join(base, p)
    drx, drx_iphone = absol(drx), absol(drx_iphone)
    usa_lut = not (drx and os.path.exists(drx))
    if usa_lut:
        lut = lut or "LUT DO GAB/LUT DO GAB.cube"
        if not os.path.exists(lut if os.path.isabs(lut) else os.path.join(LUT_PASTA, lut)):
            raise RuntimeError(f"sem PowerGrade e sem a LUT {lut} na pasta de LUTs do DaVinci ({LUT_PASTA}): "
                               "rode o instalador do Gab de novo (ou doctor.py --corrigir)")
        r.GetProjectManager().GetCurrentProject().RefreshLUTList()
    r.OpenPage("color"); res = []
    for x in t.GetItemListInTrack("video", trilha) or []:
        arq = x.GetMediaPoolItem().GetClipProperty("File Path")
        if arq and f"{os.sep}motions{os.sep}" in arq:   # motion não recebe grade (o motion pode estar numa trilha de takes)
            res.append((x.GetName(), "motion (pulado)", True)); continue
        iph = bool(arq and os.path.exists(arq) and eh_iphone(arq))
        if iph and drx_iphone and os.path.exists(drx_iphone):
            res.append((x.GetName(), "iphone", bool(x.GetNodeGraph().ApplyGradeFromDRX(drx_iphone, 0)))); continue
        if iph:
            print(f"AVISO: {x.GetName()} é de iPhone mas não há PowerGrade combinado (cor.drx_iphone); aplicado só o LUT")
        if usa_lut:
            res.append((x.GetName(), "lut", bool(x.GetNodeGraph().SetLUT(1, lut))))
        else:
            res.append((x.GetName(), "iphone" if iph else "padrao", bool(x.GetNodeGraph().ApplyGradeFromDRX(drx, 0))))
    r.OpenPage("edit")
    return res


def colocar_legendas(t, mp, srt, trocar=True, p=None):
    """Importa o SRT na trilha de legenda. Se a trilha já existe, troca só os itens (mantém o preset de estilo)."""
    # DeleteClips/AppendToTimeline só valem na timeline ATUAL: abrir `t` antes de tudo
    pagina_edit()   # DeleteClips só funciona na página Edit
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
    # sem recordFrame o SRT pode cair DEPOIS do fim da timeline (visto no ep. 5 da Lista de Planos: 58 legendas além do último quadro)
    # recordFrame sozinho é ignorado no SRT; com startFrame=0 ele respeita (testado no DaVinci 20/10/2026)
    fim_video = max([x.GetEnd() for k in range(1, t.GetTrackCount("video") + 1) for x in (t.GetItemListInTrack("video", k) or [])] or [t.GetEndFrame()])
    fim_video = max(fim_video, t.GetStartFrame() + 1)   # timeline vazia: fim == início e a legenda certa parecia "depois do fim" (relato ced19e0b5d)
    import time as _t
    for _ in range(4):   # o DaVinci às vezes ignora a posição e solta o SRT depois do fim: apaga e tenta de novo
        try: t.SetCurrentTimecode(_tc(t, t.GetStartFrame()))
        except Exception: pass
        _t.sleep(0.4)
        mp.AppendToTimeline([{"mediaPoolItem": it, "recordFrame": t.GetStartFrame(), "startFrame": 0}])
        prim = (t.GetItemListInTrack("subtitle", 1) or [None])[0]
        if not prim or prim.GetStart() < fim_video: break
        t.DeleteClips(t.GetItemListInTrack("subtitle", 1) or [], False); _t.sleep(0.4)
    prim = (t.GetItemListInTrack("subtitle", 1) or [None])[0]
    if not prim or prim.GetStart() >= fim_video:
        raise RuntimeError(f"a legenda caiu depois do fim de '{t.GetName()}'")
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
    set_fades(item, {"FadeOut": fade_f or FADE_LETTERING})


def checar_fades(t):
    """Confere se TODO lettering (título, item sem MediaPoolItem acima da V1) tem fade out no bloco. NÃO abre a
    composição do Fusion (abrir congela a animação no render)."""
    ruins = [it.GetName() for v in range(2, t.GetTrackCount("video") + 1) for it in (t.GetItemListInTrack("video", v) or [])
             if it.GetMediaPoolItem() is None and not (get_fades(it) or {}).get("FadeOut")]
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
    pagina_edit()   # DeleteClips só funciona na página Edit
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
    p.SetCurrentRenderFormatAndCodec("png", "RGB8")
    p.SetRenderSettings({"SelectAllFrames": False, "MarkIn": q, "MarkOut": q, "TargetDir": pasta, "CustomName": nome,
                         "FormatWidth": w, "FormatHeight": h, "ExportVideo": True, "ExportAudio": False})
    jid = p.AddRenderJob(); p.StartRendering(jid)
    while p.IsRenderingInProgress(): time.sleep(1)
    p.DeleteRenderJob(jid)   # só o job do Gab: a fila do usuário fica como estava
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


def takes_sem_cor(t):
    """Takes LIGADOS (qualquer trilha) que não têm grade: 1 nó só e sem LUT. Motions (.mov, /motions/) ficam de fora."""
    faltam = []
    for k in range(1, t.GetTrackCount("video") + 1):
        for x in t.GetItemListInTrack("video", k) or []:
            m = x.GetMediaPoolItem(); fp = (m.GetClipProperty("File Path") if m else "") or ""
            if m is None:   # título do Fusion (lettering) não é take e não recebe grade (relato 15/10/2026)
                continue
            if not x.GetClipEnabled() or "/motions/" in fp or fp.lower().endswith(".mov"):
                continue
            g = x.GetNodeGraph()
            if g and g.GetNumNodes() <= 1 and not g.GetLUT(1) and not take_pb(x):
                faltam.append(x.GetName())
    return faltam


def take_pb(x):
    """True se o trecho usado do take é P&B (filmagem de arquivo): regra 7b, P&B fica SEM a LUT do Gab (ela deixa sépia)."""
    try:
        import numpy as np
        m = x.GetMediaPoolItem(); arq = m.GetClipProperty("File Path"); sf = float(m.GetClipProperty("FPS"))
        meio = (x.GetSourceStartFrame() + (x.GetSourceEndFrame() - x.GetSourceStartFrame()) / 2) / sf
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{meio:.2f}", "-i", arq, "-frames:v", "1", "-vf", "scale=64:36",
                              "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
        a = np.frombuffer(raw, np.uint8).reshape(-1, 3).astype(float)
        return bool(len(a)) and (np.abs(a[:, 0] - a[:, 1]).mean() + np.abs(a[:, 1] - a[:, 2]).mean()) < 6
    except Exception:
        return False


def renderizar(p, pasta, nome, w=1080, h=1920, legenda_gravada=True, ate_fim_do_video=True, master=True, sem_sfx=False, sem_cor=False):
    """ate_fim_do_video: corta no último quadro de vídeo (música que passa do fim dava quadros pretos no final).
    master: masteriza o áudio do MP4 (masterizar).
    sem_cor: material já finalizado (ex.: vídeo de terceiro dublado), que não leva PowerGrade."""
    _cfg = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json"))) if os.path.exists(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")) else {}
    if (_cfg.get("cor") or {}).get("aplicar_power_grade") and not sem_cor:
        faltam = takes_sem_cor(p.GetCurrentTimeline())   # bug 14/10/2026: 10 takes trocados depois da cor saíram sem grade e o vídeo foi postado
        if faltam:
            raise RuntimeError(f"takes sem cor: {faltam}. Rode aplicar_grade (ou ApplyGradeFromDRX nesses) antes de exportar.")
    if not sem_sfx:   # 15/10/2026: "exporta e agenda" saiu sem SFX e o agendamento foi cancelado ("tinha que fazer o sfx")
        _t = p.GetCurrentTimeline()
        _sfx = [x for k in range(3, _t.GetTrackCount("audio") + 1) for x in (_t.GetItemListInTrack("audio", k) or [])]
        if not _sfx:
            raise RuntimeError("timeline sem SFX (nada da A3 em diante): fazer os efeitos sonoros (sfx.md) antes de exportar; "
                               "só passar sem_sfx=True se o usuário pediu para exportar sem SFX")
    _t = p.GetCurrentTimeline()   # trilha com clipes desligada some do export (V2 do modelo GAB USA, relato 16/10/2026)
    _off = [f"{k[0].upper()}{n}" for k in ("video", "audio") for n in range(1, _t.GetTrackCount(k) + 1)
            if not _t.GetIsTrackEnabled(k, n) and (_t.GetItemListInTrack(k, n) or [])]
    if _off: print("AVISO: trilhas com clipes DESLIGADAS (não saem no vídeo):", _off, "- ligar se não foi de propósito")
    # preset primeiro: só o SetCurrentRenderFormatAndCodec("mp4") saiu SÓ COM ÁUDIO depois de um render de áudio no
    # mesmo projeto (19/10/2026, prévias sem imagem); o preset H.264 Master zera o estado do Deliver
    p.LoadRenderPreset("H.264 Master")
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
    if not p.SetRenderSettings(cfg):   # uma chave recusada derruba o pacote inteiro (sem erro)
        raise RuntimeError(f"SetRenderSettings recusou as configurações: {cfg}")
    jid = p.AddRenderJob(); p.StartRendering(jid)
    time.sleep(2)
    while p.IsRenderingInProgress(): time.sleep(2)
    st = p.GetRenderJobStatus(jid) or {}; arq = os.path.join(pasta, nome + ".mp4")
    p.DeleteRenderJob(jid)   # só o job do Gab (relato 15/10/2026: apagava a fila inteira do usuário)
    # o booleano do StartRendering e o texto do JobStatus (traduzido) não provam nada: vale a % e o arquivo
    if st.get("CompletionPercentage", 0) < 100 or st.get("Error") or not os.path.exists(arq):
        raise RuntimeError(f"render não terminou (job ficou parado ou falhou): {st}; arquivo existe: {os.path.exists(arq)}")
    tem_audio = "audio" in subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type", "-of", "csv=p=0", arq],
                                          capture_output=True, text=True).stdout
    if not tem_audio: raise RuntimeError(f"render saiu SEM ÁUDIO: {arq}")
    if "video" not in subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type", "-of", "csv=p=0", arq],
                                     capture_output=True, text=True).stdout:
        raise RuntimeError(f"render saiu SEM IMAGEM: {arq} (conferir o preset/formato no Deliver)")
    if master:
        i, pk = masterizar(arq)
        if abs(i + 14) > 0.5 or pk > -1.0: raise RuntimeError(f"master fora do alvo: {i} LUFS, pico {pk}")
    return arq, st.get("JobStatus")


def salvar(r=None):
    """SaveProject com trava: no "Untitled Project" ele não tem onde salvar (False na interface, TRAVA sem interface)."""
    pm = (r or conectar(False)).GetProjectManager(); p = pm.GetCurrentProject()
    if p and p.GetName() != "Untitled Project":
        return pm.SaveProject()
    return False


def pagina_edit(r=None):
    """DeleteClips devolve False e não apaga nada fora da página Edit (ex.: usuário no Fairlight/Color)."""
    (r or conectar(False)).OpenPage("edit")


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
    if not hasattr(cv2, "CascadeClassifier"):   # relato 16/10/2026 (Windows): dois pacotes do OpenCV brigando
        print("AVISO: este OpenCV não tem detecção de rosto. Corrigir: pip uninstall -y opencv-python opencv-python-headless "
              "opencv-contrib-python && pip install opencv-python. Até lá, medir o rosto à mão num quadro com grade.")
        return None
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


ZOOM_MAX = 1.2        # teto do reenquadramento: acima disso a cabeça corta (28/10/2026, Ediel 19 e 21 saíram a 1,34x e 1,77x)


def enquadrar(face, w=1080, h=1920, tol_x=40, zmax=ZOOM_MAX):
    """(zoom, pan, tilt) com o MÍNIMO de zoom (regra do usuário): só sobe a imagem até o queixo ficar acima de
    QUEIXO_MAX e só centraliza na horizontal se o rosto estiver a mais de tol_x px do centro. Sem borda preta.
    Sem punch-in: o mesmo valor no vídeo todo. Tilt positivo sobe a imagem.
    Gravação fechada demais (rosto grande e baixo): para em zmax e sobe o que der, sem cortar a cabeça."""
    z = 1.0
    while True:
        if z > zmax:
            z = zmax; fx = w / 2 + (face["cx"] - w / 2) * z; fy = h / 2 + (face["cy"] - h / 2) * z
            lim_x, lim_y = w / 2 * (z - 1), h / 2 * (z - 1)
            pan = 0.0 if abs(w / 2 - fx) <= tol_x else max(-lim_x, min(lim_x, w / 2 - fx))
            topo = fy - 0.75 * face["lado"] * z             # não deixar o alto da cabeça sair do quadro
            dy = -min(lim_y, max(0.0, fy + 0.6 * face["lado"] * z - QUEIXO_MAX), max(0.0, topo - 40))
            return round(z, 3), round(pan), round(-dy)
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


def abrir_em_abas(p, nomes, r=None):
    """Regra 1c: deixa as timelines dos vídeos ABERTAS EM ABAS (Stacked Timelines) para o usuário, a 1ª da lista na frente.
    Rodar no FIM de toda etapa que mexe no DaVinci e depois de todo trocar_pela_copia/DuplicateTimeline (trocar a timeline
    fecha a aba dela). Abre na página Edit, da última para a primeira. Ignora as auxiliares ("(titulos via API)",
    "(backup ...)", modelo). O Stacked Timelines em si é ligado pela interface (Timeline View Options, 1º ícone da barra
    da timeline > "Display Stacked Timelines"): conferir com um screenshot na criação do projeto."""
    r = r or conectar(abrir=False)
    r.OpenPage("edit")
    tls = {p.GetTimelineByIndex(i).GetName(): p.GetTimelineByIndex(i) for i in range(1, p.GetTimelineCount() + 1)}
    for n in reversed(nomes):
        if n in tls:
            p.SetCurrentTimeline(tls[n]); time.sleep(1.5)
        else:
            print("AVISO: timeline não encontrada para abrir em aba:", n)
    return [n for n in nomes if n in tls]


def trocar_pela_copia(p, mp, t):
    """RECEITA QUE FUNCIONA (12/10/2026) para o lettering editável entrar ANIMADO: título inserido/ajustado pela API
    congela (render seco) na timeline em que a composição do Fusion foi aberta (GetFusionCompByIndex). A CÓPIA anima,
    desde que: (1) a original FIQUE no projeto (apagar a original fazia a cópia travar) e (2) NINGUÉM abra a
    composição dos títulos na cópia (nada de GetFusionCompByIndex/_textos/ajustar_titulo/checar_fades antigo).
    A cópia já leva os fades do bloco (conferido). Devolve a cópia com o nome original."""
    nome, vi = t.GetName(), t.GetVoiceIsolationState(1)
    # 2a troca na mesma timeline: "(titulos via API)" já existe, o SetName falha calado e a cópia volta None (relato 23/10/2026)
    usados = {p.GetTimelineByIndex(i).GetName() for i in range(1, p.GetTimelineCount() + 1)}
    alvo, n = nome + " (titulos via API)", 2
    while alvo in usados:
        alvo, n = f"{nome} (titulos via API {n})", n + 1
    if not t.SetName(alvo):
        raise RuntimeError(f"não consegui renomear '{nome}' para '{alvo}'")
    d = t.DuplicateTimeline(nome)
    if not d:
        raise RuntimeError(f"DuplicateTimeline('{nome}') falhou")
    p.SetCurrentTimeline(d)
    if vi and vi.get("isEnabled") and not d.GetVoiceIsolationState(1).get("isEnabled"): d.SetVoiceIsolationState(1, vi)
    for j in range(2, d.GetTrackCount("video") + 1):          # título = item sem MediaPoolItem (não abre a composição)
        for x in d.GetItemListInTrack("video", j) or []:
            if x.GetMediaPoolItem() is None and not (get_fades(x) or {}).get("FadeOut"): set_fades(x, {"FadeOut": FADE_LETTERING})
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

# ---- Recursos do DaVinci 21.1 pela API (testados em 15/10/2026, projeto NBA)

def selecionados(t, tipo="video"):
    """"Arruma esses aqui": os clipes que o USUÁRIO selecionou na timeline (Timeline.GetSelectedClips). tipo "video",
    "audio" ou None (todos). Vem o vídeo e o áudio ligado: filtrar pelo tipo. Sem seleção: para e pede para selecionar.
    O Gab age SÓ nesses itens (nunca no resto da timeline)."""
    sel = t.GetSelectedClips() or []
    if tipo: sel = [x for x in sel if (x.GetTrackTypeAndIndex() or [None])[0] == tipo]
    if not sel: raise RuntimeError("nenhum clipe selecionado no DaVinci: selecione (clique / Cmd+clique) e peça de novo")
    return sel


def reenquadrar_vertical(p, itens, espera=600):
    """Take horizontal numa timeline vertical: Smart Reframe do DaVinci (segue a ação/pessoa em vez do corte central).
    Só funciona com o clipe em PREENCHER (Scaling 3, zoom 1): com o clipe ajustado (tarjas) ele não muda nada.
    Devolve os itens que terminaram com JobStatus Complete. Conferir 2 quadros (antes x depois) quando importar."""
    ok = []
    for it in itens:
        it.SetProperties({"Scaling": 3, "ZoomX": 1.0, "ZoomY": 1.0}) if hasattr(it, "SetProperties") else it.SetProperty("Scaling", 3)
        if not it.SmartReframe(): continue
        t0 = time.time(); st = {}
        while time.time() - t0 < espera:
            st = p.GetSmartReframeStatus() or {}
            if st.get("JobStatus") in ("Complete", "Failed", "Cancelled"): break
            time.sleep(2)
        if st.get("JobStatus") == "Complete": ok.append(it)
    return ok


def estabilizar(itens):
    """Estabiliza takes tremidos (TimelineItem.Stabilize, análise de alguns segundos por clipe). A API não devolve
    nenhuma leitura do resultado: conferir a olho na prévia. Devolve os itens em que o DaVinci aceitou."""
    return [it for it in itens if it.Stabilize()]


def multicam_podcast(r, p, mp, clipes, nome, sync="audio", min_corte=1.5, w=1080, h=1920, fps=None):
    """Podcast/entrevista com 2+ câmeras: cria o clipe Multicam (ângulos sincronizados pelo áudio, pelo timecode ou pelo
    ponto de entrada), põe numa timeline nova e roda o Smart Switch (troca de câmera por quem fala, só pelo áudio).
    clipes = MediaPoolItems (um por câmera, com o áudio de cada uma). Devolve a timeline. O resultado continua multicam
    (o usuário troca o ângulo de um trecho no DaVinci); FlattenMulticam só se ele pedir."""
    modo = {"audio": r.MULTICAM_ANGLE_SYNC_AUDIO, "timecode": r.MULTICAM_ANGLE_SYNC_TIMECODE, "in": r.MULTICAM_ANGLE_SYNC_IN}[sync]
    mc = mp.CreateMulticamClip(list(clipes), {"name": nome + " - multicam", "angleSyncMode": modo, "multicamAudioMode": r.MULTICAM_AUDIO_ALL,
                                              "angleNameMode": r.MULTICAM_ANGLE_NAME_CLIP, "createBinForSourceClips": False})
    if not mc: raise RuntimeError("Multicam não foi criado (ângulos sem áudio em comum? tentar sync='timecode' ou 'in')")
    t = mp.CreateEmptyTimeline(nome); p.SetCurrentTimeline(t); r.OpenPage("edit")
    t.SetSetting("useCustomSettings", "1")
    for k, v in (("timelineResolutionWidth", w), ("timelineResolutionHeight", h), ("timelineFrameRate", fps)):
        if v: t.SetSetting(k, str(v))
    it = (mp.AppendToTimeline([{"mediaPoolItem": mc[0]}]) or [None])[0]
    if not it: raise RuntimeError("Multicam não entrou na timeline")
    ok = it.PerformMulticamSmartSwitch({"minEditDuration": float(min_corte), "editChangeDelay": 0.3,
                                        "analysisMode": r.SMART_SWITCH_ANALYSIS_MODE_AUDIO_ONLY, "quality": r.SMART_SWITCH_QUALITY_BETTER})
    time.sleep(2); n = len(t.GetItemListInTrack("video", 1) or [])
    if not ok or n < 2: print(f"AVISO: Smart Switch não trocou de câmera ({n} trecho): conferir o áudio de cada ângulo")
    return t


OGRAF_DIR = (os.path.join(os.environ.get("APPDATA", ""), "Blackmagic Design", "DaVinci Resolve", "Support", "Fusion", "Templates", "Edit", "Titles", "OGraf")
             if sys.platform.startswith("win") else
             os.path.expanduser("~/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Templates/Edit/Titles/OGraf"))


def conferir_ograf(p, t, item, quadro, arq_png):
    """Quadro do título OGraf no RENDER do DaVinci (o que sai no vídeo). Não usar o visualizador (ExportCurrentFrameAsStill
    mostra a página em cache com valores velhos) nem o Saver do Fusion (comp.Render abre a janela "Render completed!",
    que trava a API até alguém clicar em OK, mesmo com Quiet)."""
    import tempfile
    F = fps_tl(t); ini = (item.GetStart() - t.GetStartFrame() + int(quadro)) / F
    pasta = tempfile.mkdtemp(prefix="ograf_conf_")
    mp4 = renderizar_trecho(p, pasta, "conf", ini, ini + 2.0 / F, so_v1=False)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp4, "-frames:v", "1", arq_png], check=True)
    return arq_png


def _ograf_manifesto(template):
    """template = nome da pasta em Titles/OGraf (ex.: "GabLettering") ou caminho de um .ograf.json."""
    if template.endswith(".ograf.json"):
        arq = template
    else:
        pasta = os.path.join(OGRAF_DIR, template)
        arq = next((os.path.join(pasta, f) for f in os.listdir(pasta) if f.endswith(".ograf.json")), None) if os.path.isdir(pasta) else None
    if not arq or not os.path.exists(arq):
        raise RuntimeError(f"template OGraf {template!r} não instalado em {OGRAF_DIR} (rodar o instalador ou copiar a pasta de ograf/)")
    return arq, json.load(open(arq))


def ograf_no_item(item, template, valores=None, dur_f=None, t=None, p=None):
    """Transforma um item "Fusion Composition" da timeline num título OGraf (HTML) EDITÁVEL no Inspector
    (testado em 15/10/2026, DaVinci 21.1). A API não insere título OGraf pelo nome; o caminho é o nó OGrafLoader do
    Fusion: TemplatePath + parâmetros dinâmicos. O loader numera os parâmetros pela ORDEM do schema do manifesto
    (texto -> DynParamText<i>, número -> DynParamNum<i>, booleano -> DynParamCheck<i>, cor #rrggbb -> DynParamColor<i>_R/G/B),
    então aqui se passa pelo NOME do manifesto: valores={"texto": "...", "corDestaque": "#ffb300"}.
    dur_f: quadros até a saída (agenda um stopAction; a API não corta o clipe)."""
    arq, man = _ograf_manifesto(template)
    comp = item.GetFusionCompByIndex(1)
    if not comp: raise RuntimeError("item sem composição Fusion (usar InsertFusionCompositionIntoTimeline)")
    og = comp.FindTool("GabOGraf")
    if not og:
        comp.Lock(); og = comp.AddTool("OGrafLoader", -32768, -32768); og.SetAttrs({"TOOLS_Name": "GabOGraf"}); comp.Unlock()
    mo = comp.FindTool("MediaOut1")
    og.SetInput("TemplatePath", arq); mo.Input = og.Output
    props = list((man.get("schema") or {}).get("properties", {}).items())
    # o template carrega DEPOIS (assíncrono) e põe os padrões do manifesto por cima do que foi escrito antes:
    # recarregar, esperar o 1º parâmetro mostrar o padrão (carregou) e só então escrever; conferir de novo no fim
    og.SetInput("ReloadAction", 1)
    # o template só carrega de verdade quando o quadro é mostrado (e aí reseta os parâmetros para o padrão):
    # aquecer pelo visualizador (playhead dentro do item + exportar um quadro). NÃO usar comp.Render/Saver: abre janela.
    if t is not None and p is not None:
        import tempfile
        _ir(t, item.GetStart() + 2); time.sleep(1.0)
        p.ExportCurrentFrameAsStill(os.path.join(tempfile.mkdtemp(prefix="ograf_"), "aquece.png")); time.sleep(1.5)
    p0 = next(((i, d.get("default")) for i, (n, d) in enumerate(props) if d.get("type") == "string" and not d.get("gddType")), None)
    for _ in range(40):
        if not p0 or og.GetInput(f"DynParamText{p0[0]}") == p0[1]: break
        time.sleep(0.5)
    _escrever_ograf(og, props, valores or {}, template)
    time.sleep(2.0)
    _escrever_ograf(og, props, valores or {}, template)      # se o carregamento ainda pisou em algo, reescreve
    if dur_f:
        og.SetInput("ScheduledAction_1.Name", "stopAction"); og.SetInput("ScheduledAction_1.Time", float(dur_f))
        og.SetInput("StopActionUserModified", 1.0)
    return og


def _escrever_ograf(og, props, valores, template):
    for nome, v in valores.items():
        i = next((k for k, (n, _) in enumerate(props) if n == nome), None)
        if i is None: raise RuntimeError(f"parâmetro {nome!r} não existe no manifesto de {template}: {[n for n, _ in props]}")
        d = props[i][1]
        if d.get("gddType", "").startswith("color") or (isinstance(v, str) and v.startswith("#") and len(v) == 7 and d.get("type") == "string" and "color" in nome.lower()):
            for c, j in zip("RGB", (1, 3, 5)): og.SetInput(f"DynParamColor{i}_{c}", int(v[j:j + 2], 16) / 255)
        elif d.get("type") in ("number", "integer"): og.SetInput(f"DynParamNum{i}", float(v))
        elif d.get("type") == "boolean": og.SetInput(f"DynParamCheck{i}", 1.0 if v else 0.0)
        else:
            og.SetInput(f"DynParamText{i}", str(v))
            if og.GetInput(f"DynParamText{i}") != str(v): raise RuntimeError(f"OGraf não aceitou {nome}={v!r}")


def inserir_ograf_na_trilha(t, trilha, lista, template="GabLettering"):
    """Como inserir_letterings_na_trilha, mas com título OGraf: lista [(valores_dict, inicio_s, dur_s[, template]), ...].
    PRÉ-REQUISITO igual: destino da timeline na `trilha` (Option+N com o DaVinci na frente). Trava as outras trilhas."""
    F = fps_tl(t); S = t.GetStartFrame(); pagina_edit()
    travar = [(k, i) for k in ("audio", "subtitle") for i in range(1, t.GetTrackCount(k) + 1)] + \
             [("video", i) for i in range(1, t.GetTrackCount("video") + 1) if i != trilha]
    for k, i in travar: t.SetTrackLock(k, i, True)
    t.SetTrackLock("video", trilha, False)
    antes = _assinatura(t) + [(k, i, x.GetStart()) for k, i in travar if k == "video" for x in (t.GetItemListInTrack(k, i) or [])]
    feitos = []
    try:
        for item in sorted(lista, key=lambda x: x[1]):
            valores, ini, dur = item[:3]; tpl = item[3] if len(item) > 3 else template
            f = S + max(3, round(ini * F)); _ir(t, f); time.sleep(0.6); _ir(t, f)
            novo = t.InsertFusionCompositionIntoTimeline()
            if not novo: raise RuntimeError("composição Fusion não entrou")
            novos = [x for x in (t.GetItemListInTrack("video", trilha) or []) if x.GetStart() == f and x.GetUniqueId() == novo.GetUniqueId()]
            if not novos: raise RuntimeError(f"OGraf não caiu na trilha {trilha} em {f}: conferir o destino da timeline")
            ograf_no_item(novos[0], tpl, valores, dur_f=round(dur * F), t=t, p=conectar(False).GetProjectManager().GetCurrentProject())
            feitos.append(novos[0])
    finally:
        for k, i in travar: t.SetTrackLock(k, i, False)
    depois = _assinatura(t) + [(k, i, x.GetStart()) for k, i in travar if k == "video" for x in (t.GetItemListInTrack(k, i) or [])]
    if depois != antes: raise RuntimeError("outra trilha mudou durante a inserção (ripple): conferir")
    return feitos


MODELO_LEGENDA = "MODELO GAB USA"
DRT_FPS = 24   # fps gravado no modelo_gab_usa.drt
DRT_MODELO = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "davinci", "modelo_gab_usa.drt")


def timeline_do_modelo(p, mp, nome, w=None, h=None, fps=None, modelo=MODELO_LEGENDA, drt=DRT_MODELO):
    """Timeline nova JÁ com o estilo de legenda (preset GAB USA) sem clicar em nada: a API não aplica estilo de
    legenda, mas ele fica gravado na trilha e vai junto quando a timeline é duplicada ou importada (.drt).
    Usa a timeline-modelo do projeto; se não existir, importa assets/davinci/modelo_gab_usa.drt."""
    tls = {p.GetTimelineByIndex(i).GetName(): p.GetTimelineByIndex(i) for i in range(1, p.GetTimelineCount() + 1)}
    m = tls.get(modelo)
    # o .drt do modelo é 24 fps e ImportTimelineFromFile grava esse fps no PROJETO (relato 15/10/2026: 29,97 virou 24):
    # projeto em outro fps não importa o modelo; quem chama cai na timeline vazia e o preset entra por legenda_ui.py
    pfps = float(p.GetSetting("timelineFrameRate") or 0)
    if not m and os.path.exists(drt) and abs(pfps - DRT_FPS) < 0.01:
        m = mp.ImportTimelineFromFile(drt, {"timelineName": modelo})
        if m: m.SetName(modelo)
    if not m:
        return None
    p.SetCurrentTimeline(m)
    pagina_edit()
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
    for k in ("video", "audio", "subtitle"):   # o modelo GAB USA tem a V2 desligada: letterings sumiam no export (relato 16/10/2026)
        for n in range(1, t.GetTrackCount(k) + 1):
            if not t.GetIsTrackEnabled(k, n): t.SetTrackEnable(k, n, True)
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
        # Windows: o H.264 do Media Foundation derruba o DaVinci ("Fail to create output buffer", relato 15/10/2026);
        # prova sai em ProRes 422 LT (.mov), que renderiza rápido e não trava
        ext, fmt, codec = ("mov", "mov", "ProRes422LT") if os.name == "nt" else ("mp4", "mp4", "H264")
        os.makedirs(pasta, exist_ok=True); p.SetCurrentRenderFormatAndCodec(fmt, codec)
        p.SetRenderSettings({"SelectAllFrames": False, "MarkIn": S + round(ini * F), "MarkOut": S + round(fim * F) - 1,
                             "TargetDir": pasta, "CustomName": nome, "ExportVideo": True, "ExportAudio": True,
                             "FormatWidth": int(t.GetSetting("timelineResolutionWidth")), "FormatHeight": int(t.GetSetting("timelineResolutionHeight"))})
        jid = p.AddRenderJob(); p.StartRendering(jid)
        while p.IsRenderingInProgress(): time.sleep(1)
        p.DeleteRenderJob(jid)
        return os.path.join(pasta, nome + "." + ext)
    finally:
        pagina_edit()   # SetTrackEnable não religa na página Deliver (relato 15/10/2026: V2-V4 ficaram desligadas)
        for tipo, k in desligadas: t.SetTrackEnable(tipo, k, True)
        presas = [f"{tipo}{k}" for tipo, k in desligadas if not t.GetIsTrackEnabled(tipo, k)]
        if presas: print("AVISO: trilhas continuam desligadas, religar à mão:", presas)


def timeline_com_letterings(p, mp, nome, lista, w=1080, h=1920, fps=30, pasta=None, sem_menu=None):
    """Timeline NOVA (do modelo GAB USA) com os letterings EDITÁVEIS (Fusion Title do pacote) já animados, sem UI.
    Por quê (12/10/2026): título inserido numa timeline que já tem mídia entra SECO (sem animação) e a API só insere na V1;
    numa timeline vazia ele anima. Então: insere os títulos primeiro na V1 vazia, em ordem, e cria uma trilha de vídeo na
    posição 1 (os títulos sobem para a V2 = LETTERING). Depois montar takes na V1, motions acima, áudio e legenda.
    lista = [(TEXTO, inicio_s, template[, centro_y]), ...]."""
    import portao_menu; portao_menu.checar(pasta, sem_menu)
    t = timeline_do_modelo(p, mp, nome, w, h, fps) or criar_timeline(p, mp, nome, w, h, fps, sem_menu="portão já conferido")
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
            p.SetCurrentRenderFormatAndCodec("mp4", "H264")
            p.SetRenderSettings({"SelectAllFrames": False, "MarkIn": it.GetStart(), "MarkOut": it.GetStart() + quadro_fim + 2,
                                 "TargetDir": pasta, "CustomName": nome, "ExportVideo": True, "ExportAudio": False,
                                 "ExportSubtitle": False})
            jid = p.AddRenderJob(); p.StartRendering(jid)
            while p.IsRenderingInProgress(): time.sleep(0.5)
            p.DeleteRenderJob(jid)
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
    """Coloca o desenho de som de `pasta_sfx/plano_sfx.txt` (linhas 'T.TTs Ax nome -NNdB[ D.Ds]: o que acompanha'), cada som
    na primeira trilha livre (A3..A6), cortado em SFX_DMAX, volume e fade no clipe. Apaga o que havia nessas trilhas."""
    pagina_edit()   # DeleteClips só funciona na página Edit
    import re as _re
    ev = [(m[2], float(m[1]), int(m[3]), float(m[4]) if m[4] else None) for m in (_re.match(r"\s*([\d.]+)s A\d (\S+) (-?\d+)dB(?: ([\d.]+)s)?", l)
          for l in open(os.path.join(pasta_sfx, "plano_sfx.txt")).read().splitlines()) if m]
    garantir_trilhas_audio(t, max(trilhas))
    pasta_abs = os.path.abspath(pasta_sfx)
    for k in trilhas:   # só apaga o que veio DESTA pasta (bug 14/10/2026: AddTrack muda a numeração e apagava SFX do usuário)
        its = [x for x in (t.GetItemListInTrack("audio", k) or []) if x.GetMediaPoolItem() and
               os.path.dirname(os.path.abspath(x.GetMediaPoolItem().GetClipProperty("File Path") or "")) == pasta_abs]
        if its: t.DeleteClips(its)
        if not [x for x in (t.GetItemListInTrack("audio", k) or [])]:
            t.SetTrackName("audio", k, "SFX" if k == trilhas[0] else f"SFX {k - trilhas[0] + 1}")
    S, F = t.GetStartFrame(), fps_tl(t); fim = {k: -1 for k in trilhas}; ok = 0; avisou = False
    for nome, ini, db, dmax in sorted(ev, key=lambda e: e[1]):
        it = importar(mp, os.path.join(pasta_sfx, nome + ".wav"), "SFX"); fc = float(it.GetClipProperty("FPS") or F)
        dur = min(dmax or SFX_DMAX.get(nome, 2.0), fim_s - ini); rf = S + round(ini * F)   # 'NN dB D.Ds' na linha = duração própria
        livres = [k for k in trilhas if fim[k] < rf and not [y for y in (t.GetItemListInTrack("audio", k) or []) if y.GetStart() < rf + round(dur * F) and y.GetEnd() > rf]]
        if not livres: print("SFX sem trilha livre:", nome, ini); continue
        k = livres[0]
        x = mp.AppendToTimeline([{"mediaPoolItem": it, "mediaType": 2, "trackIndex": k, "recordFrame": rf, "startFrame": 0, "endFrame": round(dur * fc)}])
        if not x: print("SFX falhou:", nome, ini); continue
        if not x[0].SetProperty("AudioVolume", db) and not avisou:   # DaVinci 21.0 não aceita volume pela API (relato 15/10/2026)
            print("AVISO: o DaVinci não aceitou o volume do clipe pela API (< 21.1): SFX entraram no volume do arquivo;"
                  " atualizar para 21.1+ ou gravar o ganho numa cópia (ffmpeg volume=NNdB)"); avisou = True
        set_fades(x[0], {"FadeOut": min(8, round(dur * F / 4))}); fim[k] = x[0].GetEnd(); ok += 1
    return ok, len(ev)


# ------------------------------------------------------------------ tracking e animação (12/10/2026)

def _comp_do_clipe(item):
    comp = item.GetFusionCompByIndex(1) if item.GetFusionCompCount() else item.AddFusionComp()
    if not comp:
        raise RuntimeError(f"não consegui abrir o Fusion do clipe {item.GetName()}")
    return comp


def _quadro_comp(comp, t_arquivo, fps_arquivo):
    """Quadro da composição do Fusion de um clipe: conta na taxa do ARQUIVO, a partir do início da mídia
    (COMPN_GlobalStart é negativo = quadros antes do ponto de entrada)."""
    return round(t_arquivo * fps_arquivo + comp.GetAttrs()["COMPN_GlobalStart"])


def texto_rastreado(item, trilha, texto, deslocamento=(0.0, -0.10), tamanho=0.06, fonte="Inter", estilo="Bold",
                    cor=(1.0, 1.0, 1.0), margem=0.06, seguir_escala=False):
    """Texto que ACOMPANHA um objeto/rosto (trilha de scripts/rastrear.py) dentro do Fusion do próprio clipe.
    deslocamento = (dx, dy) em fração do quadro em relação ao centro rastreado (dy negativo = acima).
    Fica dentro da área segura (margem). Nós criados: TextoRastreado (Text+) + MergeTexto, editáveis no Fusion.
    Devolve quantos keyframes de posição foram gravados."""
    import json as _json
    tr = _json.load(open(trilha)) if isinstance(trilha, str) else trilha
    comp = _comp_do_clipe(item)
    mi, mo = comp.FindTool("MediaIn1"), comp.FindTool("MediaOut1")
    comp.Lock()
    txt = comp.AddTool("TextPlus", -32768, -32768); txt.SetAttrs({"TOOLS_Name": "TextoRastreado"})
    mg = comp.AddTool("Merge", -32768, -32768); mg.SetAttrs({"TOOLS_Name": "MergeTexto"})
    comp.Unlock()
    txt.SetInput("StyledText", texto); txt.SetInput("Font", fonte); txt.SetInput("Style", estilo); txt.SetInput("Size", tamanho)
    txt.SetInput("Red1", cor[0]); txt.SetInput("Green1", cor[1]); txt.SetInput("Blue1", cor[2])
    origem = mo.Input.GetConnectedOutput() or mi.Output
    mg.Background = origem; mg.Foreground = txt.Output; mo.Input = mg.Output
    txt.AddModifier("Center", "XYPath")
    W, H, fps = tr["w"], tr["h"], tr["fps"]
    meia = min(0.45, len(texto) * tamanho * 0.29)          # meia largura aproximada do texto (fração do quadro)
    n = 0
    for t, x, y, e in tr["pontos"]:
        cx = x / W + deslocamento[0] * (e if seguir_escala else 1)
        cy = 1 - y / H - deslocamento[1] * (e if seguir_escala else 1)
        cx = min(max(cx, margem + meia), 1 - margem - meia)
        cy = min(max(cy, margem), 1 - margem)
        txt.SetInput("Center", {1: cx, 2: cy}, _quadro_comp(comp, t, fps)); n += 1
    if seguir_escala:
        txt.AddModifier("Size", "BezierSpline")
        for t, x, y, e in tr["pontos"]:
            txt.SetInput("Size", tamanho * e, _quadro_comp(comp, t, fps))
    return n


def animar_clipe(item, chaves, fps_arquivo=None, nome="AnimGab"):
    """Animação com keyframes no clipe (zoom, pan, giro), por um nó Transform no Fusion do clipe (a API da
    timeline não grava keyframes). chaves = [(t_arquivo_s, {"zoom": 1.0, "x": 0.5, "y": 0.5, "giro": 0}), ...]
    em segundos do ARQUIVO; x/y = centro (0-1, y para cima). Ex. punch-in: [(2.0, {"zoom": 1.0}), (2.4, {"zoom": 1.15})]."""
    comp = _comp_do_clipe(item)
    mi, mo = comp.FindTool("MediaIn1"), comp.FindTool("MediaOut1")
    fps = fps_arquivo or float(item.GetMediaPoolItem().GetClipProperty("FPS") or 30)
    tf = comp.FindTool(nome)
    if not tf:
        comp.Lock(); tf = comp.AddTool("Transform", -32768, -32768); tf.SetAttrs({"TOOLS_Name": nome}); comp.Unlock()
        tf.Input = mi.Output
        seguinte = [x for x in comp.GetToolList(False).values() if x.ID == "Merge" and x.Background.GetConnectedOutput() and x.Background.GetConnectedOutput().GetTool().Name == "MediaIn1"]
        if seguinte:
            seguinte[0].Background = tf.Output
        else:
            mo.Input = tf.Output
    usados = set(k for _, c in chaves for k in c)
    if "zoom" in usados: tf.AddModifier("Size", "BezierSpline")
    if "giro" in usados: tf.AddModifier("Angle", "BezierSpline")
    if "x" in usados or "y" in usados: tf.AddModifier("Center", "XYPath")
    for t, c in chaves:
        f = _quadro_comp(comp, t, fps)
        if "zoom" in c: tf.SetInput("Size", c["zoom"], f)
        if "giro" in c: tf.SetInput("Angle", c["giro"], f)
        if "x" in c or "y" in c: tf.SetInput("Center", {1: c.get("x", 0.5), 2: c.get("y", 0.5)}, f)
    return tf.Name


# ---------------------------------------------------------------- pessoa na frente (máscara no Fusion, 22-23/10/2026)
# Engenharia reversa do DaVinci 21.1 (libfusionoperators + SaveSettings de um traço feito pelo usuário):
# - MagicMask do Fusion: o traço é ANIMADO. A entrada Strokes vem de um BezierSpline com quadro-chave no quadro de
#   referência: KeyFrames = { [ref] = { 0, Flags = {...}, Value = MagicMaskStrokes { PosStrokes = { {x, y}, ... },
#   NegStrokes = {...} } } } + ReferenceTime = ref. Coordenadas 0-1, y de baixo para cima; clique = traço de 1 ponto.
#   Com isso a máscara do quadro de referência sai sozinha. LoadSettings NÃO traz o spline (só a ferramenta) e
#   dvr.readfile perde os tipos: o caminho é o texto na área de transferência + comp.Paste() (Ctrl+V do Fusion).
# - O RASTREIO só anda pelo botão da tela (SetInput("TrackForward"), Lua e TrackBidirectional por script não fazem
#   nada): o Gab clica "Track Fwd Then Reverse" no Inspector e confere com magic_rastreado().
# - Alternativa sem rastreio: DepthMap (IA de profundidade) + MatteControl (metodo="profundidade"); o usuário achou
#   pior que o Magic Mask (23/10/2026): usar só se o rastreio pela tela não for possível.

def _calibrar_corte(r, p, t, comp, quadro, pasta=None):
    """Mede a profundidade do rosto e do fundo no quadro e devolve (baixo, alto) do corte.
    ExportCurrentFrameAsStill pega o quadro da cabeça de leitura (que às vezes não anda): as duas fotos saem do
    MESMO quadro, então a comparação vale."""
    import tempfile
    from PIL import Image
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "presets", "cena"))
    import rosto as _rosto
    pasta = pasta or tempfile.mkdtemp(prefix="gab_corte_")
    mi, mo, dm, mc = (comp.FindTool(n) for n in ("MediaIn1", "MediaOut1", "Profundidade", "Recorte"))
    fotos = {}
    for nome, fonte in (("cor", mi), ("prof", dm)):
        r.OpenPage("fusion"); comp.Lock(); mo.ConnectInput("Input", fonte); comp.Unlock()
        r.OpenPage("edit"); t.SetCurrentTimecode(_tc(t, quadro)); time.sleep(5)
        fotos[nome] = os.path.join(pasta, f"corte_{nome}.png")
        if not p.ExportCurrentFrameAsStill(fotos[nome]):
            # 21.1 no Mac: na página Edit a exportação às vezes devolve False; na Color funciona (23/10/2026)
            r.OpenPage("color"); t.SetCurrentTimecode(_tc(t, quadro)); time.sleep(3)
            ok = p.ExportCurrentFrameAsStill(fotos[nome]); r.OpenPage("edit")
            if not ok:
                raise RuntimeError("ExportCurrentFrameAsStill falhou na Edit e na Color")
    r.OpenPage("fusion"); comp.Lock(); mo.ConnectInput("Input", mc); comp.Unlock(); r.OpenPage("edit")
    cor = Image.open(fotos["cor"]); W, H = cor.size
    caixas = _rosto._caixa_vision(fotos["cor"], W, H) if sys.platform == "darwin" else []
    if not caixas:
        raise RuntimeError("nenhum rosto no quadro de calibração: passe corte=(baixo, alto) à mão")
    x0, y0, x1, y1 = max(caixas, key=lambda c: (c[2] - c[0]) * (c[3] - c[1]))
    prof = Image.open(fotos["prof"]).convert("L")
    def vals(caixa):
        return sorted(prof.crop(tuple(int(v) for v in caixa)).getdata())
    cx0, cx1 = x0 + (x1 - x0) * .25, x1 - (x1 - x0) * .25
    face = vals((cx0, y0 + (y1 - y0) * .3, cx1, y1 - (y1 - y0) * .2))
    face = face[len(face) // 2] / 255
    fw = x1 - x0   # fundo: faixa de cima e laterais na altura do rosto, longe da pessoa
    fundo = vals((0, 0, W, max(2, y0 - fw * .6))) + vals((0, y0, max(2, x0 - fw * .9), y1)) + vals((min(W - 2, x1 + fw * .9), y0, W, y1))
    fundo = fundo[int(len(fundo) * .9)] / 255
    if face - fundo < .08:
        raise RuntimeError(f"profundidade não separa a pessoa do fundo (rosto {face:.2f}, fundo {fundo:.2f}): "
                           "use o Magic Mask pintado à mão no Fusion")
    return round(fundo + .3 * (face - fundo), 3), round(fundo + .6 * (face - fundo), 3)


def _colar_magic_mask(comp, ref, pos, neg, modo="Faster", nome="PintarPessoa"):
    """Cola um MagicMask com os cliques no quadro `ref` (quadro-chave animado, como o traço feito na tela)."""
    pts = lambda L: ", ".join("{ %s, %s }" % (x, y) for x, y in L)
    txt = """{ Tools = ordered() {
  %s = MagicMask { Inputs = {
    Mode = Input { Value = FuID { "%s" }, },
    ReferenceTime = Input { Value = %d, Disabled = true, },
    UseLegacyMagicMask = Input { Value = 0, Disabled = true, },
    Strokes = Input { SourceOp = "%sStrokes", Source = "Value", }, }, },
  %sStrokes = BezierSpline { SplineColor = { Red = 242, Green = 186, Blue = 59 }, NameSet = true,
    KeyFrames = { [%d] = { 0, Flags = { Linear = true, LockedY = true }, Value = MagicMaskStrokes {
      PosStrokes = { %s }, NegStrokes = { %s } } } } } } }""" % (nome, modo, ref, nome, nome, ref, pts(pos), pts(neg))
    antes = subprocess.run(["pbpaste"], capture_output=True).stdout
    try:   # a área de transferência do usuário volta como estava
        subprocess.run(["pbcopy"], input=txt.encode())
        comp.Lock(); velho = comp.FindTool(nome); velho and velho.Delete(); comp.Paste(); comp.Unlock()
    finally:
        subprocess.run(["pbcopy"], input=antes)
    mm = comp.FindTool(nome)
    if not mm:
        raise RuntimeError("o Fusion não colou o MagicMask (Paste da área de transferência)")
    return mm


def magic_rastreado(item, nome="PintarPessoa"):
    """(primeiro, último, completo?) dos quadros com máscara depois do rastreio pela tela."""
    comp = item.GetFusionCompByIndex(1); mm = comp.FindTool(nome); a = comp.GetAttrs()
    lo, hi = mm.GetInput("ProcessedFramesLow"), mm.GetInput("ProcessedFramesHigh")
    return lo, hi, lo <= a["COMPN_RenderStart"] and hi >= a["COMPN_RenderEnd"]


def pessoa_na_frente(r, p, t, mp, ini_s, fim_s, acima_da_trilha=None, metodo="magicmask", modo="Faster", corte=None, borda=0.0, desfoque=1.0, na_trilha=None):
    """Recorta a pessoa da V1 no trecho [ini_s, fim_s] (segundos da timeline) numa trilha NOVA "PESSOA NA FRENTE",
    logo acima de `acima_da_trilha` (padrão: no topo). Tudo entre a V1 e o recorte (motion, lettering, objeto) fica
    ATRÁS da pessoa. A V1 não é tocada: o recorte é uma cópia do trecho (só vídeo, mesmo enquadramento) com uma
    composição Fusion que FICA na timeline para o usuário ajustar (regra do usuário, 23/10/2026).
    metodo="magicmask" (padrão, o que o usuário usa): MediaIn > PintarPessoa (MagicMask, modo Faster) > MediaOut, com
    cliques positivos por dentro da pessoa + cabelo + objetos que ela segura e negativos no fundo, tirados do recorte
    de sujeito da Apple (scripts/sujeito.py) num quadro de referência. A máscara desse quadro já sai pronta; FALTA o
    rastreio: abrir o Fusion no clipe, clicar "Track Fwd Then Reverse" no Inspector e conferir magic_rastreado().
    metodo="profundidade": DepthMap + MatteControl, sem rastreio (corte=(baixo, alto) ou calibrado pelo rosto).
    Devolve (item, info)."""
    pagina_edit()
    F = fps_tl(t); S = t.GetStartFrame(); a = S + round(ini_s * F); b = S + round(fim_s * F)
    base = next((x for x in (t.GetItemListInTrack("video", 1) or []) if x.GetStart() <= a < x.GetEnd()), None)
    if not base or not base.GetMediaPoolItem():
        raise RuntimeError(f"nenhum clipe de vídeo na V1 em {ini_s:.2f} s")
    b = min(b, base.GetEnd())
    m = base.GetMediaPoolItem(); r_ = float(m.GetClipProperty("FPS")) / F
    src = round((base.GetLeftOffset() + a - base.GetStart()) * r_)
    if na_trilha:   # vários trechos na MESMA trilha (aula cortada em muitos pedaços: uma trilha só, não uma por pedaço)
        trilha = na_trilha
    elif acima_da_trilha is None:
        t.AddTrack("video"); trilha = t.GetTrackCount("video")
    else:
        t.AddTrack("video", {"index": acima_da_trilha + 1}); trilha = acima_da_trilha + 1
    t.SetTrackName("video", trilha, "PESSOA NA FRENTE")
    # endFrame é EXCLUSIVO (ver montar_takes); só vídeo (mediaType 1) para não duplicar o áudio
    mp.AppendToTimeline([{"mediaPoolItem": m, "startFrame": src, "endFrame": src + round((b - a) * r_),
                          "recordFrame": a, "trackIndex": trilha, "mediaType": 1}])
    novo = next((x for x in (t.GetItemListInTrack("video", trilha) or []) if abs(x.GetStart() - a) <= 1), None)
    if not novo:
        raise RuntimeError("a cópia da pessoa não entrou na trilha (AppendToTimeline descartou sem erro)")
    for k in ("ZoomX", "ZoomY", "Pan", "Tilt", "RotationAngle", "FlipX", "FlipY", "CropLeft", "CropRight",
              "CropTop", "CropBottom", "CropSoftness", "AnchorPointX", "AnchorPointY", "Pitch", "Yaw"):
        v = base.GetProperty(k)
        if v is not None: novo.SetProperty(k, v)
    comp = novo.AddFusionComp()
    mi, mo = comp.FindTool("MediaIn1"), comp.FindTool("MediaOut1")
    novo.SetClipColor("Pink")
    if metodo == "magicmask":
        import tempfile
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import sujeito
        ca = comp.GetAttrs(); ini_c, fim_c = int(ca["COMPN_RenderStart"]), int(ca["COMPN_RenderEnd"])
        # tempo da composição começa em 0 no INÍCIO do clipe (testado 23/10: trecho com 180 quadros de entrada
        # deu RenderStart 0); a foto de referência vem do quadro da FONTE correspondente
        ref = ini_c + min(12, (fim_c - ini_c) // 2)
        q_fonte = src + round((ref - ini_c) * r_)
        png = os.path.join(tempfile.mkdtemp(prefix="gab_magic_"), "ref.png")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", m.GetClipProperty("File Path"), "-vf",
                        f"select=eq(n\\,{q_fonte})", "-frames:v", "1", png], check=True)
        pt = sujeito.pontos(png)
        # Paste só vale na composição ATIVA do Fusion (na timeline nova falhou com a página Edit aberta):
        # cabeça de leitura no clipe (trilha mais alta) e página Fusion antes de colar.
        t.SetCurrentTimecode(_tc(t, a + 1)); r.OpenPage("fusion"); time.sleep(1)
        ativa = r.Fusion().GetCurrentComp()
        if not ativa or ativa.GetAttrs("COMPS_Name") != comp.GetAttrs("COMPS_Name") or not ativa.FindTool("MediaIn1"):
            raise RuntimeError("o Fusion abriu outra composição; a cópia da pessoa precisa ser a trilha mais alta no ponto")
        comp = ativa; mi, mo = comp.FindTool("MediaIn1"), comp.FindTool("MediaOut1")
        mm = _colar_magic_mask(comp, ref, pt["pos"], pt["neg"], modo)
        comp.Lock(); mm.ConnectInput("Input", mi); mo.ConnectInput("Input", mm); comp.Unlock()
        comp.CurrentTime = ref; comp.SetActiveTool(mm); comp.CurrentFrame.ViewOn(mm, 1)
        return novo, {"ref": ref, "positivos": len(pt["pos"]), "negativos": len(pt["neg"]), "falta": "rastrear na tela"}
    comp.Lock()   # travar SÓ para criar e ligar: valor gravado dentro do Lock não sai no render (davinci_api.md)
    dm = comp.AddTool("DepthMap", -32768, -32768); dm.SetAttrs({"TOOLS_Name": "Profundidade"})
    mc = comp.AddTool("MatteControl", -32768, -32768); mc.SetAttrs({"TOOLS_Name": "Recorte"})
    dm.ConnectInput("Input", mi)
    mc.ConnectInput("Background", mi); mc.ConnectInput("Garbage.Matte", dm)
    mo.ConnectInput("Input", mc)
    comp.Unlock()
    dm.SetInput("DepthMapPreview", 1)
    mc.SetInput("Garbage.MaskInverted", 1); mc.SetInput("Garbage.MaskChannel", 0)
    mc.SetInput("PostMultiplyImage", 1); mc.SetInput("MatteContractExpand", borda); mc.SetInput("MatteBlur", desfoque)
    if corte is None:
        corte = _calibrar_corte(r, p, t, comp, a + min(12, (b - a) // 2))
    mc.SetInput("Garbage.MaskLow", corte[0]); mc.SetInput("Garbage.MaskHigh", corte[1])
    return novo, corte
