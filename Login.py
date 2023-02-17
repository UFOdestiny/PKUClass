# -*- coding: utf-8 -*-
# @Name     : Login.py
# @Date     : 2023/2/17 20:31
# @Auth     : Yu Dahai
# @Email    : yudahai@pku.edu.cn
# @Desc     :
import random

import requests
from requests.utils import dict_from_cookiejar

from Const import Const
from Logger import Logger
from Network import Network
from lxml.etree import HTML


class Login(Network):
    def __init__(self, print_table_flag=True):
        super().__init__()
        self.table_header = None
        self.action = None
        self.result = None
        self.token = None
        self.raw_pages = []
        self.print_table_flag = print_table_flag

        self.logger = Logger(file_name=f"{Const.pid}", mode="all")

    def login_portal(self):
        """
        获取token
        :return:
        """
        data = {'appid': 'syllabus',  # 选课网
                'userName': Const.username,
                'password': Const.password,
                'randCode': "",
                'smsCode': "",
                'otpCode': "",
                'redirUrl': Const.redirUrl, }

        resp_json = self.post(Const.auth_url, data=data)
        self.token = resp_json.get('token')

    def login_elective(self):
        sso_login = self.get(Const.ssoLogin,
                             params={'_rand': random.random(), 'token': self.token},
                             allow_redirects=False)

        Const.cookie = {"Hm_lvt_c7896bb34c3be32ea17322b5412545c0": "1661775435",
                        "JSESSIONID": dict_from_cookiejar(sso_login.cookies)["JSESSIONID"]}

        self.get(Const.HelpController, allow_redirects=False)

        Const.cookie["route"] = dict_from_cookiejar(Const.session.cookies)["route"]

        # 删除session
        Const.session = None
        self.logger.info(f"pid:{Const.pid} 登陆成功！")
        # print(f"pid:{Const.pid} 登陆成功！")

    def get_SupplyCancel(self):
        """
        补退选页面
        :return:
        """
        resp = self.get(Const.SupplyCancel_url, params={"xh": Const.username},
                        headers=Const.SupplyCancel_header, )
        self.raw_pages = [resp.text]

    def get_supplement(self, limit=100):
        """
        多页面
        :param limit: 限制页数
        :return:
        """
        x_page_total = "(//tr[@align='right'])[1]/td[1]/text()[1]"
        page_total = HTML(self.raw_pages[0]).xpath(x_page_total)

        page_total_number = int(page_total[0].split()[3])

        if page_total_number > 1:
            for page_number in range(2, min(page_total_number + 1, limit + 1)):
                raw_page = self.get(Const.supplement,
                                    params={'netui_row': f'electableListGrid;{20 * (page_number - 1)}'},
                                    headers=Const.s_h,
                                    )
                self.raw_pages.append(raw_page.text)

    def table(self):
        """
        表格信息抽取
        :return:
        """
        self.result = [[] for _ in range(11)]
        self.action = []

        for raw_page in self.raw_pages:
            x_table_all = "(//table[@class='datagrid'])[1]//*[@class='datagrid']"
            table = HTML(raw_page).xpath(x_table_all)

            if not self.table_header:
                self.table_header = [i.text for i in table[:11]]

            for i in range(11, len(table)):
                position = i % 11
                if position == 0:
                    a = [j for j in table[i]][0]
                    self.result[position].append([i for i in a][0].text)
                elif position != 10:
                    content = table[i][0].text
                    if content is None:  # 可能有空
                        content = "空"
                    self.result[position].append(content)
                else:
                    a = [j for j in table[i]][0]
                    self.result[position].append([i for i in a][0].text)
                    self.action.append(a.attrib['href'])

    def print_table(self):
        """
        控制台打印表格
        :return:
        """
        # ["课程名","课程类别","学分","周学时","教师","班号","开课单位","年级","上课/考试信息","限选/已选","补选"]
        fmt = "{0:<1}\t{1:{5}<8}\t{2:{5}<10}\t{3:{5}<5}\t{4}"
        length = len(self.result[0])

        print(fmt.format("序号", self.table_header[0], self.table_header[4], self.table_header[-2], self.table_header[-1],
                         " "))
        # chr(12288)
        # print(f"序号 {self.table_header[0]} {self.table_header[4]} {self.table_header[-2]} {self.table_header[-1]}")
        for i in range(length):
            # print(f"{i} {self.result[0][i]} {self.result[4][i]} {self.result[-2][i]} {self.result[-1][i]}")
            print(fmt.format(i, self.result[0][i], self.result[4][i], self.result[-2][i], self.result[-1][i],
                             chr(12288)))

    def initialize(self):
        self.get_SupplyCancel()

        self.re_login()

        self.get_supplement()
        self.table()

        if self.print_table_flag:
            self.print_table()

        return self.result, self.action

    def re_login(self):
        wrong = False
        if "目前是跨院系选课数据准备时间" in self.raw_pages[0]:
            self.logger.info(f"pid:{Const.pid} 目前是跨院系选课数据准备时间！")
            # print(f"pid:{Const.pid} 目前是跨院系选课数据准备时间！")
            wrong = True
        elif "您尚未登录或者会话超时" in self.raw_pages[0]:
            self.logger.info(f"pid:{Const.pid} 会话超时！重试！")
            # print(f"pid:{Const.pid} 会话超时！重试！")
            wrong = True

        if wrong:
            Const.session = requests.session()
            self.login_portal()
            self.login_elective()
            self.get_SupplyCancel()
            self.re_login()

    def run(self):
        self.login_portal()
        self.login_elective()

        return self.initialize()
