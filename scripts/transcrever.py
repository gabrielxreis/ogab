"""Transcrição da narração com o tempo de cada palavra, escolhendo o caminho pela versão do DaVinci.

Uso:
  python3 transcrever.py <audio.wav> <saida/transcricao.json> [--motor auto|davinci|whisper] [--idioma pt]
  python3 transcrever.py <saida/transcricao.json> --clipe "<nome do clipe no Media Pool>"
        -> lê a transcrição que já foi feita no DaVinci naquele clipe (gravação de apresentador: PREFERIR esta)
  python3 transcrever.py --versao        -> mostra a versão do DaVinci e qual motor seria usado

Motores:
  davinci  MediaPoolItem.TranscribeAudio() + GetTranscription() (a leitura só existe no DaVinci 21.1+).
           O áudio precisa estar no Media Pool do projeto aberto (procura pelo nome do arquivo).
  whisper  Whisper local, grátis, no próprio Mac: mlx-whisper em Apple Silicon, faster-whisper em Intel.
           Na primeira vez baixa o modelo (~1,6 GB). Instala com: pip3 install --user mlx-whisper (ou faster-whisper).
  auto     (padrão) davinci se a versão for 21.1 ou mais nova, senão whisper.

Saída (a mesma que o legendas.py lê): {"motor": ..., "language": ..., "segments": [{"start", "end", "text",
"words": [{"text", "start", "end"}]}]}. No motor whisper os tempos são em segundos; no davinci, timecode
HH:MM:SS:FF como o Resolve devolve.
"""
import json, os, platform, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

APP = "/Applications/DaVinci Resolve/DaVinci Resolve.app"
API = "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting"
MIN_TRANSCRICAO = (21, 1)   # MediaPoolItem.GetTranscription
MIN_AUDIO = (20, 2, 2)      # AppendToTimeline só áudio com trackIndex corrigido
MODELO_MLX = "mlx-community/whisper-large-v3-turbo"
MODELO_FW = "large-v3-turbo"


def _resolve():
    os.environ.setdefault("RESOLVE_SCRIPT_API", API)
    os.environ.setdefault("RESOLVE_SCRIPT_LIB", APP + "/Contents/Libraries/Fusion/fusionscript.so")
    sys.path.append(API + "/Modules/")
    try:
        import DaVinciResolveScript as dvr
        return dvr.scriptapp("Resolve")
    except Exception:
        return None


def versao_davinci():
    """(maior, menor, patch) do DaVinci instalado. Tenta a API (Resolve aberto); senão lê o Info.plist do app."""
    r = _resolve()
    if r:
        try:
            v = r.GetVersion()
            return tuple(int(x) for x in v[:3])
        except Exception:
            pass
    try:
        s = subprocess.run(["defaults", "read", APP + "/Contents/Info", "CFBundleShortVersionString"],
                           capture_output=True, text=True).stdout.strip()
        partes = [int(x) for x in s.split(".")[:3] if x.isdigit()]
        return tuple(partes + [0] * (3 - len(partes)))
    except Exception:
        return None


def motor_auto():
    v = versao_davinci()
    return ("davinci" if v and v[:2] >= MIN_TRANSCRICAO else "whisper"), v


