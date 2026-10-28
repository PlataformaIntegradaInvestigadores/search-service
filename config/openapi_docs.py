"""Documentacion OpenAPI (Swagger) de search-service.

Solo describe el contrato que ya existe; no cambia el comportamiento de las vistas.
Los textos viven aqui, en un unico lugar, y se aplican con dos hooks de
drf-spectacular:

* ``exclude_unused_routes`` (preprocesado) quita del documento las rutas CRUD que
  heredan los ``ModelViewSet`` del dashboard y que no tienen queryset ni serializer.
* ``organize_schema`` (postprocesado) agrupa cada operacion en un tag, escribe su
  resumen y descripcion, corrige los parametros y las respuestas (los dashboards no
  paginan ni usan los esquemas que autogeneraba spectacular) y limpia los esquemas
  que ya no se usan.
"""

import json
import re

# --------------------------------------------------------------------- tags
T_SEARCH = "Búsqueda"
T_ART = "Artículos"
T_AUT = "Autores"
T_AFF = "Afiliaciones"
T_TOP = "Tópicos"
T_DNAT = "Dashboard: producción nacional"
T_DTOP = "Dashboard: tópicos"
T_DAFF = "Dashboard: afiliaciones"
T_DAUT = "Dashboard: autores"
T_DPRO = "Dashboard: provincias"
T_DEQ = "Dashboard: equidad"
T_ADM = "Administración: datos"
T_STA = "Administración: estado"
T_LOGIN = "Autenticación"
T_TXT = "Procesamiento de texto"

TAGS = [
    {
        "name": T_SEARCH,
        "description": "Búsqueda semántica de artículos con un modelo de lenguaje y "
        "generación de preguntas y respuestas a partir de los resultados.",
    },
    {
        "name": T_ART,
        "description": "Consulta del corpus de artículos científicos: listado, "
        "detalle, artículos por autor y artículos más relevantes para un tópico.",
    },
    {
        "name": T_AUT,
        "description": "Consulta de autores: listado, búsqueda por nombre, detalle, "
        "autores más relevantes para un tópico y red de coautores.",
    },
    {
        "name": T_AFF,
        "description": "Consulta de afiliaciones (instituciones) del corpus.",
    },
    {"name": T_TOP, "description": "Tópicos detectados en el corpus."},
    {
        "name": T_DNAT,
        "description": "Totales y evolución anual de la producción científica del "
        "país (autores, artículos, afiliaciones y tópicos).",
    },
    {
        "name": T_DTOP,
        "description": "Tópicos del país: ranking, evolución por año, resumen y "
        "afiliaciones que más publican en cada tópico.",
    },
    {
        "name": T_DAFF,
        "description": "Producción por afiliación: ranking, evolución anual, tópicos "
        "y matriz de concentración (heatmap).",
    },
    {
        "name": T_DAUT,
        "description": "Producción de un autor: años de publicación y tópicos.",
    },
    {
        "name": T_DPRO,
        "description": "Producción científica por provincia, anual y acumulada.",
    },
    {
        "name": T_DEQ,
        "description": "Resultados de los experimentos de equidad (fairness) del "
        "sistema de recomendación.",
    },
    {
        "name": T_ADM,
        "description": "Operaciones que modifican datos o disparan procesos largos: "
        "ETL, repoblado del datalake, corpus y modelo TF-IDF, ingesta de Scopus. "
        "Son de uso administrativo.",
    },
    {
        "name": T_STA,
        "description": "Diagnóstico de solo lectura: estado de la sincronización, "
        "comparadores con Scopus, modelo y logs.",
    },
    {
        "name": T_LOGIN,
        "description": "Credenciales del panel de administración.",
    },
    {
        "name": T_TXT,
        "description": "Vectorización de texto (traducción, limpieza y embedding).",
    },
]

INFO_DESCRIPTION = """
API del **motor de búsqueda de Centinela** y de los **dashboards** de producción
científica. Trabaja sobre el corpus de artículos de Scopus almacenado en dos bases:

* **Neo4j** (fuente de verdad): artículos, autores, afiliaciones, tópicos y sus
  relaciones. Alimenta la búsqueda y las consultas de detalle.
* **MongoDB** (agregados): totales por año, acumulados, rankings y matrices ya
  calculados. Alimenta los dashboards.

### Cómo está organizada

| Grupo | Para qué sirve |
|---|---|
| Búsqueda, Artículos, Autores, Afiliaciones, Tópicos | Consultar el corpus |
| Dashboard: … | Datos agregados para las gráficas (país, tópicos, afiliaciones, autores, provincias, equidad) |
| Administración: datos / estado | ETL, repoblado, corpus y modelo, diagnóstico |
| Autenticación, Procesamiento de texto | Apoyo |

### Convenciones

* Detrás del gateway todas las rutas cuelgan de `/api/search/v1`.
* Los endpoints de los dashboards **no paginan**: devuelven la lista completa. Los
  de consulta del corpus paginan con `page` y `page_size`.
* Los errores devuelven un objeto con la clave `error` (o `message` / `detail` en
  algunos endpoints).
* Casi todas las rutas son públicas. Solo el repoblado del datalake
  (`/dashboard/populate`) y el vaciado de la base (`DELETE /articles/{id}/`) piden
  las credenciales de administrador por HTTP Basic.
* Para búsquedas con validación de contrato y formato de error uniforme, el
  frontend usa la API intermedia `/api/search/v2`.
"""

# --------------------------------------------------------------- parametros
YEAR_NOTE = "Año de cuatro cifras, por ejemplo `2023`."
PARAMS = {
    "year": YEAR_NOTE,
    "topic": "Nombre exacto del tópico, tal como aparece en el corpus.",
    "query": "Texto a buscar.",
    "name": "Nombre completo de la afiliación.",
    "number_top": "Cantidad de tópicos a devolver, de mayor a menor número de "
    "artículos.",
    "top_affiliations": "Cuántas afiliaciones incluir en la matriz (por defecto 10).",
    "top_topics": "Cuántos tópicos incluir en la matriz (por defecto 12).",
    "page": "Número de página, desde 1.",
    "page_size": "Resultados por página (por defecto 10).",
    "author_id": "ID del autor en Scopus.",
    "lines_per_page": "Líneas de log por página (por defecto 10).",
    "level": "Nivel de log a filtrar, por ejemplo `ERROR` o `INFO`.",
    "start_date": "Fecha inicial del filtro de logs.",
    "end_date": "Fecha final del filtro de logs.",
    "keyword": "Texto que debe contener la línea de log.",
}
PARAMS_BY_PATH = {
    ("/dashboard/affiliation/", "scopus_id"): "ID de la afiliación en Scopus.",
    ("/dashboard/author/", "scopus_id"): "ID del autor en Scopus.",
    ("/affiliations/", "id"): "ID de la afiliación en Scopus.",
    ("/authors/", "id"): "ID del autor en Scopus.",
    ("/articles/", "id"): "ID del artículo en Scopus.",
    ("/coauthors/", "id"): "ID del autor en Scopus.",
    ("/scopus-integration/", "year"): "Año a ingestar (`AAAA`). Sin él se procesa "
    "todo el rango.",
    ("/dashboard/affiliation/get_year_range/", "year"): "Último año del rango; se "
    "devuelven los años desde 2000 hasta este.",
    ("/dashboard/affiliation/get_topics_heatmap/", "year"): "Año de la matriz.",
    ("/dashboard/country/get_range_info/", "year"): "Último año del rango; se "
    "devuelven los años desde 2000 hasta este.",
    ("/dashboard/country/get_topics_range_year/", "year"): "Último año del rango; se "
    "devuelven los años desde 2000 hasta este.",
}

