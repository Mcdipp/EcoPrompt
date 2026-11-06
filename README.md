# EcoPrompt
Dans le cadre de ce projet, une application Python nommée EcoPrompt a été conçue, développée et testée. Elle permet d'estimer, de visualiser et de signaler l'empreinte environnementale (énergie, émissions de CO2 e, eau) associée à l'utilisation d'outils d'intelligence artificielle générative.

#Objectif
Estimer l'énergie (Wh), le CO₂e (g) et l'eau (L) liés à un usage déclaré de l'IA, avec des formules transparentes.
Alerter (vert / orange / rouge) avec des seuils configurables et des conseils concrets.
Comparer des scénarios d'usage et montrer l'effet d'habitudes plus sobres.
Fournir un outil simple et reproductible.

#Technologies utilisées
Python 3.10+ · Streamlit (interface) · Pandas (données) · Plotly (graphiques interactifs) · SQLite (historique local, bibliothèque standard) · Pytest (tests).

#Archi du projet

EcoPrompt/
├── app.py              # Interface Streamlit
├── calculations.py     # Formules EcoLogits, CO₂, eau, validation des entrées 
├── alerts.py           # Niveaux d'alerte configurables et conseils
├── data_manager.py     # Historique SQLite (ajout, lecture, export CSV)
├── config.py           # Parametres + bibliographie (chaque valeur avec une source)
├── requirements.txt
├── README.md
├── LICENSE             
├── .gitignore
├── .streamlit/config.toml   
├── data/               
├── tests/              
├── docs/               
└── assets/             
