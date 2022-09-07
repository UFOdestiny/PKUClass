#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# @Name     : Logger.py
# @Date     : 2022/9/2 10:45
# @Auth     : UFOdestiny
# @Desc     : logger

import logging

from logging.handlers import TimedRotatingFileHandler
from logging.handlers import RotatingFileHandler
from Config import LogSetting


class Singleton(type):
    def __call__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            cls._instance = type.__call__(cls, *args, **kwargs)
        return cls._instance


class Logger(LogSetting, metaclass=Singleton):
    def __init__(self, file_name="my", mode="all"):
        self.LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
        self.logger = logging.getLogger(name=file_name)
        self.logger.setLevel(logging.DEBUG)

        self.file_name = f"{self.path}/{file_name}.log"

        if mode == "console":
            self.stand_mode()
        elif mode == "file":
            self.file_mode()
        else:
            self.stand_mode()
            self.file_mode()

    def debug(self, msg):
        self.logger.debug(msg)

    def info(self, msg):
        self.logger.info(msg)

    def warning(self, msg):
        self.logger.warning(msg)

    def error(self, msg):
        self.logger.error(msg)

    def exception(self, e):
        self.logger.exception(e)

    def stand_mode(self):
        stand_handler = logging.StreamHandler()
        stand_handler.setLevel(logging.DEBUG)
        stand_handler.setFormatter(logging.Formatter(self.LOG_FORMAT))
        self.logger.addHandler(stand_handler)

    def file_mode(self, mode="Rotating"):
        if mode == "Rotating":  # 输出到文件
            file_handler = RotatingFileHandler(filename=self.file_name, maxBytes=1048576 * 1,
                                               backupCount=10,
                                               encoding='utf-8')

        else:  # 按时间输出
            file_handler = TimedRotatingFileHandler(filename="log/my.log", when="D", interval=7, backupCount=10,
                                                    encoding='utf-8')

        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(self.LOG_FORMAT))
        self.logger.addHandler(file_handler)


if __name__ == '__main__':
    log = Logger()
    log.debug("debug msg")
    log.info("info msg")
    log.warning("warning msg")
    log.error("error msg")

    log = Logger()
    log.info("next")
