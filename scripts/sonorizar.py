"""Sonorização de cenas e animações SEM chave de IA (desenho de som em camadas: ambiente + foley + SFX + música).

  python3 sonorizar.py analisar <video> [--pasta <saida>]      # momentos de ação, cortes, pan e folha de quadros
  python3 sonorizar.py medir <som.wav|pasta> ...                # ataque (onset), pico e duração de cada som
  python3 sonorizar.py mixar <plano.json> [--sem-voz]           # camadas, pan, ducking, -14 LUFS: stems + prévia
  python3 sonorizar.py conferir <plano.json>                     # o que cada som É (CLAP) x a cena; barra o incoerente
  python3 sonorizar.py davinci <plano.json> <pasta_sfx>         # vira plano_sfx.txt (colocar_plano_sfx no DaVinci)

analisar: OpenCV mede o movimento quadro a quadro e devolve, por evento, o tempo, o tipo (entrada = algo começa a
se mexer depois de calma; batida = movimento forte que PARA de repente, ex. pé no chão, porta, objeto pousando;
pico = auge de um movimento contínuo), a força (0-1) e o pan (-1 esquerda a 1 direita, pela posição do movimento).
Gera <pasta>/analise.json e <pasta>/folha.png (quadros com o tempo e o tipo escritos): o Gab OLHA a folha para
saber O QUE acontece em cada evento e escolhe o som pelo objeto (docs/etapas/sonorizacao.md).

plano.json (o Gab escreve; tempos em segundos do vídeo):
  {"video": "cena.mp4", "saida": "sonorizacao", "voz": true,
   "ambiente": [{"arquivo": "parque.wav", "de": 0, "ate": 12, "db": -24, "fade": 1.0, "pan": 0}],
   "eventos":  [{"t": 3.2, "arquivo": "passo.wav", "db": -14, "pan": -0.4, "dur": 0.8, "alinhar": "onset", "nota": "pé esq."}],
   "musica":   {"arquivo": "trilha.wav", "db": -18, "de": 0, "inicio_arquivo": 0, "duck": true},
   "camera_lenta": [{"de": 3.55, "ate": 5.85, "entrada": 0.3, "saida": 0.05}],
   "duck": {"folga": 12, "max": 12, "max_grave": 3},
  duck (opcional, esses são os padrões): com voz, o médio/agudo de ambiente + música fica `folga` dB abaixo da voz
  (redução de até `max` dB) e o grave desce no máximo `max_grave` dB (a música não perde o corpo).
   "superficie": "terra", "proibidos": ["..."]}
  superficie (asfalto, terra, areia, grama, agua, madeira, neve): o chão da cena; com ela (ou proibidos) o mixar roda
  `conferir` antes e PARA se algum som for do chão errado (ex.: pneu cantando no asfalto numa estrada de terra).
  Sempre proibido (salvo "permitidos": [...]): avião e jato, que o vento grave imita. O mixar sempre confere.
  camera_lenta: o mundo ABAFA na janela (grave + reverb, entra em `entrada` s e volta SECO em `saida` s, no impacto).
  Evento com "velocidade": 0.4 = som lento e grave (motor/impacto em câmera lenta); "reverso": true = som ao contrário
  que CRESCE e termina em t (sucção antes do impacto); "livre": true = não abafa na câmera lenta (o som do slow-mo);
  "de_arquivo"/"ate_arquivo" = usar só esse trecho do arquivo.
  alinhar: "onset" (padrão: o ATAQUE do som cai em t), "pico" (o pico cai em t; impacto com subida) ou "inicio".
  dur = quanto o som continua DEPOIS de t (a subida antes de t entra sozinha); sem dur, até o fim do arquivo.
  Camadas de um som importante = vários eventos no MESMO t (ataque, corpo, cauda) com db e dur diferentes.
Saída em <pasta do plano>/<saida>/: ambiente.wav, sfx.wav, musica.wav (já com ducking), mix.wav (-14 LUFS) e
previa.mp4 (vídeo + mix). Os stems entram no editor; o plano também vira clipes soltos no DaVinci (subcomando davinci).
"""
import json, math, os, shutil, subprocess, sys

SR = 48000
CACHE = ".medidas_sfx.json"


# ------------------------------------------------------------------ medir sons
def _amostras(arq, sr=8000):
    import numpy as np
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", arq, "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32), sr


