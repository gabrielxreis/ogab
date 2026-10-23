#!/usr/bin/env python3
"""Instalador do Gab (/ogab) com painel ao vivo: o que está acontecendo, o que está baixando (MB, MB/s, quanto falta),
o que já foi instalado e o que ainda falta.

Chamado pelo install.sh depois do Homebrew, do Python e do clone da skill (que não dependem dele):
    python3 ~/.claude/skills/ogab/scripts/instalador.py            # termos (aceite obrigatório), editor/motion/voz e instala
    python3 instalador.py --lista                                  # só mostra o que tem e o que falta
Variáveis: OGAB_ACEITO=sim (só depois que a PESSOA aceitou os termos), OGAB_EDITOR, OGAB_MOTION pulam as perguntas. Log completo em ~/.claude/ogab-instalacao.log.

Cada etapa tem um teste "já tem?" (pulada se sim), o comando, e um tamanho aproximado de download para a barra geral.
Os MB baixados vêm do contador de rede do sistema (vale para brew, pip, npm e git) e, quando a ferramenta diz o
tamanho do arquivo (pip "(37.1 MB)", git "Receiving objects ... MiB"), a etapa ganha barra própria.
"""
import json, os, platform, re, shutil, subprocess, sys, threading, time
from pathlib import Path

DEST = Path(__file__).resolve().parent.parent
HOME = Path.home()
MAC, WIN = sys.platform == "darwin", os.name == "nt"
LOG = HOME / ".claude" / "ogab-instalacao.log"
STATUS = HOME / ".claude" / "ogab-instalacao.json"
TTY = sys.stdout.isatty()
PY = f'"{sys.executable}"'
CFG = DEST / "config.json"

# ------------------------------------------------------------------ cores e formatação
def c(cod, s):
    return f"\033[{cod}m{s}\033[0m" if TTY else s
VERDE, AMAR, VERM, CINZA, NEG, AZUL = (lambda s: c("32", s)), (lambda s: c("33", s)), (lambda s: c("31", s)), \
    (lambda s: c("90", s)), (lambda s: c("1", s)), (lambda s: c("36", s))


def mb(b):
    m = b / 1e6
    return f"{m / 1000:.2f} GB" if m >= 1000 else (f"{m:.0f} MB" if m >= 100 else f"{m:.1f} MB")


def tempo(s):
    s = int(s)
    return f"{s // 60} min {s % 60:02d} s" if s >= 60 else f"{s} s"


def barra(frac, larg=28):
    frac = max(0.0, min(1.0, frac))
    cheio = int(frac * larg)
    return "█" * cheio + ("▌" if frac * larg - cheio >= .5 else "") + "░" * (larg - cheio - (1 if frac * larg - cheio >= .5 else 0))


# ------------------------------------------------------------------ contador de rede (bytes recebidos no sistema)
def bytes_rede():
    try:
        if MAC:
            out = subprocess.run(["netstat", "-ib"], capture_output=True, text=True, timeout=3).stdout.splitlines()
            vistos, total = set(), 0
            for l in out[1:]:
                p = l.split()
                if len(p) < 7 or not p[2].startswith("<Link#") or p[0].startswith(("lo", "gif", "stf", "utun", "awdl", "llw", "anpi", "bridge", "ap")):
                    continue
                if p[0] in vistos:
                    continue
                vistos.add(p[0])
                # colunas: Name Mtu Network [Address] Ipkts Ierrs Ibytes ...; sem Address o índice cai 1
                nums = [x for x in p[3:] if x.isdigit() or x == "-"]
                total += int(nums[2]) if len(nums) >= 3 and nums[2].isdigit() else 0
            return total
        if WIN:
            out = subprocess.run(["netstat", "-e"], capture_output=True, text=True, timeout=3).stdout
            m = re.search(r"(?:Bytes|bytes)\s+(\d+)\s+(\d+)", out)
            return int(m.group(1)) if m else 0
    except Exception:
        pass
    return 0


# ------------------------------------------------------------------ etapas
def sh_ok(cmd):
    """Teste rápido: comando de shell que sai 0 = já tem."""
    try:
        return subprocess.run(cmd, shell=True, capture_output=True, timeout=60).returncode == 0
    except Exception:
        return False


def tem_py(mod):
    return sh_ok(f'{PY} -c "import {mod}"')


