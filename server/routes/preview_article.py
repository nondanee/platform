import asyncio
import re 
from . import toolbox
from aiohttp import web
from aiohttp_session import get_session

@asyncio.coroutine
def route(request):

    room = request.match_info["room"]
    script = ""
    
    session = yield from get_session(request)
    if 'room' in session:
        if toolbox.in_session(session['room'],room):
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
    article = toolbox.linkify_article(article)

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

    return toolbox.html_response(html_back)