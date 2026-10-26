#!/usr/bin/env python3
"""Componentes da /ogab sempre atualizados (ffmpeg, yt-dlp, node) e código livre de opções que o ffmpeg tirou.

  componentes.py checar      passo zero: no máximo 1x por semana, imprime 1 linha se algo estiver velho ou quebrado
  componentes.py status      mostra tudo agora (usado pelo doctor)
  componentes.py atualizar   atualiza o que estiver velho (brew upgrade / winget upgrade)
  componentes.py varrer      procura na skill opções do ffmpeg que não existem mais (sai com erro se achar)

Opção nova saindo do ffmpeg: acrescentar em REMOVIDAS com a troca. Ex.: o FFmpeg 9 tirou -vsync e -filter_complex_script.
"""
import json, os, re, shutil, subprocess, sys, time

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAC, WIN = sys.platform == "darwin", os.name == "nt"
MARCA = os.path.join(SKILL, ".componentes_checado")
SEMANA = 7 * 24 * 3600
FFMPEG_MIN = 7  # -/filter_complex <arquivo> existe desde o 7.0

PACOTES = {"ffmpeg": ("ffmpeg", "Gyan.FFmpeg"), "yt-dlp": ("yt-dlp", "yt-dlp.yt-dlp"), "node": ("node", "OpenJS.NodeJS.LTS")}

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
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except Exception as e:
        return subprocess.CompletedProcess(cmd, 1, "", str(e))


def versao_ffmpeg():
    if not shutil.which("ffmpeg"):
        return None
    m = re.search(r"ffmpeg version n?(\d+)\.(\d+)", roda(["ffmpeg", "-version"], 30).stdout)
    return (int(m.group(1)), int(m.group(2))) if m else None


def velhos():
    """[(nome, instalada, nova)] dos pacotes da skill com atualização (só Mac/Homebrew dá para listar rápido)."""
    if not (MAC and shutil.which("brew")):
        return []
    r = roda(["brew", "outdated", "--json=v2", *[b for b, _ in PACOTES.values()]], 120)
    try:
        d = json.loads(r.stdout or "{}")
    except ValueError:
        return []
    return [(f["name"], (f.get("installed_versions") or ["?"])[-1], f.get("current_version", "?")) for f in d.get("formulae", [])]


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


def problemas():
    out = []
    v = versao_ffmpeg()
    if v and v[0] < FFMPEG_MIN:
        out.append(f"ffmpeg {v[0]}.{v[1]} antigo demais (precisa do {FFMPEG_MIN}+)")
    out += [f"{n} {i} -> {nova}" for n, i, nova in velhos()]
    out += [f"{a}:{n} usa {o} (saiu do ffmpeg; trocar por {REMOVIDAS[o]})" for a, n, o in varrer()]
    return out


def atualizar():
    ok = True
    if MAC and shutil.which("brew"):
        nomes = [n for n, _, _ in velhos()]
        if nomes:
            ok = roda(["brew", "upgrade", *nomes]).returncode == 0
    elif WIN and shutil.which("winget"):
        for b, wg in PACOTES.values():  # winget sai com erro quando não há o que atualizar: não conta como falha
            roda(["winget", "upgrade", "--id", wg, "-e", "--silent", "--accept-package-agreements", "--accept-source-agreements"])
    return ok


def main():
    sub = sys.argv[1] if len(sys.argv) > 1 else "status"
    if sub == "checar":
        try:
            if time.time() - os.path.getmtime(MARCA) < SEMANA:
                return
        except OSError:
            pass
        p = problemas()
        open(MARCA, "w").write(time.strftime("%Y-%m-%d %H:%M"))
        if p:
            print("COMPONENTES: " + "; ".join(p) + ". Rode /ogab doctor para atualizar.")
    elif sub == "status":
        v = versao_ffmpeg()
        print("ffmpeg", f"{v[0]}.{v[1]}" if v else "não encontrado")
        for linha in problemas() or ["tudo atualizado"]:
            print("-", linha)
    elif sub == "atualizar":
        sys.exit(0 if atualizar() else 1)
    elif sub == "varrer":
        a = varrer()
        for arq, n, o in a:
            print(f"{arq}:{n}: {o} -> {REMOVIDAS[o]}")
        sys.exit(1 if a else 0)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
