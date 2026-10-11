"""Preparação de mídia com ffmpeg (antes de importar no DaVinci).

  python3 midia.py preparar_take entrada saida.mp4 [1080x1920]   -> converte 4K/ProRes pesado para 1080 H.264, sem áudio
  python3 midia.py audio48k entrada saida.wav                      -> converte para 48 kHz
  python3 midia.py green arquivo                                   -> % de verde chapado (detecta green screen)
  python3 midia.py iphone arquivo                                  -> True se for vídeo de iPhone
  python3 midia.py info arquivo                                    -> codec, resolução, fps, duração
"""
import json, subprocess, sys


def info(f):
    j = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries",
        "stream=codec_name,codec_type,width,height,r_frame_rate,sample_rate,bit_rate:format=duration,size",
        "-of", "json", f], capture_output=True, text=True).stdout)
    v = next((s for s in j["streams"] if s["codec_type"] == "video"), {})
    a = next((s for s in j["streams"] if s["codec_type"] == "audio"), {})
    return {"codec": v.get("codec_name"), "w": v.get("width"), "h": v.get("height"), "fps": v.get("r_frame_rate"),
            "audio_hz": a.get("sample_rate"), "dur": float(j["format"].get("duration", 0)),
            "mb": round(int(j["format"].get("size", 0)) / 1e6, 1), "bitrate": int(v.get("bit_rate") or 0)}


def eh_iphone(f):
    """True se o arquivo veio de iPhone: metadado make/model da Apple (QuickTime) ou HEVC em HLG/Dolby Vision (padrão do iPhone)."""
    j = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries",
        "format_tags:stream_tags:stream=codec_name,color_transfer,color_primaries", "-of", "json", f],
        capture_output=True, text=True).stdout or "{}")
    tags = {k.lower(): str(v) for k, v in (j.get("format", {}).get("tags") or {}).items()}
    for s in j.get("streams", []): tags.update({k.lower(): str(v) for k, v in (s.get("tags") or {}).items()})
    txt = " ".join(tags.values()).lower()
    if "iphone" in txt or tags.get("com.apple.quicktime.make", "").lower() == "apple": return True
    v = next((s for s in j.get("streams", []) if s.get("codec_name") in ("hevc", "h264")), {})
    return v.get("codec_name") == "hevc" and v.get("color_transfer") in ("arib-std-b67", "smpte2084")


def pesado(f):
    i = info(f); return (i["w"] or 0) > 1920 or (i["h"] or 0) > 1920 or i["codec"] in ("prores", "dnxhd") or i["bitrate"] > 40e6


def preparar_take(ent, sai, res="1080x1920"):
    w, h = res.split("x")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", ent, "-vf",
                    f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}",
                    "-c:v", "libx264", "-crf", "18", "-preset", "fast", "-an", sai], check=True)
    return sai


def audio48k(ent, sai):
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", ent, "-ar", "48000", sai], check=True); return sai


def green(f, amostras=3):
    """Fração média de pixels verde-chroma em quadros amostrados (> 0.25 = provável green screen)."""
    from PIL import Image
    import io
    d = info(f)["dur"] or 1; tot = 0
    for k in range(amostras):
        img = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", str(d * (k + 1) / (amostras + 1)), "-i", f,
                              "-frames:v", "1", "-vf", "scale=96:-1", "-f", "image2pipe", "-vcodec", "png", "-"],
                             capture_output=True).stdout
        px = list(Image.open(io.BytesIO(img)).convert("RGB").getdata())
        tot += sum(1 for r, g, b in px if g > 120 and g > r * 1.4 and g > b * 1.4) / len(px)
    return round(tot / amostras, 3)


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: print(__doc__); sys.exit()
    if a[0] == "preparar_take": print(preparar_take(a[1], a[2], a[3] if len(a) > 3 else "1080x1920"))
    elif a[0] == "audio48k": print(audio48k(a[1], a[2]))
    elif a[0] == "green": print(green(a[1]))
    elif a[0] == "iphone": print(eh_iphone(a[1]))
    elif a[0] == "info": print(json.dumps(info(a[1]), ensure_ascii=False))
