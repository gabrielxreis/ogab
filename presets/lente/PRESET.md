# Preset LENTE (efeitos de câmera)

Família CENA (motor em `presets/cena`). Mexe no próprio vídeo (e no recorte junto, para o PALCO continuar atrás).

Pronto: **zoom rápido no rosto** (punch-in de ~0,14 s na palavra forte, segura e volta).
```json
"lente": {"zoom": [{"de": 11.0, "ate": 13.5, "escala": 1.25, "centro_y": 0.42}]}
```
`centro_y`: altura do foco (0 topo, 1 base; padrão 0,42, o rosto num enquadramento normal).

Próximos: foco de luz (vinheta escurecendo o fundo), congelar com etiqueta e seta, antes/depois (cortina com
pílulas), transição com zoom e desfoque, encolher o vídeo para dentro de uma janela/celular.
Regra: no máximo 1 zoom a cada 4-5 s, sempre na palavra que merece.
