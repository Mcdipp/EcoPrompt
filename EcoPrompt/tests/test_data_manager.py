"""Tests de l'historique SQLite (data_manager.py)."""
import pytest

import data_manager as dm

RECORD = {"usage_date": "2026-11-02", "scenario": "Test", "method": "ecologits",
          "model": "Modèle moyen", "requests": 10, "period": "jour", "input_tokens": 200,
          "output_tokens": 400, "weekly_requests": 70, "weekly_wh": 23.5,
          "weekly_co2_g": 11.1, "weekly_water_l": 0.08, "alert_level": "orange"}


@pytest.fixture()
def db(tmp_path):
    path = tmp_path / "test.db"
    dm.init_db(path)
    return path


def test_add_and_load(db):
    sim_id = dm.add_simulation(RECORD, db)
    df = dm.load_history(db)
    assert sim_id == 1 and len(df) == 1
    assert df.iloc[0]["weekly_wh"] == pytest.approx(23.5)


def test_summary_and_clear(db):
    dm.add_simulation(RECORD, db)
    dm.add_simulation({**RECORD, "weekly_water_l": None}, db)
    s = dm.summary(db)
    assert s["simulations"] == 2
    assert s["wh"] == pytest.approx(47.0)
    assert s["water_l"] == pytest.approx(0.08)
    dm.clear_history(db)
    assert dm.summary(db)["simulations"] == 0


def test_delete_and_export(db):
    a = dm.add_simulation(RECORD, db)
    dm.add_simulation(RECORD, db)
    dm.delete_simulation(a, db)
    assert len(dm.load_history(db)) == 1
    csv = dm.export_csv(db).decode("utf-8-sig")
    assert "weekly_wh" in csv and ";" in csv


def test_database_rejects_negative_values(db):
    import sqlite3
    with pytest.raises(sqlite3.IntegrityError):
        dm.add_simulation({**RECORD, "weekly_wh": -1}, db)
