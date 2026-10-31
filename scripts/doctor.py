"""Doctor do Gab: confere a instalação inteira e CORRIGE sozinho o que dá (Mac e Windows).

  python3 doctor.py               # só confere
  python3 doctor.py --corrigir    # confere e corrige o que for possível sem o usuário
  python3 doctor.py --json        # saída para outro programa (instalador, Gab)

Saída: uma linha por item.  ✓ ok  |  ⟳ corrigido agora  |  ! falta algo que só o usuário faz (com o passo)  |  · não usado
Os apps que o usuário NÃO escolheu (config.json editor/motion) aparecem como "·" quando faltam: tudo é instalado,
mas só o app escolhido é obrigatório. Sai com código 1 se faltar algo obrigatório.
"""
from pathlib import Path
import glob, hashlib, json, os, platform, re, shutil, subprocess, sys, urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAC, WIN = sys.platform == "darwin", os.name == "nt"
HOME = os.path.expanduser("~")
CORRIGIR = "--corrigir" in sys.argv
itens = []   # (estado, grupo, texto)


def item(estado, grupo, texto):
    itens.append((estado, grupo, texto))


def roda(cmd, timeout=900, **k):
    try:
        k.setdefault("errors", "replace")  # Windows: saida em cp850 (tasklist) quebrava o decode utf-8
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, **k)
        r.stdout = r.stdout or ""
        r.stderr = r.stderr or ""
        return r
    except Exception as e:
        return subprocess.CompletedProcess(cmd, 1, "", str(e))


