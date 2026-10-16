"""Carrossel de MOTION para o Instagram (estilo PAINEL): cada slide é um vídeo 1080x1350 de ~6,5 s que se monta
sozinho e para no quadro final. Sai MP4 (posta direto no carrossel) e PNG do quadro final de cada slide.

  python3 gerar.py plano.json <pasta_saida> [--so 3] [--sem-render]

plano.json:
{ "marca": {"nome": "ExStart", "logo_html": "<i>Ex</i>Start", "logo_img": "logo.png" (opcional), "handle": "@start.ex",
            "cores": {"dest": "#E2683C", "app1": "#4A2117", "app2": "#2A130D", "fundo": "#ECEAE6"}},
  "dur": 6.5,
  "slides": [
    {"tipo": "capa", "titulo": ["6 agentes de IA", "pra sua empresa"], "texto": "Cada um faz **um trabalho inteiro**.",
     "itens": [{"icone": "chat", "titulo": "Atendimento", "sub": "responde o cliente"}, ...]},
    {"tipo": "app", "titulo": ["Agente de", "atendimento"], "texto": "Lê cada mensagem e **decide sozinho**.",
     "app": {"usuario": "Tiago", "saudacao": "Boa tarde, Tiago", "metrica": "Tratadas hoje", "valor": 147, "total": 160,
             "selo": "92% sem humano", "blocos": [{"icone": "check", "valor": 128, "rotulo": "respondidas"}, ...3],
             "lista": [{"sigla": "MS", "cor": "#6c5ce7", "nome": "Mariana Souza", "texto": "Tem a bomba?", "tag": "Respondida",
                        "tag_tipo": "ok|neu|al", "feito": true}, ...4]},
     "entra": [{"icone": "chat", "titulo": "Mensagem do cliente", "sub": "WhatsApp, e-mail"}, ...3],
     "decide": [{"icone": "ok2", "titulo": "Responde sozinho", "valor": 128}, ...3],
     "regras": [["dúvida de produto", "responde"], ...3]},
    {"tipo": "conexao", "titulo": ["Como eles", "se conectam"], "texto": "...",
     "conexao": {"hub": "Agente de Gestão", "hub_sub": "junta tudo", "nos": [{"icone": "funil", "titulo": "Leads", "sub": "quem chegou"}, ...até 7],
                 "aviso": {"de": "Agente ExStart", "sub": "único aviso do dia", "texto": "Vendas **R$ 31,2 mil**..."}, "mao": "você só lê isso aqui."}},
    {"tipo": "cta", "titulo": ["Quer os 6", "na sua empresa?"], "arrasta": false,
     "cta": {"palavra": "AGENTES", "isca": {"selo": "KIT GRÁTIS", "titulo": "Os 6 agentes **prontos pra montar**",
             "itens": [["Atendimento", "chat"], ...], "rodape": "mapa + prompts · PDF"},
             "mao": ["te mando no direct", "o mapa + o prompt", "de cada um"]}}]}
Contador ("01 / 06") é automático nos slides "app" (ou "contador" no slide). Ícones: os do preset sketch + historico,
caixa, mao, inbox, ok2, alerta, recibo, funil.
"""
import json, os, shutil, subprocess, sys

AQUI = os.path.dirname(os.path.abspath(__file__)); RAIZ = os.path.dirname(os.path.dirname(AQUI))
FONTES = [("Poppins", f"Poppins-{p}.ttf") for p in ("Regular", "Medium", "SemiBold", "Bold", "ExtraBold", "Black")] + \
         [("PatrickHand", "PatrickHand-Regular.ttf"), ("PlayfairDisplay", "PlayfairDisplay-SemiBoldItalic.ttf")]


def projeto(slide, marca, pasta, n):
    proj = os.path.join(pasta, "_proj", f"{n:02d}"); os.makedirs(os.path.join(proj, "fonts"), exist_ok=True)
    for fam, f in FONTES:
        shutil.copy(os.path.join(RAIZ, "assets", "fontes", fam, f), os.path.join(proj, "fonts"))
    for f in ("carrossel.js", "icones.js"):
        shutil.copy(os.path.join(AQUI, "kit", f), proj)
    m = dict(marca)
    if m.get("logo_img"):
        shutil.copy(m["logo_img"], os.path.join(proj, "logo" + os.path.splitext(m["logo_img"])[1])); m["logo_img"] = "logo" + os.path.splitext(m["logo_img"])[1]
    open(os.path.join(proj, "slide.js"), "w").write("window.SLIDE = " + json.dumps(dict(slide, marca=m), ensure_ascii=False) + ";\n")
    open(os.path.join(proj, "index.html"), "w").write(open(os.path.join(AQUI, "kit", "index.html")).read().replace("%DUR%", str(slide["dur"])))
    return proj


def gerar(plano, pasta, so=None, render=True):
    os.makedirs(pasta, exist_ok=True); base = os.path.dirname(os.path.abspath(plano["_arq"]))
    marca = dict(plano["marca"])
    if marca.get("logo_img") and not os.path.isabs(marca["logo_img"]):
        marca["logo_img"] = os.path.join(base, marca["logo_img"])
    apps = [i for i, s in enumerate(plano["slides"]) if s["tipo"] == "app"]
    saidas = []
    for i, s in enumerate(plano["slides"]):
        n = i + 1
        if so and n not in so:
            continue
        s = dict(s); s.setdefault("dur", plano.get("dur", 6.5))
        if s["tipo"] == "app" and "contador" not in s:
            s["contador"] = f"{apps.index(i) + 1:02d} / {len(apps):02d}"
        if s["tipo"] == "cta":
            s.setdefault("arrasta", False)
        proj = projeto(s, marca, pasta, n)
        if not render:
            continue
        mp4 = os.path.join(pasta, f"{n:02d}.mp4"); png = os.path.join(pasta, f"{n:02d}.png")
        subprocess.run(["npx", "--yes", "hyperframes", "render", proj, "--format", "mp4", "--fps", "30", "-q", "high", "-o", mp4], check=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-sseof", "-0.05", "-i", mp4, "-frames:v", "1", "-update", "1", png], check=True)
        saidas.append(mp4); print(f"slide {n:02d} ({s['tipo']}): {mp4}")
    return saidas


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 2:
        raise SystemExit(__doc__)
    p = json.load(open(a[0], encoding="utf-8")); p["_arq"] = os.path.abspath(a[0])
    so = [int(x) for x in a[a.index("--so") + 1].split(",")] if "--so" in a else None
    gerar(p, os.path.abspath(a[1]), so, "--sem-render" not in a)
