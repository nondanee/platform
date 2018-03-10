import asyncio, aiomysql
import re, json, random
import os, pathlib
import time, datetime
import hashlib, base64
from Crypto.Cipher import AES

from aiohttp import web 
from cryptography import fernet
from aiohttp import web
from aiohttp_session import setup, get_session, session_middleware
from aiohttp_session.cookie_storage import EncryptedCookieStorage

# import logging

def main():
    host = "127.0.0.1"
    port = 8800
    loop = asyncio.get_event_loop()
    app = init(loop)
    web.run_app(app, host = host, port = port)

@asyncio.coroutine
def create_pool(app):
    app['pool'] = yield from aiomysql.create_pool(
        host = "localhost", port = 3306,
        user = "root", password = "",
        db = "platform", charset = "utf8mb4",
        loop = app.loop,
    )

@asyncio.coroutine
def check_version(request):
    os = request.match_info["os"]
    if os != "android": # and os!="ios":
        return web.HTTPBadRequest()

    json_back = {
        "versionCode": 1,
        "versionName": "1.0",
        "msg": "release 1.0",
        "download": "url"
    }
    
    return json_response(json_back)

@asyncio.coroutine
def upload_init(request):

    with (yield from request.app['pool']) as connect:
        cursor = yield from connect.cursor()

        while True:
            room = str(random.randint(0,999999)).zfill(6)
            delivery = datetime.datetime.now().strftime("%Y/%m/%d %H:%M")
            try:
                yield from cursor.execute('''
                    INSERT INTO article VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ''',(room,delivery,"","","","","","",0,0))
                yield from connect.commit()
                yield from cursor.close()
                connect.close()
                break
            except Exception as error:
                if error.args[1].find("Duplicate")!=-1:
                    continue

    token = token_generate(room)

    javascript_back = 'const token = "%s"'%(token)

    return javascript_response(javascript_back)
            

@asyncio.coroutine
def upload_photo(request):

    if request.content_type != "multipart/form-data":
        return web.HTTPBadRequest()

    query_parameters = request.rel_url.query
    if "token" in query_parameters:
        room = token_verify(query_parameters["token"])
        if room is None:
            return web.HTTPBadRequest()
        elif not re.search(r'^\d{6}$',room):
            return web.HTTPBadRequest()
    else:
        return web.HTTPBadRequest()

    try:
        reader = yield from request.multipart()
    except:
        return web.HTTPBadRequest()

    data = yield from reader.next()

    photo_dir = os.path.join(request.app["photo_dir"],room)

    if os.path.exists(photo_dir)==0:
        os.mkdir(photo_dir)

    temp_path = ''
    size = 0
    suffix = ''
    hash_calc = hashlib.md5()
    
    while True:
        try:
            chunk = yield from data.read_chunk()  # 8192 bytes by default
        except:
            return web.HTTPBadRequest()

        if not chunk:
            break

        if size == 0 : 

            if len(chunk) < 4:
                return web.HTTPUnsupportedMediaType(reason="unsupported file type")
 
            # top_bytes = chunk[0:4].hex().upper()
            top_bytes = ''.join('{:02x}'.format(x) for x in chunk[0:4]).upper()

            if top_bytes[0:6] == 'FFD8FF':
                suffix = "jpg"
            elif top_bytes[0:8] == '89504E47':
                suffix = "png"
            elif top_bytes[0:8] == '47494638':
                suffix = "gif"
            else:
                return web.HTTPUnsupportedMediaType(reason="unsupported file type")

            while True:
                temp_name = str(int(time.time())) + str(random.randint(0,9999)).zfill(4)
                temp_path = os.path.join(photo_dir,temp_name)
                if not os.path.exists(temp_path): 
                    file = open(temp_path,'wb')
                    break

        size = size + len(chunk)      
        file.write(chunk)
        hash_calc.update(chunk)

        if size / 1048576 > 3: # size limit 3MB
            file.close()
            os.remove(temp_path)
            return web.HTTPRequestEntityTooLarge(reason="file size overflow")

    file.close()
    hash_value = hash_calc.hexdigest()
    formal_name = hash_value + "." + suffix
    formal_path = os.path.join(photo_dir,formal_name)

    if os.path.exists(formal_path) != 0:
        os.remove(temp_path)
    else:
        os.rename(temp_path, formal_path)
    
    return web.Response(
        text=formal_name,
        # headers={'Access-Control-Allow-Origin':'*'}
    )


