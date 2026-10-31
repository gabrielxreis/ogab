"""Ponte Claude Code -> Codex: o Gab (rodando no Claude) passa para o Codex o que o Codex faz melhor.
Usa o `codex exec` da máquina, logado na conta ChatGPT da pessoa (sem crédito de Higgsfield/Magnific).

  python3 codex_ponte.py checar
      sai 0 e imprime CODEX_OK se o comando codex existe e está logado; senão sai 1 com o motivo
  python3 codex_ponte.py imagem "<prompt>" <saida.png> [--ref img.png ...] [--transparente]
      gera UMA imagem com o image_gen nativo do Codex e grava em <saida.png> (nome novo: nunca sobrescreve)
  python3 codex_ponte.py tarefa "<pedido>" [--pasta <dir>] [--ref img.png ...]
      tarefa livre (código de motion, conserto de script, segunda opinião); imprime a resposta final do Codex
  python3 codex_ponte.py revisar <pasta_do_repo>
      `codex review` das mudanças da pasta (olho fresco antes de renderizar ou commitar)
"""
import os, shutil, subprocess, sys, tempfile, time

CODEX_HOME = os.environ.get("CODEX_HOME") or os.path.join(os.path.expanduser("~"), ".codex")


def _codex():
    return shutil.which("codex")


def checar():
    if not _codex():
        print("CODEX_AUSENTE: instale o Codex (https://developers.openai.com/codex) e faça login com a conta ChatGPT")
        return 1
    r = subprocess.run([_codex(), "login", "status"], capture_output=True, text=True)
    if r.returncode != 0:
        print("CODEX_SEM_LOGIN: rode `codex login` no Terminal")
        return 1
    print("CODEX_OK")
    return 0


def _exec(prompt, pasta, refs=(), timeout=900):
    """Roda o codex exec e devolve (código, última mensagem)."""
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        ultima = f.name
    cmd = [_codex(), "exec", "--skip-git-repo-check", "-s", "workspace-write", "-C", pasta, "-o", ultima]
    for ref in refs:
        cmd += ["-i", os.path.abspath(ref)]
    cmd.append(prompt)
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        cod = r.returncode
    except subprocess.TimeoutExpired:
        cod = 124
    try:
        txt = open(ultima, encoding="utf-8").read().strip()
    except Exception:
        txt = ""
    os.unlink(ultima)
    return cod, txt


def _novas_imagens(desde):
    base = os.path.join(CODEX_HOME, "generated_images")
    achadas = []
    for raiz, _, fs in os.walk(base):
        for f in fs:
            p = os.path.join(raiz, f)
            if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp")) and os.path.getmtime(p) >= desde:
                achadas.append(p)
    return sorted(achadas, key=os.path.getmtime)


def imagem(prompt, saida, refs, transparente):
    if checar() != 0:
        return 1
    saida = os.path.abspath(saida)
    if os.path.exists(saida):
        print(f"ERRO: {saida} já existe; use um nome novo (regra: versão nova = nome novo)")
        return 1
    pasta = os.path.dirname(saida)
    os.makedirs(pasta, exist_ok=True)
    pedido = ("Use a ferramenta nativa image_gen para gerar exatamente UMA imagem. Não escreva código nem use API. "
              + ("Fundo transparente (PNG com alfa), objeto inteiro e centralizado, sem sombra cortada. " if transparente else "")
              + f"Depois copie a imagem gerada para {saida} e responda só com o caminho.\n\nImagem: {prompt}")
    inicio = time.time() - 2
    cod, txt = _exec(pedido, pasta, refs)
    if not os.path.exists(saida):
        novas = _novas_imagens(inicio)
        if novas:
            shutil.copy2(novas[-1], saida)
    if os.path.exists(saida):
        print("IMAGEM: " + saida)
        return 0
    print(f"IMAGEM_FALHOU (codex saiu {cod}): {txt[-300:]}")
    return 1


def tarefa(pedido, pasta, refs):
    if checar() != 0:
        return 1
    cod, txt = _exec(pedido, os.path.abspath(pasta), refs, timeout=1800)
    print(txt)
    return 0 if cod == 0 else 1


def revisar(pasta):
    if checar() != 0:
        return 1
    r = subprocess.run([_codex(), "exec", "review"], cwd=os.path.abspath(pasta), capture_output=True, text=True)
    print((r.stdout + r.stderr).strip()[-6000:])
    return r.returncode


def _opcoes(args):
    refs, livres, pasta, transp = [], [], os.getcwd(), False
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--ref":
            refs.append(args[i + 1]); i += 2; continue
        if a == "--pasta":
            pasta = args[i + 1]; i += 2; continue
        if a == "--transparente":
            transp = True; i += 1; continue
        livres.append(a); i += 1
    return livres, refs, pasta, transp


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    sub, livres, refs, pasta, transp = sys.argv[1], *_opcoes(sys.argv[2:])
    if sub == "checar":
        return checar()
    if sub == "imagem" and len(livres) == 2:
        return imagem(livres[0], livres[1], refs, transp)
    if sub == "tarefa" and len(livres) == 1:
        return tarefa(livres[0], pasta, refs)
    if sub == "revisar" and len(livres) == 1:
        return revisar(livres[0])
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())
