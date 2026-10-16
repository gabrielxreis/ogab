# Preset MARCO (pontos que formam o número)

Milhares de pontos girando num campo escuro se juntam e desenham o número do marco ("10 mil alunos", "1 milhão de views", "+10 anos"). Em seguida, o número nítido assenta por cima, os pontos ficam brilhando atrás e a frase sobe embaixo. Usa a mesma linguagem do POINT CLOUD, então os dois combinam no mesmo vídeo.

<img src="exemplo.gif" width="200" alt="Exemplo do preset marco (número fictício)">

## Regras
- **O número aparece EXATO como está no plano** (`"numero": "10 mil"`) e vem dos fatos aprovados. Quando o número vem de pesquisa, preencher `fonte`.
- **Duração:** 5-7 s. Os pontos se juntam em ~2,4 s; depois o número nítido segura.
- **Letra:** `apple` (Inter Tight 800, padrão), `editorial` ou `cinema` (serifa). O número sai na cor da marca (`destaqueNumero: false` deixa branco).
- **Tecnologia:** os pontos são desenhados em canvas com semente, então o render sai igual toda vez.

## Como fazer
```
python3 gerar.py plano.json <pasta> [--render marco.mp4 --gif]
```
Depois: storyboard, aprovação, render e revisor (`docs/etapas/revisor.md`).
