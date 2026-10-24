#!/usr/bin/env python3
"""/ogab eveng2: o óculos Even Realities G2 como monitor do Gab (Bluetooth direto do Mac).

Comandos:
    instalar               baixa a biblioteca do protocolo (versão fixa) e cria o ambiente Python
    testar                 confere tudo sem o óculos (importa, pagina, monta os pacotes)
    procurar               acha o par de lentes e grava em oculos.json
    status "<texto>"       mostra um aviso na lente (render pronto, etapa esperando você...)
    teleprompter <arquivo> roteiro no teleprompter do óculos, rolando no anel R1 ou sozinho
    planos <arquivo>       lista de planos / shot list como checklist (marca no anel)

Biblioteca: github.com/ithinkthisiscool/even-g2-protocol (MIT, engenharia reversa, não oficial).
Fica fora do git da skill em ~/.cache/ogab/eveng2/ (g2/ + venv/ + oculos.json).

Antes de conectar: o óculos só aceita UM aparelho. Desligue o Bluetooth do iPhone (ou feche o
app Even) ou as lentes nem aparecem na busca.
"""
import argparse
import asyncio
import json
import os
import subprocess
import sys
import time
from pathlib import Path

BASE = Path.home() / ".cache/ogab/eveng2"
LIB = BASE / "g2"                      # o repo clonado com o nome do pacote (import g2)
VENV = BASE / "venv"
OCULOS = BASE / "oculos.json"
REPO = "https://github.com/ithinkthisiscool/even-g2-protocol"
COMMIT = "f352806135c1a892eb10ca4d616f9fa0c186fc83"   # versão testada offline (13/10/2026)


# ── Ambiente ─────────────────────────────────────────────────────────────────────────────────

def _python_bom():
    """Primeiro Python >= 3.11 da máquina (a biblioteca exige)."""
    for p in ("/opt/homebrew/bin/python3", "/usr/local/bin/python3", "python3.12", "python3.11",
              "python3"):
        try:
            v = subprocess.run([p, "-c", "import sys;print(sys.version_info[:2]>=(3,11))"],
                               capture_output=True, text=True, timeout=10)
        except (OSError, subprocess.TimeoutExpired):
            continue
        if v.stdout.strip() == "True":
            return p
    return None


def _venv_python():
    return VENV / "bin" / "python3"


def _reexec_no_venv():
    """Os comandos de óculos rodam no venv (bleak); se este processo não é o venv, troca."""
    vp = _venv_python()
    if not vp.exists() or not (LIB / "__init__.py").exists():
        sys.exit("EVENG2_NAO_INSTALADO: rode `python3 eveng2/eveng2.py instalar` primeiro.")
    if Path(sys.prefix).resolve() != VENV.resolve():
        # Filho, não execv: sem permissão de Bluetooth o macOS mata o processo com SIGABRT sem
        # mensagem nenhuma, e só o pai consegue explicar.
        r = subprocess.run([str(vp), os.path.abspath(__file__), *sys.argv[1:]])
        if r.returncode in (-6, 134):
            sys.exit("EVENG2_SEM_PERMISSAO_BLUETOOTH: o macOS bloqueou o Bluetooth para o app que "
                     "rodou o comando.\nAjustes do Sistema > Privacidade e Segurança > Bluetooth: "
                     "ligar o Terminal (ou o app Claude) e abrir de novo. Ou rodar no Terminal.")
        sys.exit(r.returncode)
    sys.path.insert(0, str(BASE))      # `import g2` acha ~/.cache/ogab/eveng2/g2


