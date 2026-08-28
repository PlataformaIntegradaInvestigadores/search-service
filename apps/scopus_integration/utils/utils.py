"""
Created on Mon May 23 2021

@author: Nicolas
"""

from urllib.parse import unquote

import numpy as np


def encodeFacets(url, facets):
    """Codifica las "facets" de la URL a percent-encoding
    para que pueda ser utilizada en las peticiones a las APIs"""

    if facets:
        return url.replace(unquote(facets), facets)
    else:
        return url


def recastDfAffiliations(dfAffiliations):
    """Reestructura el dataframe de afiliaciones para que tenga
    los campos adecuados y una estructura de datos más útil"""

    # Elimina la columna @_fa
    dfAffiliations.pop("@_fa")

    # Elimina la columna prism:url
    dfAffiliations.pop("prism:url")

    # Renombra las columnas
    dfAffiliations.rename(
        columns={
            "dc:identifier": "identifier",
            "affiliation-name": "affiliation_name",
            "document-count": "document_count",
        },
        inplace=True,
    )

    # Modifica el valor de la columna identifier. Ej. AFFILIATION_ID:60072059 -> 60072059
    dfAffiliations["identifier"] = dfAffiliations["identifier"].apply(
        lambda x: x.split(":")[1]
    )


def rewrite_article_affil_list(articleAffilList):
    """Reestructura el diccionario de afiliaciones de los artículos para
    que tenga los campos adecuados y una estructura de datos más útil"""

    for articleAffildict in articleAffilList:
        articleAffildict.pop("@_fa")
        articleAffildict.pop("affiliation-url")
    return articleAffilList


def rewrite_article_authors(article_authors_list):
    """Reestructura el diccionario de autores de los artículos para
    que tenga los campos adecuados y una estructura de datos más útil"""

    for article_authorsdict in article_authors_list:
        article_authorsdict.pop("@_fa")
        article_authorsdict.pop("author-url")
        new_afid = []
        if "afid" in article_authorsdict:
            for item in article_authorsdict["afid"]:
                new_afid.append(item["$"])
            article_authorsdict["afid"] = new_afid
        else:
            article_authorsdict["afid"] = new_afid
    return article_authors_list


def recast_df_articles(df_articles):
    """Reestructura el dataframe de artículos para que tenga
    los campos adecuados y una estructura de datos más útil"""

    # Elimina los registros con affiliations igual a NaN
    df_articles.dropna(subset=["affiliation"], inplace=True)

    # Reinicia los índices del dataframe
    df_articles.reset_index(drop=True, inplace=True)

    # Elimina la columna @_fa
    df_articles.pop("@_fa")

    # Elimina la columna prism:url
    df_articles.pop("prism:url")

    # Renombra las sigueintes columnas
    df_articles.rename(
        columns={
            "dc:identifier": "identifier",
            "dc:title": "title",
            "prism:coverDate": "publication_date",
            "dc:description": "abstract",
            "author": "authors",
            "affiliation": "affiliations",
            "authkeywords": "author_keywords",
        },
        inplace=True,
    )

    # Modifica el valor de la columna affiliations.
    df_articles["affiliations"] = df_articles["affiliations"].apply(
        lambda x: rewrite_article_affil_list(x)
    )

    # Modifica el valor de la columna authors.
    df_articles["authors"] = df_articles["authors"].apply(
        lambda x: rewrite_article_authors(x)
    )

    # Modifica el valor de la columna identifier.
    df_articles["identifier"] = df_articles["identifier"].apply(
        lambda x: x.split(":")[1]
    )

    # Agrega la columna author_count que contiene el número de autores de un artículo.
    df_articles["author_count"] = df_articles["authors"].apply(lambda x: len(x))

    # Agrega la columna affiliation_count que contiene el número de afiliaciones de un artículo.
    df_articles["affiliation_count"] = df_articles["affiliations"].apply(
        lambda x: len(x)
    )


def chunker(seq, size):
    """Divide una lista en sublistas con un tamaño máximo"""

    return (seq[pos : pos + size] for pos in range(0, len(seq), size))


def recast_df_authors(df_authors):
    """Reestructura el dataframe de autores para que tenga
    los campos adecuados y una estructura de datos más útil"""

    # Agrega la columna identifier que contiene el identificador de SCOPUS de un autor.
    df_authors["identifier"] = df_authors["coredata"].apply(
        lambda x: x["dc:identifier"].split(":")[1] if "dc:identifier" in x else np.nan
    )

    # Agrega la columna identifier que contiene el electronic identifier de un autor.
    df_authors["eid"] = df_authors["coredata"].apply(
        lambda x: x["eid"] if "eid" in x else np.nan
    )

    # Agrega la columna identifier que contiene el ORCID de un autor.
    df_authors["orcid"] = df_authors["coredata"].apply(
        lambda x: x["orcid"] if "orcid" in x else np.nan
    )

    # Agrega la columna identifier que contiene el número de documentos de un autor.
    df_authors["document_count"] = df_authors["coredata"].apply(
        lambda x: x["document-count"] if "document-count" in x else np.nan
    )

    # Agrega la columna identifier que contiene el nombre de un autor.
    df_authors["first_name"] = df_authors["preferred-name"].apply(
        lambda x: x["given-name"] if type(x) is dict else np.nan
    )

    # Agrega la columna identifier que contiene el apellido de un autor.
    df_authors["last_name"] = df_authors["preferred-name"].apply(
        lambda x: x["surname"] if type(x) is dict else np.nan
    )

    # Elimina la columna @status
    df_authors.pop("@status")

    # Elimina la columna @_fa
    df_authors.pop("@_fa")

    # Elimina la columna coredata
    df_authors.pop("coredata")

    # Elimina la columna preferred-name
    df_authors.pop("preferred-name")


