import logging
import os
import subprocess
from hashlib import sha256
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from aiohttp.test_utils import TestClient, loop_context
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.models import AdminModel
from app.store import Database
from app.store import Store
from app.web.app import setup_app
from app.web.config import Config

BASE_DIR = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def event_loop():
    with loop_context() as _loop:
        yield _loop


@pytest.fixture(scope="session")
def load_alembic():
    subprocess.call(['sh', os.path.join(BASE_DIR, "load_alembic.sh")])


@pytest.fixture(scope="session")
def server(load_alembic):
    app = setup_app(
        config_path=os.path.join(
            os.path.abspath(os.path.dirname(__file__)), "..", "config_test.yaml"
        )
    )
    app.on_startup.clear()
    app.on_shutdown.clear()

    app.store.tg_api = AsyncMock()
    app.store.tg_api.send_message = AsyncMock()

    app.database = Database(app)
    app.on_startup.append(app.database.connect)
    app.on_shutdown.append(app.database.disconnect)

    return app


@pytest.fixture
def store(server) -> Store:
    return server.store


@pytest.fixture
def db_session(server):
    return server.database.session


@pytest.fixture(autouse=True, scope="function")
async def clear_db(server):
    yield
    try:
        session = AsyncSession(server.database._engine)
        connection = session.connection()
        for table in server.database._db.metadata.tables:
            await session.execute(text(f"TRUNCATE {table} CASCADE"))
            await session.execute(text(f"ALTER SEQUENCE {table}_id_seq RESTART WITH 1"))

        await session.commit()
        connection.close()

    except Exception as err:
        logging.warning(err)


@pytest.fixture
def config(server) -> Config:
    return server.config


@pytest.fixture(autouse=True)
def cli(aiohttp_client, event_loop, server) -> TestClient:
    return event_loop.run_until_complete(aiohttp_client(server))


@pytest.fixture
async def authed_cli(cli, config) -> TestClient:
    await cli.post(
        "/admin.login",
        data={
            "username": config.admin.username,
            "password": config.admin.password,
        },
    )
    yield cli


@pytest.fixture(autouse=True)
async def admin(cli, db_session, config: Config) -> AdminModel:
    new_admin = AdminModel(
        username=config.admin.username,
        password=sha256(config.admin.password.encode()).hexdigest(),
    )
    async with db_session.begin() as session:
        session.add(new_admin)

    return new_admin
