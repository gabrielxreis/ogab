"""Envia o tráfego do Meta Ads de um cliente para o CRM dele (definido em clientes/<cliente>/crm.json).

  python3 painel/crm.py listar                          clientes com CRM e a conta de anúncio de cada um
  python3 painel/crm.py enviar --cliente X arquivo.json manda o resumo (formato em painel/CRM.md)

crm.json (fora do git, viaja pelo Drive junto com a pasta do cliente):
  {"crm": "https://...", "conta_meta": "123", "token_trafego": "..."}
O token só aceita envio de tráfego: não lê nem muda alunos, leads ou qualquer outra coisa do CRM.
"""
import argparse, json, os, sys, urllib.error, urllib.request

PASTA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "clientes")


def config(cliente):
    p = os.path.join(PASTA, cliente, "crm.json")
    if not os.path.exists(p):
        sys.exit(f"SEM_CRM: {cliente} não tem crm.json")
    return json.load(open(p, encoding="utf-8"))


def listar():
    achou = False
    for c in sorted(os.listdir(PASTA)):
        p = os.path.join(PASTA, c, "crm.json")
        if os.path.exists(p):
            d = json.load(open(p, encoding="utf-8"))
            print(f"CRM_CLIENTE: {c} | conta Meta {d.get('conta_meta')} | {d.get('crm')}")
            achou = True
    if not achou:
        print("SEM_CRM: nenhum cliente com crm.json")


def enviar(cliente, arquivo):
    cfg = config(cliente)
    dados = json.load(open(arquivo, encoding="utf-8"))
    g_dias = sum(float(d.get("gasto") or 0) for d in dados.get("dias", []))
    g_camp = sum(float(c.get("gasto") or 0) for c in dados.get("campanhas", []))
    if dados.get("campanhas") and abs(g_dias - g_camp) > 1:
        print(f"AVISO: soma dos dias R$ {g_dias:.2f} diferente da soma das campanhas R$ {g_camp:.2f}")
    req = urllib.request.Request(cfg["crm"].rstrip("/") + "/api/sync/trafego", data=json.dumps(dados).encode(),
                                 headers={"Authorization": f"Bearer {cfg['token_trafego']}", "Content-Type": "application/json",
                                          "User-Agent": "ojhon-crm"})
    try:
        r = urllib.request.urlopen(req, timeout=60).read().decode()
        print(f"CRM_ATUALIZADO: {cliente} {r} (R$ {g_dias:.2f} em {len(dados.get('dias', []))} dias)")
    except urllib.error.HTTPError as e:
        sys.exit(f"CRM_FALHOU: {cliente} HTTP {e.code} {e.read().decode(errors='replace')[:200]}")
    except Exception as e:
        sys.exit(f"CRM_FALHOU: {cliente} {e}")


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("acao", choices=["listar", "enviar"])
    a.add_argument("--cliente"); a.add_argument("arquivo", nargs="?")
    x = a.parse_args()
    listar() if x.acao == "listar" else enviar(x.cliente, x.arquivo)
