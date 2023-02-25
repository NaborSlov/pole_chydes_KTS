from aiohttp.web import \
    Application as AiohttpApplication, \
    Request as AiohttpRequest, \
    View as AiohttpView

from app.store import Store
from app.store.database.database import Database
from app.web.config import setup_config, Config
from app.web.logger import setup_logging


class Application(AiohttpApplication):
    config: Config | None = None
    store: Store | None = None
    database: Database | None = None


class Request(AiohttpRequest):
    @property
    def app(self) -> Application:
        return super().app()


class View(AiohttpView):
    @property
    def request(self) -> Request:
        return super().request

    @property
    def database(self) -> Database:
        return self.request.app.database

    @property
    def store(self) -> Store:
        return self.request.app.store

    @property
    def data(self) -> dict:
        return self.request.get('data', {})


app = Application()


def setup_app(config_path):
    setup_logging(app)
    setup_config(app, config_path)
    return app
