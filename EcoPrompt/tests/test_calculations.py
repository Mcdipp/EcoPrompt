"""Tests unitaires des formules d'EcoPrompt (calculations.py)."""
import math

import pytest

import calculations as calc
import config as cfg


# --- Formules EcoLogits -----------------------------------------------------
def test_gpu_energy_per_token_matches_published_formula():
    # f_E(P=70, B=64) = 1,17e-6 · e^(-1,12e-2·64) · 70 + 4,05e-5
    expected = 1.17e-6 * math.exp(-1.12e-2 * 64) * 70 + 4.05e-5
    assert calc.gpu_energy_per_token_wh(70) == pytest.approx(expected)
    assert calc.gpu_energy_per_token_wh(70) == pytest.approx(8.049e-5, rel=1e-3)


def test_latency_per_token_matches_published_formula():
    expected = 6.78e-4 * 70 + 3.12e-4 * 64 + 1.94e-2
    assert calc.latency_per_token_s(70) == pytest.approx(expected)


@pytest.mark.parametrize("params, gpus", [(8, 1), (39, 2), (70, 4), (141, 8), (405, 16)])
def test_required_gpus_power_of_two(params, gpus):
    # mémoire = 1,2 × P × 2 Go ; GPU de 80 Go ; arrondi à la puissance de 2
    assert calc.required_gpus(params) == gpus


def test_request_energy_70b_400_tokens_hand_computed():
    br = calc.ecologits_request_energy(400, 70, 70, pue=1.2)
    e_gpu = 400 * (1.17e-6 * math.exp(-0.7168) * 70 + 4.05e-5) * 4
    dt = 400 * (6.78e-4 * 70 + 3.12e-4 * 64 + 1.94e-2)
    e_other = dt / 3600 * 1.2 * 1000 * (4 / 8) / 64
    assert br["gpu_wh"] == pytest.approx(e_gpu)
    assert br["server_other_wh"] == pytest.approx(e_other)
    assert br["total_wh"] == pytest.approx((e_gpu + e_other) * 1.2)
    assert br["overhead_wh"] == pytest.approx((e_gpu + e_other) * 0.2)


def test_energy_is_linear_in_output_tokens():
    e1 = calc.ecologits_request_energy(100, 70, 70, 1.2)["total_wh"]
    e2 = calc.ecologits_request_energy(200, 70, 70, 1.2)["total_wh"]
    assert e2 == pytest.approx(2 * e1)
    assert calc.ecologits_request_energy(0, 70, 70, 1.2)["total_wh"] == 0


def test_bigger_model_uses_more_energy():
    small = calc.ecologits_request_energy(400, 8, 8, 1.2)["total_wh"]
    big = calc.ecologits_request_energy(400, 405, 405, 1.2)["total_wh"]
    assert big > small


def test_active_params_cannot_exceed_total():
    with pytest.raises(calc.ValidationError):
        calc.ecologits_request_energy(400, 100, 50, 1.2)


# --- Valeurs de référence ---------------------------------------------------
def test_reference_value_with_included_pue_is_unchanged():
    ref = cfg.REFERENCE_VALUES["gemini_median"]
    br = calc.reference_request_energy(ref, pue=1.5)  # le PUE utilisateur est ignoré
    assert br["total_wh"] == pytest.approx(0.24)
    assert br["it_wh"] == pytest.approx(0.24 / 1.09)


def test_reference_value_without_pue_gets_user_pue():
    ref = cfg.REFERENCE_VALUES["image_gen_lab"]
    br = calc.reference_request_energy(ref, pue=1.2)
    assert br["total_wh"] == pytest.approx(2.907 * 1.2)


# --- CO2 et eau -------------------------------------------------------------
def test_co2_conversion():
    # 1000 Wh = 1 kWh × 473 g/kWh = 473 g
    assert calc.co2_from_energy(1000, 473) == pytest.approx(473)
    assert calc.co2_from_energy(0.24, 94) == pytest.approx(0.02256)


def test_water_formula_li_et_al():
    # 1 kWh serveur, WUE 0,55 + 1,2 × 3,142 = 4,3204 L
    assert calc.water_from_energy(1000, 0.55, 3.142, 1.2) == pytest.approx(4.3204)


def test_water_google_consistency_order_of_magnitude():
    # Google publie 0,26 mL pour 0,24 Wh avec WUE 1,15 L/kWh (sur site)
    litres = calc.water_from_energy(0.24 / 1.09, 1.15, 0.0, 1.09)
    assert litres * 1000 == pytest.approx(0.253, abs=0.01)