def authorkeywords_to_scopus_search(authorkeywords):
    new_author_keywords = ""
    for item in authorkeywords:
        if "$" in item:
            new_author_keywords = new_author_keywords + item["$"] + " | "
    return new_author_keywords[:-3]


def affiliation_to_scopus_search(affiliation):
    newAffiliation = []
    for item in affiliation:
        newAffiliation.append(
            {
                "@_fa": "true",
                "affiliation-url": item["@href"],
                "afid": item["@id"],
                "affilname": item["affilname"] if "affilname" in item else np.nan,
                "affiliation-city": (
                    item["affiliation-city"] if "affiliation-city" in item else np.nan
                ),
                "affiliation-country": item["affiliation-country"],
            }
        )
    return newAffiliation


def author_to_scopus_search(author):
    newAuthor = []
    for item in author:
        newAuthorDict = {}
        newAuthorDict["@_fa"] = "true"
        newAuthorDict["author-url"] = item["author-url"]
        newAuthorDict["authid"] = item["@auid"]
        newAuthorDict["authname"] = (
            item["ce:indexed-name"] if "ce:indexed-name" in item else np.nan
        )
        newAuthorDict["surname"] = (
            item["ce:surname"] if "ce:surname" in item else np.nan
        )
        newAuthorDict["given-name"] = (
            item["ce:given-name"] if "ce:given-name" in item else np.nan
        )
        newAuthorDict["initials"] = (
            item["ce:initials"] if "ce:initials" in item else np.nan
        )
        if "affiliation" in item:
            if type(item["affiliation"]) is list:
                newAuthorDict["afid"] = [
                    {"@_fa": "true", "$": afil["@id"]} for afil in item["affiliation"]
                ]
            else:
                newAuthorDict["afid"] = [
                    {"@_fa": "true", "$": item["affiliation"]["@id"]}
                ]
        else:
            newAuthorDict["afid"] = []
        newAuthor.append(newAuthorDict)

    return newAuthor


def article_retrieval_to_scopus_search(articleRetrieval):
    """Reestructura un artículo obtenido a través de la API abstract
    retrieval a la estructura de la API scopus search"""

    scopusSearch = {}
    """
    #@_fa
    scopusSearch['@_fa'] = 'true'
    #prism:url
    if 'prism:url' in articleRetrieval['coredata']:
        scopusSearch['prism:url'] = articleRetrieval['coredata']['prism:url']
    else:
        scopusSearch['prism:url'] = np.nan
    """
    # dc:identifier
    if "dc:identifier" in articleRetrieval["coredata"]:
        scopusSearch["dc:identifier"] = articleRetrieval["coredata"]["dc:identifier"]
    else:
        scopusSearch["dc:identifier"] = np.nan
    """
    #prism:doi
    if 'eid' in articleRetrieval['coredata']:
        scopusSearch['eid'] = articleRetrieval['coredata']['eid']
    else:
        scopusSearch['eid'] = np.nan
    #dc:title
    if 'dc:title' in articleRetrieval['coredata']:
        scopusSearch['dc:title'] = articleRetrieval['coredata']['dc:title']
    else:
        scopusSearch['dc:title'] = np.nan
    #prism:coverDate
    if 'prism:coverDate' in articleRetrieval['coredata']:
        scopusSearch['prism:coverDate'] = articleRetrieval['coredata']['prism:coverDate']
    else:
        scopusSearch['prism:coverDate'] = np.nan
    #dc:description
    if 'dc:description' in articleRetrieval['coredata']:
        scopusSearch['dc:description'] = articleRetrieval['coredata']['dc:description']
    else:
        scopusSearch['dc:description'] = np.nan
    """
    # affiliation
    if "affiliation" in articleRetrieval:
        if type(articleRetrieval["affiliation"]) is list:
            scopusSearch["affiliation"] = affiliation_to_scopus_search(
                articleRetrieval["affiliation"]
            )
        else:
            scopusSearch["affiliation"] = affiliation_to_scopus_search(
                [articleRetrieval["affiliation"]]
            )
    else:
        scopusSearch["affiliation"] = np.nan
    # author
    if "authors" in articleRetrieval:
        scopusSearch["author"] = author_to_scopus_search(
            articleRetrieval["authors"]["author"]
        )
    else:
        scopusSearch["author"] = np.nan
    """
    #authkeywords
    if 'authkeywords' in articleRetrieval:
        if articleRetrieval['authkeywords'] is not None:
            scopusSearch['authkeywords'] = authorkeywordsToScopusSearch(
                articleRetrieval['authkeywords']['author-keyword'])
        else:
            scopusSearch['authkeywords'] = np.nan
    else:
        scopusSearch['authkeywords'] = np.nan
    """

    return scopusSearch
