from apps.dashboards.application.services.province_service import ProvinceService


class ProvincesYearUseCase:
    def __init__(self, province_service: ProvinceService):
        self.province_service = province_service

    def execute(self, year):
        return self.province_service.get_provinces_year(year=year)
