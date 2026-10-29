"""Passo zero do Gab numa chamada só (economia de tokens, regra do Gabriel 28/10/2026: antes eram 8 comandos e 8 saídas).
Roda na ordem: atualizar > termos > licença > abrir o cofre > novidades > componentes > comunidade > relatos (fundo).
Imprime SÓ o que pede ação; tudo certo = 3 linhas (CONTEUDO_PRONTO, CONFIG e, se houver, o que mudou no cofre).

  python3 inicio.py        # sai 0 = seguir; 1 = PARAR e mostrar a mensagem (termos, key, cofre)

Linhas que podem sair (o SKILL.md do carregador diz o que fazer com cada uma):
  ATUALIZADO: ... / ATUALIZAR_FALHOU: ...       avisar em uma linha e seguir
  TERMOS_PENDENTES (+ resumo)                   mostrar o resumo e PARAR até a pessoa digitar ACEITO
  LICENCA_* (+ mensagem)                        mostrar e PARAR
  CONTEUDO_PRONTO: <pasta>                      o mapa é <pasta>/SKILL.md
  CONFIG: editor=... motion=... dono=...        qual README de editor/motion vale (não ler os outros)
  MUDOU_NO_COFRE: <arquivos>                    desde a última abertura nesta máquina: reler só esses
  NOVIDADES: (bloco)                            primeira coisa da resposta, em lista curta
  COMPONENTES: ... / PERGUNTAR_APRESENTACAO: ... / LEMBRETE: ...   como no SKILL.md do carregador
"""
import json, os, subprocess, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(AQUI)
VISTO = os.path.join(os.path.expanduser("~"), ".claude", "ogab_manifesto_visto.json")


def rodar(*args, timeout=180):
    try:
        r = subprocess.run([sys.executable, os.path.join(AQUI, args[0])] + list(args[1:]),
                           capture_output=True, text=True, timeout=timeout, cwd=SKILL)
        return r.returncode, (r.stdout + r.stderr).strip()
    except Exception as e:  # nunca travar o passo zero por um script auxiliar
        return 99, f"{args[0]}: {e}"


def config():
    try:
        c = json.load(open(os.path.join(SKILL, "config.json"), encoding="utf-8"))
    except Exception:
        c = {}
    return (f"CONFIG: editor={c.get('editor', 'davinci')} motion={c.get('motion', 'hyperframes')} "
            f"dono={'sim' if c.get('dono_biblioteca') else 'nao'} "
            f"boas_vindas={'sim' if c.get('boas_vindas_mostrada') else 'nao'}")


def mudou_no_cofre():
    try:
        atual = json.load(open(os.path.join(SKILL, "cofre", "manifesto.json"), encoding="utf-8"))["arquivos"]
    except Exception:
        return None
    try:
        antes = json.load(open(VISTO, encoding="utf-8"))
    except Exception:
        antes = None
    try:
        json.dump(atual, open(VISTO, "w", encoding="utf-8"))
    except Exception:
        pass
    if antes is None:
        return None  # primeira vez: lê o mapa normal, nada a comparar
    return sorted(k for k, v in atual.items() if antes.get(k) != v)


def main():
    out = []
    cod, txt = rodar("atualizar.py")
    for l in txt.splitlines():
        if l.startswith("ATUALIZADO"):
            out.append(l)
    if cod not in (0,) and txt:
        out.append("ATUALIZAR_FALHOU: " + txt.splitlines()[-1][:160])

    cod, txt = rodar("termos.py", "checar")
    if cod != 0:
        print("\n".join(out + ["TERMOS_PENDENTES", rodar("termos.py", "resumo")[1]]))
        return 1

    cod, txt = rodar("licenca.py", "checar")
    if cod != 0:
        print("\n".join(out + [txt]))
        return 1
    out += [l for l in txt.splitlines() if l.startswith("LICENCA_OFFLINE")]

    cod, txt = rodar("carregar.py")
    if cod != 0 or "CONTEUDO_PRONTO" not in txt:
        print("\n".join(out + [txt]))
        return 1
    out += [l for l in txt.splitlines() if l.startswith(("CONTEUDO_PRONTO", "COFRE_OFFLINE"))]
    out.append(config())
    m = mudou_no_cofre()
    if m:
        out.append("MUDOU_NO_COFRE: " + ", ".join(m))

    _, txt = rodar("novidades.py")
    if txt:
        out += ["NOVIDADES:", txt]
    _, txt = rodar("componentes.py", "checar", timeout=20)
    out += [l for l in txt.splitlines() if l.startswith("COMPONENTES")]
    _, txt = rodar("comunidade.py", "abrir", timeout=20)
    out += [l for l in txt.splitlines() if l.startswith(("PERGUNTAR_APRESENTACAO", "LEMBRETE"))]

    try:  # relatos anônimos: em segundo plano, sem saída
        subprocess.Popen([sys.executable, os.path.join(AQUI, "relatar.py"), "enviar"], cwd=SKILL,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    except Exception:
        pass
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
