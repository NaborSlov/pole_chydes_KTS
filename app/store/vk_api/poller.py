import asyncio
from asyncio import Task
from logging import getLogger
from typing import Optional, Union

from aio_pika import connect_robust, RobustConnection
from aio_pika.patterns import Master, RejectMessage

from app.store import Store
from app.web.config import Config


class Poller:
    def __init__(self, store: Store, config: Config):
        self.config = config
        self.store = store
        self.logger = getLogger("poller")
        self.is_running = False
        self.poll_task: Optional[Task] = None
        self.worker: Optional[Task] = None
        self.handle_tasks: Union[list[Task], list] = []
        self.connection_master: Optional[RobustConnection] = None
        self.connection_worker: Optional[RobustConnection] = None

    async def start(self):
        self.connection_master = await connect_robust(f"{self.config.rabbit.url}?name=aio-pika%20master")
        self.connection_worker = await connect_robust(f"{self.config.rabbit.url}?name=aio-pika%20worker")
        self.is_running = True
        self.worker = asyncio.create_task(self.working())
        self.poll_task = asyncio.create_task(self.poll())

    async def stop(self):
        self.is_running = False

        tasks = await asyncio.gather(*self.handle_tasks, return_exceptions=True)
        for task in tasks:
            if isinstance(task, Exception):
                self.logger.error(str(task))

        self.worker.cancel()
        await self.worker
        await self.poll_task

    async def poll(self):
        async with self.connection_master:
            channel = await self.connection_master.channel()
            master = Master(channel)

            while self.is_running:
                updates = await self.store.tg_api.poll()

                if updates:
                    await master.create_task(
                        "updates_poll", kwargs=dict(updates=updates)
                    )

    async def working(self):
        channel = await self.connection_worker.channel()
        master = Master(channel)
        await master.create_worker("updates_poll", self.worker_updates, auto_delete=True)

        try:
            await asyncio.Future()
        finally:
            await self.connection_worker.close()

    async def worker_updates(self, updates: list) -> None:
        if not updates:
            raise RejectMessage(requeue=False)

        try:
            await self.store.bots_manager.handle_updates(updates)
        except Exception as e:
            self.logger.exception("task_exception", exc_info=e)
