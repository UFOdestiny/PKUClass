#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Name     : main.py
# @Date     : 2022/9/6 10:33
# @Auth     : UFOdestiny
# @Desc     :

import os
import sys
import time
from multiprocessing import Process

# 去除代理
from module.Elective import Elective

os.environ['no_proxy'] = '*'


def select(course_name=None, auto_mode=True, auto_verify=True):
    """
    :param auto_verify:
    :param auto_mode:
    :param course_name: 课程名
    :return:
    """
    Elective(course_name=course_name,
             auto_mode=auto_mode,
             auto_verify=auto_verify, ).run()


def multiprocess(name_list, auto_mode=True, auto_verify=True):
    """
    :param name_list:
    :param auto_mode:
    :param auto_verify:
    :return:
    """
    stat_time = time.time()
    process_list = []
    if len(sys.argv) >= 4:
        name_list = sys.argv[3:]

    for name in name_list:
        p = Process(target=select, args=(name, auto_mode, auto_verify))
        p.start()
        process_list.append(p)

    for p in process_list:
        p.join()

    print(f"total time:{time.time() - stat_time}")


if __name__ == "__main__":
    # names = ["实用英语：从听说到演讲"]
    names = ["论证性论文写作", "互联网认知", "现代电子与通信导论", ]
    multiprocess(names, auto_mode=True, auto_verify=True)
    # select(auto_mode=False, auto_verify=True)
