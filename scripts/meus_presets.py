#!/usr/bin/env python3
"""Presets que o USUÁRIO criou: achar tudo o que precisam para funcionar, preparar a prévia e mandar COMPLETOS à
comunidade (Formulário Google do dono, via relatar.py). Depois de enviado, o preset aparece no /ogab menu.

  python3 meus_presets.py listar [--json]               # presets locais: nome, categoria, prévia, estado do envio
  python3 meus_presets.py dependencias <pasta> [--json] # tudo que o preset usa e de onde vem
  python3 meus_presets.py preparar <pasta> [--categoria X] [--sem-render]
                                                        # resolve dependências, preset.json, exemplo.gif, manifesto.json
  python3 meus_presets.py enviar <pasta> [--simular <pasta_saida>]
                                                        # registra o pacote completo e envia (ou só grava, --simular)

Presets locais = pastas em presets/ que não vieram no update (fora do git) e biblioteca_motions_local/<nome>/.
Dependências: o que está dentro da pasta vai junto; arquivo rastreado da skill já existe no dono; arquivo da skill
NÃO rastreado vai junto; arquivo de FORA da skill (Área de Trabalho, Downloads...) é copiado para assets/ e a
referência é reescrita; CDN e npm ficam anotados com a versão; pacote Python que não é da biblioteca padrão fica
anotado. Nada é mandado pela metade: se o pacote não couber, o envio é recusado com o motivo.
Na máquina do dono ("dono_biblioteca": true) nada é enviado: os presets locais dele aparecem direto no menu.
"""
import glob, hashlib, json, os, re, shutil, subprocess, sys, tempfile

AQUI = os.path.dirname(os.path.abspath(__file__)); SKILL = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
import relatar  # noqa: E402
from componentes import hf  # noqa: E402

ESTADO = os.path.join(relatar.PASTA, "presets_enviados.json")
CATEGORIAS = ("apresentador", "ideia", "lista", "dados", "produto", "social", "marca")
PALAVRAS_CAT = (("marca", ("logo", "abertura", "vinheta", "marca")), ("dados", ("número", "numero", "gráfico", "grafico", "dado", "contador", "marco")),
                ("produto", ("app", "produto", "lançamento", "lancamento", "site", "saas", "tela")),
                ("social", ("comentário", "comentario", "depoimento", "entrevista", "podcast", "prova")),
                ("lista", ("lista", "ranking", "passo", "top ", "tier")),
                ("apresentador", ("apresentador", "talking", "pessoa", "rosto", "legenda", "câmera", "camera")))
EXT_TEXTO = (".html", ".htm", ".js", ".mjs", ".css", ".py", ".json")
EXT_MIDIA = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".mp4", ".mov", ".webm", ".mp3", ".wav", ".m4a",
             ".ttf", ".otf", ".woff", ".woff2", ".json", ".js", ".css", ".html", ".py", ".lottie", ".glb", ".gltf")
LIBS_CDN = {"gsap": "gsap", "three": "three", "lottie": "lottie-web", "matter": "matter-js", "rough": "roughjs", "anime": "animejs"}


def _sha1(p):
    h = hashlib.sha1()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 16), b""):
            h.update(b)
    return h.hexdigest()


def _rastreados():
    try:
        out = subprocess.run(["git", "-C", SKILL, "ls-files"], capture_output=True, text=True, timeout=30).stdout
        return set(out.splitlines())
    except Exception:
        return set()


def _estado():
    try:
        return json.load(open(ESTADO, encoding="utf-8"))
    except Exception:
        return {}


