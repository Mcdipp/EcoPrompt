"""
calculations.py — Logique de calcul d'EcoPrompt (indépendante de l'interface).

Deux méthodes d'estimation sont proposées :

1. Méthode paramétrique « EcoLogits » (par défaut) : l'énergie d'une requête est
   estimée à partir du nombre de tokens de sortie et du nombre de paramètres du
   modèle, avec les coefficients publiés par EcoLogits (Rincé & Banse, 2025).

2. Méthode « valeur de référence publiée » : une énergie par requête publiée
   (Google 2025, Luccioni et al. 2024) est multipliée par le nombre de requêtes.

Toutes les grandeurs produites sont des ESTIMATIONS : EcoPrompt ne dispose
d'aucune télémétrie sur les serveurs réellement utilisés.

Unités internes : énergie en Wh, CO2 en g CO2e, eau en litres.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass

import config as cfg


class ValidationError(ValueError):
    """Erreur levée lorsqu'une entrée utilisateur est invalide."""


# ---------------------------------------------------------------------------
# Validation des entrées
# ---------------------------------------------------------------------------
def validate_number(value, name: str, minimum: float = 0.0, maximum: float | None = None,
                    allow_zero: bool = True) -> float:
    """Vérifie qu'une valeur est un nombre fini, positif et dans les bornes."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationError(f"« {name} » doit être un nombre.")
    if math.isnan(value) or math.isinf(value):
        raise ValidationError(f"« {name} » doit être un nombre fini.")
    if value < minimum:
        raise ValidationError(f"« {name} » ne peut pas être inférieur à {minimum}.")
    if not allow_zero and value == 0:
        raise ValidationError(f"« {name} » doit être strictement positif.")
    if maximum is not None and value > maximum:
        raise ValidationError(f"« {name} » ne peut pas dépasser {maximum}.")
    return float(value)


def validate_integer(value, name: str, minimum: int = 0, maximum: int | None = None) -> int:
    """Vérifie qu'une valeur est un entier positif dans les bornes."""
    if isinstance(value, bool):
        raise ValidationError(f"« {name} » doit être un entier.")
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    if not isinstance(value, int):
        raise ValidationError(f"« {name} » doit être un entier.")
    validate_number(value, name, minimum, maximum)
    return value


# ---------------------------------------------------------------------------
# Méthode paramétrique EcoLogits
# ---------------------------------------------------------------------------
def gpu_energy_per_token_wh(active_params_b: float,
                            coef: cfg.EcoLogitsCoefficients = cfg.ECOLOGITS) -> float:
    """Énergie d'un GPU par token de sortie (Wh) : f_E(P, B) = α·e^(β·B)·P + γ."""
    p = validate_number(active_params_b, "Paramètres actifs", 0, cfg.MAX_PARAMS_B,
                        allow_zero=False)
    return coef.alpha_e * math.exp(coef.beta_e * coef.batch_size) * p + coef.gamma_e


def latency_per_token_s(active_params_b: float,
                        coef: cfg.EcoLogitsCoefficients = cfg.ECOLOGITS) -> float:
    """Latence par token de sortie (s) : f_L(P, B) = α·P + β·B + γ (repli ML.ENERGY)."""
    p = validate_number(active_params_b, "Paramètres actifs", 0, cfg.MAX_PARAMS_B,
                        allow_zero=False)
    return coef.alpha_l * p + coef.beta_l * coef.batch_size + coef.gamma_l


def required_gpus(total_params_b: float,
                  coef: cfg.EcoLogitsCoefficients = cfg.ECOLOGITS) -> int:
    """Nombre de GPU nécessaires pour charger le modèle (arrondi à la puissance de 2).

    Mémoire du modèle (Go) = 1,2 × P_total × Q / 8, avec Q = 16 bits.
    """
    p = validate_number(total_params_b, "Paramètres totaux", 0, cfg.MAX_PARAMS_B,
                        allow_zero=False)
    memory_gb = coef.memory_overhead * p * coef.quantization_bits / 8
    raw = max(1, math.ceil(memory_gb / coef.gpu_memory_gb))
    return 2 ** math.ceil(math.log2(raw))


