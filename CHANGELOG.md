# Novidades do Gab (/ogab)

O Gab mostra aqui o que mudou desde a última vez que você usou (ele se atualiza sozinho ao abrir).
Mais novo em cima. Cada versão é uma linha `## <versão> (<data>)` seguida dos itens.

## 2026.10.12-6 (12/10/2026)
- **Docker não é mais instalado:** o Gab não usa. Se o `hyperframes doctor` avisar "Docker: not found", pode ignorar. Quem já instalou pode manter ou desinstalar, tanto faz.

## 2026.10.12-5 (12/10/2026)
- **Novidades ao abrir:** o Gab se atualiza sozinho e agora mostra o que mudou (é esta mensagem).
- **`/ogab doctor`:** confere a instalação inteira (ferramentas, Docker, DaVinci, Premiere, After Effects, fontes) e corrige sozinho o que der; o que sobrar ele te guia passo a passo. Roda também no fim do instalador e no `/ogab comecar`.
- **Biblioteca de motions:** modelos prontos (lista com checks, contador com barra, frase em duas linhas) que se ajustam ao seu vídeo e às cores do cliente. Cresce a cada motion novo aprovado e chega para você no update.
- **MOGRTs para o Premiere:** cada modelo da biblioteca também vira um template do Premiere, com texto e cores editáveis no Essential Graphics (já instalados pelo instalador).

## 2026.10.12-4 (12/10/2026)
- **Motions no After Effects:** na instalação você escolhe se os motions são automáticos (HyperFrames) ou montados no After Effects como camadas editáveis: cada texto, número, check e cor dá para mudar no AE. Uma camada CONTROLES troca as cores da marca do motion inteiro. Trocar depois: `/ogab config motion aftereffects` ou `hyperframes`.
- **O instalador agora instala tudo** (DaVinci, Premiere e After Effects) em qualquer máquina. As perguntas da instalação só escolhem qual app o Gab usa.

## 2026.10.12-3 (12/10/2026)
- **Docker Desktop instalado automaticamente** (o HyperFrames pede). Se você já tinha instalado o Gab, rode o instalador de novo.
- **Inspiração para motions:** antes de criar um motion novo, o Gab procura referências de movimento numa coleção com mais de 850 vídeos feitos em código.

## 2026.10.12-2 (12/10/2026)
- **Adobe Premiere Pro:** o Gab agora edita também no Premiere 2026 (projeto, sequência, takes, narração, música, SFX, transcrição do próprio Premiere, Enhance Speech e o LUT DO GAB). Na instalação você escolhe DaVinci ou Premiere. Trocar depois: `/ogab config editor premiere` ou `davinci`.
- No Premiere, a legenda (SRT) fica no bin "Legendas": arraste uma vez para a timeline.

## 2026.10.12-1 (12/10/2026)
- **Windows:** o Gab funciona no Windows (instalador próprio em PowerShell). Diferenças em `windows/README.md`.
