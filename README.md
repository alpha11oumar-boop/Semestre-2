# DBR Job Intelligence Pro

> Application d'analyse d'offres d'emploi avec matching CV automatique, scraping en temps réel et alertes bureau.

---

## Description du projet

**DBR Job Intelligence Pro** est une application web développée avec **Streamlit** qui permet à un chercheur d'emploi de :

- Charger son **CV au format PDF** et en extraire automatiquement les compétences et outils maîtrisés
- Lancer un **scraping en temps réel** sur le portail France Travail pour trouver des offres correspondant à un poste et une ville
- Calculer un **score de matching (%)** entre chaque offre et le profil du candidat
- Recevoir des **alertes bureau** (notifications système) pour les nouvelles offres avec un score ≥ 50%
- Visualiser les résultats dans un **tableau interactif** et un **graphique circulaire** détaillé

---

## Structure du projet

```
dbr-job-intelligence/
│
├── .venv/                       # Environnement virtuel (exclu du git)
├── .gitignore                   # Fichiers à ignorer par Git
├── requirements.txt             # Liste des dépendances Python
├── README.md                    # Documentation du projet
│
├── app_veille_job.py                       # Script principal (Streamlit)
│
├── data/
│   └── dbr_historique.sqlite    # Base de données locale (exclue du git)
│
├── docs/
│   └── README.html              # Version HTML de la documentation
│
└── assets/
    └── cv_exemple.pdf           # Exemple de CV (optionnel)
```

### Fichier .gitignore

```
# Environnement virtuel
.venv/

# Base de données locale
data/
*.sqlite

# Cache Python
__pycache__/
*.pyc
*.pyo

# Fichiers système
.DS_Store
Thumbs.db

# CV et données personnelles
assets/*.pdf

# Variables d'environnement
.env
```

---

## Installation

### Prérequis

- Python
- Google Chrome installé sur la machine
- `pip`

### Étapes

Avant de commencer le développement, un environnement virtuel a été créé via le terminal (cmd) afin d'isoler les dépendances du projet :

```bash
# 1. Créer l'environnement virtuel
python -m venv .venv

# 2. Activer l'environnement virtuel
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # macOS / Linux
```

Une fois l'environnement activé, le prompt du terminal affiche `(.venv)` pour confirmer que l'environnement est bien actif.

```bash
# 3. Cloner le dépôt
git clone https://github.com/votre-utilisateur/dbr-job-intelligence.git
cd dbr-job-intelligence

# 4. Installer les dépendances
pip install -r requirements.txt

# 5. Lancer l'application
streamlit run app_veille_job.py
```

L'application s'ouvre dans votre navigateur à l'adresse `http://localhost:8501`.

---

## Exemples d'utilisation

### 1. Analyser des offres de Data Scientist à Strasbourg

1. Ouvrez l'application dans votre navigateur
2. Dans la barre latérale gauche, chargez votre CV au format PDF
3. Renseignez le poste : `Data Scientist`, la ville : `Strasbourg`, et sélectionnez le type de contrat (ex : `Alternance`)
4. Cliquez sur **"Lancer la recherche"**
5. Les 10 premières offres s'affichent triées par score de matching décroissant
6. Sélectionnez une entreprise pour voir l'analyse détaillée

### 2. Recevoir une alerte bureau

Dès qu'une nouvelle offre présente un score ≥ 50%, une notification système s'affiche automatiquement avec le nom de l'entreprise et le score.

---

## Dépendances

| Bibliothèque | Usage |
|---|---|
| `streamlit` | Interface web interactive |
| `pandas` | Manipulation des données tabulaires |
| `pdfplumber` | Extraction de texte depuis les CV PDF |
| `sqlite3` | Base de données locale pour l'historique des offres |
| `selenium` | Scraping dynamique du portail France Travail |
| `webdriver-manager` | Gestion automatique du driver Chrome |
| `plotly` | Graphiques interactifs (camembert de matching) |
| `plyer` | Notifications bureau système |
| `re` | Traitement des expressions régulières |

### Fichier requirements.txt

Ce fichier liste toutes les bibliothèques tierces à installer. Il se trouve à la racine du projet :

```
streamlit
pandas
pdfplumber
selenium
webdriver-manager
plotly
plyer
```

> `sqlite3` et `re` sont inclus dans la bibliothèque standard Python — aucune installation requise.

---

## Avertissement légal

> **Ce projet est destiné à un usage strictement personnel et éducatif.**

### Scraping web

