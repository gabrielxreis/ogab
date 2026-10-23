#!/usr/bin/env python3
"""/ogab menu: painel local (PT/EN) para a pessoa escolher o que vai no vídeo antes de criar, ou deixar no automático.

  python3 menu.py [--pasta <pasta do vídeo>] [--cliente <empresa>] [--pedido "texto"] [--roteiro roteiro.txt]
                  [--formato vertical|horizontal] [--editor davinci|premiere|capcut|finalcut|nenhum] [--lingua pt|en] [--porta 0] [--sem-abrir] [--sem-voltar] [--timeout 1800]

- Cada opção tem um check: marcou, entra no vídeo. Grupo sem nada marcado = o Gab escolhe aquele grupo.
- "Automático": o Gab escolhe TUDO pelo que já sabe da pessoa e da marca (estilo.md do cliente, memória da marca,
  escolher_preset.py com o pedido/roteiro). Com --pedido/--roteiro, as sugestões já aparecem marcadas como "sugerido".
- As prévias ficam em loop: GIF de cada preset (presets/catalogo.json) e animação própria nas opções sem GIF.
- Ao confirmar grava <pasta>/menu_escolha.json (ou ./menu_escolha.json) e termina; rodar em segundo plano.
Identidade visual da /ogab (logo da Apresentação ogab, 22/10/2026): fundo #070B08/#16201A, verde #2BFF88,
degradê #9CFFC9 > #14E070, Inter Tight 800 (assets/fontes/InterTight, OFL). Só 127.0.0.1.
"""
import json, os, re, socket, subprocess, sys, threading, time, webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote

AQUI = os.path.dirname(os.path.abspath(__file__)); SKILL = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
from escolher_preset import catalogo  # noqa: E402

# ícones das plataformas: Simple Icons (CC0, simpleicons.org); megafone de Anúncios desenhado aqui
ICONES = {"instagram": "M7.0301.084c-1.2768.0602-2.1487.264-2.911.5634-.7888.3075-1.4575.72-2.1228 1.3877-.6652.6677-1.075 1.3368-1.3802 2.127-.2954.7638-.4956 1.6365-.552 2.914-.0564 1.2775-.0689 1.6882-.0626 4.947.0062 3.2586.0206 3.6671.0825 4.9473.061 1.2765.264 2.1482.5635 2.9107.308.7889.72 1.4573 1.388 2.1228.6679.6655 1.3365 1.0743 2.1285 1.38.7632.295 1.6361.4961 2.9134.552 1.2773.056 1.6884.069 4.9462.0627 3.2578-.0062 3.668-.0207 4.9478-.0814 1.28-.0607 2.147-.2652 2.9098-.5633.7889-.3086 1.4578-.72 2.1228-1.3881.665-.6682 1.0745-1.3378 1.3795-2.1284.2957-.7632.4966-1.636.552-2.9124.056-1.2809.0692-1.6898.063-4.948-.0063-3.2583-.021-3.6668-.0817-4.9465-.0607-1.2797-.264-2.1487-.5633-2.9117-.3084-.7889-.72-1.4568-1.3876-2.1228C21.2982 1.33 20.628.9208 19.8378.6165 19.074.321 18.2017.1197 16.9244.0645 15.6471.0093 15.236-.005 11.977.0014 8.718.0076 8.31.0215 7.0301.0839m.1402 21.6932c-1.17-.0509-1.8053-.2453-2.2287-.408-.5606-.216-.96-.4771-1.3819-.895-.422-.4178-.6811-.8186-.9-1.378-.1644-.4234-.3624-1.058-.4171-2.228-.0595-1.2645-.072-1.6442-.079-4.848-.007-3.2037.0053-3.583.0607-4.848.05-1.169.2456-1.805.408-2.2282.216-.5613.4762-.96.895-1.3816.4188-.4217.8184-.6814 1.3783-.9003.423-.1651 1.0575-.3614 2.227-.4171 1.2655-.06 1.6447-.072 4.848-.079 3.2033-.007 3.5835.005 4.8495.0608 1.169.0508 1.8053.2445 2.228.408.5608.216.96.4754 1.3816.895.4217.4194.6816.8176.9005 1.3787.1653.4217.3617 1.056.4169 2.2263.0602 1.2655.0739 1.645.0796 4.848.0058 3.203-.0055 3.5834-.061 4.848-.051 1.17-.245 1.8055-.408 2.2294-.216.5604-.4763.96-.8954 1.3814-.419.4215-.8181.6811-1.3783.9-.4224.1649-1.0577.3617-2.2262.4174-1.2656.0595-1.6448.072-4.8493.079-3.2045.007-3.5825-.006-4.848-.0608M16.953 5.5864A1.44 1.44 0 1 0 18.39 4.144a1.44 1.44 0 0 0-1.437 1.4424M5.8385 12.012c.0067 3.4032 2.7706 6.1557 6.173 6.1493 3.4026-.0065 6.157-2.7701 6.1506-6.1733-.0065-3.4032-2.771-6.1565-6.174-6.1498-3.403.0067-6.156 2.771-6.1496 6.1738M8 12.0077a4 4 0 1 1 4.008 3.9921A3.9996 3.9996 0 0 1 8 12.0077", "tiktok": "M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.93-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.19-3.44-3.37-3.65-5.71-.02-.5-.03-1-.01-1.49.18-1.9 1.12-3.72 2.58-4.96 1.66-1.44 3.98-2.13 6.15-1.72.02 1.48-.04 2.96-.04 4.44-.99-.32-2.15-.23-3.02.37-.63.41-1.11 1.04-1.36 1.75-.21.51-.15 1.07-.14 1.61.24 1.64 1.82 3.02 3.5 2.87 1.12-.01 2.19-.66 2.77-1.61.19-.33.4-.67.41-1.06.1-1.79.06-3.57.07-5.36.01-4.03-.01-8.05.02-12.07z", "youtube": "M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z", "facebook": "M9.101 23.691v-7.98H6.627v-3.667h2.474v-1.58c0-4.085 1.848-5.978 5.858-5.978.401 0 .955.042 1.468.103a8.68 8.68 0 0 1 1.141.195v3.325a8.623 8.623 0 0 0-.653-.036 26.805 26.805 0 0 0-.733-.009c-.707 0-1.259.096-1.675.309a1.686 1.686 0 0 0-.679.622c-.258.42-.374.995-.374 1.752v1.297h3.919l-.386 2.103-.287 1.564h-3.246v8.245C19.396 23.238 24 18.179 24 12.044c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.628 3.874 10.35 9.101 11.647Z", "linkedin": "M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z", "ads": "M3 10v4a1 1 0 0 0 1 1h2l4 4V5L6 9H4a1 1 0 0 0-1 1zm10.5-4.5v13l7.5 3V2.5l-7.5 3z"}
TIPOS = {".gif": "image/gif", ".png": "image/png", ".jpg": "image/jpeg", ".webp": "image/webp", ".woff2": "font/woff2"}
FORA_DO_MENU = {"lottie"}   # não é vídeo

PRESET_EN = {
    "painel": "Finance/data app: navy, 3D app cards with rolling numbers, a chart drawing itself, camera diving in.",
    "launch": "Premium Apple-style launch film: black, one idea per scene, real product screens in 3D glass.",
    "vitrine": "Clean luxury interface: every line becomes a piece of UI (converter, profile, card, window, pill).",
    "kinetic": "Aggressive kinetic type: giant words swapping on the beat of the voice, red box, glitch, whip.",
    "vector-motion": "Each line becomes a simple black and white visual metaphor, the hero glowing against the rest.",
    "point-cloud": "Thousands of dots draw real photos, 3D text and shapes (galaxy, sphere) and flow between scenes.",
    "gravura": "A copper engraving plate etching itself, title cut letter by letter, watercolour only where it matters.",
    "sketch": "Everything becomes a marker sketch drawing itself: A to B header, app grid, tool to result, checklist.",
    "tela-dividida": "Motion panel on top, presenter below, a caption tag on the seam.",
    "serif-azul": "Editorial: sans captions with the keyword in blue serif italic, steps 1-2-3 and light paper scenes.",
    "lume": "Keyword glowing letter by letter behind the hand, top-down desk scenes, warm light leak.",
    "glass": "YouTube 16:9: dark glass with aurora, metallic title, real screenshots with the number highlighted.",
    "destaque": "Word-by-word captions with a big yellow or serif keyword and a highlighter pill.",
    "palco": "The spoken word appears giant BEHIND the person (automatic cutout).",
    "orbita": "Glass cards around the person: checklist ticking on the line, 'ready 100%' bar, comment typing.",
    "lente": "Quick zoom into the face on the strong word.",
    "grafico": "Bars, line, donut or comparison with the exact approved value and the source on screen.",
    "marco": "Thousands of dots come together and draw the milestone ('10K', '1 million', '+10 years').",
    "ranking": "S-D tier list or top 3 podium building as you talk; each item lands and stays.",
    "respostas": "Top strip with '?' that turn into icon + word the moment each answer is said.",
    "comentario": "A follower's comment card with @, likes and the keyword highlighted.",
    "cartoes": "Proof cards (numbers, testimonials, screenshots) stacking in depth and fanning out.",
    "podcast": "Two people in split screen, karaoke captions in the speaker's colour, below the chin.",
    "logo-reveal": "5-8 s brand opener: the logo born from the dark in light, lines or dots.",
}
CAT_EN = {"dados": "Numbers, charts and milestones", "produto": "Product, app and launch", "apresentador": "Person talking to camera",
          "ideia": "Punchline, idea and story", "lista": "List, ranking and step by step", "social": "Comment, social proof and interview",
          "marca": "Opener, brand and web delivery"}


def it(id, pt, en, dpt, den, anim=None, gif=None, extra=None):
    d = {"id": id, "nome": {"pt": pt, "en": en}, "desc": {"pt": dpt, "en": den}, "anim": anim, "gif": gif}
    if extra: d.update(extra)
    return d


def lettering_do_editor(editor, cfg):
    """(nome do editor, [(id_template, nome visível)]) com os títulos que o editor da pessoa tem."""
    if editor == "premiere":
        d = os.path.join(SKILL, "premiere", "assets", "mogrt")
        nomes = sorted(os.path.splitext(f)[0] for f in os.listdir(d) if f.endswith(".mogrt")) if os.path.isdir(d) else []
        return "Premiere", [(n, n.replace("-", " ").capitalize()) for n in nomes]
    if editor == "capcut":
        try:
            c = json.load(open(os.path.join(SKILL, "capcut", "catalogo.json"), encoding="utf-8"))["texto_entrada"]
        except Exception:
            c = {}
        return "CapCut", [(k, v.get("nome", k)) for k, v in c.items() if not v.get("vip")]
    if editor == "finalcut":
        return "Final Cut", [("Basic Title", "Basic Title")]
    if editor == "nenhum":
        return "Gab", [("texto", "Texto simples")]
    lt = (cfg.get("lettering") or {}).get("templates_disponiveis") or []
    return "DaVinci", [(n, n.replace("@gabrielxreis_ ", "")) for n in lt]


def fmt(id, plat, pt, en, prop, res, dpt, den):
    return it(id, pt, en, f"{prop} · {res} · {dpt}", f"{prop} · {res} · {den}", f"fmt {prop}", extra={"aba": plat, "proporcao": prop, "resolucao": res})