def cfg():
    p = os.path.join(RAIZ, "config.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}


# ---------------------------------------------------------------- skill e configuração

def skill():
    g = ["git", "-C", RAIZ]
    if not os.path.isdir(os.path.join(RAIZ, ".git")):
        item("!", "skill", "a pasta da skill não é um clone do git: reinstale pelo instalador")
        return
    sujo = roda(g + ["status", "--porcelain", "--untracked-files=no"]).stdout.strip()
    roda(g + ["fetch", "-q"], timeout=60)
    atras = roda(g + ["rev-list", "--count", "HEAD..@{u}"]).stdout.strip()
    if sujo and atras not in ("", "0"):
        if CORRIGIR:
            roda(g + ["stash", "push", "-m", "doctor: mudanças locais guardadas antes do update"])
            r = roda(g + ["pull", "--ff-only", "-q"])
            item("⟳" if r.returncode == 0 else "!", "skill",
                 "mudanças locais guardadas (git stash list) e skill atualizada" if r.returncode == 0 else f"update falhou: {r.stderr.strip()[:120]}")
        else:
            item("!", "skill", f"mudanças locais travam o update ({atras} versões atrás): rode o doctor com --corrigir")
    elif atras not in ("", "0"):
        if CORRIGIR and roda(g + ["pull", "--ff-only", "-q"]).returncode == 0:
            item("⟳", "skill", f"skill atualizada ({atras} versões novas)")
        else:
            item("!", "skill", f"{atras} versões novas: rode /ogab update")
    else:
        item("✓", "skill", "skill atualizada")
    p = os.path.join(RAIZ, "config.json")
    if not os.path.exists(p):
        if CORRIGIR:
            shutil.copy(os.path.join(RAIZ, "config.example.json"), p); item("⟳", "skill", "config.json criado")
        else:
            item("!", "skill", "config.json não existe")
    c = cfg()
    if c and (not c.get("editor") or not c.get("motion")):
        if CORRIGIR:
            c.setdefault("editor", "davinci"); c.setdefault("motion", "hyperframes")
            json.dump(c, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            item("⟳", "skill", f"escolha gravada: editor {c['editor']}, motions {c['motion']} (trocar: /ogab config editor|motion ...)")
        else:
            item("!", "skill", "editor/motion não escolhidos no config.json")
    elif c:
        item("✓", "skill", f"editor {c['editor']}, motions {c['motion']}")


# ---------------------------------------------------------------- ferramentas

PACOTES = {  # binário: (brew, winget)
    "ffmpeg": ("ffmpeg", "Gyan.FFmpeg"), "yt-dlp": ("yt-dlp", "yt-dlp.yt-dlp"),
    "node": ("node", "OpenJS.NodeJS.LTS"), "git": ("git", "Git.Git"),
}


def instalar_pacote(brew, winget):
    if MAC and shutil.which("brew"):
        return roda(["brew", "install", brew]).returncode == 0
    if WIN and shutil.which("winget"):
        return roda(["winget", "install", "--id", winget, "-e", "--silent", "--accept-package-agreements",
                     "--accept-source-agreements"]).returncode == 0
    return False


def ferramentas():
    for b, (brew, wg) in PACOTES.items():
        if shutil.which(b):
            item("✓", "ferramentas", b)
        elif CORRIGIR and instalar_pacote(brew, wg):
            item("⟳", "ferramentas", f"{b} instalado")
        else:
            item("!", "ferramentas", f"{b} não encontrado: " + (f"brew install {brew}" if MAC else f"winget install --id {wg} -e"))
    docker()


def pip_instalar(pacote):
    """pip --user no Python que roda a skill (no Mac com Python do Homebrew precisa de --break-system-packages)."""
    pacote = {"opencv-python": "opencv-python<5"}.get(pacote, pacote)   # OpenCV 5.0 tirou o CascadeClassifier
    base = [sys.executable, "-m", "pip", "install", "--user", "--quiet", pacote]
    return roda(base).returncode == 0 or roda(base + ["--break-system-packages"]).returncode == 0


def python():
    """O Python que a skill usa e cada pacote de que algum recurso depende."""
    v = sys.version_info
    py3 = shutil.which("python3") or (shutil.which("py") if WIN else None)
    item("✓" if v >= (3, 10) else "!", "python", f"Python {v.major}.{v.minor}.{v.micro} em {sys.executable}"
         + ("" if v >= (3, 10) else ": precisa do 3.10 ou mais novo (" + ("brew install python" if MAC else "winget install Python.Python.3.12") + ")"))
    if not py3:
        item("!", "python", "o comando python3 não existe no terminal: " + ("brew install python" if MAC else "rode o windows\\install.ps1 (cria o atalho python3)"))
    elif MAC and os.path.realpath(py3) != os.path.realpath(sys.executable):
        r = roda([py3, "-c", "import sys; print(sys.version.split()[0])"]).stdout.strip()
        item("·", "python", f"python3 do terminal é outro ({py3}, {r}); a skill usa o que roda os scripts")
    if roda([sys.executable, "-m", "pip", "--version"]).returncode != 0:
        ok = CORRIGIR and roda([sys.executable, "-m", "ensurepip", "--user"]).returncode == 0
        item("⟳" if ok else "!", "python", "pip instalado" if ok else "pip não existe: " + sys.executable + " -m ensurepip --user")
    c = cfg()
    pacotes = [("PIL", "pillow", "imagens (prévias, legenda baixa, QC)", True),
               ("numpy", "numpy", "contas de imagem e rastreio", True),
               ("cv2", "opencv-python", "rastreio de texto/objeto/rosto (rastrear.py)", True),
               ("requests", "requests", "Instagram: publicar e ler dados (instagram/lib)", True),
               ("dotenv", "python-dotenv", "Instagram: chaves em instagram/.env", True),
               ("fontTools", "fonttools", "texto em contorno: morph de logo e preset sketch", True),
               ("psd_tools", "psd-tools", "animar arte em PSD (arte_animada.py)", False),
               ("fitz", "pymupdf", "animar arte do Canva/Illustrator em PDF (arte_animada.py)", False)]
    if sys.version_info < (3, 10):
        item("!", "python", f"Python {sys.version.split()[0]} é antigo (o do macOS); instale um 3.10+: "
             + ("brew install python e abra um Terminal novo" if MAC else "winget install --id Python.Python.3.12 -e"))
    if MAC and c.get("editor", "davinci") == "davinci":
        pacotes.append(("Vision", "pyobjc-framework-Vision", "OCR da legenda no DaVinci (legenda_ui.py)", False))
        pacotes.append(("Quartz", "pyobjc-framework-Quartz", "cliques da legenda no DaVinci (legenda_ui.py)", False))
    if MAC and c.get("editor") == "finalcut":
        pacotes.append(("ApplicationServices", "pyobjc-framework-ApplicationServices", "ajustes no Final Cut pela acessibilidade (finalcut/ax.py)", True))
    # CLAP (conferir se cada SFX é o que diz ser): torch + transformers ~2 GB, por isso não instala sozinho (15/10/2026)
    import importlib.util as _iu
    clap = [m for m in ("torch", "transformers") if _iu.find_spec(m) is None]
    item("✓" if not clap else "·", "python", "torch + transformers (conferência de SFX: sfx_conferir.py, sonorizar.py conferir)" if not clap
         else f"{' e '.join(clap)} faltando: sem a conferência automática de SFX (~2 GB; com espaço: {sys.executable} -m pip install --user torch transformers)")
    # Open-Unmix (separar faixas): instala sozinho no 1º uso de separar.py, aqui só informa
    unmix = _iu.find_spec("openunmix") is not None
    item("✓" if unmix else "·", "python", "openunmix (separar faixas da música: separar.py)" if unmix
         else "openunmix faltando: instala sozinho no 1º uso de separar.py (ou: separar.py --instalar)")
    for mod, pac, uso, obrig in pacotes:
        try:
            m_ = __import__(mod)
            if mod == "cv2" and not hasattr(m_, "CascadeClassifier"):   # relato 16/10/2026: dois OpenCV instalados juntos
                ok = CORRIGIR and roda([sys.executable, "-m", "pip", "uninstall", "-y", "opencv-python", "opencv-python-headless",
                                        "opencv-contrib-python"]).returncode == 0 and pip_instalar("opencv-python<5")  # 5.0 tirou o CascadeClassifier
                item("⟳" if ok else "!", "python", "opencv-python reinstalado (detecção de rosto)" if ok else
                     f"OpenCV sem detecção de rosto: {sys.executable} -m pip uninstall -y opencv-python opencv-python-headless opencv-contrib-python && {sys.executable} -m pip install --user \"opencv-python<5\"")
                continue
            item("✓", "python", f"{pac} ({uso})")
        except Exception:
            ok = CORRIGIR and pip_instalar(pac)
            item("⟳" if ok else ("!" if obrig else "·"), "python",
                 f"{pac} instalado ({uso})" if ok else f"{pac} faltando ({uso}): {sys.executable} -m pip install --user {pac}")


def ffmpeg_detalhes():
    if not shutil.which("ffmpeg"):
        return
    enc = roda(["ffmpeg", "-hide_banner", "-encoders"]).stdout
    fil = roda(["ffmpeg", "-hide_banner", "-filters"]).stdout
    faltam = [n for n, txt in (("prores_ks (MOV com alfa)", "prores_ks"), ("libx264 (MP4)", "libx264"), ("aac", " aac "))
              if txt not in enc] + [n for n, txt in (("loudnorm", "loudnorm"), ("ebur128", "ebur128")) if txt not in fil]
    item("✓" if not faltam else "!", "ferramentas", "ffmpeg com ProRes 4444, H.264, AAC, loudnorm e ebur128" if not faltam
         else "ffmpeg sem " + ", ".join(faltam) + ": reinstale o ffmpeg completo (" + ("brew reinstall ffmpeg" if MAC else "winget install Gyan.FFmpeg") + ")")
    if shutil.which("node"):
        nv = roda(["node", "--version"]).stdout.strip().lstrip("v")
        maior = int(nv.split(".")[0]) if nv[:1].isdigit() else 0
        item("✓" if maior >= 18 else "!", "ferramentas", f"Node {nv}" + ("" if maior >= 18 else ": precisa do 18+ (HyperFrames)"))
    livre = shutil.disk_usage(HOME).free / 1e9
    item("✓" if livre >= 20 else "!", "ferramentas", f"{livre:.0f} GB livres no disco" + ("" if livre >= 20 else ": render e takes precisam de 20 GB+; libere espaço"))


def _versao_app(caminho_app):
    if MAC:
        v = roda(["defaults", "read", os.path.join(caminho_app, "Contents", "Info"), "CFBundleShortVersionString"]).stdout.strip()
    else:
        v = roda(["powershell", "-NoProfile", "-Command", f"(Get-Item '{caminho_app}').VersionInfo.ProductVersion"]).stdout.strip()
    try:
        return tuple(int(x) for x in re.findall(r"\d+", v)[:3]), v
    except Exception:
        return (0,), v


def docker():
    """Docker é OPCIONAL: o HyperFrames só usa no render com --docker (saída idêntica entre máquinas), que o Gab não
    usa. O aviso "Docker: not found" do hyperframes doctor pode ser ignorado."""
    app = "/Applications/Docker.app" if MAC else os.path.join(os.environ.get("ProgramFiles", ""), "Docker", "Docker", "Docker Desktop.exe")
    if shutil.which("docker") or os.path.exists(app):
        item("·", "ferramentas", "Docker instalado (opcional, o Gab não usa)")
    else:
        item("·", "ferramentas", "Docker não instalado: opcional, o Gab não usa (ignore o aviso do hyperframes doctor)")


def _instalar_blender():
    if WIN:
        return instalar_pacote("", "BlenderFoundation.Blender")
    return sys.stdin.isatty() and roda(["brew", "install", "--cask", "blender"]).returncode == 0   # pede senha: só com alguém no terminal


def blender():
    cands = ["/Applications/Blender.app"] if MAC else glob.glob(os.path.join(os.environ.get("ProgramFiles", ""), "Blender Foundation", "Blender*"))
    if any(os.path.exists(c) for c in cands):
        item("✓", "extras", "Blender (3D de verdade: tresd/tresd.py)")
    elif CORRIGIR and _instalar_blender():
        item("⟳", "extras", "Blender instalado")
    else:
        item("·", "extras", "Blender não instalado (só para motion 3D): " + ("brew install --cask blender" if MAC else "winget install --id BlenderFoundation.Blender -e"))
    ccb = glob.glob(os.path.join(HOME, ".claude", "skills", "*", ".cc-blender"))
    if len(ccb) >= 25:
        item("✓", "extras", f"cc-blender-skill ({len(ccb)} skills de Blender)")
    else:
        item("!", "extras", "cc-blender-skill não instalado (objetos 3D): rode o instalador do Gab de novo")


def extras():
    if os.path.isdir(os.path.join(HOME, ".claude", "skills", "hyperframes")):
        item("✓", "extras", "skills do HyperFrames")
    elif CORRIGIR and roda(["npx", "--yes", "skills", "add", "heygen-com/hyperframes", "-g", "-a", "claude-code", "-s", "*", "-y"],
                           shell=WIN).returncode == 0:
        item("⟳", "extras", "skills do HyperFrames instaladas")
    else:
        item("!", "extras", "skills do HyperFrames: npx skills add heygen-com/hyperframes -g -a claude-code -s '*' -y")
    car = os.path.join(RAIZ, "instagram", "carrossel")
    if os.path.isdir(os.path.join(car, "template", "node_modules", "next")):
        item("✓", "extras", "carrossel do Instagram (slides PNG/PDF)")
    elif CORRIGIR and roda([sys.executable, os.path.join(car, "carrossel.py"), "instalar"]).returncode == 0:
        item("⟳", "extras", "carrossel do Instagram instalado")
    else:
        item("!", "extras", "carrossel do Instagram: python3 instagram/carrossel/carrossel.py instalar")
    for nome, url in (("awesome-design-md", "https://github.com/voltagent/awesome-design-md.git"),
                      ("awesome-opus5-5-videos", "https://github.com/yihui-dev/awesome-opus5-5-videos.git")):
        d = os.path.join(HOME, ".claude", "referencias", nome)
        if os.path.isdir(os.path.join(d, ".git")):
            item("✓", "extras", f"referência {nome}")
        elif CORRIGIR and roda(["git", "clone", "--depth", "1", "-q", url, d]).returncode == 0:
            item("⟳", "extras", f"referência {nome} baixada")
        else:
            item("!", "extras", f"referência {nome} faltando (rode com --corrigir)")
    fontes = os.path.join(HOME, "Library", "Fonts") if MAC else os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "Fonts")
    faltam = [f for f in glob.glob(os.path.join(RAIZ, "assets", "fontes", "*", "*.ttf")) if not os.path.exists(os.path.join(fontes, os.path.basename(f)))]
    if not faltam:
        item("✓", "extras", "fontes (Poppins, Playfair, Lobster)")
    elif CORRIGIR and MAC:
        os.makedirs(fontes, exist_ok=True)
        for f in faltam: shutil.copy(f, fontes)
        item("⟳", "extras", f"{len(faltam)} fonte(s) instalada(s)")
    else:
        item("!", "extras", f"{len(faltam)} fonte(s) faltando: rode o instalador de novo")


def hook_imagem():
    """Hook do Read que reduz imagem grande antes do Claude olhar (scripts/olhar.py; economia de tokens, 22/10/2026)."""
    arq = os.path.join(HOME, ".claude", "settings.json")
    olhar = os.path.join(RAIZ, "scripts", "olhar.py")
    # Mac: python3 do PATH (o caminho do Homebrew muda a cada versão); Windows: o Python que roda o doctor
    cmd = 'python3 "$HOME/.claude/skills/ogab/scripts/olhar.py" hook' if not WIN and RAIZ == os.path.join(HOME, ".claude", "skills", "ogab") \
        else f'"{sys.executable}" "{olhar}" hook'
    try:
        conf = json.load(open(arq, encoding="utf-8")) if os.path.exists(arq) else {}
    except Exception:
        item("!", "extras", f"economia de tokens: {arq} não é um JSON válido; corrija o arquivo e rode o doctor de novo")
        return
    pre = conf.setdefault("hooks", {}).setdefault("PreToolUse", [])
    if any("olhar.py" in h.get("command", "") for e in pre for h in e.get("hooks", [])):
        item("✓", "extras", "economia de tokens: imagens reduzidas antes do Claude ver (hook olhar.py)")
    elif not MAC and not WIN:
        item("·", "extras", "economia de tokens: hook olhar.py só no Mac e no Windows")
    elif CORRIGIR:
        pre.append({"matcher": "Read", "hooks": [{"type": "command", "command": cmd, "timeout": 20}]})
        os.makedirs(os.path.dirname(arq), exist_ok=True)
        tmp = arq + ".tmp"
        json.dump(conf, open(tmp, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        os.replace(tmp, arq)
        item("⟳", "extras", "economia de tokens: hook olhar.py registrado (vale ao abrir o Claude Code de novo)")
    else:
        item("!", "extras", "economia de tokens: hook olhar.py não registrado: rode o doctor com --corrigir")


# ---------------------------------------------------------------- apps

def _rel(app_escolhido):
    """Estado para algo que falta: '!' se o app é o escolhido, '·' se não é usado."""
    return "!" if app_escolhido else "·"


def davinci(usa):
    if MAC:
        app = "/Applications/DaVinci Resolve/DaVinci Resolve.app"; lib = app + "/Contents/Libraries/Fusion/fusionscript.so"
        tpl = os.path.join(HOME, "Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Templates")
    else:
        app = os.path.join(os.environ.get("ProgramFiles", ""), "Blackmagic Design", "DaVinci Resolve")
        lib = os.path.join(app, "fusionscript.dll")
        tpl = os.path.join(os.environ.get("APPDATA", ""), "Blackmagic Design", "DaVinci Resolve", "Support", "Fusion", "Templates")
    if not os.path.exists(app):
        item(_rel(usa), "DaVinci", "DaVinci Resolve Studio não instalado (21.1+): blackmagicdesign.com/products/davinciresolve")
        return
    item("✓" if os.path.exists(lib) else _rel(usa), "DaVinci",
         "scripting do Resolve" if os.path.exists(lib) else "sem scripting: precisa do DaVinci Resolve STUDIO")
    ver, vtxt = _versao_app(app if MAC else os.path.join(app, "Resolve.exe"))
    if ver >= (21, 1):
        item("✓", "DaVinci", f"DaVinci {vtxt} (transcreve pela API)")
    else:
        mod, pac = ("mlx_whisper", "mlx-whisper") if (MAC and platform.machine() == "arm64") else ("faster_whisper", "faster-whisper")
        try:
            __import__(mod); item("✓", "DaVinci", f"DaVinci {vtxt}: transcrição pelo Whisper local ({pac})")
        except Exception:
            ok = CORRIGIR and usa and pip_instalar(pac)
            item("⟳" if ok else _rel(usa), "DaVinci", f"DaVinci {vtxt} é anterior à 21.1: " + (f"{pac} instalado para a transcrição" if ok else f"falta o Whisper local ({pac}) ou atualizar para a 21.1+"))
    pac = glob.glob(os.path.join(RAIZ, "assets", "lettering", "*.drfx"))
    if pac and not all(os.path.exists(os.path.join(tpl, os.path.basename(p))) for p in pac):
        if CORRIGIR:
            os.makedirs(tpl, exist_ok=True)
            for p in pac: shutil.copy(p, tpl)
            item("⟳", "DaVinci", "pacote de lettering instalado (reinicie o DaVinci)")
        else:
            item(_rel(usa), "DaVinci", "pacote de lettering não instalado")
    elif pac:
        item("✓", "DaVinci", "pacote de lettering")
    # LUT DO GAB na pasta de LUTs do DaVinci (a cor padrão dos takes) + config de quem ficou sem cor nenhuma
    lutd = (Path("/Library/Application Support/Blackmagic Design/DaVinci Resolve/LUT/LUT DO GAB") if MAC else
            Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData")) / "Blackmagic Design" / "DaVinci Resolve" / "Support" / "LUT" / "LUT DO GAB")
    luts = os.path.join(RAIZ, "premiere", "assets", "lut", "LUT DO GAB.cube")
    if os.path.exists(luts):
        if (lutd / "LUT DO GAB.cube").exists():
            item("✓", "DaVinci", "LUT DO GAB na pasta de LUTs")
        else:
            ok = False
            if CORRIGIR:
                try:
                    lutd.mkdir(parents=True, exist_ok=True); shutil.copy(luts, lutd); ok = True
                except Exception:
                    ok = False
            item("⟳" if ok else _rel(usa), "DaVinci", "LUT DO GAB copiada para a pasta de LUTs" if ok else
                 f"LUT DO GAB fora da pasta de LUTs do DaVinci: rode o instalador de novo (ou copie {luts} para {lutd} como administrador)")
    c = cfg(); cor = c.get("cor") or {}
    sem_cor = (not cor.get("lut")) and (not cor.get("drx") or "<" in str(cor.get("drx")) or not os.path.exists(os.path.join(RAIZ, str(cor.get("drx")))))
    if usa and sem_cor:
        if CORRIGIR:
            cor.update(aplicar_power_grade=True, lut="LUT DO GAB/LUT DO GAB.cube")
            if "<" in str(cor.get("drx", "")):
                cor["drx"] = ""
            if "<" in str(cor.get("drx_iphone", "")):
                cor["drx_iphone"] = ""
            c["cor"] = cor
            json.dump(c, open(os.path.join(RAIZ, "config.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            item("⟳", "DaVinci", "cor dos takes ligada com a LUT DO GAB (não havia PowerGrade configurado)")
        else:
            item("!", "DaVinci", "cor dos takes desligada (sem PowerGrade e sem LUT no config): rode com --corrigir")
    aberto = roda(["pgrep", "-f", "DaVinci Resolve.app/Contents/MacOS/Resolve"] if MAC else ["tasklist", "/FI", "IMAGENAME eq Resolve.exe"]).stdout
    aberto = bool(aberto.strip()) and (MAC or "Resolve.exe" in aberto)
    if usa and aberto:
        sys.path.insert(0, os.path.join(RAIZ, "scripts"))
        try:
            import resolve_lib as R
            R.ambiente()
            import DaVinciResolveScript as dvr
            ok = bool(dvr.scriptapp("Resolve"))
        except Exception:
            ok = False
        item("✓" if ok else "!", "DaVinci", "o Gab conecta no DaVinci aberto" if ok else
             "o DaVinci está aberto mas não aceita o Gab: Preferences > System > General > External scripting using: Local, e reinicie o Resolve")


def _premiere_registro():
    """Pastas do Premiere 20xx pelo InstallLocation do desinstalador (Windows), em qualquer disco."""
    import winreg
    achou = set()
    for raiz, chave in ((winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
                        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
                        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")):
        try:
            k = winreg.OpenKey(raiz, chave)
        except OSError:
            continue
        for i in range(winreg.QueryInfoKey(k)[0]):
            try:
                sub = winreg.OpenKey(k, winreg.EnumKey(k, i))
                nome = winreg.QueryValueEx(sub, "DisplayName")[0]
                local = winreg.QueryValueEx(sub, "InstallLocation")[0]
            except OSError:
                continue
            if not str(nome).startswith("Adobe Premiere Pro 20") or not local:
                continue
            # o InstallLocation pode ser a pasta do app ou a pasta Adobe acima dela
            for p in [local] + glob.glob(os.path.join(local, "Adobe Premiere Pro 20*")):
                if os.path.exists(os.path.join(p, "Adobe Premiere Pro.exe")):
                    achou.add(p)
    return achou


def premiere(usa):
    if MAC:
        apps = glob.glob("/Applications/Adobe Premiere Pro 20*/Adobe Premiere Pro 20*.app")
        luts = os.path.join(HOME, "Library/Application Support/Adobe/Common/LUTs")
        uxp = glob.glob(os.path.join(HOME, "Library/Application Support/Adobe/UXP/Plugins/External/*ogab.ponte*")) + \
              glob.glob("/Library/Application Support/Adobe/UXP/Plugins/External/*ogab.ponte*")
    else:
        apps = glob.glob(os.path.join(os.environ.get("ProgramFiles", ""), "Adobe", "Adobe Premiere Pro 20*"))
        if not apps:  # instalado em outro disco pela Creative Cloud (ex.: D:\Adobe): o caminho está no registro
            apps = sorted(_premiere_registro())
        luts = os.path.join(os.environ.get("APPDATA", ""), "Adobe", "Common", "LUTs")
        uxp = glob.glob(os.path.join(os.environ.get("APPDATA", ""), "Adobe", "UXP", "Plugins", "External", "*ogab.ponte*")) + \
              glob.glob(os.path.join(os.environ.get("ProgramData", ""), "Adobe", "UXP", "Plugins", "External", "*ogab.ponte*"))
    if not apps:
        item(_rel(usa), "Premiere", "Premiere Pro 2026+ não instalado (Creative Cloud)")
        return
    versao = json.load(open(os.path.join(RAIZ, "premiere", "plugin", "manifest.json"))).get("version", "")
    uxp = [u for u in uxp if u.endswith("_" + versao)]          # versão antiga do plugin conta como faltando
    inst = os.path.join(RAIZ, "premiere", "instalar.sh" if MAC else "instalar.ps1")
    lut_ok = os.path.exists(os.path.join(luts, "Creative", "LUT DO GAB.cube"))
    if (not uxp or not lut_ok) and CORRIGIR:
        env = dict(os.environ, OGAB_SEM_CONFIG="1")
        roda(["bash", inst] if MAC else ["powershell", "-ExecutionPolicy", "Bypass", "-File", inst], env=env)
        item("⟳", "Premiere", "plugin Gab Ponte e LUT reinstalados (reinicie o Premiere)")
    else:
        item("✓" if uxp else _rel(usa), "Premiere", "plugin Gab Ponte" if uxp else "plugin Gab Ponte não instalado (rode com --corrigir)")
        item("✓" if lut_ok else _rel(usa), "Premiere", "LUT DO GAB" if lut_ok else "LUT DO GAB não instalado (rode com --corrigir)")
    ver, vtxt = _versao_app(apps[-1] if MAC else os.path.join(apps[-1], "Adobe Premiere Pro.exe"))
    item("✓" if ver >= (26,) else _rel(usa), "Premiere", f"Premiere {vtxt}" + ("" if ver >= (26,) else ": a ponte precisa do 26 (2026) ou mais novo"))
    mg = os.path.join(HOME, "Library/Application Support/Adobe/Common/Motion Graphics Templates") if MAC else \
         os.path.join(os.environ.get("APPDATA", ""), "Adobe", "Common", "Motion Graphics Templates")
    faltam = [f for f in glob.glob(os.path.join(RAIZ, "premiere", "assets", "mogrt", "*.mogrt")) if not os.path.exists(os.path.join(mg, os.path.basename(f)))]
    if faltam and CORRIGIR:
        os.makedirs(mg, exist_ok=True)
        for f in faltam: shutil.copy(f, mg)
        item("⟳", "Premiere", f"{len(faltam)} MOGRT(s) da biblioteca instalados")
    else:
        item("✓" if not faltam else _rel(usa), "Premiere", "MOGRTs da biblioteca" if not faltam else f"{len(faltam)} MOGRT(s) da biblioteca faltando (rode com --corrigir)")
    if usa:
        item("·", "Premiere", "no Premiere, uma vez: Window > UXP Plugins > Gab Ponte (painel encaixado)")


def aftereffects(usa):
    if MAC:
        apps = glob.glob("/Applications/Adobe After Effects 20*")
        ext = os.path.join(HOME, "Library/Application Support/Adobe/CEP/extensions/com.gabrielxreis.ogab.aeponte")
    else:
        apps = glob.glob(os.path.join(os.environ.get("ProgramFiles", ""), "Adobe", "Adobe After Effects 20*"))
        ext = os.path.join(os.environ.get("APPDATA", ""), "Adobe", "CEP", "extensions", "com.gabrielxreis.ogab.aeponte")
    if not apps:
        item(_rel(usa), "After Effects", "After Effects não instalado (Creative Cloud)")
        return
    app_ae = glob.glob(os.path.join(apps[-1], "Adobe After Effects 20*.app"))[0] if MAC else os.path.join(apps[-1], "Support Files", "AfterFX.exe")
    ver, vtxt = _versao_app(app_ae)
    item("✓" if ver >= (24,) else _rel(usa), "After Effects", f"After Effects {vtxt}" + ("" if ver >= (24,) else ": precisa do 2024 ou mais novo"))
    debug = roda(["defaults", "read", "com.adobe.CSXS.12", "PlayerDebugMode"]).stdout.strip() == "1" if MAC else \
            "0x1" in roda(["reg", "query", r"HKCU\Software\Adobe\CSXS.12", "/v", "PlayerDebugMode"]).stdout or \
            "1" in roda(["reg", "query", r"HKCU\Software\Adobe\CSXS.12", "/v", "PlayerDebugMode"]).stdout
    item("✓" if debug else _rel(usa), "After Effects", "extensões sem assinatura liberadas (CEP)" if debug else "extensões sem assinatura bloqueadas (rode com --corrigir com o AE fechado)")
    h = lambda p: hashlib.md5(open(p, "rb").read()).hexdigest() if os.path.exists(p) else None
    atual = h(os.path.join(ext, "main.js")) == h(os.path.join(RAIZ, "aftereffects", "cep", "main.js"))
    aberto = roda(["pgrep", "-f", "After Effects.app/Contents/MacOS/After Effects"] if MAC else ["tasklist", "/FI", "IMAGENAME eq AfterFX.exe"]).stdout
    aberto = bool(aberto.strip()) and ("AfterFX" in aberto or MAC)
    if not atual or not debug:
        if CORRIGIR and not aberto:
            inst = os.path.join(RAIZ, "aftereffects", "instalar.sh" if MAC else "instalar.ps1")
            roda(["bash", inst] if MAC else ["powershell", "-ExecutionPolicy", "Bypass", "-File", inst], env=dict(os.environ, OGAB_SEM_CONFIG="1"))
            item("⟳", "After Effects", "extensão Gab Ponte AE e liberação de extensões corrigidas")
        else:
            falta = [x for x, ok in (("extensão Gab Ponte AE desatualizada ou ausente", atual), ("liberação de extensões", debug)) if not ok]
            item(_rel(usa), "After Effects", "; ".join(falta) + (": feche o AE e rode com --corrigir" if aberto else ": rode com --corrigir"))
    else:
        item("✓", "After Effects", "extensão Gab Ponte AE")
    if aberto and usa:
        try:
            ok = urllib.request.urlopen("http://127.0.0.1:8766/ping", timeout=3).read() == b"ok"
        except Exception:
            ok = False
        if ok:   # o que importa: a ponte gravar arquivo (quadros, render, MOGRT); a preferência do menu não vale para ela
            try:
                teste = os.path.join(HOME, ".ogab_teste_ae.txt")
                req = urllib.request.Request("http://127.0.0.1:8766/jsx", method="POST",
                    data=('var f = new File(' + json.dumps(teste) + '); f.open("w"); f.write("ok"); f.close(); f.exists;').encode())
                grava = urllib.request.urlopen(req, timeout=15).read().decode().strip() == "true" and os.path.exists(teste)
                if os.path.exists(teste): os.remove(teste)
            except Exception:
                grava = False
            item("✓" if grava else "!", "After Effects", "a ponte grava arquivos (quadros, render, MOGRT)" if grava else
                 "a ponte não consegue gravar arquivos: AE > Ajustes > Scripts e expressões > permitir que scripts gravem arquivos")
        item("✓" if ok else "!", "After Effects", "o Gab conecta no AE aberto" if ok else
             "o AE está aberto mas a ponte não responde: veja se há um aviso aberto no AE; se não, feche e abra o AE")


def capcut(usa):
    """CapCut (Mac e Windows, beta): sem API; o Gab escreve o rascunho JSON (capcut/README.md)."""
    if WIN:
        sys.path.insert(0, os.path.join(RAIZ, "capcut"))
        try:
            import capcut_lib as C
        except Exception as e:
            item(_rel(usa), "CapCut", f"capcut_lib não carregou: {e}")
            return
        if not C.capcut_exe():
            item(_rel(usa), "CapCut", "CapCut não instalado (capcut.com, versão para Windows)")
            return
        if not os.path.isdir(C.RAIZ_CAPCUT):
            item(_rel(usa), "CapCut", "CapCut instalado, mas a pasta de rascunhos não existe: abra o CapCut uma vez e entre na "
                 "sua conta. Se mudou o local do rascunho nos Ajustes, grave GAB_CAPCUT_RAIZ com a pasta nova")
            return
        item("✓", "CapCut", "CapCut e pasta de rascunhos" + ("" if usa else " (não é o editor escolhido)"))
        return
    if not MAC:
        if usa:
            item("!", "CapCut", "o Gab no CapCut é só no Mac e no Windows: /ogab config editor davinci|premiere")
        return
    if not os.path.isdir("/Applications/CapCut.app"):
        item(_rel(usa), "CapCut", "CapCut não instalado (capcut.com ou App Store)")
        return
    _, v = _versao_app("/Applications/CapCut.app")
    rasc = os.path.join(HOME, "Movies/CapCut/User Data/Projects/com.lveditor.draft")
    if not os.path.isdir(rasc):
        item(_rel(usa), "CapCut", f"CapCut {v} instalado, mas ainda não foi aberto: abra uma vez e entre na sua conta")
        return
    item("✓", "CapCut", f"CapCut {v} e pasta de rascunhos" + ("" if usa else " (não é o editor escolhido)"))
    if usa and not os.path.exists(os.path.join(RAIZ, "capcut", "loja.json")):
        item("·", "CapCut", "loja.json ainda não lida: abra os painéis de Filtros/Texto no CapCut e o Gab roda atualizar_loja()")


def finalcut(usa):
    """Final Cut Pro (Mac, beta): projeto FCPXML (finalcut/fcpxml.py) e ajustes pela acessibilidade (finalcut/ax.py)."""
    if not MAC:
        if usa:
            item("!", "Final Cut", "Final Cut Pro é só no Mac: /ogab config editor davinci|premiere")
        return
    apps = glob.glob("/Applications/Final Cut Pro*.app")
    if not apps:
        item(_rel(usa), "Final Cut", "Final Cut Pro não instalado (App Store)")
        return
    _, v = _versao_app(apps[0])
    item("✓", "Final Cut", f"{os.path.basename(apps[0])[:-4]} {v}" + ("" if usa else " (não é o editor escolhido)"))
    if not usa:
        return
    item("✓" if shutil.which("xmllint") else "·", "Final Cut", "xmllint (confere o FCPXML no DTD do Final Cut)" if shutil.which("xmllint")
         else "xmllint faltando: o FCPXML sai sem a conferência no DTD (xcode-select --install)")
    bibl = glob.glob(os.path.join(HOME, "Movies", "*.fcpbundle"))
    item("✓" if bibl else "!", "Final Cut", f"{len(bibl)} biblioteca(s) em ~/Movies" if bibl else
         "nenhuma biblioteca: no Final Cut, Arquivo > Nova > Biblioteca (uma vez) e deixe aberta; sem ela o import pergunta onde salvar")


def windows():
    if not WIN:
        return
    faltam = [v for v in ("RESOLVE_SCRIPT_API", "RESOLVE_SCRIPT_LIB", "PYTHONUTF8") if not os.environ.get(v)]
    item("✓" if not faltam else "!", "Windows", "variáveis do Resolve e do Python" if not faltam else
         f"faltam variáveis {', '.join(faltam)}: rode windows\\install.ps1 e abra o Claude Code de novo")


def componentes_em_dia():
    """ffmpeg/yt-dlp/node na última versão e código sem opção que o ffmpeg tirou (scripts/componentes.py)."""
    sys.path.insert(0, os.path.join(RAIZ, "scripts"))
    import componentes as comp
    if CORRIGIR:
        for linha in comp.atualizar():
            item("!" if linha.startswith(("FALHOU", "ATENÇÃO")) else "⟳", "ferramentas", linha)
    p = comp.problemas()
    item("✓" if not p else "!", "ferramentas", "componentes em dia (programas, pacotes Python, " + comp.hf() + ")" if not p
         else "; ".join(p) + ": rode /ogab doctor para atualizar")


def main():
    skill(); python(); ferramentas(); ffmpeg_detalhes(); componentes_em_dia(); extras(); hook_imagem(); blender(); windows()
    c = cfg()
    davinci(c.get("editor", "davinci") == "davinci")
    premiere(c.get("editor") == "premiere")
    capcut(c.get("editor") == "capcut")
    finalcut(c.get("editor") == "finalcut")
    if c.get("editor") == "nenhum":
        item("✓", "Sem editor", "o Gab entrega o MP4 pronto (capcut.py previa); dica: CapCut grátis para customizar")
    aftereffects(c.get("motion") == "aftereffects")
    if "--json" in sys.argv:
        print(json.dumps([{"estado": e, "grupo": g, "texto": t} for e, g, t in itens], ensure_ascii=False, indent=1))
    else:
        grupo = None
        for e, g, t in itens:
            if g != grupo:
                print(f"\n{g}"); grupo = g
            print(f"  {e} {t}")
        pend = [t for e, _, t in itens if e == "!"]
        print("\n" + ("Tudo certo." if not pend else f"{len(pend)} pendência(s) acima marcadas com '!'."))
    sys.exit(1 if any(e == "!" for e, _, _ in itens) else 0)


if __name__ == "__main__":
    main()
