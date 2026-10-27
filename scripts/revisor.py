"""Revisor com nota ANTES de entregar (regra do usuário, 16/10/2026). Duas partes:

  python3 revisor.py <video.mp4> [--pasta <pasta_hyperframes>] [--rodada 1] [--saida <pasta>]

1) Conferência automática (este script): gera as provas e a lista de defeitos com o tempo de cada um.
   - folha.jpg (12 quadros) e folha_celular.jpg (mesmos quadros no tamanho de tela de celular)
   - cortes_NN.jpg: tira de 6 quadros em volta de cada corte (pulo, quadro sujo, elemento sumindo antes da hora)
   - quadro preto, imagem congelada fora do fim, gancho parado (nada se mexe nos 2 primeiros segundos)
   - algo encostado na borda (texto ou elemento cortado pela margem de 4%)
   - tempo de leitura de cada frase na tela (OCR do macOS, scripts/leitura.py texto): lista em revisao.md
   - som: volume integrado (-14 LUFS, +-1), pico (<= -1 dBTP), trecho mudo
   - com --pasta: clichês proibidos no código do motion (docs/etapas/motion_proibidos.md)
2) Nota de 0 a 10 em 7 critérios, dada por um revisor de OLHOS NOVOS (subagente sem o contexto da edição) que lê
   revisao.md e as imagens e preenche a tabela com evidência (arquivo e tempo). Ver docs/etapas/revisor.md.

Regra de entrega: nenhum ERRO, todos os critérios >= 8 e pelo menos 2 rodadas. A cada rodada corrigir os 3 piores
problemas e rodar de novo (--rodada 2...). Depois de 3 rodadas, entregar listando o que ficou em aberto.
"""
import json, os, re, subprocess, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
CRITERIOS = [
    ("Gancho", "nos 2 primeiros segundos algo forte acontece e a mensagem principal aparece; nada de tela vazia"),
    ("Leitura no celular", "na folha_celular todo texto se lê; cada frase fica na tela tempo de ler (~0,3 s por palavra + 0,5 s). "
     "Cada ERRO da seção 'Tempo de leitura' que NÃO repete a fala limita a nota a 7"),
    ("Som na batida", "cada efeito cai no quadro do movimento dele; música e efeitos sem embolar; volume certo"),
    ("Acabamento", "nada cortado (acento, perna do g, borda), nada sobreposto, nada encostado na margem"),
    ("Ritmo e respiro", "uma ideia por cena, cortes sem pulo, sem cena arrastada nem atropelada"),
    ("Marca e fatos", "cores, fonte e logo do cliente; todo número e afirmação vem da lista aprovada"),
    ("Movimento", "curvas que freiam no fim, nada linear no que se vê, nenhum clichê proibido"),
]


def sh(args, **k):
    return subprocess.run(args, capture_output=True, text=True, **k)