def presets_do_usuario(C):
    """Presets que a pessoa criou (meus_presets.py): entram no passo de estilo só depois de enviados COMPLETOS à
    comunidade (no dono, sempre) e com prévia. id 'local:<id>' = preset em presets/<id>/ (ou biblioteca_motions_local/)."""
    try:
        import meus_presets
        locais = meus_presets.listar()
    except Exception:
        return []
    r = []
    for p in locais:
        if not p.get("no_menu"):
            continue
        cat = p.get("categoria") or "ideia"
        r.append(it("local:" + p["id"], p["nome"], p["nome"], p.get("resumo") or "", p.get("resumo") or "",
                    gif=(p["pasta"] + "/" + p["gif"]) if p.get("gif") else None,
                    extra={"aba": cat, "cat": cat, "catn": {"pt": C["categorias"].get(cat, ""), "en": CAT_EN.get(cat, "")},
                           "formato": p.get("formato") or [], "seu": True, "pasta": p["pasta"]}))
    return r


def estilos_prontos():
    """{grupo: [itens]} dos ESTILOS (presets/estilos/<grupo>/<id>/) que já têm exemplo.gif: o menu mostra só o que funciona."""
    import glob
    r = {}
    for j in sorted(glob.glob(os.path.join(SKILL, "presets", "estilos", "*", "*", "estilo.json"))):
        try:
            m = json.load(open(j, encoding="utf-8"))
        except Exception:
            continue
        pasta = os.path.dirname(j)
        if not os.path.exists(os.path.join(pasta, "exemplo.gif")) or m.get("id", "").startswith("_"):
            continue
        rel = os.path.relpath(pasta, SKILL).replace(os.sep, "/")
        r.setdefault(m.get("grupo", ""), []).append(it(m["id"], m["nome"]["pt"], m["nome"].get("en", m["nome"]["pt"]),
            m["desc"]["pt"], m["desc"].get("en", m["desc"]["pt"]), gif=rel + "/exemplo.gif",
            extra={"estilo": True, "aba": m.get("grupo", "")}))
    return r