# ---------------------------------------------------------- esquemas nuevos
S = "string"
I = "integer"  # noqa: E741


def _obj(props, required=None, desc=None):
    schema = {
        "type": "object",
        "properties": {k: dict(v) for k, v in props.items()},
    }
    schema["required"] = required if required is not None else list(props)
    if desc:
        schema["description"] = desc
    return schema


def _t(type_, desc, **extra):
    return {"type": type_, "description": desc, **extra}


EXTRA_SCHEMAS = {
    "WordItem": _obj(
        {
            "text": _t(S, "Etiqueta: nombre del tópico o de la afiliación."),
            "size": _t(
                I, "Número de artículos asociados; define el tamaño en la nube."
            ),
        },
        desc="Elemento de ranking o nube de palabras.",
    ),
    "CountryTotals": _obj(
        {
            "author": _t(I, "Total de autores."),
            "article": _t(I, "Total de artículos."),
            "affiliation": _t(I, "Total de afiliaciones."),
            "topic": _t(I, "Total de tópicos."),
        },
        desc="Totales de producción científica del país.",
    ),
    "CountryYearTotals": _obj(
        {
            "year": _t(I, "Año."),
            "author": _t(I, "Autores con producción ese año."),
            "article": _t(I, "Artículos publicados ese año."),
            "affiliation": _t(I, "Afiliaciones con producción ese año."),
            "topic": _t(I, "Tópicos trabajados ese año."),
        },
        desc="Totales del país en un año.",
    ),
    "YearItem": _obj({"year": _t(I, "Año con datos.")}, desc="Año disponible."),
    "TopicSummary": _obj(
        {
            "articles": _t(I, "Artículos del tópico."),
            "affiliations": _t(I, "Afiliaciones que publican sobre el tópico."),
        },
        desc="Resumen de un tópico.",
    ),
    "ArticlesTopicsCount": _obj(
        {
            "articles": _t(I, "Cantidad de artículos."),
            "topics": _t(I, "Cantidad de tópicos."),
        },
        desc="Artículos y tópicos de una afiliación.",
    ),
    "AffiliationRankingItem": _obj(
        {
            "scopus_id": _t(S, "ID de la afiliación en Scopus."),
            "name": _t(S, "Nombre de la afiliación."),
            "total_articles": _t(I, "Artículos de la afiliación."),
        },
        desc="Afiliación con su producción.",
    ),
    "TopicSearchItem": _obj(
        {
            "name": _t(S, "Nombre del tópico."),
            "total_articles": _t(I, "Artículos del tópico."),
        },
        desc="Tópico con su producción.",
    ),
    "AffiliationIdResponse": _obj(
        {"scopus_id": _t(S, "ID de la afiliación en Scopus.")},
        desc="Afiliación encontrada por nombre.",
    ),
    "HeatmapResponse": _obj(
        {
            "affiliations": {
                "type": "array",
                "description": "Afiliaciones con más artículos en el año (filas).",
                "items": {"$ref": "#/components/schemas/AffiliationRankingItem"},
            },
            "topics": {
                "type": "array",
                "description": "Tópicos con más artículos en el año (columnas).",
                "items": {"type": S},
            },
            "cells": {
                "type": "array",
                "description": "Artículos por cada par afiliación-tópico; los pares "
                "sin producción no aparecen.",
                "items": _obj(
                    {
                        "scopus_id": _t(S, "ID de la afiliación."),
                        "topic_name": _t(S, "Tópico."),
                        "total_articles": _t(I, "Artículos del par."),
                    }
                ),
            },
        },
        desc="Matriz afiliaciones × tópicos de un año.",
    ),
    "ErrorMessage": _obj(
        {"error": _t(S, "Descripción del error.")}, desc="Error de la operación."
    ),
    "MessageResponse": _obj({"message": _t(S, "Mensaje del resultado.")}),
    "DetailResponse": _obj({"detail": _t(S, "Mensaje del resultado.")}),
    "SuccessResponse": _obj(
        {
            "success": _t("boolean", "Si la operación terminó bien."),
            "message": _t(S, "Mensaje, presente cuando hubo un problema."),
        },
        required=["success"],
        desc="Resultado de una operación de administración.",
    ),
    "CorpusGeneratedResponse": _obj(
        {
            "success": _t("boolean", "Si el corpus se generó."),
            "total": _t(I, "Documentos incluidos en el corpus."),
        }
    ),
    "EtlStatusResponse": _obj(
        {
            "status": _t(
                S,
                "`running` si hay una ejecución activa; `idle` si no.",
                enum=["running", "idle"],
            ),
            "last_run_at": _t(
                S, "Fecha de la última ejecución, si hubo.", nullable=True
            ),
            "last_run_status": _t(
                S,
                "Resultado de la última ejecución: `success` o `error`.",
                nullable=True,
            ),
        },
        desc="Estado del ETL Neo4j → MongoDB.",
    ),
    "EtlStartedResponse": _obj(
        {
            "status": _t(
                S,
                "`processing` al iniciar; `already_running` si ya "
                "había una ejecución.",
            ),
            "message": _t(S, "Mensaje legible."),
        }
    ),
    "LogsPageResponse": _obj(
        {
            "page": _t(I, "Página devuelta."),
            "lines_per_page": _t(I, "Líneas por página."),
            "total_lines": _t(I, "Líneas que cumplen el filtro."),
            "logs": {
                "type": "array",
                "description": "Líneas de log de la página.",
                "items": {"type": S},
            },
        },
        desc="Página de logs del servicio.",
    ),
    "AuthorsComparatorResponse": _obj(
        {
            "authors_no_updated": _t(I, "Autores sin datos actualizados desde Scopus."),
            "total_authors": _t(I, "Total de autores en Centinela."),
        }
    ),
    "ArticlesComparatorResponse": _obj(
        {
            "total_centinela": _t(I, "Artículos en Centinela."),
            "total_scopus": _t(I, "Artículos que Scopus reporta para el país."),
        }
    ),
    "ModelCorpusResponse": _obj(
        {
            "model": _t("boolean", "Si existe el modelo TF-IDF."),
            "corpus": _t("boolean", "Si existe el corpus."),
        }
    ),
    "SystemHealthResponse": _obj(
        {
            "authors_no_updated": _t(I, "Autores sin actualizar."),
            "total_authors": _t(I, "Autores en Neo4j (fuente de verdad)."),
            "articles_pending": _t(I, "Artículos de Neo4j aún no materializados."),
            "stale_collections": _t(I, "Colecciones de MongoDB desactualizadas."),
            "stale_collection_names": {
                "type": "array",
                "description": "Nombres de esas colecciones.",
                "items": {"type": S},
            },
        },
        desc="Sincronización entre Neo4j y MongoDB.",
    ),
    "ArticleCountResponse": _obj({"total_articles": _t(I, "Total de artículos.")}),
    "SummaryResponse": _obj(
        {
            "authors": _t(I, "Total de autores."),
            "topics": _t(I, "Total de tópicos."),
            "articles": _t(I, "Total de artículos."),
        },
        desc="Totales del corpus.",
    ),
    "PagedAffiliationsResponse": _obj(
        {
            "total": _t(I, "Total de afiliaciones."),
            "next_page": _t(S, "URL de la página siguiente.", nullable=True),
            "previous_page": _t(S, "URL de la página anterior.", nullable=True),
            "results": {
                "type": "array",
                "description": "Afiliaciones de la página.",
                "items": {"$ref": "#/components/schemas/Affiliation"},
            },
        }
    ),
    "PagedArticlesResponse": _obj(
        {
            "total": _t(I, "Total de artículos."),
            "next_page": _t(S, "URL de la página siguiente.", nullable=True),
            "previous_page": _t(S, "URL de la página anterior.", nullable=True),
            "articles": {
                "type": "array",
                "description": "Artículos de la página.",
                "items": {"$ref": "#/components/schemas/Article"},
            },
        }
    ),
    "PagedAuthorsResponse": _obj(
        {
            "total": _t(I, "Total de autores."),
            "next_page": _t(S, "URL de la página siguiente.", nullable=True),
            "previous_page": _t(S, "URL de la página anterior.", nullable=True),
            "data": {
                "type": "array",
                "description": "Autores de la página.",
                "items": {"$ref": "#/components/schemas/Author"},
            },
        }
    ),
    "PagedAuthorMatchesResponse": _obj(
        {
            "total": _t(I, "Total de autores que coinciden."),
            "next_page": _t(S, "URL de la página siguiente.", nullable=True),
            "previous_page": _t(S, "URL de la página anterior.", nullable=True),
            "data": {
                "type": "array",
                "description": "Autores de la página.",
                "items": {"$ref": "#/components/schemas/RetrieveAuthor"},
            },
        }
    ),
    "RelevantArticlesResponse": _obj(
        {
            "data": {
                "type": "array",
                "description": "Artículos más relevantes.",
                "items": {"$ref": "#/components/schemas/Article"},
            },
            "years": {
                "type": "array",
                "description": "Años presentes en los resultados.",
                "items": {"type": S},
            },
            "total": _t(I, "Cantidad de artículos devueltos."),
        }
    ),
    "AuthorCommunityResponse": _obj(
        {
            "affiliations": {
                "type": "array",
                "description": "Afiliaciones de los autores, sin repetir.",
                "items": {"type": "object"},
            },
            "size_nodes": _t(I, "Cantidad de autores (nodos)."),
            "size_links": _t(I, "Cantidad de colaboraciones (aristas)."),
            "nodes": {
                "type": "array",
                "description": "Autores más relevantes.",
                "items": {"$ref": "#/components/schemas/Author"},
            },
            "links": {
                "type": "array",
                "description": "Colaboraciones entre esos autores.",
                "items": _obj(
                    {
                        "source": _t(S, "ID de Scopus del autor de origen."),
                        "target": _t(S, "ID de Scopus del autor de destino."),
                        "collabStrength": _t("number", "Fuerza de la colaboración."),
                    }
                ),
            },
        },
        desc="Autores relevantes y sus colaboraciones.",
    ),
    "CoauthorsResponse": _obj(
        {
            "data": _obj(
                {
                    "nodes": {
                        "type": "array",
                        "description": "El autor y sus coautores.",
                        "items": {"$ref": "#/components/schemas/Author"},
                    },
                    "links": {
                        "type": "array",
                        "description": "Colaboraciones entre ellos.",
                        "items": {"type": "object"},
                    },
                },
                desc="Red de coautoría.",
            )
        }
    ),
    "TopicsResponse": _obj(
        {
            "topics": {
                "type": "array",
                "description": "Tópicos del corpus.",
                "items": {"$ref": "#/components/schemas/Topic"},
            }
        }
    ),
    "SemanticSearchResponse": _obj(
        {
            "data": {
                "type": "array",
                "description": "Artículos ordenados por relevancia.",
                "items": _obj(
                    {
                        "title": _t(S, "Título."),
                        "abstract": _t(S, "Resumen."),
                        "author_count": _t(I, "Cantidad de autores."),
                        "affiliation_count": _t(I, "Cantidad de afiliaciones."),
                        "publication_date": _t(S, "Fecha de publicación."),
                        "scopus_id": _t(S, "ID del artículo en Scopus."),
                        "authors": {
                            "type": "array",
                            "description": "Autores.",
                            "items": {"type": S},
                        },
                        "affiliations": {
                            "type": "array",
                            "description": "Afiliaciones.",
                            "items": {"type": S},
                        },
                        "relevance": _t("number", "Puntaje de relevancia."),
                    }
                ),
            },
            "years": {
                "type": "array",
                "description": "Años presentes en los resultados.",
                "items": {"type": S},
            },
            "total": _t(I, "Cantidad de resultados."),
            "qa_context_hint": _obj(
                {
                    "endpoint": _t(S, "Endpoint al que enviar los mejores resultados."),
                    "top_n": _t(I, "Cuántos resultados usar."),
                    "documents": {
                        "type": "array",
                        "description": "Los mejores resultados, listos para enviar.",
                        "items": {"type": "object"},
                    },
                },
                desc="Sugerencia para generar preguntas y respuestas.",
            ),
        },
        desc="Resultados de la búsqueda semántica.",
    ),
    "QAResponse": _obj(
        {
            "query": _t(S, "Consulta original."),
            "status": _t(S, "Estado de la generación."),
            "qa_pairs": {
                "type": "array",
                "description": "Pares pregunta-respuesta generados.",
                "items": {"type": "object"},
            },
            "raw_response": _t(S, "Respuesta cruda del modelo."),
            "intentos_utilizados": _t(I, "Intentos de generación usados."),
            "latency": {"type": "object", "description": "Tiempos en milisegundos."},
            "source_docs": {
                "type": "array",
                "description": "Artículos usados como contexto.",
                "items": {"type": "object"},
            },
        },
        required=["query", "status", "qa_pairs"],
        desc="Preguntas y respuestas generadas a partir de los artículos.",
    ),
    "TextHealthResponse": _obj(
        {
            "status": _t(S, "`healthy` o `unhealthy`."),
            "service": _t(S, "Nombre del servicio."),
            "model_dimension": _t(I, "Dimensión del modelo de embeddings."),
            "message": _t(S, "Mensaje legible."),
        },
        required=["status", "service"],
    ),
    "VectorizeResponse": {
        "type": "object",
        "description": "Resultado de la vectorización: incluye el vector del texto "
        "y los datos del procesamiento.",
        "additionalProperties": True,
    },
    "FairnessResultsResponse": {
        "type": "object",
        "description": "Resultados del experimento tal como los entregó el "
        "pipeline de equidad (estructura propia de cada experimento).",
        "additionalProperties": True,
    },
}


