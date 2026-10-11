"""Baixa vídeo do YouTube (e outros sites que o yt-dlp aceita) para usar como b-roll:
reportagem, cena histórica/pública citada na fala (ex.: 11 de setembro), discurso, evento.

  python3 baixar_video.py buscar "<termos>" [--n 5]
        -> lista título, canal, duração, link (não baixa nada)
  python3 baixar_video.py baixar <url> <pasta_brolls> <nome> [--de 12.5 --ate 18] [--max 1080]
        -> baixa só o trecho (ou o vídeo inteiro sem --de/--ate) em MP4 H.264, sem áudio por padrão
           (--com-audio para manter), e anota a origem em <pasta do vídeo>/links.txt

Precisa do yt-dlp e do ffmpeg (install.sh instala os dois). Tempos em segundos ou mm:ss.
"""
import json, os, re, shutil, subprocess, sys, datetime


def _seg(x):
    if x is None:
        return None
    if ":" in str(x):
        p = [float(v) for v in str(x).split(":")]
        return sum(v * 60 ** i for i, v in enumerate(reversed(p)))
    return float(x)


def _ytdlp():
    exe = shutil.which("yt-dlp")
    if not exe:
        raise SystemExit("yt-dlp não encontrado: brew install yt-dlp (ou rode o install.sh)")
    return exe


def buscar(termos, n=5):
    out = subprocess.run([_ytdlp(), f"ytsearch{n}:{termos}", "--flat-playlist", "-j", "--no-warnings"],
                         capture_output=True, text=True, timeout=120).stdout
    res = []
    for linha in out.splitlines():
        d = json.loads(linha)
        dur = d.get("duration") or 0
        res.append({"titulo": d.get("title"), "canal": d.get("channel") or d.get("uploader"),
                    "duracao": f"{int(dur//60)}:{int(dur%60):02d}", "url": d.get("url") or f"https://www.youtube.com/watch?v={d.get('id')}"})
        print(f"{res[-1]['duracao']:>6}  {res[-1]['canal']}  |  {res[-1]['titulo']}\n        {res[-1]['url']}")
    return res


def baixar(url, pasta, nome, de=None, ate=None, maxh=1080, com_audio=False):
    os.makedirs(pasta, exist_ok=True)
    de, ate = _seg(de), _seg(ate)
    destino = os.path.join(pasta, nome + ".mp4")
    tmp = os.path.join(pasta, f"_tmp_{nome}.%(ext)s")
    cmd = [_ytdlp(), url, "--no-playlist", "--no-warnings", "-f",
           f"bv*[height<={maxh}][vcodec^=avc1]+ba/bv*[height<={maxh}]+ba/b[height<={maxh}]/b",
           "--merge-output-format", "mp4", "-o", tmp]
    if de is not None or ate is not None:
        cmd += ["--download-sections", f"*{de or 0}-{ate if ate is not None else 'inf'}", "--force-keyframes-at-cuts"]
    for tentativa in range(3):
        if subprocess.run(cmd + ["--retries", "5"]).returncode == 0:
            break
    else:
        raise SystemExit("yt-dlp falhou 3 vezes (vídeo privado/bloqueado? atualize: brew upgrade yt-dlp)")
    baixado = next(os.path.join(pasta, f) for f in os.listdir(pasta) if f.startswith(f"_tmp_{nome}."))
    # normaliza para o DaVinci: H.264, yuv420p, sem áudio (a não ser que peça)
    enc = ["ffmpeg", "-y", "-loglevel", "error", "-i", baixado, "-c:v", "libx264", "-preset", "medium",
           "-crf", "16", "-pix_fmt", "yuv420p"]
    enc += ["-c:a", "aac", "-b:a", "192k"] if com_audio else ["-an"]
    subprocess.run(enc + [destino], check=True)
    os.remove(baixado)
    info = json.loads(subprocess.run([_ytdlp(), url, "-j", "--no-warnings", "--no-playlist"],
                                     capture_output=True, text=True).stdout or "{}")
    links = os.path.join(os.path.dirname(os.path.abspath(pasta.rstrip("/"))), "links.txt")
    with open(links, "a") as f:
        f.write(f"{datetime.date.today()}  {nome}.mp4  <-  {info.get('title','?')} | {info.get('channel') or info.get('uploader','?')} | "
                f"{url}  trecho {de or 0}-{ate if ate is not None else 'fim'} s\n")
    print(f"ok: {destino}")
    return destino


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] not in ("buscar", "baixar"):
        print(__doc__); sys.exit(1)
    def opt(k, d=None):
        return a[a.index(k) + 1] if k in a else d
    if a[0] == "buscar":
        buscar(a[1], int(opt("--n", 5)))
    else:
        baixar(a[1], a[2], a[3], opt("--de"), opt("--ate"), int(opt("--max", 1080)), "--com-audio" in a)
