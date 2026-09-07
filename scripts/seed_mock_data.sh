#!/usr/bin/env bash
# Loads a small synthetic dataset into Neo4j + Mongo for local dev/testing.
# Does NOT touch real production/dev data. Safe to run against a fresh,
# empty stack (docker compose up -d) instead of running bootstrap.sh with
# a real backup.json / centinela_db dump.
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yaml}"
ENV_FILE="${ENV_FILE:-.env}"
COMPOSE=(docker compose -f "$COMPOSE_FILE")

log() { printf '[mock-seed] %s\n' "$*"; }
fail() { printf '[mock-seed] error: %s\n' "$*" >&2; exit 1; }

env_value() {
  local key="$1" default="${2:-}" value="${!key:-}"
  if [[ -z "$value" && -f "$ENV_FILE" ]]; then
    value="$(grep -E "^${key}=" "$ENV_FILE" | tail -n 1 | cut -d= -f2- || true)"
  fi
  printf '%s' "${value:-$default}"
}

neo4j_user="$(env_value NEO4J_USERNAME neo4j)"
neo4j_password="$(env_value NEO4J_PASSWORD)"
[[ -n "$neo4j_password" ]] || fail "NEO4J_PASSWORD is required"

log "creating constraints"
"${COMPOSE[@]}" exec -T search-neo4j cypher-shell -u "$neo4j_user" -p "$neo4j_password" <<'CYPHER'
CREATE CONSTRAINT constraint_unique_Affiliation_scopus_id IF NOT EXISTS FOR (n:Affiliation) REQUIRE n.scopus_id IS UNIQUE;
CREATE CONSTRAINT constraint_unique_Article_scopus_id IF NOT EXISTS FOR (n:Article) REQUIRE n.scopus_id IS UNIQUE;
CREATE CONSTRAINT constraint_unique_Author_scopus_id IF NOT EXISTS FOR (n:Author) REQUIRE n.scopus_id IS UNIQUE;
CREATE CONSTRAINT constraint_unique_Topic_name IF NOT EXISTS FOR (n:Topic) REQUIRE n.name IS UNIQUE;
CYPHER

log "loading mock graph (3 affiliations, 5 authors, 4 articles, 4 topics)"
"${COMPOSE[@]}" exec -T search-neo4j cypher-shell -u "$neo4j_user" -p "$neo4j_password" <<'CYPHER'
MERGE (a1:Affiliation {scopus_id:"MOCK-AFF-1"}) SET a1.name="Universidad Mock A";
MERGE (a2:Affiliation {scopus_id:"MOCK-AFF-2"}) SET a2.name="Universidad Mock B";
MERGE (a3:Affiliation {scopus_id:"MOCK-AFF-3"}) SET a3.name="Instituto Mock C";

MERGE (:Topic {name:"machine learning"});
MERGE (:Topic {name:"graph databases"});
MERGE (:Topic {name:"bioinformatics"});
MERGE (:Topic {name:"nlp"});

MERGE (au1:Author {scopus_id:"MOCK-AUTH-1"}) SET au1.first_name="Ana", au1.last_name="Gomez", au1.auth_name="Gomez, Ana", au1.initials="A.", au1.citation_count=42, au1.current_affiliation="Universidad Mock A";
MERGE (au2:Author {scopus_id:"MOCK-AUTH-2"}) SET au2.first_name="Luis", au2.last_name="Perez", au2.auth_name="Perez, Luis", au2.initials="L.", au2.citation_count=17, au2.current_affiliation="Universidad Mock A";
MERGE (au3:Author {scopus_id:"MOCK-AUTH-3"}) SET au3.first_name="Maria", au3.last_name="Diaz", au3.auth_name="Diaz, Maria", au3.initials="M.", au3.citation_count=30, au3.current_affiliation="Universidad Mock B";
MERGE (au4:Author {scopus_id:"MOCK-AUTH-4"}) SET au4.first_name="Carlos", au4.last_name="Ruiz", au4.auth_name="Ruiz, Carlos", au4.initials="C.", au4.citation_count=5, au4.current_affiliation="Instituto Mock C";
MERGE (au5:Author {scopus_id:"MOCK-AUTH-5"}) SET au5.first_name="Sofia", au5.last_name="Lopez", au5.auth_name="Lopez, Sofia", au5.initials="S.", au5.citation_count=63, au5.current_affiliation="Universidad Mock B";

