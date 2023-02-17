# -*- coding: utf-8 -*-
# @Name     : Const.py
# @Date     : 2023/2/17 20:26
# @Auth     : Yu Dahai
# @Email    : yudahai@pku.edu.cn
# @Desc     :
import os
import sys

import requests

from Config import User


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

    if len(sys.argv) == 1:
        username = User.username
        password = User.password
    else:
        username = sys.argv[1]
        password = sys.argv[2]

    s_h = {'Referer': f"{domain}elective2008/edu/pku/stu/elective/controller/supplement/SupplyCancel.do?xh={username}"}

    session = requests.session()
    # session.mount('http://', HTTPAdapter(max_retries=Retry(total=2, allowed_methods=frozenset(['GET', 'POST']))))
    # session.mount('https://', HTTPAdapter(max_retries=Retry(total=2, allowed_methods=frozenset(['GET', 'POST']))))
    cookie = None
    pid = os.getpid()
