import asyncio
from asyncio import Task
from logging import getLogger
from typing import Optional

from app.store import Store


class Poller:
    def __init__(self, store: Store):
        self.store = store
        self.logger = getLogger("poller")
        self.is_running = False
        self.poll_task: Task | None = None
        self.handle_tasks: list[Task] | list = []

    async def start(self):
        self.is_running = True
        self.poll_task = asyncio.create_task(self.poll())

    async def stop(self):
        self.is_running = False
        await asyncio.gather(*self.handle_tasks)
        await self.poll_task

    async def poll(self):
        while self.is_running:
            updates = await self.store.tg_api.poll()
            try:
                await self.store.bots_manager.handle_updates(updates)
            except Exception as e:
                print(e)

            # task = asyncio.create_task(self.store.bots_manager.handle_updates(updates))
            # task.add_done_callback(lambda x: self.logger.info(f"Выполнено {x}"))
            # self.handle_tasks.append(task)

