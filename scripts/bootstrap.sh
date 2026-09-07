#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yaml}"
ENV_FILE="${ENV_FILE:-.env}"
SEED_REMOTE="${SEED_REMOTE:-}"
SEED_DIR="${SEED_DIR:-$ROOT_DIR/seed_data}"
COMPOSE=(docker compose -f "$COMPOSE_FILE")

log() {
  printf '[bootstrap] %s\n' "$*"
}

fail() {
  printf '[bootstrap] error: %s\n' "$*" >&2
  exit 1
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || fail "missing required command: $1"
}

env_value() {
  local key="$1"
  local default="${2:-}"
  local value="${!key:-}"

  if [[ -z "$value" && -f "$ENV_FILE" ]]; then
    value="$(grep -E "^${key}=" "$ENV_FILE" | tail -n 1 | cut -d= -f2- || true)"
  fi

  printf '%s' "${value:-$default}"
}

compose_exec() {
  "${COMPOSE[@]}" exec -T "$@"
}

container_id() {
  "${COMPOSE[@]}" ps -q "$1"
}

wait_for() {
  local label="$1"
  local retries="${2:-60}"
  shift 2

  log "waiting for $label"
  for _ in $(seq 1 "$retries"); do
    if "$@" >/dev/null 2>&1; then
      log "$label is ready"
      return 0
    fi
    sleep 5
  done

  fail "$label did not become ready"
}

prepare_local_files() {
  require_command git
  require_command docker

  if ! git lfs version >/dev/null 2>&1; then
    fail "git-lfs is required. Install it and run: git lfs install"
  fi

  log "pulling Git LFS assets"
  git lfs pull

  log "preparing local log directory"
  mkdir -p "$ROOT_DIR/centinela_logs" "$SEED_DIR"
  chmod -R a+rwX "$ROOT_DIR/centinela_logs"
}

seed_data_ready() {
  [[ -f "$SEED_DIR/backup.json" && -d "$SEED_DIR/centinela_db" ]]
}

extract_mongo_archive() {
  if [[ -f "$SEED_DIR/centinela_db.zip" && ! -d "$SEED_DIR/centinela_db" ]]; then
    require_command unzip
    log "extracting Mongo seed archive"
    unzip -o "$SEED_DIR/centinela_db.zip" -d "$SEED_DIR"
  fi
}

missing_seed_data_message() {
  cat >&2 <<EOF
[bootstrap] error: missing Search seed data.
[bootstrap] expected:
[bootstrap]   $SEED_DIR/backup.json
[bootstrap]   $SEED_DIR/centinela_db/
[bootstrap]
[bootstrap] Download the Neo4j backup and Mongo dump from the agreed project source,
[bootstrap] place them in the paths above, and rerun this script.
[bootstrap] If you have a configured rclone remote, you can also run:
[bootstrap]   SEED_REMOTE=<remote>:<path> $0
EOF
  exit 1
}

fetch_seed_data() {
  extract_mongo_archive

  if seed_data_ready; then
    log "using local seed data from $SEED_DIR"
    return
  fi

  if [[ -n "$SEED_REMOTE" ]]; then
    require_command rclone
    log "copying seed data from $SEED_REMOTE"
    rclone copy "$SEED_REMOTE" "$SEED_DIR" -P
    extract_mongo_archive
  fi

  seed_data_ready || missing_seed_data_message
}

start_stack() {
  log "starting compose stack"
  "${COMPOSE[@]}" up -d --build
}

wait_for_databases() {
  local neo4j_user neo4j_password mongo_user mongo_password
  neo4j_user="$(env_value NEO4J_USERNAME neo4j)"
  neo4j_password="$(env_value NEO4J_PASSWORD)"
  mongo_user="$(env_value MONGO_DB_USERNAME)"
  mongo_password="$(env_value MONGO_DB_PASSWORD)"

  [[ -n "$neo4j_password" ]] || fail "NEO4J_PASSWORD is required"
  [[ -n "$mongo_user" ]] || fail "MONGO_DB_USERNAME is required"
  [[ -n "$mongo_password" ]] || fail "MONGO_DB_PASSWORD is required"

  wait_for "Neo4j" 60 compose_exec search-neo4j cypher-shell -u "$neo4j_user" -p "$neo4j_password" "RETURN 1"
  wait_for "MongoDB" 60 compose_exec search-mongo mongosh --quiet --username "$mongo_user" --password "$mongo_password" --authenticationDatabase admin --eval 'db.runCommand({ ping: 1 }).ok'
}

