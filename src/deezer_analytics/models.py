"""Modèles de données utilisés pour le Projet Deezer."""

from dataclasses import dataclass
from datetime import date

@dataclass(frozen=True)
class TrackEnriched:
    """Représente un titre Deezer enrichi avec son album et son artiste.

    Attributes:
        id: Identifiant unique du titre sur Deezer.
        title: Nom du titre.
        duration: Durée du titre en secondes.
        bpm: BPM du titre, si disponible.
        release_date: Date de sortie du titre, si disponible.
        rank: Rang du titre sur Deezer.
        album_id: Identifiant unique de l'album sur Deezer.
        album_title: Nom de l'album.
        album_release_date: Date de sortie de l'album, si disponible.
        album_genres: Genres musicaux associés à l'album, si disponible.
        album_label: Label de l'album, si disponible.
        album_duration: Durée totale de l'album en secondes.
        album_nb_fan: Nombre de fans de l'album.
        album_record_type: Type de disque de l'album, si disponible.
        artist_id: Identifiant unique de l'artiste sur Deezer.
        artist_name: Nom de l'artiste.
        artist_nb_album: Nombre d'albums de l'artiste.
        artist_nb_fan: Nombre de fans de l'artiste.
    """

    id: int
    title: str
    duration: int
    bpm: float | None
    release_date: date | None
    rank: int

    album_id: int
    album_title: str
    album_release_date: date | None
    album_genres: tuple[str, ...] | None
    album_label: str | None
    album_duration: int
    album_nb_fan: int
    album_record_type: str | None

    artist_id: int
    artist_name: str
    artist_nb_album: int
    artist_nb_fan: int
