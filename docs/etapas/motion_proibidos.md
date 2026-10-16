# Clichês proibidos nos motions

Regra do usuário (16/10/2026). Estes recursos deixam o motion com cara de template genérico, ou "solto", como na primeira versão do preset launch. O `revisor.py --pasta` procura vários deles no código. O que não dá para achar no código, o revisor de olhos novos confere no critério 7.

## Proibidos (só se o usuário pedir pelo nome)
Exceção: quando o recurso é a assinatura de um preset que o usuário escolheu, ele vale dentro daquele preset. Exemplos: a aurora violeta do GLASS e o prompt digitando do KINETIC. Nesse caso, o aviso do revisor é ignorado.

- **Texto digitando letra a letra (máquina de escrever).**
  - Única exceção: um prompt ou campo de busca que a cena mostra de propósito, como a caixa de comentário do ÓRBITA ou o prompt do KINETIC.
  - Fora isso, a frase entra inteira ou linha a linha por máscara.
- **Brilho (glow) em texto**, com `text-shadow` grande e colorido. Para destacar, usar peso, tamanho ou a cor da marca.
- **Quique e elástico** (`bounce`, `elastic`, `back` exagerado, `cubic-bezier` passando de 1.5). O movimento freia no fim (`expo.out`, `power3.out`) e não volta.
- **Texto em degradê colorido** (arco-íris, roxo para rosa, ciano para roxo).
  - Permitido: degradê metálico da MESMA cor, claro para escuro, como o dourado do launch.
  - Quando usar degradê em texto, ele precisa cobrir acento e descendente (padding e margem negativa).
- **Fundo roxo e azul de "IA"** (degradê violeta para azul ou ciano). O fundo vem da marca do cliente ou é preto, branco ou papel.
- **Movimento linear** no que se vê entrar ou sair.
  - Permitido: câmera contínua bem lenta, contador e rotação constante de fundo.
- **Efeitos empilhados:** desfoque, mais brilho, mais tremida, mais flash, todos no mesmo elemento. No máximo um efeito de entrada por elemento.
- **Elementos de canto genéricos:** "REC", cantoneiras de visor, números de quadro e linhas de HUD sem motivo. Só valem quando a cena é de interface, câmera ou gravação.
- **Emoji como ícone**, cartões coloridos com sombra forte e neon. O ícone é desenhado (SVG) no traço da marca.
- **`Math.random`** sem semente. O render precisa sair igual toda vez, então usar gerador com semente.

## Sempre
- Uma ideia por cena.
- Os 3 primeiros segundos carregam o gancho.
- Texto grande, com tempo de leitura.
- Cores, fontes, logos e prints só do material do cliente.
