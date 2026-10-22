"""Gab no CapCut pela linha de comando (Mac). Mesmo papel do resolve_lib no DaVinci: tudo por comando, sem clicar.

    python3 capcut.py rascunhos
    python3 capcut.py retrato "<rascunho>" [--json saida.json]
    python3 capcut.py plano plano.json [--projeto-fechado]      monta/edita um rascunho a partir de um plano JSON
    python3 capcut.py cortes cortes.json <video> --transcricao t.json [--prefixo "CORTE"] [--correcoes c.json]
                     [--credito "Fonte"] [--secoes secoes.txt] [--tam-titulo 17] [--tam-legenda 11]
                                                               um rascunho vertical por corte (fabrica_cortes.py)
    python3 capcut.py previa "<rascunho>" saida.mp4 [--ate 10] [--escala 0.5]
    python3 capcut.py previa "DEBATE*" <pasta> [--paralelo 3]  vários rascunhos de uma vez
                                                               renderiza o rascunho SEM o CapCut (ffmpeg + Pillow)
    python3 capcut.py conferir "<rascunho>"                     mídia offline, efeitos sem arquivo, buracos na V1
    python3 capcut.py abrir "<rascunho>"                        põe o rascunho no topo da tela inicial e abre o CapCut
    python3 capcut.py fechar                                    fecha o CapCut (ele salva o que estiver aberto)

Comandos rápidos (uma ação = um comando, em 1 ou vários rascunhos):
    python3 capcut.py ops                                       todas as ações com os parâmetros
    python3 capcut.py ids "<rascunho>"                          segmentos com o seletor de cada um (@v0:2, @t1:0...)
    python3 capcut.py faz "<rascunho|CORTE*|A,B>" <ação> [@seletor] [args] [chave=valor] [+ outra ação ...]
        faz "CORTE*" estilo_texto @t2:todos tamanho=12 cor='"#FFE600"'      legenda de todos os cortes
        faz "CORTE 01*" transicao @v0:todos Dissolve dur=0.3 + zoom @v0:0 1 1.08
        faz "CORTE 03*" trocar_texto @texto=Vot "Vota em mim"
    python3 capcut.py catalogo [grupo] [busca]                  transições, animações, efeitos, máscaras
    python3 capcut.py loja [grupo] [busca] [--tipo in]          filtros, adesivos, modelos de texto, vozes, fontes

Plano JSON (cada op é um método do Rascunho da capcut_lib; "id" guarda o segmento para usar depois como "$id"):
    {"nome": "Reels 01", "w": 1080, "h": 1920, "fps": 30, "substituir": true,
     "ops": [{"op": "video", "id": "v1", "arquivo": "/x/take.mp4", "tempo": 0, "de": 12.5, "ate": 20},
             {"op": "fundo", "alvo": "$v1", "desfoque": 0.6},
             {"op": "texto", "texto": "OLÁ", "tempo": 0, "dur": 2, "tamanho": 15, "y": 1500},
             {"op": "animar", "alvo": "$v1", "entrada": "Zoom In"}]}
Sem "substituir" e com o rascunho existente, o plano EDITA o rascunho (abre, aplica as ops, salva).

Limites conhecidos (engenharia reversa do CapCut 9.4, ver README): não há porta, deep link nem argumento que abra
um rascunho; abrir no app e exportar pelo app é um clique (o Gab faz em segundo plano com o computer-use).
A prévia do `previa` é do Gab, não do motor do CapCut: transições, efeitos, filtros e animações da loja não
aparecem nela (são listados no fim).
"""
import json, os, re, shutil, subprocess, sys, tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import capcut_lib as C

US = 1_000_000
FONTE_PADRAO = os.path.expanduser("~/Library/Fonts/Montserrat-SemiBold.ttf")
# Medido no CapCut 9.4 (22/10/2026, Anton e Montserrat): a ALTURA DE LINHA da fonte (hhea ascent - descent) é
# tamanho x 6,35 px num quadro de 1080 de largura; o corpo da letra (em) sai dessa altura dividida pela métrica.
LINHA_POR_TAMANHO = 6.35


# ---------------------------------------------------------------- plano
def _resolver(v, ids):
    if isinstance(v, str) and v.startswith("$"):
        return ids[v[1:]]
    if isinstance(v, list):
        return [_resolver(x, ids) for x in v]
    if isinstance(v, dict):
        return {k: _resolver(x, ids) for k, x in v.items()}
    return v


