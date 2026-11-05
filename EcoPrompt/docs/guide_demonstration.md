# Guide de démonstration orale — EcoPrompt

**Durée conseillée : 10 minutes + 5 minutes de questions.**
Matériel : ordinateur avec l'application lancée (`streamlit run app.py`), rapport PDF ouvert en secours, captures dans `assets/` si la démo échoue.

## Avant la soutenance (J-1)

- [ ] `pip install -r requirements.txt` puis `python -m pytest -q` → **59 passed**.
- [ ] `streamlit run app.py` : l'application s'ouvre sur http://localhost:8501.
- [ ] Tableau de bord → cliquer « Charger un historique de démonstration (8 semaines) ».
- [ ] Paramètres remis par défaut (PUE 1,20 ; monde 473 g CO₂e/kWh ; profil eau Li et al.).
- [ ] Mode plein écran du navigateur, zoom à 110 %.

## Déroulé minuté

| Temps | Partie | Écran |
|---|---|---|
| 0:00 – 1:30 | 1. Problématique | Rapport, tableau 1 |
| 1:30 – 2:30 | 2. Objectif | Rapport, tableau 2 |
| 2:30 – 7:00 | 3. Démonstration pratique | Application |
| 7:00 – 8:30 | 4. Résultats | Comparer des scénarios, tableau 14 |
| 8:30 – 9:30 | 5. Impact sociétal | Mon impact citoyen |
| 9:30 – 10:00 | 6. Conclusion | Page d'accueil (slogan) |

### 1. Problématique (1 min 30)

> « Chaque fois que nous posons une question à une IA, un serveur consomme de l'électricité et parfois de l'eau. Selon l'Agence internationale de l'énergie, les centres de données ont consommé environ 415 TWh en 2024, soit 1,5 % de l'électricité mondiale, et pourraient atteindre 945 TWh en 2030. Pourtant, l'utilisateur ne voit rien de cet impact. D'où notre problématique : **comment sensibiliser les utilisateurs à l'impact environnemental de leurs interactions avec l'IA ?** »

Insister sur les trois obstacles : invisibilité, effet d'échelle, opacité des fournisseurs.

### 2. Objectif (1 min)

> « EcoPrompt doit estimer, visualiser et signaler l'énergie, le CO₂ et l'eau liés à un usage de l'IA, avec des formules publiées et des sources vérifiables, sans service payant, et en distinguant toujours ce qui est mesuré de ce qui est estimé. »

### 3. Démonstration pratique (4 min 30)

1. **Simulation** — laisser les valeurs par défaut (15 requêtes/jour, modèle 70 Md, 400 tokens) → *Estimer mon impact*.
   - Lire : ≈ 0,263 Wh par requête, 27,6 Wh par semaine, alerte **orange**.
   - Montrer le badge « Valeurs estimées » et le graphique de décomposition (GPU / serveur / PUE).
2. **Changer le modèle** → « Grand modèle 405 Md » → l'énergie par requête passe à ≈ 3,7 Wh, alerte **rouge**, conseil ciblé « utilisez un modèle plus petit ».
3. **Changer la méthode** → « Valeur publiée » → « Requête médiane Gemini » : 0,24 Wh, valeur **mesurée** par Google. Souligner que les deux méthodes donnent le même ordre de grandeur.
4. **Paramètres** → passer l'intensité carbone de « Monde » à « France (RTE) » → retour à Simulation : le CO₂ est divisé par ≈ 22. Message : *la localisation compte autant que l'usage*.
5. **Enregistrer** puis **Tableau de bord** : évolution sur 8 semaines (historique fictif annoncé comme tel), répartition des alertes.

### 4. Résultats (1 min 30)

- Page **Comparer des scénarios** : sobre 0,04 kWh/an → intensif 133 kWh/an (facteur > 3 000).
- Trois enseignements : la **taille du modèle** et la **longueur des réponses** pèsent plus que le nombre de requêtes ; la **localisation** peut changer le CO₂ d'un facteur > 20 ; les **données publiques sont rares et hétérogènes** (eau : 0,26 mL à 45 mL selon le périmètre).
- Validation : tableau 14 du rapport (même ordre de grandeur que Google 2025 et Luccioni 2024 ; écart de 3 % sur l'eau) + 59 tests automatisés réussis.

### 5. Impact sociétal (1 min)

- Page **Mon impact citoyen** : −30 % de requêtes, −25 % de longueur, modèle plus petit → ≈ −93 % d'énergie estimée ; pour 30 personnes ≈ 40 kWh et 19 kg CO₂e évités par an (estimation).
- Phrase clé : « EcoPrompt ne réduit pas les émissions à lui seul : **il informe, estime et sensibilise**. La réduction dépend de nos choix, de ceux des fournisseurs et des politiques énergétiques. »

### 6. Conclusion (30 s)

> « EcoPrompt rend visible un impact invisible, avec honnêteté sur ses limites. Il est libre, local, testé et publiable sur GitHub. Notre message tient dans le slogan : **comprendre son impact, utiliser l'IA autrement.** »

## Questions probables du jury

| Question | Réponse courte |
|---|---|
| D'où viennent vos chiffres ? | Méthode EcoLogits (JOSS 2025), mesures Google 2025 et Luccioni 2024, eau Li et al. 2025, mix Ember/RTE. Tout est dans la page « Méthodologie » et dans `config.py`. |
| Connaissez-vous la consommation réelle de ChatGPT ? | Non. Aucun fournisseur ne publie de télémétrie par requête vérifiable (Google publie une médiane auto-déclarée). C'est pourquoi tout est étiqueté « estimé ». |
| Pourquoi ignorer les tokens d'entrée ? | La méthode de référence ne les compte pas ; une hypothèse optionnelle existe, signalée comme non sourcée. |
| Vos seuils d'alerte sont-ils scientifiques ? | Non, c'est une convention pédagogique modifiable, exprimée aussi en « requêtes médianes Gemini » pour rester interprétable. |
| Et l'entraînement ? | Présenté à part (GPT-3 : 1 287 MWh estimés ; BLOOM : 433 MWh), non additionné faute de connaître le nombre total de requêtes servies. |
| Comment valider expérimentalement ? | Protocole proposé : petit modèle local + CodeCarbon ou wattmètre, réponses de 100/400/1 000 tokens, 10 répétitions, comparaison de la pente. |
| Risque d'effet rebond ? | Oui : montrer que l'impact unitaire est faible peut inciter à plus d'usage. D'où l'accent sur l'effet d'échelle et les gestes de sobriété. |

## Plan B si la démo échoue

Ouvrir `assets/capture_simulation.png`, `capture_dashboard.png`, `capture_comparaison.png`, `capture_impact_citoyen.png` et commenter les mêmes étapes.
