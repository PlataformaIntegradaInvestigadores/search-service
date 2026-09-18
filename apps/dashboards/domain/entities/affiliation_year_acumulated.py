from mongoengine import Document, fields


class AffiliationAcumulated(Document):
    scopus_id = fields.IntField()
    name = fields.StringField()
    year = fields.IntField()
    total_articles = fields.IntField()
    total_topics = fields.IntField()
