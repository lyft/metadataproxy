# -*- coding: utf-8 -*-
"""
log:
    Encapsulates all of the log setup for seatgeek default loggers.

    Environment Variables:
        LOGGING_VERBOSE: Should run logger in verbose mode, which outputs
            logger.debug() messages. Default = False.

    Interface:
        from metadataproxy import log
        logger = log.get_logger("my.logger")
        logger.info("Hi There)
        >> [2012-11-12 15:05:22] my.logger - INFO - Hi There
"""
import datetime
import os
import sys
import logging
import logging.config


# log settings for root logger by default
LOG_SETTINGS = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'normal': {
            'format': "[%(asctime)s +0000] [%(process)d] [%(levelname)s] [name:%(name)s] %(message)s",
            'datefmt': "%Y-%m-%d %H:%M:%S"
        },
        'werkzeug': {
            'format': "[%(asctime)s +0000] [%(process)d] [%(levelname)s] [name:%(name)s] %(message)s",
            'datefmt': "%Y-%m-%d %H:%M:%S"
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'normal',
            'stream': 'ext://sys.stdout'
        },
        'console_werkzeug': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'werkzeug',
            'stream': 'ext://sys.stdout'
        },
        'error': {
            'level': 'ERROR',
            'class': 'logging.StreamHandler',
            'formatter': 'normal',
            'stream': 'ext://sys.stderr'
        },
    },
    'loggers': {
        'sqlalchemy.engine': {
            'level': os.getenv('SQLALCHEMY_ENGINE_LOGGER_LEVEL' 'INFO'),
            'propagate': True,
        },
        'werkzeug': {
            'handlers': ['console_werkzeug'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
    'root': {
        'level': 'NOTSET',
        'handlers': ['console', 'error']
    },
}

normal_formatter = logging.Formatter(
    fmt=LOG_SETTINGS['formatters']['normal']['format'],
    datefmt=LOG_SETTINGS['formatters']['normal']['datefmt'])

werkzeug_formatter = logging.Formatter(
    fmt=LOG_SETTINGS['formatters']['werkzeug']['format'],
    datefmt=LOG_SETTINGS['formatters']['werkzeug']['datefmt'])

werkzeug_stream_handler = logging.StreamHandler(sys.stdout)
werkzeug_stream_handler.setFormatter(werkzeug_formatter)

werkzeug_error_stream_handler = logging.StreamHandler(sys.stderr)
werkzeug_error_stream_handler.setFormatter(werkzeug_formatter)
werkzeug_error_stream_handler.setLevel(logging.ERROR)

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(normal_formatter)

error_stream_handler = logging.StreamHandler(sys.stderr)
error_stream_handler.setFormatter(normal_formatter)
error_stream_handler.setLevel(logging.ERROR)

# environment flags we should honor
BUGSNAG_API_KEY = os.getenv('BUGSNAG_API_KEY', None)
SENTRY_DSN = os.getenv('SENTRY_DSN', None)

logging.config.dictConfig(LOG_SETTINGS)

if BUGSNAG_API_KEY:
    import bugsnag

if SENTRY_DSN:
    from raven.conf import setup_logging
    from raven.handlers.logging import SentryHandler
    assert setup_logging


def _configure_error_handler():
    handler = None
    if BUGSNAG_API_KEY:
        client = bugsnag.Client(api_key=BUGSNAG_API_KEY)
        handler = client.log_handler()
        handler.setLevel(logging.ERROR)

    if SENTRY_DSN:
        handler = SentryHandler(SENTRY_DSN)
        handler.setLevel(logging.ERROR)
    return handler


def get_logger(name, loglevel=None):
    """
    returns a python logger object configured according to seatgeek's standards

    Args:
        loglevel: a log level
    """
    logger = logging.getLogger(name)

    # just in case that was not a new logger, get rid of all the handlers
    # already attached to it.
    del logger.handlers[:]

    if not loglevel:
        loglevel = logging.INFO

    logger.setLevel(loglevel)
    if name == 'werkzeug':
        logger.addHandler(werkzeug_stream_handler)
        logger.addHandler(werkzeug_error_stream_handler)
    else:
        logger.addHandler(stream_handler)
        logger.addHandler(error_stream_handler)

    logger.propagate = False
    error_handler = _configure_error_handler()
    if error_handler:
        logger.addHandler(error_handler)

    return logger


def log_request(request, response, logger=None):
    server_software = request.environ.get('SERVER_SOFTWARE')
    if logger is None or 'gunicorn' not in server_software:
        return

    now = datetime.datetime.utcnow()
    message = '{0} - - [{1}] "{2} {3} {4}" {5} -'
    logger.info(message.format(
        request.environ.get("REMOTE_ADDR"),
        now.strftime("%d/%b/%Y:%H:%M:%S"),
        request.method,
        request.path,
        request.environ.get("SERVER_PROTOCOL"),
        response.status_code,
    ))
