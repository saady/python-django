from .middleware import OpenTracingMiddleware
from .tracer import DjangoTracer
from ._version import get_versions
__version__ = get_versions()['version']
del get_versions


default_app_config = 'django_opentracing.apps.DjangoOpenTracingConfig'
