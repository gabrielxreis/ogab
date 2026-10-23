#!/usr/bin/env python3
"""/ogab menu: painel local (PT/EN) para a pessoa escolher o que vai no vídeo antes de criar, ou deixar no automático.

  python3 menu.py [--pasta <pasta do vídeo>] [--cliente <empresa>] [--pedido "texto"] [--roteiro roteiro.txt]
                  [--formato vertical|horizontal] [--editor davinci|premiere|capcut|finalcut|nenhum] [--lingua pt|en] [--porta 0] [--sem-abrir] [--timeout 1800]

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


def grupos(formato, lettering, editor_nome="DaVinci"):
    """lettering = [(id_template, nome visível)] do editor da pessoa (lettering_do_editor)."""
    C = catalogo()
    presets = [p for p in C["presets"] if p["id"] not in FORA_DO_MENU]
    est = [it(p["id"], p["nome"], p["nome"].replace(" (CENA)", " (SCENE)"), p["resumo"], PRESET_EN.get(p["id"], p["resumo"]),
              gif=p.get("gif") or None, extra={"cat": p["categoria"], "catn": {"pt": C["categorias"].get(p["categoria"], ""),
              "en": CAT_EN.get(p["categoria"], "")}, "formato": p.get("formato") or []}) for p in presets]
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
        {"id": "estilo", "letra": "E", "unico": False, "max": 3, "nome": {"pt": "Estilo dos motions (presets)", "en": "Motion style (presets)"},
         "sub": {"pt": "Como os motions vão parecer. Até 3; eles se misturam trecho a trecho.", "en": "How the motion graphics will look. Up to 3; they mix section by section."},
         "itens": est},
        {"id": "legenda", "letra": "L", "unico": True, "nome": {"pt": "Legenda", "en": "Captions"},
         "sub": {"pt": "Como a fala aparece. Nunca em cima do rosto.", "en": "How the words show up. Never over the face."},
         "abas": [{"id": "editor", "nome": {"pt": f"No editor ({editor_nome})", "en": f"In the editor ({editor_nome})"}},
                  {"id": "animada", "nome": {"pt": "Animada (motion)", "en": "Animated (motion)"}}],
         "itens": [
            it("gab_usa", "GAB USA (padrão)", "GAB USA (default)", f"Legenda nativa do {editor_nome} com o seu preset: editável na trilha de legenda, uma linha, do primeiro ao último segundo.",
               f"Native {editor_nome} subtitles with your preset: editable on the subtitle track, one line, first to last second.", "cap-gab", extra={"aba": "editor"}),
            it("editor_padrao", f"Legenda padrão do {editor_nome}", f"Default {editor_nome} subtitles", "Create Subtitles from Audio sem estilo extra, para você ajustar no editor.",
               "Create Subtitles from Audio with no extra style, for you to tweak in the editor.", "cap-plain", extra={"aba": "editor"}),
            it("sem", "Sem legenda", "No captions", "Quadro limpo, só títulos e gráficos.", "Clean frame, only titles and graphics.", "none", extra={"aba": "editor"}),
            it("destaque", "Destaque palavra por palavra", "Word-by-word highlight", "Palavra-chave grande amarela ou em serifa (render em motion).", "Big yellow or serif keyword (rendered as motion).", "cap-hl", extra={"aba": "animada"}),
            it("serif_azul", "Serif azul", "Blue serif", "Sans com a palavra-chave em serifada itálica azul.", "Sans with the keyword in blue serif italic.", "cap-serif", extra={"aba": "animada"}),
            it("lume", "Lume (duas camadas)", "Lume (two layers)", "Linha fina + palavra que brilha em amarelo.", "Thin line + a word that glows yellow.", "cap-lume", extra={"aba": "animada"}),
            it("podcast", "Cor por quem fala", "Colour per speaker", "Para podcast e entrevista com duas pessoas.", "For podcasts and two-person interviews.", "cap-pod", extra={"aba": "animada"})]},
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
         "sub": {"pt": "O clima da trilha (instrumental, entra bruta na timeline).", "en": "The mood of the track (instrumental, placed raw on the timeline)."}, "itens": [
            it("emotiva", "Emotiva (padrão)", "Emotional (default)", "Faz sonhar, sobe no CTA.", "Dreamy, lifts at the CTA.", "bars m1"),
            it("epica", "Épica", "Epic", "Grande, cinematográfica.", "Big, cinematic.", "bars m2"),
            it("tensa", "Tensa / suspense", "Tense / suspense", "Para história e revelação.", "For story and reveals.", "bars m3"),
            it("alegre", "Alegre", "Upbeat", "Leve e animada.", "Light and lively.", "bars m4"),
            it("corporativa", "Corporativa", "Corporate", "Limpa, para marca e serviço.", "Clean, for brand and service.", "bars m5"),
            it("calma", "Calma / lo-fi", "Calm / lo-fi", "Baixinha, para conteúdo explicativo.", "Low, for explainer content.", "bars m6"),
            it("sem", "Sem música", "No music", "Só voz e efeitos.", "Voice and effects only.", "none")]},
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
            it("pb", "Preto e branco", "Black and white", "Neutro, com contraste.", "Neutral, with contrast.", "col c3")]},
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
.wrap{max-width:1180px;margin:0 auto;padding:0 24px}
header{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:30px 0 6px}
.logo{display:flex;align-items:center;gap:14px}.logo svg{width:44px;height:44px;border-radius:12px;box-shadow:0 0 20px rgba(43,255,136,.45)}
.wm{font-weight:800;font-size:22px;letter-spacing:-.03em;line-height:1.1}.wm .s{color:var(--g)}.wm small{display:block;font-size:12px;color:var(--mu);letter-spacing:0;font-weight:500}
.lang{display:flex;background:rgba(255,255,255,.06);border-radius:999px;padding:3px}
.lang button{background:none;border:0;color:var(--mu);font:800 12px "Inter Tight";padding:7px 14px;border-radius:999px;cursor:pointer;letter-spacing:.04em}
.lang button[aria-pressed=true]{background:var(--grad);color:var(--ink);box-shadow:0 0 10px rgba(43,255,136,.5)}
h1{font-weight:800;font-size:clamp(28px,4vw,42px);letter-spacing:-.035em;line-height:1.08;margin:24px 0 8px}
.lead{color:var(--mu);max-width:720px}
.fim{position:fixed;inset:0;background:rgba(4,8,5,.92);display:none;place-items:center;z-index:20;text-align:center}.fim div{max-width:460px;padding:24px}.fim b{font-size:30px;font-weight:800;letter-spacing:-.03em;display:block;margin:14px 0 6px;background:var(--grad);-webkit-background-clip:text;color:transparent}
.sabe{margin:16px 0 4px;padding:16px;border-radius:16px;background:var(--card);backdrop-filter:blur(14px);border:1px solid var(--line);font-size:14px;text-align:left}.sabe b{font:800 10.5px "Inter Tight";letter-spacing:.12em;text-transform:uppercase;color:var(--mu);display:block;margin-bottom:6px}.sabe li{color:var(--mu);margin-left:18px}
.prog{display:flex;gap:5px;margin:20px 0 0;padding:3px;border-radius:999px;background:rgba(255,255,255,.06)}.prog i{flex:1;height:6px;border-radius:9px;background:transparent}.prog i.on{background:var(--grad);box-shadow:0 0 8px rgba(43,255,136,.5)}
.passo{font:800 10.5px "Inter Tight";color:var(--mu);letter-spacing:.12em;text-transform:uppercase;margin-top:18px}
h2{font-weight:800;font-size:clamp(24px,3.2vw,34px);letter-spacing:-.03em;line-height:1.1;margin:4px 0 4px;display:flex;align-items:center;gap:10px;flex-wrap:wrap}
h2 .k{color:var(--ink);background:var(--grad);border-radius:12px;width:40px;height:40px;display:grid;place-items:center;font-size:18px;box-shadow:0 0 14px rgba(43,255,136,.45)}
.sub{color:var(--mu);font-size:14.5px;margin-bottom:16px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(168px,1fr));gap:12px;max-height:calc(100vh - 330px);overflow-y:auto;padding:2px 2px 8px;scrollbar-width:thin}
.card{position:relative;background:var(--card);backdrop-filter:blur(14px);border:1px solid var(--line);border-radius:16px;overflow:hidden;cursor:pointer;transition:transform .15s,border-color .15s;text-align:left;color:inherit;font:inherit;padding:0}
.card:hover{transform:translateY(-2px);border-color:rgba(43,255,136,.4)}
.card[aria-pressed=true]{border-color:rgba(43,255,136,.55);box-shadow:0 0 18px rgba(43,255,136,.35)}
.vis{aspect-ratio:4/5;background:#050806;position:relative;overflow:hidden;display:grid;place-items:center}
.vis img{width:100%;height:100%;object-fit:cover;display:block}
.chk{position:absolute;top:9px;right:9px;width:26px;height:26px;border-radius:50%;border:2px solid rgba(255,255,255,.7);background:rgba(0,0,0,.35);display:grid;place-items:center;z-index:2}
.card[aria-pressed=true] .chk{background:var(--g);border-color:var(--g)}
.chk svg{width:14px;height:14px;opacity:0}.card[aria-pressed=true] .chk svg{opacity:1}
.code{position:absolute;top:10px;left:10px;font:800 11px "Inter Tight";background:rgba(0,0,0,.55);border:1px solid var(--line);color:var(--g1);padding:2px 7px;border-radius:7px;z-index:2}
.tag{position:absolute;bottom:9px;left:9px;font:800 10.5px "Inter Tight";letter-spacing:.06em;text-transform:uppercase;background:rgba(43,255,136,.14);border:1px solid rgba(43,255,136,.3);color:var(--g);padding:3px 9px;border-radius:999px;z-index:2;backdrop-filter:blur(6px)}
.tx{padding:11px 12px 13px}.tx b{font-weight:800;font-size:15px;letter-spacing:-.015em;display:block}.tx span{color:var(--mu);font-size:12.5px;display:block;margin-top:3px}
.inicio{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:22px}
.op{border:1px solid var(--line);border-radius:16px;padding:16px;background:var(--card);backdrop-filter:blur(14px);cursor:pointer;color:inherit;font:inherit;text-align:left;transition:.15s}
.op:hover{border-color:rgba(43,255,136,.55);box-shadow:0 0 18px rgba(43,255,136,.3);transform:translateY(-2px)}.op b{display:block;font-weight:800;font-size:22px;letter-spacing:-.025em;margin:12px 0 6px}.op p{color:var(--mu);font-size:14px}
.op .ic{width:100%;aspect-ratio:16/9;border-radius:12px;overflow:hidden;border:1px solid var(--line)}
.resumo{display:grid;gap:8px;margin-top:10px;max-height:calc(100vh - 330px);overflow:auto}.resumo div{display:flex;gap:12px;padding:12px 16px;border-radius:12px;background:var(--card);backdrop-filter:blur(14px);border:1px solid var(--line)}
.resumo b{min-width:200px;font:800 10.5px "Inter Tight";letter-spacing:.12em;text-transform:uppercase;color:var(--mu);padding-top:3px}.resumo span{color:var(--mu)}.resumo .ok{color:var(--tx)}
.barra{position:fixed;left:0;right:0;bottom:0;background:rgba(5,8,6,.8);backdrop-filter:blur(14px);border-top:1px solid var(--line);z-index:9}
.barra .wrap{display:flex;align-items:center;gap:10px;padding:14px 20px}.barra .codes{flex:1;min-width:0;overflow-x:auto;white-space:nowrap;font:800 13px "Inter Tight";color:var(--g1);scrollbar-width:none}
.barra button{border:0;font:800 13px "Inter Tight";cursor:pointer;border-radius:10px;padding:0 16px;height:42px}
.go{background:var(--grad);color:var(--ink);border-radius:12px!important;min-width:170px;letter-spacing:.08em;text-transform:uppercase;animation:respira 1.6s ease-in-out infinite alternate}
@keyframes respira{from{box-shadow:0 0 6px rgba(43,255,136,.25);transform:scale(1)}to{box-shadow:0 0 16px rgba(43,255,136,.7);transform:scale(1.015)}}
.bk{background:rgba(255,255,255,.08);color:var(--tx);border:1px solid var(--line)!important}.pl{background:rgba(245,181,68,.12);color:var(--amb);border:1px solid rgba(245,181,68,.3)!important;border-radius:999px!important}
.barra button[hidden]{display:none}
.fim{position:fixed;inset:0;background:rgba(4,8,5,.92);display:none;place-items:center;z-index:20;text-align:center}.fim div{max-width:460px;padding:24px}.fim b{font-size:26px;font-weight:800;letter-spacing:-.03em;display:block;margin:14px 0 6px}
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
<div class="fim" id="fim"><div><b data-t="fim_t"></b><p data-t="fim_p" style="color:var(--mu)"></p></div></div>
<script>
const D = __DADOS__;
const T = {
 pt:{menu:"Menu do vídeo",ola:"Como você quer montar este vídeo?",ola_p:"Escolha passo a passo o que entra no vídeo, ou deixe tudo com o Gab.",
  auto_t:"Automático",auto_p:"O Gab escolhe tudo pelo que já sabe de você e da marca (estilo, memória da marca, pedidos anteriores) e pelo roteiro.",
  eu_t:"Eu escolho",eu_p:"Passo a passo: formato, estilo, legenda, lettering, motion, b-roll, música, efeitos, ritmo, cor e extras.",
  sabe:"O que o Gab já sabe dessa marca",gab_escolhe:"automático",sug:"sugerido",passo:(i,n)=>`Passo ${i} de ${n}`,
  voltar:"Voltar",pular:"Automático neste passo",avancar:"Avançar",revisar:"Revisar",confirmar:"Confirmar",conf_auto:"Confirmar: automático",
  resumo_t:"Confere antes de mandar",resumo_p:"Clique num item para voltar e mudar.",auto_resumo:"O Gab vai escolher tudo pelo que já sabe de você e da marca.",
  max:n=>`até ${n}`,fim_t:"Pronto!",fim_p:"Pode voltar para o Claude: o Gab já recebeu as suas escolhas.",erro:"Não consegui salvar. O Gab ainda está aberto?"},
 en:{menu:"Video menu",ola:"How do you want to build this video?",ola_p:"Pick step by step what goes in, or leave it all to Gab.",
  auto_t:"Automatic",auto_p:"Gab picks everything from what he already knows about you and the brand (style, brand memory, past requests) and the script.",
  eu_t:"I'll choose",eu_p:"Step by step: format, style, captions, lettering, motion, b-roll, music, effects, pace, colour and extras.",
  sabe:"What Gab already knows about this brand",gab_escolhe:"automatic",sug:"suggested",passo:(i,n)=>`Step ${i} of ${n}`,
  voltar:"Back",pular:"Automatic for this step",avancar:"Next",revisar:"Review",confirmar:"Confirm",conf_auto:"Confirm: automatic",
  resumo_t:"Check before sending",resumo_p:"Click an item to go back and change it.",auto_resumo:"Gab will pick everything from what he knows about you and the brand.",
  max:n=>`up to ${n}`,fim_t:"Done!",fim_p:"Go back to Claude: Gab already has your choices.",erro:"Couldn't save. Is Gab still open?"}};
let L = D.lingua || ((navigator.language||"pt").toLowerCase().startsWith("pt") ? "pt" : "en");
try { L = localStorage.getItem("ogab_menu_lang") || L } catch(e) {}
const sel = {}; D.grupos.forEach(g => sel[g.id] = new Set());
const N = D.grupos.length; let passo = 0, auto = false; const aba = {};
D.grupos.forEach(g => { if (g.abas) aba[g.id] = g.abas[0].id; });   // 0 = início, 1..N = grupos, N+1 = resumo
const $ = s => document.querySelector(s), esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
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
  if (a.startsWith("bars")) { const d = {m1:"1.3s",m2:".9s",m3:"1.8s",m4:".5s",m5:"1s",m6:"2.2s"}[a.split(" ")[1]]; return `<div class="an"><div class="bars" style="--d:${d}">${"<span></span>".repeat(9)}</div></div>`; }
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
      <p class="sub">${esc(g.sub[L])}${g.max ? " · " + T[L].max(g.max) : ""}${sel[g.id].size ? "" : " · <b style='color:var(--g)'>" + T[L].gab_escolhe + "</b>"}</p>
      ${g.abas ? `<div class="abas">${g.abas.map(x => { const c = g.itens.filter(i => i.aba === x.id && sel[g.id].has(i.id)).length;
        return `<button data-aba="${x.id}" aria-pressed="${aba[g.id] === x.id}">${esc(x.nome[L])}${c ? `<span class="n">${c}</span>` : ""}</button>`; }).join("")}</div>` : ""}
      <div class="grid">${g.itens.map((i, n) => (g.abas && i.aba !== aba[g.id]) ? "" : `<button class="card" data-g="${g.id}" data-i="${esc(i.id)}" aria-pressed="${sel[g.id].has(i.id)}">
      <div class="vis">${prev(i)}<span class="code">${g.letra}${n + 1}</span><span class="chk">${CHK}</span>${D.sugeridos.includes(i.id) && g.id === "estilo" ? `<span class="tag">${T[L].sug}</span>` : ""}</div>
      <div class="tx"><b>${esc(i.nome[L])}</b><span>${esc(i.desc[L])}</span></div></button>`).join("")}</div>`;
  } else {
    h = `<h2>${T[L].resumo_t}</h2>` + (auto ? `<p class="sub">${T[L].auto_resumo}</p>${sabe}` :
      `<p class="sub">${T[L].resumo_p}</p><div class="resumo">${D.grupos.map((g, k) => `<div data-ir="${k + 1}" style="cursor:pointer"><b>${g.letra} · ${esc(g.nome[L])}</b>
      <span class="${sel[g.id].size ? "ok" : ""}">${sel[g.id].size ? g.itens.filter(i => sel[g.id].has(i.id)).map(i => esc(i.nome[L])).join(", ") : T[L].gab_escolhe}</span></div>`).join("")}</div>`);
  }
  $("#tela").innerHTML = h;
  $("#bk").hidden = passo === 0; $("#pl").hidden = !(passo >= 1 && passo <= N); $("#go").hidden = passo === 0;
  $("#go").textContent = passo > N ? (auto ? T[L].conf_auto : T[L].confirmar) : (passo === N ? T[L].revisar : T[L].avancar);
  $("#codes").textContent = auto ? T[L].auto_t : codigos().join("  ");
  scrollTo(0, 0);
}
function pula(p) { const g = D.grupos[p - 1]; return g && g.id === "estilo" && sel.motions && sel.motions.has("sem"); }
function ir(p) { const dir = p >= passo ? 1 : -1; while (p >= 1 && p <= N && pula(p)) p += dir; passo = Math.max(0, Math.min(N + 1, p)); render(); }
document.addEventListener("click", e => {
  const op = e.target.closest(".op"); if (op) { auto = op.dataset.op === "auto"; return ir(auto ? N + 1 : 1); }
  const r = e.target.closest("[data-ir]"); if (r) return ir(+r.dataset.ir);
  const ab = e.target.closest("[data-aba]"); if (ab) { aba[D.grupos[passo - 1].id] = ab.dataset.aba; return render(); }
  const b = e.target.closest(".card"); if (b) {
    const g = D.grupos.find(x => x.id === b.dataset.g), s = sel[g.id], id = b.dataset.i;
    if (s.has(id)) s.delete(id);
    else { if (g.unico || id === "sem") s.clear(); else s.delete("sem"); if (g.max && s.size >= g.max) return; s.add(id); }
    const gr = $(".grid"), y = gr ? gr.scrollTop : 0; render(); if ($(".grid")) $(".grid").scrollTop = y; return;
  }
  const l = e.target.closest(".lang button"); if (l) { L = l.dataset.l; try { localStorage.setItem("ogab_menu_lang", L) } catch(e) {} render(); }
});
$("#bk").onclick = () => ir(auto ? 0 : passo - 1);
$("#pl").onclick = () => { sel[D.grupos[passo - 1].id].clear(); ir(passo + 1); };
$("#go").onclick = async () => {
  if (passo <= N) return ir(passo + 1);
  const esc_ = {}, deixou = []; D.grupos.forEach(g => { if (sel[g.id].size) esc_[g.id] = [...sel[g.id]]; else deixou.push(g.id); });
  const lt = D.grupos.find(g => g.id === "lettering"); if (esc_.lettering) esc_.lettering_templates = esc_.lettering.map(id => (lt.itens.find(x => x.id === id) || {}).template).filter(Boolean);
  const corpo = {modo: auto ? "auto" : "manual", lingua: L, escolhas: auto ? {} : esc_, gab_escolhe: auto ? D.grupos.map(g => g.id) : deixou, codigos: auto ? [] : codigos()};
  try { const r = await fetch("/escolha", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(corpo)}); if (!r.ok) throw 0; $("#fim").style.display = "grid"; }
  catch (e) { alert(T[L].erro); }
};
document.addEventListener("keydown", e => { if (e.key === "ArrowRight" && passo > 0 && passo <= N) ir(passo + 1); if (e.key === "ArrowLeft" && passo > 0) ir(auto ? 0 : passo - 1); });
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
    dados = {"grupos": grupos(formato, lettering, editor_nome), "ja_sabe": ja_sabe(cliente), "lingua": arg("--lingua"),
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
            self._envia(200, b"ok", "text/plain"); pronto.set()

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
