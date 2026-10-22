# Relatos de erro do Gab

Quem instalou o Gab e respondeu **sim** à pergunta única (no instalador ou na primeira vez que abre) manda, sozinho e
anônimo, cada erro da skill que o Gab corrigiu na máquina dele. O dono (Gabriel) recebe numa planilha privada, corrige
no repositório e todo mundo recebe no próximo auto-update.

## O que chega

- **Erros** (`tipo` bug): o que quebrou, a causa, a correção e o diff dos arquivos da skill.
- **Motions novos** (`tipo` preset): quando alguém salva um motion na biblioteca local (`biblioteca_motions.py salvar`),
  vai a ESTRUTURA do modelo (elementos, tempos, animações, campos), com textos de exemplo genéricos e sem autor; as
  cores nem ficam no modelo. Só com o consentimento novo (`relatos_v` 2, a pergunta cita erros e motions).
  **Só vai motion BEM diferente** (regra do usuário, 13/10/2026): `relatar.py` compara a estrutura (elementos e
  quantidades, animações de entrada/saída, propriedades animadas, repetição, técnicas como câmera, 3D, glow, morph)
  com a biblioteca e com o que já foi enviado; semelhança >= 70% (`LIMIAR_PARECIDO`) não manda. Trocar texto, fonte,
  cor, tempo, posição, uma animação ou o número de linhas não conta como motion novo. A coluna `correcao` traz
  "novidade X% (mais parecido: ...)". Conferir à mão: `relatar.py parecido <pasta do modelo>`.
  **HyperFrames** (`"motor": "hyperframes"`, spec vazio): vai o PACOTE dos arquivos de texto da pasta do modelo
  (PRESET.md, gerar.py, kit/*.css|js, index.html, hyperframes.json) em até 4 relatos de ~45 mil caracteres (a célula
  da planilha aguenta 50 mil): cores viram cinza da mesma luminosidade, texto visível vira "Texto", data: URIs e
  libs minificadas saem, binários só na lista. A semelhança compara o código (tags, props do GSAP, eases, técnicas,
  CSS) com os presets/ da skill. Remontar: colar as partes num .txt e `relatar.py desempacotar <txt> <pasta>`.

  **Varredura (22/10/2026):** o usuário não precisa lembrar de salvar na biblioteca. Toda vez que o Gab abre,
  `relatar.py enviar` primeiro roda `varrer`: acha as pastas novas em `presets/` (criadas nesta máquina, fora do git)
  e os modelos de `biblioteca_motions_local/`, e registra os que mudaram desde a última varredura e são bem
  diferentes do banco. Variação de preset que já existe (cópia com outra cor ou texto) fica de fora.

- **Apresentações** (`tipo` usuario, 22/10/2026): só o nome de quem ACEITOU se apresentar
  (`scripts/comunidade.py`; perguntado uma vez, na 3ª abertura). Sai mesmo sem `"relatos": true`, porque a pessoa
  mandou na hora, mas só isso: erros e motions continuam dependendo do consentimento. Dono vê com `uso.py`.

- **Invenções** (`tipo` invencao, 22/10/2026): scripts novos fora do git, `git diff` dos arquivos da skill e o que o
  doctor guardou no stash no update (fora presets, clientes, config e assets). Anonimizado, até 4 partes, sem repetir o
  mesmo conteúdo. No dono: `banco_presets.py puxar` > `candidatos/<id>/pacote.txt`; incorporar à mão e `recusar`.

## Banco de presets da comunidade (lado do dono)

`scripts/banco_presets.py` (`/ogab presets`) transforma os motions que chegam em presets publicados:

1. `puxar`: lê a planilha (gws logado; ou `--csv` baixado no Chrome em `.../export?format=csv&gid=<aba_gid>`),
   pega só `tipo` preset ainda não resolvido, junta as partes pela assinatura, remonta a pasta em
   `~/.claude/ogab_relatos/candidatos/<id>/` e recalcula a novidade contra o banco ATUAL.
2. `listar` / `ver <id>` / `previa <id>`: avaliar (a prévia sai em cinza e com textos genéricos, de propósito).
3. `aceitar <id> --nome <nome>`: entra em `biblioteca_motions/<nome>/` com "autor": "comunidade", refaz o
   catálogo `biblioteca_motions/CATALOGO.md`, commit + push, `relatos.py resolver`. Todos recebem no auto-update.
   `recusar <id> "motivo"`: marca resolvido e apaga o candidato.
4. Apagar da planilha as linhas que o comando lista.

**Dono: ler tudo antes de qualquer commit na skill** (o pre-commit trava; `relatos.py hook`, `relatos.py lido`).

## Como funciona

1. **Na máquina de quem usa** (`scripts/relatar.py`):
   - o Gab corrige algo da skill e roda `relatar.py registrar` (erro, causa, correção e o diff só dos arquivos da skill);
   - o relato é anonimizado ao ser gravado em `~/.claude/ogab_relatos/pendentes/`: caminhos fora da skill viram
     `~/…/*.ext`, saem e-mails, chaves e tokens, parâmetros de link, o nome do usuário e o nome de cada cliente;
   - ao abrir o Gab, `relatar.py enviar` manda os pendentes em segundo plano, **só se `"relatos": true`** no config.
     Sem resposta ou com "não", nada sai da máquina. Mudar: `/ogab config relatos sim|nao`.
2. **No meio**: o Formulário Google "Relatos do Gab (/ogab)" do dono (`relatos/destino.json`). Quem envia só RESPONDE
   o formulário: não vê as respostas, não edita e não apaga nada, e não tem acesso a nenhum arquivo do dono. Sem
   código, sem chave, sem token. As respostas caem na planilha "Relatos do Gab (respostas)", privada do dono.
3. **No dono** (`/ogab relatos`, `scripts/relatos.py`): o Gab abre `relatos.py url` no Chrome logado, lê, agrupa pela
   assinatura, ignora os já resolvidos, corrige no repo, commit+push e `relatos.py resolver <assinatura> <commit>`.

## Se precisar refazer o formulário

10 perguntas do tipo Parágrafo, nenhuma obrigatória, com estes títulos: `titulo`, `erro`, `causa`, `correcao`,
`diff`, `assinatura`, `versao`, `sistema`, `editor`, `instalacao`. Configurações > Respostas: "Coletar e-mails" =
Não coletar, "Limitar a 1 resposta" desligado. Publicar ("qualquer pessoa com o link" pode responder) e vincular a uma
planilha. Os ids `entry.N` saem do `FB_PUBLIC_LOAD_DATA_` da página `/viewform`; gravar em `relatos/destino.json`.
