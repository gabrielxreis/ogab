# Módulos de efeito: cinema e física (`assets/fx/`, `scripts/fx.py`)

Valem para qualquer motion HyperFrames da /ogab (motion de vídeo, só motion, arte animada, presets).

## Cinema: acabamento cinematográfico

Brilho estourado (bloom), aberração cromática e grão de filme num filtro SVG só, mais vinheta e vazamento de luz
nos cantos. Dá o ar premium de uma vez; testado no stories X-Trader Global (16/10/2026).

```bash
python3 SKILL_DIR/scripts/fx.py cinema <projeto> --nivel sutil|suave|forte [--cor "#ff9a3c"] [--alfa]
python3 SKILL_DIR/scripts/fx.py cinema <projeto> --tirar
```
- **Quando:** `suave` é o padrão para arte animada, abertura, CTA, só motion e vídeo emocional. `sutil` para motion de cutaway sobre o apresentador (não pesa). `forte` para gancho, kinetic e trailer. Interface limpa (preset vitrine, sketch) e motion de dado com número pequeno: sem cinema ou `sutil` (a aberração borra texto fino).
- **Por cliente:** `cinema: suave` (ou `sutil`/`forte`/`não`) e `cinema_cor: "#..."` no `estilo.md`; sem nada, o Gab decide pela tabela acima. A cor do vazamento de luz sai da cor quente/destaque da marca.
- **MOV com alfa (motion por cima do vídeo):** sempre `--alfa`. Liga só o filtro (bloom, aberração e grão ficam dentro do recorte do motion) e desliga vinheta e vazamento, que pintariam a tela inteira.
- **Ajuste fino:** `--bloom --limiar --raio --aberracao --grao --vinheta --vazamento` por cima do nível. O limiar alto (0,76 no suave) evita deixar pele leitosa; vazamento fica nos cantos, longe do rosto.
- **Custo:** render ~40% mais lento e MP4 ~3x maior (o grão vira detalhe). Normal.
- Arte animada: `arte_animada.py montar ... --cinema suave [--cinema-cor "#..."]` já liga.

## Física: cair, empilhar e explodir

matter.js simulado inteiro no carregamento (passo fixo) e gravado em keyframes do GSAP: o HyperFrames pula de quadro em quadro, então física "ao vivo" sairia diferente a cada render.

```bash
python3 SKILL_DIR/scripts/fx.py fisica <projeto>      # copia matter.min.js + fisica.js e liga no <head>
```
No script do motion, depois de criar a `tl`:
```js
const pilha = Fisica.cair(tl, { itens: ".peca", inicio: .9, duracao: 4, chao: 1560, paredes: [70, 1010], atraso: .14, quique: .25 });
Fisica.explodir(tl, { de: pilha, inicio: 5, duracao: 2, ponto: { x: 540, y: 1700 }, forca: 34 });   // some no fim
```
- Cada peça: `position:absolute` com **largura e altura fixas no CSS**. O lugar no CSS é o ponto de partida: para `cair`, acima da tela (`top` negativo, cada uma numa altura) e soltas em ordem (`atraso`). `data-forma="circulo"` vira círculo; o resto, retângulo com o canto do `border-radius`.
- Texto e CTA vêm **depois** das peças no HTML (ficam na frente quando a explosão passa).
- Opções: `gravidade` (1,6 no cair, 0,45 no explodir), `quique`, `atrito`, `ar`, `sumir:false` (explodir sem sumir no fim).
- **Quando usar:** "tudo que você precisa" (pílulas de benefício caindo num chão), "acumular" (moedas, likes, seguidores, pedidos empilhando), "bagunça → solução" (empilha e explode revelando a resposta/CTA), lista de ferramentas/apps, logos de clientes. SFX: impacto leve por peça que bate no chão (pegar os tempos de soltura: `inicio + i*atraso` + a queda) e um whoosh grave na explosão.
- Exemplo completo: `X-Trader/_motions/xtrader-fisica-demo/index.html` (Mac do dono).