def plano(arq, projeto_fechado=False):
    p = json.load(open(arq))
    nome = p["nome"]
    existe = any(n == nome for n, *_ in C.rascunhos())
    if p.get("substituir") or not existe:
        d = C.novo(nome, p.get("w", 1080), p.get("h", 1920), p.get("fps", 30), substituir=bool(p.get("substituir")))
    else:
        d = C.abrir(nome)
    ids = {}
    for i, op in enumerate(p.get("ops", []), 1):
        op = dict(op)
        nome_op, guarda = op.pop("op"), op.pop("id", None)
        alvo = op.pop("alvo", None)
        metodo = getattr(d, nome_op, None)
        if metodo is None or nome_op.startswith("_"):
            raise SystemExit(f"op {i}: '{nome_op}' não existe no Rascunho")
        args = [_resolver(alvo, ids)] if alvo is not None else []
        try:
            r = metodo(*args, **_resolver(op, ids))
        except Exception as e:
            raise SystemExit(f"op {i} ({nome_op}): {e}")
        if guarda:
            ids[guarda] = r
    d.salvar(projeto_fechado=projeto_fechado or not C.capcut_aberto())
    print(f"{nome}: {len(p.get('ops', []))} ops, {d.j['duration'] / US:.1f} s -> {d.pasta}")
    return d


# ---------------------------------------------------------------- cortes (fabrica_cortes.py -> CapCut)
def _palavras(trans):
    d = json.load(open(trans))
    return [w for s in d["segments"] for w in s.get("words", [])]


def _corrigir(txt, cor):
    for errado, certo in cor.items():
        txt = re.sub(r"(?<!\w)" + re.escape(errado) + r"(?!\w)", certo, txt, flags=re.I)
    return txt


def _corrigir_itens(itens, cor):
    """Correções palavra a palavra ANTES de quebrar a legenda (chave com várias palavras também vale).
    A pontuação colada na última palavra trocada é mantida."""
    limpa = lambda t: re.sub(r"[^\w%-]", "", t.lower())
    regras = sorted(((k.split(), v.split()) for k, v in cor.items()), key=lambda r: -len(r[0]))
    out, i = [], 0
    while i < len(itens):
        for chave, troca in regras:
            n = len(chave)
            if i + n <= len(itens) and all(limpa(itens[i + j][2]) == limpa(chave[j]) for j in range(n)):
                ini, fim = itens[i][0], itens[i + n - 1][1]
                pont = re.search(r"[.,?!:;]+$", itens[i + n - 1][2])
                passo = (fim - ini) / len(troca)
                for j, pal in enumerate(troca):
                    out.append([ini + j * passo, ini + (j + 1) * passo,
                                pal + (pont.group(0) if pont and j == len(troca) - 1 and not re.search(r"[.,?!:;]$", pal) else "")])
                i += n
                break
        else:
            out.append(itens[i]); i += 1
    return out


def legenda_dos_trechos(ws, trechos, cor=None, max_pal=4, max_car=22):
    """Blocos de legenda (ini, fim, texto) no tempo do corte, contínuos, quebrando em pontuação."""
    cor = cor or {}
    itens, acc = [], 0.0
    for a, b in trechos:
        for w in ws:
            t = w["text"].replace("&gt;", ">").strip()
            if t.strip(">") and w["start"] >= a - .02 and w["start"] < b - .05 and w["end"] <= b + .3:
                itens.append([acc + max(0, w["start"] - a), acc + min(b, w["end"]) - a, t])
        acc += b - a
    itens = _corrigir_itens(itens, cor)
    blocos, cur = [], []
    for k, it in enumerate(itens):
        cur.append(it)
        txt = " ".join(x[2] for x in cur)
        prox = itens[k + 1] if k + 1 < len(itens) else None
        if (prox is None or len(cur) >= max_pal or len(txt) + 1 + len(prox[2]) > max_car
                or re.search(r"[.?!:;]$", it[2]) or prox[0] - it[1] > .6):
            blocos.append([cur[0][0], cur[-1][1], txt])
            cur = []
    for i in range(len(blocos) - 1):   # contínua: cada bloco vai até o próximo (buraco curto)
        if blocos[i + 1][0] - blocos[i][1] < 1.0:
            blocos[i][1] = blocos[i + 1][0]
    return [(round(a, 3), round(b, 3), t.replace(">>", "").strip()) for a, b, t in blocos if t.replace(">>", "").strip()]


