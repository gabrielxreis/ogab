"""Key de uso do Gab (/ogab). Regra do Gabriel (26/10/2026): sem key válida o Gab não roda; key grátis por cadastro
(email), presa a 1 computador. Toda abertura consulta o servidor de licenças (passo zero do SKILL.md).

  python3 licenca.py checar               # sai 0 se a key desta máquina vale; 1 com LICENCA_* e o que fazer
  python3 licenca.py registrar --email X  # cadastro grátis: cria a key e prende neste computador (SÓ com o email
                                          # que a PESSOA digitou; nunca inventar nem usar um que você "já sabe")
  python3 licenca.py ativar --key GAB-... # usa uma key que a pessoa já tem
  python3 licenca.py liberar              # solta a key deste computador para ativar em outro (1 troca a cada 7 dias)
  python3 licenca.py status               # key, email, máquina e última validação
  python3 licenca.py maquina              # só o código desta máquina (para o autor bloquear/liberar)

Sem internet: vale a última validação boa por até 3 dias; depois disso, para até conectar.
Guardado em ~/.claude/ogab_licenca.json (fora da pasta da skill, sobrevive a update e reinstalação).
"""
import hashlib, json, os, platform, subprocess, sys, time, urllib.error, urllib.request

URL = os.environ.get("OGAB_LICENCA_URL", "https://licencas.gabrielxreis.com").rstrip("/")
ARQ = os.path.join(os.path.expanduser("~"), ".claude", "ogab_licenca.json")
OFFLINE_DIAS = 3
TIMEOUT = 6
SAL = "ogab-maquina-v1"


def _cmd(args):
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=8).stdout
    except Exception:
        return ""


def maquina():
    """Código fixo do computador: hash do UUID de hardware (não dá pra voltar ao número original)."""
    s, bruto = platform.system(), ""
    if s == "Darwin":
        for linha in _cmd(["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"]).splitlines():
            if "IOPlatformUUID" in linha:
                bruto = linha.split('"')[-2]
    elif s == "Windows":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography", 0,
                                winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as k:
                bruto = winreg.QueryValueEx(k, "MachineGuid")[0]
        except Exception:
            bruto = _cmd(["powershell", "-NoProfile", "-Command", "(Get-CimInstance Win32_ComputerSystemProduct).UUID"])
    else:
        for p in ("/etc/machine-id", "/var/lib/dbus/machine-id"):
            try:
                bruto = open(p).read()
                break
            except Exception:
                pass
    bruto = bruto.strip() or platform.node()
    return hashlib.sha256(f"{SAL}:{bruto}".encode()).hexdigest()[:32]


def _ler():
    try:
        return json.load(open(ARQ, encoding="utf-8"))
    except Exception:
        return {}


