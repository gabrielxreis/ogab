"""Identidade visual da empresa direto do site oficial: logos, cores, fontes, favicon e imagem de compartilhamento.

  python3 marca.py https://site-da-empresa.com ~/Desktop/<Empresa>/marca

Salva em <destino>/:
  logos/          todos os candidatos a logo (img/svg com "logo" no nome/classe/alt, favicons, apple-touch-icon, og:image)
  identidade.json cores (hex mais usados no HTML/CSS, theme-color), fontes (font-family, Google Fonts), arquivos baixados
  identidade.md   resumo legível para o perfil do cliente
Depois a skill confere as logos (olhar as imagens) e marca no identidade.md qual é a principal, a clara e a escura.
Só lê páginas públicas do site; não faz login. Fontes: só registra o nome e o link (licença de quem usa).
"""
import json, os, re, sys, urllib.parse, urllib.request
from collections import Counter

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"}
NEUTRAS = {"#ffffff", "#000000", "#fff", "#000", "#fefefe", "#f5f5f5", "#eeeeee", "#e5e5e5", "#333333", "#222222", "#111111",
           "#666666", "#999999", "#cccccc", "#dddddd", "#f9f9f9", "#fafafa", "#f0f0f0", "#e0e0e0", "#1a1a1a"}


def baixar(url, limite=8_000_000):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read(limite), r.headers.get("Content-Type", "")


def texto(url):
    b, _ = baixar(url); return b.decode("utf-8", "ignore")


def hex6(h):
    h = h.lower()
    return "#" + "".join(c * 2 for c in h[1:]) if len(h) == 4 else h


def cores(txt):
    c = Counter(hex6(h) for h in re.findall(r"#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b", txt))
    for r_, g, b in re.findall(r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)", txt):
        c["#%02x%02x%02x" % (int(r_), int(g), int(b))] += 1
    return c


