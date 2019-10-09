FROM python:2.7.11

RUN mkdir /srv/metadataproxy
COPY requirements.txt requirements_wsgi.txt /srv/metadataproxy/
RUN pip --no-cache-dir install -r /srv/metadataproxy/requirements.txt && \
    pip --no-cache-dir install -r /srv/metadataproxy/requirements_wsgi.txt

RUN mkdir -p /etc/gunicorn /etc/metadataproxy
COPY config/gunicorn.conf /etc/gunicorn/gunicorn.conf
COPY config/logging.conf /etc/metadataproxy/logging.conf

COPY . /srv/metadataproxy/

EXPOSE 8000
VOLUME ["/var/run/docker.sock"]

WORKDIR /srv/metadataproxy
CMD ["/bin/sh", "run-server.sh"]
