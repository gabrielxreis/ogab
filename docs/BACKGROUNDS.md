# BGs animados para gráficos de dados

Gráfico de dados (barras, linhas, pizza, ranking, número contando) **nunca entra direto em cima do take**: vira uma cena de tela cheia com um BG animado atrás e o gráfico centralizado. Os BGs são **criados em código no HyperFrames** (zero crédito, sem IA), recriando os 6 estilos de referência abaixo, que são os que o usuário usa. Os arquivos originais não vêm com a skill; este documento é a receita para reproduzir o visual.

Se o `config.json` tiver `backgrounds.pasta` apontando para uma biblioteca local de BGs, pode usar de lá em vez de gerar.

## Regras comuns a todos

- **Formato:** 1080x1920 (ou o da plataforma), mesmo fps da timeline, **loop de 10 s sem emenda** (o último quadro casa com o primeiro). Render em MP4 opaco (H.264); o gráfico vai por cima em outra camada, ou na mesma composição.
- **Loop perfeito:** todo movimento é função do tempo com período igual à duração (ex.: `sin(2π·t/10)`, partículas com posição `(p0 + v·t) mod altura`). Aleatoriedade só com gerador de números com semente fixa (determinismo do HyperFrames: nada de `Math.random()` solto).
- **Fundo quase preto** (`#050608` a `#0b0d10`), com vinheta suave nas bordas e leve brilho no centro. Na versão clara (só Shadow Grid), fundo `#f2f2f2` a `#fafafa`.
- **Cor de destaque = cor principal da marca** (de `<Empresa>/marca/identidade.md`). Os originais existem em azul (`#2f8cff`), laranja (`#ff8a1f`), vermelho (`#ff3b2f`), verde e branco; trocar pela cor da marca.
- **Atrás de número ou gráfico, o BG é discreto:** brilho médio baixo (o BG não passa de ~20% de luminância onde o dado fica), elementos pequenos e lentos, nada piscando forte no centro. Os estilos de energia alta (Explosion, Vortex) servem para abertura, virada ou CTA, não para leitura de dado.
- Guardar o BG gerado por cliente em `~/Desktop/<Empresa>/marca/bg/<estilo>-<cor>.mp4` e reaproveitar.

## Os 6 estilos

### 1. Shadow Grid (discreto, o padrão para dados)
- **Base:** preto com uma **malha de pontos ou quadradinhos** muito fina e tênue (passo ~12 px, quase invisível), com vinheta.
- **Variações:**
  - **Partículas:** 60 a 90 **triângulos pequenos** (6 a 14 px) cinza-claros com opacidade variada, flutuando devagar em direções aleatórias e girando de leve. Profundidade: os maiores mais nítidos, os menores mais apagados.
  - **Circuito:** **linhas finas de circuito** (traço 2 a 3 px, cinza `#8a8a8a` a 60%) descendo do topo com ramificações em 45° e terminações em forquilha, como trilhas de placa. Animação: as linhas **se desenham** (stroke-dashoffset) e seguem crescendo pela tela.
  - **Grade:** grade quadriculada larga (células ~90 px), linhas finas a 15%, com leve deslocamento ou pulsação.
- **Versão clara:** mesmo desenho em fundo `#f5f5f5` com elementos cinza-escuros, para marcas claras.

### 2. Vibrant Flow (seda, elegante)
- **Base:** preto com **feixes de linhas onduladas paralelas** (10 a 25 linhas, traço 1 a 4 px), na diagonal (de baixo-esquerda para cima-direita), formando uma "seda" ou cabo de fibra.
- **Luz:** cor da marca com **brilho (glow) e desfoque de profundidade**; algumas linhas nítidas e brilhantes na frente, outras desfocadas e escuras atrás. Uma variação tem um "nó" de luz mais forte no meio.
- **Movimento:** as ondas deslizam devagar ao longo da diagonal e ondulam (deslocamento de fase com `sin`), sem cortes.
- Há variações com **quadrados vazados** (contorno de quadrado, 10 a 60 px, cor da marca, em várias profundidades) flutuando, e com **partículas de pontos** em perspectiva (dois planos de poeira de luz convergindo para uma linha de horizonte no centro).

### 3. Jitter (textura, quase parado)
- **Base:** preto ou grafite (`#101010` a `#1a1a1a`) com **textura de filme velho**: arranhões finos verticais e diagonais, poeira e grão.
- **Movimento:** os arranhões e a poeira **trocam de posição a cada 2 a 3 quadros** (efeito tremido de película), com leve oscilação de brilho (flicker de 3% a 6%). Fica quase estático, ótimo atrás de texto ou número grande.
- Sem cor de marca (neutro), ou com um tom bem leve da cor no grão.

### 4. Flames (faíscas, energia média)
- **Base:** preto.
- **Elementos:** **faíscas/brasas em traços curtos** (riscos de 10 a 60 px, motion blur), cor da marca com glow, subindo na diagonal em velocidades diferentes; algumas em primeiro plano grandes e desfocadas, outras pequenas e nítidas ao fundo.
- **Movimento:** fluxo contínuo de baixo para cima, densidade constante (loop pelo módulo da altura). Bom para tema de urgência ou "esquentando".

### 5. Explosion (estouro, energia alta, ~5 s)
- **Base:** preto; no primeiro instante um **clarão** (fumaça/luz cinza que some em ~0,5 s).
- **Elementos:** **estilhaços retangulares e losangos** (5 a 40 px), cor da marca ou branco, explodindo **do centro para fora** em 3D (perspectiva: os que vêm para a frente crescem e saem da tela), girando, com desaceleração.
- **Uso:** virada de assunto, revelação de número ("o resultado é..."), abertura. Não usar atrás de leitura longa.

### 6. Vortex (redemoinho, energia alta, ~6 s)
- **Base:** preto.
- **Elementos:** **cacos triangulares** (cor da marca ou branco, com brilho) girando em espiral e caindo de cima, concentrados na metade de cima da tela, com motion blur e profundidade.
- **Uso:** transição, abertura de bloco, CTA final.

## Qual usar

| Situação | Estilo |
|---|---|
| Gráfico de barras, linha, pizza, ranking, tabela | Shadow Grid (partículas ou grade) ou Jitter |
| Número grande contando | Shadow Grid ou Vibrant Flow |
| Comparação antes/depois, tendência | Vibrant Flow |
| Urgência, prazo, "a janela está fechando" | Flames |
| Revelação, virada, abertura | Explosion |
| Transição, CTA | Vortex |

## Como montar (HyperFrames)

1. Projeto próprio (ex.: `~/Documents/videos/<assunto>-motions/bg-<estilo>/`), composição 1080x1920, `data-duration="10"`.
2. Desenhar em `<canvas>` (partículas, faíscas, estilhaços) ou SVG (circuito, grade, linhas de seda), com uma timeline GSAP pausada que controla um `progress` de 0 a 1 e redesenha a cena por tempo (seek-safe). Glow com `filter: blur()` numa cópia por baixo ou `shadowBlur` no canvas.
3. `npx hyperframes check` e `snapshot --at 0,5,9.9` (conferir que 0 e 9,9 casam para o loop), render `--format mp4`.
4. Na timeline: BG na trilha acima dos takes durante o trecho do dado, gráfico (motion com alfa) por cima, **centralizado** (centro x=540, y=960, ver regra de centralização na seção 8c do SKILL.md). Trecho maior que 10 s: repetir o loop.
