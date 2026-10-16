# Preset GRÁFICO (dado animado)

Barras, linha, rosca ou comparação com o **valor exato** que o cliente aprovou e a **fonte do dado sempre na tela**. O acabamento é o do launch: preto, uma cor de destaque e revelações que freiam no fim.

<img src="exemplo.gif" width="200" alt="Exemplo do preset gráfico (dados fictícios)">

## Regras
- **O número vem da lista de fatos aprovados** (roteiro, `empresa.md` ou o usuário). Nunca inventar nem arredondar "para ficar bonito". O contador termina gravando o texto exato.
- **`fonte` é obrigatória.** O `gerar.py` recusa o plano sem ela. Exemplos: "Fonte: IBGE, 2025" ou "Dados internos da empresa, 2026".
- **Cor:** um destaque na cor da marca (`destaque`, que por padrão é o último item); o resto em cinza.
- **Tamanho para celular:** rótulos de 34-38 px, título grande, fonte de 27 px.

## Tipos
| `tipo` | Para quê | Itens |
|---|---|---|
| `barras` | crescimento, ranking, ano a ano | 2-6 |
| `linha` | evolução no tempo (`zero: false` quando não faz sentido começar do zero) | 3-12 |
| `rosca` | parte do todo; o centro conta o destaque | 2-5 |
| `comparacao` | antes x depois, nós x eles | 2-4 |

## Como fazer
```
python3 gerar.py plano.json <pasta> [--render grafico.mp4 --gif]
```
1. Escrever o `plano.json`. Os campos estão na docstring do `gerar.py`, e há um exemplo em [`exemplo/plano.json`](exemplo/plano.json).
2. Gerar o projeto e passar pelo storyboard (`scripts/storyboard.py <pasta>`), depois parar e esperar a aprovação.
3. Renderizar e rodar `scripts/revisor.py <mp4> --pasta <pasta>` (ver `docs/etapas/revisor.md`).
