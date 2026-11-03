# Atualizar o CRM do cliente com o Meta Ads

Vale para todo cliente com `clientes/<cliente>/crm.json`. Só leitura da conta de anúncio: nada é criado, pausado ou mudado.

## 1. Puxar pelo MCP do Meta Ads
Conta = `conta_meta` do crm.json. Em todas as chamadas: `advertiser_job: "report_measure_or_look_up"`, `include_additional_context: false`, `reporting_purpose: ["metric_lookup"]`.

a) `ads_get_ad_entities` level `ad_account`, `date_preset: "last_30d"`, `time_increment: "1"`, fields: amount_spent, impressions, link_click, landing_page_view, lead, omni_purchase, omni_purchase_values.
b) level `campaign`, mesmo período, `filtering: [{"field":"amount_spent","operator":"GREATER_THAN","value":["0"]}]`, `sort: "amount_spent_descending"`, `limit: 200`, fields: id, name, effective_status, objective, daily_budget, amount_spent, results, cost_per_result, omni_purchase, ctr.
c) level `ad`, mesmo período, filtro e ordem, `limit: 300`, fields: id, name, campaign_name, adset_name, effective_status, amount_spent, results, cost_per_result, omni_purchase, ctr.
Com `pagination.next_cursor`, buscar as próximas páginas.

## 2. Montar o arquivo `clientes/<cliente>/crm_trafego.json`
Números como número (vírgula vira ponto, nulo vira 0):
```json
{"conta": "<nome da conta> <id>", "fonte": "MCP do Meta Ads (Gab)", "periodo": "last_30d",
 "dias": [{"data": "AAAA-MM-DD", "gasto": 0, "impressoes": 0, "cliques": 0, "visitas": 0, "compras": 0, "valor": 0, "leads": 0}],
 "campanhas": [{"id": "", "nome": "", "status": "<effective_status>", "objetivo": "<objective>", "orcamento": null,
                "gasto": 0, "resultados": 0, "tipo_resultado": "compras", "custo_resultado": null, "ctr": "4,42%", "compras": 0}],
 "anuncios": [{"id": "", "nome": "", "status": "", "campanha": "<campaign_name>", "conjunto": "<adset_name>",
               "gasto": 0, "resultados": 0, "tipo_resultado": "compras", "custo_resultado": null, "ctr": "", "compras": 0}]}
```
- dias: amount_spent.value, impressions, link_click, landing_page_view, omni_purchase, omni_purchase_values.value, lead.
- resultados: `results.values[0].value` (0 se "Not available"); tipo_resultado pelo `results.indicator`: fb_pixel_purchase = compras, profile_visit_view = visitas ao perfil, post_engagement = engajamentos, video_thruplay = ThruPlays, post_interaction_gross = interações, link_click = cliques no link, lead = cadastros.
- custo_resultado: `cost_per_result.value` ou null. orcamento: `daily_budget.value` ou null.

## 3. Enviar
`python3 SKILL_DIR/painel/crm.py enviar --cliente <cliente> clientes/<cliente>/crm_trafego.json` → `CRM_ATUALIZADO` ou `CRM_FALHOU: <erro>`.