def grupos(formato, lettering, editor_nome="DaVinci"):
    """lettering = [(id_template, nome visível)] do editor da pessoa (lettering_do_editor)."""
    C = catalogo()
    presets = [p for p in C["presets"] if p["id"] not in FORA_DO_MENU]
    est = [it(p["id"], p["nome"], p["nome"].replace(" (CENA)", " (SCENE)"), p["resumo"], PRESET_EN.get(p["id"], p["resumo"]),
              gif=p.get("gif") or None, extra={"aba": p["categoria"], "cat": p["categoria"], "catn": {"pt": C["categorias"].get(p["categoria"], ""),
              "en": CAT_EN.get(p["categoria"], "")}, "formato": p.get("formato") or []}) for p in presets]
    est += presets_do_usuario(C)
    EST = estilos_prontos()
    est += EST.get("batida", []) + EST.get("broll", [])   # batidas e b-roll animado: abas no passo de estilo dos motions
    sem = lambda pt, en: it("sem", pt, en, "", "", "none")
    def anim_let(n):
        n = n.lower()
        for k, a in (("palavra", "let-word"), ("blur up", "let-blurup"), ("blur", "let-blur"), ("acima", "let-up"), ("abaixo", "let-down"),
                     ("direita", "let-right"), ("esquerda", "let-left"), ("brilho", "let-glow"), ("flick", "let-flick"), ("corte", "let-cut"),
                     ("cinematic", "let-cine"), ("gira", "let-spin"), ("zoom", "let-zoom"), ("sublinh", "let-under"), ("gold", "let-gold"),
                     ("silver", "let-silver"), ("slide", "let-right"), ("surgir", "let-blurup"), ("reveal", "let-cut"), ("destac", "let-hl"),
                     ("moderno", "let-up"), ("typewriter", "let-word"), ("fade", "let-blur"), ("up", "let-up"), ("down", "let-down"),
                     ("left", "let-left"), ("right", "let-right"), ("spin", "let-spin"), ("rotat", "let-spin"), ("glow", "let-glow"),
                     ("shine", "let-glow"), ("flash", "let-flick"), ("zoom", "let-zoom"), ("scale", "let-zoom"), ("wipe", "let-cut"),
                     ("lista", "let-word"), ("contador", "let-zoom"), ("frase", "let-up")):
            if k in n: return a + (" fast" if "rápido" in n else "")
        return "let-blurup"
    let = [it("t%02d" % i, nome, nome, f"Título do {editor_nome}, editável no próprio editor.", f"{editor_nome} title, editable in the editor itself.",
              anim=anim_let(nome), extra={"template": tid}) for i, (tid, nome) in enumerate(lettering, 1)]
    G = [
        {"id": "formato", "letra": "F", "unico": False, "nome": {"pt": "Formato", "en": "Format"},
         "sub": {"pt": "Escolha a plataforma e marque os formatos. Pode marcar vários: o vídeo sai em cada um.",
                 "en": "Pick the platform and tick the formats. You can tick several: the video is exported in each."},
         "abas": [{"id": "instagram", "nome": {"pt": "Instagram", "en": "Instagram"}}, {"id": "tiktok", "nome": {"pt": "TikTok", "en": "TikTok"}},
                  {"id": "youtube", "nome": {"pt": "YouTube", "en": "YouTube"}}, {"id": "facebook", "nome": {"pt": "Facebook", "en": "Facebook"}},
                  {"id": "linkedin", "nome": {"pt": "LinkedIn", "en": "LinkedIn"}}, {"id": "ads", "nome": {"pt": "Anúncios", "en": "Ads"}}],
         "itens": [
            fmt("ig_reels", "instagram", "Reels", "Reels", "9:16", "1080x1920", "Vertical em tela cheia, até 3 min.", "Full-screen vertical, up to 3 min."),
            fmt("ig_feed45", "instagram", "Feed vertical", "Vertical feed", "4:5", "1080x1350", "Ocupa mais tela no feed.", "Takes more of the feed."),
            fmt("ig_feed11", "instagram", "Feed quadrado", "Square feed", "1:1", "1080x1080", "Clássico do feed.", "Classic feed post."),
            fmt("ig_stories", "instagram", "Stories", "Stories", "9:16", "1080x1920", "Até 60 s por story, cortado em partes.", "Up to 60 s per story, split in parts."),
            fmt("tt_video", "tiktok", "Vídeo TikTok", "TikTok video", "9:16", "1080x1920", "Vertical, legenda fora da área da interface.", "Vertical, captions clear of the app UI."),
            fmt("yt_video", "youtube", "Vídeo do YouTube", "YouTube video", "16:9", "1920x1080", "Horizontal, vídeo longo (também em 4K).", "Horizontal, long video (4K too)."),
            fmt("yt_shorts", "youtube", "Shorts", "Shorts", "9:16", "1080x1920", "Vertical, até 3 min.", "Vertical, up to 3 min."),
            fmt("fb_reels", "facebook", "Reels do Facebook", "Facebook Reels", "9:16", "1080x1920", "Vertical em tela cheia.", "Full-screen vertical."),
            fmt("fb_feed", "facebook", "Feed do Facebook", "Facebook feed", "4:5", "1080x1350", "Vertical no feed.", "Vertical in the feed."),
            fmt("fb_horizontal", "facebook", "Vídeo horizontal", "Landscape video", "16:9", "1920x1080", "Vídeo longo na página.", "Long video on the page."),
            fmt("li_quadrado", "linkedin", "Feed quadrado", "Square feed", "1:1", "1080x1080", "O que mais aparece no feed.", "Shows best in the feed."),
            fmt("li_vertical", "linkedin", "Vertical", "Vertical", "4:5", "1080x1350", "Vertical no feed.", "Vertical in the feed."),
            fmt("li_horizontal", "linkedin", "Horizontal", "Landscape", "16:9", "1920x1080", "Palestra, entrevista, institucional.", "Talks, interviews, corporate."),
            fmt("ads_meta_vertical", "ads", "Meta Ads: Reels e Stories", "Meta Ads: Reels and Stories", "9:16", "1080x1920", "15, 30 ou 60 s, com variações de gancho.", "15, 30 or 60 s, with hook variations."),
            fmt("ads_meta_feed", "ads", "Meta Ads: Feed", "Meta Ads: Feed", "4:5", "1080x1350", "Feed do Instagram e do Facebook.", "Instagram and Facebook feed."),
            fmt("ads_tiktok", "ads", "TikTok Ads", "TikTok Ads", "9:16", "1080x1920", "Nativo, cara de conteúdo e não de anúncio.", "Native, looks like content, not an ad."),
            fmt("ads_yt_instream", "ads", "YouTube Ads: in-stream", "YouTube Ads: in-stream", "16:9", "1920x1080", "Antes do vídeo, com gancho nos 5 s de pular.", "Before videos, hook inside the 5 s skip."),
            fmt("ads_yt_bumper", "ads", "YouTube Ads: bumper 6 s", "YouTube Ads: 6 s bumper", "16:9", "1920x1080", "6 s sem pular: uma ideia só.", "6 s, non-skippable: one idea."),
            fmt("ads_yt_shorts", "ads", "YouTube Ads: Shorts", "YouTube Ads: Shorts", "9:16", "1080x1920", "Entre os Shorts.", "Between Shorts."),
            fmt("ads_linkedin", "ads", "LinkedIn Ads", "LinkedIn Ads", "1:1", "1080x1080", "Também sai em 16:9 e 9:16.", "Also in 16:9 and 9:16."),
         ]},
        {"id": "motions", "letra": "M", "unico": True, "nome": {"pt": "Quantidade de motion", "en": "Amount of motion"},
         "sub": {"pt": "Motion = animação em HyperFrames. Lettering simples não entra aqui.", "en": "Motion = HyperFrames animation. Plain lettering is not counted here."}, "itens": [
            it("poucos", "Poucos", "A few", "Só nos números, dados e no CTA.", "Only numbers, data and the CTA.", "dens d1"),
            it("equilibrado", "Equilibrado", "Balanced", "Nos momentos que pedem imagem, com respiro de pessoa falando.", "Where an image helps, with talking breathers.", "dens d2"),
            it("muitos", "Muitos", "Lots", "Uma ideia, uma imagem: quase o vídeo todo.", "One idea, one image: almost the whole video.", "dens d3"),
            it("sem", "Sem motion", "No motion", "Só a pessoa, legenda e lettering.", "Just the person, captions and lettering.", "none")]},
        {"id": "estilo", "letra": "E", "unico": False, "max": 6, "nome": {"pt": "Estilo dos motions (presets)", "en": "Motion style (presets)"},
         "abas": [{"id": "todos", "nome": {"pt": "Todos", "en": "All"}}, {"id": "sugeridos", "nome": {"pt": "Sugeridos", "en": "Suggested"}}] + [x for x in (
                  {"id": "batida", "nome": {"pt": "Batidas visuais", "en": "Visual beats"}}, {"id": "broll", "nome": {"pt": "B-roll animado", "en": "Animated b-roll"}})
                  if EST.get(x["id"])] + [{"id": c, "nome": {"pt": C["categorias"][c], "en": CAT_EN.get(c, c)}}
                  for c in ("apresentador", "ideia", "lista", "dados", "produto", "social", "marca") if c in C["categorias"]],
         "sub": {"pt": "Como os motions vão parecer: presets, batidas visuais e b-roll animado. Eles se misturam trecho a trecho.", "en": "How the motion graphics will look: presets, visual beats and animated b-roll. They mix section by section."},
         "itens": est},
        *[g for g in (
            {"id": "gancho", "letra": "G", "unico": False, "max": 2, "nome": {"pt": "Gancho", "en": "Hook"},
             "sub": {"pt": "O que aparece nos primeiros 1 a 3 segundos para segurar quem está rolando.", "en": "What shows in the first 1 to 3 seconds to stop the scroll."},
             "itens": [sem("Sem gancho especial", "No special hook")] + EST.get("gancho", [])},
            {"id": "layout", "letra": "Q", "unico": False, "max": 3, "nome": {"pt": "Layout", "en": "Layout"},
             "sub": {"pt": "Como você e os gráficos dividem o quadro.", "en": "How you and the graphics share the frame."},
             "itens": [sem("Quadro normal", "Normal frame")] + EST.get("layout", [])},
            {"id": "prova", "letra": "P", "unico": False, "max": 4, "nome": {"pt": "Prova", "en": "Proof"},
             "sub": {"pt": "Como mostrar que é verdade: prints, números, posts, arquivo pessoal.", "en": "How to show it's real: screenshots, numbers, posts, personal archive."},
             "itens": [sem("Sem prova na tela", "No on-screen proof")] + EST.get("prova", [])},
            {"id": "efeitos", "letra": "Z", "unico": False, "max": 4, "nome": {"pt": "Efeitos", "en": "Effects"},
             "sub": {"pt": "Efeitos de destaque de cerca de 1 segundo, um por ideia, e movimentos de câmera e transições.", "en": "About one-second showpiece effects, one per idea, plus camera moves and transitions."},
             "abas": [x for x in ({"id": "efeito", "nome": {"pt": "Efeitos", "en": "Effects"}}, {"id": "ritmo", "nome": {"pt": "Câmera e transições", "en": "Camera and transitions"}}) if EST.get(x["id"])],
             "itens": [dict(sem("Sem efeitos", "No effects"), aba="efeito")] + EST.get("efeito", []) + EST.get("ritmo", [])},
        ) if len(g["itens"]) > 1],
        {"id": "legenda", "letra": "L", "unico": True, "nome": {"pt": "Legenda", "en": "Captions"},
         "sub": {"pt": "Como a fala aparece. Nunca em cima do rosto.", "en": "How the words show up. Never over the face."},
         "abas": [{"id": "editor", "nome": {"pt": f"No editor ({editor_nome})", "en": f"In the editor ({editor_nome})"}},
                  {"id": "animada", "nome": {"pt": "Animada (motion)", "en": "Animated (motion)"}}],
         "itens": [
            it("gab_usa", f"Padrão do {editor_nome}", f"{editor_nome} default", f"Legenda do próprio {editor_nome} no estilo do Gab: uma linha, do começo ao fim, editável na trilha de legenda.",
               f"{editor_nome}'s own subtitles in Gab's style: one line, start to end, editable on the subtitle track.", "cap-gab", extra={"aba": "editor"}),
            it("editor_padrao", f"Simples do {editor_nome}", f"Plain {editor_nome}", f"Legenda do {editor_nome} sem estilo, para você ajustar do seu jeito.",
               f"{editor_nome} subtitles with no style, for you to tweak your way.", "cap-plain", extra={"aba": "editor"}),
            it("sem", "Sem legenda", "No captions", "Quadro limpo, só títulos e gráficos.", "Clean frame, only titles and graphics.", "none", extra={"aba": "editor"}),
            it("destaque", "Destaque palavra por palavra", "Word-by-word highlight", "Palavra-chave grande amarela ou em serifa (render em motion).", "Big yellow or serif keyword (rendered as motion).", "cap-hl", extra={"aba": "animada"}),
            it("serif_azul", "Serif azul", "Blue serif", "Sans com a palavra-chave em serifada itálica azul.", "Sans with the keyword in blue serif italic.", "cap-serif", extra={"aba": "animada"}),
            it("lume", "Lume (duas camadas)", "Lume (two layers)", "Linha fina + palavra que brilha em amarelo.", "Thin line + a word that glows yellow.", "cap-lume", extra={"aba": "animada"}),
            it("podcast", "Cor por quem fala", "Colour per speaker", "Para podcast e entrevista com duas pessoas.", "For podcasts and two-person interviews.", "cap-pod", extra={"aba": "animada"})]
            + [dict(x, aba="animada") for x in EST.get("legenda", [])]},
        {"id": "lettering", "letra": "T", "unico": False, "nome": {"pt": f"Lettering (títulos do {editor_nome})", "en": f"Lettering ({editor_nome} titles)"},
         "sub": {"pt": f"Palavras-chave na tela com os títulos que o seu {editor_nome} tem. Marque os que pode usar.", "en": f"On-screen keywords with the titles your {editor_nome} has. Tick the ones it may use."},
         "itens": [it("sem", "Sem lettering", "No lettering", "Só legenda e motions.", "Only captions and motion.", "none")] + let},
        {"id": "takes", "letra": "B", "unico": True, "nome": {"pt": "Imagens de apoio (b-roll)", "en": "Supporting footage (b-roll)"},
         "sub": {"pt": "De onde vêm os takes que ilustram a fala.", "en": "Where the shots that illustrate the talk come from."}, "itens": [
            it("banco", "Banco de imagens", "Stock footage", "Envato, Artlist, Pexels, nas suas contas.", "Envato, Artlist, Pexels, on your accounts.", "takes t1"),
            it("ia", "Gerado por IA", "AI generated", "Imagem aprovada antes, depois vira vídeo (ilimitado).", "Image approved first, then animated (unlimited plan).", "takes t2"),
            it("misto", "Misto", "Mixed", "Banco no que existe de verdade, IA no conceitual.", "Stock for real things, AI for concepts.", "takes t3"),
            it("real", "Material real", "Real footage", "Vídeo público e acervo (fatos, pessoas, lugares reais).", "Public video and archives (real facts, people, places).", "takes t4"),
            it("sem", "Sem b-roll", "No b-roll", "Só a gravação.", "Only the recording.", "none")]},
        {"id": "musica", "letra": "A", "unico": True, "nome": {"pt": "Música", "en": "Music"},
         "sub": {"pt": "Escolha pelo sentimento que o vídeo deve passar (a música vem do seu Artlist ou Envato). Na dúvida, deixe no automático: o Gab escolhe pelo assunto.",
                 "en": "Pick the feeling the video should carry (the track comes from your Artlist or Envato). Not sure? Leave it on automatic: Gab picks by topic."}, "itens": [
            it("emotiva", "Emocionante", "Moving", "Boa para: história de vida, depoimento, conquista.", "Good for: life story, testimonial, achievement.", "bars m1", extra={"som": "emotiva"}),
            it("epica", "Épica, de cinema", "Epic, cinematic", "Boa para: grande revelação, trailer, momento histórico.", "Good for: big reveal, trailer, historic moment.", "bars m2", extra={"som": "epica"}),
            it("tensa", "Suspense, mistério", "Suspense, mystery", "Boa para: curiosidade, 'você sabia', caso misterioso.", "Good for: curiosity, 'did you know', mystery story.", "bars m3", extra={"som": "tensa"}),
            it("alegre", "Alegre, pra cima", "Happy, upbeat", "Boa para: dica rápida, novidade, bastidor leve.", "Good for: quick tip, news, light behind the scenes.", "bars m4", extra={"som": "alegre"}),
            it("energia", "Energia, motivação", "Energy, motivation", "Boa para: desafio, treino, chamada forte.", "Good for: challenge, workout, strong call to action.", "bars m7", extra={"som": "energia"}),
            it("corporativa", "Confiança, empresa", "Trust, corporate", "Boa para: serviço, institucional, apresentação da marca.", "Good for: services, corporate, brand intro.", "bars m5", extra={"som": "corporativa"}),
            it("calma", "Calma, reflexão", "Calm, reflective", "Boa para: explicação, tutorial, fé e reflexão.", "Good for: explainer, tutorial, faith and reflection.", "bars m6", extra={"som": "calma"}),
            it("delicada", "Delicada, afetiva", "Gentle, heartfelt", "Boa para: família, casamento, homenagem.", "Good for: family, wedding, tribute.", "bars m8", extra={"som": "delicada"}),
            it("sem", "Sem música", "No music", "Só a voz e os efeitos.", "Voice and effects only.", "none")]},
        {"id": "sfx", "letra": "S", "unico": True, "nome": {"pt": "Efeitos sonoros", "en": "Sound effects"},
         "sub": {"pt": "Som do que aparece na tela (gaveta, papel, avião), nunca mais alto que a voz.", "en": "The sound of what's on screen (drawer, paper, plane), never louder than the voice."}, "itens": [
            it("completo", "Desenho de som completo", "Full sound design", "Foley do que o motion mostra + ambiente.", "Foley for what the motion shows + ambience.", "sfx s1"),
            it("discreto", "Discreto", "Subtle", "Só nas entradas fortes.", "Only on strong entrances.", "sfx s2"),
            it("sem", "Sem efeitos", "No effects", "", "", "none")]},
        {"id": "ritmo", "letra": "R", "unico": True, "nome": {"pt": "Ritmo dos cortes", "en": "Cutting pace"},
         "sub": {"pt": "De quanto em quanto tempo a imagem muda.", "en": "How often the picture changes."}, "itens": [
            it("calmo", "Calmo", "Calm", "3 a 4 s por plano.", "3 to 4 s per shot.", "pace p1"),
            it("padrao", "Padrão (1,5 a 3 s)", "Default (1.5 to 3 s)", "Gancho com o take mais forte.", "Hook with the strongest shot.", "pace p2"),
            it("rapido", "Rápido", "Fast", "1 a 1,5 s, na batida da música.", "1 to 1.5 s, on the music beat.", "pace p3")]},
        {"id": "cor", "letra": "C", "unico": True, "nome": {"pt": "Cor", "en": "Colour"},
         "sub": {"pt": "Acabamento de cor em todos os takes.", "en": "Colour finish on every shot."}, "itens": [
            it("lut_gab", "LUT do Gab", "Gab's LUT", "O PowerGrade/LUT da instalação.", "The PowerGrade/LUT from the install.", "col c1"),
            it("natural", "Natural", "Natural", "Só correção, sem estilo.", "Correction only, no look.", "col c2"),
            it("pb", "Preto e branco", "Black and white", "Neutro, com contraste.", "Neutral, with contrast.", "col c3")] + EST.get("cor", [])},
        {"id": "extras", "letra": "X", "unico": False, "nome": {"pt": "Extras", "en": "Extras"},
         "sub": {"pt": "Marque o que quer a mais.", "en": "Tick what you want on top."}, "itens": [
            it("atras_pessoa", "Motion atrás da pessoa", "Motion behind the person", "Magic Mask no Fusion: texto e objetos passam atrás de você.", "Magic Mask in Fusion: text and objects go behind you.", "behind"),
            it("gancho_lettering", "Gancho com lettering", "Hook with lettering", "Título forte nos 3 primeiros segundos.", "A strong title in the first 3 seconds.", "let-cine"),
            it("variacoes_gancho", "Variações de gancho", "Hook variations", "3 a 5 ganchos para testar no anúncio.", "3 to 5 hooks to test in the ad.", "hooks"),
            it("capa", "Capa + legenda do post", "Cover + post caption", "Capa PNG e texto do post prontos.", "PNG cover and post text ready.", "cover"),
            it("logo_abertura", "Logo na abertura", "Logo opener", "Abertura de marca de 5-8 s.", "5-8 s brand opener.", "logo"),
            it("cta_site", "CTA com o site", "CTA with website", "Chamada final com o site da marca.", "Final call with the brand website.", "cta"),
         ]},
    ]
    if formato == "horizontal":
        for g in G:
            if g["id"] == "estilo":
                g["itens"] = [x for x in g["itens"] if "horizontal" in (x.get("formato") or ["vertical", "horizontal"])]
    return G


def _limpa(l):
    l = re.sub(r"[*`_]", "", l).strip().lstrip("-• ").strip()
    l = re.sub(r"\([^)]{30,}\)", "", l)                 # parênteses longos (ids, caminhos, detalhes técnicos)
    l = re.sub(r"\b[\w-]*\d[\w-]{12,}\b", "", l)          # ids e hashes
    l = re.sub(r"\s{2,}", " ", l).strip(" ;,.")
    return (l[:105] + "…") if len(l) > 106 else l


