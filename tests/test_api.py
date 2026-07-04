from fastapi.testclient import TestClient

from api.main import app

# Client HTTP simulant des appels vers l'API FastAPI.
client = TestClient(app)


def test_health_endpoint():
    """
    Vérifie que l'API est démarrée et répond correctement.
    """
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_notifications_latest_limit_validation():
    """
    Vérifie que la validation FastAPI empêche
    de demander plus de 200 notifications.
    """
    response = client.get("/notifications/latest?limit=500")

    assert response.status_code == 422


def test_price_alerts_latest_limit_validation():
    """
    Vérifie que la limite maximale autorisée
    est bien appliquée sur les alertes de prix.
    """
    response = client.get("/price-alerts/latest?limit=500")

    assert response.status_code == 422