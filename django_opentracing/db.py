from django.db import connections

import opentracing


def patch_db(tracer):
    """
    patch database
    """
    for c in connections.all():
        patch_conn(tracer, c)


def patch_conn(tracer, conn):
    """
    Patch connection
    """
    def cursor():
        return TracedCursor(tracer, conn)

    conn.cursor = cursor


class TracedCursor(object):
    """
    Traced cursor
    """
    def __init__(self, tracer, conn):
        self.tracer = tracer
        self.conn = conn

        self._vendor = getattr(conn, 'vendor', 'db') # mysql
        self._alias = getattr(conn, 'alias', 'default') # default, users

        prefix = self._vendor
        self._name = "%s.%s" % (prefix, "query")

        self._service = "{}{}".format(
            self._alias,
            "db"
        )
        
    def _trace(self, func, sql, params):
        span = None
        try:
            span_ctx = self.tracer.extract(opentracing.Format.HTTP_HEADERS, params)
            span = self.tracer.start_span(func.__name__, child_of=span_ctx)

        except (opentracing.InvalidCarrierException, opentracing.SpanContextCorruptedException):
            span = self.tracer.start_span(func.__name__)

        span.set_tag(opentracing.ext.tags.DATABASE_STATEMENT, sql)
        span.set_tag(opentracing.ext.tag.DATABASE_TYPE, self._vendor)
        span.set_tag(opentracing.ext.tag.DATABASE_USER, self._alias)
        return span
