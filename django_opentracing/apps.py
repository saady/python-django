
from django.apps import AppConfig
from .db import patch_db
 
def tracer():
    from jaeger_client import Config
    config = Config(
        config={ # usually read from some yaml config
            'sampler': {
                'type': 'const',
                'param': 1,
            },
            'logging': True,
            'metrics': True,
            'enabled': True
        },
        service_name='SERVICE_NAME')
    return config.initialize_tracer()

TRACER = tracer()

class DjangoOpenTracingConfig(AppConfig):
    name = 'django_opentracing'
    def ready(self):
        patch_db(TRACER)
