"""
app.py — Interface Streamlit d'EcoPrompt.

Lancement :  streamlit run app.py

L'interface ne contient aucune formule : elle appelle calculations.py,
alerts.py et data_manager.py. Tout le texte visible est en français.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import date

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import alerts
import calculations as calc
import config as cfg
import data_manager as dm

# ---------------------------------------------------------------------------
# Configuration générale et style
# ---------------------------------------------------------------------------
st.set_page_config(page_title="EcoPrompt", page_icon="🌿", layout="wide")

GREEN = "#2E7D32"
GREEN_LIGHT = "#E8F5E9"
PALETTE = ["#2E7D32", "#66BB6A", "#A5D6A7", "#00897B", "#81C784", "#C5E1A5"]
# Palette catégorielle validée (séparation daltonisme, contraste ≥ 3:1)
CATEGORICAL = ["#2E7D32", "#1E88E5", "#C77700", "#8E24AA"]

st.markdown(f"""
<style>
  .stApp {{ background: #FFFFFF; }}
  section[data-testid="stSidebar"] {{ background: {GREEN_LIGHT}; }}
  h1, h2, h3 {{ color: {GREEN}; }}
  .eco-hero {{ background: linear-gradient(90deg, {GREEN} 0%, #43A047 100%); color: white;
               padding: 1.1rem 1.4rem; border-radius: 14px; margin-bottom: 1rem; }}
  .eco-hero h1 {{ color: white; margin: 0; font-size: 2rem; }}
  .eco-hero p {{ margin: .2rem 0 0 0; font-style: italic; opacity: .95; }}
  .eco-card {{ border: 1px solid #C8E6C9; border-radius: 12px; padding: .9rem 1rem;
               background: #FAFFFA; height: 100%; }}
  .eco-card .lbl {{ color: #555; font-size: .85rem; }}
  .eco-card .val {{ color: {GREEN}; font-size: 1.55rem; font-weight: 700; }}
  .eco-card .sub {{ color: #777; font-size: .78rem; }}
  .eco-alert {{ border-radius: 12px; padding: 1rem 1.2rem; border-left: 8px solid; }}
  .eco-tag {{ display:inline-block; padding: 2px 8px; border-radius: 10px; font-size: .75rem;
              background: #FFF8E1; color: #8D6E00; border: 1px solid #FFE082; }}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Paramètres de session (modifiables dans la page « Paramètres »)
# ---------------------------------------------------------------------------
def init_state() -> None:
    defaults = {
        "pue_key": cfg.DEFAULT_PUE_KEY, "pue_custom": 1.20,
        "grid_key": cfg.DEFAULT_GRID_KEY, "grid_custom": 473.0,
        "water_key": cfg.DEFAULT_WATER_KEY, "wue_on_custom": 0.55, "wue_off_custom": 3.142,
        "include_water": True, "input_weight": 0.0,
        "green_max": cfg.DEFAULT_THRESHOLDS.green_max_wh,
        "orange_max": cfg.DEFAULT_THRESHOLDS.orange_max_wh,
        "last_scenario": None,
    }
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)
        # Streamlit efface l'état d'un widget non affiché : on le réaffecte à chaque
        # exécution pour conserver les paramètres lors du changement de page.
        st.session_state[k] = st.session_state[k]


def current_pue() -> float:
    k = st.session_state.pue_key
    return st.session_state.pue_custom if k == "perso" else cfg.PUE_OPTIONS[k][0]


def current_grid() -> float:
    k = st.session_state.grid_key
    return st.session_state.grid_custom if k == "perso" else cfg.GRID_FACTORS[k][0]


def current_water() -> tuple[float, float]:
    k = st.session_state.water_key
    if k == "perso":
        return st.session_state.wue_on_custom, st.session_state.wue_off_custom
    p = cfg.WATER_PROFILES[k]
    return p.wue_onsite, p.wue_offsite


def current_thresholds() -> cfg.AlertThresholds:
    return cfg.AlertThresholds(green_max_wh=st.session_state.green_max,
                               orange_max_wh=st.session_state.orange_max)


def apply_settings(s: calc.UsageScenario) -> calc.UsageScenario:
    """Injecte les paramètres environnementaux courants dans un scénario."""
    on, off = current_water()
    return replace(s, pue=current_pue(), grid_g_per_kwh=current_grid(), wue_onsite=on,
                   wue_offsite=off, include_water=st.session_state.include_water,
                   input_token_weight=st.session_state.input_weight)


# ---------------------------------------------------------------------------
# Composants d'affichage
# ---------------------------------------------------------------------------
def fmt(x: float | None, unit: str, digits: int = 2) -> str:
    """Formatage français des nombres (espace fine pour les milliers, virgule décimale)."""
    if x is None:
        return "non estimé"
    if abs(x) >= 1000:
        s = f"{x:,.0f}".replace(",", " ")
    elif abs(x) >= 10:
        s = f"{x:.1f}".replace(".", ",")
    else:
        s = f"{x:.{digits}f}".replace(".", ",")
    return f"{s} {unit}"


def smart_energy(wh: float) -> str:
    return fmt(wh / 1000, "kWh") if wh >= 1000 else fmt(wh, "Wh", 3 if wh < 1 else 2)


def smart_co2(g: float) -> str:
    return fmt(g / 1000, "kg CO₂e") if g >= 1000 else fmt(g, "g CO₂e", 3 if g < 1 else 2)


def smart_water(l: float | None) -> str:
    if l is None:
        return "non estimé"
    return fmt(l * 1000, "mL") if l < 1 else fmt(l, "L")


def card(col, label: str, value: str, sub: str = "") -> None:
    col.markdown(f'<div class="eco-card"><div class="lbl">{label}</div>'
                 f'<div class="val">{value}</div><div class="sub">{sub}</div></div>',
                 unsafe_allow_html=True)


def show_alert(a: alerts.Alert) -> None:
    tips = "".join(f"<li>{t}</li>" for t in a.advice)
    eq = f"{a.gemini_equivalent:,.0f}".replace(",", "\u202f")
    st.markdown(
        f'<div class="eco-alert" style="background:{a.background};border-color:{a.color}">'
        f'<h4 style="color:{a.color};margin:0">{a.icon} {a.title}</h4>'
        f'<p style="margin:.4rem 0">{a.message}</p>'
        f'<p style="margin:.2rem 0;font-size:.85rem;color:#555">Énergie hebdomadaire estimée : '
        f'<b>{smart_energy(a.weekly_wh)}</b> ≈ {eq} requêtes texte médianes '
        f'Gemini (0,24 Wh, Google 2025).</p>'
        f'<b>Conseils :</b><ul style="margin:.2rem 0">{tips}</ul></div>'.replace(",", " ", 0),
        unsafe_allow_html=True)
    st.caption("Les seuils d'alerte sont une convention pédagogique modifiable "
               "(page « Paramètres »), et non une limite scientifique.")


def estimate_badge() -> None:
    st.markdown('<span class="eco-tag">⚠️ Valeurs estimées — aucune télémétrie des serveurs '
                'réellement utilisés</span>', unsafe_allow_html=True)


def hero() -> None:
    st.markdown(f'<div class="eco-hero"><h1>🌿 {cfg.APP_NAME}</h1>'
                f'<p>« {cfg.APP_SLOGAN} »</p></div>', unsafe_allow_html=True)


def model_label(s: calc.UsageScenario) -> str:
    if s.method == "reference":
        return cfg.REFERENCE_VALUES[s.reference_key].label
    if s.model_key == "perso":
        return f"Personnalisé ({s.custom_total_params_b:g} Md / {s.custom_active_params_b:g} Md actifs)"
    return cfg.MODEL_PROFILES[s.model_key].label


# ---------------------------------------------------------------------------
# Page 1 — Simulation
# ---------------------------------------------------------------------------
def page_simulation() -> None:
    st.header("🧮 Simuler mon utilisation de l'IA")
    st.write("Décrivez votre utilisation habituelle. EcoPrompt estime l'énergie, les émissions "
             "et l'eau associées à la phase d'**inférence** (réponse aux requêtes).")

    with st.form("sim"):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Nom du scénario", "Mon utilisation")
            requests = st.number_input("Nombre de requêtes", min_value=0, max_value=cfg.MAX_REQUESTS,
                                       value=15, step=1)
            period = st.radio("Fréquence", ["jour", "semaine"], horizontal=True,
                              format_func=lambda p: f"par {p}")
            usage_date = st.date_input("Semaine d'utilisation (pour l'historique)", date.today())
        with c2:
            method = st.radio("Méthode d'estimation", ["ecologits", "reference"],
                              format_func=lambda m: "Paramétrique (EcoLogits, selon les tokens)"
                              if m == "ecologits" else "Valeur publiée par requête")
            model_options = list(cfg.MODEL_PROFILES) + ["perso"]
            model_key = st.selectbox("Catégorie de modèle (méthode paramétrique)", model_options,
                                     index=1, format_func=lambda k: "Profil personnalisé"
                                     if k == "perso" else cfg.MODEL_PROFILES[k].label)
            ref_key = st.selectbox("Valeur publiée (méthode par requête)",
                                   list(cfg.REFERENCE_VALUES),
                                   format_func=lambda k: cfg.REFERENCE_VALUES[k].label)
            cc1, cc2 = st.columns(2)
            total_b = cc1.number_input("Param. totaux (Md) — perso", 0.1, cfg.MAX_PARAMS_B, 70.0)
            active_b = cc2.number_input("Param. actifs (Md) — perso", 0.1, cfg.MAX_PARAMS_B, 70.0)
        c3, c4 = st.columns(2)
        t_in = c3.number_input("Tokens d'entrée par requête (≈ 0,75 mot/token en anglais)",
                               0, cfg.MAX_TOKENS, 200, step=50)
        t_out = c4.number_input("Tokens de sortie par requête", 0, cfg.MAX_TOKENS, 400, step=50)
        submitted = st.form_submit_button("🌿 Estimer mon impact", width="stretch")

    if submitted:
        s = calc.UsageScenario(name=name, requests=int(requests), period=period,
                               input_tokens=int(t_in), output_tokens=int(t_out), method=method,
                               model_key=model_key, reference_key=ref_key,
                               custom_total_params_b=float(total_b),
                               custom_active_params_b=float(active_b))
        st.session_state.last_scenario = s
        st.session_state.last_date = usage_date

    s = st.session_state.last_scenario
    if s is None:
        st.info("Remplissez le formulaire puis cliquez sur « Estimer mon impact ».")
        return
    try:
        s_full = apply_settings(s)
        r = calc.compute_impact(s_full)
    except calc.ValidationError as e:
        st.error(f"Entrée invalide : {e}")
        return

    st.subheader("Résultats estimés")
    estimate_badge()
    st.caption(f"{r.method_label} — {model_label(s)}")
    c = st.columns(4)
    card(c[0], "⚡ Énergie par requête", smart_energy(r.per_request_wh),
         f"dont {smart_energy(r.per_request_it_wh)} côté serveurs")
    card(c[1], "⚡ Énergie par semaine", smart_energy(r.weekly_wh),
         f"{r.weekly_requests:,.0f} requêtes".replace(",", " "))
    card(c[2], "🌫️ CO₂e par semaine", smart_co2(r.weekly_co2_g),
         f"intensité : {fmt(current_grid(), 'g/kWh', 1)}")
    card(c[3], "💧 Eau par semaine", smart_water(r.weekly_water_l),
         "sur site + production d'électricité")
    st.write("")
    c = st.columns(3)
    card(c[0], "Projection annuelle — énergie", smart_energy(r.yearly_wh), "52 semaines")
    card(c[1], "Projection annuelle — CO₂e", smart_co2(r.yearly_co2_g), "52 semaines")
    card(c[2], "Projection annuelle — eau", smart_water(r.yearly_water_l), "52 semaines")

    st.write("")
    left, right = st.columns([1.1, 1])
    with left:
        uses_large = s.method == "ecologits" and s.model_key in ("grand", "moyen")
        uses_img = s.method == "reference" and s.reference_key == "image_gen_lab"
        a = alerts.build_alert(r.weekly_wh, s.output_tokens, uses_large, uses_img,
                               current_thresholds())
        show_alert(a)
        if st.button("💾 Enregistrer dans mon historique", width="stretch"):
            dm.add_simulation({
                "usage_date": st.session_state.get("last_date", date.today()),
                "scenario": s.name, "method": s.method, "model": model_label(s),
                "requests": s.requests, "period": s.period, "input_tokens": s.input_tokens,
                "output_tokens": s.output_tokens, "weekly_requests": r.weekly_requests,
                "weekly_wh": r.weekly_wh, "weekly_co2_g": r.weekly_co2_g,
                "weekly_water_l": r.weekly_water_l, "alert_level": a.level})
            st.success("Simulation enregistrée localement (data/ecoprompt.db).")
    with right:
        b = r.breakdown
        if s.method == "ecologits":
            parts = {"GPU": b["gpu_wh"], "Serveur hors GPU": b["server_other_wh"],
                     "Surcoût du centre (PUE)": b["overhead_wh"]}
            st.caption(f"Décomposition d'une requête — {b['n_gpu']} GPU H100 supposé(s), "
                       f"latence estimée {b['latency_s']:.1f} s".replace(".", ","))
        else:
            parts = {"Serveurs (informatique)": b["it_wh"],
                     "Surcoût du centre (PUE)": b["overhead_wh"]}
            st.caption("Décomposition d'une requête (valeur publiée)")
        fig = px.pie(names=list(parts), values=list(parts.values()), hole=.55,
                     color_discrete_sequence=PALETTE)
        fig.update_traces(texttemplate="%{label}<br>%{percent}", hovertemplate="%{label} : "
                          "%{value:.4f} Wh<extra></extra>")
        fig.update_layout(showlegend=False, height=320, margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig, width="stretch")

    if s.method == "ecologits" and s.input_tokens > 0 and st.session_state.input_weight == 0:
        st.caption("ℹ️ Conformément à EcoLogits, les tokens d'entrée ne sont pas comptés dans "
                   "l'énergie. Vous pouvez tester une hypothèse dans « Paramètres ».")


# ---------------------------------------------------------------------------
# Page 2 — Tableau de bord
# ---------------------------------------------------------------------------
def page_dashboard() -> None:
    st.header("📊 Tableau de bord environnemental")
    df = dm.load_history()
    if df.empty:
        st.info("Aucune simulation enregistrée. Utilisez « Simulation » puis « Enregistrer ».")
        if st.button("Charger un historique de démonstration (8 semaines)"):
            load_demo_history()
            st.rerun()
        return

    estimate_badge()
    sm = dm.summary()
    c = st.columns(5)
    card(c[0], "📝 Simulations", f"{sm['simulations']}", "semaines enregistrées")
    card(c[1], "💬 Requêtes totales", f"{sm['requests']:,.0f}".replace(",", " "), "cumulées")
    card(c[2], "⚡ Énergie estimée", smart_energy(sm["wh"]), "cumulée")
    card(c[3], "🌫️ CO₂e estimé", smart_co2(sm["co2_g"]), "cumulé")
    card(c[4], "💧 Eau estimée", smart_water(sm["water_l"]), "cumulée")

    st.subheader("Évolution dans le temps")
    metric = st.radio("Indicateur", ["weekly_wh", "weekly_co2_g", "weekly_water_l",
                                     "weekly_requests"], horizontal=True,
                      format_func={"weekly_wh": "Énergie (Wh)", "weekly_co2_g": "CO₂e (g)",
                                   "weekly_water_l": "Eau (L)",
                                   "weekly_requests": "Requêtes"}.get)
    by_week = df.groupby("usage_date", as_index=False)[metric].sum()
    fig = px.area(by_week, x="usage_date", y=metric, markers=True,
                  color_discrete_sequence=[GREEN])
    if metric == "weekly_wh":  # seuils d'alerte affichés seulement pour l'énergie
        fig.add_hline(y=st.session_state.green_max, line_dash="dot", line_color="#2E7D32",
                      annotation_text="seuil vert")
        fig.add_hline(y=st.session_state.orange_max, line_dash="dot", line_color="#E65100",
                      annotation_text="seuil orange")
    fig.update_layout(height=340, xaxis_title="Semaine", yaxis_title="", plot_bgcolor="white",
                      margin=dict(t=10, b=10))
    st.plotly_chart(fig, width="stretch")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Niveaux d'alerte")
        counts = df["alert_level"].value_counts().reindex(["vert", "orange", "rouge"],
                                                          fill_value=0)
        fig = px.bar(x=counts.index, y=counts.values, color=counts.index,
                     color_discrete_map={"vert": "#2E7D32", "orange": "#E65100",
                                         "rouge": "#C62828"})
        fig.update_yaxes(dtick=1)
        fig.update_layout(showlegend=False, height=280, xaxis_title="", yaxis_title="Semaines",
                          plot_bgcolor="white", margin=dict(t=10, b=10))
        st.plotly_chart(fig, width="stretch")
    with c2:
        st.subheader("Énergie par catégorie de modèle")
        bym = df.groupby("model", as_index=False)["weekly_wh"].sum()
        bym["model"] = bym["model"].str.split(" \\(").str[0]  # libellé court
        fig = px.bar(bym, x="weekly_wh", y="model", orientation="h",
                     color_discrete_sequence=[GREEN])
        fig.update_layout(height=280, xaxis_title="Wh estimés", yaxis_title="",
                          plot_bgcolor="white", margin=dict(t=10, b=10))
        st.plotly_chart(fig, width="stretch")

    st.subheader("Dernière alerte")
    last = df.iloc[-1]
    show_alert(alerts.build_alert(float(last["weekly_wh"]), int(last["output_tokens"]),
                                  thresholds=current_thresholds()))

    with st.expander("📄 Historique détaillé"):
        show = df.rename(columns={
            "usage_date": "Semaine", "scenario": "Scénario", "model": "Modèle",
            "weekly_requests": "Requêtes/sem.", "weekly_wh": "Wh/sem.",
            "weekly_co2_g": "g CO₂e/sem.", "weekly_water_l": "L/sem.", "alert_level": "Alerte"})
        st.dataframe(show[["id", "Semaine", "Scénario", "Modèle", "Requêtes/sem.", "Wh/sem.",
                           "g CO₂e/sem.", "L/sem.", "Alerte"]], width="stretch",
                     hide_index=True)
        c1, c2 = st.columns(2)
        c1.download_button("⬇️ Exporter en CSV", dm.export_csv(), "ecoprompt_historique.csv",
                           "text/csv", width="stretch")
        if c2.button("🗑️ Vider l'historique", width="stretch"):
            dm.clear_history()
            st.rerun()


def load_demo_history() -> None:
    """Historique fictif de démonstration (clairement nommé comme tel)."""
    today = pd.Timestamp(date.today())
    plan = [(25, "grand", 600), (30, "grand", 700), (22, "moyen", 500), (20, "moyen", 450),
            (15, "moe", 400), (12, "moe", 350), (10, "petit", 300), (8, "petit", 250)]
    for i, (n, mk, tout) in enumerate(plan):
        s = apply_settings(calc.UsageScenario(name="Démonstration", requests=n, period="jour",
                                              input_tokens=200, output_tokens=tout,
                                              model_key=mk))
        r = calc.compute_impact(s)
        a = alerts.build_alert(r.weekly_wh, tout, thresholds=current_thresholds())
        dm.add_simulation({"usage_date": (today - pd.Timedelta(weeks=len(plan) - 1 - i)).date(),
                           "scenario": "Démonstration (fictif)", "method": "ecologits",
                           "model": model_label(s), "requests": n, "period": "jour",
                           "input_tokens": 200, "output_tokens": tout,
                           "weekly_requests": r.weekly_requests, "weekly_wh": r.weekly_wh,
                           "weekly_co2_g": r.weekly_co2_g, "weekly_water_l": r.weekly_water_l,
                           "alert_level": a.level})


# ---------------------------------------------------------------------------
# Page 3 — Comparaison de scénarios
# ---------------------------------------------------------------------------
PRESETS = [
    calc.UsageScenario(name="Sobre : 5 req./jour, petit modèle, réponses courtes", requests=5,
                       period="jour", output_tokens=250, model_key="petit"),
    calc.UsageScenario(name="Courant : 15 req./jour, modèle moyen", requests=15, period="jour",
                       output_tokens=400, model_key="moyen"),
    calc.UsageScenario(name="Intensif : 40 req./jour, grand modèle, réponses longues",
                       requests=40, period="jour", output_tokens=1000, model_key="grand"),
    calc.UsageScenario(name="Images : 10 images/jour", requests=10, period="jour",
                       method="reference", reference_key="image_gen_lab"),
]


def page_compare() -> None:
    st.header("⚖️ Comparer des scénarios d'utilisation")
    st.write("Les scénarios ci-dessous sont des **exemples illustratifs**, calculés avec vos "
             "paramètres actuels. Votre dernière simulation est ajoutée si elle existe.")
    scen = [apply_settings(p) for p in PRESETS]
    if st.session_state.last_scenario is not None:
        scen.append(apply_settings(replace(st.session_state.last_scenario,
                                           name=f"Vous : {st.session_state.last_scenario.name}")))
    df = pd.DataFrame(calc.compare_scenarios(scen))
    estimate_badge()

    ind = st.selectbox("Indicateur", ["Énergie / an (kWh)", "CO₂e / an (kg)", "Eau / an (L)"])
    fig = px.bar(df, x=ind, y="Scénario", orientation="h",
                 color_discrete_sequence=[GREEN], text_auto=".2f")
    fig.update_layout(showlegend=False, height=380, yaxis_title="", plot_bgcolor="white",
                      margin=dict(t=10, b=10))
    st.plotly_chart(fig, width="stretch")

    st.subheader("Énergie estimée par requête selon le modèle et la longueur de réponse")
    rows = []
    for k, p in cfg.MODEL_PROFILES.items():
        for t in (100, 400, 1000, 2000):
            br = calc.ecologits_request_energy(t, p.active_params_b, p.total_params_b,
                                               current_pue())
            rows.append({"Modèle": p.label.split(" (")[0], "Tokens de sortie": t,
                         "Wh / requête": br["total_wh"]})
    fig = px.line(pd.DataFrame(rows), x="Tokens de sortie", y="Wh / requête", color="Modèle",
                  markers=True, color_discrete_sequence=CATEGORICAL, log_y=True)
    fig.add_hline(y=0.24, line_dash="dot", line_color="#888",
                  annotation_text="médiane Gemini publiée : 0,24 Wh")
    fig.update_layout(height=360, plot_bgcolor="white", margin=dict(t=10, b=10))
    st.plotly_chart(fig, width="stretch")

    fmt_df = df.copy()
    st.dataframe(fmt_df.style.format(precision=3, decimal=",", thousands=" "),
                 width="stretch", hide_index=True)


# ---------------------------------------------------------------------------
# Page 4 — Mon impact citoyen
# ---------------------------------------------------------------------------
def page_citizen() -> None:
    st.header("🌍 Mon impact citoyen")
    st.write(
        "Une seule requête représente une énergie très faible. Mais l'IA est utilisée des "
        "milliards de fois : l'Agence internationale de l'énergie estime que les centres de "
        f"données ont consommé **{cfg.IEA_DATACENTERS_2024_TWH:.0f} TWh en 2024** (≈ 1,5 % de "
        f"l'électricité mondiale) et projette **{cfg.IEA_DATACENTERS_2030_TWH:.0f} TWh en 2030**, "
        "l'IA étant un moteur majeur de cette hausse (IEA, 2025).")
    st.info("EcoPrompt ne réduit pas automatiquement les émissions : il **informe, estime et "
            "sensibilise**. La réduction dépend des choix des utilisateurs, des fournisseurs "
            "et des politiques énergétiques.")

    base = st.session_state.last_scenario or PRESETS[1]
    st.subheader(f"Et si je changeais mes habitudes ? (base : « {base.name} »)")
    c = st.columns(4)
    fewer = c[0].slider("Requêtes évitées ou regroupées (%)", 0, 80, 30, step=5)
    shorter = c[1].slider("Réponses plus courtes (%)", 0, 80, 25, step=5)
    smaller = c[2].checkbox("Modèle moins énergivore", True)
    people = c[3].number_input("Nombre de personnes (classe, promo…)", 1, 100000, 30)

    # Profils classés par énergie estimée croissante (le MoE 141 Md nécessite plus de GPU
    # que le modèle dense de 70 Md, d'où une énergie estimée supérieure).
    order = ["petit", "moyen", "moe", "grand"]
    alt = replace(base, name="Usage plus sobre",
                  requests=max(0, round(base.requests * (1 - fewer / 100))),
                  output_tokens=max(0, round(base.output_tokens * (1 - shorter / 100))))
    if smaller and base.method == "ecologits" and base.model_key in order[1:]:
        alt = replace(alt, model_key=order[order.index(base.model_key) - 1])
    try:
        r0 = calc.compute_impact(apply_settings(base))
        r1 = calc.compute_impact(apply_settings(alt))
    except calc.ValidationError as e:
        st.error(str(e))
        return

    red = calc.relative_reduction(r0.yearly_wh, r1.yearly_wh)
    cc = st.columns(3)
    card(cc[0], "Réduction estimée de l'énergie", f"{red*100:.0f} %".replace(".", ","),
         "par rapport à votre scénario")
    card(cc[1], f"Énergie évitée / an — {people} pers.",
         smart_energy((r0.yearly_wh - r1.yearly_wh) * people), "estimation")
    card(cc[2], f"CO₂e évité / an — {people} pers.",
         smart_co2((r0.yearly_co2_g - r1.yearly_co2_g) * people), "estimation")

    comp = pd.DataFrame({
        "Scénario": ["Actuel", "Plus sobre"] * 3,
        "Indicateur": ["Énergie (kWh/an)"] * 2 + ["CO₂e (kg/an)"] * 2 + ["Eau (L/an)"] * 2,
        "Valeur": [r0.yearly_wh / 1000, r1.yearly_wh / 1000, r0.yearly_co2_g / 1000,
                   r1.yearly_co2_g / 1000, r0.yearly_water_l or 0, r1.yearly_water_l or 0]})
    fig = px.bar(comp, x="Indicateur", y="Valeur", color="Scénario", barmode="group",
                 color_discrete_map={"Actuel": "#A5D6A7", "Plus sobre": "#2E7D32"},
                 facet_col="Indicateur", facet_col_spacing=.06)
    fig.update_yaxes(matches=None, showticklabels=True, title="")
    fig.update_xaxes(title="", showticklabels=False)
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    fig.update_layout(height=340, plot_bgcolor="white", margin=dict(t=30, b=10))
    st.plotly_chart(fig, width="stretch")

    st.subheader("Les bons réflexes")
    cols = st.columns(2)
    for i, tip in enumerate(alerts.GENERAL_ADVICE):
        cols[i % 2].markdown(f"✅ {tip}")
    st.subheader("Pourquoi c'est un enjeu citoyen ?")
    st.markdown(
        "- **Effet d'échelle** : un geste négligeable individuellement devient significatif "
        "multiplié par des millions d'utilisateurs.\n"
        "- **Ressources partagées** : électricité et eau des centres de données sont prélevées "
        "sur des territoires réels (Li et al., 2025).\n"
        "- **Transparence** : la plupart des fournisseurs ne publient pas de mesures par "
        "requête ; exiger des données vérifiables est aussi un acte citoyen.\n"
        "- **Sobriété numérique** : utiliser l'IA quand elle apporte une vraie valeur, et "
        "choisir l'outil le plus léger suffisant.")


# ---------------------------------------------------------------------------
# Page 5 — Méthodologie et sources
# ---------------------------------------------------------------------------
def page_method() -> None:
    st.header("📚 Méthodologie et sources")
    st.markdown("""
**1. Énergie d'inférence — méthode paramétrique (EcoLogits)**

- Énergie GPU par token de sortie : `f_E(P) = 1,17·10⁻⁶ · e^(−1,12·10⁻²·64) · P + 4,05·10⁻⁵` Wh (P en milliards de paramètres actifs)
- Nombre de GPU H100 (80 Go) : mémoire = `1,2 × P_total × 16 / 8` Go, arrondi à la puissance de 2 supérieure
- Latence : `f_L(P) = 6,78·10⁻⁴·P + 3,12·10⁻⁴·64 + 1,94·10⁻²` s/token
- Serveur hors GPU : `ΔT × 1,2 kW × (n_GPU/8) / 64`
- Énergie du centre de données : `E = PUE × (E_GPU + E_serveur hors GPU)`

**2. Émissions** : `CO₂e (g) = E (kWh) × intensité carbone (g CO₂e/kWh)`

**3. Eau** (Li et al., 2025) : `Eau (L) = E_serveur (kWh) × [WUE_sur site + PUE × WUE_hors site]`

**4. Hors périmètre** : terminal de l'utilisateur, réseau, fabrication du matériel
(sauf mention), stockage des données et entraînement (présenté séparément ci-dessous).
""")
    st.subheader("Paramètres et références")
    rows = []
    for k, p in cfg.MODEL_PROFILES.items():
        rows.append(["Modèle", p.label, f"{p.total_params_b:g} / {p.active_params_b:g} Md",
                     "documenté", p.source])
    for k, v in cfg.REFERENCE_VALUES.items():
        rows.append(["Valeur par requête", v.label, f"{v.wh_per_request} Wh", v.nature, v.source])
    for k, (v, l, src) in cfg.PUE_OPTIONS.items():
        rows.append(["PUE", l, f"{v}", "publié", src])
    for k, (v, l, src) in cfg.GRID_FACTORS.items():
        rows.append(["Intensité carbone", l, f"{v} g/kWh", "statistique", src])
    for k, w in cfg.WATER_PROFILES.items():
        rows.append(["Eau", w.label, f"{w.wue_onsite} + {w.wue_offsite} L/kWh", "estimé",
                     w.source])
    rows.append(["Seuils d'alerte", "Vert / orange", f"{cfg.DEFAULT_THRESHOLDS.green_max_wh} / "
                 f"{cfg.DEFAULT_THRESHOLDS.orange_max_wh} Wh/sem.", "convention", "ecoprompt"])
    st.dataframe(pd.DataFrame(rows, columns=["Type", "Paramètre", "Valeur", "Nature", "Source"]),
                 width="stretch", hide_index=True)

    st.subheader("Entraînement : un impact à part")
    st.write("L'entraînement est un coût initial, très élevé, partagé ensuite entre toutes les "
             "requêtes. Le nombre total de requêtes servies n'étant pas publié, EcoPrompt "
             "**n'additionne pas** l'entraînement aux résultats par défaut.")
    tr = pd.DataFrame(cfg.TRAINING_REFERENCES).rename(columns={
        "modele": "Modèle", "energie_mwh": "Énergie (MWh)", "co2_t": "CO₂e (t)",
        "eau_m3": "Eau (m³)", "nature": "Nature", "source": "Source", "note": "Remarque"})
    st.dataframe(tr, width="stretch", hide_index=True)
    st.caption(f"Luccioni et al. (2024) : il faut ≈ {cfg.BLOOMZ_PARITY_INFERENCES:,} inférences "
               "de BLOOMz-7B pour égaler l'énergie de son entraînement et de son ajustement."
               .replace(",", " "))
    with st.expander("🧪 Calcul illustratif : part de l'entraînement par requête"):
        c1, c2 = st.columns(2)
        e = c1.number_input("Énergie d'entraînement (MWh)", 0.0, 1e7, 1287.0)
        n = c2.number_input("Hypothèse : requêtes servies sur la durée de vie", 1.0, 1e14, 1e9,
                            format="%.0f")
        st.write(f"Part attribuée : **{calc.training_share_per_request(e, n):.4f} Wh / requête** "
                 "(résultat entièrement dépendant de l'hypothèse choisie).".replace(".", ",", 1))

    st.subheader("Bibliographie")
    for key, s in cfg.SOURCES.items():
        if key == "ecoprompt":
            continue
        link = f" [{s['url']}]({s['url']})" if s["url"] else ""
        st.markdown(f"- **[{key}]** {s['citation']} — *{s['type']}*, {s['date']}.{link}")


# ---------------------------------------------------------------------------
# Page 6 — Paramètres
# ---------------------------------------------------------------------------
def page_settings() -> None:
    st.header("⚙️ Paramètres environnementaux")
    st.write("Adaptez les hypothèses lorsque vous disposez de données plus fiables "
             "(localisation des serveurs, rapport du fournisseur…).")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("⚡ Centre de données")
        st.selectbox("PUE (efficacité énergétique du centre)", list(cfg.PUE_OPTIONS) + ["perso"],
                     key="pue_key", format_func=lambda k: "Valeur personnalisée" if k == "perso"
                     else cfg.PUE_OPTIONS[k][1])
        if st.session_state.pue_key == "perso":
            st.number_input("PUE personnalisé", 1.0, 3.0, key="pue_custom", step=0.01)
        st.subheader("🌫️ Électricité")
        st.selectbox("Intensité carbone du réseau", list(cfg.GRID_FACTORS) + ["perso"],
                     key="grid_key", format_func=lambda k: "Valeur personnalisée" if k == "perso"
                     else cfg.GRID_FACTORS[k][1])
        if st.session_state.grid_key == "perso":
            st.number_input("g CO₂e/kWh", 0.0, 2000.0, key="grid_custom")
        st.caption("La localisation des serveurs est rarement connue : la moyenne mondiale est "
                   "utilisée par défaut.")
    with c2:
        st.subheader("💧 Eau")
        st.checkbox("Estimer la consommation d'eau", key="include_water")
        st.selectbox("Profil hydrique", list(cfg.WATER_PROFILES) + ["perso"], key="water_key",
                     format_func=lambda k: "Valeur personnalisée" if k == "perso"
                     else cfg.WATER_PROFILES[k].label)
        if st.session_state.water_key == "perso":
            st.number_input("WUE sur site (L/kWh)", 0.0, 20.0, key="wue_on_custom")
            st.number_input("WUE hors site (L/kWh)", 0.0, 50.0, key="wue_off_custom")
        st.subheader("🚦 Seuils d'alerte (Wh / semaine)")
        st.number_input("Limite du niveau vert", 0.1, 1e6, key="green_max")
        st.number_input("Limite du niveau orange", 0.2, 1e6, key="orange_max")
        try:
            alerts.validate_thresholds(current_thresholds())
        except calc.ValidationError as e:
            st.error(str(e))
        st.subheader("🧪 Hypothèse avancée")
        st.slider("Poids d'un token d'entrée (fraction d'un token de sortie)", 0.0, 1.0,
                  key="input_weight", step=0.05,
                  help="0 = méthode EcoLogits (seuls les tokens de sortie comptent). Toute autre "
                       "valeur est une hypothèse personnelle non sourcée.")
        if st.session_state.input_weight > 0:
            st.warning("Hypothèse personnelle active : les résultats s'écartent de la méthode "
                       "EcoLogits publiée.")


# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------
PAGES = {
    "🧮 Simulation": page_simulation,
    "📊 Tableau de bord": page_dashboard,
    "⚖️ Comparer des scénarios": page_compare,
    "🌍 Mon impact citoyen": page_citizen,
    "📚 Méthodologie et sources": page_method,
    "⚙️ Paramètres": page_settings,
}


def main() -> None:
    init_state()
    dm.init_db()
    with st.sidebar:
        st.markdown(f"## 🌿 {cfg.APP_NAME}")
        st.caption(cfg.APP_SLOGAN)
        page = st.radio("Navigation", list(PAGES), label_visibility="collapsed")
        st.divider()
        st.caption(f"PUE : {current_pue():.2f} · Réseau : {current_grid():.0f} g CO₂e/kWh"
                   .replace(".", ","))
        st.caption("Projet Ingénieur Citoyen — estimations pédagogiques, "
                   "sources dans « Méthodologie ».")
    hero()
    PAGES[page]()


if __name__ == "__main__":
    main()