EXTRA_SCHEMAS.update(
    {
        "SemanticSearchRequest": _obj(
            {
                "query": _t(S, "Texto de la búsqueda.", example="energías renovables"),
                "top_k": _t(
                    I, "Cuántos resultados devolver (por defecto 10).", default=10
                ),
                "use_hyde": _t(
                    "boolean",
                    "Genera antes un texto hipotético para mejorar la búsqueda "
                    "(por defecto `false`).",
                    default=False,
                ),
            },
            required=["query"],
        ),
        "GenerateQARequest": _obj(
            {
                "query": _t(S, "Consulta original de la búsqueda."),
                "documents": {
                    "type": "array",
                    "description": "Mejores resultados de la búsqueda (`data` de "
                    "`semantic-search`). También se acepta con el nombre `data`.",
                    "items": {"type": "object"},
                },
                "use_compression": _t(
                    "boolean",
                    "Comprime el contexto antes de generar (por defecto `true`).",
                    default=True,
                ),
                "use_iterative": _t(
                    "boolean",
                    "Reintenta la generación si la respuesta no es válida "
                    "(por defecto `true`).",
                    default=True,
                ),
            },
            required=["query", "documents"],
        ),
        "VectorizeRequest": _obj(
            {
                "text": _t(S, "Texto a vectorizar; no puede estar vacío."),
                "translate_to_english": _t(
                    "boolean",
                    "Traduce el texto al inglés antes de vectorizar "
                    "(por defecto `true`).",
                    default=True,
                ),
                "clean_text": _t(
                    "boolean",
                    "Limpia el texto antes de vectorizar (por defecto `true`).",
                    default=True,
                ),
            },
            required=["text"],
        ),
    }
)


