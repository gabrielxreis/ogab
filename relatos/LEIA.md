# Relatos de erro do Gab

Quem instalou o Gab e respondeu **sim** à pergunta única (no instalador ou na primeira vez que abre) manda, sozinho e
anônimo, cada erro da skill que o Gab corrigiu na máquina dele. O dono (Gabriel) recebe numa planilha privada, corrige
no repositório e todo mundo recebe no próximo auto-update.

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
