# PKUClass

最后一个学年，给本科的抢课生涯做一个了断。感谢资方WHG的鼎力支持——2CNY。

v1.2 更新：增加电子邮件模块，选课成功后自动发送邮件，便于定时任务的部署提示。

### 环境

Python-3.9.12 requests-2.28.1 lxml-4.9.1 

### 配置文件

在Config.py对应输入门户账号密码与api识别接口账号密码。

### 验证码

```
auto_verify=True # 自动识别验证码
```

自动识别验证码使用的是[图鉴平台](http://ttshitu.com/)，可以自行申请。

```
auto_verify=False # 手动识别验证码
```

图片自动保存在当前文件夹，查看后在控制台直接输入即可。

### 自动模式

```
auto_mode=True # 自动选课
```

请手动更改name_list

```
auto_mode=False # 手动选课
```

手动输入课程序号即可。

### 免责声明

本项目仅供网络测试，爬虫交流学习使用。