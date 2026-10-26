"""Carregador do Gab (/ogab): no passo zero, valida a key, pega a senha da sessão no servidor e abre a
"inteligência" (etapas, regras, receitas) criptografada em `cofre/conteudo.enc` para uma pasta temporária.
Sem key válida, a senha não vem e o cofre continua embaralhado: o Gab não roda.

  python3 carregar.py            # sai 0 e imprime CONTEUDO_PRONTO: <pasta> ; ou sai 1 com a mensagem do que fazer

A senha vem do servidor a cada abertura. Offline, vale a última senha boa por OFFLINE_DIAS (como a licença).
Bloqueou/ inválida: a senha em cache é apagada e o conteúdo não abre mais até validar de novo.
"""
import io, os, shutil, sys, tempfile, time, zipfile

AQUI = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
import licenca  # noqa: E402  (mesma pasta)
import cofre     # noqa: E402

ENC = os.path.join(SKILL, "cofre", "conteudo.enc")


def destino():
    return os.path.join(tempfile.gettempdir(), "ogab_cofre_" + licenca.maquina()[:12])


def _extrair(blob_senha):
    dados = cofre.decriptar(open(ENC, "rb").read(), cofre.chave(blob_senha))
    dst = destino()
    shutil.rmtree(dst, ignore_errors=True)
    os.makedirs(dst)
    with zipfile.ZipFile(io.BytesIO(dados)) as z:
        z.extractall(dst)
    print("CONTEUDO_PRONTO: " + dst)
    return 0


def abrir():
    if not os.path.exists(ENC):
        # skill ainda sem cofre (antes da migração): não bloqueia, segue com os arquivos abertos
        return 0
    d = licenca._ler()
    if not d.get("key"):
        print(licenca.PENDENTE)
        return 1
    r = licenca._post("/v1/abrir", {"key": d["key"], "maquina": licenca.maquina()})
    if r is None:   # offline: usa a senha em cache dentro da validade
        if d.get("cofre") and d.get("maquina") == licenca.maquina() \
                and time.time() - d.get("validado_em", 0) < licenca.OFFLINE_DIAS * 86400:
            print(f"COFRE_OFFLINE: sem conexão; abrindo com a senha de "
                  f"{time.strftime('%d/%m %H:%M', time.localtime(d['validado_em']))} (vale {licenca.OFFLINE_DIAS} dias)")
            try:
                return _extrair(d["cofre"])
            except Exception:
                pass
        print(f"LICENCA_SEM_CONEXAO: não deu pra validar a key (sem internet há mais de {licenca.OFFLINE_DIAS} "
              "dias ou nunca validou). Conecte e tente de novo; o Gab não roda até validar.")
        return 1
    st = r.get("status")
    if st == "ok" and r.get("cofre"):
        d.update(cofre=r["cofre"], maquina=licenca.maquina(), validado_em=int(time.time()),
                 email=r.get("email", d.get("email", "")))
        licenca._gravar(d)
        try:
            return _extrair(r["cofre"])
        except Exception as e:
            print(f"COFRE_ERRO: a senha não abriu o cofre ({e}). Rode de novo; se persistir, reinstale o Gab.")
            return 1
    # bloqueada / inválida / outra máquina: apaga a senha em cache (não reabre offline) e explica
    d["cofre"], d["validado_em"] = "", 0
    licenca._gravar(d)
    shutil.rmtree(destino(), ignore_errors=True)
    if st == "bloqueada":
        print("LICENCA_BLOQUEADA: esta instalação foi desativada pelo autor. Falar com @gabrielxreis_ no "
              "Instagram. O Gab não roda.")
    elif st == "outra_maquina":
        print("LICENCA_OUTRA_MAQUINA: esta key está ativa em outro computador (1 por key). No computador antigo: "
              "`licenca.py liberar`; ou cadastrar outro email aqui com `licenca.py registrar --email <email>`.")
    else:
        print("LICENCA_INVALIDA: " + r.get("msg", st) + ". " + licenca.PENDENTE.split(": ", 1)[1])
    return 1


if __name__ == "__main__":
    sys.exit(abrir())
