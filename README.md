# Crypto Alerts

> Plateforme de **Data Engineering & Analytics Engineering** reproduisant une architecture de production capable de collecter des données historiques et temps réel, d'alimenter des pipelines analytiques et de Machine Learning, puis de générer des prédictions quotidiennes et des alertes personnalisées.

![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)
![Apache Airflow](https://img.shields.io/badge/Apache%20Airflow-017CEE?style=for-the-badge&logo=Apache%20Airflow&logoColor=white)
![dbt](https://img.shields.io/badge/dbt-Core-FF694B?style=for-the-badge&logo=dbt) 
![FastAPI](https://img.shields.io/badge/FastAPI-005571.svg?style=for-the-badge&logo=fastapi)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-%23FE4B4B.svg?style=for-the-badge&logo=streamlit&logoColor=white)
![Tableau](https://img.shields.io/badge/Tableau-E97627?style=for-the-badge&logo=tableau&logoColor=white)
![Grafana](https://img.shields.io/badge/Grafana-F46800?style=for-the-badge&logo=grafana&logoColor=white)
![Prometheus](https://img.shields.io/badge/Prometheus-E6522C?style=for-the-badge&logo=prometheus&logoColor=white)
![Pytest](https://img.shields.io/badge/Pytest-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-CI-2088FF?style=for-the-badge&logo=githubactions&logoColor=white)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)

## Pourquoi ce projet ?

Crypto Alerts a été conçu pour reproduire une plateforme de données de production couvrant l'ensemble du cycle de vie de la donnée : collecte, stockage, transformation, analyse, prédiction et restitution.

Le projet combine ingestion batch et temps réel, orchestration, automatisation, modélisation analytique, Machine Learning, API REST, monitoring, génération d'alertes.

## Ce que fait la plateforme

- Collecte des **données** historiques avec CCXT
- **Streaming** temps réel via WebSocket
- Stockage **PostgreSQL**
- Feature Engineering des données de marché
- Entraînement et prédiction Machine Learning
- Génération d'alertes personnalisées
- Modélisation analytique avec **dbt**
- **Orchestration** des pipelines avec **Airflow**
- Exposition des données via **FastAPI**
- Visualisation opérationnelle avec Streamlit
- Visualisation analytique avec **Tableau**


## Architecture

Le diagramme suivant présente les principaux composants de la plateforme ainsi que les flux de données entre les différents services.

<p align="center">
  <img src="assets/images/archi.svg" alt="Architecture" width="700">
</p>

L'architecture repose sur deux pipelines complémentaires :

- **un pipeline batch**, chargé de collecter les données historiques, de construire les indicateurs techniques, d'entraîner les modèles de Machine Learning et de générer les prédictions quotidiennes ;
- **un pipeline temps réel**, chargé de surveiller en continu les prix des cryptomonnaies et de déclencher les alertes personnalisées lorsque les conditions définies par les utilisateurs sont remplies.


##  Démonstration

<p align="center">
  <a href="assets/gif/streamlit.gif">
    <img src="assets/gif/streamlit.gif" width="900" alt="Dashboard Streamlit">
  </a>
  <br>
  <b>Dashboard Streamlit</b>
</p>

<p align="center">
  <a href="assets/gif/airflow.gif">
    <img src="assets/gif/airflow.gif" width="900" alt="Pipeline Airflow">
  </a>
  <br>
  <b>Pipelines Airflow</b>
</p>

### Dashboards Tableau

<p align="center">
  <a href="assets/images/mart_users.png">
    <img src="assets/images/mart_users.png" width="700" alt="Dashboard Tableau - Utilisateurs">
  </a>
  <br>
  <b>Analyse des portefeuilles utilisateurs</b>
</p>

<p align="center">
  <a href="assets/images/mart_notifications.png">
    <img src="assets/images/mart_notifications.png" width="700" alt="Dashboard Tableau - Notifications">
  </a>
  <br>
  <b>Analyse des notifications de la plateforme</b>
</p>

<p align="center">
  <a href="assets/images/mart_crypto.png">
    <img src="assets/images/mart_crypto.png" width="700" alt="Dashboard Tableau - Cryptomonnaies">
  </a>
  <br>
  <b>Analyse des cryptomonnaies et des alertes</b>
</p>


## Choix d'architecture

Les principaux choix d'architecture sont les suivants :

- **PostgreSQL** centralise les données opérationnelles et permet d'exécuter les traitements **SQL** au plus près des données.
- **Airflow** orchestre les pipelines de collecte, de transformation, d'entraînement et de prédiction.
- **dbt** construit une couche analytique réutilisable, séparée logiquement des tables opérationnelles par des schémas dédiés (`staging`, `marts`) au sein de la même base PostgreSQL.
- **FastAPI** expose les données, les prédictions et les métriques via une API REST documentée automatiquement.
- **Streamlit** fournit un tableau de bord opérationnel pour le suivi de la plateforme en temps réel.
- **Tableau** exploite la couche analytique afin de produire des tableaux de bord orientés métier.
- **Prometheus** collecte les métriques de l'API (endpoint `/metrics`) et des conteneurs via cAdvisor, tandis que **Grafana** assure leur supervision et leur visualisation.
- **Docker Compose** permet de reproduire l'ensemble de l'environnement de développement avec une seule commande.

Cette architecture favorise la séparation des responsabilités, améliore la maintenabilité de la plateforme et facilite son évolution.

## Observabilité et visualisation

Afin de proposer une plateforme de données complète, le projet intègre également :

- **Streamlit** fournit une interface opérationnelle permettant de suivre les données de marché, les prédictions, les notifications et les principaux indicateurs de la plateforme.
- **Tableau** permet d'explorer les données métier à travers des tableaux de bord analytiques (répartition des utilisateurs, composition des portefeuilles, statistiques d'utilisation, etc.).
- **Prometheus** collecte les métriques de l'API (endpoint `/metrics`) et des conteneurs via cAdvisor.
- **Grafana** supervise la plateforme et visualise les métriques techniques.

## Qualité logicielle

Le projet applique plusieurs bonnes pratiques afin d'améliorer sa fiabilité.

- **Pytest** pour les tests unitaires.
- **GitHub Actions** pour automatiser les tests et valider le projet à chaque Push ou Pull Request.


## Points techniques

- Pipelines ETL / ELT modulaires
- Collecte idempotente (upsert `ON CONFLICT`)
- Traitements **SQL-first**
- Batch processing
- Optimisation PostgreSQL (`INSERT ... SELECT`, `ON CONFLICT DO NOTHING`, `FOR UPDATE SKIP LOCKED`)
- Couche analytique avec **dbt**
- DAGs **Airflow** indépendants
- Architecture en services découplés
- API REST documentée avec OpenAPI


## Mesures de performance

Mesures relevées les 6 et 24 août 2026, en local (macOS, Docker Desktop,
nœud unique), à l'échelle de **200 000 utilisateurs générés**. Les volumes
en base croissent mécaniquement, les DAGs `@daily` régénérant environ
372 000 notifications par jour :

- Build Docker complet from scratch (`--no-cache`) : **90 s**, 16 services
  (dépendances épinglées incluses)
- Base PostgreSQL : **~2,4 M de lignes / 473 MB** (10 tables)
- Génération d'utilisateurs : **200 000 utilisateurs en 77 s**, soit
  **1 407 243 lignes** au total (utilisateurs + positions + préférences +
  alertes) à **~18 300 lignes/s** en batch processing
- Alertes de prix générées : **361 810** à cette échelle
- Ingestion batch : 180 jours × 2 symboles (**8 640 bougies**) en **8,0 s**
- Notifications quotidiennes : **372 503 en 6,2 s** en SQL pur
  (`INSERT ... SELECT`)
- Stream d'alertes : **2 994 notifications/s** en résorption de backlog,
  batchs de 5 000 commités en **~90 ms** (`FOR UPDATE SKIP LOCKED`)
- API : **p95 de 2 à 39 ms** selon l'endpoint, mesuré avec 553 000
  notifications en base
- dbt : 12 modèles, 52 tests, **64/64 PASS**

Aucun chargement massif des alertes en mémoire Python : les traitements
volumineux sont délégués à PostgreSQL.

### Machine Learning : un résultat assumé

Les performances prédictives mesurées sont mauvaises, et c'est documenté
volontairement : **R² de −0,48 (BTC/USDT) et −2,65 (ETH/USDT)** sur un
split chronologique 80/20 — le modèle RandomForest est battu par une
baseline constante à zéro sur les deux symboles. Prédire le marché crypto
à 24 h avec des indicateurs techniques simples ne fonctionne pas, et ce
projet ne prétend pas le contraire.

Le composant ML sert à démontrer le **cycle MLOps complet** : entraînement,
évaluation champion/challenger sur un jeu de test commun, promotion
conditionnelle du modèle, archivage des versions et historisation des
métriques (MAE, RMSE, MAPE, R²) en base — c'est précisément cette
instrumentation qui permet de mesurer honnêtement les limites du modèle.


## Évolutions prévues
- Déploiement Cloud
- Validation automatique des modèles
- Notifications Email et SMS
- Amélioration de la couverture de tests
- Amélioration de Dbt

## Stack technique

- Python
- PostgreSQL
- Docker Compose
- Airflow
- dbt
- FastAPI
- Streamlit
- Tableau
- Prometheus
- Grafana
- GitHub Actions
- Pytest
---


## Lancer le projet

### 1. Configuration

Les fichiers de configuration `.env` ne sont pas versionnés et sont exclus du dépôt via `.gitignore`.

Avant de lancer le projet, créer les fichiers `.env` à partir des modèles fournis :

```bash
cp .env.exemple .env
cp .env.docker.exemple .env.docker
```

Modifier ensuite les variables d'environnement selon votre configuration si nécessaire.

### 2. Démarrer l’environnement Docker

Cette commande lance les services principaux du projet et initialise automatiquement les tables de la base PostgreSQL.

```bash
docker compose --env-file .env.docker build --no-cache
docker compose --env-file .env.docker up -d
```
Vérifier que l'initialisation de la base s'est correctement déroulée : 
```bash
docker logs crypto_init_db 
```
Le message suivant doit être affiché :
"Base de données initialisée avec succès."

### 3. La génération des utilisateurs se fait manuellement : 
```bash
docker compose --env-file .env.docker run --rm pipeline python users_db/generate_fake_users.py <nombre d'utilisateurs souhaités>
```

**Exemple:**
```bash
docker compose --env-file .env.docker run --rm pipeline python users_db/generate_fake_users.py 2000000
```


### 4. Accéder à l'interface Airflow puis lancer le DAG `setup` pour Collect > Features Engineering > Train > Predict

http://localhost:8080

### 5. La partie analytics est optionnelle. Pour lancer dbt : 
```bash
docker compose --env-file .env.docker --profile manual run --rm dbt dbt debug
docker compose --env-file .env.docker --profile manual run --rm dbt dbt run
docker compose --env-file .env.docker --profile manual run --rm dbt dbt test
docker compose --env-file .env.docker --profile manual run --rm dbt dbt docs generate
```

Services utiles:

- API FastAPI      : http://localhost:8000
- Streamlit        : http://localhost:8501
- Airflow          : http://localhost:8080
- pgAdmin          : http://localhost:5050
- Prometheus       : http://localhost:9090
- Grafana          : http://localhost:3000