def cmd_instalar(_a):
    BASE.mkdir(parents=True, exist_ok=True)
    py = _python_bom()
    if not py:
        sys.exit("Precisa de Python 3.11 ou mais novo (brew install python).")
    if not (LIB / ".git").exists():
        subprocess.run(["git", "clone", "-q", REPO, str(LIB)], check=True)
    # Versão fixa: o repo é engenharia reversa e muda sem aviso.
    subprocess.run(["git", "-C", str(LIB), "fetch", "-q", "origin", COMMIT], check=False)
    subprocess.run(["git", "-C", str(LIB), "checkout", "-q", COMMIT], check=True)
    if not _venv_python().exists():
        subprocess.run([py, "-m", "venv", str(VENV)], check=True)
    # O pyproject do repo aponta para uma pasta src/ que não existe: não dá `pip install` nele.
    # Instala só a dependência e importa a pasta clonada direto.
    subprocess.run([str(_venv_python()), "-m", "pip", "install", "-q", "--upgrade", "bleak>=0.21",
                    "pytest"], check=True)
    print(f"ok: biblioteca em {LIB} ({COMMIT[:7]}), ambiente em {VENV}")
    print("Próximo: `eveng2.py testar` (sem óculos) e `eveng2.py procurar` (com o óculos ligado).")


# ── Texto ────────────────────────────────────────────────────────────────────────────────────

def ler_roteiro(caminho):
    """roteiro.txt da /ogab: texto puro. Tira marcações de cena [..] e linhas de comentário #,
    que não são para ler em voz alta."""
    linhas = []
    for ln in Path(caminho).read_text(encoding="utf-8").splitlines():
        s = ln.strip()
        if s.startswith("#"):
            continue
        if s.startswith("[") and s.endswith("]"):
            continue
        linhas.append(ln)
    return "\n".join(linhas).strip()


def ler_planos(caminho):
    """Uma linha por plano. Aceita '- [ ] plano', '- [x] plano', '1. plano' ou só o texto."""
    itens = []
    for ln in Path(caminho).read_text(encoding="utf-8").splitlines():
        s = ln.strip()
        if not s or s.startswith("#"):
            continue
        feito = False
        for pre in ("- [x]", "- [X]", "* [x]", "[x]"):
            if s.startswith(pre):
                feito, s = True, s[len(pre):].strip()
        for pre in ("- [ ]", "* [ ]", "[ ]", "- ", "* "):
            if s.startswith(pre):
                s = s[len(pre):].strip()
        if s[:1].isdigit() and "." in s[:4]:
            s = s.split(".", 1)[1].strip()
        if s:
            itens.append((s, feito))
    return itens


# ── Conexão ──────────────────────────────────────────────────────────────────────────────────

def _par_salvo():
    if OCULOS.exists():
        d = json.loads(OCULOS.read_text())
        return d.get("direita"), d.get("esquerda")
    return None, None


async def _abrir(texto_inicial=None, com_pagina=False):
    from g2.session import GlassesSession
    r, l = _par_salvo()
    s = GlassesSession(initial_text=texto_inicial or "Gab", right_mac=r, left_mac=l)
    try:
        await s.connect(launch_app=True, skip_page=not com_pagina)
    except Exception as e:
        sys.exit(f"EVENG2_SEM_CONEXAO: {e}\nConfira: óculos fora do estojo, Bluetooth do iPhone "
                 "desligado (o óculos só aceita um aparelho) e `eveng2.py procurar`.")
    return s


async def _procurar(_a):
    from g2.session import discover_pairs
    print("Procurando o G2 (10 s)... deixe o Bluetooth do iPhone desligado.", flush=True)
    pares = await discover_pairs(timeout=10.0)
    completos = [p for p in pares if p.get("complete")]
    if not completos:
        sys.exit("Nenhum par completo achado. " + (f"Vi só: {pares}" if pares else
                 "Nada achado: o óculos está conectado no celular ou desligado."))
    p = completos[0]
    OCULOS.write_text(json.dumps({"direita": p["right_mac"], "esquerda": p["left_mac"],
                                  "par": p["pair_id"], "serial": p.get("serial"),
                                  "achado_em": time.strftime("%Y-%m-%d %H:%M")}, indent=2))
    print(f"ok: par {p['pair_id']} ({p['right_name']} / {p['left_name']}) gravado em {OCULOS}")


async def _status(a):
    texto = a.texto.strip()
    s = await _abrir(texto, com_pagina=True)      # cria a página já com o texto (confirmado ao vivo)
    try:
        info = await s.query_settings()
        if info and info.get("battery") is not None:
            print(f"bateria do óculos: {info.get('battery')}%")
        await asyncio.sleep(a.segundos)
    finally:
        await s.close()
    print("ok: aviso mostrado")


