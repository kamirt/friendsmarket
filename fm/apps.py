from django.apps import AppConfig


class FmConfig(AppConfig):
    name = 'fm'

    def ready(self):
        import fm.signals
