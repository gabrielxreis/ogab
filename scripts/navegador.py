"""Roda os scripts .mjs da skill no Google Chrome instalado (playwright-core em ~/.cache/ogab-navegador, sem baixar
outro navegador). Usado por storyboard.py, revisor.py e pelas prévias dos presets.

  from navegador import rodar
  rodar("quadros.mjs", [index_html, pasta, "1,5,9", "1080", "1920"])
"""
import os, shutil, subprocess

CACHE = os.path.expanduser("~/.cache/ogab-navegador")
AQUI = os.path.dirname(os.path.abspath(__file__))


def garantir():
    os.makedirs(CACHE, exist_ok=True)
    if not os.path.isdir(os.path.join(CACHE, "node_modules", "playwright-core")):
        subprocess.run(["npm", "install", "--silent", "--prefix", CACHE, "playwright-core@1.56.1"], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=300)


def rodar(script, args, origem=None, timeout=300):
    """Copia o .mjs para o cache (onde o playwright-core resolve) e roda com node. Devolve as linhas da saída."""
    garantir()
    shutil.copy(os.path.join(origem or AQUI, script), CACHE)
    r = subprocess.run(["node", script] + [str(a) for a in args], cwd=CACHE, capture_output=True, text=True, timeout=timeout)
    if r.returncode:
        raise RuntimeError(f"{script} falhou: {r.stderr.strip()[-800:]}")
    return [l for l in r.stdout.splitlines() if l.strip()]
