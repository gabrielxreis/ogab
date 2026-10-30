#!/usr/bin/env python3
"""Tudo que a /ogab usa sempre atualizado: programas (ffmpeg, yt-dlp, node, git), pacotes Python, skills de
terceiros (HyperFrames e as outras do `npx skills`) e a versão fixada do HyperFrames. Também vigia o código da skill
contra opções que o ffmpeg tirou.

  componentes.py checar      passo zero: mostra o resultado da última atualização e, se faz 1 semana, dispara
                             a próxima em SEGUNDO PLANO (não trava o pedido)
  componentes.py status      mostra tudo agora (usado pelo doctor)
  componentes.py atualizar   atualiza tudo agora (o doctor --corrigir usa)
  componentes.py varrer      procura na skill opções do ffmpeg que não existem mais (sai com erro se achar)
  componentes.py hf          imprime o pacote do HyperFrames fixado (ex.: hyperframes@0.8.200)
  componentes.py fixar-hf    (dono) testa a versão mais nova do HyperFrames e grava em versoes.json

HyperFrames: todo comando usa `npx --yes <componentes.py hf>`; nada de `npx hyperframes` solto (pega versão velha do
cache) nem número escrito no script. Opção nova saindo do ffmpeg: acrescentar em REMOVIDAS com a troca.
"""
import json, os, re, shutil, subprocess, sys, time

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAC, WIN = sys.platform == "darwin", os.name == "nt"
MARCA = os.path.join(SKILL, ".componentes_checado")
ULTIMO = os.path.join(SKILL, ".componentes_ultimo.txt")  # resultado da última atualização em segundo plano
VERSOES = os.path.join(SKILL, "versoes.json")
SEMANA = 7 * 24 * 3600
FFMPEG_MIN = 7  # -/filter_complex <arquivo> existe desde o 7.0

PACOTES = {"ffmpeg": ("ffmpeg", "Gyan.FFmpeg"), "yt-dlp": ("yt-dlp", "yt-dlp.yt-dlp"),
           "node": ("node", "OpenJS.NodeJS.LTS"), "git": ("git", "Git.Git")}
PIP = ["pillow", "numpy", "opencv-python", "requests", "python-dotenv", "fonttools", "psd-tools", "pymupdf"]
# teto de versão: o OpenCV 5.0 tirou o CascadeClassifier (detecção de rosto do Gab), então fica no 4.x
TETO = {"opencv-python": "opencv-python<5"}

REMOVIDAS = {  # opção (como aparece no código) -> troca
    "-vsync": "-fps_mode",
    "-filter_complex_script": "-/filter_complex <arquivo>",
    "-filter_script": "-/filter <arquivo>",
}
PADRAO = re.compile(r"""["'\s](%s)["'\s]""" % "|".join(re.escape(o) for o in REMOVIDAS))
EXTS = (".py", ".sh", ".ps1", ".js", ".mjs", ".command", ".bat")
PULAR = {".git", "node_modules", "clientes", "__pycache__"}


def roda(cmd, timeout=900):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, shell=WIN and cmd[0] == "npx")
    except Exception as e:
        return subprocess.CompletedProcess(cmd, 1, "", str(e))