def ja_sabe(cliente):
    """O que o Gab já sabe da marca, em poucas linhas limpas: preferências do estilo.md + últimos pedidos da memória."""
    if not cliente:
        return []
    linhas = []
    est = os.path.join(SKILL, "clientes", cliente, "estilo.md")
    if os.path.exists(est):
        for l in open(est, encoding="utf-8", errors="ignore"):
            if l.strip().startswith(("-", "*")) and len(l.strip()) > 6:
                linhas.append(_limpa(l))
            if len(linhas) >= 4: break
    try:
        cfg = json.load(open(os.path.join(SKILL, "config.json"), encoding="utf-8"))
        base = os.path.expanduser(cfg.get("pasta_saida", ""))
        for nome in os.listdir(base) if os.path.isdir(base) else []:
            if nome.lower().replace(" ", "") == cliente.lower().replace(" ", ""):
                mem = os.path.join(base, nome, nome + ".md")
                if os.path.exists(mem):
                    ped = [l for l in open(mem, encoding="utf-8", errors="ignore") if l.strip().startswith(("-", "*")) and "pedido" in l.lower()]
                    linhas += [_limpa(x) for x in ped[-2:]]
    except Exception:
        pass
    return [l for l in linhas if l][:6]


def sugestoes(pedido, roteiro, formato, cliente, pasta):
    """Presets que o escolher_preset.py sugere (aparecem com o selo 'sugerido')."""
    sug = set()
    try:
        if roteiro and os.path.exists(roteiro):
            out = os.path.join(pasta or os.getcwd(), ".menu_sugestao.json")
            cmd = [sys.executable, os.path.join(AQUI, "escolher_preset.py"), "sugerir", roteiro, "--formato", formato, "--saida", out]
            if cliente: cmd += ["--cliente", cliente]
            subprocess.run(cmd, capture_output=True, timeout=60)
            d = json.load(open(out, encoding="utf-8"))
            sug.add(d.get("linguagem")); sug |= {t.get("preset") for t in d.get("trechos", [])}
        elif pedido:
            r = subprocess.run([sys.executable, os.path.join(AQUI, "escolher_preset.py"), "pedido", pedido, "--formato", formato],
                               capture_output=True, text=True, timeout=60).stdout
            ids = {p["id"] for p in catalogo()["presets"]}
            sug |= {w for w in re.findall(r"[a-z][a-z-]+", r) if w in ids}
    except Exception:
        pass
    return sorted(x for x in sug if x)


