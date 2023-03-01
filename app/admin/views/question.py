from aiohttp_apispec import response_schema, request_schema, match_info_schema

from app.admin.schemes import QuestionSchema, RetrieveQuestionSchema, PatchQuestionSchema
from app.web.app import View
from app.web.mixins import AuthRequiredMixin
from app.web.schemes import OkResponseSchema
from app.web.utils import json_response


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


class RetrieveQuestionView(AuthRequiredMixin, View):
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
