import asyncio
import re, time
from . import toolbox
from aiohttp import web

@asyncio.coroutine
def route(request):

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
        # article=re.sub(r'([\d|a-f]{32}\.(jpg|png|gif))','http:// + 'request.app["qiniu_domain"] + '/' + room + '/\g<1>',article)

    article = toolbox.linkify_article(article)

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

        return toolbox.html_response(html_back)


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

        return toolbox.json_response(json_back)