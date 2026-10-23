# Preset LETREIRO (texto gigante atrás da pessoa; id interno "palco")

Família CENA (motor em `presets/cena`). A palavra dita aparece GIGANTE atrás da cabeça e das mãos dele: a pessoa é
recortada do fundo (`cena/recorte.py`, segmentação da Apple, grátis e local) e vai por cima do texto.
Variantes: sans black branca (nome, palavra de impacto), serifa itálica amarela (emoção), com subtítulo pequeno e
espaçado embaixo ("ALUNO · A GRANDE MISSÃO"), desfocada (`"desfocado": true`).

```json
"palco": [{"texto": "JOÃO", "de": 1.0, "ate": 2.6, "sub": "ALUNO · A GRANDE MISSÃO"},
          {"texto": "diferencial", "de": 11.0, "ate": 13.4, "estilo": "serifa", "cor": "#F2D16B"}]
```
Opcionais: `y` (topo, padrão 17% da altura), `tam` (px; padrão cabe em 92% da largura), `cor`.

Regras: 1 palavra (no máximo 2 curtas), 1,5-3 s, entra na hora em que é dita. Funciona melhor com fundo simples e a
cabeça na metade de cima do quadro. Câmera tremendo ou pessoa saindo do quadro: conferir o recorte antes.
Camadas: V1 vídeo · V2 `palco.mov` · V3 `recorte(.._lente).mov`.
