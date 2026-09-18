from abc import ABC, abstractmethod


class AffiliationRepository(ABC):
    @abstractmethod
    def get_top_affiliations(self):
        pass

    @abstractmethod
    def get_affiliation(self, scopus_id):
        pass

    @abstractmethod
    def get_top_affiliations_acumulated(self, year):
        pass

    @abstractmethod
    def get_affiliations_by_year(self, year):
        pass

    @abstractmethod
    def get_affiliation_year(self, scopus_id, year):
        pass

    @abstractmethod
    def get_affiliation_year_acumulated(self, scopus_id, year):
        pass

    @abstractmethod
    def get_affiliation_topic(self, scopus_id, year):
        pass

    @abstractmethod
    def get_affiliation_topics_acumulated(self, scopus_id, year):
        pass

    @abstractmethod
    def get_last_years(self, scopus_id):
        pass
