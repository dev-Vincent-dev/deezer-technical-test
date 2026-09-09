"""Analyse de la relation entre BPM, durée et popularité des titres Deezer."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


DATA_PATH = Path("data/best_2026-09-09_02-15-29.csv")
OUTPUT_DIR = Path("data/analysis/bpm_duration_popularity")

BPM_BIN_SIZE = 10
DURATION_BIN_SIZE = 30

# Nombre minimal de titres dans une cellule pour considérer
# le résultat comme suffisamment représentatif.
MIN_TRACKS_PER_CELL = 30


def prepare_data(df: pd.DataFrame) -> pd.DataFrame:
    """Prépare les données nécessaires à l'analyse."""

    data = df[["id", "bpm", "duration", "rank"]].copy()

    data = data.dropna(subset=["bpm", "duration", "rank"])

    # Filtrage des valeurs incohérentes
    data = data[
        (data["bpm"] > 0)
        & (data["duration"] > 0)
        & (data["rank"] > 0)
    ]

    # Création des intervalles de BPM
    bpm_min = int(data["bpm"].min() // BPM_BIN_SIZE * BPM_BIN_SIZE)
    bpm_max = int(
        (data["bpm"].max() // BPM_BIN_SIZE + 1) * BPM_BIN_SIZE
    )

    bpm_bins = range(bpm_min, bpm_max + BPM_BIN_SIZE, BPM_BIN_SIZE)

    data["bpm_bin"] = pd.cut(data["bpm"], bins=bpm_bins, right=False)

    # Création des intervalles de durée
    duration_min = int(
        data["duration"].min() // DURATION_BIN_SIZE
        * DURATION_BIN_SIZE
    )
    duration_max = int(
        (data["duration"].max() // DURATION_BIN_SIZE + 1)
        * DURATION_BIN_SIZE
    )

    duration_bins = range(
        duration_min,
        duration_max + DURATION_BIN_SIZE,
        DURATION_BIN_SIZE,
    )

    data["duration_bin"] = pd.cut(
        data["duration"],
        bins=duration_bins,
        right=False,
    )

    return data


def compute_heatmap_data(
    data: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Calcule le rank médian et le nombre de titres par cellule."""

    median_rank = pd.pivot_table(
        data,
        values="rank",
        index="duration_bin",
        columns="bpm_bin",
        aggfunc="median",
        observed=False,
    )

    track_count = pd.pivot_table(
        data,
        values="id",
        index="duration_bin",
        columns="bpm_bin",
        aggfunc="count",
        observed=False,
    )

    return median_rank, track_count


def print_best_combinations(
    median_rank: pd.DataFrame,
    track_count: pd.DataFrame,
) -> None:
    """Affiche les couples BPM/durée associés aux meilleurs ranks."""

    results = (median_rank.stack().rename("median_rank").reset_index())

    counts = (track_count.stack().rename("n_tracks").reset_index())

    results = results.merge(counts, on=["duration_bin", "bpm_bin"])

    results = results[results["n_tracks"] >= MIN_TRACKS_PER_CELL]

    results = results.sort_values("median_rank", ascending=False)

    print()
    print("-" * 52)
    print("  COUPLES BPM / DURÉE ASSOCIÉS AUX MEILLEURS RANKS  ")
    print("-" * 52)
    print()
    print(
        f" Nombre minimal de titres par cellule : "
        f"{MIN_TRACKS_PER_CELL}"
    )
    print()

    if results.empty:
        print("Aucune cellule ne contient suffisamment de titres.")
        return

    print(
        results.to_string(
            index=False,
            formatters={
                "median_rank": "{:.0f}".format,
            },
        )
    )


def plot_heatmap(
    median_rank: pd.DataFrame,
    track_count: pd.DataFrame,
    output_path: Path,
) -> None:
    """Crée une heatmap du rank médian selon BPM et durée."""

    fig, ax = plt.subplots(figsize=(14, 9))

    # On masque les cellules trop peu représentées
    masked_rank = median_rank.mask(
        track_count < MIN_TRACKS_PER_CELL
    )

    image = ax.imshow(
        masked_rank,
        aspect="auto",
        cmap="Reds",
        interpolation="nearest",
    )

    # Axes X : BPM
    ax.set_xticks(range(len(median_rank.columns)))
    ax.set_xticklabels(
        [
            f"{interval.left:.0f}-{interval.right:.0f}"
            for interval in median_rank.columns
        ],
        rotation=45,
        ha="right",
    )

    # Axes Y : durée
    ax.set_yticks(range(len(median_rank.index)))
    ax.set_yticklabels(
        [
            f"{interval.left:.0f}-{interval.right:.0f}s"
            for interval in median_rank.index
        ]
    )

    ax.set_xlabel("BPM")
    ax.set_ylabel("Durée du titre")
    ax.set_title(
        "Popularité des titres selon le BPM et la durée\n"
        "Médiane du rang Deezer"
    )

    # Affichage du nombre de titres dans chaque cellule
    for row in range(len(median_rank.index)):
        for column in range(len(median_rank.columns)):
            count = track_count.iloc[row, column]

            if count >= MIN_TRACKS_PER_CELL:
                rank = median_rank.iloc[row, column]

                ax.text(
                    column,
                    row,
                    f"{rank:.0f}\n(n={count})",
                    ha="center",
                    va="center",
                    fontsize=7,
                    color="black",
                )

    colorbar = fig.colorbar(image, ax=ax)

    colorbar.set_label("Rang Deezer médian")

    ax.grid(visible=False)

    fig.tight_layout()

    fig.savefig(output_path, dpi=300)

    plt.close(fig)


def print_summary(
    data: pd.DataFrame,
    median_rank: pd.DataFrame,
    track_count: pd.DataFrame,
) -> None:
    """Affiche un résumé de l'analyse."""

    print()
    print("-" * 23)
    print("  RÉSUMÉ DE L'ANALYSE  ")
    print("-" * 23)
    print()

    print(f" Nombre de titres analysés : {len(data)}")
    print(f" BPM minimum              : {data['bpm'].min():.1f}")
    print(f" BPM maximum              : {data['bpm'].max():.1f}")
    print(f" BPM médian               : {data['bpm'].median():.1f}")
    print()
    print(
        f" Durée minimum            : "
        f"{data['duration'].min():.0f}s"
    )
    print(
        f" Durée maximum            : "
        f"{data['duration'].max():.0f}s"
    )
    print(
        f" Durée médiane            : "
        f"{data['duration'].median():.0f}s"
    )
    print()

    valid_cells = (
        track_count >= MIN_TRACKS_PER_CELL
    ).sum().sum()

    print(
        f" Cellules avec au moins "
        f"{MIN_TRACKS_PER_CELL} titres : {valid_cells}"
    )


def run_analysis() -> None:
    """Exécute l'analyse BPM / durée / popularité."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(DATA_PATH)

    print("-" * 36)
    print("  ANALYSE BPM / DURÉE / POPULARITÉ  ")
    print("-" * 36)

    data = prepare_data(df)

    print_summary(data, *compute_heatmap_data(data))

    median_rank, track_count = compute_heatmap_data(data)

    print_best_combinations(median_rank, track_count)

    output_path = OUTPUT_DIR / "bpm_duration_popularity_heatmap.png"

    plot_heatmap(median_rank, track_count, output_path)

    print()
    print(f" Heatmap sauvegardée dans : {output_path}")
    print()


if __name__ == "__main__":
    run_analysis()
