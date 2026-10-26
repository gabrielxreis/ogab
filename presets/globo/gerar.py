"""Preset GLOBO: explicador de dados num globo 3D que gira até cada cidade, rotas pontilhadas e cartão de dado.

  python3 gerar.py plano.json <pasta_saida> [--render saida.mp4] [--gif]

plano.json: { "w": 1080, "h": 1920, "fps": 30, "cor": "#F4F78A",
  "serie": "LINHA PEQUENA NO TOPO · NOME DA SÉRIE",
  "fontes": "FONTES: IBGE · BACEN · 25/10/2026",        <- OBRIGATÓRIA quando alguma cena tem "numero"
  "cidades": { "varginha": {"nome": "VARGINHA", "lat": -21.55, "lon": -45.43} },   (as da tabela CIDADES já existem)
  "transcricao": "transcricao.json"    (transcrever.py; dá o tempo das palavras para "em" e a legenda)
  "legenda": false,                    (true = legenda karaokê no MP4; ver PRESET.md, regra 1h3)
  "cenas": [
    { "de": 0, "ate": 6.2, "secao": "O CAFÉ", "etiqueta": "DO PÉ À XÍCARA", "foco": "varginha",
      "zoom": 1, "inclina": 7, "giro": 0,                          (câmera: zoom do globo, cidade abaixo do centro, giro em graus)
      "camera": [ {"em": "palavra", "zoom": 0.9, "y": 0.57, "inclina": 12, "giro": 8} ],   (passos de câmera dentro da cena)
      "numero": {"valor": -20, "decimais": 0, "sufixo": "%", "prefixo": "", "sinal": true, "em": "caiu"},  (ou "texto": "R$ 5,51")
      "rotulo": "LINHA EM MAIÚSCULAS", "sub": "linha de apoio",
      "topicos": [ {"texto": "Item que entra na palavra", "em": "palavra"} ],
      "rotas": [ {"de": "varginha", "para": "santos", "em": 2.0, "arco": 0.12, "alt": 0, "dur": 1.1} ],
      "pinos": ["sao_paulo"], "carimbo": {"titulo": "VOCÊ SENTE NO BOLSO", "sub": "linha pequena", "em": "bolso"},
      "fala": "texto falado nesta cena (sem transcrição, a legenda e os 'em' usam o tempo estimado)" },
    { "de": 30, "ate": 34, "tipo": "cta", "foco": "varginha", "pergunta": "Quer mais vídeos assim?", "botao": "COMENTA CAFÉ" } ] }
"em": segundos do vídeo OU uma palavra da fala (a primeira dela depois do início da cena).
Cenas: "de"/"ate" em segundos, ou só "dur" (somadas em sequência). Sem "ate" na última, o vídeo termina nela.
Regra: o número aparece EXATO como está no plano e vem da lista de fatos aprovados; nunca inventar dado.
"""
import json, os, re, sys, unicodedata
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))
from hf_preset import montar, renderizar, args_render

AQUI = os.path.dirname(os.path.abspath(__file__))