def medir(arq):
    """onset = 1º ponto a 50% do máximo do envelope (ataque); pico = ponto máximo; dur = duração total (s)."""
    pasta = os.path.dirname(os.path.abspath(arq)); cache_arq = os.path.join(pasta, CACHE)
    try:
        cache = json.load(open(cache_arq))
    except Exception:
        cache = {}
    chave = f"{os.path.basename(arq)}|{os.path.getsize(arq)}"
    if chave in cache:
        return cache[chave]
    import numpy as np
    x, sr = _amostras(arq); jan = int(sr * 0.005)
    n = max(1, len(x) // jan); env = np.abs(x[:n * jan]).reshape(n, jan).max(axis=1) if len(x) >= jan else np.abs(x)
    mx = float(env.max()) if len(env) else 0.0
    if mx <= 0:
        m = {"onset": 0.0, "pico": 0.0, "dur": round(len(x) / sr, 3)}
    else:
        m = {"onset": round(int(np.argmax(env >= 0.5 * mx)) * jan / sr, 3), "pico": round(int(np.argmax(env)) * jan / sr, 3),
             "dur": round(len(x) / sr, 3)}
    cache[chave] = m
    try:
        json.dump(cache, open(cache_arq, "w"), indent=1)
    except Exception:
        pass
    return m


def preparar(arq, ev):
    """Som com velocidade (asetrate: mais lento = mais grave) e/ou reverso vira um WAV processado (cache ao lado)."""
    v = float(ev.get("velocidade") or 1.0); rev = bool(ev.get("reverso"))
    a, b = ev.get("de_arquivo"), ev.get("ate_arquivo")   # só um trecho de um arquivo longo (ex.: 12-15 s de um rally)
    if v == 1.0 and not rev and a is None and b is None:
        return arq
    pasta = os.path.join(os.path.dirname(os.path.abspath(arq)), "_processados"); os.makedirs(pasta, exist_ok=True)
    nome = (os.path.splitext(os.path.basename(arq))[0] + (f"_{a}-{b}s" if a is not None or b is not None else "") +
            (f"_v{int(v * 100)}" if v != 1.0 else "") + ("_rev" if rev else "") + ".wav")
    dst = os.path.join(pasta, nome)
    if not os.path.exists(dst):
        corte = (["-ss", str(a)] if a is not None else []) + (["-to", str(b)] if b is not None else [])
        f = (f"asetrate={int(SR * v)},aresample={SR}" if v != 1.0 else "anull") + (",areverse" if rev else "")
        subprocess.run(["ffmpeg", "-v", "error", "-y"] + corte + ["-i", arq, "-ar", str(SR), "-af", f, "-c:a", "pcm_s24le", dst], check=True)
    return dst


def _alinhar_padrao(ev):
    return ev.get("alinhar") or ("pico" if ev.get("reverso") else "onset")


# ------------------------------------------------------------------ analisar vídeo
def analisar(video, pasta=None):
    import cv2, numpy as np
    video = os.path.abspath(video); pasta = os.path.abspath(pasta or os.path.splitext(video)[0] + "_som")
    os.makedirs(pasta, exist_ok=True)
    cap = cv2.VideoCapture(video); fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    W = 160; ant = None; hant = None; en, cx, cortes, quadros, fluxo = [], [], [], [], []
    i = 0
    while True:
        ok, q = cap.read()
        if not ok:
            break
        h, w = q.shape[:2]; p = cv2.resize(q, (W, int(W * h / w)))
        g = cv2.GaussianBlur(cv2.cvtColor(p, cv2.COLOR_BGR2GRAY), (5, 5), 0)
        hist = cv2.calcHist([cv2.cvtColor(p, cv2.COLOR_BGR2HSV)], [0, 1], None, [16, 8], [0, 180, 0, 256]); cv2.normalize(hist, hist)
        if ant is None:
            en.append(0.0); cx.append(0.0)
        else:
            if cv2.compareHist(hist, hant, cv2.HISTCMP_CORREL) < 0.55:
                cortes.append(round(i / fps, 3)); en.append(0.0); cx.append(0.0)
            else:
                d = cv2.absdiff(g, ant); m = d > 14; e = float(m.mean()); en.append(e)
                if i % 2 == 0:   # velocidade real do movimento (px/quadro): cai muito na câmera lenta
                    fl = cv2.calcOpticalFlowFarneback(ant, g, None, 0.5, 3, 15, 3, 5, 1.2, 0)
                    fluxo.append((i, float(np.percentile(np.linalg.norm(fl, axis=2), 95))))
                if m.any():
                    xs = np.nonzero(m)[1]; cx.append(float(xs.mean() / m.shape[1] * 2 - 1))
                else:
                    cx.append(0.0)
        ant, hant = g, hist
        quadros.append(i); i += 1
    cap.release()
    n = len(en); t = lambda k: round(k / fps, 3)
    e = np.convolve(np.array(en), np.ones(3) / 3, mode="same") if n >= 3 else np.array(en)
    ref = float(np.percentile(e, 95)) if n else 0.0
    alto, baixo = max(0.012, ref * 0.35), max(0.006, ref * 0.15)
    ev = []
    calma = 0
    jan = max(2, int(fps * 0.15))
    for k in range(1, n - 1):
        calma = calma + 1 if e[k - 1] < baixo else 0
        if e[k] >= alto and e[k - 1] < alto and calma >= int(fps * 0.25):
            ev.append({"t": t(k), "tipo": "entrada", "forca": e[k], "pan": cx[k]})
        eh = e[k] >= e[k - 1] and e[k] >= e[k + 1] and e[k] >= alto
        if eh:
            depois = e[k + 1:k + 1 + jan]
            if len(depois) and depois.min() < e[k] * 0.4:
                ev.append({"t": t(k), "tipo": "batida", "forca": e[k], "pan": cx[k]})
            elif e[k] >= ref * 0.8:
                ev.append({"t": t(k), "tipo": "pico", "forca": e[k], "pan": cx[k]})
    # um evento por 0,25 s (batida > entrada > pico)
    prio = {"batida": 0, "entrada": 1, "pico": 2}; final = []
    for x in sorted(ev, key=lambda x: (prio[x["tipo"]], -x["forca"])):
        if all(abs(x["t"] - y["t"]) >= 0.25 for y in final) and all(abs(x["t"] - c) >= 0.1 for c in cortes):
            final.append(x)
    final.sort(key=lambda x: x["t"]); mxf = max([x["forca"] for x in final] or [1])
    for x in final:
        x["forca"] = round(x["forca"] / mxf, 2); x["pan"] = round(max(-1, min(1, x["pan"])) * 0.8, 2)
    dur = t(n)
    lentas = _camera_lenta(fluxo, fps, cortes)
    cenas = [{"de": a, "ate": b} for a, b in zip([0.0] + cortes, cortes + [dur])]
    audio = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=codec_name", "-of", "csv=p=0", video],
                           capture_output=True, text=True).stdout.strip()
    res = {"video": video, "fps": round(fps, 3), "dur": dur, "tem_audio": bool(audio), "cortes": cortes, "cenas": cenas, "eventos": final,
           "camera_lenta": lentas,
           "energia": [round(float(v), 4) for v in e[::max(1, int(fps / 10))]]}
    json.dump(res, open(os.path.join(pasta, "analise.json"), "w"), indent=1, ensure_ascii=False)
    _folha(video, res, os.path.join(pasta, "folha.png"))
    return res, pasta