def _salvar_estado(e):
    os.makedirs(relatar.PASTA, exist_ok=True)
    json.dump(e, open(ESTADO, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def _chave(pasta):
    return os.path.relpath(os.path.abspath(pasta), SKILL).replace(os.sep, "/")


# ---------------------------------------------------------------- dependências

_RE_REFS = [
    re.compile(r"""\b(?:src|href|poster|data-src)\s*=\s*["']([^"'#?]+)"""),             # html
    re.compile(r"""url\(\s*["']?([^"')#?]+)"""),                                         # css
    re.compile(r"""@import\s+["']([^"']+)"""),                                           # css
    re.compile(r"""\bimport\s+(?:[\w*{}\s,]+\s+from\s+)?["']([^"']+)["']"""),             # js
    re.compile(r"""\b(?:import|require)\(\s*["']([^"']+)["']"""),                        # js
    re.compile(r"""\bfetch\(\s*["']([^"']+)["']"""),                                     # js
]
_RE_PY_IMPORT = re.compile(r"^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))", re.M)
_RE_CAMINHO = re.compile(r"""["']((?:~|/|\.\.?/|[A-Za-z]:\\)[^"'\n]{2,}?\.(?:%s))["']""" % "|".join(e[1:] for e in EXT_MIDIA), re.I)


def _resolve(ref, base_dir, pasta):
    ref = ref.strip()
    if ref.startswith("~"):
        return os.path.expanduser(ref)
    if os.path.isabs(ref) or re.match(r"^[A-Za-z]:\\", ref):
        return ref
    p = os.path.normpath(os.path.join(base_dir, ref))
    if not os.path.exists(p):   # plano.json costuma ser relativo à pasta do preset
        q = os.path.normpath(os.path.join(pasta, ref))
        if os.path.exists(q):
            return q
    return p


def _modulo_py(nome, pasta, base_dir):
    """Onde está o módulo Python importado: 'stdlib', caminho local, ou None (pacote instalado/terceiro)."""
    raiz = nome.split(".")[0]
    if raiz in getattr(sys, "stdlib_module_names", ()) or raiz in sys.builtin_module_names:
        return "stdlib"
    for d in (base_dir, pasta, AQUI, os.path.join(SKILL, "presets", "cena"), SKILL):
        for cand in (os.path.join(d, raiz + ".py"), os.path.join(d, raiz, "__init__.py")):
            if os.path.exists(cand):
                return cand
    return None


def dependencias(pasta):
    """{'itens': [{ref, de, tipo, caminho?, nota?}], 'resumo': {tipo: n}}. Tipos: interno, skill, skill_nao_rastreado,
    fora (copiar para assets/), cdn, npm, pip, faltando."""
    pasta = os.path.abspath(pasta); rastreados = _rastreados(); itens, vistos = [], set()

    def add(ref, de, tipo, caminho=None, nota=None):
        k = (ref, tipo, caminho)
        if k in vistos:
            return
        vistos.add(k)
        d = {"ref": ref, "de": de, "tipo": tipo}
        if caminho: d["caminho"] = caminho
        if nota: d["nota"] = nota
        itens.append(d)

    def classifica(ref, de, base_dir):
        if re.match(r"^(https?:)?//", ref):
            m = re.search(r"/(?:npm/)?((?:@[\w.-]+/)?[\w.-]+)@([\w.^~-]+)", ref)
            return add(ref, de, "cdn", nota=f"{m.group(1)}@{m.group(2)}" if m else None)
        if ref.startswith(("data:", "blob:", "mailto:", "#", "javascript:")) or "${" in ref or "{{" in ref or "%" in ref:
            return
        p = _resolve(ref, base_dir, pasta)
        if p.startswith(pasta + os.sep) or p == pasta:
            return add(ref, de, "interno" if os.path.exists(p) else "faltando", os.path.relpath(p, pasta))
        if p.startswith(SKILL + os.sep):
            rel = os.path.relpath(p, SKILL).replace(os.sep, "/")
            if not os.path.exists(p):
                return add(ref, de, "faltando", rel)
            return add(ref, de, "skill" if rel in rastreados else "skill_nao_rastreado", rel)
        if os.path.exists(p):
            return add(ref, de, "fora", p)
        return add(ref, de, "faltando", p)

    for raiz, dirs, arqs in os.walk(pasta):
        dirs[:] = [d for d in dirs if d not in relatar.PULAR_DIRS_HF and not d.startswith(".")]
        for a in arqs:
            f = os.path.join(raiz, a); rel = os.path.relpath(f, pasta); ext = os.path.splitext(a)[1].lower()
            if ext not in EXT_TEXTO or a.endswith(".min.js") or os.path.getsize(f) > 2_000_000:
                continue
            txt = open(f, encoding="utf-8", errors="replace").read()
            if ext in (".html", ".htm", ".css", ".js", ".mjs"):
                for rx in _RE_REFS:
                    for ref in rx.findall(txt):
                        ref = ref.strip()
                        if not ref:
                            continue
                        if ext in (".js", ".mjs") and rx in _RE_REFS[3:5] and not ref.startswith((".", "/", "~", "http")):
                            add(ref, rel, "npm", nota=ref)   # import 'gsap' (pacote npm)
                            continue
                        classifica(ref, rel, os.path.dirname(f))
            if ext == ".py":
                for a1, a2 in _RE_PY_IMPORT.findall(txt):
                    nome = a1 or a2; onde = _modulo_py(nome, pasta, os.path.dirname(f))
                    if onde == "stdlib":
                        continue
                    if onde is None:
                        add(nome, rel, "pip", nota=nome.split(".")[0])
                    else:
                        classifica(onde, rel, os.path.dirname(f))
            for ref in _RE_CAMINHO.findall(txt):   # caminhos literais (plano.json, gerar.py)
                classifica(ref, rel, os.path.dirname(f))
    for f in glob.glob(os.path.join(pasta, "**", "*.min.js"), recursive=True):
        nome = os.path.basename(f).lower()
        lib = next((p for k, p in LIBS_CDN.items() if k in nome), None)
        add(os.path.relpath(f, pasta), "pasta", "cdn" if lib else "interno", os.path.relpath(f, pasta),
            nota=f"{lib} (biblioteca pública: o dono usa a do npm/CDN)" if lib else "biblioteca local")
    resumo = {}
    for i in itens:
        resumo[i["tipo"]] = resumo.get(i["tipo"], 0) + 1
    return {"pasta": pasta, "itens": itens, "resumo": resumo}


# ---------------------------------------------------------------- preparar

def _titulo_resumo(pasta):
    titulo, resumo = os.path.basename(os.path.normpath(pasta)), ""
    md = os.path.join(pasta, "PRESET.md")
    if os.path.exists(md):
        linhas = open(md, encoding="utf-8", errors="replace").read().splitlines()
        for l in linhas:
            if l.startswith("# "):
                titulo = re.sub(r"^Preset\s+", "", l[2:].strip(), flags=re.I); break
        para = []
        for l in linhas:
            if l.startswith(("#", "<", "|", "```")) or not l.strip():
                if para: break
                continue
            para.append(l.strip())
        resumo = re.sub(r"[*`_]", "", " ".join(para))
    m = os.path.join(pasta, "modelo.json")
    if not resumo and os.path.exists(m):
        try:
            d = json.load(open(m, encoding="utf-8")); titulo = d.get("nome", titulo); resumo = d.get("descricao", "")
        except Exception:
            pass
    return titulo[:60], (resumo[:157] + "...") if len(resumo) > 160 else resumo


def _categoria(texto):
    t = texto.lower()
    for cat, palavras in PALAVRAS_CAT:
        if any(p in t for p in palavras):
            return cat
    return "ideia"


def _formato(pasta):
    for p in glob.glob(os.path.join(pasta, "exemplo*", "plano.json")) + glob.glob(os.path.join(pasta, "plano.json")):
        try:
            d = json.load(open(p, encoding="utf-8"))
            w, h = int(d.get("w", 1080)), int(d.get("h", 1920))
            return ["horizontal"] if w > h else ["vertical"]
        except Exception:
            pass
    return ["vertical"]


def _gif_existente(pasta):
    for padrao in ("exemplo.gif", "exemplo/*.gif", "exemplos/*.gif", "*.gif"):
        g = sorted(glob.glob(os.path.join(pasta, padrao)))
        if g:
            return os.path.relpath(g[0], pasta)
    return None


def _mp4_para_gif(mp4, gif):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-t", "6", "-i", mp4, "-vf",
                    "fps=12,scale=270:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer:bayer_scale=4",
                    gif], check=True, timeout=180)


