from fastapi.testclient import TestClient


def test_read_main(test_client: TestClient):
    response = test_client.get("/__status__/")
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["status"] == "OK"
    assert response_data["timestamp"]
