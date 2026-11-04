"""Contrato de prestação de serviços sem IA: o mesmo modelo de 14 cláusulas que a função generate-contract do
Frame Zero pedia para a IA, preenchido com os dados do formulário. Sai no formato de stream (SSE) que o painel lê."""
import datetime as dt, json

MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro",
         "novembro", "dezembro"]


def brl(v):
    s = f"{float(v or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


def texto(d):
    valor = float(d.get("contractValue") or 0)
    pagamento = f"O presente serviço será remunerado pela quantia de {brl(valor)}."
    n = int(d.get("installmentCount") or 0)
    if d.get("isInstallment") and n > 1:
        pagamento = (f"O presente serviço será remunerado pela quantia total de {brl(valor)}, divididos em {n} parcelas "
                     f"de {brl(valor / n)} cada.")
        if d.get("installmentDueDay"):
            pagamento += f" A data de vencimento será todo dia {d['installmentDueDay']} de cada mês."
    if d.get("paymentMethod"):
        pagamento += f" O pagamento deverá ser feito via {d['paymentMethod']}."
    if d.get("pixKey"):
        pagamento += f" (Chave PIX: {d['pixKey']})"
    servico = d.get("serviceType") or "serviços"
    descricao = (d.get("serviceDescription") or "conforme especificações acordadas entre as partes").strip().rstrip(".")
    projeto = f", referente ao projeto {d['projectName']}" if d.get("projectName") else ""
    foro = d.get("forumCity") or d.get("companyCity") or "da sede do CONTRATADO"
    prazo = d.get("deliveryDays") or 30
    hoje = dt.date.today()
    data = f"{hoje.day:02d} de {MESES[hoje.month - 1]} de {hoje.year}"
    extras = (d.get("terms") or "").strip()
    partes = [
        "DO OBJETO DO CONTRATO",
        f"CLÁUSULA 1ª - É objeto do presente contrato a prestação do serviço de {servico}{projeto}: {descricao}.",
        "",
        "OBRIGAÇÕES DO CONTRATADO",
        "CLÁUSULA 2ª - É dever do CONTRATADO executar os serviços com qualidade, zelo e dentro dos prazos combinados, "
        "mantendo o CONTRATANTE informado sobre o andamento do trabalho.",
        "CLÁUSULA 3ª - O CONTRATADO deverá fornecer recibo ou nota referente a cada pagamento recebido.",
        "",
        "DO PREÇO E DAS CONDIÇÕES DE PAGAMENTO",
        f"CLÁUSULA 4ª - {pagamento}",
        "",
        "DO INADIMPLEMENTO, DO DESCUMPRIMENTO E DA MULTA",
        "CLÁUSULA 5ª - Em caso de inadimplência, incidirá multa de 5% (cinco por cento) sobre o valor devido, juros de "
        "mora de 1% (um por cento) ao mês e correção monetária pro rata die.",
        "Parágrafo único - Em caso de cobrança judicial, serão devidos honorários advocatícios de 20% (vinte por cento) "
        "sobre o valor do débito.",
        "",
        "DA RESCISÃO IMOTIVADA",
        "CLÁUSULA 6ª - A parte que rescindir o presente contrato sem justo motivo pagará multa de 50% (cinquenta por "
        "cento) do valor do contrato, mediante aviso prévio de 30 (trinta) dias.",
        "",
        "DO PRAZO",
        f"CLÁUSULA 7ª - Os serviços serão entregues em até {prazo} dias após o início dos trabalhos, salvo acordo "
        "diferente entre as partes por escrito.",
        "CLÁUSULA 8ª - Nenhuma das partes responderá por atrasos causados por caso fortuito ou força maior, como "
        "epidemias, pandemias, guerras, lockdown ou decisões de autoridades, enquanto durarem esses eventos.",
        "",
        "INFORMAÇÕES E AUTORIZAÇÕES",
        "CLÁUSULA 9ª - O CONTRATANTE autoriza o CONTRATADO a usar trechos do material produzido em seu portfólio e "
        "redes sociais, salvo pedido contrário por escrito.",
        "CLÁUSULA 10ª - É vedado a qualquer das partes negociar ou divulgar o material em nome da outra sem autorização.",
        "",
        "DO SIGILO",
        "CLÁUSULA 11ª - As partes manterão sigilo sobre informações confidenciais a que tiverem acesso em razão deste "
        "contrato, durante a vigência dele e após o seu término.",
        "",
        "DA RESPONSABILIDADE",
        "CLÁUSULA 12ª - O CONTRATANTE é responsável pela veracidade das informações e pelos direitos sobre os materiais "
        "que fornecer para a execução do serviço.",
        "",
        "DAS PENALIDADES",
        "CLÁUSULA 13ª - A violação de qualquer cláusula deste contrato sujeita a parte infratora às penalidades aqui "
        "previstas, sem prejuízo de perdas e danos.",
    ]
    if extras:
        partes += ["", "TERMOS ADICIONAIS", extras]
    partes += [
        "",
        "DO FORO",
        f"CLÁUSULA 14ª - Fica eleito o foro da cidade de {foro} para dirimir quaisquer dúvidas oriundas deste contrato, "
        "sendo regido pelas leis brasileiras.",
        "",
        "E por estarem assim justas e acordadas, as Partes assinam o presente contrato.",
        "",
        f"{d.get('companyCity') or foro}, {data}.",
    ]
    return "\n".join(partes)


def sse(conteudo, pedaco=400):
    """Formato de stream que o painel espera (igual ao gateway de IA): linhas 'data: {...}' e 'data: [DONE]'."""
    linhas = []
    for i in range(0, len(conteudo), pedaco):
        linhas.append("data: " + json.dumps({"choices": [{"delta": {"content": conteudo[i:i + pedaco]}}]}, ensure_ascii=False))
    linhas.append("data: [DONE]")
    return ("\n\n".join(linhas) + "\n\n").encode()
