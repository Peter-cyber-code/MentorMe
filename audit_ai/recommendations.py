"""
Pont audit IA → recommandations.

Le LLM ne nomme jamais de personnes : il produit des besoins
(`recommended_support`). Seuls des profils RÉELS de la base sont recommandés,
classés par un score déterministe et explicable.
"""
from profiles.models import Profile
from profiles.roles import PRIVILEGED_ROLE_CODES

VALID_SUPPORT_CODES = PRIVILEGED_ROLE_CODES | {"collaborator"}

MAX_PER_CATEGORY = 5

WEIGHTS = {
    "sector": 0.45,
    "verified": 0.25,
    "rating": 0.20,
    "available": 0.10,
}


def _sector_match(profile, sector):
    sector = (sector or "").strip().lower()
    if not sector:
        return False
    for name in profile.expertise.values_list("name", flat=True):
        name = name.lower()
        if name in sector or sector in name:
            return True
    return False


def score_profile(profile, project):
    breakdown = {
        "sector": 1.0 if _sector_match(profile, project.sector) else 0.0,
        "verified": 1.0 if profile.is_verified else 0.0,
        "rating": min(max(profile.user.rating or 0, 0), 5) / 5,
        "available": 1.0 if profile.is_available else 0.0,
    }
    score = sum(WEIGHTS[key] * value for key, value in breakdown.items())
    return round(score, 3), breakdown


def explain(breakdown):
    reasons = []
    if breakdown["sector"]:
        reasons.append("expertise alignée avec votre secteur")
    if breakdown["verified"]:
        reasons.append("profil vérifié")
    if breakdown["rating"] >= 0.8:
        reasons.append("très bien noté")
    if breakdown["available"]:
        reasons.append("disponible")
    return ", ".join(reasons).capitalize() if reasons else "Profil correspondant au besoin"


def build_recommendations(audit):
    """Retourne {code_besoin: [profils scorés]} pour un audit terminé."""
    report = audit.report or {}
    project = audit.project

    needs = [
        code
        for code in report.get("recommended_support", [])
        if code in VALID_SUPPORT_CODES
    ]

    result = {}

    for code in dict.fromkeys(needs):  # sans doublons, ordre conservé
        profiles = (
            Profile.objects
            .filter(roles__code=code, is_available=True)
            .exclude(user=project.owner)
            .select_related("user")
            .prefetch_related("roles", "expertise")
            .distinct()
        )

        scored = []
        for profile in profiles:
            score, breakdown = score_profile(profile, project)
            scored.append((score, breakdown, profile))

        scored.sort(key=lambda item: item[0], reverse=True)

        result[code] = [
            {
                "profile": profile,
                "score": score,
                "score_breakdown": breakdown,
                "reason": explain(breakdown),
            }
            for score, breakdown, profile in scored[:MAX_PER_CATEGORY]
        ]

    return result
