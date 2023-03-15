import asyncio
import json
import typing
from dataclasses import asdict

import marshmallow_dataclass
from aiohttp import TCPConnector
from aiohttp.client import ClientSession

from app.base.base_accessor import BaseAccessor
from app.field_wonder import UserTG, Game, Player
from app.store.vk_api.dataclasses import GetUpdates, SendMessage, SendPoll
from app.store.vk_api.poller import Poller

if typing.TYPE_CHECKING:
    from app.web.app import Application

API_PATH = "https://api.telegram.org/"
schema_update = marshmallow_dataclass.class_schema(GetUpdates)


class VkApiAccessor(BaseAccessor):
    def __init__(self, app: "Application", *args, **kwargs):
        super().__init__(app, *args, **kwargs)
        self.session: ClientSession | None = None
        self.poller: Poller | None = None
        self.offset: int = 0
        self.token: str | None = None

    async def connect(self, app: "Application"):
        self.token = self.app.config.bot.token
        self.session = ClientSession(connector=TCPConnector(verify_ssl=False))
        self.poller = Poller(app.store, app.config)
        self.logger.info("start polling")
        await self.poller.start()

    async def disconnect(self, app: "Application"):
        if self.session:
            await self.session.close()
        if self.poller:
            await self.poller.stop()

    @staticmethod
    def _build_query(host: str, method: str, token: str, query_params: dict = None) -> str:
        url = host + token + "/" + method + "?"

        if query_params:
            url += "&".join([f"{k}={v}" for k, v in query_params.items()])

        return url

    async def poll(self):
        async with self.session.get(self._build_query(host=API_PATH,
                                                      method="getUpdates",
                                                      token=self.token,
                                                      query_params={
                                                          "offset": self.offset,
                                                          "timeout": 30,
                                                          "allowed_updates": [],
                                                      }, )) as resp:
            data = await resp.json()

            if not data['ok']:
                self.logger.error(f"poll_result:{data}")

            self.logger.info(f"poll_result:{data}")

            try:
                data_updates: GetUpdates = schema_update().load(data)
                results = data_updates.result
            except Exception as e:
                results = []
                self.logger.error(e)

            for update in results:
                if self.offset <= update.update_id:
                    self.offset = update.update_id + 1

            return data_updates.result

    async def send_message(self, message: SendMessage) -> None:
        params = asdict(message)

        async with self.session.get(
                self._build_query(
                    API_PATH,
                    token=self.token,
                    method="sendMessage",
                    query_params=params
                ),
        ) as resp:
            data = await resp.json()
            self.logger.info(f"send_message:{data}")

    async def send_inline_button_create_game(self, user: UserTG):
        reply_markup = {"inline_keyboard": [
            [
                {"text": f"Начать игру",
                 "callback_data": "create_poll@null"}
            ]
        ]}

        message = SendMessage(chat_id=user.chat_id,
                              text="Для того чтобы начать игру нажмите на",
                              reply_markup=json.dumps(reply_markup, ensure_ascii=False))

        await self.send_message(message)

    async def send_inline_button_start(self, user: UserTG, game: Game):
        reply_markup = {"inline_keyboard": [
            [
                {"text": f"Начать игру сразу",
                 "callback_data": f"just_start_game@{game.id}"}
            ]
        ]}

        message = SendMessage(chat_id=user.chat_id,
                              text="Ожидайте когда соберутся все игроки",
                              reply_markup=json.dumps(reply_markup, ensure_ascii=False))

        await self.send_message(message)

    async def send_inline_button_poll(self, game: Game, chat_id: int, username: str):
        reply_markup = {"inline_keyboard": [
            [
                {"text": f"Да",
                 "callback_data": f"poll_game@{game.id}"},
                {"text": f"Нет",
                 "callback_data": f"no@null"}

            ]
        ]}

        message = SendMessage(chat_id=chat_id,
                              text=f"Игрок {username} создал игру, хотите присоединиться?",
                              reply_markup=json.dumps(reply_markup, ensure_ascii=False))

        await self.send_message(message)

    async def send_you_turn(self, chat_id: int, game: Game):
        reply_markup = {"inline_keyboard": [
            [
                {"text": f"Выйти из игры",
                 "callback_data": f"exit_game@{game.id}"},
            ]
        ]}
        message = SendMessage(chat_id=chat_id,
                              text="Ваш ход",
                              reply_markup=json.dumps(reply_markup, ensure_ascii=False))

        await self.send_message(message)