load_neo4j() {
  local neo4j_container neo4j_user neo4j_password
  neo4j_container="$(container_id search-neo4j)"
  neo4j_user="$(env_value NEO4J_USERNAME neo4j)"
  neo4j_password="$(env_value NEO4J_PASSWORD)"

  [[ -n "$neo4j_container" ]] || fail "Neo4j container was not found"

  log "copying Neo4j backup"
  docker cp "$SEED_DIR/backup.json" "$neo4j_container:/var/lib/neo4j/import/backup.json"

  log "creating Neo4j constraints"
  compose_exec search-neo4j cypher-shell -u "$neo4j_user" -p "$neo4j_password" <<'CYPHER'
CREATE CONSTRAINT constraint_unique_Affiliation_name IF NOT EXISTS FOR (n:Affiliation) REQUIRE n.name IS UNIQUE;
CREATE CONSTRAINT constraint_unique_Affiliation_pk IF NOT EXISTS FOR (n:Affiliation) REQUIRE n.pk IS UNIQUE;
CREATE CONSTRAINT constraint_unique_Affiliation_scopus_id IF NOT EXISTS FOR (n:Affiliation) REQUIRE n.scopus_id IS UNIQUE;
CREATE CONSTRAINT constraint_unique_Article_pk IF NOT EXISTS FOR (n:Article) REQUIRE n.pk IS UNIQUE;
CREATE CONSTRAINT constraint_unique_Article_scopus_id IF NOT EXISTS FOR (n:Article) REQUIRE n.scopus_id IS UNIQUE;
CREATE CONSTRAINT constraint_unique_Author_pk IF NOT EXISTS FOR (n:Author) REQUIRE n.pk IS UNIQUE;
CREATE CONSTRAINT constraint_unique_Author_scopus_id IF NOT EXISTS FOR (n:Author) REQUIRE n.scopus_id IS UNIQUE;
CREATE CONSTRAINT constraint_unique_CursorReference_cursor IF NOT EXISTS FOR (n:CursorReference) REQUIRE n.cursor IS UNIQUE;
CREATE CONSTRAINT constraint_unique_CursorReference_reference IF NOT EXISTS FOR (n:CursorReference) REQUIRE n.reference IS UNIQUE;
CREATE CONSTRAINT constraint_unique_Topic_name IF NOT EXISTS FOR (n:Topic) REQUIRE n.name IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (n:Article) REQUIRE n.neo4jImportId IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (n:Affiliation) REQUIRE n.neo4jImportId IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (n:Topic) REQUIRE n.neo4jImportId IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (n:Author) REQUIRE n.neo4jImportId IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (n:CursorReference) REQUIRE n.neo4jImportId IS UNIQUE;
CYPHER

  log "importing Neo4j data"
  compose_exec search-neo4j cypher-shell -u "$neo4j_user" -p "$neo4j_password" <<'CYPHER'
CALL apoc.import.json("backup.json", {
  createMissingNodes: true,
  batchSize: 10000
});
CYPHER
}

restore_mongo() {
  local mongo_container mongo_user mongo_password mongo_db
  mongo_container="$(container_id search-mongo)"
  mongo_user="$(env_value MONGO_DB_USERNAME)"
  mongo_password="$(env_value MONGO_DB_PASSWORD)"
  mongo_db="$(env_value MONGO_DB_NAME centinela)"

  [[ -n "$mongo_container" ]] || fail "MongoDB container was not found"

  log "copying Mongo dump"
  docker cp "$SEED_DIR/centinela_db" "$mongo_container:/tmp/centinela_db"

  log "restoring Mongo dump"
  compose_exec search-mongo mongorestore \
    --host localhost \
    --port 27017 \
    --username "$mongo_user" \
    --password "$mongo_password" \
    --authenticationDatabase admin \
    --db "$mongo_db" \
    /tmp/centinela_db
}

finish_django_setup() {
  log "running Django setup"
  compose_exec search-service python manage.py install_labels
}

main() {
  prepare_local_files
  fetch_seed_data
  start_stack
  wait_for_databases
  load_neo4j
  restore_mongo
  finish_django_setup
  log "bootstrap completed"
}

main "$@"
