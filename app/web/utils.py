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
