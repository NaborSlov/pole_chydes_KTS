import asyncio
from asyncio import Task
from logging import getLogger

from aio_pika import connect_robust
from aio_pika.patterns import Master

from app.store import Store


class Poller:
    def __init__(self, store: Store):
        self.store = store
        self.logger = getLogger("poller")
        self.is_running = False
        self.poll_task: Task | None = None
        self.worker: Task | None = None
        self.handle_tasks: list[Task] | list = []

    async def start(self):
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
        self.connection_master = await connect_robust(
            "amqp://guest:guest@127.0.0.1/?name=aio-pika%20master",
        )
        async with self.connection_master:
            channel = await self.connection_master.channel()
            master = Master(channel)

            while self.is_running:
                updates = await self.store.tg_api.poll()

                if updates:
                    await master.create_task(
                        "updates_poll", kwargs=dict(updates=updates)
                    )

                # task = asyncio.create_task(self.store.bots_manager.handle_updates(updates))
                # task.add_done_callback(lambda x: self.logger.info(f"Выполнено {x}"))
                # self.handle_tasks.append(task)

    async def working(self):
        self.connection_worker = await connect_robust(
            "amqp://guest:guest@127.0.0.1/?name=aio-pika%20worker",
        )

        channel = await self.connection_worker.channel()
        master = Master(channel)
        await master.create_worker("updates_poll", self.workering, auto_delete=True)

        try:
            await asyncio.Future()
        finally:
            await self.connection_worker.close()

    async def workering(self, *, updates: list) -> None:
        await self.store.bots_manager.handle_updates(updates)
