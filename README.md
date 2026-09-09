# Projet Deezer

Projet réalisé dans le cadre d'un test technique basé sur l'API publique de Deezer.

<br>

# Auteur

Vincent RICHARD - vincent.richard.contact@gmail.com

<br>

# Technologies

- Python 3.11
- Requests 2.32
- Pandas 2.2
- SciPy 1.14

<br>

# Outils de développement

- Mypy 1.18
- Pytest 8.4

<br>

# Installation

Cloner le dépôt puis installer le projet et ses dépendances (dépendances de développement incluses) :

```bash
git clone https://github.com/dev-Vincent-dev/deezer-technical-test.git
cd deezer-technical-test
python3.11 -m venv .venv
source .venv/bin/activate # Sur Linux / macOS ou...
# .venv\Scripts\activate.bat # Sur Windows (Invite de commandes) ou...
# .venv\Scripts\Activate.ps1 # Sur Windows (PowerShell)
pip install -e ".[dev]"
```

<br>

# Tests et vérification des types

Le projet utilise `pytest` pour les tests et `mypy` pour la vérification statique des types.

```bash
pytest -v  # pour lancer les tests
mypy src/  # pour lancer la vérification des types
```

<br>

# Stratégie de collecte

La collecte est basée sur la recherche de playlists Deezer à partir de mots-clés combinant un genre musical et une année de sortie.

Les requêtes de recherche par mot-clé couvrent cinq genres (Pop, Alternative, Dance, Latino et Country) et trois années (2000, 2010 et 2020), ce qui représente soit 15 requêtes `/search/playlists` au total. Cette stratégie permet de favoriser une répartition relativement équilibrée entre plusieurs genres et années. Les playlists sont ici intéressantes car de nombreuses playlists liées à un genre et une année existent (*Soirée 2000*, *Country music 2019*, *Latino Hits 2026*, etc.)

Avec ces 15 recherches, la collecte de 67 titres uniques par recherche suffirait pour atteindre les 1 000 titres demandés. Or, des doublons peuvent être présents entre les différentes requêtes. J'ai donc fait le choix d'imposer la récupération d'au moins 120 titres uniques par recherche afin de compenser ces éventuels doublons.

Aussi, pour s'assurer d'un bon équilibre entre les genres et années, chaque recherche par mot-clé se poursuit tant que 120 tracks ne sont pas collectées.

L'ordre de collecte est le suivant :\
Playlists -> Tracks -> Albums -> Artists

Des dictionnaires ayant pour clés les ids des Playlists, Tracks, Albums et Artists sont utilisés afin d'éviter des collectes de données identiques et minimiser le nombre de requêtes effectuées.

Une fois toutes les données collectées, elles sont assemblées entre elles afin de construire des objets `TrackEnriched`.

<br>

# Choix techniques

- Séparation des responsabilités : client API, logique de collecte et modèles de données indépendants.
- Client HTTP robuste : timeout, retries automatiques et gestion explicite des erreurs API/réseau.
- Pagination et collecte contrôlée : gestion des pages Deezer avec un objectif minimum global et par requête.
- Rate limiting afin de limiter la fréquence des requêtes et réduire les risques de dépassement du quota Deezer
- Déduplication des données : tracks, albums et artistes dédupliqués via leurs identifiants.
- Enrichissement multi-entités : récupération des détails des tracks, albums et artistes.
- Validation et normalisation des données : vérification des types, gestion des champs optionnels et conversion des dates.
- Modèle de données typé avec une dataclass `TrackEnriched`.
- Gestion des données incomplètes : une erreur sur une ressource Deezer ne fait pas échouer inutilement toute la collecte.
- Code configurable et testable : paramètres de collecte, injection du client API et méthodes séparées.
- Export structuré des données collectées vers CSV.
- Monitoring de la collecte en temps réel.