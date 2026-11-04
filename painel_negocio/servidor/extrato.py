"""Extrato do banco (OFX/QFX/CSV) -> transações. Porte da função parse-bank-statement do Frame Zero.
PDF precisa de IA: por enquanto pede OFX ou CSV (todo banco exporta um dos dois)."""
import datetime as dt, re


class Erro(Exception):
    pass


def categoria(desc):
    d = desc.lower()
    regras = [
        (("pix", "ted", "transf"), "Transferência"),
        (("salario", "folha", "pagto func"), "Salário"),
        (("energia", "luz", "agua", "internet", "telefone", "assinatura"), "Manutenção"),
        (("imposto", "taxa", "darf", "gps", "inss", "fgts"), "Impostos"),
        (("uber", "99", "combustivel", "gasolina", "estacion"), "Transporte"),
        (("restaur", "ifood", "rappi", "mercado", "supermercado", "padaria"), "Alimentação"),
        (("licenca", "software", "google", "microsoft", "adobe"), "Licença"),
        (("material", "equip", "compra"), "Material"),
        (("cliente", "servico", "projeto", "pagamento", "fatura"), "Projeto"),
    ]
    for chaves, cat in regras:
        if any(k in d for k in chaves):
            return cat
    return "Outro"


def data(txt):
    txt = (txt or "").strip()
    m = re.match(r"^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$", txt)
    if m:
        return f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"
    m = re.match(r"^(\d{4})[/-](\d{1,2})[/-](\d{1,2})$", txt)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    if re.fullmatch(r"\d{8}", txt):
        return f"{txt[:4]}-{txt[4:6]}-{txt[6:8]}"
    return None


def numero(txt):
    txt = re.sub(r"[^\d,.\-()]", "", (txt or "").strip())
    negativo = "(" in txt or "-" in txt
    txt = txt.replace("(", "").replace(")", "").replace("-", "")
    if "," in txt and "." in txt:
        txt = txt.replace(".", "").replace(",", ".") if txt.rfind(",") > txt.rfind(".") else txt.replace(",", "")
    elif "," in txt:
        txt = txt.replace(",", ".")
    try:
        n = abs(float(txt))
    except ValueError:
        n = 0.0
    return -n if negativo else n


def csv(texto):
    linhas = [l for l in texto.split("\n") if l.strip()]
    if len(linhas) < 2:
        return []
    cab = linhas[0].lower()
    sep = ";" if ";" in cab else ","
    cols = [c.strip().replace('"', "") for c in cab.split(sep)]

    def idx(*chaves):
        return next((i for i, c in enumerate(cols) if any(k in c for k in chaves)), -1)
    i_data, i_desc, i_valor = idx("data", "date", "dt"), idx("descri", "hist", "memo", "lancamento"), idx("valor", "value", "amount", "quantia")
    i_tipo, i_cred, i_deb = idx("tipo", "type", "natureza", "dc"), idx("credito", "credit", "entrada"), idx("debito", "debit", "saida")
    saida = []
    for linha in linhas[1:]:
        v = [x.strip().replace('"', "") for x in linha.split(sep)]
        if len(v) < 2:
            continue
        d = data(v[i_data] if i_data >= 0 else v[0])
        desc = v[i_desc] if i_desc >= 0 else v[1]
        if not d or not desc or len(desc) < 2:
            continue
        valor, tipo = 0.0, "expense"
        if i_cred >= 0 and i_deb >= 0:
            c, db = numero(v[i_cred]), numero(v[i_deb])
            if c > 0:
                valor, tipo = c, "income"
            elif db > 0:
                valor, tipo = db, "expense"
        elif i_valor >= 0:
            bruto = v[i_valor]
            valor = abs(numero(bruto))
            if i_tipo >= 0:
                t = v[i_tipo].lower()
                tipo = "income" if ("c" in t or "credit" in t or "entrada" in t) else "expense"
            elif "-" in bruto or bruto.startswith("("):
                tipo = "expense"
            elif "+" in bruto:
                tipo = "income"
            else:
                dl = desc.lower()
                tipo = "income" if any(k in dl for k in ("receb", "pix receb", "deposito", "ted receb")) else "expense"
        if valor > 0:
            saida.append({"date": d, "description": desc[:100], "amount": valor, "type": tipo, "category": categoria(desc)})
    return saida


def ofx(texto):
    texto = texto.replace("\r\n", "\n").replace("\r", "\n")
    blocos = re.findall(r"<STMTTRN>([\s\S]*?)</STMTTRN>", texto, re.I) or re.split(r"<STMTTRN>", texto, flags=re.I)[1:]
    saida = []
    for b in blocos:
        def campo(tag, ate=r"[^<\n\r]+"):
            m = re.search(rf"<{tag}>\s*({ate})", b, re.I)
            return m.group(1).strip() if m else None
        tipo_trn = (campo("TRNTYPE") or "").upper()
        dtp, val = campo("DTPOSTED"), campo("TRNAMT")
        if not dtp or not val or len(dtp) < 8:
            continue
        d = f"{dtp[:4]}-{dtp[4:6]}-{dtp[6:8]}"
        try:
            n = float(re.sub(r"\[.*\]", "", val).strip().replace(",", ".", 1))
        except ValueError:
            continue
        if not n:
            continue
        credito = n > 0 or tipo_trn in ("CREDIT", "DEP", "DIRECTDEP")
        desc = campo("MEMO") or campo("NAME") or tipo_trn or "Transação"
        num = campo("CHECKNUM")
        if num and num not in desc:
            desc += f" #{num}"
        saida.append({"date": d, "description": desc[:100], "amount": abs(n), "type": "income" if credito else "expense",
                      "category": categoria(desc)})
    return saida


def ler(nome, dados, periodo="all"):
    ext = nome.lower().rsplit(".", 1)[-1]
    texto = None
    for cod in ("utf-8", "latin-1"):
        try:
            texto = dados.decode(cod)
            break
        except UnicodeDecodeError:
            continue
    if ext == "csv":
        trans = csv(texto)
    elif ext in ("ofx", "qfx"):
        trans = ofx(texto)
    elif ext == "pdf":
        raise Erro("PDF ainda não: exporte o extrato em OFX ou CSV no app do seu banco (todos têm essa opção).")
    else:
        raise Erro("Formato de arquivo não suportado. Use CSV ou OFX.")
    if periodo != "all":
        try:
            corte = (dt.date.today() - dt.timedelta(days=int(periodo))).isoformat()
            trans = [t for t in trans if t["date"] >= corte]
        except ValueError:
            pass
    if not trans:
        raise Erro("Nenhuma transação válida encontrada no arquivo. Verifique o formato do arquivo.")
    return {"success": True, "transactions": trans, "total": len(trans),
            "summary": {"income": sum(t["amount"] for t in trans if t["type"] == "income"),
                        "expense": sum(t["amount"] for t in trans if t["type"] == "expense")}}