def pip(pac):
    return f'{PY} -m pip install --user --progress-bar raw "{pac}" || {PY} -m pip install --user --progress-bar raw --break-system-packages "{pac}"'


class Etapa:
    def __init__(self, grupo, nome, cmd, teste=None, mb=1, sempre=False, interativo=False, opcional=False, quando=True):
        self.grupo, self.nome, self.cmd, self.teste, self.mb = grupo, nome, cmd, teste, mb
        self.sempre, self.interativo, self.opcional, self.quando = sempre, interativo, opcional, quando
        self.estado = "?"          # ? conferindo | ja | falta | rodando | ok | erro
        self.baixado = 0
        self.total = 0             # tamanho que a ferramenta informou (0 = não sabe)
        self.feito = 0             # quanto a ferramenta diz que já baixou (pip raw, git); vale mais que o contador
        self.linha = ""
        self.dur = 0.0
        self.erro = ""


def etapas_mac(cfg):
    brew = lambda f: f'brew install {f}'
    ed = cfg.get("editor", "davinci")
    E = []
    G = "Ferramentas"
    E += [Etapa(G, "ffmpeg (vídeo e áudio)", brew("ffmpeg"), lambda: shutil.which("ffmpeg"), mb=180),
          Etapa(G, "yt-dlp (baixar vídeo público)", brew("yt-dlp"), lambda: shutil.which("yt-dlp"), mb=15),
          Etapa(G, "Node.js (HyperFrames)", brew("node"), lambda: shutil.which("node"), mb=35),
          Etapa(G, "git", brew("git"), lambda: shutil.which("git"), mb=15)]
    G = "Python"
    for mod, pac, uso, tam in [("PIL", "pillow", "imagens", 5), ("numpy", "numpy", "contas de imagem", 7),
                               ("cv2", "opencv-python", "rastreio e recortes", 45), ("requests", "requests", "Instagram", 1),
                               ("dotenv", "python-dotenv", "Instagram", 1), ("fontTools", "fonttools", "morph e sketch", 4),
                               ("psd_tools", "psd-tools", "animar PSD", 3), ("fitz", "pymupdf", "animar PDF do Canva", 22)]:
        E.append(Etapa(G, f"{pac} ({uso})", pip(pac), (lambda m=mod: tem_py(m)), mb=tam))
    if ed == "davinci":
        E += [Etapa(G, "OCR da Apple (legenda no DaVinci)", pip("pyobjc-framework-Vision"), lambda: tem_py("Vision"), mb=2),
              Etapa(G, "cliques no DaVinci (Quartz)", pip("pyobjc-framework-Quartz"), lambda: tem_py("Quartz"), mb=2)]
    if ed == "finalcut":
        E.append(Etapa(G, "acessibilidade (Final Cut)", pip("pyobjc-framework-ApplicationServices"), lambda: tem_py("ApplicationServices"), mb=2))
    G = "3D"
    E.append(Etapa(G, "Blender (3D nos motions)", "brew install --cask blender", lambda: Path("/Applications/Blender.app").exists(), mb=420))
    ccb = HOME / ".claude/referencias/cc-blender-skill"
    E.append(Etapa(G, "cc-blender-skill (30 skills de Blender)",
                   f'mkdir -p "{ccb.parent}" "{HOME}/.claude/skills"; '
                   f'if [ -d "{ccb}/.git" ]; then git -C "{ccb}" pull --progress; else git clone --progress --depth 1 https://github.com/RobLe3/cc-blender-skill.git "{ccb}"; fi && '
                   f'for d in "{ccb}"/plugin/skills/*/; do n="$(basename "$d")"; [ -f "$d/SKILL.md" ] || continue; '
                   f'if [ -e "{HOME}/.claude/skills/$n" ] && [ ! -f "{HOME}/.claude/skills/$n/.cc-blender" ]; then continue; fi; '
                   f'rm -rf "{HOME}/.claude/skills/$n"; cp -R "$d" "{HOME}/.claude/skills/$n"; touch "{HOME}/.claude/skills/$n/.cc-blender"; done',
                   sempre=True, mb=4))
    G = "Motions e design"
    npx = "npx --yes skills add"
    E += [Etapa(G, "HyperFrames (motions)", f"{npx} heygen-com/hyperframes -g -a claude-code -s '*' -y", sempre=True, mb=8),
          Etapa(G, "HyperFrames: navegador de render", "npx --yes hyperframes doctor", sempre=True, mb=5, opcional=True),
          Etapa(G, "carrossel do Instagram (PNG/PDF)", f'{PY} "{DEST}/instagram/carrossel/carrossel.py" instalar',
                lambda: (DEST / "instagram/carrossel/template/node_modules").exists(), mb=60),
          Etapa(G, "taste-skill (design)", f"{npx} leonxlnx/taste-skill -g -a claude-code -s design-taste-frontend -s image-to-code -y", sempre=True, mb=2),
          Etapa(G, "web-design-guidelines", f"{npx} vercel-labs/agent-skills -g -a claude-code -s web-design-guidelines -y", sempre=True, mb=2),
          Etapa(G, "playwright-cli (navegador)", 'command -v playwright-cli >/dev/null || npm install -g @playwright/cli@latest; cd ~ && playwright-cli install --skills',
                sempre=True, mb=12, opcional=True),
          Etapa(G, "REA (engenharia reversa)", f"{npx} morluto/rea -g -a claude-code -s reverse-engineer-anything -y && npx --yes rea-agents setup --client claude_code --yes",
                sempre=True, mb=30, opcional=True)]
    for nome, url, tam in [("awesome-design-md (DESIGN.md de 70+ marcas)", "https://github.com/voltagent/awesome-design-md.git", 20),
                           ("awesome-opus5-5-videos (inspiração de motions)", "https://github.com/yihui-dev/awesome-opus5-5-videos.git", 60)]:
        d = HOME / ".claude/referencias" / url.rsplit("/", 1)[1][:-4]
        E.append(Etapa(G, nome, f'mkdir -p "{d.parent}"; if [ -d "{d}/.git" ]; then git -C "{d}" pull --progress; else git clone --progress --depth 1 {url} "{d}"; fi',
                       sempre=True, mb=tam, opcional=True))
    G = "Editor"
    tpl = HOME / "Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Templates"
    E += [Etapa(G, "fontes do Gab (Poppins, Playfair, Lobster)",
                f'mkdir -p "{HOME}/Library/Fonts"; find "{DEST}/assets/fontes" -type f \\( -name "*.ttf" -o -name "*.otf" \\) -exec cp -n {{}} "{HOME}/Library/Fonts/" \\;',
                sempre=True, mb=0),
          Etapa(G, "lettering e títulos OGraf no DaVinci",
                f'mkdir -p "{tpl}/Edit/Titles/OGraf"; for f in "{DEST}"/assets/lettering/*.drfx; do [ -f "$f" ] && cp -f "$f" "{tpl}/"; done; '
                f'for d in "{DEST}"/ograf/*/; do ls "$d"*.ograf.json >/dev/null 2>&1 && cp -R "${{d%/}}" "{tpl}/Edit/Titles/OGraf/"; done; true',
                sempre=True, mb=0)]
    # transcrição: o DaVinci 21.1+ transcreve sozinho; abaixo disso, Whisper local
    app = Path("/Applications/DaVinci Resolve/DaVinci Resolve.app")
    precisa_whisper = True
    if app.exists():
        v = subprocess.run(["defaults", "read", str(app / "Contents/Info"), "CFBundleShortVersionString"], capture_output=True, text=True).stdout.strip()
        try:
            precisa_whisper = tuple(int(x) for x in (v.split(".") + ["0", "0"])[:2]) < (21, 1)
        except ValueError:
            pass
    wpk, wmod = ("mlx-whisper", "mlx_whisper") if platform.machine() == "arm64" else ("faster-whisper", "faster_whisper")
    E.append(Etapa(G, f"Whisper local ({wpk}, DaVinci abaixo da 21.1)", pip(wpk), lambda: tem_py(wmod), mb=40, quando=precisa_whisper))
    E += [Etapa(G, "Premiere Pro (plugin Gab Ponte)", f'OGAB_SEM_CONFIG=1 bash "{DEST}/premiere/instalar.sh"', sempre=True, mb=1, opcional=True),
          Etapa(G, "After Effects (Gab Ponte AE)", f'OGAB_SEM_CONFIG=1 bash "{DEST}/aftereffects/instalar.sh"', sempre=True, mb=1, opcional=True)]
    lut_d = Path("/Library/Application Support/Blackmagic Design/DaVinci Resolve/LUT/LUT DO GAB")
    lut_s = DEST / "premiere/assets/lut/LUT DO GAB.cube"
    E.append(Etapa(G, "LUT DO GAB no DaVinci (pode pedir a senha do Mac)",
                   f'mkdir -p "{lut_d}" 2>/dev/null && cp -f "{lut_s}" "{lut_d}/" 2>/dev/null || '
                   f'{{ sudo mkdir -p "{lut_d}" && sudo cp -f "{lut_s}" "{lut_d}/" && sudo chmod -R a+rwX "{lut_d}"; }}',
                   lambda: (lut_d / "LUT DO GAB.cube").exists(), mb=0, interativo=True, quando=lut_s.exists()))
    if cfg.get("voz_local", {}).get("ativo"):
        vs = f'zsh "{DEST}/voz_local/voicestudio.sh"'
        E.append(Etapa("Voz local", "clonador de voz (motor + modelo OmniVoice)", f"{vs} instalar && {vs} modelo && {vs} stop",
                       lambda: sh_ok(f"{vs} status"), mb=5600))
    return [e for e in E if e.quando]


