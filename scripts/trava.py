"""Trava da key no CÓDIGO (regra do Gabriel, 26/10/2026: usuário atualizou e seguiu usando sem key, porque a key só era
exigida pelo texto do SKILL.md). As bibliotecas dos editores, o menu, os motions e os presets chamam `exigir()` ao
carregar: sem key válida nesta máquina, o script para com a mensagem do licenca.py (cadastro no site).

Rápido: com uma validação boa nas últimas HORAS horas nesta máquina, nem consulta o servidor. Senão chama
`licenca.checar()` (que já cuida de sem internet: vale a última validação boa por 3 dias).
"""
import os, sys, time

AQUI = os.path.dirname(os.path.abspath(__file__))
if AQUI not in sys.path:
    sys.path.insert(0, AQUI)
import licenca  # noqa: E402

HORAS = 12
_ok = False


def valida():
    global _ok
    if _ok:
        return True
    d = licenca._ler()
    if d.get("key") and d.get("maquina") == licenca.maquina() and time.time() - d.get("validado_em", 0) < HORAS * 3600:
        _ok = True
        return True
    import contextlib, io
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        _ok = licenca.checar() == 0
    valida.msg = buf.getvalue().strip()
    return _ok


valida.msg = ""


def exigir():
    if valida():
        return
    sys.stderr.write((valida.msg or licenca.PENDENTE) + "\n")
    sys.stdout.flush()
    raise SystemExit(3)
