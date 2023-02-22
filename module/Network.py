# -*- coding: utf-8 -*-
# @Name     : Network.py
# @Date     : 2023/2/17 20:29
# @Auth     : Yu Dahai
# @Email    : yudahai@pku.edu.cn
# @Desc     :
import requests

from module.Const import Const


class Network:
    retry = 10

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

        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectTimeout):
            self.retry -= 1
            if self.retry:
                print(f"pid:{Const.pid} 登陆失败！重试——→{self.retry}")
                resp = self.request(method, url, raw=True, headers=None, **kwargs)
            else:
                raise Exception("登陆拉了")

        self.retry = 10
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
