# Preset DEGRAUS (minimalista)

Arte preto e branco: um ponto sobe degraus e, ao chegar ao topo, a segunda linha da frase aparece. ~4 s. Cenário fixo de propósito: é a linguagem do preset.

<img src="exemplo.gif" width="270" alt="Exemplo do preset DEGRAUS (minimalista)">

Origem: [claude-animation-skills](https://github.com/artemnovitckii/claude-animation-skills) de Artem Novitckii (MIT, `../_reels/LICENSE`), adaptado para a /ogab: 24 qps, textos em pt-BR, kit comum em `presets/_reels/kit`. O guia original em inglês está em `ORIGINAL.md` (campos completos e como trocar a forma).

## Como fazer
1. `plano.json`: `lines` (1 ou 2 linhas curtas), `steps` (3 a 7), `light` (preto no branco). Exemplo em `exemplo/exemplo.json`.
2. `python3 SKILL_DIR/scripts/progresso.py --nome degraus -- python3 gerar.py plano.json`.

## Regras da /ogab que valem aqui
- 24 qps (o kit lê `OGAB_FPS`, padrão 24). Render sempre no painel Terminal com `scripts/progresso.py`.
- Vídeo de marca: trocar a cor de destaque pela oficial do cliente; logo do cliente entra no DaVinci por cima, se pedir.
- Conferir a folha `<saida>.sheet.jpg` (moldura vermelha = área segura do Instagram) antes de mostrar.
- SFX em todo movimento, colocados no DaVinci como no resto da /ogab.
- Frase curta, minúscula, sem travessão.
