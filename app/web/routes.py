from aiohttp.web_app import Application


def setup_routes(app: Application):
    from app.admin.routes import setup_routes as admin_setup_routes
    from app.field_wonder.routes import setup_routes as field_wonder_setup_routes

    admin_setup_routes(app)
    field_wonder_setup_routes(app)
