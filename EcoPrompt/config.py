"""
config.py — Paramètres configurables d'EcoPrompt et leurs références bibliographiques.

Principe : AUCUNE valeur numérique n'est utilisée dans les calculs sans être
rattachée à une source (clé de SOURCES). Chaque paramètre précise :
  - sa valeur et son unité,
  - sa nature : "mesuré" (télémétrie ou mesure instrumentée publiée),
    "estimé" (modèle ou hypothèse publiée), ou "convention" (choix
    pédagogique propre à EcoPrompt, non scientifique),
  - la source, la date et la méthodologie.

Les valeurs ont été vérifiées le 6 novembre 2026 sur les documents originaux.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# 1. Bibliographie (identifiants utilisés dans tout le projet)
# ---------------------------------------------------------------------------
SOURCES: dict[str, dict[str, str]] = {
    "ecologits": {
        "citation": "Rincé, S. & Banse, A. (2025). EcoLogits: Evaluating the Environmental "
                    "Impacts of Generative AI. Journal of Open Source Software, 10(111), 7471.",
        "url": "https://ecologits.ai/latest/methodology/llm_inference/",
        "doi": "10.21105/joss.07471",
        "date": "2025 (page consultée le 06/11/2026)",
        "type": "Méthode d'estimation open source (régression sur mesures ML.ENERGY / LLM-Perf)",
    },
    "google2025": {
        "citation": "Elsworth, C. et al. (2025). Measuring the environmental impact of delivering "
                    "AI at Google Scale. arXiv:2508.15734.",
        "url": "https://arxiv.org/abs/2508.15734",
        "date": "21/08/2025 (données de mai 2025)",
        "type": "Télémétrie de production publiée par le fournisseur (non auditée par un tiers)",
    },
    "luccioni2024": {
        "citation": "Luccioni, A. S., Jernite, Y. & Strubell, E. (2024). Power Hungry Processing: "
                    "Watts Driving the Cost of AI Deployment? ACM FAccT 2024. arXiv:2311.16863.",
        "url": "https://arxiv.org/abs/2311.16863",
        "date": "2024",
        "type": "Mesure expérimentale (CodeCarbon, nœud 8×A100-80GB, AWS)",
    },
    "li2025": {
        "citation": "Li, P., Yang, J., Islam, M. A. & Ren, S. (2025). Making AI Less 'Thirsty': "
                    "Uncovering and Addressing the Secret Water Footprint of AI Models. "
                    "Communications of the ACM (accepté). arXiv:2304.03271v5.",
        "url": "https://arxiv.org/abs/2304.03271",
        "date": "v5 du 26/03/2025",
        "type": "Modèle d'estimation (WUE sur site + intensité hydrique de l'électricité)",
    },
    "patterson2021": {
        "citation": "Patterson, D. et al. (2021). Carbon Emissions and Large Neural Network "
                    "Training. arXiv:2104.10350.",
        "url": "https://arxiv.org/abs/2104.10350",
        "date": "2021",
        "type": "Estimation (données partielles fournies par OpenAI + moyenne réseau US)",
    },
    "luccioni2023": {
        "citation": "Luccioni, A. S., Viguier, S. & Ligozat, A.-L. (2023). Estimating the Carbon "
                    "Footprint of BLOOM, a 176B Parameter Language Model. JMLR 24(253). "
                    "arXiv:2211.02001.",
        "url": "https://arxiv.org/abs/2211.02001",
        "date": "2022–2023",
        "type": "Mesure (énergie de calcul) + estimation (fabrication, inactivité)",
    },
    "mistral2025": {
        "citation": "Mistral AI, Carbone 4, ADEME (2025). Our contribution to a global "
                    "environmental standard for AI (ACV de Mistral Large 2, méthodologie "
                    "AFNOR Frugal AI, revue par Resilio et Hubblo).",
        "url": "https://mistral.ai/news/our-contribution-to-a-global-environmental-standard-for-ai",
        "date": "22/07/2025",
        "type": "Analyse de cycle de vie (ISO 14040/44), « première approximation »",
    },
    "iea2025": {
        "citation": "Agence internationale de l'énergie (2025). Energy and AI. Chiffres repris "
                    "par Scientific American, 10/04/2025.",
        "url": "https://www.iea.org/reports/energy-and-ai",
        "date": "10/04/2025",
        "type": "Rapport d'organisme public (estimation et projection)",
    },
    "ember2025": {
        "citation": "Ember (2025). Global Electricity Review 2025, chap. 3.3.",
        "url": "https://ember-energy.org/latest-insights/global-electricity-review-2025/",
        "date": "08/04/2025 (données 2024)",
        "type": "Statistique (intensité des émissions de la production électrique)",
    },
    "rte2024": {
        "citation": "RTE (2025). Bilan électrique 2024 — Émissions.",
        "url": "https://analysesetdonnees.rte-france.com/bilan-electrique-2024/emissions",
        "date": "2025 (données 2024)",
        "type": "Statistique officielle du gestionnaire de réseau français",
    },
    "owid2026": {
        "citation": "Our World in Data, d'après Ember (2026) et Energy Institute (2026). "
                    "Carbon intensity of electricity.",
        "url": "https://ourworldindata.org/grapher/carbon-intensity-electricity",
        "date": "mise à jour du 30/06/2026 (données 2024)",
        "type": "Statistique agrégée (cycle de vie)",
    },
    "meta2024": {
        "citation": "Meta AI (2024). Introducing Llama 3.1 (modèles 8B, 70B, 405B).",
        "url": "https://ai.meta.com/blog/meta-llama-3-1/",
        "date": "23/07/2024",
        "type": "Documentation technique du modèle",
    },
    "mistral2024": {
        "citation": "Mistral AI (2024). Cheaper, Better, Faster, Stronger — Mixtral 8x22B "
                    "(141 Md de paramètres, 39 Md actifs).",
        "url": "https://mistral.ai/news/mixtral-8x22b",
        "date": "17/04/2024",
        "type": "Documentation technique du modèle",
    },
    "ecoprompt": {
        "citation": "Convention pédagogique propre à EcoPrompt (non scientifique).",
        "url": "",
        "date": "2026",
        "type": "Choix de conception, modifiable par l'utilisateur",
    },
}


# ---------------------------------------------------------------------------
# 2. Méthode paramétrique EcoLogits (inférence des LLM)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class EcoLogitsCoefficients:
    """Coefficients publiés par EcoLogits (source : 'ecologits').

    Énergie GPU par token de sortie (Wh/token), P_active en milliards :
        f_E(P, B) = alpha_e * exp(beta_e * B) * P + gamma_e
    Latence par token de sortie (s/token), méthode de repli ML.ENERGY :
        f_L(P, B) = alpha_l * P + beta_l * B + gamma_l
    """

    alpha_e: float = 1.17e-6
    beta_e: float = -1.12e-2
    gamma_e: float = 4.05e-5
    alpha_l: float = 6.78e-4
    beta_l: float = 3.12e-4
    gamma_l: float = 1.94e-2
    batch_size: int = 64              # taille de lot fixée par EcoLogits
    server_power_kw: float = 1.2      # puissance hors GPU d'un serveur p5.48xlarge (kW)
    gpus_per_server: int = 8          # GPU installés par serveur
    gpu_memory_gb: float = 80.0       # mémoire d'un GPU H100 (Go)
    quantization_bits: int = 16       # précision des poids
    memory_overhead: float = 1.2      # facteur 1,2 appliqué à la mémoire du modèle


ECOLOGITS = EcoLogitsCoefficients()


# ---------------------------------------------------------------------------
# 3. Profils de modèles (nombre de paramètres documenté par l'éditeur)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class ModelProfile:
    label: str
    total_params_b: float      # paramètres totaux (milliards)
    active_params_b: float     # paramètres actifs par token (milliards)
    source: str
    note: str = ""


MODEL_PROFILES: dict[str, ModelProfile] = {
    "petit": ModelProfile("Petit modèle — 8 Md de paramètres (ex. Llama 3.1 8B)", 8.0, 8.0,
                          "meta2024"),
    "moyen": ModelProfile("Modèle moyen — 70 Md de paramètres (ex. Llama 3.1 70B)", 70.0, 70.0,
                          "meta2024"),
    "moe": ModelProfile("Mélange d'experts — 141 Md / 39 Md actifs (ex. Mixtral 8x22B)",
                        141.0, 39.0, "mistral2024",
                        "Seule une partie des paramètres est activée pour chaque token."),
    "grand": ModelProfile("Grand modèle — 405 Md de paramètres (ex. Llama 3.1 405B)",
                          405.0, 405.0, "meta2024"),
}

# Les modèles commerciaux fermés (ChatGPT, Gemini, Claude…) ne publient pas leur taille :
# EcoPrompt ne leur attribue donc AUCUN nombre de paramètres. L'utilisateur peut choisir
# un profil de taille comparable ou un profil personnalisé, en tant qu'hypothèse.


# ---------------------------------------------------------------------------
# 4. Valeurs de référence publiées « par requête » (méthode alternative)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class ReferenceValue:
    label: str
    wh_per_request: float      # énergie publiée par requête (Wh)
    includes_pue: bool         # la valeur inclut-elle déjà le surcoût du centre de données ?
    pue_included: float        # PUE intégré à la valeur (1.0 si non inclus)
    nature: str                # "mesuré" ou "estimé"
    source: str
    note: str = ""


REFERENCE_VALUES: dict[str, ReferenceValue] = {
    "gemini_median": ReferenceValue(
        "Requête texte médiane Gemini Apps (Google, mai 2025)", 0.24, True, 1.09, "mesuré",
        "google2025",
        "Périmètre complet : accélérateurs, CPU/DRAM, machines inactives, PUE 1,09. "
        "Valeur médiane d'un seul fournisseur, non auditée par un tiers."),
    "text_gen_lab": ReferenceValue(
        "Génération de texte, modèles ouverts ≤ 11 Md (Luccioni et al., 2024)", 0.047, False,
        1.0, "mesuré", "luccioni2024",
        "Moyenne de 0,047 kWh pour 1 000 requêtes (écart-type 0,03), sans traitement par lots."),
    "image_gen_lab": ReferenceValue(
        "Génération d'image (Luccioni et al., 2024)", 2.907, False, 1.0, "mesuré",
        "luccioni2024",
        "Moyenne de 2,907 kWh pour 1 000 images (écart-type 3,31) : forte variabilité."),
}


# ---------------------------------------------------------------------------
# 5. Efficacité des centres de données (PUE)
# ---------------------------------------------------------------------------
PUE_OPTIONS: dict[str, tuple[float, str, str]] = {
    # clé : (valeur, libellé, source)
    "google": (1.09, "1,09 — moyenne de la flotte Google (2024)", "google2025"),
    "mistral": (1.16, "1,16 — Microsoft, Suède (valeur EcoLogits pour Mistral AI)", "ecologits"),
    "microsoft_us": (1.20, "1,20 — Microsoft, États-Unis (valeur EcoLogits pour OpenAI)",
                     "ecologits"),
}
DEFAULT_PUE_KEY = "microsoft_us"


# ---------------------------------------------------------------------------
# 6. Intensité carbone de l'électricité (gCO2e/kWh)
# ---------------------------------------------------------------------------
GRID_FACTORS: dict[str, tuple[float, str, str]] = {
    "monde": (473.0, "Moyenne mondiale 2024 — 473 g/kWh (Ember)", "ember2025"),
    "ue": (211.2, "Union européenne 2024 — 211 g/kWh (Ember via OWID, cycle de vie)",
           "owid2026"),
    "chili": (259.87, "Chili 2024 — 260 g/kWh (Ember via OWID, cycle de vie)", "owid2026"),
    "france_direct": (21.7, "France 2024 — 21,7 g/kWh (RTE, émissions directes)", "rte2024"),
    "france_acv": (30.2, "France 2024 — 30,2 g/kWh (RTE, cycle de vie)", "rte2024"),
    "google_lb": (345.0, "Flotte Google 2024, location-based — 345 g/kWh", "google2025"),
    "google_mb": (94.0, "Flotte Google 2024, market-based — 94 g/kWh", "google2025"),
}
# Par défaut : moyenne mondiale, car la localisation des serveurs est généralement inconnue.
DEFAULT_GRID_KEY = "monde"


# ---------------------------------------------------------------------------
# 7. Facteurs hydriques (L/kWh)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class WaterProfile:
    label: str
    wue_onsite: float      # eau consommée sur site (refroidissement) par kWh serveur
    wue_offsite: float     # eau consommée pour produire l'électricité (EWIF) par kWh
    source: str
    note: str = ""


WATER_PROFILES: dict[str, WaterProfile] = {
    "li_us": WaterProfile("Moyenne Microsoft États-Unis (Li et al., 2025)", 0.550, 3.142, "li2025",
                          "Sur site 0,55 L/kWh ; hors site (production d'électricité) 3,14 L/kWh."),
    "google_onsite": WaterProfile("Flotte Google, sur site uniquement (2023–2024)", 1.15, 0.0,
                                  "google2025",
                                  "L'eau consommée pour produire l'électricité n'est pas incluse."),
}
DEFAULT_WATER_KEY = "li_us"


# ---------------------------------------------------------------------------
# 8. Références sur l'entraînement (contexte, non additionnées par défaut)
# ---------------------------------------------------------------------------
TRAINING_REFERENCES: list[dict] = [
    {"modele": "GPT-3 (175 Md)", "energie_mwh": 1287.0, "co2_t": 552.0, "eau_m3": 5439.0,
     "nature": "estimé", "source": "patterson2021 / li2025",
     "note": "Eau : 5,4 millions de litres (dont 0,7 sur site), centres Microsoft US (Li et al.)."},
    {"modele": "BLOOM (176 Md)", "energie_mwh": 433.2, "co2_t": 24.7, "eau_m3": None,
     "nature": "mesuré", "source": "luccioni2023",
     "note": "24,7 t (énergie dynamique) ; 50,5 t avec fabrication et inactivité ; "
             "réseau français ≈ 57 gCO2e/kWh."},
    {"modele": "Mistral Large 2", "energie_mwh": None, "co2_t": 20400.0, "eau_m3": 281000.0,
     "nature": "estimé (ACV)", "source": "mistral2025",
     "note": "Entraînement + 18 mois d'utilisation, fabrication incluse."},
]

# Luccioni et al. (2024) : nombre d'inférences de BLOOMz-7B pour égaler
# l'énergie d'entraînement + d'ajustement (51 686 + 7 571 kWh).
BLOOMZ_PARITY_INFERENCES = 592_570_000

# Contexte macroscopique (IEA, 2025)
IEA_DATACENTERS_2024_TWH = 415.0
IEA_DATACENTERS_2024_SHARE = 0.015
IEA_DATACENTERS_2030_TWH = 945.0


# ---------------------------------------------------------------------------
# 9. Seuils d'alerte (CONVENTION PÉDAGOGIQUE, modifiable)
# ---------------------------------------------------------------------------
@dataclass
class AlertThresholds:
    """Seuils hebdomadaires d'énergie estimée (Wh/semaine).

    Ce ne sont PAS des limites scientifiques : ils servent seulement à classer
    une utilisation par rapport à d'autres usages. Exprimés aussi en « requêtes
    médianes Gemini » (0,24 Wh) pour rester interprétables :
        5 Wh ≈ 21 requêtes médianes ; 50 Wh ≈ 208 requêtes médianes.
    """

    green_max_wh: float = 5.0
    orange_max_wh: float = 50.0
    source: str = "ecoprompt"
    extra: dict = field(default_factory=dict)


DEFAULT_THRESHOLDS = AlertThresholds()

# Durées utilisées pour les projections
DAYS_PER_WEEK = 7
WEEKS_PER_YEAR = 52

# Bornes de validation des entrées
MAX_REQUESTS = 100_000
MAX_TOKENS = 2_000_000
MAX_PARAMS_B = 10_000.0

APP_NAME = "EcoPrompt"
APP_SLOGAN = "Comprendre son impact, utiliser l'IA autrement."
