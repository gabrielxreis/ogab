"""Detecta onde o Gab pode trabalhar nesta máquina e guarda o motor que o usuário escolheu (config.json, fora do git).

  python3 detectar_apps.py detectar          # o que tem instalado + recomendação (JSON); grava em config.json "apps"
  python3 detectar_apps.py escolher <motor>  # ia | photoshop | canva  (grava "motor" no config.json)
  python3 detectar_apps.py status            # motor escolhido e apps detectados
  python3 detectar_apps.py instalar_canva    # instala o app do Canva (só depois do ok do usuário)

Motores (o padrão é ia):
  ia         peça inteira gerada por IA de imagem (ChatGPT, Gemini/Nano Banana ou IA conectada), sem editor
  photoshop  PSD em camadas editáveis montado pelo Gab (Adobe Photoshop 2026; Mac por AppleScript, Windows por COM)
  canva      design montado DENTRO do Canva, camada por camada, pelo conector oficial (docs/canva.md); o app do Canva
             é obrigatório nesse motor (o usuário vê e mexe nele): faltando, perguntar e instalar com instalar_canva

Padrão: ia (recomendado sempre). Photoshop e Canva são opção quando o usuário escolhe ou pede; nada aqui é obrigatório.
"""
import glob, json, os, platform, re, sys, time

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(SKILL, "config.json")
MOTORES = ("ia", "photoshop", "canva")
IAS_CONECTADAS = ("higgsfield", "magnific", "artlist", "freepik", "krea", "wonda", "leonardo", "midjourney", "ideogram",
                  "flux", "replicate", "fal", "openai", "gemini", "runway", "recraft")
WIN = platform.system() == "Windows"


def _config():
    try:
        return json.load(open(CONFIG, encoding="utf-8"))
    except Exception:
        return {}


