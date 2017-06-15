# coding=utf-8
#
# -------------------------------------------------------------------------
# Copyright 2014-2015 T2T Inc. All rights reserved.
#
# FILE:
#     logger.py
#
# DESCRIPTION:
#     Logging service for T-T-T
#
#
# REVISION HISTORY
#     2017/02/03, yagamy, initial version.
#
#
# -------------------------------------------------------------------------

from collections import OrderedDict, Counter
import colorama
from colorama import Fore, Back, Style
import time
from datetime import datetime


class Logger:
    def __init__(self, verbose, milliseconds=False):
        self._verbose = verbose
        self._milliseconds = milliseconds
        return

    def output(self, msg, level, color):
        now = datetime.now()
        mss = now.strftime('%f')[:-3]
        now = now.strftime('%b/%d %H:%M:%S')
        now = "%s.%s%s%s" % (now, Fore.RED, mss, Style.RESET_ALL) if self._milliseconds else now
        line = "%s [%s%s%s]: %s" % (now, color, level, Style.RESET_ALL, msg)
        print(line)

    def debug(self, msg):
        if self._verbose:
            return self.output(msg, "DBG", Fore.BLUE)

    def info(self, msg):
        return self.output(msg, "INF", Fore.GREEN)

    def warn(self, msg):
        return self.output(msg, "WRN", Fore.YELLOW)

    def error(self, msg):
        return self.output(msg, "ERR", Fore.RED)