# --- Scénario complet -------------------------------------------------------
def test_weekly_conversion():
    assert calc.weekly_request_count(10, "jour") == 70
    assert calc.weekly_request_count(10, "semaine") == 10
    with pytest.raises(calc.ValidationError):
        calc.weekly_request_count(10, "mois")


def test_compute_impact_scaling():
    s = calc.UsageScenario(requests=10, period="jour", output_tokens=400, model_key="moyen",
                           pue=1.2, grid_g_per_kwh=473)
    r = calc.compute_impact(s)
    assert r.weekly_requests == 70
    assert r.weekly_wh == pytest.approx(r.per_request_wh * 70)
    assert r.yearly_wh == pytest.approx(r.weekly_wh * 52)
    assert r.weekly_co2_g == pytest.approx(r.weekly_wh / 1000 * 473)
    assert r.weekly_water_l is not None and r.weekly_water_l > 0


def test_water_can_be_disabled():
    r = calc.compute_impact(calc.UsageScenario(include_water=False))
    assert r.per_request_water_l is None and r.yearly_water_l is None


def test_input_tokens_ignored_by_default_and_weighted_if_requested():
    base = calc.UsageScenario(input_tokens=0, output_tokens=400)
    with_in = calc.UsageScenario(input_tokens=1000, output_tokens=400)
    weighted = calc.UsageScenario(input_tokens=1000, output_tokens=400, input_token_weight=0.1)
    assert calc.compute_impact(with_in).per_request_wh == pytest.approx(
        calc.compute_impact(base).per_request_wh)
    assert calc.compute_impact(weighted).per_request_wh > calc.compute_impact(base).per_request_wh


def test_custom_model_profile():
    s = calc.UsageScenario(model_key="perso", custom_total_params_b=141,
                           custom_active_params_b=39)
    moe = calc.UsageScenario(model_key="moe")
    assert calc.compute_impact(s).per_request_wh == pytest.approx(
        calc.compute_impact(moe).per_request_wh)


# --- Validation -------------------------------------------------------------
@pytest.mark.parametrize("field, value", [
    ("requests", -1), ("input_tokens", -5), ("output_tokens", -1), ("requests", 2.5),
    ("pue", 0.8), ("grid_g_per_kwh", -10), ("wue_onsite", -1), ("model_key", "inconnu"),
    ("method", "magie"), ("requests", "dix"),
])
def test_invalid_inputs_are_rejected(field, value):
    s = calc.UsageScenario(**{field: value})
    with pytest.raises(calc.ValidationError):
        calc.compute_impact(s)


def test_nan_and_bool_rejected():
    with pytest.raises(calc.ValidationError):
        calc.validate_number(float("nan"), "x")
    with pytest.raises(calc.ValidationError):
        calc.validate_number(True, "x")


# --- Outils -----------------------------------------------------------------
def test_relative_reduction_and_equivalent():
    assert calc.relative_reduction(100, 60) == pytest.approx(0.4)
    assert calc.relative_reduction(0, 0) == 0
    assert calc.gemini_median_equivalent(2.4) == pytest.approx(10)


def test_training_share_per_request():
    # 1287 MWh répartis sur 1 milliard de requêtes = 1,287 Wh / requête
    assert calc.training_share_per_request(1287, 1e9) == pytest.approx(1.287)
    with pytest.raises(calc.ValidationError):
        calc.training_share_per_request(1287, 0)


def test_compare_scenarios_returns_one_row_each():
    rows = calc.compare_scenarios([calc.UsageScenario(name="A"),
                                   calc.UsageScenario(name="B", model_key="petit")])
    assert [r["Scénario"] for r in rows] == ["A", "B"]
    assert rows[1]["Énergie / semaine (Wh)"] < rows[0]["Énergie / semaine (Wh)"]


def test_every_parameter_has_a_known_source():
    keys = set(cfg.SOURCES)
    for p in cfg.MODEL_PROFILES.values():
        assert p.source in keys
    for v in cfg.REFERENCE_VALUES.values():
        assert v.source in keys
    for _, _, src in list(cfg.PUE_OPTIONS.values()) + list(cfg.GRID_FACTORS.values()):
        assert src in keys
    for w in cfg.WATER_PROFILES.values():
        assert w.source in keys
