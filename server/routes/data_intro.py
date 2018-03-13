import asyncio
import re
from . import toolbox
from aiohttp import web

@asyncio.coroutine
def route(request):

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
            FROM member where romaji = %s
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
        return toolbox.json_response(json_back[0])
    else:
        return toolbox.json_response(json_back)