async def _teleprompter(a):
    from g2 import teleprompter as tp
    script = ler_roteiro(a.arquivo)
    pages = tp.paginate(script, chars_per_line=a.largura)
    if not pages:
        sys.exit("Roteiro vazio.")
    total_p, total_l = tp.totals(pages)
    modo = tp.MODE_AUTO if a.auto else tp.MODE_MANUAL
    print(f"{total_p} páginas, {total_l} linhas, modo {'automático' if a.auto else 'anel R1'}")

    s = await _abrir()
    fim = asyncio.Event()
    pos = {"page": 0, "line": 0}
    loop = asyncio.get_running_loop()

    def chegou(sid, _flag, pb):
        if sid != tp.SID:
            return
        m = tp.decode(pb)
        if a.verbose:
            print("  <-", m["label"])
        if m["cmd"] == tp.CMD_PAGE_DATA_REQUEST and 0 <= m["page"] < len(pages):
            pb_out = tp.build_page(s.next_magic(), m["page"], pages[m["page"]])
            loop.create_task(s.send(tp.SID, pb_out))
        elif m["cmd"] in (tp.CMD_PAGE_SCROLL_SYNC, tp.CMD_HEARTBEAT) and m["page"] is not None:
            pos["page"], pos["line"] = m["page"], m["line"] or 0
        elif m["cmd"] == tp.CMD_COMM_RESP and m["error"]:
            print(f"  !! óculos recusou: {tp.ERROR_NAMES.get(m['error'], m['error'])}")
        elif tp.is_close(m):
            fim.set()

    s.on_raw_frame = chegou
    try:
        extra = {"scroll_interval_ms": a.intervalo} if a.auto else {}
        await s.send(tp.SID, tp.build_start(s.next_magic(), total_p, total_l, modo, **extra))
        print("Teleprompter aberto. Feche no óculos (ou Ctrl+C) para sair.")
        while not fim.is_set():
            try:
                await asyncio.wait_for(fim.wait(), timeout=tp.HEARTBEAT_INTERVAL_S)
            except asyncio.TimeoutError:
                await s.send(tp.SID, tp.build_heartbeat(s.next_magic(), pos["page"], pos["line"]))
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        try:
            await s.send(tp.SID, tp.build_close(s.next_magic()))
        except Exception:
            pass
        await s.close()
    print(f"ok: teleprompter fechado (parou na página {pos['page'] + 1} de {total_p})")


async def _planos(a):
    from g2 import dashboard, quicklist as ql
    itens = ler_planos(a.arquivo)[:ql.MAX_ITEMS_PER_PACKET]
    if not itens:
        sys.exit("Lista vazia.")
    tarefas = [(i + 1, i, feito, 0, titulo, ql.TS_TYPE_TIME) for i, (titulo, feito) in enumerate(itens)]
    s = await _abrir()
    marcados = {}

    def chegou(sid, _flag, pb):
        if sid != ql.SID_QUICKLIST:
            return
        for t in ql.decode_status_updates(pb) or []:
            marcados[t["uid"]] = t["completed"]
            nome = itens[t["uid"] - 1][0] if 0 < t["uid"] <= len(itens) else t["uid"]
            print(f"  {'[x]' if t['completed'] else '[ ]'} {nome}")

    s.on_raw_frame = chegou
    try:
        await s.send(dashboard.SID_DASHBOARD, dashboard.build_dashboard_init(s.next_magic()))
        await asyncio.sleep(0.5)
        m = s.next_magic()
        ok = await s.request(ql.SID_QUICKLIST, ql.build_quicklist_full_update(tarefas, m), m,
                             "quicklist")
        s.stop_heartbeat()                 # devolve a tela ao painel nativo, que mostra a lista
        print(f"{'ok' if ok else '?? sem confirmação'}: {len(tarefas)} planos no óculos. "
              f"Marcando no anel aparece aqui. Ctrl+C para sair.")
        if a.ficar:
            while True:
                await asyncio.sleep(1)
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        await s.close()
        if marcados and a.gravar:
            _gravar_marcados(a.arquivo, itens, marcados)


