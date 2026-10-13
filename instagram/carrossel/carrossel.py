"""Carrossel do Gab: slides de Instagram/Threads/LinkedIn/Stories a partir do texto, na marca do cliente.

  python3 carrossel.py instalar                      # uma vez: npm install no template (~350 MB, fora do git)
  python3 carrossel.py novo <pasta>                  # cópia de trabalho do template (node_modules por link)
  python3 carrossel.py previa <pasta> [--porta 3333] # sobe a prévia no navegador (barra para trocar fonte, cor, formato)
  python3 carrossel.py exportar <pasta> <saida> [--pdf] [--porta 3333]
        -> PNG por slide (01-hook.png, 02-list.png...) e, com --pdf, carrossel.pdf (LinkedIn), sem clicar em nada:
           sobe o servidor, lê /info (quantos slides e o tamanho), fotografa /?slide=N no Chrome sem janela e desliga.

Conteúdo e marca ficam só em <pasta>/src/slides.ts (SLIDES, MARCA e os DEFAULT_*); fonte do cliente em
<pasta>/public/fonts/marca.ttf (e marca-titulo.ttf, opcional); imagens em <pasta>/public/images/.
"""
import json, os, shutil, signal, subprocess, sys, tempfile, time, urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(AQUI, "template")


def _npm():
    exe = shutil.which("npm")
    if not exe:
        raise SystemExit("npm não encontrado: instale o Node.js (o install.sh do Gab instala)")
    return exe


def instalar():
    subprocess.run([_npm(), "install", "--no-audit", "--no-fund", "--loglevel=error"], cwd=TEMPLATE, check=True)
    print("ok: dependências do carrossel instaladas")


def novo(pasta):
    if not os.path.isdir(os.path.join(TEMPLATE, "node_modules")):
        instalar()
    pasta = os.path.abspath(pasta)
    if os.path.exists(os.path.join(pasta, "src", "slides.ts")):
        raise SystemExit(f"já existe um carrossel em {pasta}")
    shutil.copytree(TEMPLATE, pasta, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("node_modules", ".next", "next-env.d.ts"))
    alvo, link = os.path.join(TEMPLATE, "node_modules"), os.path.join(pasta, "node_modules")
    try:
        os.symlink(alvo, link, target_is_directory=True)
    except OSError:   # Windows sem permissão de symlink: junção de pasta (não precisa de admin)
        subprocess.run(["cmd", "/c", "mklink", "/J", link, alvo], check=True, capture_output=True)
    print(f"ok: {pasta}  (editar src/slides.ts; fonte do cliente em public/fonts/marca.ttf)")
    return pasta


def _subir(pasta, porta):
    log = open(os.path.join(pasta, ".servidor.log"), "w")
    nxt = os.path.join(pasta, "node_modules", ".bin", "next.cmd" if os.name == "nt" else "next")
    proc = subprocess.Popen([nxt, "dev", "-p", str(porta)],
                            cwd=pasta, stdout=log, stderr=subprocess.STDOUT, start_new_session=(os.name != "nt"))
    url = f"http://localhost:{porta}"
    for _ in range(120):   # a 1ª compilação leva uns segundos
        if proc.poll() is not None:
            raise SystemExit("o servidor do carrossel caiu: veja " + log.name)
        try:
            urllib.request.urlopen(url + "/info", timeout=5).read()
            return proc, url
        except Exception:
            time.sleep(1)
    _parar(proc)
    raise SystemExit("o servidor do carrossel não respondeu em 2 min: veja " + log.name)


def _parar(proc):
    if os.name == "nt":
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
        return
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except Exception:
        proc.terminate()


def _chrome():
    for p in ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
              "/Applications/Chromium.app/Contents/MacOS/Chromium",
              r"C:\Program Files\Google\Chrome\Application\chrome.exe",
              r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"]:
        if os.path.exists(p):
            return p
    return shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chrome")


def previa(pasta, porta=3333):
    proc, url = _subir(os.path.abspath(pasta), porta)
    print(f"prévia: {url}  (o servidor fica rodando; para desligar: kill {proc.pid})")


def exportar(pasta, saida, pdf=False, porta=3333):
    pasta, saida = os.path.abspath(pasta), os.path.abspath(saida)
    chrome = _chrome()
    if not chrome:
        raise SystemExit("Chrome não encontrado: exportar pela prévia (botão Exportar PNG)")
    os.makedirs(saida, exist_ok=True)
    proc, url = _subir(pasta, porta)
    perfil = tempfile.mkdtemp(prefix="ogab_carrossel_")
    feitos = []
    try:
        info = json.loads(urllib.request.urlopen(url + "/info", timeout=30).read())
        for n in range(1, info["total"] + 1):
            arq = os.path.join(saida, f"{n:02d}-{info['tipos'][n - 1]}.png")
            subprocess.run([chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--user-data-dir={perfil}",
                            f"--window-size={info['w']},{info['h']}", "--force-device-scale-factor=1", "--run-all-compositor-stages-before-draw",
                            "--virtual-time-budget=6000", f"--screenshot={arq}", f"{url}/?slide={n}"],
                           capture_output=True, timeout=120)
            if not os.path.exists(arq):
                raise SystemExit(f"o slide {n} não saiu")
            feitos.append(arq)
            print(f"  {os.path.basename(arq)}")
    finally:
        _parar(proc)
        shutil.rmtree(perfil, ignore_errors=True)
    if pdf:
        from PIL import Image
        Image.init()   # registra o JPEG que o PDF usa por dentro
        imgs = [Image.open(f).convert("RGB") for f in feitos]
        destino = os.path.join(saida, "carrossel.pdf")
        imgs[0].save(destino, save_all=True, append_images=imgs[1:], resolution=72)
        print(f"  {os.path.basename(destino)}")
    print(f"ok: {len(feitos)} slides em {saida}  (abrir e conferir antes de postar)")
    return feitos


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] not in ("instalar", "novo", "previa", "exportar"):
        print(__doc__); sys.exit(1)

    def opt(k, d=None):
        return a[a.index(k) + 1] if k in a else d

    porta = int(opt("--porta", 3333))
    if a[0] == "instalar":
        instalar()
    elif a[0] == "novo":
        novo(a[1])
    elif a[0] == "previa":
        previa(a[1], porta)
    else:
        exportar(a[1], a[2], "--pdf" in a, porta)
