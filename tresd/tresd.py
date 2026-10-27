"""3D de verdade para os vídeos do Gab (Blender sem janela): logo/texto extrudado, metal, luz e câmera, com alfa.

  python3 tresd.py logo plano.json saida.mov      # logo/texto extrudado (renderiza e junta em MOV ProRes 4444 com alfa)
  python3 tresd.py cena cena.py saida.mov [--dur 4]   # OBJETO 3D: script bpy que monta a cena (usa tresd/cena_base.py)
  python3 tresd.py progresso <saida.mov | pasta>      # barra de progresso do render (quadros, %, tempo restante)
Motor: EEVEE SEMPRE (rápido; cena_base.eevee_qualidade()). Cycles só se o usuário quiser abrir/renderizar na interface.
Objeto pronto: procurar antes nos bancos grátis de docs/BANCOS_3D.md (ordem e licenças).
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
    saida_txt = _rodar_com_progresso([blender(), "-b", "--factory-startup", "-P", runner, "--", pj], int(round(dur * fps)), saida)
    if "GAB_OK" not in saida_txt:
        raise RuntimeError("Blender falhou:\n" + saida_txt[-4000:])
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(fps), "-start_number", "1", "-i", os.path.join(pasta, "q_%04d.png"),
                    "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le", "-alpha_bits", "16", "-vendor", "apl0", saida], check=True)
    shutil.move(os.path.join(pasta, "q_cena.blend"), os.path.splitext(saida)[0] + ".blend")
    return saida


def barra(feitos, total, t0, nome=""):
    """Barra de progresso do render 3D (regra do usuário, 13/10/2026: render 3D demora, tem que mostrar o andamento)."""
    import time
    pct = feitos / max(1, total); el = time.time() - t0; resta = el / feitos * (total - feitos) if feitos else 0
    cheio = int(pct * 20)
    return f"{nome} [{'█' * cheio}{'░' * (20 - cheio)}] {feitos}/{total} quadros {pct:4.0%} · faltam ~{int(resta // 60)}min{int(resta % 60):02d}s"


def _rodar_com_progresso(cmd, total, saida):
    """Roda o Blender lendo a saída: a cada quadro salvo atualiza <saida>.progresso e imprime a barra a cada 5%."""
    import time
    t0 = time.time(); feitos = 0; ult = -1; linhas = []; arq = os.path.splitext(saida)[0] + ".progresso"
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    for l in p.stdout:
        linhas.append(l); linhas = linhas[-400:]
        if l.startswith("Saved:") or "Saved: '" in l:
            feitos += 1; b = barra(feitos, total, t0, os.path.basename(os.path.splitext(saida)[0]))
            open(arq, "w").write(b + "\n")
            if int(feitos / max(1, total) * 20) != ult:
                ult = int(feitos / max(1, total) * 20); print(b, flush=True)
    p.wait(); return "".join(linhas)


def progresso(alvo):
    """`tresd.py progresso <saida.mov | pasta>`: mostra a barra de cada render 3D em andamento ou terminado."""
    import glob
    arqs = [alvo] if alvo.endswith(".progresso") else glob.glob(os.path.join(alvo, "*.progresso")) if os.path.isdir(alvo) else [os.path.splitext(alvo)[0] + ".progresso"]
    for a in sorted(arqs):
        mov = os.path.splitext(a)[0] + ".mov"
        print(open(a).read().strip() + ("  ✔ MOV pronto" if os.path.exists(mov) else "") if os.path.exists(a) else f"{a}: sem progresso ainda")


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) >= 3 and a[0] == "logo":
        print(logo(json.load(open(a[1])), a[2]))
    elif len(a) >= 2 and a[0] == "progresso":
        progresso(a[1])
    elif len(a) >= 3 and a[0] == "cena":
        dur = float(a[a.index("--dur") + 1]) if "--dur" in a else 4.0
        print(cena(a[1], a[2], dur=dur))
    else:
        raise SystemExit(__doc__)
