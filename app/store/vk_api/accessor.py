import json
import random
import typing

import marshmallow_dataclass
from aiohttp import TCPConnector
from aiohttp.client import ClientSession

from app.base.base_accessor import BaseAccessor
from app.store.vk_api.dataclasses import Message, GetUpdates, SendMessage
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
        self.poller = Poller(app.store)
        self.logger.info("start polling")
        await self.poller.start()

    async def disconnect(self, app: "Application"):
        if self.session:
            await self.session.close()
        if self.poller:
            await self.poller.stop()

    @staticmethod
    def _build_query(host: str, method: str, token: str, params: dict) -> str:
        url = host + token + "/" + method + "?"
        url += "&".join([f"{k}={v}" for k, v in params.items()])
        return url

    async def poll(self):
        async with self.session.get(self._build_query(host=API_PATH,
                                                      method="getUpdates",
                                                      token=self.token,
                                                      params={
                                                          "offset": self.offset,
                                                          "timeout": 30,
                                                          "allowed_updates": json.dumps([]),
                                                      },                                                      )) as resp:
            data = await resp.json()
            self.logger.info(data)

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
        params = {
            "chat_id": message.chat_id,
            "text": message.text,
        }

        async with self.session.get(
                self._build_query(
                    API_PATH,
                    token=self.token,
                    method="sendMessage",
                    params=params,
                )
        ) as resp:
            data = await resp.json()
            self.logger.info(data)
