"""Comunidade do Gab (lado de quem usa): apresentação OPCIONAL ao Gabriel e lembrete de estrela + Instagram.

  python3 comunidade.py abrir                         # passo zero: imprime PERGUNTAR_APRESENTACAO e/ou LEMBRETE (ou nada)
  python3 comunidade.py apresentar --nome "Ana" [--instagram @ana] [--cidade "Recife"]   # só depois do "sim" da pessoa
  python3 comunidade.py apresentar --nao              # não quer: nunca mais pergunta
  python3 comunidade.py status

Apresentação (regra do Gabriel, 22/10/2026: saber quem usa a skill): perguntada UMA vez, na 3ª abertura (para não
chegar junto do onboarding). O Gab sugere o nome que já conhece da pessoa ("posso dizer que é a Ana?"), mas só manda
o que ela CONFIRMAR, e só nome, @ e cidade, se ela quiser. Vai pelo mesmo Formulário Google dos relatos (tipo
usuario): quem envia só responde, não vê nada da conta do Gabriel. Sem resposta ou "não", nada sai da máquina.
A contagem de quantos usam NÃO depende disso: o Gabriel vê os computadores únicos pelo tráfego do GitHub (uso.py).

Lembrete: a cada LEMBRETE_CADA aberturas e no máximo 1 vez a cada LEMBRETE_DIAS dias, uma linha no FIM da resposta
convidando a dar estrela no repositório e seguir @gabrielxreis_. Para depois de LEMBRETE_MAX vezes. Nunca na máquina
do dono.
"""
import json, os, sys, time

AQUI = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(AQUI)
CONFIG = os.path.join(SKILL, "config.json")
sys.path.insert(0, AQUI)

REPO = "https://github.com/gabrielxreis/ogab"
INSTAGRAM = "https://instagram.com/gabrielxreis_"
LEMBRETE_CADA, LEMBRETE_DIAS, LEMBRETE_MAX = 10, 7, 6
APRESENTAR_NA = 3
PERGUNTA = ("O Gabriel (criador do Gab) gosta de saber quem está usando a skill. Quer se apresentar para ele? É opcional: "
            "vai só o nome que você confirmar (e o @ do Instagram e a cidade, se quiser), nada de projeto, cliente ou "
            "arquivo. Se preferir não, tudo bem, não pergunto de novo.")
LEMBRETE = (f"Se o Gab está te ajudando, deixa uma estrela em {REPO} e segue o Gabriel no Instagram: @gabrielxreis_ "
            f"({INSTAGRAM}). Ajuda muito a skill a crescer.")


def _cfg():
    try:
        return json.load(open(CONFIG, encoding="utf-8"))
    except Exception:
        return {}


def _salvar(c):
    json.dump(c, open(CONFIG, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def abrir():
    """Conta a abertura e devolve as linhas que o Gab deve mostrar (pergunta no começo, lembrete no fim)."""
    c = _cfg()
    if c.get("dono_biblioteca"):
        return []
    com = c.setdefault("comunidade", {})
    com["aberturas"] = int(com.get("aberturas", 0)) + 1
    saida = []
    if "apresentacao" not in com and com["aberturas"] >= APRESENTAR_NA:
        saida.append("PERGUNTAR_APRESENTACAO: " + PERGUNTA)
        com["apresentacao"] = "perguntado"   # uma vez só, mesmo se a pessoa ignorar
    agora = time.time()
    if (com["aberturas"] % LEMBRETE_CADA == 0 and int(com.get("lembretes", 0)) < LEMBRETE_MAX
            and agora - float(com.get("ultimo_lembrete", 0)) > LEMBRETE_DIAS * 86400 and not saida):
        saida.append("LEMBRETE: " + LEMBRETE)
        com["lembretes"] = int(com.get("lembretes", 0)) + 1
        com["ultimo_lembrete"] = agora
    _salvar(c)
    return saida


def apresentar(nome=None, instagram="", cidade="", nao=False):
    c = _cfg(); com = c.setdefault("comunidade", {})
    if nao or not (nome or "").strip():
        com["apresentacao"] = "nao"; _salvar(c)
        return "ok, não pergunto de novo"
    import relatar
    ig = instagram.strip()
    if ig and not ig.startswith("@"):
        ig = "@" + ig.split("/")[-1]
    rel = {"chave_envio": relatar.CHAVE_ENVIO, "tipo": "usuario", "titulo": nome.strip()[:120],
           "erro": ig[:60], "causa": cidade.strip()[:80], "correcao": f"versão {relatar._versao()}",
           "diff": "", "assinatura": "usuario-" + relatar._instalacao(), "versao": relatar._versao(),
           "sistema": f"{__import__('platform').system()}", "editor": c.get("editor", ""),
           "instalacao": relatar._instalacao(), "quando": time.strftime("%Y-%m-%dT%H:%M:%S")}
    os.makedirs(relatar.PEND, exist_ok=True)
    json.dump(rel, open(os.path.join(relatar.PEND, f"{time.strftime('%Y%m%d-%H%M%S')}-usuario.json"), "w",
                        encoding="utf-8"), ensure_ascii=False, indent=1)
    com["apresentacao"] = "sim"; _salvar(c)
    n = relatar.enviar()
    return f"apresentação {'enviada' if n else 'guardada (sai na próxima abertura com internet)'}: {nome}" + (f" {ig}" if ig else "")


def main(a):
    if not a:
        raise SystemExit(__doc__)

    def arg(n, pad=""):
        return a[a.index(n) + 1] if n in a else pad
    if a[0] == "abrir":
        for l in abrir():
            print(l)
    elif a[0] == "apresentar":
        print(apresentar(arg("--nome", None), arg("--instagram"), arg("--cidade"), "--nao" in a))
    elif a[0] == "status":
        print(json.dumps(_cfg().get("comunidade", {}), ensure_ascii=False))
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