# ------------------------------------------------------------------ painel
class Painel:
    def __init__(self, etapas):
        self.E, self.t0, self.alt = etapas, time.time(), 0
        self.rede0 = bytes_rede()
        self.rede, self.vel, self._ult = self.rede0, 0.0, (time.time(), self.rede0)
        self.atual, self.pausado, self.lock = None, False, threading.Lock()
        self.giro = 0
        self.titulo = "Instalando o Gab (/ogab)"

    def medir(self):
        agora, b = time.time(), bytes_rede()
        t, b0 = self._ult
        if agora - t >= .5:
            inst = max(0, b - b0) / (agora - t)
            self.vel = inst if self.vel == 0 else self.vel * .6 + inst * .4
            self._ult = (agora, b)
        self.rede = b
        if self.atual:
            self.atual.baixado = max(0, b - self.atual._rede0)

    def linhas(self, tudo=False):
        L = []
        cols = shutil.get_terminal_size((90, 30)).columns
        fazer = [e for e in self.E if e.estado not in ("ja",)]
        prontas = [e for e in fazer if e.estado in ("ok", "erro")]
        peso = lambda e: max(e.mb, 1)
        total = sum(peso(e) for e in fazer) or 1
        feito = sum(peso(e) for e in prontas)
        if self.atual:
            a = self.atual
            if a.total:
                feito += peso(a) * min(1, (a.feito or a.baixado) / a.total)
            elif a.mb > 1:
                feito += peso(a) * min(.95, a.baixado / (a.mb * 1e6))
        frac = feito / total
        baixado = self.rede - self.rede0
        est = sum(e.mb for e in fazer) * 1e6
        L.append(NEG(self.titulo) + CINZA(f"   {tempo(time.time() - self.t0)}"))
        L.append(f"{AZUL(barra(frac, 36))} {frac * 100:3.0f}%   {len(prontas)}/{len(fazer)} etapas")
        L.append(f"baixado {NEG(mb(baixado))}" + CINZA(f" de ~{mb(max(est, baixado))}") +
                 f"   {mb(self.vel)}/s" + (CINZA(f"   falta ~{tempo(max(0, est - baixado) / self.vel)}") if self.vel > 2e5 and est > baixado and len(prontas) < len(fazer) else ""))
        L.append("")
        giro = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"[self.giro % 10]
        itens, grupo = [], None   # (tipo, texto): tipo decide o que some primeiro quando a tela é pequena
        for e in self.E:
            if e.grupo != grupo:
                grupo = e.grupo
                itens.append(("grupo", CINZA(f"  {grupo}")))
            if e.estado == "ja":
                itens.append(("ja", f"   {CINZA('✓ ' + e.nome + '  (já tinha)')}"))
            elif e.estado == "ok":
                itens.append(("ok", f"   {VERDE('✓')} {e.nome}" + CINZA(f"  {tempo(e.dur)}" + (f", {mb(e.baixado)}" if e.baixado > 5e5 else ""))))
            elif e.estado == "erro":
                itens.append(("erro", f"   {VERM('✗') if not e.opcional else AMAR('!')} {e.nome}" + CINZA("  (detalhes no fim)")))
            elif e.estado == "rodando":
                agora = min(e.feito or e.baixado, e.total) if e.total else e.baixado
                info = mb(agora) + (f" de {mb(e.total)}" if e.total else (f" de ~{mb(e.mb * 1e6)}" if e.mb > 5 else ""))
                sub = f"  {barra(agora / e.total, 14)}" if e.total else ""
                itens.append(("run", f"   {AMAR(giro)} {NEG(e.nome)}  {AMAR(info)}{sub}  {mb(self.vel)}/s"))
                if e.linha:
                    itens.append(("run", CINZA(f"       {e.linha[:cols - 10]}")))
            elif e.estado == "?":
                itens.append(("fila", CINZA(f"   … {e.nome}  (conferindo)")))
            else:
                itens.append(("fila", CINZA(f"   · {e.nome}" + ("  (atualiza)" if e.sempre else "") + (f"  ~{mb(e.mb * 1e6)}" if e.mb >= 5 else ""))))
        alt = shutil.get_terminal_size((90, 30)).lines - 1
        if tudo or len(L) + len(itens) <= alt:
            return L + [t for _, t in itens]
        # não cabe: resumo dos prontos, erros, o que está rodando e o começo da fila
        ja = sum(1 for e in self.E if e.estado == "ja")
        ok = [e for e in self.E if e.estado == "ok"]
        L.append(VERDE(f"  ✓ {len(ok)} instalados agora") + CINZA(f"  ·  {ja} já tinha") + (CINZA(f"  ·  último: {ok[-1].nome}") if ok else ""))
        L += [t for k, t in itens if k in ("erro", "run")]
        fila = [t for k, t in itens if k == "fila"]
        cabe = max(0, alt - len(L) - 1)
        L += fila[:cabe]
        if len(fila) > cabe:
            L.append(CINZA(f"   … e mais {len(fila) - cabe} na fila"))
        return L

    def salvar_status(self, fim=False):
        """Estado em ~/.claude/ogab-instalacao.json: o Claude lê com `instalador.py --status` e mostra no chat."""
        try:
            fazer = [e for e in self.E if e.estado != "ja"]
            st = {"atualizado": time.time(), "fim": fim, "titulo": self.titulo,
                  "painel": [re.sub(r"\x1b\[[0-9;]*m", "", l) for l in self.linhas(tudo=True)],
                  "prontas": [e.nome for e in self.E if e.estado == "ok"], "ja_tinha": [e.nome for e in self.E if e.estado == "ja"],
                  "erros": [{"nome": e.nome, "erro": e.erro, "comando": e.cmd, "opcional": e.opcional} for e in self.E if e.estado == "erro"],
                  "fila": [e.nome for e in self.E if e.estado in ("falta", "?")],
                  "atual": self.atual.nome if self.atual else None, "etapas": [len([e for e in fazer if e.estado in ("ok", "erro")]), len(fazer)],
                  "baixado_mb": round((self.rede - self.rede0) / 1e6, 1), "mb_s": round(self.vel / 1e6, 2)}
            STATUS.write_text(json.dumps(st, ensure_ascii=False))
        except Exception:
            pass

    def desenhar(self, final=False):
        if not TTY:
            with self.lock:
                self.medir()
                self.salvar_status()
                a = self.atual
                if a and not a.interativo and time.time() - getattr(self, "_txt", 0) >= 5:
                    self._txt = time.time()
                    agora = min(a.feito or a.baixado, a.total) if a.total else a.baixado
                    print(f"    ... {a.nome}: {mb(agora)}" + (f" de {mb(a.total)}" if a.total else "") + f" ({mb(self.vel)}/s)", flush=True)
            return
        with self.lock:
            self.salvar_status()
            if self.pausado and not final:
                return
            self.medir()
            self.giro += 1
            L = self.linhas()
            s = ("\033[%dF\033[J" % self.alt if self.alt else "") + "\n".join(L) + "\n"
            sys.stdout.write(s)
            sys.stdout.flush()
            self.alt = len(L)

    def soltar(self):
        """Antes de uma etapa interativa (senha): deixa o painel parado na tela e libera o terminal."""
        self.desenhar(final=True)
        self.pausado, self.alt = True, 0

    def retomar(self):
        self.pausado = False


