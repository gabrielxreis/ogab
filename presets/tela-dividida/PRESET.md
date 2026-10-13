# Preset TELA DIVIDIDA (Reels de talking head com painel de motion)

Estudado em 13/10/2026 a partir das aulas "Edição Braba com IA" (Edições 01 a 04 e os dois antes/depois). Os vídeos de referência ficam só na máquina (`~/Documents/videos/referencias/edicao-braba/`), nunca no repo.

## Quando usar
- Talking head explicativo ou de opinião, de 40 a 60 s, que cita muita coisa concreta: app, site, número, marca, passo a passo, ferramenta.
- Quando o usuário pede "tela dividida", "split screen", "estilo edição braba" ou "metade motion, metade eu".
- Não usar em vídeo emocional (lá o b-roll em tela cheia funciona melhor) nem quando o rosto precisa da tela toda.

## Layout (1080x1920)
Guia pronta: `python3 layout.py guia` (gera `guia.png`; use como overlay para conferir).

| Zona | Faixa | O que vai |
|---|---|---|
| Painel | 0 a 893 px (46,5 %) | motion do assunto: card de interface, print, logo, número, ícone, recorte |
| Emenda | y 893 | legenda-etiqueta centrada na linha; no fim, linha de progresso fina |
| Apresentador | 893 a 1920 px | rosto com centro em y ≈ 1330, do peito para cima |
| UI do Instagram | 0-220 e 1600-1920 | nada importante (o painel útil é 120 a 800) |

- Painel e apresentador não se sobrepõem: o apresentador é cortado acima da emenda (CropTop) para o painel ficar limpo.
- Fundo do painel: cor do tema (ver abaixo), nunca o vídeo do apresentador borrado.

## Legenda
- Etiqueta branca arredondada com texto preto em negrito, 1 a 3 palavras por vez, centrada na emenda (y 893).
- Palavra-chave em cor de destaque (cor do tema) ou sublinhada. No DaVinci a legenda nativa faz a etiqueta (estilo com fundo branco); a palavra colorida por palavra só via motion/HyperFrames.
- Nas quebras em tela cheia a etiqueta continua na mesma altura.

## Quebras em tela cheia (trilha TELA CHEIA, acima de tudo)
A cada 2,7 a 5,3 s o layout inteiro muda por 1 a 2 s:
- título grande (fundo preto ou branco, palavra em amarelo/cor do tema);
- b-roll ou print em tela cheia;
- card de afirmação na cor da marca citada;
- o apresentador em tela cheia (só zoom, sem o painel) para frase forte.
Dentro do painel o elemento troca a cada 1,5 a 2 s (entra com escala/blur rápido, sai com corte seco).

## Temas observados (escolher 1 por vídeo)
1. **Cor do assunto:** o painel assume a cor da marca de que se fala (ex.: verde do Duolingo), cards brancos de interface.
2. **Preto e amarelo:** fundo preto, destaque amarelo, mockups de interface, objeto 3D pontual (parede com porta amarela), linha de progresso na emenda.
3. **Gravura P&B:** recortes estilo gravura (mão, celular, olho, bússola) sobre preto ou creme, com um acento de cor.
4. **Pastel UI:** cards de interface em tons pastel, lower-third sobre o apresentador e botão de CTA com seta no fim.
Cliente com `estilo.md`: o tema usa as cores da marca; logo e CTA continuam os do cliente.

## Processo (como o Gab monta)
1. Cortes, depois legenda (regra do talking head: cortes > legenda > b-roll).
2. Plano trecho a trecho: para cada frase, o que vai no painel (o objeto concreto citado) e onde entra quebra em tela cheia. Mostrar o plano.
3. Enquadrar o apresentador: `python3 layout.py aplicar "<timeline>"` (mede o rosto com `resolve_lib.medir_rosto` e aplica Zoom, Pan, Tilt e CropTop em todos os pedaços da V1; V1 nunca é apagada). Conferir 1 quadro.
4. Painel: motions HyperFrames 1080x893 (os cards do preset **vitrine** servem direto, `presets/vitrine/kit`), com a duração da fala de cada trecho, na trilha PAINEL em y 0.
5. Quebras em tela cheia na trilha TELA CHEIA (lettering do pacote, b-roll, card).
6. Legenda-etiqueta na emenda (trilha toda em Y da emenda; quando a quebra tem texto embaixo, nada muda: a etiqueta fica na emenda).
7. SFX em cada troca do painel (pop, click de interface, whoosh na tela cheia), música leve, master -14 LUFS.
8. Fim: linha de progresso na emenda nos últimos segundos e CTA (botão com seta) no painel.

## Checklist antes de dizer pronto
- [ ] Rosto inteiro na metade de baixo, nada do apresentador acima da emenda.
- [ ] Nenhum quadro com painel vazio.
- [ ] Troca no painel a cada 1,5 a 2 s e quebra em tela cheia a cada 3 a 5 s.
- [ ] Legenda do começo ao fim, na emenda.
- [ ] Nada importante nas faixas da UI do Instagram.
