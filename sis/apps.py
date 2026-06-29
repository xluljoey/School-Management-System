from django.apps import AppConfig


class SisConfig(AppConfig):
    name = 'sis'

    def ready(self):
        import sis.signals
