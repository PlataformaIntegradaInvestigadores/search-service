# Centinela — search-service

Servicio Django que implementa el motor de búsqueda de la plataforma: grafo de autores/afiliaciones/artículos/coautorías sobre Neo4j, integración con la API de Scopus, procesamiento de texto (TF-IDF, embeddings) y dashboards analíticos. Incluye además una búsqueda semántica basada en LLM (`llm-search`, stack SciBERT + KeyBERT + BM25) independiente del motor por grafo.

Parte del org multi-repo `PlataformaIntegradaInvestigadores`. Se comunica con el resto de la plataforma a través de `gateway-service` (nginx), en la red Docker `centinela-net`. Es el único backend que usa dos bases de datos a la vez (Neo4j + MongoDB).

## Stack

- Django 5 + Django REST Framework, servido con Gunicorn
- Neo4j (`neomodel`) — grafo de autores, artículos, afiliaciones, coautorías, tópicos
- MongoDB (`mongoengine`) — datos de Scopus y dashboards
- SciBERT / KeyBERT / `sentence-transformers` / `rank-bm25` / spaCy — búsqueda semántica (`llm-search`)
- Scopus API (integración vía `scopus_integration`)

## Estructura del proyecto

```
apps/
  authentication/        # login/logout
  text_processing/        # limpieza de texto, TF-IDF, vectorización
  scopus_integration/      # cliente e ingesta de la API de Scopus
  search_engine/            # dominio principal: autores, artículos, afiliaciones,
                              # coautorías, tópicos, búsqueda semántica (llm-search)
  dashboards/                # endpoints analíticos (países, provincias, fairness)

resources/                   # modelos pre-entrenados y corpus (SciBERT, KeyBERT, TF-IDF)
```

Cada app en `apps/<app>/` sigue arquitectura por capas (Clean/Hexagonal):

```
apps/<app>/
  domain/
    entities/
    repositories/
  application/
    use_cases/
    services/
  infrastructure/
    api/v1/
      views/
      serializers/
      urls/
    migrations/
  tests/                      # test_*.py (pytest-django)
```

## Requisitos previos

- Docker y Docker Compose
- Red Docker externa `centinela-net`

## Levantar en local

### Con Docker (recomendado)

```bash
docker compose -f docker-compose.yaml up -d --build
```

Levanta `search-service` (Gunicorn, puerto `8001`), `search-neo4j` (puertos `7474`/`7687`, con plugins APOC y Graph Data Science) y `search-mongo` (puerto `27017`).

### Cargar datos (Neo4j + Mongo)

El stack levanta con las DBs vacías. Con el stack ya arriba y healthy, elegí una opción:

- **Si tenés `seed_data/backup.json` y `seed_data/centinela_db/`** (dump real, se consigue con el equipo — no está en el repo): corré `bash scripts/bootstrap.sh`. Restaura ambas DBs con data real.
- **Si NO tenés esos archivos**: corré `bash scripts/seed_mock_data.sh`. Genera un grafo sintético chico (autores, artículos, afiliaciones, tópicos) directo en Neo4j y sincroniza Mongo con el mismo comando `upsert_mongo` que usa el ETL real. Sirve para desarrollar/probar sin depender de data real ni de acceso al servidor de dev.

Ninguno de los dos corre solo — hay que ejecutarlos a mano después de `docker compose up`.

### Sin Docker (desarrollo)

```bash
python -m venv .venv && .venv/Scripts/activate  # o source .venv/bin/activate en Linux/Mac
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Requiere una instancia de Neo4j y otra de MongoDB accesibles (ver variables de entorno).

## Variables de entorno

Ver `.env.example`. Variables clave:

| Variable | Descripción |
|---|---|
| `DJANGO_SECRET_KEY` | Clave de Django |
| `NEO4J_HOST` / `NEO4J_USERNAME` / `NEO4J_PASSWORD` / `NEO4J_PORT` | Conexión a Neo4j |
| `MONGO_DB_HOST` / `MONGO_DB_NAME` / `MONGO_DB_USERNAME` / `MONGO_DB_PASSWORD` / `MONGO_DB_PORT` | Conexión a MongoDB |
| `X_ELS_APIKEY` / `X_ELS_INSTTOKEN` / `X_ELS_AUTHTOKEN` | Credenciales de la API de Scopus |
| `ADMIN_CENTINELA` / `PASSWORD_CENTINELA` | Superusuario inicial |

## Documentación (Swagger)

Schema OpenAPI: `GET /api-se/schema/?format=json`. UI local propia en `/api-se/schema/swagger-ui/` (y Redoc en `/api-se/schema/redoc/`), además disponible centralizada en el hub del `gateway-service`: `/api/docs/v1/search`. `SPECTACULAR_SETTINGS` recorta el prefijo interno `/api-se` y declara `servers: [{"url": "/api/search"}]` para que "Try it out" funcione a través del gateway.

## Tests

```bash
pytest apps/ --cov=apps --cov-report=term
```

Cobertura mínima exigida en CI: **90%** (`--cov-fail-under=90` en `.github/workflows/ci.yml`). Los tests de cada app viven en `apps/<app>/tests/test_*.py`.

## CI/CD

GitHub Actions (`.github/workflows/ci.yml`): tests unitarios (Neo4j + MongoDB) → tests de integración → build de imagen Docker → deploy automático a staging (`develop` branch, runner self-hosted `ticcd`), con healthcheck contra `/api-se/v1/health/` y rollback automático si falla.

## Convenciones

- Branches: `feature/*` → `develop`, `hotfix/*` → `main`.
- Commits: [Conventional Commits](https://www.conventionalcommits.org/), inglés, con el *por qué* en el cuerpo.
