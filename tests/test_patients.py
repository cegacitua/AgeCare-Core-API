import pytest


@pytest.mark.asyncio
async def test_patient_creation_and_wearable_flow(client):
    # Register user
    reg_payload = {
        "email": "familiar@agecare.cl",
        "password": "Password123!",
        "full_name": "Carlos Silva"
    }
    reg_res = await client.post("/api/v1/auth/register", json=reg_payload)
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create patient
    pat_payload = {
        "full_name": "Don Roberto Silva",
        "birth_date": "1948-05-15",
        "sex": "M",
        "conditions": ["Hipertensión", "Diabetes Tipo 2"]
    }
    res_pat = await client.post("/api/v1/patients", json=pat_payload, headers=headers)
    assert res_pat.status_code == 201
    patient_id = res_pat.json()["id"]

    # Bind wearable
    wearable_payload = {
        "serial_number": "WEAR-998877",
        "model": "AgeCare Watch v1"
    }
    res_wearable = await client.post(f"/api/v1/patients/{patient_id}/wearable", json=wearable_payload, headers=headers)
    assert res_wearable.status_code == 200
    assert res_wearable.json()["serial_number"] == "WEAR-998877"
