"""Confere o desenho de som SEM ouvir (regra do usuário, 12/10/2026: "o sfx não tá preenchendo, tem whoosh que não combina").

  python3 sfx_conferir.py arquivos <pasta_wav>                 o que cada som É de verdade (CLAP), não o título do Artlist
  python3 sfx_conferir.py densidade <mix.wav> [ref.mp4]        % do tempo com som (REF de motion fica ~95% acima de -40 dB)
  python3 sfx_conferir.py trechos <mix.wav> "ini-fim:nome" ... o que cada trecho do mix parece (praia soa praia? algo soa terror?)
  python3 sfx_conferir.py sincronia <mix.wav> t1 t2 ...         distância de cada movimento ao ataque de som mais próximo

CLAP = laion/clap-htsat-unfused (pip install --user transformers; baixa ~600 MB na 1ª vez).
"""
import sys, subprocess, glob, os
import numpy as np

ROTULOS = ["air whoosh swoosh", "glitch digital distortion", "keyboard typing", "camera shutter click", "paper card sliding",
           "cinematic boom impact", "rising riser tension", "reverse swell", "notification pop sound", "mouse click",
           "computer beeps and blips", "magic shimmer chimes sparkle", "choir singing pad", "horror scary hit",
           "dark drone ambience", "warm bright hopeful ambient pad", "ocean waves on beach", "lake water lapping with birds",
           "birds chirping outdoors", "crowd of people chatting", "quiet room tone", "city street traffic ambience",
           "old tv turning on static", "fabric bag rustling", "book pages flipping", "stick swinging", "stamp thud hit",
           "tires squealing on asphalt", "car skidding on gravel and dirt", "car engine revving", "footsteps on gravel",
           "footsteps on wood floor", "splashing water", "wind blowing",
           "airplane flying overhead", "jet engine roar"]


def _pcm(f, ini=None, fim=None, sr=48000):
    cmd = ["ffmpeg", "-v", "error"] + (["-ss", str(ini)] if ini is not None else []) + ["-i", f]
    cmd += (["-t", str(fim - ini)] if fim is not None else []) + ["-vn", "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.float32)


def _clap():
    import torch
    from transformers import ClapModel, ClapProcessor
    m = ClapModel.from_pretrained("laion/clap-htsat-unfused").eval(); p = ClapProcessor.from_pretrained("laion/clap-htsat-unfused")
    with torch.no_grad():
        te = m.get_text_features(**p(text=ROTULOS, return_tensors="pt", padding=True)); te = getattr(te, "pooler_output", te)
        te = te / te.norm(dim=-1, keepdim=True)

    def top(a, n=3):
        with torch.no_grad():
            ae = m.get_audio_features(**p(audio=[a], sampling_rate=48000, return_tensors="pt")); ae = getattr(ae, "pooler_output", ae)
            s = (ae / ae.norm(dim=-1, keepdim=True) @ te.T)[0].numpy()
        return " | ".join(f"{ROTULOS[i]} {s[i]:.2f}" for i in s.argsort()[::-1][:n])
    return top


def _db(a, h):
    return 20 * np.log10(np.array([np.sqrt((a[i:i + h] ** 2).mean()) for i in range(0, len(a) - h, h)]) + 1e-9)


if __name__ == "__main__":
    modo, alvo, resto = sys.argv[1], sys.argv[2], sys.argv[3:]
    if modo == "arquivos":
        top = _clap()
        for f in sorted(glob.glob(os.path.join(alvo, "*.wav"))):
            print(f"{os.path.basename(f)[:-4]:22s} {top(_pcm(f, 0, 10))}", flush=True)
    elif modo == "trechos":
        top = _clap(); a = _pcm(alvo)
        for r in resto:
            faixa, nome = r.split(":", 1); i, f = map(float, faixa.split("-"))
            print(f"{nome:24s} {top(a[int(i * 48000):int(f * 48000)])}", flush=True)
    elif modo == "densidade":
        for f in [alvo] + resto:
            d = _db(_pcm(f), 4800)
            print(f"{os.path.basename(f)[:24]:24s} acima -40 dB: {(d > -40).mean():.0%}  acima -30: {(d > -30).mean():.0%}  mediana {np.median(d):.1f} dB")
    elif modo == "sincronia":
        d = _db(_pcm(alvo), 480)
        pk = [i / 100 for i in range(30, len(d) - 30) if d[i] == d[i - 15:i + 15].max() and d[i] - d[i - 30] > 5]
        mov = [float(x) for x in resto]; err = [min(abs(m - p) for p in pk) for m in mov]
        print(f"erro médio {np.mean(err):.3f} s; fora de 0,12 s: {[(m, round(e, 2)) for m, e in zip(mov, err) if e > .12]}")
