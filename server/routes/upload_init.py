import asyncio
import random, datetime
from . import toolbox
from aiohttp import web

@asyncio.coroutine
def route(request):

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

    token = toolbox.token_generate(room)

    javascript_back = 'const token = "%s"'%(token)

    return toolbox.javascript_response(javascript_back)