# ------------------------------------------------------------------ execução
TAM = re.compile(r"\(([\d.]+)\s*(kB|MB|GB)\)")
RAW = re.compile(r"Progress (\d+) of (\d+)")
GIT = re.compile(r"Receiving objects:\s+(\d+)%.*?([\d.]+)\s*(KiB|MiB|GiB)")


def rodar(e, painel, log):
    e.estado, e._rede0, t0 = "rodando", bytes_rede(), time.time()
    painel.atual = e
    if not TTY:
        n = [x for x in painel.E if x.estado != "ja"]
        print(f"[{n.index(e) + 1}/{len(n)}] {e.nome}...", flush=True)
    log.write(f"\n===== {e.grupo} / {e.nome}\n$ {e.cmd}\n")
    log.flush()
    if e.interativo:
        painel.soltar()
        print(AMAR(f"  → {e.nome}"))
        rc = subprocess.run(e.cmd, shell=True, executable="/bin/bash" if MAC else None).returncode
        painel.retomar()
    else:
        p = subprocess.Popen(e.cmd, shell=True, executable="/bin/bash" if MAC else None, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, env=dict(os.environ, HOMEBREW_NO_AUTO_UPDATE="1"))
        tamanhos, base_pip = 0.0, 0   # vários arquivos no mesmo pip: soma os que já terminaram
        buf = b""
        while True:
            ch = p.stdout.read1(4096) if hasattr(p.stdout, "read1") else p.stdout.read(1)
            if not ch:
                break
            log.write(ch.decode("utf-8", "replace"))
            buf += ch
            *partes, buf = re.split(rb"[\r\n]", buf)
            for parte in partes:
                l = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", parte.decode("utf-8", "replace")).strip()
                if not l:
                    continue
                m = TAM.search(l)
                if m and "Downloading" in l:
                    tamanhos += float(m.group(1)) * {"kB": 1e3, "MB": 1e6, "GB": 1e9}[m.group(2)]
                    e.total = int(tamanhos)
                r = RAW.search(l)
                if r:
                    feito, tot = int(r.group(1)), int(r.group(2))
                    e.feito = base_pip + feito
                    if feito >= tot:
                        base_pip += tot
                    e.total = max(e.total, base_pip if feito >= tot else base_pip + tot)
                    continue          # não mostra "Progress ..." como linha de status
                g = GIT.search(l)
                if g and int(g.group(1)) > 0:
                    rec = float(g.group(2)) * {"KiB": 1024, "MiB": 1024 ** 2, "GiB": 1024 ** 3}[g.group(3)]
                    e.total = int(rec * 100 / int(g.group(1)))
                    e.feito = int(rec)
                e.linha = l
        rc = p.wait()
    e.dur = time.time() - t0
    e.baixado = e.total if e.total else max(e.baixado, bytes_rede() - e._rede0)
    e.estado = "ok" if rc == 0 else "erro"
    if rc:
        e.erro = e.linha or f"saiu com código {rc}"
    if not TTY:
        print(f"    {'ok' if rc == 0 else ('AVISO' if e.opcional else 'ERRO')}: {e.nome} ({tempo(e.dur)}" +
              (f", {mb(e.baixado)}" if e.baixado > 5e5 else "") + ")" + (f": {e.erro[:100]}" if rc else ""), flush=True)
    log.write(f"\n----- {'ok' if rc == 0 else 'ERRO ' + str(rc)} em {e.dur:.0f}s\n")
    log.flush()
    painel.atual = None


