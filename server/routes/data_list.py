import asyncio
import re, time
from . import toolbox
from aiohttp import web

@asyncio.coroutine
def route(request):

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
            article = re.sub(r'([\d|a-f]{32}\.(jpg|png|gif))','https://'+request.app["server_domain"]+'/photo/'+line[0]+'/\g<1>',line[7])
        elif line[8] == 1:
            article = re.sub(r'([\d|a-f]{32}\.(jpg|png|gif))','http://'+request.app["qiniu_domain"]+'/'+line[0]+'/\g<1>'+"?imageView2/1/w/250/h/200/q/80",line[7])
        
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

    return toolbox.json_response(json_back)
