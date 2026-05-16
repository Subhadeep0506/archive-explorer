def test_root_returns_welcome_message(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to The Arxplorer Backend API"}


def test_health_returns_runtime_metrics(client):
    response = client.get("/health")

    assert response.status_code == 200

    payload = response.json()
    assert payload["health"] == "ok"
    assert isinstance(payload["cpu_usage"], (int, float))
    assert isinstance(payload["memory_usage"], (int, float))
    assert isinstance(payload["num_threads"], int)
