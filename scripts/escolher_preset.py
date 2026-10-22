"""Escolhe o preset certo para cada pedido e para cada trecho do vídeo (cérebro: presets/catalogo.json).

  python3 escolher_preset.py pedido "<o que o usuário pediu>" [--formato vertical|horizontal]
      -> que fluxo/preset atende o pedido (anima arte, cortes, abertura de logo, lançamento, lottie...) e a linguagem
  python3 escolher_preset.py sugerir <roteiro.txt | transcricao.json> [--formato vertical|horizontal]
      [--apresentador sim|nao] [--falantes 2] [--marca Nome] [--cliente <pasta de clientes/>] [--forcar <preset>]
      [--saida sugestao.json]
      -> escolhe a LINGUAGEM do vídeo (preset que dá o estilo) e, trecho a trecho, a cena dela ou um preset especial
         (gráfico no dado com fonte, ranking, comentário, marco, respostas...) com o motivo de cada escolha
  python3 escolher_preset.py conferir   -> preset em presets/ sem entrada no catalogo.json ou sem GIF (rodar antes do commit)
  python3 escolher_preset.py listar [--categoria dados|produto|apresentador|ideia|lista|social|marca]

A sugestão é o ponto de partida: o Gab lê, ajusta com o que sabe do cliente e mostra a tabela ao usuário, oferecendo
o seletor visual (scripts/seletor.py sugestao.json) para quem quiser escolher pelas miniaturas.
"""
import json, os, re, sys, unicodedata

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAT = os.path.join(SKILL, "presets", "catalogo.json")