MERGE (ar1:Article {scopus_id:"MOCK-ART-1"}) SET ar1.title="Graph-based recommendation systems", ar1.abstract="mock abstract 1", ar1.doi="10.0000/mock1", ar1.publication_date="2023-01-15", ar1.author_count=2, ar1.affiliation_count=1, ar1.corpus="mock corpus text one";
MERGE (ar2:Article {scopus_id:"MOCK-ART-2"}) SET ar2.title="Applying NLP to biomedical text", ar2.abstract="mock abstract 2", ar2.doi="10.0000/mock2", ar2.publication_date="2023-06-02", ar2.author_count=2, ar2.affiliation_count=2, ar2.corpus="mock corpus text two";
MERGE (ar3:Article {scopus_id:"MOCK-ART-3"}) SET ar3.title="Scalable machine learning pipelines", ar3.abstract="mock abstract 3", ar3.doi="10.0000/mock3", ar3.publication_date="2024-02-20", ar3.author_count=3, ar3.affiliation_count=2, ar3.corpus="mock corpus text three";
MERGE (ar4:Article {scopus_id:"MOCK-ART-4"}) SET ar4.title="Bioinformatics network analysis", ar4.abstract="mock abstract 4", ar4.doi="10.0000/mock4", ar4.publication_date="2024-09-10", ar4.author_count=2, ar4.affiliation_count=1, ar4.corpus="mock corpus text four";

MATCH (au:Author {scopus_id:"MOCK-AUTH-1"}), (a:Affiliation {scopus_id:"MOCK-AFF-1"}) MERGE (au)-[:AFFILIATED_WITH]->(a);
MATCH (au:Author {scopus_id:"MOCK-AUTH-2"}), (a:Affiliation {scopus_id:"MOCK-AFF-1"}) MERGE (au)-[:AFFILIATED_WITH]->(a);
MATCH (au:Author {scopus_id:"MOCK-AUTH-3"}), (a:Affiliation {scopus_id:"MOCK-AFF-2"}) MERGE (au)-[:AFFILIATED_WITH]->(a);
MATCH (au:Author {scopus_id:"MOCK-AUTH-4"}), (a:Affiliation {scopus_id:"MOCK-AFF-3"}) MERGE (au)-[:AFFILIATED_WITH]->(a);
MATCH (au:Author {scopus_id:"MOCK-AUTH-5"}), (a:Affiliation {scopus_id:"MOCK-AFF-2"}) MERGE (au)-[:AFFILIATED_WITH]->(a);

MATCH (au:Author {scopus_id:"MOCK-AUTH-1"}), (ar:Article {scopus_id:"MOCK-ART-1"}) MERGE (au)-[:WROTE {order:1}]->(ar);
MATCH (au:Author {scopus_id:"MOCK-AUTH-2"}), (ar:Article {scopus_id:"MOCK-ART-1"}) MERGE (au)-[:WROTE {order:2}]->(ar);
MATCH (au:Author {scopus_id:"MOCK-AUTH-3"}), (ar:Article {scopus_id:"MOCK-ART-2"}) MERGE (au)-[:WROTE {order:1}]->(ar);
MATCH (au:Author {scopus_id:"MOCK-AUTH-4"}), (ar:Article {scopus_id:"MOCK-ART-2"}) MERGE (au)-[:WROTE {order:2}]->(ar);
MATCH (au:Author {scopus_id:"MOCK-AUTH-1"}), (ar:Article {scopus_id:"MOCK-ART-3"}) MERGE (au)-[:WROTE {order:1}]->(ar);
MATCH (au:Author {scopus_id:"MOCK-AUTH-3"}), (ar:Article {scopus_id:"MOCK-ART-3"}) MERGE (au)-[:WROTE {order:2}]->(ar);
MATCH (au:Author {scopus_id:"MOCK-AUTH-5"}), (ar:Article {scopus_id:"MOCK-ART-3"}) MERGE (au)-[:WROTE {order:3}]->(ar);
MATCH (au:Author {scopus_id:"MOCK-AUTH-4"}), (ar:Article {scopus_id:"MOCK-ART-4"}) MERGE (au)-[:WROTE {order:1}]->(ar);
MATCH (au:Author {scopus_id:"MOCK-AUTH-5"}), (ar:Article {scopus_id:"MOCK-ART-4"}) MERGE (au)-[:WROTE {order:2}]->(ar);

