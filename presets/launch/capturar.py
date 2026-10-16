"""Preset LAUNCH, passo 1: captura um site (ou um app rodando em localhost) para o vídeo de lançamento.

  python3 capturar.py <url> <pasta_saida> [--altura 3600]

Gera em <pasta_saida>:
  desktop.png   a página inteira em 1440 px de largura (até --altura px), para a cena "tela" num navegador
  topo.png      a primeira dobra em 1440x900 (o que se vê ao abrir o site)
  celular.png   a página em 390 px (iPhone), para a cena "tela" num celular
  marca.json    nome, frase, descrição, cor da marca, cores achadas no CSS, logo/ícone e imagem de compartilhamento

Página inteira: pagina.mjs (playwright-core + o Chrome instalado) rola até o fim antes do print, para as seções com
animação de entrada aparecerem; sem Node, cai no print de janela alta do Chrome. Usa o Chrome sem janela (headless). Nada é enviado a lugar nenhum: só abre a página, como um navegador.
"""
import collections, colorsys, html, json, os, re, shutil, subprocess, sys, urllib.parse, urllib.request

CHROMES = ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
           "/Applications/Chromium.app/Contents/MacOS/Chromium",
           "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
           "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
           r"C:\Program Files\Google\Chrome\Application\chrome.exe",
           r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"]
IPHONE = ("Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 "
          "(KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1")


def chrome():
    for c in CHROMES:
        if os.path.exists(c):
            return c
    raise SystemExit("Preciso do Google Chrome (ou Chromium/Brave/Edge) instalado para capturar o site.")


def foto(url, saida, w, h, ua=None):
    args = [chrome(), "--headless=new", "--hide-scrollbars", "--disable-gpu", "--no-first-run",
            "--force-device-scale-factor=1", f"--window-size={w},{h}", "--virtual-time-budget=6000",
            f"--screenshot={saida}"]
    if ua:
        args.append(f"--user-agent={ua}")
    subprocess.run(args + [url], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=90)
    return os.path.exists(saida)


CACHE = os.path.expanduser("~/.cache/ogab-launch")


def pagina_inteira(url, saida, w, h, celular=False):
    """Print da página inteira rolando antes (pagina.mjs). Devolve False se não der (sem Node/npm)."""
    try:
        os.makedirs(CACHE, exist_ok=True)
        if not os.path.isdir(os.path.join(CACHE, "node_modules", "playwright-core")):
            subprocess.run(["npm", "install", "--silent", "--prefix", CACHE, "playwright-core@1.56.1"], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=300)
        shutil.copy(os.path.join(os.path.dirname(os.path.abspath(__file__)), "pagina.mjs"), CACHE)
        subprocess.run(["node", "pagina.mjs", url, saida, str(w), str(h)] + (["celular"] if celular else []), cwd=CACHE,
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180)
        return os.path.exists(saida)
    except Exception:
        return False


def baixar(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Macintosh) ogab-launch"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8", "ignore")


def meta(doc, *nomes):
    for n in nomes:
        m = re.search(r'<meta[^>]+(?:name|property)=["\']%s["\'][^>]*content=["\']([^"\']+)' % re.escape(n), doc, re.I) \
            or re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]*(?:name|property)=["\']%s["\']' % re.escape(n), doc, re.I)
        if m:
            return html.unescape(m.group(1)).strip()
    return ""


# Cores de botões de terceiros que aparecem em quase todo site e não são a marca (WhatsApp, Facebook, Google...).
DE_TERCEIROS = {"#25D366", "#128C7E", "#075E54", "#1877F2", "#4285F4", "#34A853", "#FBBC05", "#EA4335", "#1DA1F2", "#0A66C2", "#FF0000"}


