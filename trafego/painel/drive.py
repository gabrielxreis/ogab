#!/usr/bin/env python3
"""Leva o tráfego de um cliente para o Google Drive e traz de volta (para outras máquinas usarem o mesmo Jhon).

  python3 ~/.claude/skills/ogab/trafego/painel/drive.py subir --cliente xtrader [--pasta-pai <id da pasta no Drive>]
  python3 ~/.claude/skills/ogab/trafego/painel/drive.py puxar --cliente xtrader

No Drive fica uma pasta "Jhon - <cliente>" com os arquivos crus de clientes/<cliente>/ (trafego.md, painel.json e
miniaturas/*.jpg). A pasta é achada pelo NOME, em qualquer Drive (inclusive drive compartilhado): nenhum ID de cliente
vai para o git. Na primeira vez, `subir` precisa de --pasta-pai (a pasta do cliente no Drive) para criar a pasta.
`puxar` só troca o arquivo local quando o do Drive é mais novo. Usa o `gws` (Google Workspace CLI) já logado.
"""
import argparse
import datetime as dt
import json
import os
import subprocess
import sys

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_MIME = "application/vnd.google-apps.folder"
TODOS = {"supportsAllDrives": True, "includeItemsFromAllDrives": True}


def gws(*args, params=None, corpo=None, upload=None, saida=None):
    cmd = ["gws", "drive", *args]
    if params is not None:
        cmd += ["--params", json.dumps(params)]
    if corpo is not None:
        cmd += ["--json", json.dumps(corpo)]
    if upload:
        cmd += ["--upload", upload]
        if upload.endswith(".md"):
            cmd += ["--upload-content-type", "text/markdown"]
    if saida:
        cmd += ["-o", saida]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        msg = (r.stderr or r.stdout).strip()
        if "invalid_grant" in msg or "login" in msg.lower():
            raise SystemExit("DRIVE_SEM_LOGIN: o gws perdeu o login. Rode `gws auth login` e tente de novo.")
        raise SystemExit(f"DRIVE_ERRO: {' '.join(args)}: {msg[:300]}")
    if saida:
        return None
    texto = r.stdout[r.stdout.find("{"):] if "{" in r.stdout else "{}"
    return json.loads(texto)


def listar(q):
    return gws("files", "list", params={**TODOS, "q": q, "pageSize": 200, "corpora": "allDrives",
                                         "fields": "files(id,name,mimeType,modifiedTime,parents)"}).get("files", [])


def achar_pasta(nome, pai=None):
    q = f"name = '{nome}' and mimeType = '{PASTA_MIME}' and trashed = false"
    if pai:
        q += f" and '{pai}' in parents"
    achadas = listar(q)
    return achadas[0]["id"] if achadas else None


def criar_pasta(nome, pai):
    return gws("files", "create", params={"supportsAllDrives": True}, corpo={"name": nome, "mimeType": PASTA_MIME, "parents": [pai]})["id"]


def mtime_drive(f):
    return dt.datetime.fromisoformat(f["modifiedTime"].replace("Z", "+00:00")).timestamp()


def subir_pasta(local, pasta_id):
    """Sobe cada arquivo de `local` (sem subpastas, salvo miniaturas/) atualizando o que já existe pelo nome."""
    remotos = {f["name"]: f for f in listar(f"'{pasta_id}' in parents and trashed = false")}
    n = 0
    for nome in sorted(os.listdir(local)):
        caminho = os.path.join(local, nome)
        if nome.startswith(".") or os.path.isdir(caminho):
            continue
        r = remotos.get(nome)
        if r and mtime_drive(r) >= os.path.getmtime(caminho):
            continue
        if r:
            gws("files", "update", params={"fileId": r["id"], "supportsAllDrives": True}, corpo={}, upload=caminho)
        else:
            gws("files", "create", params={"supportsAllDrives": True}, corpo={"name": nome, "parents": [pasta_id]}, upload=caminho)
        n += 1
    return n


