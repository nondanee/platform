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
sudo apt-get install python3-pip git nginx supervisor mysql-client mysql-server
sudo pip3 install pycrypto aiohttp aiomysql aiohttp_session cryptography
```

把源码拉下来

```
git clone https://github.com/nondanee/platform.git
```

把旧数据搬过去

改一下代码里的数据库配置

改一下域名解析

重新签个证书

```
git clone https://github.com/certbot/certbot.git
sudo bash certbot/certbot-auto certonly --standalone --email admin@example.com -d example.com
```

放好配置文件

```
sudo ln -s /home/ubuntu/platform/nginx.conf /etc/nginx/sites-enabled/platform
sudo ln -s /home/ubuntu/platform/supervisor.conf /etc/supervisor/conf.d/platform.conf
```

重载一下两个服务

```
sudo service nginx reload
sudo service supervisorctl reload
```
检查一下能否访问

应该就好了