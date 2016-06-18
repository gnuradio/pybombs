#!/usr/bin/env python
#
# Copyright 2015 Free Software Foundation, Inc.
#
# This file is part of PyBOMBS
#
# PyBOMBS is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# PyBOMBS is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PyBOMBS; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.
#
"""
Logging interface: Creates a logger object for use in PyBOMBS commands
"""

import logging
from logging import CRITICAL, ERROR, WARNING, INFO, DEBUG
import copy

BOLD = str('\033[1m')
OBNOXIOUS = 1

class ColoredConsoleHandler(logging.StreamHandler):
    def emit(self, record):
        # Need to make a actual copy of the record
        # to prevent altering the message for other loggers
        myrecord = copy.copy(record)
        levelno = myrecord.levelno
        if levelno >= 50:  # CRITICAL / FATAL
            color = '\x1b[31m'  # red
        elif levelno >= 40:  # ERROR
            color = '\x1b[31m'  # red
        elif levelno >= 30:  # WARNING
            color = '\x1b[33m'  # yellow
        elif levelno >= 20:  # INFO
            color = '\x1b[32m'  # green
        elif levelno >= 10:  # DEBUG
            color = '\x1b[35m'  # pink
        elif levelno >= 1:  # OBNOXIOUS
            color = '\x1b[90m'  # grey
        else:  # NOTSET and anything else
            color = '\x1b[0m'  # normal
        myrecord.msg = BOLD + color + str(myrecord.msg) + '\x1b[0m'  # normal
        logging.StreamHandler.emit(self, myrecord)

class PBLogger(logging.getLoggerClass()):
    def __init__(self, *args, **kwargs):
        logging.Logger.__init__(self, *args, **kwargs)

    def obnoxious(self, *args, **kwargs):
        """ Extends logging for super-high verbosity """
        self.log(OBNOXIOUS, *args, **kwargs)


logging.addLevelName(OBNOXIOUS, 'OBNOXIOUS')
logging.setLoggerClass(PBLogger)
logger = logging.getLogger('PyBOMBS')
ch = ColoredConsoleHandler()
formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)
# Set default level:
default_log_level = INFO
logger.setLevel(default_log_level)

if __name__ == "__main__":
    print("Testing logger: ")
    logger.setLevel(1)
    logger.obnoxious("super-verbose message")
    logger.debug("debug message")
    logger.info("info message")
    logger.warning("warning message")
    logger.error("error message")
    logger.critical("critical message")

