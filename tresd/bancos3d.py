"""Acha e baixa objeto 3D grátis para as cenas (ordem e licenças em docs/BANCOS_3D.md).
  python3 bancos3d.py buscar <palavras> [--n 8]           -> Poly Haven (CC0) + Sketchfab (CC0 e CC-BY, baixáveis)
  python3 bancos3d.py baixar polyhaven <id> <pasta> [1k]  -> <pasta>/<id>/<id>_1k.gltf + texturas + LICENCA.txt
  python3 bancos3d.py baixar sketchfab <uid> <pasta>      -> <pasta>/<uid>/*.glb + LICENCA.txt (precisa SKETCHFAB_TOKEN;
                                                             sem token, baixa pelo Chrome logado: ver navegador/downloads.md)
Kenney, Quaternius, Poly Pizza, Smithsonian e NASA não têm busca aberta: procurar no site (links no fim da busca).
Importar no Blender: bpy.ops.import_scene.gltf(filepath=...). Crédito CC-BY vai na descrição do post."""
import json, os, subprocess, sys, urllib.parse
UA = ["-A", "gab-ogab/1.0"]
def api(u, *h): return json.loads(subprocess.run(["curl", "-s", *UA, *h, u], capture_output=True, text=True, check=True).stdout)
def baixar(u, saida): os.makedirs(os.path.dirname(saida), exist_ok=True); subprocess.run(["curl", "-sL", *UA, "-o", saida, u], check=True); return saida
def licenca(pasta, **k): open(os.path.join(pasta, "LICENCA.txt"), "w").write("".join(f"{a}: {b}\n" for a, b in k.items()))


def buscar(q, n=8):
    termos = q.lower().split()
    achados = [(k, v) for k, v in api("https://api.polyhaven.com/assets?t=models").items()
               if all(t in (k + " " + v.get("name", "") + " " + " ".join(v.get("tags", []) + v.get("categories", []))).lower() for t in termos)]
    print(f"== Poly Haven (CC0, realista) {len(achados)}")
    for k, v in achados[:n]: print(f"  polyhaven {k} | {v.get('name')} | https://polyhaven.com/a/{k}")
    for lic, nome in (("cc0", "CC0"), ("by", "CC-BY, creditar")):
        r = api("https://api.sketchfab.com/v3/search?" + urllib.parse.urlencode(
            {"type": "models", "q": q, "downloadable": "true", "license": lic, "count": n, "sort_by": "-likeCount"}))["results"]
        print(f"== Sketchfab ({nome}) {len(r)}")
        for m in r: print(f"  sketchfab {m['uid']} | {m['name']} | {m.get('faceCount') or '?'} faces | {m['user']['username']} | https://sketchfab.com/models/{m['uid']}")
    s = urllib.parse.quote(q)
    print("== Procurar também no site:\n  https://kenney.nl/assets  https://quaternius.com  https://poly.pizza/search/" + s +
          "\n  https://3d.si.edu/search/collections?edan_q=" + s + "  https://science.nasa.gov/3d-resources/")


def polyhaven(i, pasta, res="1k"):
    g = api(f"https://api.polyhaven.com/files/{i}")["gltf"][res]["gltf"]; dest = os.path.join(pasta, i)
    for rel, f in g["include"].items(): baixar(f["url"], os.path.join(dest, rel))
    arq = baixar(g["url"], os.path.join(dest, os.path.basename(g["url"])))
    info = api(f"https://api.polyhaven.com/info/{i}")
    licenca(dest, banco="Poly Haven", link=f"https://polyhaven.com/a/{i}", nome=info.get("name"), autor=", ".join(info.get("authors", {})), licenca="CC0 (sem crédito)")
    print(arq)


def sketchfab(uid, pasta):
    m = api(f"https://api.sketchfab.com/v3/models/{uid}"); dest = os.path.join(pasta, uid)
    tok = os.environ.get("SKETCHFAB_TOKEN")
    if not tok: raise SystemExit(f"Sem SKETCHFAB_TOKEN: baixar o GLB pelo Chrome logado em {m['viewerUrl']} (botão Download 3D Model > glTF/GLB).")
    d = api(f"https://api.sketchfab.com/v3/models/{uid}/download", "-H", f"Authorization: Token {tok}")
    f = d.get("glb") or d["gltf"]; arq = baixar(f["url"], os.path.join(dest, uid + (".glb" if "glb" in d else ".zip")))
    licenca(dest, banco="Sketchfab", link=m["viewerUrl"], nome=m["name"], autor=m["user"]["username"], licenca=m["license"]["label"])
    print(arq)


a = sys.argv[1:]
if not a: raise SystemExit(__doc__)
if a[0] == "buscar":
    n = int(a[a.index("--n") + 1]) if "--n" in a else 8
    buscar(" ".join(x for x in a[1:] if x != "--n" and x != str(n)), n)
elif a[:2] == ["baixar", "polyhaven"]: polyhaven(a[2], a[3], *a[4:5])
elif a[:2] == ["baixar", "sketchfab"]: sketchfab(a[2], a[3])
else: raise SystemExit(__doc__)
