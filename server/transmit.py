# -*- coding: utf-8 -*-
from qiniu import Auth, put_file, etag, urlsafe_base64_encode
import os, sys, pathlib
import pymysql
import logging
logging.basicConfig(level=logging.INFO,format='%(message)s')

working_directory = pathlib.Path(__file__).resolve().parents[1]

import configparser
config = configparser.ConfigParser()
config.read(str(working_directory/"preferences"))

local_depot = str(working_directory/"photo")
access_key = config.get("qiniu", "access")
secret_key = config.get("qiniu", "secret")
bucket_name = config.get("qiniu", "bucket")
auth = Auth(access_key, secret_key)

def mysql_connect():
    return pymysql.connect(
        host = config.get("mysql", "host"),
        port = config.getint("mysql", "port"),
        user = config.get("mysql", "user"),
        passwd = config.get("mysql", "password"),
        db = config.get("mysql", "database"),
        charset = "utf8mb4"
    )

upload_queue = []

if len(sys.argv) > 1:
    upload_queue.append(sys.argv[1])
else:
    connect = mysql_connect()
    cursor = connect.cursor()
    exist = cursor.execute("SELECT id FROM article WHERE status = 1 AND cdn = 0 ORDER BY delivery DESC LIMIT 20")
    data = cursor.fetchall()
    cursor.close()
    connect.close()
    if exist == 0: 
        exit()
    
    for line in data: 
        upload_queue.append(line[0])
    

finish_list = []

for room in upload_queue:

    room_path = os.path.join(local_depot,room)

    if os.path.exists(room_path):
    
        files = os.listdir(room_path)
        
        for file_name in files:

            file_path = os.path.join(room_path,file_name)

            key = "{}/{}".format(room,file_name)
                    
            token = auth.upload_token(bucket_name,key,3600)
                        
            ret,info = put_file(token,key,file_path)
            
            assert ret['key'] == key
            assert ret['hash'] == etag(file_path)
        
            logging.info("{} {}".format(key,info.status_code))
            
        finish_list.append((room,))

connect = mysql_connect()
cursor = connect.cursor()

try:
    cursor.executemany("UPDATE article SET cdn = 1 WHERE id = %s",finish_list)
except Exception as e:
    logging.info(e)    
else:
    cursor.close()
    connect.commit()
    connect.close()
    
logging.info("transmission done")
