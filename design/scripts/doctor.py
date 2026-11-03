"""Doctor da área de design do Gab (o antigo Rick, /orick): confere a instalação e CORRIGE sozinho o que dá (Mac e Windows).

  python3 doctor.py               # só confere
  python3 doctor.py --corrigir    # confere e corrige o que for possível sem o usuário
  python3 doctor.py --json        # saída para outro programa

Saída: uma linha por item.  ✓ ok  |  ⟳ corrigido agora  |  ! falta algo que só o usuário faz (com o passo)  |  · não usado
O que só o motor Photoshop precisa (catálogo, OCR, pacotes do Windows) aparece como "·" em quem usa Canva ou só IA.
Sai com código 1 se faltar algo obrigatório.
"""
import glob, json, os, platform, shutil, subprocess, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
MAC, WIN = sys.platform == "darwin", os.name == "nt"
CORRIGIR = "--corrigir" in sys.argv
PACOTES = {"psd_tools": "psd-tools", "fontTools": "fonttools", "numpy": "numpy", "PIL": "pillow"}
PACOTES_WIN = ["winrt-Windows.Media.Ocr", "winrt-Windows.Graphics.Imaging", "winrt-Windows.Storage",
               "winrt-Windows.Storage.Streams", "winrt-Windows.Foundation", "winrt-Windows.Foundation.Collections",
               "winrt-Windows.Globalization"]
itens = []   # (estado, grupo, texto)


def item(estado, grupo, texto):
    itens.append((estado, grupo, texto))


def roda(cmd, timeout=900, **k):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, errors="replace", timeout=timeout, **k)
        r.stdout, r.stderr = r.stdout or "", r.stderr or ""
        return r
    except Exception as e:
        return subprocess.CompletedProcess(cmd, 1, "", str(e))


def config():
    try:
        return json.load(open(os.path.join(RAIZ, "config.json"), encoding="utf-8"))
    except Exception:
        return {}


def py_venv():
    return os.path.join(RAIZ, ".venv", "Scripts" if WIN else "bin", "python.exe" if WIN else "python")


def skill():
    g = "skill"
    if sys.version_info < (3, 10):
        item("!", g, f"Python {platform.python_version()}: precisa de 3.10 ou mais novo (python.org)")
    else:
        item("✓", g, f"Python {platform.python_version()}")
    for velho in ("~/.claude/skills/oyoshi", "~/.claude/skills/orick"):
        if os.path.isdir(os.path.join(os.path.expanduser(velho), "scripts")):
            item("!", g, f"sobrou a pasta antiga {velho}: o Gab agora é o design do /ogab ({RAIZ}); apagar depois de conferir")
    item("✓", g, f"design dentro do /ogab ({RAIZ}), atualiza junto com o Gab")


def python_venv(motor):
    g = "python"
    py = py_venv()
    if not os.path.exists(py):
        if CORRIGIR and roda([sys.executable, "-m", "venv", os.path.join(RAIZ, ".venv")]).returncode == 0 and os.path.exists(py):
            item("⟳", g, ".venv criado")
        else:
            item("!", g, f"falta o .venv: {sys.executable} -m venv {os.path.join(RAIZ, '.venv')}")
            return
    falta = [pip for mod, pip in PACOTES.items()
             if roda([py, "-c", f"import {mod}"], timeout=120).returncode != 0]
    if WIN and motor == "photoshop":
        if roda([py, "-c", "import winrt.windows.media.ocr"], timeout=120).returncode != 0:
            falta += PACOTES_WIN
    if falta and CORRIGIR:
        r = roda([py, "-m", "pip", "install", "-q", *falta], timeout=1800)
        if r.returncode == 0:
            item("⟳", g, "pacotes instalados no .venv: " + ", ".join(falta)); falta = []
    if falta:
        item("!", g, f"faltam pacotes no .venv: {py} -m pip install " + " ".join(falta))
    else:
        item("✓", g, "pacotes do .venv (psd-tools, fonttools, numpy, pillow" + (", OCR do Windows" if WIN and motor == "photoshop" else "") + ")")
    if WIN:   # os scripts chamam .venv/bin/python
        alvo = os.path.join(RAIZ, ".venv", "bin", "python.exe")
        if not os.path.exists(alvo):
            if CORRIGIR:
                os.makedirs(os.path.dirname(alvo), exist_ok=True); shutil.copy2(py, alvo)
                item("⟳", g, ".venv/bin/python.exe criado (os scripts chamam esse caminho)")
            else:
                item("!", g, "falta .venv/bin/python.exe (copiar de .venv/Scripts/python.exe)")


