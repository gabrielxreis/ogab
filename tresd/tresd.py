"""3D de verdade para os vídeos do Gab (Blender sem janela): logo/texto extrudado, metal, luz e câmera, com alfa.

  python3 tresd.py logo plano.json saida.mov      # renderiza e junta em MOV ProRes 4444 com alfa
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


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 3 or a[0] != "logo":
        raise SystemExit(__doc__)
    print(logo(json.load(open(a[1])), a[2]))
