"""Analyse de la relation entre le nombre de fans et la popularité des titres."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import spearmanr


DATA_PATH = Path("data/best_2026-09-09_02-15-29.csv")
OUTPUT_DIR = Path("data/analysis/popularity")


def compute_spearman(
    df: pd.DataFrame,
    x_column: str,
    y_column: str,
) -> tuple[float, float]:
    """Calcule la corrélation de Spearman entre deux colonnes.

    Les lignes contenant des valeurs manquantes dans les deux colonnes
    sont exclues du calcul.

    Returns:
        Un tuple contenant :
        - le coefficient de corrélation de Spearman ;
        - la p-value associée.
    """

    data = df[[x_column, y_column]].dropna()

    correlation, p_value = spearmanr(
        data[x_column],
        data[y_column],
    )

    return float(correlation), float(p_value)


def aggregate_by_artist(df: pd.DataFrame) -> pd.DataFrame:
    """Agrège les titres afin d'obtenir une ligne par artiste.

    Un artiste a un seul nombre de fans. Toutes ses valeurs nb_fan sont
    identiques. La valeur first est donc utilisée.

    Leurs ranks sont agrégés afin de représenter la popularité
    des titres de chaque artiste tout en assurant que chaque artiste ait
    le même poids dans l'échantillon de données.

    La valeur médiane est utilisée afin de diminuer l'impact
    des valeurs de rank extrêmes.
    """

    return (
        df.groupby("artist_id", as_index=False)
        .agg(
            artist_name=("artist_name", "first"),
            artist_nb_fan=("artist_nb_fan", "first"),
            median_rank=("rank", "median"),
            nb_tracks=("id", "count"),
        )
    )


def aggregate_by_album(df: pd.DataFrame) -> pd.DataFrame:
    """Agrège les titres afin d'obtenir une ligne par album.

    Un album a un seul nombre de fans. Toutes ses valeurs nb_fan sont
    identiques. La valeur first est donc utilisée.

    Leurs ranks sont agrégés afin de représenter la popularité
    des titres de chaque album tout en assurant que chaque album ait
    le même poids dans l'échantillon de données.

    La valeur médiane est utilisée afin de diminuer l'impact
    des valeurs de rank extrêmes.
    """

    return (
        df.groupby("album_id", as_index=False)
        .agg(
            album_title=("album_title", "first"),
            album_nb_fan=("album_nb_fan", "first"),
            median_rank=("rank", "median"),
            nb_tracks=("id", "count"),
        )
    )


def print_correlation_result(
    label: str,
    correlation: float,
    p_value: float,
    nb_tracks: int,
) -> None:
    """Affiche un résultat de corrélation de manière lisible."""

    print(f"{label}")
    print(f"  Spearman ρ : {correlation:.3f}")
    print(f"  p-value    : {p_value:.4g}")
    print(f"  nb_tracks   : {nb_tracks}")
    print()


def analyze_track_level(df: pd.DataFrame) -> None:
    """Analyse les corrélations au niveau des titres."""

    print("~" * 32)
    print("  ANALYSE AU NIVEAU DES TITRES  ")
    print("~" * 32)
    print()

    # rank et artist_nb_fan
    correlation, p_value = compute_spearman(
        df,
        "artist_nb_fan",
        "rank",
    )

    print_correlation_result(
        " Artistes : nombre de fans & ranks",
        correlation,
        p_value,
        len(df[["artist_nb_fan", "rank"]].dropna()),
    )

    # rank et album_nb_fan
    correlation, p_value = compute_spearman(
        df,
        "album_nb_fan",
        "rank",
    )

    print_correlation_result(
        " Albums : nombre de fans & ranks",
        correlation,
        p_value,
        len(df[["album_nb_fan", "rank"]].dropna()),
    )


def analyze_artist_level(df: pd.DataFrame) -> pd.DataFrame:
    """Analyse la corrélation au niveau des artistes
       (tous les artistes ont le même poids dans l'échantillon).
    """

    artist_df = aggregate_by_artist(df)

    correlation, p_value = compute_spearman(
        artist_df,
        "artist_nb_fan",
        "median_rank",
    )

    print_correlation_result(
        " Artistes (agrégés) : nombre de fans & ranks médians des titres",
        correlation,
        p_value,
        len(artist_df[["artist_nb_fan", "median_rank"]].dropna()),
    )

    return artist_df


def analyze_album_level(df: pd.DataFrame) -> pd.DataFrame:
    """Analyse la corrélation au niveau des albums
       (tous les albums ont le même poids dans l'échantillon).
    """

    album_df = aggregate_by_album(df)

    correlation, p_value = compute_spearman(
        album_df,
        "album_nb_fan",
        "median_rank",
    )

    print_correlation_result(
        " Albums (agrégés) : nombre de fans & ranks médians des titres",
        correlation,
        p_value,
        len(album_df[["album_nb_fan", "median_rank"]].dropna()),
    )

    return album_df

def plot_correlation(
    df: pd.DataFrame,
    x_column: str,
    y_column: str,
    title: str,
    x_label: str,
    y_label: str,
    output_path: Path,
) -> None:
    """Crée un scatter plot et affiche la corrélation de Spearman."""

    data = df[[x_column, y_column]].dropna()

    correlation, p_value = compute_spearman(
        data,
        x_column,
        y_column,
    )

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.scatter(
        data[x_column],
        data[y_column],
        alpha=0.4,
        s=20,
    )

    ax.set_title(title)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.grid(alpha=0.2)

    ax.text(
        0.05,
        0.95,
        (
            f"Spearman ρ = {correlation:.3f}\n"
            f"p-value = {p_value:.4g}\n"
            f"n = {len(data)}"
        ),
        transform=ax.transAxes,
        verticalalignment="top",
        bbox={
            "boxstyle": "round",
            "facecolor": "white",
            "alpha": 0.8,
        },
    )

    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)

def create_plots(df: pd.DataFrame, output_dir: Path) -> None:
    """Crée les graphiques permettant la visualisation des données."""

    output_dir.mkdir(parents=True, exist_ok=True)

    # Transformations logarithmiques utilisées pour
    # faciliter la visualisation des distributions.
    plot_df = df.copy()

    plot_df["log_artist_nb_fan"] = np.log1p(plot_df["artist_nb_fan"])
    plot_df["log_album_nb_fan"] = np.log1p(plot_df["album_nb_fan"])
    plot_df["log_rank"] = np.log1p(plot_df["rank"])

    # 1. Artiste - sans log
    plot_correlation(
        df=plot_df,
        x_column="artist_nb_fan",
        y_column="rank",
        title="Nombre de fans de l'artiste & Rang Deezer",
        x_label="Nombre de fans de l'artiste",
        y_label="Rang Deezer",
        output_path=output_dir / "artist_fans_&_rank.png",
    )

    # 2. Artiste - avec log
    plot_correlation(
        df=plot_df,
        x_column="log_artist_nb_fan",
        y_column="log_rank",
        title="Nombre de fans de l'artiste (log) & Rang Deezer (log)",
        x_label="log(1 + nombre de fans de l'artiste)",
        y_label="log(1 + rang Deezer)",
        output_path=output_dir / "artist_fans_log_&_rank_log.png",
    )

    # 3. Album - sans log
    plot_correlation(
        df=plot_df,
        x_column="album_nb_fan",
        y_column="rank",
        title="Nombre de fans de l'album & Rang Deezer",
        x_label="Nombre de fans de l'album",
        y_label="Rang Deezer",
        output_path=output_dir / "album_fans_&_rank.png",
    )

    # 4. Album - avec log
    plot_correlation(
        df=plot_df,
        x_column="log_album_nb_fan",
        y_column="log_rank",
        title="Nombre de fans de l'album (log) & Rang Deezer (log)",
        x_label="log(1 + nombre de fans de l'album)",
        y_label="log(1 + rang Deezer)",
        output_path=output_dir / "album_fans_log_&_rank_log.png",
    )


def main() -> None:
    """Exécute l'ensemble de l'analyse."""

    df = pd.read_csv(DATA_PATH)

    print(f"Nombre de titres : {len(df)}")
    print()

    # 1. Analyse au niveau des titres.
    analyze_track_level(df)

    # 2. Agrégation et analyse au niveau des artistes.
    artist_df = analyze_artist_level(df)

    # 3. Agrégation et analyse au niveau des albums.
    album_df = analyze_album_level(df)

    # 4. Création des quatre graphiques.
    create_plots(df, OUTPUT_DIR)

    print(f" Graphiques sauvegardés dans : {OUTPUT_DIR}")


if __name__ == "__main__":
    main()