# Preset PAINEL (apresentação de app, fintech, painel de dados)

Filme curto (15-30 s) que apresenta um app ou serviço com cara de painel: finanças, investimentos, metas, controle de gastos, SaaS com números. Estudado quadro a quadro num reel de lançamento de app de finanças (22/10/2026). O motor é próprio; nada do material da referência é copiado.

<img src="exemplo.gif" width="200" alt="Exemplo do preset painel (marca fictícia Rumo)">

## O que faz o estilo (medido na referência)
- **Fundo navy contínuo** que nunca corta: foco azul no alto à direita, névoa da cor de destaque embaixo à esquerda, grão leve. As cenas trocam por cima dele.
- **Uma cor de destaque** (verde-menta por padrão) em tudo que "está vivo": a linha, a ponta acesa, a barra do dia, o ponto final das frases, o disco que cobre a tela. Um azul e um lilás só dentro dos gráficos.
- **Letra:** grotesca pesada em caixa alta (Inter Tight 800), espaçamento apertado (-0,055 em), linhas coladas, ponto final na cor. Interface em Inter Tight 500-700, sem caixa alta.
- **Linha de gráfico que se desenha** com brilho só na linha (nunca no texto) e uma ponta acesa que corre na frente; a palavra nasce em contorno e se preenche quando a ponta passa.
- **Frase empilhada:** cada linha sobe de dentro de uma máscara com um leve desfoque; o grupo anterior encolhe, fica cinza e sai por cima.
- **Cartões de interface em 3D** (saldo, barras da semana, rosca de gastos, lista com barrinhas, meta, aviso de transação, cartão de crédito) entrando de trás com desfoque, um depois do outro; os números ROLAM até o valor com um borrão que some.
- **Câmera que mergulha** no cartão que importa e depois desliza para o próximo.
- **Disco da cor** que nasce de um ponto e cobre a tela, a palavra fechando o espaçamento (de bem aberto para colado) e o cartão girando em 3D até assentar.
- **Palavras trocando em fila** ("SIMPLES." > "RÁPIDO." > "DO SEU JEITO.") com fio ligando o cartão a uma pílula que conta e ganha o selo "Enviado".
- **Palavra que nasce do chão** e vira gráfico: as letras sobem da linha, a linha segue subindo, a câmera acompanha a ponta com o valor contando e no fim abre mostrando a meta.
- **Caos para controle:** mosaico de cartões inclinado deslizando; as letras de "MENOS CAOS" se espalham e se refazem em "MAIS CONTROLE" enquanto os cartões assentam numa grade reta.
- **Fecho:** ícone que se desenha, frase em duas linhas com a palavra-chave na cor, encolhe com desfoque e vira a marca com a frase dela.
- **Ritmo:** uma cena por ideia, 1,5-3,5 s cada; troca por desfoque (o que sai cresce um pouco e borra), chicote lateral ou disco.

## Quando usar
Serve para: lançamento ou anúncio de app, fintech, banco digital, investimento, controle financeiro, painel/SaaS, "acompanhe seus números", metas, crescimento.
Não serve para: tema emocional ou de fé (frio demais), vídeo de apresentador falando (usar só uma cena como inserto), produto físico sem interface.

## Como pedir
`/ogab faz um motion no preset painel para <produto>` (ou `preset: painel` no `estilo.md` do cliente). Cor da marca em `cor`; se a marca for clara, trocar também `fundo` e `tinta`.

## Processo (o que o Gab faz)
1. Roteiro de 6-10 frases curtas (2-4 palavras por linha) e, se tiver narração, os tempos de cada frase pela transcrição: `dur` de cada cena = início da próxima frase - início desta.
2. Tipo por sentido: gancho com dinheiro/crescimento > `linha`; frase de efeito > `pilha`; "acompanhe", "veja", "tudo num lugar" > `painel` com `foco`; nome do produto > `revela`; três qualidades > `troca`; crescer, render, meta > `cresce`; antes e depois, bagunça > ordem > `caos`; automação, regras, configurações > `regras`; slogan + marca > `fecho`.
3. **Todo número na tela vem do cliente ou é exemplo claro de interface** (saldo, gastos). Dado real (rendimento, %) só com fonte aprovada.
4. Cores da marca (`cor`, `cor2`, `cor3`), nome em `marca` e, se tiver, os 4 últimos dígitos do cartão de exemplo em `final_cartao`.
5. `python3 presets/painel/gerar.py plano.json <pasta>/motions/painel`, depois `centro.py preto`, `storyboard.py` (PARAR para aprovação), render com `--render` e `revisor.py`.
6. Som: sopro curto em cada entrada de cartão, tique suave nos números rolando, swell no disco da cor, grave contido no fecho; música eletrônica limpa com batida marcada, troca de cena NA batida.

## Regras de bom gosto
- No máximo 4 linhas por frase e 14 caracteres por linha; linha longa encolhe sozinha.
- Cada cena com no máximo 5 cartões; o cartão de foco com texto grande o bastante para ler no celular depois do mergulho.
- Brilho só na linha e na ponta, nunca no texto. Nada de quique: tudo freia no fim (`expo.out`, `power3.inOut`).
- Legenda: em cima do painel não vai legenda (o texto já é a fala); com apresentador, o painel entra como inserto e a legenda volta no take dele.

Exemplo: `exemplo/plano.json` (marca fictícia Rumo, 9 cenas, 24 s) e `exemplo.mp4`. Campos de cada tipo: docstring do `gerar.py`.
