"""The signal vocabulary Mariana proposes, and the user confirms.

Mariana never decides on its own what makes a good prospect. It proposes a
catalog of signals it knows how to collect — each with a plain-language
description, what it costs, and why it might matter — and the user confirms,
edits, or rejects them in the dashboard before any collection runs.

Only ``confirmed`` signals get collected. That keeps spend intentional and
keeps the resulting cohorts explainable: a prospect list is a query over
signals a human chose, not a black box.

Design note: every signal is recorded as an OBSERVATION (a row), never a
column. A new signal needs no migration, history comes free, and confidence
and provenance travel with the fact.
"""

# category: discovery | profile | people | verification
# value_type: num | text | bool
# cost_note: what collecting it actually costs, in plain language
SIGNAL_CATALOG: list[dict] = [
    # ── Discovery: who exists, and how visible are they ──
    {
        "code": "SERP_RANK",
        "label": "Search rank position",
        "description": (
            "Where the business ranks for its core '<service> <city>' search. "
            "The most useful prospecting signal there is: positions 11-30 are "
            "the sweet spot — visible enough to be trying, not winning yet. "
            "Top 10 are already winning (harder sell); 31+ are cheaper but "
            "less motivated."
        ),
        "category": "discovery",
        "value_type": "num",
        "collector": "discover",
        "cost_note": "~$0.0006 per search (paid SERP API, queued endpoint)",
        "confidence_floor": 0.0,
    },
    {
        "code": "FOUND_IN_SERP",
        "label": "Discovered via search",
        "description": "The business appeared in a target-market search — how Mariana found it at all.",
        "category": "discovery",
        "value_type": "text",
        "collector": "discover",
        "cost_note": "included in the search above",
        "confidence_floor": 0.0,
    },

    {
        "code": "NO_WEBSITE",
        "label": "No website at all",
        "description": (
            "The business has a listing and a phone number but no site. If you "
            "sell websites this is the highest-intent signal that exists — and "
            "it is a filter you can query for directly, not something you infer."
        ),
        "category": "discovery",
        "value_type": "bool",
        "collector": "discover",
        "cost_note": "included in the business listing lookup",
        "confidence_floor": 0.0,
    },
    {
        "code": "UNCLAIMED_LISTING",
        "label": "Unclaimed Google listing",
        "description": (
            "Nobody has claimed their Google Business Profile, so they are not "
            "managing how they show up locally. Strong signal for anyone "
            "selling local marketing."
        ),
        "category": "discovery",
        "value_type": "bool",
        "collector": "discover",
        "cost_note": "included in the business listing lookup",
        "confidence_floor": 0.0,
    },
    {
        "code": "REVIEW_RATING",
        "label": "Review rating",
        "description": (
            "Their average star rating. Useful in both directions: a low "
            "rating is a reputation problem to solve, a high one with few "
            "reviews is proof they are good but invisible."
        ),
        "category": "discovery",
        "value_type": "num",
        "collector": "discover",
        "cost_note": "included in the business listing lookup",
        "confidence_floor": 0.0,
    },
    {
        "code": "REVIEW_COUNT",
        "label": "Number of reviews",
        "description": (
            "How many reviews they have. A rough proxy for size and for how "
            "much attention they pay to their online presence."
        ),
        "category": "discovery",
        "value_type": "num",
        "collector": "discover",
        "cost_note": "included in the business listing lookup",
        "confidence_floor": 0.0,
    },

    # ── Profile: what they are (free — HTML Mariana already fetches) ──
    {
        "code": "INCUMBENT_AGENCY",
        "label": "Has a marketing/web agency",
        "description": (
            "An agency credited in the site footer ('Website by X'). High-value: "
            "it tells you who you're displacing, and every detection builds a "
            "roster you can target as a whole book of business. Only recorded "
            "when the credit wording is explicit — a wrong incumbent is worse "
            "than none."
        ),
        "category": "profile",
        "value_type": "text",
        "collector": "profile",
        "cost_note": "free (homepage HTML)",
        "confidence_floor": 0.75,
    },
    {
        "code": "RUNNING_GOOGLE_ADS",
        "label": "Running Google Ads",
        "description": "Google Ads tag on the site — they are spending on acquisition TODAY. Strong budget signal.",
        "category": "profile",
        "value_type": "bool",
        "collector": "profile",
        "cost_note": "free (homepage HTML)",
        "confidence_floor": 0.0,
    },
    {
        "code": "RUNNING_META_ADS",
        "label": "Running Meta/Facebook Ads",
        "description": "Meta Pixel on the site — actively spending on paid social.",
        "category": "profile",
        "value_type": "bool",
        "collector": "profile",
        "cost_note": "free (homepage HTML)",
        "confidence_floor": 0.0,
    },
    {
        "code": "TECH_STACK",
        "label": "Website platform / tools",
        "description": "What the site is built on and which tools it runs (WordPress, Shopify, HubSpot, chat widgets, booking tools).",
        "category": "profile",
        "value_type": "text",
        "collector": "profile",
        "cost_note": "free (homepage HTML)",
        "confidence_floor": 0.0,
    },
    {
        "code": "NO_SCHEMA_MARKUP",
        "label": "Missing structured data",
        "description": "No JSON-LD schema markup — a concrete, checkable SEO gap you can name in an email.",
        "category": "profile",
        "value_type": "bool",
        "collector": "profile",
        "cost_note": "free (homepage HTML)",
        "confidence_floor": 0.0,
    },
    {
        "code": "NO_ONLINE_BOOKING",
        "label": "No online booking/scheduling",
        "description": "No booking or scheduling widget detected — leads have to phone in, so after-hours demand is lost.",
        "category": "profile",
        "value_type": "bool",
        "collector": "profile",
        "cost_note": "free (homepage HTML)",
        "confidence_floor": 0.0,
    },
    {
        "code": "SITE_PAGE_COUNT",
        "label": "Site size",
        "description": "Page count from sitemap.xml. A very thin site suggests little investment; a large stale one suggests neglect.",
        "category": "profile",
        "value_type": "num",
        "collector": "profile",
        "cost_note": "free (sitemap.xml)",
        "confidence_floor": 0.0,
    },
    {
        "code": "BLOG_STALE",
        "label": "Content gone stale",
        "description": "No new content in a long time — content marketing started and abandoned.",
        "category": "profile",
        "value_type": "num",
        "collector": "profile",
        "cost_note": "free (sitemap.xml)",
        "confidence_floor": 0.0,
    },
    {
        "code": "BLOCKS_AI_CRAWLERS",
        "label": "Blocks AI crawlers",
        "description": "robots.txt blocks AI crawlers — they'll be invisible in AI search answers.",
        "category": "profile",
        "value_type": "bool",
        "collector": "profile",
        "cost_note": "free (robots.txt)",
        "confidence_floor": 0.0,
    },
    {
        "code": "HIRING_ROLE",
        "label": "Hiring for a relevant role",
        "description": "An open role on their careers page that implies they're buying in your category right now.",
        "category": "profile",
        "value_type": "text",
        "collector": "profile",
        "cost_note": "free (careers page)",
        "confidence_floor": 0.0,
    },

    # ── People: who decides ──
    {
        "code": "CONTACT_FOUND",
        "label": "Named contact found",
        "description": "A named person scraped from the team/about page, with their title.",
        "category": "people",
        "value_type": "text",
        "collector": "people",
        "cost_note": "free (team page)",
        "confidence_floor": 0.0,
    },
    {
        "code": "DECISION_MAKER_TITLE",
        "label": "Decision-maker title",
        "description": "Title matches an owner/decision-maker pattern (Owner, President, Practice Manager, Marketing Director).",
        "category": "people",
        "value_type": "text",
        "collector": "people",
        "cost_note": "free (team page)",
        "confidence_floor": 0.0,
    },
    {
        "code": "REGISTRY_VERIFIED",
        "label": "Confirmed in a public registry",
        "description": (
            "The person was confirmed in an authoritative public registry "
            "(licensing board, professional registry). Also filters out "
            "scraping artifacts — a name that matches nothing usually wasn't a person."
        ),
        "category": "people",
        "value_type": "text",
        "collector": "people",
        "cost_note": "free (public registry API)",
        "confidence_floor": 0.0,
    },
    {
        "code": "LIKELY_OWNER",
        "label": "Likely the owner",
        "description": "Registry indicators suggest this person owns the business rather than working there.",
        "category": "people",
        "value_type": "bool",
        "collector": "people",
        "cost_note": "free (public registry API)",
        "confidence_floor": 0.0,
    },

    # ── Verification ──
    {
        "code": "EMAIL_PATTERN",
        "label": "Company email pattern",
        "description": "The domain's address format (first.last@, flast@). One real address cracks the whole company.",
        "category": "verification",
        "value_type": "text",
        "collector": "verify",
        "cost_note": "free, or ~1 lookup credit",
        "confidence_floor": 0.0,
    },
    {
        "code": "EMAIL_STATUS",
        "label": "Email deliverability",
        "description": "Whether the address is verified, catch-all/risky, an unverified guess, or invalid.",
        "category": "verification",
        "value_type": "text",
        "collector": "verify",
        "cost_note": "1 verification credit (free tiers available)",
        "confidence_floor": 0.0,
    },
    # ── Audiovisual (Mariana): does this business already use video? ──
    {
        "code": "NO_VIDEO_ON_SITE",
        "label": "No video on the website",
        "description": (
            "The homepage has no embedded video at all (no YouTube, Vimeo or "
            "<video> player). For a filmmaker or editor this is the clearest "
            "gap there is: a business that sells something visual and shows "
            "it with stills only."
        ),
        "category": "profile",
        "value_type": "bool",
        "collector": "profile",
        "cost_note": "free (homepage HTML)",
        "confidence_floor": 0.0,
    },
    {
        "code": "HAS_YOUTUBE_CHANNEL",
        "label": "Links a YouTube channel",
        "description": (
            "The site links to a YouTube channel. They already believe in "
            "video, so the angle is quality, consistency or editing volume, "
            "not convincing them video matters."
        ),
        "category": "profile",
        "value_type": "text",
        "collector": "profile",
        "cost_note": "free (homepage HTML)",
        "confidence_floor": 0.0,
    },
    {
        "code": "INSTAGRAM_PROFILE",
        "label": "Instagram profile",
        "description": (
            "The business's Instagram, linked from its site. Where short-form "
            "video (Reels) lives, and a channel to reach them by DM when "
            "there is no email."
        ),
        "category": "profile",
        "value_type": "text",
        "collector": "profile",
        "cost_note": "free (homepage HTML)",
        "confidence_floor": 0.0,
    },
    {
        "code": "LINKEDIN_COMPANY",
        "label": "LinkedIn company page",
        "description": (
            "The company's LinkedIn page, linked from its site. Used to reach "
            "decision makers abroad, where LinkedIn is the normal channel "
            "for business outreach."
        ),
        "category": "profile",
        "value_type": "text",
        "collector": "profile",
        "cost_note": "free (homepage HTML)",
        "confidence_floor": 0.0,
    },
    {
        "code": "CONTACT_FORM_URL",
        "label": "Contact form available",
        "description": (
            "A contact form on the site. Worth knowing because it reaches the "
            "business without needing an email address at all — and roughly "
            "half of domains can't be email-verified."
        ),
        "category": "verification",
        "value_type": "text",
        "collector": "profile",
        "cost_note": "free (site HTML)",
        "confidence_floor": 0.0,
    },

    # ── Timing: the right moment to reach out (Mariana, `mariana linkedin momento`) ──
    {
        "code": "EVENT_ANNOUNCED",
        "label": "Event announced",
        "description": "They announced an event (conference, launch, show) in the coming months.",
        "category": "profile",
        "value_type": "text",
        "collector": "momento",
        "cost_note": "1 Serper search per lead",
        "confidence_floor": 0.0,
    },
    {
        "code": "NEW_ROLE",
        "label": "New marketing role",
        "description": "The contact recently started a new marketing or communications role.",
        "category": "profile",
        "value_type": "text",
        "collector": "momento",
        "cost_note": "1 Serper search per lead",
        "confidence_floor": 0.0,
    },
]


