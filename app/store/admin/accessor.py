from hashlib import sha256

from sqlalchemy import select
from sqlalchemy.engine import ChunkedIteratorResult

from app.admin.models import AdminModel
from app.base.base_accessor import BaseAccessor


class AdminAccessor(BaseAccessor):
    async def get_by_email(self, username: str) -> AdminModel | None:
        query = select(AdminModel).where(AdminModel.username == username)
        async with self.app.database.session.begin() as session:
            rows = await session.execute(query)
            result: AdminModel = rows.scalars().first()

        if result:
            return result

    async def create_admin(self, username: str, password: str) -> AdminModel:
        password = sha256(password.encode()).hexdigest()
        admin = AdminModel(username=username, password=password)

        query = select(AdminModel).where(AdminModel.username == username)

        async with self.app.database.session.begin() as session:
            rows = await session.execute(query)
            if not rows.first():
                session.add(admin)
                await session.commit()

        return admin

    async def connect(self, app):
        await self.create_admin(username=app.config.admin.username, password=app.config.admin.password)
