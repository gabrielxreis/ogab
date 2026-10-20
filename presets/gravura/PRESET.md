# Preset GRAVURA (gravura em cobre que se grava sozinha)

Cada frase vira uma **prancha de gravura antiga** que se grava na frente da pessoa: o buril corta o contorno, a forma
ganha volume em três passadas de hachura (contorno, hachura, cruzamento), o título em romanas é cortado letra a letra, a
nota em letra cursiva é escrita num traço só e, no fim, a **aquarela à mão** acende só a parte que importa. Papel creme
com textura, marca da prensa e filete duplo. Entre as frases, a folha seguinte é deitada por cima (nada de fade).

Serve para história, Bíblia, fé, tradição, "você sabia", ciência antiga, herança de marca, mapa, objeto com história.
Casa com A Grande Missão (fecho premium, serifa, papel antigo). Não serve para dado frio, tecnologia ou interface.

Exemplo: `exemplo/exemplo.mp4` (16,5 s: lamparina "A Grande Missão" -> barco "Pelo mar" -> pergaminho "A palavra
escrita"), plano em `exemplo/plano.json`.

Motor de traço: estilo "Copperplate Engraving" do **lemo-opuscar** (MIT, LemoLab), em `kit/engine/`. A gramática
completa do estilo (regras do buril, câmera, som, armadilhas) está em `STYLE_lemo.md`: ler antes de inventar cena nova.

## Como pedir
`/ogab faz um reels no preset gravura sobre <tema>` (ou `preset: gravura` no estilo.md do cliente).

## Processo (o que o Gab faz)
1. Roteiro com 1 ideia por frase. Para cada frase: **um objeto que a pessoa veria numa prancha** (lamparina, barco,
   pergaminho, chave, coroa, mapa, pomba, sino) + título curto (até 3 palavras) + nota cursiva (até 6 palavras).
2. Figura de cada cena, nesta ordem de preferência:
   - `forma` pronta: `lamparina`, `chama`, `pergaminho`, `cruz`, `selo`;
   - `icone` do Iconify, de preferência `game-icons:<nome>` (navios, pombas, coroas, chaves, mapas, ferramentas;
     licença CC BY 3.0: pôr "ícones: game-icons.net" no crédito do post). Buscar em https://icon-sets.iconify.design/game-icons/;
   - `svg`: caminho próprio (forma simples e fechada; a hachura segue o contorno).
3. **Cor só no fim e em uma coisa** (`cor`): a chama, a vela, o mar. A gravura é preto no papel; a cor chegar é um evento.
   Tons de terra e mineral (âmbar `#c98a2b`, azul-cinza `#5b7f8c`, terracota `#a2492e`, verde-mar `#4f7a6a`).
4. `python3 presets/gravura/gerar.py plano.json <pasta>/motions/gravura --render <pasta>/motions/gravura.mp4`
   (~2 s de render por segundo de vídeo). Storyboard e revisor como todo motion (`docs/etapas/revisor.md`); stills
   rápidos: `npx hyperframes snapshot <pasta> --at 1,3,5`.
5. Som (STYLE_lemo.md §7): buril chiando em cada traço (agudo, seco), papel na troca de folha, tic do pincel com água
   quando a cor entra. Música de câmara: cravo, quarteto de cordas, violoncelo solo. Nada de whoosh.

## Regras de bom gosto
- Cena com **pelo menos 4 s** (5-6 s com nota longa): a gravura precisa de tempo para se construir E ser lida.
  O revisor mede o tempo de leitura de cada frase; nota cursiva tem que ficar inteira pelo menos 0,3 s por palavra + 0,5 s.
- Uma figura por prancha, centralizada (`centro_y` 900); título em cima, nota embaixo, nunca texto sobre a figura.
- Nada de fade, deslize de interface ou quique: linha é cortada, texto é cortado ou escrito, cor floresce, folha é deitada.
- Legenda do Gab vai abaixo da nota (ou a nota faz o papel da legenda naquele trecho); conferir que não sobrepõe.
- O aviso de "conteúdo encostado na borda" do revisor é falso neste preset (o papel é claro até a borda): ignorar.
- Não copiar o filme de exemplo do lemo (abelha, prancha VII): a cada vídeo, mudar abertura, figura, ordem e final.
