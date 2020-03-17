#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging


class LogLevelFilter(logging.Filter):

    def __init__(self, name='', level=logging.DEBUG):
        super(LogLevelFilter, self).__init__(name)
        self.level = level

    def filter(self, record):
        return record.levelno == self.level


# create logger
format = '%(asctime)s - %(threadName)s - %(levelname)s - %(message)s'
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

fh_info = logging.FileHandler('spider.log')
fh_info.setLevel(logging.INFO)
fh_info.setFormatter(logging.Formatter(format))

fh_error = logging.FileHandler('spider_error.log')
fh_error.setLevel(logging.ERROR)
fh_error.setFormatter(logging.Formatter(format))

filter_info = LogLevelFilter(level=logging.INFO)
filter_error = LogLevelFilter(level=logging.ERROR)

fh_info.addFilter(filter_info)
fh_error.addFilter(filter_error)

logger.addHandler(fh_info)
logger.addHandler(fh_error)