def _secoes(arq):
    """secoes.txt ("NN inicio fim" por linha, arquivos trecho_NN.mp4 ao lado): trechos baixados à parte
    (yt-dlp --download-sections ... --force-keyframes-at-cuts). Devolve {NN: (arquivo, deslocamento)}."""
    base = os.path.dirname(os.path.abspath(arq))
    out = {}
    for l in open(arq):
        if l.strip():
            n, a, _ = l.split()
            out[int(n)] = (os.path.join(base, f"trecho_{n}.mp4"), float(a))
    return out


def cortes(cortes_json, video, transcricao, prefixo="CORTE", correcoes=None, credito="", fonte_titulo=None,
           fonte_legenda=None, escala=1.3, projeto_fechado=False, secoes=None, tam_titulo=17, tam_legenda=11):
    """video: o original inteiro (material bruto). secoes: secoes.txt quando só os trechos chegaram;
    depois, com o original baixado, Rascunho.religar() troca sem mexer na edição."""
    lista = json.load(open(cortes_json))
    pasta = os.path.join(os.path.dirname(os.path.abspath(cortes_json)), "cortes")
    cor = json.load(open(correcoes)) if correcoes else {}
    ws = _palavras(transcricao)
    secoes = _secoes(secoes) if secoes else {}
    fonte_titulo = fonte_titulo or os.path.expanduser("~/Library/Fonts/Anton-Regular.ttf")
    fonte_legenda = fonte_legenda or FONTE_PADRAO
    for c in lista:   # mesma ordem do fabrica_cortes.py conferir (média das notas, estável) = cortes/NN.json
        n = c.get("notas") or {}
        c["media"] = round(sum(n.values()) / len(n), 2) if n else 0
    lista.sort(key=lambda c: -c["media"])
    feitos = []
    for k, c in enumerate(lista, 1):
        plano_c = json.load(open(os.path.join(pasta, f"{k:02d}.json")))
        nome = f"{prefixo} {k:02d} - {c['titulo']}"
        d = C.novo(nome, 1080, 1920, 30, substituir=True)
        t = 0.0
        arq, desl = secoes.get(k, (video, 0.0))
        for a, b in plano_c["trechos"]:
            sid = d.video(arq, t, de=a - desl, ate=b - desl, trilha=0, escala=escala)
            d.fundo(sid, desfoque=0.6)
            t += b - a
        total = t
        # título (gancho) no topo, o corte inteiro
        d.texto(c.get("gancho", c["titulo"]).upper(), 0, total, trilha=0, tamanho=tam_titulo, cor="#FFFFFF",
                contorno="#000000", contorno_largura=0.12, fonte=fonte_titulo, y=1500, largura_max=0.86)
        if credito:
            d.texto(credito, 0, total, trilha=1, tamanho=5, cor="#FFFFFF", fonte=fonte_legenda, y=230,
                    largura_max=0.9)
        for a, b, txt in legenda_dos_trechos(ws, plano_c["trechos"], cor):
            d.texto(txt, a, b - a, trilha=2, tamanho=tam_legenda, cor="#FFFFFF", contorno="#000000", contorno_largura=0.1,
                    negrito=True, fonte=fonte_legenda, y=470)
        d.salvar(projeto_fechado=projeto_fechado or not C.capcut_aberto())
        feitos.append((nome, total))
        print(f"{nome}: {total:.1f} s")
    return feitos


