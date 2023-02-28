from typing import Any

from aiohttp.web import json_response as aiohttp_json_response
from aiohttp.web_response import Response


def json_response(data: Any = None, status: str = "ok") -> Response:
    if data is None:
        data = {}
    return aiohttp_json_response(
        data={
            "status": status,
            "data": data,
        }
    )


def error_json_response(
        http_status: int,
        status: str = "error",
        message: str | None = None,
        data: dict | None = None,
):
    if data is None:
        data = {}
    return aiohttp_json_response(
        status=http_status,
        data={
            "status": status,
            "message": str(message),
            "data": data,
        },
    )


def build_url_database(user: str,
                       password: str,
                       database: str,
                       host: str = "localhost",
                       port: str | int = 5432) -> str:
    return "postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}".format(
        user=user,
        password=password,
        host=host,
        port=port,
        database=database)
