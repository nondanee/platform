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

    if "member" in query_parameters:
        if re.search(r'^[a-z|-]+$',query_parameters["member"]):
            addition = "WHERE romaji = '%s'"%query_parameters["member"]
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

    return toolbox.json_response(json_back)