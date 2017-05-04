FROM python:2.7.11
COPY requirements.txt /srv/metadataproxy/
COPY requirements_wsgi.txt /srv/metadataproxy/

RUN pip --no-cache-dir install -r /srv/metadataproxy/requirements.txt && \
    pip --no-cache-dir install -r /srv/metadataproxy/requirements_wsgi.txt

COPY . /srv/metadataproxy/

EXPOSE 8000
VOLUME ["/var/run/docker.sock"]

WORKDIR /srv/metadataproxy
CMD ["/bin/sh", "run-server.sh"]
