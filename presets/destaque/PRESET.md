# Preset DESTAQUE (legenda palavra por palavra com palavra-chave em destaque)

Família CENA (motor em `presets/cena`, ver `cena/LEIA.md`). Legenda sempre presente, frase curta (até 3 palavras por
grupo, quebra em pausa e pontuação, nunca no meio de uma ênfase), no meio-baixo do quadro, entrando palavra a palavra.

| Estilo | Visual | No plano (`destaque.enfase`) |
|---|---|---|
| base | sans branca pequena (Poppins ExtraBold 54 px), sombra suave | (padrão) |
| grande | a palavra-chave em Poppins Black amarela, 150 px, entra com mola | `"diferencial": "grande"` |
| serifa | Playfair itálica amarela com brilhinhos ✦ girando | `"a grande missão": "serifa"` |
| pílula | o grupo inteiro numa pílula branca, a palavra com marca-texto amarelo | `"recomendação": "marca"` |
| empilhada | linhas de tamanhos diferentes ("estar / UM PASSO / à frente / mesmo com pouco tempo") | `destaque.empilhadas` |

Escolha das ênfases: 1 por frase no máximo, sempre a palavra que carrega a ideia (nome, número, promessa, a
palavra do CTA). Serifa para emoção/qualidade, grande para impacto/fato, pílula para benefício ("de graça",
"em 7 dias"). Empilhada só para a frase-tese do vídeo (1 ou 2 por vídeo).

```json
"destaque": {"y": 1180, "max_palavras": 3,
  "enfase": {"joão": "grande", "a grande missão": "serifa", "recomendação": "marca"},
  "empilhadas": [{"de": 20.1, "ate": 23.4, "linhas": [["estar", "pequena"], ["um passo", "grande"],
                                                      ["à frente,", "serifa"], ["mesmo com pouco tempo.", "pequena"]]}]}
```
`y` é o topo da legenda em px (blocos altos sobem sozinhos para o centro ficar no mesmo lugar). Legenda abaixo de
lettering/motion continua valendo (regra do Gab): se houver motion no meio-baixo, baixe o `y`.
