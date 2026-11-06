"""Reparo do atualizador do Gab (06/11/2026). Roda uma vez nas máquinas que pararam de se atualizar.

O atualizar.py antigo (até a 2026.10.30-7), num clone do git, tratava como "edição do usuário" todo arquivo que o
próprio sync tinha gravado: cada arquivo atualizava uma vez e congelava. A máquina ficava parada numa versão velha e
nem a correção do atualizador chegava (ele mesmo estava congelado). Este arquivo é novo, então até o sync antigo o
baixa; o servidor avisa pelo /v1/validar quem precisa rodar.

  python3 reparar.py          # baixa o licenca.py e o atualizar.py atuais e roda o sync novo
  python3 reparar.py --calado # sem mensagem (o licenca.py novo chama sozinho quando acha o atualizador velho)

Não apaga nada do usuário: o sync novo só sobrescreve o que é versão nossa (o servidor confere pelo histórico).
"""
import base64, json, os, subprocess, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(AQUI)
os.environ["OGAB_REPARANDO"] = "1"   # a ponte scripts/licenca/ não dispara outro reparo daqui
sys.path.insert(0, AQUI)
import licenca  # noqa: E402   (serve até o licenca.py antigo: só usa _ler, _post e maquina)

BASICOS = ("scripts/licenca.py", "scripts/atualizar.py")


def _dono():
    try:
        return os.path.isdir(os.path.join(SKILL, ".git")) and \
            json.load(open(os.path.join(SKILL, "config.json"), encoding="utf-8")).get("dono_biblioteca") is True
    except Exception:
        return False


def _gravar(path, dados):
    full = os.path.join(SKILL, path)
    tmp = full + ".parcial"
    with open(tmp, "wb") as f:
        f.write(dados)
    if os.path.exists(full):
        try:
            import shutil
            shutil.copymode(full, tmp)
        except Exception:
            pass
    os.replace(tmp, full)


def reparar(calado=False):
    if _dono():
        calado or print("REPARO_DONO: no computador do criador a fonte é o git; nada a fazer")
        return 0
    d = licenca._ler()
    if not d.get("key"):
        calado or print("REPARO_SEM_KEY: ative a key primeiro (licenca.py ativar --key GAB-...)")
        return 1
    corpo = {"key": d["key"], "maquina": licenca.maquina()}
    for path in BASICOS:
        r = licenca._post("/v1/release/baixar", dict(corpo, path=path))
        if not r or r.get("b64") is None:
            calado or print(f"REPARO_SEM_CONEXAO: não baixou {path} ({(r or {}).get('msg', 'sem internet')}); "
                            "tente de novo com internet")
            return 1
        _gravar(path, base64.b64decode(r["b64"]))
    p = subprocess.run([sys.executable, os.path.join(AQUI, "atualizar.py")], capture_output=True, text=True,
                       timeout=900)
    saida = (p.stdout or "").strip()
    if not calado:
        print(saida or "ATUALIZADO: já estava na versão atual")
        print("REPARADO: o Gab volta a se atualizar sozinho. Recomece o passo zero e releia o SKILL.md.")
    return 0 if p.returncode == 0 else 1


if __name__ == "__main__":
    sys.exit(reparar("--calado" in sys.argv[1:]))
