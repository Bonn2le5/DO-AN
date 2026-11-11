from django.apps import AppConfig


class ApiConfig(AppConfig):
    name = "api"

    def ready(self):
        from .van_hanh import ket_noi_signal
        ket_noi_signal()
