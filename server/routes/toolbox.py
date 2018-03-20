import bleach, base64, json, time
from Crypto.Cipher import AES
from aiohttp import web

def purify_plain_text(string):
    return bleach.clean(
        text = string,
        tags = [],
        strip = True,
    )

def purify_article(string):
    return bleach.clean(
        text = string,
        tags = ["img","br"],
        attributes = {"img":["src"]}
    )

def linkify_article(string):
    return bleach.linkify(string)


def in_session(room_in_session,room):
    rooms = set(room_in_session.split(","))
    if room in rooms:
        return True
    else:
        return False

def add_to_session(room_in_session,room):
    rooms = set(room_in_session.split(","))
    if room in rooms:
        return ",".join(rooms)
    else:
        rooms.add(room)
        return ",".join(rooms)

def remove_from_session(room_in_session,room):
    rooms = set(room_in_session.split(","))
    if room not in rooms:
        return ",".join(rooms)
    else:
        rooms.remove(room)
        return ",".join(rooms)


pad = lambda s: s + (16 - len(s) % 16) * chr(16 - len(s) % 16)
unpad = lambda s : s[0:-(s[-1])]

def cipher():
    key = "key_for_token"
    iv = "iv_for_token"
    key = pad(key)
    iv = pad(iv)
    return AES.new(key,AES.MODE_CBC,iv)

def token_generate(value):
    expire = int(time.time()) + 3600
    message = "{}:{}".format(value,expire)
    message = pad(message)
    raw = cipher().encrypt(message)
    token = base64.urlsafe_b64encode(raw)
    return bytes.decode(token)

def token_verify(token):
    raw = base64.urlsafe_b64decode(token)
    try: message = cipher().decrypt(raw)
    except: return
    message = unpad(message)
    message = bytes.decode(message)
    message = message.split(":")
    if len(message) != 2: return
    value = message[0]
    expire = message[1]
    try: expire = int(expire)
    except: return
    if expire < int(time.time()): return
    return value


def html_response(html_str):
    return web.Response(
        text = html_str,
        content_type = "text/html",
        charset = "utf-8"
    )

def javascript_response(javascript_str):
    return web.Response(
        text = javascript_str,
        content_type = "application/javascript",
        charset = "utf-8"
    )

def json_response(json_dict):
    return web.Response(
        text = json.dumps(json_dict,ensure_ascii=False,sort_keys=False,indent=4),
        content_type = "application/json",
        charset = "utf-8"
    )