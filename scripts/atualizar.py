"""Atualiza o Gab pelo servidor do autor, por DIFERENÇA (baixa só o arquivo que mudou), no passo zero. Preserva o
que é do usuário: só mexe nos arquivos que fazem parte do release (config.json, clientes/, presets e biblioteca
locais nunca são tocados). Sem internet ou sem key, não faz nada e deixa seguir.

  python3 atualizar.py            # sincroniza esta instalação com a versão do servidor

Enquanto o GitHub ainda existir e o servidor não tiver release, cai no `git pull` como antes.
"""
import base64, hashlib, json, os, subprocess, sys, tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
import licenca  # noqa: E402

CACHE = os.path.join(os.path.expanduser("~"), ".claude", "ogab_release_local.json")


def _sha(full):
    try:
        return hashlib.sha256(open(full, "rb").read()).hexdigest()
    except Exception:
        return None


def _cache():
    try:
        return json.load(open(CACHE, encoding="utf-8")).get(SKILL, {})
    except Exception:
        return {}


def _salvar_cache(arquivos):
    try:
        todo = json.load(open(CACHE, encoding="utf-8"))
    except Exception:
        todo = {}
    todo[SKILL] = arquivos
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    json.dump(todo, open(CACHE, "w", encoding="utf-8"))


def _escrever(path, dados):
    full = os.path.join(SKILL, path)
    os.makedirs(os.path.dirname(full) or SKILL, exist_ok=True)
    tmp = full + ".parcial"
    with open(tmp, "wb") as f:
        f.write(dados)
    os.replace(tmp, full)


def _git_pull():
    if os.path.isdir(os.path.join(SKILL, ".git")):
        subprocess.run(["git", "-C", SKILL, "pull", "--ff-only", "--quiet"], capture_output=True)


def sync():
    d = licenca._ler()
    if not d.get("key"):
        _git_pull()   # ainda sem key (1ª vez): tenta o git enquanto existir
        return 0
    man = licenca._post("/v1/release", {"key": d["key"], "maquina": licenca.maquina()})
    if man is None:
        _git_pull()
        return 0
    arquivos = man.get("arquivos")
    if not isinstance(arquivos, dict) or not man.get("versao"):
        _git_pull()   # servidor sem release ainda
        return 0
    antigos = _cache()
    baixados = 0
    for path, sha in arquivos.items():
        if _sha(os.path.join(SKILL, path)) != sha:
            r = licenca._post("/v1/release/baixar", {"key": d["key"], "maquina": licenca.maquina(), "path": path})
            if r and r.get("b64") is not None:
                try:
                    _escrever(path, base64.b64decode(r["b64"]))
                    baixados += 1
                except Exception:
                    pass
    # apaga o que saiu do release (estava no último sync e não está mais), sem tocar no que é do usuário
    removidos = 0
    for path in antigos:
        if path not in arquivos:
            full = os.path.join(SKILL, path)
            if os.path.isfile(full):
                os.remove(full)
                removidos += 1
    _salvar_cache(arquivos)
    if baixados or removidos:
        print(f"ATUALIZADO: versão {man['versao']} ({baixados} baixado(s), {removidos} removido(s))")
    return 0


if __name__ == "__main__":
    sys.exit(sync())