def ecologits_request_energy(output_tokens: float, active_params_b: float,
                             total_params_b: float, pue: float,
                             coef: cfg.EcoLogitsCoefficients = cfg.ECOLOGITS) -> dict:
    """Énergie d'UNE requête selon EcoLogits (Wh), décomposée par poste.

    E_GPU          = T_out × f_E(P_actifs) × n_GPU
    ΔT             = T_out × f_L(P_actifs)                (secondes)
    E_serveur\\GPU  = ΔT × W_serveur × (n_GPU / 8) × (1 / B)
    E_serveur      = E_GPU + E_serveur\\GPU               (énergie informatique)
    E_requête      = PUE × E_serveur                      (énergie du centre de données)
    """
    t_out = validate_number(output_tokens, "Tokens de sortie", 0, cfg.MAX_TOKENS)
    pue = validate_number(pue, "PUE", 1.0, 3.0)
    if active_params_b > total_params_b:
        raise ValidationError("Les paramètres actifs ne peuvent pas dépasser les paramètres totaux.")

    n_gpu = required_gpus(total_params_b, coef)
    e_gpu = t_out * gpu_energy_per_token_wh(active_params_b, coef) * n_gpu
    latency_s = t_out * latency_per_token_s(active_params_b, coef)
    # kW × h = kWh → × 1000 pour obtenir des Wh
    e_server_other = (latency_s / 3600) * coef.server_power_kw * 1000 \
        * (n_gpu / coef.gpus_per_server) / coef.batch_size
    e_server = e_gpu + e_server_other
    return {
        "n_gpu": n_gpu,
        "latency_s": latency_s,
        "gpu_wh": e_gpu,
        "server_other_wh": e_server_other,
        "it_wh": e_server,
        "overhead_wh": e_server * (pue - 1),
        "total_wh": e_server * pue,
    }


# ---------------------------------------------------------------------------
# Méthode « valeur de référence »
# ---------------------------------------------------------------------------
def reference_request_energy(ref: cfg.ReferenceValue, pue: float) -> dict:
    """Énergie d'une requête à partir d'une valeur publiée (Wh).

    Si la valeur publiée inclut déjà le PUE du fournisseur, elle est conservée
    telle quelle et l'énergie informatique est obtenue en divisant par ce PUE.
    Sinon, le PUE choisi par l'utilisateur est appliqué.
    """
    pue = validate_number(pue, "PUE", 1.0, 3.0)
    if ref.includes_pue:
        it_wh = ref.wh_per_request / ref.pue_included
        total = ref.wh_per_request
    else:
        it_wh = ref.wh_per_request
        total = it_wh * pue
    return {"n_gpu": None, "latency_s": None, "gpu_wh": None, "server_other_wh": None,
            "it_wh": it_wh, "overhead_wh": total - it_wh, "total_wh": total}


# ---------------------------------------------------------------------------
# Conversions énergie → CO2 et eau
# ---------------------------------------------------------------------------
def co2_from_energy(energy_wh: float, grid_g_per_kwh: float) -> float:
    """Émissions (g CO2e) = énergie (kWh) × intensité carbone (g CO2e/kWh)."""
    e = validate_number(energy_wh, "Énergie")
    f = validate_number(grid_g_per_kwh, "Intensité carbone", 0, 2000)
    return e / 1000 * f


def water_from_energy(it_energy_wh: float, wue_onsite: float, wue_offsite: float,
                      pue: float) -> float:
    """Eau consommée (L) = E_serveur (kWh) × [WUE_sur site + PUE × WUE_hors site].

    Formule de Li et al. (2025), reprise par EcoLogits. Le terme hors site
    représente l'eau évaporée pour produire l'électricité du centre de données.
    """
    e = validate_number(it_energy_wh, "Énergie informatique")
    on = validate_number(wue_onsite, "WUE sur site", 0, 20)
    off = validate_number(wue_offsite, "WUE hors site", 0, 50)
    p = validate_number(pue, "PUE", 1.0, 3.0)
    return e / 1000 * (on + p * off)


