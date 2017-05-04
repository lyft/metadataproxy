# -*- coding: utf-8 -*-
import os
from flask import Flask

config_file = os.getenv('NEW_RELIC_CONFIG_FILE', None)
if config_file:
    import newrelic.agent
    newrelic.agent.initialize(config_file)


def make_application():
    from metadataproxy.settings import Settings

    flask_app = Flask(__name__, static_url_path='')

    if Settings.BUGSNAG_API_KEY:
        import bugsnag
        from bugsnag.flask import handle_exceptions
        bugsnag.configure(api_key=Settings.BUGSNAG_API_KEY)
        handle_exceptions(flask_app)
    elif Settings.SENTRY_DSN:
        from raven.contrib.flask import Sentry
        sentry = Sentry()
        sentry.init_app(flask_app, dsn=Settings.SENTRY_DSN)

    flask_app.config.from_object('metadataproxy.settings.Settings')
    flask_app.debug = Settings.DEBUG

    if flask_app.config['MOCK_API']:
        import metadataproxy.routes.mock
        flask_app.register_blueprint(metadataproxy.routes.mock.blueprint_http)
        metadataproxy.routes.mock.blueprint_http.config = flask_app.config
    else:
        import metadataproxy.routes.proxy
        flask_app.register_blueprint(metadataproxy.routes.proxy.blueprint_http)
        metadataproxy.routes.proxy.blueprint_http.config = flask_app.config

    return flask_app
