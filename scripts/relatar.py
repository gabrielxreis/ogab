"""Relatos de erro do Gab: quem instalou e CONCORDOU manda, anônimo, o que quebrou e como foi corrigido (o dono atualiza).

  python3 relatar.py consentir sim|nao     # resposta da pergunta única (instalador ou 1ª abertura); grava "relatos" no config
  python3 relatar.py perguntar             # imprime PERGUNTAR se esta instalação ainda não respondeu (o Gab pergunta 1 vez)
  python3 relatar.py registrar --titulo "..." --erro "..." --causa "..." --correcao "..." [--arquivo scripts/x.py ...]
  python3 relatar.py enviar                # manda os pendentes (ao abrir o Gab, em segundo plano) SÓ se "relatos": true
  python3 relatar.py status                # consentimento, pendentes e enviados

Consentimento: sem "relatos": true no config.json nada sai da máquina (relatos ficam só em ~/.claude/ogab_relatos/).
O relato é ANONIMIZADO antes de ser gravado: caminhos viram ~/..., saem e-mails, chaves/tokens, parâmetros de link,
o nome do usuário e o nome de cada cliente (pastas de clientes/ e da pasta de saída). Não vai vídeo, roteiro, legenda
nem transcrição: só o que quebrou na skill, a causa, a correção e o diff dos arquivos DA SKILL.
Na máquina do dono ("dono_biblioteca": true) não envia (ele corrige direto). Destino: relatos/destino.json.
"""
import glob, hashlib, json, os, platform, re, subprocess, sys, time, urllib.request

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(SKILL, "config.json")
PASTA = os.path.expanduser("~/.claude/ogab_relatos")
PEND, ENV = os.path.join(PASTA, "pendentes"), os.path.join(PASTA, "enviados")
CHAVE_ENVIO = "ogab-relato-v1"
LIMITES = {"titulo": 200, "erro": 3000, "causa": 2000, "correcao": 3000, "diff": 15000}
PERGUNTA = ("Quando algo da skill quebra e o Gab corrige, posso mandar um relato ANÔNIMO para o Gabriel melhorar o Gab "
            "para todo mundo? (só o erro, a causa e a correção no código da skill; nada de vídeo, roteiro, cliente, nome "
            "ou caminho de pasta). Dá para mudar depois: /ogab config relatos sim|nao")


def _config():
    try:
        return json.load(open(CONFIG, encoding="utf-8"))
    except Exception:
        return {}