# ---------------------------------------------------------------- conferir
def conferir(nome):
    d = C.abrir(nome)
    probs = []
    for lista in ("videos", "audios"):
        for m in d.j["materials"].get(lista, []):
            if m.get("path") and not os.path.exists(m["path"]):
                probs.append(f"mídia offline: {m['path']}")
            elif m.get("path") and not m["path"].startswith(os.path.expanduser("~/Movies/")):
                probs.append(f"fora de ~/Movies (CapCut não lê sem pedir): {m['path']}")
    for grupo in ("effects", "video_effects", "transitions", "material_animations", "stickers", "filters"):
        for m in d.j["materials"].get(grupo, []) or []:
            itens = m.get("animations") if grupo == "material_animations" else [m]
            for it in itens or []:
                if it.get("resource_id") and not it.get("path"):
                    probs.append(f"{grupo}: '{it.get('name') or it.get('resource_id')}' ainda sem arquivo "
                                 "(o CapCut baixa ao abrir o projeto com internet)")
    v1 = next((t for t in d.j["tracks"] if t["type"] == "video"), None)
    if v1:
        fim = 0
        for s in sorted(v1["segments"], key=lambda s: s["target_timerange"]["start"]):
            a = s["target_timerange"]["start"]
            if a - fim > 40_000:
                probs.append(f"buraco na V1 de {(a - fim) / US:.2f} s em {fim / US:.2f} s")
            fim = a + s["target_timerange"]["duration"]
    print(f"{nome}: {d.j['duration'] / US:.1f} s, {len(d.j['tracks'])} trilhas, "
          f"versão do rascunho {d.j.get('new_version')}, app {d.j.get('last_modified_platform', {}).get('app_version', '?')}")
    for p in probs:
        print("  !", p)
    print("  ok" if not probs else f"  {len(probs)} ponto(s) para olhar")
    return probs


# ---------------------------------------------------------------- abrir / fechar
def abrir_no_app(nome):
    """Põe o rascunho no topo da lista (1a miniatura da tela inicial) e abre o CapCut. Abrir o projeto é o
    clique na 1a miniatura: o Gab faz com o computer-use em segundo plano (app_click), sem tomar a tela."""
    d = C.abrir(nome)
    if C.capcut_aberto():
        print("CapCut já aberto: se este projeto não estiver aberto nele, ok; senão feche antes de editar por comando")
    d._registrar(int(__import__("time").time() * US))
    subprocess.run(["open", "-a", "CapCut"])
    print(f"'{nome}' é a 1a miniatura em Projetos. Clique nela para abrir.")


