# Efeitos extras (biblioteca `presets/efeitos/kit/`, para qualquer motion HyperFrames)

Avaliados em 16/10/2026 a partir da lista "Claude Motion Tips" (withian.notion.site). Só entrou o que o Gab ainda não
tinha; Anime.js ficou de fora (o GSAP já faz) e p5.brush também (textura de nicho, instável quadro a quadro).

| Efeito | Arquivo | O que faz | Quando usar | Exemplo |
|---|---|---|---|---|
| **Física** (Matter.js) | `fisica.js` | palavras/cartões caem, quicam e empilham com gravidade e colisão | lista que "pesa", itens se acumulando, CTA chegando com peso, "tudo desabou" | `exemplos/fisica.gif` |
| **IA pensando** (estilo thinking-orbs) | `orbe.js` | esfera de pontos em 6 estados: pensando, buscando, resolvendo, ouvindo, escrevendo, moldando | vídeo/carrossel sobre IA, agente trabalhando, "carregando", espera | `exemplos/orbe.gif` |
| **ASCII** (como o filtro do PixiJS) | `ascii.js` | texto/imagem/vídeo vira caracteres pela luz, com revelação ou dissolução | tecnologia, código, hacker, "por trás da tela", glitch elegante | `exemplos/ascii.gif` |
| **Lupa** (bulge, WebGL próprio) | `lupa.js` | lente que estufa o texto/imagem e passa por cima | "olha esse detalhe", ler um contrato/print, letra miúda | `exemplos/lupa.gif` |
| **Rabisco** (Rough.js) | `rabisco.js` | círculo, sublinhado, seta, caixa, X e preenchimento HACHURADO à mão, que se desenham e fervem | anotação sobre texto ou vídeo (família CENA), ênfase numa palavra, riscar o errado | `exemplos/rabisco.gif` |

## Como usar numa composição
```html
<script src="https://cdn.jsdelivr.net/npm/matter-js@0.20.0/build/matter.min.js"></script>   <!-- só se usar física -->
<script src="https://cdn.jsdelivr.net/npm/roughjs@4.6.6/bundled/rough.js"></script>         <!-- só se usar rabisco -->
<script src="efeitos.js"></script><script src="fisica.js"></script> ... (copiar os .js do kit para o projeto)
```
- Regra do render: o HyperFrames salta quadros, então tudo é função do tempo. Física, orbe, ASCII e lupa devolvem um
  `draw(...)`; junte todos num `EFX.relogio(tl, dur, t => { ... })` (um tween só, de 0 ao fim). O rabisco escreve
  direto na timeline.
- Texto desenhado em canvas (`EFX.texto_canvas`) é redesenhado quando a fonte carrega; medir palavras do DOM para
  rabiscar só dentro de `document.fonts.ready.then(...)` (ver `exemplo/index.html`).
- Física: ângulo inicial pequeno (±0,06) para cair legível; `de` escalonado em ~0,4 s; `chao` acima da legenda.
- Cores: amarelo/laranja do cliente no destaque; o orbe fica monocromático (branco no escuro, preto no claro).
- Regra do rosto continua valendo: nada disso na frente do rosto.

Exemplo completo: `exemplo/index.html` (os 5 em sequência); `python3 exemplo/fazer.py <pasta>` refaz o vídeo e os GIFs.

## Acervo de referência (para novos presets)
Mais de 400 vídeos feitos com o Claude, com o post de origem e o prompt: galeria Skillry
(https://skillry.dev/ai-videos/opus-5-5) e https://github.com/yihui-dev/awesome-opus5-5-videos. Ao pedir um estilo
novo sem referência, procurar lá um movimento parecido (revelação de texto, transição, ritmo) e estudar quadro a quadro
como foi feito com os reels da família CENA.