def via_davinci(audio, idioma):
    r = _resolve()
    if not r:
        raise SystemExit("DaVinci fechado ou sem scripting: abra o projeto ou use --motor whisper")
    mp = r.GetProjectManager().GetCurrentProject().GetMediaPool()
    alvo = os.path.basename(audio)
    caminho = os.path.realpath(os.path.abspath(audio))

    def busca(pasta):
        # pelo CAMINHO completo: vários vídeos usam o mesmo nome (narracoes/audio.wav) e comparar só o nome
        # devolvia a transcrição de outro vídeo (bug de 11/10/2026)
        for c in pasta.GetClipList() or []:
            fp = c.GetClipProperty("File Path") or ""
            if fp and os.path.realpath(fp) == caminho:
                return c
        for sub in pasta.GetSubFolderList() or []:
            achou = busca(sub)
            if achou:
                return achou
    item = busca(mp.GetRootFolder())
    if not item:
        item = (mp.ImportMedia([os.path.abspath(audio)]) or [None])[0]
    if not item:
        raise SystemExit(f"não achei nem consegui importar {alvo} no Media Pool")
    # TranscribeAudio volta False fora das páginas Media/Cut/Edit (ex.: DaVinci parado na Deliver) e o resultado
    # chega segundos depois (relato 16/10/2026): abrir a Edit e esperar até 3 min
    if r.GetCurrentPage() not in ("media", "cut", "edit"):
        r.OpenPage("edit"); time.sleep(2)
    tr = item.GetTranscription()
    if not tr or not tr.get("segments"):
        item.TranscribeAudio()
        for _ in range(90):
            tr = item.GetTranscription()
            if tr and tr.get("segments"): break
            time.sleep(2)
    if not tr or not tr.get("segments"):
        raise SystemExit("o DaVinci não devolveu transcrição (original offline? ver PROCESSO.md); use --motor whisper")
    tr["motor"] = "davinci"
    return tr


def via_clipe(nome_clipe):
    """Lê a transcrição que o usuário JÁ fez no DaVinci num clipe do Media Pool (sem transcrever de novo).
    Tempos em timecode do clipe -> segundos."""
    r = _resolve()
    if not r:
        raise SystemExit("DaVinci fechado ou sem scripting")
    mp = r.GetProjectManager().GetCurrentProject().GetMediaPool()

    def busca(pasta):
        for c in pasta.GetClipList() or []:
            if c.GetName() == nome_clipe:
                return c
        for sub in pasta.GetSubFolderList() or []:
            achou = busca(sub)
            if achou:
                return achou
    item = busca(mp.GetRootFolder())
    if not item:
        raise SystemExit(f"clipe {nome_clipe!r} não está no Media Pool")
    tr = item.GetTranscription()
    if not tr or not tr.get("segments"):
        raise SystemExit(f"o clipe {nome_clipe!r} ainda não tem transcrição no DaVinci (clique direito > Transcribe)")
    fps = float(item.GetClipProperty("FPS") or 30)
    # palavras vêm no timecode DA CÂMERA (ex.: 06:15:36;24, drop frame em 29,97): descontar o Start TC do clipe para
    # virar segundos do arquivo (bug 15/10/2026: sem isso os tempos saíam em horas e ';' quebrava o split)
    from silencios import tc_quadros
    ini = tc_quadros(item.GetClipProperty("Start TC") or "00:00:00:00", fps)
    def seg(tc):
        if isinstance(tc, (int, float)): return float(tc)
        return (tc_quadros(tc, fps) - ini) / fps
    segs = []
    for s_ in tr["segments"]:
        ws = [{"text": w["text"].strip(), "start": round(seg(w["start"]), 3), "end": round(seg(w["end"]), 3)}
              for w in s_.get("words", []) if w["text"].strip() and w["text"].strip() != "(...)"]
        if ws:
            segs.append({"start": ws[0]["start"], "end": ws[-1]["end"], "text": " ".join(w["text"] for w in ws), "words": ws})
    return {"language": tr.get("language", "pt"), "motor": f"davinci-clipe ({nome_clipe})", "segments": segs}


