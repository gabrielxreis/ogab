"""Inspiração para motions: busca na coleção awesome-opus5-5-videos (vídeos feitos com o Opus 5.5 em código).

  python3 inspiracao.py "counter numbers"                  # termos EM INGLÊS (os prompts são em inglês)
  python3 inspiracao.py "map route" --cat motion,explainer --n 5
  python3 inspiracao.py --atualizar                         # git pull da coleção

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


def main(a):
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
