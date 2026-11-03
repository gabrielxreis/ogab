# Enviar de uma caixa do Microsoft 365

A Mariana envia e lê emails por uma caixa do Microsoft 365 / Outlook
(Exchange Online) usando o Microsoft Graph. Use quando o email do seu
domínio de envio estiver no Microsoft 365.

## Por que não SMTP + IMAP?

O Exchange Online não aceita mais senha no IMAP, e o SMTP AUTH vem desligado
na maioria das organizações. O provedor `smtp` às vezes ainda envia, mas não
consegue ler a caixa de entrada. A Mariana precisa ler as respostas para
parar as sequências, respeitar pedidos de descadastro e pegar bounces. Se ela
envia mas não lê, continua mandando email para quem já respondeu.

O provedor `microsoft` entra com OAuth (código de autorização + PKCE). A
Mariana nunca guarda senha nem segredo de cliente.

## Configuração

### 1. Registrar um app no Entra ID

Em [entra.microsoft.com](https://entra.microsoft.com), vá em
**Applications → App registrations → New registration**:

| Campo | Valor |
|---|---|
| Name | `Mariana` |
| Supported account types | *Accounts in this organizational directory only* |
| Redirect URI, plataforma | **Public client/native (mobile & desktop)** |
| Redirect URI, valor | `http://localhost:8766` |

Na **Overview** do app, copie o **Application (client) ID** e o
**Directory (tenant) ID**.

Não crie segredo de cliente. A Mariana é um cliente público.

### 2. Configurar a Mariana

`.env`:

```
M365_CLIENT_ID=<Application (client) ID>
M365_TENANT_ID=<Directory (tenant) ID>
```

`harvey.local.yaml`:

```yaml
persona:
  email: "voce@seudominio.com"   # precisa ser a caixa com que você entra
channels:
  email:
    provider: "microsoft"
```

### 3. Entrar uma vez

```bash
mariana microsoft auth   # abre o navegador; entre como persona.email
mariana microsoft test   # → ✓ Connected as voce@seudominio.com
```

A Mariana pede quatro permissões **delegadas**:

| Permissão | Para quê |
|---|---|
| `Mail.ReadWrite` | ler respostas e criar rascunhos (respostas no mesmo fio) |
| `Mail.Send` | enviar |
| `User.Read` | conferir de qual caixa é o token |
| `offline_access` | continuar funcionando sem entrar de novo |

O token de renovação fica em `data/m365_token.json` (fora do git). No macOS e
no Linux o arquivo só pode ser lido pelo dono (modo 600). No Windows ele fica
protegido só pelas permissões da pasta, então deixe a Mariana numa pasta que
só você acessa. A Microsoft troca o token a cada uso e a Mariana salva o novo.

### Se aparecer "Need admin approval"

A sua organização não deixa usuários aprovarem apps. Um administrador precisa
aprovar uma vez:

1. No Entra, abra **App registrations → Mariana → API permissions**. Adicione
   as quatro permissões delegadas do Microsoft Graph acima e clique em
   **Grant admin consent**.
2. Rode `mariana microsoft auth` de novo e entre com a **caixa de envio**, não
   com o administrador. A Mariana sempre age como quem entrou.

Para ninguém mais da organização usar o app, vá em
**Enterprise applications → Mariana**:

1. **Users and groups**: atribua só a caixa de envio.
2. **Properties**: marque **Assignment required?** como **Yes**. Faça isso
   depois do passo 1, senão a própria caixa de envio fica bloqueada.

## Como funciona

- **Envio.** A Mariana cria um rascunho e envia, para saber o `Message-ID` do
  email. Bounces e respostas são casados por ele.
- **Respostas no mesmo fio.** Ela responde com `createReply` na mensagem do
  próprio cliente, então `In-Reply-To` e `References` ficam certos. Se a
  mensagem foi apagada, a resposta sai como email novo.
- **Sua caixa não é mexida.** A cada ciclo ela lê os últimos 7 dias da caixa
  de entrada, do mais novo pro mais antigo, página por página, e ignora os
  seus próprios emails. Nunca marca como lido, move ou apaga. Ela guarda o
  próprio registro do que já tratou.
- **Só age como a caixa certa.** Se a caixa conectada não for o
  `persona.email`, toda leitura e envio é recusado com uma mensagem dizendo
  isso. Pega o erro comum de entrar como o administrador que aprovou o app.
- **Falha segura o envio.** Se a caixa não puder ser lida (login vencido,
  Graph fora do ar, limite de uso), o ciclo não envia nada: uma resposta não
  lida não teria parado os follow-ups. Limite do Graph (429/503 com
  `Retry-After` curto) é tentado de novo uma vez. Uma leitura que falha no
  meio conta como falha: a Mariana nunca age sobre parte da caixa.
- **Rascunhos não enviados são apagados.** Se um envio falha, o rascunho é
  apagado para não ficar na sua pasta de Rascunhos.
- **O nome do remetente é o da caixa.** O email sai com o nome de exibição da
  caixa no Microsoft 365, não com o `persona.name`.

## Problemas comuns

| Sintoma | Solução |
|---|---|
| `Timed out waiting for the browser round-trip` | O navegador não voltou para `localhost:8766`. Confira se nada mais usa a porta e se o redirect URI é `http://localhost:8766` em *Mobile and desktop applications* (não *Web*). |
| `AADSTS50011` (redirect URI diferente) | O mesmo: o endereço e a plataforma precisam bater exatamente. |
| `Need admin approval` | Veja [Se aparecer "Need admin approval"](#se-aparecer-need-admin-approval). |
| `signed in as X, but persona.email is Y` | Rode `mariana microsoft auth` de novo e escolha a conta certa ("Use another account" se o navegador já estiver em outra). |
| `token refresh rejected` | O login venceu (90 dias sem uso) ou foi revogado. Rode `mariana microsoft auth` de novo. |

Para tirar o acesso da Mariana, vá em
[myaccount.microsoft.com](https://myaccount.microsoft.com) → **Apps**, ou
apague o registro do app. Depois apague `data/m365_token.json`.

## Entregabilidade

- **Ative o DKIM** do seu domínio no Microsoft Defender (Email
  authentication → DKIM). Sem ele, o email do Exchange Online não sai
  assinado com o seu domínio.
- **Cuidado com a organização.** O Exchange Online vigia o spam de saída da
  organização inteira. Se você divide com uma empresa, a reputação dela
  depende da sua: mantenha `max_daily_sends` baixo e `require_approval: true`.

## Para desenvolvedores

| Arquivo | O que é |
|---|---|
| `harvey/integrations/microsoft.py` | `MicrosoftProvider` (um `MailProvider`) e `run_auth_flow` |
| `harvey/integrations/mail_provider.py` | Registra `microsoft` em `NATIVE_PROVIDERS` e `get_mail_provider` |
| `harvey/cli.py` | `mariana microsoft auth\|test` |
| `tests/test_microsoft.py` | Graph e login simulados com `httpx.MockTransport`; sem rede |

`get_replies` **levanta** `GraphError` quando a caixa não pode ser lida, em
vez de devolver `[]`. O handler trata isso como leitura falha e o ciclo
segura os envios. Ele devolve a janela inteira de 7 dias ou nada:

- **Todas as páginas.** `limit` é só o tamanho da página (`$top`). A Mariana
  segue o `@odata.nextLink` até o Graph parar de mandar, usando o link
  exatamente como veio. Mensagens repetidas entre páginas voltam uma vez só.
- **Links conferidos antes do token.** O `nextLink` precisa ser
  `https://graph.microsoft.com` (porta padrão), no caminho
  `/v1.0/me/mailFolders/inbox/messages`, com query, sem credenciais,
  fragmento, barra invertida ou caracteres de controle. Link que repete uma
  página anterior é loop. Em qualquer caso a leitura falha sem fazer o pedido.
- **Com limite.** Mais de `MAX_INBOX_PAGES` (40) páginas, ou 2.000 mensagens
  em uma semana no tamanho padrão, faz a leitura falhar em vez de cortar.
- **Dado malformado falha.** Toda resposta do Graph precisa ser um objeto
  JSON; só `202`/`204` (envio, apagar) podem vir vazias.

Limitações: uma caixa com mais de 2.000 mensagens em 7 dias segura os envios
até o volume cair (aumente `MAX_INBOX_PAGES` ou o tamanho da página). Email
que chega durante a leitura pode deslocar o `$skip` e uma mensagem fica para
o ciclo seguinte, que a lê, já que a janela é de 7 dias.

O servidor de retorno do login escuta em `127.0.0.1` e `::1`, porque
`localhost` aponta para os dois e cada navegador tenta um.
