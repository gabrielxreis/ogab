"""Números do negócio de uma empresa, para o Gab mentor (/ogab negocio): ficha, série semanal, painel com alertas e diário.

  python3 negocio.py iniciar <empresa>                       # cria clientes/<empresa>/negocio/ (negocio.md + numeros.json)
  python3 negocio.py meta <empresa> <valor_mensal>           # meta de faturamento por mês (R$)
  python3 negocio.py semana <empresa> [--data AAAA-MM-DD] [--faturamento N] [--recebido N] [--custos N] [--leads N]
        [--vendas N] [--caixa N] [--custo_fixo N] [--divida N] [--lucro_mes N] [--clientes N] [--maior_cliente_pct N]
        [--cac N] [--ltv N]
        # registra um lançamento. Fluxo (somado no mês): faturamento, recebido, custos, leads, vendas.
        # Posição (vale o último): caixa, custo_fixo (mensal), divida, lucro_mes, clientes, maior_cliente_pct, cac, ltv.
  python3 negocio.py painel <empresa>                        # placar do mês, tendência, caixa em meses e ALERTAs
  python3 negocio.py anotar <empresa> "texto"                # decisão ou aprendizado com data no negocio.md

Valores em reais, sem ponto de milhar (1.500,50 ou 1500.50 também servem). Os alertas seguem as regras de decisão de
docs/etapas/negocios.md (caixa < 3 meses, recebido < 85%, margem < 20%, cliente > 1/3, dívida > 3x lucro, LTV/CAC < 3).
"""
import datetime as dt, json, os, re, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FLUXO = ["faturamento", "recebido", "custos", "leads", "vendas"]
POSICAO = ["caixa", "custo_fixo", "divida", "lucro_mes", "clientes", "maior_cliente_pct", "cac", "ltv"]
MODELO = """# Negócio: {empresa}

## Ficha
- O que vende, para quem, ticket:
- Como o cliente chega e como paga:
- Time e sócios (quem faz o quê; quanto o dono ainda executa):
- Meta:

## Diagnóstico (nota 1 a 5 e porquê)
- Estratégia:
- Vendas:
- Marketing:
- Finanças:
- Pessoas:
- Gestão:
- Gargalo número 1:

## Plano de 90 dias
| Prioridade | Ação | Dono | Prazo | Número (hoje > alvo) |
|---|---|---|---|---|

## Decisões e aprendizados
"""


def pasta(empresa):
    return os.path.join(RAIZ, "clientes", empresa, "negocio")


def carregar(empresa):
    p = os.path.join(pasta(empresa), "numeros.json")
    if not os.path.exists(p):
        raise SystemExit(f"SEM_NEGOCIO: rode antes `negocio.py iniciar {empresa}`")
    return json.load(open(p, encoding="utf-8"))


