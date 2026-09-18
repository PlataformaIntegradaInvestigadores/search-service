from abc import ABC, abstractmethod


class PopulateRepository(ABC):
    @abstractmethod
    def populate_author(self):
        pass

    @abstractmethod
    def populate_country(self):
        pass

    @abstractmethod
    def get_country_articles_topics_dict(self):
        pass

    @abstractmethod
    def get_country_authors_dict(self):
        pass

    @abstractmethod
    def get_country_affiliations_dict(self):
        pass

    @abstractmethod
    def drop_database(self):
        pass

    @abstractmethod
    def populate_affiliation(self):
        pass

    @abstractmethod
    def get_affiliations_articles_dict(self):
        pass

    @abstractmethod
    def get_affiliations_authors_dict(self):
        pass

    @abstractmethod
    def get_affiliations_topics_dict(self):
        pass

    @abstractmethod
    def get_affiliations_dict(self):
        pass

    @abstractmethod
    def get_provinces_dict(self):
        pass

    @abstractmethod
    def populate_province(self):
        pass

    @abstractmethod
    def get_authors_dict(self):
        pass