def perguntar(cfg):
    """As perguntas vêm todas antes do painel (depois ele roda sozinho)."""
    entrada = sys.stdin if sys.stdin.isatty() else None
    if entrada is None and MAC:
        try:
            entrada = open("/dev/tty")
        except OSError:
            entrada = None   # sem terminal (ex.: o Claude rodando): vale variável de ambiente ou o padrão

    def ler(msg, padrao):
        if entrada is None:
            return padrao
        sys.stdout.write(msg)
        sys.stdout.flush()
        r = entrada.readline().strip()
        return r or padrao

    sys.path.insert(0, str(DEST / "scripts"))
    import termos   # aceite obrigatório (regra do autor, 22/10/2026): relatos anônimos fazem parte dos termos
    if not termos.aceito():
        if os.environ.get("OGAB_ACEITO") != "sim":
            print("\n" + termos.RESUMO)
            r = ler("  ", "")
            if r.strip().upper() not in ("ACEITO", "ACEITA", "ACEITE"):
                sys.exit("\n  Instalação cancelada: os termos não foram aceitos. Nada foi instalado.")
        termos.gravar(True)
        cfg.update(json.loads(CFG.read_text()))
    ed = os.environ.get("OGAB_EDITOR") or cfg.get("editor")
    if not ed:
        r = ler("\n  Em qual editor o Gab vai montar seus vídeos?\n    1) DaVinci Resolve Studio\n    2) Adobe Premiere Pro\n"
                "    3) CapCut (beta, grátis)\n    4) Final Cut Pro (beta)\n"
                "    5) Nenhum: o Claude faz tudo e entrega o MP4 pronto\n  Escolha [1-5]: ", "1")
        ed = {"2": "premiere", "3": "capcut", "4": "finalcut", "5": "nenhum"}.get(r, "davinci")
        if ed == "nenhum":
            print("  Ok. Dica: o CapCut é grátis (capcut.com); com ele você abre o vídeo e muda o que quiser.\n"
                  "  Instalou depois? /ogab config editor capcut (os vídeos já feitos vão junto com capcut.py levar).")
    cfg["editor"] = ed if ed in ("davinci", "premiere", "capcut", "finalcut", "nenhum") else "davinci"
    mo = os.environ.get("OGAB_MOTION") or cfg.get("motion")
    if not mo:
        r = ler("\n  Como o Gab faz os motions?\n    1) Automático (HyperFrames, rápido)\n"
                "    2) No After Effects (camadas editáveis)\n  Escolha [1/2]: ", "1")
        mo = "aftereffects" if r == "2" else "hyperframes"
    cfg["motion"] = mo
    # relatos anônimos: já vêm ligados pelo aceite dos termos (seção 2 de docs/TERMOS.md)
    v = cfg.setdefault("voz_local", {"motor": "omnivoice", "passos": 32})
    if MAC and platform.machine() == "arm64" and not v.get("perguntado"):
        r = os.environ.get("OGAB_VOZ_LOCAL") or ler("\n  Quer o clonador de voz LOCAL (narra com a sua voz no Mac, grátis)? Baixa ~5,5 GB;\n"
                "  o modelo padrão é de uso NÃO comercial (cliente continua no ElevenLabs). [s/N]: ", "n")
        v["perguntado"], v["ativo"] = True, r.lower().startswith("s")
    CFG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2))
    return cfg


