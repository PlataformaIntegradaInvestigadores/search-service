from apps.dashboards.application.services.populate_service import PopulateService


class PopulateUseCase:
    def __init__(self, populate_service: PopulateService):
        self.populate_service = populate_service

    def execute(self):
        return self.populate_service.populate()
