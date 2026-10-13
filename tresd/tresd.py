"""3D de verdade para os vídeos do Gab (Blender sem janela): logo/texto extrudado, metal, luz e câmera, com alfa.

  python3 tresd.py logo plano.json saida.mov      # logo/texto extrudado (renderiza e junta em MOV ProRes 4444 com alfa)
  python3 tresd.py cena cena.py saida.mov [--dur 4]   # OBJETO 3D: script bpy que monta a cena (usa tresd/cena_base.py)
Ver tresd/logo3d.py para os campos do plano. O .blend fica ao lado do MOV (editável no Blender).
"""
import glob, json, os, shutil, subprocess, sys

AQUI = os.path.dirname(os.path.abspath(__file__))


def blender():
    for c in ("/Applications/Blender.app/Contents/MacOS/Blender", shutil.which("blender") or "",
              *glob.glob(os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "Blender Foundation", "Blender*", "blender.exe"))):
        if c and os.path.exists(c):
            return c
    raise SystemExit("Blender não encontrado (instale grátis em blender.org; o instalador do Gab instala).")


def logo(plano, saida):
    saida = os.path.abspath(os.path.expanduser(saida))
    pasta = os.path.splitext(saida)[0] + "_quadros"
    shutil.rmtree(pasta, ignore_errors=True); os.makedirs(pasta)
    plano = dict(plano, saida=os.path.join(pasta, "q_"))
    pj = os.path.join(pasta, "plano.json"); json.dump(plano, open(pj, "w"))
    r = subprocess.run([blender(), "-b", "--factory-startup", "-P", os.path.join(AQUI, "logo3d.py"), "--", pj],
                       capture_output=True, text=True)
    if "GAB_OK" not in r.stdout:
        raise RuntimeError("Blender falhou:\n" + (r.stdout[-2000:] + r.stderr[-1500:]))
    fps = plano.get("fps", 30)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(fps), "-start_number", "1", "-i", os.path.join(pasta, "q_%04d.png"),
                    "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le", "-alpha_bits", "16", "-vendor", "apl0", saida], check=True)
    shutil.move(os.path.join(pasta, "q_cena.blend"), os.path.splitext(saida)[0] + ".blend")
    return saida


def cena(script, saida, dur=4.0, fps=30, w=1080, h=1920, transparente=True, amostras=32, motor="EEVEE", params=None):
    """Roda um script de cena (bpy) que monta o objeto 3D e renderiza com o padrão do Gab (alfa, 9:16).
    O script recebe `base` (tresd/cena_base.py) e `P` (params) já prontos e NÃO chama render: o runner chama."""
    saida = os.path.abspath(os.path.expanduser(saida))
    pasta = os.path.splitext(saida)[0] + "_quadros"
    shutil.rmtree(pasta, ignore_errors=True); os.makedirs(pasta)
    cfg = {"script": os.path.abspath(script), "saida": os.path.join(pasta, "q_"), "dur": dur, "fps": fps, "w": w, "h": h,
           "transparente": transparente, "amostras": amostras, "motor": motor, "params": params or {}, "base": AQUI}
    pj = os.path.join(pasta, "cena.json"); json.dump(cfg, open(pj, "w"))
    runner = os.path.join(pasta, "runner.py")
    open(runner, "w").write('''import json, sys, runpy
cfg = json.load(open(sys.argv[sys.argv.index("--") + 1]))
sys.path.insert(0, cfg["base"])
import bpy, cena_base as base
base.limpar()
base.render(cfg["w"], cfg["h"], cfg["fps"], cfg["dur"], cfg["transparente"], cfg["amostras"], cfg["motor"])
runpy.run_path(cfg["script"], init_globals={"base": base, "P": cfg["params"], "bpy": bpy})
base.suavizar_tudo()
bpy.context.scene.render.filepath = cfg["saida"]
bpy.ops.wm.save_as_mainfile(filepath=cfg["saida"] + "cena.blend")
bpy.ops.render.render(animation=True)
print("GAB_OK")
''')
    r = subprocess.run([blender(), "-b", "--factory-startup", "-P", runner, "--", pj], capture_output=True, text=True)
    if "GAB_OK" not in r.stdout:
        raise RuntimeError("Blender falhou:\n" + (r.stdout[-2500:] + r.stderr[-1500:]))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(fps), "-start_number", "1", "-i", os.path.join(pasta, "q_%04d.png"),
                    "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le", "-alpha_bits", "16", "-vendor", "apl0", saida], check=True)
    shutil.move(os.path.join(pasta, "q_cena.blend"), os.path.splitext(saida)[0] + ".blend")
    return saida


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) >= 3 and a[0] == "logo":
        print(logo(json.load(open(a[1])), a[2]))
    elif len(a) >= 3 and a[0] == "cena":
        dur = float(a[a.index("--dur") + 1]) if "--dur" in a else 4.0
        print(cena(a[1], a[2], dur=dur))
    else:
        raise SystemExit(__doc__)