def salvar(empresa, d):
    p = os.path.join(pasta(empresa), "numeros.json")
    tmp = p + ".tmp"
    json.dump(d, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    os.replace(tmp, p)


def numero(txt):
    t = str(txt).strip().replace("R$", "").replace(" ", "")
    if re.search(r",\d{1,2}$", t):
        t = t.replace(".", "").replace(",", ".")
    else:
        t = t.replace(",", "")
    return float(t)


def reais(v):
    s = f"{abs(v):,.0f}".replace(",", ".")
    return ("-" if v < 0 else "") + "R$ " + s


def barra(frac, larg=20):
    frac = max(0.0, min(1.0, frac))
    n = int(round(frac * larg))
    return "█" * n + "·" * (larg - n)


def iniciar(empresa):
    p = pasta(empresa)
    os.makedirs(p, exist_ok=True)
    md = os.path.join(p, "negocio.md")
    if not os.path.exists(md):
        open(md, "w", encoding="utf-8").write(MODELO.format(empresa=empresa))
    js = os.path.join(p, "numeros.json")
    if not os.path.exists(js):
        salvar(empresa, {"empresa": empresa, "meta_mensal": None, "lancamentos": []})
    print(f"OK {p}")


def opcoes(args):
    o, i = {}, 0
    while i < len(args):
        if args[i].startswith("--") and i + 1 < len(args):
            o[args[i][2:]] = args[i + 1]
            i += 2
        else:
            raise SystemExit(f"argumento inesperado: {args[i]}")
    return o


def semana(empresa, args):
    d = carregar(empresa)
    o = opcoes(args)
    data = o.pop("data", dt.date.today().isoformat())
    dt.date.fromisoformat(data)
    reg = {"data": data}
    for k, v in o.items():
        if k not in FLUXO + POSICAO:
            raise SystemExit(f"campo desconhecido: --{k} (use {', '.join(FLUXO + POSICAO)})")
        reg[k] = numero(v)
    d["lancamentos"].append(reg)
    d["lancamentos"].sort(key=lambda r: r["data"])
    salvar(empresa, d)
    print(f"OK lançamento {data}: " + ", ".join(f"{k}={v:g}" for k, v in reg.items() if k != "data"))


def ultimo(lanc, campo):
    for r in reversed(lanc):
        if campo in r:
            return r[campo]
    return None


def soma_mes(lanc, campo, ano, mes):
    vals = [r[campo] for r in lanc if campo in r and r["data"][:7] == f"{ano:04d}-{mes:02d}"]
    return sum(vals) if vals else None


def painel(empresa):
    d = carregar(empresa)
    lanc = d["lancamentos"]
    hoje = dt.date.today()
    print(f"NEGÓCIO: {empresa}  ({len(lanc)} lançamentos, último {lanc[-1]['data'] if lanc else 'nenhum'})")
    if not lanc:
        print("Sem números ainda: registrar com `negocio.py semana`.")
        return
    ref = dt.date.fromisoformat(lanc[-1]["data"])
    ano, mes = ref.year, ref.month
    pa, pm = (ano, mes - 1) if mes > 1 else (ano - 1, 12)
    fat = soma_mes(lanc, "faturamento", ano, mes)
    fat_ant = soma_mes(lanc, "faturamento", pa, pm)
    meta = d.get("meta_mensal")
    if fat is not None:
        linha = f"Faturamento {ref:%m/%Y}: {reais(fat)}"
        if meta:
            linha += f"  meta {reais(meta)}  {barra(fat / meta)} {fat / meta:.0%}"
        if fat_ant:
            linha += f"  (mês anterior {reais(fat_ant)}, {fat / fat_ant - 1:+.0%})"
        print(linha)
    alertas = []
    rec = soma_mes(lanc, "recebido", ano, mes)
    if fat and rec is not None:
        print(f"Recebido: {reais(rec)} ({rec / fat:.0%} do faturado)")
        if rec / fat < 0.85:
            alertas.append(f"recebido é {rec / fat:.0%} do faturado: o problema é cobrança e forma de pagamento, não venda")
    custos = soma_mes(lanc, "custos", ano, mes)
    if fat and custos is not None:
        marg = (fat - custos) / fat
        print(f"Custos do mês: {reais(custos)}  margem {marg:.0%}")
        if marg < 0.20:
            alertas.append(f"margem de {marg:.0%}: rever preço e escopo antes de buscar mais clientes")
    leads, vendas = soma_mes(lanc, "leads", ano, mes), soma_mes(lanc, "vendas", ano, mes)
    if leads:
        conv = f", conversão {vendas / leads:.0%}" if vendas is not None else ""
        print(f"Funil do mês: {leads:g} leads{f', {vendas:g} vendas' if vendas is not None else ''}{conv}")
    if vendas and fat:
        print(f"Ticket médio: {reais(fat / vendas)}")
    caixa, fixo = ultimo(lanc, "caixa"), ultimo(lanc, "custo_fixo")
    if caixa is not None:
        if fixo:
            meses = caixa / fixo
            print(f"Caixa: {reais(caixa)} = {meses:.1f} meses de custo fixo ({reais(fixo)}/mês)")
            if meses < 3:
                alertas.append(f"caixa para {meses:.1f} meses: prioridade zero é caixa (cobrar, cortar custo ruim, vender para a base)")
        else:
            print(f"Caixa: {reais(caixa)} (registrar --custo_fixo para ver quantos meses aguenta)")
    divida, lucro = ultimo(lanc, "divida"), ultimo(lanc, "lucro_mes")
    if divida:
        if lucro and lucro > 0:
            x = divida / lucro
            print(f"Dívida: {reais(divida)} = {x:.1f} meses de lucro")
            if x > 3:
                alertas.append(f"dívida de {x:.1f} meses de lucro: renegociar e atacar a mais cara primeiro")
        else:
            print(f"Dívida: {reais(divida)}" + (" com lucro zero ou negativo" if lucro is not None else ""))
            if lucro is not None:
                alertas.append("dívida sem lucro para pagar: renegociar antes de qualquer investimento")
    conc = ultimo(lanc, "maior_cliente_pct")
    if conc is not None and conc > 33:
        alertas.append(f"maior cliente é {conc:g}% da receita: montar alternativa em 90 dias")
    cac, ltv = ultimo(lanc, "cac"), ultimo(lanc, "ltv")
    if cac and ltv:
        r = ltv / cac
        print(f"LTV/CAC: {r:.1f}")
        if r < 3:
            alertas.append(f"LTV/CAC de {r:.1f} (mínimo saudável 3): levar para o tráfego (/ogab trafego) com esses números")
    serie = [(r["data"], r["faturamento"]) for r in lanc if "faturamento" in r][-8:]
    if len(serie) >= 2:
        mx = max(v for _, v in serie) or 1
        print("Últimos lançamentos de faturamento:")
        for data, v in serie:
            print(f"  {data}  {barra(v / mx, 16)} {reais(v)}")
    if (hoje - ref).days > 10:
        alertas.append(f"último lançamento há {(hoje - ref).days} dias: pedir os números da semana")
    for a in alertas:
        print(f"ALERTA: {a}")
    if not alertas:
        print("Sem alertas.")


def anotar(empresa, texto):
    md = os.path.join(pasta(empresa), "negocio.md")
    if not os.path.exists(md):
        raise SystemExit(f"SEM_NEGOCIO: rode antes `negocio.py iniciar {empresa}`")
    s = open(md, encoding="utf-8").read().rstrip("\n")
    open(md, "w", encoding="utf-8").write(f"{s}\n- {dt.date.today():%d/%m/%Y}: {texto}\n")
    print("OK anotado")


def main():
    a = sys.argv[1:]
    if len(a) < 2:
        raise SystemExit(__doc__)
    cmd, empresa = a[0], a[1]
    if cmd == "iniciar":
        iniciar(empresa)
    elif cmd == "meta":
        d = carregar(empresa)
        d["meta_mensal"] = numero(a[2])
        salvar(empresa, d)
        print(f"OK meta mensal {reais(d['meta_mensal'])}")
    elif cmd == "semana":
        semana(empresa, a[2:])
    elif cmd == "painel":
        painel(empresa)
    elif cmd == "anotar":
        anotar(empresa, " ".join(a[2:]))
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
