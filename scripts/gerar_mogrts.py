"""Gera MOGRTs (templates editáveis do Premiere) a partir da biblioteca de motions, pelo After Effects.

  python3 gerar_mogrts.py                 # todos os modelos da biblioteca
  python3 gerar_mogrts.py lista-checks    # só os modelos citados

Cada modelo vira "<modelo>.mogrt" em premiere/assets/mogrt/ com fundo transparente (vai por cima do vídeo) e
os textos + as 4 cores da camada CONTROLES editáveis no Essential Graphics do Premiere. Usa os exemplos do
próprio modelo como texto inicial. Instala na pasta de Motion Graphics Templates desta máquina e, no Mac do dono
(config "dono_biblioteca": true), publica no GitHub para todo usuário receber no update.
"""
import glob, json, os, shutil, subprocess, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts")); sys.path.insert(0, os.path.join(RAIZ, "aftereffects"))
import biblioteca_motions as B
import ae_lib as AE

DESTINO = os.path.join(RAIZ, "premiere", "assets", "mogrt")
CORES = {"principal": "#0B1F3A", "destaque": "#C9A657", "texto": "#FFFFFF", "fundo": "#0B1F3A"}   # trocáveis no Premiere


def pasta_mg():
    if sys.platform == "darwin":
        return os.path.expanduser("~/Library/Application Support/Adobe/Common/Motion Graphics Templates")
    return os.path.join(os.environ.get("APPDATA", ""), "Adobe", "Common", "Motion Graphics Templates")


def gerar(nomes=None):
    ms = B.modelos()
    nomes = nomes or [n for n, m in ms.items() if m["_origem"] == "biblioteca"]
    os.makedirs(DESTINO, exist_ok=True)
    tmp = os.path.join(RAIZ, "premiere", "assets", "mogrt", "_projeto")
    os.makedirs(tmp, exist_ok=True)
    AE.conectar()
    AE.abrir_projeto(os.path.join(tmp, "mogrts.aep"))
    feitos = []
    for n in nomes:
        m = ms[n]
        exemplos = {c: d.get("exemplo") for c, d in m["campos"].items()}
        spec = B.aplicar(n, exemplos, CORES, nome_comp=n)
        spec["elementos"] = [e for e in spec["elementos"] if e.get("tipo") not in ("fundo", "fundo_rico")]   # transparente
        AE.motion(spec, salvar=False)
        AE.jsx("return GAB.mogrt(args.comp, args.p);", "mogrt", espera=180, comp=n, p=DESTINO)
        arq = os.path.join(DESTINO, n + ".mogrt")
        if os.path.exists(arq):
            feitos.append(arq)
            os.makedirs(pasta_mg(), exist_ok=True)
            shutil.copy(arq, pasta_mg())
            print("ok", arq, flush=True)
        else:
            print("FALHOU", n, flush=True)
    AE.salvar()
    shutil.rmtree(tmp, ignore_errors=True)
    cfg = json.load(open(os.path.join(RAIZ, "config.json"))) if os.path.exists(os.path.join(RAIZ, "config.json")) else {}
    if feitos and cfg.get("dono_biblioteca"):
        g = ["git", "-C", RAIZ]
        subprocess.run(g + ["add"] + feitos, check=True)
        if subprocess.run(g + ["diff", "--cached", "--quiet"]).returncode != 0:
            subprocess.run(g + ["commit", "-q", "-m", "mogrt: " + ", ".join(os.path.basename(f) for f in feitos) +
                                "\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"], check=True)
            subprocess.run(g + ["push", "-q"])
    return feitos


if __name__ == "__main__":
    gerar(sys.argv[1:] or None)