# ------------------------------------------------------------ respuestas
def ref(name):
    return ("ref", name)


def arr(name):
    return ("array", name)


def inline(schema):
    return ("inline", schema)


ERR = {
    400: ("Petición inválida o error al procesarla.", "ErrorMessage"),
    404: ("No se encontró el recurso.", "ErrorMessage"),
    409: ("Ya hay una ejecución en curso.", "EtlStartedResponse"),
    429: ("Ya hay otra ejecución en curso.", "SuccessResponse"),
    403: ("Se requieren las credenciales de administrador.", "DetailResponse"),
    500: ("Error interno al consultar los datos.", "ErrorMessage"),
    503: ("El servicio no está disponible.", "TextHealthResponse"),
}
OK_TEXT = {
    200: "Operación exitosa.",
    201: "Recurso creado.",
    202: "Aceptado.",
    204: "Sin contenido.",
}

OPERATIONS = {}


def op(
    method,
    path,
    tag,
    summary,
    description,
    ok=None,
    status=200,
    errors=(),
    admin=False,
    **extra,
):
    OPERATIONS[(method, path)] = {
        "tag": tag,
        "summary": summary,
        "description": description,
        "ok": ok,
        "status": status,
        "errors": tuple(errors),
        "admin": admin,
        **extra,
    }


# ----------------------------------------------------------- Búsqueda
op(
    "POST",
    "/llm-search/semantic-search/",
    T_SEARCH,
    "Búsqueda semántica de artículos",
    "Busca artículos por significado con un modelo de lenguaje y devuelve solo los "
    "resultados ordenados por relevancia. Con `use_hyde` genera antes un texto "
    "hipotético para mejorar la búsqueda. La generación de preguntas y respuestas es "
    "aparte: `qa_context_hint` indica qué enviar a `generate-qa`.",
    ref("SemanticSearchResponse"),
    errors=(400,),
    body="SemanticSearchRequest",
)
op(
    "POST",
    "/llm-search/generate-qa/",
    T_SEARCH,
    "Generar preguntas y respuestas",
    "Genera preguntas y respuestas académicas a partir de la consulta y de los mejores "
    "resultados de la búsqueda (`documents` o `data`). Es independiente de la "
    "búsqueda y puede tardar porque usa un modelo de lenguaje local.",
    ref("QAResponse"),
    errors=(400,),
    body="GenerateQARequest",
)

# ----------------------------------------------------------- Artículos
op(
    "GET",
    "/articles/",
    T_ART,
    "Listar artículos",
    "Devuelve los artículos del corpus paginados. La respuesta incluye el total y los "
    "enlaces a la página siguiente y anterior.",
    ref("PagedArticlesResponse"),
    errors=(500,),
)
op(
    "GET",
    "/articles/count/",
    T_ART,
    "Contar artículos",
    "Devuelve el número total de artículos del corpus.",
    ref("ArticleCountResponse"),
    errors=(500,),
)
op(
    "GET",
    "/articles/find-articles-by-author-id/",
    T_ART,
    "Artículos de un autor",
    "Lista los artículos publicados por un autor, dado su ID de Scopus.",
    arr("Article"),
    errors=(500,),
)
op(
    "POST",
    "/articles/most-relevant-articles-by-topic/",
    T_ART,
    "Artículos más relevantes para un tópico",
    "Devuelve los artículos más relevantes para un tópico. `type` y `years` permiten "
    "incluir o excluir años. La respuesta trae también los años presentes.",
    ref("RelevantArticlesResponse"),
    errors=(400,),
)
op(
    "GET",
    "/articles/{id}/",
    T_ART,
    "Detalle de un artículo",
    "Devuelve un artículo por su ID de Scopus, con sus autores, afiliaciones y "
    "tópicos.",
    ref("Article"),
    errors=(500,),
)
op(
    "DELETE",
    "/articles/{id}/",
    T_ART,
    "Vaciar la base de datos de Neo4j",
    "**Operación destructiva y exclusiva de administración.** Ignora el `{id}` y "
    "borra todos los nodos de la base de Neo4j. Exige las credenciales de "
    "administrador por HTTP Basic. No se usa desde el frontend.",
    None,
    status=204,
    errors=(403, 500),
    admin=True,
)