def _gravar_marcados(caminho, itens, marcados):
    linhas = [f"- [{'x' if marcados.get(i + 1, feito) else ' '}] {t}" for i, (t, feito) in enumerate(itens)]
    Path(caminho).write_text("\n".join(linhas) + "\n", encoding="utf-8")
    print(f"ok: marcações gravadas em {caminho}")


# ── Teste sem óculos ─────────────────────────────────────────────────────────────────────────

def cmd_testar(_a):
    _reexec_no_venv()
    from g2 import teleprompter as tp, quicklist as ql, evenhub as eh
    texto = "Primeira frase do roteiro.\n\n[take: drone]\n" + "palavra " * 120
    tmp = BASE / "teste_roteiro.txt"
    tmp.write_text(texto, encoding="utf-8")
    pages = tp.paginate(ler_roteiro(tmp))
    assert pages and all(len(p) <= tp.LINES_PER_PAGE for p in pages)
    assert "[take" not in " ".join(sum(pages, []))
    pb = tp.build_start(101, *tp.totals(pages))
    assert tp.decode(pb)["cmd"] == tp.CMD_CONTROL
    assert eh.frame_pb(tp.build_page(102, 0, pages[0]), tp.SID, eh.FLAG_REQUEST, 1)
    tmp.write_text("- [ ] Plano aberto\n- [x] Detalhe mão\n3. Contraplano\n", encoding="utf-8")
    itens = ler_planos(tmp)
    assert itens == [("Plano aberto", False), ("Detalhe mão", True), ("Contraplano", False)], itens
    assert ql.build_quicklist_full_update([(1, 0, False, 0, "Plano", ql.TS_TYPE_TIME)], 5)
    tmp.unlink()
    # Pulados: test_g2_ble.py usa endereços apagados pelo autor ("GRAB MAC ADDRESS"); news_widget
    # e discover importam um _common que não foi publicado. O resto cobre os pacotes que usamos.
    pular = ["--ignore=tests/test_g2_ble.py", "--ignore=tests/test_g2_news_widget.py",
             "--ignore=tests/test_g2_discover.py"]
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests",
                        *pular], cwd=LIB, capture_output=True, text=True,
                       env={**os.environ, "PYTHONPATH": str(BASE)})
    ult = (r.stdout.strip().splitlines() or ["?"])[-1]
    print(f"testes da biblioteca: {ult}")
    print(f"ok: {len(pages)} páginas de teleprompter e {len(itens)} planos montados sem óculos")


def main():
    ap = argparse.ArgumentParser(prog="eveng2", description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("instalar")
    sub.add_parser("testar")
    sub.add_parser("procurar")
    p = sub.add_parser("status")
    p.add_argument("texto")
    p.add_argument("--segundos", type=float, default=8.0)
    p = sub.add_parser("teleprompter")
    p.add_argument("arquivo")
    p.add_argument("--auto", action="store_true", help="rola sozinho em vez do anel")
    p.add_argument("--intervalo", type=int, default=2500, help="ms por linha no --auto")
    p.add_argument("--largura", type=int, default=28, help="caracteres por linha (25-30)")
    p.add_argument("--verbose", action="store_true")
    p = sub.add_parser("planos")
    p.add_argument("arquivo")
    p.add_argument("--ficar", action="store_true", help="fica ouvindo as marcações do anel")
    p.add_argument("--gravar", action="store_true", help="grava as marcações de volta no arquivo")
    a = ap.parse_args()

    if a.cmd == "instalar":
        return cmd_instalar(a)
    if a.cmd == "testar":
        return cmd_testar(a)
    _reexec_no_venv()
    alvo = {"procurar": _procurar, "status": _status, "teleprompter": _teleprompter,
            "planos": _planos}[a.cmd]
    asyncio.run(alvo(a))


if __name__ == "__main__":
    main()
