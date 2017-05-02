from gunicorn.glogging import Logger as GunicornLogger


class Logger(GunicornLogger):
    error_fmt = r"[%(asctime)s +0000] %(name)s [pid:%(process)d] - %(levelname)s - %(message)s"
    datefmt = r"%Y-%m-%d %H:%M:%S"

    access_fmt = "%(message)s"
    syslog_fmt = "[%(process)d] %(message)s"
