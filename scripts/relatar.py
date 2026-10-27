"""Relatos de erro do Gab: quem instalou e CONCORDOU manda, anônimo, o que quebrou e como foi corrigido (o dono atualiza).

  python3 relatar.py consentir sim|nao     # resposta da pergunta única (instalador ou 1ª abertura); grava "relatos" no config
  python3 relatar.py perguntar             # imprime PERGUNTAR se esta instalação ainda não respondeu (o Gab pergunta 1 vez)
  python3 relatar.py registrar --titulo "..." --erro "..." --causa "..." --correcao "..." [--arquivo scripts/x.py ...]
  python3 relatar.py preset <pasta do modelo | modelo.json>   # motion novo da biblioteca local (biblioteca_motions salvar chama sozinho)
  python3 relatar.py parecido <pasta do modelo | modelo.json>  # quão diferente é da biblioteca (e dos já enviados)
  python3 relatar.py desempacotar <texto.txt> <pasta>  # (dono) remonta a pasta de um preset HyperFrames (colunas diff coladas)
  python3 relatar.py varrer                # acha os motions que ESTE usuário criou (presets/ novos e biblioteca local)
                                           # e as INVENÇÕES na skill (scripts novos, melhorias, o que o doctor guardou no stash)
  python3 relatar.py enviar                # varre + manda os pendentes (ao abrir o Gab, em segundo plano) SÓ se "relatos": true
  python3 relatar.py status                # consentimento, pendentes e enviados

Consentimento: sem "relatos": true no config.json nada sai da máquina (relatos ficam só em ~/.claude/ogab_relatos/).
Motions (presets) só saem com o consentimento da pergunta nova ("relatos_v" >= 2), que cita erros E motions.
Preset vai como ESTRUTURA: elementos, tempos, animações e campos; textos de exemplo viram genéricos, sai o autor,
nome de cliente sai pela anonimização e as cores nem ficam no modelo (vêm do cliente na hora de aplicar).
Preset HyperFrames ("motor": "hyperframes", spec vazio) vai como PACOTE dos arquivos de texto da pasta do modelo
(PRESET.md, gerar.py, kit/*.css|js, index.html, hyperframes.json), para o dono remontar e renderizar: anonimizados,
cores viram cinza da mesma luminosidade (sem a cor da marca), textos visíveis viram "Texto", data: URIs e libs
minificadas saem, binários só aparecem na lista. Até PARTES_MAX partes de ~LIMITE_PARTE caracteres (juntadas na VPS).
O relato é ANONIMIZADO antes de ser gravado: caminhos viram ~/..., saem e-mails, chaves/tokens, parâmetros de link,
o nome do usuário e o nome de cada cliente (pastas de clientes/ e da pasta de saída). Não vai vídeo, roteiro, legenda
nem transcrição: só o que quebrou na skill, a causa, a correção e o diff dos arquivos DA SKILL.
Na máquina do dono ("dono_biblioteca": true) não envia (ele corrige direto). Destino: SÓ a fila da VPS do autor
(`/v1/preset`, com a key de licença; regra do usuário 26/10/2026). A planilha/Formulário Google foi desativada: nunca
recriar nem mandar para outro lugar (planilha, formulário, Drive, gws, webhook, e-mail).
"""
import glob, hashlib, json, os, platform, re, subprocess, sys, time, urllib.request

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(SKILL, "config.json")
PASTA = os.path.expanduser("~/.claude/ogab_relatos")
PEND, ENV = os.path.join(PASTA, "pendentes"), os.path.join(PASTA, "enviados")
CHAVE_ENVIO = "ogab-relato-v1"
LIMITES = {"titulo": 200, "erro": 3000, "causa": 2000, "correcao": 3000, "diff": 15000}
CONSENTIMENTO_V = 2   # 2 = erros + motions novos
PERGUNTA = ("Posso mandar ao Gabriel, de forma ANÔNIMA, (1) os erros da skill que eu corrigir aqui e (2) a estrutura dos "
            "motions novos que você salvar na biblioteca, para ele melhorar o Gab e publicar os melhores motions para todo "
            "mundo? Não vai vídeo, roteiro, texto do cliente, cor da marca, nome nem pasta. Dá para mudar depois: "
            "/ogab config relatos sim|nao")


def _config():
    try:
        return json.load(open(CONFIG, encoding="utf-8"))
    except Exception:
        return {}


