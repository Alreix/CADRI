#!/usr/bin/env bash
# CADRI full cURL smoke/regression test suite
# ------------------------------------------------------------
# Purpose:
#   Run a broad HTTP-level verification of the CADRI backend routes.
#   This script complements pytest; it does not replace the automated unit,
#   integration, and API tests.
#
# Requirements:
#   - CADRI Docker stack running
#   - backend reachable on BASE_URL, default: http://127.0.0.1:5000
#   - python3 and curl installed on the host
#   - seeded local users available:
#       admin@cadri.local / StrongPass1
#       responsable@cadri.local / StrongPass1
#       agent@cadri.local / StrongPass1
#
# Usage from apps/backend or project root:
#   chmod +x cadri_curl_full_test_suite.sh
#   ./cadri_curl_full_test_suite.sh
#
# Optional:
#   BASE_URL="http://127.0.0.1:5000" ./cadri_curl_full_test_suite.sh
#
# WARNING:
#   This script creates and deletes test users/missions in the development DB.
#   Run it only on a local/dev database, never on production.

set -u

BASE_URL="${BASE_URL:-http://127.0.0.1:5000}"
MAILPIT_URL="${MAILPIT_URL:-http://127.0.0.1:8025}"
TMP_DIR="$(mktemp -d)"
COOKIE_ADMIN="$TMP_DIR/admin.cookies"
COOKIE_RESPONSABLE="$TMP_DIR/responsable.cookies"
COOKIE_AGENT="$TMP_DIR/agent.cookies"
COOKIE_TEMP="$TMP_DIR/temp.cookies"
COOKIE_PREVIOUS="$TMP_DIR/previous.cookies"
LAST_BODY="$TMP_DIR/last_body.json"
PASS=0
FAIL=0
SKIP=0
RUN_ID="$(date +%s)"

cleanup() {
    rm -rf "$TMP_DIR"
}
trap cleanup EXIT

line() {
    echo "------------------------------------------------------------"
}

section() {
    echo ""
    line
    echo "$1"
    line
}

check() {
    local description="$1"
    local expected="$2"
    local actual="$3"

    if [ "$actual" = "$expected" ]; then
        echo "PASS — $description"
        PASS=$((PASS + 1))
    else
        echo "FAIL — $description (expected $expected, got $actual)"
        echo "Response body:"
        sed 's/^/  /' "$LAST_BODY" 2>/dev/null || true
        FAIL=$((FAIL + 1))
    fi
}

check_one_of() {
    local description="$1"
    local actual="$2"
    shift 2
    local allowed="$*"

    for expected in "$@"; do
        if [ "$actual" = "$expected" ]; then
            echo "PASS — $description"
            PASS=$((PASS + 1))
            return
        fi
    done

    echo "FAIL — $description (expected one of: $allowed, got $actual)"
    echo "Response body:"
    sed 's/^/  /' "$LAST_BODY" 2>/dev/null || true
    FAIL=$((FAIL + 1))
}

skip_check() {
    local description="$1"
    local reason="$2"
    echo "SKIP — $description ($reason)"
    SKIP=$((SKIP + 1))
}

request() {
    # Usage: STATUS=$(request curl args...)
    curl -sS -o "$LAST_BODY" -w "%{http_code}" "$@"
}

json_get() {
    # Usage: json_get path.to.value [file]
    # Supports dict keys and list indexes: user.id, 0.id, items.0.id
    local path="$1"
    local file="${2:-$LAST_BODY}"
    python3 - "$path" "$file" <<'PY'
import json
import sys
path = sys.argv[1]
file = sys.argv[2]
try:
    with open(file, "r", encoding="utf-8") as f:
        data = json.load(f)
    current = data
    if path:
        for part in path.split("."):
            if isinstance(current, list):
                current = current[int(part)]
            else:
                current = current[part]
    if current is None:
        print("")
    elif isinstance(current, (dict, list)):
        print(json.dumps(current))
    else:
        print(current)
except Exception:
    print("")
PY
}

json_find_id_by_name() {
    # Usage: json_find_id_by_name name [file]
    local target_name="$1"
    local file="${2:-$LAST_BODY}"
    python3 - "$target_name" "$file" <<'PY'
import json
import sys
name = sys.argv[1]
file = sys.argv[2]
try:
    with open(file, "r", encoding="utf-8") as f:
        data = json.load(f)
    for item in data:
        if item.get("name") == name:
            print(item.get("id", ""))
            break
except Exception:
    print("")
PY
}

json_find_user_id_by_email() {
    local target_email="$1"
    local file="${2:-$LAST_BODY}"
    python3 - "$target_email" "$file" <<'PY'
import json
import sys
email = sys.argv[1]
file = sys.argv[2]
try:
    with open(file, "r", encoding="utf-8") as f:
        data = json.load(f)
    items = data.get("items", data if isinstance(data, list) else [])
    for item in items:
        if item.get("email") == email:
            print(item.get("id", ""))
            break
except Exception:
    print("")
PY
}

make_mission_payload() {
    local title="$1"
    local priority="${2:-medium}"
    local service_id="${3:-$GREEN_SERVICE_ID}"
    local assigned_user_id="${4:-$AGENT_ID}"
    local start_date="${5:-2026-06-01T09:00:00}"
    local end_date="${6:-2026-06-01T12:00:00}"
    cat <<JSON
{
  "title": "$title",
  "intervention_type": "maintenance",
  "location": "Cavalaire-sur-Mer",
  "description": "Automated cURL test mission $RUN_ID",
  "planned_agents_count": 1,
  "estimated_duration": 3,
  "start_date": "$start_date",
  "end_date": "$end_date",
  "priority": "$priority",
  "required_equipment": "standard tools",
  "signage_required": false,
  "service_ids": ["$service_id"],
  "assigned_user_ids": ["$assigned_user_id"]
}
JSON
}

login_and_capture() {
    local email="$1"
    local password="$2"
    local cookie_file="$3"
    local token_var_name="$4"
    local description="$5"

    local status
    status=$(request -X POST "$BASE_URL/auth/login" \
        -c "$cookie_file" \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"$email\",\"password\":\"$password\"}")
    check "$description" 200 "$status"

    local token
    token=$(json_get "access_token")
    if [ -z "$token" ]; then
        echo "FAIL — $description token capture failed"
        FAIL=$((FAIL + 1))
    fi
    printf -v "$token_var_name" '%s' "$token"
}

