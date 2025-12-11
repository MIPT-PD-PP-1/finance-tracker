"""
Тесты групп (Groups Tests)

Эндпоинты:
- GET /api/groups - Получить список групп пользователя
- POST /api/groups - Создать группу
- PUT /api/groups/{group_id} - Редактировать группу
- DELETE /api/groups/{group_id} - Удалить группу
- GET /api/groups/{group_id} - Посмотреть группу
- POST /api/groups/{group_id}/users/{user_id} - Добавить пользователя в группу
- DELETE /api/groups/{group_id}/users/{user_id} - Удалить пользователя из группы
- GET /api/groups/{group_id}/users - Список пользователей группы
- GET /api/transactions/group/{group_id}/stats - Аналитика по расходам в группе
"""
import pytest
from httpx import AsyncClient
from app.models import User, Group


class TestGetGroups:
    """Тесты получения списка групп GET /api/groups"""

    async def test_get_groups_success(
        self, client: AsyncClient, auth_headers, test_group
    ):
        """Успешное получение списка групп пользователя"""
        response = await client.get("/api/groups", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["name"] == test_group.name

    async def test_get_groups_empty(self, client: AsyncClient, auth_headers):
        """Получение пустого списка групп"""
        response = await client.get("/api/groups", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    async def test_get_groups_unauthorized(self, client: AsyncClient):
        """Получение списка групп без авторизации"""
        response = await client.get("/api/groups")

        assert response.status_code == 403


class TestCreateGroup:
    """Тесты создания группы POST /api/groups"""

    async def test_create_group_success(self, client: AsyncClient, auth_headers):
        """Успешное создание группы"""
        response = await client.post(
            "/api/groups",
            headers=auth_headers,
            json={"name": "New Test Group"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Test Group"
        assert "id" in data
        assert "users" in data

    async def test_create_group_owner_in_users(
        self, client: AsyncClient, auth_headers, test_user
    ):
        """Создатель группы автоматически добавляется в участники"""
        response = await client.post(
            "/api/groups",
            headers=auth_headers,
            json={"name": "Owner Group"}
        )

        assert response.status_code == 201
        data = response.json()
        user_ids = [u["id"] for u in data["users"]]
        assert test_user.id in user_ids

    async def test_create_group_unauthorized(self, client: AsyncClient):
        """Создание группы без авторизации"""
        response = await client.post(
            "/api/groups",
            json={"name": "Unauthorized Group"}
        )

        assert response.status_code == 403

    async def test_create_group_missing_name(self, client: AsyncClient, auth_headers):
        """Создание группы без имени"""
        response = await client.post(
            "/api/groups",
            headers=auth_headers,
            json={}
        )

        assert response.status_code == 422


class TestUpdateGroup:
    """Тесты редактирования группы PUT /api/groups/{group_id}"""

    async def test_update_group_success(
        self, client: AsyncClient, auth_headers, test_group
    ):
        """Успешное обновление группы"""
        response = await client.put(
            f"/api/groups/{test_group.id}",
            headers=auth_headers,
            json={"name": "Updated Group Name"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Group Name"
        assert data["id"] == test_group.id

    async def test_update_group_not_found(self, client: AsyncClient, auth_headers):
        """Обновление несуществующей группы"""
        response = await client.put(
            "/api/groups/99999",
            headers=auth_headers,
            json={"name": "New Name"}
        )

        assert response.status_code == 404

    async def test_update_group_forbidden(
        self, client: AsyncClient, auth_headers2, test_group
    ):
        """Обновление группы пользователем не из группы"""
        response = await client.put(
            f"/api/groups/{test_group.id}",
            headers=auth_headers2,
            json={"name": "Hacked Name"}
        )

        assert response.status_code == 403

    async def test_update_group_unauthorized(self, client: AsyncClient, test_group):
        """Обновление группы без авторизации"""
        response = await client.put(
            f"/api/groups/{test_group.id}",
            json={"name": "New Name"}
        )

        assert response.status_code == 403


class TestDeleteGroup:
    """Тесты удаления группы DELETE /api/groups/{group_id}"""

    async def test_delete_group_success(
        self, client: AsyncClient, auth_headers, test_group
    ):
        """Успешное удаление группы"""
        response = await client.delete(
            f"/api/groups/{test_group.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        assert "успешно удалена" in response.json()["message"]

        get_response = await client.get(
            f"/api/groups/{test_group.id}",
            headers=auth_headers
        )
        assert get_response.status_code == 404

    async def test_delete_group_not_found(self, client: AsyncClient, auth_headers):
        """Удаление несуществующей группы"""
        response = await client.delete(
            "/api/groups/99999",
            headers=auth_headers
        )

        assert response.status_code == 404

    async def test_delete_group_forbidden(
        self, client: AsyncClient, auth_headers2, test_group
    ):
        """Удаление группы пользователем не из группы"""
        response = await client.delete(
            f"/api/groups/{test_group.id}",
            headers=auth_headers2
        )

        assert response.status_code == 403

    async def test_delete_group_unauthorized(self, client: AsyncClient, test_group):
        """Удаление группы без авторизации"""
        response = await client.delete(f"/api/groups/{test_group.id}")

        assert response.status_code == 403


class TestGetGroup:
    """Тесты просмотра группы GET /api/groups/{group_id}"""

    async def test_get_group_success(
        self, client: AsyncClient, auth_headers, test_group
    ):
        """Успешное получение информации о группе"""
        response = await client.get(
            f"/api/groups/{test_group.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_group.id
        assert data["name"] == test_group.name
        assert "users" in data

    async def test_get_group_not_found(self, client: AsyncClient, auth_headers):
        """Получение несуществующей группы"""
        response = await client.get(
            "/api/groups/99999",
            headers=auth_headers
        )

        assert response.status_code == 404

    async def test_get_group_forbidden(
        self, client: AsyncClient, auth_headers2, test_group
    ):
        """Получение группы пользователем не из группы"""
        response = await client.get(
            f"/api/groups/{test_group.id}",
            headers=auth_headers2
        )

        assert response.status_code == 403

    async def test_get_group_unauthorized(self, client: AsyncClient, test_group):
        """Получение группы без авторизации"""
        response = await client.get(f"/api/groups/{test_group.id}")

        assert response.status_code == 403


class TestAddUserToGroup:
    """Тесты добавления пользователя в группу POST /api/groups/{group_id}/users/{user_id}"""

    async def test_add_user_success(
        self, client: AsyncClient, auth_headers, test_group, test_user2
    ):
        """Успешное добавление пользователя в группу"""
        response = await client.post(
            f"/api/groups/{test_group.id}/users/{test_user2.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        assert "успешно добавлен" in response.json()["message"]

    async def test_add_user_already_in_group(
        self, client: AsyncClient, auth_headers, test_group, test_user
    ):
        """Добавление пользователя, который уже в группе (идемпотентность)"""
        response = await client.post(
            f"/api/groups/{test_group.id}/users/{test_user.id}",
            headers=auth_headers
        )

        assert response.status_code == 200

    async def test_add_user_group_not_found(
        self, client: AsyncClient, auth_headers, test_user2
    ):
        """Добавление пользователя в несуществующую группу"""
        response = await client.post(
            f"/api/groups/99999/users/{test_user2.id}",
            headers=auth_headers
        )

        assert response.status_code == 404

    async def test_add_nonexistent_user(
        self, client: AsyncClient, auth_headers, test_group
    ):
        """Добавление несуществующего пользователя"""
        response = await client.post(
            f"/api/groups/{test_group.id}/users/99999",
            headers=auth_headers
        )

        assert response.status_code == 404

    async def test_add_user_forbidden(
        self, client: AsyncClient, auth_headers2, test_group, test_user
    ):
        """Добавление пользователя не членом группы"""
        response = await client.post(
            f"/api/groups/{test_group.id}/users/{test_user.id}",
            headers=auth_headers2
        )

        assert response.status_code == 403


class TestRemoveUserFromGroup:
    """Тесты удаления пользователя из группы DELETE /api/groups/{group_id}/users/{user_id}"""

    async def test_remove_user_success(
        self, client: AsyncClient, auth_headers, test_group, test_user2, db_session
    ):
        """Успешное удаление пользователя из группы"""
        test_group.users.append(test_user2)
        await db_session.commit()

        response = await client.delete(
            f"/api/groups/{test_group.id}/users/{test_user2.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        assert "успешно удален" in response.json()["message"]

    async def test_remove_user_not_in_group(
        self, client: AsyncClient, auth_headers, test_group, test_user2
    ):
        """Удаление пользователя, который не в группе"""
        response = await client.delete(
            f"/api/groups/{test_group.id}/users/{test_user2.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        assert "не состоит в группе" in response.json()["message"]

    async def test_remove_user_group_not_found(
        self, client: AsyncClient, auth_headers, test_user2
    ):
        """Удаление пользователя из несуществующей группы"""
        response = await client.delete(
            f"/api/groups/99999/users/{test_user2.id}",
            headers=auth_headers
        )

        assert response.status_code == 404

    async def test_remove_nonexistent_user(
        self, client: AsyncClient, auth_headers, test_group
    ):
        """Удаление несуществующего пользователя"""
        response = await client.delete(
            f"/api/groups/{test_group.id}/users/99999",
            headers=auth_headers
        )

        assert response.status_code == 404

    async def test_remove_user_forbidden(
        self, client: AsyncClient, auth_headers2, test_group, test_user
    ):
        """Удаление пользователя не членом группы"""
        response = await client.delete(
            f"/api/groups/{test_group.id}/users/{test_user.id}",
            headers=auth_headers2
        )

        assert response.status_code == 403


class TestGetGroupUsers:
    """Тесты списка пользователей группы GET /api/groups/{group_id}/users"""

    async def test_get_group_users_success(
        self, client: AsyncClient, auth_headers, test_group, test_user
    ):
        """Успешное получение списка пользователей группы"""
        response = await client.get(
            f"/api/groups/{test_group.id}/users",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        user_ids = [u["id"] for u in data]
        assert test_user.id in user_ids

    async def test_get_group_users_not_found(self, client: AsyncClient, auth_headers):
        """Получение пользователей несуществующей группы"""
        response = await client.get(
            "/api/groups/99999/users",
            headers=auth_headers
        )

        assert response.status_code == 404

    async def test_get_group_users_forbidden(
        self, client: AsyncClient, auth_headers2, test_group
    ):
        """Получение пользователей группы не членом группы"""
        response = await client.get(
            f"/api/groups/{test_group.id}/users",
            headers=auth_headers2
        )

        assert response.status_code == 403

    async def test_get_group_users_unauthorized(self, client: AsyncClient, test_group):
        """Получение пользователей группы без авторизации"""
        response = await client.get(f"/api/groups/{test_group.id}/users")

        assert response.status_code == 403


class TestGroupAnalytics:
    """Тесты аналитики группы GET /api/transactions/group/{group_id}/stats"""

    async def test_get_group_stats_success(
        self, client: AsyncClient, auth_headers, test_group
    ):
        """Успешное получение статистики группы (пустая)"""
        response = await client.get(
            f"/api/transactions/group/{test_group.id}/stats",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["group_id"] == test_group.id
        assert "total_income" in data
        assert "total_expense" in data
        assert "balance" in data
        assert "total_transactions" in data

    async def test_get_group_stats_with_transactions(
        self, client: AsyncClient, auth_headers, test_group, test_transaction_with_group
    ):
        """Получение статистики группы с транзакциями"""
        response = await client.get(
            f"/api/transactions/group/{test_group.id}/stats",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["group_id"] == test_group.id
        assert float(data["total_income"]) == 5000.00
        assert data["total_transactions"] >= 1

    async def test_get_group_stats_not_found(self, client: AsyncClient, auth_headers):
        """Получение статистики несуществующей группы"""
        response = await client.get(
            "/api/transactions/group/99999/stats",
            headers=auth_headers
        )

        assert response.status_code == 404

    async def test_get_group_stats_forbidden(
        self, client: AsyncClient, auth_headers2, test_group
    ):
        """Получение статистики группы не членом группы"""
        response = await client.get(
            f"/api/transactions/group/{test_group.id}/stats",
            headers=auth_headers2
        )

        assert response.status_code == 403

    async def test_get_group_stats_unauthorized(self, client: AsyncClient, test_group):
        """Получение статистики группы без авторизации"""
        response = await client.get(
            f"/api/transactions/group/{test_group.id}/stats"
        )

        assert response.status_code == 403
