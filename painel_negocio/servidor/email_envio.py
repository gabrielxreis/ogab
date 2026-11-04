"""E-mail do Meu Negócio: manda orçamento (com o PDF anexado) pelo SMTP da própria pessoa (Gmail com senha de app,
Outlook, Hostinger, iCloud ou qualquer outro). A configuração fica cifrada em DADOS/email.enc com uma chave local
(DADOS/.chave_email, só leitura do dono); nada disso vai para o git nem sai do computador."""
import base64, hashlib, hmac, json, os, re, secrets, smtplib, socket, ssl
from email.message import EmailMessage
from email.utils import formataddr, make_msgid

# provedores conhecidos: o host sai do domínio do e-mail quando a pessoa não informa
PROVEDORES = {
    "gmail.com": ("smtp.gmail.com", 465), "googlemail.com": ("smtp.gmail.com", 465),
    "outlook.com": ("smtp.office365.com", 587), "hotmail.com": ("smtp.office365.com", 587),
    "live.com": ("smtp.office365.com", 587), "icloud.com": ("smtp.mail.me.com", 587), "me.com": ("smtp.mail.me.com", 587),
    "yahoo.com": ("smtp.mail.yahoo.com", 465), "yahoo.com.br": ("smtp.mail.yahoo.com", 465),
}


class Erro(Exception):
    pass


def _caminhos(dados):
    return os.path.join(dados, "email.enc"), os.path.join(dados, ".chave_email")


def _chave(dados):
    _, arq = _caminhos(dados)
    if not os.path.exists(arq):
        with open(arq, "wb") as f:
            f.write(secrets.token_bytes(32))
        os.chmod(arq, 0o600)
    return open(arq, "rb").read()


def _fluxo(k, nonce, n):
    saida, i = b"", 0
    while len(saida) < n:
        saida += hashlib.sha256(k + nonce + i.to_bytes(8, "big")).digest()
        i += 1
    return saida[:n]


def _cifrar(dados_txt, k):
    nonce = secrets.token_bytes(16)
    corpo = bytes(a ^ b for a, b in zip(dados_txt, _fluxo(k, nonce, len(dados_txt))))
    tag = hmac.new(k, nonce + corpo, hashlib.sha256).digest()
    return nonce + tag + corpo


def _decifrar(blob, k):
    nonce, tag, corpo = blob[:16], blob[16:48], blob[48:]
    if not hmac.compare_digest(tag, hmac.new(k, nonce + corpo, hashlib.sha256).digest()):
        raise Erro("configuração de e-mail corrompida; configure de novo em Ajustes")
    return bytes(a ^ b for a, b in zip(corpo, _fluxo(k, nonce, len(corpo))))


def carregar(dados):
    arq, _ = _caminhos(dados)
    if not os.path.exists(arq):
        return None
    return json.loads(_decifrar(open(arq, "rb").read(), _chave(dados)))


def salvar(dados, cfg):
    arq, _ = _caminhos(dados)
    with open(arq, "wb") as f:
        f.write(_cifrar(json.dumps(cfg).encode(), _chave(dados)))
    os.chmod(arq, 0o600)


def apagar(dados):
    arq, _ = _caminhos(dados)
    if os.path.exists(arq):
        os.remove(arq)


def status(dados):
    try:
        cfg = carregar(dados)
    except Erro:
        cfg = None
    if not cfg:
        return {"configurado": False}
    return {"configurado": True, "usuario": cfg["usuario"], "nome": cfg.get("nome") or "", "host": cfg["host"], "porta": cfg["porta"]}


def completar(cfg):
    """Preenche host/porta pelo domínio do e-mail quando faltar."""
    usuario = (cfg.get("usuario") or "").strip()
    if "@" not in usuario:
        raise Erro("Coloque o seu e-mail completo (ex.: voce@gmail.com)")
    if not cfg.get("senha"):
        raise Erro("Coloque a senha de app do e-mail")
    host = (cfg.get("host") or "").strip()
    porta = int(cfg.get("porta") or 0)
    if not host:
        dominio = usuario.split("@", 1)[1].lower()
        host, porta_padrao = PROVEDORES.get(dominio, (f"smtp.{dominio}", 465))
        porta = porta or porta_padrao
    return {"usuario": usuario, "senha": re.sub(r"[\s\u200b-\u200d\u2060\ufeff]", "", cfg["senha"]), "host": host, "porta": porta or 465,
            "nome": (cfg.get("nome") or "").strip()}


