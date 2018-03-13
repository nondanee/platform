import asyncio
import re, os, hashlib, random, time
from . import toolbox
from aiohttp import web

@asyncio.coroutine
def route(request):

    if request.content_type != "multipart/form-data":
        return web.HTTPBadRequest()

    query_parameters = request.rel_url.query
    if "token" in query_parameters:
        room = toolbox.token_verify(query_parameters["token"])
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

        if size == 0:

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
