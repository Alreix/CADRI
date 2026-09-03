#!/bin/bash

set -e

echo ""
echo "================================================"
echo " CADRI Bootstrap Script"
echo "================================================"
echo ""

# ---------------------------------------------------------------------------
# Locate project root
# ---------------------------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

while [ "$PROJECT_ROOT" != "/" ] && [ ! -f "$PROJECT_ROOT/docker-compose.yml" ]; do
    PROJECT_ROOT="$(dirname "$PROJECT_ROOT")"
done

if [ ! -f "$PROJECT_ROOT/docker-compose.yml" ]; then
    echo "ERROR: docker-compose.yml was not found."
    echo "Run this script from inside the CADRI project."
    exit 1
fi

cd "$PROJECT_ROOT"

echo "Project root detected:"
echo "$PROJECT_ROOT"
echo ""

# ---------------------------------------------------------------------------
# Start database and mail service
# ---------------------------------------------------------------------------

echo "Starting database and mail containers..."
docker compose up -d db mailpit

echo ""
echo "Waiting for PostgreSQL to be ready..."

until docker compose exec -T db pg_isready -U cadri_user -d postgres > /dev/null 2>&1; do
    echo "PostgreSQL is not ready yet. Waiting..."
    sleep 2
done

echo "PostgreSQL is ready."
echo ""

# ---------------------------------------------------------------------------
# Reset development and test databases
# ---------------------------------------------------------------------------

echo "Resetting development database..."
docker compose exec -T db psql -U cadri_user -d postgres -c "DROP DATABASE IF EXISTS cadri_db WITH (FORCE);"
docker compose exec -T db psql -U cadri_user -d postgres -c "CREATE DATABASE cadri_db;"

echo ""
echo "Resetting test database..."
docker compose exec -T db psql -U cadri_user -d postgres -c "DROP DATABASE IF EXISTS cadri_test_db WITH (FORCE);"
docker compose exec -T db psql -U cadri_user -d postgres -c "CREATE DATABASE cadri_test_db;"

echo ""

# ---------------------------------------------------------------------------
# Build and start application containers
# ---------------------------------------------------------------------------

echo "Starting application containers..."
docker compose up --build -d backend frontend

echo ""

# ---------------------------------------------------------------------------
# Upgrade development database
# ---------------------------------------------------------------------------

echo "Running migrations on development database..."
docker compose exec -T backend flask db upgrade

echo ""

# ---------------------------------------------------------------------------
# Seed development database
# ---------------------------------------------------------------------------

echo "Seeding development database..."
docker compose exec -T backend python -c "
from app import create_app
from app.seeds import run_seed

app = create_app()

with app.app_context():
    run_seed()
"

echo ""

# ---------------------------------------------------------------------------
# Upgrade test database
# ---------------------------------------------------------------------------

echo "Running migrations on test database..."
docker compose exec -T -e FLASK_ENV=testing backend flask db upgrade

echo ""

# ---------------------------------------------------------------------------
# Seed test database
# ---------------------------------------------------------------------------

echo "Seeding test database..."
docker compose exec -T -e FLASK_ENV=testing backend python -c "
from app import create_app
from app.seeds import run_seed

app = create_app()

with app.app_context():
    run_seed()
"

echo ""

# ---------------------------------------------------------------------------
# Verify development seed
# ---------------------------------------------------------------------------

echo "Verifying development seed..."
docker compose exec -T backend python -c "
from app import create_app
from app.models.role import Role
from app.models.service import Service
from app.models.user import User

app = create_app()

with app.app_context():
    roles = Role.query.count()
    services = Service.query.count()
    users = User.query.count()
    admin = User.query.filter_by(email='admin@cadri.local').first()
    responsable = User.query.filter_by(email='responsable@cadri.local').first()
    agent = User.query.filter_by(email='agent@cadri.local').first()

    print(f'Development seed: roles={roles}, services={services}, users={users}')

    if roles < 3 or services < 6 or not admin or not responsable or not agent:
        raise SystemExit('ERROR: Development seed verification failed.')
"

echo ""

# ---------------------------------------------------------------------------
# Verify test seed
# ---------------------------------------------------------------------------

echo "Verifying test seed..."
docker compose exec -T -e FLASK_ENV=testing backend python -c "
from app import create_app
from app.models.role import Role
from app.models.service import Service
from app.models.user import User

app = create_app()

with app.app_context():
    roles = Role.query.count()
    services = Service.query.count()
    users = User.query.count()
    admin = User.query.filter_by(email='admin@cadri.local').first()
    responsable = User.query.filter_by(email='responsable@cadri.local').first()
    agent = User.query.filter_by(email='agent@cadri.local').first()

    print(f'Test seed: roles={roles}, services={services}, users={users}')

    if roles < 3 or services < 6 or not admin or not responsable or not agent:
        raise SystemExit('ERROR: Test seed verification failed.')
"

echo ""

# ---------------------------------------------------------------------------
# Compile backend
# ---------------------------------------------------------------------------

echo "Checking Python compilation..."
docker compose exec -T backend python -m compileall app tests

echo ""

# ---------------------------------------------------------------------------
# Final information
# ---------------------------------------------------------------------------

echo "================================================"
echo " CADRI is ready."
echo "================================================"
echo ""
echo "Frontend:"
echo "http://localhost:5173"
echo ""
echo "Backend:"
echo "http://localhost:5000"
echo ""
echo "Swagger / API docs:"
echo "http://localhost:5000/docs"
echo ""
echo "Mailpit:"
echo "http://localhost:8025"
echo ""
echo "Default users:"
echo "Admin:        admin@cadri.local / StrongPass1*"
echo "Responsable:  responsable@cadri.local / StrongPass1*"
echo "Agent:        agent@cadri.local / StrongPass1*"
echo ""
echo "To run backend tests:"
echo "docker compose exec backend pytest -v"
echo ""
echo "To run cURL QA tests:"
echo "./cadri_curl_full_test_suite.sh"
echo ""
