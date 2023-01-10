from fastapi.testclient import TestClient

from app.run import app

client = TestClient(app)


def test_get_client():
    response = client.get("/client/101")
    assert response.status_code == 200
    assert response.json() == {"client_id": 101, "age": 1}


def test_post_client():
    response = client.post("/clients/", json={"ids": [101, 102]})
    assert response.status_code == 200
    assert response.json() == {
        "clients": [{"client_id": 101, "age": 1}, {"client_id": 102, "age": 2}]
    }