def _camera_lenta(fluxo, fps, cortes, minimo=0.7):
    """Janela de câmera lenta provável: logo depois de um movimento forte, a velocidade cai para < 30% por >= `minimo` s
    sem corte de cena, e volta forte no fim (ex.: carro salta, flutua lento, aterrissa). O Gab confirma na folha."""
    if len(fluxo) < 6:
        return []
    ks = [k for k, _ in fluxo]; vs = [v for _, v in fluxo]; jan = int(fps * 0.6) // 2 or 1; res = []; j = 0
    while j < len(vs):
        antes = max(vs[max(0, j - jan):j] or [0])
        if antes > 3.0 and vs[j] < antes * 0.3:
            k = j
            while k < len(vs) and vs[k] < antes * 0.3:
                k += 1
            depois = max(vs[k:k + jan] or [0]); de, ate = ks[j] / fps, ks[min(k, len(ks) - 1)] / fps
            if ate - de >= minimo and depois > antes * 0.5 and not any(de < c < ate for c in cortes):
                res.append({"de": round(de, 2), "ate": round(ate, 2), "antes": round(antes, 1), "durante": round(max(vs[j:k]), 1), "depois": round(depois, 1)})
            j = k
        j += 1
    return res


def _folha(video, res, saida, colunas=4, larg=270):
    """Folha de quadros: início de cada cena + cada evento, com tempo/tipo/pan escritos (para o Gab olhar)."""
    import cv2, numpy as np
    alvos = [(c["de"] + 0.05, "cena") for c in res["cenas"]] + [((l["de"] + l["ate"]) / 2, "CAMERA LENTA?") for l in res.get("camera_lenta", [])] + [(x["t"], f'{x["tipo"]} {x["forca"]:.1f} pan {x["pan"]:+.1f}') for x in res["eventos"]]
    alvos = sorted(alvos)[:32]
    cap = cv2.VideoCapture(video); tiles = []
    for tt, rot in alvos:
        cap.set(cv2.CAP_PROP_POS_MSEC, tt * 1000); ok, q = cap.read()
        if not ok:
            continue
        h, w = q.shape[:2]; q = cv2.resize(q, (larg, int(larg * h / w)))
        cv2.rectangle(q, (0, 0), (larg, 44), (0, 0, 0), -1)
        cv2.putText(q, f"{tt:.2f}s", (6, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(q, rot, (6, 38), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (80, 220, 255), 1, cv2.LINE_AA)
        tiles.append(q)
    cap.release()
    if not tiles:
        return
    hmax = max(t.shape[0] for t in tiles)
    tiles = [cv2.copyMakeBorder(t, 0, hmax - t.shape[0], 0, 0, cv2.BORDER_CONSTANT) for t in tiles]
    while len(tiles) % colunas:
        tiles.append(np.zeros_like(tiles[0]))
    linhas = [np.hstack(tiles[i:i + colunas]) for i in range(0, len(tiles), colunas)]
    cv2.imwrite(saida, np.vstack(linhas))


# ------------------------------------------------------------------ mixar
def _ganhos_pan(p):
    p = max(-1.0, min(1.0, float(p or 0))); a = (p + 1) * math.pi / 4
    return round(math.cos(a) * math.sqrt(2), 4), round(math.sin(a) * math.sqrt(2), 4)


def _caminho(base, arq):
    arq = os.path.expanduser(arq)
    return arq if os.path.isabs(arq) else os.path.join(base, arq)


def _segmento(ev, med, dur_video=1e9):
    """(início na timeline, ponto de entrada no arquivo, duração). O ataque/pico do som cai em t; `dur` = quanto o som
    continua DEPOIS de t (sem dur: até o fim do arquivo)."""
    al = _alinhar_padrao(ev); hit = med["onset"] if al == "onset" else med["pico"] if al == "pico" else 0.0
    # Sobra antes do ataque é CORTADA (bug 14/10/2026: passo entrava 2,7 s antes da pisada tocando o começo do arquivo,
    # riser de 6 s vazava por 3 cenas). Só fica a subida curta: 0,03 s no onset, 0,25 s no pico, ou "subida" no evento.
    pre = float(ev.get("subida", 0.03 if al == "onset" else 0.25 if al == "pico" else 0.0))
    lead = min(hit, pre)
    t = float(ev["t"]); ini = t - lead; corte = hit - lead + max(0.0, -ini); ini = max(0.0, ini)
    fim_arq = med["dur"] - corte
    d = min((t - ini) + float(ev["dur"]), fim_arq) if ev.get("dur") else fim_arq
    return ini, corte, min(d, dur_video - ini)


def _loudness(arq):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", arq, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    li = [l for l in r.splitlines() if l.strip().startswith("I:")]; pk = [l for l in r.splitlines() if l.strip().startswith("Peak:")]
    return (li[-1].split()[1] if li else "?") + " LUFS", (pk[-1].split()[1] if pk else "?") + " dBTP"


def _render(entradas, cadeias, rotulos, saida, dur):
    """entradas: lista de listas de args -i; cadeias: filtros por entrada terminando em [rotulo]. Soma tudo em `saida`."""
    if not rotulos:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"anullsrc=r={SR}:cl=stereo", "-t", str(dur), saida], check=True)
        return
    fc = ";".join(cadeias) + ";" + "".join(f"[{r}]" for r in rotulos) + \
        f"amix=inputs={len(rotulos)}:normalize=0:duration=longest,apad=whole_dur={dur},atrim=0:{dur}[o]"
    args = ["ffmpeg", "-v", "error", "-y"]
    for e in entradas:
        args += e
    fcf = saida + ".filtro.txt"; open(fcf, "w").write(fc)
    subprocess.run(args + ["-filter_complex_script", fcf, "-map", "[o]", "-ar", str(SR), "-c:a", "pcm_s24le", saida], check=True)
    os.remove(fcf)