CIDADES = {   # lat, lon (graus decimais)
    "brasilia": ("BRASÍLIA", -15.79, -47.88), "sao_paulo": ("SÃO PAULO", -23.55, -46.63), "rio": ("RIO DE JANEIRO", -22.91, -43.17),
    "belo_horizonte": ("BELO HORIZONTE", -19.92, -43.94), "salvador": ("SALVADOR", -12.97, -38.50), "recife": ("RECIFE", -8.05, -34.88),
    "fortaleza": ("FORTALEZA", -3.73, -38.52), "manaus": ("MANAUS", -3.12, -60.02), "porto_alegre": ("PORTO ALEGRE", -30.03, -51.23),
    "curitiba": ("CURITIBA", -25.43, -49.27), "santos": ("SANTOS", -23.96, -46.33), "buenos_aires": ("BUENOS AIRES", -34.60, -58.38),
    "santiago": ("SANTIAGO", -33.45, -70.67), "lima": ("LIMA", -12.05, -77.04), "bogota": ("BOGOTÁ", 4.71, -74.07),
    "cidade_do_mexico": ("CIDADE DO MÉXICO", 19.43, -99.13), "miami": ("MIAMI", 25.76, -80.19), "orlando": ("ORLANDO", 28.54, -81.38),
    "nova_york": ("NOVA YORK", 40.71, -74.01), "washington": ("WASHINGTON", 38.91, -77.04), "chicago": ("CHICAGO", 41.88, -87.63),
    "los_angeles": ("LOS ANGELES", 34.05, -118.24), "sao_francisco": ("SÃO FRANCISCO", 37.77, -122.42), "toronto": ("TORONTO", 43.65, -79.38),
    "londres": ("LONDRES", 51.51, -0.13), "lisboa": ("LISBOA", 38.72, -9.14), "madri": ("MADRI", 40.42, -3.70), "paris": ("PARIS", 48.86, 2.35),
    "frankfurt": ("FRANKFURT", 50.11, 8.68), "berlim": ("BERLIM", 52.52, 13.40), "hamburgo": ("HAMBURGO", 53.55, 9.99),
    "roma": ("ROMA", 41.90, 12.50), "zurique": ("ZURIQUE", 47.38, 8.54), "moscou": ("MOSCOU", 55.76, 37.62), "dubai": ("DUBAI", 25.20, 55.27),
    "jerusalem": ("JERUSALÉM", 31.77, 35.21), "cairo": ("CAIRO", 30.04, 31.24), "lagos": ("LAGOS", 6.52, 3.38),
    "joanesburgo": ("JOANESBURGO", -26.20, 28.05), "mumbai": ("MUMBAI", 19.08, 72.88), "pequim": ("PEQUIM", 39.90, 116.41),
    "xangai": ("XANGAI", 31.23, 121.47), "hong_kong": ("HONG KONG", 22.32, 114.17), "singapura": ("SINGAPURA", 1.35, 103.82),
    "seul": ("SEUL", 37.57, 126.98), "toquio": ("TÓQUIO", 35.68, 139.69), "sydney": ("SYDNEY", -33.87, 151.21),
}


def _norm(s):
    s = unicodedata.normalize("NFD", str(s).lower())
    return re.sub(r"[^a-z0-9%]", "", "".join(c for c in s if unicodedata.category(c) != "Mn"))


def _palavras_transcricao(caminho, base):
    tr = json.load(open(caminho if os.path.isabs(caminho) else os.path.join(base, caminho), encoding="utf-8"))
    out = []
    for seg in tr.get("segments", []):
        for w in seg.get("words", []):
            t = str(w.get("text", w.get("word", ""))).strip()
            if t:
                out.append({"t": t, "s": round(float(w["start"]), 3), "e": round(float(w["end"]), 3)})
    return out


def _palavras_estimadas(cenas):
    """Sem transcrição: espalha a 'fala' de cada cena pelo tempo dela (proporcional ao tamanho da palavra)."""
    out = []
    for c in cenas:
        ws = str(c.get("fala", "")).split()
        if not ws:
            continue
        ini, fim = c["de"] + .25, c["ate"] - .35
        pesos = [len(w) + 2 + (3 if re.search(r"[.,!?:;]$", w) else 0) for w in ws]
        tot, acc = sum(pesos), 0.0
        for w, p in zip(ws, pesos):
            s = ini + (fim - ini) * acc / tot
            acc += p
            out.append({"t": w, "s": round(s, 3), "e": round(ini + (fim - ini) * acc / tot, 3)})
    return out


