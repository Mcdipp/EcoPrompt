"""Tests unitaires du système d'alertes (alerts.py)."""
import pytest

import alerts
import config as cfg
from calculations import ValidationError


@pytest.mark.parametrize("wh, level", [(0, "vert"), (4.99, "vert"), (5, "orange"),
                                       (49.9, "orange"), (50, "rouge"), (10_000, "rouge")])
def test_default_thresholds(wh, level):
    assert alerts.classify(wh) == level


def test_custom_thresholds():
    t = cfg.AlertThresholds(green_max_wh=100, orange_max_wh=1000)
    assert alerts.classify(50, t) == "vert"
    assert alerts.classify(500, t) == "orange"
    assert alerts.classify(5000, t) == "rouge"


def test_incoherent_thresholds_rejected():
    with pytest.raises(ValidationError):
        alerts.classify(10, cfg.AlertThresholds(green_max_wh=50, orange_max_wh=10))
    with pytest.raises(ValidationError):
        alerts.classify(10, cfg.AlertThresholds(green_max_wh=0, orange_max_wh=10))


def test_negative_energy_rejected():
    with pytest.raises(ValidationError):
        alerts.classify(-1)


def test_red_alert_message_and_colors():
    a = alerts.build_alert(120)
    assert a.level == "rouge"
    assert a.message.startswith("Attention")
    assert a.color == alerts.LEVELS["rouge"]["couleur"]
    assert a.gemini_equivalent == pytest.approx(500)
    assert len(a.advice) >= 3


def test_targeted_advice():
    a = alerts.build_alert(60, output_tokens=1200, uses_large_model=True, uses_images=True)
    assert a.advice[0] == alerts.GENERAL_ADVICE[5]          # images en premier
    assert alerts.GENERAL_ADVICE[3] in a.advice              # modèle plus petit
    assert alerts.GENERAL_ADVICE[4] in a.advice              # réponses concises
    assert len(a.advice) == len(set(a.advice))               # pas de doublon


def test_green_alert_has_short_advice():
    a = alerts.build_alert(1)
    assert a.level == "vert" and len(a.advice) == 2