def main(site, destino):
    if not site.startswith("http"): site = "https://" + site
    os.makedirs(os.path.join(destino, "logos"), exist_ok=True)
    html = texto(site)
    abs_ = lambda u: urllib.parse.urljoin(site, u.strip())
    cand = []
    for m in re.finditer(r"<link[^>]+>", html, re.I):
        tag = m.group(0)
        if re.search(r'rel=["\'][^"\']*(icon|apple-touch-icon|mask-icon)', tag, re.I):
            h = re.search(r'href=["\']([^"\']+)', tag)
            if h: cand.append(("icone", abs_(h.group(1))))
    for prop in ("og:image", "twitter:image"):
        m = re.search(r'<meta[^>]+(?:property|name)=["\']%s["\'][^>]+content=["\']([^"\']+)' % prop, html, re.I) or \
            re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\']%s["\']' % prop, html, re.I)
        if m: cand.append(("compartilhamento", abs_(m.group(1))))
    for m in re.finditer(r"<img[^>]+>", html, re.I):
        tag = m.group(0)
        if re.search(r"logo|brand|marca", tag, re.I):
            s = re.search(r'(?:data-src|src)=["\']([^"\']+)', tag)
            if s and not s.group(1).startswith("data:"): cand.append(("logo", abs_(s.group(1))))
            ss = re.search(r'srcset=["\']([^"\']+)', tag)
            if ss: cand.append(("logo", abs_(ss.group(1).split(",")[-1].split()[0])))
    # SVG inline com "logo" (muito comum no cabeçalho)
    svgs = [m.group(0) for m in re.finditer(r"<svg[\s\S]*?</svg>", html, re.I) if re.search(r"logo|brand", m.group(0)[:400], re.I)]
    css_links = [abs_(h) for h in re.findall(r'<link[^>]+rel=["\']stylesheet["\'][^>]+href=["\']([^"\']+)', html, re.I)] + \
                [abs_(h) for h in re.findall(r'<link[^>]+href=["\']([^"\']+\.css[^"\']*)["\'][^>]*rel=["\']stylesheet', html, re.I)]
    css_txt = "\n".join(re.findall(r"<style[^>]*>([\s\S]*?)</style>", html, re.I))
    for u in list(dict.fromkeys(css_links))[:8]:
        try: css_txt += "\n" + texto(u)
        except Exception: pass
    # baixar logos
    salvos, vistos = [], set()
    for k, (tipo, u) in enumerate(cand):
        if u in vistos: continue
        vistos.add(u)
        try:
            b, ct = baixar(u)
            ext = os.path.splitext(urllib.parse.urlparse(u).path)[1].lower() or \
                  {"image/svg+xml": ".svg", "image/png": ".png", "image/webp": ".webp", "image/jpeg": ".jpg", "image/x-icon": ".ico"}.get(ct.split(";")[0], ".bin")
            nome = f"{tipo}_{k:02d}{ext[:5]}"
            open(os.path.join(destino, "logos", nome), "wb").write(b); salvos.append({"tipo": tipo, "arquivo": f"logos/{nome}", "url": u})
        except Exception as e:
            salvos.append({"tipo": tipo, "url": u, "erro": str(e)[:80]})
    for k, svg in enumerate(svgs[:4]):
        nome = f"logo_inline_{k:02d}.svg"
        if "xmlns" not in svg[:200]: svg = svg.replace("<svg", '<svg xmlns="http://www.w3.org/2000/svg"', 1)
        open(os.path.join(destino, "logos", nome), "w").write(svg); salvos.append({"tipo": "logo", "arquivo": f"logos/{nome}", "url": "svg no html"})
    tc = re.search(r'<meta[^>]+name=["\']theme-color["\'][^>]+content=["\']([^"\']+)', html, re.I)
    todas = cores(html + css_txt)
    marca = [(c, n) for c, n in todas.most_common(40) if c not in NEUTRAS][:10]
    fontes = Counter(f.strip().strip("'\"") for ff in re.findall(r"font-family\s*:\s*([^;}{]+)", css_txt + html, re.I)
                     for f in ff.split(",")[:1] if f.strip() and "var(" not in f and not f.strip().startswith("-"))
    gfonts = list(dict.fromkeys(re.findall(r'https://fonts\.googleapis\.com/css2?\?[^"\'\s)]+', html + css_txt)))
    ident = {"site": site, "theme_color": tc.group(1) if tc else None, "cores_marca": marca,
             "fontes": fontes.most_common(6), "google_fonts": gfonts, "arquivos": salvos}
    json.dump(ident, open(os.path.join(destino, "identidade.json"), "w"), ensure_ascii=False, indent=2)
    with open(os.path.join(destino, "identidade.md"), "w") as f:
        f.write(f"# Identidade visual (tirada de {site})\n\n")
        f.write(f"- theme-color: {ident['theme_color'] or '-'}\n- Cores mais usadas (sem neutras): " +
                ", ".join(f"{c} ({n}x)" for c, n in marca) + "\n- Fontes: " + ", ".join(f"{n}" for n, _ in fontes.most_common(6)) + "\n")
        if gfonts: f.write("- Google Fonts: " + " | ".join(gfonts) + "\n")
        f.write("\n## Logos baixadas (conferir e marcar a principal, versão clara e escura)\n")
        for s in salvos: f.write(f"- {s['tipo']}: {s.get('arquivo') or 'ERRO ' + s.get('erro', '')} ({s['url'][:120]})\n")
    print(json.dumps({k: ident[k] for k in ("theme_color", "cores_marca", "fontes")}, ensure_ascii=False))
    print(len([s for s in salvos if "arquivo" in s]), "arquivos em", os.path.join(destino, "logos"))


if __name__ == "__main__":
    if len(sys.argv) < 3: print(__doc__); sys.exit()
    main(sys.argv[1], os.path.expanduser(sys.argv[2]))
