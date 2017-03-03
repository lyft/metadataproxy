#!/bin/sh -e

if [ -z "$HOST" ]; then
    HOST="0.0.0.0"
fi

if [ -z "$PORT" ]; then
    PORT=8000
fi

if [ "$DEBUG" = "True" ]; then
    LEVEL="debug"
else
    LEVEL="warning"
fi

if [ -z "$WORKERS" ]; then
    WORKERS="1"
fi

/usr/local/bin/gunicorn metadataproxy:app --log-level ${LEVEL} --workers=${WORKERS} -k gevent -b ${HOST}:${PORT} --access-logfile=- --error-logfile=-