# ---------------------------------------------------------------------------
# Scénario d'utilisation complet
# ---------------------------------------------------------------------------
@dataclass
class UsageScenario:
    """Description d'une utilisation de l'IA saisie par l'utilisateur."""

    name: str = "Mon scénario"
    requests: int = 10                    # nombre de requêtes par période
    period: str = "jour"                  # "jour" ou "semaine"
    input_tokens: int = 200               # tokens d'entrée moyens par requête
    output_tokens: int = 400              # tokens de sortie moyens par requête
    method: str = "ecologits"             # "ecologits" ou "reference"
    model_key: str = "moyen"              # clé de MODEL_PROFILES ou "perso"
    reference_key: str = "gemini_median"  # clé de REFERENCE_VALUES
    custom_total_params_b: float = 70.0
    custom_active_params_b: float = 70.0
    input_token_weight: float = 0.0       # hypothèse utilisateur (0 = méthode EcoLogits)
    pue: float = 1.20
    grid_g_per_kwh: float = 473.0
    wue_onsite: float = 0.55
    wue_offsite: float = 3.142
    include_water: bool = True


@dataclass
class ImpactResult:
    """Résultats d'estimation (par requête, par semaine, par an)."""

    per_request_wh: float
    per_request_it_wh: float
    per_request_co2_g: float
    per_request_water_l: float | None
    weekly_requests: float
    weekly_wh: float
    weekly_co2_g: float
    weekly_water_l: float | None
    yearly_wh: float
    yearly_co2_g: float
    yearly_water_l: float | None
    breakdown: dict
    method_label: str

    def to_dict(self) -> dict:
        return asdict(self)


def weekly_request_count(requests: int, period: str) -> float:
    """Convertit une fréquence (par jour / par semaine) en requêtes par semaine."""
    n = validate_integer(requests, "Nombre de requêtes", 0, cfg.MAX_REQUESTS)
    if period == "jour":
        return n * cfg.DAYS_PER_WEEK
    if period == "semaine":
        return float(n)
    raise ValidationError("La période doit être « jour » ou « semaine ».")


def resolve_params(s: UsageScenario) -> tuple[float, float]:
    """Retourne (paramètres totaux, paramètres actifs) en milliards."""
    if s.model_key == "perso":
        total = validate_number(s.custom_total_params_b, "Paramètres totaux", 0,
                                cfg.MAX_PARAMS_B, allow_zero=False)
        active = validate_number(s.custom_active_params_b, "Paramètres actifs", 0,
                                 cfg.MAX_PARAMS_B, allow_zero=False)
        return total, active
    if s.model_key not in cfg.MODEL_PROFILES:
        raise ValidationError(f"Profil de modèle inconnu : {s.model_key}")
    prof = cfg.MODEL_PROFILES[s.model_key]
    return prof.total_params_b, prof.active_params_b