# ----------------------------------------------------------- Autores
op(
    "GET",
    "/authors/",
    T_AUT,
    "Listar autores",
    "Devuelve los autores del corpus paginados.",
    ref("PagedAuthorsResponse"),
    errors=(500,),
)
op(
    "GET",
    "/authors/find_by_query/",
    T_AUT,
    "Buscar autores por nombre",
    "Busca autores cuyo nombre, apellido, iniciales, correo o ID coincidan con el "
    "texto. Ignora mayúsculas y tildes, y ordena por citas.",
    ref("PagedAuthorMatchesResponse"),
    errors=(400,),
)
op(
    "POST",
    "/authors/most_relevant_authors/",
    T_AUT,
    "Autores más relevantes para un tópico",
    "Devuelve los autores más relevantes para un tópico como una red: autores "
    "(`nodes`) y sus colaboraciones (`links`). Con `type` y `affiliations` filtra: "
    "`include` deja solo los autores de esas afiliaciones; cualquier otro valor los "
    "excluye.",
    ref("AuthorCommunityResponse"),
    errors=(400,),
)
op(
    "GET",
    "/authors/{id}/",
    T_AUT,
    "Detalle de un autor",
    "Devuelve un autor por su ID de Scopus.",
    ref("Author"),
    errors=(400,),
)
op(
    "GET",
    "/coauthors/{id}/coauthors_by_id/",
    T_AUT,
    "Red de coautores de un autor",
    "Devuelve el autor, sus coautores y las colaboraciones entre todos ellos.",
    ref("CoauthorsResponse"),
)

# ----------------------------------------------------------- Afiliaciones
op(
    "GET",
    "/affiliations/",
    T_AFF,
    "Listar afiliaciones",
    "Devuelve las afiliaciones del corpus paginadas.",
    ref("PagedAffiliationsResponse"),
    errors=(500,),
)
op(
    "GET",
    "/affiliations/{id}/",
    T_AFF,
    "Detalle de una afiliación",
    "Devuelve una afiliación por su ID de Scopus.",
    ref("Affiliation"),
    errors=(500,),
)

# ----------------------------------------------------------- Tópicos
op(
    "GET",
    "/topics/",
    T_TOP,
    "Listar tópicos",
    "Devuelve todos los tópicos del corpus.",
    ref("TopicsResponse"),
)

# ------------------------------------------- Dashboard: producción nacional
op(
    "GET",
    "/summary/",
    T_DNAT,
    "Totales del corpus",
    "Devuelve cuántos autores, tópicos y artículos tiene el corpus.",
    ref("SummaryResponse"),
    errors=(404,),
)
op(
    "GET",
    "/dashboard/country/get_last_years/",
    T_DNAT,
    "Totales del país por año",
    "Devuelve, para cada año desde 2000, los autores, artículos, afiliaciones y "
    "tópicos del país.",
    arr("CountryYearTotals"),
    errors=(500,),
)
op(
    "GET",
    "/dashboard/country/get_years/",
    T_DNAT,
    "Años con datos",
    "Devuelve los años para los que hay datos del país.",
    arr("YearItem"),
    errors=(500,),
)
op(
    "GET",
    "/dashboard/country/get_year/",
    T_DNAT,
    "Totales del país en un año",
    "Devuelve los autores, artículos, afiliaciones y tópicos de un año.",
    ref("CountryTotals"),
    errors=(500,),
)
op(
    "GET",
    "/dashboard/country/get_year_info/",
    T_DNAT,
    "Totales del país en un año, con el año",
    "Igual que `get_year`, pero la respuesta incluye el campo `year`.",
    ref("CountryYearTotals"),
    errors=(500,),
)
op(
    "GET",
    "/dashboard/country/get_range_info/",
    T_DNAT,
    "Totales del país por año hasta un año",
    "Devuelve los totales de cada año desde 2000 hasta el año indicado.",
    arr("CountryYearTotals"),
    errors=(500,),
)
op(
    "GET",
    "/dashboard/country/get_acumulated/",
    T_DNAT,
    "Totales acumulados del país hasta un año",
    "Devuelve los totales acumulados desde el inicio del corpus hasta el año "
    "indicado (por defecto 2023).",
    ref("CountryTotals"),
    errors=(500,),
)

# -------------------------------------------------- Dashboard: tópicos
op(
    "GET",
    "/dashboard/country/get_topics/",
    T_DTOP,
    "Tópicos principales del país",
    "Devuelve los tópicos con más artículos, de mayor a menor, en formato de nube de "
    "palabras (`text`, `size`).",
    arr("WordItem"),
    errors=(500,),
)
op(
    "GET",
    "/dashboard/country/get_top_topics/",
    T_DTOP,
    "Los 10 tópicos principales de un año",
    "Devuelve los 10 tópicos con más artículos acumulados hasta el año indicado.",
    arr("WordItem"),
    errors=(500,),
)
op(
    "GET",
    "/dashboard/country/get_top_topics_year/",
    T_DTOP,
    "Los 30 tópicos principales publicados en un año",
    "Devuelve los 30 tópicos con más artículos publicados solo en ese año.",
    arr("WordItem"),
    errors=(500,),
)
op(
    "GET",
    "/dashboard/country/search/",
    T_DTOP,
    "Buscar tópicos por nombre",
    "Devuelve hasta 20 tópicos cuyo nombre coincide con el texto, ordenados por "
    "número de artículos.",
    arr("TopicSearchItem"),
    errors=(500,),
)
op(
    "GET",
    "/dashboard/country/get_topics_summary/",
    T_DTOP,
    "Resumen de un tópico",
    "Devuelve cuántos artículos tiene un tópico y cuántas afiliaciones publican "
    "sobre él.",
    ref("TopicSummary"),
    errors=(500,),
)
op(
    "GET",
    "/dashboard/country/get_topics_summary_year/",
    T_DTOP,
    "Resumen de un tópico en un año",
    "Igual que el resumen, pero solo con lo publicado en el año indicado.",
    ref("TopicSummary"),
    errors=(500,),
)
op(
    "GET",
    "/dashboard/country/get_topics_summary_acumulated/",
    T_DTOP,
    "Resumen acumulado de un tópico hasta un año",
    "Igual que el resumen, acumulado hasta el año indicado.",
    ref("TopicSummary"),
    errors=(500,),
)
op(
    "GET",
    "/dashboard/country/get_topics_years/",
    T_DTOP,
    "Años de un tópico",
    "Devuelve los años desde 2000 en los que hay artículos del tópico.",
    arr("YearItem"),
    errors=(500,),
)
op(
    "GET",
    "/dashboard/country/get_topics_year_info/",
    T_DTOP,
    "Evolución anual de un tópico",
    "Devuelve, año por año desde 2000, los artículos del tópico.",
    arr("CountryTopicsYear"),
    errors=(500,),
)
op(
    "GET",
    "/dashboard/country/get_topics_range_year/",
    T_DTOP,
    "Evolución de un tópico hasta un año",
    "Devuelve los artículos del tópico de cada año desde 2000 hasta el año "
    "indicado.",
    arr("CountryTopicsYear"),
    errors=(500,),
)
op(
    "GET",
    "/dashboard/country/get_topics_year/",
    T_DTOP,
    "Un tópico en un año",
    "Devuelve los artículos de un tópico en un año, dentro de una lista de un "
    "elemento.",
    arr("CountryTopicsYear"),
    errors=(500,),
)
op(
    "GET",
    "/dashboard/country/get_topics_acumulated/",
    T_DTOP,
    "Tópico acumulado hasta un año",
    "Devuelve el acumulado del tópico hasta el año indicado.",
    arr("CountryTopics"),
    errors=(500,),
)
op(
    "GET",
    "/dashboard/country/get_topics_affiliations/",
    T_DTOP,
    "Afiliaciones que más publican en un tópico",
    "Devuelve las 30 afiliaciones con más artículos en el tópico.",
    arr("WordItem"),
    errors=(500,),
)
op(
    "GET",
    "/dashboard/country/get_topics_affiliations_year/",
    T_DTOP,
    "Afiliaciones que más publican en un tópico, en un año",
    "Devuelve las 30 afiliaciones con más artículos del tópico en ese año.",
    arr("WordItem"),
    errors=(500,),
)
op(
    "GET",
    "/dashboard/country/get_topics_affiliations_acumulated/",
    T_DTOP,
    "Afiliaciones que más publican en un tópico, acumulado",
    "Devuelve las 30 afiliaciones con más artículos del tópico acumulados hasta el "
    "año indicado.",
    arr("WordItem"),
    errors=(500,),
)

