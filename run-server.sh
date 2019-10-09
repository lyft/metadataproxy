#!/bin/sh -e

if [ "z$GUNICORN_CONFIG" = "z" ]; then
    GUNICORN_CONFIG="/etc/gunicorn/gunicorn.conf"
fi

if [ "z$HOST" = "z" ]; then
    HOST="0.0.0.0"
fi

if [ "z$PORT" = "z" ]; then
    PORT=8000
fi

if [ "$DEBUG" = "True" ]; then
    LEVEL="debug"
else
    LEVEL="warning"
fi

if [ "z$WORKERS" = "z" ]; then
    WORKERS="1"
fi

export PYTHONUNBUFFERED="true"

/usr/local/bin/gunicorn metadataproxy:app -c $GUNICORN_CONFIG --log-level $LEVEL --workers=$WORKERS -k gevent -b $HOST:$PORT --access-logfile - --error-logfile - --log-file -
