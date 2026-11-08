from .schemas import (
    AuditResult,
    AuditScores,
)


def generate_project_audit(audit):

    project = audit.project

    result = AuditResult(

        executive_summary=(
            f"Audit de développement pour le projet "
            f"{project.title}. "
            "Ce résultat est simulé et ne constitue "
            "pas une analyse IA réelle."
        ),

        scores=AuditScores(
            problem_clarity=4,
            solution=4,
            market=3,
            business_model=3,
            financial_readiness=2,
            team=3,
        ),

        strengths=[
            "Le problème est clairement présenté.",
            "La solution proposée est compréhensible.",
        ],

        risks=[
            "Le modèle financier doit être approfondi.",
            "La validation du marché doit être renforcée.",
        ],

        market_analysis=(
            "Analyse simulée pour le développement."
        ),

        business_model_analysis=(
            "Le modèle économique doit être "
            "davantage documenté."
        ),

        financial_analysis=(
            "Les informations financières doivent "
            "être complétées."
        ),

        recommendations=[
            "Préparer des prévisions financières.",
            "Valider le besoin avec des clients potentiels.",
            "Clarifier la stratégie commerciale.",
        ],

        recommended_support=[
            "financial_expert",
            "mentor",
        ],
    )

    return result.model_dump()