create_user_api() {
    local token="$1"
    local first_name="$2"
    local last_name="$3"
    local email="$4"
    local role="$5"
    local service_id="$6"
    request -X POST "$BASE_URL/users" \
        -H "Authorization: Bearer $token" \
        -H "Content-Type: application/json" \
        -d "{\"first_name\":\"$first_name\",\"last_name\":\"$last_name\",\"email\":\"$email\",\"role\":\"$role\",\"service_id\":\"$service_id\"}"
}

get_activation_token_from_db() {
    local email="$1"
    docker compose exec -T backend python - "$email" <<'PY' 2>/dev/null
import sys
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.account_activation_token import AccountActivationToken
app = create_app()
with app.app_context():
    user = User.query.filter_by(email=sys.argv[1]).first()
    if not user:
        print("")
        raise SystemExit
    token, raw = AccountActivationToken.create_for_user(user.id)
    db.session.add(token)
    db.session.commit()
    print(raw)
PY
}

get_reset_token_from_db() {
    local email="$1"
    docker compose exec -T backend python - "$email" <<'PY' 2>/dev/null
import sys
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.password_reset_token import PasswordResetToken
app = create_app()
with app.app_context():
    user = User.query.filter_by(email=sys.argv[1]).first()
    if not user:
        print("")
        raise SystemExit
    token, raw = PasswordResetToken.create_for_user(user.id)
    db.session.add(token)
    db.session.commit()
    print(raw)
PY
}

ensure_seed_data() {
    if command -v docker >/dev/null 2>&1 && docker compose ps backend >/dev/null 2>&1; then
        docker compose exec -T backend python - <<'PY' >/dev/null 2>&1 || true
from app import create_app
from app.seeds.seed_initial_data import run_seed
app = create_app()
with app.app_context():
    run_seed()
PY
    fi
}

reset_test_passwords() {
    # Keep local seed users reusable after the cURL suite.
    if command -v docker >/dev/null 2>&1 && docker compose ps backend >/dev/null 2>&1; then
        docker compose exec -T backend python - <<'PY' >/dev/null 2>&1 || true
from app import create_app
from app.extensions import db
from app.models.user import User
app = create_app()
with app.app_context():
    for email in ("admin@cadri.local", "responsable@cadri.local", "agent@cadri.local"):
        user = User.query.filter_by(email=email).first()
        if user:
            user.set_password("StrongPass1")
            user.is_active = True
    db.session.commit()
PY
    fi
}

UNKNOWN_UUID="00000000-0000-0000-0000-000000000000"

section "CADRI cURL Test Suite"
echo "Backend URL: $BASE_URL"
echo "Mailpit URL: $MAILPIT_URL"
echo "Run ID: $RUN_ID"
echo ""
echo "This script is destructive for test data. Use only on local/dev DB."

ensure_seed_data
reset_test_passwords

section "Health routes"
STATUS=$(request -X GET "$BASE_URL/auth/health")
check "GET /auth/health returns 200" 200 "$STATUS"
STATUS=$(request -X GET "$BASE_URL/me/health")
check "GET /me/health returns 200" 200 "$STATUS"
STATUS=$(request -X GET "$BASE_URL/users/health")
check "GET /users/health returns 200" 200 "$STATUS"
STATUS=$(request -X GET "$BASE_URL/metadata/health")
check "GET /metadata/health returns 200" 200 "$STATUS"
STATUS=$(request -X GET "$BASE_URL/missions/health")
check "GET /missions/health returns 200" 200 "$STATUS"
STATUS=$(request -X GET "$BASE_URL/docs")
check_one_of "GET /docs is reachable" "$STATUS" 200 308 301

section "Authentication setup"
login_and_capture "admin@cadri.local" "StrongPass1" "$COOKIE_ADMIN" ADMIN_TOKEN "Admin login returns 200"
login_and_capture "responsable@cadri.local" "StrongPass1" "$COOKIE_RESPONSABLE" RESPONSABLE_TOKEN "Responsable login returns 200"
login_and_capture "agent@cadri.local" "StrongPass1" "$COOKIE_AGENT" AGENT_TOKEN "Agent login returns 200"

STATUS=$(request -X POST "$BASE_URL/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email":"admin@cadri.local","password":"WrongPassword1"}')
check "POST /auth/login wrong password returns 401" 401 "$STATUS"

STATUS=$(request -X POST "$BASE_URL/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email":"unknown@cadri.local","password":"StrongPass1"}')
check "POST /auth/login unknown email returns 401" 401 "$STATUS"

STATUS=$(request -X POST "$BASE_URL/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email":"invalid-email","password":"StrongPass1"}')
check "POST /auth/login invalid email returns 400" 400 "$STATUS"

STATUS=$(request -X POST "$BASE_URL/auth/login" \
    -H "Content-Type: application/json" \
    -d '{}')
check_one_of "POST /auth/login empty JSON returns validation error" "$STATUS" 400 415

section "Metadata routes"
STATUS=$(request -X GET "$BASE_URL/metadata/roles")
check "GET /metadata/roles without token returns 401" 401 "$STATUS"

STATUS=$(request -X GET "$BASE_URL/metadata/roles" -H "Authorization: Bearer $ADMIN_TOKEN")
check "GET /metadata/roles with admin returns 200" 200 "$STATUS"

STATUS=$(request -X GET "$BASE_URL/metadata/services" -H "Authorization: Bearer $ADMIN_TOKEN")
check "GET /metadata/services with admin returns 200" 200 "$STATUS"
GREEN_SERVICE_ID=$(json_find_id_by_name "green_spaces")
ROADS_SERVICE_ID=$(json_find_id_by_name "roads")

if [ -z "$GREEN_SERVICE_ID" ] || [ -z "$ROADS_SERVICE_ID" ]; then
    echo "FAIL — Could not capture service IDs from /metadata/services"
    FAIL=$((FAIL + 1))
else
    echo "INFO — green_spaces service id: $GREEN_SERVICE_ID"
    echo "INFO — roads service id: $ROADS_SERVICE_ID"
fi

STATUS=$(request -X GET "$BASE_URL/metadata/priorities" -H "Authorization: Bearer $ADMIN_TOKEN")
check "GET /metadata/priorities with admin returns 200" 200 "$STATUS"

STATUS=$(request -X GET "$BASE_URL/metadata/statuses" -H "Authorization: Bearer $ADMIN_TOKEN")
check "GET /metadata/statuses with admin returns 200" 200 "$STATUS"

