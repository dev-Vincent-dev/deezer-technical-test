"""Point d'entrée principal du projet pour l'analyse de données."""

from deezer_analytics import (
    popularity_analysis,
    genre_analysis,
    bpm_duration_popularity,
)


def main():
    print("-" * 44)
    print("       PROJET DEEZER - TEST TECHNIQUE")
    print("             ANALYSE DES DONNÉES")
    print("-" * 44)
    print()
    print(
        "Vous allez analyser les données du fichier "
        "'data/best_2026-09-09_02-15-29.csv' "
        "(données ayant été collectées depuis l'API publique de Deezer)."
    )
    print()

    print("-" * 58)
    print("   QUESTION 1 : Nombre de fans et popularité des titres")
    print("-" * 58)
    print()

    popularity_analysis.run_analysis()

    print()
    print("-" * 39)
    print("   QUESTION 2 : Genres, BPM et durée")
    print("-" * 39)
    print()

    genre_analysis.run_analysis()

    print()
    print("-" * 43)
    print("   QUESTION 3 : BPM, durée et popularité")
    print("-" * 43)
    print()

    bpm_duration_popularity.run_analysis()


if __name__ == "__main__":
    main()
