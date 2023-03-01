import typing

from app.admin.views import RetrieveQuestionView, ListQuestionView
from app.admin.views.admin import AdminCurrentView, AdminLoginView

if typing.TYPE_CHECKING:
    from app.web.app import Application


def setup_routes(app: "Application"):
    app.router.add_view("/admin.login", AdminLoginView)
    app.router.add_view("/admin.current", AdminCurrentView)
    app.router.add_view("/admin.questions", ListQuestionView)
    app.router.add_view("/admin.questions/{id}", RetrieveQuestionView)