section "Current user /me routes"
STATUS=$(request -X GET "$BASE_URL/me")
check "GET /me without token returns 401" 401 "$STATUS"

STATUS=$(request -X GET "$BASE_URL/me" -H "Authorization: Bearer $ADMIN_TOKEN")
check "GET /me as admin returns 200" 200 "$STATUS"
ADMIN_ID=$(json_get "id")

STATUS=$(request -X GET "$BASE_URL/me" -H "Authorization: Bearer $RESPONSABLE_TOKEN")
check "GET /me as responsable returns 200" 200 "$STATUS"
RESPONSABLE_ID=$(json_get "id")

STATUS=$(request -X GET "$BASE_URL/me" -H "Authorization: Bearer $AGENT_TOKEN")
check "GET /me as agent returns 200" 200 "$STATUS"
AGENT_ID=$(json_get "id")

STATUS=$(request -X PATCH "$BASE_URL/me" \
    -H "Authorization: Bearer $AGENT_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"first_name":"Agent","last_name":"Cadri","email":"agent@cadri.local"}')
check "PATCH /me valid profile update returns 200" 200 "$STATUS"

STATUS=$(request -X PATCH "$BASE_URL/me" \
    -H "Content-Type: application/json" \
    -d '{"first_name":"No","last_name":"Auth","email":"noauth@cadri.test"}')
check "PATCH /me without token returns 401" 401 "$STATUS"

STATUS=$(request -X PATCH "$BASE_URL/me" \
    -H "Authorization: Bearer $AGENT_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"first_name":"Agent","last_name":"Cadri","email":"admin@cadri.local"}')
check "PATCH /me duplicate email returns 409" 409 "$STATUS"

STATUS=$(request -X PATCH "$BASE_URL/me" \
    -H "Authorization: Bearer $AGENT_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"first_name":"Agent","last_name":"Cadri","email":"invalid-email"}')
check "PATCH /me invalid email returns 400" 400 "$STATUS"

STATUS=$(request -X PATCH "$BASE_URL/me" \
    -H "Authorization: Bearer $AGENT_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{}')
check_one_of "PATCH /me empty body returns validation error" "$STATUS" 400 415

section "User management routes"
STATUS=$(request -X GET "$BASE_URL/users")
check "GET /users without token returns 401" 401 "$STATUS"

STATUS=$(request -X GET "$BASE_URL/users" -H "Authorization: Bearer $ADMIN_TOKEN")
check "GET /users as admin returns 200" 200 "$STATUS"

STATUS=$(request -X GET "$BASE_URL/users" -H "Authorization: Bearer $RESPONSABLE_TOKEN")
check "GET /users as responsable returns 403" 403 "$STATUS"

STATUS=$(request -X GET "$BASE_URL/users" -H "Authorization: Bearer $AGENT_TOKEN")
check "GET /users as agent returns 403" 403 "$STATUS"

STATUS=$(request -X GET "$BASE_URL/users?search=agent" -H "Authorization: Bearer $ADMIN_TOKEN")
check "GET /users?search=agent returns 200" 200 "$STATUS"

STATUS=$(request -X GET "$BASE_URL/users?role=agent" -H "Authorization: Bearer $ADMIN_TOKEN")
check "GET /users?role=agent returns 200" 200 "$STATUS"

STATUS=$(request -X GET "$BASE_URL/users?service_id=$GREEN_SERVICE_ID" -H "Authorization: Bearer $ADMIN_TOKEN")
check "GET /users?service_id=<id> returns 200" 200 "$STATUS"

STATUS=$(request -X GET "$BASE_URL/users?page=1&per_page=2" -H "Authorization: Bearer $ADMIN_TOKEN")
check "GET /users pagination returns 200" 200 "$STATUS"

STATUS=$(request -X GET "$BASE_URL/users?page=0&per_page=10" -H "Authorization: Bearer $ADMIN_TOKEN")
check "GET /users page=0 returns 400" 400 "$STATUS"

STATUS=$(request -X GET "$BASE_URL/users?page=1&per_page=101" -H "Authorization: Bearer $ADMIN_TOKEN")
check "GET /users per_page=101 returns 400" 400 "$STATUS"

STATUS=$(request -X GET "$BASE_URL/users?role=unknown" -H "Authorization: Bearer $ADMIN_TOKEN")
check "GET /users unknown role filter returns 404" 404 "$STATUS"

STATUS=$(request -X GET "$BASE_URL/users?service_id=$UNKNOWN_UUID" -H "Authorization: Bearer $ADMIN_TOKEN")
check "GET /users unknown service filter returns 404" 404 "$STATUS"

TEMP_AGENT_EMAIL="curl.agent.$RUN_ID@cadri.test"
STATUS=$(create_user_api "$ADMIN_TOKEN" "Curl" "Agent" "$TEMP_AGENT_EMAIL" "agent" "$GREEN_SERVICE_ID")
check "POST /users as admin creates inactive agent returns 201" 201 "$STATUS"
TEMP_AGENT_ID=$(json_get "user.id")

STATUS=$(create_user_api "$RESPONSABLE_TOKEN" "Resp" "Agent" "curl.resp.agent.$RUN_ID@cadri.test" "agent" "$GREEN_SERVICE_ID")
check "POST /users as responsable creates agent returns 201" 201 "$STATUS"
RESP_CREATED_AGENT_ID=$(json_get "user.id")

STATUS=$(create_user_api "$RESPONSABLE_TOKEN" "Blocked" "Admin" "curl.blocked.admin.$RUN_ID@cadri.test" "admin" "$GREEN_SERVICE_ID")
check "POST /users responsable cannot create admin returns 403" 403 "$STATUS"

STATUS=$(create_user_api "$AGENT_TOKEN" "Blocked" "User" "curl.blocked.user.$RUN_ID@cadri.test" "agent" "$GREEN_SERVICE_ID")
check "POST /users agent cannot create user returns 403" 403 "$STATUS"

STATUS=$(create_user_api "$ADMIN_TOKEN" "Duplicate" "Email" "admin@cadri.local" "agent" "$GREEN_SERVICE_ID")
check "POST /users duplicate active email returns 409" 409 "$STATUS"

STATUS=$(create_user_api "$ADMIN_TOKEN" "Unknown" "Role" "curl.unknown.role.$RUN_ID@cadri.test" "unknown" "$GREEN_SERVICE_ID")
check "POST /users unknown role returns 403" 403 "$STATUS"

STATUS=$(create_user_api "$ADMIN_TOKEN" "Unknown" "Service" "curl.unknown.service.$RUN_ID@cadri.test" "agent" "$UNKNOWN_UUID")
check "POST /users unknown service returns 404" 404 "$STATUS"

STATUS=$(request -X POST "$BASE_URL/users" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{}')
check_one_of "POST /users empty body returns validation error" "$STATUS" 400 415

STATUS=$(request -X GET "$BASE_URL/users/$AGENT_ID" -H "Authorization: Bearer $ADMIN_TOKEN")
check "GET /users/<agent_id> as admin returns 200" 200 "$STATUS"

STATUS=$(request -X GET "$BASE_URL/users/$UNKNOWN_UUID" -H "Authorization: Bearer $ADMIN_TOKEN")
check "GET /users/<unknown_id> returns 404" 404 "$STATUS"

STATUS=$(request -X PATCH "$BASE_URL/users/$TEMP_AGENT_ID" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"first_name\":\"Updated\",\"last_name\":\"Agent\",\"email\":\"$TEMP_AGENT_EMAIL\",\"role\":\"agent\",\"service_id\":\"$ROADS_SERVICE_ID\"}")
check "PATCH /users/<id> as admin returns 200" 200 "$STATUS"

STATUS=$(request -X PATCH "$BASE_URL/users/$TEMP_AGENT_ID" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"first_name\":\"Duplicate\",\"last_name\":\"Agent\",\"email\":\"admin@cadri.local\",\"role\":\"agent\",\"service_id\":\"$GREEN_SERVICE_ID\"}")
check "PATCH /users/<id> duplicate email returns 409" 409 "$STATUS"

STATUS=$(request -X PATCH "$BASE_URL/users/$TEMP_AGENT_ID" \
    -H "Authorization: Bearer $RESPONSABLE_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"first_name\":\"Blocked\",\"last_name\":\"Agent\",\"email\":\"$TEMP_AGENT_EMAIL\",\"role\":\"agent\",\"service_id\":\"$GREEN_SERVICE_ID\"}")
check "PATCH /users/<id> as responsable returns 403" 403 "$STATUS"

STATUS=$(request -X PATCH "$BASE_URL/users/$TEMP_AGENT_ID" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{}')
check_one_of "PATCH /users/<id> empty body returns validation error" "$STATUS" 400 415

STATUS=$(request -X GET "$BASE_URL/users/assignable" -H "Authorization: Bearer $ADMIN_TOKEN")
check "GET /users/assignable as admin returns 200" 200 "$STATUS"

STATUS=$(request -X GET "$BASE_URL/users/assignable" -H "Authorization: Bearer $RESPONSABLE_TOKEN")
check "GET /users/assignable as responsable returns 200" 200 "$STATUS"

STATUS=$(request -X GET "$BASE_URL/users/assignable" -H "Authorization: Bearer $AGENT_TOKEN")
check "GET /users/assignable as agent returns 403" 403 "$STATUS"

# Activate one temp agent for login and mission assignment edge cases.
TEMP_ACTIVATION_TOKEN=$(get_activation_token_from_db "$TEMP_AGENT_EMAIL")
if [ -n "$TEMP_ACTIVATION_TOKEN" ]; then
    STATUS=$(request -X POST "$BASE_URL/auth/activate-account" \
        -H "Content-Type: application/json" \
        -d "{\"token\":\"$TEMP_ACTIVATION_TOKEN\",\"password\":\"TempStrongPass1\"}")
    check "POST /auth/activate-account valid token returns 200" 200 "$STATUS"

    STATUS=$(request -X POST "$BASE_URL/auth/activate-account" \
        -H "Content-Type: application/json" \
        -d "{\"token\":\"$TEMP_ACTIVATION_TOKEN\",\"password\":\"TempStrongPass1\"}")
    check "POST /auth/activate-account reused token returns 410" 410 "$STATUS"

    login_and_capture "$TEMP_AGENT_EMAIL" "TempStrongPass1" "$COOKIE_TEMP" TEMP_AGENT_TOKEN "Activated temp agent login returns 200"
else
    skip_check "Activation token tests" "docker compose backend setup not available"
fi

STATUS=$(request -X POST "$BASE_URL/auth/activate-account" \
    -H "Content-Type: application/json" \
    -d '{"token":"unknown-token","password":"StrongPass1"}')
check "POST /auth/activate-account unknown token returns 404" 404 "$STATUS"

STATUS=$(request -X POST "$BASE_URL/auth/activate-account" \
    -H "Content-Type: application/json" \
    -d '{"token":"","password":"StrongPass1"}')
check "POST /auth/activate-account missing token returns 400" 400 "$STATUS"

STATUS=$(request -X POST "$BASE_URL/auth/activate-account" \
    -H "Content-Type: application/json" \
    -d '{"token":"unknown-token","password":"short"}')
check "POST /auth/activate-account weak password returns 400" 400 "$STATUS"

section "Password reset and refresh-token routes"
STATUS=$(request -X POST "$BASE_URL/auth/forgot-password" \
    -H "Content-Type: application/json" \
    -d '{"email":"admin@cadri.local"}')
check "POST /auth/forgot-password active user returns 200" 200 "$STATUS"

STATUS=$(request -X POST "$BASE_URL/auth/forgot-password" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$TEMP_AGENT_EMAIL\"}")
check "POST /auth/forgot-password active temp user returns 200" 200 "$STATUS"

STATUS=$(request -X POST "$BASE_URL/auth/forgot-password" \
    -H "Content-Type: application/json" \
    -d '{"email":"inactive.or.unknown@cadri.local"}')
check "POST /auth/forgot-password unknown user returns 200 generic" 200 "$STATUS"

STATUS=$(request -X POST "$BASE_URL/auth/forgot-password" \
    -H "Content-Type: application/json" \
    -d '{"email":"invalid-email"}')
check "POST /auth/forgot-password invalid email returns 400" 400 "$STATUS"

RESET_USER_EMAIL="curl.reset.$RUN_ID@cadri.test"
STATUS=$(create_user_api "$ADMIN_TOKEN" "Reset" "User" "$RESET_USER_EMAIL" "agent" "$GREEN_SERVICE_ID")
check "POST /users creates reset test user returns 201" 201 "$STATUS"
RESET_ACTIVATION_TOKEN=$(get_activation_token_from_db "$RESET_USER_EMAIL")
if [ -n "$RESET_ACTIVATION_TOKEN" ]; then
    STATUS=$(request -X POST "$BASE_URL/auth/activate-account" \
        -H "Content-Type: application/json" \
        -d "{\"token\":\"$RESET_ACTIVATION_TOKEN\",\"password\":\"ResetOldPass1\"}")
    check "Activate reset test user returns 200" 200 "$STATUS"

    RESET_TOKEN=$(get_reset_token_from_db "$RESET_USER_EMAIL")
    STATUS=$(request -X POST "$BASE_URL/auth/reset-password" \
        -H "Content-Type: application/json" \
        -d "{\"token\":\"$RESET_TOKEN\",\"password\":\"ResetNewPass1\"}")
    check "POST /auth/reset-password valid token returns 200" 200 "$STATUS"

    STATUS=$(request -X POST "$BASE_URL/auth/reset-password" \
        -H "Content-Type: application/json" \
        -d "{\"token\":\"$RESET_TOKEN\",\"password\":\"ResetNewPass2\"}")
    check "POST /auth/reset-password reused token returns 410" 410 "$STATUS"
else
    skip_check "Reset-password valid/reused token tests" "docker compose backend setup not available"
fi

STATUS=$(request -X POST "$BASE_URL/auth/reset-password" \
    -H "Content-Type: application/json" \
    -d '{"token":"unknown-token","password":"ResetNewPass1"}')
check "POST /auth/reset-password unknown token returns 404" 404 "$STATUS"

STATUS=$(request -X POST "$BASE_URL/auth/reset-password" \
    -H "Content-Type: application/json" \
    -d '{"token":"unknown-token","password":"short"}')
check "POST /auth/reset-password weak password returns 400" 400 "$STATUS"

STATUS=$(request -X POST "$BASE_URL/auth/refresh")
check "POST /auth/refresh without cookie returns 401" 401 "$STATUS"

STATUS=$(request -X POST "$BASE_URL/auth/refresh" -b "$COOKIE_AGENT" -c "$COOKIE_AGENT")
check "POST /auth/refresh with cookie returns 200" 200 "$STATUS"
AGENT_TOKEN=$(json_get "access_token")

STATUS=$(request -X POST "$BASE_URL/auth/logout")
check "POST /auth/logout without cookie returns 401" 401 "$STATUS"

STATUS=$(request -X POST "$BASE_URL/auth/logout" -b "$COOKIE_RESPONSABLE")
check "POST /auth/logout with cookie returns 200" 200 "$STATUS"
# Login responsable again because logout revoked cookie/token session record only, access token remains valid until expiry but refresh cookie is cleared.
login_and_capture "responsable@cadri.local" "StrongPass1" "$COOKIE_RESPONSABLE" RESPONSABLE_TOKEN "Responsable re-login after logout returns 200"

CHANGE_EMAIL="curl.change.$RUN_ID@cadri.test"
STATUS=$(create_user_api "$ADMIN_TOKEN" "Change" "Password" "$CHANGE_EMAIL" "agent" "$GREEN_SERVICE_ID")
check "POST /users creates password-change user returns 201" 201 "$STATUS"
CHANGE_ACTIVATION_TOKEN=$(get_activation_token_from_db "$CHANGE_EMAIL")
if [ -n "$CHANGE_ACTIVATION_TOKEN" ]; then
    STATUS=$(request -X POST "$BASE_URL/auth/activate-account" \
        -H "Content-Type: application/json" \
        -d "{\"token\":\"$CHANGE_ACTIVATION_TOKEN\",\"password\":\"ChangeOldPass1\"}")
    check "Activate password-change user returns 200" 200 "$STATUS"
    login_and_capture "$CHANGE_EMAIL" "ChangeOldPass1" "$COOKIE_PREVIOUS" CHANGE_TOKEN "Password-change user login returns 200"

    STATUS=$(request -X PATCH "$BASE_URL/auth/change-password" \
        -H "Authorization: Bearer $CHANGE_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"current_password":"WrongPassword1","new_password":"ChangeNewPass1"}')
    check "PATCH /auth/change-password wrong current password returns 403" 403 "$STATUS"

    STATUS=$(request -X PATCH "$BASE_URL/auth/change-password" \
        -H "Authorization: Bearer $CHANGE_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"current_password":"ChangeOldPass1","new_password":"short"}')
    check "PATCH /auth/change-password weak new password returns 400" 400 "$STATUS"

    STATUS=$(request -X PATCH "$BASE_URL/auth/change-password" \
        -H "Authorization: Bearer $CHANGE_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"current_password":"ChangeOldPass1","new_password":"ChangeNewPass1"}')
    check "PATCH /auth/change-password valid returns 200" 200 "$STATUS"

    STATUS=$(request -X POST "$BASE_URL/auth/login" \
        -c "$COOKIE_PREVIOUS" \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"$CHANGE_EMAIL\",\"password\":\"ChangeNewPass1\"}")
    check "Login with changed password returns 200" 200 "$STATUS"
else
    skip_check "Change-password valid flow" "docker compose backend setup not available"
fi

section "Mission routes: creation, listing, filters, detail, update, delete"
MISSION_PAYLOAD=$(make_mission_payload "Curl mission main $RUN_ID" "medium" "$GREEN_SERVICE_ID" "$AGENT_ID")
STATUS=$(request -X POST "$BASE_URL/missions" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$MISSION_PAYLOAD")
check "POST /missions as admin returns 201" 201 "$STATUS"
MISSION_ID=$(json_get "mission.id")

MISSION_RESP_PAYLOAD=$(make_mission_payload "Curl mission responsable $RUN_ID" "low" "$GREEN_SERVICE_ID" "$AGENT_ID")
STATUS=$(request -X POST "$BASE_URL/missions" \
    -H "Authorization: Bearer $RESPONSABLE_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$MISSION_RESP_PAYLOAD")
check "POST /missions as responsable returns 201" 201 "$STATUS"
RESP_MISSION_ID=$(json_get "mission.id")

MISSION_AGENT_PAYLOAD=$(make_mission_payload "Curl blocked mission $RUN_ID" "medium" "$GREEN_SERVICE_ID" "$AGENT_ID")
STATUS=$(request -X POST "$BASE_URL/missions" \
    -H "Authorization: Bearer $AGENT_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$MISSION_AGENT_PAYLOAD")
check "POST /missions as agent returns 403" 403 "$STATUS"

STATUS=$(request -X POST "$BASE_URL/missions" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"title":"Missing fields"}')
check_one_of "POST /missions incomplete payload returns validation error" "$STATUS" 400 500

NO_SERVICE_PAYLOAD=$(make_mission_payload "Curl no service $RUN_ID" "medium" "$GREEN_SERVICE_ID" "$AGENT_ID")
NO_SERVICE_PAYLOAD=$(python3 -c 'import json,sys; d=json.loads(sys.stdin.read()); d["service_ids"]=[]; print(json.dumps(d))' <<< "$NO_SERVICE_PAYLOAD")
STATUS=$(request -X POST "$BASE_URL/missions" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$NO_SERVICE_PAYLOAD")
check "POST /missions without service returns 400" 400 "$STATUS"

BAD_DATE_PAYLOAD=$(make_mission_payload "Curl bad dates $RUN_ID" "medium" "$GREEN_SERVICE_ID" "$AGENT_ID" "2026-06-10T09:00:00" "2026-06-01T09:00:00")
STATUS=$(request -X POST "$BASE_URL/missions" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$BAD_DATE_PAYLOAD")
check "POST /missions invalid date order returns 400" 400 "$STATUS"

UNKNOWN_SERVICE_PAYLOAD=$(make_mission_payload "Curl unknown service $RUN_ID" "medium" "$UNKNOWN_UUID" "$AGENT_ID")
STATUS=$(request -X POST "$BASE_URL/missions" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$UNKNOWN_SERVICE_PAYLOAD")
check "POST /missions unknown service returns 404" 404 "$STATUS"

INACTIVE_ASSIGNED_PAYLOAD=$(make_mission_payload "Curl inactive assigned $RUN_ID" "medium" "$GREEN_SERVICE_ID" "$TEMP_AGENT_ID")
# TEMP_AGENT_ID was activated earlier if token setup worked; create a fresh inactive user for this edge case.
INACTIVE_EMAIL="curl.inactive.$RUN_ID@cadri.test"
STATUS=$(create_user_api "$ADMIN_TOKEN" "Inactive" "Assigned" "$INACTIVE_EMAIL" "agent" "$GREEN_SERVICE_ID")
check "POST /users creates inactive assigned test user returns 201" 201 "$STATUS"
INACTIVE_ID=$(json_get "user.id")
INACTIVE_ASSIGNED_PAYLOAD=$(make_mission_payload "Curl inactive assigned $RUN_ID" "medium" "$GREEN_SERVICE_ID" "$INACTIVE_ID")
STATUS=$(request -X POST "$BASE_URL/missions" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$INACTIVE_ASSIGNED_PAYLOAD")
check "POST /missions inactive assigned user returns 400" 400 "$STATUS"

ADMIN_ASSIGNED_PAYLOAD=$(make_mission_payload "Curl admin assigned $RUN_ID" "medium" "$GREEN_SERVICE_ID" "$ADMIN_ID")
STATUS=$(request -X POST "$BASE_URL/missions" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$ADMIN_ASSIGNED_PAYLOAD")
check "POST /missions admin assigned user returns 400" 400 "$STATUS"

STATUS=$(request -X GET "$BASE_URL/missions" -H "Authorization: Bearer $ADMIN_TOKEN")
check "GET /missions as admin returns 200" 200 "$STATUS"

STATUS=$(request -X GET "$BASE_URL/missions?my_missions_only=true" -H "Authorization: Bearer $AGENT_TOKEN")
check "GET /missions?my_missions_only=true as agent returns 200" 200 "$STATUS"

STATUS=$(request -X GET "$BASE_URL/missions?has_remark=false" -H "Authorization: Bearer $ADMIN_TOKEN")
check "GET /missions?has_remark=false returns 200" 200 "$STATUS"

STATUS=$(request -X GET "$BASE_URL/missions?has_remark=invalid" -H "Authorization: Bearer $ADMIN_TOKEN")
check "GET /missions?has_remark=invalid returns 400" 400 "$STATUS"

STATUS=$(request -X GET "$BASE_URL/missions?search=Curl" -H "Authorization: Bearer $ADMIN_TOKEN")
check "GET /missions?search=Curl returns 200" 200 "$STATUS"

STATUS=$(request -X GET "$BASE_URL/missions?status=to_do" -H "Authorization: Bearer $ADMIN_TOKEN")
check "GET /missions?status=to_do returns 200" 200 "$STATUS"

STATUS=$(request -X GET "$BASE_URL/missions?priority=medium" -H "Authorization: Bearer $ADMIN_TOKEN")
check "GET /missions?priority=medium returns 200" 200 "$STATUS"

STATUS=$(request -X GET "$BASE_URL/missions?service_id=$GREEN_SERVICE_ID" -H "Authorization: Bearer $ADMIN_TOKEN")
check "GET /missions?service_id=<id> returns 200" 200 "$STATUS"

STATUS=$(request -X GET "$BASE_URL/missions?start_date=2026-06-01T00:00:00&end_date=2026-06-30T23:59:59" -H "Authorization: Bearer $ADMIN_TOKEN")
check "GET /missions date filters return 200" 200 "$STATUS"

STATUS=$(request -X GET "$BASE_URL/missions?page=1&per_page=2" -H "Authorization: Bearer $ADMIN_TOKEN")
check "GET /missions pagination returns 200" 200 "$STATUS"

STATUS=$(request -X GET "$BASE_URL/missions/$MISSION_ID" -H "Authorization: Bearer $ADMIN_TOKEN")
check "GET /missions/<id> returns 200" 200 "$STATUS"

STATUS=$(request -X GET "$BASE_URL/missions/$UNKNOWN_UUID" -H "Authorization: Bearer $ADMIN_TOKEN")
check "GET /missions/<unknown_id> returns 404" 404 "$STATUS"

UPDATED_MISSION_PAYLOAD=$(make_mission_payload "Curl mission updated $RUN_ID" "high" "$ROADS_SERVICE_ID" "$AGENT_ID")
STATUS=$(request -X PATCH "$BASE_URL/missions/$MISSION_ID" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$UPDATED_MISSION_PAYLOAD")
check "PATCH /missions/<id> as admin returns 200" 200 "$STATUS"

RESP_UPDATE_PAYLOAD=$(make_mission_payload "Curl mission resp updated $RUN_ID" "medium" "$GREEN_SERVICE_ID" "$AGENT_ID")
STATUS=$(request -X PATCH "$BASE_URL/missions/$MISSION_ID" \
    -H "Authorization: Bearer $RESPONSABLE_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$RESP_UPDATE_PAYLOAD")
check "PATCH /missions/<id> as responsable returns 200" 200 "$STATUS"

STATUS=$(request -X PATCH "$BASE_URL/missions/$MISSION_ID" \
    -H "Authorization: Bearer $AGENT_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$UPDATED_MISSION_PAYLOAD")
check "PATCH /missions/<id> as agent returns 403" 403 "$STATUS"

BAD_UPDATE_PAYLOAD=$(make_mission_payload "Curl mission bad update $RUN_ID" "medium" "$GREEN_SERVICE_ID" "$AGENT_ID" "2026-06-10T09:00:00" "2026-06-01T09:00:00")
STATUS=$(request -X PATCH "$BASE_URL/missions/$MISSION_ID" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$BAD_UPDATE_PAYLOAD")
check "PATCH /missions/<id> invalid dates returns 400" 400 "$STATUS"

section "Mission action routes: status, duration, remark, validate, complete"
ACTION_PAYLOAD=$(make_mission_payload "Curl action mission $RUN_ID" "medium" "$GREEN_SERVICE_ID" "$AGENT_ID")
STATUS=$(request -X POST "$BASE_URL/missions" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$ACTION_PAYLOAD")
check "POST /missions creates action mission returns 201" 201 "$STATUS"
ACTION_MISSION_ID=$(json_get "mission.id")

STATUS=$(request -X PATCH "$BASE_URL/missions/$ACTION_MISSION_ID/status" \
    -H "Authorization: Bearer $AGENT_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"status":"in_progress"}')
check "PATCH /missions/<id>/status as assigned agent returns 200" 200 "$STATUS"

ADMIN_STATUS_PAYLOAD=$(make_mission_payload "Curl admin status mission $RUN_ID" "medium" "$GREEN_SERVICE_ID" "$AGENT_ID")
STATUS=$(request -X POST "$BASE_URL/missions" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$ADMIN_STATUS_PAYLOAD")
check "POST /missions creates admin status mission returns 201" 201 "$STATUS"
ADMIN_STATUS_MISSION_ID=$(json_get "mission.id")

STATUS=$(request -X PATCH "$BASE_URL/missions/$ADMIN_STATUS_MISSION_ID/status" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"status":"in_progress"}')
check "PATCH /missions/<id>/status as admin returns 200" 200 "$STATUS"

STATUS=$(request -X PATCH "$BASE_URL/missions/$ACTION_MISSION_ID/status" \
    -H "Authorization: Bearer $AGENT_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"status":"completed"}')
check "PATCH /missions/<id>/status invalid transition returns 400" 400 "$STATUS"

STATUS=$(request -X PATCH "$BASE_URL/missions/$ACTION_MISSION_ID/actual-duration" \
    -H "Authorization: Bearer $AGENT_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"actual_duration":2.5}')
check "PATCH /missions/<id>/actual-duration assigned agent returns 200" 200 "$STATUS"

STATUS=$(request -X PATCH "$BASE_URL/missions/$ACTION_MISSION_ID/actual-duration" \
    -H "Authorization: Bearer $AGENT_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"actual_duration":0}')
check "PATCH /missions/<id>/actual-duration zero returns 400" 400 "$STATUS"

if [ -n "${TEMP_AGENT_TOKEN:-}" ]; then
    STATUS=$(request -X PATCH "$BASE_URL/missions/$ACTION_MISSION_ID/actual-duration" \
        -H "Authorization: Bearer $TEMP_AGENT_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"actual_duration":1}')
    check "PATCH /missions/<id>/actual-duration non-assigned agent returns 403" 403 "$STATUS"
else
    skip_check "Non-assigned agent actual-duration edge" "temp active agent token unavailable"
fi

STATUS=$(request -X POST "$BASE_URL/missions/$ACTION_MISSION_ID/complete" \
    -H "Authorization: Bearer $AGENT_TOKEN")
check "POST /missions/<id>/complete assigned agent returns 200" 200 "$STATUS"

STATUS=$(request -X POST "$BASE_URL/missions/$ACTION_MISSION_ID/complete" \
    -H "Authorization: Bearer $AGENT_TOKEN")
check "POST /missions/<id>/complete already completed returns 409" 409 "$STATUS"

REMARK_PAYLOAD=$(make_mission_payload "Curl remark mission $RUN_ID" "high" "$GREEN_SERVICE_ID" "$AGENT_ID")
STATUS=$(request -X POST "$BASE_URL/missions" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$REMARK_PAYLOAD")
check "POST /missions creates remark mission returns 201" 201 "$STATUS"
REMARK_MISSION_ID=$(json_get "mission.id")

STATUS=$(request -X PATCH "$BASE_URL/missions/$REMARK_MISSION_ID/actual-duration" \
    -H "Authorization: Bearer $AGENT_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"actual_duration":4}')
check "PATCH /missions/<id>/actual-duration before remark returns 200" 200 "$STATUS"

STATUS=$(request -X POST "$BASE_URL/missions/$REMARK_MISSION_ID/remark" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"remark":"Admin should not add remark"}')
check "POST /missions/<id>/remark as admin returns 403" 403 "$STATUS"

STATUS=$(request -X POST "$BASE_URL/missions/$REMARK_MISSION_ID/remark" \
    -H "Authorization: Bearer $RESPONSABLE_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"remark":"Unassigned responsable should not add remark"}')
check "POST /missions/<id>/remark as unassigned responsable returns 403" 403 "$STATUS"

RESP_REMARK_PAYLOAD=$(make_mission_payload "Curl responsable remark mission $RUN_ID" "high" "$GREEN_SERVICE_ID" "$RESPONSABLE_ID")
STATUS=$(request -X POST "$BASE_URL/missions" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$RESP_REMARK_PAYLOAD")
check "POST /missions creates responsable remark mission returns 201" 201 "$STATUS"
RESP_REMARK_MISSION_ID=$(json_get "mission.id")

STATUS=$(request -X POST "$BASE_URL/missions/$RESP_REMARK_MISSION_ID/remark" \
    -H "Authorization: Bearer $RESPONSABLE_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"remark":"Assigned responsable remark"}')
check "POST /missions/<id>/remark as assigned responsable returns 200" 200 "$STATUS"

STATUS=$(request -X POST "$BASE_URL/missions/$REMARK_MISSION_ID/remark" \
    -H "Authorization: Bearer $AGENT_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"remark":"Need validation"}')
check "POST /missions/<id>/remark as assigned agent returns 200" 200 "$STATUS"

STATUS=$(request -X POST "$BASE_URL/missions/$REMARK_MISSION_ID/remark" \
    -H "Authorization: Bearer $AGENT_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"remark":"Second remark"}')
check "POST /missions/<id>/remark second remark returns 409" 409 "$STATUS"

STATUS=$(request -X POST "$BASE_URL/missions/$REMARK_MISSION_ID/complete" \
    -H "Authorization: Bearer $AGENT_TOKEN")
check "POST /missions/<id>/complete with unvalidated remark returns 409" 409 "$STATUS"

STATUS=$(request -X POST "$BASE_URL/missions/$REMARK_MISSION_ID/validate" \
    -H "Authorization: Bearer $AGENT_TOKEN")
check "POST /missions/<id>/validate as agent returns 403" 403 "$STATUS"

STATUS=$(request -X POST "$BASE_URL/missions/$REMARK_MISSION_ID/validate" \
    -H "Authorization: Bearer $ADMIN_TOKEN")
check "POST /missions/<id>/validate as admin returns 200" 200 "$STATUS"

NO_REMARK_PAYLOAD=$(make_mission_payload "Curl no remark validation $RUN_ID" "medium" "$GREEN_SERVICE_ID" "$AGENT_ID")
STATUS=$(request -X POST "$BASE_URL/missions" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$NO_REMARK_PAYLOAD")
check "POST /missions creates no-remark validation test returns 201" 201 "$STATUS"
NO_REMARK_MISSION_ID=$(json_get "mission.id")
STATUS=$(request -X POST "$BASE_URL/missions/$NO_REMARK_MISSION_ID/validate" \
    -H "Authorization: Bearer $ADMIN_TOKEN")
check "POST /missions/<id>/validate without remark returns 400" 400 "$STATUS"

NO_DURATION_PAYLOAD=$(make_mission_payload "Curl no duration complete $RUN_ID" "medium" "$GREEN_SERVICE_ID" "$AGENT_ID")
STATUS=$(request -X POST "$BASE_URL/missions" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$NO_DURATION_PAYLOAD")
check "POST /missions creates no-duration complete test returns 201" 201 "$STATUS"
NO_DURATION_MISSION_ID=$(json_get "mission.id")
STATUS=$(request -X POST "$BASE_URL/missions/$NO_DURATION_MISSION_ID/complete" \
    -H "Authorization: Bearer $AGENT_TOKEN")
check "POST /missions/<id>/complete without duration returns 400" 400 "$STATUS"

section "Mission deletion routes"
DELETE_PAYLOAD=$(make_mission_payload "Curl delete by admin $RUN_ID" "low" "$GREEN_SERVICE_ID" "$AGENT_ID")
STATUS=$(request -X POST "$BASE_URL/missions" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$DELETE_PAYLOAD")
check "POST /missions creates delete-admin mission returns 201" 201 "$STATUS"
DELETE_MISSION_ID=$(json_get "mission.id")

STATUS=$(request -X DELETE "$BASE_URL/missions/$DELETE_MISSION_ID" \
    -H "Authorization: Bearer $AGENT_TOKEN")
check "DELETE /missions/<id> as agent returns 403" 403 "$STATUS"

STATUS=$(request -X DELETE "$BASE_URL/missions/$DELETE_MISSION_ID" \
    -H "Authorization: Bearer $ADMIN_TOKEN")
check "DELETE /missions/<id> as admin returns 200" 200 "$STATUS"

RESP_DELETE_PAYLOAD=$(make_mission_payload "Curl delete by responsable $RUN_ID" "low" "$GREEN_SERVICE_ID" "$AGENT_ID")
STATUS=$(request -X POST "$BASE_URL/missions" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$RESP_DELETE_PAYLOAD")
check "POST /missions creates delete-responsable mission returns 201" 201 "$STATUS"
RESP_DELETE_MISSION_ID=$(json_get "mission.id")

STATUS=$(request -X DELETE "$BASE_URL/missions/$RESP_DELETE_MISSION_ID" \
    -H "Authorization: Bearer $RESPONSABLE_TOKEN")
check "DELETE /missions/<id> as responsable returns 200" 200 "$STATUS"

STATUS=$(request -X DELETE "$BASE_URL/missions/$UNKNOWN_UUID" \
    -H "Authorization: Bearer $ADMIN_TOKEN")
check "DELETE /missions/<unknown_id> returns 404" 404 "$STATUS"

section "User deletion cleanup route"
DELETE_USER_EMAIL="curl.delete.$RUN_ID@cadri.test"
STATUS=$(create_user_api "$ADMIN_TOKEN" "Delete" "User" "$DELETE_USER_EMAIL" "agent" "$GREEN_SERVICE_ID")
check "POST /users creates delete test user returns 201" 201 "$STATUS"
DELETE_USER_ID=$(json_get "user.id")

STATUS=$(request -X DELETE "$BASE_URL/users/$DELETE_USER_ID" \
    -H "Authorization: Bearer $RESPONSABLE_TOKEN")
check "DELETE /users/<id> as responsable returns 403" 403 "$STATUS"

STATUS=$(request -X DELETE "$BASE_URL/users/$DELETE_USER_ID" \
    -H "Authorization: Bearer $ADMIN_TOKEN")
check "DELETE /users/<id> as admin returns 200" 200 "$STATUS"

STATUS=$(request -X DELETE "$BASE_URL/users/$UNKNOWN_UUID" \
    -H "Authorization: Bearer $ADMIN_TOKEN")
check "DELETE /users/<unknown_id> returns 404" 404 "$STATUS"

section "Known manual-only / not-safe-for-cURL checks"
skip_check "Expired JWT access token" "would require waiting or custom token generation"
skip_check "Expired activation/reset/refresh token via HTTP only" "requires DB time manipulation; covered in pytest unit tests"
skip_check "Invalid UUID format" "current routes do not consistently convert ValueError/StatementError into AppError"
skip_check "CORS browser behavior" "must be verified in browser/front-end integration"
skip_check "Mailpit email content" "can be verified manually in Mailpit UI or API"
skip_check "Production cookie Secure flag" "depends on production env configuration"

section "Results"
echo "PASS: $PASS"
echo "FAIL: $FAIL"
echo "SKIP: $SKIP"

if [ "$FAIL" -eq 0 ]; then
    echo "All executable cURL checks passed."
    exit 0
fi

echo "Some cURL checks failed. Review the response bodies above."
exit 1