def _ler_audio(arq):
    """Áudio (ou o áudio de um vídeo) como array float32 (amostras, 2) a 48 kHz."""
    import numpy as np
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", arq, "-map", "0:a:0", "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).reshape(-1, 2).copy()


def _gravar_audio(x, saida):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-c:a", "pcm_f32le", saida],
                   input=x.astype("float32").tobytes(), check=True)


def _duck_por_faixa(cama_arq, voz_arq, saida, folga=12.0, maximo=12.0, max_grave=3.0, corte_hz=250.0):
    """Ducking por faixa (14/10/2026, método da trilha cinematográfica do @iamjeff.ia): a cama (ambiente + música) se
    divide em grave (< corte_hz) e médio/agudo (onde a voz mora). Enquanto a voz fala, o médio/agudo fica pelo menos
    `folga` dB abaixo da voz (até `maximo` dB de redução) e o grave desce no máximo `max_grave` dB, então a música não
    perde o corpo. Ganho por janela de 10 ms (RMS de 50 ms), ataque 15 ms, soltura 300 ms. Só numpy."""
    import numpy as np
    cama, voz = _ler_audio(cama_arq), _ler_audio(voz_arq)
    n = len(cama); voz = np.pad(voz, ((0, max(0, n - len(voz))), (0, 0)))[:n]
    # divisão grave/agudo no domínio da frequência com rampa de 200 a 300 Hz; agudo = cama - grave (soma exata)
    f = np.fft.rfftfreq(n, 1 / SR); k = np.clip((corte_hz * 1.2 - f) / (corte_hz * 0.4), 0, 1)
    grave = np.fft.irfft(np.fft.rfft(cama, axis=0) * k[:, None], n=n, axis=0).astype(np.float32); agudo = cama - grave
    hop, win = SR // 100, SR // 20

    def db(x):
        e = np.convolve((x ** 2).mean(axis=1), np.ones(win) / win, mode="same")[::hop]
        return 10 * np.log10(e + 1e-12)
    vd, ad = db(voz), db(agudo)
    fala = vd > max(vd.max() - 35, -50)                      # janelas com voz (ignora respiro e ruído de fundo)
    alvo = np.where(fala, np.clip((vd - folga) - ad, -maximo, 0), 0.0)
    g = np.zeros_like(alvo); a, r = 1 - np.exp(-1 / 1.5), 1 - np.exp(-1 / 30)   # 15 ms / 300 ms em passos de 10 ms
    for i in range(1, len(alvo)):
        g[i] = g[i - 1] + (a if alvo[i] < g[i - 1] else r) * (alvo[i] - g[i - 1])
    t = np.arange(n) / hop
    ga = 10 ** (np.interp(t, np.arange(len(g)), g) / 20); gg = 10 ** (np.interp(t, np.arange(len(g)), np.maximum(g, -max_grave)) / 20)
    _gravar_audio(agudo * ga[:, None] + grave * gg[:, None], saida)
    return round(float(g.min()), 1)


