import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_and_login_flow(client: AsyncClient):
    # 1. Register a student user
    register_payload = {
        "username": "teststudent",
        "email": "student@university.edu",
        "full_name": "Test Student",
        "password": "StrongPassword123!",
        "institution": "Tech University",
        "course": "Computer Science",
        "year": "3rd",
        "semester": "6th",
    }
    reg_res = await client.post("/api/v1/auth/register", json=register_payload)
    assert reg_res.status_code == 201
    reg_data = reg_res.json()
    assert "access_token" in reg_data
    token = reg_data["access_token"]

    # 2. Login with valid credentials
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"username": "teststudent", "password": "StrongPassword123!"},
    )
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert "access_token" in login_data

    # 3. Retrieve user profile
    headers = {"Authorization": f"Bearer {token}"}
    me_res = await client.get("/api/v1/users/me", headers=headers)
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["username"] == "teststudent"
    assert me_data["profile"]["institution"] == "Tech University"
