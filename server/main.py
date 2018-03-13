# -*- coding: utf-8 -*-
import asyncio, aiomysql
import pathlib, configparser, base64
# import logging

from aiohttp import web
from cryptography import fernet
from aiohttp_session import setup
from aiohttp_session.cookie_storage import EncryptedCookieStorage

from routes import setup_routes

working_directory = pathlib.Path(__file__).resolve().parents[1]

config = configparser.ConfigParser()
config.read(str(working_directory/"preferences"))

@asyncio.coroutine
def create_pool(app):
    app['pool'] = yield from aiomysql.create_pool(
        host = config.get("mysql", "host"), 
        port = config.getint("mysql", "port"),
        user = config.get("mysql", "user"), 
        password = config.get("mysql", "password"),
        db = config.get("mysql", "database"), 
        charset = "utf8mb4",
        loop = app.loop,
    )

def init(loop):
    app = web.Application(loop = loop)
    app.on_startup.append(create_pool)
    setup_routes(app)

    # fernet_key = fernet.Fernet.generate_key()
    fernet_key = b'wAYavr8zyR2kvmf1uXGko4MdGJ8cpDFOUW0lHIxoQ-I='
    secret_key = base64.urlsafe_b64decode(fernet_key)

    setup(app, EncryptedCookieStorage(secret_key,max_age=43200))

    return app

def main():
    host = config.get("server", "host")
    port = config.getint("server", "port")
    loop = asyncio.get_event_loop()
    app = init(loop)

    app["working_dir"] = str(working_directory)
    app["photo_dir"] = str(working_directory/"photo")
    app["server_domain"] = config.get("server", "domain")
    app["qiniu_domain"] = config.get("qiniu", "domain")

    web.run_app(app, host = host, port = port)

if __name__ == '__main__':
    main()