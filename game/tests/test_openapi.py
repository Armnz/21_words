from django.test import Client


def test_openapi_schema_endpoint_returns_200():
    client = Client()

    response = client.get("/api/schema/")

    assert response.status_code == 200
