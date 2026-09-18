from django_neomodel import admin as neo_admin

from apps.search_engine.domain.entities.affiliation import Affiliation
from apps.search_engine.domain.entities.article import Article
from apps.search_engine.domain.entities.author import Author
from apps.search_engine.domain.entities.topic import Topic

# Register your models here.


class AuthorAdmin(neo_admin.admin.ModelAdmin):
    list_display = ("first_name", "last_name", "auth_name", "initials")


class AffiliationAdmin(neo_admin.admin.ModelAdmin):
    list_display = ("scopus_id", "name", "city", "country")
    search_fields = ("name", "city", "country")


class TopicAdmin(neo_admin.admin.ModelAdmin):
    list_display = ("name",)


class ArticleAdmin(neo_admin.admin.ModelAdmin):
    list_display = (
        "title",
        "abstract",
        "doi",
        "publication_date",
        "author_count",
        "affiliation_count",
        "corpus",
    )


neo_admin.register(Affiliation, AffiliationAdmin)
neo_admin.register(Topic, TopicAdmin)
neo_admin.register(Article, ArticleAdmin)
neo_admin.register(Author, AuthorAdmin)
