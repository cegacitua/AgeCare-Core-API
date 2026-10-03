import asyncio
import sys
import os

# Asegurar que podemos importar desde app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime, timezone, timedelta, date
from app.core.database import async_engine, AsyncSessionLocal
from app.core.security import get_password_hash
from app.models.user import User
from app.models.patient import Patient, PatientMember, Wearable
from app.models.vital import VitalReading, VitalThreshold
from app.models.medication import Medication, ScheduledDose
from app.models.alert import Alert

async def seed_data():
    async with AsyncSessionLocal() as session:
        # 1. Crear Usuario
        user = User(
            email="demo@agecare.app",
            password_hash=get_password_hash("password123"),
            full_name="Usuario Demo Familiar",
            phone="+56912345678"
        )
        session.add(user)
        await session.flush()
        
        # 2. Crear Paciente
        patient = Patient(
            full_name="Roberto Gómez (Abuelo)",
            birth_date=date(1945, 5, 12),
            sex="M",
            conditions=["Hipertensión", "Diabetes Tipo 2"]
        )
        session.add(patient)
        await session.flush()

        # 3. Vincular Usuario y Paciente
        member = PatientMember(
            patient_id=patient.id,
            user_id=user.id,
            role="family",
            is_owner=True
        )
        session.add(member)
        
        # 4. Dispositivo Wearable
        wearable = Wearable(
            patient_id=patient.id,
            serial_number="AC-W-2026-0001",
            model="AgeCare Band Pro",
            battery_pct=85,
            last_sync_at=datetime.now(timezone.utc)
        )
        session.add(wearable)

        # 5. Umbrales Vitales
        vt_hr = VitalThreshold(patient_id=patient.id, type="heart_rate", min_value=50.0, max_value=100.0)
        vt_spo2 = VitalThreshold(patient_id=patient.id, type="spo2", min_value=92.0, max_value=100.0)
        session.add_all([vt_hr, vt_spo2])

        # 6. Historial de Signos Vitales
        now = datetime.now(timezone.utc)
        for i in range(12):
            hr = VitalReading(
                patient_id=patient.id,
                type="heart_rate",
                value=70.0 + (i % 5),
                measured_at=now - timedelta(hours=i),
                source="wearable"
            )
            spo2 = VitalReading(
                patient_id=patient.id,
                type="spo2",
                value=96.0 + (i % 3),
                measured_at=now - timedelta(hours=i),
                source="wearable"
            )
            session.add_all([hr, spo2])
        
        # 7. Medicamentos
        med = Medication(
            patient_id=patient.id,
            name="Losartán",
            dose="50 mg",
            instructions="Tomar con agua en ayunas",
            times=["08:00"],
            days_of_week=[0, 1, 2, 3, 4, 5, 6],
            start_date=date.today(),
            prescribed_by="Dr. Pérez"
        )
        session.add(med)
        await session.flush()
        
        # 8. Dosis Programadas (Simular adherence de hoy)
        dose_time = datetime.combine(date.today(), datetime.strptime("08:00", "%H:%M").time()).replace(tzinfo=timezone.utc)
        dose = ScheduledDose(
            medication_id=med.id,
            patient_id=patient.id,
            scheduled_at=dose_time,
            status="taken",
            logged_by=user.id,
            logged_at=dose_time + timedelta(minutes=10)
        )
        session.add(dose)

        # 9. Alerta
        alert = Alert(
            patient_id=patient.id,
            type="vital_out_of_range",
            severity="warning",
            title="Ritmo cardíaco algo elevado",
            detail="Se detectaron 102 lpm de forma puntual.",
            status="pending"
        )
        session.add(alert)
        
        await session.commit()
        print("✅ Base de datos poblada con éxito.")
        print(f"📧 Email de ingreso: demo@agecare.app")
        print(f"🔑 Contraseña: password123")
        print(f"👤 ID de Paciente generado: {patient.id}")

if __name__ == "__main__":
    asyncio.run(seed_data())
