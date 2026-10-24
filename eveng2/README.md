# /ogab eveng2: óculos Even Realities G2

O G2 vira monitor do Gab: roteiro no teleprompter da lente, lista de planos como checklist no anel R1 e aviso na lente quando uma etapa termina. Tudo por Bluetooth direto do Mac, sem o app do celular.

Base: [even-g2-protocol](https://github.com/ithinkthisiscool/even-g2-protocol) (MIT, engenharia reversa, não oficial), numa versão fixa (`COMMIT` no `eveng2.py`). Fica fora do git da skill, em `~/.cache/ogab/eveng2/` (`g2/`, `venv/`, `oculos.json`).

## Comandos

```bash
python3 SKILL_DIR/eveng2/eveng2.py instalar                 # uma vez: biblioteca + venv (Python 3.11+)
python3 SKILL_DIR/eveng2/eveng2.py testar                   # sem óculos: 98 testes da biblioteca + os do Gab
python3 SKILL_DIR/eveng2/eveng2.py procurar                 # acha o par de lentes, grava oculos.json
python3 SKILL_DIR/eveng2/eveng2.py status "Render pronto"   # aviso na lente (--segundos 8)
python3 SKILL_DIR/eveng2/eveng2.py teleprompter <pasta>/roteiro.txt [--auto --intervalo 2500] [--largura 28]
python3 SKILL_DIR/eveng2/eveng2.py planos <arquivo.md> [--ficar --gravar]
```

| Pedido | O que o Gab faz |
|---|---|
| `/ogab eveng2` ou "liga o óculos" | `testar`; se não instalado, `instalar`; depois `procurar` |
| "manda o roteiro pro óculos", "vou gravar" | `teleprompter` com o `roteiro.txt` APROVADO da pasta do vídeo, em segundo plano. Marcações `[take...]` e linhas `#` saem sozinhas. `--auto` rola sozinho |
| "lista de planos no óculos", shot list | `planos` com uma linha por plano (`- [ ] plano`, `1. plano` ou texto). Até 20. `--ficar --gravar` escuta o anel e grava `[x]` de volta no arquivo |
| aviso de etapa | `status "<curto>"` quando um render longo acaba, a timeline fica pronta para validar ou o Gab para esperando a pessoa. Só se `config.eveng2.avisos` for `true` |
| "falar com o Gab pelo óculos" | Ainda não é deste módulo: indicar a ponte pronta [g2-channels](https://github.com/Alireza29675/g2-channels) ou [cc-g2](https://github.com/wmoto-ai/cc-g2) (aprovar permissão e mandar voz para a sessão do Claude Code) |

## Antes de conectar (armadilhas)

- **Um aparelho por vez:** a lente conectada ao iPhone para de anunciar e não aparece na busca. Desligar o Bluetooth do iPhone (ou fechar o app Even) antes. Depois de usar, religar o celular para voltar ao app Even.
- **Permissão de Bluetooth do macOS:** sem ela o processo morre calado (SIGABRT). O script mostra `EVENG2_SEM_PERMISSAO_BLUETOOTH`: ligar o app que rodou o comando (Terminal ou Claude) em Ajustes do Sistema > Privacidade e Segurança > Bluetooth e reabrir o app. Se o Claude não aparecer na lista, rodar o comando no Terminal (botão Run do bloco `bash`).
- **No Mac os endereços são UUIDs do CoreBluetooth**, não MAC. `procurar` grava o que o Mac vê; se trocar de Mac, rodar `procurar` de novo.
- **`pip install` do repo não funciona:** o `pyproject.toml` aponta para `src/`, que não existe. Por isso o `instalar` clona a pasta com o nome `g2` e importa direto.
- `tests/test_g2_ble.py` vem com os endereços apagados pelo autor (`GRAB MAC ADDRESS`) e dois testes importam um `_common` não publicado: o `testar` pula esses três arquivos.

## O que já foi visto funcionando

Pela própria biblioteca: conexão, autenticação, página de texto (o `status`) e checklist (`planos`) estão confirmados ao vivo pelo autor. **O teleprompter foi decodificado do app oficial mas nunca testado num óculos real.** Primeiro uso: rodar com `--verbose` e, se o óculos recusar ou não pedir as páginas, registrar o que apareceu (`relatar.py registrar`). A largura de linha também é chute do autor (25 a 30 caracteres): ajustar com `--largura` olhando a lente.