def gerar_gif(pasta, render=True):
    """exemplo.gif: GIF que já existe > MP4 da pasta (exemplo.mp4, renders/) > render HyperFrames do index.html.
    Devolve (caminho relativo ou None, mensagem)."""
    g = _gif_existente(pasta)
    if g:
        return g, "prévia existente"
    mp4s = sorted(glob.glob(os.path.join(pasta, "exemplo*.mp4")) + glob.glob(os.path.join(pasta, "renders", "*.mp4"))
                  + glob.glob(os.path.join(pasta, "exemplo*", "*.mp4")))
    destino = os.path.join(pasta, "exemplo.gif")
    if mp4s:
        _mp4_para_gif(mp4s[0], destino)
        return "exemplo.gif", f"GIF feito de {os.path.relpath(mp4s[0], pasta)}"
    if render and os.path.exists(os.path.join(pasta, "index.html")):
        tmp = os.path.join(tempfile.mkdtemp(prefix="gab_previa_"), "previa.mp4")
        try:
            subprocess.run(["npx", "--yes", hf(), "render", pasta, "--format", "mp4", "-q", "draft",
                            "-w", "2", "-o", tmp], check=True, capture_output=True, timeout=900)
            _mp4_para_gif(tmp, destino)
            return "exemplo.gif", "GIF renderizado do index.html (HyperFrames)"
        except Exception as e:
            return None, f"render da prévia falhou ({e}); renderize o exemplo e rode preparar de novo"
    return None, "sem prévia: renderize o exemplo do preset (MP4 em exemplo.mp4) e rode preparar de novo"


