"""Preset LÚDICO: explicador viral no estilo do @ludificando.br, no tema da marca.

  python gerar.py plano.json <pasta_saida> [--tema padrao|<marca>|caminho/tema.json] [--render saida.mp4 --gif]
  (sem --tema: "padrao", estúdio neutro; marca nova = copiar temas/padrao.json ou temas/xtrader.json e trocar as cores)

Duas linguagens no mesmo vídeo (ver PRESET.md):
  - globo: cenas "cidade" (padrão) e "cta", campos do preset globo do /ogab (~/.claude/skills/ogab/presets/globo/gerar.py).
  - estúdio 3D: "tipo": "palco" | "disjuntor" | "barras" | "blocos" | "placas" (cada uma com o cartão, tópicos e carimbo de sempre).
    palco:     {"placa": "X-TRADER", "placas": [{"titulo", "valor", "etiqueta", "em"}]}
    disjuntor: {"rotulo_caixa": "B3", "desliga": "palavra|seg", "religa": "palavra|seg", "relogio": {"de": "10:00", "para": "10:30"}}
    barras:    {"barras": [{"rotulo", "valor", "texto", "de", "destaque", "em"}], "max": 100, "altura": 3.6}
    blocos:    {"n": 140, "colunas": 14, "forma": "grade|arco", "acende": {"fracao", "em"}, "cai": {"fracao", "em"}}
    placas:    {"placas": [{"titulo", "valor", "etiqueta", "em"}]}   (até 4)
    duelo:     {"lados": [{"foto": "fotos/a.jpg", "nome", "valor": "51,79%", "num": 51.79, "destaque", "selo", "em", "em_valor"}]}
               pessoas lado a lado (eleição, A x B): foto em moldura sobre pedestal com altura pelo número; fotos com licença e crédito
    grafico:   {"inicio": 100, "limite": {"valor": 90, "texto", "em"}, "pausa": {"texto", "em"}, "retoma": {"em"},
                "valor_final": 83, "fim_em", "velas": 18, "futuro": true, "completo": true}   candles de um índice
    CTA em qualquer cenário 3D: "cta": true + "pergunta" + "botao" na cena.
    qualquer:  "camera3d": {"pos": [x,y,z], "alvo": [x,y,z]}, "orbita": 0.025
  "em"/"desliga"/"religa": segundos OU uma palavra da fala (a primeira dela depois do começo da cena).
Do tema vêm: cor, serie, fonte, tema3d (cores do estúdio) e as trocas de cor do globo.
"""
import json, os, sys, importlib.util

AQUI = os.path.dirname(os.path.abspath(__file__))
GLOBO = os.path.join(os.path.expanduser("~"), ".claude", "skills", "ogab", "presets", "globo", "gerar.py")


def _globo():
    spec = importlib.util.spec_from_file_location("globo_gerar", GLOBO)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.AQUI = AQUI   # o motor do globo monta com o kit DESTE preset (globo + estúdio 3D)
    return m


def aplicar_tema(pasta, tema):
    arquivos = [os.path.join(pasta, a) for a in os.listdir(pasta) if a.endswith((".css", ".js", ".html")) and a != "plano.js"]
    textos = {a: open(a, encoding="utf-8").read() for a in arquivos}
    faltou = []
    for de, para in tema["trocas"]:
        achou = False
        for a, s in textos.items():
            if de in s:
                textos[a] = s.replace(de, para)
                achou = True
        if not achou:
            faltou.append(de)
    if faltou:
        raise SystemExit("Tema: o kit mudou e estes trechos sumiram (atualizar temas/*.json): " + " | ".join(faltou))
    for a, s in textos.items():
        open(a, "w", encoding="utf-8").write(s)


def copiar_fotos(plano, base, pasta):
    """Fotos do "duelo", do "instagram" e a "logo" das cenas vão para <pasta>/fotos/ e o plano passa a apontar para elas (o render só enxerga a pasta)."""
    import shutil
    def leva(rel):   # copia para <pasta>/fotos/ e devolve o caminho que o render enxerga
        orig = rel if os.path.isabs(rel) else os.path.join(base, rel)
        if not os.path.exists(orig):
            raise SystemExit("Foto não encontrada: " + orig)
        os.makedirs(os.path.join(pasta, "fotos"), exist_ok=True)
        shutil.copy(orig, os.path.join(pasta, "fotos", os.path.basename(orig)))
        return "fotos/" + os.path.basename(orig)
    for c in plano.get("cenas", []):
        if c.get("logo"):   # logo real da instituição/marca citada (regra 27/10/2026)
            c["logo"] = leva(c["logo"])
        pf = c.get("perfil")
        if pf:   # cenário "instagram": foto de perfil e capas da grade
            if pf.get("foto"):
                pf["foto"] = leva(pf["foto"])
            pf["capas"] = [leva(x) for x in pf.get("capas", [])]
        for l in c.get("lados") or []:
            if l.get("foto"):
                orig = l["foto"] if os.path.isabs(l["foto"]) else os.path.join(base, l["foto"])
                if not os.path.exists(orig):
                    raise SystemExit("Foto não encontrada: " + orig)
                os.makedirs(os.path.join(pasta, "fotos"), exist_ok=True)
                shutil.copy(orig, os.path.join(pasta, "fotos", os.path.basename(orig)))
                l["foto"] = "fotos/" + os.path.basename(orig)


