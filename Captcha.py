import base64
import json
import requests
from Config import TuJianSetting


class TuJian(TuJianSetting):
    def __init__(self):
        self.typeid = 3

    def check(self, img):
        with open(img, 'rb') as f:
            return self.send(f.read())

    def check_auto(self, img):
        return self.send(img)

    def send(self, data):
        base64_data = base64.b64encode(data)
        b64 = base64_data.decode()
        data = {"username": self.uname, "password": self.pwd, "typeid": self.typeid, "image": b64}
        result = json.loads(requests.post("http://api.ttshitu.com/predict", json=data).text)
        if result['success']:
            return result["data"]["result"]
        else:
            return result["message"]


if __name__ == "__main__":
    t = TuJian()
    img_path = r"D:\COURSE\program\python\class\2.png"
    print(t.check(img_path))