def cores_do_css(texto):
    """Cores mais usadas, só as que têm cor de verdade (nada de cinza, preto ou branco). Lê hex e hsl()/variáveis
    no formato do Tailwind/shadcn ("--primary: 43 49% 54%")."""
    conta = collections.Counter()

    def soma(r, g, b, peso=1):
        hh, l, s = colorsys.rgb_to_hls(r, g, b)
        if s > 0.35 and 0.18 < l < 0.82:
            c = "#%02X%02X%02X" % tuple(round(v * 255) for v in (r, g, b))
            if c not in DE_TERCEIROS:
                conta[c] += peso
    for h in re.findall(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b", texto):
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        soma(*(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)))
    for nome, hh, ss, ll in re.findall(r"(--[\w-]+:\s*|hsla?\()\s*([\d.]+)(?:deg)?[\s,]+([\d.]+)%[\s,]+([\d.]+)%", texto):
        r, g, b = colorsys.hls_to_rgb(float(hh) / 360, float(ll) / 100, float(ss) / 100)
        soma(r, g, b, 3 if re.search(r"primary|accent|brand|gold|cor", nome) else 1)   # variável de tema pesa mais
    return [c for c, _ in conta.most_common(6)]


def marca(url, doc):
    base = url
    titulo = html.unescape((re.search(r"<title[^>]*>(.*?)</title>", doc, re.I | re.S) or [None, ""])[1]).strip()
    nome = meta(doc, "og:site_name", "application-name") or re.split(r"\s[|\-–—:]\s", titulo)[0].strip()
    css = doc
    for href in re.findall(r'<link[^>]+rel=["\']stylesheet["\'][^>]*href=["\']([^"\']+)', doc, re.I)[:4]:
        try:
            css += baixar(urllib.parse.urljoin(base, href))
        except Exception:
            pass
    icone = ""
    for rel in ("apple-touch-icon", "icon", "shortcut icon"):
        m = re.search(r'<link[^>]+rel=["\']%s["\'][^>]*href=["\']([^"\']+)' % rel, doc, re.I)
        if m:
            icone = urllib.parse.urljoin(base, m.group(1)); break
    cores = cores_do_css(css)
    tema = meta(doc, "theme-color")
    return {
        "url": url,
        "nome": nome or urllib.parse.urlparse(url).hostname,
        "titulo": titulo,
        "frase": meta(doc, "og:title", "twitter:title") or titulo,
        "descricao": meta(doc, "description", "og:description", "twitter:description"),
        "cor": tema if re.match(r"^#[0-9a-fA-F]{6}$", tema or "") else (cores[0] if cores else "#C4A34F"),
        "cores": cores,
        "icone": icone,
        "imagem": urllib.parse.urljoin(base, meta(doc, "og:image", "twitter:image")) if meta(doc, "og:image", "twitter:image") else "",
        "dominio": urllib.parse.urlparse(url).hostname or "",
    }


def main(a):
    if len(a) < 2:
        raise SystemExit(__doc__)
    url, pasta = a[0], os.path.abspath(a[1])
    if not re.match(r"^(https?|file)://", url):
        url = "https://" + url
    alt = int(a[a.index("--altura") + 1]) if "--altura" in a else 3600
    os.makedirs(pasta, exist_ok=True)
    foto(url, os.path.join(pasta, "topo.png"), 1440, 900)
    if not pagina_inteira(url, os.path.join(pasta, "desktop.png"), 1440, 900):
        foto(url, os.path.join(pasta, "desktop.png"), 1440, alt)
    if not pagina_inteira(url, os.path.join(pasta, "celular.png"), 390, 844, celular=True):
        foto(url, os.path.join(pasta, "celular.png"), 390, 1900, IPHONE)
    try:
        doc = baixar(url) if url.startswith("http") else open(urllib.parse.urlparse(url).path, encoding="utf-8").read()
        dados = marca(url, doc)
    except Exception as e:
        dados = {"url": url, "nome": urllib.parse.urlparse(url).hostname or url, "erro": str(e), "cor": "#C4A34F"}
    json.dump(dados, open(os.path.join(pasta, "marca.json"), "w"), ensure_ascii=False, indent=2)
    print(json.dumps(dados, ensure_ascii=False, indent=2))
    print("prints:", ", ".join(f for f in ("topo.png", "desktop.png", "celular.png") if os.path.exists(os.path.join(pasta, f))))


if __name__ == "__main__":
    main(sys.argv[1:])