# ------------------------------------------------ Dashboard: afiliaciones
op(
    "GET",
    "/dashboard/affiliation/get_affiliations/",
    T_DAFF,
    "Afiliaciones principales",
    "Devuelve las 50 afiliaciones con más artículos en todo el corpus.",
    arr("WordItem"),
    errors=(500,),
)
op(
    "GET",
    "/dashboard/affiliation/get_top_affiliations/",
    T_DAFF,
    "Afiliaciones principales acumuladas hasta un año",
    "Devuelve las 50 afiliaciones con más artículos acumulados hasta el año "
    "indicado.",
    arr("WordItem"),
    errors=(500,),
)
op(
    "GET",
    "/dashboard/affiliation/get_top_affiliations_year/",
    T_DAFF,
    "Afiliaciones principales de un año",
    "Devuelve las 50 afiliaciones con más artículos publicados en ese año.",
    arr("WordItem"),
    errors=(500,),
)
op(
    "GET",
    "/dashboard/affiliation/search/",
    T_DAFF,
    "Buscar afiliaciones por nombre",
    "Devuelve las afiliaciones cuyo nombre coincide con el texto, ordenadas por "
    "número de artículos.",
    arr("AffiliationRankingItem"),
    errors=(500,),
)
op(
    "GET",
    "/dashboard/affiliation/get_by_name/",
    T_DAFF,
    "ID de una afiliación por su nombre",
    "Devuelve el ID de Scopus de la afiliación con ese nombre.",
    ref("AffiliationIdResponse"),
    errors=(404, 500),
)
op(
    "GET",
    "/dashboard/affiliation/get_years/",
    T_DAFF,
    "Años con datos de una afiliación",
    "Devuelve los años en los que la afiliación tiene producción.",
    arr("YearItem"),
    errors=(500,),
)
op(
    "GET",
    "/dashboard/affiliation/get_affiliation_years/",
    T_DAFF,
    "Producción anual de una afiliación",
    "Devuelve, año por año desde 2000, los artículos y tópicos de la afiliación.",
    arr("AffiliationYear"),
    errors=(500,),
)
op(
    "GET",
    "/dashboard/affiliation/get_year/",
    T_DAFF,
    "Producción de una afiliación en un año",
    "Devuelve los artículos y tópicos de la afiliación en el año, dentro de una "
    "lista de un elemento.",
    arr("AffiliationYear"),
    errors=(500,),
)
op(
    "GET",
    "/dashboard/affiliation/get_year_range/",
    T_DAFF,
    "Producción de una afiliación hasta un año",
    "Devuelve la producción de la afiliación en cada año desde 2000 hasta el año "
    "indicado.",
    arr("AffiliationYear"),
    errors=(500,),
)
op(
    "GET",
    "/dashboard/affiliation/get_affiliation_topics/",
    T_DAFF,
    "Tópicos principales de una afiliación",
    "Devuelve los 20 tópicos con más artículos de la afiliación.",
    arr("WordItem"),
    errors=(500,),
)
op(
    "GET",
    "/dashboard/affiliation/get_topics_year/",
    T_DAFF,
    "Tópicos de una afiliación en un año",
    "Devuelve los 30 tópicos con más artículos de la afiliación en ese año.",
    arr("WordItem"),
    errors=(500,),
)
op(
    "GET",
    "/dashboard/affiliation/get_topics_acumulated/",
    T_DAFF,
    "Tópicos de una afiliación, acumulado hasta un año",
    "Devuelve los 30 tópicos con más artículos de la afiliación acumulados hasta "
    "el año indicado.",
    arr("WordItem"),
    errors=(500,),
)
op(
    "GET",
    "/dashboard/affiliation/get_articles_topics/",
    T_DAFF,
    "Artículos y tópicos de una afiliación",
    "Devuelve cuántos artículos y tópicos tiene la afiliación en total.",
    ref("ArticlesTopicsCount"),
    errors=(500,),
)
op(
    "GET",
    "/dashboard/affiliation/get_articles_topics_year/",
    T_DAFF,
    "Artículos y tópicos de una afiliación en un año",
    "Devuelve cuántos artículos y tópicos tiene la afiliación en el año.",
    ref("ArticlesTopicsCount"),
    errors=(500,),
)
op(
    "GET",
    "/dashboard/affiliation/get_articles_topics_acumulated/",
    T_DAFF,
    "Artículos y tópicos de una afiliación, acumulado",
    "Devuelve cuántos artículos y tópicos tiene la afiliación acumulados hasta el "
    "año indicado.",
    ref("ArticlesTopicsCount"),
    errors=(500,),
)
op(
    "GET",
    "/dashboard/affiliation/get_topics_heatmap/",
    T_DAFF,
    "Matriz de concentración afiliaciones × tópicos",
    "Devuelve, para un año, las afiliaciones con más artículos, los tópicos con más "
    "artículos y cuántos artículos tiene cada par. Sirve para dibujar un mapa de "
    "calor.",
    ref("HeatmapResponse"),
    errors=(500,),
)

# ---------------------------------------------------- Dashboard: autores
op(
    "GET",
    "/dashboard/author/get_author_years/",
    T_DAUT,
    "Años de publicación de un autor",
    "Devuelve, año por año desde 2000, los artículos del autor.",
    arr("AuthorYear"),
    errors=(500,),
)
op(
    "GET",
    "/dashboard/author/get_topics/",
    T_DAUT,
    "Tópicos de un autor",
    "Devuelve los tópicos del autor ordenados por número de artículos.",
    arr("WordItem"),
    errors=(500,),
)

# --------------------------------------------------- Dashboard: provincias
op(
    "GET",
    "/dashboard/province/get_provinces/",
    T_DPRO,
    "Producción por provincia",
    "Devuelve los artículos de cada provincia en todo el corpus, sin incluir las "
    "pendientes de asignar.",
    arr("Province"),
    errors=(500,),
)
op(
    "GET",
    "/dashboard/province/get_provinces_year/",
    T_DPRO,
    "Producción por provincia en un año",
    "Devuelve los artículos de cada provincia en el año.",
    arr("ProvinceYear"),
    errors=(500,),
)
op(
    "GET",
    "/dashboard/province/get_provinces_acumulated/",
    T_DPRO,
    "Producción por provincia, acumulada hasta un año",
    "Devuelve los artículos de cada provincia acumulados hasta el año indicado.",
    arr("ProvinceAcumulated"),
    errors=(500,),
)

