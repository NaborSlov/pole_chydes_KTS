import typing

from app.admin.views import AdminCurrentView, ListQuestionView, RetrieveQuestionView

if typing.TYPE_CHECKING:
    from app.web.app import Application


def setup_routes(app: "Application"):
    from app.admin.views import AdminLoginView

    app.router.add_view("/admin.login", AdminLoginView)
    app.router.add_view("/admin.current", AdminCurrentView)
    app.router.add_view("/admin.questions", ListQuestionView)
    app.router.add_view("/admin.questions/{id}", RetrieveQuestionView)
