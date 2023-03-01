import typing

from app.field_wonder.views import GameStaticView

if typing.TYPE_CHECKING:
    from app.web.app import Application


def setup_routes(app: "Application"):
    app.router.add_view("/statistics", GameStaticView)
