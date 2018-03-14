<img src="static/logo.png" alt="logo" width="128" height="128" align="right" />

# Platform

A submisson platform for translation of blogs and news about Nogizaka46

Python3 & aiohttp & MySQL & Vanilla JS

### Deployment
(For a new created CVM with Ubuntu 16.04 on Tencent Cloud)

Install required packages on the server

```
sudo apt-get install python3-pip git nginx supervisor letsencrypt mysql-client mysql-server
sudo pip3 install pycrypto aiohttp aiomysql aiohttp_session bleach qiniu cryptography
```

Pull down the project codes

```
git clone https://github.com/nondanee/platform.git
```

Rebuild data from backup

manage dns and sign a new certificate

```
sudo letsencrypt certonly --standalone --email admin@example.com -d example.com
```

Add personal configuration in [preferences](preferences) file

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

Run script to deploy

```
sudo python3 deploy.py
```

Check for access

All done