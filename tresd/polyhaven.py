"""Baixa assets CC0 do Poly Haven (HDRI de estúdio, texturas PBR, modelos) para as cenas 3D.
  python3 polyhaven.py hdri brown_photostudio_02 <pasta> [2k]        -> <pasta>/<id>.hdr
  python3 polyhaven.py textura lacquered_cherry_wood <pasta> [2k]   -> <id>_diff.jpg, _rough.jpg, _nor.jpg
  python3 polyhaven.py buscar <palavra> [models|textures|hdris]
A API recusa pedido sem User-Agent (HTTP 403): por isso curl com UA."""
import json, os, subprocess, sys
UA = ["-A", "gab-ogab/1.0"]
def api(u): return json.loads(subprocess.run(["curl", "-s", *UA, u], capture_output=True, text=True, check=True).stdout)
def baixar(u, saida): subprocess.run(["curl", "-sL", *UA, "-o", saida, u], check=True); return saida
a = sys.argv[1:]
if not a: raise SystemExit(__doc__)
if a[0] == "buscar":
    tipo = a[2] if len(a) > 2 else "models"
    for k, v in api(f"https://api.polyhaven.com/assets?t={tipo}").items():
        if a[1].lower() in (k + " " + v.get("name", "") + " " + " ".join(v.get("tags", []))).lower(): print(k, "|", v.get("name"))
elif a[0] == "hdri":
    res = a[3] if len(a) > 3 else "2k"; os.makedirs(a[2], exist_ok=True)
    print(baixar(api(f"https://api.polyhaven.com/files/{a[1]}")["hdri"][res]["hdr"]["url"], os.path.join(a[2], a[1] + ".hdr")))
elif a[0] == "textura":
    res = a[3] if len(a) > 3 else "2k"; os.makedirs(a[2], exist_ok=True); f = api(f"https://api.polyhaven.com/files/{a[1]}")
    for mapa, suf in (("diffuse", "diff"), ("rough", "rough"), ("nor_gl", "nor")):
        k = [x for x in f if x.lower() == mapa][0]; print(baixar(f[k][res]["jpg"]["url"], os.path.join(a[2], f"{a[1]}_{suf}.jpg")))
