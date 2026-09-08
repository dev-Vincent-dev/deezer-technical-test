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

# Stratégie de requêtage

Afin de constituer un échantillon d'au moins 1 000 titres, la collecte est basée sur la recherche de playlists Deezer à partir de requêtes combinant un genre musical et une année de sortie.

Les requêtes couvrent cinq genres (Pop, Rock, Indie, Jazz et Electro) sur trois années (2024, 2025 et 2026), soit 15 requêtes `/search/playlists` au total. Cette stratégie permet de favoriser une répartition relativement équilibrée entre plusieurs genres et années. Les playlists sont ici intéressantes car elles permettent de compenser l'impossibilité de l'API de faire des requêtes de tracks filtrées par genre et année.

Pour chaque requête, les playlists retournées sont parcourues avec pagination. Le contenu de chaque playlist est ensuite récupéré afin d'extraire les titres qu'elle contient. Les titres sont dédupliqués à l'aide de leur identifiant Deezer afin qu'un même titre présent dans plusieurs playlists ne soit conservé qu'une seule fois.

Pour atteindre les 1 000 titres demandés, la récupération de 67 titres uniques par requête suffirait (1 000 / 15 ≈ 67). Or, des doublons peuvent être présents entre les différentes requêtes. J'ai donc fait le choix d'imposer la récupération d'au moins 120 titres uniques par requête afin de compenser ces éventuels doublons.

Une fois les titres collectés, les informations détaillées de chaque track sont récupérées via l'API Deezer, notamment le BPM et la date de sortie. Les identifiants uniques des albums et des artistes sont ensuite extraits afin de récupérer leurs informations une seule fois par entité afin d'optimiser le nombre de requêtes exéctuées. Les données des albums et des artistes sont finalement réunies aux données des tracks par identifiant pour construire les objets `TrackEnriched`.

<br>

# Choix techniques

- Séparation des responsabilités : client API, logique de collecte et modèles de données indépendants.
- Client HTTP robuste : timeout, retries automatiques et gestion explicite des erreurs API/réseau.
- Pagination et collecte contrôlée : gestion des pages Deezer avec un objectif minimum global et par requête.
- Déduplication des données : tracks, albums et artistes dédupliqués via leurs identifiants.
- Enrichissement multi-entités : récupération des détails des tracks, albums et artistes.
- Validation et normalisation des données : vérification des types, gestion des champs optionnels et conversion des dates.
- Modèle de données typé avec une dataclass `TrackEnriched`.
- Gestion des données incomplètes : une erreur sur une ressource Deezer ne fait pas échouer inutilement toute la collecte.
- Code configurable et testable : paramètres de collecte, injection du client API et méthodes séparées.
- Export structuré des données collectées vers CSV.
- Monitoring de la collecte en temps réel.

<br>

# Qualité du code

- Annotations de type Python vérifiées avec Mypy
- Documentation en "Google-style docstring"
- Tests automatisés avec Pytest
- Versionnement avec Git