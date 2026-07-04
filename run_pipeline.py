"""
Pipeline manuel d'exécution.

Ce script permet d'exécuter manuellement l'ensemble de la chaîne
de traitement sans passer par Airflow.

Étapes exécutées :
1. Collecte des données OHLCV
2. Feature engineering
3. Entraînement du modèle
4. Prédiction et génération des notifications

Il est principalement utilisé pour :
- les tests locaux ;
- le débogage ;
- les exécutions ponctuelles.

En production, cette orchestration est assurée par les DAGs Airflow.
"""
import subprocess
from datetime import datetime


SCRIPTS = [
    "data/collector.py",
    "data/feature_engineering.py",
    "ml/train_model.py",
    "ml/predict.py",
]


def run_script(script_name):
    """
    Exécute un script Python et arrête le pipeline en cas d'erreur.

    Args:
        script_name (str):
            Chemin du script à exécuter.
    """
    print(f"\n[{datetime.now()}] Lancement : {script_name}")

    result = subprocess.run(
        ["python", script_name],
        capture_output=False,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(f"Erreur pendant l'exécution de {script_name}")

    print(f"[{datetime.now()}] Terminé : {script_name}")


def run_pipeline_once():
    """
    Exécute une fois l'ensemble du pipeline.
    """
    print("\n==============================")
    print(f"Pipeline lancé à {datetime.now()}")
    print("==============================")

    for script in SCRIPTS:
        run_script(script)

    print("\nPipeline terminé.")


def main():
    """
    Point d'entrée du pipeline.
    """
    run_pipeline_once()


if __name__ == "__main__":
    main()