def gerar(plano, pasta, base="."):
    plano = json.loads(json.dumps(plano))
    for k, v in (("w", 1080), ("h", 1920), ("fps", 30), ("cor", "#F4F78A"), ("legenda", False)):
        plano.setdefault(k, v)
    cenas = plano.get("cenas") or []
    if not cenas:
        raise SystemExit('Falta "cenas".')
    t = 0.0
    for i, c in enumerate(cenas):
        c["de"] = float(c.get("de", t))
        if "ate" not in c:
            if "dur" in c:
                c["ate"] = c["de"] + float(c["dur"])
            elif i + 1 < len(cenas) and "de" in cenas[i + 1]:
                c["ate"] = float(cenas[i + 1]["de"])
            else:
                raise SystemExit(f'Cena {i + 1}: falta "ate" ou "dur".')
        t = c["ate"] = float(c["ate"])
    plano["dur"] = round(float(plano.get("dur", cenas[-1]["ate"])), 3)
    cid = {k: {"nome": n, "lat": la, "lon": lo} for k, (n, la, lo) in CIDADES.items()}
    cid.update(plano.get("cidades") or {})
    usados = set()
    for c in cenas:
        usados.update([c.get("foco")] + list(c.get("pinos") or []))
        for r in c.get("rotas") or []:
            usados.update([r.get("de"), r.get("para")])
    usados.discard(None)
    falta = sorted(u for u in usados if u not in cid)
    if falta:
        raise SystemExit("Cidade sem coordenada: " + ", ".join(falta) + ' (pôr em "cidades": {"id": {"nome", "lat", "lon"}}).')
    plano["cidades"] = {k: cid[k] for k in usados}
    if any(c.get("numero") for c in cenas) and not str(plano.get("fontes", "")).strip():
        raise SystemExit('Falta "fontes": todo número mostra de onde vem (ex.: "FONTES: IBGE · 25/10/2026").')
    pal = _palavras_transcricao(plano.pop("transcricao"), base) if plano.get("transcricao") else _palavras_estimadas(cenas)
    pal = [w for w in pal if w["s"] < plano["dur"] - .1]
    plano["palavras"] = pal

    def quando(v, c, padrao):
        if v is None:
            return round(c["de"] + padrao, 3)
        if isinstance(v, (int, float)):
            return float(v)
        alvo = _norm(v)
        for w in pal:
            if w["s"] >= c["de"] - .3 and _norm(w["t"]) == alvo:
                return w["s"]
        for w in pal:   # palavra só parecida (ex.: "caía" x "caia", pontuação)
            if w["s"] >= c["de"] - .3 and alvo and alvo in _norm(w["t"]):
                return w["s"]
        print(f'aviso: palavra "{v}" não achada na cena de {c["de"]:.1f}s; usando o começo da cena', file=sys.stderr)
        return round(c["de"] + padrao, 3)

    for c in cenas:
        if c.get("numero"):
            c["numero"]["em"] = quando(c["numero"].get("em"), c, .4)
        for tp in c.get("topicos") or []:
            tp["em"] = quando(tp.get("em"), c, .9)
        for r in c.get("rotas") or []:
            r["em"] = quando(r.get("em"), c, .3)
        if c.get("carimbo"):
            c["carimbo"]["em"] = quando(c["carimbo"].get("em"), c, 1.0)
        for p in c.get("camera") or []:
            p["em"] = quando(p.get("em"), c, 1.0)
        c["camera"] = sorted(c.get("camera") or [], key=lambda p: p["em"])
        c.pop("fala", None)
        # para o storyboard.py: duração, tipo e a mensagem da cena
        c["dur"] = round(c["ate"] - c["de"], 3)
        c.setdefault("tipo", "cidade")
        n = c.get("numero") or {}
        num = n.get("texto") or (f'{n["valor"]}{n.get("sufixo", "")}' if "valor" in n else "")
        c["texto"] = " · ".join(x for x in (c.get("secao"), cid.get(c.get("foco"), {}).get("nome"), num, c.get("rotulo"), c.get("pergunta")) if x)
    montar(os.path.join(AQUI, "kit"), plano, pasta, plano["dur"])
    print("ok", pasta, len(cenas), "cenas", plano["dur"], "s", len(pal), "palavras", "legenda" if plano["legenda"] else "sem legenda")
    return pasta


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 2:
        raise SystemExit(__doc__)
    pasta = gerar(json.load(open(a[0], encoding="utf-8")), os.path.abspath(a[1]), os.path.dirname(os.path.abspath(a[0])))
    saida, gif = args_render(a)
    if saida:
        renderizar(pasta, saida, gif)
