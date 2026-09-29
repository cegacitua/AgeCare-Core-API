import pytest


@pytest.mark.asyncio
async def test_alloxentric_voice_upload_and_transcription(client):
    # Setup user & patient
    reg_res = await client.post("/api/v1/auth/register", json={
        "email": "cuidadora_voz@agecare.cl", "password": "Password123!", "full_name": "Ana Cuidadora"
    })
    token = reg_res.json()["access_token"]
    user_id = reg_res.json()["user"]["id"]
    headers = {"Authorization": f"Bearer {token}"}

    pat_res = await client.post("/api/v1/patients", json={"full_name": "Paciente Voz"}, headers=headers)
    patient_id = pat_res.json()["id"]

    # Upload voice note file (.wav)
    files = {"file": ("nota_observacion.wav", b"RIFF....WAVEfmt ....data....", "audio/wav")}
    data = {"patientId": patient_id, "caregiverId": user_id}

    res_upload = await client.post("/api/v1/voice/upload", files=files, data=data, headers=headers)
    assert res_upload.status_code == 202
    res_json = res_upload.json()
    assert "jobId" in res_json

    job_id = res_json["jobId"]

    # Retrieve STT transcription
    res_stt = await client.get(f"/api/v1/voice/transcriptions/{job_id}", headers=headers)
    assert res_stt.status_code == 200
    stt_data = res_stt.json()
    assert stt_data["status"] == "completed"
    assert "presión alta" in stt_data["transcription"]
    assert stt_data["extractedData"]["sentiment"] == "positive"
