from app.store import Store


class TestAdminLoginView:
    async def test_create_on_startup(self, store: Store, config):
        admin = await store.admins.get_by_username(config.admin.username)
        assert admin is not None
        assert admin.username == config.admin.username
        # Password must be hashed
        assert admin.password != config.admin.password
        assert admin.id == 1
