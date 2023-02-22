# -*- coding: utf-8 -*-
# @Name     : Elective.py
# @Date     : 2023/2/22 13:57
# @Auth     : Yu Dahai
# @Email    : yudahai@pku.edu.cn
# @Desc     :
import random
import time

from lxml.etree import HTML

from config import CaptchaSetting
from module.Captcha import TuJian
from module.Const import Const
from module.Email import QQMail
from module.Logger import Logger
from module.Login import Login
from module.Network import Network


class Elective(Network):
    def __init__(self, course_name=None, auto_mode=False, auto_verify=False):
        super().__init__()

        self.fresh = False
        self.auto_mode = auto_mode

        self.auto_verify = auto_verify
        if self.auto_verify:
            self.verifier = TuJian()

        self.course_name = course_name
        self.index = None
        self.end = False

        self.result = None
        self.action = None

        self.cache = None
        self.elective_initialize()

        self.logger = Logger(file_name=f"{Const.pid}", mode="all")

    def elective_initialize(self):
        login = Login(print_table_flag=not self.auto_mode)
        self.result, self.action = login.run()
        self.cache = login

    def re_initialize(self):
        self.result, self.action = self.cache.initialize()

    def manipulate(self, index: int, link: str, action: str):
        """
        进行操作
        :param action:
        :param link:
        :param index:
        :return:
        """
        action_link = Const.domain + link

        if action == "刷新":
            self.fresh = True

        while self.fresh:
            self.refresh(index)

        self.get_verify(index)
        self.select(action_link)

    def manual(self):
        """
        手动输入
        :return:
        """
        while True:
            self.index = int(input())
            self.course_name = self.result[0][self.index]

            self.manipulate(index=self.index,
                            link=self.action[self.index],
                            action=self.result[-1][self.index])

    def get_verify(self, index, retry=10):
        """
        获取验证码
        :param retry:
        :param index:
        :return:
        """
        if retry == 0:
            raise Exception("验证码识别出现了问题！")

        rand = 10000 * random.random()
        resp = self.get(Const.verify_image, params={"Rand": rand},
                        headers=Const.s_h)

        if self.course_name is None:
            path = f"{CaptchaSetting.path}/{Const.pid}-{index}.png"
        else:
            path = f"{CaptchaSetting.path}/{Const.pid}-{self.course_name}.png"

        with open(path, 'wb') as file:
            file.write(resp.content)

        if self.auto_verify:
            code = self.verifier.check(path)
            # print(f"pid:{Const.pid} 验证码自动预测为：{code}")

        else:
            code = input("输入验证码:")

        post = self.post(url=Const.validate,
                         data={"xh": Const.username, "validCode": code},
                         headers=Const.s_h)

        if post["valid"] == '2':
            # print(f"pid:{Const.pid} 验证码正确！")
            pass
        else:
            if self.auto_verify:
                msg = f"pid:{Const.pid} 自动识别验证码错误，正在重试！"
            else:
                msg = f"pid:{Const.pid} 验证码错误，重新输入:\n"
            self.logger.info(msg)
            self.get_verify(index, retry - 1)

    def select(self, link):
        """
        补选
        :param link:
        :return:
        """

        resp = self.get(link, headers=Const.s_h)

        xpath = "(//*[@id='msgTips'])[1]//text()"
        msgs = HTML(resp.text).xpath(xpath)
        msg = [i.strip() for i in msgs if len(i.strip()) > 2][0]

        if "该课程在补退选阶段开始后的约一周开放选课" in msg:
            msg = "跨院系选课尚未开放！"

        self.logger.info(f"pid:{Const.pid} {self.course_name} {msg}")
        # print(f"pid:{Const.pid} {self.course_name} {msg}")
        if "成功" in msg:
            self.end = True

    def refresh(self, index):
        """
        刷新
        :param index:
        :return:
        """
        if not index:
            index = self.index
        url = Const.domain + self.action[index]
        parse = url.split('?')[1].split('&')
        data = {
            "index": f"{parse[0].split('=')[1]}",
            "xh": f"{Const.username}",
            "seq": f"{parse[2].split('=')[1]}",
        }
        start = 20 * int(data["index"]) // 20
        resp = self.post(Const.refresh_limit, data=data,
                         headers={"Referer": Const.supplement + f"?netui_row=electableListGrid%3B{start}"})

        if 'electedNum' in resp and 'limitNum' in resp:
            if resp['electedNum'] == resp['limitNum']:
                self.logger.info(f"pid:{Const.pid} {self.course_name} 没有空余名额！")
                # print(f"pid:{Const.pid} {self.course_name} 没有空余名额！")
                self.fresh = True
                time.sleep(3)
            else:
                self.logger.info(f"pid:{Const.pid} {self.course_name} 有空余名额！")
                # print(f"pid:{Const.pid} {self.course_name} 有空余名额！")
                self.fresh = False
        else:
            self.logger.info(f"pid:{Const.pid} {self.course_name} 出现错误！")
            # print(f"pid:{Const.pid} {self.course_name} 出现错误！")
            self.fresh = True
            time.sleep(3)

    def locate(self):
        """
        定位
        :return:
        """
        for index in range(len(self.result[0])):
            if self.result[0][index] == self.course_name:
                self.manipulate(index=index, link=self.action[index], action=self.result[-1][index])

                if not self.end:
                    self.re_initialize()
                    self.locate()
                else:
                    if Const.username[0] == 1:
                        suffix = "pku.edu.cn"
                    else:
                        suffix = "stu.pku.edu.cn"
                    email = QQMail()  # [f"{Const.username}@{suffix}"]
                    email.send(f"{self.course_name} 选课成功！")
                    self.logger.info(f"{self.course_name} 选课成功！")

    def run(self):
        if self.auto_mode:
            self.locate()
        else:
            self.manual()
