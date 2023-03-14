from hashlib import sha256

from sqlalchemy import select, delete, update
from sqlalchemy.engine import ChunkedIteratorResult

from app.admin.models import AdminModel
from app.admin.schemes import QuestionSchema
from app.base.base_accessor import BaseAccessor
from app.field_wonder import Question


class AdminAccessor(BaseAccessor):
    async def get_by_username(self, username: str) -> AdminModel | None:
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

    async def get_list_questions(self) -> list[Question] | None:
        async with self.app.database.session.begin() as session:
            rows = await session.execute(select(Question))
            result = rows.scalars().all()

        return result if result else None

    async def create_question(self, description: str, answer: str) -> Question:
        new_question = Question(description=description, answer=answer.lower())

        query = select(Question).where(Question.description == description)

        async with self.app.database.session.begin() as session:
            rows = await session.execute(query)
            if not rows.first():
                session.add(new_question)
                await session.commit()

        return new_question

    async def get_question_by_id(self, id_question: int) -> Question | None:
        query = select(Question).where(Question.id == id_question)

        async with self.app.database.session.begin() as session:
            result = await session.scalar(query)

        return result

    async def delete_question_by_id(self, id_question: int) -> None:
        query = delete(Question).where(Question.id == id_question)

        async with self.app.database.session.begin() as session:
            await session.execute(query)

    async def update_question(self, id_question: int, update_data: dict) -> Question | None:
        query = update(Question). \
            where(Question.id == id_question). \
            values(**update_data). \
            returning(Question)

        async with self.app.database.session.begin() as session:
            result = await session.scalar(query)

        return result
