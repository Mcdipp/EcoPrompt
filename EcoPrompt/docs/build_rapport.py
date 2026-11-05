"""
build_rapport.py — Génère le rapport académique EcoPrompt (PDF) avec ReportLab.

Reprend l'identité visuelle du document « Projet citoyen » de référence :
bandeau jaune de couverture, titres numérotés avec chiffre jaune, en-tête
centré et numéro de page souligné en jaune.

Usage :  python docs/build_rapport.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, CondPageBreak, Frame, Image, KeepTogether,
                                NextPageTemplate, PageBreak, PageTemplate, Paragraph, Preformatted,
                                Spacer, Table, TableStyle)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import calculations as calc  # noqa: E402
import config as cfg  # noqa: E402

ASSETS = ROOT / "assets"
OUT = ROOT / "docs" / "EcoPrompt_Rapport_Ingenieur_Citoyen.pdf"

# --- Polices (Liberation Sans : métrique identique à Arial, police de l'original) ---------
FONT_DIR = Path("/usr/share/fonts/truetype/liberation")
pdfmetrics.registerFont(TTFont("Arial", str(FONT_DIR / "LiberationSans-Regular.ttf")))
pdfmetrics.registerFont(TTFont("Arial-Bold", str(FONT_DIR / "LiberationSans-Bold.ttf")))
pdfmetrics.registerFont(TTFont("Arial-Italic", str(FONT_DIR / "LiberationSans-Italic.ttf")))
pdfmetrics.registerFont(TTFont("Arial-BoldItalic", str(FONT_DIR / "LiberationSans-BoldItalic.ttf")))
pdfmetrics.registerFont(TTFont("Mono", str(FONT_DIR / "LiberationMono-Regular.ttf")))
from reportlab.lib.fonts import addMapping  # noqa: E402
addMapping("Arial", 0, 0, "Arial")
addMapping("Arial", 1, 0, "Arial-Bold")
addMapping("Arial", 0, 1, "Arial-Italic")
addMapping("Arial", 1, 1, "Arial-BoldItalic")

YELLOW = colors.HexColor("#FFE11F")
GREEN = colors.HexColor("#2E7D32")
GREEN_L = colors.HexColor("#E8F5E9")
GREY = colors.HexColor("#555555")
LINK = colors.HexColor("#1155CC")
W, H = A4
LM = RM = 2.4 * cm

# --- Styles -------------------------------------------------------------------------------
body = ParagraphStyle("body", fontName="Arial", fontSize=10.5, leading=15.5, alignment=TA_JUSTIFY,
                      firstLineIndent=1.1 * cm, spaceAfter=7)
body_ni = ParagraphStyle("body_ni", parent=body, firstLineIndent=0)
small = ParagraphStyle("small", parent=body_ni, fontSize=8.5, leading=11.5, textColor=GREY,
                       alignment=TA_LEFT)
caption = ParagraphStyle("cap", parent=small, alignment=TA_CENTER, spaceBefore=3, spaceAfter=10,
                         fontName="Arial-Italic")
bullet = ParagraphStyle("bul", parent=body_ni, leftIndent=0.9 * cm, bulletIndent=0.35 * cm,
                        spaceAfter=3)
h1 = ParagraphStyle("h1", fontName="Arial-Bold", fontSize=15, leading=19, spaceBefore=6,
                    spaceAfter=12, textColor=colors.black, keepWithNext=1)
h2 = ParagraphStyle("h2", fontName="Arial-Bold", fontSize=11.5, leading=15, spaceBefore=8,
                    spaceAfter=6, textColor=colors.HexColor("#222222"), keepWithNext=1)
cell = ParagraphStyle("cell", fontName="Arial", fontSize=8.3, leading=10.5)
cell_b = ParagraphStyle("cellb", parent=cell, fontName="Arial-Bold")
quote = ParagraphStyle("quote", parent=body_ni, fontName="Arial-BoldItalic", fontSize=12,
                       leading=17, alignment=TA_CENTER, textColor=colors.HexColor("#222"),
                       spaceBefore=6, spaceAfter=10)
code = ParagraphStyle("code", fontName="Mono", fontSize=7.6, leading=9.6,
                      backColor=colors.HexColor("#F6F8F6"), borderPadding=6, leftIndent=4)
toc_style = ParagraphStyle("toc", parent=body_ni, fontSize=10.5, leading=16, spaceAfter=0)


def P(t, st=body):
    return Paragraph(t, st)


def H1(n, t):
    return CondPageBreak(4 * cm), Paragraph(
        f'<font color="#FFD200" size="19"><b>{n}.</b></font>&nbsp;&nbsp;{t.upper()}', h1)


def H2(t):
    return Paragraph(t, h2)


def B(items):
    return [Paragraph(i, bullet, bulletText="–") for i in items]


def tag(nature):
    col = {"mesuré": "#2E7D32", "estimé": "#C77700", "convention": "#6A1B9A",
           "statistique": "#1E63B5", "documenté": "#455A64"}.get(nature.split()[0], "#455A64")
    return f'<font color="{col}"><b>{nature}</b></font>'


def T(rows, widths, header=True, zebra=True, font=8.3):
    data = [[Paragraph(str(c), cell_b if (header and i == 0) else cell) for c in r]
            for i, r in enumerate(rows)]
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0, hAlign="CENTER")
    style = [("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#C8C8C8")),
             ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
             ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]
    if header:
        style.append(("BACKGROUND", (0, 0), (-1, 0), YELLOW))
    if zebra:
        for i in range(1, len(rows)):
            if i % 2 == 0:
                style.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#FAFAF5")))
    t.setStyle(TableStyle(style))
    return t


def FIG(path, width_cm, cap):
    img = Image(str(path))
    ratio = img.imageHeight / img.imageWidth
    img.drawWidth = width_cm * cm
    img.drawHeight = width_cm * cm * ratio
    return KeepTogether([img, Paragraph(cap, caption)])


def BOX(text, color="#FFF8D6", border="#FFD200"):
    t = Table([[Paragraph(text, body_ni)]], colWidths=[W - LM - RM - 0.2 * cm])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(color)),
                           ("LINEBEFORE", (0, 0), (0, -1), 4, colors.HexColor(border)),
                           ("LEFTPADDING", (0, 0), (-1, -1), 10),
                           ("TOPPADDING", (0, 0), (-1, -1), 7),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    return t


def fr(x, d=3):
    """Format numérique français."""
    s = f"{x:,.{d}f}".replace(",", " ").replace(".", ",")
    return s


# --- Mise en page -------------------------------------------------------------------------
def cover(c, doc):
    c.saveState()
    band = 9.6 * cm
    c.setFillColor(YELLOW)
    c.rect(0, H - band, W, band, stroke=0, fill=1)
    c.setFillColor(colors.black)
    c.setFont("Arial-Bold", 15)
    c.drawString(LM, H - 2.2 * cm, "EcoPrompt")
    c.setFont("Arial", 7.5)
    c.drawString(LM, H - 2.65 * cm, "COMPRENDRE SON IMPACT, UTILISER L'IA AUTREMENT")
    c.setFont("Arial", 9)
    c.drawRightString(W - RM, H - 2.0 * cm, "Felipe DIPP ALCON")
    c.setFont("Arial-Bold", 22)
    c.drawString(LM, H - 6.3 * cm, "PROJET INGÉNIEUR CITOYEN")
    c.setFont("Arial-Bold", 15)
    c.drawString(LM, H - 7.15 * cm, "EcoPrompt")
    c.setFont("Arial", 10.5)
    c.drawString(LM, H - 7.9 * cm, "Analyse et sensibilisation à l'empreinte environnementale "
                                   "de l'intelligence artificielle")
    c.setFillColor(YELLOW)
    c.rect(W - 1.2 * cm, 1.6 * cm, 1.2 * cm, 0.22 * cm, stroke=0, fill=1)
    c.setFillColor(colors.black)
    c.setFont("Arial-Bold", 7)
    c.drawRightString(W - 1.6 * cm, 1.62 * cm, "Novembre 2026")
    c.restoreState()


def later(c, doc):
    c.saveState()
    c.setFont("Arial-Bold", 7.5)
    c.drawCentredString(W / 2, H - 1.25 * cm, "PROJET INGÉNIEUR CITOYEN — ECOPROMPT")
    c.setFont("Arial", 8)
    c.drawRightString(W - RM + 0.4 * cm, 1.55 * cm, str(doc.page))
    c.setStrokeColor(YELLOW)
    c.setLineWidth(1.6)
    c.line(W - RM - 0.15 * cm, 1.35 * cm, W - RM + 0.55 * cm, 1.35 * cm)
    c.setStrokeColor(colors.black)
    c.setLineWidth(0.8)
    c.line(LM - 0.5 * cm, 1.2 * cm, LM - 0.5 * cm, 1.75 * cm)
    c.restoreState()


doc = BaseDocTemplate(str(OUT), pagesize=A4, leftMargin=LM, rightMargin=RM, topMargin=2.3 * cm,
                      bottomMargin=2.2 * cm, title="EcoPrompt — Projet Ingénieur Citoyen",
                      author="Felipe Dipp Alcon", subject="Empreinte environnementale de l'IA")
fr_cover = Frame(LM, 2.4 * cm, W - LM - RM, H - 9.6 * cm - 3.2 * cm, id="cover")
fr_body = Frame(LM, 2.2 * cm, W - LM - RM, H - 4.5 * cm, id="body")
doc.addPageTemplates([PageTemplate("cover", [fr_cover], onPage=cover),
                      PageTemplate("later", [fr_body], onPage=later)])

# --- Valeurs calculées (reproductibles) ---------------------------------------------------
PUE = 1.20
def per_req(key, t):
    p = cfg.MODEL_PROFILES[key]
    return calc.ecologits_request_energy(t, p.active_params_b, p.total_params_b, PUE)

r70 = per_req("moyen", 400)
co2_world = calc.co2_from_energy(r70["total_wh"], 473)
co2_fr = calc.co2_from_energy(r70["total_wh"], 21.7)
co2_eu = calc.co2_from_energy(r70["total_wh"], 211.2)
water_li = calc.water_from_energy(r70["it_wh"], 0.55, 3.142, PUE) * 1000
water_g = calc.water_from_energy(0.24 / 1.09, 1.15, 0.0, 1.09) * 1000
SCEN = [
    ("Sobre", "5 req./jour, 8 Md, 250 tokens",
     calc.UsageScenario(requests=5, output_tokens=250, model_key="petit")),
    ("Courant", "15 req./jour, 70 Md, 400 tokens",
     calc.UsageScenario(requests=15, output_tokens=400, model_key="moyen")),
    ("Images", "10 images/jour (Luccioni et al.)",
     calc.UsageScenario(requests=10, method="reference", reference_key="image_gen_lab")),
    ("Intensif", "40 req./jour, 405 Md, 1 000 tokens",
     calc.UsageScenario(requests=40, output_tokens=1000, model_key="grand")),
]
import alerts  # noqa: E402

story = []
S = story.append
E = story.extend

# ===================== COUVERTURE =====================
S(Spacer(1, 0.6 * cm))
S(P("Le projet Ingénieur Citoyen a pour objectif de concrétiser une réponse à un besoin en lien "
    "avec une problématique écologique ou sociale."))
S(P("Dans le cadre de ce projet, une application Python nommée <b>EcoPrompt</b> a été conçue, "
    "développée et testée. Elle permet d'<b>estimer</b>, de <b>visualiser</b> et de "
    "<b>signaler</b> l'empreinte environnementale (énergie, émissions de CO<sub>2</sub>e, eau) "
    "associée à l'utilisation d'outils d'intelligence artificielle générative."))
S(P("Le projet comprend quatre livrables :", body))
E(B(["le présent rapport académique ;",
     "le code source Python complet (Streamlit, Pandas, Plotly, SQLite, Pytest) ;",
     "un dépôt GitHub prêt à publier (README, dépendances, tests, licence) ;",
     "un guide de démonstration pour la soutenance orale."]))
S(Spacer(1, 0.4 * cm))
S(P("Auteur : Felipe DIPP ALCON — INSA Toulouse, cycle préparatoire intégré.", body_ni))
S(P("Dépôt du code : <font color='#1155CC'>https://github.com/&lt;identifiant&gt;/EcoPrompt</font> "
    "<i>(à compléter après publication)</i>.", body_ni))
S(Spacer(1, 0.4 * cm))
S(BOX("<b>Règle de rigueur appliquée dans tout le document.</b> Chaque chiffre est accompagné de "
      "sa source, de sa date, de son unité et de sa nature : "
      f"{tag('mesuré')} (télémétrie ou mesure instrumentée publiée), "
      f"{tag('estimé')} (modèle ou calcul), {tag('statistique')} (donnée officielle agrégée) "
      f"ou {tag('convention')} (choix pédagogique propre à EcoPrompt). Les résultats produits "
      "par EcoPrompt sont toujours des <b>estimations</b>."))
S(NextPageTemplate("later"))
S(PageBreak())

# ===================== SOMMAIRE =====================
S(Paragraph('<font color="#FFD200" size="19"><b>■</b></font>&nbsp;&nbsp;SOMMAIRE', h1))
toc = ["Introduction et contexte environnemental", "Présentation du problème sociétal",
       "Problématique", "Objectifs du projet", "Présentation de la solution EcoPrompt",
       "Fonctionnement technique de l'application", "Méthodologie et architecture informatique",
       "Travail pratique et développement Python", "Calcul estimatif des émissions de CO2",
       "Estimation de la consommation énergétique", "Estimation de la consommation d'eau",
       "Système d'alertes environnementales", "Résultats attendus et validation expérimentale",
       "Impact social et sensibilisation citoyenne", "Limites scientifiques et techniques",
       "Perspectives d'amélioration", "Conclusion", "Bibliographie et sources scientifiques"]
for i, t in enumerate(toc, 1):
    t = t.replace("CO2", "CO<sub>2</sub>")
    S(P(f'<font color="#C9A800"><b>{i}.</b></font>&nbsp;&nbsp;{t}', toc_style))
S(Spacer(1, 0.5 * cm))
S(P("<b>Liste des figures</b>", body_ni))
for f in ["Fig. 1 — Schéma de fonctionnement d'EcoPrompt",
          "Fig. 2 — Architecture logicielle en couches",
          "Fig. 3 — Formulaire de simulation", "Fig. 4 — Résultats, alerte et décomposition",
          "Fig. 5 — Chaîne de calcul de l'énergie, du CO2e et de l'eau",
          "Fig. 6 — Énergie estimée par requête selon le modèle et la longueur de réponse",
          "Fig. 7 — Tableau de bord environnemental", "Fig. 8 — Comparaison de scénarios",
          "Fig. 9 — Énergie annuelle estimée de quatre scénarios",
          "Fig. 10 — Page « Mon impact citoyen »", "Fig. 11 — Page « Méthodologie et sources »"]:
    S(P(f.replace("CO2e", "CO<sub>2</sub>e"), small))
S(PageBreak())

# ===================== 1. INTRODUCTION =====================
E(H1(1, "Introduction et contexte environnemental"))
S(P("L'intelligence artificielle générative (agents conversationnels, génération de texte, de "
    "code ou d'images) s'est diffusée très rapidement dans les usages étudiants, professionnels "
    "et domestiques. Derrière chaque requête se trouve pourtant une infrastructure physique : des "
    "centres de données équipés d'accélérateurs (GPU, TPU), alimentés en électricité et "
    "refroidis, souvent avec de l'eau."))
S(P("À l'échelle mondiale, l'Agence internationale de l'énergie estime que les centres de données "
    "ont consommé environ <b>415 TWh en 2024</b>, soit près de <b>1,5 %</b> de l'électricité "
    "mondiale, et projette <b>945 TWh en 2030</b> dans son scénario de référence, l'IA étant "
    "présentée comme le principal moteur de cette hausse [8]. Les impacts environnementaux de "
    "l'IA se mesurent principalement selon trois grandeurs : l'<b>énergie</b> consommée, les "
    "<b>émissions de gaz à effet de serre</b> qui en résultent (selon le mix électrique) et la "
    "<b>consommation d'eau</b> (refroidissement sur site et production de l'électricité)."))
S(T([["Indicateur", "Valeur", "Unité", "Date", "Nature", "Source"],
     ["Électricité des centres de données (monde)", "415 (≈ 1,5 %)", "TWh/an", "2024",
      tag("estimé"), "IEA 2025 [8]"],
     ["Projection 2030, scénario de référence", "945", "TWh/an", "2030", tag("estimé"),
      "IEA 2025 [8]"],
     ["Prélèvements d'eau liés à l'IA (projection)", "4,2 – 6,6", "milliards de m³", "2027",
      tag("estimé"), "Li et al. 2025 [4]"],
     ["Intensité carbone moyenne de l'électricité", "473", "g CO<sub>2</sub>/kWh", "2024",
      tag("statistique"), "Ember 2025 [9]"],
     ["Énergie d'une requête texte médiane Gemini", "0,24", "Wh", "mai 2025", tag("mesuré"),
      "Google 2025 [2]"]],
    [4.6 * cm, 2.2 * cm, 2.0 * cm, 1.4 * cm, 1.6 * cm, 2.4 * cm]))
S(P("Tableau 1 — Chiffres de contexte utilisés dans le rapport.", caption))
S(P("Ces chiffres globaux sont difficiles à relier à l'usage individuel : un utilisateur ne voit "
    "ni le serveur, ni l'électricité, ni l'eau mobilisés par sa requête. C'est ce décalage que le "
    "projet EcoPrompt cherche à réduire."))

# ===================== 2. PROBLÈME SOCIÉTAL =====================
E(H1(2, "Présentation du problème sociétal"))
S(P("La sobriété numérique est un levier reconnu pour limiter la consommation de ressources. Or "
    "l'IA générative présente trois caractéristiques qui rendent cette sobriété difficile :"))
E(B(["<b>L'invisibilité</b> : l'interface d'un assistant conversationnel ne donne aucune "
     "indication sur le coût énergétique d'une réponse. L'utilisateur perçoit un service "
     "immatériel et gratuit.",
     "<b>L'effet d'échelle</b> : une requête isolée représente une énergie faible (de l'ordre du "
     "dixième de wattheure selon la mesure publiée par Google [2]), mais les usages se comptent "
     "en milliards de requêtes.",
     "<b>L'opacité des données</b> : la plupart des fournisseurs ne publient ni la taille de leurs "
     "modèles, ni leur consommation par requête. Les rares valeurs publiées proviennent de "
     "périmètres et de méthodes différents [2][7]."]))
S(P("Il est par ailleurs courant de reformuler plusieurs fois la même demande, de régénérer une "
    "réponse jugée imparfaite, de solliciter un grand modèle pour une tâche simple ou de demander "
    "des réponses très longues. Chacun de ces comportements augmente le nombre de tokens générés, "
    "donc l'énergie estimée, sans toujours apporter de valeur supplémentaire."))
S(P("Un outil doit donc être conçu pour répondre à ce besoin : il doit être <b>léger</b> (sans "
    "serveur ni service payant), <b>transparent</b> sur ses hypothèses, et capable de "
    "<b>traduire un usage déclaré en ordres de grandeur compréhensibles</b>, accompagnés de "
    "conseils concrets."))

# ===================== 3. PROBLÉMATIQUE =====================
E(H1(3, "Problématique"))
S(P("« Comment sensibiliser les utilisateurs à l'impact environnemental de leurs interactions "
    "avec l'intelligence artificielle ? »", quote))
S(P("Cette question en contient trois : comment <b>estimer</b> honnêtement un impact qui n'est "
    "pas mesuré directement ; comment le <b>rendre lisible</b> sans le dramatiser ni le "
    "minimiser ; et comment <b>orienter les comportements</b> sans prétendre réduire "
    "automatiquement les émissions."))

# ===================== 4. OBJECTIFS =====================
E(H1(4, "Objectifs du projet"))
S(P("<b>Objectif général</b> : développer une application Python fonctionnelle, locale et "
    "gratuite qui estime, visualise et signale l'empreinte environnementale d'un usage de l'IA, "
    "afin de favoriser une utilisation plus consciente.", body_ni))
S(T([["N°", "Objectif spécifique", "Indicateur de réussite"],
     ["O1", "Estimer l'énergie (Wh), le CO<sub>2</sub>e (g) et l'eau (L) à partir d'un usage "
      "déclaré", "Formules publiées, implémentées et testées"],
     ["O2", "Rendre chaque hypothèse traçable et modifiable",
      "100 % des paramètres reliés à une source (test automatique)"],
     ["O3", "Distinguer mesuré, estimé et convention", "Étiquetage visible dans l'application"],
     ["O4", "Alerter avec des niveaux vert / orange / rouge et des conseils",
      "Seuils configurables, messages contextualisés"],
     ["O5", "Suivre l'évolution et comparer des scénarios",
      "Historique SQLite, graphiques interactifs"],
     ["O6", "Sensibiliser à l'échelle collective", "Page « Mon impact citoyen »"],
     ["O7", "Garantir la reproductibilité", "Dépôt GitHub, dépendances documentées, tests"]],
    [1.0 * cm, 8.2 * cm, 5.6 * cm]))
S(P("Tableau 2 — Objectifs spécifiques et critères de réussite.", caption))

# ===================== 5. SOLUTION =====================
E(H1(5, "Présentation de la solution EcoPrompt"))
S(P("EcoPrompt (« Comprendre son impact, utiliser l'IA autrement ») est une application web "
    "locale développée avec Streamlit. L'utilisateur décrit son usage (nombre de requêtes, "
    "fréquence, catégorie de modèle, tokens d'entrée et de sortie) ; l'application calcule une "
    "estimation, l'affiche sous forme d'indicateurs et de graphiques, attribue un niveau "
    "d'alerte et propose des conseils. Les simulations peuvent être enregistrées pour suivre "
    "leur évolution."))
S(FIG(ASSETS / "schema_fonctionnement.png", 15.5, "Fig. 1 — Schéma de fonctionnement d'EcoPrompt."))
S(T([["Page", "Rôle"],
     ["Simulation", "Saisie de l'usage, résultats par requête / semaine / an, alerte"],
     ["Tableau de bord", "Indicateurs cumulés, évolution temporelle, alertes, export CSV"],
     ["Comparer des scénarios", "Scénarios sobre / courant / intensif / images, courbes"],
     ["Mon impact citoyen", "Effet de nouvelles habitudes, à l'échelle d'un groupe"],
     ["Méthodologie et sources", "Formules, paramètres, entraînement, bibliographie"],
     ["Paramètres", "PUE, intensité carbone, eau, seuils, hypothèse avancée"]],
    [4.6 * cm, 10.2 * cm]))
S(P("Tableau 3 — Les six pages de l'application.", caption))
S(P("EcoPrompt fonctionne <b>sans connexion à une API d'IA</b> : il ne mesure pas les requêtes "
    "réelles, il estime l'impact d'un usage déclaré. Ce choix garantit la gratuité, la "
    "confidentialité (aucune donnée ne quitte l'ordinateur) et la reproductibilité."))

# ===================== 6. FONCTIONNEMENT =====================
E(H1(6, "Fonctionnement technique de l'application"))
S(P("Le parcours utilisateur se déroule en quatre étapes : (1) saisie du scénario dans un "
    "formulaire ; (2) validation des entrées (valeurs négatives, non numériques ou incohérentes "
    "refusées avec un message en français) ; (3) calcul par le moteur <i>calculations.py</i> ; "
    "(4) affichage des résultats, de l'alerte et, sur demande, enregistrement dans l'historique."))
S(FIG(ASSETS / "capture_formulaire.png", 13.5, "Fig. 3 — Formulaire de simulation (capture de "
      "l'application, paramètres par défaut)."))
S(P("Deux méthodes d'estimation sont proposées. La <b>méthode paramétrique</b> (par défaut) "
    "dépend du nombre de tokens de sortie et de la taille du modèle (section 10). La "
    "<b>méthode par valeur publiée</b> multiplie le nombre de requêtes par une énergie par "
    "requête issue de la littérature (Google 2025 ; Luccioni et al. 2024). Les paramètres "
    "environnementaux (PUE, intensité carbone, facteurs hydriques) sont choisis dans la page "
    "« Paramètres » parmi des valeurs sourcées, ou saisis librement."))
S(FIG(ASSETS / "capture_resultats.png", 13.0, "Fig. 4 — Résultats estimés, alerte et "
      "décomposition d'une requête (15 requêtes/jour, modèle 70 Md, 400 tokens)."))

# ===================== 7. ARCHITECTURE =====================
E(H1(7, "Méthodologie et architecture informatique"))
S(P("Le projet suit une démarche itérative : (1) recherche bibliographique et sélection des "
    "sources ; (2) choix d'une méthode de calcul publiée et réutilisable ; (3) implémentation "
    "de la logique métier indépendante de l'interface ; (4) écriture des tests unitaires ; "
    "(5) développement de l'interface ; (6) vérification par comparaison avec des valeurs "
    "publiées (section 13)."))
S(FIG(ASSETS / "schema_architecture.png", 12.5, "Fig. 2 — Architecture logicielle en couches."))
S(T([["Fichier", "Contenu", "Lignes"],
     ["app.py", "Interface Streamlit, 6 pages, graphiques Plotly, style vert et blanc", "≈ 670"],
     ["calculations.py", "Formules EcoLogits, CO<sub>2</sub>e, eau, scénarios, validation", "≈ 330"],
     ["alerts.py", "Classement vert / orange / rouge, messages, conseils ciblés", "≈ 110"],
     ["data_manager.py", "Historique SQLite : ajout, lecture, suppression, export CSV", "≈ 120"],
     ["config.py", "Paramètres, profils de modèles, bibliographie structurée", "≈ 330"],
     ["tests/", "59 tests pytest : formules, alertes, base de données, interface", "≈ 310"]],
    [3.2 * cm, 9.8 * cm, 1.8 * cm]))
S(P("Tableau 4 — Organisation du code source.", caption))
S(P("<b>Choix techniques justifiés.</b> Streamlit permet une interface web en Python pur, sans "
    "compétences front-end. SQLite, inclus dans la bibliothèque standard, stocke l'historique "
    "dans un fichier local sans serveur. Plotly produit des graphiques interactifs (survol, "
    "zoom). La séparation stricte entre interface et calcul rend les formules testables "
    "indépendamment de l'affichage."))

# ===================== 8. DÉVELOPPEMENT =====================
E(H1(8, "Travail pratique et développement Python"))
S(P("Le cœur du programme est la fonction qui estime l'énergie d'une requête. Elle transcrit "
    "directement les formules publiées par EcoLogits [1] et renvoie une décomposition par poste, "
    "ce qui permet de l'afficher et de la tester :"))
S(Preformatted(
    "def ecologits_request_energy(output_tokens, active_params_b, total_params_b, pue):\n"
    "    n_gpu = required_gpus(total_params_b)                  # GPU H100 de 80 Go\n"
    "    e_gpu = output_tokens * gpu_energy_per_token_wh(active_params_b) * n_gpu\n"
    "    latency_s = output_tokens * latency_per_token_s(active_params_b)\n"
    "    e_server_other = (latency_s / 3600) * 1.2 * 1000 * (n_gpu / 8) / 64   # Wh\n"
    "    e_server = e_gpu + e_server_other                    # énergie informatique\n"
    "    return {..., \"it_wh\": e_server, \"total_wh\": e_server * pue}", code))
S(Spacer(1, 6))
S(P("<b>Validation des entrées.</b> Toute valeur est contrôlée avant calcul : type numérique, "
    "valeur finie, positivité, bornes maximales, cohérence (paramètres actifs ≤ paramètres "
    "totaux ; seuil orange &gt; seuil vert). Les erreurs lèvent une exception "
    "<i>ValidationError</i> affichée en français dans l'interface. La base SQLite comporte en "
    "plus des contraintes <i>CHECK</i> qui refusent les valeurs négatives."))
S(P("<b>Tests.</b> La suite pytest comporte 59 tests : vérification des formules contre un calcul "
    "manuel indépendant, linéarité en nombre de tokens, conversions CO<sub>2</sub>e et eau, "
    "rejet des entrées invalides, classement des alertes aux bornes, persistance SQLite, et "
    "affichage sans erreur des six pages (tests Streamlit <i>AppTest</i>). "
    "<b>Résultat de l'exécution : 59 tests réussis, 0 échec</b> (Python 3.13, novembre 2026)."))
S(P("<b>Galerie</b> — les captures suivantes ont été réalisées sur l'application en "
    "fonctionnement local (figures 7, 8, 10 et 11).", body_ni))

# ===================== 9. CO2 =====================
E(H1(9, "Calcul estimatif des émissions de CO<sub>2</sub>"))
S(P("Les émissions liées à l'usage sont obtenues en multipliant l'énergie estimée par "
    "l'intensité carbone de l'électricité du centre de données :"))
S(P("<b>CO<sub>2</sub>e (g) = E<sub>requête</sub> (kWh) × I<sub>réseau</sub> "
    "(g CO<sub>2</sub>e/kWh)</b>", quote))
S(P("La localisation des serveurs étant généralement inconnue de l'utilisateur, la "
    "<b>moyenne mondiale</b> est utilisée par défaut. L'utilisateur peut choisir d'autres "
    "valeurs officielles :"))
rows = [["Zone", "Intensité", "Année", "Périmètre", "Source"]]
for k, (v, lab, src) in cfg.GRID_FACTORS.items():
    zone, _, rest = lab.partition(" — ")
    perim = ("direct" if "direct" in lab else "cycle de vie" if ("cycle" in lab or "ACV" in lab)
             else "market-based" if "market" in lab else "location-based" if "location" in lab
             else "production")
    S_ = {"ember2025": "Ember 2025 [9]", "owid2026": "OWID/Ember [11]", "rte2024": "RTE [10]",
          "google2025": "Google 2025 [2]"}[src]
    rows.append([zone.split(" 2024")[0].replace(", location-based", "").replace(", market-based", ""),
                 f"{fr(v, 1)} g CO<sub>2</sub>e/kWh", "2024", perim, S_])
S(T(rows, [4.4 * cm, 3.6 * cm, 1.3 * cm, 2.6 * cm, 2.9 * cm]))
S(P("Tableau 5 — Intensités carbone disponibles dans EcoPrompt (" + tag("statistique") + ").",
    caption))
S(P(f"<b>Exemple</b> ({tag('estimé')}) : pour une requête de 400 tokens sur un modèle de 70 Md "
    f"de paramètres (énergie estimée {fr(r70['total_wh'])} Wh, section 10), les émissions sont "
    f"de <b>{fr(co2_world)} g CO<sub>2</sub>e</b> avec la moyenne mondiale, {fr(co2_eu)} g avec "
    f"l'Union européenne et {fr(co2_fr, 4)} g avec le mix français direct. La localisation "
    "peut donc faire varier le résultat d'un facteur supérieur à 20.", body_ni))
S(P("Ce calcul ne couvre que l'électricité consommée pendant l'utilisation. Les publications "
    "les plus complètes ajoutent la fabrication du matériel : Google déclare 0,03 g "
    "CO<sub>2</sub>e par requête médiane en approche <i>market-based</i> [2], et l'analyse de "
    "cycle de vie de Mistral AI indique 1,14 g CO<sub>2</sub>e pour une réponse de 400 tokens, "
    "fabrication incluse [7]. Ces écarts traduisent des périmètres et des modèles différents."))

# ===================== 10. ÉNERGIE =====================
E(H1(10, "Estimation de la consommation énergétique"))
S(H2("10.1 Méthode paramétrique EcoLogits"))
S(P("EcoLogits est une bibliothèque open source publiée dans le <i>Journal of Open Source "
    "Software</i> [1]. Sa méthodologie modélise l'énergie d'inférence d'un grand modèle de "
    "langage à partir de régressions sur des mesures publiques. EcoPrompt en reprend les "
    "coefficients sans les modifier ("+tag("estimé")+") :"))
eq = [["Grandeur", "Formule (P en milliards de paramètres, B = 64)"],
      ["Énergie GPU par token de sortie",
       "f<sub>E</sub>(P) = 1,17·10<super>-6</super> · e<super>-1,12·10<super>-2</super>·B</super>"
       " · P<sub>actifs</sub> + 4,05·10<super>-5</super> &nbsp;[Wh]"],
      ["Nombre de GPU", "n<sub>GPU</sub> = plus petite puissance de 2 ≥ "
       "1,2 · P<sub>total</sub> · 16/8 / 80 &nbsp;(GPU H100, 80 Go)"],
      ["Latence", "ΔT = T<sub>out</sub> · (6,78·10<super>-4</super>·P<sub>actifs</sub> + "
       "3,12·10<super>-4</super>·B + 1,94·10<super>-2</super>) &nbsp;[s]"],
      ["Serveur hors GPU", "E<sub>srv</sub> = ΔT · 1,2 kW · (n<sub>GPU</sub>/8) / B"],
      ["Énergie informatique", "E<sub>serveur</sub> = T<sub>out</sub> · f<sub>E</sub> · "
       "n<sub>GPU</sub> + E<sub>srv</sub>"],
      ["Énergie du centre", "E<sub>requête</sub> = PUE · E<sub>serveur</sub>"]]
S(T(eq, [4.0 * cm, 10.8 * cm]))
S(P("Tableau 6 — Formules EcoLogits implémentées dans <i>calculations.py</i> [1].", caption))
S(FIG(ASSETS / "schema_calcul.png", 12.5, "Fig. 5 — Chaîne de calcul de l'énergie, du "
      "CO<sub>2</sub>e et de l'eau."))
S(P("Le <b>PUE</b> (Power Usage Effectiveness) traduit le surcoût du centre de données "
    "(refroidissement, conversion électrique). Valeurs proposées : 1,09 (flotte Google 2024 "
    "[2]), 1,16 et 1,20 (valeurs retenues par EcoLogits pour Microsoft en Suède et aux "
    "États-Unis [1]). La valeur par défaut est 1,20, la plus prudente des trois."))
S(P("Les modèles commerciaux (ChatGPT, Gemini, Claude…) ne publient pas leur nombre de "
    "paramètres. EcoPrompt propose donc des <b>profils de taille</b> correspondant à des modèles "
    "ouverts documentés : Llama 3.1 8B, 70B et 405B [12] et Mixtral 8x22B (141 Md, dont 39 Md "
    "actifs) [13]. Le choix d'un profil pour représenter un service commercial est une "
    "hypothèse de l'utilisateur."))
rows = [["Profil", "GPU", "100 tokens", "400 tokens", "1 000 tokens"]]
for k, p in cfg.MODEL_PROFILES.items():
    rows.append([p.label.split(" (")[0], str(calc.required_gpus(p.total_params_b))] +
                [f"{fr(per_req(k, t)['total_wh'])} Wh" for t in (100, 400, 1000)])
S(T(rows, [6.2 * cm, 1.2 * cm, 2.4 * cm, 2.4 * cm, 2.6 * cm]))
S(P(f"Tableau 7 — Énergie estimée par requête, PUE 1,20 ({tag('estimé')}, calcul EcoPrompt).",
    caption))
S(FIG(ASSETS / "graph_energie_tokens.png", 15.0, "Fig. 6 — Énergie estimée par requête selon le "
      "modèle et la longueur de réponse, comparée à deux valeurs mesurées publiées."))
S(P("Deux constats ressortent : l'énergie est proportionnelle au nombre de tokens générés, et "
    "la taille du modèle a un effet très fort (facteur ≈ 100 entre 8 Md et 405 Md). Le modèle "
    "MoE, malgré 39 Md de paramètres actifs, est estimé plus énergivore que le modèle dense de "
    "70 Md, car ses 141 Md de paramètres totaux exigent davantage de GPU."))
S(P("<b>Tokens d'entrée.</b> La méthode EcoLogits ne compte que les tokens de sortie. "
    "EcoPrompt les demande quand même à l'utilisateur, les affiche, et propose dans les "
    "paramètres un poids optionnel (0 par défaut), signalé comme hypothèse personnelle non "
    "sourcée s'il est activé.", body_ni))
S(H2("10.2 Valeurs publiées par requête"))
S(T([["Valeur", "Énergie", "Nature", "Conditions", "Source"],
     ["Requête texte médiane Gemini Apps", "0,24 Wh", tag("mesuré"),
      "Production, mai 2025 ; accélérateurs, CPU/DRAM, machines inactives, PUE 1,09", "[2]"],
     ["Génération de texte (modèles ≤ 11 Md)", "0,047 Wh", tag("mesuré"),
      "0,047 kWh / 1 000 requêtes, écart-type 0,03 ; A100, sans traitement par lots", "[3]"],
     ["Génération d'image", "2,907 Wh", tag("mesuré"),
      "2,907 kWh / 1 000 images, écart-type 3,31", "[3]"]],
    [3.7 * cm, 1.7 * cm, 1.5 * cm, 6.4 * cm, 1.5 * cm]))
S(P("Tableau 8 — Valeurs par requête utilisables dans la méthode alternative.", caption))
S(H2("10.3 Inférence, entraînement et impacts indirects"))
S(P("EcoPrompt distingue trois niveaux. L'<b>inférence</b> (réponse aux requêtes) est seule "
    "calculée par défaut. L'<b>entraînement</b> est un coût initial très élevé, partagé ensuite "
    "entre toutes les requêtes ; comme le nombre total de requêtes servies n'est pas publié, il "
    "est présenté séparément, avec un calcul illustratif dont l'hypothèse est choisie par "
    "l'utilisateur. Les <b>impacts indirects</b> (fabrication du matériel, réseau, terminal, "
    "effets rebond) sont hors périmètre et signalés comme tels."))
S(T([["Modèle", "Énergie", "CO<sub>2</sub>e", "Eau", "Nature", "Source"],
     ["GPT-3 (175 Md)", "1 287 MWh", "552 t", "5,4 millions L (dont 0,7 sur site)",
      tag("estimé"), "[5] [4]"],
     ["BLOOM (176 Md)", "433 MWh", "24,7 t (50,5 t avec fabrication et inactivité)", "—",
      tag("mesuré") + " + " + tag("estimé"), "[6]"],
     ["Mistral Large 2", "—", "20 400 t (entraînement + 18 mois d'usage)", "281 000 m³",
      tag("estimé") + " (ACV)", "[7]"]],
    [2.6 * cm, 1.8 * cm, 3.7 * cm, 3.2 * cm, 2.0 * cm, 1.5 * cm]))
S(P("Tableau 9 — Impacts publiés de l'entraînement (contexte, non additionnés par défaut).",
    caption))
S(P("Luccioni et al. (2024) estiment qu'il faut environ <b>592 millions d'inférences</b> de "
    "BLOOMz-7B pour égaler l'énergie de son entraînement et de son ajustement [3] : pour un "
    "modèle très utilisé, l'inférence cumulée peut donc dépasser l'entraînement."))

# ===================== 11. EAU =====================
E(H1(11, "Estimation de la consommation d'eau"))
S(P("Une méthode documentée existe : Li et al. (2025) [4], reprise par EcoLogits [1], "
    "distinguent l'eau évaporée sur site pour le refroidissement (WUE sur site) et l'eau "
    "consommée pour produire l'électricité (WUE hors site, ou EWIF) :"))
S(P("<b>Eau (L) = E<sub>serveur</sub> (kWh) × [WUE<sub>site</sub> + PUE × "
    "WUE<sub>hors site</sub>]</b>", quote))
S(T([["Profil hydrique", "WUE site", "WUE hors site", "Source"],
     ["Moyenne Microsoft, États-Unis", "0,55 L/kWh", "3,142 L/kWh", "Li et al. 2025 [4]"],
     ["Flotte Google 2023–2024 (sur site seulement)", "1,15 L/kWh", "non inclus",
      "Google 2025 [2]"]],
    [6.4 * cm, 2.4 * cm, 2.6 * cm, 3.4 * cm]))
S(P(f"Tableau 10 — Facteurs hydriques ({tag('estimé')}).", caption))
S(P(f"<b>Exemple</b> ({tag('estimé')}) : la requête de référence (70 Md, 400 tokens) correspond "
    f"à <b>{fr(water_li, 2)} mL</b> avec le profil Li et al. Appliquée à la valeur médiane "
    f"Gemini (0,24 Wh) avec le facteur de Google, la même formule donne {fr(water_g, 2)} mL, "
    "proche des 0,26 mL publiés par Google [2], ce qui vérifie la cohérence de "
    "l'implémentation.", body_ni))
S(T([["Valeur publiée par requête", "Eau", "Périmètre", "Nature", "Source"],
     ["Requête médiane Gemini", "0,26 mL", "Sur site uniquement", tag("mesuré"), "[2]"],
     ["GPT-3, moyenne US, requête moyenne", "16,9 mL", "Sur site + électricité", tag("estimé"),
      "[4]"],
     ["Le Chat, réponse de 400 tokens", "45 mL", "ACV (dont fabrication)", tag("estimé"), "[7]"]],
    [5.2 * cm, 1.7 * cm, 3.8 * cm, 2.0 * cm, 2.1 * cm]))
S(P("Tableau 11 — Dispersion des valeurs publiées : un facteur ≈ 170 selon le périmètre.",
    caption))
S(P("Cette dispersion justifie l'affichage systématique de la mention « estimé » et la "
    "possibilité de désactiver l'estimation de l'eau."))

# ===================== 12. ALERTES =====================
E(H1(12, "Système d'alertes environnementales"))
S(P("Le niveau d'alerte est déterminé à partir de l'énergie hebdomadaire estimée. Les seuils "
    "sont une <b>convention pédagogique</b> ("+tag("convention")+"), modifiable dans les "
    "paramètres, et non une limite scientifique. Pour rester interprétables, ils sont aussi "
    "exprimés en « requêtes médianes Gemini » (0,24 Wh, [2])."))
S(T([["Niveau", "Énergie hebdomadaire", "≈ requêtes médianes", "Message"],
     ['<font color="#2E7D32"><b>Vert</b></font>', "&lt; 5 Wh", "&lt; 21",
      "Utilisation sous le seuil défini : continuer de façon raisonnée"],
     ['<font color="#E65100"><b>Orange</b></font>', "5 à 50 Wh", "21 à 208",
      "Empreinte estimée modérée : quelques ajustements simples"],
     ['<font color="#C62828"><b>Rouge</b></font>', "≥ 50 Wh", "≥ 208",
      "« Attention : votre utilisation cumulée de l'intelligence artificielle représente une "
      "empreinte environnementale estimée. Adoptez une utilisation plus responsable. »"]],
    [1.8 * cm, 3.0 * cm, 2.8 * cm, 7.2 * cm]))
S(P("Tableau 12 — Seuils par défaut et messages.", caption))
S(P("Les conseils sont <b>ciblés</b> selon le scénario : génération d'images → réserver aux "
    "besoins réels ; grand modèle → utiliser un modèle plus petit lorsqu'il suffit ; réponses "
    "≥ 800 tokens → demander des réponses concises. S'y ajoutent des conseils généraux : éviter "
    "les requêtes inutiles, regrouper les questions liées, éviter de régénérer des contenus "
    "similaires. Chaque niveau combine couleur, icône et titre textuel, pour ne jamais reposer "
    "sur la couleur seule."))

# ===================== 13. RÉSULTATS =====================
E(H1(13, "Résultats attendus et validation expérimentale"))
S(H2("13.1 Résultats de simulation"))
rows = [["Cas", "Description", "Wh / requête", "Wh / semaine", "kg CO<sub>2</sub>e / an",
         "L d'eau / an", "Alerte"]]
for name, desc, s in SCEN:
    r = calc.compute_impact(s)
    lvl = alerts.classify(r.weekly_wh)
    col = {"vert": "#2E7D32", "orange": "#E65100", "rouge": "#C62828"}[lvl]
    rows.append([name, desc, fr(r.per_request_wh), fr(r.weekly_wh, 1), fr(r.yearly_co2_g / 1000),
                 fr(r.yearly_water_l, 2), f'<font color="{col}"><b>{lvl}</b></font>'])
S(T(rows, [1.6 * cm, 4.2 * cm, 1.8 * cm, 2.0 * cm, 1.9 * cm, 1.8 * cm, 1.4 * cm]))
S(P(f"Tableau 13 — Résultats {tag('estimé')}s (PUE 1,20 ; 473 g CO<sub>2</sub>e/kWh ; profil "
    "hydrique Li et al.).", caption))
S(FIG(ASSETS / "graph_scenarios.png", 14.5, "Fig. 9 — Énergie annuelle estimée de quatre "
      "scénarios (échelle logarithmique)."))
S(P("L'écart entre un usage sobre et un usage intensif atteint un facteur supérieur à 3 000. "
    "Le choix du modèle et la longueur des réponses pèsent davantage que le nombre de requêtes."))
S(FIG(ASSETS / "capture_dashboard.png", 12.5, "Fig. 7 — Tableau de bord environnemental "
      "(historique de démonstration fictif de 8 semaines)."))
S(H2("13.2 Validation par comparaison avec des valeurs publiées"))
S(P("Aucune mesure physique n'a été réalisée dans ce projet. La validation consiste à vérifier "
    "que les estimations d'EcoPrompt sont du même ordre de grandeur que des valeurs publiées "
    "indépendantes, en gardant à l'esprit que les conditions ne sont pas identiques."))
p8 = per_req("petit", 400)["total_wh"]
S(T([["Comparaison", "EcoPrompt (estimé)", "Valeur publiée", "Remarque"],
     ["Petit modèle (8 Md), 400 tokens", f"{fr(p8)} Wh", "0,047 Wh — texte, ≤ 11 Md [3]",
      "Même ordre de grandeur ; longueur des réponses non contrôlée dans [3]"],
     ["Modèle 70 Md, 400 tokens", f"{fr(r70['total_wh'])} Wh", "0,24 Wh — médiane Gemini [2]",
      "Même ordre de grandeur ; modèle et tokens de Gemini non publiés"],
     ["Eau, 0,24 Wh avec WUE Google", f"{fr(water_g, 3)} mL", "0,26 mL [2]",
      "Écart ≈ 3 % : implémentation cohérente"],
     ["CO<sub>2</sub>e, 70 Md, 400 tokens", f"{fr(co2_world)} g", "0,03 g [2] ; 1,14 g [7]",
      "Encadré par deux périmètres différents (market-based / ACV)"]],
    [3.8 * cm, 2.6 * cm, 3.6 * cm, 4.8 * cm]))
S(P("Tableau 14 — Confrontation des estimations aux valeurs publiées.", caption))
S(H2("13.3 Protocole de validation expérimentale proposé"))
S(P("Pour aller plus loin, un protocole de mesure peut être conduit avec du matériel "
    "accessible : (1) exécuter localement un petit modèle ouvert ; (2) mesurer l'énergie avec "
    "CodeCarbon (logiciel déjà utilisé dans [3] et [6]) ou un wattmètre sur prise ; (3) générer "
    "des réponses de 100, 400 et 1 000 tokens, répétées au moins dix fois ; (4) comparer la "
    "pente énergie/token mesurée à la prédiction d'EcoPrompt. Ce protocole n'a pas encore été "
    "réalisé : il constitue la première perspective du projet (section 16)."))

# ===================== 14. IMPACT SOCIAL =====================
E(H1(14, "Impact social et sensibilisation citoyenne"))
S(P("La page « Mon impact citoyen » permet de simuler des changements d'habitudes et d'en "
    "observer l'effet à l'échelle d'un groupe (classe, promotion, association)."))
base = SCEN[1][2]
from dataclasses import replace  # noqa: E402
alt = replace(base, requests=round(base.requests * 0.7), output_tokens=300, model_key="petit")
alt2 = replace(base, requests=round(base.requests * 0.7), output_tokens=300)
r0, r1, r2 = (calc.compute_impact(x) for x in (base, alt, alt2))
S(P(f"<b>Exemple</b> ({tag('estimé')}) : en partant du scénario « courant », éviter ou "
    "regrouper 30 % des requêtes et raccourcir les réponses de 25 % réduit l'énergie annuelle "
    f"estimée de {fr(calc.relative_reduction(r0.yearly_wh, r2.yearly_wh) * 100, 0)} %. Si "
    "l'on utilise en plus un modèle de 8 Md, la réduction estimée atteint "
    f"{fr(calc.relative_reduction(r0.yearly_wh, r1.yearly_wh) * 100, 0)} %. Pour une classe de "
    f"30 personnes, cela représente environ {fr((r0.yearly_wh - r1.yearly_wh) * 30 / 1000, 1)} "
    f"kWh et {fr((r0.yearly_co2_g - r1.yearly_co2_g) * 30 / 1000, 1)} kg CO<sub>2</sub>e "
    "évités par an selon les hypothèses par défaut.", body_ni))
S(FIG(ASSETS / "capture_impact_citoyen.png", 11.0, "Fig. 10 — Page « Mon impact citoyen »."))
S(BOX("<b>Positionnement.</b> EcoPrompt ne réduit pas automatiquement les émissions : sa "
      "fonction est d'<b>informer, estimer et sensibiliser</b>. Une réduction réelle dépend des "
      "choix des utilisateurs, mais aussi des fournisseurs (efficacité des modèles, énergie "
      "bas-carbone) et des politiques publiques. Un risque d'effet rebond existe : une IA "
      "perçue comme « peu coûteuse » peut être davantage utilisée."))
S(Spacer(1, 6))
S(P("La dimension citoyenne du projet repose sur quatre idées : l'<b>effet d'échelle</b> (un geste "
    "négligeable individuellement devient significatif collectivement) ; les <b>ressources "
    "partagées</b> (électricité et eau prélevées sur des territoires réels) ; la "
    "<b>transparence</b> (exiger des données vérifiables des fournisseurs) ; la <b>sobriété "
    "numérique</b> (utiliser l'IA quand elle apporte une vraie valeur, avec l'outil le plus "
    "léger suffisant)."))

# ===================== 15. LIMITES =====================
E(H1(15, "Limites scientifiques et techniques"))
E(B(["<b>Absence de télémétrie</b> : EcoPrompt n'a accès à aucune mesure des serveurs réellement "
     "utilisés. Il estime l'impact d'un usage déclaré, pas d'une requête individuelle réelle.",
     "<b>Modèle simplifié</b> : EcoLogits suppose des GPU H100, un lot de 64 requêtes, et ne "
     "modélise ni le réseau, ni le stockage, ni les machines inactives [1]. La latence utilise "
     "une formule de repli que la documentation annonce comme amenée à être remplacée.",
     "<b>Taille des modèles commerciaux inconnue</b> : le rattachement d'un service à un profil "
     "de taille est une hypothèse.",
     "<b>Tokens d'entrée</b> non pris en compte par la méthode de référence.",
     "<b>Localisation et heure</b> inconnues : l'intensité carbone varie d'un facteur supérieur "
     "à 20 entre la France et la moyenne mondiale ; elle varie aussi selon l'heure.",
     "<b>Périmètres hétérogènes</b> : les valeurs publiées pour l'eau varient d'un facteur "
     "≈ 170 selon qu'elles incluent ou non l'électricité et la fabrication (tableau 11).",
     "<b>Valeurs fournisseurs non auditées</b> : la mesure de Google [2] est une auto-déclaration ; "
     "l'ACV de Mistral [7] se présente comme une « première approximation ».",
     "<b>Hors périmètre</b> : terminal de l'utilisateur, fabrication (sauf valeurs ACV "
     "citées), entraînement (présenté séparément), effets rebond.",
     "<b>Seuils d'alerte</b> conventionnels, non scientifiques.",
     "<b>Données déclaratives</b> : l'utilisateur estime lui-même son nombre de requêtes et de "
     "tokens."]))

# ===================== 16. PERSPECTIVES =====================
E(H1(16, "Perspectives d'amélioration"))
E(B(["Réaliser le protocole de mesure locale avec CodeCarbon (section 13.3) et publier les "
     "résultats dans le dépôt.",
     "Développer une extension de navigateur comptant automatiquement les requêtes et la "
     "longueur des réponses, sans transmettre leur contenu.",
     "Intégrer l'intensité carbone horaire (par exemple les données éCO2mix de RTE) et la "
     "localisation probable des centres de données.",
     "Ajouter les impacts de fabrication (carbone intrinsèque) lorsque des données fiables "
     "par requête seront disponibles.",
     "Mettre à jour automatiquement les coefficients à chaque nouvelle version d'EcoLogits.",
     "S'aligner sur les référentiels émergents, comme la méthodologie AFNOR Frugal AI utilisée "
     "par Mistral AI [7].",
     "Proposer une version anglaise et espagnole, et un mode « atelier » pour les classes."]))

# ===================== 17. CONCLUSION =====================
E(H1(17, "Conclusion"))
S(P("Le projet EcoPrompt répond à la problématique en rendant visible un impact habituellement "
    "invisible. L'application estime l'énergie, les émissions de CO<sub>2</sub>e et l'eau "
    "associées à un usage de l'IA à partir d'une méthode publiée, avec des paramètres sourcés "
    "et modifiables ; elle les traduit en indicateurs, en graphiques et en alertes "
    "compréhensibles ; elle propose des gestes concrets et en montre l'effet à l'échelle d'un "
    "groupe."))
S(P("Les principaux enseignements sont que <b>la taille du modèle et la longueur des réponses "
    "comptent davantage que le nombre de requêtes</b>, que <b>la localisation des serveurs peut "
    "changer le bilan carbone d'un facteur supérieur à 20</b>, et que <b>les données publiques "
    "restent rares et hétérogènes</b>. L'application est fonctionnelle, testée (59 tests "
    "réussis), exécutable localement sans service payant et documentée pour être publiée sur "
    "GitHub."))
S(P("L'objectif du projet est atteint dans son périmètre : EcoPrompt n'est pas un instrument de "
    "mesure, mais un outil d'estimation honnête et de sensibilisation, qui invite chacun à "
    "« comprendre son impact, et utiliser l'IA autrement »."))

# ===================== 18. BIBLIOGRAPHIE =====================
E(H1(18, "Bibliographie et sources scientifiques"))
S(P("Sources consultées et vérifiées le 6 novembre 2026.", small))
refs = [
    ("ecologits", "[1]"), ("google2025", "[2]"), ("luccioni2024", "[3]"), ("li2025", "[4]"),
    ("patterson2021", "[5]"), ("luccioni2023", "[6]"), ("mistral2025", "[7]"),
    ("iea2025", "[8]"), ("ember2025", "[9]"), ("rte2024", "[10]"), ("owid2026", "[11]"),
    ("meta2024", "[12]"), ("mistral2024", "[13]")]
ref_style = ParagraphStyle("ref", parent=body_ni, fontSize=9, leading=12.5, leftIndent=0.9 * cm,
                           firstLineIndent=-0.9 * cm, spaceAfter=5, alignment=TA_LEFT)
for key, n in refs:
    s = cfg.SOURCES[key]
    doi = f" DOI : {s['doi']}." if s.get("doi") else ""
    S(P(f"<b>{n}</b>&nbsp;&nbsp;{s['citation']}{doi} <i>{s['type']}</i>, {s['date']}. "
        f"<font color='#1155CC'>{s['url']}</font>", ref_style))
S(Spacer(1, 8))
S(P("Note : la page web de l'IEA n'étant pas accessible lors de la vérification, les chiffres de "
    "[8] ont été contrôlés via leur reprise par <i>Scientific American</i> (10 avril 2025).",
    small))
S(PageBreak())
S(P("<b>Annexe — Galerie de l'application</b>", h2))
S(FIG(ASSETS / "capture_comparaison.png", 11.5, "Fig. 8 — Page « Comparer des scénarios »."))
S(FIG(ASSETS / "capture_methodologie.png", 10.5, "Fig. 11 — Page « Méthodologie et sources »."))

# Garder chaque tableau avec sa légende (pas de tableau coupé de sa légende)
grouped = []
i = 0
while i < len(story):
    f = story[i]
    nxt = story[i + 1] if i + 1 < len(story) else None
    if isinstance(f, Table) and isinstance(nxt, Paragraph) and nxt.style.name == "cap":
        grouped.append(KeepTogether([f, nxt]))
        i += 2
        continue
    grouped.append(f)
    i += 1

doc.build(grouped)
print(f"PDF généré : {OUT}")
