#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Name     : PKUClass.py
# @Date     : 2022/9/6 10:33
# @Auth     : UFOdestiny
# @Desc     :

import os
import random
import time
from multiprocessing import Process

import requests
from lxml.etree import HTML
from requests.utils import dict_from_cookiejar

from Config import User as User
from Verify import TuJian

# 去除代理
os.environ['no_proxy'] = '*'


class Const:
    headers = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X)"
                             " AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1", }

    auth_url = 'https://iaaa.pku.edu.cn/iaaa/oauthlogin.do'

    domain = "https://elective.pku.edu.cn/"

    redirUrl = "http://elective.pku.edu.cn:80/elective2008/ssoLogin.do"

    ssoLogin = f"{domain}elective2008/ssoLogin.do"

    HelpController = f"{domain}elective2008/edu/pku/stu/elective/controller/help/HelpController.jpf"

    SupplyCancel_url = f"{domain}elective2008/edu/pku/stu/elective/controller/supplement/SupplyCancel.do"

    SupplyCancel_header = {"Referer": f"{domain}elective2008/edu/pku/stu/elective/controller/help/HelpController.jpf", }

    supplement = f"{domain}elective2008/edu/pku/stu/elective/controller/supplement/supplement.jsp"

    verify_image = f"{domain}elective2008/DrawServlet"
    validate = f"{domain}elective2008/edu/pku/stu/elective/controller/supplement/validate.do"

    refresh_limit = f"{domain}elective2008/edu/pku/stu/elective/controller/supplement/refreshLimit.do"

    username = User.username
    password = User.password

    s_h = {'Referer': f"{domain}elective2008/edu/pku/stu/elective/controller/supplement/SupplyCancel.do?xh={username}"}

    session = requests.session()
    # session.mount('http://', HTTPAdapter(max_retries=Retry(total=2, allowed_methods=frozenset(['GET', 'POST']))))
    # session.mount('https://', HTTPAdapter(max_retries=Retry(total=2, allowed_methods=frozenset(['GET', 'POST']))))
    cookie = None


class Network:
    retry = 5

    def request(self, method, url, raw=False, headers=None, **kwargs):
        """
        请求函数
        :param method: GET/POST
        :param url:
        :param raw: False → json True→html(str)
        :param headers:
        :param kwargs:
        :return:
        """

        header = Const.headers
        if headers:
            headers.update(header)

        try:
            if Const.session:
                resp = Const.session.request(method, url, headers=header, timeout=2, **kwargs)
            else:
                resp = requests.request(method, url, headers=headers, cookies=Const.cookie, timeout=3, **kwargs)

        except requests.exceptions.ReadTimeout:
            self.retry -= 1
            if self.retry:
                print(f"pid:{os.getpid()} 登陆失败！重试——→{self.retry}")
                resp = self.request(method, url, raw=True, headers=None, **kwargs)

        self.retry = 5
        if not resp.ok:
            raise Exception(resp.status_code)

        if raw:
            return resp

        resp_json = resp.json()

        # if not resp_json.get('success'):
        #     msg = resp_json.get("msg")
        #     print(resp.text)
        #     raise Exception(msg)

        return resp_json

    def post(self, url, data=None, **kwargs):
        """
        POST
        :param url:
        :param data:
        :param kwargs:
        :return:
        """

        return self.request('POST', url, data=data, **kwargs)

    def get(self, url, params=None, raw=True, **kwargs):
        """
        GET
        :param url:
        :param params:
        :param raw:
        :param kwargs:
        :return:
        """

        return self.request('GET', url, params=params, raw=raw, **kwargs)


class Login(Network):
    def __init__(self, print_table_flag=True):
        super().__init__()
        self.table_header = None
        self.action = None
        self.result = None
        self.token = None
        self.raw_pages = []
        self.print_table_flag = print_table_flag

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
        print(f"pid:{os.getpid()} 登陆成功！")

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
            print(f"pid:{os.getpid()} 目前是跨院系选课数据准备时间！")
            wrong = True
        elif "您尚未登录或者会话超时" in self.raw_pages[0]:
            print(f"pid:{os.getpid()} 会话超时！重试！")
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