@asyncio.coroutine
def upload_article(request):

    session = yield from get_session(request)

    if request.content_type!="application/x-www-form-urlencoded":
        return web.HTTPBadRequest(reason="error content type")

    query_parameters = request.rel_url.query
    if "token" in query_parameters:
        room = token_verify(query_parameters["token"])
        if room is None:
            return web.HTTPBadRequest()
        elif not re.search(r'^\d{6}$',room):
            return web.HTTPBadRequest()
    else:
        return web.HTTPBadRequest()

    data = yield from request.post()

    if 'title' in data:
        title = data['title'] 
    else:
        return web.HTTPBadRequest()
    
    if 'subtitle' in data:
        subtitle = data['subtitle']
    else:
        return web.HTTPBadRequest()
    
    if 'provider' in data:
        provider = data['provider']
    else:
        return web.HTTPBadRequest()

    if 'type' in data:
        category = data['type'].lower()
        if category not in {"blog":"","news":"","magazine":""}:
            return web.HTTPBadRequest()
    else:
        return web.HTTPBadRequest()

    if 'article' in data:
        article = data['article']
    else:
        return web.HTTPBadRequest()

    delivery = datetime.datetime.now().strftime("%Y/%m/%d %H:%M")

    snippet = re.sub(r'http://',"", article)
    snippet = re.sub(r'https://',"", snippet)
    snippet = re.sub(r'\!\[[^\]]*\]\([^\)]+?\)',"",snippet)
    snippet = re.sub(r'\s+'," ",snippet)
    snippet = re.sub(r'^\s+',"",snippet)
    snippet = snippet[0:80]
    snippet = re.sub(r'\s$',"",snippet)
    if len(snippet) == 80: snippet = snippet + "..."

    images = re.findall(r'([\d|a-f]{32}\.(jpg|png|gif))',article)

    article = re.sub(r'\r\n','\n',article)
    article = re.sub(r'\n','<br>',article)
    article = re.sub(r'\!\[[^\]]*\]\(([^\)]+?)\)','<img src="\g<1>">',article)

    photo_dir = os.path.join(request.app["photo_dir"],room)

    uses = []
    for line in images: uses.append(line[0])

    exists = os.listdir(photo_dir)

    if len(exists) > len(uses):
        nouses = list(set(exists).difference(set(uses)))
        for photo_name in nouses:
            os.remove(os.path.join(photo_dir,photo_name))

    with (yield from request.app['pool']) as connect:
        cursor = yield from connect.cursor()
        yield from cursor.execute('''
            UPDATE article SET 
            delivery = %s, 
            type = %s, 
            title = %s, 
            subtitle = %s, 
            provider = %s, 
            summary = %s, 
            full = %s, 
            status = %s 
            WHERE id = %s
        ''',(delivery,category,title,subtitle,provider,snippet,article,1,room))
        yield from connect.commit()
        yield from cursor.close()
        connect.close()

    # os.system("python transcdn.py " + room + "&")

    if "room" not in session:
        session['room'] = room
    else:
        room_in_session = session['room']
        if not in_session(room_in_session,room):
            session['room'] = room_in_session + "," + room

    return web.Response(
        text="/preview/"+room,
        # headers={'Access-Control-Allow-Origin':'*'}
    )

@asyncio.coroutine
def preview_article(request):

    room = request.match_info["room"]
    script = ""
    
    session = yield from get_session(request)
    if 'room' in session:
        room_in_session = session['room']
        if in_session(room_in_session,room):
            script = '<script src="/static/modify.js"></script>'

    with (yield from request.app['pool']) as connect:
        cursor = yield from connect.cursor()
        exist = yield from cursor.execute('''
            SELECT delivery, title, subtitle, provider, full 
            FROM article WHERE id = %s and status = 1
            ''',(room,))
        out = yield from cursor.fetchall()
        yield from cursor.close()
        connect.close()

        if exist == 0: return web.HTTPNotFound()

    delivery = out[0][0].strftime("%Y/%m/%d %H:%M")
    title = out[0][1]
    subtitle = out[0][2]
    provider = out[0][3]
    article = out[0][4]
    article = re.sub(r'([\d|a-f]{32}\.(jpg|png|gif))','/photo/' + room + '/\g<1>',article)

    html_back = '''
<!DOCTYPE html>
<html>
<head>
	<meta charset="utf-8">
	<title>{title} | Platform · idol</title>
	<link rel="stylesheet" type="text/css" href="/static/preview.css"/>
	{script}
</head>
<body>
	<div id="whole">
		<div id="title">{title}</div>
		<div id="subtitle">{subtitle}</div>
		<div id="provider">{provider}</div>
		<div id="delivery">Archive: {delivery}</div>
		<div id="article">{article}</div>
	</div>
</body>
</html>
'''.format(
        script = script,
        title = title,
        subtitle = subtitle,
        provider = provider,
        delivery = delivery,
        article = article
    )

    return html_response(html_back)