MATCH (ar:Article {scopus_id:"MOCK-ART-1"}), (a:Affiliation {scopus_id:"MOCK-AFF-1"}) MERGE (ar)-[:BELONGS_TO]->(a);
MATCH (ar:Article {scopus_id:"MOCK-ART-2"}), (a:Affiliation {scopus_id:"MOCK-AFF-2"}) MERGE (ar)-[:BELONGS_TO]->(a);
MATCH (ar:Article {scopus_id:"MOCK-ART-3"}), (a:Affiliation {scopus_id:"MOCK-AFF-1"}) MERGE (ar)-[:BELONGS_TO]->(a);
MATCH (ar:Article {scopus_id:"MOCK-ART-4"}), (a:Affiliation {scopus_id:"MOCK-AFF-3"}) MERGE (ar)-[:BELONGS_TO]->(a);

MATCH (ar:Article {scopus_id:"MOCK-ART-1"}), (t:Topic {name:"graph databases"}) MERGE (ar)-[:USES]->(t);
MATCH (ar:Article {scopus_id:"MOCK-ART-1"}), (t:Topic {name:"machine learning"}) MERGE (ar)-[:USES]->(t);
MATCH (ar:Article {scopus_id:"MOCK-ART-2"}), (t:Topic {name:"nlp"}) MERGE (ar)-[:USES]->(t);
MATCH (ar:Article {scopus_id:"MOCK-ART-2"}), (t:Topic {name:"bioinformatics"}) MERGE (ar)-[:USES]->(t);
MATCH (ar:Article {scopus_id:"MOCK-ART-3"}), (t:Topic {name:"machine learning"}) MERGE (ar)-[:USES]->(t);
MATCH (ar:Article {scopus_id:"MOCK-ART-4"}), (t:Topic {name:"bioinformatics"}) MERGE (ar)-[:USES]->(t);

MATCH (au:Author {scopus_id:"MOCK-AUTH-1"}), (t:Topic {name:"machine learning"}) MERGE (au)-[:EXPERT_IN]->(t);
MATCH (au:Author {scopus_id:"MOCK-AUTH-1"}), (t:Topic {name:"graph databases"}) MERGE (au)-[:EXPERT_IN]->(t);
MATCH (au:Author {scopus_id:"MOCK-AUTH-3"}), (t:Topic {name:"nlp"}) MERGE (au)-[:EXPERT_IN]->(t);
MATCH (au:Author {scopus_id:"MOCK-AUTH-4"}), (t:Topic {name:"bioinformatics"}) MERGE (au)-[:EXPERT_IN]->(t);
MATCH (au:Author {scopus_id:"MOCK-AUTH-5"}), (t:Topic {name:"machine learning"}) MERGE (au)-[:EXPERT_IN]->(t);

MATCH (a:Author {scopus_id:"MOCK-AUTH-1"}), (b:Author {scopus_id:"MOCK-AUTH-2"}) MERGE (a)-[:CO_AUTHORED {collab_strength:1.0, shared_pubs:1}]->(b);
MATCH (a:Author {scopus_id:"MOCK-AUTH-1"}), (b:Author {scopus_id:"MOCK-AUTH-3"}) MERGE (a)-[:CO_AUTHORED {collab_strength:1.0, shared_pubs:1}]->(b);
MATCH (a:Author {scopus_id:"MOCK-AUTH-1"}), (b:Author {scopus_id:"MOCK-AUTH-5"}) MERGE (a)-[:CO_AUTHORED {collab_strength:1.0, shared_pubs:1}]->(b);
MATCH (a:Author {scopus_id:"MOCK-AUTH-3"}), (b:Author {scopus_id:"MOCK-AUTH-5"}) MERGE (a)-[:CO_AUTHORED {collab_strength:1.0, shared_pubs:1}]->(b);
MATCH (a:Author {scopus_id:"MOCK-AUTH-4"}), (b:Author {scopus_id:"MOCK-AUTH-5"}) MERGE (a)-[:CO_AUTHORED {collab_strength:1.0, shared_pubs:1}]->(b);
CYPHER

log "syncing Mongo dashboards from mock graph (reuses upsert_mongo ETL, no hand-crafted bson needed)"
"${COMPOSE[@]}" exec -T search-service python manage.py upsert_mongo

log "mock data loaded"