class Elective(Network):
    def __init__(self, course_name=None, auto_mode=False, auto_verify=False):
        super().__init__()

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

    def elective_initialize(self):
        login = Login(print_table_flag=not self.auto_mode)
        self.result, self.action = login.run()
        self.cache = login

    def re_initialize(self):
        self.result, self.action = self.cache.initialize()

    def manipulate(self, obj):
        """
        进行操作
        :param obj: [操作类型（刷新/补选）, 操作链接, 序号]
        :return:
        """
        action_link = Const.domain + obj[1]
        if obj[0] == "刷新":
            self.refresh(obj[2])
        self.get_verify(obj[2])
        self.select(action_link)

    def manual(self):
        """
        手动输入
        :return:
        """
        while True:
            self.index = int(input())
            obj = [self.result[-1][self.index], self.action[self.index], self.index]
            self.manipulate(obj)

    def get_verify(self, index=None, retry=10):
        """
        获取验证码
        :param retry:
        :param index:
        :return:
        """
        if retry == 0:
            raise Exception("验证码自动识别出现了问题！")
        if not index:
            index = self.index

        rand = 10000 * random.random()
        resp = self.get(Const.verify_image, params={"Rand": rand},
                        headers=Const.s_h)

        path = f"{index}.png"
        with open(path, 'wb') as file:
            file.write(resp.content)

        if self.auto_verify:
            code = self.verifier.check(path)
            # print(f"pid:{os.getpid()} 验证码自动预测为：{code}")

        else:
            code = input("输入验证码:")

        post = self.post(url=Const.validate,
                         data={"xh": Const.username, "validCode": code},
                         headers=Const.s_h)

        if post["valid"] == '2':
            # print(f"pid:{os.getpid()} 验证码正确！")
            pass
        else:
            print(f"pid:{os.getpid()} 验证码错误，重新输入:\n")
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

        print(f"pid:{os.getpid()} {msg}")
        if "成功" in msg:
            self.end = True

    def refresh(self, index=None, sleep=3):
        """
        刷新
        :param index:
        :param sleep: 休眠时间
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

        if resp['electedNum'] == resp['limitNum']:
            print(f"pid:{os.getpid()} 没有空余名额！")
            time.sleep(sleep)
            self.refresh(index=index, sleep=sleep)
        else:
            print(f"pid:{os.getpid()} 有空余名额！")

    def locate(self):
        """
        定位
        :return:
        """
        for index in range(len(self.result[0])):
            if self.result[0][index] == self.course_name:
                self.manipulate([self.result[-1][index], self.action[index], index])

                if not self.end:
                    self.re_initialize()
                    self.locate()

    def run(self):
        """
        运行
        :return:
        """
        if self.auto_mode:
            self.locate()
        else:
            self.manual()


def select(course_name=None, auto_mode=True, auto_verify=True):
    """
    :param auto_verify:
    :param auto_mode:
    :param course_name: 课程名
    :return:
    """
    Elective(course_name=course_name,
             auto_mode=auto_mode,
             auto_verify=auto_verify).run()


def multiprocess(name_list, auto_mode=True, auto_verify=True):
    """
    :param name_list:
    :param auto_mode:
    :param auto_verify:
    :return:
    """
    stat_time = time.time()
    process_list = []
    for name in name_list:
        p = Process(target=select, args=(name, auto_mode, auto_verify))
        p.start()
        process_list.append(p)

    for p in process_list:
        p.join()

    print(f"total time:{time.time() - stat_time}")


if __name__ == "__main__":
    names = ["中华人民共和国对外关系", "应用数理统计方法", "社会学概论"]
    # names = ["信息系统分析与设计", "复杂网络理论与实践"]
    # names = ["实用英语：从听说到演讲"]
    # multiprocess(names, auto_mode=True, auto_verify=True)
    select(auto_mode=False, auto_verify=True)