def compute_impact(s: UsageScenario) -> ImpactResult:
    """Calcule l'impact estimé d'un scénario d'utilisation."""
    weekly_n = weekly_request_count(s.requests, s.period)
    t_in = validate_integer(s.input_tokens, "Tokens d'entrée", 0, cfg.MAX_TOKENS)
    t_out = validate_integer(s.output_tokens, "Tokens de sortie", 0, cfg.MAX_TOKENS)
    w_in = validate_number(s.input_token_weight, "Poids des tokens d'entrée", 0, 1)

    if s.method == "ecologits":
        total_b, active_b = resolve_params(s)
        # Hypothèse optionnelle : les tokens d'entrée comptent pour une fraction w_in
        # d'un token de sortie. Par défaut w_in = 0, comme dans EcoLogits.
        effective_tokens = t_out + w_in * t_in
        br = ecologits_request_energy(effective_tokens, active_b, total_b, s.pue)
        label = "Méthode paramétrique EcoLogits (estimation)"
    elif s.method == "reference":
        if s.reference_key not in cfg.REFERENCE_VALUES:
            raise ValidationError(f"Valeur de référence inconnue : {s.reference_key}")
        ref = cfg.REFERENCE_VALUES[s.reference_key]
        br = reference_request_energy(ref, s.pue)
        label = f"Valeur publiée : {ref.label}"
    else:
        raise ValidationError("Méthode de calcul inconnue.")

    per_wh = br["total_wh"]
    per_co2 = co2_from_energy(per_wh, s.grid_g_per_kwh)
    # PUE effectivement intégré à l'énergie totale (celui du fournisseur si la valeur
    # publiée l'inclut déjà, sinon celui choisi par l'utilisateur).
    effective_pue = per_wh / br["it_wh"] if br["it_wh"] > 0 else s.pue
    per_water = (water_from_energy(br["it_wh"], s.wue_onsite, s.wue_offsite, effective_pue)
                 if s.include_water else None)

    def scale(x, k):
        return None if x is None else x * k

    yearly_n = weekly_n * cfg.WEEKS_PER_YEAR
    return ImpactResult(
        per_request_wh=per_wh, per_request_it_wh=br["it_wh"], per_request_co2_g=per_co2,
        per_request_water_l=per_water, weekly_requests=weekly_n,
        weekly_wh=per_wh * weekly_n, weekly_co2_g=per_co2 * weekly_n,
        weekly_water_l=scale(per_water, weekly_n),
        yearly_wh=per_wh * yearly_n, yearly_co2_g=per_co2 * yearly_n,
        yearly_water_l=scale(per_water, yearly_n),
        breakdown=br, method_label=label)


# ---------------------------------------------------------------------------
# Outils de comparaison et de contexte
# ---------------------------------------------------------------------------
def compare_scenarios(scenarios: list[UsageScenario]) -> list[dict]:
    """Calcule l'impact hebdomadaire et annuel de plusieurs scénarios."""
    rows = []
    for s in scenarios:
        r = compute_impact(s)
        rows.append({
            "Scénario": s.name,
            "Requêtes / semaine": r.weekly_requests,
            "Énergie / requête (Wh)": r.per_request_wh,
            "Énergie / semaine (Wh)": r.weekly_wh,
            "CO₂e / semaine (g)": r.weekly_co2_g,
            "Eau / semaine (L)": r.weekly_water_l,
            "Énergie / an (kWh)": r.yearly_wh / 1000,
            "CO₂e / an (kg)": r.yearly_co2_g / 1000,
            "Eau / an (L)": r.yearly_water_l,
        })
    return rows


def relative_reduction(baseline: float, alternative: float) -> float:
    """Réduction relative (0–1) d'un scénario alternatif par rapport à une référence."""
    b = validate_number(baseline, "Valeur de référence")
    a = validate_number(alternative, "Valeur alternative")
    if b == 0:
        return 0.0
    return (b - a) / b


def gemini_median_equivalent(energy_wh: float) -> float:
    """Exprime une énergie en nombre de « requêtes médianes Gemini » (0,24 Wh, Google 2025)."""
    e = validate_number(energy_wh, "Énergie")
    return e / cfg.REFERENCE_VALUES["gemini_median"].wh_per_request


def training_share_per_request(training_energy_mwh: float, total_requests: float) -> float:
    """Part d'énergie d'entraînement attribuée à une requête (Wh) — CALCUL ILLUSTRATIF.

    Le nombre total de requêtes servies pendant la vie d'un modèle n'est pas publié :
    il s'agit d'une hypothèse de l'utilisateur.
    """
    e = validate_number(training_energy_mwh, "Énergie d'entraînement", 0, 1e9)
    n = validate_number(total_requests, "Nombre total de requêtes", 0, 1e15, allow_zero=False)
    return e * 1e6 / n
