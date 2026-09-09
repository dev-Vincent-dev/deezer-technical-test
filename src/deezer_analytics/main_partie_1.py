"""Point d'entrée principal du projet pour la collecte de données."""

from pathlib import Path

from deezer_analytics.deezer_client import DeezerClient
from deezer_analytics.collect import DeezerCollector
from deezer_analytics.export import save_enriched_tracks_to_csv


def main():
    print("-" * 44)
    print("       PROJET DEEZER - TEST TECHNIQUE")
    print("            COLLECTE DE DONNÉES")
    print("-" * 44)
    print()
    print("Vous allez collecter des données depuis l'API publique de Deezer.")
    print(
        "Attention : Plus vous choisissez des valeurs importantes "
        "(100 ou 1000 par exemple), plus la collecte prendra du temps "
        "jusqu'à l'affichage du message final : 'Enrichissement "
        "des données Tracks avec les données Albums et Artists terminé'.\n"
    )
    print(
        f"Ces {len(DeezerCollector.DEFAULT_QUERIES)} catégories de musique "
        "seront recherchées :"
    )
    print(*DeezerCollector.DEFAULT_QUERIES, sep="\n")

    while True:
        try:
            target_size_per_query = int(
                input(
                    "\nEntrez le nombre de titres uniques collectés "
                    "par recherche (target_size_per_query) : "
                )
            )

            if target_size_per_query <= 0:
                print("Veuillez entrer un entier supérieur à 0.")
                continue

            break

        except ValueError:
            print("Veuillez entrer un entier valide.")

    while True:
        try:
            target_size = int(
                input(
                    "\nEntrez le nombre minimal de titres uniques "
                    "à obtenir au total (target_size) : "
                )
            )

            if target_size <= 0:
                print("Veuillez entrer un entier supérieur à 0.")
                continue

            max_target_size = (
                len(DeezerCollector.DEFAULT_QUERIES)
                * target_size_per_query
            )

            if target_size > max_target_size:
                print(
                    "Veuillez entrer un entier inférieur ou égal à "
                    f"{max_target_size}."
                )
                continue

            break

        except ValueError:
            print("Veuillez entrer un entier valide.")

    while True:
        filename = input(
            "\nIndiquer le nom du fichier CSV (sans extension) "
            "qui stockera les données collectées dans le dossier 'data/' : "
        ).strip()

        if filename:
            break

        print("Veuillez entrer un nom de fichier valide.")
    
    path = Path("data")
    path.mkdir(parents=True, exist_ok=True)

    # Si l'utilisateur a quand même écrit l'extension (.csv ou .CSV)
    if filename.lower().endswith(".csv"):
        filename = filename[:-4]

    filepath = path / f"{filename}.csv"

    print()
    print("-" * 27)
    print("       Configuration       ")
    print("-" * 27)
    print(f"target_size_per_query : {target_size_per_query}")
    print(f"target_size           : {target_size}")
    print(f"filepath              : {filepath}")
    print("-" * 27)
    print()
    print("La collecte des données va commencer... ")
    print()

    with DeezerClient() as client:
        collector = DeezerCollector(client, target_size, target_size_per_query)
        collected_tracks = collector.collect()
        save_enriched_tracks_to_csv(collected_tracks, filepath)

    print(
        "\nLes données collectées ont été enregistrées dans "
        f"'{filepath}'"
    )


if __name__ == "__main__":
    main()
