"""Test de fumée de l'interface : chaque page s'affiche sans exception."""
import pytest
from streamlit.testing.v1 import AppTest

import data_manager as dm

PAGES = ["🧮 Simulation", "📊 Tableau de bord", "⚖️ Comparer des scénarios",
         "🌍 Mon impact citoyen", "📚 Méthodologie et sources", "⚙️ Paramètres"]


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(dm, "DEFAULT_DB_PATH", tmp_path / "app.db")


@pytest.mark.parametrize("page", PAGES)
def test_page_renders(page):
    at = AppTest.from_file("../app.py", default_timeout=30).run()
    at.sidebar.radio[0].set_value(page).run()
    assert not at.exception, at.exception


def test_simulation_flow():
    at = AppTest.from_file("../app.py", default_timeout=30).run()
    at.button[0].click().run()          # « Estimer mon impact »
    assert not at.exception
    assert any("Impact estimé" in m.value for m in at.markdown)
