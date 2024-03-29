import typing
import yaml
from dataclasses import dataclass

from app.web.utils import build_url_database

if typing.TYPE_CHECKING:
    from app.web.app import Application


@dataclass
class Session:
    key: str


@dataclass
class BotConfig:
    token: str


@dataclass
class AdminConfig:
    username: str
    password: str


@dataclass
class DatabaseConfig:
    url_database: str
    host: str = 'localhost'
    port: int = 5432
    user: str = "postgres"
    password: str = "postgres"
    database: str = "project"


@dataclass
class RabbitMQ:
    url: str


@dataclass
class Config:
    admin: AdminConfig
    session: Session
    bot: BotConfig
    database: DatabaseConfig
    rabbit: RabbitMQ


def setup_config(app: "Application", config_path: str) -> None:
    with open(config_path, 'r') as file:
        raw_config = yaml.safe_load(file)

    url_database = build_url_database(**raw_config['database'])

    app.config = Config(
        session=Session(
            key=raw_config['session']['key']
        ),
        admin=AdminConfig(
            username=raw_config['admin']['username'],
            password=raw_config['admin']['password'],
        ),
        bot=BotConfig(
            token=raw_config['bot']['token'],
        ),
        database=DatabaseConfig(**raw_config['database'], url_database=url_database),
        rabbit=RabbitMQ(url=raw_config['rabbitmq']['url'])
    )
