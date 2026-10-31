"""Efeitos sonoros do Freesound (freesound.org), SÓ os de licença CC0 (domínio público: uso comercial livre, inclusive
anúncio de cliente, sem crédito obrigatório). Segunda fonte grátis, para quando o Pixabay não tem o som.

Dois caminhos, o script escolhe sozinho:
- Com a chave grátis do Freesound (rápido, ~1 s): criar conta em freesound.org, pegar a chave em
  https://freesound.org/apiv2/apply e salvar com `python3 sfx_freesound.py chave <CHAVE>` (fica em
  ~/.config/ogab/freesound.json, fora da skill e do git). Ou a variável FREESOUND_TOKEN.
- Sem chave: busca pelo Openverse (api.openverse.org, que espelha o Freesound CC0). Funciona, mas leva 30-60 s por
  busca e às vezes cai: oferecer a chave à pessoa se for usar muito.

  python3 sfx_freesound.py busca "<termos em inglês>" [--n 8] [--max 6] > lista.json
        -> lista JSON [{titulo, pagina, mp3, duracao, autor}], só CC0, até --max segundos (padrão 6, SFX curto)
  python3 sfx_freesound.py baixar <lista.json> <pasta_sfx> [--so 1,3] [--nomes gaveta,papel]
        -> igual ao sfx_pixabay.py: WAV 48 kHz estéreo a -16 LUFS, título/página/autor/licença em CREDITOS.txt

Baixa a prévia em alta do Freesound (MP3 ~128 kbps; o original exige login OAuth). Termos em inglês, pelo OBJETO +
ação ("drawer close wood", "paper slide"). Acervo da comunidade: ouvir/medir e conferir com sfx_conferir.py antes de usar.
"""
import json, os, sys, urllib.parse, urllib.request
from sfx_pixabay import UA, _ssl, baixar_wav, slug

CFG = os.path.expanduser("~/.config/ogab/freesound.json")
LICENCA = "CC0 1.0 (domínio público, uso comercial livre, sem crédito obrigatório)"


def chave():
    if os.environ.get("FREESOUND_TOKEN"):
        return os.environ["FREESOUND_TOKEN"]
    try:
        return json.load(open(CFG)).get("token")
    except (OSError, ValueError):
        return None


def _get(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout, context=_ssl()) as r:
        return json.loads(r.read())


def busca_freesound(termos, n, maximo, token):
    q = {"query": termos, "filter": f'license:"Creative Commons 0" duration:[0 TO {maximo}]', "sort": "score",
         "page_size": n, "fields": "id,name,username,license,duration,previews,url", "token": token}
    d = _get("https://freesound.org/apiv2/search/text/?" + urllib.parse.urlencode(q))
    return [{"titulo": r["name"], "pagina": r["url"], "mp3": r["previews"]["preview-hq-mp3"],
             "duracao": round(r["duration"], 1), "autor": r["username"]}
            for r in d.get("results", []) if "publicdomain/zero" in r.get("license", "")]


def busca_openverse(termos, n, maximo):
    # o filtro source=freesound na URL dá erro 500 no Openverse (31/10/2026): filtra a fonte aqui
    q = {"q": termos, "license": "cc0", "page_size": 20}
    url = "https://api.openverse.org/v1/audio/?" + urllib.parse.urlencode(q)
    for tentativa in (1, 2):
        try:
            d = _get(url, timeout=90)
            break
        except Exception as e:
            if tentativa == 2:
                raise SystemExit(f"Openverse fora do ar ({e}). Tente de novo, use o Pixabay ou salve a chave do "
                                 "Freesound (sfx_freesound.py chave <CHAVE>).")
    out = []
    for r in d.get("results", []):
        dur = (r.get("duration") or 0) / 1000
        if r.get("source") == "freesound" and r.get("url") and r.get("license") == "cc0" and 0 < dur <= maximo:
            out.append({"titulo": r["title"], "pagina": r.get("foreign_landing_url"), "mp3": r["url"],
                        "duracao": round(dur, 1), "autor": r.get("creator")})
    return out[:n]


def busca(termos, n=8, maximo=6):
    token = chave()
    if token:
        return busca_freesound(termos, n, maximo, token)
    print("sem chave do Freesound: buscando pelo Openverse (30-60 s)...", file=sys.stderr)
    return busca_openverse(termos, n, maximo)


def baixar(lista_json, pasta, so=None, nomes=None):
    lista = json.load(open(lista_json))
    idx = [int(x) - 1 for x in so.split(",")] if so else range(len(lista))
    nomes = nomes.split(",") if nomes else []
    os.makedirs(pasta, exist_ok=True)
    feitos = []
    for k, i in enumerate(idx):
        it = lista[i]
        if not it.get("mp3", "").startswith(("https://cdn.freesound.org/", "https://freesound.org/")):
            print(f"pulado (link fora do Freesound): {it.get('titulo')}"); continue
        nome = nomes[k] if k < len(nomes) else slug(it.get("titulo", ""))
        destino = os.path.join(pasta, nome + ".wav")
        baixar_wav(it["mp3"], destino)
        with open(os.path.join(pasta, "CREDITOS.txt"), "a", encoding="utf-8") as f:
            f.write(f"{nome}.wav  <-  {it.get('titulo')} por {it.get('autor')} | {it.get('pagina')} | Freesound {LICENCA}\n")
        feitos.append(destino); print("ok:", destino)
    return feitos


if __name__ == "__main__":
    a = sys.argv[1:]
    op = lambda k: a[a.index(k) + 1] if k in a else None
    if len(a) >= 2 and a[0] == "busca":
        print(json.dumps(busca(a[1], int(op("--n") or 8), float(op("--max") or 6)), ensure_ascii=False, indent=1))
    elif len(a) >= 3 and a[0] == "baixar":
        baixar(a[1], a[2], op("--so"), op("--nomes"))
    elif len(a) == 2 and a[0] == "chave":
        os.makedirs(os.path.dirname(CFG), exist_ok=True)
        fd = os.open(CFG, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as f:
            json.dump({"token": a[1]}, f)
        print("chave salva em", CFG)
    else:
        raise SystemExit(__doc__)
