from aiohttp.web import HTTPForbidden
from aiohttp_apispec import request_schema, response_schema
from aiohttp_session import new_session

from app.admin.schemes import AdminSchema
from app.web.app import View
from app.web.utils import json_response


class AdminLoginView(View):
    @request_schema(AdminSchema)
    @response_schema(AdminSchema, 200)
    async def post(self):
        data_user = self.data
        admin = await self.store.admins.get_by_email(data_user.get('email'))

        if admin is None or not admin.is_password_valid(data_user.get('password')):
            raise HTTPForbidden

        session = await new_session(request=self.request)
        session["admin"] = {"id": admin.id,
                            "username": admin.username}

        return json_response(data=AdminSchema().dump(admin))


class AdminCurrentView(View):
    @response_schema(AdminSchema, 200)
    async def get(self):
        return json_response(data=AdminSchema().dump(self.request.admin))