def _salvar(c):
    json.dump(c, open(CONFIG, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def _apps_mac(padroes):
    achados = []
    for base in ("/Applications", os.path.expanduser("~/Applications")):
        for p in padroes:
            achados += glob.glob(os.path.join(base, p))
    return sorted(set(achados))


def _apps_win(padroes):
    bases = [os.environ.get(v, "") for v in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA")]
    achados = []
    for b in filter(None, bases):
        for p in padroes:
            achados += glob.glob(os.path.join(b, p))
    return sorted(set(achados))


def photoshop():
    if WIN:
        achados = _apps_win([r"Adobe\Adobe Photoshop*\Photoshop.exe"])
    else:
        achados = _apps_mac(["Adobe Photoshop*/Adobe Photoshop*.app", "Adobe Photoshop*.app"])
    versoes = []
    for a in achados:
        m = re.search(r"Photoshop (\d{4}|CC \d{4}|\d+)", a)
        versoes.append(m.group(1) if m else "?")
    return {"instalado": bool(achados), "versoes": sorted(set(versoes)), "caminhos": achados,
            "agente_nativo": any(v.isdigit() and int(v) >= 2026 for v in versoes)}


def _textos_config_claude():
    """Configurações do Claude Code onde aparecem conectores (MCP) e plugins. Só leitura, só para sugerir."""
    arqs = [os.path.expanduser("~/.claude.json"), os.path.expanduser("~/.claude/settings.json"),
            os.path.expanduser("~/.claude/settings.local.json")]
    arqs += glob.glob(os.path.expanduser("~/.claude/plugins/*.json"))
    arqs += [a for a in glob.glob(os.path.expanduser("~/.claude/plugins/**/.mcp.json"), recursive=True)
             if "/.trash/" not in a.replace("\\", "/")]   # conectores que vêm dentro de plugins (ex.: Canva no "marketing")
    out = ""
    for a in arqs:
        try:
            d = json.load(open(a, encoding="utf-8"))
        except Exception:
            continue
        for chave in ("mcpServers", "enabledPlugins"):   # só nomes, nunca tokens
            v = d.get(chave)
            if isinstance(v, dict):
                out += " " + " ".join(v.keys())
        for proj in (d.get("projects") or {}).values():
            if isinstance(proj, dict) and isinstance(proj.get("mcpServers"), dict):
                out += " " + " ".join(proj["mcpServers"].keys())
    return out.lower()


def canva(conf):
    app = _apps_win([r"Programs\Canva\Canva.exe", r"Canva\Canva.exe"]) if WIN else _apps_mac(["Canva.app"])
    return {"app": bool(app), "conector": "canva" in conf, "navegador": True}


def ia(conf):
    app = (_apps_win([r"Programs\ChatGPT\ChatGPT.exe", r"WindowsApps\*ChatGPT*"]) if WIN
           else _apps_mac(["ChatGPT*.app"]))
    return {"chatgpt_app": bool(app), "navegador": ["chatgpt.com", "gemini.google.com"],
            "conectadas": sorted({n for n in IAS_CONECTADAS if n in conf})}


def detectar():
    conf = _textos_config_claude()
    r = {"sistema": platform.system(), "photoshop": photoshop(), "canva": canva(conf), "ia": ia(conf)}
    # Padrão do design do Gab é IA de imagem (regra do dono, 31/10/2026): funciona em qualquer máquina. Photoshop e Canva
    # aparecem como opção quando instalados; a detecção só conta o que tem, não muda o recomendado.
    rec, porque = "ia", "padrão do design do Gab: IA de imagem (ChatGPT, Gemini) funciona em qualquer máquina"
    extras = [n for n, ok in (("Photoshop", r["photoshop"]["instalado"]),
                              ("Canva", r["canva"]["app"] or r["canva"]["conector"])) if ok]
    if extras:
        porque += "; " + " e ".join(extras) + " também disponíve" + ("is" if len(extras) > 1 else "l") + " se você pedir"
    r["recomendado"], r["porque"] = rec, porque
    c = _config(); c["apps"] = dict(r, quando=time.strftime("%Y-%m-%d")); _salvar(c)
    return r


def instalar_canva():
    """App oficial: Mac pelo Homebrew (cask 'canva') ou página oficial; Windows pelo winget. Só com o ok do usuário."""
    import shutil, subprocess
    if canva("")["app"]:
        return "app do Canva já instalado"
    if WIN and shutil.which("winget"):
        r = subprocess.run(["winget", "install", "--id", "Canva.Canva", "-e", "--accept-source-agreements",
                            "--accept-package-agreements"], capture_output=True, text=True)
        return "instalado pelo winget" if r.returncode == 0 else f"winget falhou: {r.stdout[-300:]}"
    if not WIN and shutil.which("brew"):
        r = subprocess.run(["brew", "install", "--cask", "canva"], capture_output=True, text=True)
        return "instalado pelo Homebrew" if r.returncode == 0 else f"brew falhou: {r.stderr[-300:]}"
    url = "https://www.canva.com/download/windows/" if WIN else "https://www.canva.com/download/mac/"
    subprocess.run(["cmd", "/c", "start", url] if WIN else ["open", url])
    return f"abri a página oficial de download ({url}): o usuário instala e avisa"


# Photoshop e Canva desligados pelo dono em 02/11/2026: só IA de imagem até ele religar
DESLIGADOS = {"photoshop", "canva"}


def escolher(motor):
    motor = motor.lower().strip()
    if motor in DESLIGADOS:
        raise SystemExit(f"motor {motor} está desligado por enquanto: o Gab gera só por IA de imagem (use ia)")
    if motor not in MOTORES:
        raise SystemExit(f"motor inválido: {motor} (use {' | '.join(MOTORES)})")
    c = _config(); c["motor"] = motor; c["motor_respondido"] = time.strftime("%Y-%m-%d"); _salvar(c)
    aviso = ""
    if motor == "photoshop" and not ((c.get("apps") or {}).get("photoshop") or {}).get("instalado"):
        aviso = " (Photoshop não foi encontrado: o Gab prepara tudo, mas para montar o PSD precisa instalar)"
    return motor + aviso


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["detectar"]:
        print(json.dumps(detectar(), ensure_ascii=False, indent=1))
    elif a[:1] == ["escolher"] and len(a) > 1:
        print("motor:", escolher(a[1]))
    elif a[:1] == ["instalar_canva"]:
        print(instalar_canva())
    elif a[:1] == ["status"]:
        c = _config()
        print(json.dumps({"motor": ("ia" if c.get("motor") in DESLIGADOS else c.get("motor")) or "ainda não escolhido", "apps": c.get("apps") or "não detectado"},
                         ensure_ascii=False, indent=1))
    else:
        raise SystemExit(__doc__)
