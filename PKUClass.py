# -*- coding: utf-8 -*-
# @Name     : PkuClass.py
# @Date     : 2022/9/4 10:48
# @Auth     : UFOdestiny
# @Desc     :

from Config import User
import os
import random
import time
from multiprocessing import Process

import requests
from lxml.etree import HTML
from requests.adapters import HTTPAdapter, Retry
from requests.utils import dict_from_cookiejar

from Verify import TuJian

os.environ['no_proxy'] = '*'


class PKUClass(User):
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1", }

    auth_url = 'https://iaaa.pku.edu.cn/iaaa/oauthlogin.do'

    redirUrl = "http://elective.pku.edu.cn:80/elective2008/ssoLogin.do"

    ssoLogin = "https://elective.pku.edu.cn/elective2008/ssoLogin.do"

    HelpController = "https://elective.pku.edu.cn/elective2008/edu/pku/stu/elective/controller/help/HelpController.jpf"

    SupplyCancel_url = "https://elective.pku.edu.cn/elective2008/edu/pku/stu/elective/controller/supplement/SupplyCancel.do"

    SupplyCancel_header = {
        "Referer": "https://elective.pku.edu.cn/elective2008/edu/pku/stu/elective/controller/help/HelpController.jpf", }

    supplement = "https://elective.pku.edu.cn/elective2008/edu/pku/stu/elective/controller/supplement/supplement.jsp"

    domain = "https://elective.pku.edu.cn/"

    verify_image = "https://elective.pku.edu.cn/elective2008/DrawServlet"
    validate = "https://elective.pku.edu.cn/elective2008/edu/pku/stu/elective/controller/supplement/validate.do"

    refresh_limit = "https://elective.pku.edu.cn/elective2008/edu/pku/stu/elective/controller/supplement/refreshLimit.do"

    def __init__(self, course_name=None, auto_mode=False, auto_verify=False):
        """
        :param course_name: 课程名
        :param auto_mode: 自动模式
        :param auto_verify: 自动验证码模式
        """

        self.supplement_header = {
            "Referer": f"https://elective.pku.edu.cn/elective2008/edu/pku/stu/elective/controller/supplement/SupplyCancel.do?xh={self.username}"}

        self.start_time = time.time()  # 记录开始时间
        self.end = None  # 结束符
        self.result = None  # 存放课程信息
        self.action = None  # 存放行动（补选/刷新）
        self.token = None  # IAAA验证token

        self.session = requests.session()  # 生成session
        self.session.mount('https://', HTTPAdapter(
            max_retries=Retry(total=5, allowed_methods=frozenset(['GET', 'POST']))))  # 重试

        self.cookie = None
        self.index = None  # 手动输入时的标号

        self.raw_pages = []  # 原始html
        self.table_header = None  # 表头
        self.auto_mode = auto_mode

        self.auto_verify = auto_verify
        if self.auto_verify:
            self.verifier = TuJian()

        self.course_name = course_name

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

        header = self.headers
        if headers:
            headers.update(header)

        if self.session:
            resp = self.session.request(method, url, headers=header, **kwargs)
        else:
            resp = requests.request(method, url, headers=headers, cookies=self.cookie, **kwargs)

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

    def login_portal(self):
        """
        获取token
        :return:
        """
        data = {'appid': 'syllabus',  # 选课网
                'userName': self.username,
                'password': self.password,
                'randCode': "",
                'smsCode': "",
                'otpCode': "",
                'redirUrl': self.redirUrl, }

        resp_json = self.post(self.auth_url, data=data)
        self.token = resp_json.get('token')

    def login_elective(self):

        sso_login = self.get(self.ssoLogin,
                             params={'_rand': random.random(), 'token': self.token},
                             allow_redirects=False)

        self.cookie = {"Hm_lvt_c7896bb34c3be32ea17322b5412545c0": "1661775435",
                       "JSESSIONID": dict_from_cookiejar(sso_login.cookies)["JSESSIONID"]}

        self.get(self.HelpController, allow_redirects=False)

        self.cookie["route"] = dict_from_cookiejar(self.session.cookies)["route"]

        # 删除session
        self.session = None

    def SupplyCancel(self):
        """
        补退选页面
        :return:
        """
        resp = self.get(self.SupplyCancel_url, params={"xh": self.username},
                        headers=self.SupplyCancel_header, )

        self.raw_pages.append(resp.text)

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
                raw_page = self.get(self.supplement,
                                    params={'netui_row': f'electableListGrid;{20 * (page_number - 1)}'},
                                    headers=self.supplement_header,
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
                    self.result[position].append(table[i][0].text)
                else:
                    a = [j for j in table[i]][0]
                    self.result[position].append([i for i in a][0].text)
                    self.action.append(a.attrib['href'])

    def print_table(self):
        """
        控制台打印表格
        :return:
        """
        for column in self.result:
            for ind in range(len(column)):
                if column[ind] is None:
                    column[ind] = "空"

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

    def manipulate(self, obj):
        """
        进行操作
        :param obj: [操作类型（刷新/补选）, 操作链接, 序号]
        :return:
        """
        action_link = self.domain + obj[1]
        if obj[0] == "刷新":
            self.refresh(obj[2])
        self.get_verify(obj[2])
        self.select(action_link)

    def get_input(self):
        """
        手动输入
        :return:
        """
        while True:
            self.index = int(input())
            obj = [self.result[-1][self.index], self.action[self.index], self.index]
            self.manipulate(obj)

    def get_verify(self, index=None):
        """
        获取验证码
        :param index:
        :return:
        """
        if not index:
            index = self.index

        rand = 10000 * random.random()
        resp = self.get(self.verify_image, params={"Rand": rand},
                        headers=self.supplement_header)

        path = f"{index}.png"
        with open(path, 'wb') as file:
            file.write(resp.content)

        if self.auto_verify:
            code = self.verifier.check(path)

            print(f"pid:{os.getpid()} 自动预测为：{code}")

        else:
            code = input("输入验证码:\n")

        post = self.post(url=self.validate,
                         data={"xh": self.username, "validCode": code},
                         headers=self.supplement_header)

        if post["valid"] == '2':
            print(f"pid:{os.getpid()} 验证码正确！")
        else:
            print(f"pid:{os.getpid()} 验证码错误，重新输入:\n")
            self.get_verify(index)

    def select(self, link):
        """
        补选
        :param link:
        :return:
        """

        resp = self.get(link, headers=self.supplement_header)

        xpath = "(//*[@id='msgTips'])[1]//text()"
        msgs = HTML(resp.text).xpath(xpath)
        msg = [i.strip() for i in msgs if len(i.strip()) > 2][0]

        print(f"pid:{os.getpid()} 结束:{msg}")
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
        url = self.domain + self.action[index]
        parse = url.split('?')[1].split('&')
        data = {
            "index": f"{parse[0].split('=')[1]}",
            "xh": f"{self.username}",
            "seq": f"{parse[2].split('=')[1]}",
        }
        start = 20 * int(data["index"]) // 20
        resp = self.post(self.refresh_limit, data=data,
                         headers={"Referer": self.supplement + f"?netui_row=electableListGrid%3B{start}"})

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
        # names = ["中华人民共和国对外关系", "社会学概论"]
        # names = ["信息系统分析与设计", "复杂网络理论与实践"]

        for index in range(len(self.result[0])):
            if self.result[0][index] == self.course_name:
                self.manipulate([self.result[-1][index], self.action[index], index])
                if self.end:
                    print(f"pid:{os.getpid()} {time.time() - self.start_time}")
                    return
                else:
                    self.raw_pages = []
                    self.SupplyCancel()
                    self.get_supplement()
                    self.table()

                    self.locate()

    def run(self):
        """
        运行
        :return:
        """
        self.login_portal()
        self.login_elective()
        self.SupplyCancel()
        self.get_supplement()
        self.table()

        if self.auto_mode:
            self.locate()
        else:
            self.print_table()
            self.get_input()


def select(course_name):
    """
    :param course_name: 课程名
    :return:
    """
    PKUClass(course_name=course_name,
             auto_mode=True,
             auto_verify=True).run()


if __name__ == "__main__":
    # name_list = ["信息系统分析与设计", "复杂网络理论与实践"]
    name_list = ["实用英语：从听说到演讲", "社会学概论"]
    stat_time = time.time()

    process_list = []
    for i in name_list:
        p = Process(target=select, args=(i,))
        p.start()
        process_list.append(p)

    for p in process_list:
        p.join()

    print(f"total time:{time.time() - stat_time}")

    # PKUClass(auto_mode=False, auto_verify=False).run()
