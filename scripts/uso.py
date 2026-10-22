"""Quantas pessoas usam o Gab (lado do DONO: /ogab uso). Nada é coletado de quem usa para esta contagem.

  python3 uso.py              # usuários únicos por dia (média 7 e 14 dias), estrelas e quem se apresentou
  python3 uso.py --csv respostas.csv   # lista de apresentações a partir do CSV da planilha (sem gws)

Contagem: o auto-update roda `git pull` toda vez que o Gab abre, e o GitHub conta os computadores únicos que
buscaram o repositório (API de tráfego, só o dono vê, guarda 14 dias). Este script junta cada consulta num
histórico local (~/.claude/ogab_relatos/uso.json) para não perder o que passa dos 14 dias. É aproximado: um
computador conta uma vez por dia; quem roda em dois computadores conta duas.
Apresentações: linhas `tipo` usuario da planilha dos relatos (só quem aceitou se apresentar; scripts/comunidade.py).
"""
import json, os, subprocess, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
REPO = "gabrielxreis/ogab"
HIST = os.path.expanduser("~/.claude/ogab_relatos/uso.json")


def _gh(caminho):
    r = subprocess.run(["gh", "api", caminho], capture_output=True, text=True, timeout=60)
    if r.returncode:
        raise SystemExit(f"gh api {caminho} falhou: {r.stderr.strip()[:200]} (gh logado na conta dona do repositório?)")
    return json.loads(r.stdout)


def atualizar():
    try:
        h = json.load(open(HIST, encoding="utf-8"))
    except Exception:
        h = {"dias": {}}
    cl = _gh(f"repos/{REPO}/traffic/clones")
    vi = _gh(f"repos/{REPO}/traffic/views")
    for x in cl.get("clones", []):
        d = h["dias"].setdefault(x["timestamp"][:10], {})
        d["computadores"], d["buscas"] = x["uniques"], x["count"]
    for x in vi.get("views", []):
        h["dias"].setdefault(x["timestamp"][:10], {})["visitas_site"] = x["uniques"]
    repo = _gh(f"repos/{REPO}")
    h["estrelas"], h["forks"] = repo.get("stargazers_count", 0), repo.get("forks_count", 0)
    h["unicos_14d"] = cl.get("uniques", 0)
    os.makedirs(os.path.dirname(HIST), exist_ok=True)
    json.dump(h, open(HIST, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return h


def apresentacoes(csv_arq=None):
    try:
        import banco_presets
        ls = banco_presets.linhas(csv_arq)
    except SystemExit as e:
        return None, str(e).splitlines()[0]
    vistos = {}
    for l in ls:
        if (l.get("tipo") or "").strip().lower() == "usuario":
            vistos[l.get("instalacao") or l.get("titulo")] = l   # a mais recente de cada instalação
    return list(vistos.values()), None


def main(a):
    h = atualizar()
    dias = sorted((d, v) for d, v in h["dias"].items() if v.get("computadores"))
    def media(n):
        ult = [v["computadores"] for _, v in dias[-n:]]
        return sum(ult) / len(ult) if ult else 0
    print(f"Computadores únicos nos últimos 14 dias: {h['unicos_14d']}")
    print(f"Média por dia: {media(7):.0f} (7 dias) | {media(14):.0f} (14 dias) | recorde: "
          + (max(dias, key=lambda x: x[1]['computadores'])[0] + f" com {max(v['computadores'] for _, v in dias)}" if dias else "-"))
    print(f"Estrelas: {h['estrelas']} | forks: {h['forks']}")
    print("\nÚltimos dias (computadores únicos):")
    for d, v in dias[-10:]:
        print(f"  {d}  {v['computadores']:>4}  " + "#" * min(60, v["computadores"] // 4))
    pessoas, erro = apresentacoes(a[a.index("--csv") + 1] if "--csv" in a else None)
    if pessoas is None:
        print(f"\nApresentações: não li a planilha ({erro})")
    else:
        print(f"\nSe apresentaram: {len(pessoas)}")
        for l in pessoas:
            print(f"  - {l.get('titulo')}")


if __name__ == "__main__":
    main(sys.argv[1:])
