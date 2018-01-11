import logging

from django.db import connections

import opentracing

log = logging.getLogger(__name__)


CURSOR_ATTR = '_jaeger_cursor'


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
    if hasattr(conn, CURSOR_ATTR):
        log.debug('already patched')
        return

    setattr(conn, CURSOR_ATTR, conn.cursor)

    def cursor():
        return TracedCursor(tracer, conn, conn._jaeger_cursor())

    conn.cursor = cursor


class TracedCursor(object):
    """
    Traced cursor
    """
    def __init__(self, tracer, conn, cursor):
        self.tracer = tracer
        self.conn = conn
        self.cursor = cursor

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
        self.tracer.service_name = self._service

        span = self.tracer.start_span(operation_name=func.__name__)
        span.set_tag(opentracing.ext.tags.DATABASE_STATEMENT, sql)
        span.set_tag(opentracing.ext.tag.DATABASE_TYPE, self._vendor)
        span.set_tag(opentracing.ext.tag.DATABASE_USER, self._alias)
        return span

    def callproc(self, procname, params=None):
        return self._trace(self.cursor.callproc, procname, params)

    def execute(self, sql, params=None):
        return self._trace(self.cursor.execute, sql, params)

    def executemany(self, sql, param_list):
        return self._trace(self.cursor.executemany, sql, param_list)

    def close(self):
        return self.cursor.close()

    def __getattr__(self, attr):
        return getattr(self.cursor, attr)

    def __iter__(self):
        return iter(self.cursor)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()
