from . import data_list, data_blog, data_intro
from . import upload_init, upload_photo, upload_article
from . import preview_article, delete_article, article

def setup_routes(app):

    app.router.add_route('GET', '/upload/init', upload_init.route)
    app.router.add_route('POST', '/upload/photo', upload_photo.route)
    app.router.add_route('POST', '/upload/article', upload_article.route)
    app.router.add_route('POST', '/delete/article', delete_article.route)

    app.router.add_route('GET', '/preview/{room:\d{6}}', preview_article.route)
    app.router.add_route('GET', '/{type:view}/{room:\d{6}}', article.route)
    app.router.add_route('GET', '/{type:data}/{room:\d{6}}', article.route)

    app.router.add_route('GET', '/data/list', data_list.route)
    app.router.add_route('GET', '/data/blogs', data_blog.route)
    app.router.add_route('GET', '/data/intro', data_intro.route)