def _abafar(arq, lentas):
    """Câmera lenta: troca suave do som normal pelo som abafado (grave + reverb) dentro de cada janela e volta SECO no fim
    (o impacto que encerra o slow-mo soa cheio). Edita o stem no lugar."""
    if not lentas:
        return
    ks = []
    for l in lentas:
        de, ate = float(l["de"]), float(l["ate"]); ent, sai = float(l.get("entrada", 0.3)), float(l.get("saida", 0.05))
        ks.append(f"max(0,min(1,(t-{de})/{ent}))*max(0,min(1,({ate}-t)/{sai}))")
    k = "min(1," + "+".join(ks) + ")"
    fc = (f"[0:a]asplit=2[s][m];[s]volume='1-{k}':eval=frame[seco];"
          f"[m]lowpass=f=420,lowpass=f=420,aecho=0.8:0.55:110|230:0.4|0.25,volume='{k}*1.15':eval=frame[abaf];"
          f"[seco][abaf]amix=inputs=2:normalize=0[o]")
    tmp = arq + ".tmp.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", arq, "-filter_complex", fc, "-map", "[o]", "-c:a", "pcm_s24le", tmp], check=True)
    os.replace(tmp, arq)


def mixar(plano_arq, com_voz=True):
    plano = json.load(open(plano_arq)); base = os.path.dirname(os.path.abspath(plano_arq))
    try:                       # trava: som do chão errado ou de algo que não está na cena (avião, jato) não entra
        import transformers  # noqa: F401
        tem_clap = True
    except ImportError:
        tem_clap = False
        print("aviso: sem transformers (CLAP), a conferência de coerência não rodou: pip install --user transformers")
    if tem_clap and not plano.get("sem_conferir"):
        ruins = [r for r in conferir(plano_arq) if r[3]]
        if ruins:
            raise SystemExit("PAROU: som que não combina com a cena (superfície " + str(plano.get("superficie")) + "; avião/jato só com 'permitidos'):\n" +
                             "\n".join(f"  {n} ({a}): {p}" for n, a, _, p in ruins) + "\nTrocar o som (sfx_conferir/conferir) e rodar de novo.")
    video = _caminho(base, plano["video"]); out = _caminho(base, plano.get("saida", "sonorizacao")); os.makedirs(out, exist_ok=True)
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", video], capture_output=True, text=True).stdout)
    fmt = f"aformat=sample_rates={SR}:channel_layouts=stereo"
    lentas = plano.get("camera_lenta") or []
    # --- SFX / foley (camadas = vários eventos no mesmo t); "livre" = som do slow-mo, não abafa
    def eventos(livres):
        ent, cad, rot = [], [], []
        for i, ev in enumerate(plano.get("eventos", [])):
            if bool(ev.get("livre")) != livres:
                continue
            arq = preparar(_caminho(base, ev["arquivo"]), ev); ini, corte, d = _segmento(ev, medir(arq), dur)
            if d <= 0.02:
                continue
            gl, gr = _ganhos_pan(ev.get("pan")); f = min(float(ev.get("fade", 0.12)), d / 2); ms = int(ini * 1000)
            fi = min(float(ev.get("fade_in", 0)), d / 2)
            ent.append(["-i", arq])
            cad.append(f"[{len(ent)-1}:a]{fmt},atrim={corte}:{corte + d},asetpts=PTS-STARTPTS," + (f"afade=t=in:d={fi}," if fi else "") +
                       f"afade=t=out:st={d - f}:d={f},volume={ev.get('db', -14)}dB,pan=stereo|c0={gl}*c0|c1={gr}*c1,adelay={ms}|{ms}[e{i}]")
            rot.append(f"e{i}")
        return ent, cad, rot
    sfx = os.path.join(out, "sfx.wav")
    _render(*eventos(False), sfx, dur)
    _abafar(sfx, lentas)
    livres = [e for e in plano.get("eventos", []) if e.get("livre")]
    if livres:
        sl = os.path.join(out, "_sfx_livre.wav"); _render(*eventos(True), sl, dur); tmp = sfx + ".tmp.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", sfx, "-i", sl, "-filter_complex", "amix=inputs=2:normalize=0", "-c:a", "pcm_s24le", tmp], check=True)
        os.replace(tmp, sfx); os.remove(sl)
    # --- ambiente (loop, fade nas pontas)
    ent, cad, rot = [], [], []
    for i, a in enumerate(plano.get("ambiente", [])):
        de, ate = float(a.get("de", 0)), float(a.get("ate", dur)); d = max(0.1, min(ate, dur) - de); f = min(float(a.get("fade", 1.0)), d / 2)
        gl, gr = _ganhos_pan(a.get("pan")); ms = int(de * 1000)
        ent.append(["-stream_loop", "-1", "-i", _caminho(base, a["arquivo"])])
        cad.append(f"[{len(ent)-1}:a]{fmt},atrim=0:{d},asetpts=PTS-STARTPTS,afade=t=in:d={f},afade=t=out:st={d - f}:d={f},"
                   f"volume={a.get('db', -24)}dB,pan=stereo|c0={gl}*c0|c1={gr}*c1,adelay={ms}|{ms}[a{i}]")
        rot.append(f"a{i}")
    _render(ent, cad, rot, os.path.join(out, "ambiente.wav"), dur)
    _abafar(os.path.join(out, "ambiente.wav"), lentas)
    # --- música
    mus = plano.get("musica"); mus_arq = os.path.join(out, "musica.wav")
    if mus:
        de = float(mus.get("de", 0)); ms = int(de * 1000); d = dur - de
        _render([["-ss", str(mus.get("inicio_arquivo", 0)), "-i", _caminho(base, mus["arquivo"])]],
                [f"[0:a]{fmt},atrim=0:{d},asetpts=PTS-STARTPTS,afade=t=in:d=0.5,afade=t=out:st={max(0, d - 1.5)}:d=1.5,volume={mus.get('db', -18)}dB,adelay={ms}|{ms}[m]"],
                ["m"], mus_arq, dur)
        _abafar(mus_arq, lentas)
    # --- voz (áudio do próprio vídeo) e ducking de ambiente + música sob a voz
    tem_voz = com_voz and plano.get("voz", True) and bool(subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0", video], capture_output=True, text=True).stdout.strip())
    cama = [os.path.join(out, "ambiente.wav")] + ([mus_arq] if mus else [])
    cama_arq = os.path.join(out, "_cama.wav"); reducao = None
    _render([["-i", c] for c in cama], [f"[{k}:a]anull[c{k}]" for k in range(len(cama))], [f"c{k}" for k in range(len(cama))], cama_arq, dur)
    if tem_voz:   # ducking por faixa: abaixa o médio/agudo da cama sob a voz, o grave quase não mexe
        d = plano.get("duck") if isinstance(plano.get("duck"), dict) else {}
        camad = os.path.join(out, "_cama_duck.wav")
        reducao = _duck_por_faixa(cama_arq, video, camad, d.get("folga", 12.0), d.get("max", 12.0), d.get("max_grave", 3.0))
        os.replace(camad, cama_arq)
    args = ["ffmpeg", "-v", "error", "-y", "-i", cama_arq, "-i", os.path.join(out, "sfx.wav")]
    if tem_voz:
        args += ["-i", video]
        fc = f"[2:a]{fmt}[voz];[voz][0:a][1:a]amix=inputs=3:normalize=0"
    else:
        fc = "[0:a][1:a]amix=inputs=2:normalize=0"
    fc += f",atrim=0:{dur},aresample={SR}[o]"
    mix = os.path.join(out, "mix.wav"); bruto = os.path.join(out, "_mix_bruto.wav")
    subprocess.run(args + ["-filter_complex", fc, "-map", "[o]", "-c:a", "pcm_f32le", bruto], check=True)
    # -14 LUFS em duas passadas: mede, corrige o ganho e segura o pico em -1,5 dBTP (o loudnorm de uma passada erra ~1,5 dB)
    try:
        ganho = -14.0 - float(_loudness(bruto)[0].split()[0])
    except ValueError:
        ganho = 0.0
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", bruto, "-af", f"volume={ganho:.2f}dB,alimiter=limit=0.84:attack=2:release=60:level=disabled",
                    "-ar", str(SR), "-c:a", "pcm_s24le", mix], check=True)
    os.remove(bruto); os.remove(cama_arq)
    previa = os.path.join(out, "previa.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-i", mix, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-shortest", previa], check=True)
    li, pk = _loudness(mix)
    return {"pasta": out, "stems": ["ambiente.wav", "sfx.wav"] + (["musica.wav"] if mus else []), "mix": mix, "previa": previa,
            "voz": tem_voz, "duck_max_db": reducao, "loudness": li, "pico": pk, "eventos": len(plano.get("eventos", []))}


# ------------------------------------------------------------------ conferir (o som combina com a cena?)
SUPERFICIE = {  # o que NÃO pode tocar em cada chão (rótulos do CLAP em sfx_conferir.ROTULOS)
    "terra": ["tires squealing on asphalt", "footsteps on wood floor"],
    "areia": ["tires squealing on asphalt", "footsteps on wood floor"],
    "grama": ["tires squealing on asphalt", "footsteps on wood floor"],
    "neve": ["tires squealing on asphalt", "footsteps on wood floor"],
    "agua": ["tires squealing on asphalt", "footsteps on wood floor", "footsteps on gravel"],
    "asfalto": ["car skidding on gravel and dirt", "footsteps on gravel"],
    "madeira": ["footsteps on gravel", "car skidding on gravel and dirt"],
}


FORA_DE_CENA = ["airplane flying overhead", "jet engine roar"]   # proibidos por padrão: só com "permitidos" no plano


def conferir(plano_arq, limite=0.38):
    """Classifica cada som do plano com o CLAP (scripts/sfx_conferir.py) e devolve [(nota, arquivo, top3, problema)].
    Problema = rótulo proibido (pela superfície ou pela lista do plano) em 1º lugar ou acima de `limite`."""
    import sfx_conferir as C
    plano = json.load(open(plano_arq)); base = os.path.dirname(os.path.abspath(plano_arq))
    proib = (set(plano.get("proibidos", [])) | set(SUPERFICIE.get(plano.get("superficie", ""), [])) |
             set(FORA_DE_CENA)) - set(plano.get("permitidos", []))
    faltam = proib - set(C.ROTULOS)
    if faltam:
        C.ROTULOS += sorted(faltam)
    top = C._clap(); res = []; vistos = {}
    itens = [(a.get("nota", "ambiente"), a) for a in plano.get("ambiente", [])] + [(e.get("nota", ""), e) for e in plano.get("eventos", [])]
    for nota, it in itens:
        arq = preparar(_caminho(base, it["arquivo"]), it)
        if arq not in vistos:
            pares = [x.rsplit(" ", 1) for x in top(C._pcm(arq, 0, 10), n=len(C.ROTULOS)).split(" | ")]
            vistos[arq] = [(r, float(v)) for r, v in pares]
        cl = vistos[arq]
        prob = [f"{r} {v:.2f}" for i, (r, v) in enumerate(cl) if r in proib and (i == 0 or v >= limite)]
        res.append((nota, os.path.basename(arq), " | ".join(f"{r} {v:.2f}" for r, v in cl[:3]), "; ".join(prob)))
    return res


# ------------------------------------------------------------------ DaVinci
def davinci(plano_arq, pasta_sfx):
    """Escreve <pasta_sfx>/plano_sfx.txt (formato de resolve_lib.colocar_plano_sfx) e copia os sons como WAV 48 kHz.
    O tempo de cada linha já desconta o ataque (onset/pico) do som. O pan fica no Inspector (a API não define pan)."""
    plano = json.load(open(plano_arq)); base = os.path.dirname(os.path.abspath(plano_arq)); os.makedirs(pasta_sfx, exist_ok=True)
    linhas = []

    def wav(arq, corte=0.0):
        nome = os.path.splitext(os.path.basename(arq))[0].replace(" ", "_") + (f"_a{int(corte * 1000)}" if corte > 0 else "")
        dst = os.path.join(pasta_sfx, nome + ".wav")
        if not os.path.exists(dst):   # som que entra no meio: arquivo já recortado (o DaVinci coloca do início do arquivo)
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(corte), "-i", arq, "-ar", str(SR), "-c:a", "pcm_s24le", dst], check=True)
        return nome
    for a in plano.get("ambiente", []):
        de, ate = float(a.get("de", 0)), float(a["ate"]); nome = wav(_caminho(base, a["arquivo"]))
        linhas.append((de, f"{de:.2f}s A3 {nome} {int(a.get('db', -24))}dB {ate - de:.1f}s: ambiente"))
    for ev in plano.get("eventos", []):
        arq = preparar(_caminho(base, ev["arquivo"]), ev); ini, corte, d = _segmento(ev, medir(arq)); nome = wav(arq, corte)
        linhas.append((ini, f"{ini:.2f}s A3 {nome} {int(ev.get('db', -14))}dB {d:.1f}s: {ev.get('nota', '')} (pan {ev.get('pan', 0)})"))
    open(os.path.join(pasta_sfx, "plano_sfx.txt"), "w").write("\n".join(l for _, l in sorted(linhas)) + "\n")
    return os.path.join(pasta_sfx, "plano_sfx.txt"), len(linhas)


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        raise SystemExit(__doc__)
    if a[0] == "analisar" and len(a) >= 2:
        res, pasta = analisar(a[1], a[a.index("--pasta") + 1] if "--pasta" in a else None)
        print(f"{len(res['eventos'])} eventos, {len(res['cenas'])} cena(s), {res['dur']} s, áudio no vídeo: {res['tem_audio']}")
        for l in res["camera_lenta"]:
            print(f"  CÂMERA LENTA provável {l['de']:.2f}-{l['ate']:.2f}s (movimento {l['antes']} -> {l['durante']} -> {l['depois']}): usar camera_lenta no plano")
        for x in res["eventos"]:
            print(f"  {x['t']:6.2f}s  {x['tipo']:8s} força {x['forca']:.2f}  pan {x['pan']:+.2f}")
        print("folha:", os.path.join(pasta, "folha.png"))
    elif a[0] == "medir" and len(a) >= 2:
        arqs = []
        for p in a[1:]:
            arqs += sorted(os.path.join(p, f) for f in os.listdir(p) if f.lower().endswith((".wav", ".mp3", ".aif", ".aiff", ".m4a"))) if os.path.isdir(p) else [p]
        for f in arqs:
            m = medir(f); print(f"  {os.path.basename(f):40s} ataque {m['onset']:5.2f}s  pico {m['pico']:5.2f}s  dur {m['dur']:6.2f}s")
    elif a[0] == "mixar" and len(a) >= 2:
        print(json.dumps(mixar(a[1], "--sem-voz" not in a), indent=1, ensure_ascii=False))
    elif a[0] == "conferir" and len(a) >= 2:
        rs = conferir(a[1])
        for n, arq, t3, p in rs:
            print(f"  {'X' if p else 'ok'}  {n[:38]:38s} {arq[:28]:28s} {t3}" + (f"\n      PROIBIDO AQUI: {p}" if p else ""))
        if any(r[3] for r in rs):
            sys.exit(1)
    elif a[0] == "davinci" and len(a) >= 3:
        print(*davinci(a[1], a[2]))
    else:
        raise SystemExit(__doc__)
