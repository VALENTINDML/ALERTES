from fastapi.testclient import TestClient

from api.main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_notifications_latest_limit_validation():
    response = client.get("/notifications/latest?limit=500")

    assert response.status_code == 422


def test_price_alerts_latest_limit_validation():
    response = client.get("/price-alerts/latest?limit=500")

    assert response.status_code == 422