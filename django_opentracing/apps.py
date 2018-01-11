
from django.apps import AppConfig

class DjangoOpenTracingConfig(AppConfig):
    name = 'django_opentracing'
    def ready(self):
        pass