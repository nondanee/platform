import asyncio
import re, datetime, os
from . import toolbox
from aiohttp import web
from aiohttp_session import get_session

@asyncio.coroutine
def route(request):

    session = yield from get_session(request)

    if request.content_type!="application/x-www-form-urlencoded":
        return web.HTTPBadRequest(reason="error content type")

    query_parameters = request.rel_url.query
    if "token" in query_parameters:
        room = toolbox.token_verify(query_parameters["token"])
        if room is None:
            return web.HTTPBadRequest()
        elif not re.search(r'^\d{6}$',room):
            return web.HTTPBadRequest()
    else:
        return web.HTTPBadRequest()

    data = yield from request.post()

    if 'title' in data:
        title = data['title']
        title = toolbox.purify_plain_text(title)
    else:
        return web.HTTPBadRequest()
    
    if 'subtitle' in data:
        subtitle = data['subtitle']
        subtitle = toolbox.purify_plain_text(subtitle)
    else:
        return web.HTTPBadRequest()
    
    if 'provider' in data:
        provider = data['provider']
        provider = toolbox.purify_plain_text(provider)
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
    article = toolbox.purify_article(article)

    photo_dir = os.path.join(request.app["photo_dir"],room)

    uses = []
    for line in images:
        uses.append(line[0])

    exists = []
    if os.path.exists(photo_dir):
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
            snippet = %s, 
            full = %s, 
            status = %s 
            WHERE id = %s
        ''',(delivery,category,title,subtitle,provider,snippet,article,1,room))
        yield from connect.commit()
        yield from cursor.close()
        connect.close()

    os.system("python3 {working_dir}/server/transmit.py {room} &".format(
        working_dir = request.app["working_dir"],
        room = room
    ))

    if "room" not in session:
        session['room'] = room
    else:
        session['room'] = toolbox.add_to_session(session['room'],room)

    return web.Response(
        text="/preview/"+room,
        # headers={'Access-Control-Allow-Origin':'*'}
    )


