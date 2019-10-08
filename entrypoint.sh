#!/bin/bash
set -e

export DOCKER_URL="unix://var/run/docker_sockets/docker.sock"

if [ ! -z "$DEVBOX" ]; then
  export MOCK_API="true"
  export MOCKED_INSTANCE_ID="onebox"
  export RELOAD="true"
  export RELOAD_EXTRA_FILES="/root/.aws/credentials"
fi
exec gunicorn wsgi:app --bind 0.0.0.0:45001 -c /etc/gunicorn/gunicorn.conf --access-logfile - --error-logfile - --log-file -