def puxar_pasta(pasta_id, local):
    os.makedirs(local, exist_ok=True)
    n = 0
    for f in listar(f"'{pasta_id}' in parents and trashed = false"):
        if f["mimeType"] == PASTA_MIME or f["mimeType"].startswith("application/vnd.google-apps"):
            continue
        caminho = os.path.join(local, f["name"])
        if os.path.exists(caminho) and os.path.getmtime(caminho) >= mtime_drive(f):
            continue
        gws("files", "get", params={"fileId": f["id"], "alt": "media", "supportsAllDrives": True}, saida=caminho)
        os.utime(caminho, (mtime_drive(f), mtime_drive(f)))
        n += 1
    return n


def atualizar_doc(local, pasta_id):
    """Reescreve o Google Doc legível "<Cliente> - Tráfego pago (Jhon)" que fica na mesma pasta que "Jhon - <cliente>"
    (para quem procura à mão no Drive). Cria o Doc se ainda não existir. Nunca cria "v2": atualiza o mesmo arquivo."""
    md = os.path.join(local, "trafego.md")
    if not os.path.isfile(md):
        return None
    pai = gws("files", "get", params={"fileId": pasta_id, "supportsAllDrives": True, "fields": "parents"}).get("parents", [None])[0]
    if not pai:
        return None
    docs = [f for f in listar(f"'{pai}' in parents and mimeType = 'application/vnd.google-apps.document' and trashed = false")
            if "Tráfego pago (Jhon)" in f["name"] and " v2" not in f["name"]]
    if docs:
        gws("files", "update", params={"fileId": docs[0]["id"], "supportsAllDrives": True}, corpo={}, upload=md)
        return docs[0]["name"]
    titulo = (open(md, encoding="utf-8").readline().split(":", 1)[-1].strip() or "Cliente") + " - Tráfego pago (Jhon)"
    gws("files", "create", params={"supportsAllDrives": True},
        corpo={"name": titulo, "parents": [pai], "mimeType": "application/vnd.google-apps.document"}, upload=md)
    return titulo


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("acao", choices=["subir", "puxar"])
    ap.add_argument("--cliente", required=True)
    ap.add_argument("--pasta-pai", help="pasta do cliente no Drive (só na primeira subida)")
    a = ap.parse_args()

    nome = f"Jhon - {a.cliente}"
    local = os.path.join(SKILL, "clientes", a.cliente)
    pasta = achar_pasta(nome)
    if a.acao == "subir":
        if not os.path.isdir(local):
            raise SystemExit(f"SEM_CLIENTE: {local} não existe")
        if not pasta:
            if not a.pasta_pai:
                raise SystemExit(f'SEM_PASTA: não achei "{nome}" no Drive; passe --pasta-pai <id da pasta do cliente>')
            pasta = criar_pasta(nome, a.pasta_pai)
        n = subir_pasta(local, pasta)
        if os.path.isdir(os.path.join(local, "miniaturas")):
            sub = achar_pasta("miniaturas", pasta) or criar_pasta("miniaturas", pasta)
            n += subir_pasta(os.path.join(local, "miniaturas"), sub)
        print(f"DRIVE_SUBIU: {n} arquivo(s) novo(s) ou atualizado(s) em \"{nome}\" (https://drive.google.com/drive/folders/{pasta})")
        doc = atualizar_doc(local, pasta)
        if doc:
            print(f"DRIVE_DOC: \"{doc}\" reescrito com o trafego.md (mesmo Doc, sem cópia nova)")
    else:
        if not pasta:
            raise SystemExit(f'SEM_PASTA: não achei "{nome}" no Drive (alguém precisa rodar `subir` primeiro)')
        n = puxar_pasta(pasta, local)
        sub = achar_pasta("miniaturas", pasta)
        if sub:
            n += puxar_pasta(sub, os.path.join(local, "miniaturas"))
        print(f"DRIVE_PUXOU: {n} arquivo(s) atualizado(s) em clientes/{a.cliente}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
