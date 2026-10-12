"""Doctor do Gab: confere a instalação inteira e CORRIGE sozinho o que dá (Mac e Windows).

  python3 doctor.py               # só confere
  python3 doctor.py --corrigir    # confere e corrige o que for possível sem o usuário
  python3 doctor.py --json        # saída para outro programa (instalador, Gab)

Saída: uma linha por item.  ✓ ok  |  ⟳ corrigido agora  |  ! falta algo que só o usuário faz (com o passo)  |  · não usado
Os apps que o usuário NÃO escolheu (config.json editor/motion) aparecem como "·" quando faltam: tudo é instalado,
mas só o app escolhido é obrigatório. Sai com código 1 se faltar algo obrigatório.
"""
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
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, **k)
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
    v = sys.version_info
    item("✓" if v >= (3, 10) else "!", "ferramentas", f"Python {v.major}.{v.minor}" + ("" if v >= (3, 10) else ": instale o 3.10 ou mais novo"))
    try:
        import PIL  # noqa
        item("✓", "ferramentas", "Pillow")
    except ImportError:
        ok = CORRIGIR and roda([sys.executable, "-m", "pip", "install", "--user", "--quiet", "pillow"]).returncode == 0
        item("⟳" if ok else "!", "ferramentas", "Pillow instalado" if ok else "Pillow: python3 -m pip install --user pillow")
    docker()


def docker():
    app = "/Applications/Docker.app" if MAC else os.path.join(os.environ.get("ProgramFiles", ""), "Docker", "Docker", "Docker Desktop.exe")
    instalado = shutil.which("docker") or os.path.exists(app)
    if not instalado:
        # no Mac a instalação pede a senha: só tenta com alguém no terminal (instalador), senão orienta
        if CORRIGIR and (instalar_pacote("", "Docker.DockerDesktop") if WIN else
                         (sys.stdin.isatty() and roda(["brew", "install", "--cask", "docker-desktop"]).returncode == 0)):
            item("⟳", "ferramentas", "Docker Desktop instalado (abra uma vez e aceite os termos)")
        else:
            item("!", "ferramentas", "Docker Desktop não instalado: no Terminal rode  brew install --cask docker-desktop  (pede a senha do Mac)"
                 if MAC else "Docker Desktop não instalado: winget install --id Docker.DockerDesktop -e")
        return
    if roda(["docker", "info"], timeout=20).returncode == 0:
        item("✓", "ferramentas", "Docker rodando")
    elif CORRIGIR:
        roda(["open", "-a", "Docker"] if MAC else ["cmd", "/c", "start", "", app], timeout=20)
        item("⟳", "ferramentas", "Docker Desktop aberto (se for a 1ª vez, aceite os termos na janela dele)")
    else:
        item("!", "ferramentas", "Docker instalado mas parado: abra o Docker Desktop")


def extras():
    if os.path.isdir(os.path.join(HOME, ".claude", "skills", "hyperframes")):
        item("✓", "extras", "skills do HyperFrames")
    elif CORRIGIR and roda(["npx", "--yes", "skills", "add", "heygen-com/hyperframes", "-g", "-a", "claude-code", "-s", "*", "-y"],
                           shell=WIN).returncode == 0:
        item("⟳", "extras", "skills do HyperFrames instaladas")
    else:
        item("!", "extras", "skills do HyperFrames: npx skills add heygen-com/hyperframes -g -a claude-code -s '*' -y")
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


def premiere(usa):
    if MAC:
        apps = glob.glob("/Applications/Adobe Premiere Pro 20*/Adobe Premiere Pro 20*.app")
        luts = os.path.join(HOME, "Library/Application Support/Adobe/Common/LUTs")
        uxp = glob.glob(os.path.join(HOME, "Library/Application Support/Adobe/UXP/Plugins/External/*ogab.ponte*")) + \
              glob.glob("/Library/Application Support/Adobe/UXP/Plugins/External/*ogab.ponte*")
    else:
        apps = glob.glob(os.path.join(os.environ.get("ProgramFiles", ""), "Adobe", "Adobe Premiere Pro 20*"))
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
    h = lambda p: hashlib.md5(open(p, "rb").read()).hexdigest() if os.path.exists(p) else None
    atual = h(os.path.join(ext, "main.js")) == h(os.path.join(RAIZ, "aftereffects", "cep", "main.js"))
    aberto = roda(["pgrep", "-f", "After Effects.app/Contents/MacOS/After Effects"] if MAC else ["tasklist", "/FI", "IMAGENAME eq AfterFX.exe"]).stdout
    aberto = bool(aberto.strip()) and ("AfterFX" in aberto or MAC)
    if not atual:
        if CORRIGIR and not aberto:
            inst = os.path.join(RAIZ, "aftereffects", "instalar.sh" if MAC else "instalar.ps1")
            roda(["bash", inst] if MAC else ["powershell", "-ExecutionPolicy", "Bypass", "-File", inst], env=dict(os.environ, OGAB_SEM_CONFIG="1"))
            item("⟳", "After Effects", "extensão Gab Ponte AE instalada/atualizada")
        else:
            item(_rel(usa), "After Effects", "extensão Gab Ponte AE desatualizada ou ausente" + (": feche o AE e rode com --corrigir" if aberto else ": rode com --corrigir"))
    else:
        item("✓", "After Effects", "extensão Gab Ponte AE")
    if aberto and usa:
        try:
            ok = urllib.request.urlopen("http://127.0.0.1:8766/ping", timeout=3).read() == b"ok"
        except Exception:
            ok = False
        item("✓" if ok else "!", "After Effects", "o Gab conecta no AE aberto" if ok else
             "o AE está aberto mas a ponte não responde: veja se há um aviso aberto no AE; se não, feche e abra o AE")


def windows():
    if not WIN:
        return
    faltam = [v for v in ("RESOLVE_SCRIPT_API", "RESOLVE_SCRIPT_LIB", "PYTHONUTF8") if not os.environ.get(v)]
    item("✓" if not faltam else "!", "Windows", "variáveis do Resolve e do Python" if not faltam else
         f"faltam variáveis {', '.join(faltam)}: rode windows\\install.ps1 e abra o Claude Code de novo")


def main():
    skill(); ferramentas(); extras(); windows()
    c = cfg()
    davinci(c.get("editor", "davinci") == "davinci")
    premiere(c.get("editor") == "premiere")
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