def resolver_3d(plano, base, g):
    """Troca palavra por segundo nos campos dos cenários 3D (o motor do globo só resolve os campos dele)."""
    if not plano.get("transcricao"):
        return
    pal = g._palavras_transcricao(plano["transcricao"], base)
    t = 0.0
    for c in plano.get("cenas", []):
        c.setdefault("de", t)
        t = c.get("ate", c["de"] + c.get("dur", 0))

        def quando(v, c=c):
            if v is None or isinstance(v, (int, float)):
                return v
            alvo = g._norm(v)
            for w in pal:
                if w["s"] >= c["de"] - .3 and g._norm(w["t"]) == alvo:
                    return w["s"]
            for w in pal:
                if w["s"] >= c["de"] - .3 and alvo and alvo in g._norm(w["t"]):
                    return w["s"]
            print(f'aviso: palavra "{v}" não achada na cena de {c["de"]:.1f}s; usando o começo da cena', file=sys.stderr)
            return None

        TEMPO = {"em", "em_valor", "desliga", "religa", "apaga"}

        def anda(o):   # todo campo de tempo, em qualquer nível da cena (cenários novos não precisam mexer aqui)
            if isinstance(o, dict):
                for k, v in list(o.items()):
                    if (k in TEMPO or k.endswith("_em")) and isinstance(v, str):
                        o[k] = quando(v)
                    else:
                        anda(v)
            elif isinstance(o, list):
                for x in o:
                    anda(x)
        anda(c)


def batidas(plano, base, g):
    """Movimento contínuo (Gabriel, 27/10/2026: "ele termina o movimento tem que entrar outra coisa, senão não retém"):
    em cada cena, nos vãos sem nenhum evento, uma batida na palavra forte (empurrão de câmera, pulso, onda e faíscas no kit).
    Palavra forte = 4+ letras ou número; longe 0,9 s de qualquer evento da cena e 1,3 s da batida anterior.
    "batidas": false no plano desliga; uma lista de segundos no plano manda."""
    if plano.get("batidas") is False or isinstance(plano.get("batidas"), list) or not plano.get("transcricao"):
        return
    pal = g._palavras_transcricao(plano["transcricao"], base)
    out = []
    for c in plano.get("cenas", []):
        ev = []
        def junta(o):
            if isinstance(o, dict):
                for k, v in o.items():
                    if (k in ("em", "em_valor", "desliga", "religa", "apaga", "botao_em") or k.endswith("_em")) and isinstance(v, (int, float)):
                        ev.append(float(v))
                    else:
                        junta(v)
            elif isinstance(o, list):
                for x in o:
                    junta(x)
        junta(c)
        ev.append(c["de"])
        ult = -9
        for w in pal:
            if not (c["de"] + .9 <= w["s"] <= c.get("ate", 1e9) - .5):
                continue
            n = g._norm(w["t"])
            if len(n) < 4 and not any(ch.isdigit() for ch in n):
                continue
            if min(abs(w["s"] - e) for e in ev) < .9 or w["s"] - ult < 1.3:
                continue
            out.append(round(w["s"], 3)); ult = w["s"]
    plano["batidas"] = out
    print(f"batidas: {len(out)}")


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 2:
        raise SystemExit(__doc__)
    nome_tema = a[a.index("--tema") + 1] if "--tema" in a else "padrao"
    arq_tema = nome_tema if nome_tema.endswith(".json") else os.path.join(AQUI, "temas", nome_tema + ".json")
    tema = json.load(open(arq_tema, encoding="utf-8"))
    caminho_plano = os.path.abspath(a[0])
    base = os.path.dirname(caminho_plano)
    plano = json.load(open(caminho_plano, encoding="utf-8"))
    for k in ("cor", "serie", "fonte", "tema3d"):
        if k in tema:
            plano.setdefault(k, tema[k])
    g = _globo()
    longas = [(i + 1, c.get("tipo", "globo"), round(c["ate"] - c["de"], 1)) for i, c in enumerate(plano["cenas"])
              if "ate" in c and c["ate"] - c["de"] > (7.0 if (c.get("tipo") == "cta" or c.get("cta")) else plano.get("cena_max", 4.5))]
    if longas:   # tela sempre mudando (regra do usuário, 27/10/2026): uma ideia = um elemento novo, nada parado na tela
        raise SystemExit("CENA_LONGA: quebrar em 2-3 elementos novos (máx. 4,5 s; CTA 7 s): " + ", ".join(f"cena {n} ({t}, {d} s)" for n, t, d in longas))
    resolver_3d(plano, base, g)
    batidas(plano, base, g)
    pasta = os.path.abspath(a[1])
    copiar_fotos(plano, base, pasta)
    pasta = g.gerar(plano, pasta, base)
    if plano.get("cenas_extra"):   # cenários do cliente fora do kit (regra: o preset é só a base; os cenários são criados)
        import shutil
        orig = plano["cenas_extra"] if os.path.isabs(plano["cenas_extra"]) else os.path.join(base, plano["cenas_extra"])
        shutil.copy(orig, os.path.join(pasta, "cenas_extra.js"))
        ih = os.path.join(pasta, "index.html"); html = open(ih, encoding="utf-8").read()
        if "cenas_extra.js" not in html:
            html = html.replace('<script src="ludico.js"></script>', '<script src="cenas_extra.js"></script>\n<script src="ludico.js"></script>', 1)
            open(ih, "w", encoding="utf-8").write(html)
    aplicar_tema(pasta, tema)
    print("tema", tema["nome"])
    saida, gif = g.args_render(a)
    if saida:
        g.renderizar(pasta, saida, gif)