# ------------------------------------------------------ Dashboard: equidad
op(
    "GET",
    "/dashboard/fairness/summary/",
    T_DEQ,
    "Resultados consolidados de equidad",
    "Devuelve todos los resultados de equidad del sistema de recomendación en una "
    "sola respuesta.",
    ref("FairnessResultsResponse"),
    errors=(404, 500),
)
op(
    "GET",
    "/dashboard/fairness/baseline/",
    T_DEQ,
    "Línea base de equidad",
    "Devuelve el diagnóstico inicial de equidad (sesión S5) con los valores SHAP.",
    ref("FairnessResultsResponse"),
    errors=(404, 500),
)
op(
    "GET",
    "/dashboard/fairness/mitigation/",
    T_DEQ,
    "Impacto de la mitigación",
    "Devuelve el antes y después de aplicar la mitigación, el veredicto y la "
    "selección final (sesión S10).",
    ref("FairnessResultsResponse"),
    errors=(404, 500),
)
op(
    "GET",
    "/dashboard/fairness/sensitivity/",
    T_DEQ,
    "Sensibilidad de los parámetros",
    "Devuelve los barridos de sensibilidad de los parámetros alfa y lambda "
    "(sesión S10).",
    ref("FairnessResultsResponse"),
    errors=(404, 500),
)

# ------------------------------------------------ Administración: datos
op(
    "POST",
    "/dashboard/populate",
    T_ADM,
    "Repoblar el datalake de dashboards",
    "Recalcula en MongoDB todos los agregados que alimentan los dashboards a partir "
    "de Neo4j. **Exige las credenciales de administrador** por HTTP Basic.",
    ref("MessageResponse"),
    errors=(403, 500),
    admin=True,
)
op(
    "POST",
    "/admin/etl/run/",
    T_ADM,
    "Iniciar el ETL Neo4j → MongoDB",
    "Ejecuta `upsert_mongo` en segundo plano y responde 202 de inmediato. Si ya hay "
    "una ejecución en curso responde 409. Consulta el avance con "
    "`GET /admin/etl/run/`.",
    ref("EtlStartedResponse"),
    status=202,
    errors=(409,),
)
op(
    "POST",
    "/generate-corpus/",
    T_ADM,
    "Generar el corpus TF-IDF",
    "Construye el corpus de texto a partir de los artículos de Neo4j. Es el paso "
    "previo a generar el modelo.",
    ref("CorpusGeneratedResponse"),
    errors=(400,),
)
op(
    "POST",
    "/generate-model/",
    T_ADM,
    "Generar el modelo TF-IDF",
    "Entrena el modelo TF-IDF con el corpus generado.",
    ref("SuccessResponse"),
    errors=(400,),
)
op(
    "GET",
    "/scopus-integration/",
    T_ADM,
    "Ingestar datos desde Scopus",
    "Consulta la API de Scopus e incorpora los artículos nuevos al corpus. Con "
    "`year` procesa solo ese año. Consume cuota de la API de Scopus y puede tardar.",
    ref("SuccessResponse"),
    errors=(400,),
)
op(
    "POST",
    "/information/update/author-information/",
    T_ADM,
    "Actualizar los datos de los autores desde Scopus",
    "Actualiza la información de los autores desde Scopus. Si ya hay una "
    "actualización en curso responde 429.",
    ref("SuccessResponse"),
    errors=(429, 400),
)

# ------------------------------------------------ Administración: estado
op(
    "GET",
    "/admin/etl/run/",
    T_STA,
    "Estado del ETL",
    "Indica si el ETL está corriendo y cómo terminó la última ejecución. El frontend "
    "lo consulta periódicamente.",
    ref("EtlStatusResponse"),
)
op(
    "GET",
    "/admin/logs/",
    T_STA,
    "Consultar los logs del servicio",
    "Devuelve líneas de log paginadas, con filtros por nivel, rango de fechas y "
    "texto.",
    ref("LogsPageResponse"),
    errors=(400,),
)
op(
    "GET",
    "/dashboard/information/get_authors_comparator/",
    T_STA,
    "Comparador de autores",
    "Devuelve cuántos autores hay en Centinela y cuántos no están actualizados.",
    ref("AuthorsComparatorResponse"),
    errors=(400,),
)
op(
    "GET",
    "/dashboard/information/get_articles_comparator/",
    T_STA,
    "Comparador de artículos con Scopus",
    "Compara los artículos de Centinela con los que Scopus reporta para el país.",
    ref("ArticlesComparatorResponse"),
    errors=(400,),
)
op(
    "GET",
    "/dashboard/information/tfidf_model_corpus/",
    T_STA,
    "¿Existen el modelo y el corpus TF-IDF?",
    "Indica si los archivos del modelo y del corpus existen en disco.",
    ref("ModelCorpusResponse"),
    errors=(400,),
)
op(
    "GET",
    "/dashboard/information/get_system_health/",
    T_STA,
    "Salud de la sincronización Neo4j → MongoDB",
    "Compara los totales de Neo4j (fuente de verdad) con los agregados ya "
    "materializados en MongoDB e indica qué colecciones están desactualizadas.",
    ref("SystemHealthResponse"),
    errors=(400,),
)

# ------------------------------------------------------ Autenticación
op(
    "POST",
    "/auth/login/",
    T_LOGIN,
    "Validar las credenciales de administración",
    "Comprueba el usuario y la contraseña del panel de administración contra la "
    "configuración del servicio. **No emite token ni sesión**: solo responde si las "
    "credenciales son correctas.",
    ref("MessageResponse"),
    errors=(400,),
)
op(
    "POST",
    "/auth/logout/",
    T_LOGIN,
    "Cerrar la sesión de administración",
    "Responde que el cierre de sesión fue exitoso. No guarda estado en el servidor.",
    ref("DetailResponse"),
)

# --------------------------------------------- Procesamiento de texto
op(
    "GET",
    "/text-processing/health/",
    T_TXT,
    "Estado del procesamiento de texto",
    "Comprueba que el modelo de embeddings responde y devuelve su dimensión.",
    ref("TextHealthResponse"),
    errors=(503,),
)
op(
    "POST",
    "/text-processing/vectorize/",
    T_TXT,
    "Vectorizar un texto",
    "Limpia el texto, opcionalmente lo traduce al inglés y devuelve su vector. "
    "Cuerpo: `text` (obligatorio), `translate_to_english` (por defecto `true`) y "
    "`clean_text` (por defecto `true`).",
    ref("VectorizeResponse"),
    errors=(400,),
    body="VectorizeRequest",
)