def _gravar(d):
    os.makedirs(os.path.dirname(ARQ), exist_ok=True)
    json.dump(d, open(ARQ, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def _post(rota, corpo):
    req = urllib.request.Request(URL + rota, data=json.dumps(corpo).encode(),
                                 headers={"Content-Type": "application/json", "User-Agent": "ogab-licenca/1"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:   # 4xx do servidor trazem status/msg em JSON
        try:
            return json.loads(e.read() or b"{}")
        except Exception:
            return {"status": "erro", "msg": f"servidor respondeu {e.code}"}
    except Exception:
        return None   # sem conexão


def _sistema():
    return f"{platform.system()} {platform.release()} {platform.machine()}"


PENDENTE = ("LICENCA_PENDENTE: o Gab precisa de uma key (grátis). Perguntar o email da pessoa e rodar "
            "`licenca.py registrar --email <email>`; se ela já tem key: `licenca.py ativar --key <key>`. "
            "Não fazer nada do pedido antes disso.")


def checar():
    d, m = _ler(), maquina()
    if not d.get("key"):
        print(PENDENTE)
        return 1
    r = _post("/v1/validar", {"key": d["key"], "maquina": m})
    if r is None:
        ok_em = d.get("validado_em", 0)
        if d.get("maquina") == m and time.time() - ok_em < OFFLINE_DIAS * 86400:
            print(f"LICENCA_OFFLINE: sem conexão com o servidor de licenças; usando a validação de "
                  f"{time.strftime('%d/%m %H:%M', time.localtime(ok_em))} (vale {OFFLINE_DIAS} dias)")
            return 0
        print("LICENCA_SEM_CONEXAO: não deu pra validar a key (sem internet há mais de "
              f"{OFFLINE_DIAS} dias ou nunca validou). Conecte e tente de novo; o Gab não roda até validar.")
        return 1
    st = r.get("status")
    if st == "ok":
        d.update(maquina=m, validado_em=int(time.time()), email=r.get("email", d.get("email", "")))
        _gravar(d)
        return 0
    d["validado_em"] = 0
    _gravar(d)
    if st == "bloqueada":
        print("LICENCA_BLOQUEADA: esta instalação foi desativada pelo autor. Falar com @gabrielxreis_ no "
              "Instagram. O Gab não roda.")
    elif st == "outra_maquina":
        print("LICENCA_OUTRA_MAQUINA: esta key está ativa em outro computador (1 por key). No computador antigo: "
              "`licenca.py liberar`; ou cadastrar outro email aqui com `licenca.py registrar --email <email>`.")
    elif st == "invalida":
        print("LICENCA_INVALIDA: a key salva não existe mais. " + PENDENTE.split(": ", 1)[1])
    else:
        print(f"LICENCA_ERRO: {r.get('msg', st)}")
    return 1


def registrar(email):
    r = _post("/v1/registrar", {"email": email, "maquina": maquina(), "sistema": _sistema()})
    if r is None:
        print("sem conexão com o servidor de licenças; tente de novo")
        return 1
    if r.get("status") != "ok":
        print(f"não registrou: {r.get('msg', r.get('status'))}")
        return 1
    _gravar({"key": r["key"], "email": r.get("email", email), "maquina": maquina(), "validado_em": int(time.time())})
    print(f"key criada e ativada neste computador: {r['key']} ({r.get('email', email)})")
    return 0


def ativar(key):
    antes, d = _ler(), {"key": key.strip().upper()}
    _gravar(d)
    if checar() == 0:
        print(f"key {d['key']} ativada neste computador")
        return 0
    if antes.get("key"):   # key digitada não serviu: volta a que já estava salva
        _gravar(antes)
    return 1


def liberar():
    d = _ler()
    if not d.get("key"):
        print("nenhuma key neste computador")
        return 1
    r = _post("/v1/liberar", {"key": d["key"], "maquina": maquina()})
    if r is None:
        print("sem conexão com o servidor de licenças; tente de novo")
        return 1
    print(r.get("msg", r.get("status")))
    if r.get("status") == "ok":
        _gravar({"key_liberada": d["key"], "email": d.get("email", "")})
        return 0
    return 1


def main(a):
    cmd = a[0] if a else ""
    arg = lambda nome: a[a.index(nome) + 1] if nome in a and a.index(nome) + 1 < len(a) else ""
    if cmd == "checar":
        sys.exit(checar())
    elif cmd == "registrar" and arg("--email"):
        sys.exit(registrar(arg("--email").strip().lower()))
    elif cmd == "ativar" and arg("--key"):
        sys.exit(ativar(arg("--key")))
    elif cmd == "liberar":
        sys.exit(liberar())
    elif cmd == "status":
        d = _ler()
        quando = time.strftime("%d/%m/%Y %H:%M", time.localtime(d["validado_em"])) if d.get("validado_em") else "nunca"
        print(f"key: {d.get('key', '(nenhuma)')}\nemail: {d.get('email', '')}\nmáquina: {maquina()}\n"
              f"última validação: {quando}\nservidor: {URL}")
    elif cmd == "maquina":
        print(maquina())
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