def motor_e_apps():
    g = "motor"
    cfg = config()
    motor = cfg.get("motor")
    try:
        import detectar_apps
        apps = detectar_apps.detectar()
    except Exception as e:
        item("!", g, f"detectar_apps.py falhou: {e}")
        return motor
    if not motor:
        item("·", g, f"motor ainda não escolhido (sugestão: {apps['recomendado']}): na próxima peça de design o Gab pergunta")
    else:
        item("✓", g, f"motor escolhido: {motor}")
    ps = apps["photoshop"]
    if motor == "photoshop":
        if not ps["instalado"]:
            item("!", g, "motor Photoshop sem o Photoshop instalado: instalar o Photoshop 2026 ou trocar o motor (/ogab design motor)")
        else:
            item("✓", g, "Photoshop " + ", ".join(ps["versoes"]) + ("" if ps["agente_nativo"] else " (o 2026 tem as ferramentas nativas do agente)"))
            if os.path.exists(os.path.join(RAIZ, "docs", "catalogo", "local", "agente_ferramentas.json")):
                item("✓", g, "catálogo do Photoshop desta máquina")
            else:
                item("!", g, f"falta o catálogo: com o Photoshop aberto, python3 {os.path.join(AQUI, 'sondar', 'catalogar.py')}")
            if MAC:
                ocr, fonte = os.path.join(AQUI, "swift", "ocr"), os.path.join(AQUI, "swift", "ocr.swift")
                if os.path.exists(ocr):
                    item("✓", g, "OCR do Mac compilado (imagem -> PSD)")
                elif CORRIGIR and shutil.which("swiftc") and roda(["swiftc", "-O", fonte, "-o", ocr], timeout=600).returncode == 0:
                    item("⟳", g, "OCR do Mac compilado agora (scripts/swift/ocr)")
                else:
                    item("!", g, f"OCR do Mac não compilado: swiftc -O {fonte} -o {ocr} (precisa das Command Line Tools: xcode-select --install)")
    else:
        item("·", g, "Photoshop: " + ("instalado (não é o motor escolhido)" if ps["instalado"] else "não instalado (não precisa no motor " + str(motor or "?") + ")"))
    cv = apps["canva"]
    if motor == "canva" and not (cv["conector"] or cv["app"]):
        item("!", g, "motor Canva sem conector nem app: ligar o conector oficial do Canva no Claude e autorizar em /mcp")
    elif cv["conector"] or cv["app"]:
        item("✓" if motor == "canva" else "·", g, "Canva " + ("conectado no Claude" if cv["conector"] else "instalado"))
    ia = apps["ia"]
    item("✓" if motor == "ia" else "·", g, "IA de imagem: ChatGPT/Gemini no navegador" +
         (", IAs conectadas: " + ", ".join(ia["conectadas"]) if ia["conectadas"] else ""))
    return motor


def irmaos():
    g = "gab"
    ok = os.path.exists(os.path.join(os.path.dirname(RAIZ), "SKILL.md"))
    item("✓" if ok else "!", g, "/ogab " + ("instalado (motion, tráfego, relatos e ferramentas de marca/capa)"
                                         if ok else "não encontrado: o design vive dentro do /ogab, reinstalar o Gab"))


def main():
    skill()
    motor = motor_e_apps()
    python_venv(motor)
    irmaos()
    if "--json" in sys.argv:
        print(json.dumps([{"estado": e, "grupo": g, "texto": t} for e, g, t in itens], ensure_ascii=False, indent=1))
    else:
        grupo = None
        for e, g, t in itens:
            if g != grupo:
                print(f"\n[{g}]"); grupo = g
            print(f"  {e} {t}")
        faltas = sum(1 for e, _, _ in itens if e == "!")
        print(f"\n{'tudo certo' if not faltas else f'{faltas} item(ns) para resolver'}"
              + ("" if CORRIGIR or not faltas else " (python3 doctor.py --corrigir conserta o que dá)"))
    sys.exit(1 if any(e == "!" for e, _, _ in itens) else 0)


if __name__ == "__main__":
    main()
