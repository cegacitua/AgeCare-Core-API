# 🏥 AgeCare Core API (Backend REST & Real-time WebSockets)

Backend oficial de la Suite de Cuidado de Adultos Mayores **AgeCare**, desarrollado bajo la especificación v1 de la empresa y alineado con los requerimientos técnicos de **Alloxentric**.

---

## 🛠️ Stack Tecnológico
- **Framework:** FastAPI (Python 3.12+)
- **Validación de Esquemas:** Pydantic v2 (ConfigDict, Pydantic-Settings)
- **Base de Datos:** PostgreSQL (Azure Database for PostgreSQL Flexible Server) vía SQLAlchemy 2.0 Async (`asyncpg`)
- **Migraciones:** Alembic
- **Seguridad:** JWT Bearer (Access Token 30m / Refresh Token 30d rotatorio) y Hashing con `bcrypt`
- **Integraciones:**
  - **Alloxentric Speech-to-Text & NLP Engine:** Transcripción asincrónica de notas de voz clínicas y extracción de entidades/sentimiento.
  - **Azure Blob Storage:** Carga directa con URLs firmadas (SAS) para exámenes y fotos.
  - **FastAPI WebSockets:** Chat bidireccional en tiempo real para el círculo de cuidado.

---

## 🚀 Arquitectura de Módulos (82 Endpoints + WebSockets)

| Módulo | Prefijo | Descripción |
| :--- | :--- | :--- |
| **Autenticación** | `/api/v1/auth` | Registro, login, refresh JWT, perfil, tokens push |
| **Pacientes & Onboarding** | `/api/v1/patients` | CRUD paciente, invitaciones, miembros y vinculación de wearable |
| **Signos Vitales & Semáforo** | `/api/v1/patients/{id}/vitals` | Ingesta por lotes (wearable), ingreso manual, umbrales y semáforo de bienestar |
| **Medicamentos & Adherencia** | `/api/v1/patients/{id}/medications` | Plan de medicamentos, dosis del día, confirmación de tomas y adherencia |
| **Bitácora & Incidentes** | `/api/v1/patients/{id}/observations` | Observaciones, incidentes, notas de relevo entre turnos y check-in |
| **Archivos & Documentos** | `/api/v1/uploads` & `/patients/{id}/documents` | Solicitar URLs de subida a Blob Storage y repositorio médico |
| **Alertas &SOS** | `/api/v1/alerts` & `/patients/{id}/sos` | Centro de alertas (caídas, signos fuera de rango, SOS), ack, solución |
| **Asistente IA** | `/api/v1/patients/{id}/assistant` | Consultas inteligentes en lenguaje natural sobre la historia del paciente |
| **Mensajes & Chat** | `/api/v1/patients/{id}/messages` | Historial del chat humano y puntero de mensajes leídos |
| **Vista Adulto Mayor** | `/api/v1/elder` | Galería de fotos, reacciones por voz, chistes/noticias y TTS/STT |
| **Vista Cuidadora** | `/api/v1/caregiver` | Tareas del día, perfil profesional, suscripción gratis/premium y bolsa de trabajo |
| **Marketplace** | `/api/v1/marketplace` | Vitrina de cuidadoras, calificaciones, contacto y catálogo de artículos |
| **Procesamiento de Voz (Alloxentric)** | `/api/v1/voice` | Subida multipart de audio `.wav`/`.m4a`, transcripción STT y análisis NLP |
| **WebSocket Chat** | `/ws/chat/{patient_id}` | Canal bidireccional en tiempo real |

---

## 🧪 Ejecución de Pruebas Unitarias e Integración

Para ejecutar la suite de pruebas automatizadas:

```bash
# 1. Crear entorno e instalar dependencias
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Ejecutar pytest
PYTHONPATH=. pytest
```

---

## 🐋 Ejecución Local con Docker Compose

```bash
# Iniciar API FastAPI y PostgreSQL en contenedor
docker-compose up --build
```

- Documentación Interactiva Swagger UI: `http://localhost:8000/docs`
- Especificación OpenAPI JSON: `http://localhost:8000/api/v1/openapi.json`
