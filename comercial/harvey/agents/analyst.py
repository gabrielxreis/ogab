"""Analyst — tracks performance and identifies what's working."""

import json
import logging
from datetime import datetime
from pathlib import Path

from harvey.state import StateManager

logger = logging.getLogger("harvey.analyst")


class Analyst:
    """Analyzes campaign performance, reply rates, and ICP segment conversion.

    Runs during idle cycles and writes a report to data/analytics.json.
    """

    def __init__(self, state: StateManager):
        self.state = state

    async def run(self):
        """Generate analytics report from current pipeline data."""
        logger.info("Analyst: analisando o desempenho...")

        report = {
            "generated_at": datetime.utcnow().isoformat(),
            "pipeline": await self._pipeline_summary(),
            "campaigns": await self._campaign_performance(),
            "intents": await self._intent_breakdown(),
            "stages": await self._stage_breakdown(),
            "insights": [],
        }

        # Generate insights
        report["insights"] = self._generate_insights(report)

        # Write report atomically (temp file + rename) so a crash mid-write
        # never leaves a corrupt analytics.json for the dashboard to choke on.
        data_dir = Path(self.state.db_path).parent
        report_path = data_dir / "analytics.json"
        try:
            tmp_path = report_path.with_suffix(".json.tmp")
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)
            tmp_path.replace(report_path)
            logger.info(f"Analyst: relatório salvo em {report_path}")
        except OSError as e:
            logger.error(f"Analyst: não deu para salvar o relatório: {e}")

        # Log key metrics
        pipeline = report["pipeline"]
        total = sum(pipeline.values())
        if total > 0:
            reply_rate = pipeline.get("replied", 0) / max(pipeline.get("contacted", 0), 1) * 100
            logger.info(
                f"Analyst: {total} leads | "
                f"{pipeline.get('contacted', 0)} contatados | "
                f"Taxa de resposta: {reply_rate:.1f}%"
            )

        for insight in report["insights"]:
            logger.info(f"Analyst: aprendizado: {insight}")

    async def _pipeline_summary(self) -> dict:
        """Count prospects by status."""
        return await self.state.count_prospects_by_status()

    async def _campaign_performance(self) -> list[dict]:
        """Get stats for each campaign."""
        return await self.state.get_campaign_stats()

    async def _intent_breakdown(self) -> dict:
        """Count replies by intent classification."""
        return await self.state.get_intent_distribution()

    async def _stage_breakdown(self) -> dict:
        """Count conversations by sales stage."""
        return await self.state.get_stage_distribution()

    def _generate_insights(self, report: dict) -> list[str]:
        """Derive actionable insights from the data.

        Every insight names the metric, the threshold it crossed, and the
        specific file or config to change — so a human (or Mariana itself)
        can act on it without further analysis.
        """
        insights = []
        pipeline = report.get("pipeline") or {}
        intents = report.get("intents") or {}
        campaigns = report.get("campaigns") or []
        stages = report.get("stages") or {}

        # Pipeline health
        total_new = pipeline.get("new", 0)
        total_queued = pipeline.get("queued", 0)
        total_contacted = pipeline.get("contacted", 0)
        total_replied = pipeline.get("replied", 0)
        total_opted_out = pipeline.get("opted_out", 0)
        total_interested = intents.get("interested", 0)
        total_objections = intents.get("objection", 0)
        total_unsubscribes = intents.get("unsubscribe", 0) + total_opted_out
        total_escalations = intents.get("escalate", 0)

        if total_contacted > 10:
            reply_rate = total_replied / total_contacted * 100
            if reply_rate < 5:
                insights.append(
                    f"AÇÃO: taxa de resposta baixa ({reply_rate:.1f}%, referência 5% a 10%). "
                    "Reescreva o email 1 em prompts/writer.md com uma observação mais afiada "
                    "e teste 2 ou 3 assuntos novos (skills/email_frameworks.md)."
                )
            elif reply_rate > 15:
                insights.append(
                    f"MANTER: taxa de resposta forte ({reply_rate:.1f}%). Não mude as "
                    "mensagens. Aumente a prospecção para alimentar com mais leads."
                )

        # Deliverability / reputation warning — the most urgent signal
        if total_contacted > 10:
            optout_rate = total_unsubscribes / total_contacted * 100
            if optout_rate > 2:
                insights.append(
                    f"URGENTE: {optout_rate:.1f}% pediram para sair (acima de 2% arrisca bloqueio). "
                    "Pause os envios, aperte o perfil de cliente no config e reduza "
                    "o max_daily_sends até a lista melhorar."
                )

        if total_escalations > 0:
            insights.append(
                f"PRECISA DE VOCÊ: {total_escalations} conversa(s) passada(s) para você (irritado/jurídico). "
                "Revise as conversas com status 'needs_human' no painel antes de "
                "enviar de novo para esses domínios."
            )

        # Objection patterns
        total_replies = sum(intents.values()) if intents else 0
        if total_replies > 5:
            objection_pct = total_objections / total_replies * 100
            if objection_pct > 40:
                insights.append(
                    f"AÇÃO: {objection_pct:.0f}% das respostas são objeções. Coloque as "
                    "objeções que se repetem em skills/objection_handling.md e "
                    "skills/audiovisual_offer.md, ou foque em clientes com mais encaixe."
                )

        # Interest conversion
        if total_interested > 0 and total_contacted > 0:
            interest_rate = total_interested / total_contacted * 100
            insights.append(
                f"Taxa de interesse: {interest_rate:.1f}% dos contatados mostraram interesse "
                f"({total_interested} de {total_contacted})."
            )

        # Campaign comparison — name winner AND loser so the fix is obvious
        rated = [c for c in campaigns if c.get("reply_rate") is not None]
        if len(rated) >= 2:
            best = max(rated, key=lambda c: c.get("reply_rate", 0))
            worst = min(rated, key=lambda c: c.get("reply_rate", 0))
            if best.get("reply_rate", 0) > 0 and best is not worst:
                insights.append(
                    f"AÇÃO: '{best.get('name')}' ({best.get('reply_rate')}% de resposta) vence "
                    f"'{worst.get('name')}' ({worst.get('reply_rate', 0)}%). Repita o ângulo e o "
                    "estilo de assunto da vencedora; pause ou reescreva a outra."
                )

        # Pipeline bottlenecks
        if stages.get("engaged", 0) > 3 and stages.get("closing", 0) == 0:
            insights.append(
                "AÇÃO: os leads conversam, mas ninguém chega ao fechamento. Ajuste em "
                "prompts/handler.md para propor horários mais cedo (até a 2ª mensagem)."
            )
        if total_queued > 0 and total_contacted == 0:
            insights.append(
                f"TRAVADO: {total_queued} leads na fila e nada foi enviado. "
                "Confira a aprovação na Outbox, o email de envio (mariana email-check) e os registros."
            )
        if total_new < 10 and total_queued == 0:
            insights.append(
                f"AÇÃO: quase sem leads novos ({total_new}). O Scout roda no próximo ciclo; "
                "se continuar vazio, amplie o perfil de cliente no config ou rode mariana eventos."
            )

        if not insights:
            insights.append("Ainda sem dados suficientes. Continue prospectando e enviando.")

        return insights