def _entrar(s, usuario, senha):
    """Login só por AUTH PLAIN: o smtplib tenta LOGIN depois de um 535 e o Gmail derruba a conexão, escondendo o motivo."""
    s.ehlo()
    if "plain" not in s.esmtp_features.get("auth", "").lower():
        return s.login(usuario, senha)
    s.user, s.password = usuario, senha
    s.auth("PLAIN", s.auth_plain)


def enviar(cfg, para, assunto, texto, anexos=()):
    msg = EmailMessage()
    msg["From"] = formataddr((cfg.get("nome") or cfg["usuario"], cfg["usuario"]))
    msg["To"] = para
    msg["Subject"] = assunto
    msg["Message-ID"] = make_msgid()
    msg.set_content(texto)
    for nome, conteudo, tipo in anexos:
        principal, _, sub = (tipo or "application/octet-stream").partition("/")
        msg.add_attachment(conteudo, maintype=principal, subtype=sub or "octet-stream", filename=nome)
    contexto = ssl.create_default_context()
    try:
        if int(cfg["porta"]) == 465:
            with smtplib.SMTP_SSL(cfg["host"], 465, timeout=25, context=contexto) as s:
                _entrar(s, cfg["usuario"], cfg["senha"])
                s.send_message(msg)
        else:
            with smtplib.SMTP(cfg["host"], int(cfg["porta"]), timeout=25) as s:
                s.starttls(context=contexto)
                _entrar(s, cfg["usuario"], cfg["senha"])
                s.send_message(msg)
    except smtplib.SMTPAuthenticationError as e:
        motivo = (e.smtp_error or b"").decode("utf-8", "replace")
        if e.smtp_code == 534 or "Application-specific" in motivo:
            raise Erro("O Gmail pediu uma senha de app: a senha normal da conta não funciona aqui. Crie em myaccount.google.com/apppasswords (precisa da verificação em duas etapas ligada).")
        raise Erro("O e-mail recusou o login: o e-mail ou a senha de app não conferem. Confira se a senha de app foi criada nesta mesma conta "
                   f"({cfg['usuario']}) e cole de novo, só as 16 letras. Resposta do servidor: {e.smtp_code} {motivo.splitlines()[0] if motivo else ''}".strip())
    except smtplib.SMTPRecipientsRefused:
        raise Erro(f"O e-mail recusou o destinatário {para}. Confira o endereço.")
    except smtplib.SMTPException as e:  # vem antes do OSError: SMTPException herda dele
        raise Erro(f"O servidor de e-mail recusou o envio: {e}")
    except (socket.gaierror, OSError):
        raise Erro(f"Não consegui falar com o servidor {cfg['host']}:{cfg['porta']}. Confira o servidor e a internet.")


def configurar(dados, corpo):
    """POST /api/ogab/email: salva só depois que o e-mail de teste para o próprio remetente sair."""
    if corpo.get("acao") == "apagar":
        apagar(dados)
        return {"ok": True, "configurado": False}
    cfg = completar(corpo)
    enviar(cfg, cfg["usuario"], "Meu Negócio: e-mail configurado",
           "Tudo certo! A partir de agora os seus orçamentos saem deste e-mail, direto do Meu Negócio do O Gab.")
    salvar(dados, cfg)
    return {"ok": True, **status(dados)}


def enviar_orcamento(dados, corpo):
    """Função send-quote-email do painel: {to, customSubject, customBody, pdf_base64?, pdf_nome?}."""
    cfg = carregar(dados)
    if not cfg:
        return 412, {"error": "email_nao_configurado", "message": "Configure o seu e-mail em Ajustes para enviar direto daqui."}
    para = (corpo.get("to") or "").strip()
    if "@" not in para:
        return 400, {"error": "Informe o e-mail do cliente"}
    anexos = []
    if corpo.get("pdf_base64"):
        try:
            anexos.append((corpo.get("pdf_nome") or "orcamento.pdf", base64.b64decode(corpo["pdf_base64"]), "application/pdf"))
        except (ValueError, TypeError):
            return 400, {"error": "PDF do orçamento inválido"}
    try:
        enviar(cfg, para, corpo.get("customSubject") or "Orçamento", corpo.get("customBody") or "", anexos)
    except Erro as e:
        return 502, {"error": str(e)}
    return 200, {"ok": True, "enviado_para": para, "anexos": len(anexos)}
