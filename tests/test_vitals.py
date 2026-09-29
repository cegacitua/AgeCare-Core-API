import pytest


@pytest.mark.asyncio
async def test_vitals_and_wellbeing_summary(client):
    # Setup user & patient
    reg_res = await client.post("/api/v1/auth/register", json={
        "email": "doctor@agecare.cl", "password": "Password123!", "full_name": "Dr. Ruiz"
    })
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    pat_res = await client.post("/api/v1/patients", json={"full_name": "Paciente Test"}, headers=headers)
    patient_id = pat_res.json()["id"]

    # Manual vital register
    vital_payload = {
        "type": "heart_rate",
        "value": 75.0,
        "measured_at": "2026-09-28T12:00:00Z",
        "source": "manual"
    }
    res_v = await client.post(f"/api/v1/patients/{patient_id}/vitals/manual", json=vital_payload, headers=headers)
    assert res_v.status_code == 201

    # Wellbeing summary query
    res_summary = await client.get(f"/api/v1/patients/{patient_id}/vitals/wellbeing", headers=headers)
    assert res_summary.status_code == 200
    assert res_summary.json()["status"] == "ok"