def etapas_demo():
    """Teste do painel sem instalar nada: baixa de verdade para uma pasta temporária e apaga no fim."""
    t = Path(os.environ.get("TMPDIR", "/tmp")) / "ogab_demo_instalador"
    return [Etapa("Demo", "download direto (curl, 80 MB)", f'mkdir -p "{t}" && curl -L --progress-bar -o "{t}/a.bin" "https://speed.cloudflare.com/__down?bytes=80000000"', mb=80),
            Etapa("Demo", "pacote Python (pip download opencv)", f'{PY} -m pip download --no-cache-dir --no-deps --progress-bar raw -d "{t}/pip" opencv-python', mb=45),
            Etapa("Demo", "repositório (git clone)", f'git clone --progress --depth 1 https://github.com/voltagent/awesome-design-md.git "{t}/git"', mb=20),
            Etapa("Demo", "algo que já está instalado", "true", lambda: True),
            Etapa("Demo", "etapa que falha (opcional)", "exit 3", mb=0, opcional=True),
            Etapa("Demo", "limpar a pasta temporária", f'rm -rf "{t}"', mb=0)]


def mostrar_status():
    """Para o Claude (ou outra aba): o painel da instalação que está rodando, em texto."""
    if not STATUS.exists():
        sys.exit("Nenhuma instalação rodando (ainda não existe ~/.claude/ogab-instalacao.json).")
    st = json.loads(STATUS.read_text())
    idade = time.time() - st.get("atualizado", 0)
    print("\n".join(st["painel"]))
    if st.get("fim"):
        print("\nTERMINOU." + (f" {len(st['erros'])} item(ns) com problema (ver acima e no log)." if st["erros"] else " Tudo certo."))
    elif idade > 120:
        print(f"\n(sem atualização há {tempo(idade)}: o instalador pode ter parado; ver {LOG})")


