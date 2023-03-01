from aiohttp.web import HTTPForbidden
from aiohttp_apispec import request_schema, response_schema, match_info_schema
from aiohttp_session import new_session

from app.admin.schemes import AdminSchema, QuestionSchema, RetrieveQuestionSchema, PatchQuestionSchema
from app.web.app import View
from app.web.mixins import AuthRequiredMixin
from app.web.schemes import OkResponseSchema
from app.web.utils import json_response


class AdminLoginView(View):
    @request_schema(AdminSchema)
    @response_schema(OkResponseSchema, 200)
    async def post(self):
        data_user = self.data
        admin = await self.store.admins.get_by_username(data_user.get('username'))

        if admin is None or not admin.is_password_valid(data_user.get('password')):
            raise HTTPForbidden

        session = await new_session(request=self.request)
        session["admin"] = {"id": admin.id,
                            "username": admin.username}

        return json_response(data=AdminSchema().dump(admin))


class AdminCurrentView(View):
    @response_schema(OkResponseSchema, 200)
    async def get(self):
        return json_response(data=AdminSchema().dump(self.request.admin))


class ListQuestionView(AuthRequiredMixin, View):
    @response_schema(OkResponseSchema, 200)
    async def get(self):
        questions = await self.store.admins.get_list_questions()
        return json_response(data=QuestionSchema().dump(questions, many=True))

    @request_schema(QuestionSchema)
    @response_schema(OkResponseSchema, 201)
    async def post(self):
        data = self.data
        new_question = await self.store.admins.create_question(**data)
        return json_response(data=QuestionSchema().dump(new_question), status_code=201)


class RetrieveQuestionView(View):
    @match_info_schema(RetrieveQuestionSchema)
    @response_schema(OkResponseSchema, 200)
    async def get(self):
        quest_id = self.request.match_info['id']
        question = await self.store.admins.get_question_by_id(int(quest_id))

        if not question:
            return json_response(status_code=204)

        return json_response(QuestionSchema().dump(question))

    @match_info_schema(RetrieveQuestionSchema)
    @response_schema(OkResponseSchema, 203)
    async def delete(self):
        quest_id = self.request.match_info['id']
        await self.store.admins.delete_question_by_id(int(quest_id))
        return json_response(status_code=204)

    @match_info_schema(RetrieveQuestionSchema)
    @request_schema(PatchQuestionSchema)
    @response_schema(OkResponseSchema, 200)
    async def patch(self):
        quest_id = self.request.match_info['id']
        data = self.data
        question = await self.store.admins.update_question(id_question=int(quest_id), update_data=data)
        return json_response(data=QuestionSchema().dump(question))

