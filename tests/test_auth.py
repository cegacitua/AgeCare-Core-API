import pytest


@pytest.mark.asyncio
async def test_register_and_login_flow(client):
    # 1. Register User
    reg_payload = {
        "email": "cuidador_test@agecare.cl",
        "password": "PasswordSegura123!",
        "full_name": "María González",
        "phone": "+56912345678",
        "locale": "es-CL"
    }
    res = await client.post("/api/v1/auth/register", json=reg_payload)
    assert res.status_code == 201
    data = res.json()
    assert "access_token" in data
    assert data["user"]["email"] == "cuidador_test@agecare.cl"

    # 2. Login User
    login_payload = {
        "email": "cuidador_test@agecare.cl",
        "password": "PasswordSegura123!"
    }
    res_login = await client.post("/api/v1/auth/login", json=login_payload)
    assert res_login.status_code == 200
    token_data = res_login.json()
    assert "access_token" in token_data
    token = token_data["access_token"]

    # 3. Get Me Profile
    headers = {"Authorization": f"Bearer {token}"}
    res_me = await client.get("/api/v1/auth/me", headers=headers)
    assert res_me.status_code == 200
    assert res_me.json()["full_name"] == "María González"
