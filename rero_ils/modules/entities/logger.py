# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Entities logger."""

import logging
import os
from logging.config import dictConfig

from flask import current_app


def create_logger(name, file_name, log_dir=None, verbose=False):
    """Initialize the module logger.

    :param name: name of logger.
    :param file_name: log file name.
    :param logdir: logdir ro use default RERO_ILS_MEF_SYNC_LOG_DIR.
    :param verbose: verbose print.
    :returns: logger object.
    """
    # default value
    if not log_dir:
        log_dir = current_app.config.get("RERO_ILS_MEF_SYNC_LOG_DIR", os.path.join(current_app.instance_path, "logs"))
    # create the log directory if does not exists
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)
    verbose_level = ["ERROR", "INFO", "DEBUG"]
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {"standard": {"format": "%(asctime)s [%(levelname)s] :: %(message)s"}},
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "level": verbose_level[min(verbose, 2)],
            },
            "file": {
                "class": "logging.handlers.TimedRotatingFileHandler",
                "filename": os.path.join(log_dir, file_name),
                "when": "D",
                "interval": 7,
                "backupCount": 10,
                "formatter": "standard",
            },
        },
        "loggers": {name: {"handlers": ["console", "file"], "level": "INFO", "propagate": False}},
    }
    dictConfig(logging_config)
    return logging.getLogger(name)