@asyncio.coroutine
def delete_article(request):

    room = request.match_info["room"]

    session = yield from get_session(request)
    if 'room' in session:
        room_in_session = session['room']
        if not in_session(room_in_session,room):
            return web.HTTPForbidden()

    with (yield from request.app['pool']) as connect:
        cursor = yield from connect.cursor()
        result = yield from cursor.execute("UPDATE article SET status = 0 WHERE id = %s;",(room,))
        yield from connect.commit()
        yield from cursor.close()
        connect.close()

    return web.HTTPOk()


@asyncio.coroutine
def article(request):

    room = request.match_info["room"]

    with (yield from request.app['pool']) as connect:
        cursor = yield from connect.cursor()
        exist = yield from cursor.execute('''
            SELECT delivery, type, title, subtitle, provider, full, cdn 
            FROM article WHERE id = %s and status = 1
        ''',(room))
        out = yield from cursor.fetchall()
        yield from cursor.close()
        connect.close()

    if exist == 0: return web.HTTPNotFound()

    delivery = out[0][0]
    category = out[0][1]
    title = out[0][2]
    subtitle = out[0][3]
    provider = out[0][4]
    article = out[0][5]

    if out[0][6] == 0:
        article = re.sub(r'([\d|a-f]{32}\.(jpg|png|gif))','/photo/' + room + '/\g<1>',article)
    elif out[0][6] == 1:
        article = re.sub(r'([\d|a-f]{32}\.(jpg|png|gif))','/photo/' + room + '/\g<1>',article)

        # article=re.sub(r'([\d|a-f]{32}\.(jpg|png|gif))','http://os04l39cu.bkt.clouddn.com/' + room + '/\g<1>',article)

    if request.match_info["type"] == "view":

        html_back = '''
<!DOCTYPE html>
<html>
<head>
	<meta charset="utf-8">
	<meta name="theme-color" content="#812990">
	<title>乃木物</title>
	<link rel="stylesheet" type="text/css" href="/static/view.css"/>
	<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=0">
</head>
<body>
	<div id="block">
		<div id="title">{title}</div>
		<div id="subtitle">{subtitle}</div>
	</div>
	<div id="post">
		<div id="provider">{provider}</div>
		<div id="delivery">{delivery}</div>
	</div>
	<div id="article">{article}</div>
</body>
</html>
        '''.format(
            title = title,
            subtitle = subtitle,
            provider = provider,
            delivery = delivery.strftime("%m/%d %H:%M"),
            article = article
        )

        return html_response(html_back)


    elif request.match_info["type"] == "data":

        json_back = {
            "id": room,
            "delivery": int(time.mktime(delivery.timetuple())),
            "type": category,
            "title": title,
            "subtitle": subtitle,
            "provider": provider,
            "article": article
        }

        return json_response(json_back)


@asyncio.coroutine
def data_list(request):

    query_parameters = request.rel_url.query
    addition = ""
    limit = 10
    offset = 0

    if "type" in query_parameters:
        if query_parameters["type"] in {"blog":"","magazine":"","news":""}:
            addition = 'and type = "' + query_parameters["type"] + '"'
        else:
            return web.HTTPBadRequest(reason="no that type")

    if "size" in query_parameters:
        try:
            limit = int(query_parameters["size"])
            if limit > 100:
                return web.HTTPBadRequest(reason="page size over limit")
        except:
            return web.HTTPBadRequest()

    if "page" in query_parameters:
        try:
            page = int(query_parameters["page"])
            if page == 0:
                return web.HTTPBadRequest(reason="page start from 1")
            offset = (page-1)*limit
        except:
            return web.HTTPBadRequest()


    with (yield from request.app['pool']) as connect:
        cursor = yield from connect.cursor()
        exist = yield from cursor.execute('''
            SELECT id, delivery, type, title, subtitle, provider, snippet, full, cdn 
            FROM article WHERE status = 1 %s ORDER BY delivery DESC LIMIT %s,%s
            '''%(addition,offset,limit))

        out = yield from cursor.fetchall()
        yield from cursor.close()
        connect.close()

        if exist == 0: return web.HTTPNotFound(reason="empty page")

    json_back = []

    for line in out:

        if line[8] == 0:
            article = re.sub(r'([\d|a-f]{32}\.(jpg|png|gif))','https://nogimono.tk/photo/'+line[0]+'/\g<1>',line[7])
        elif line[8] == 1:
            article = re.sub(r'([\d|a-f]{32}\.(jpg|png|gif))','http://os04l39cu.bkt.clouddn.com/'+line[0]+'/\g<1>'+"?imageView2/1/w/250/h/200/q/80",line[7])
        
        images_raw = re.findall(r'<img src="([^"]+)">',article)
        images = list(set(images_raw))
        images.sort(key=images_raw.index)

        if len(images) >= 3:
            images_dealt = []
            for n in range(0,3):
                images_dealt.append({"image":images[n]})
        elif len(images) >= 1:
            images_dealt = [{"image":images[0]}]
        else:
            images_dealt = None

        json_back.append({
            "id": line[0],
            "delivery": int(time.mktime(line[1].timetuple())),
            "type": line[2],
            "title": line[3],
            "subtitle": line[4],
            "provider": line[5],
            "summary": line[6],
            "detail": "/data/" + line[0],
            "view": "/view/" + line[0],
            "withpic": images_dealt
        })

    return json_response(json_back)


