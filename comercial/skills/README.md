# Base de conhecimento

Arquivos Markdown editáveis que dão à Mariana o conhecimento de vendas. Cada agente carrega os arquivos de que precisa antes de decidir.

## Como funciona

Quando um agente roda, ele chama `brain.load_skills_for_agent("nome_do_agente")`, que junta os arquivos certos e coloca no prompt. Ou seja: dá pra mudar o comportamento da Mariana só editando estes arquivos, sem mexer no código.

## Qual agente usa o quê

| Arquivo | Scout | Writer | Handler | Sender | Channels |
|-------|-------|--------|---------|--------|----------|
| `prospecting_tactics.md` | x | | | | |
| `lead_qualification.md` | x | | | | |
| `account_navigation.md` | x | | | | |
| `signal_playbook.md` | x | x | | | |
| `audiovisual_offer.md` | x | x | x | | x |
| `email_frameworks.md` | | x | | x | |
| `sales_methodology.md` | | x | x | | |
| `offer_strategy.md` | | x | x | | |
| `objection_handling.md` | | | x | | |
| `channel_messages.md` | | | | | x |
| `linkedin_outreach.md` | | | | | x |
| `product_knowledge.md` | x | x | x | x | x |
| `competitive_intel.md` | | x | x | | |

## Arquivos que vêm com a Mariana

- **`audiovisual_offer.md`**: quem compra vídeo, gancho por segmento, objeções e briefing para orçar
- **`channel_messages.md`**: WhatsApp, LinkedIn e Instagram por mercado
- **`prospecting_tactics.md`**: buscas avançadas, garimpo em sites, gatilhos, indicações
- **`lead_qualification.md`**: triagem BANT, pontuação de perfil, MEDDIC, critérios de desqualificação
- **`account_navigation.md`**: vários contatos na mesma empresa, por onde entrar, multi-thread
- **`signal_playbook.md`**: como transformar um sinal na primeira linha da mensagem; qual sinal vence quando há vários
- **`email_frameworks.md`**: regras de escrita de email frio, padrões de IA proibidos, dados de taxa de resposta, 5 frameworks (AIDA, PAS, BAB, QVC, 3Ps)
- **`sales_methodology.md`**: ciclo ABC, fluxo da conversa, calibragem de tom, ética
- **`offer_strategy.md`**: escada de ofertas por nível de interesse, fechamento, timing
- **`objection_handling.md`**: método LAARC, 4 tipos de objeção com respostas
- **`linkedin_outreach.md`**: sequência de conexão, modelos de mensagem, limites

## Gerados para você

Criados pelo `mariana onboard` (ou `mariana train <url>`), específicos do seu negócio e fora do git:

- **`product_knowledge.md`**: quem você é, serviços, preços, portfólio por segmento, clientes, quem procurar
- **`competitive_intel.md`**: comparação com concorrentes (quando gerado pelo train)

## Editar ou criar

1. Edite qualquer `.md` desta pasta
2. Vale a partir do próximo ciclo (sem reiniciar)
3. Para um arquivo novo, crie e acrescente o nome no `skill_map` em `harvey/brain.py`
