"""Collecte et enrichissement des données Deezer."""

from datetime import date
from typing import Any
from random import shuffle

from deezer_analytics.deezer_client import DeezerClient, DeezerAPIError
from deezer_analytics.models import TrackEnriched


class DeezerCollector:
    """Collecte un échantillon de titres depuis l'API Deezer."""

    DEFAULT_QUERIES = [
        "pop 2000",
        "pop 2010",
        "pop 2020",
        "alternative 2000",
        "alternative 2010",
        "alternative 2020",
        "dance 2000",
        "dance 2010",
        "dance 2020",
        "latino 2000",
        "latino 2010",
        "latino 2020",
        "country 2000",
        "country 2010",
        "country 2020"
    ]

    def __init__(
        self,
        client: DeezerClient,
        target_size: int = 1000,
        target_size_per_query: int = 120,
        queries: list[str] = DEFAULT_QUERIES,
        playlist_page_size: int = 40,
    ) -> None:
        """Initialise le collecteur Deezer.

        Args:
            client: Client utilisé pour communiquer avec l'API Deezer.
            target_size: Nombre minimum de titres uniques à collecter
                         au total.
            target_size_per_query: Nombre minimum de titres à collecter
                                   pour chaque requête.
            queries: Requêtes utilisées pour rechercher des playlists.
            playlist_page_size: Nombre de playlists demandées par page.

        Raises:
            ValueError: Si un paramètre possède une valeur invalide.
        """
        if target_size <= 0:
            raise ValueError("target_size doit être supérieur à zéro.")

        if target_size_per_query <= 0:
            raise ValueError(
                "target_size_per_query doit être supérieur à zéro."
            )

        if not queries:
            raise ValueError("Au moins une requête doit être fournie.")

        if playlist_page_size <= 0:
            raise ValueError(
                "playlist_page_size doit être supérieur à zéro."
            )

        self._client = client
        self._target_size = target_size
        self._target_size_per_query = target_size_per_query
        self._queries = queries
        self._playlist_page_size = playlist_page_size

    def _add_playlist_tracks(
        self,
        tracks_by_id: dict[int, dict[str, Any]],
        query_track_ids: set[int],
        playlist_data: dict[str, Any],
    ) -> None:
        """Ajoute les titres d'une playlist aux collections.

        Args:
            tracks_by_id: Dictionnaire global des titres indexés par ID.
            query_track_ids: IDs des titres déjà trouvés pour la query.
            playlist_data: Données JSON de la playlist.
        """
        tracks_data = playlist_data.get("tracks")

        if not isinstance(tracks_data, dict):
            return

        tracks = tracks_data.get("data")

        if not isinstance(tracks, list):
            return

        for track in tracks:
            if not isinstance(track, dict):
                continue

            track_id = track.get("id")

            if not isinstance(track_id, int):
                continue

            if track_id not in tracks_by_id:
                # La track dont l'id est track_id n'a jamais été
                # collectée. Cela est sûr car elle ne fait pas partie
                # de tracks_by_id. Donc on l'ajoute.
                tracks_by_id[track_id] = track
                query_track_ids.add(track_id)

            if len(query_track_ids) >= self._target_size_per_query:
                # On stope l'ajout de nouvelles tracks
                break

    def _collect_tracks_from_playlists(self) -> list[dict[str, Any]]:
        """Collecte les titres uniques provenant des playlists.

        Chaque requête tente de collecter au moins
        target_size_per_query titres.

        Returns:
            Liste de données JSON de titres uniques.
        """
        tracks_by_id: dict[int, dict[str, Any]] = {}

        for query in self._queries:
            query_track_ids: set[int] = set()
            index = 0

            while len(query_track_ids) < self._target_size_per_query:
                result = self._client.search_playlists(
                    query=query,
                    index=index,
                    limit=self._playlist_page_size,
                )

                playlists = result.get("data")

                if not isinstance(playlists, list) or not playlists:
                    break

                for playlist in playlists:
                    if not isinstance(playlist, dict):
                        continue

                    playlist_id = playlist.get("id")
                    
                    if not isinstance(playlist_id, int):
                        continue

                    playlist_data = self._client.get_playlist(playlist_id)

                    self._add_playlist_tracks(
                        tracks_by_id=tracks_by_id,
                        query_track_ids=query_track_ids,
                        playlist_data=playlist_data,
                    )
                    
                    if len(query_track_ids) >= self._target_size_per_query:
                        # On quitte la collecte depuis la page actuelle...
                        break

                if len(query_track_ids) >= self._target_size_per_query:
                    # ... et on quitte l'étude de la requête actuelle
                    break

                if len(playlists) < self._playlist_page_size:
                    # Dernière page de la requête atteinte
                    break

                index += self._playlist_page_size

            print(
                f"Requête '{query}' terminée :",
                f"{len(query_track_ids)} nouvelles tracks uniques ajoutées"
            )

        return list(tracks_by_id.values())

    def _collect_track_details(
        self,
        tracks: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Récupère les informations détaillées de chaque titre.

        Cette étape permet notamment de récupérer le BPM et la date
        de sortie du titre.

        Args:
            tracks: Données JSON des titres collectés.

        Returns:
            Données détaillées des titres.
        """
        tracks_with_details: list[dict[str, Any]] = []

        for track in tracks:
            track_id = track.get("id")

            if not isinstance(track_id, int):
                continue

            detailed_track = self._client.get_track(track_id)

            tracks_with_details.append(detailed_track)

        return tracks_with_details

    @staticmethod
    def _extract_ids(
        tracks: list[dict[str, Any]],
        entity_key: str,
    ) -> set[int]:
        """Extrait les identifiants uniques d'une entité liée aux tracks.

        Args:
            tracks: Données JSON des titres collectés.
            entity_key: Clé de l'entité liée, par exemple album ou artist.

        Returns:
            Ensemble d'identifiants uniques.
        """
        ids: set[int] = set()

        for track in tracks:
            entity = track.get(entity_key)

            if not isinstance(entity, dict):
                continue

            entity_id = entity.get("id")

            if isinstance(entity_id, int):
                ids.add(entity_id)

        return ids

    def _collect_albums(
        self,
        tracks: list[dict[str, Any]],
    ) -> dict[int, dict[str, Any]]:
        """Récupère les informations des albums utilisés par les tracks.

        Args:
            tracks: Données JSON détaillées des titres collectés.

        Returns:
            Albums indexés par leur identifiant Deezer.
        """
        album_ids = self._extract_ids(tracks, "album")

        albums: dict[int, dict[str, Any]] = {}

        for album_id in album_ids:
            try:
                albums[album_id] = self._client.get_album(album_id)
            except DeezerAPIError:
                continue

        return albums

    def _collect_artists(
        self,
        tracks: list[dict[str, Any]],
    ) -> dict[int, dict[str, Any]]:
        """Récupère les informations des artistes utilisés par les tracks.

        Args:
            tracks: Données JSON détaillées des titres collectés.

        Returns:
            Artistes indexés par leur identifiant Deezer.
        """
        artist_ids = self._extract_ids(tracks, "artist")

        artists: dict[int, dict[str, Any]] = {}

        for artist_id in artist_ids:
            try:
                artists[artist_id] = self._client.get_artist(artist_id)
            except DeezerAPIError:
                continue

        return artists

    @staticmethod
    def _get_related_entity(
        track: dict[str, Any],
        entity_key: str,
        entities: dict[int, dict[str, Any]],
    ) -> dict[str, Any] | None:
        """Récupère une entité liée à partir de son identifiant.

        Args:
            track: Données JSON du titre.
            entity_key: Clé de l'entité liée.
            entities: Entités indexées par leur identifiant.

        Returns:
            Données de l'entité ou None si elle est introuvable.
        """
        entity = track.get(entity_key)

        if not isinstance(entity, dict):
            return None

        entity_id = entity.get("id")

        if not isinstance(entity_id, int):
            return None

        return entities.get(entity_id)

    def _build_enriched_tracks(
        self,
        tracks: list[dict[str, Any]],
        albums: dict[int, dict[str, Any]],
        artists: dict[int, dict[str, Any]],
    ) -> list[TrackEnriched]:
        """Construit les tracks enrichis à partir des données collectées.

        Args:
            tracks: Données JSON détaillées des titres.
            albums: Albums indexés par leur identifiant.
            artists: Artistes indexés par leur identifiant.

        Returns:
            Liste de tracks enrichis.
        """
        enriched_tracks: list[TrackEnriched] = []

        for track in tracks:
            album = self._get_related_entity(
                track,
                "album",
                albums,
            )
            artist = self._get_related_entity(
                track,
                "artist",
                artists,
            )

            if album is None or artist is None:
                # Si l'album ou l'artiste sont inconnus,
                # alors il est inutile de conserver le track
                continue

            try:
                enriched_track = self._build_track(
                    track_data=track,
                    album_data=album,
                    artist_data=artist,
                )
            except ValueError as error:
                raise ValueError(
                    f"Impossible de construire le track "
                    f"{track.get('id')}: {error}"
                ) from error

            enriched_tracks.append(enriched_track)

        return enriched_tracks

    @staticmethod
    def _require_int(data: dict[str, Any], key: str) -> int:
        """Récupère un entier obligatoire dans un dictionnaire.

        Args:
            data: Dictionnaire contenant la donnée.
            key: Clé de la donnée recherchée.

        Returns:
            Valeur entière associée à la clé.

        Raises:
            ValueError: Si la donnée est absente ou invalide.
        """
        
        value = data.get(key)

        if not isinstance(value, int):
            raise ValueError(f"Le champ '{key}' est invalide.")

        return value

    @staticmethod
    def _require_str(data: dict[str, Any], key: str) -> str:
        """Récupère une chaîne obligatoire dans un dictionnaire.

        Args:
            data: Dictionnaire contenant la donnée.
            key: Clé de la donnée recherchée.

        Returns:
            Valeur textuelle associée à la clé.

        Raises:
            ValueError: Si la donnée est absente ou invalide.
        """
        value = data.get(key)

        if not isinstance(value, str):
            raise ValueError(f"Le champ '{key}' est invalide.")

        return value

    @staticmethod
    def _optional_str(value: Any) -> str | None:
        """Convertit une valeur en chaîne si elle est disponible.

        Args:
            value: Valeur à convertir.

        Returns:
            Chaîne de caractères ou None si la valeur est absente.
        """
        return value if isinstance(value, str) else None

    @staticmethod
    def _optional_float(value: Any) -> float | None:
        """Convertit une valeur en nombre flottant si elle est disponible.

        Args:
            value: Valeur à convertir.

        Returns:
            Valeur flottante ou None si la valeur est absente ou invalide.
        """
        if isinstance(value, (int, float)):
            return float(value)

        return None

    @staticmethod
    def _parse_date(value: Any) -> date | None:
        """Convertit une date Deezer en objet date.

        Args:
            value: Date au format YYYY-mm-dd.

        Returns:
            Date convertie ou None si la valeur est absente ou invalide.
        """
        if not isinstance(value, str):
            return None

        try:
            return date.fromisoformat(value)
        except ValueError:
            return None

    @staticmethod
    def _parse_genres(value: Any) -> tuple[str, ...] | None:
        """Extrait les noms des genres d'une réponse Deezer.

        Args:
            value: Données JSON du champ genres.

        Returns:
            Tuple contenant les noms des genres disponibles.
        """
        if not isinstance(value, dict):
            return None

        genres = value.get("data")

        if not isinstance(genres, list):
            return None

        return tuple(
            genre["name"]
            for genre in genres
            if isinstance(genre, dict)
            and isinstance(genre.get("name"), str)
        )

    @staticmethod
    def _build_track(
        track_data: dict[str, Any],
        album_data: dict[str, Any],
        artist_data: dict[str, Any],
    ) -> TrackEnriched:
        """Construit un TrackEnriched à partir des données Deezer.

        Args:
            track_data: Données JSON du titre.
            album_data: Données JSON de l'album.
            artist_data: Données JSON de l'artiste.

        Returns:
            Titre enrichi avec ses informations d'album et d'artiste.

        Raises:
            ValueError: Si une donnée obligatoire est absente ou invalide.
        """
        return TrackEnriched(
            id=DeezerCollector._require_int(track_data, "id"),
            title=DeezerCollector._require_str(track_data, "title"),
            duration=DeezerCollector._require_int(track_data, "duration"),
            bpm=DeezerCollector._optional_float(track_data.get("bpm")),
            release_date=DeezerCollector._parse_date(
                track_data.get("release_date")
            ),
            rank=DeezerCollector._require_int(track_data, "rank"),
            album_id=DeezerCollector._require_int(album_data, "id"),
            album_title=DeezerCollector._require_str(
                album_data,
                "title",
            ),
            album_release_date=DeezerCollector._parse_date(
                album_data.get("release_date")
            ),
            album_genres=DeezerCollector._parse_genres(
                album_data.get("genres")
            ),
            album_label=DeezerCollector._optional_str(
                album_data.get("label")
            ),
            album_duration=DeezerCollector._require_int(
                album_data,
                "duration",
            ),
            album_nb_fan=DeezerCollector._require_int(
                album_data,
                "fans",
            ),
            album_record_type=DeezerCollector._optional_str(
                album_data.get("record_type")
            ),
            artist_id=DeezerCollector._require_int(
                artist_data,
                "id",
            ),
            artist_name=DeezerCollector._require_str(
                artist_data,
                "name",
            ),
            artist_nb_album=DeezerCollector._require_int(
                artist_data,
                "nb_album",
            ),
            artist_nb_fan=DeezerCollector._require_int(
                artist_data,
                "nb_fan",
            ),
        )

    def collect(self) -> list[TrackEnriched]:
        """Collecte et enrichit les titres Deezer.

        Returns:
            Liste de titres uniques enrichis avec leurs données
            d'album et d'artiste.

        Raises:
            ValueError: Si suffisamment de titres ne peuvent pas être
                        collectés.
        """
        tracks = self._collect_tracks_from_playlists()

        if len(tracks) < self._target_size:
            raise ValueError(
                f"Impossible de collecter {self._target_size} titres "
                f"uniques. Seulement {len(tracks)} titres ont été trouvés."
            )

        tracks = self._collect_track_details(tracks)
        print("Collecte des données Tracks terminée")
        albums = self._collect_albums(tracks)
        print("Collecte des données Albums terminée")
        artists = self._collect_artists(tracks)
        print("Collecte des données Artists terminée")

        enriched_tracks = self._build_enriched_tracks(
            tracks=tracks,
            albums=albums,
            artists=artists,
        )
        print(
            "Enrichissement des données Tracks",
            "avec les données Albums et Artists terminé :",
            f"{len(enriched_tracks)} tracks enrichies"
        )

        if len(enriched_tracks) < self._target_size:
            raise ValueError(
                f"Impossible de construire {self._target_size} titres "
                f"enrichis. Seulement {len(enriched_tracks)} sont valides."
            )

        return enriched_tracks