def consentir(sim):
    c = _config(); c["relatos"] = bool(sim); c["relatos_respondido"] = time.strftime("%Y-%m-%d")
    c["relatos_v"] = CONSENTIMENTO_V
    if not sim and not c.get("dono_biblioteca"):   # relatos fazem parte dos termos (docs/TERMOS.md): "não" = retirar o aceite
        c["termos"] = dict(c.get("termos") or {}, aceito=False, quando=time.strftime("%Y-%m-%d %H:%M"))
    json.dump(c, open(CONFIG, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return c["relatos"]


def precisa_perguntar():
    c = _config()
    if c.get("dono_biblioteca"):
        return False
    return False   # desde 22/10/2026 os relatos vêm do aceite dos termos (termos.py), sem pergunta separada


def _versao():
    try:
        for l in open(os.path.join(SKILL, "CHANGELOG.md"), encoding="utf-8"):
            m = re.match(r"## (\S+)", l)
            if m:
                return m.group(1)
    except Exception:
        pass
    return "?"


def _instalacao():
    """Id aleatório da instalação (conta em quantas máquinas o mesmo erro aconteceu). Não identifica a pessoa."""
    os.makedirs(PASTA, exist_ok=True); arq = os.path.join(PASTA, "instalacao.txt")
    if not os.path.exists(arq):
        open(arq, "w").write(hashlib.sha256(os.urandom(32)).hexdigest()[:12])
    return open(arq).read().strip()


def _nomes_privados(cfg):
    nomes = set()
    for d in glob.glob(os.path.join(SKILL, "clientes", "*")):
        b = os.path.basename(d)
        if os.path.isdir(d) and not b.startswith(("_", ".")):
            nomes.add(b)
            try:
                for l in open(os.path.join(d, "cliente.md"), encoding="utf-8"):
                    m = re.match(r"#\s+(.+)", l)
                    if m:
                        nomes.add(m.group(1).strip()); break
            except Exception:
                pass
    saida = os.path.expanduser(cfg.get("pasta_saida", "~/Desktop"))
    for d in glob.glob(os.path.join(saida, "*")):
        if os.path.isdir(d):
            nomes.add(os.path.basename(d))
    try:
        import pwd
        nomes.add(pwd.getpwuid(os.getuid()).pw_gecos.split(",")[0])
    except Exception:
        pass
    nomes.add(os.path.basename(os.path.expanduser("~")))
    return sorted((n for n in nomes if n and len(n) >= 3), key=len, reverse=True)


def anonimizar(txt, nomes):
    if not txt:
        return ""
    t = str(txt).replace(SKILL, "SKILL_DIR").replace(os.path.expanduser("~"), "~")
    t = re.sub(r"(/Users/|/home/|[A-Za-z]:\\\\?Users\\\\?)[^/\\\s]+", "~", t)
    def _so_ext(m):   # caminho fora da skill (pode ter espaço): sobra só a extensão do arquivo
        e = re.findall(r"\.(\w{1,5})$", m.group(0).rstrip(". "))
        return "~/…/*" + ("." + e[0] if e else "")
    t = re.sub(r"~[/\\](?:(?!, |: |;|\n|['\"]).)*", _so_ext, t)
    t = re.sub(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)*\.[A-Za-z]{2,}\b", "<email>", t)   # gsap@3.14.2 (CDN) não é e-mail
    t = re.sub(r"\b(sk|pk|rk|ghp|gho|ghs|xox[abp]|AKIA|AIza|ya29)[-_A-Za-z0-9]{12,}", "<chave>", t)
    t = re.sub(r"(?i)\b(api[_-]?key|token|secret|senha|password|authorization|bearer)\b(\s*[:=]\s*|\s+)\S+", r"\1=<oculto>", t)
    t = re.sub(r"\b[A-Za-z0-9_\-]{40,}\b", "<longo>", t)
    t = re.sub(r"(https?://[^\s?#]+)\?[^\s)\"']+", r"\1?<params>", t)
    for n in nomes:
        t = re.sub(re.escape(n), "<cliente>", t, flags=re.I)
    return t


def _assinatura(erro):
    """Mesmo erro em máquinas diferentes = mesma assinatura (números, caminhos e textos entre aspas viram curinga)."""
    e = re.sub(r"\d+(\.\d+)?", "N", erro.lower()); e = re.sub(r"['\"][^'\"]{0,80}['\"]", "S", e)
    e = re.sub(r"~[^\s:]*", "P", e); e = re.sub(r"\s+", " ", e).strip()[:300]
    return hashlib.sha1(e.encode()).hexdigest()[:10]


def registrar(titulo, erro, causa="", correcao="", arquivos=()):
    cfg = _config(); nomes = _nomes_privados(cfg); diff = ""
    if arquivos:
        diff = subprocess.run(["git", "-C", SKILL, "diff", "--"] + list(arquivos), capture_output=True, text=True).stdout
    rel = {"chave_envio": CHAVE_ENVIO, "tipo": "bug", "titulo": titulo, "erro": erro, "causa": causa, "correcao": correcao, "diff": diff}
    for k, lim in LIMITES.items():
        rel[k] = anonimizar(rel[k], nomes)[:lim]
    rel.update({"assinatura": _assinatura(rel["erro"] or rel["titulo"]), "versao": _versao(),
                "sistema": f"{platform.system()} {platform.release()} {platform.machine()}", "python": platform.python_version(),
                "editor": cfg.get("editor", ""), "motion": cfg.get("motion", ""), "instalacao": _instalacao(),
                "quando": time.strftime("%Y-%m-%dT%H:%M:%S")})
    os.makedirs(PEND, exist_ok=True)
    arq = os.path.join(PEND, f"{time.strftime('%Y%m%d-%H%M%S')}-{rel['assinatura']}.json")
    json.dump(rel, open(arq, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return arq


def _generico(v, i=1):
    if isinstance(v, list):
        return [f"Item {k + 1}" for k in range(len(v))]
    if isinstance(v, (int, float)):
        return v
    return f"Texto {i}"


def _limpar_spec(x):
    """Textos literais do spec (sem {{campo}}) viram genéricos; o resto (tempos, animações, posições) fica."""
    if isinstance(x, dict):
        return {k: (("Texto" if isinstance(v, str) and "{{" not in v else v) if k in ("texto", "text", "rotulo", "legenda")
                    else _limpar_spec(v)) for k, v in x.items()}
    if isinstance(x, list):
        return [_limpar_spec(v) for v in x]
    return x


# ------------------------------------------------------------ motion "bem diferente" do que já existe?
LIMIAR_PARECIDO = 0.70   # similaridade >= isto = variação de um motion que já existe: não manda
BASICAS = {"w", "h", "fps", "nome", "texto", "fonte", "tamanho", "cor", "x", "y", "inicio", "dur", "dur_entrada", "saida_em",
           "elementos", "tipo", "de", "para", "t", "ate", "sufixo", "vars", "passo", "lista", "anim", "entrada", "saida",
           "ease", "repetir", "centralizar"}
VISTOS = os.path.join(PASTA, "presets_vistos.json")


def tracos_motion(modelo):
    """Marcas da ESTRUTURA do motion (elementos, quantidades, animações, técnicas), com peso. Textos, cores, tempos e
    posições não contam: mudar só isso não faz um motion novo."""
    t, cont = {}, {}

    def add(k, w):
        t[k] = max(t.get(k, 0), w)

    def walk(x):
        if isinstance(x, dict):
            if isinstance(x.get("tipo"), str):
                tp = x["tipo"]; cont[tp] = cont.get(tp, 0) + 1
                add(f"el:{tp}", 3.0); add(f"el:{tp}#{min(cont[tp], 4)}", 1.0)
            if "repetir" in x:
                add("repetir", 2.0)
            for k in ("entrada", "saida"):
                if isinstance(x.get(k), str):
                    add(f"{k}:{x[k]}", 2.0)
            if isinstance(x.get("ease"), str):
                add(f"ease:{x['ease'].split('.')[0]}", 0.5)
            for a in (x.get("anim") or []) if isinstance(x.get("anim"), list) else [x.get("anim")] if isinstance(x.get("anim"), dict) else []:
                if isinstance(a, dict):
                    for k in a:
                        if k not in ("t", "dur", "ease", "de", "para", "inicio"):
                            add(f"anima:{k}", 1.5)
            for k, v in x.items():
                if k not in BASICAS:
                    add(f"usa:{k}", 1.0)
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    walk(modelo.get("spec", {}))
    if _e_hyperframes(modelo):
        arqs = modelo.get("_arquivos")
        if arqs is None and modelo.get("_pasta"):
            arqs = _arquivos_hf(modelo["_pasta"])
        for k, w in tracos_hf(arqs or {}, modelo.get("_pasta")).items():
            add(k, w)
    return t


# ------------------------------------------------------------ motion HyperFrames (a pasta é o motion)
CODIGO_HF = (".html", ".js", ".css", ".py")
TEXTO_HF = CODIGO_HF + (".md", ".json", ".svg", ".txt")
PULAR_DIRS_HF = {"node_modules", "renders", "snapshots", ".git", "__pycache__", ".hyperframes", "dist"}
LIMITE_ARQ_HF = 30000     # caracteres por arquivo (o resto é cortado com aviso)
LIMITE_PARTE = 45000      # célula da planilha do Formulário Google aguenta 50.000
PARTES_MAX = 8            # pacote maior que isso NÃO vai pela metade: o envio é recusado com o motivo
BIN_MAX = 60_000          # binário até esse tamanho vai embutido em base64; maior vai só pelo nome (fonte, mídia de exemplo)
PREVIAS_HF = ("exemplo.gif", "exemplo.mp4")   # prévia o dono renderiza de novo: não vai no pacote
PROPS_GSAP = ("x", "y", "z", "xPercent", "yPercent", "scale", "scaleX", "scaleY", "rotation", "rotationX", "rotationY",
              "rotationZ", "skewX", "skewY", "opacity", "autoAlpha", "filter", "clipPath", "strokeDashoffset",
              "strokeDasharray", "drawSVG", "morphSVG", "motionPath", "backgroundPosition", "width", "height",
              "borderRadius", "letterSpacing", "transformOrigin", "perspective", "boxShadow", "textShadow", "fontSize",
              "color", "backgroundColor", "attr", "text", "scrambleText", "innerText")
TECNICAS_HF = ("SplitText", "MotionPathPlugin", "DrawSVGPlugin", "MorphSVGPlugin", "ScrambleTextPlugin", "CustomEase",
               "Flip", "THREE", "lottie", "canvas", "getContext", "requestAnimationFrame", "stagger", "repeat", "yoyo",
               "timeline", "fromTo", "Math.random", "noise")
CSS_HF = ("backdrop-filter", "perspective", "preserve-3d", "mix-blend-mode", "mask", "clip-path", "blur(", "drop-shadow",
          "linear-gradient", "radial-gradient", "conic-gradient", "@keyframes", "text-stroke", "box-shadow",
          "text-shadow", "background-clip", "filter", "grid", "font-variation-settings")
TAGS_HF = ("svg", "canvas", "video", "img", "path", "circle", "rect", "line", "polyline", "text", "iframe", "audio")


def _e_hyperframes(m):
    return m.get("motor") == "hyperframes" or (not (m.get("spec") or {}).get("elementos") and "plano" in m)


def _arquivos_hf(pasta):
    """{caminho relativo: tamanho} de tudo na pasta do modelo (menos dependências, renders e o próprio modelo.json)."""
    r = {}
    for raiz, dirs, arqs in os.walk(pasta):
        dirs[:] = sorted(d for d in dirs if d not in PULAR_DIRS_HF and not d.startswith("."))
        for a in sorted(arqs):
            if a.startswith(".") or a == "modelo.json":
                continue
            f = os.path.join(raiz, a)
            r[os.path.relpath(f, pasta).replace(os.sep, "/")] = os.path.getsize(f)
    return r


def _ler_hf(pasta, rel):
    try:
        return open(os.path.join(pasta, rel), encoding="utf-8", errors="replace").read()
    except Exception:
        return ""


def tracos_hf(arquivos, pasta=None):
    """Marcas da estrutura de um motion HyperFrames lidas do código (tags, props animadas no GSAP, eases, técnicas, CSS).
    arquivos: {rel: tamanho} (lidos de pasta) ou {rel: texto}."""
    t = {}

    def add(k, w):
        t[k] = max(t.get(k, 0), w)
    for rel, v in arquivos.items():
        if not rel.endswith(CODIGO_HF) or rel.endswith(".min.js"):
            continue
        txt = v if isinstance(v, str) else _ler_hf(pasta, rel) if pasta else ""
        for tag in TAGS_HF:
            n = len(re.findall(rf"<{tag}[\s>/]", txt))
            if n:
                add(f"el:{tag}", 3.0); add(f"el:{tag}#{min(n, 4)}", 1.0)
        for metodo in set(re.findall(r"\b(?:gsap|tl|timeline)\.(to|from|fromTo|set|timeline)\b", txt)):
            add(f"gsap:{metodo}", 1.0)
        for prop in PROPS_GSAP:
            if re.search(rf"[{{,\s]{prop}\s*:", txt):
                add(f"anima:{prop}", 1.5)
        for e in set(re.findall(r"ease\s*:\s*['\"]([A-Za-z]+)", txt)):
            add(f"ease:{e}", 0.5)
        for tec in TECNICAS_HF:
            if tec in txt:
                add(f"usa:{tec}", 2.0)
        if rel.endswith((".css", ".html", ".py")):
            for c in CSS_HF:
                if c in txt:
                    add(f"css:{c}", 1.0)
    return t


def _cinza(r, g, b):
    y = round(0.2126 * r + 0.7152 * g + 0.0722 * b)
    return y, y, y


def _cores_neutras(txt, ids=()):
    """Cor da marca não sai: toda cor vira cinza da mesma luminosidade (o motion continua renderizável, com o contraste)."""
    def hexa(m):
        h = m.group(1)
        if h in ids:
            return m.group(0)   # é um #id do HTML (ex.: #cab), não cor
        if len(h) in (3, 4):
            h = "".join(c * 2 for c in h)
        r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
        y = _cinza(r, g, b)[0]
        return "#" + f"{y:02x}" * 3 + h[6:8]

    def rgb(m):
        vals = [v.strip() for v in re.split(r"[,\s/]+", m.group(2).strip()) if v.strip()]
        try:
            r, g, b = (float(v.rstrip("%")) * (2.55 if v.endswith("%") else 1) for v in vals[:3])
        except Exception:
            return m.group(0)
        y = _cinza(r, g, b)[0]
        return f"{m.group(1)}({y}, {y}, {y}" + (f", {vals[3]}" if len(vals) > 3 else "") + ")"
    t = re.sub(r"(?<![\w&])#([0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3,4})\b(?!\s*[{.>\[])", hexa, txt)
    t = re.sub(r"\b(rgba?)\(([^)]*)\)", rgb, t)
    t = re.sub(r"\b(hsla?\(\s*[\d.]+(?:deg)?\s*[,\s]\s*)[\d.]+%", r"\g<1>0%", t)
    return t


def _parece_frase(s):
    """String de JS/Python que é texto visível (2+ palavras de letras), não seletor, ease, fonte nem CSS."""
    if s[:1] in ".#[*:" or re.search(r"(?i)(^|\s)(div|span|path|svg|g|p|li|ul|img|circle|rect|line|text|b|i|s|em|"
                                      r"strong|section|video|canvas|polyline|use|tspan)(?=$|[\s.#\[:>,])", s):
        return False   # seletor CSS/DOM
    if len(s) < 4 or not re.search(r"[A-Za-zÀ-ÿ]{2,}\s+[A-Za-zÀ-ÿ]{2,}", s) or re.search(r"[{};=<>#$`\\]|\.\w+\(|px\b|%", s):
        return False
    if re.search(r"(?i)\b(serif|sans|mono|ease|power\d|inherit|solid|bold|italic|translate|rotate|scale|none|auto)\b", s):
        return False
    letras = sum(c.isalpha() or c.isspace() for c in s)
    return letras / len(s) > 0.75


def _textos_genericos(txt, ext):
    """Texto do cliente não sai: texto visível do HTML e frases em strings de JS/Python/JSON viram "Texto"."""
    if ext == ".html":
        partes = re.split(r"(<script\b.*?</script>|<style\b.*?</style>)", txt, flags=re.S | re.I)
        for i in range(0, len(partes), 2):
            partes[i] = re.sub(r">(\s*)([^<>]*?[A-Za-zÀ-ÿ]{2,}[^<>]*?)(\s*)<", r">\1Texto\3<", partes[i])
            partes[i] = re.sub(r'\b(alt|title|aria-label|placeholder)="[^"]*"', r'\1="Texto"', partes[i])
        for i in range(1, len(partes), 2):
            if partes[i].lower().startswith("<script"):
                partes[i] = _textos_genericos(partes[i], ".js")
        return "".join(partes)
    if ext in (".js", ".py", ".json"):
        return re.sub(r"""(?P<q>["'])((?:(?!(?P=q))[^\\\n]|\\.){4,})(?P=q)""",
                      lambda m: f"{m.group('q')}Texto{m.group('q')}" if _parece_frase(m.group(2)) else m.group(0), txt)
    return txt


def _prioridade_hf(rel):
    b = rel.rsplit("/", 1)[-1].lower()
    ordem = ["preset.md", "leia.md", "readme.md", "gerar.py"]
    if b in ordem:
        return (ordem.index(b), rel)
    if rel.startswith("kit/"):
        return (5, rel)
    if b in ("index.html", "hyperframes.json"):
        return (6, rel)
    return (7 if rel.endswith(CODIGO_HF) else 8, rel)


class PacoteGrande(Exception):
    """O pacote não cabe em PARTES_MAX partes: não manda pela metade."""


def _empacotar_hf(corpo_modelo, arquivos, pasta, nomes):
    """Pacote de texto COMPLETO com os arquivos da pasta do modelo, já limpos, em até PARTES_MAX partes de LIMITE_PARTE.
    Formato (relatar.py desempacotar lê): '--- arquivo: <rel> ---' + conteúdo; '--- binario: <rel> (base64) ---' para
    binário pequeno; '--- manifesto ---' com o sha1 de cada arquivo COMO FOI ENVIADO (o dono confere que chegou tudo).
    Não corta: se não couber, levanta PacoteGrande. Binário grande e biblioteca pública minificada vão pelo nome."""
    import base64
    blocos, fora, manifesto = [f"--- arquivo: modelo.json ---\n{corpo_modelo}\n"], [], {}
    manifesto["modelo.json"] = hashlib.sha1(corpo_modelo.encode()).hexdigest()
    ids = {i for rel in arquivos if rel.endswith((".html", ".py", ".js"))
           for i in re.findall(r"""\bid\s*=\s*["']([\w-]+)""", _ler_hf(pasta, rel))}
    for rel in sorted(arquivos, key=_prioridade_hf):
        ext = os.path.splitext(rel)[1].lower(); rel_env = anonimizar(rel, nomes)
        if rel.rsplit("/", 1)[-1] in PREVIAS_HF or rel.startswith("renders/") or rel in ("manifesto.json",):
            continue
        if ext not in TEXTO_HF:
            if arquivos[rel] <= BIN_MAX:
                dados = open(os.path.join(pasta, rel), "rb").read()
                manifesto[rel_env] = hashlib.sha1(dados).hexdigest()
                blocos.append(f"--- binario: {rel_env} (base64) ---\n{base64.b64encode(dados).decode()}\n")
            else:
                fora.append(f"{rel} ({arquivos[rel] // 1024} KB, binário grande: vai pelo nome)")
            continue
        if rel.endswith(".min.js"):
            fora.append(f"{rel} ({arquivos[rel] // 1024} KB, biblioteca minificada: o dono usa a pública pelo nome)"); continue
        txt = _ler_hf(pasta, rel)
        txt = re.sub(r"data:[\w/+.-]+;base64,[A-Za-z0-9+/=]+", "data:<removido>", txt)
        if ext != ".md" and rel not in ("preset.json",):
            txt = _textos_genericos(_cores_neutras(txt, ids), ext)
        txt = anonimizar(txt, nomes)
        txt = re.sub(r"[ \t]+\n", "\n", txt); txt = re.sub(r"\n{3,}", "\n\n", txt)
        manifesto[rel_env] = hashlib.sha1(txt.encode()).hexdigest()
        blocos.append(f"--- arquivo: {rel_env} ---\n{txt}\n")
    blocos.append("--- manifesto ---\n" + json.dumps({"arquivos": manifesto, "por_nome": fora}, ensure_ascii=False) + "\n")
    partes, atual = [], ""
    for b in blocos:
        while b:
            if len(atual) + len(b) <= LIMITE_PARTE - 300:
                atual += b; b = ""
            elif atual:
                partes.append(atual); atual = ""
            else:   # bloco sozinho maior que a parte: quebra e continua na próxima
                corte = LIMITE_PARTE - 300
                atual, b = b[:corte], "--- continua ---\n" + b[corte:]
    if atual:
        partes.append(atual)
    if len(partes) > PARTES_MAX:
        raise PacoteGrande(f"o preset precisa de {len(partes)} partes e o limite é {PARTES_MAX}: "
                           "tire mídias de exemplo grandes da pasta (vão pelo nome) ou divida o preset")
    n = len(partes)
    return [f"=== PACOTE HYPERFRAMES ogab v1 parte {i}/{n} ===\n{p}" for i, p in enumerate(partes, 1)]


def desempacotar(texto, destino):
    """(dono) Remonta a pasta do preset a partir das colunas diff (todas as partes, em qualquer ordem, coladas num texto).
    Binários em base64 voltam a ser arquivos; o manifesto vai para manifesto_envio.json (conferir com conferir_pacote)."""
    import base64
    pecas = re.split(r"^=== PACOTE (?:HYPERFRAMES|INVENCAO) ogab v1 parte (\d+)/\d+ ===\n", texto, flags=re.M)
    corpo = "".join(p for _, p in sorted(((int(pecas[i]), pecas[i + 1]) for i in range(1, len(pecas) - 1, 2))))
    corpo = re.sub(r"\n?--- continua ---\n", "", corpo)
    corpo = corpo.split("--- fora do pacote ---")[0]
    manifesto = None
    if "\n--- manifesto ---\n" in "\n" + corpo:
        corpo, _, resto = ("\n" + corpo).partition("\n--- manifesto ---\n"); corpo = corpo[1:]
        try:
            manifesto = json.loads(resto.strip())
        except Exception:
            manifesto = {"ilegivel": True}
    feitos = []
    for tipo, rel, conteudo in re.findall(r"^--- (arquivo|binario): (.+?)(?: \(base64\))? ---\n(.*?)(?=^--- (?:arquivo|binario): |\Z)",
                                          corpo, flags=re.M | re.S):
        rel = rel.strip()
        if rel.startswith(("/", "\\")) or ".." in rel.split("/") or ":" in rel or "<" in rel:
            continue   # caminho estranho (ou anonimizado): não grava fora da pasta
        alvo = os.path.join(destino, rel)
        os.makedirs(os.path.dirname(alvo) or destino, exist_ok=True)
        conteudo = conteudo[:-1] if conteudo.endswith("\n") else conteudo
        if tipo == "binario":
            open(alvo, "wb").write(base64.b64decode(conteudo.strip()))
        else:
            open(alvo, "w", encoding="utf-8").write(conteudo)
        feitos.append(rel)
    if manifesto is not None:
        json.dump(manifesto, open(os.path.join(destino, "manifesto_envio.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return feitos


def conferir_pacote(pasta):
    """(dono) Confere a pasta remontada contra o manifesto_envio.json: devolve (completo, [problemas])."""
    m = os.path.join(pasta, "manifesto_envio.json")
    if not os.path.exists(m):
        return False, ["pacote sem manifesto (enviado por versão antiga da skill: pode estar incompleto)"]
    try:
        man = json.load(open(m, encoding="utf-8"))
    except Exception:
        return False, ["manifesto ilegível"]
    prob = []
    for rel, sha in (man.get("arquivos") or {}).items():
        p = os.path.join(pasta, rel)
        if not os.path.exists(p):
            prob.append(f"faltou: {rel}"); continue
        dados = open(p, "rb").read()
        if hashlib.sha1(dados).hexdigest() != sha:
            prob.append(f"diferente do enviado: {rel}")
    prob += [f"por nome: {x}" for x in man.get("por_nome", [])]
    return not any(x.startswith(("faltou", "diferente")) for x in prob), prob


def similaridade(a, b):
    ks = set(a) | set(b)
    if not ks:
        return 1.0
    return sum(min(a.get(k, 0), b.get(k, 0)) for k in ks) / sum(max(a.get(k, 0), b.get(k, 0)) for k in ks)


def _referencias():
    refs = {}
    for f in glob.glob(os.path.join(SKILL, "biblioteca_motions", "*", "modelo.json")):
        try:
            m = json.load(open(f, encoding="utf-8")); m["_pasta"] = os.path.dirname(f)
            refs["biblioteca:" + os.path.basename(os.path.dirname(f))] = tracos_motion(m)
        except Exception:
            pass
    for d in glob.glob(os.path.join(SKILL, "presets", "*", "")):   # presets HyperFrames da skill (kit + gerar.py)
        try:
            arqs = _arquivos_hf(d); nome = os.path.basename(os.path.dirname(d))
            for sufixo, sel in (("", arqs), ("/kit", {k: v for k, v in arqs.items() if not k.startswith("exemplo/")})):
                tr = tracos_hf(sel, d)   # com e sem o exemplo/ (cópia de um preset pode vir só com o kit)
                if tr:
                    refs["preset:" + nome + sufixo] = tr
        except Exception:
            pass
    try:
        for nome, tr in json.load(open(VISTOS, encoding="utf-8")).items():
            refs["enviado:" + nome] = tr
    except Exception:
        pass
    return refs


def parecido(modelo, ignorar=""):
    """[(similaridade, referência)] do mais parecido ao menos parecido."""
    tr = tracos_motion(modelo)
    return sorted(((round(similaridade(tr, r), 2), n) for n, r in _referencias().items()
                   if n.split(":", 1)[1].split("/")[0] != ignorar),
                  reverse=True)


def registrar_preset(caminho, motivo=None, saidas=None, destino=None, forcar=False):
    """Grava o relato do motion novo em pendentes/ (só sai com consentimento). Devolve o arquivo (o 1º, se o pacote
    HyperFrames vier em partes) ou None; motivo (lista), se passado, recebe o porquê de não registrar."""
    motivo = motivo if motivo is not None else []
    arq = os.path.join(caminho, "modelo.json") if os.path.isdir(caminho) else caminho
    pasta_modelo = os.path.dirname(os.path.abspath(arq))
    if os.path.isdir(caminho) and not os.path.exists(arq):
        m = modelo_de_preset(caminho)   # presets/<nome>/ criado pelo usuário (PRESET.md + kit), sem modelo.json
    else:
        m = json.load(open(arq, encoding="utf-8"))
    hf = _e_hyperframes(m)
    if hf:
        m["_arquivos"], m["_pasta"] = _arquivos_hf(pasta_modelo), pasta_modelo
        if not any(r.endswith(CODIGO_HF) for r in m["_arquivos"]):
            motivo.append("modelo HyperFrames sem os arquivos do motion (salvar com biblioteca_motions.py salvar --pasta)")
            return None   # sem os arquivos não dá para recriar: relato inútil para o dono
    ranking = parecido(m, ignorar=m.get("nome", ""))
    if ranking and ranking[0][0] >= LIMIAR_PARECIDO:
        motivo.append(f"parecido demais com {ranking[0][1]} ({ranking[0][0]:.0%})")
        return None   # variação de um motion que já existe (mesma estrutura com outros textos/tempos): não manda
    tracos = tracos_motion(m)
    arquivos = m.pop("_arquivos", {}); m.pop("_pasta", None)
    m.pop("autor", None)
    for i, (k, c) in enumerate((m.get("campos") or {}).items(), 1):
        if isinstance(c, dict) and "exemplo" in c:
            c["exemplo"] = _generico(c["exemplo"], i)
    m["spec"] = _limpar_spec(m.get("spec", {}))
    cfg = _config(); nomes = _nomes_privados(cfg)
    corpo = anonimizar(json.dumps(m, ensure_ascii=False, indent=1), nomes)[:40000]
    estrutura = json.dumps(m.get("spec", {}), sort_keys=True)
    partes = [corpo]
    if hf:
        try:
            partes = _empacotar_hf(corpo, arquivos, pasta_modelo, nomes)
        except PacoteGrande as e:
            motivo.append(str(e)); return None
        estrutura = json.dumps(tracos, sort_keys=True)   # spec vazio: assinatura vem da estrutura dos arquivos
    rel = {"chave_envio": CHAVE_ENVIO, "tipo": "preset", "titulo": anonimizar(m.get("nome", "motion"), nomes)[:200],
           "erro": anonimizar(m.get("descricao", ""), nomes)[:3000], "causa": ", ".join(m.get("tags", []))[:2000],
           "correcao": (f"novidade {1 - (ranking[0][0] if ranking else 0):.0%} (mais parecido: "
                        f"{ranking[0][1] if ranking else 'nenhum'} {ranking[0][0] if ranking else 0:.0%}); "
                        f"dur {m.get('dur', '?')} s; campos: {', '.join(m.get('campos', {}))}"
                        + (f"; HyperFrames: {len(arquivos)} arquivo(s) em {len(partes)} parte(s), "
                           f"remontar com relatar.py desempacotar" if hf else ""))[:3000], "diff": partes[0],
           "assinatura": hashlib.sha1(estrutura.encode()).hexdigest()[:10], "versao": _versao(),
           "sistema": f"{platform.system()} {platform.release()} {platform.machine()}", "python": platform.python_version(),
           "editor": cfg.get("editor", ""), "motion": cfg.get("motion", ""), "instalacao": _instalacao(),
           "quando": time.strftime("%Y-%m-%dT%H:%M:%S")}
    if not forcar and any(rel["assinatura"] in os.path.basename(f) for f in glob.glob(os.path.join(PASTA, "*", "*.json"))):
        motivo.append("este motion (mesma estrutura) já foi registrado")
        return None   # este motion (mesma estrutura) já foi registrado
    dest = destino or PEND
    os.makedirs(dest, exist_ok=True)
    if not destino:   # simulação (destino próprio) não conta como visto
        try:
            vistos = json.load(open(VISTOS, encoding="utf-8"))
        except Exception:
            vistos = {}
        vistos[rel["titulo"]] = tracos
        json.dump(vistos, open(VISTOS, "w", encoding="utf-8"), ensure_ascii=False)
    carimbo = time.strftime('%Y%m%d-%H%M%S')
    saidas = saidas if saidas is not None else []
    for i, diff in enumerate(partes, 1):
        r = dict(rel, diff=diff)
        if len(partes) > 1:
            r["titulo"] = f"{rel['titulo']} (parte {i}/{len(partes)})"[:200]
        saida = os.path.join(dest, f"{carimbo}-preset-{rel['assinatura']}" + (f"-p{i}" if len(partes) > 1 else "") + ".json")
        json.dump(r, open(saida, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        saidas.append(saida)
    return saidas[0]


def modelo_de_preset(pasta):
    """Modelo HyperFrames montado a partir de uma pasta presets/<nome>/ (PRESET.md, gerar.py, kit/) sem modelo.json."""
    nome = os.path.basename(os.path.normpath(pasta))
    desc, titulo = "", nome
    md = os.path.join(pasta, "PRESET.md")
    if os.path.exists(md):
        linhas = open(md, encoding="utf-8").read().splitlines()
        for l in linhas:
            if l.startswith("# "):
                titulo = l[2:].strip(); break
        para = []
        for l in linhas:
            if l.startswith("#") or l.startswith("<") or not l.strip():
                if para:
                    break
                continue
            para.append(l.strip())
        desc = " ".join(para)
    plano = os.path.join(pasta, "exemplo", "plano.json")
    campos = {}
    try:
        for k, v in json.load(open(plano, encoding="utf-8")).items():
            if k not in ("w", "h", "fps", "dur"):
                campos[k] = {"tipo": "lista" if isinstance(v, list) else "numero" if isinstance(v, (int, float))
                             else "texto", "exemplo": v}
    except Exception:
        pass
    return {"nome": nome, "descricao": (desc or titulo)[:600], "tags": ["preset"], "motor": "hyperframes",
            "campos": campos, "spec": {}, "_arquivos": None}


VARRIDOS = os.path.join(PASTA, "varridos.json")


def _impressao(pasta):
    """Muda quando algum arquivo de código/texto da pasta muda (para não varrer de novo o que não mudou)."""
    h = hashlib.sha1()
    for rel, tam in sorted(_arquivos_hf(pasta).items()):
        if rel.endswith(TEXTO_HF):
            h.update(f"{rel}:{tam}:{int(os.path.getmtime(os.path.join(pasta, rel)))}".encode())
    return h.hexdigest()[:12]


def _presets_do_usuario():
    """Pastas de motion que ESTE usuário criou: presets/<nome>/ fora do git (não vieram no update) e
    biblioteca_motions_local/<nome>/ (salvos pela biblioteca)."""
    r = []
    rastreados = set()
    try:
        out = subprocess.run(["git", "-C", SKILL, "ls-files", "presets"], capture_output=True, text=True, timeout=20).stdout
        rastreados = {l.split("/")[1] for l in out.splitlines() if l.count("/") >= 2}
    except Exception:
        return r   # sem git não dá para saber o que é do usuário
    for d in sorted(glob.glob(os.path.join(SKILL, "presets", "*", ""))):
        nome = os.path.basename(os.path.dirname(d))
        if nome not in rastreados and any(a.endswith(CODIGO_HF) for a in _arquivos_hf(d)):
            r.append(os.path.dirname(d))
    for d in sorted(glob.glob(os.path.join(SKILL, "biblioteca_motions_local", "*", "modelo.json"))):
        r.append(os.path.dirname(d))
    return r


def varrer():
    """Registra (em pendentes/, só sai com consentimento) os motions novos deste usuário que ainda não foram
    avaliados. Variação de preset que já existe não vai (LIMIAR_PARECIDO). Devolve [(pasta, resultado)]."""
    if _config().get("dono_biblioteca"):
        return []   # o dono publica direto
    try:
        vistos = json.load(open(VARRIDOS, encoding="utf-8"))
    except Exception:
        vistos = {}
    feitos = []
    for pasta in _presets_do_usuario():
        chave = os.path.relpath(pasta, SKILL); imp = _impressao(pasta)
        if vistos.get(chave) == imp:
            continue
        porque, arqs = [], []
        try:
            import meus_presets   # acha e resolve tudo que o preset precisa (arquivos de fora, manifesto, preset.json)
            prep = meus_presets.preparar(pasta, render=False)
            if prep["manifesto"]["faltando"]:
                raise ValueError("faltando arquivo: " + ", ".join(prep["manifesto"]["faltando"][:5]))
            res = registrar_preset(pasta, porque, saidas=arqs)
        except Exception as e:
            res, porque = None, [f"erro: {e}"]
        try:
            import meus_presets
            est = meus_presets._estado()
            est[chave] = ({"estado": "na fila", "arquivos": arqs, "impressao": _impressao(pasta)} if res
                          else {"estado": "não enviado: " + ("; ".join(porque) or "?")})
            meus_presets._salvar_estado(est)
        except Exception:
            pass
        imp = _impressao(pasta)   # preparar pode ter mudado a pasta (assets/, preset.json)
        vistos[chave] = imp
        feitos.append((chave, res or "não registrado: " + ("; ".join(porque) or "?")))
    porque = []
    try:
        inv = registrar_invencoes(porque)
    except Exception as e:
        inv, porque = [], [f"erro: {e}"]
    if inv:
        feitos.append(("invenções na skill", f"{len(inv)} parte(s) registrada(s)"))
    if feitos:
        os.makedirs(PASTA, exist_ok=True)
        json.dump(vistos, open(VARRIDOS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return feitos


# ------------------------------------------------------------ invenções (scripts novos e melhorias na skill)
EXT_INVENCAO = (".py", ".js", ".mjs", ".css", ".html", ".md", ".json", ".sh", ".ps1", ".jsx", ".lua", ".txt")
FORA_INVENCAO = ("presets/", "biblioteca_motions_local/", "clientes/", "assets/", "biblioteca_sfx/", "config.json",
                 "relatos/destino.json", "voz_local/modelos/")
MIN_LINHAS_INVENCAO = 6   # menos que isso é ajuste, não invenção
# pasta de temporário (scripts gerados na hora, com conteúdo de cliente) nunca é invenção (relato de 27/10/2026)
TEMP_INVENCAO = re.compile(r"(^|/)(_?tmp|_?temp|_?cache)(/|$)|\.parcial$", re.I)
RELEASE_LOCAL = os.path.expanduser("~/.claude/ogab_release_local.json")


def _git(*args):
    r = subprocess.run(["git", "-C", SKILL, *args], capture_output=True, text=True, timeout=60)
    return r.stdout if r.returncode == 0 else ""


def _do_release():
    """{caminho: sha256} que o update pelo servidor (atualizar.py) gravou. Quem atualiza pelo servidor fica com o git
    parado na versão da instalação: sem isto, o próprio update oficial aparecia como "invenção" do usuário."""
    try:
        return json.load(open(RELEASE_LOCAL, encoding="utf-8")).get(SKILL, {})
    except Exception:
        return {}


def _oficial(rel, release):
    """O arquivo está igual ao do release oficial (não foi o usuário que mudou)."""
    sha = release.get(rel)
    if not sha:
        return False
    try:
        return hashlib.sha256(open(os.path.join(SKILL, rel), "rb").read()).hexdigest() == sha
    except Exception:
        return False


def _blocos_invencao():
    """[(rótulo, texto)] do que este usuário mudou ou criou na skill (fora presets, que vão pelo varrer de motions)."""
    blocos, release = [], _do_release()
    for rel in sorted(_git("ls-files", "--others", "--exclude-standard").splitlines()):
        if rel.startswith(FORA_INVENCAO) or not rel.endswith(EXT_INVENCAO) or "__pycache__" in rel \
                or TEMP_INVENCAO.search(rel) or _oficial(rel, release):
            continue
        f = os.path.join(SKILL, rel)
        if os.path.getsize(f) > 200_000:
            continue
        try:
            blocos.append((f"arquivo novo: {rel}", open(f, encoding="utf-8").read()))
        except Exception:
            pass
    fora = [f":(exclude){x}*" if x.endswith("/") else f":(exclude){x}" for x in FORA_INVENCAO]
    mudados = [r for r in _git("diff", "HEAD", "--name-only", "--", ".", *fora).splitlines()
               if r and not TEMP_INVENCAO.search(r) and not _oficial(r, release)]
    d = _git("diff", "HEAD", "--", *mudados) if mudados else ""
    if d.strip():
        blocos.append(("melhorias nos arquivos da skill (git diff)", d))
    for linha in _git("stash", "list").splitlines():   # o doctor guarda as mudanças locais antes do update
        ref = linha.split(":", 1)[0]
        if "doctor" in linha:
            sd = _git("stash", "show", "-p", "--include-untracked", ref, "--", ".", *fora) or _git("stash", "show", "-p", ref)
            if sd.strip():
                blocos.append((f"guardado pelo doctor antes do update ({ref})", sd))
    return blocos


def registrar_invencoes(motivo=None):
    """Grava em pendentes/ (só sai com o aceite dos termos) as invenções deste usuário na skill, anonimizadas e em
    partes de LIMITE_PARTE. Não repete o mesmo conteúdo (assinatura = hash). Devolve a lista de arquivos gravados."""
    motivo = motivo if motivo is not None else []
    blocos = _blocos_invencao()
    linhas = sum(t.count("\n") for _, t in blocos)
    if not blocos or linhas < MIN_LINHAS_INVENCAO:
        motivo.append("nada novo na skill"); return []
    cfg = _config(); nomes = _nomes_privados(cfg)
    corpo = ""
    for rot, txt in blocos:
        txt = re.sub(r"data:[\w/+.-]+;base64,[A-Za-z0-9+/=]+", "data:<removido>", txt)
        txt = anonimizar(txt, nomes)
        if len(txt) > LIMITE_ARQ_HF:
            txt = txt[:LIMITE_ARQ_HF] + f"\n... cortado: {len(txt) - LIMITE_ARQ_HF} caracteres a mais"
        corpo += f"--- {anonimizar(rot, nomes)} ---\n{txt}\n"
    assinatura = "inv-" + hashlib.sha1(corpo.encode()).hexdigest()[:10]
    if any(assinatura in os.path.basename(f) for f in glob.glob(os.path.join(PASTA, "*", "*.json"))):
        motivo.append("estas invenções já foram registradas"); return []
    partes = [corpo[i:i + LIMITE_PARTE - 300] for i in range(0, len(corpo), LIMITE_PARTE - 300)][:PARTES_MAX]
    n = len(partes)
    titulos = [r for r, _ in blocos]
    os.makedirs(PEND, exist_ok=True); carimbo = time.strftime("%Y%m%d-%H%M%S"); saidas = []
    for i, p_ in enumerate(partes, 1):
        rel = {"chave_envio": CHAVE_ENVIO, "tipo": "invencao",
               "titulo": (f"invenção na skill ({len(blocos)} item(ns))" + (f" (parte {i}/{n})" if n > 1 else ""))[:200],
               "erro": anonimizar("; ".join(titulos), nomes)[:3000], "causa": f"{linhas} linhas",
               "correcao": "remontar: relatar.py desempacotar (partes coladas) ou ler direto", "diff":
               f"=== PACOTE INVENCAO ogab v1 parte {i}/{n} ===\n{p_}", "assinatura": assinatura, "versao": _versao(),
               "sistema": f"{platform.system()} {platform.release()} {platform.machine()}", "editor": cfg.get("editor", ""),
               "instalacao": _instalacao(), "quando": time.strftime("%Y-%m-%dT%H:%M:%S")}
        f = os.path.join(PEND, f"{carimbo}-invencao-{assinatura}" + (f"-p{i}" if n > 1 else "") + ".json")
        json.dump(rel, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=1); saidas.append(f)
    return saidas


def _log(msg):
    os.makedirs(PASTA, exist_ok=True)
    with open(os.path.join(PASTA, "envio.log"), "a", encoding="utf-8") as f:
        f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + msg + "\n")


def enviar():
    """Envia os pendentes para a VPS do autor (/v1/preset): presets (tipo=preset, partes juntas) e relatos de erro
    (tipo=relato, como txt). Precisa de chave de licenca; na maquina do dono nao envia."""
    cfg = _config()
    if cfg.get("dono_biblioteca"):
        return 0
    try:
        import licenca
    except Exception as e:
        _log(f"sem licenca.py: {e}"); return 0
    d = licenca._ler()
    if not d.get("key"):
        return 0   # ainda sem chave: nada a enviar
    key, maq = d["key"], licenca.maquina()
    usuario = str((cfg.get("comunidade") or {}).get("nome") or "anon")[:60]
    so_apresentacao = cfg.get("relatos") is not True
    try:
        for chave, res in ([] if so_apresentacao else varrer()):
            _log(f"varredura {chave}: {res}")
    except Exception as e:
        _log(f"varredura falhou: {e}")
    os.makedirs(ENV, exist_ok=True)
    presets, soltos = {}, []
    for arq in sorted(glob.glob(os.path.join(PEND, "*.json")))[:40]:
        try:
            rel = json.load(open(arq, encoding="utf-8"))
        except Exception:
            continue
        if so_apresentacao and rel.get("tipo") != "usuario":
            continue
        if rel.get("tipo") == "preset":
            if int(cfg.get("relatos_v", 1)) < CONSENTIMENTO_V:
                continue
            g = presets.setdefault(rel.get("assinatura", os.path.basename(arq)), {"rel": rel, "arqs": [], "diffs": []})
            g["arqs"].append(arq); g["diffs"].append(rel.get("diff", ""))
        else:
            soltos.append((arq, rel))

    def _mandar(nome, pacote, tipo):
        return licenca._post("/v1/preset", {"key": key, "maquina": maq, "usuario": usuario,
                                            "preset": str(nome)[:80], "pacote": pacote, "tipo": tipo})

    def _mover(arqs):
        for arq in arqs:
            os.replace(arq, os.path.join(ENV, os.path.basename(arq)))

    n = 0
    for sig, g in presets.items():
        nome = re.sub(r"\s*\(parte \d+/\d+\)", "", g["rel"].get("titulo", "motion"))
        r = _mandar(nome, "\n".join(g["diffs"]), "preset")
        if r is None:
            break   # sem internet: tenta na proxima abertura
        if r.get("status") == "ok":
            _mover(g["arqs"]); n += 1
    rot = [("titulo", "titulo"), ("erro", "erro"), ("causa", "causa"), ("correcao", "correcao"),
           ("versao", "versao"), ("sistema", "sistema"), ("editor", "editor"), ("diff", "diff")]
    for arq, rel in soltos:
        txt = "\n".join(f"[{r}] {rel.get(k, '')}" for k, r in rot if rel.get(k))
        res = _mandar(rel.get("titulo") or "relato", txt, "relato")
        if res is None:
            break
        if res.get("status") == "ok":
            _mover([arq]); n += 1
    if n:
        _log(f"{n} item(ns) enviado(s) para a VPS")
    return n

def status():
    cfg = _config()
    cons = "sim" if cfg.get("relatos") is True else "não" if cfg.get("relatos") is False else "ainda não respondeu"
    return {"consentimento": cons, "maquina_do_dono": bool(cfg.get("dono_biblioteca")), "destino": "vps",
            "pendentes": len(glob.glob(os.path.join(PEND, "*.json"))), "enviados": len(glob.glob(os.path.join(ENV, "*.json")))}


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        raise SystemExit(__doc__)
    if a[0] == "consentir" and len(a) >= 2:
        print("relatos:", "sim" if consentir(a[1].lower() in ("sim", "s", "yes", "y", "1", "true")) else "não")
    elif a[0] == "perguntar":
        if precisa_perguntar():
            print("PERGUNTAR: " + PERGUNTA)
    elif a[0] == "registrar":
        def arg(n, pad=""):
            return a[a.index(n) + 1] if n in a else pad
        arqs = [a[i + 1] for i, x in enumerate(a) if x == "--arquivo" and i + 1 < len(a)]
        print(registrar(arg("--titulo"), arg("--erro"), arg("--causa"), arg("--correcao"), arqs))
    elif a[0] == "preset" and len(a) >= 2:
        porque = []
        print(registrar_preset(a[1], porque) or "não registrado: " + ("; ".join(porque) or "?"))
    elif a[0] == "desempacotar" and len(a) >= 3:
        feitos = desempacotar(open(a[1], encoding="utf-8").read(), a[2])
        print(f"{len(feitos)} arquivo(s) em {a[2]}:\n  " + "\n  ".join(feitos))
    elif a[0] == "parecido" and len(a) >= 2:
        arq = os.path.join(a[1], "modelo.json") if os.path.isdir(a[1]) else a[1]
        m = json.load(open(arq, encoding="utf-8")); m["_pasta"] = os.path.dirname(os.path.abspath(arq))
        for sim, n in parecido(m, ignorar=m.get("nome", ""))[:5]:
            print(f"  {sim:.0%}  {n}" + ("  <- parecido demais, não seria enviado" if sim >= LIMIAR_PARECIDO else ""))
    elif a[0] == "varrer":
        for chave, res in varrer() or [("-", "nada novo para avaliar")]:
            print(f"  {chave}: {res}")
    elif a[0] == "enviar":
        enviar()
    elif a[0] == "status":
        print(json.dumps(status(), ensure_ascii=False))
    else:
        raise SystemExit(__doc__)