def consentir(sim):
    c = _config(); c["relatos"] = bool(sim); c["relatos_respondido"] = time.strftime("%Y-%m-%d")
    json.dump(c, open(CONFIG, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return c["relatos"]


def precisa_perguntar():
    c = _config()
    return "relatos" not in c and not c.get("dono_biblioteca")


def _destino():
    try:
        return json.load(open(os.path.join(SKILL, "relatos", "destino.json"), encoding="utf-8"))
    except Exception:
        return {}


def _versao():
    try:
        for l in open(os.path.join(SKILL, "CHANGELOG.md"), encoding="utf-8"):
            m = re.match(r"## (\S+)", l)
            if m:
                return m.group(1)
    except Exception:
        pass
    return "?"


def _instalacao():
    """Id aleatório da instalação (conta em quantas máquinas o mesmo erro aconteceu). Não identifica a pessoa."""
    os.makedirs(PASTA, exist_ok=True); arq = os.path.join(PASTA, "instalacao.txt")
    if not os.path.exists(arq):
        open(arq, "w").write(hashlib.sha256(os.urandom(32)).hexdigest()[:12])
    return open(arq).read().strip()


def _nomes_privados(cfg):
    nomes = set()
    for d in glob.glob(os.path.join(SKILL, "clientes", "*")):
        b = os.path.basename(d)
        if os.path.isdir(d) and not b.startswith(("_", ".")):
            nomes.add(b)
            try:
                for l in open(os.path.join(d, "cliente.md"), encoding="utf-8"):
                    m = re.match(r"#\s+(.+)", l)
                    if m:
                        nomes.add(m.group(1).strip()); break
            except Exception:
                pass
    saida = os.path.expanduser(cfg.get("pasta_saida", "~/Desktop"))
    for d in glob.glob(os.path.join(saida, "*")):
        if os.path.isdir(d):
            nomes.add(os.path.basename(d))
    try:
        import pwd
        nomes.add(pwd.getpwuid(os.getuid()).pw_gecos.split(",")[0])
    except Exception:
        pass
    nomes.add(os.path.basename(os.path.expanduser("~")))
    return sorted((n for n in nomes if n and len(n) >= 3), key=len, reverse=True)


def anonimizar(txt, nomes):
    if not txt:
        return ""
    t = str(txt).replace(SKILL, "SKILL_DIR").replace(os.path.expanduser("~"), "~")
    t = re.sub(r"(/Users/|/home/|[A-Za-z]:\\\\?Users\\\\?)[^/\\\s]+", "~", t)
    def _so_ext(m):   # caminho fora da skill (pode ter espaço): sobra só a extensão do arquivo
        e = re.findall(r"\.(\w{1,5})$", m.group(0).rstrip(". "))
        return "~/…/*" + ("." + e[0] if e else "")
    t = re.sub(r"~[/\\](?:(?!, |: |;|\n|['\"]).)*", _so_ext, t)
    t = re.sub(r"[\w.+-]+@[\w-]+\.[\w.-]+", "<email>", t)
    t = re.sub(r"\b(sk|pk|rk|ghp|gho|ghs|xox[abp]|AKIA|AIza|ya29)[-_A-Za-z0-9]{12,}", "<chave>", t)
    t = re.sub(r"(?i)\b(api[_-]?key|token|secret|senha|password|authorization|bearer)\b(\s*[:=]\s*|\s+)\S+", r"\1=<oculto>", t)
    t = re.sub(r"\b[A-Za-z0-9_\-]{40,}\b", "<longo>", t)
    t = re.sub(r"(https?://[^\s?#]+)\?[^\s)\"']+", r"\1?<params>", t)
    for n in nomes:
        t = re.sub(re.escape(n), "<cliente>", t, flags=re.I)
    return t


def _assinatura(erro):
    """Mesmo erro em máquinas diferentes = mesma assinatura (números, caminhos e textos entre aspas viram curinga)."""
    e = re.sub(r"\d+(\.\d+)?", "N", erro.lower()); e = re.sub(r"['\"][^'\"]{0,80}['\"]", "S", e)
    e = re.sub(r"~[^\s:]*", "P", e); e = re.sub(r"\s+", " ", e).strip()[:300]
    return hashlib.sha1(e.encode()).hexdigest()[:10]


def registrar(titulo, erro, causa="", correcao="", arquivos=()):
    cfg = _config(); nomes = _nomes_privados(cfg); diff = ""
    if arquivos:
        diff = subprocess.run(["git", "-C", SKILL, "diff", "--"] + list(arquivos), capture_output=True, text=True).stdout
    rel = {"chave_envio": CHAVE_ENVIO, "titulo": titulo, "erro": erro, "causa": causa, "correcao": correcao, "diff": diff}
    for k, lim in LIMITES.items():
        rel[k] = anonimizar(rel[k], nomes)[:lim]
    rel.update({"assinatura": _assinatura(rel["erro"] or rel["titulo"]), "versao": _versao(),
                "sistema": f"{platform.system()} {platform.release()} {platform.machine()}", "python": platform.python_version(),
                "editor": cfg.get("editor", ""), "motion": cfg.get("motion", ""), "instalacao": _instalacao(),
                "quando": time.strftime("%Y-%m-%dT%H:%M:%S")})
    os.makedirs(PEND, exist_ok=True)
    arq = os.path.join(PEND, f"{time.strftime('%Y%m%d-%H%M%S')}-{rel['assinatura']}.json")
    json.dump(rel, open(arq, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return arq


def _log(msg):
    os.makedirs(PASTA, exist_ok=True)
    with open(os.path.join(PASTA, "envio.log"), "a", encoding="utf-8") as f:
        f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + msg + "\n")


def enviar():
    cfg = _config(); url = _destino().get("url", "")
    if cfg.get("relatos") is not True or cfg.get("dono_biblioteca") or not url:   # só com consentimento explícito
        return 0
    os.makedirs(ENV, exist_ok=True); n = 0
    for arq in sorted(glob.glob(os.path.join(PEND, "*.json")))[:20]:
        try:
            req = urllib.request.Request(url, data=open(arq, "rb").read(), headers={"Content-Type": "application/json"}, method="POST")
            resp = json.loads(urllib.request.urlopen(req, timeout=15).read().decode("utf-8") or "{}")
            if resp.get("ok"):
                os.replace(arq, os.path.join(ENV, os.path.basename(arq))); n += 1
            else:
                _log(f"recusado {os.path.basename(arq)}: {resp}")
        except Exception as e:
            _log(f"falhou {os.path.basename(arq)}: {e}"); break   # sem internet: tenta de novo na próxima abertura
    if n:
        _log(f"{n} relato(s) enviado(s)")
    return n


def status():
    cfg = _config(); url = _destino().get("url", "")
    cons = "sim" if cfg.get("relatos") is True else "não" if cfg.get("relatos") is False else "ainda não respondeu"
    return {"consentimento": cons, "maquina_do_dono": bool(cfg.get("dono_biblioteca")), "destino": bool(url),
            "pendentes": len(glob.glob(os.path.join(PEND, "*.json"))), "enviados": len(glob.glob(os.path.join(ENV, "*.json")))}


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        raise SystemExit(__doc__)
    if a[0] == "consentir" and len(a) >= 2:
        print("relatos:", "sim" if consentir(a[1].lower() in ("sim", "s", "yes", "y", "1", "true")) else "não")
    elif a[0] == "perguntar":
        if precisa_perguntar():
            print("PERGUNTAR: " + PERGUNTA)
    elif a[0] == "registrar":
        def arg(n, pad=""):
            return a[a.index(n) + 1] if n in a else pad
        arqs = [a[i + 1] for i, x in enumerate(a) if x == "--arquivo" and i + 1 < len(a)]
        print(registrar(arg("--titulo"), arg("--erro"), arg("--causa"), arg("--correcao"), arqs))
    elif a[0] == "enviar":
        enviar()
    elif a[0] == "status":
        print(json.dumps(status(), ensure_ascii=False))
    else:
        raise SystemExit(__doc__)
