from app.store import Store


class TestAdminLoginView:
    async def test_create_on_startup(self, store: Store, config):
        admin = await store.admins.get_by_username(config.admin.username)
        assert admin is not None
        assert admin.id == 1
        assert admin.username == config.admin.username
        assert admin.is_password_valid(config.admin.password)

    async def test_login_admin(self, config, cli):
        response = await cli.post(
            "/admin.login",
            data={
                "username": config.admin.username,
                "password": config.admin.password,
            },
        )
        data = await response.json()

        assert response.status == 200
        assert response.cookies
        assert data['data']['username'] == config.admin.username
