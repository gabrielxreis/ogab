"""Efeitos sonoros grátis do Pixabay, para quem não tem conta no Artlist nem no Envato (ou quando eles não acham).
Licença Pixabay Content License: uso comercial liberado, inclusive anúncio, sem crédito obrigatório; não vale revender o
som solto. Não precisa de conta nem de chave.

O site do Pixabay bloqueia script (Cloudflare), então a BUSCA roda no navegador (Claude in Chrome ou o navegador do
app) e o DOWNLOAD, que vem do CDN deles, roda aqui:

  python3 sfx_pixabay.py busca "<termos em inglês>" [--n 8]
        -> imprime a URL da busca e o JavaScript para rodar nela (javascript_tool). O resultado é uma lista JSON
           [{titulo, pagina, mp3}]: salvar em lista.json.
  python3 sfx_pixabay.py baixar <lista.json> <pasta_sfx> [--so 1,3] [--nomes gaveta,papel]
        -> baixa os escolhidos, converte para WAV 48 kHz estéreo a -16 LUFS (o padrão da biblioteca de SFX) e anota
           título, página e licença em <pasta_sfx>/CREDITOS.txt. Depois: ouvir/medir com sonorizar.py medir e
           conferir o que o som É com sfx_conferir.py, como qualquer SFX.

Termos sempre em inglês, pelo OBJETO + ação ("drawer close wood", "paper slide", "rubber stamp", "pen writing").
"""
import json, os, re, subprocess, sys, tempfile, urllib.parse, urllib.request

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"
LICENCA = "Pixabay Content License (uso comercial livre, sem crédito obrigatório)"

JS = r"""const links=[...new Set([...document.querySelectorAll('a[href*="/sound-effects/"]')].map(a=>a.href)
  .filter(h=>/-\d+\/?$/.test(h)))].slice(0,%N%);
const out=[];
for (const u of links){ const t=await (await fetch(u)).text();
  const mp3=(t.match(/https:\/\/cdn\.pixabay\.com\/download\/audio\/[^"'\s]*?\.mp3[^"'\s]*/)||[''])[0].replace(/&amp;/g,'&');
  const tit=(t.match(/<title>([^<|]*)/)||['',''])[1].replace(/&amp;/g,'&').trim();
  if (mp3) out.push({titulo:tit, pagina:u, mp3}); }
JSON.stringify(out)"""


def busca(termos, n=8):
    url = "https://pixabay.com/sound-effects/search/" + urllib.parse.quote(termos) + "/"
    print("1) abrir no navegador:", url)
    print("2) rodar este JavaScript na página (javascript_tool) e salvar o resultado em lista.json:\n")
    print(JS.replace("%N%", str(n)))


def _ssl():
    """Python do python.org no Mac vem sem certificados (CERTIFICATE_VERIFY_FAILED): usa os do certifi se houver
    (trecho de usuário, relato de 30/10/2026)."""
    import ssl
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def slug(s):
    s = re.sub(r"\s+by\s+.*$", "", s, flags=re.I)
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")[:40] or "sfx"


def baixar(lista_json, pasta, so=None, nomes=None):
    lista = json.load(open(lista_json))
    if isinstance(lista, str):   # o javascript_tool devolve a string JSON
        lista = json.loads(lista)
    idx = [int(x) - 1 for x in so.split(",")] if so else range(len(lista))
    nomes = nomes.split(",") if nomes else []
    os.makedirs(pasta, exist_ok=True)
    feitos = []
    for k, i in enumerate(idx):
        it = lista[i]
        if not it.get("mp3", "").startswith("https://cdn.pixabay.com/"):
            print(f"pulado (sem link do CDN): {it.get('titulo')}"); continue
        nome = nomes[k] if k < len(nomes) else slug(it.get("titulo", ""))
        destino = os.path.join(pasta, nome + ".wav")
        tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False).name
        req = urllib.request.Request(it["mp3"], headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=60, context=_ssl()) as r, open(tmp, "wb") as f:
            f.write(r.read())
        # 48 kHz estéreo e -16 LUFS como a biblioteca do Artlist: mede e aplica um ganho fixo (o loudnorm dinâmico
        # erra em som curto), sem passar de -1 dBTP de pico
        m = subprocess.run(["ffmpeg", "-hide_banner", "-i", tmp, "-af", "loudnorm=print_format=json", "-f", "null", "-"],
                           capture_output=True, text=True).stderr
        med = json.loads(m[m.rindex("{"):m.rindex("}") + 1])
        ganho = min(-16 - float(med["input_i"]), -1 - float(med["input_tp"]))
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", tmp, "-af", f"volume={ganho:.2f}dB",
                        "-ar", "48000", "-ac", "2", destino], check=True)
        os.remove(tmp)
        with open(os.path.join(pasta, "CREDITOS.txt"), "a", encoding="utf-8") as f:
            f.write(f"{nome}.wav  <-  {it.get('titulo')} | {it.get('pagina')} | {LICENCA}\n")
        feitos.append(destino); print("ok:", destino)
    return feitos


if __name__ == "__main__":
    a = sys.argv[1:]
    op = lambda k: a[a.index(k) + 1] if k in a else None
    if len(a) >= 2 and a[0] == "busca":
        busca(a[1], int(op("--n") or 8))
    elif len(a) >= 3 and a[0] == "baixar":
        baixar(a[1], a[2], op("--so"), op("--nomes"))
    else:
        raise SystemExit(__doc__)
