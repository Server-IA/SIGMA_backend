# Copilot Instructions for AppMachineryPayrollBackend

## Project Overview
This backend powers the "Gestión de Maquinaria y Nómina" system. It is the central service, providing the database and main business modules. The architecture is modular, with each domain (machinery, maintenance, monitoring, payroll, service_requests, users, etc.) implemented as a Django app under the project root.

## Key Architectural Patterns
- **Modular Django Apps:** Each major business domain is a separate Django app (see folders: `machinery/`, `maintenance/`, `monitoring/`, `payroll/`, `service_requests/`, `users/`).
- **API Layer:** REST APIs are implemented in each app's `api/` subfolder using Django REST Framework viewsets.
- **Migrations:** Each app manages its own migrations in a `migrations/` subfolder.
- **Configuration:** Central settings are in `machpaymanager/settings.py`. Environment variables are loaded from `.env` (see `.env.example`).
- **Dockerized Development:** All development and execution is done inside Docker containers. No local Python venvs are used.

## Developer Workflows
- **Build & Run:**
  - Use `docker-compose up --build` to build and start the backend.
  - Ensure Docker network `shared_net` exists for cross-service communication (`docker network create shared_net`).
- **Database Initialization:**
  - Run migrations inside the container:
    - `docker-compose exec web python manage.py makemigrations`
    - `docker-compose exec web python manage.py migrate`
- **Testing:**
  - Tests are located in each app's `tests.py` or `tests/` folder.
  - Use `pytest` for running tests (see `pytest.ini`).
- **Environment:**
  - Copy `.env.example` to `.env` and configure as needed.

## Project-Specific Conventions
- **Branch Workflow:**
  - Main branches: `develop` (feature dev), `main` (approved changes), `test` (QA), `dokploy` (production).
  - PRs target `develop`; merges flow to `main`, then `test`, then `dokploy`.
- **Service Boundaries:**
  - Each Django app is responsible for its own models, serializers, views, and API endpoints.
  - Shared config (e.g., Firebase) is in `config/`.
- **External Integrations:**
  - Database: PostgreSQL (see Docker config).
  - Firebase integration in `config/firebase_config.py`.

## Examples
- To add a new API endpoint for machinery, create a viewset in `machinery/api/` and register it in `machinery/urls.py`.
- To add a migration, update models in the relevant app and run migration commands inside the container.

## References
- Main settings: `machpaymanager/settings.py`
- Docker config: `docker-compose.yml`, `Dockerfile`
- API implementations: `*/api/`
- Migrations: `*/migrations/`
- Tests: `*/tests.py`, `*/tests/`
- Firebase: `config/firebase_config.py`

---
For questions about unclear workflows or missing conventions, ask the user for clarification or examples from their team.
