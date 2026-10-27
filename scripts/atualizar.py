"""Atualiza o Gab pelo servidor do autor, por DIFERENÇA (baixa só o arquivo que mudou), no passo zero. Preserva o
que é do usuário: só mexe nos arquivos que fazem parte do release (config.json, clientes/, presets e biblioteca
locais nunca são tocados). Sem internet ou sem key, não faz nada e deixa seguir.

  python3 atualizar.py            # sincroniza esta instalação com a versão do servidor (e garante o hook abaixo)
  python3 atualizar.py hook       # hook UserPromptSubmit: a cada pedido numa conversa que já abriu o Gab

A cada pedido no meio de um projeto (regra do Gabriel, 27/10/2026: "se o usuário já estiver usando o ogab e mandar
algum comando, tem que atualizar também"): o hook só age em conversa onde o cofre já foi aberto (CONTEUDO_PRONTO na
transcrição), no máximo 1 vez por minuto, e nunca trava o pedido (sem internet ou erro = segue calado). Se baixou algo,
avisa o Claude para reabrir o cofre e reler o SKILL.md antes de responder.

Enquanto o GitHub ainda existir e o servidor não tiver release, cai no `git pull` como antes.
"""
import base64, hashlib, json, os, subprocess, sys, tempfile, time

AQUI = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
import licenca  # noqa: E402

CACHE = os.path.join(os.path.expanduser("~"), ".claude", "ogab_release_local.json")
ESTADO_HOOK = os.path.join(os.path.expanduser("~"), ".claude", "ogab_hook_atualizar.json")
INTERVALO = 60   # s entre duas checagens pelo hook


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


def _editados_local():
    """Arquivos mudados e ainda não commitados no clone do dono: o update não pode sobrescrever trabalho em andamento."""
    if not os.path.isdir(os.path.join(SKILL, ".git")):
        return set()
    r = subprocess.run(["git", "-C", SKILL, "status", "--porcelain", "--untracked-files=no"], capture_output=True, text=True)
    return {l[3:].strip().strip('"') for l in r.stdout.splitlines() if l.strip()}


def _e_dono():
    """Clone do dono: tem .git e config.json com "dono_biblioteca": true."""
    try:
        import json
        return os.path.isdir(os.path.join(SKILL, ".git")) and json.load(open(os.path.join(SKILL, "config.json"), encoding="utf-8")).get("dono_biblioteca") is True
    except Exception:
        return False


def sync(calado=False):
    """Devolve (versão, baixados, removidos); versão None quando não sincronizou pelo servidor."""
    d = licenca._ler()
    if not d.get("key"):
        _git_pull()   # ainda sem key (1ª vez): tenta o git enquanto existir
        return None, 0, 0
    if _e_dono():   # no Mac do dono a fonte é o git: o release do servidor pode estar ATRÁS do último commit e
        _git_pull()  # rebaixava arquivos já commitados (27/10/2026: o -7 publicado de outra sessão desfez o progresso.py)
        return None, 0, 0
    man = licenca._post("/v1/release", {"key": d["key"], "maquina": licenca.maquina()})
    if man is None:
        _git_pull()
        return None, 0, 0
    arquivos = man.get("arquivos")
    if not isinstance(arquivos, dict) or not man.get("versao"):
        _git_pull()   # servidor sem release ainda
        return None, 0, 0
    antigos = _cache()
    baixados = 0
    editados = _editados_local()
    for path, sha in arquivos.items():
        if path in editados:
            continue
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
    if (baixados or removidos) and not calado:
        print(f"ATUALIZADO: versão {man['versao']} ({baixados} baixado(s), {removidos} removido(s))")
    return man["versao"], baixados, removidos


def _usando_gab(transcricao):
    """A conversa já abriu o cofre do Gab (o passo zero imprime CONTEUDO_PRONTO)."""
    try:
        with open(transcricao, "rb") as f:
            return b"CONTEUDO_PRONTO" in f.read()
    except Exception:
        return False


def hook():
    """UserPromptSubmit: atualiza no meio do projeto. Nunca falha nem segura o pedido."""
    try:
        ev = json.load(sys.stdin)
        sessao = ev.get("session_id") or ""
        try:
            est = json.load(open(ESTADO_HOOK, encoding="utf-8"))
        except Exception:
            est = {}
        s = est.get(sessao) or {}
        if not s.get("gab"):
            if not _usando_gab(ev.get("transcript_path") or ""):
                return 0
            s["gab"] = True
        if time.time() - s.get("checado", 0) < INTERVALO:
            return 0
        s["checado"] = time.time()
        est = {k: v for k, v in est.items() if time.time() - v.get("checado", 0) < 3 * 86400}   # esquece conversas velhas
        est[sessao] = s
        json.dump(est, open(ESTADO_HOOK, "w", encoding="utf-8"))
        versao, baixados, removidos = sync(calado=True)
        if baixados or removidos:
            aviso = (f"O Gab (/ogab) acabou de ser ATUALIZADO para a versão {versao} ({baixados} arquivo(s) novo(s)). "
                     "Antes de responder este pedido: rodar de novo `python3 " + os.path.join(AQUI, "carregar.py") +
                     "` e reler o <pasta>/SKILL.md que ele imprimir (regras e etapas podem ter mudado); se o pedido usa "
                     "um script, preset ou editor, reler o arquivo dele. Avisar o usuário em uma linha que o Gab foi atualizado.")
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": aviso}},
                             ensure_ascii=False))
    except Exception:
        pass
    return 0


def garantir_hook():
    """Registra o hook acima no ~/.claude/settings.json (uma vez; vale a partir da próxima conversa)."""
    try:
        arq = os.path.join(os.path.expanduser("~"), ".claude", "settings.json")
        conf = json.load(open(arq, encoding="utf-8")) if os.path.exists(arq) else {}
        lista = conf.setdefault("hooks", {}).setdefault("UserPromptSubmit", [])
        if any("atualizar.py" in h.get("command", "") for e in lista for h in e.get("hooks", [])):
            return
        padrao = os.path.join(os.path.expanduser("~"), ".claude", "skills", "ogab")
        cmd = 'python3 "$HOME/.claude/skills/ogab/scripts/atualizar.py" hook' if os.name != "nt" and SKILL == padrao \
            else f'"{sys.executable}" "{os.path.join(AQUI, "atualizar.py")}" hook'
        lista.append({"hooks": [{"type": "command", "command": cmd, "timeout": 20}]})
        tmp = arq + ".tmp"
        json.dump(conf, open(tmp, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        os.replace(tmp, arq)
    except Exception:
        pass   # settings.json inválido: o doctor avisa; a atualização do passo zero segue valendo


if __name__ == "__main__":
    if sys.argv[1:2] == ["hook"]:
        sys.exit(hook())
    sync()
    garantir_hook()
    sys.exit(0)