# ---------------------------------------------------------------- hooks
# La ruta de detalle llega al preprocesado como "{id}", "(?P<pk>...)" o "<pk>", y las
# acciones del dashboard empiezan con una letra ("get_...", "search").
CRUD_ROUTES = re.compile(
    r"^/api-se/v1/dashboard/(affiliation|author|country|province)/([{(<][^/]*/)?$"
)
HTTP_METHODS = ("get", "post", "put", "patch", "delete")
SCHEMA_REF = re.compile(r"#/components/schemas/([A-Za-z0-9_]+)")

PROP_DESCRIPTIONS = {
    "scopus_id": "ID en Scopus.",
    "name": "Nombre.",
    "city": "Ciudad.",
    "country": "País.",
    "id": "Identificador interno del registro.",
    "year": "Año.",
    "total_articles": "Artículos.",
    "total_topics": "Tópicos.",
    "total_authors": "Autores.",
    "total_affiliations": "Afiliaciones.",
    "topic_name": "Nombre del tópico.",
    "province_name": "Nombre de la provincia.",
    "title": "Título.",
    "abstract": "Resumen.",
    "doi": "DOI.",
    "publication_date": "Fecha de publicación.",
    "author_count": "Cantidad de autores.",
    "affiliation_count": "Cantidad de afiliaciones.",
    "corpus": "Corpus de origen.",
    "affiliations": "Afiliaciones.",
    "topics": "Tópicos.",
    "first_name": "Nombres.",
    "last_name": "Apellidos.",
    "auth_name": "Nombre con el que firma, estilo Scopus.",
    "initials": "Iniciales.",
    "articles": "Artículos.",
    "co_authors": "IDs de Scopus de los coautores.",
    "citation_count": "Citas acumuladas.",
    "current_affiliation": "Afiliación actual.",
    "updated": "Si los datos del autor ya se actualizaron desde Scopus.",
    "username": "Usuario.",
    "password": "Contraseña.",
    "query": "Texto de la consulta.",
    "page": "Número de página.",
    "size": "Resultados por página.",
    "type": "`include` deja solo lo indicado; cualquier otro valor lo excluye.",
    "years": "Años a filtrar.",
    "topic": "Tópico.",
    "authors_number": "Cantidad de autores a devolver.",
    "lines_per_page": "Líneas por página.",
    "level": "Nivel de log.",
    "start_date": "Fecha inicial.",
    "end_date": "Fecha final.",
    "keyword": "Texto a buscar.",
}


def exclude_unused_routes(endpoints, **kwargs):
    """Quita las rutas CRUD heredadas de los ModelViewSet del dashboard."""
    return [e for e in endpoints if not CRUD_ROUTES.match(e[0])]


def _schema(kind, value):
    if kind == "ref":
        return {"$ref": f"#/components/schemas/{value}"}
    if kind == "array":
        return {"type": "array", "items": {"$ref": f"#/components/schemas/{value}"}}
    return value


def _response(text, ref_name):
    return {
        "description": text,
        "content": {
            "application/json": {"schema": {"$ref": f"#/components/schemas/{ref_name}"}}
        },
    }


def _specific_param_text(path, name):
    specific = PARAMS_BY_PATH.get((path, name))
    if specific:
        return specific
    best = None
    for (prefix, key), text in PARAMS_BY_PATH.items():
        if key == name and prefix.endswith("/") and path.startswith(prefix):
            if best is None or len(prefix) > len(best[0]):
                best = (prefix, text)
    if best:
        return best[1]
    return PARAMS.get(name)


def _apply(path, operation, doc):
    operation["tags"] = [doc["tag"]]
    operation["summary"] = doc["summary"]
    operation["description"] = doc["description"]

    parameters = []
    for parameter in operation.get("parameters", []):
        name = parameter["name"]
        if name == "page" and path.startswith("/dashboard/"):
            continue  # los dashboards no paginan
        text = _specific_param_text(path, name)
        if text:
            parameter["description"] = text
            if isinstance(parameter.get("schema"), dict):
                parameter["schema"].pop("description", None)
        parameters.append(parameter)
    if parameters:
        operation["parameters"] = parameters
    else:
        operation.pop("parameters", None)

    responses = {}
    if doc["ok"] is None:
        responses[str(doc["status"])] = {
            "description": OK_TEXT.get(doc["status"], "Operación exitosa.")
        }
    else:
        kind, value = doc["ok"]
        responses[str(doc["status"])] = {
            "description": OK_TEXT.get(doc["status"], "Operación exitosa."),
            "content": {"application/json": {"schema": _schema(kind, value)}},
        }
    for code in doc["errors"]:
        text, ref_name = ERR[code]
        responses[str(code)] = _response(text, ref_name)
    operation["responses"] = responses

    operation["security"] = [{"basicAuth": []}] if doc["admin"] else []
    if doc.get("body"):
        operation["requestBody"] = {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {"$ref": f"#/components/schemas/{doc['body']}"}
                }
            },
        }


def _used_schemas(result):
    schemas = result.get("components", {}).get("schemas", {})
    seen, queue = set(), []
    for name in SCHEMA_REF.findall(json.dumps(result.get("paths", {}), default=str)):
        queue.append(name)
    while queue:
        name = queue.pop()
        if name in seen or name not in schemas:
            continue
        seen.add(name)
        queue.extend(SCHEMA_REF.findall(json.dumps(schemas[name], default=str)))
    return seen


def organize_schema(result, generator, request, public):
    """Agrupa, ordena y documenta las operaciones; ver el docstring del modulo."""
    components = result.setdefault("components", {})
    schemas = components.setdefault("schemas", {})
    schemas.update(EXTRA_SCHEMAS)

    published = {}
    for path, item in result.get("paths", {}).items():
        key = path[3:] if path.startswith("/v1/") else path
        published[key] = item

    ordered = {}
    for (method, key), doc in OPERATIONS.items():
        item = published.get(key)
        if not item or method.lower() not in item:
            continue
        operation = item[method.lower()]
        _apply(key, operation, doc)
        ordered.setdefault(path_for(result, key), {})[method.lower()] = operation

    # operaciones que no estan en la tabla se conservan al final
    documented = {(m.lower(), k) for (m, k) in OPERATIONS}
    for key, item in published.items():
        for method, operation in item.items():
            if method in HTTP_METHODS and (method, key) not in documented:
                ordered.setdefault(path_for(result, key), {})[method] = operation
    result["paths"] = ordered

    # esquemas: descripciones en espanol y fuera los que ya no se usan
    used = _used_schemas(result)
    for name in list(schemas):
        if name not in used:
            del schemas[name]
    for definition in schemas.values():
        for prop, spec in definition.get("properties", {}).items():
            spec.pop("title", None)
            if not spec.get("description") and not any(
                "description" in part for part in spec.get("allOf", [])
            ):
                text = PROP_DESCRIPTIONS.get(prop)
                if text:
                    spec["description"] = text

    result["tags"] = TAGS
    components["securitySchemes"] = {
        "basicAuth": {
            "type": "http",
            "scheme": "basic",
            "description": "Credenciales de administrador (`ADMIN_CENTINELA` / "
            "`PASSWORD_CENTINELA`).",
        }
    }
    return result


def path_for(result, key):
    return "/v1" + key
