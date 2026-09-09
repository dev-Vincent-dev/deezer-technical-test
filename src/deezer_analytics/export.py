import csv
from dataclasses import asdict

from deezer_analytics.models import TrackEnriched

def save_enriched_tracks_to_csv(
    tracks: list[TrackEnriched],
    filepath: str,
) -> None:
    """Sauvegarde les tracks enrichis dans un fichier CSV."""

    if not tracks:
        return

    rows = []

    for track in tracks:
        row = asdict(track)
        if track.album_genres is not None:
            row["album_genres"] = "|".join(track.album_genres)
        else:
            row["album_genres"] = ""
        rows.append(row)

    with open(filepath, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=rows[0].keys(),
        )

        writer.writeheader()
        writer.writerows(rows)
