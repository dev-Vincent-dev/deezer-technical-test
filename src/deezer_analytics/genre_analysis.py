"""Analyse des genres musicaux de l'échantillon Deezer."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from scipy.stats import kruskal


DATA_PATH = Path("data/best_2026-09-09_02-15-29.csv")
OUTPUT_DIR = Path("data/analysis/genre")

# Nombre minimal de titres requis pour qu'un genre soit inclus
# dans les tests statistiques
MIN_TRACKS_PER_GENRE = 100


def prepare_genre_data(df: pd.DataFrame) -> pd.DataFrame:
    """Prépare les données afin d'avoir une ligne par titre et par genre."""

    genre_df = df.copy()

    # Un album peut être associé à plusieurs genres
    genre_df["album_genres"] = genre_df["album_genres"].fillna("")
    genre_df["genre"] = genre_df["album_genres"].str.split("|")

    # Création d'une ligne par titre et par genre
    genre_df = genre_df.explode("genre")

    # Nettoyage des valeurs
    genre_df["genre"] = genre_df["genre"].str.strip()
    genre_df = genre_df[genre_df["genre"] != ""]

    return genre_df


def compute_genre_statistics(
    genre_df: pd.DataFrame,
) -> pd.DataFrame:
    """Calcule les statistiques descriptives pour chaque genre."""

    return (
        genre_df.groupby("genre")
        .agg(
            n_tracks=("id", "nunique"),
            mean_bpm=("bpm", "mean"),
            mean_duration=("duration", "mean"),
        )
        .sort_values("n_tracks", ascending=False)
        .reset_index()
    )


def filter_genres(
    genre_df: pd.DataFrame,
    min_tracks: int = MIN_TRACKS_PER_GENRE,
) -> pd.DataFrame:
    """Conserve uniquement les genres suffisamment représentés."""

    genre_counts = (genre_df.groupby("genre")["id"].nunique())

    selected_genres = genre_counts[genre_counts >= min_tracks].index

    return genre_df[genre_df["genre"].isin(selected_genres)].copy()


def kruskal_wallis_by_genre(
    genre_df: pd.DataFrame,
    value_column: str,
) -> tuple[float, float]:
    """Teste si une variable diffère significativement entre les genres.

    Le test de Kruskal-Wallis permet de comparer les distributions
    d'une variable entre plusieurs groupes indépendants.
    """

    groups = [
        group[value_column].dropna()
        for _, group in genre_df.groupby("genre")
    ]

    statistic, p_value = kruskal(*groups)

    return float(statistic), float(p_value)


def plot_genre_counts(
    genre_stats: pd.DataFrame,
    output_path: Path,
) -> None:
    """Affiche le nombre de titres par genre."""

    data = genre_stats.sort_values("n_tracks")

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.barh(
        data["genre"],
        data["n_tracks"],
    )

    ax.set_title("Nombre de titres par genre")
    ax.set_xlabel("Nombre de titres")
    ax.set_ylabel("Genre")

    ax.grid(
        axis="x",
        alpha=0.2,
    )

    fig.tight_layout()
    fig.savefig(
        output_path,
        dpi=300,
    )
    plt.close(fig)


def plot_distribution_by_genre(
    genre_df: pd.DataFrame,
    value_column: str,
    title: str,
    y_label: str,
    output_path: Path,
) -> None:
    """Affiche la distribution d'une variable pour chaque genre."""

    data = genre_df[["genre", value_column]].dropna()

    # Tri des genres par moyenne afin de faciliter la lecture
    genres = (
        data.groupby("genre")[value_column]
        .mean()
        .sort_values()
        .index
    )

    values = [
        data.loc[data["genre"] == genre, value_column]
        for genre in genres
    ]

    fig, ax = plt.subplots(figsize=(12, 7))

    ax.boxplot(
        values,
        tick_labels=genres,
        showfliers=False,
    )

    ax.set_title(title)
    ax.set_xlabel("Genre")
    ax.set_ylabel(y_label)

    ax.grid(
        axis="y",
        alpha=0.2,
    )

    plt.xticks(
        rotation=45,
        ha="right",
    )

    fig.tight_layout()
    fig.savefig(
        output_path,
        dpi=300,
    )
    plt.close(fig)


def print_genre_statistics(
    genre_stats: pd.DataFrame,
) -> None:
    """Affiche les statistiques descriptives par genre."""

    print()
    print("  Statistiques par genre  ")
    print("-" * 26)

    print(
        genre_stats.to_string(
            index=False,
            formatters={
                "mean_bpm": "{:.1f}".format,
                "mean_duration": "{:.1f}".format,
            },
        )
    )


def print_kruskal_result(
    variable: str,
    statistic: float,
    p_value: float,
) -> None:
    """Affiche le résultat d'un test de Kruskal-Wallis."""

    print()
    print(f" {variable}")
    print(f"   Statistique H : {statistic:.3f}")
    print(f"   p-value       : {p_value:.4g}")

    if p_value < 0.05:
        print(
            "   Conclusion    : différence significative "
            "entre au moins deux genres."
        )
    else:
        print(
            "   Conclusion    : aucune différence significative "
            "détectée entre les genres."
        )


def main() -> None:
    """Exécute l'ensemble de l'analyse des genres."""

    output_dir = OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(DATA_PATH)

    print("-" * 22)
    print("  ANALYSE DES GENRES  ")
    print("-" * 22)
    print()
    print(f" Nombre de titres : {len(df)}")

    # Préparation des genres
    genre_df = prepare_genre_data(df)

    print(
        f" Nombre de lignes après association "
        f"titre/genre : {len(genre_df)}"
    )

    # Statistiques descriptives
    genre_stats = compute_genre_statistics(genre_df)

    print_genre_statistics(genre_stats)

    # Graphique : représentation visuelle des genres
    plot_genre_counts(genre_stats, output_dir / "genre_counts.png")

    # Sélection des genres suffisamment représentés
    statistical_genre_df = filter_genres(genre_df)

    statistical_genre_stats = compute_genre_statistics(
        statistical_genre_df
    )

    print()
    print(
        f" Genres retenus pour les tests de Kruskal-Wallis "
        f"(minimum {MIN_TRACKS_PER_GENRE} titres) : "
        f"{len(statistical_genre_stats)}"
    )

    # Tests de Kruskal-Wallis
    
    bpm_statistic, bpm_p_value = kruskal_wallis_by_genre(
        statistical_genre_df,
        "bpm"
    )

    duration_statistic, duration_p_value = kruskal_wallis_by_genre(
        statistical_genre_df,
        "duration"
    )

    print()
    print("-" * 27)
    print("  TESTS DE KRUSKAL-WALLIS  ")
    print("-" * 27)

    print_kruskal_result("BPM", bpm_statistic, bpm_p_value)

    print_kruskal_result("Durée", duration_statistic, duration_p_value)

    # Graphiques : BPM et durée
    
    plot_distribution_by_genre(
        statistical_genre_df,
        "bpm",
        "Distribution du BPM par genre",
        "BPM",
        output_dir / "bpm_by_genre.png",
    )

    plot_distribution_by_genre(
        statistical_genre_df,
        "duration",
        "Distribution de la durée par genre",
        "Durée (en secondes)",
        output_dir / "duration_by_genre.png",
    )

    print()
    print("-" * 31)
    print("  ANALYSE DES GENRES TERMINÉE  ")
    print("-" * 31)
    print()
    print(f" Graphiques sauvegardés dans : {output_dir}")


if __name__ == "__main__":
    main()