def dur_de(v):
    return float(sh(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", v]).stdout.strip() or 0)


def quadro(v, t, saida, larg=None):
    vf = ["-vf", f"scale={larg}:-1"] if larg else []
    sh(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{t:.3f}", "-i", v, "-frames:v", "1"] + vf + [saida])
    return saida


def mosaico(fotos, saida, colunas):
    """Grade de quadros (Pillow; sem ele, tile do ffmpeg pelos nomes _fNN/_cNN)."""
    try:
        from PIL import Image
        ims = [Image.open(f).convert("RGB") for f in fotos]
        w, h = ims[0].size; linhas = (len(ims) + colunas - 1) // colunas
        g = Image.new("RGB", (w * colunas, h * linhas), (20, 20, 22))
        for i, im in enumerate(ims):
            g.paste(im, ((i % colunas) * w, (i // colunas) * h))
        g.save(saida, quality=88)
    except ImportError:
        pref = os.path.basename(fotos[0])[:2]
        sh(["ffmpeg", "-loglevel", "error", "-y", "-i", os.path.join(os.path.dirname(fotos[0]), pref + "%02d.jpg"),
            "-vf", f"tile={colunas}x{(len(fotos) + colunas - 1) // colunas}", "-frames:v", "1", saida])
    return saida


def cortes(v, limiar=0.25):
    r = sh(["ffmpeg", "-hide_banner", "-i", v, "-vf", f"select='gt(scene,{limiar})',showinfo", "-an", "-f", "null", "-"])
    return [float(m) for m in re.findall(r"pts_time:([\d.]+)", r.stderr)]


def detecta(v, filtro, chave_ini, chave_fim):
    r = sh(["ffmpeg", "-hide_banner", "-i", v, "-vf", filtro, "-an", "-f", "null", "-"])
    ini = [float(x) for x in re.findall(chave_ini + r"[:=]\s*([\d.]+)", r.stderr)]
    fim = [float(x) for x in re.findall(chave_fim + r"[:=]\s*([\d.]+)", r.stderr)]
    return list(zip(ini, fim + [None] * (len(ini) - len(fim))))


def diferenca(a, b):
    """Diferença média entre dois quadros (0-255), para saber se algo se mexeu."""
    try:
        from PIL import Image, ImageChops, ImageStat
        x, y = Image.open(a).convert("L").resize((270, 480)), Image.open(b).convert("L").resize((270, 480))
        return ImageStat.Stat(ImageChops.difference(x, y)).mean[0]
    except Exception:
        return None


def borda(foto, margem=.04):
    """Há conteúdo claro e com contraste encostado na margem? Devolve o lado ou None."""
    try:
        from PIL import Image
        im = Image.open(foto).convert("L"); W, H = im.size; m = max(2, int(min(W, H) * margem))
        lados = {"esquerda": (0, 0, m, H), "direita": (W - m, 0, W, H), "topo": (0, 0, W, m), "base": (0, H - m, W, H)}
        achou = []
        for nome, caixa in lados.items():
            hist = im.crop(caixa).histogram()
            if sum(hist[201:]) > sum(hist) * .004:
                achou.append(nome)
        return achou
    except Exception:
        return []


def audio(v, dur):
    r = sh(["ffmpeg", "-hide_banner", "-i", v, "-af", "ebur128=peak=true", "-f", "null", "-"])
    if "Stream #0:1" not in r.stderr and "Audio:" not in r.stderr:
        return None
    integ = re.findall(r"I:\s*(-?[\d.]+) LUFS", r.stderr)
    pico = re.findall(r"Peak:\s*(-?[\d.]+) dBFS", r.stderr)
    s = sh(["ffmpeg", "-hide_banner", "-i", v, "-af", "silencedetect=n=-50dB:d=1.2", "-f", "null", "-"]).stderr
    mudos = list(zip(re.findall(r"silence_start: ([\d.]+)", s), re.findall(r"silence_end: ([\d.]+)", s)))
    return {"lufs": float(integ[-1]) if integ else None, "pico": float(pico[-1]) if pico else None,
            "mudos": [(float(a), float(b)) for a, b in mudos if float(b) - float(a) < dur - .5]}


def lint(pasta):
    """Clichês proibidos no código do motion (lista em docs/etapas/motion_proibidos.md)."""
    regras = [
        (r"(bounce|elastic|back)\.(in|out|inOut)?|cubic-bezier\([^)]*1\.[5-9]", "quique/elástico (bounce, elastic, back) no movimento"),
        (r"steps\(\d+|typewriter|maquina.?de.?escrever|\.split\(\"\"\)", "texto digitando letra a letra (máquina de escrever)"),
        (r"text-shadow:[^;]*\b([2-9]\d|1\d\d)px", "brilho (glow) em texto"),
        (r"(#(7c3aed|8b5cf6|a855f7|6d28d9|9333ea)[^;]*#(3b82f6|2563eb|06b6d4|0ea5e9))|purple[^;]*blue", "fundo em degradê roxo e azul"),
        (r"Math\.random\(", "Math.random (o render tem que ser determinístico; usar semente)"),
        (r"gsap\.utils\.random\(|scrambleText", "gsap.utils.random / ScrambleText (sorteiam sem semente; o render tem que ser determinístico)"),
        (r"autoSplit\s*:\s*true", "SplitText com autoSplit (refaz a divisão no meio do render e quebra o seek)"),
        (r"ease:\s*[\"'](none|linear)[\"']", "movimento linear (só vale para câmera contínua ou contador; conferir)"),
    ]
    achados = []
    for raiz, _, arqs in os.walk(pasta):
        if "node_modules" in raiz:
            continue
        for a in arqs:
            if a.endswith((".js", ".css", ".html")) and not a.endswith(".min.js"):
                txt = open(os.path.join(raiz, a), encoding="utf-8", errors="ignore").read()
                for rx, msg in regras:
                    linhas = txt.splitlines()
                    if "linear" in msg:   # câmera contínua, relógio de partículas e contador podem ser lineares
                        linhas = [l for l in linhas if not re.search(r"#cam|relogio|\brel\b|onUpdate|// linear ok", l)]
                    n = len(re.findall(rx, "\n".join(linhas), re.I))
                    if n:
                        achados.append((a, msg, n))
    return achados


def gemeos(pasta):
    """Elementos irmãos animando em sincronia perfeita (ideia do ClaudeAnimationBase, MIT): 3+ movimentos com o mesmo
    início, duração, ease e propriedades, ou um movimento com 3+ alvos sem stagger. Lê o movimentos.json da pasta
    (`OUT=<pasta>/movimentos.json node movimentos.mjs <base> <id>`); sem ele, não confere."""
    arq = os.path.join(pasta, "movimentos.json")
    if not os.path.exists(arq):
        return []
    from collections import Counter
    achados = []
    for cid, tws in json.load(open(arq, encoding="utf-8")).items():
        iguais = Counter((t[0], t[1], t[3], t[4]) for t in tws if t[5] == 1 and t[1] > 0)
        for (ini, d, props, ease), n in iguais.items():
            if n >= 3:
                achados.append((f"{cid} {ini:.2f} s", f"{n} elementos com o mesmo movimento ({props}, {d:g} s, {ease or 'padrão'}) "
                                                       "ao mesmo tempo: variar início/duração (stagger ou distribute)"))
        for t in tws:
            if t[5] >= 3 and not (len(t) > 6 and t[6]):
                achados.append((f"{cid} {t[0]:.2f} s", f"{t[5]} alvos ({t[2]}) entrando juntos sem stagger"))
    return achados


def main(a):
    if not a:
        raise SystemExit(__doc__)
    v = os.path.abspath(a[0]); op = lambda k: a[a.index(k) + 1] if k in a else None
    rodada = int(op("--rodada") or 1)
    out = os.path.abspath(op("--saida") or os.path.join(os.path.dirname(v), f"revisao_{os.path.splitext(os.path.basename(v))[0]}"))
    os.makedirs(out, exist_ok=True)
    dur = dur_de(v); erros, avisos = [], []
    # Folhas: 12 quadros em tamanho de revisão e em tamanho de celular (texto que some aqui some no telefone).
    tempos = [round(.15 + (dur - .3) * i / 11, 2) for i in range(12)]
    for f in os.listdir(out):
        if f.startswith("_f") or f.startswith("_c"):
            os.remove(os.path.join(out, f))
    fotos = [quadro(v, t, os.path.join(out, f"_f{i:02d}.jpg"), 360) for i, t in enumerate(tempos)]
    mosaico(fotos, os.path.join(out, "folha.jpg"), 6)
    cel = [quadro(v, t, os.path.join(out, f"_c{i:02d}.jpg"), 140) for i, t in enumerate(tempos)]
    mosaico(cel, os.path.join(out, "folha_celular.jpg"), 6)
    # Gancho: algo tem que mudar entre 0,1 s e 2 s.
    a0, a1 = quadro(v, .1, os.path.join(out, "_g0.png")), quadro(v, min(2.0, dur - .1), os.path.join(out, "_g1.png"))
    d = diferenca(a0, a1)
    if d is not None and d < 2.0:
        erros.append(("0-2 s", "gancho parado: quase nada muda nos 2 primeiros segundos"))
    # Cortes: tiras de 6 quadros em volta de cada corte.
    cs = cortes(v)
    for k, t in enumerate(cs[:10], 1):
        tira = [quadro(v, max(0, t + dt), os.path.join(out, f"_t{j}.jpg"), 200) for j, dt in enumerate((-.1, -.05, -.017, .017, .05, .1))]
        sh(["ffmpeg", "-loglevel", "error", "-y"] + sum([["-i", f] for f in tira], []) + ["-filter_complex", "hstack=6", os.path.join(out, f"corte_{k:02d}.jpg")])
    # Preto e congelado.
    for ini, fim in detecta(v, "blackdetect=d=0.15:pix_th=0.06", "black_start", "black_end"):
        if ini > .05 and (fim or dur) < dur - .05:
            erros.append((f"{ini:.2f}-{fim:.2f} s" if fim else f"{ini:.2f} s", "quadro preto no meio do vídeo"))
    for ini, fim in detecta(v, "freezedetect=n=0.002:d=1.2", "freeze_start", "freeze_end"):
        if (fim or dur) < dur - .2:
            avisos.append((f"{ini:.2f}-{(fim or dur):.2f} s", "imagem parada por mais de 1,2 s (respiro intencional? se não, dar vida)"))
    # Borda.
    for t, f in zip(tempos, fotos):
        lados = borda(f)
        if lados:
            avisos.append((f"{t:.2f} s", "conteúdo encostado na borda (" + ", ".join(lados) + "): conferir se nada está cortado"))
    # Tempo de leitura (OCR): fica numa seção própria; o revisor decide se a fala cobre o texto rápido.
    leit = []
    try:
        from leitura import texto as ler_texto
        leit = [x for x in ler_texto(v) if x["nivel"]]
    except Exception as e:
        avisos.append(("todo", f"tempo de leitura não conferido ({str(e)[:60]}); rodar leitura.py texto no Mac"))
    # Som.
    au = audio(v, dur)
    if au is None:
        avisos.append(("todo", "vídeo sem áudio (motion mudo vai para a timeline? se é entrega final, falta som)"))
    else:
        if au["lufs"] is not None and abs(au["lufs"] + 14) > 1:
            erros.append(("todo", f"volume integrado {au['lufs']:.1f} LUFS (alvo -14 +-1)"))
        if au["pico"] is not None and au["pico"] > -1:
            avisos.append(("todo", f"pico {au['pico']:.1f} dBFS (deixar abaixo de -1)"))
        for x, y in au["mudos"]:
            avisos.append((f"{x:.1f}-{y:.1f} s", "trecho mudo (sem música nem efeito)"))
    # Código do motion.
    if op("--pasta"):
        for arq, msg, n in lint(os.path.abspath(op("--pasta"))):
            (avisos if "linear" in msg else erros).append((arq, f"proibido: {msg} ({n}x)"))
        avisos += gemeos(os.path.abspath(op("--pasta")))
    for f in os.listdir(out):
        if f.startswith(("_t", "_g", "_f", "_c")):
            os.remove(os.path.join(out, f))
    # Relatório para o revisor de olhos novos.
    L = [f"# Revisão (rodada {rodada})", "", f"Vídeo: `{v}` ({dur:.1f} s). Provas nesta pasta: `folha.jpg`, `folha_celular.jpg`, "
         f"`corte_NN.jpg` ({len(cs)} cortes achados).", "", "## Conferência automática", ""]
    L += [f"- **ERRO** [{t}] {m}" for t, m in erros] + [f"- aviso [{t}] {m}" for t, m in avisos] or ["- nada encontrado"]
    if leit:
        L += ["", "## Tempo de leitura (OCR, mínimo 0,3 s por palavra + 0,5 s)", "",
              "Texto que repete a fala pode ser mais rápido (quem ouve já leu). Texto que só aparece escrito precisa do tempo.", ""]
        L += [f"- {x['nivel']} [{x['ini']:.2f} s] \"{x['texto']}\" fica {x['dur']:.2f} s (mínimo {x['minimo']:.1f} s)" for x in leit]
    L += ["", "## Nota (preencher: revisor de olhos novos, com evidência de arquivo e tempo)", "",
          "| # | Critério | O que olhar | Nota 0-10 | Evidência (arquivo, tempo) | Correção |", "|---|---|---|---|---|---|"]
    L += [f"| {i} | {n} | {o} |  |  |  |" for i, (n, o) in enumerate(CRITERIOS, 1)]
    L += ["", "Entrega: nenhum ERRO, todos >= 8 e pelo menos 2 rodadas. Senão: corrigir os 3 piores e rodar com "
          f"`--rodada {rodada + 1}`. Depois da rodada 3, entregar listando o que ficou em aberto."]
    open(os.path.join(out, "revisao.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    json.dump({"rodada": rodada, "erros": erros, "avisos": avisos, "cortes": cs, "audio": au, "leitura": leit},
              open(os.path.join(out, "revisao.json"), "w"), ensure_ascii=False, indent=1)
    print(os.path.join(out, "revisao.md"))
    print(f"{len(erros)} erro(s), {len(avisos)} aviso(s), {len(cs)} corte(s)")
    sys.exit(1 if erros else 0)


if __name__ == "__main__":
    main(sys.argv[1:])