def norm(t):
    t = unicodedata.normalize("NFD", str(t).lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def tem(n, kw):
    """kw é começo de palavra (ou frase inteira se tiver espaço/símbolo)."""
    if kw.startswith("@"):
        return False
    if re.search(r"[^a-z0-9]", kw.strip()):
        return kw in n
    return re.search(r"(?<![a-z0-9])" + re.escape(kw), n) is not None


def catalogo():
    c = json.load(open(CAT, encoding="utf-8"))
    for p in c["presets"]:
        if not p.get("gif"):
            g = (p.get("gifs") or [None])[0] or f"presets/{p['id']}/exemplo.gif"
            p["gif"] = g if os.path.exists(os.path.join(SKILL, g)) else ""
    return c


# ---------- sinais da frase ----------
NUM_PAL = r"(dois|duas|tres|quatro|cinco|seis|sete|oito|nove|dez|\d+)"
LISTAVEIS = r"(regras|coisas|dicas|erros|passos|motivos|formas|habitos|apps|aplicativos|ferramentas|sites|segredos|maneiras|jeitos|licoes|sinais|perguntas)"


def sinais(txt, ctx):
    n = norm(txt); pal = re.findall(r"[a-z0-9%$]+", n)
    f = set()
    if re.search(r"\d", n): f.add("numero")
    if re.search(r"\d[\d.,]*\s*(mil|milhao|milhoes|k\b|bi)", n) or re.search(r"\d{2,3}[.]\d{3}", n) or "milhao" in n or "milhoes" in n: f.add("numero_grande")
    if "%" in n or "por cento" in n or "porcento" in n: f.add("porcentagem")
    if re.search(r"r\$|reais|\breal\b|dolar|grana|dinheiro|salario|\bpix\b", n): f.add("dinheiro")
    if "?" in txt: f.add("pergunta")
    if "!" in txt: f.add("exclamacao")
    if len(pal) <= 3: f.add("curta")
    if re.search(r"\b(primeir[oa]|segund[oa]|terceir[oa]|em primeiro|por ultimo)\b", n) or re.search(r"(^|\s)\d[.)]\s", n) or n.count(",") >= 2: f.add("lista")
    if re.search(NUM_PAL + r"\s+(\w+\s+)?" + LISTAVEIS, n): f.add("lista_anunciada"); f.add("lista")
    if re.search(r"antes e depois|\bversus\b|\bvs\b|\bcontra\b|melhor que|pior que|mais .{1,20} do que|enquanto", n): f.add("comparacao")
    if re.search(r"segundo (o|a|os|as) |pesquisa|estudo|levantamento|dados d|ibge|fonte|relatorio", n): f.add("fonte")
    if re.search(r"\b(sempre|nunca|todos|ninguem|maioria|poucos|enquanto|quem)\b", n) and re.search(r"\b(voce|seu|sua|todos|quem)\b", n): f.add("efeito")
    if re.search(r"\b(eu|meu|minha|comigo|aprendi|descobri)\b", n): f.add("primeira_pessoa")
    if re.search(r"seculo|antig|\bem 1\d{3}\b|\bano \d{3,4}\b|historia|biblia|imperio|faraó|farao|rei ", n): f.add("historico")
    if re.search(r"perfil|seguidor|notific|inscrit|arquivo|cotac|\bpreco|\bbotao|\bjanela", n): f.add("interface")
    if re.search(r"\b(app|apps|aplicativo|site|ferramenta|extensao|plugin)\b|\bia\b|chatgpt|claude|gemini|canva|notion", n): f.add("ferramenta")
    if re.search(r"tier|ranking|\btop \d|\btop (tres|cinco)|(primeiro|segundo|terceiro|ultimo) lugar|podio|do pior|do melhor", n): f.add("ranking")
    if re.search(r"comentou|me perguntaram|comentario|perguntou|respondendo|mandaram (no|na)", n): f.add("comentario")
    if re.search(r"depoiment|alunos?\b|clientes?\b|resultado|feedback|transformou", n): f.add("prova")
    if re.search(r"\b(segue|siga|link na bio|comenta|comente|inscrev|clica|clique|acesse|baixe|garanta|compartilh|salva|salve|manda pra)\b", n): f.add("cta")
    if ctx.get("marca") and any(tem(n, norm(m)) for m in ctx["marca"]): f.add("marca")
    partes = [x.strip() for x in re.split(r",| e ", re.sub(r"[.!?]", "", n)) if x.strip()]
    if len(partes) >= 3 and all(len(x.split()) <= 3 for x in partes): f.add("tres_adjetivos")
    if ctx.get("falantes", 1) >= 2: f.add("dois_falantes")
    return n, f


# ---------- pontuação ----------
def ok_contexto(p, ctx):
    if ctx["formato"] not in p.get("formato", ["vertical", "horizontal"]):
        return False
    ap = p.get("apresentador", "tanto_faz")
    if ap == "precisa" and ctx.get("apresentador") == "nao":
        return False
    if p["id"] == "podcast" and ctx.get("falantes", 1) < 2:
        return False
    return True


def nota(p, n, f):
    s, motivo = 0.0, []
    hits = [k for k in p.get("sinais", []) if tem(n, k)]
    if hits:
        s += min(3, len(hits)); motivo.append("fala " + ", ".join(f'"{h.strip()}"' for h in hits[:3]))
    for k, w in p.get("padroes", {}).items():
        if k in f:
            s += w; motivo.append(k.replace("_", " "))
    if any(tem(n, k) for k in p.get("evitar", [])):
        s -= 5; motivo.append("tema que o preset evita")
    return s, motivo


def escolher_cena(p, n, f, i, total, ant):
    cenas = p.get("cenas") or {}
    if not cenas:
        return "", ""
    especiais = {"@primeira": i == 0, "@ultima": i == total - 1, "@marca": "marca" in f, "@lista": "lista" in f, "@numero": "numero" in f,
                 "@pergunta": "pergunta" in f, "@exclamacao": "exclamacao" in f, "@tres_adjetivos": "tres_adjetivos" in f,
                 "@cta": "cta" in f, "@pessoa_historica": "historico" in f}
    melhor, mv, porque = list(cenas)[0], 0, "cena padrão do preset"
    for nome, kws in cenas.items():
        v, pq = 0, ""
        for k in kws:
            if k.startswith("@") and especiais.get(k):
                v += 3 if k in ("@ultima", "@primeira") else 2; pq = {"@primeira": "gancho do vídeo", "@ultima": "fecho do vídeo", "@marca": "cita a marca", "@lista": "é uma lista",
                    "@numero": "tem número", "@pergunta": "é pergunta", "@exclamacao": "é reação", "@tres_adjetivos": "três qualidades em fila",
                    "@cta": "chamada para ação", "@pessoa_historica": "fato histórico"}[k]
            elif tem(n, k):
                v += 1; pq = pq or f'fala "{k.strip()}"'
        if v > mv:
            melhor, mv, porque = nome, v, pq
    if ant and ant[-2:] == [melhor, melhor] and mv <= 1:    # nada de três cenas iguais seguidas por acaso
        for nome in cenas:
            if nome != melhor and not any(k.startswith("@") for k in cenas[nome]):
                return nome, "variar (três iguais seguidas)"
    return melhor, porque


def frases_de(arq):
    if arq.lower().endswith(".json"):
        d = json.load(open(arq, encoding="utf-8")); segs = d.get("segments") or d.get("trechos") or d if isinstance(d, (dict, list)) else []
        if isinstance(segs, dict): segs = []
        out, cur = [], []
        for s in segs:
            ws = s.get("words") or s.get("palavras")
            if not ws:
                out.append({"ini": s.get("start", 0), "fim": s.get("end", 0), "texto": s.get("text", "").strip()}); continue
            for w in ws:
                cur.append(w)
                if re.search(r"[.!?]$", (w.get("text") or w.get("word") or "").strip()):
                    out.append({"ini": cur[0].get("start", 0), "fim": cur[-1].get("end", 0), "texto": " ".join((x.get("text") or x.get("word") or "").strip() for x in cur)}); cur = []
        if cur:
            out.append({"ini": cur[0].get("start", 0), "fim": cur[-1].get("end", 0), "texto": " ".join((x.get("text") or x.get("word") or "").strip() for x in cur)})
        return [x for x in out if x["texto"]]
    txt = open(arq, encoding="utf-8").read()
    partes = [p.strip() for p in re.split(r"(?<=[.!?])\s+|\n+", txt) if p.strip() and not p.strip().startswith("#")]
    return [{"ini": None, "fim": None, "texto": p} for p in partes]


def preset_do_cliente(cliente):
    if not cliente:
        return None
    for base in (os.path.join(SKILL, "clientes", cliente), cliente):
        e = os.path.join(base, "estilo.md")
        if os.path.exists(e):
            m = re.search(r"^\s*-?\s*\**preset\**\s*:\s*\**\s*([a-z0-9-]+)", open(e, encoding="utf-8").read(), re.I | re.M)
            if m:
                return m.group(1).lower()
    return None


def sugerir(arq, ctx):
    C = catalogo(); P = [p for p in C["presets"] if ok_contexto(p, ctx)]; por_id = {p["id"]: p for p in C["presets"]}
    fr = frases_de(arq)
    if not fr:
        raise SystemExit("roteiro vazio")
    tudo = norm(" ".join(x["texto"] for x in fr))
    for x in fr:
        x["n"], x["f"] = sinais(x["texto"], ctx)
    # 1. linguagem do vídeo
    ling = [p for p in P if p.get("papel") == "linguagem"]
    total = {}
    for p in ling:
        s = sum(max(0, nota(p, x["n"], x["f"])[0]) for x in fr) / max(1, len(fr)) * 4
        nh = [k for k in p.get("nichos", []) if tem(tudo, k)]
        s += min(6, 1.5 * len(nh))
        if ctx.get("apresentador") == "sim" and p.get("apresentador") == "precisa": s += 2
        if ctx.get("apresentador") == "sim" and p.get("apresentador") == "sem": s -= 2
        if ctx.get("apresentador") == "nao" and p.get("apresentador") == "sem": s += 1
        total[p["id"]] = (round(s, 2), nh)
    forc = ctx.get("forcar") or preset_do_cliente(ctx.get("cliente"))
    ordem = sorted(total, key=lambda k: -total[k][0])
    lid = forc if forc in por_id else (ordem[0] if ordem else None)
    L = por_id.get(lid)
    por_que_l = ("pedido/estilo do cliente" if forc == lid else
                 ("nicho: " + ", ".join(total[lid][1][:4]) if total[lid][1] else "sinais das frases")) if L else ""
    # 2. trecho a trecho
    especiais = [p for p in P if p.get("papel") == "trecho"]
    linhas, cenas_ant = [], []
    for i, x in enumerate(fr):
        n, f = x["n"], x["f"]
        cand = []
        for p in especiais:
            s, m = nota(p, n, f)
            if s > 0: cand.append((s, p, m))
        cand.sort(key=lambda z: -z[0])
        sl, ml = nota(L, n, f) if L else (0, [])
        if cand and cand[0][0] >= 4 and cand[0][0] > sl + 1:
            s, p, m = cand[0]
            cena, pq = escolher_cena(p, n, f, i, len(fr), [])
            esc = {"preset": p["id"], "cena": cena, "motivo": "; ".join(m[:3]) + (f" ({pq})" if pq and cena else "")}
        else:
            cena, pq = escolher_cena(L, n, f, i, len(fr), cenas_ant) if L else ("", "")
            cenas_ant.append(cena)
            esc = {"preset": lid, "cena": cena, "motivo": pq or ("; ".join(ml[:2]) if ml else "linguagem do vídeo")}
        alts = [{"preset": p["id"], "nota": s} for s, p, _ in cand[:3] if p["id"] != esc["preset"]]
        linhas.append({"i": i + 1, "ini": x["ini"], "fim": x["fim"], "texto": x["texto"], **esc, "alternativas": alts})
    return {"formato": ctx["formato"], "apresentador": ctx.get("apresentador"), "linguagem": lid, "linguagem_motivo": por_que_l,
            "linguagem_alternativas": [{"preset": k, "nota": total[k][0]} for k in ordem[:4] if k != lid],
            "trechos": linhas}


def mostrar(s):
    C = {p["id"]: p for p in catalogo()["presets"]}
    L = C.get(s["linguagem"], {})
    print(f"Linguagem do vídeo: **{L.get('nome', s['linguagem'])}** ({s['linguagem_motivo']}). {L.get('resumo', '')}")
    if s["linguagem_alternativas"]:
        print("Outras que combinam: " + ", ".join(C[a["preset"]]["nome"] for a in s["linguagem_alternativas"][:3]))
    print()
    print("| # | Tempo | Frase | Preset | Cena | Por quê |")
    print("|---|---|---|---|---|---|")
    for t in s["trechos"]:
        tp = f"{t['ini']:.1f}-{t['fim']:.1f} s" if t["ini"] is not None else ""
        fr = t["texto"] if len(t["texto"]) <= 60 else t["texto"][:57] + "..."
        print(f"| {t['i']} | {tp} | {fr} | {C.get(t['preset'], {}).get('nome', t['preset'])} | {t['cena']} | {t['motivo']} |")


def pedido(txt, ctx):
    C = catalogo(); n = norm(txt); rotas = []
    for r in C["pedidos"]:
        h = [k for k in r["sinais"] if tem(n, k)]
        if h:
            extra = r.get("extra") or {}
            if extra and any(tem(n, k) for k in extra.get("se", [])):
                r = dict(r, **{k: v for k, v in extra.items() if k != "se"})
            rotas.append((len(h), r, h))
    rotas.sort(key=lambda z: -z[0])
    for _, r, h in rotas:
        alvo = r["rota"]; guia = r.get("guia") or (f"presets/{alvo.split(':')[1]}/PRESET.md" if alvo.startswith("preset:") else "")
        print(f"- {alvo}" + (f" + preset {r['preset']}" if r.get("preset") else "") + f"  (sinal: {', '.join(h[:3])}; guia: {guia})")
    nf, f = sinais(txt, ctx)
    ps = sorted(((nota(p, nf, f)[0] + min(6, 1.5 * sum(tem(nf, k) for k in p.get("nichos", []))), p) for p in C["presets"] if ok_contexto(p, ctx)), key=lambda z: -z[0])
    boas = [p for s, p in ps[:3] if s > 0]
    if not rotas:
        print("- sem rota fixa: fluxo normal do Gab (roteiro > voz > ...); escolher o preset por trecho com `sugerir` depois do roteiro")
    if boas and not any(r["rota"].startswith("preset:") for _, r, _ in rotas):
        print("Presets que combinam com o pedido: " + ", ".join(f"{p['nome']} ({p['resumo']})" for p in boas))


def listar(cat=None):
    C = catalogo()
    for k, nome in C["categorias"].items():
        if cat and cat != k: continue
        print(f"\n## {nome}")
        for p in C["presets"]:
            if p["categoria"] == k:
                print(f"- **{p['nome']}** (`{p['id']}`, {p['papel']}, {'/'.join(p['formato'])}, apresentador {p['apresentador']}): {p['resumo']} Quando: {p['quando']}.")


def conferir():
    C = catalogo(); ids = {p["id"] for p in C["presets"]}; ruim = 0
    pastas = sorted(d for d in os.listdir(os.path.join(SKILL, "presets")) if os.path.isdir(os.path.join(SKILL, "presets", d)) and os.path.exists(os.path.join(SKILL, "presets", d, "PRESET.md")))
    for d in pastas:
        if d not in ids and d not in C.get("fora_do_seletor", []):
            print(f"! {d}: falta a entrada em presets/catalogo.json"); ruim += 1
    for p in C["presets"]:
        if p["id"] not in pastas: print(f"! {p['id']}: está no catálogo mas não existe presets/{p['id']}/PRESET.md"); ruim += 1
        elif not p["gif"]: print(f"· {p['id']}: sem GIF de prévia (o seletor mostra 'sem prévia ainda')")
    print("catálogo ok" if not ruim else f"{ruim} problema(s)"); return ruim


def main(a):
    if not a:
        raise SystemExit(__doc__)
    def arg(k, d=None):
        return a[a.index(k) + 1] if k in a else d
    ctx = {"formato": arg("--formato", "vertical"), "apresentador": arg("--apresentador"), "falantes": int(arg("--falantes", 1)),
           "marca": [m for m in (arg("--marca") or "").split(",") if m], "cliente": arg("--cliente"), "forcar": arg("--forcar")}
    if a[0] == "pedido":
        pedido(" ".join(x for x in a[1:2]), ctx)
    elif a[0] == "sugerir":
        s = sugerir(a[1], ctx); mostrar(s)
        saida = arg("--saida")
        if saida:
            json.dump(s, open(saida, "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(f"\nsalvo: {saida}  (seletor: python3 {os.path.join(SKILL, 'scripts', 'seletor.py')} {saida})")
    elif a[0] == "conferir":
        sys.exit(1 if conferir() else 0)
    elif a[0] == "listar":
        listar(arg("--categoria"))
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
