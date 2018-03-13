import asyncio
import re
from . import toolbox
from aiohttp import web
from aiohttp_session import get_session

@asyncio.coroutine
def route(request):

    if "Referer" not in request.headers:
        return web.HTTPForbidden()

    referer_check = re.search(request.app["server_domain"]+"/preview/(\d{6})",request.headers["Referer"])
    if not referer_check:
        return web.HTTPForbidden()
    room = referer_check.group(1)

    session = yield from get_session(request)
    if "room" in session:
        if not toolbox.in_session(session["room"],room):
            return web.HTTPForbidden()
        session["room"] = toolbox.remove_from_session(session["room"],room)

    with (yield from request.app["pool"]) as connect:
        cursor = yield from connect.cursor()
        result = yield from cursor.execute("UPDATE article SET status = 0 WHERE id = %s;",(room,))
        yield from connect.commit()
        yield from cursor.close()
        connect.close()



    return web.HTTPOk()