def versoes():
    try:
        return json.load(open(VERSOES, encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def hf():
    """Pacote do HyperFrames que a skill usa: `npx --yes` + isto."""
    return "hyperframes@" + versoes().get("hyperframes", "latest")


def versao_ffmpeg():
    if not shutil.which("ffmpeg"):
        return None
    m = re.search(r"ffmpeg version n?(\d+)\.(\d+)", roda(["ffmpeg", "-version"], 30).stdout)
    return (int(m.group(1)), int(m.group(2))) if m else None


def velhos():
    """[(nome, instalada, nova)] dos programas com atualização (Homebrew; no Windows o winget só atualiza)."""
    if not (MAC and shutil.which("brew")):
        return []
    r = roda(["brew", "outdated", "--json=v2", *[b for b, _ in PACOTES.values()]], 120)
    try:
        d = json.loads(r.stdout or "{}")
    except ValueError:
        return []
    return [(f["name"], (f.get("installed_versions") or ["?"])[-1], f.get("current_version", "?")) for f in d.get("formulae", [])]


def pip_velhos():
    r = roda([sys.executable, "-m", "pip", "list", "--outdated", "--format=json"], 180)
    try:
        d = json.loads(r.stdout or "[]")
    except ValueError:
        return []
    return [(p["name"], p["version"], p["latest_version"]) for p in d if p["name"].lower() in PIP]


def hf_novo():
    """Versão mais nova do HyperFrames no npm, se for diferente da fixada (None se igual ou sem internet)."""
    if not shutil.which("npm"):
        return None
    nova = roda(["npm", "view", "hyperframes", "version"], 60).stdout.strip()
    return nova if re.match(r"^\d+\.\d+\.\d+$", nova) and nova != versoes().get("hyperframes") else None


def varrer():
    """[(arquivo, linha, opção)] com opção removida do ffmpeg no código da skill."""
    achados = []
    for raiz, pastas, arqs in os.walk(SKILL):
        pastas[:] = [p for p in pastas if p not in PULAR]
        for a in arqs:
            if not a.endswith(EXTS) or a == os.path.basename(__file__):
                continue
            cam = os.path.join(raiz, a)
            try:
                for n, linha in enumerate(open(cam, encoding="utf-8", errors="ignore"), 1):
                    for m in PADRAO.finditer(linha):
                        achados.append((os.path.relpath(cam, SKILL), n, m.group(1)))
            except OSError:
                pass
    return achados


def dono():
    try:
        return bool(json.load(open(os.path.join(SKILL, "config.json"), encoding="utf-8")).get("dono_biblioteca"))
    except (OSError, ValueError):
        return False


def problemas(rede=True):
    out = []
    v = versao_ffmpeg()
    if v and v[0] < FFMPEG_MIN:
        out.append(f"ffmpeg {v[0]}.{v[1]} antigo demais (precisa do {FFMPEG_MIN}+)")
    if rede:
        out += [f"{n} {i} -> {nova}" for n, i, nova in velhos()]
        out += [f"python {n} {i} -> {nova}" for n, i, nova in pip_velhos()]
        nova = hf_novo() if dono() else None
        if nova:
            out.append(f"HyperFrames {nova} saiu (fixado {versoes().get('hyperframes')}): componentes.py fixar-hf")
    out += [f"{a}:{n} usa {o} (saiu do ffmpeg; trocar por {REMOVIDAS[o]})" for a, n, o in varrer()]
    return out


def pip_instalar(nomes):
    base = [sys.executable, "-m", "pip", "install", "--user", "--quiet", "-U", *[TETO.get(n.lower(), n) for n in nomes]]
    if roda(base).returncode == 0:
        return True
    return roda(base + ["--break-system-packages"]).returncode == 0  # Python do Homebrew


def atualizar():
    """Atualiza tudo; devolve as linhas do que mudou ou falhou."""
    feito = []
    if MAC and shutil.which("brew"):
        nomes = [n for n, _, _ in velhos()]
        if nomes:
            ok = roda(["brew", "upgrade", *nomes]).returncode == 0
            feito.append(("atualizado: " if ok else "FALHOU brew upgrade: ") + ", ".join(nomes))
    elif WIN and shutil.which("winget"):
        for b, wg in PACOTES.values():  # winget sai com erro quando não há o que atualizar: não conta como falha
            r = roda(["winget", "upgrade", "--id", wg, "-e", "--silent", "--accept-package-agreements", "--accept-source-agreements"])
            if r.returncode == 0 and "No applicable" not in r.stdout:
                feito.append(f"atualizado: {b}")
    pv = [n for n, _, _ in pip_velhos()]
    if pv:
        feito.append(("atualizado: python " if pip_instalar(pv) else "FALHOU pip: ") + ", ".join(pv))
    if shutil.which("npx"):  # skills de terceiros (HyperFrames, design etc.) instaladas pelo `npx skills`
        r = roda(["npx", "--yes", "skills", "update", "-g", "-y"], 600)
        if r.returncode:
            r = roda(["npx", "--yes", "skills", "update", "-y"], 600)
        if r.returncode == 0:
            feito.append("skills de terceiros conferidas (npx skills update)")
        else:
            feito.append("FALHOU npx skills update: " + (r.stderr or r.stdout).strip()[-200:])
        r = roda(["npx", "--yes", hf(), "skills", "update"], 600)  # o render avisava "HyperFrames skills out of date"
        feito.append("skills do HyperFrames conferidas" if r.returncode == 0
                     else "FALHOU hyperframes skills update: " + (r.stderr or r.stdout).strip()[-200:])
    for a, n, o in varrer():
        feito.append(f"ATENÇÃO {a}:{n} usa {o} (saiu do ffmpeg; trocar por {REMOVIDAS[o]})")
    return feito


def fixar_hf():
    nova = hf_novo()
    if not nova:
        print("HyperFrames já está na versão mais nova:", hf())
        return 0
    r = roda(["npx", "--yes", f"hyperframes@{nova}", "--version"], 600)
    if r.returncode:
        print(f"hyperframes@{nova} não rodou: {(r.stderr or r.stdout)[-300:]}")
        return 1
    v = versoes(); v["hyperframes"] = nova
    json.dump(v, open(VERSOES, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"fixado hyperframes@{nova}: renderize um preset para conferir e faça o commit de versoes.json")
    return 0


def em_segundo_plano():
    """Dispara `atualizar --registrar` desligado do terminal (o pedido do usuário segue sem esperar)."""
    k = dict(stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL)
    if WIN:
        k["creationflags"] = 0x00000008 | 0x00000200  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
    else:
        k["start_new_session"] = True
    subprocess.Popen([sys.executable, os.path.abspath(__file__), "atualizar", "--registrar"], **k)


def main():
    sub = sys.argv[1] if len(sys.argv) > 1 else "status"
    if sub == "checar":
        if os.path.exists(ULTIMO):  # resultado da rodada anterior: mostra uma vez
            linhas = [l.strip() for l in open(ULTIMO, encoding="utf-8") if l.strip()]
            os.remove(ULTIMO)
            if linhas:
                print("COMPONENTES: " + "; ".join(linhas))
        for p in problemas(rede=False):  # o que não se resolve sozinho (ffmpeg velho demais, código com opção removida)
            print("COMPONENTES: " + p)
        try:  # preset whiteboard: quem recebeu no update instala o motor sozinho, em segundo plano
            sys.path.insert(0, os.path.join(SKILL, "presets", "whiteboard"))
            import whiteboard
            whiteboard.garantir()
        except Exception:
            pass
        try:
            if time.time() - os.path.getmtime(MARCA) < SEMANA:
                return
        except OSError:
            pass
        open(MARCA, "w").write(time.strftime("%Y-%m-%d %H:%M"))
        em_segundo_plano()
    elif sub == "status":
        v = versao_ffmpeg()
        print("ffmpeg", f"{v[0]}.{v[1]}" if v else "não encontrado", "|", hf())
        for linha in problemas() or ["tudo atualizado"]:
            print("-", linha)
    elif sub == "atualizar":
        feito = atualizar()
        if "--registrar" in sys.argv:
            nova = hf_novo() if dono() else None
            if nova:
                feito.append(f"HyperFrames {nova} saiu (fixado {versoes().get('hyperframes')}): rode componentes.py fixar-hf")
            open(ULTIMO, "w", encoding="utf-8").write("\n".join(feito))
        else:
            print("\n".join(feito) or "nada para atualizar")
        sys.exit(1 if any(l.startswith("FALHOU") for l in feito) else 0)
    elif sub == "varrer":
        a = varrer()
        for arq, n, o in a:
            print(f"{arq}:{n}: {o} -> {REMOVIDAS[o]}")
        sys.exit(1 if a else 0)
    elif sub == "hf":
        print(hf())
    elif sub == "fixar-hf":
        sys.exit(fixar_hf())
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
