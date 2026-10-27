"""Lê a retenção de público exportada do YouTube Studio e acha onde as pessoas saíram.

  python3 retencao.py retencao.csv [--duracao 612 | --duracao 10:12] [--transcricao transcricao.json] [--json]

Pegar o arquivo: Studio > o vídeo > Análises > Engajamento > gráfico de retenção > ícone de baixar > "Retenção de
público". Duas colunas: a posição (% do vídeo, segundos ou m:ss) e a % que ainda está assistindo. Aceita número com
vírgula decimal (Studio em português) e proporção 0-1.

Três problemas diferentes, com três consertos diferentes:
  GANCHO   o que se perde nos primeiros 30 s. Abaixo de 25% é saudável. Conserto: a 1ª frase do roteiro, nunca a edição.
  QUEDAS   descidas bruscas num ponto: troca de assunto sem aviso, merchan, preparação longa. Com --transcricao
           imprime o que estava sendo dito ali, que é o que torna o relatório útil.
  ESCORRE  a perda constante no meio. Escorrer reto é ritmo: o conserto é cortar, não reescrever.
Com eixo em % do vídeo, a duração vem de --duracao ou do fim da transcrição (sem ela, o gancho vira os primeiros 10%).

Adaptado de youtube-agent-skill (c) 2026 Jake Schincariol, licença MIT.
"""
import csv, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def numero(c):
    c = c.strip().replace("%", "").replace(" ", "").replace(" ", "")
    if re.fullmatch(r"\d+:\d\d(:\d\d)?", c):
        p = [int(x) for x in c.split(":")]
        return p[0] * 60 + p[1] if len(p) == 2 else p[0] * 3600 + p[1] * 60 + p[2]
    if "," in c and "." in c:            # o último separador é o decimal
        c = c.replace(".", "").replace(",", ".") if c.rfind(",") > c.rfind(".") else c.replace(",", "")
    elif "," in c:
        c = c.replace(",", "") if re.fullmatch(r"\d{1,3}(,\d{3})+", c) else c.replace(",", ".")
    try:
        return float(c)
    except ValueError:
        return None


def ler_csv(caminho):
    bruto = open(caminho, encoding="utf-8-sig", errors="replace").read()
    sep = ";" if ";" in bruto.splitlines()[0] or bruto.count(";") > 4 else ","   # Studio em pt usa ; com vírgula decimal
    linhas = []
    for r in csv.reader(bruto.splitlines(), delimiter=sep):
        vals = [v for v in (numero(c) for c in r) if v is not None]
        if len(vals) >= 2:
            linhas.append((vals[0], vals[1]))
    if linhas and max(y for _, y in linhas) <= 1.5:      # proporção 0-1
        linhas = [(x, y * 100) for x, y in linhas]
    if linhas and max(x for x, _ in linhas) <= 1.0:      # posição 0-1
        linhas = [(x * 100, y) for x, y in linhas]
    return linhas


def analisar(linhas, dur=None, cues=None):
    xs = [r[0] for r in linhas]; ys = [r[1] for r in linhas]
    eixo_pct = max(xs) <= 100.5
    if eixo_pct and not dur and cues:
        dur = cues[-1][1]
    def seg(x): return (x / 100.0 * dur) if (eixo_pct and dur) else (None if eixo_pct else x)
    ini = ys[0] or 100.0
    corte = 30.0 if not eixo_pct else (30.0 / dur * 100 if dur else 10.0)
    gancho = ini - min((y for x, y in linhas if x <= corte), default=ini)
    descidas = []
    for i in range(1, len(linhas)):
        d = ys[i - 1] - ys[i]
        descidas.append((d / (xs[i] - xs[i - 1] or 1), xs[i - 1], xs[i], d))
    # quedas só depois do gancho (o gancho já tem a própria linha) e sem repetir pontos vizinhos
    passo = (max(xs) - min(xs)) / max(1, len(xs) - 1)
    quedas = []
    for _, a, b, d in sorted(descidas, reverse=True):
        if len(quedas) >= 5:
            break
        if d > 0.8 and a >= corte and all(abs(a - q["de"]) > 2.5 * passo for q in quedas):
            quedas.append({"de": round(a, 2), "ate": round(b, 2), "perdeu": round(d, 2),
                           "segundo": round(seg(a), 1) if seg(a) is not None else None})
    meio = [taxa for taxa, x0, _, _ in descidas if x0 > corte]
    escorre = sum(meio) / len(meio) if meio else 0
    if cues:
        for q in quedas:
            if q["segundo"] is not None:
                t = q["segundo"]
                q["fala"] = " ".join(c[2] for c in cues if c[0] <= t + 4 and c[1] >= t - 4)[:160]
    return {"pontos": len(linhas), "inicio": ini, "fim": ys[-1], "gancho_perda": round(gancho, 2),
            "quedas": quedas, "escorre_por_unidade": round(escorre, 3), "eixo": "%" if eixo_pct else "s", "duracao": dur}


def main(a):
    como_json = "--json" in a
    tr = a[a.index("--transcricao") + 1] if "--transcricao" in a else None
    dur = numero(a[a.index("--duracao") + 1]) if "--duracao" in a else None
    usados = {tr, a[a.index("--duracao") + 1] if "--duracao" in a else None}
    arqs = [x for x in a if not x.startswith("--") and x not in usados]
    if not arqs or not os.path.exists(arqs[0]):
        sys.exit(__doc__)
    linhas = ler_csv(arqs[0])
    if len(linhas) < 8:
        sys.exit("não consegui ler pelo menos 8 pontos desse CSV")
    cues = None
    if tr and os.path.exists(tr):
        from capitulos import trechos
        cues = trechos(tr)
    r = analisar(linhas, dur, cues)
    if como_json:
        print(json.dumps(r, ensure_ascii=False, indent=1)); return
    unid = "por % do vídeo" if r["eixo"] == "%" else "por segundo"
    print(f"\n{arqs[0]}   {r['pontos']} pontos   {r['inicio']:.1f}% -> {r['fim']:.1f}%\n")
    g = r["gancho_perda"]
    print(f"GANCHO   {g:.1f}% perdidos na abertura   [{'saudável' if g < 25 else 'vazando' if g < 40 else 'grave'}]")
    print("         abaixo de 25 é saudável. Consertar a 1ª frase antes de qualquer outra coisa.\n")
    print("QUEDAS   os momentos em que as pessoas saíram")
    for q in r["quedas"]:
        onde = f"{q['segundo']:.0f}s" if q["segundo"] is not None else f"{q['de']}%"
        print(f"  -{q['perdeu']:5.1f}%  em {onde:>7}" + (f'   "{q["fala"]}"' if q.get("fala") else ""))
    if not r["quedas"]:
        print("  nenhuma acima de 0,8% depois do gancho: a perda é toda escorrida, não um momento")
    print(f"\nESCORRE  {r['escorre_por_unidade']:.3f}% {unid} no meio")
    print("         escorrer reto é ritmo, não conteúdo. Cortar o meio, não reescrever.\n")


if __name__ == "__main__":
    main(sys.argv[1:])
