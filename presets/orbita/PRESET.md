# Preset ÓRBITA (cartões em volta da pessoa)

Família CENA (motor em `presets/cena`). Cartões de vidro escuro (borda clara, cantos 30 px) flutuando em volta dele,
amarelo como destaque. Ficam na camada da frente (`frente.mov`), junto com a legenda DESTAQUE.

Tipos prontos:
| Tipo | O que é |
|---|---|
| `checklist` | título espaçado + itens que recebem check amarelo um a um, no tempo em que são ditos |
| `progresso` | "Seu reel está pronto" com % contando até 100, barra enchendo e pílulas com check |
| `giro` | cartões girando em volta dele (texto ou print de reel `"img"`): atrás passam na altura da cabeça e somem atrás dela (recorte por cima), na frente passam abaixo do queixo; a legenda desce para baixo deles durante o giro |
| `cta` | caixa de comentário com contorno amarelo digitando a palavra ("MISSÃO"), botão enviar pulsando |

Próximos (estudo em `cena/REFERENCIA.md`): prova social (prints de reels inclinados), parede de manchetes, janela do app com passo a passo, recibo de papel
e etiquetas (riscado em vermelho).

```json
"orbita": [{"tipo": "giro", "de": 3.3, "ate": 6.25, "voltas": 0.75,
            "cartoes": [{"texto": "AULAS", "sub": "AO VIVO"}, {"img": "print_reel.jpg"}, {"texto": "CARREIRA"}]},
           {"tipo": "checklist", "de": 14.6, "ate": 19.9, "titulo": "O QUE MUDOU",
            "itens": [["Diferencial na carreira", 15.4], ["Um passo à frente", 17.5]]},
           {"tipo": "progresso", "de": 7.6, "ate": 10.3, "titulo": "Recomendo pra todos", "itens": ["Prática", "Carreira"]},
           {"tipo": "cta", "de": 27.2, "ate": 30, "texto": "MISSÃO", "rotulo": "comenta", "y": 1480}]
```
Posição: `x`, `y`, `w` em px (padrão: canto de cima à esquerda, 55% da largura). Nunca em cima do rosto.