def _trazer_fora(pasta, dep):
    """Copia um arquivo de fora da skill para assets/ e reescreve a referência no arquivo que o usa."""
    origem = dep["caminho"]; nome = re.sub(r"[^\w.-]", "_", os.path.basename(origem))
    os.makedirs(os.path.join(pasta, "assets"), exist_ok=True)
    alvo = os.path.join(pasta, "assets", nome)
    if not os.path.exists(alvo):
        shutil.copy2(origem, alvo)
    arq = os.path.join(pasta, dep["de"])
    txt = open(arq, encoding="utf-8", errors="replace").read()
    novo_ref = os.path.relpath(alvo, os.path.dirname(arq)).replace(os.sep, "/")
    if dep["ref"] in txt:
        open(arq, "w", encoding="utf-8").write(txt.replace(dep["ref"], novo_ref))
    return os.path.relpath(alvo, pasta)


def preparar(pasta, categoria=None, render=True):
    pasta = os.path.abspath(pasta); avisos = []
    dep = dependencias(pasta)
    for d in dep["itens"]:
        if d["tipo"] == "fora":
            d["copiado_para"] = _trazer_fora(pasta, d); avisos.append(f"copiado para a pasta: {d['ref']} -> {d['copiado_para']}")
        elif d["tipo"] == "skill_nao_rastreado":
            rel = d["caminho"]; alvo = os.path.join(pasta, "_skill", rel)
            os.makedirs(os.path.dirname(alvo), exist_ok=True); shutil.copy2(os.path.join(SKILL, rel), alvo)
            avisos.append(f"arquivo da skill que só existe aqui vai junto: {rel} (em _skill/)")
        elif d["tipo"] == "faltando":
            avisos.append(f"FALTANDO: {d['ref']} (usado em {d['de']})")
    if any(d["tipo"] == "fora" for d in dep["itens"]):
        dep = dependencias(pasta)   # referências reescritas: medir de novo
    meta_arq = os.path.join(pasta, "preset.json")
    try:
        meta = json.load(open(meta_arq, encoding="utf-8"))
    except Exception:
        meta = {}
    titulo, resumo = _titulo_resumo(pasta)
    meta.setdefault("id", os.path.basename(pasta)); meta.setdefault("nome", titulo); meta.setdefault("resumo", resumo)
    if categoria:
        meta["categoria"] = categoria
    meta.setdefault("categoria", _categoria(f"{titulo} {resumo}"))
    if meta["categoria"] not in CATEGORIAS:
        raise SystemExit(f"categoria inválida: {meta['categoria']} (use {', '.join(CATEGORIAS)})")
    meta.setdefault("formato", _formato(pasta))
    gif, msg = gerar_gif(pasta, render)
    meta["gif"] = gif
    avisos.append(msg)
    json.dump(meta, open(meta_arq, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    arquivos = {}
    for rel in relatar._arquivos_hf(pasta):
        if rel != "manifesto.json":
            arquivos[rel] = _sha1(os.path.join(pasta, rel))
    manifesto = {"preset": meta["id"], "arquivos": arquivos,
                 "dependencias": [d for d in dep["itens"] if d["tipo"] in ("cdn", "npm", "pip", "skill", "faltando")],
                 "faltando": [d["ref"] for d in dep["itens"] if d["tipo"] == "faltando"]}
    json.dump(manifesto, open(os.path.join(pasta, "manifesto.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return {"meta": meta, "manifesto": manifesto, "avisos": avisos}


# ---------------------------------------------------------------- listar / enviar

def presets_locais():
    pastas = relatar._presets_do_usuario()
    if relatar._config().get("dono_biblioteca"):   # no dono, _presets_do_usuario não é usado pelo varrer; a lista vale igual
        pass
    return pastas


def _enviado(chave, est):
    e = est.get(chave) or {}
    if not e.get("arquivos"):
        return False
    return all(os.path.exists(os.path.join(relatar.ENV, os.path.basename(a))) for a in e["arquivos"])


def listar():
    est = _estado(); dono = bool(relatar._config().get("dono_biblioteca")); r = []
    for p in presets_locais():
        chave = _chave(p)
        try:
            meta = json.load(open(os.path.join(p, "preset.json"), encoding="utf-8"))
        except Exception:
            t, s = _titulo_resumo(p); meta = {"id": os.path.basename(p), "nome": t, "resumo": s, "categoria": _categoria(f"{t} {s}"),
                                              "formato": _formato(p), "gif": _gif_existente(p)}
        enviado = _enviado(chave, est)
        r.append({**meta, "pasta": chave, "enviado": enviado, "no_menu": bool(meta.get("gif")) and (enviado or dono),
                  "estado": "dono (não envia)" if dono else ("enviado" if enviado else (est.get(chave) or {}).get("estado", "ainda não enviado"))})
    return r


def enviar(pasta, simular=None):
    """Registra o pacote completo (relatar.registrar_preset) e envia. simular=<pasta>: grava as partes lá e não posta."""
    pasta = os.path.abspath(pasta); cfg = relatar._config(); chave = _chave(pasta); est = _estado()
    if cfg.get("dono_biblioteca") and not simular:
        return "máquina do dono: não envia (o preset já aparece no menu)"
    if not simular and (cfg.get("relatos") is not True or int(cfg.get("relatos_v", 1)) < relatar.CONSENTIMENTO_V):
        return "sem o aceite dos relatos (termos): o preset fica só nesta máquina e não aparece no menu"
    prep = preparar(pasta, render=True)
    if prep["manifesto"]["faltando"]:
        msg = "faltando arquivo: " + ", ".join(prep["manifesto"]["faltando"][:5])
        if not simular:
            est[chave] = {"estado": msg}; _salvar_estado(est)
        return "não enviado: " + msg
    porque, saidas = [], []
    res = relatar.registrar_preset(pasta, porque, saidas=saidas, destino=simular, forcar=bool(simular))
    if not res:
        msg = "não enviado: " + "; ".join(porque)
        if not simular:   # simulação não mexe no estado real
            est[chave] = {"estado": msg}; _salvar_estado(est)
        return msg
    if simular:
        return f"simulado: {len(saidas)} parte(s) em {simular}"
    est[chave] = {"estado": "na fila", "arquivos": saidas, "impressao": relatar._impressao(pasta)}; _salvar_estado(est)
    relatar.enviar()
    return "enviado" if _enviado(chave, _estado()) else "na fila (sem internet agora: vai na próxima abertura)"


def main(a):
    if not a or a[0] in ("-h", "--help"):
        raise SystemExit(__doc__)
    js = "--json" in a
    def arg(k, d=None):
        return a[a.index(k) + 1] if k in a else d
    if a[0] == "listar":
        r = listar()
        if js:
            print(json.dumps(r, ensure_ascii=False, indent=1)); return
        if not r:
            print("nenhum preset criado por você nesta máquina"); return
        for p in r:
            print(f"- {p['nome']} [{p['categoria']}] {p['pasta']}  prévia: {p.get('gif') or 'falta'}  {p['estado']}"
                  f"{'  (no menu)' if p['no_menu'] else ''}")
    elif a[0] == "dependencias":
        d = dependencias(a[1])
        if js:
            print(json.dumps(d, ensure_ascii=False, indent=1)); return
        print("resumo:", ", ".join(f"{k} {v}" for k, v in sorted(d["resumo"].items())) or "nenhuma")
        for i in d["itens"]:
            if i["tipo"] != "interno":
                print(f"  {i['tipo']:20} {i['ref']}  (em {i['de']}){'  ' + i['nota'] if i.get('nota') else ''}")
    elif a[0] == "preparar":
        r = preparar(a[1], arg("--categoria"), render="--sem-render" not in a)
        print(f"{r['meta']['nome']} [{r['meta']['categoria']}] prévia: {r['meta'].get('gif') or 'falta'}; "
              f"{len(r['manifesto']['arquivos'])} arquivo(s) no manifesto")
        for x in r["avisos"]:
            print("  " + x)
    elif a[0] == "enviar":
        print(enviar(a[1], arg("--simular")))
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