def main():
    if "--status" in sys.argv:
        return mostrar_status()
    lista_so = "--lista" in sys.argv
    demo = "--demo" in sys.argv
    if not CFG.exists():
        shutil.copy(DEST / "config.example.json", CFG)
    try:
        cfg = json.loads(CFG.read_text())
    except Exception:
        CFG.rename(CFG.with_name(f"config.json.quebrado.{int(time.time())}"))
        shutil.copy(DEST / "config.example.json", CFG)
        cfg = json.loads(CFG.read_text())
    if not (lista_so or demo):
        cfg = perguntar(cfg)
    if not MAC:
        sys.exit("Este painel por enquanto é do instalador do Mac; no Windows use windows/install.ps1.")
    E = etapas_demo() if demo else etapas_mac(cfg)
    painel = Painel(E)
    if lista_so:
        painel.titulo = "Gab (/ogab): o que já tem e o que o instalador faria"
    print()
    parar = threading.Event()

    def laco():
        while not parar.is_set():
            painel.desenhar()
            time.sleep(.25)
    th = threading.Thread(target=laco, daemon=True)
    th.start()
    # 1) confere o que já tem (vai riscando na tela)
    for e in E:
        e.estado = "falta" if (e.sempre or not e.teste) else ("ja" if e.teste() else "falta")
    if lista_so:
        parar.set(); th.join(); painel.desenhar(final=True)
        return
    # 2) instala o que falta
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as log:
        log.write(f"\n\n######## instalação {time.strftime('%d/%m/%Y %H:%M')} ({platform.platform()})\n")
        for e in E:
            if e.estado == "falta":
                rodar(e, painel, log)
    parar.set(); th.join()
    painel.desenhar(final=True)
    painel.salvar_status(fim=True)
    # 3) resumo
    novos = [e for e in E if e.estado == "ok"]
    ja = [e for e in E if e.estado == "ja"]
    erros = [e for e in E if e.estado == "erro"]
    print(f"\n{VERDE('✓')} {len(novos)} instalados/atualizados agora   {CINZA(f'{len(ja)} já estavam')}   "
          f"baixado no total: {mb(painel.rede - painel.rede0)} em {tempo(time.time() - painel.t0)}")
    if erros:
        print(AMAR("\nNão deu certo (o resto funciona; detalhes em " + str(LOG) + "):"))
        for e in erros:
            print(f"  {'!' if e.opcional else '✗'} {e.nome}: {CINZA(e.erro[:120])}\n      rode de novo: {CINZA(e.cmd[:160])}")
    if demo:
        return
    print(NEG("\nConferência final (doctor: confere tudo e corrige o que der)"))
    subprocess.run([sys.executable, str(DEST / "scripts/doctor.py"), "--corrigir"])
    print(f"""
Pronto. Seu Gab vai editar no: {NEG(cfg.get('editor'))}   |   motions: {NEG(cfg.get('motion'))}
(trocar a qualquer hora: /ogab config editor davinci|premiere|capcut|finalcut|nenhum  e  /ogab config motion hyperframes|aftereffects)

Falta só o que precisa de você (uma vez), no app que você usa:
  DaVinci:        Preferences > System > General > External scripting using: Local (e reinicie o Resolve).
                  Reinicie o DaVinci para carregar o lettering (@gabrielxreis_ Text Presets) e os títulos OGraf.
  Premiere:       Window > UXP Plugins > Gab Ponte (deixe o painel encaixado).
  CapCut:         abra o CapCut uma vez e entre na sua conta; feche o projeto quando o Gab for gravar nele.
  Final Cut Pro:  crie uma biblioteca (Arquivo > Nova > Biblioteca) e deixe aberta; dê Acessibilidade ao Terminal/Claude.
  Sem editor:     nada: o Gab entrega o MP4 pronto (recomendado instalar o CapCut, grátis, para customizar).
  After Effects:  nada: a ponte sobe sozinha (se o AE estava aberto na instalação, feche e rode o instalador de novo).
  Todos:          conecte as SUAS contas no Claude (Configurações > Conectores): ElevenLabs, Artlist, Envato, Magnific...
                  e a extensão Claude in Chrome logada nos sites (downloads são pelo navegador).

Reinicie o Claude Code e digite:  {NEG('/ogab comecar')}
""")


if __name__ == "__main__":
    main()
