"""Ponte do reparo automático (06/11/2026). `import licenca` carrega o scripts/licenca.py de sempre e, se o
atualizar.py desta pasta ainda for o antigo (que congelava arquivos), roda o reparar.py sozinho, sem o usuário fazer
nada.

Por que um pacote: nas máquinas presas o licenca.py e o atualizar.py estão congelados, mas o atualizador antigo baixa
arquivo NOVO normalmente, e o carregar.py antigo faz `import licenca` toda vez que o Gab abre. No Python, a pasta
`licenca/` vence o `licenca.py` da mesma pasta, então este arquivo roda e conserta a máquina na primeira abertura.
"""
import importlib.util, json, os, subprocess, sys, time

_SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_spec = importlib.util.spec_from_file_location("_licenca_arquivo", os.path.join(_SCRIPTS, "licenca.py"))
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
globals().update({k: v for k, v in vars(_mod).items() if not k.startswith("__")})

_TENTATIVA = os.path.join(os.path.expanduser("~"), ".claude", "ogab_reparo_tentativa.json")


def _atualizador_velho():
    try:
        import re
        txt = open(os.path.join(_SCRIPTS, "atualizar.py"), encoding="utf-8").read()
        m = re.search(r"^VERSAO_ATUALIZADOR = (\d+)", txt, re.M)
        return not m or int(m.group(1)) < 2
    except Exception:
        return False


def _dono():
    skill = os.path.dirname(_SCRIPTS)
    try:
        return os.path.isdir(os.path.join(skill, ".git")) and \
            json.load(open(os.path.join(skill, "config.json"), encoding="utf-8")).get("dono_biblioteca") is True
    except Exception:
        return False


def _reparo_automatico():
    if os.environ.get("OGAB_REPARANDO") or not _atualizador_velho() or _dono():
        return
    try:   # sem internet ou falhou: tenta de novo só depois de 10 min (não pesa toda abertura)
        if time.time() - json.load(open(_TENTATIVA, encoding="utf-8")).get("quando", 0) < 600:
            return
    except Exception:
        pass
    try:
        os.makedirs(os.path.dirname(_TENTATIVA), exist_ok=True)
        json.dump({"quando": time.time()}, open(_TENTATIVA, "w", encoding="utf-8"))
        subprocess.run([sys.executable, os.path.join(_SCRIPTS, "reparar.py"), "--calado"], capture_output=True,
                       timeout=900, env=dict(os.environ, OGAB_REPARANDO="1"))
    except Exception:
        pass


_reparo_automatico()
