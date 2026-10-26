# Relatos de erro do Gab

Quem instalou o Gab e respondeu **sim** à pergunta única (no instalador ou na primeira vez que abre) manda, sozinho e
anônimo, cada erro da skill que o Gab corrigiu na máquina dele. O dono (Gabriel) recebe na fila privada da VPS dele, corrige
no repositório e todo mundo recebe no próximo auto-update.

**SÓ VPS (regra do usuário, 26/10/2026):** relatos, presets, invenções e apresentações vão APENAS para a fila da VPS
do autor (`/v1/preset`, com a key de licença). A planilha/Formulário Google e o Drive foram desativados. Nunca
recriar planilha ou formulário, nem inventar outro destino (Drive, gws, webhook, e-mail, repositório).

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
  (PRESET.md, gerar.py, kit/*.css|js, index.html, hyperframes.json) em até 4 partes de ~45 mil caracteres (juntadas
  de novo na VPS): cores viram cinza da mesma luminosidade, texto visível vira "Texto", data: URIs e
  libs minificadas saem, binários só na lista. A semelhança compara o código (tags, props do GSAP, eases, técnicas,
  CSS) com os presets/ da skill. Remontar: `presets_vps.py puxar` já junta; à mão, `relatar.py desempacotar <txt> <pasta>`.

  **Varredura (22/10/2026):** o usuário não precisa lembrar de salvar na biblioteca. Toda vez que o Gab abre,
  `relatar.py enviar` primeiro roda `varrer`: acha as pastas novas em `presets/` (criadas nesta máquina, fora do git)
  e os modelos de `biblioteca_motions_local/`, e registra os que mudaram desde a última varredura e são bem
  diferentes do banco. Variação de preset que já existe (cópia com outra cor ou texto) fica de fora.

- **Apresentações** (`tipo` usuario, 22/10/2026): só o nome de quem ACEITOU se apresentar
  (`scripts/comunidade.py`; perguntado uma vez, na 3ª abertura). Sai mesmo sem `"relatos": true`, porque a pessoa
  mandou na hora, mas só isso: erros e motions continuam dependendo do consentimento. Dono vê o nome como `usuario` na fila (`presets_vps.py listar`).

- **Invenções** (`tipo` invencao, 22/10/2026): scripts novos fora do git, `git diff` dos arquivos da skill e o que o
  doctor guardou no stash no update (fora presets, clientes, config e assets). Anonimizado, até 4 partes, sem repetir o
  mesmo conteúdo. No dono: `presets_vps.py puxar` > `~/.claude/ogab_presets_vps/`; incorporar à mão e apagar da fila.

## Fila da VPS (lado do dono)

`scripts/presets_vps.py` (só no Mac do dono, fora do git; usa a key marcada como criador):

1. `listar` (ou `relatos.py fila`): o que chegou, separado em `presets/` e `relatos/` por usuário.
2. `puxar`: baixa tudo e reconstrói em `~/.claude/ogab_presets_vps/` (partes juntadas).
3. Tratar: erro = reproduzir, corrigir no repo, PROCESSO/CHANGELOG, commit+push, `relatos.py resolver`; motion bom =
   `biblioteca_motions.py salvar` com "autor": "comunidade"; fraco ou repetido = só descartar.
4. `apagar <path>` de cada item tratado (ou `limpar` quando a fila inteira foi tratada).

**Dono: ler tudo antes de qualquer commit na skill** (o pre-commit trava; `relatos.py hook`, `relatos.py lido`).

## Como funciona

1. **Na máquina de quem usa** (`scripts/relatar.py`):
   - o Gab corrige algo da skill e roda `relatar.py registrar` (erro, causa, correção e o diff só dos arquivos da skill);
   - o relato é anonimizado ao ser gravado em `~/.claude/ogab_relatos/pendentes/`: caminhos fora da skill viram
     `~/…/*.ext`, saem e-mails, chaves e tokens, parâmetros de link, o nome do usuário e o nome de cada cliente;
   - ao abrir o Gab, `relatar.py enviar` manda os pendentes em segundo plano, **só se `"relatos": true`** no config.
     Sem resposta ou com "não", nada sai da máquina. Mudar: `/ogab config relatos sim|nao`.
2. **No meio**: a fila da VPS do autor (`/v1/preset`). Quem envia só manda: não lista, não lê e não apaga nada da
   fila (essas rotas exigem a key de criador).
3. **No dono** (`/ogab relatos`, `scripts/relatos.py`): o Gab lê a fila (`relatos.py fila`, `presets_vps.py puxar`), agrupa pela
   assinatura, ignora os já resolvidos, corrige no repo, commit+push e `relatos.py resolver <assinatura> <commit>`.
