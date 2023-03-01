from aiohttp_apispec import response_schema

from app.field_wonder.schemes import GameSchema
from app.web.app import View
from app.web.mixins import AuthRequiredMixin
from app.web.schemes import OkResponseSchema
from app.web.utils import json_response


class GameStaticView(AuthRequiredMixin, View):
    @response_schema(OkResponseSchema, 200)
    async def get(self):
        games = await self.store.field.get_games()

        if not games:
            return json_response(status_code=204)

        return json_response(data=GameSchema().dump(games, many=True))
