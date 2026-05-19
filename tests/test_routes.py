from app import create_app


def test_health_route():
    app = create_app()
    client = app.test_client()

    response = client.get("/status")

    assert response.status_code == 200
    assert response.json["status"] == "ok"


def test_dashboard_route():
    app = create_app()
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200