# ---------------------------------------------------------------- prévia sem o CapCut
def _txt_png(mat, seg, W, H, png):
    from PIL import Image, ImageDraw, ImageFont
    conteudo = json.loads(mat["content"])
    texto = conteudo.get("text", "")
    est = (conteudo.get("styles") or [{}])[0]
    tam = est.get("size", mat.get("font_size", 8))
    fonte = (est.get("font") or {}).get("path") or mat.get("font_path") or FONTE_PADRAO
    if not os.path.exists(fonte):
        fonte = FONTE_PADRAO
    linha = tam * LINHA_POR_TAMANHO * W / 1080
    try:
        from fontTools.ttLib import TTFont
        tt = TTFont(fonte, lazy=True)
        metrica = (tt["hhea"].ascent - tt["hhea"].descent) / tt["head"].unitsPerEm
    except Exception:
        metrica = 1.2
    px = max(8, int(round(linha / metrica)))
    f = ImageFont.truetype(fonte, px)
    try:
        if "[wght]" in fonte or "Variable" in fonte:
            f.set_variation_by_name("Bold" if est.get("bold") else "SemiBold")
    except Exception:
        pass
    cor = tuple(int(c * 255) for c in ((est.get("fill") or {}).get("content", {}).get("solid", {}).get("color") or [1, 1, 1]))
    borda = None
    if est.get("strokes"):
        sc = est["strokes"][0]
        borda = (tuple(int(c * 255) for c in sc["content"]["solid"]["color"]), max(1, int(px * sc.get("width", .08) * .9)))
    larg_max = mat.get("line_max_width", .82) * W
    linhas = []
    for par in texto.split("\n"):
        cur = ""
        for pal in par.split():
            teste = (cur + " " + pal).strip()
            if f.getlength(teste) > larg_max and cur:
                linhas.append(cur); cur = pal
            else:
                cur = teste
        linhas.append(cur)
    clip = seg.get("clip") or {}
    esc = (clip.get("scale") or {}).get("x", 1.0)
    tr = clip.get("transform") or {}
    cx, cy = W / 2 + tr.get("x", 0) * W / 2, H / 2 - tr.get("y", 0) * H / 2
    alt = linha
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)
    y0 = cy - alt * len(linhas) / 2
    for i, l in enumerate(linhas):
        lw = f.getlength(l)
        x = cx - lw / 2
        y = y0 + i * alt
        kw = {"stroke_width": borda[1], "stroke_fill": borda[0]} if borda else {}
        dr.text((x, y), l, font=f, fill=cor + (255,), **kw)
        if est.get("bold") and "[wght]" not in fonte:
            dr.text((x + max(1, px // 40), y), l, font=f, fill=cor + (255,))
    if esc != 1.0:
        big = img.resize((int(W * esc), int(H * esc)))
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        img.paste(big, (int((W - big.width) / 2), int((H - big.height) / 2)))
    img.save(png)


def previa(nome, saida, ate=None, escala=1.0):
    d = C.abrir(nome)
    j = d.j
    W, H = int(d.W * escala) // 2 * 2, int(d.H * escala) // 2 * 2
    fps = j.get("fps", 30)
    dur = j["duration"] / US if ate is None else min(ate, j["duration"] / US)
    mats = {}
    for lista in j["materials"].values():
        if isinstance(lista, list):
            for m in lista:
                if isinstance(m, dict) and "id" in m:
                    mats[m["id"]] = m
    tmp = tempfile.mkdtemp(prefix="gab_previa_")
    entradas, filtros, audios, avisos = [], [], [], []
    filtros.append(f"color=c=black:s={W}x{H}:r={fps}:d={dur:.3f}[base0]")
    atual, n = "base0", 0

    def entrada(args):
        entradas.extend(args)
        return len([a for a in entradas if a == "-i"]) - 1

    ordem = [t for t in j["tracks"] if t["type"] == "video"] + [t for t in j["tracks"] if t["type"] == "text"]
    for t in j["tracks"]:
        if t["type"] not in ("video", "text", "audio") and t["segments"]:
            avisos.append(f"trilha '{t['type']}' fora da prévia ({len(t['segments'])} itens)")
    principal = ordem[0] if ordem and ordem[0]["type"] == "video" else None
    for t in ordem:
        for s in t["segments"]:
            if not s.get("visible", True):
                continue
            a = s["target_timerange"]["start"] / US
            sd = s["target_timerange"]["duration"] / US
            if a >= dur:
                continue
            sd = min(sd, dur - a)
            m = mats.get(s["material_id"], {})
            en = f"between(t\\,{a:.3f}\\,{a + sd:.3f})"
            n += 1
            if t["type"] == "text":
                if m.get("type") != "text":
                    avisos.append("modelo de texto da loja fora da prévia"); continue
                png = os.path.join(tmp, f"t{n}.png")
                _txt_png(m, s, W, H, png)
                i = entrada(["-loop", "1", "-framerate", str(fps), "-t", f"{sd:.3f}", "-i", png])
                filtros.append(f"[{i}:v]setpts=PTS-STARTPTS+{a:.3f}/TB[o{n}]")
                filtros.append(f"[{atual}][o{n}]overlay=0:0:enable='{en}':eof_action=pass[b{n}]")
                atual = f"b{n}"
                continue
            if not m.get("path") or not os.path.exists(m["path"]):
                avisos.append(f"mídia offline: {m.get('path')}"); continue
            de = (s.get("source_timerange") or {}).get("start", 0) / US
            foto = m.get("type") == "photo"
            i = entrada((["-loop", "1", "-framerate", str(fps)] if foto else ["-ss", f"{de:.3f}"])
                        + ["-t", f"{sd * s.get('speed', 1):.3f}", "-i", m["path"]])
            w, h = m.get("width") or W, m.get("height") or H
            clip = s.get("clip") or {}
            esc = (clip.get("scale") or {}).get("x", 1.0)
            tr = clip.get("transform") or {}
            fit = min(W / w, H / h) * esc
            ow, oh = int(w * fit) // 2 * 2, int(h * fit) // 2 * 2
            ox = int(W / 2 + tr.get("x", 0) * W / 2 - ow / 2)
            oy = int(H / 2 - tr.get("y", 0) * H / 2 - oh / 2)
            vel = s.get("speed", 1) or 1
            cad = f"[{i}:v]setpts=(PTS-STARTPTS)/{vel}+{a:.3f}/TB,fps={fps}"
            canvas = next((mats[r] for r in s.get("extra_material_refs", []) if mats.get(r, {}).get("type", "").startswith("canvas_")), None)
            if t is principal and canvas and canvas["type"] == "canvas_blur":
                filtros.append(f"{cad},split[f{n}][v{n}]")
                raio = max(10, int(60 * canvas.get("blur", .5) * escala))
                filtros.append(f"[f{n}]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur={raio}:2[fb{n}]")
                filtros.append(f"[{atual}][fb{n}]overlay=0:0:enable='{en}':eof_action=pass[bf{n}]")
                atual = f"bf{n}"
                fonte_v = f"[v{n}]"
            else:
                filtros.append(f"{cad}[v{n}]")
                fonte_v = f"[v{n}]"
            alfa = clip.get("alpha", 1.0)
            extra = f",format=rgba,colorchannelmixer=aa={alfa}" if alfa < 1 else ""
            filtros.append(f"{fonte_v}scale={ow}:{oh}{extra}[e{n}]")
            filtros.append(f"[{atual}][e{n}]overlay={ox}:{oy}:enable='{en}':eof_action=pass[b{n}]")
            atual = f"b{n}"
            if m.get("has_audio") and s.get("volume", 1) > 0:
                audios.append((i, a, s.get("volume", 1), sd, 0, 0))
    for t in j["tracks"]:
        if t["type"] != "audio":
            continue
        for s in t["segments"]:
            m = mats.get(s["material_id"], {})
            a = s["target_timerange"]["start"] / US
            sd = min(s["target_timerange"]["duration"] / US, dur - a)
            if sd <= 0 or not m.get("path") or not os.path.exists(m["path"]):
                continue
            de = (s.get("source_timerange") or {}).get("start", 0) / US
            i = entrada(["-ss", f"{de:.3f}", "-t", f"{sd:.3f}", "-i", m["path"]])
            fade = next((mats[r] for r in s.get("extra_material_refs", []) if mats.get(r, {}).get("type") == "audio_fade"), {})
            audios.append((i, a, s.get("volume", 1), sd, fade.get("fade_in_duration", 0) / US, fade.get("fade_out_duration", 0) / US))
    rotulos = []
    for k, (i, a, vol, sd, fi, fo) in enumerate(audios):
        f = f"[{i}:a]asetpts=PTS-STARTPTS,volume={vol:.4f}"
        if fi: f += f",afade=t=in:d={fi:.3f}"
        if fo: f += f",afade=t=out:st={max(0, sd - fo):.3f}:d={fo:.3f}"
        f += f",adelay={int(a * 1000)}:all=1[a{k}]"
        filtros.append(f); rotulos.append(f"[a{k}]")
    mapa = ["-map", f"[{atual}]"]
    if rotulos:
        filtros.append("".join(rotulos) + f"amix=inputs={len(rotulos)}:normalize=0:dropout_transition=0,atrim=0:{dur:.3f}[aout]")
        mapa += ["-map", "[aout]"]
    script = os.path.join(tmp, "filtros.txt")
    open(script, "w").write(";\n".join(filtros))
    cmd = ["ffmpeg", "-y", "-v", "error", *entradas, "-filter_complex_script", script, *mapa, "-t", f"{dur:.3f}",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
           "-movflags", "+faststart", saida]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"ffmpeg falhou ({tmp}):\n{r.stderr[-2000:]}")
    shutil.rmtree(tmp, ignore_errors=True)
    for linha in sorted(set(avisos)):
        print("  aviso:", linha)
    print(f"{saida}: {dur:.1f} s, {W}x{H}")
    return saida


# ---------------------------------------------------------------- comandos rápidos (faz / ids / ops)
TIPOS = {"v": "video", "t": "text", "a": "audio", "e": "effect", "f": "filter", "s": "sticker"}


def _valor(v):
    try:
        return json.loads(v)
    except Exception:
        return v


def _nomes(padrao):
    """'CORTE*' (curinga), 'A,B' (lista) ou nome exato."""
    import fnmatch
    todos = [n for n, *_ in C.rascunhos()]
    achados = []
    for p in padrao.split(","):
        p = p.strip()
        achados += [n for n in todos if fnmatch.fnmatchcase(n, p)] if any(c in p for c in "*?[") else [p]
    if not achados:
        raise SystemExit(f"nenhum rascunho com '{padrao}'")
    return list(dict.fromkeys(achados))


def alvos(d, sel):
    """Seletor -> lista de ids de segmento.
    @v0:2  vídeo trilha 0, segmento 2 (0 = primeiro, -1 = último)   @v0:todos (ou '@v0:*')  todos da trilha   @t*:*  todos os textos
    @t1:2-5  intervalo   @em=12.5  segmento da V1 nesse segundo   @texto=palavra  textos que contêm a palavra
    Sem @: id literal."""
    if not isinstance(sel, str) or not sel.startswith("@"):
        return [sel]
    sel = sel[1:].replace(":todos", ":*").replace("todos:", "*:")   # zsh expande '*': @v0:todos = @v0:*
    if sel.startswith("em="):
        t = float(sel[3:]) * US
        v1 = next(tr for tr in d.j["tracks"] if tr["type"] == "video")
        return [s["id"] for s in v1["segments"]
                if s["target_timerange"]["start"] <= t < s["target_timerange"]["start"] + s["target_timerange"]["duration"]]
    if sel.startswith("texto="):
        busca = sel[6:].lower()
        out = []
        for tr in d.j["tracks"]:
            if tr["type"] == "text":
                for s in tr["segments"]:
                    m = d._mat(s["material_id"]) or {}
                    if m.get("type") == "text" and busca in json.loads(m["content"]).get("text", "").lower():
                        out.append(s["id"])
        return out
    m = re.fullmatch(r"([vtaefs])(\d+|\*):(\*|-?\d+(?:-\d+)?)", sel)
    if not m:
        raise SystemExit(f"seletor inválido: @{sel} (ex.: @v0:2, @t1:*, @em=12.5, @texto=Lula)")
    tipo, n, i = TIPOS[m.group(1)], m.group(2), m.group(3)
    trilhas = [tr for tr in d.j["tracks"] if tr["type"] == tipo]
    trilhas = trilhas if n == "*" else trilhas[int(n):int(n) + 1]
    out = []
    for tr in trilhas:
        segs = sorted(tr["segments"], key=lambda s: s["target_timerange"]["start"])
        if i == "*":
            out += [s["id"] for s in segs]
        elif re.fullmatch(r"\d+-\d+", i):
            a, b = map(int, i.split("-")); out += [s["id"] for s in segs[a:b + 1]]
        else:
            out += [segs[int(i)]["id"]] if segs else []
    return out


def faz(padrao, args, projeto_fechado=False):
    """Uma ou mais ações (separadas por '+') em um ou vários rascunhos; salva cada rascunho uma vez.
    capcut.py faz "CORTE*" fundo @v0:* desfoque=0.6 + estilo_texto @t2:* tamanho=12"""
    acoes, cur = [], []
    for x in args:
        if x == "+":
            acoes.append(cur); cur = []
        else:
            cur.append(x)
    acoes.append(cur)
    if C.capcut_aberto() and not projeto_fechado:
        print("aviso: CapCut aberto; se um destes rascunhos estiver aberto nele, a edição será sobrescrita")
    for nome in _nomes(padrao):
        d = C.abrir(nome)
        feitos = 0
        for acao in acoes:
            if not acao:
                continue
            metodo = getattr(d, acao[0], None)
            if metodo is None or acao[0].startswith("_"):
                raise SystemExit(f"'{acao[0]}' não existe. capcut.py ops lista as ações")
            pos = [a for a in acao[1:] if not re.match(r"^[a-z_]+=", a)]
            kw = {k: _valor(v) for k, v in (a.split("=", 1) for a in acao[1:] if re.match(r"^[a-z_]+=", a))}
            ids_alvo = alvos(d, pos[0]) if pos and isinstance(pos[0], str) and pos[0].startswith("@") else None
            resto = [_valor(p) for p in (pos[1:] if ids_alvo is not None else pos)]
            for sid in (ids_alvo if ids_alvo is not None else [None]):
                metodo(*([sid] if sid else []), *resto, **kw)
                feitos += 1
        d.salvar(projeto_fechado=True)
        print(f"{nome}: {feitos} ação(ões)")


def ids(nome):
    d = C.abrir(nome)
    letra = {v: k for k, v in TIPOS.items()}
    cont = {}
    for tr in d.j["tracks"]:
        k = letra.get(tr["type"], tr["type"][0]); n = cont.get(k, 0); cont[k] = n + 1
        print(f"{k}{n} ({tr['type']})")
        for i, s in enumerate(sorted(tr["segments"], key=lambda s: s["target_timerange"]["start"])):
            a = s["target_timerange"]["start"] / US; b = a + s["target_timerange"]["duration"] / US
            m = d._mat(s["material_id"]) or {}
            nome_m = json.loads(m["content"]).get("text", "") if m.get("type") == "text" else \
                (m.get("material_name") or m.get("name") or m.get("type", ""))
            print(f"  @{k}{n}:{i:<3} {a:7.2f}-{b:7.2f}  {str(nome_m)[:50]}")


def ops():
    import inspect
    print("Ações (capcut.py faz \"<rascunho|CORTE*>\" <ação> [@seletor] [args] [chave=valor] [+ outra ação]):")
    for n, f in inspect.getmembers(C.Rascunho, inspect.isfunction):
        if n.startswith("_") or n in ("salvar", "segmento", "retrato"):
            continue
        sig = str(inspect.signature(f)).replace("self, ", "").replace("(self)", "()")
        sig = re.sub(r"\bsid\b", "@alvo", sig)
        doc = (f.__doc__ or "").strip().splitlines()[0] if f.__doc__ else ""
        print(f"  {n}{sig}\n      {doc}")
    print("\nSeletores:", alvos.__doc__.split("\n", 1)[1])
    print("Nomes de transição/animação/efeito/máscara: capcut.py catalogo <grupo> [busca]")
    print("Filtros, adesivos, modelos de texto, vozes, fontes da loja: capcut.py loja <grupo> [busca] [--tipo in|out|loop|caption]")


# ---------------------------------------------------------------- CLI
def main(a):
    op = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    if not a or a[0] in ("-h", "--help", "ajuda"):
        print(__doc__); return
    cmd = a[0]
    if cmd == "rascunhos":
        for n, dur, mod in C.rascunhos():
            print(f"{mod}  {dur:7.1f} s  {n}")
    elif cmd == "retrato":
        r = C.abrir(a[1]).retrato(salvar_em=op("--json"))
        for t in r:
            print(f"[{t['trilha']}] {t['tipo']}: {len(t['segmentos'])} itens")
            for s in t["segmentos"][:200]:
                print(f"     {s['inicio']:7.2f}-{s['fim']:7.2f}  {s['nome'][:60]}{'' if s['visivel'] else '  (desligado)'}")
    elif cmd == "plano":
        plano(a[1], "--projeto-fechado" in a)
    elif cmd == "cortes":
        cortes(a[1], a[2], op("--transcricao"), op("--prefixo", "CORTE"), op("--correcoes"), op("--credito", ""),
               op("--fonte-titulo"), op("--fonte-legenda"), float(op("--escala", 1.3)), "--projeto-fechado" in a,
               op("--secoes"), float(op("--tam-titulo", 17)), float(op("--tam-legenda", 11)))
    elif cmd == "previa":
        nomes = _nomes(a[1])
        ate, esc = (float(op("--ate")) if op("--ate") else None), float(op("--escala", 1.0))
        if len(nomes) == 1 and a[2].lower().endswith(".mp4"):
            previa(nomes[0], a[2], ate, esc)
        else:   # vários rascunhos -> uma pasta, em paralelo
            from concurrent.futures import ThreadPoolExecutor
            os.makedirs(a[2], exist_ok=True)
            def um(n):
                try:
                    previa(n, os.path.join(a[2], n + ".mp4"), ate, esc); return f"ok {n}"
                except SystemExit as e:
                    return f"FALHOU {n}: {str(e)[-300:]}"
            with ThreadPoolExecutor(int(op("--paralelo", 3))) as ex:
                for r in ex.map(um, nomes):
                    print(r)
    elif cmd == "conferir":
        sys.exit(1 if conferir(a[1]) else 0)
    elif cmd == "abrir":
        abrir_no_app(a[1])
    elif cmd == "faz":
        faz(a[1], [x for x in a[2:] if x != "--projeto-fechado"], "--projeto-fechado" in a)
    elif cmd == "ids":
        ids(a[1])
    elif cmd == "ops":
        ops()
    elif cmd == "catalogo":
        if len(a) < 2:
            print("grupos:", ", ".join(g for g in C.CATALOGO if not g.startswith("_")))
        else:
            print("\n".join(C.catalogo(a[1], a[2] if len(a) > 2 and not a[2].startswith("--") else "")))
    elif cmd == "loja":
        if len(a) < 2:
            print("grupos:", ", ".join(f"{g} ({len(v)})" for g, v in C.LOJA.items()))
        else:
            r = C.loja(a[1], a[2] if len(a) > 2 and not a[2].startswith("--") else "", op("--tipo"))
            print("\n".join(r[:int(op("--max", 80))]), f"\n({len(r)} itens)")
    elif cmd == "fechar":
        print("fechado" if C.fechar_capcut() else "não fechou (diálogo aberto no CapCut?)")
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
