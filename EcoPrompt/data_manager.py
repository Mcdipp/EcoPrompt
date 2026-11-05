"""
data_manager.py — Historique local des simulations (SQLite).

Les données restent sur l'ordinateur de l'utilisateur (fichier data/ecoprompt.db) :
aucune donnée n'est envoyée sur Internet.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import date, datetime
from pathlib import Path

import pandas as pd

DEFAULT_DB_PATH = Path(__file__).resolve().parent / "data" / "ecoprompt.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS simulations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at      TEXT    NOT NULL,
    usage_date      TEXT    NOT NULL,
    scenario        TEXT    NOT NULL,
    method          TEXT    NOT NULL,
    model           TEXT    NOT NULL,
    requests        INTEGER NOT NULL CHECK (requests >= 0),
    period          TEXT    NOT NULL CHECK (period IN ('jour', 'semaine')),
    input_tokens    INTEGER NOT NULL CHECK (input_tokens >= 0),
    output_tokens   INTEGER NOT NULL CHECK (output_tokens >= 0),
    weekly_requests REAL    NOT NULL,
    weekly_wh       REAL    NOT NULL CHECK (weekly_wh >= 0),
    weekly_co2_g    REAL    NOT NULL CHECK (weekly_co2_g >= 0),
    weekly_water_l  REAL,
    alert_level     TEXT    NOT NULL
);
"""


def _connect(db_path: Path | str | None) -> sqlite3.Connection:
    # Le chemin par défaut est résolu à l'appel (permet de l'isoler dans les tests).
    path = Path(db_path) if db_path is not None else DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(path)


def init_db(db_path: Path | str | None = None) -> None:
    """Crée la base et la table si elles n'existent pas encore."""
    with closing(_connect(db_path)) as conn:
        conn.executescript(SCHEMA)
        conn.commit()


def add_simulation(record: dict, db_path: Path | str | None = None) -> int:
    """Enregistre une simulation et renvoie son identifiant."""
    init_db(db_path)
    usage_date = record.get("usage_date") or date.today().isoformat()
    if isinstance(usage_date, date):
        usage_date = usage_date.isoformat()
    values = (
        datetime.now().isoformat(timespec="seconds"), usage_date,
        str(record["scenario"]), str(record["method"]), str(record["model"]),
        int(record["requests"]), str(record["period"]),
        int(record["input_tokens"]), int(record["output_tokens"]),
        float(record["weekly_requests"]), float(record["weekly_wh"]),
        float(record["weekly_co2_g"]),
        None if record.get("weekly_water_l") is None else float(record["weekly_water_l"]),
        str(record["alert_level"]),
    )
    with closing(_connect(db_path)) as conn:
        cur = conn.execute(
            "INSERT INTO simulations (created_at, usage_date, scenario, method, model, requests, "
            "period, input_tokens, output_tokens, weekly_requests, weekly_wh, weekly_co2_g, "
            "weekly_water_l, alert_level) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", values)
        conn.commit()
        return int(cur.lastrowid)


def load_history(db_path: Path | str | None = None) -> pd.DataFrame:
    """Renvoie l'historique complet trié par date d'utilisation."""
    init_db(db_path)
    with closing(_connect(db_path)) as conn:
        df = pd.read_sql_query("SELECT * FROM simulations ORDER BY usage_date, id", conn)
    if not df.empty:
        df["usage_date"] = pd.to_datetime(df["usage_date"])
    return df


def delete_simulation(sim_id: int, db_path: Path | str | None = None) -> None:
    """Supprime une simulation de l'historique."""
    with closing(_connect(db_path)) as conn:
        conn.execute("DELETE FROM simulations WHERE id = ?", (int(sim_id),))
        conn.commit()


def clear_history(db_path: Path | str | None = None) -> None:
    """Vide entièrement l'historique."""
    init_db(db_path)
    with closing(_connect(db_path)) as conn:
        conn.execute("DELETE FROM simulations")
        conn.commit()


def export_csv(db_path: Path | str | None = None) -> bytes:
    """Exporte l'historique au format CSV (UTF-8, séparateur ';' pour Excel FR)."""
    return load_history(db_path).to_csv(index=False, sep=";").encode("utf-8-sig")


def summary(db_path: Path | str | None = None) -> dict:
    """Indicateurs agrégés de l'historique (sommes des valeurs hebdomadaires enregistrées)."""
    df = load_history(db_path)
    if df.empty:
        return {"simulations": 0, "requests": 0.0, "wh": 0.0, "co2_g": 0.0, "water_l": 0.0}
    return {
        "simulations": int(len(df)),
        "requests": float(df["weekly_requests"].sum()),
        "wh": float(df["weekly_wh"].sum()),
        "co2_g": float(df["weekly_co2_g"].sum()),
        "water_l": float(df["weekly_water_l"].fillna(0).sum()),
    }
