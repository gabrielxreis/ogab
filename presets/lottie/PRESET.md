# LOTTIE (animações para site e app)

Animações de interface em arquivo `.json` leve (1-8 KB) que tocam em qualquer tamanho sem perder qualidade. Funcionam em site (lottie-web, `<lottie-player>`), Webflow, Framer, WordPress, iOS e Android. É uma entrega nova para o cliente que tem site ou app.

<img src="exemplo.gif" width="560" alt="Exemplos de Lottie: carregando, sucesso, curtir, saiba mais">

## Modelos
| Modelo | O que faz | Duração |
|---|---|---|
| `carregando` | arco girando sobre o trilho | 1,2 s em loop |
| `sucesso` | círculo se desenha, o check se traça e assenta | 1,2 s, para no fim |
| `curtir` | coração se enche de cor com pontinhos saindo | 1 s, para no fim |
| `saiba-mais` | botão em pílula com a seta empurrando para a direita | 1,4 s em loop |

## Como fazer
```
python3 lottie.py todos <pasta> --cor "#C4A34F" --cor2 "#F2E2B3"
python3 lottie.py previa <pasta>/carregando.json <pasta>/sucesso.json --gif <pasta>/previa.gif
```
- **Cores:** `--cor` é a cor principal da marca, `--cor2` a de apoio, `--trilho` o fundo do carregando e `--tinta` a seta do botão. `--tamanho 512` e `--fps 60` são o padrão.
- **Regras:**
  - só camadas de forma (sem imagem, fonte ou expressão), para o arquivo ficar leve e funcionar em qualquer player;
  - curvas que freiam no fim, sem quique;
  - cores só da marca.
- **Entrega:** os `.json`, o GIF de prévia e a linha para o desenvolvedor:
  `<lottie-player src="carregando.json" background="transparent" loop autoplay></lottie-player>`
- **Modelo novo:** escrever a função em `lottie.py` (formas: `el`, `rc`, `sh`; animação: `anim([(quadro, valor), ...])`), conferir na prévia e registrar na tabela acima.