@asyncio.coroutine
def data_blogs(request):
    
    query_parameters = request.rel_url.query

    addition = ""
    limit = 10
    offset = 0

    if "member" in query_parameters:
        if re.search(r'^[a-z|-]+$',query_parameters["member"]):
            addition = "WHERE rome = '%s'"%query_parameters["member"]
        else:
            return web.HTTPBadRequest()

    if "size" in query_parameters:
        if re.search(r'^\d+$',query_parameters["size"]):
            limit = int(query_parameters["size"])
            if limit > 100:
                return web.HTTPBadRequest()

    if "page" in query_parameters:
        if re.search(r'^\d+$',query_parameters["page"]):
            page = int(query_parameters["page"])
            if page == 0:
                return web.HTTPBadRequest()
            offset = (page-1)*limit


    with (yield from request.app['pool']) as connect:
        cursor = yield from connect.cursor()
        exist = yield from cursor.execute('''
            SELECT post, author, title, snippet, link 
            FROM official_blog %s ORDER BY post DESC, furigana DESC LIMIT %s,%s
            '''%(addition,offset,limit))
        out = yield from cursor.fetchall()
        yield from cursor.close()
        connect.close()

    if exist == 0: return web.HTTPNotFound()

    json_back = []

    for line in out:

        json_back.append({
            "post": int(time.mktime(line[0].timetuple())),
            "author": line[1],
            "title": line[2],
            "summary": line[3],
            "url": line[4]
        })

    return json_response(json_back)


@asyncio.coroutine
def data_intro(request):

    query_parameters=request.rel_url.query

    if "member" in query_parameters:
        if re.search(r'^[a-z|-]+$',query_parameters["member"]):
            member = query_parameters["member"]
        else:
            return web.HTTPBadRequest()
    else:
        return web.HTTPBadRequest()

    with (yield from request.app['pool']) as connect:
        cursor = yield from connect.cursor()
        exist = yield from cursor.execute('''
            SELECT name, furigana, romaji, birthdate, bloodtype, constellation, height, status, portrait, link 
            FROM member where rome = %s
            ''',(member,))
        out = yield from cursor.fetchall()
        yield from cursor.close()
        connect.close()

    if exist == 0: return web.HTTPNotFound()

    json_back = []

    for line in out:
        json_back.append({
            'name': line[0],
            'furigana': line[1],
            'romaji': line[2],
            'birthdate': line[3],
            'bloodtype': line[4],
            'constellation': line[5],
            'height': line[6],
            'status': line[7],
            'portrait': line[8],
            'link': line[9]
        })

    if len(json_back)==1:
        return json_response(json_back[0])
    else:
        return json_response(json_back)


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

def in_session(room_in_session,room):
    room_in_session = room_in_session.split(",")
    if room in room_in_session:
        return True
    else:
        return False

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


def setup_routes(app):

    app.router.add_route('GET', '/upload/init', upload_init)
    app.router.add_route('POST', '/upload/photo', upload_photo)
    app.router.add_route('POST', '/upload/article', upload_article)
    app.router.add_route('POST', '/delete/{room:\d{6}}', delete_article)
    app.router.add_route('GET', '/preview/{room:\d{6}}', preview_article)

    app.router.add_route('GET', '/{type:view}/{room:\d{6}}', article)
    app.router.add_route('GET', '/{type:data}/{room:\d{6}}', article)

    app.router.add_route('GET', '/data/list', data_list)
    app.router.add_route('GET', '/data/blogs', data_blogs)
    app.router.add_route('GET', '/data/intro', data_intro)

    app.router.add_route('GET', '/check/version/{os:\w+}', check_version)


def init(loop):
    app = web.Application(loop = loop)
    app.on_startup.append(create_pool)
    setup_routes(app)

    app["photo_dir"] = str(pathlib.Path(__file__).resolve().parents[1]/"photo")

    # fernet_key = fernet.Fernet.generate_key()
    fernet_key = b'wAYavr8zyR2kvmf1uXGko4MdGJ8cpDFOUW0lHIxoQ-I='
    secret_key = base64.urlsafe_b64decode(fernet_key)

    setup(app, EncryptedCookieStorage(secret_key,max_age=43200))

    return app

if __name__ == '__main__':
    main()