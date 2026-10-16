"""Inspiração para motions: busca na coleção awesome-opus5-5-videos (vídeos feitos com o Opus 5.5 em código).

  python3 inspiracao.py "counter numbers"                  # termos EM INGLÊS (os prompts são em inglês)
  python3 inspiracao.py "map route" --cat motion,explainer --n 5
  python3 inspiracao.py --atualizar                         # git pull da coleção
  python3 inspiracao.py "launch phone" --galeria            # busca na galeria Prompt Motion (prompt-motion.com)
  python3 inspiracao.py --galerias                          # lista as galerias de referência para ver no Chrome

Pedido "um vídeo estilo X" ou "parecido com aquele": ANTES do plano, buscar referência aqui e nas galerias, ASSISTIR
(preview mp4 ou página no Chrome), anotar a linguagem (ritmo, curvas, tipografia, transições, paleta, som) e recriar com
o material do cliente. Nunca copiar o vídeo, os textos, as marcas nem o prompt inteiro; não citar o autor no vídeo.

Só INSPIRAÇÃO de movimento e ritmo: as regras da skill continuam mandando (centro 540/960, visual do site do
cliente, duração da fala, calmo). Nunca copiar o prompt inteiro para o cliente nem citar o autor no vídeo.
A coleção fica fora da skill, em ~/.claude/referencias/awesome-opus5-5-videos (o install clona).
Saída: categoria, tecnologias, link do vídeo (ver antes de usar) e o começo do prompt.
"""
import json, os, re, subprocess, sys, unicodedata

PASTA = os.path.expanduser("~/.claude/referencias/awesome-opus5-5-videos")
REPO = "https://github.com/yihui-dev/awesome-opus5-5-videos.git"
# O que serve para Reels de cliente: prioriza vertical, GSAP/HyperFrames e o que já tem remake para assistir.
BONUS = [(r"9:16|vertical|1080x1920|reels?|tiktok|shorts", 3), (r"gsap|hyperframes", 2)]


def _sem_acento(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s.lower()) if not unicodedata.combining(c))


def garantir(atualizar=False):
    if not os.path.isdir(os.path.join(PASTA, ".git")):
        os.makedirs(os.path.dirname(PASTA), exist_ok=True)
        subprocess.run(["git", "clone", "--depth", "1", "-q", REPO, PASTA], check=True)
    elif atualizar:
        subprocess.run(["git", "-C", PASTA, "pull", "-q", "--ff-only"])


def buscar(termos, cats=None, n=8):
    garantir()
    vids = json.load(open(os.path.join(PASTA, "data", "videos.json"), encoding="utf-8"))
    palavras = [_sem_acento(t) for t in re.split(r"\s+", termos.strip()) if t]
    saida = []
    for v in vids:
        if cats and v.get("category") not in cats:
            continue
        texto = _sem_acento(" ".join([v.get("prompt") or "", v.get("category") or "", " ".join(v.get("tech_tags") or [])]))
        acertos = sum(1 for p in palavras if re.search(r"\b" + re.escape(p), texto))   # palavra inteira (o começo)
        if palavras and not acertos:
            continue
        nota = acertos * 5 + (6 if acertos == len(palavras) else 0) + sum(b for r, b in BONUS if re.search(r, texto)) + (1 if v.get("has_remake") else 0)
        nota += min(len(v.get("prompt") or ""), 1500) / 500       # prompt detalhado ensina mais que "go all out"
        saida.append((nota, v))
    saida.sort(key=lambda x: -x[0])
    return [v for _, v in saida[:n]]


GALERIAS = [
    ("Prompt Motion", "https://prompt-motion.com/", "230+ filmes feitos com Claude, com prompt ou skill ao lado; filtro por tipo (product UI, phone, kinetic type, charts, particles...)"),
    ("AI x Leaders", "https://ai-x-leaders.com/en/prompt/", "mural dos mais curtidos (launch, logo reveal, kinetic type), com o prompt completo"),
    ("Promptcat", "https://promptcat.org/use-cases/animation/", "161 casos de animação: Lottie de interface, filmes de produto, explicativos"),
    ("Promptslove (pago)", "https://promptslove.com/motion-graphics-claude-skill/", "só a lista de tipos de vídeo e estilos serve de ideia; não usar o material"),
]


def galeria(termos, n=8):
    """Busca na Prompt Motion: título e etiquetas; vertical e com prompt aberto sobem na lista."""
    import urllib.request
    req = urllib.request.Request("https://prompt-motion.com/", headers={"User-Agent": "Mozilla/5.0 ogab-inspiracao"})
    html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "ignore").replace('\\"', '"')
    itens, vistos = [], set()
    for m in re.finditer(r'\{"slug":"([^"]+)","title":"([^"]+)".*?"contentTags":\[([^\]]*)\].*?"promptShared":(true|false).*?"preview":"([^"]+)".*?"width":(\d+),"height":(\d+)', html):
        slug, tit, tags, aberto, prev, w, h = m.groups()
        if slug in vistos:
            continue
        vistos.add(slug)
        itens.append({"url": "https://prompt-motion.com/" + slug, "titulo": tit, "tags": re.findall(r'"([^"]+)"', tags),
                      "prompt": aberto == "true", "previa": prev, "formato": "vertical" if int(h) > int(w) else ("quadrado" if h == w else "horizontal")})
    palavras = [_sem_acento(t) for t in termos.split() if t]
    saida = []
    for it in itens:
        texto = _sem_acento(it["titulo"] + " " + " ".join(it["tags"]))
        acertos = sum(1 for p in palavras if p in texto)
        if palavras and not acertos:
            continue
        saida.append((acertos * 5 + (3 if it["formato"] == "vertical" else 0) + (2 if it["prompt"] else 0), it))
    saida.sort(key=lambda x: -x[0])
    return [it for _, it in saida[:n]], len(itens)


def main(a):
    if "--galerias" in a:
        for nome, url, d in GALERIAS:
            print(f"- {nome}: {url}\n  {d}")
        return
    if "--galeria" in a:
        achados, total = galeria(a[0] if a and not a[0].startswith("--") else "", int(a[a.index("--n") + 1]) if "--n" in a else 8)
        print(f"Prompt Motion: {len(achados)} de {total} filmes")
        for it in achados:
            print(f"- {it['titulo']} [{it['formato']}, {', '.join(it['tags'])}{', prompt aberto' if it['prompt'] else ''}]\n  {it['url']}  prévia: {it['previa']}")
        return
    if "--atualizar" in a:
        garantir(True); print("coleção atualizada em", PASTA); return
    if not a or a[0].startswith("--"):
        raise SystemExit(__doc__)
    cats = a[a.index("--cat") + 1].split(",") if "--cat" in a else None
    n = int(a[a.index("--n") + 1]) if "--n" in a else 8
    for v in buscar(a[0], cats, n):
        p = re.sub(r"\s+", " ", v.get("prompt") or "").strip()
        print(f"- [{v.get('category')}] {', '.join(v.get('tech_tags') or [])}  {v.get('skillry_url') or v.get('post_url')}")
        print(f"  {p[:400]}{'...' if len(p) > 400 else ''}")


if __name__ == "__main__":
    main(sys.argv[1:])
