# Ajudante barato (subagente) para o trabalho mecânico

Regra do usuário (12/10/2026): o vaivém no navegador e as tarefas repetitivas são o que mais gasta tokens. O Gab
**não faz** esse trabalho na conversa principal: decide O QUE fazer e passa para um ajudante mais barato, que executa
e devolve só o resultado.

## Quando delegar (sempre que for lote mecânico já decidido)

| Tarefa | Ajudante | Por quê |
|---|---|---|
| Baixar 2+ takes do Envato, músicas/SFX da Artlist, gerações do Magnific | `Agent` com `model: "sonnet"` | precisa operar o Chrome (Claude in Chrome) |
| Converter mídia (ffmpeg), normalizar áudio, `midia.py`, renomear e mover para a pasta do vídeo | `Agent` com `model: "haiku"` | só terminal |
| Conferir arquivos (existe, duração, fps, resolução, áudio), procurar o que caiu em ~/Downloads | `Agent` com `model: "haiku"` | só terminal |

**Nunca delegar:** roteiro, escolha de take/música/voz, ritmo, onde entra cada motion, conferência final, nada que mexa
na timeline do usuário sem plano fechado, nada que gaste crédito.

## Como passar (modelo de pedido)

O ajudante não vê esta conversa: o pedido tem que ser completo. Rodar em segundo plano (`run_in_background`) e, enquanto
isso, adiantar outra coisa (regra 1i).

**Downloads do Envato (ou Artlist):**
```
Baixe estes arquivos pelo Chrome do usuário (Claude in Chrome; ele já está logado; nunca digite senha nem aceite
termos ou cookies além do necessário). Siga EXATAMENTE a receita de ~/.claude/skills/ogab/navegador/downloads.md,
seção "Envato Elements" (ou "Artlist"). Use browser_batch e screenshots pequenos (scale 0.2).
Itens (link -> nome final):
1. https://elements.envato.com/... -> take_01_cozinha.mp4
2. ...
Depois de cada download, mova o arquivo de ~/Downloads para <pasta do vídeo>/brolls/ com o nome final.
Responda SÓ com: uma linha por item "ok <caminho final> <tamanho>" ou "falhou <item> <motivo curto>". Nada mais.
```

**Conversões / conferência:**
```
No terminal (sem navegador): para cada arquivo de <pasta>, rode <comando exato, ex.: python3 ~/.claude/skills/ogab/scripts/midia.py iphone ARQ>
e confira com ffprobe duração, fps, resolução e se tem áudio. Não apague nenhum original.
Responda SÓ com uma linha por arquivo: "<nome> <duração>s <fps>fps <LxA> <áudio sim/não> <ok|problema>".
```

## Depois que o ajudante volta

- Conferir rápido (um `ls -la` da pasta), sem reler o trabalho dele.
- O que falhou: tentar de novo UMA vez com o ajudante, citando o motivo; se falhar de novo, avisar o usuário em uma linha.
- Seguir com a parte criativa na conversa principal.
