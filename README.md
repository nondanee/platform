<img src="static/logo.png" alt="logo" width="128" height="128" align="right" />

# 乃木物平台

搬家之前还把前后端代码都好好改了一遍

确实啊看以前写的都是什么玩意儿！

虽然现在写的也不怎么样...

Python3 & aiohttp & MySQL & Vanilla JS

### 部署
对一台崭新的 Ubuntu 16.04 腾讯云 CVM 而言

需要装点东西

```
sudo apt-get install python3-pip git nginx supervisor letsencrypt mysql-client mysql-server
sudo pip3 install pycrypto aiohttp aiomysql aiohttp_session bleach qiniu cryptography
```

把源码拉下来

```
git clone https://github.com/nondanee/platform.git
```

把旧数据搬过去...

改一下域名解析

重新签个证书

```
sudo letsencrypt certonly --standalone --email admin@example.com -d example.com
```

改一下 preferences 里的配置

```
[server]
host = ???
port = ???
domain = ???

[mysql]
host = ???
port = ???
user = ???
password = ???
database = ???

[qiniu]
domain = ???
access = ???
secret = ???
bucket = ???
```

执行一下部署

```
sudo python3 deploy.py
```

检查一下能否访问

应该就好了