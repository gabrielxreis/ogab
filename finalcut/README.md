# Gab (/ogab) no Final Cut Pro (Mac, beta)

Camada à parte, igual a `premiere/` e `capcut/`: o método do `SKILL.md` não muda (roteiro, voz, legenda, música, SFX,
takes, lettering, motions, QC). Quando `"editor": "finalcut"` no config (ou o usuário pedir "monta no Final Cut"),
usar o que está aqui onde o `SKILL.md` manda usar `resolve_lib.py`. O que o app expõe e o que já foi testado:
[`ENGENHARIA_REVERSA.md`](ENGENHARIA_REVERSA.md).

> **Status: beta.** Testado em 13/10/2026 (Final Cut Pro Creator Studio 12.2): um vídeo de 63 s do DaVinci
> reconstruído no Final Cut com 24 takes, 18 motions em 2 camadas, 44 áudios e 58 legendas, duração conferida.
> Avisar o usuário que é beta.

## Como o Gab fala com o Final Cut
- **Não há API de edição.** O AppleScript só lê (biblioteca > evento > projeto > sequência: nome e duração).
- **Montagem = FCPXML.** `fcpxml.py` gera o projeto inteiro (linha principal com gaps, camadas, áudios com volume e
  fade, títulos, legenda queimada no estilo do cliente), confere no DTD oficial que vem dentro do app e importa.
- **Ajustes = acessibilidade (AX).** `ax.py` lê a timeline aberta clipe a clipe (tipo, nome, início, fim, camada),
  seleciona clipes e escreve no Inspetor (tamanho, posição, fonte, texto). Com os clipes selecionados, os comandos de
  menu do Final Cut agem neles.

## Regras
1. **Montar UMA vez, depois modificar (regra do usuário, 13/10/2026: "tenta não ficar criando várias timelines,
   modifica o que já existe").** Reimportar FCPXML sempre cria projeto novo. FCPXML só na montagem inicial; correção
   de legenda, posição, tamanho ou texto pelo `ax.py` no projeto aberto. Se precisar refazer tudo, apagar o projeto
   anterior antes (com o usuário).
2. **Biblioteca aberta antes de importar.** Sem biblioteca aberta, o Final Cut pergunta onde importar (painel que só
   clique humano resolve). O usuário cria uma vez (Arquivo > Nova > Biblioteca) e deixa aberta. O `doctor` confere.
3. **Final Cut na mesa (Space) atual.** Em outra mesa as janelas somem da AX (só a barra de menus).
4. **Acessibilidade** liberada para o Terminal/Claude (Ajustes > Privacidade > Acessibilidade) e
   `pyobjc-framework-ApplicationServices` instalado (o `doctor --corrigir` instala).
5. **Medidas do Final Cut:** tamanho e posição de título/legenda numa escala de 1080 de altura. No vertical
   1080x1920, px reais x 1080/1920 (o gerador converte; no `ax.py inspetor` converter à mão).
6. **Material bruto:** take entra como arquivo original e o corte é feito no plano (`de`/`ate`), igual no DaVinci.
7. Conferir depois do import: o AppleScript lê o projeto e a duração tem que bater com o plano.

## Comandos
```bash
python3 SKILL_DIR/finalcut/fcpxml.py plano.json saida.fcpxml --validar --importar
python3 SKILL_DIR/finalcut/ax.py timeline 30        # clipes do projeto aberto (fps da timeline)
```
Formato do `plano.json`: no topo do `fcpxml.py` (`v1`, `camadas`, `audios`, `titulos`, `legenda`, `legenda_preset`,
`legenda_estilo`). Legenda medida de um cliente: `presets/legenda/<cliente>.json`.

```python
import sys, os; sys.path.insert(0, os.path.expanduser("~/.claude/skills/ogab/finalcut")); import ax
it = ax.achar("Title", "texto da legenda", fps=30)   # acha o clipe
ax.selecionar(it)                                     # seleciona na timeline
ax.inspetor("y scrubber", -490.0)                     # escreve no Inspetor (vale para os selecionados)
```

## Ainda não faz (fazer à mão no Final Cut e avisar o usuário)
Isolamento de voz, cor/LUT, transcrição nativa (usar a do DaVinci ou `legendas.py`), cortar no cabeçote e render pelo
Gab. Próximos testes (colar FCPXML no cabeçote, comandos por menu, Custom LUT, Workflow Extension) em
[`ENGENHARIA_REVERSA.md`](ENGENHARIA_REVERSA.md).