def via_whisper(audio, idioma):
    if platform.machine() == "arm64":
        try:
            import mlx_whisper
        except ImportError:
            raise SystemExit("falta o Whisper local: pip3 install --user mlx-whisper  (ou rode o install.sh de novo)")
        res = mlx_whisper.transcribe(audio, path_or_hf_repo=MODELO_MLX, language=idioma,
                                     word_timestamps=True, verbose=False)
        segs = res["segments"]
        lang = res.get("language", idioma)
        conv = lambda w: {"text": w["word"].strip(), "start": round(w["start"], 3), "end": round(w["end"], 3)}
        segments = [{"start": round(s["start"], 3), "end": round(s["end"], 3), "text": s["text"].strip(),
                     "words": [conv(w) for w in s.get("words", [])]} for s in segs]
    else:
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            raise SystemExit("falta o Whisper local: pip3 install --user faster-whisper  (ou rode o install.sh de novo)")
        # Áudio decodificado pelo ffmpeg e entregue como array: o PyAV de algumas instalações quebra ao abrir o arquivo
        # ("metadata_errors"). GPU NVIDIA primeiro em int8_float16 (cabe com o DaVinci aberto ocupando ~3,5 GB; 9 min de
        # áudio em ~30 s), CPU int8 se faltar CUDA/memória (relato de 15/10/2026, Windows + RTX 4060 Ti).
        import numpy as np
        pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", audio, "-f", "s16le", "-ac", "1", "-ar", "16000", "-"],
                             capture_output=True, check=True).stdout
        onda = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768.0
        it = info = None
        for dev, ct in (("cuda", "int8_float16"), ("cpu", "int8")):
            try:
                modelo = WhisperModel(MODELO_FW, device=dev, compute_type=ct)
                it, info = modelo.transcribe(onda, language=idioma, word_timestamps=True)
                it = list(it)   # a transcrição roda aqui: erro de CUDA/memória aparece agora, não depois
                break
            except Exception as e:
                if dev == "cpu": raise
                print(f"Whisper na GPU não rodou ({str(e)[:80]}); usando a CPU", file=sys.stderr)
        lang = info.language
        segments = [{"start": round(s.start, 3), "end": round(s.end, 3), "text": s.text.strip(),
                     "words": [{"text": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3)}
                               for w in (s.words or [])]} for s in it]
    return {"motor": "whisper", "language": lang, "segments": segments}


def main(a):
    if "--versao" in a:
        m, v = motor_auto()
        print("DaVinci:", ".".join(map(str, v)) if v else "não encontrado")
        print("Transcrição:", m, "(DaVinci 21.1+ lê a própria transcrição; abaixo disso usa o Whisper local)")
        if v and v < MIN_AUDIO:
            print("AVISO: abaixo do 20.2.2 a API pode errar a trilha ao colocar áudio sozinho; conferir A1/A2 na timeline.")
        return
    if "--clipe" in a:   # transcrição que o usuário já fez no DaVinci (preferida para gravação de apresentador)
        saida = a[0]; tr = via_clipe(a[a.index("--clipe") + 1])
        os.makedirs(os.path.dirname(os.path.abspath(saida)), exist_ok=True)
        json.dump(tr, open(saida, "w"), ensure_ascii=False, indent=1)
        print(f"{saida}: {sum(len(s_['words']) for s_ in tr['segments'])} palavras ({tr['motor']})"); return
    if len(a) < 2:
        raise SystemExit(__doc__)
    audio, saida = a[0], a[1]
    motor = a[a.index("--motor") + 1] if "--motor" in a else "auto"
    idioma = a[a.index("--idioma") + 1] if "--idioma" in a else "pt"
    if motor == "auto":
        motor, v = motor_auto()
        print(f"DaVinci {'.'.join(map(str, v)) if v else '?'}: usando {motor}")
    tr = via_davinci(audio, idioma) if motor == "davinci" else via_whisper(audio, idioma)
    os.makedirs(os.path.dirname(os.path.abspath(saida)), exist_ok=True)
    json.dump(tr, open(saida, "w"), ensure_ascii=False, indent=1)
    n = sum(len(s["words"]) for s in tr["segments"])
    print(f"{saida}: {len(tr['segments'])} trechos, {n} palavras ({tr['motor']})")


if __name__ == "__main__":
    main(sys.argv[1:])
