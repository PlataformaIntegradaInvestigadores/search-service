from apps.dashboards.domain.entities.province import Province
from apps.dashboards.domain.entities.province_acumulated import ProvinceAcumulated
from apps.dashboards.domain.entities.province_year import ProvinceYear
from apps.dashboards.domain.repositories.province_repository import ProvinceRepository


class ProvinceService(ProvinceRepository):
    def get_provinces_acumulated(self, year):
        return ProvinceAcumulated.objects(year=year).filter(
            province_name__ne="Pendiente"
        )

    def get_provinces_info(self):
        return Province.objects().filter(province_name__ne="Pendiente")

    def get_province_year(self, name, year):
        pass

    def get_province_acumulated(self, name, year):
        pass

    def get_provinces_year(self, year):
        return ProvinceYear.objects(year=year).filter(province_name__ne="Pendiente")

    def get_province_topic_year(self, year):
        pass

    def get_province_topic_acumulated(self, year):
        pass
