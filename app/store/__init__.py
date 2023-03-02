import typing

from app.store.database.database import Database

if typing.TYPE_CHECKING:
    from app.web.app import Application


class Store:
    def __init__(self, app: "Application"):
        from app.store.bot.manager import BotManager
        from app.store.vk_api.accessor import VkApiAccessor
        from app.store.admin.accessor import AdminAccessor
        from app.store.field_wonder.accessor import FieldWonder

        self.bots_manager = BotManager(app)
        self.tg_api = VkApiAccessor(app)
        self.admins = AdminAccessor(app)
        self.field = FieldWonder(app)


def setup_store(app: "Application"):
    app.database = Database(app)
    app.on_startup.append(app.database.connect)
    app.on_cleanup.append(app.database.disconnect)
    app.store = Store(app)
