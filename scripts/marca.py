"""Identidade visual da empresa direto do site oficial: logos, cores, fontes, favicon e imagem de compartilhamento.

  python3 marca.py https://site-da-empresa.com ~/Desktop/<Empresa>/marca
  python3 marca.py inverter logo.png [saida.png]   -> versão oposta da logo (branca <-> preta), mantendo a transparência
  python3 marca.py paleta logo.png [print.png ...] [--salvar identidade.json]   -> cores MEDIDAS nos pixels
  python3 marca.py conferir quadro.png identidade.json [--limite 12]          -> o quadro saiu nas cores da marca?

paleta: agrupa os pixels (ignora transparência e as cores da interface do Instagram), junta tons quase iguais (ΔE) e
devolve hex + fatia da imagem + papel (fundo, principal, destaque). Olhar no olho puxa a cor para um tom "conhecido";
medir não. conferir: cada cor que ocupa 3% ou mais do quadro tem que estar perto (ΔE) de uma cor da marca ou de um
neutro; as que não estão saem como aviso. Ideia do design-dna (zanwei, MIT), refeita em Pillow.

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


INTERFACE_IG = ["#ff3040", "#f83040", "#0095f6", "#efefef", "#dbdbdb", "#8e8e8e", "#262626", "#363636", "#737373"]


def _lab(h):
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))
    r, g, b = (((c + .055) / 1.055) ** 2.4 if c > .04045 else c / 12.92 for c in (r, g, b))
    x, y, z = ((r * .4124 + g * .3576 + b * .1805) / .95047, r * .2126 + g * .7152 + b * .0722,
               (r * .0193 + g * .1192 + b * .9505) / 1.08883)
    f = lambda t: t ** (1 / 3) if t > .008856 else 7.787 * t + 16 / 116
    return 116 * f(y) - 16, 500 * (f(x) - f(y)), 200 * (f(y) - f(z))


def delta_e(h1, h2):
    a, b = _lab(h1), _lab(h2)
    return sum((p - q) ** 2 for p, q in zip(a, b)) ** .5


def _sat(h):
    r, g, b = (int(h[i:i + 2], 16) for i in (1, 3, 5))
    return (max(r, g, b) - min(r, g, b)) / 255


def medir(arquivos, k=12, juntar=8.0, sem_interface=True):
    """[{hex, fatia, papel}] das imagens juntas, maior fatia primeiro."""
    from PIL import Image
    conta, total, transparente = {}, 0, False
    for arq in arquivos:
        im = Image.open(arq).convert("RGBA"); im.thumbnail((400, 400))
        fundo = Image.new("RGB", im.size, (0, 0, 0)); mascara = im.split()[3].point(lambda a: 255 if a >= 128 else 0)
        fundo.paste(im.convert("RGB"), mask=mascara)
        q = fundo.quantize(colors=k, method=Image.Quantize.MEDIANCUT)
        pal = q.getpalette()[:k * 3]
        visiveis = [p for p, m in zip(q.tobytes(), mascara.tobytes()) if m]
        transparente |= len(visiveis) < .95 * im.size[0] * im.size[1]   # logo recortada: sem cor de fundo
        for idx in visiveis:
            h = "#%02x%02x%02x" % tuple(pal[idx * 3:idx * 3 + 3])
            conta[h] = conta.get(h, 0) + 1
        total += len(visiveis)
    grupos = []                      # junta tons quase iguais, ficando com o tom de maior fatia
    for h, n in sorted(conta.items(), key=lambda x: -x[1]):
        if sem_interface and any(delta_e(h, ui) < 6 for ui in INTERFACE_IG):
            total -= n; continue
        for g in grupos:
            if delta_e(h, g["hex"]) < juntar:
                g["n"] += n; break
        else:
            grupos.append({"hex": h, "n": n})
    out = [{"hex": g["hex"], "fatia": round(g["n"] / max(total, 1), 3)} for g in grupos if g["n"] / max(total, 1) >= .01]
    if out:
        out[0]["papel"] = "principal" if transparente else "fundo"
        resto = out[1:]
        if resto:
            max(resto, key=lambda c: delta_e(c["hex"], out[0]["hex"]) * c["fatia"] ** .3)["papel"] = "secundária" if transparente else "principal"
            cor = [c for c in resto if "papel" not in c and _sat(c["hex"]) > .35]
            if cor:
                max(cor, key=lambda c: _sat(c["hex"]))["papel"] = "destaque"
    return out


def paleta(arquivos, salvar=None):
    cs = medir(arquivos)
    for c in cs:
        print(f"{c['hex']}  {c['fatia'] * 100:5.1f}%  {c.get('papel', '')}")
    if salvar:
        d = json.load(open(salvar, encoding="utf-8")) if os.path.exists(salvar) else {}
        d["paleta_medida"] = {"fontes": [os.path.basename(a) for a in arquivos], "cores": cs}
        json.dump(d, open(salvar, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(f"gravado em {salvar} (paleta_medida)")
    return cs


def conferir(quadro, identidade, limite=12.0):
    d = json.load(open(identidade, encoding="utf-8"))
    marca = [c["hex"] for c in d.get("paleta_medida", {}).get("cores", [])]
    marca += [c if isinstance(c, str) else c.get("hex", "") for c in (d.get("cores") or [])][:8]
    marca = [hex6(m) for m in marca if re.fullmatch(r"#[0-9a-fA-F]{3}([0-9a-fA-F]{3})?", m or "")]
    if not marca:
        raise SystemExit("identidade.json sem cores: rodar `marca.py paleta ... --salvar` antes")
    neutros = ["#ffffff", "#000000", "#808080", "#f2f2f2", "#1a1a1a", "#c0c0c0", "#404040"]
    fora = []
    for c in medir([quadro], sem_interface=False):
        if c["fatia"] < .03:
            continue
        perto = min(marca, key=lambda m: delta_e(c["hex"], m))
        de = delta_e(c["hex"], perto)
        if de > limite and min(delta_e(c["hex"], n) for n in neutros) > limite:
            fora.append((c, perto, de))
        print(f"{c['hex']}  {c['fatia'] * 100:5.1f}%  -> {perto} ΔE {de:4.1f}  {'FORA' if (c, perto, de) in fora else 'ok'}")
    print("PASSA: o quadro está nas cores da marca" if not fora else f"AVISO: {len(fora)} cor(es) fora da marca (ΔE > {limite:g})")
    return not fora


def inverter(ent, sai=None):
    """Branco vira preto e preto vira branco (inverte só o RGB; o canal alfa fica igual, então o fundo transparente
    continua transparente). Para logo monocromática: gera a versão para fundo claro a partir da branca e vice-versa.
    Logo colorida: inverter troca as cores da marca; nesse caso pedir a versão oficial ao cliente."""
    from PIL import Image, ImageOps
    im = Image.open(ent).convert("RGBA"); r, g, b, a = im.split()
    rgb = ImageOps.invert(Image.merge("RGB", (r, g, b)))
    out = Image.merge("RGBA", (*rgb.split(), a))
    if not sai:
        base, ext = os.path.splitext(ent)
        sai = base.replace("branca", "preta") if "branca" in base else base.replace("preta", "branca") if "preta" in base else base + "_invertida"
        sai += ".png"
    out.save(sai); print(sai); return sai


if __name__ == "__main__":
    if len(sys.argv) < 3: print(__doc__); sys.exit()
    a = sys.argv[1:]
    op = lambda k: a[a.index(k) + 1] if k in a else None
    if a[0] == "inverter": inverter(os.path.expanduser(a[1]), a[2] if len(a) > 2 else None)
    elif a[0] == "paleta": paleta([os.path.expanduser(x) for x in a[1:] if not x.startswith("--") and x != op("--salvar")], op("--salvar"))
    elif a[0] == "conferir": sys.exit(0 if conferir(os.path.expanduser(a[1]), os.path.expanduser(a[2]), float(op("--limite") or 12)) else 1)
    else: main(sys.argv[1], os.path.expanduser(sys.argv[2]))
