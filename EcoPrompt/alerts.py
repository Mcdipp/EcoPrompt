"""
alerts.py — Système d'alertes environnementales d'EcoPrompt.

Les niveaux (vert / orange / rouge) sont attribués à partir de l'énergie
hebdomadaire ESTIMÉE et de seuils configurables. Ces seuils sont une
convention pédagogique : ils ne constituent pas des limites scientifiques
universelles et peuvent être modifiés dans la page « Paramètres ».
"""

from __future__ import annotations

from dataclasses import dataclass

import config as cfg
from calculations import ValidationError, gemini_median_equivalent, validate_number

LEVELS = {
    "vert": {"couleur": "#2E7D32", "fond": "#E8F5E9", "icone": "🌱",
             "titre": "Impact estimé faible"},
    "orange": {"couleur": "#E65100", "fond": "#FFF3E0", "icone": "🍂",
               "titre": "Impact estimé modéré"},
    "rouge": {"couleur": "#C62828", "fond": "#FFEBEE", "icone": "🔥",
              "titre": "Impact estimé élevé"},
}

GENERAL_ADVICE = [
    "Évitez les requêtes inutiles : une recherche classique ou un document déjà ouvert "
    "suffit parfois.",
    "Regroupez les questions liées dans une seule requête bien formulée.",
    "Évitez de régénérer plusieurs fois des contenus similaires : précisez plutôt "
    "votre demande.",
    "Utilisez un modèle plus petit lorsqu'il suffit (reformulation, résumé court, "
    "correction).",
    "Demandez des réponses concises : l'énergie estimée augmente avec le nombre de "
    "tokens générés.",
    "Réservez la génération d'images aux besoins réels : c'est l'usage mesuré le plus "
    "énergivore dans Luccioni et al. (2024).",
]


@dataclass
class Alert:
    level: str
    color: str
    background: str
    icon: str
    title: str
    message: str
    advice: list[str]
    weekly_wh: float
    gemini_equivalent: float


def validate_thresholds(t: cfg.AlertThresholds) -> cfg.AlertThresholds:
    """Vérifie la cohérence des seuils (positifs et croissants)."""
    g = validate_number(t.green_max_wh, "Seuil vert", 0, 1e9, allow_zero=False)
    o = validate_number(t.orange_max_wh, "Seuil orange", 0, 1e9, allow_zero=False)
    if o <= g:
        raise ValidationError("Le seuil orange doit être strictement supérieur au seuil vert.")
    return t


def classify(weekly_wh: float, thresholds: cfg.AlertThresholds = cfg.DEFAULT_THRESHOLDS) -> str:
    """Retourne « vert », « orange » ou « rouge » selon l'énergie hebdomadaire estimée."""
    e = validate_number(weekly_wh, "Énergie hebdomadaire")
    validate_thresholds(thresholds)
    if e < thresholds.green_max_wh:
        return "vert"
    if e < thresholds.orange_max_wh:
        return "orange"
    return "rouge"


def build_alert(weekly_wh: float, output_tokens: int = 0, uses_large_model: bool = False,
                uses_images: bool = False,
                thresholds: cfg.AlertThresholds = cfg.DEFAULT_THRESHOLDS) -> Alert:
    """Construit l'alerte et les conseils adaptés au scénario."""
    level = classify(weekly_wh, thresholds)
    style = LEVELS[level]
    eq = gemini_median_equivalent(weekly_wh)

    if level == "vert":
        message = ("Votre utilisation hebdomadaire estimée reste sous le seuil vert que vous "
                   "avez défini. Continuez à utiliser l'IA de façon raisonnée.")
    elif level == "orange":
        message = ("Votre utilisation cumulée de l'intelligence artificielle représente une "
                   "empreinte environnementale estimée modérée. Quelques ajustements simples "
                   "peuvent la limiter.")
    else:
        message = ("Attention : votre utilisation cumulée de l'intelligence artificielle "
                   "représente une empreinte environnementale estimée élevée au regard des "
                   "seuils choisis. Adoptez une utilisation plus responsable.")

    # Conseils ciblés en premier, puis conseils généraux
    targeted = []
    if uses_images:
        targeted.append(GENERAL_ADVICE[5])
    if uses_large_model:
        targeted.append(GENERAL_ADVICE[3])
    if output_tokens >= 800:
        targeted.append(GENERAL_ADVICE[4])
    advice = targeted + [a for a in GENERAL_ADVICE[:3] if a not in targeted]
    if level == "vert":
        advice = advice[:2]

    return Alert(level=level, color=style["couleur"], background=style["fond"],
                 icon=style["icone"], title=style["titre"], message=message, advice=advice,
                 weekly_wh=weekly_wh, gemini_equivalent=eq)
