#!/bin/sh -e

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

/usr/local/bin/gunicorn metadataproxy:app --log-level $LEVEL --workers=2 -k gevent -b $HOST:$PORT