PAGINA = r"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>/ogab menu</title>
<style>
@font-face{font-family:"Inter Tight";font-weight:800;src:url(/fonte/InterTight-800.woff2) format("woff2");font-display:block}
@font-face{font-family:"Inter Tight";font-weight:500;src:url(/fonte/InterTight-500.woff2) format("woff2");font-display:block}
:root{--bg:#070B08;--bg2:#16201A;--card:rgba(255,255,255,.04);--line:rgba(120,255,180,.16);--tx:#EEF7F1;--mu:#93A89B;--g:#2BFF88;--g1:#9CFFC9;--g2:#14E070;--ink:#04130A;--amb:#F5B544;--grad:linear-gradient(90deg,#9CFFC9,#14E070)}
*{box-sizing:border-box;margin:0}
/* estrutura visual do Monitor de Visto (fundo com brilho radial, vidro, rótulos em caixa alta, botão que respira) com a ID da /ogab */
body{min-height:100vh;color:var(--tx);font:500 15px/1.45 "Inter Tight",system-ui,sans-serif;padding-bottom:110px;
  background:radial-gradient(520px 520px at 30% 12%,rgba(43,255,136,.16),transparent 70%),linear-gradient(135deg,#16201A,#070B08) fixed}
.wrap{max-width:min(1680px,94vw);margin:0 auto;padding:0 24px}
header{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:30px 0 6px}
.logo{display:flex;align-items:center;gap:14px}.logo svg{width:44px;height:44px;border-radius:12px;box-shadow:0 0 20px rgba(43,255,136,.45)}
.wm{font-weight:800;font-size:22px;letter-spacing:-.03em;line-height:1.1}.wm .s{color:var(--g)}.wm small{display:block;font-size:12px;color:var(--mu);letter-spacing:0;font-weight:500}
.lang{display:flex;background:rgba(255,255,255,.06);border-radius:999px;padding:3px}
.lang button{background:none;border:0;color:var(--mu);font:800 12px "Inter Tight";padding:7px 14px;border-radius:999px;cursor:pointer;letter-spacing:.04em}
.lang button[aria-pressed=true]{background:var(--grad);color:var(--ink);box-shadow:0 0 10px rgba(43,255,136,.5)}
h1{font-weight:800;font-size:clamp(28px,4vw,42px);letter-spacing:-.035em;line-height:1.08;margin:24px 0 8px}
.lead{color:var(--mu);max-width:720px}
.fimbox{max-width:560px;width:calc(100% - 32px);padding:28px;border-radius:20px;background:var(--card);backdrop-filter:blur(14px);border:1px solid rgba(43,255,136,.4);box-shadow:0 0 40px rgba(43,255,136,.18);text-align:center}
.fimbox .ok{width:64px;height:64px;margin:0 auto;border-radius:50%;background:var(--grad);color:var(--ink);display:grid;place-items:center;font:800 32px "Inter Tight";box-shadow:0 0 24px rgba(43,255,136,.6)}
.cole{margin:18px 0 12px;padding:18px;border-radius:16px;background:rgba(43,255,136,.1);border:2px solid var(--g);animation:brilha 1.4s ease-in-out infinite alternate}
@keyframes brilha{from{box-shadow:0 0 0 rgba(43,255,136,0)}to{box-shadow:0 0 26px rgba(43,255,136,.55)}}
.cole .rot{font:800 26px "Inter Tight";letter-spacing:-.02em;color:var(--g)}
.teclas{display:flex;justify-content:center;align-items:center;gap:10px;margin:12px 0}.teclas span{font:800 22px "Inter Tight";color:var(--mu)}
kbd{min-width:58px;height:58px;padding:0 12px;border-radius:12px;background:#F2F7F3;color:var(--ink);font:800 26px "Inter Tight";display:grid;place-items:center;box-shadow:0 5px 0 #9DB3A6}
.cole ol{text-align:left;margin:6px auto 0;max-width:340px;color:var(--tx);font:500 15px "Inter Tight";padding-left:22px}.cole li{margin:4px 0}
#msgprev{text-align:left;white-space:pre-wrap;font:500 12.5px ui-monospace,Menlo,monospace;color:var(--mu);background:rgba(0,0,0,.35);border:1px solid var(--line);border-radius:12px;padding:12px;max-height:150px;overflow:auto;margin:0 0 12px}
#copiar{width:100%;height:46px;border:0;cursor:pointer}.fimbox .nota{color:var(--mu);font-size:13px;margin-top:10px}
.fim{position:fixed;inset:0;background:rgba(4,8,5,.92);display:none;place-items:center;z-index:20;text-align:center}.fim b{font-size:30px;font-weight:800;letter-spacing:-.03em;display:block;margin:14px 0 6px;background:var(--grad);-webkit-background-clip:text;color:transparent}
.sabe{margin:16px 0 4px;padding:16px;border-radius:16px;background:var(--card);backdrop-filter:blur(14px);border:1px solid var(--line);font-size:14px;text-align:left}.sabe b{font:800 10.5px "Inter Tight";letter-spacing:.12em;text-transform:uppercase;color:var(--mu);display:block;margin-bottom:6px}.sabe li{color:var(--mu);margin-left:18px}
.prog{display:flex;gap:5px;margin:20px 0 0;padding:3px;border-radius:999px;background:rgba(255,255,255,.06)}.prog i{flex:1;height:6px;border-radius:9px;background:transparent}.prog i.on{background:var(--grad);box-shadow:0 0 8px rgba(43,255,136,.5)}
.passo{font:800 10.5px "Inter Tight";color:var(--mu);letter-spacing:.12em;text-transform:uppercase;margin-top:18px}
h2{font-weight:800;font-size:clamp(24px,3.2vw,34px);letter-spacing:-.03em;line-height:1.1;margin:4px 0 4px;display:flex;align-items:center;gap:10px;flex-wrap:wrap}
h2 .k{color:var(--ink);background:var(--grad);border-radius:12px;width:40px;height:40px;display:grid;place-items:center;font-size:18px;box-shadow:0 0 14px rgba(43,255,136,.45)}
.sub{color:var(--mu);font-size:14.5px;margin-bottom:16px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:12px;align-items:stretch;overflow-y:auto;padding:2px 2px 8px;scrollbar-width:thin}
.card{position:relative;background:var(--card);backdrop-filter:blur(14px);border:1px solid var(--line);border-radius:16px;overflow:hidden;cursor:pointer;transition:transform .15s,border-color .15s;text-align:left;color:inherit;font:inherit;padding:0}
.card:hover{transform:translateY(-2px);border-color:rgba(43,255,136,.4)}
.card[aria-pressed=true]{border-color:rgba(43,255,136,.55);box-shadow:0 0 18px rgba(43,255,136,.35)}
.vis{aspect-ratio:var(--ar,4/5);background:#050806;position:relative;overflow:hidden;display:grid;place-items:center}
.card{display:flex;flex-direction:column}.card .tx{flex:1}
.pager{display:flex;justify-content:center;align-items:center;gap:14px;margin-top:10px;font:800 13px "Inter Tight";color:var(--mu)}
.pager button{width:38px;height:38px;border-radius:10px;border:1px solid var(--line);background:rgba(255,255,255,.06);color:var(--tx);font:800 18px "Inter Tight";cursor:pointer}.pager button:disabled{opacity:.3;cursor:default}
.vis img{width:100%;height:100%;object-fit:cover;display:block}
.chk{position:absolute;top:9px;right:9px;width:26px;height:26px;border-radius:50%;border:2px solid rgba(255,255,255,.7);background:rgba(0,0,0,.35);display:grid;place-items:center;z-index:2}
.card[aria-pressed=true] .chk{background:var(--g);border-color:var(--g)}
.chk svg{width:14px;height:14px;opacity:0}.card[aria-pressed=true] .chk svg{opacity:1}
.code{position:absolute;top:10px;left:10px;font:800 11px "Inter Tight";background:rgba(0,0,0,.55);border:1px solid var(--line);color:var(--g1);padding:2px 7px;border-radius:7px;z-index:2}
.tag{position:absolute;bottom:9px;left:9px;font:800 10.5px "Inter Tight";letter-spacing:.06em;text-transform:uppercase;background:rgba(43,255,136,.14);border:1px solid rgba(43,255,136,.3);color:var(--g);padding:3px 9px;border-radius:999px;z-index:2;backdrop-filter:blur(6px)}
.tx{padding:11px 12px 13px}.tx b{font-weight:800;font-size:15px;letter-spacing:-.015em;display:block}.tx span{color:var(--mu);font-size:12.5px;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;margin-top:3px}
.inicio{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:22px}
.op{border:1px solid var(--line);border-radius:16px;padding:16px;background:var(--card);backdrop-filter:blur(14px);cursor:pointer;color:inherit;font:inherit;text-align:left;transition:.15s}
.op:hover{border-color:rgba(43,255,136,.55);box-shadow:0 0 18px rgba(43,255,136,.3);transform:translateY(-2px)}.op b{display:block;font-weight:800;font-size:22px;letter-spacing:-.025em;margin:12px 0 6px}.op p{color:var(--mu);font-size:14px}
.op .ic{width:100%;aspect-ratio:16/9;border-radius:12px;overflow:hidden;border:1px solid var(--line)}
.rev{display:grid;grid-template-columns:auto 1fr;gap:22px;align-items:center;margin:8px 0 18px;padding:18px 22px;border-radius:16px;background:var(--card);backdrop-filter:blur(14px);border:1px solid var(--line)}
.anel{width:104px;height:104px;position:relative}.anel svg{width:100%;height:100%;transform:rotate(-90deg)}.anel .n{position:absolute;inset:0;display:grid;place-items:center;text-align:center;font:800 26px "Inter Tight";letter-spacing:-.03em;line-height:1}.anel .n small{display:block;font:500 11px "Inter Tight";color:var(--mu);letter-spacing:0;margin-top:2px}
.rev h2{margin:0}.rev .pills{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}
.pill{display:inline-flex;align-items:center;gap:7px;font:800 12px "Inter Tight";padding:6px 12px;border-radius:999px;border:1px solid}
.pill.g{color:var(--g);background:rgba(43,255,136,.12);border-color:rgba(43,255,136,.3)}.pill.a{color:var(--amb);background:rgba(245,181,68,.12);border-color:rgba(245,181,68,.3)}
.pill i{width:8px;height:8px;border-radius:50%;background:currentColor;box-shadow:0 0 8px currentColor;animation:breathe 1.6s infinite}
.rgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:12px;max-height:calc(100vh - 360px);overflow:auto;padding:2px}
.rc{display:grid;grid-template-columns:86px 1fr;gap:12px;align-items:center;padding:10px;border-radius:16px;background:var(--card);backdrop-filter:blur(14px);border:1px solid var(--line);cursor:pointer;transition:.15s;text-align:left;color:inherit;font:inherit}
.rc:hover{border-color:rgba(43,255,136,.55);box-shadow:0 0 18px rgba(43,255,136,.25);transform:translateY(-2px)}
.rc .mini{width:86px;aspect-ratio:4/5;border-radius:12px;overflow:hidden;border:1px solid var(--line);background:#050806;display:grid;place-items:center}.rc .mini img{width:100%;height:100%;object-fit:cover}
.rc .mini.auto{background:radial-gradient(circle at 50% 40%,rgba(245,181,68,.22),transparent 70%),#0B110D}.rc .mini.auto span{font:800 13px "Inter Tight";letter-spacing:.12em;color:var(--amb)}
.rc .rot{font:800 10.5px "Inter Tight";letter-spacing:.12em;text-transform:uppercase;color:var(--mu);display:flex;align-items:center;gap:6px}.rc .rot b{color:var(--ink);background:var(--grad);border-radius:6px;padding:0 6px;letter-spacing:0}
.rc .esc{font-weight:800;font-size:15px;letter-spacing:-.015em;margin-top:4px;line-height:1.25}.rc .mais{display:flex;gap:5px;flex-wrap:wrap;margin-top:6px}.rc .mais span{font:800 11px "Inter Tight";color:var(--g1);background:rgba(43,255,136,.1);border:1px solid rgba(43,255,136,.25);padding:2px 8px;border-radius:999px}
.rc .ed{font:500 12px "Inter Tight";color:var(--mu);margin-top:6px}
.autobox{display:grid;grid-template-columns:auto 1fr;gap:22px;align-items:center;padding:24px;border-radius:16px;background:var(--card);backdrop-filter:blur(14px);border:1px solid rgba(43,255,136,.4);box-shadow:0 0 30px rgba(43,255,136,.15);margin-top:8px}
.autobox .lg svg{width:120px;height:120px;border-radius:30px;box-shadow:0 0 34px rgba(43,255,136,.5);animation:breathe 2.4s ease-in-out infinite}
.autobox b{display:block;font-weight:800;font-size:24px;letter-spacing:-.03em;margin-bottom:6px}.autobox p{color:var(--mu)}
@media (max-width:640px){.rev,.autobox{grid-template-columns:1fr}}
.resumo{display:grid;gap:8px;margin-top:10px;max-height:calc(100vh - 330px);overflow:auto}.resumo div{display:flex;gap:12px;padding:12px 16px;border-radius:12px;background:var(--card);backdrop-filter:blur(14px);border:1px solid var(--line)}
.resumo b{min-width:200px;font:800 10.5px "Inter Tight";letter-spacing:.12em;text-transform:uppercase;color:var(--mu);padding-top:3px}.resumo span{color:var(--mu)}.resumo .ok{color:var(--tx)}
.barra{position:fixed;left:0;right:0;bottom:0;background:rgba(5,8,6,.8);backdrop-filter:blur(14px);border-top:1px solid var(--line);z-index:9}
.barra .wrap{display:flex;align-items:center;gap:10px;padding:14px 20px}.barra .codes{flex:1;min-width:0;overflow-x:auto;white-space:nowrap;font:800 13px "Inter Tight";color:var(--g1);scrollbar-width:none}
.barra button{border:0;font:800 13px "Inter Tight";cursor:pointer;border-radius:10px;padding:0 16px;height:42px}
.go{background:var(--grad);color:var(--ink);border-radius:12px!important;min-width:170px;letter-spacing:.08em;text-transform:uppercase;animation:respira 1.6s ease-in-out infinite alternate}
@keyframes respira{from{box-shadow:0 0 6px rgba(43,255,136,.25);transform:scale(1)}to{box-shadow:0 0 16px rgba(43,255,136,.7);transform:scale(1.015)}}
.bk{background:rgba(255,255,255,.08);color:var(--tx);border:1px solid var(--line)!important}.pl{background:rgba(245,181,68,.12);color:var(--amb);border:1px solid rgba(245,181,68,.3)!important;border-radius:999px!important}
.barra button[hidden]{display:none}
.go:disabled{animation:none;opacity:.35;cursor:not-allowed;filter:grayscale(.6)}
.pl.ativo{background:var(--amb)!important;color:var(--ink)!important}
.fim{position:fixed;inset:0;background:rgba(4,8,5,.92);display:none;place-items:center;z-index:20;text-align:center}.fim b{font-size:26px;font-weight:800;letter-spacing:-.03em;display:block;margin:14px 0 6px}
@media (max-width:640px){.inicio{grid-template-columns:1fr}.grid{grid-template-columns:repeat(2,1fr)}.resumo b{min-width:110px}.barra .codes{display:none}}
/* ---------- prévias em loop (opções sem GIF) ---------- */
.an{width:100%;height:100%;position:relative;display:grid;place-items:center;font-family:"Inter Tight";overflow:hidden;background:radial-gradient(circle at 50% 30%,#13241A,#050806 70%)}
.an .person{position:absolute;bottom:-6%;left:50%;width:46%;height:62%;transform:translateX(-50%);background:linear-gradient(#2A3A31,#1A251F);border-radius:48% 48% 18% 18%}
.an .person::before{content:"";position:absolute;top:-36%;left:50%;width:56%;aspect-ratio:1;transform:translateX(-50%);border-radius:50%;background:#33463B}
.cap{position:absolute;left:8%;right:8%;bottom:16%;text-align:center;font-weight:800;color:#fff;font-size:15px;line-height:1.15;text-shadow:0 2px 6px #000}
.cap i{font-style:normal;display:inline-block;opacity:0;animation:pop 3s infinite}
.cap i:nth-child(2){animation-delay:.35s}.cap i:nth-child(3){animation-delay:.7s}.cap i:nth-child(4){animation-delay:1.05s}
.cap .y{color:#FFD43B;font-size:24px}.cap .pl{color:#fff}.cap-plain .cap{font-weight:500;background:rgba(0,0,0,.55);border-radius:4px;padding:2px 4px}.cap .sf{font-family:Georgia,serif;font-style:italic;color:#5AA9FF;font-size:22px;font-weight:400}
.cap .gl{color:#FFE45C;font-size:24px;text-shadow:0 0 12px rgba(255,228,92,.9)}
@keyframes pop{0%,8%{opacity:0;transform:translateY(6px) scale(.9)}14%,80%{opacity:1;transform:none}92%,100%{opacity:0}}
.pod .cap{bottom:12%}.pod .a{color:#2BFF88}.pod .b{color:#FFB84D}
.none::after{content:"";width:46%;aspect-ratio:1;border-radius:50%;border:3px solid #3A4A41;background:linear-gradient(45deg,transparent 47%,#3A4A41 47% 53%,transparent 53%)}
.L{font-weight:800;font-size:26px;letter-spacing:-.03em;color:#fff;animation:3s infinite both}
.let-blur .L{animation-name:lblur}.let-blurup .L{animation-name:lblurup}.let-up .L{animation-name:lup}.let-down .L{animation-name:ldown}
.let-right .L{animation-name:lright}.let-left .L{animation-name:lleft}.let-glow .L{animation-name:lglow}.let-flick .L{animation-name:lflick}
.let-cut .L{animation-name:lcut}.let-cine .L{animation-name:lcine;letter-spacing:.18em;font-size:20px}.let-spin .L{animation-name:lspin}
.let-zoom .L{animation-name:lzoom}.let-gold .L{background:linear-gradient(#FFE9A8,#C9932B);-webkit-background-clip:text;color:transparent;animation-name:lblurup}
.let-silver .L{background:linear-gradient(#FFFFFF,#8C969E);-webkit-background-clip:text;color:transparent;animation-name:lblurup}
.let-under .L{animation-name:lblurup;text-decoration:underline 3px var(--g);text-underline-offset:6px}.let-hl .L{animation-name:lblurup;background:var(--g);color:var(--ink);padding:0 8px;border-radius:6px}
.fast .L{animation-duration:2s}
.let-word .L i{font-style:normal;display:inline-block;opacity:0;animation:pop 3s infinite}.let-word .L i:nth-child(2){animation-delay:.3s}.let-word .L i:nth-child(3){animation-delay:.6s}
@keyframes lblur{0%,10%{opacity:0;filter:blur(12px)}25%,80%{opacity:1;filter:none}95%,100%{opacity:0}}
@keyframes lblurup{0%,10%{opacity:0;filter:blur(10px);transform:translateY(14px)}25%,80%{opacity:1;filter:none;transform:none}95%,100%{opacity:0}}
@keyframes lup{0%,10%{opacity:0;transform:translateY(30px)}25%,80%{opacity:1;transform:none}95%,100%{opacity:0;transform:translateY(-10px)}}
@keyframes ldown{0%,10%{opacity:0;transform:translateY(-30px)}25%,80%{opacity:1;transform:none}95%,100%{opacity:0}}
@keyframes lright{0%,10%{opacity:0;transform:translateX(-40px)}25%,80%{opacity:1;transform:none}95%,100%{opacity:0}}
@keyframes lleft{0%,10%{opacity:0;transform:translateX(40px)}25%,80%{opacity:1;transform:none}95%,100%{opacity:0}}
@keyframes lglow{0%,10%{opacity:0;text-shadow:none}25%{opacity:1;text-shadow:0 0 24px #fff}40%,80%{opacity:1;text-shadow:0 0 8px rgba(255,255,255,.5)}95%,100%{opacity:0}}
@keyframes lflick{0%,10%{opacity:0}12%{opacity:1}14%{opacity:.2}17%{opacity:1}19%{opacity:.3}22%,80%{opacity:1}95%,100%{opacity:0}}
@keyframes lcut{0%,10%{clip-path:inset(0 100% 0 0)}30%,80%{clip-path:inset(0 0 0 0)}95%,100%{clip-path:inset(0 0 0 100%)}}
@keyframes lcine{0%,10%{opacity:0;letter-spacing:.6em}35%,80%{opacity:1;letter-spacing:.18em}95%,100%{opacity:0}}
@keyframes lspin{0%,10%{opacity:0;transform:rotate(-90deg) scale(.5)}30%,80%{opacity:1;transform:none}95%,100%{opacity:0}}
@keyframes lzoom{0%,10%{opacity:0;transform:scale(1.8)}30%,80%{opacity:1;transform:none}95%,100%{opacity:0}}
.frame{border:3px solid #CFE9DA;border-radius:8px;animation:breathe 3s ease-in-out infinite}.fmt.v .frame{width:38%;aspect-ratio:9/16}.fmt.h .frame{width:74%;aspect-ratio:16/9}
.fmt.multi .frame{width:30%;aspect-ratio:4/5;box-shadow:42px 10px 0 -3px #050806,42px 10px 0 0 var(--g)}.fmt .frame{display:grid;place-items:center}.fmt .pr{font:800 13px "Inter Tight";color:var(--g1)}
.abas{display:flex;gap:6px;flex-wrap:wrap;margin:0 0 14px}.abas button{border:1px solid var(--line);background:rgba(255,255,255,.04);color:var(--mu);font:800 13px "Inter Tight";padding:8px 14px;border-radius:999px;cursor:pointer}
.abas button{display:inline-flex;align-items:center;gap:7px}.pi{width:15px;height:15px;fill:currentColor;flex:none}
.pcard{position:absolute;bottom:12px;left:12px;width:32px;height:32px;fill:var(--g1);opacity:.9;z-index:2;filter:drop-shadow(0 0 6px rgba(43,255,136,.4))}
.abas button[aria-pressed=true]{background:var(--grad);color:var(--ink);border-color:transparent;box-shadow:0 0 10px rgba(43,255,136,.45)}.abas .n{margin-left:6px;opacity:.8}
.fmt.ad .frame::after{content:"AD";display:block;font:800 12px "Inter Tight";color:var(--g);margin:6px}
@keyframes breathe{50%{transform:scale(1.06)}}
.dots{display:grid;grid-template-columns:repeat(3,22px);gap:8px}.dots span{width:22px;height:22px;border-radius:6px;background:var(--g);opacity:0;animation:pop 2.6s infinite}
.dots span:nth-child(n){animation-delay:calc(var(--i)*.18s)}
.bars{display:flex;align-items:flex-end;gap:5px;height:44%}.bars span{width:9px;border-radius:5px;background:linear-gradient(var(--g1),var(--g2));animation:eq var(--d,1s) ease-in-out infinite alternate}
.bars span:nth-child(2n){animation-delay:-.4s}.bars span:nth-child(3n){animation-delay:-.7s}
@keyframes eq{from{height:18%}to{height:100%}}
.rings{width:30%;aspect-ratio:1;border-radius:50%;background:var(--g);position:relative}.rings::before,.rings::after{content:"";position:absolute;inset:0;border-radius:50%;border:2px solid var(--g);animation:ring 1.8s infinite}.rings::after{animation-delay:.9s}
@keyframes ring{from{transform:scale(1);opacity:.9}to{transform:scale(2.6);opacity:0}}
.strip{display:flex;gap:4px;width:200%;animation:scroll var(--d,4s) linear infinite}.strip span{height:58px;border-radius:6px;background:#26392E;flex:none}.strip span:nth-child(odd){background:#1B2B22}
@keyframes scroll{to{transform:translateX(-50%)}}
.sw3{width:64%;aspect-ratio:1;border-radius:18px;animation:hue 4s ease-in-out infinite alternate}
@keyframes hue{50%{filter:saturate(1.6) contrast(1.15)}}
.behind .big{position:absolute;top:22%;font:800 34px "Inter Tight";color:var(--g);animation:lblurup 3s infinite}.behind .person{z-index:2}
.hooks span{display:block;font-weight:800;color:#fff;font-size:15px;opacity:0;animation:pop 3s infinite;margin:3px 0}.hooks span:nth-child(2){animation-delay:.5s;color:var(--g)}.hooks span:nth-child(3){animation-delay:1s}
.cover .frame{background:linear-gradient(160deg,#1F3A2A,#0B140F);display:grid;place-items:end center;padding-bottom:10px}.cover .frame::after{content:"TÍTULO";font:800 13px "Inter Tight";color:#FFD43B}
.logo-an svg{width:40%;animation:lzoom 3s infinite}
.cta .btn{font:800 14px "Inter Tight";background:var(--g);color:var(--ink);padding:9px 14px;border-radius:999px;animation:breathe 1.6s infinite}
@media (prefers-reduced-motion:reduce){.an *,.an *::before,.an *::after{animation-duration:6s!important}}
</style></head><body>
<div class="wrap">
<header><div class="logo"><svg viewBox="0 0 220 220" aria-hidden="true"><defs><linearGradient id="g6" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#16201A"/><stop offset="1" stop-color="#070B08"/></linearGradient><linearGradient id="v6" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#9CFFC9"/><stop offset="1" stop-color="#14E070"/></linearGradient></defs><rect width="220" height="220" rx="56" fill="url(#g6)"/><rect x="1.5" y="1.5" width="217" height="217" rx="55" fill="none" stroke="#fff" stroke-opacity=".08" stroke-width="3"/><rect x="112" y="40" width="74" height="34" rx="12" fill="url(#v6)"/><rect x="73" y="93" width="74" height="34" rx="12" fill="url(#v6)" fill-opacity=".85"/><rect x="34" y="146" width="74" height="34" rx="12" fill="url(#v6)" fill-opacity=".6"/></svg>
<div class="wm"><span class="s">/</span>ogab<small data-t="menu"></small></div></div>
<div class="lang" role="group" aria-label="Idioma / Language"><button data-l="pt">PT</button><button data-l="en">EN</button></div></header>
<div class="prog" id="prog"></div>
<div id="tela"></div>
</div>
<div class="barra"><div class="wrap"><button class="bk" id="bk" data-t="voltar"></button><span class="codes" id="codes"></span><button class="pl" id="pl" data-t="pular"></button><button class="go" id="go"></button></div></div>
<div class="fim" id="fim"><div class="fimbox">
  <div class="ok">✓</div><b data-t="fim_t"></b>
  <div class="cole"><div class="rot" data-t="cole_rot"></div><div class="teclas"><kbd id="kmod">⌘</kbd><span>+</span><kbd>V</kbd></div>
    <ol><li data-t="cole_1"></li><li data-t="cole_2"></li></ol></div>
  <pre id="msgprev"></pre>
  <button class="go" id="copiar" data-t="copiar"></button>
  <p class="nota" data-t="fim_p"></p></div></div>
<script>
const D = __DADOS__;
const T = {
 pt:{menu:"Menu do vídeo",ola:"Como você quer montar este vídeo?",ola_p:"Escolha passo a passo o que entra no vídeo, ou deixe tudo com o Gab.",
  auto_t:"Automático",auto_p:"O Gab escolhe tudo pelo que já sabe de você e da marca (estilo, memória da marca, pedidos anteriores) e pelo roteiro.",
  eu_t:"Eu escolho",eu_p:"Passo a passo: formato, estilo, legenda, lettering, motion, b-roll, música, efeitos, ritmo, cor e extras.",
  sabe:"O que o Gab já sabe dessa marca",gab_escolhe:"automático",sug:"sugerido",passo:(i,n)=>`Passo ${i} de ${n}`,
  voltar:"Voltar",pular:"Automático neste passo",avancar:"Avançar",revisar:"Revisar",confirmar:"Confirmar",conf_auto:"Confirmar: automático",
  resumo_t:"Seu vídeo vai ficar assim",resumo_p:"Clique num cartão para voltar e mudar.",resumo_rot:"Revisão",suas:"suas",escolhas_suas:"escolhas suas",no_auto:"no automático",passos_auto:"passos no automático",editar:"Clique para mudar",auto_resumo:"O Gab vai escolher tudo pelo que já sabe de você e da marca.",
  ouvir:"Ouvir o clima",seu:"seu",trava:"Marque uma opção ou aperte Automático neste passo",marque:"marque uma opção ou use o automático",max:n=>`até ${n}`,fim_t:"Pronto! Agora falta um passo",fim_p:"Se o Claude já mostrou as suas escolhas, não precisa colar.",cole_rot:"Cole no Claude",cole_1:"Volte para a janela do Claude",cole_2:"Cole a mensagem e aperte Enter",copiar:"Copiar a mensagem de novo",copiado:"Copiado!",cab:"/ogab menu confirmado",cab_auto:"/ogab menu confirmado: automático (o Gab escolhe tudo pelo que já sabe de você e da marca).",auto_l:"Automático",erro:"Não consegui salvar. O Gab ainda está aberto?"},
 en:{menu:"Video menu",ola:"How do you want to build this video?",ola_p:"Pick step by step what goes in, or leave it all to Gab.",
  auto_t:"Automatic",auto_p:"Gab picks everything from what he already knows about you and the brand (style, brand memory, past requests) and the script.",
  eu_t:"I'll choose",eu_p:"Step by step: format, style, captions, lettering, motion, b-roll, music, effects, pace, colour and extras.",
  sabe:"What Gab already knows about this brand",gab_escolhe:"automatic",sug:"suggested",seu:"yours",passo:(i,n)=>`Step ${i} of ${n}`,
  voltar:"Back",pular:"Automatic for this step",avancar:"Next",revisar:"Review",confirmar:"Confirm",conf_auto:"Confirm: automatic",
  resumo_t:"Here is your video",resumo_p:"Click a card to go back and change it.",resumo_rot:"Review",suas:"yours",escolhas_suas:"your picks",no_auto:"on automatic",passos_auto:"steps on automatic",editar:"Click to change",auto_resumo:"Gab will pick everything from what he knows about you and the brand.",
  ouvir:"Hear the mood",trava:"Tick an option or press Automatic for this step",marque:"tick an option or use automatic",max:n=>`up to ${n}`,fim_t:"Done! One more step",fim_p:"If Claude already shows your choices, no need to paste.",cole_rot:"Paste into Claude",cole_1:"Go back to the Claude window",cole_2:"Paste the message and press Enter",copiar:"Copy the message again",copiado:"Copied!",cab:"/ogab menu confirmed",cab_auto:"/ogab menu confirmed: automatic (Gab picks everything from what he knows about you and the brand).",auto_l:"Automatic",erro:"Couldn't save. Is Gab still open?"}};
let L = D.lingua || ((navigator.language||"pt").toLowerCase().startsWith("pt") ? "pt" : "en");
try { L = localStorage.getItem("ogab_menu_lang") || L } catch(e) {}
const sel = {}; D.grupos.forEach(g => sel[g.id] = new Set());
const N = D.grupos.length; let passo = 0, auto = false; const aba = {};
const pag = {}, autoPasso = {};   // autoPasso[g] = a pessoa apertou 'Automático neste passo'
D.grupos.forEach(g => { if (g.abas) aba[g.id] = g.abas[0].id; });   // estilos abrem em "Todos"   // 0 = início, 1..N = grupos, N+1 = resumo
const $ = s => document.querySelector(s), esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const ic = (id, cls = "pi") => D.icones && D.icones[id] ? `<svg class="${cls}" viewBox="0 0 24 24" aria-hidden="true"><path d="${D.icones[id]}"/></svg>` : "";
const CHK = '<svg viewBox="0 0 16 16"><path d="M3 8.5l3 3 7-7" fill="none" stroke="#04130A" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg>';
function prev(i) {
  if (i.gif) return `<img loading="lazy" src="/arquivo/${esc(i.gif)}" alt="">`;
  const a = i.anim || "none", P = '<div class="person"></div>';
  const w = L === "pt" ? ["isso","muda","o","JOGO"] : ["this","changes","the","GAME"];
  if (a === "none") return `<div class="an none"></div>`;
  if (a.startsWith("cap-")) {
    const k = {"cap-gab":"", "cap-plain":"", "cap-hl":"y", "cap-serif":"sf", "cap-lume":"gl"}[a] ?? "";
    if (a === "cap-pod") return `<div class="an pod">${P}<div class="cap"><i class="a">${w[0]} ${w[1]}</i><br><i class="b">${w[2]} ${w[3].toLowerCase()}</i></div></div>`;
    return `<div class="an ${a}">${P}<div class="cap"><i>${w[0]}</i> <i>${w[1]}</i> <i>${w[2]}</i> <i class="${k}">${k ? w[3] : w[3].toLowerCase()}</i></div></div>`;
  }
  if (a.startsWith("let-")) {
    const t = a.startsWith("let-word") ? `<i>${w[1].toUpperCase()}</i> <i>${w[2].toUpperCase()}</i> <i>${w[3]}</i>` : (a.startsWith("let-cine") ? "CINEMA" : "Lettering");
    return `<div class="an ${a}"><div class="L">${t}</div></div>`;
  }
  if (a.startsWith("fmt ")) { const pr = a.split(" ")[1], [w, h] = pr.split(":").map(Number), wd = Math.min(74, Math.round(46 * w / h + 8));
    return `<div class="an fmt"><div class="frame" style="width:${wd}%;aspect-ratio:${w}/${h}"><span class="pr">${pr}</span></div></div>`; }
  if (a.startsWith("fmt")) return `<div class="an ${a}"><div class="frame"></div></div>`;
  if (a.startsWith("dens")) { const n = {d1:2,d2:5,d3:9}[a.split(" ")[1]]; return `<div class="an"><div class="dots">${Array.from({length:9},(_,k)=>`<span style="--i:${k};${k<n?"":"visibility:hidden"}"></span>`).join("")}</div></div>`; }
  if (a.startsWith("bars")) { const d = {m1:"1.3s",m2:".9s",m3:"1.8s",m4:".5s",m5:"1s",m6:"2.2s",m7:".4s",m8:"1.6s"}[a.split(" ")[1]]; return `<div class="an"><div class="bars" style="--d:${d}">${"<span></span>".repeat(9)}</div></div>`; }
  if (a.startsWith("sfx")) return `<div class="an"><div class="rings" style="${a.endsWith("s2")?"width:18%":""}"></div></div>`;
  if (a.startsWith("pace")) { const d = {p1:"9s",p2:"5s",p3:"2.5s"}[a.split(" ")[1]], ws = {p1:[90,110,100],p2:[60,40,70],p3:[30,22,26]}[a.split(" ")[1]];
    return `<div class="an"><div class="strip" style="--d:${d}">${Array.from({length:16},(_,k)=>`<span style="width:${ws[k%3]}px"></span>`).join("")}</div></div>`; }
  if (a.startsWith("takes")) { const c = {t1:"#2B5A44",t2:"linear-gradient(135deg,#2BFF88,#7A5CFF)",t3:"linear-gradient(90deg,#2B5A44 50%,#5B4FC9 50%)",t4:"#5A4A2B"}[a.split(" ")[1]];
    return `<div class="an"><div class="strip" style="--d:5s">${Array.from({length:10},()=>`<span style="width:70px;height:90px;background:${c}"></span>`).join("")}</div></div>`; }
  if (a.startsWith("col")) { const c = {c1:"linear-gradient(135deg,#2B4A63,#C9824A)",c2:"linear-gradient(135deg,#6B7F8C,#B9A48F)",c3:"linear-gradient(135deg,#111,#DDD)"}[a.split(" ")[1]];
    return `<div class="an"><div class="sw3" style="background:${c}"></div></div>`; }
  if (a === "behind") return `<div class="an behind"><div class="big">${L==="pt"?"ATRÁS":"BEHIND"}</div>${P}</div>`;
  if (a === "hooks") return `<div class="an hooks"><div>${(L==="pt"?["Gancho A","Gancho B","Gancho C"]:["Hook A","Hook B","Hook C"]).map(x=>`<span>${x}</span>`).join("")}</div></div>`;
  if (a === "cover") return `<div class="an cover fmt v"><div class="frame"></div></div>`;
  if (a === "logo") return `<div class="an logo-an">${document.querySelector(".logo svg").outerHTML}</div>`;
  if (a === "cta") return `<div class="an cta"><span class="btn">${L==="pt"?"seusite.com":"yoursite.com"}</span></div>`;
  return `<div class="an none"></div>`;
}
function pronto(p) { const g = D.grupos[p - 1]; return !g || sel[g.id].size > 0 || autoPasso[g.id] || pula(p); }
function codigos() { const out = []; D.grupos.forEach(g => g.itens.forEach((i, n) => { if (sel[g.id].has(i.id)) out.push(g.letra + (n + 1)); })); return out; }
function render() {
  document.documentElement.lang = L === "pt" ? "pt-BR" : "en";
  document.querySelectorAll("[data-t]").forEach(e => { const v = T[L][e.dataset.t]; if (typeof v === "string") e.innerHTML = v; });
  document.querySelectorAll(".lang button").forEach(b => b.setAttribute("aria-pressed", b.dataset.l === L));
  $("#prog").innerHTML = passo === 0 || auto ? "" : Array.from({length: N + 1}, (_, k) => `<i class="${k < passo ? "on" : ""}"></i>`).join("");
  const sabe = D.ja_sabe.length ? `<div class="sabe"><b>${T[L].sabe}</b><ul>${D.ja_sabe.map(x=>`<li>${esc(x)}</li>`).join("")}</ul></div>` : "";
  let h = "";
  if (passo === 0) {
    h = `<h1>${T[L].ola}</h1><p class="lead">${T[L].ola_p}</p><div class="inicio">
      <button class="op" data-op="auto"><div class="ic">${prev({anim:"dens d3"})}</div><b>${T[L].auto_t}</b><p>${T[L].auto_p}</p></button>
      <button class="op" data-op="eu"><div class="ic">${prev({anim:"let-word"})}</div><b>${T[L].eu_t}</b><p>${T[L].eu_p}</p></button></div>${sabe}`;
  } else if (passo <= N) {
    const g = D.grupos[passo - 1];
    h = `<div class="passo">${T[L].passo(passo, N)}</div><h2><span class="k">${g.letra}</span>${esc(g.nome[L])}</h2>
      <p class="sub">${esc(g.sub[L])}${g.max ? " · " + T[L].max(g.max) : ""}${sel[g.id].size ? "" : (autoPasso[g.id] ? " · <b style='color:var(--amb)'>" + T[L].gab_escolhe + "</b>" : " · <b style='color:var(--mu)'>" + T[L].marque + "</b>")}</p>
      ${g.abas ? `<div class="abas">${g.abas.filter(x => x.id !== "sugeridos" || D.sugeridos.length).map(x => { const c = g.itens.filter(i => (x.id === "todos" || (x.id === "sugeridos" ? D.sugeridos.includes(i.id) : i.aba === x.id)) && sel[g.id].has(i.id)).length;
        return `<button data-aba="${x.id}" aria-pressed="${aba[g.id] === x.id}">${ic(x.id)}${esc(x.nome[L])}${c ? `<span class="n">${c}</span>` : ""}</button>`; }).join("")}</div>` : ""}
      <div class="grid" style="${g.id === "lettering" ? "--ar:4/3" : (["formato", "musica", "sfx", "ritmo", "cor"].includes(g.id) ? "--ar:1/1" : "")}">${g.itens.map((i, n) => (g.abas && !(aba[g.id] === "todos" || (aba[g.id] === "sugeridos" ? D.sugeridos.includes(i.id) : i.aba === aba[g.id]))) ? "" : `<button class="card" data-g="${g.id}" data-i="${esc(i.id)}" aria-pressed="${sel[g.id].has(i.id)}" title="${esc(i.desc[L])}">
      <div class="vis">${prev(i)}${g.id === "formato" ? ic(i.aba, "pcard") : ""}<span class="code">${g.letra}${n + 1}</span><span class="chk">${CHK}</span>${D.sugeridos.includes(i.id) && g.id === "estilo" ? `<span class="tag">${T[L].sug}</span>` : ""}${i.seu ? `<span class="tag">${T[L].seu}</span>` : ""}</div>
      <div class="tx"><b>${esc(i.nome[L])}</b><span>${esc(i.desc[L])}</span></div></button>`).join("")}</div><div class="pager" id="pager"></div>`;
  } else {
    const man = D.grupos.filter(g => sel[g.id].size).length, tot = D.grupos.length, pct = auto ? 0 : man / tot;
    const C = 2 * Math.PI * 46, anel = `<div class="anel"><svg viewBox="0 0 104 104"><circle cx="52" cy="52" r="46" fill="none" stroke="rgba(255,255,255,.06)" stroke-width="9"/>
      <circle cx="52" cy="52" r="46" fill="none" stroke="url(#ga)" stroke-width="9" stroke-linecap="round" stroke-dasharray="${C}" stroke-dashoffset="${C * (1 - pct)}" style="filter:drop-shadow(0 0 6px rgba(43,255,136,.6));transition:stroke-dashoffset .8s"/>
      <defs><linearGradient id="ga"><stop offset="0" stop-color="#9CFFC9"/><stop offset="1" stop-color="#14E070"/></linearGradient></defs></svg>
      <div class="n"><div>${auto ? "auto" : man + "/" + tot}<small>${T[L].suas}</small></div></div></div>`;
    if (auto) {
      h = `<div class="passo">${T[L].resumo_rot}</div><h2>${T[L].resumo_t}</h2><div class="autobox"><div class="lg">${document.querySelector(".logo svg").outerHTML}</div>
        <div><b>${T[L].auto_t}</b><p>${T[L].auto_resumo}</p><div class="rev" style="margin:12px 0 0;padding:0;border:0;background:none;display:block">
        <div class="pills"><span class="pill g"><i></i>${tot} ${T[L].passos_auto}</span></div></div></div></div>${sabe}`;
    } else {
      h = `<div class="passo">${T[L].resumo_rot}</div><div class="rev">${anel}<div><h2>${T[L].resumo_t}</h2><p class="sub" style="margin:4px 0 0">${T[L].resumo_p}</p>
        <div class="pills"><span class="pill g"><i></i>${man} ${T[L].escolhas_suas}</span><span class="pill a"><i></i>${tot - man} ${T[L].no_auto}</span></div></div></div>
        <div class="rgrid">${D.grupos.map((g, k) => { const its = g.itens.filter(i => sel[g.id].has(i.id));
          const mini = its.length ? `<div class="mini">${prev(its[0])}</div>` : `<div class="mini auto"><span>AUTO</span></div>`;
          return `<button class="rc" data-ir="${k + 1}">${mini}<div><div class="rot"><b>${g.letra}</b>${esc(g.nome[L])}</div>
            <div class="esc">${its.length ? esc(its[0].nome[L]) : `<span style="color:var(--amb)">${T[L].gab_escolhe}</span>`}</div>
            ${its.length > 1 ? `<div class="mais">${its.slice(1, 4).map(i => `<span>${esc(i.nome[L])}</span>`).join("")}${its.length > 4 ? `<span>+${its.length - 4}</span>` : ""}</div>` : ""}
            <div class="ed">${T[L].editar}</div></div></button>`; }).join("")}</div>`;
    }
  }
  $("#tela").innerHTML = h;
  ajustar();
  $("#bk").hidden = passo === 0; $("#pl").hidden = !(passo >= 1 && passo <= N); $("#go").hidden = passo === 0;
  $("#go").textContent = passo > N ? (auto ? T[L].conf_auto : T[L].confirmar) : (passo === N ? T[L].revisar : T[L].avancar);
  $("#codes").textContent = auto ? T[L].auto_t : codigos().join("  ");
  const trava = passo >= 1 && passo <= N && !pronto(passo);
  $("#go").disabled = trava; $("#go").title = trava ? T[L].trava : "";
  $("#pl").classList.toggle("ativo", passo >= 1 && passo <= N && !!autoPasso[D.grupos[passo - 1].id]);
  scrollTo(0, 0);
}
function pula(p) { const g = D.grupos[p - 1]; return g && ["estilo", "gancho", "layout", "prova", "efeitos"].includes(g.id) && sel.motions && sel.motions.has("sem"); }
// cabe tudo na tela, sem letra miúda: cartão entre 160 e 300 px; mede quantas colunas e linhas cabem e,
// se não couber tudo, divide em páginas (‹ 1/2 ›) em vez de rolar ou encolher.
function ajustar() {
  const g = $(".grid"), pager = $("#pager"); if (!g) return;
  const cards = [...g.children]; cards.forEach(c => c.style.display = "");
  const n = cards.length, gap = 12, W = g.clientWidth;
  const H = innerHeight - g.getBoundingClientRect().top - $(".barra").offsetHeight - 58;
  const ini = Math.max(2, Math.ceil((W + gap) / (300 + gap))), fim = Math.max(ini, Math.floor((W + gap) / (160 + gap)));
  let esc_ = null;
  for (let c = ini; c <= fim; c++) {
    g.style.gridTemplateColumns = `repeat(${c}, 1fr)`;
    const alt = Math.max(...cards.slice(0, c).map(x => x.offsetHeight)) || 300, linhas = Math.max(1, Math.floor((H + gap) / (alt + gap)));
    esc_ = {c, cap: c * linhas}; if (c * linhas >= n) break;
  }
  g.style.gridTemplateColumns = `repeat(${esc_.c}, 1fr)`; g.style.maxHeight = "none"; g.style.overflow = "visible";
  const gid = D.grupos[passo - 1].id, paginas = Math.ceil(n / esc_.cap);
  pag[gid] = Math.max(0, Math.min(paginas - 1, pag[gid] || 0));
  if (paginas > 1) cards.forEach((c, k) => { if (k < pag[gid] * esc_.cap || k >= (pag[gid] + 1) * esc_.cap) c.style.display = "none"; });
  pager.innerHTML = paginas > 1 ? `<button data-pg="-1" ${pag[gid] ? "" : "disabled"}>‹</button><span>${pag[gid] + 1} / ${paginas}</span><button data-pg="1" ${pag[gid] < paginas - 1 ? "" : "disabled"}>›</button>` : "";
}
addEventListener("resize", ajustar);
function ir(p) { const dir = p >= passo ? 1 : -1; while (p >= 1 && p <= N && pula(p)) p += dir; passo = Math.max(0, Math.min(N + 1, p)); render(); }
document.addEventListener("click", e => {
  const op = e.target.closest(".op"); if (op) { auto = op.dataset.op === "auto"; return ir(auto ? N + 1 : 1); }
  const r = e.target.closest("[data-ir]"); if (r) return ir(+r.dataset.ir);
  const ab = e.target.closest("[data-aba]"); if (ab) { const gid = D.grupos[passo - 1].id; aba[gid] = ab.dataset.aba; pag[gid] = 0; return render(); }
  const pg = e.target.closest("[data-pg]"); if (pg) { const gid = D.grupos[passo - 1].id; pag[gid] = (pag[gid] || 0) + (+pg.dataset.pg); return ajustar(); }
  const b = e.target.closest(".card"); if (b) {
    const g = D.grupos.find(x => x.id === b.dataset.g), s = sel[g.id], id = b.dataset.i;
    if (s.has(id)) s.delete(id);
    else { if (g.unico || id === "sem") s.clear(); else s.delete("sem"); if (g.max && s.size >= g.max) return; s.add(id); }
    autoPasso[g.id] = false;
    const gr = $(".grid"), y = gr ? gr.scrollTop : 0; render(); if ($(".grid")) $(".grid").scrollTop = y; return;
  }
  const l = e.target.closest(".lang button"); if (l) { L = l.dataset.l; try { localStorage.setItem("ogab_menu_lang", L) } catch(e) {} render(); }
});
$("#bk").onclick = () => ir(auto ? 0 : passo - 1);
$("#pl").onclick = () => { const gid = D.grupos[passo - 1].id; sel[gid].clear(); autoPasso[gid] = true; ir(passo + 1); };
$("#go").onclick = async () => {
  if (passo >= 1 && passo <= N && !pronto(passo)) return;
  if (passo <= N) return ir(passo + 1);
  const esc_ = {}, deixou = []; D.grupos.forEach(g => { if (sel[g.id].size) esc_[g.id] = [...sel[g.id]]; else deixou.push(g.id); });
  const lt = D.grupos.find(g => g.id === "lettering"); if (esc_.lettering) esc_.lettering_templates = esc_.lettering.map(id => (lt.itens.find(x => x.id === id) || {}).template).filter(Boolean);
  const corpo = {modo: auto ? "auto" : "manual", lingua: L, escolhas: auto ? {} : esc_, gab_escolhe: auto ? D.grupos.map(g => g.id) : deixou, codigos: auto ? [] : codigos()};
  try {
    const r = await fetch("/escolha", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(corpo)}); if (!r.ok) throw 0;
    const arq = (await r.json()).arquivo;
    const msg = auto ? T[L].cab_auto : [T[L].cab + ":"].concat(D.grupos.map(g => {
      const its = g.itens.filter(i => sel[g.id].has(i.id)).map(i => (g.id === "formato" ? (g.abas.find(x => x.id === i.aba) || {nome: {}}).nome[L] + " " : "") + i.nome[L] + (i.proporcao ? ` (${i.proporcao})` : ""));
      return `- ${g.nome[L]}: ${its.length ? its.join(", ") : T[L].auto_l}`; })).join("\n");
    try { await navigator.clipboard.writeText(msg); } catch (e) {}
    $("#msgprev").textContent = msg; $("#kmod").textContent = /Mac|iPhone|iPad/.test(navigator.platform) ? "⌘" : "Ctrl";
    $("#copiar").onclick = async () => { try { await navigator.clipboard.writeText(msg); } catch (e) {} $("#copiar").textContent = T[L].copiado; setTimeout(() => $("#copiar").textContent = T[L].copiar, 1500); };
    $("#fim").style.display = "grid";
  } catch (e) { alert(T[L].erro); }
};
document.addEventListener("keydown", e => { if (e.key === "ArrowRight" && passo > 0 && passo <= N && pronto(passo)) ir(passo + 1); if (e.key === "ArrowLeft" && passo > 0) ir(auto ? 0 : passo - 1); });
render();
</script></body></html>"""


def porta_livre(p):
    if p:
        return p
    s = socket.socket(); s.bind(("127.0.0.1", 0)); n = s.getsockname()[1]; s.close(); return n


def main(a):
    if a and a[0] in ("-h", "--help"):
        raise SystemExit(__doc__)
    def arg(k, d=None):
        return a[a.index(k) + 1] if k in a else d
    pasta = arg("--pasta"); cliente = arg("--cliente"); formato = arg("--formato", "vertical")
    saida = os.path.abspath(os.path.join(pasta or os.getcwd(), "menu_escolha.json"))
    try:
        cfg = json.load(open(os.path.join(SKILL, "config.json"), encoding="utf-8"))
    except Exception:
        cfg = {}
    editor_nome, lettering = lettering_do_editor(arg("--editor", cfg.get("editor", "davinci")), cfg)
    dados = {"icones": ICONES, "grupos": grupos(formato, lettering, editor_nome), "ja_sabe": ja_sabe(cliente), "lingua": arg("--lingua"),
             "sugeridos": sugestoes(arg("--pedido"), arg("--roteiro"), formato, cliente, pasta)}
    html = PAGINA.replace("__DADOS__", json.dumps(dados, ensure_ascii=False).replace("</", "<\\/")).encode("utf-8")
    pronto = threading.Event()
    fontes = os.path.realpath(os.path.join(SKILL, "assets", "fontes", "InterTight"))
    presets = os.path.realpath(os.path.join(SKILL, "presets"))

    class H(BaseHTTPRequestHandler):
        def log_message(self, *x):
            pass

        def _envia(self, cod, corpo, tipo):
            self.send_response(cod); self.send_header("Content-Type", tipo); self.send_header("Content-Length", str(len(corpo)))
            self.send_header("Cache-Control", "no-store"); self.end_headers(); self.wfile.write(corpo)

        def _arquivo(self, base, rel):
            arq = os.path.realpath(os.path.join(base, rel)); ext = os.path.splitext(arq)[1].lower()
            if arq.startswith(base + os.sep) and ext in TIPOS and os.path.isfile(arq):
                return self._envia(200, open(arq, "rb").read(), TIPOS[ext])
            self._envia(404, b"nao achei", "text/plain")

        def do_GET(self):
            p = unquote(self.path.split("?")[0])
            if p in ("/", "/index.html"):
                return self._envia(200, html, "text/html; charset=utf-8")
            if p.startswith("/arquivo/biblioteca_motions_local/"):
                return self._arquivo(os.path.realpath(os.path.join(SKILL, "biblioteca_motions_local")), p[len("/arquivo/biblioteca_motions_local/"):])
            if p.startswith("/arquivo/presets/"):
                return self._arquivo(presets, p[len("/arquivo/presets/"):])
            if p.startswith("/fonte/"):
                return self._arquivo(fontes, p[len("/fonte/"):])
            self._envia(404, b"nao achei", "text/plain")

        def do_POST(self):
            if self.path != "/escolha":
                return self._envia(404, b"", "text/plain")
            try:
                d = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            except Exception:
                return self._envia(400, b"json invalido", "text/plain")
            d["salvo_em"] = time.strftime("%Y-%m-%d %H:%M"); d["cliente"] = cliente
            os.makedirs(os.path.dirname(saida), exist_ok=True)
            json.dump(d, open(saida, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            self._envia(200, json.dumps({"arquivo": saida}).encode(), "application/json"); pronto.set()
            if "--sem-voltar" not in a:   # traz o Claude para a frente (o Gab já é avisado porque o menu roda em segundo plano)
                try:
                    if sys.platform == "darwin":
                        subprocess.Popen(["open", "-a", "Claude"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    elif os.name == "nt":
                        subprocess.Popen(["powershell", "-NoProfile", "-Command",
                                          "(New-Object -ComObject WScript.Shell).AppActivate('Claude')"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except Exception:
                    pass

    porta = porta_livre(int(arg("--porta", 0)))
    srv = ThreadingHTTPServer(("127.0.0.1", porta), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{porta}/"
    print(f"menu aberto: {url}\nesperando a escolha (salva em {saida})", flush=True)
    if "--sem-abrir" not in a:
        webbrowser.open(url)
    ok = pronto.wait(float(arg("--timeout", 1800)))
    time.sleep(.4); srv.shutdown()
    if not ok:
        raise SystemExit("tempo esgotado sem escolha")
    d = json.load(open(saida, encoding="utf-8"))
    if d["modo"] == "auto":
        print("AUTOMÁTICO: o Gab escolhe tudo (estilo.md do cliente, memória da marca, escolher_preset.py)")
    else:
        for g, ids in d["escolhas"].items():
            print(f"  {g}: {', '.join(ids)}")
        if d["gab_escolhe"]:
            print("  o Gab escolhe: " + ", ".join(d["gab_escolhe"]))
    print(f"salvo: {saida}")


if __name__ == "__main__":
    main(sys.argv[1:])
