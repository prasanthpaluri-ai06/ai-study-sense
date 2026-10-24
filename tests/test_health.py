import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoints(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "hardware_connected" in data

    api_health = await client.get("/api/v1/health")
    assert api_health.status_code == 200
    api_data = api_health.json()
    assert api_data["status"] == "healthy"
    assert "hardware" in api_data
