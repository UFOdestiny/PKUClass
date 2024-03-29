#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Name     : Email.py
# @Date     : 2022/9/7 14:46
# @Auth     : UFOdestiny
# @Desc     :

import smtplib
from email.mime.text import MIMEText
from email.header import Header
import socket
import requests
import os
from config import Email

os.environ['no_proxy'] = '*'


class QQMail(Email):
    def __init__(self, receiver=None):
        self._name = self._getName()
        self._smtp = self._connect()

        if self._use and receiver is not None:
            self._receivers.extend(receiver)

    def _getName(self):
        hostname = socket.gethostname()
        ip = requests.get('https://checkip.amazonaws.com').text.strip()
        return f"{hostname}<{hostname}@{ip}>"

    def _connect(self):
        try:
            smtp = smtplib.SMTP_SSL(host="smtp.qq.com", port=465)
            smtp.login(self._user, self._smtpcode)
            return smtp
        except socket.gaierror:
            print("HOST ERROR")

    def _message(self, msg, from_, to, subject):
        msg = MIMEText(msg, 'plain', 'utf-8')
        msg['From'] = Header(from_, 'utf-8')
        msg['To'] = Header(to, 'utf-8')
        msg['Subject'] = Header(subject, 'utf-8')

        return msg.as_string()

    def send(self, msg="MESSAGE IS EMPTY", from_=None, to=None, subject=None):
        if self._use:
            if not from_:
                from_ = self._name
            if not to:
                to = self._receivers[0]
            if not subject:
                subject = msg

            msg = self._message(msg=msg, from_=from_, to=to, subject=subject)

            try:
                self._smtp.sendmail(self._sender, self._receivers, msg)
            except smtplib.SMTPException:
                print("SEND FAILURE")


if __name__ == "__main__":
    qq = QQMail()
    qq.send(msg="摸摸哒")