Cette application effectue un scraping automatisé du portail [France Travail](https://candidat.francetravail.fr). Ce type d'accès peut être soumis aux Conditions Générales d'Utilisation du site. Il est recommandé de ne pas effectuer un nombre excessif de requêtes, de respecter les délais entre les appels et de consulter les CGU avant toute utilisation intensive.

### Données personnelles

Le CV chargé dans l'application est traité **localement sur votre machine**. Aucune donnée personnelle n'est envoyée vers un serveur externe. Conformément au **RGPD**, l'utilisateur est seul responsable du traitement des données personnelles qu'il charge dans l'application.

### Responsabilité

L'auteur ne saurait être tenu responsable de tout dommage direct ou indirect résultant de l'utilisation de ce logiciel. Ce projet est fourni **"tel quel"**, sans garantie d'aucune sorte.

---

## Code documenté

Le fichier `app_veille_job.py` est organisé en 5 blocs fonctionnels distincts. Voici une description des fonctions principales :

### 1. Initialisation de la base de données

La fonction `init_db()` crée la base de données SQLite `dbr_historique.sqlite` si elle n'existe pas encore. Elle contient une table `historique` qui stocke les liens des offres déjà vues, afin d'éviter les doublons et de détecter les nouvelles offres.

### 2. Détection des nouvelles offres

La fonction `check_and_save_new_job(lien_offre)` vérifie si un lien d'offre est déjà présent dans la base de données. Si ce n'est pas le cas, elle l'enregistre et retourne `True` pour signaler qu'il s'agit d'une nouvelle offre.

### 3. Envoi des notifications bureau

La fonction `envoyer_alerte_bureau(entreprise, poste, score)` envoie une notification système sur le bureau de l'utilisateur via la bibliothèque `plyer`. Elle est déclenchée automatiquement lorsqu'une nouvelle offre présente un score de matching supérieur ou égal à 50%. La notification affiche le nom de l'entreprise, le poste recherché et le score obtenu. En cas d'échec, la fonction échoue silencieusement sans bloquer l'application.

```python
def envoyer_alerte_bureau(entreprise, poste, score):
    try:
        notification.notify(
            title=f"Nouvelle Offre : {entreprise}",
            message=f"Match : {score}% pour {poste}",
            app_name="DBR Job Scraper",
            timeout=5
        )
    except: pass
```

### 4. Extraction du profil CV

La fonction `extraire_profil(texte)` analyse le texte brut du CV et recherche la présence de mots-clés prédéfinis (outils informatiques et compétences métier) via des expressions régulières. Elle retourne deux listes : les outils détectés et les compétences détectées.

### 5. Moteur de scraping

La fonction `moteur_scraping()` pilote un navigateur Chrome en mode headless via Selenium pour interroger le portail France Travail. Pour chaque offre trouvée, elle extrait le nom de l'entreprise et le descriptif du poste, calcule le score de matching avec le profil du CV, et déclenche une alerte bureau si l'offre est nouvelle et pertinente.

---

## Difficultés rencontrées

Des tentatives de scraping ont été effectuées sur **HelloWork** et **Indeed**, sans succès pour les raisons suivantes :

- **Blocage anti-bot** : ces plateformes utilisent des systèmes de détection automatisés (Cloudflare, CAPTCHA, fingerprinting) qui bloquent les navigateurs headless
- **Structure HTML dynamique** : le contenu est chargé via JavaScript de manière asynchrone, rendant l'extraction instable
- **Extraction imprécise sur France Travail** : l'ensemble du descriptif d'une offre est regroupé dans une seule balise HTML (`div[itemprop="description"]`), sans sous-structure distincte. Il est donc impossible de différencier automatiquement les compétences obligatoires des compétences souhaitées, ce qui peut introduire des imprécisions dans le score de matching.

Le projet s'appuie finalement uniquement sur **France Travail**, dont le portail s'est révélé plus accessible.

---

## Informations complémentaires

### Limites connues

- **Matching basé sur des mots-clés fixes** : la détection des compétences repose sur une liste de mots-clés codée en dur. Toute compétence absente de cette liste ne sera jamais détectée.
- **Connexion internet requise** : l'application nécessite une connexion internet active pour scraper le portail France Travail.
- **Limite des 10 offres** : le scraper est volontairement limité aux 10 premières offres retournées par France Travail.
- **Compatibilité des alertes bureau** : les notifications via `plyer` peuvent ne pas fonctionner de manière identique selon le système d'exploitation, notamment sur certaines distributions Linux.
- **Persistance de l'historique** : la base de données SQLite s'accumule au fil des recherches. Il n'existe pas de bouton dans l'interface pour réinitialiser l'historique — une suppression manuelle du fichier `dbr_historique.sqlite` est nécessaire si besoin.

---

## Auteurs

Projet développé dans le cadre d'un usage personnel d'aide à la recherche d'emploi.

| Nom | Prénom |
|---|---|
| BAH | Alpha Oumar |
| GNINGUE | Yaye Fatou |
| DIALLO | Alpha Oumar |
