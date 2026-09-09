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
- Matplotlib 3.11

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

# Exécution du projet

```bash
python -m deezer_analytics.main_partie_1  # Récupération des données via l'API Deezer

python -m deezer_analytics.main_partie_2  # Analyse des données
```

<br>

# Partie 1 : Récupération des données via l'API Deezer


## Stratégie de collecte

La collecte est basée sur la recherche de playlists Deezer à partir de mots-clés combinant un genre musical et une année de sortie.

Les requêtes de recherche par mot-clé couvrent cinq genres (Pop, Alternative, Dance, Latino et Country) et trois années (2000, 2010 et 2020), ce qui représente soit 15 requêtes `/search/playlists` au total. Cette stratégie permet de favoriser une répartition relativement équilibrée entre plusieurs genres et années. Les playlists sont ici intéressantes car de nombreuses playlists liées à un genre et une année existent (*Soirée 2000*, *Country music 2019*, *Latino Hits 2026*, etc.)

Avec ces 15 recherches, la collecte de 67 titres uniques par recherche suffirait pour atteindre les 1 000 titres demandés. Or, des doublons peuvent être présents entre les différentes requêtes. J'ai donc fait le choix d'imposer la récupération d'au moins 120 titres uniques par recherche afin de compenser ces éventuels doublons.

Aussi, pour s'assurer d'un bon équilibre entre les genres et années, chaque recherche par mot-clé se poursuit tant que 120 tracks ne sont pas collectées.

L'ordre de collecte est le suivant :\
Playlists -> Tracks -> Albums -> Artists

Des dictionnaires ayant pour clés les ids des Playlists, Tracks, Albums et Artists sont utilisés afin d'éviter des collectes de données identiques et minimiser le nombre de requêtes effectuées.

Une fois toutes les données collectées, elles sont assemblées entre elles afin de construire des objets `TrackEnriched`.

<br>

## Choix techniques

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

<br>

# Partie 2 : Analyse des données

## Question 1 : Nombre de fans et popularité des titres

La corrélation de Spearman a été choisie afin de mesurer la relation entre le nombre de fans et la popularité des titres. La corrélation de Pearson n'a pas été choisie car je ne suppose pas de relation linéaire entre ces variables.

Les résultats montrent une corrélation positive et significative entre le nombre de fans et la popularité des titres :

|         |   ρ   |  p-value   |
|---------|-------|------------|
| Artiste | 0.428 | 7.668e-79  |
| Album   | 0.627 | 1.115e-191 |
|         |       |            |

La relation est donc modérée pour les artistes et plus forte pour les albums. Les résultats restent quasiment identiques après agrégation par artiste et par album. Cela indique que cette relation n'est pas uniquement liée au fait que certains artistes ou albums sont représentés par plusieurs titres dans l'échantillon.

Même si ces résultats ne permettent pas d'établir une relation de causalité certaine, on peut conclure que, dans notre échantillon, les titres associés à davantage de fans tendent à être plus populaires sur Deezer, avec une relation plus marquée au niveau des albums.

## Question 2 : Genres, BPM et durée

Les genres les plus représentés ont été identifiés en comptant le nombre de titres associés à chaque genre. Pour les tests statistiques, je n'ai retenu que les genres représentés par au moins 100 titres.

|         |   H    |  p-value  |
|---------|--------|-----------|
| BPM     | 50.450 | 1.179e-08 |
| Durée   | 44.673 | 1.583e-07 |
|         |        |           |

Les résultat des tests de Kruskal-Wallis montre une différence significative entre les genres, aussi bien pour le BPM que pour la durée des titres.

On peut donc en conclure que, dans notre échantillon, le BPM et la durée des titres diffèrent significativement selon le genre musical.

## Question 3 : BPM, durée et popularité

*__Question__ : Existe-t-il des combinaisons de BPM et de durée davantage associées aux titres les plus populaires sur Deezer ?*


Pour étudier cette relation, les titres ont été regroupés par intervalles de 10 BPM et de 30 secondes. Pour chaque combinaison, le rang Deezer médian a été calculé. Un rang élevé correspond à une popularité plus importante sur Deezer.

Les combinaisons présentant les rangs médians les plus élevés sont notamment :

90–100 BPM et 210–240 secondes : rang médian de 757 446, pour 30 titres\
90–100 BPM et 180–210 secondes : rang médian de 719 292, pour 30 titres\
120–130 BPM et 240–270 secondes : rang médian de 708 680, pour 37 titres\
120–130 BPM et 210–240 secondes : rang médian de 664 222, pour 50 titres\
110–120 BPM et 210–240 secondes : rang médian de 619 486, pour 37 titres

Les résultats suggèrent qu'il existe, dans notre échantillon, certaines combinaisons de BPM et de durée associées à des titres plus populaires. Les zones autour de 90–100 BPM et 110–130 BPM, avec des durées principalement comprises entre 3 et 4 minutes, présentent notamment des rangs médians élevés.

Cependant, cette analyse montre une association et non une relation de causalité. Elle ne permet pas à elle-seule de conclure qu'un BPM et une durée particulière rend un titre plus populaire.

De plus, l'échantillon est constitué de titres issus de playlists et donc déjà sélectionnés pour leur popularité. Les titres étudiés sont ainsi globalement populaires et ne représentent pas nécessairement l'ensemble de la diversité musicale disponible. Les résultats peuvent donc être biaisés par cette sélection et ne peuvent pas être généralisés à l'ensemble des titres et genres musicaux.
