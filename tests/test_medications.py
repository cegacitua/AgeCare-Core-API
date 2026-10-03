import pytest
import pytest_asyncio
from httpx import AsyncClient
from app.models.user import User
from app.models.patient import Patient, PatientMember
from app.models.medication import Medication
from app.core.security import get_password_hash, create_access_token
from datetime import date

@pytest_asyncio.fixture
async def test_user_and_patient(db):
    user = User(email="medtest@agecare.app", password_hash=get_password_hash("test"), full_name="Test")
    db.add(user)
    await db.flush()

    patient = Patient(full_name="Pat Test", birth_date=date(1950, 1, 1), sex="M")
    db.add(patient)
    await db.flush()

    member = PatientMember(patient_id=patient.id, user_id=user.id, role="family", is_owner=True)
    db.add(member)
    await db.commit()

    token = create_access_token(subject=user.id)
    return {"token": token, "patient_id": patient.id, "user_id": user.id}


@pytest.mark.asyncio
async def test_create_medication(client: AsyncClient, test_user_and_patient):
    token = test_user_and_patient["token"]
    pat_id = test_user_and_patient["patient_id"]

    resp = await client.post(
        f"/api/v1/patients/{pat_id}/medications",
        json={
            "name": "Paracetamol",
            "dose": "500 mg",
            "instructions": "Para el dolor",
            "times": ["08:00", "20:00"],
            "days_of_week": [0,1,2,3,4,5,6],
            "start_date": "2026-09-01",
            "grace_window_min": 60,
            "prescribed_by": "Dr. Test"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Paracetamol"
    assert len(data["schedule"]) == 2


@pytest.mark.asyncio
async def test_list_medications(client: AsyncClient, test_user_and_patient, db):
    token = test_user_and_patient["token"]
    pat_id = test_user_and_patient["patient_id"]

    med = Medication(patient_id=pat_id, name="Losartán", dose="50 mg", times=["10:00"], days_of_week=[1], start_date=date(2026, 9, 1))
    db.add(med)
    await db.commit()

    resp = await client.get(f"/api/v1/patients/{pat_id}/medications", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert len(resp.json()["items"]) == 1
    assert resp.json()["items"][0]["name"] == "Losartán"


@pytest.mark.asyncio
async def test_adherence_metrics(client: AsyncClient, test_user_and_patient):
    token = test_user_and_patient["token"]
    pat_id = test_user_and_patient["patient_id"]

    # Since no doses exist yet, fallback array should be generated and adherence 100%
    resp = await client.get(f"/api/v1/patients/{pat_id}/adherence", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["adherence_rate_pct"] == 100.0
    assert data["total_scheduled"] == 0
    assert len(data["by_day"]) == 1  # Fallback