# Textos em português do Brasil mostrados no painel e no terminal. Os códigos
# (SERP_RANK, NO_VIDEO_ON_SITE...) não mudam: são a chave interna.
_PT_BR = {
    "SERP_RANK": ("Posição na busca",
        "Onde a empresa aparece na busca do próprio serviço ('<serviço> <cidade>'). "
        "Posições 11 a 30 são o ponto ideal: visíveis o bastante para estarem "
        "tentando, sem estar ganhando ainda. Top 10 já ganha (venda mais difícil); "
        "31+ é mais barato, mas menos motivado.",
        "~US$ 0,0006 por busca (API de busca paga)"),
    "FOUND_IN_SERP": ("Encontrada pela busca",
        "A empresa apareceu numa busca do mercado-alvo: foi assim que a Mariana a achou.",
        "incluído na busca acima"),
    "NO_WEBSITE": ("Sem site",
        "Tem cadastro e telefone, mas não tem site. Dá para filtrar direto, sem adivinhar.",
        "incluído na consulta de empresas"),
    "UNCLAIMED_LISTING": ("Perfil do Google não reivindicado",
        "Ninguém reivindicou o Perfil da Empresa no Google: não cuidam de como aparecem localmente.",
        "incluído na consulta de empresas"),
    "REVIEW_RATING": ("Nota das avaliações",
        "A média de estrelas. Serve para os dois lados: nota baixa é problema de "
        "reputação; nota alta com poucas avaliações é prova de que são bons, mas invisíveis.",
        "incluído na consulta de empresas"),
    "REVIEW_COUNT": ("Número de avaliações",
        "Quantas avaliações têm. Indica tamanho e o quanto cuidam da presença online.",
        "incluído na consulta de empresas"),
    "INCUMBENT_AGENCY": ("Tem agência de marketing/site",
        "Agência creditada no rodapé do site ('Site por X'). Diz quem já atende a conta. "
        "Só é registrado quando o crédito é explícito: agência errada é pior que nenhuma.",
        "grátis (página inicial)"),
    "RUNNING_GOOGLE_ADS": ("Anunciando no Google",
        "Tag do Google Ads no site: estão gastando com aquisição HOJE. Sinal forte de verba "
        "e de que precisam de criativo.",
        "grátis (página inicial)"),
    "RUNNING_META_ADS": ("Anunciando no Instagram/Facebook",
        "Pixel da Meta no site: anunciam nas redes. Precisam renovar vídeo de anúncio com frequência.",
        "grátis (página inicial)"),
    "TECH_STACK": ("Plataforma e ferramentas do site",
        "Em que o site é feito e que ferramentas usa (WordPress, Shopify, chat, agendamento).",
        "grátis (página inicial)"),
    "NO_SCHEMA_MARKUP": ("Sem dados estruturados",
        "Sem marcação JSON-LD: uma lacuna de SEO concreta e verificável.",
        "grátis (página inicial)"),
    "NO_ONLINE_BOOKING": ("Sem agendamento online",
        "Nenhum agendamento no site: o cliente precisa ligar. Um vídeo do atendimento ajuda quem está em dúvida.",
        "grátis (página inicial)"),
    "SITE_PAGE_COUNT": ("Tamanho do site",
        "Número de páginas do sitemap.xml. Site muito magro indica pouco investimento; "
        "grande e parado indica abandono.",
        "grátis (sitemap.xml)"),
    "BLOG_STALE": ("Conteúdo parado",
        "Nada novo há muito tempo: começaram a produzir conteúdo e pararam.",
        "grátis (sitemap.xml)"),
    "BLOCKS_AI_CRAWLERS": ("Bloqueia robôs de IA",
        "O robots.txt bloqueia robôs de IA: não vão aparecer nas respostas de buscas com IA.",
        "grátis (robots.txt)"),
    "HIRING_ROLE": ("Contratando para uma função relevante",
        "Vaga aberta (social media, editor de vídeo, videomaker, marketing) que indica "
        "necessidade agora.",
        "grátis (página de vagas)"),
    "CONTACT_FOUND": ("Contato com nome",
        "Uma pessoa com nome e cargo, tirada da página de equipe.",
        "grátis (página de equipe)"),
    "DECISION_MAKER_TITLE": ("Cargo de quem decide",
        "O cargo bate com dono/decisor (dono, fundador, diretor, pastor, diretor de marketing).",
        "grátis (página de equipe)"),
    "REGISTRY_VERIFIED": ("Confirmado em registro público",
        "A pessoa foi confirmada num registro público oficial. Também filtra erros de "
        "leitura: um nome que não bate com nada geralmente não era uma pessoa.",
        "grátis (API de registro público)"),
    "LIKELY_OWNER": ("Provavelmente o dono",
        "Indícios do registro mostram que a pessoa é dona do negócio, não funcionária.",
        "grátis (API de registro público)"),
    "EMAIL_PATTERN": ("Padrão de email da empresa",
        "O formato dos endereços do domínio (nome.sobrenome@, nsobrenome@). Um endereço "
        "real abre a empresa inteira.",
        "grátis, ou ~1 crédito de consulta"),
    "EMAIL_STATUS": ("Entregabilidade do email",
        "Se o endereço está verificado, aceita tudo (arriscado), é um chute ou é inválido.",
        "1 crédito de verificação (há planos grátis)"),
    "NO_VIDEO_ON_SITE": ("Sem vídeo no site",
        "A página inicial não tem nenhum vídeo (YouTube, Vimeo ou player). Para quem filma "
        "ou edita, é a lacuna mais clara: vendem algo visual e mostram só com foto.",
        "grátis (página inicial)"),
    "HAS_YOUTUBE_CHANNEL": ("Tem canal no YouTube",
        "O site linka um canal do YouTube. Já acreditam em vídeo; o ângulo é qualidade, "
        "constância ou volume de edição.",
        "grátis (página inicial)"),
    "INSTAGRAM_PROFILE": ("Perfil no Instagram",
        "O Instagram da empresa, linkado no site. Onde ficam os Reels, e um canal para "
        "mandar DM quando não há email.",
        "grátis (página inicial)"),
    "LINKEDIN_COMPANY": ("Página no LinkedIn",
        "A página da empresa no LinkedIn, linkada no site. Usada para falar com decisores "
        "no exterior, onde o LinkedIn é o canal normal de contato comercial.",
        "grátis (página inicial)"),
    "EVENT_ANNOUNCED": ("Evento anunciado",
        "Anunciaram um evento (conferência, lançamento, show) nos próximos meses: precisam de vídeo agora.",
        "1 busca no Serper por lead"),
    "NEW_ROLE": ("Cargo novo no marketing",
        "O contato começou há pouco num cargo de marketing ou comunicação: quem chega quer mostrar serviço.",
        "1 busca no Serper por lead"),
    "CONTACT_FORM_URL": ("Formulário de contato",
        "Um formulário no site. Chega na empresa sem precisar de email, e cerca de metade "
        "dos domínios não deixa verificar email.",
        "grátis (site)"),
}

for _sig in SIGNAL_CATALOG:
    if _sig["code"] in _PT_BR:
        _sig["label"], _sig["description"], _sig["cost_note"] = _PT_BR[_sig["code"]]


async def seed_signal_catalog(state) -> int:
    """Register the catalog as PROPOSED signals awaiting user confirmation.

    Idempotent, and never overrides a decision the user already made: an
    existing signal keeps its confirmed/rejected status.
    """
    for sig in SIGNAL_CATALOG:
        await state.upsert_signal_code(
            sig["code"],
            label=sig["label"],
            description=sig["description"],
            category=sig["category"],
            value_type=sig["value_type"],
            collector=sig["collector"],
            cost_note=sig["cost_note"],
            confidence_floor=sig.get("confidence_floor", 0.0),
        )
    return len(SIGNAL_CATALOG)
