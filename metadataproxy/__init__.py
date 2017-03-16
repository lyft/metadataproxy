import logging
import sys

from flask import Flask

from metadataproxy import settings
from logging import StreamHandler

log = logging.getLogger(__name__)
stream_handler = StreamHandler(stream=sys.stdout)
if app.config['DEBUG']:
    stream_handler.setLevel(logging.DEBUG)
else:
    stream_handler.setLevel(logging.ERROR)
    

app = Flask(__name__)
app.config.from_object(settings)
app.debug = app.config['DEBUG']
app.logger.addHandler(stream_handler)

if app.config['MOCK_API']:
    from metadataproxy.routes import mock  # NOQA
else:
    from metadataproxy.routes import proxy  # NOQA
