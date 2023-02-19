import base64
import json
import requests
from config import TuJianSetting

import cv2
import numpy as np


class TuJian(TuJianSetting):
    def __init__(self):
        self.typeid = 3
        self.cv = CvProcess()

    def check(self, img, process=False):
        if process:
            self.cv.process(img)

        with open(img, 'rb') as f:
            return self.send(f.read())

    def send(self, data):
        base64_data = base64.b64encode(data)
        b64 = base64_data.decode()
        data = {"username": self.uname, "password": self.pwd, "typeid": self.typeid, "image": b64}
        result = json.loads(requests.post("http://api.ttshitu.com/predict", json=data).text)
        if result['success']:
            return result["data"]["result"]
        else:
            return result["message"]


class CvProcess:
    def __init__(self, setting=[250, 255], threshold=510):
        self.setting = setting
        self.threshold = threshold

    def read(self, name):
        img = cv2.imread(name, 0)
        _, th = cv2.threshold(img, self.setting[0], self.setting[1], cv2.THRESH_TOZERO)
        return th

    def pool(self, th):
        th = np.copy(th)
        indexes = []
        for i in range(1, len(th) - 1):
            for j in range(1, len(th[0]) - 1):
                # print(i, j)
                sum_ = 0
                for a, b in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                    sum_ += th[i + a][j + b]
                if sum_ >= self.threshold:
                    indexes.append((i, j))

        for index in indexes:
            th[index[0]][index[1]] = 255
        return th

    def process(self, name):
        th = self.read(name)
        th_ = self.pool(th)
        cv2.imwrite(name, th_)

        # cv2.imshow('canny', np.hstack((th, th_)))
        # cv2.waitKey(0)


if __name__ == "__main__":
    t = TuJian()
    img_path = r"D:/COURSE/program/python/pkuclass/captcha/13184 2.png"
    print(t.check(img_path))

    # img_path = r"D:\COURSE\program\python\pkuclass\captcha\2.jpg"
    # print(t.check(img_path))
    #
    # img_path = r"D:\COURSE\program\python\pkuclass\captcha\3.jpg"
    # print(t.check(img_path))

    # c = CvProcess()
    # c.process("captcha/1.png")
