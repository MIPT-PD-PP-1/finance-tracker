"""
Тесты аутентификации (Authentication Tests)

Эндпоинты:
- POST /api/auth/register - Регистрация
- POST /api/auth/login - Авторизация
- GET /api/auth/me - Просмотр пользователя
- PUT /api/auth/change-password - Смена пароля
- POST /api/auth/refresh-token - Обновление токена
"""
import pytest
from httpx import AsyncClient


class TestRegister:
    """Тесты регистрации пользователя POST /api/auth/register"""

    async def test_register_success(self, client: AsyncClient):
        """Успешная регистрация нового пользователя"""
        response = await client.post(
            "/api/auth/register",
            json={
                "first_name": "John",
                "last_name": "Doe",
                "login": "johndoe",
                "password": "securepassword123"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["first_name"] == "John"
        assert data["last_name"] == "Doe"
        assert data["login"] == "johndoe"
        assert "id" in data
        assert "password" not in data

    async def test_register_duplicate_login(self, client: AsyncClient, test_user):
        """Регистрация с существующим логином должна вернуть ошибку"""
        response = await client.post(
            "/api/auth/register",
            json={
                "first_name": "Another",
                "last_name": "User",
                "login": "testuser",
                "password": "password123"
            }
        )

        assert response.status_code == 400
        assert "уже существует" in response.json()["detail"]

    async def test_register_missing_fields(self, client: AsyncClient):
        """Регистрация без обязательных полей должна вернуть ошибку"""
        response = await client.post(
            "/api/auth/register",
            json={
                "first_name": "John"
            }
        )

        assert response.status_code == 422

    async def test_register_empty_login(self, client: AsyncClient):
        """Регистрация с пустым логином (текущее поведение - разрешено)"""
        response = await client.post(
            "/api/auth/register",
            json={
                "first_name": "John",
                "last_name": "Doe",
                "login": "",
                "password": "password123"
            }
        )
        # NOTE: API в текущей версии позволяет пустой логин
        # Рекомендуется добавить валидацию min_length=1 в схему UserCreate
        assert response.status_code == 201


class TestLogin:
    """Тесты авторизации POST /api/auth/login"""

    async def test_login_success(self, client: AsyncClient, test_user):
        """Успешная авторизация"""
        response = await client.post(
            "/api/auth/login",
            json={
                "login": "testuser",
                "password": "testpassword123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user_id"] == test_user.id

    async def test_login_wrong_password(self, client: AsyncClient, test_user):
        """Авторизация с неправильным паролем"""
        response = await client.post(
            "/api/auth/login",
            json={
                "login": "testuser",
                "password": "wrongpassword"
            }
        )

        assert response.status_code == 401
        assert "Неправильный логин или пароль" in response.json()["detail"]

    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Авторизация несуществующего пользователя"""
        response = await client.post(
            "/api/auth/login",
            json={
                "login": "nonexistent",
                "password": "password123"
            }
        )

        assert response.status_code == 401
        assert "Неправильный логин или пароль" in response.json()["detail"]

    async def test_login_missing_credentials(self, client: AsyncClient):
        """Авторизация без учётных данных"""
        response = await client.post(
            "/api/auth/login",
            json={}
        )

        assert response.status_code == 422


class TestGetCurrentUser:
    """Тесты просмотра текущего пользователя GET /api/auth/me"""

    async def test_get_me_success(self, client: AsyncClient, test_user, auth_headers):
        """Успешное получение информации о текущем пользователе"""
        response = await client.get("/api/auth/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
        assert data["first_name"] == test_user.first_name
        assert data["last_name"] == test_user.last_name
        assert data["login"] == test_user.login
        assert "password" not in data

    async def test_get_me_unauthorized(self, client: AsyncClient):
        """Запрос без токена должен вернуть ошибку"""
        response = await client.get("/api/auth/me")

        assert response.status_code == 403

    async def test_get_me_invalid_token(self, client: AsyncClient):
        """Запрос с невалидным токеном"""
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401


class TestChangePassword:
    """Тесты смены пароля PUT /api/auth/change-password"""

    async def test_change_password_success(self, client: AsyncClient, test_user, auth_headers):
        """Успешная смена пароля"""
        response = await client.put(
            "/api/auth/change-password",
            headers=auth_headers,
            json={
                "old_password": "testpassword123",
                "new_password": "newpassword456"
            }
        )

        assert response.status_code == 200
        assert "успешно" in response.json()["message"]

        login_response = await client.post(
            "/api/auth/login",
            json={
                "login": "testuser",
                "password": "newpassword456"
            }
        )
        assert login_response.status_code == 200

    async def test_change_password_wrong_old_password(
        self, client: AsyncClient, auth_headers
    ):
        """Смена пароля с неправильным текущим паролем"""
        response = await client.put(
            "/api/auth/change-password",
            headers=auth_headers,
            json={
                "old_password": "wrongoldpassword",
                "new_password": "newpassword456"
            }
        )

        assert response.status_code == 401
        assert "Неправильный текущий пароль" in response.json()["detail"]

    async def test_change_password_unauthorized(self, client: AsyncClient):
        """Смена пароля без авторизации"""
        response = await client.put(
            "/api/auth/change-password",
            json={
                "old_password": "oldpassword",
                "new_password": "newpassword"
            }
        )

        assert response.status_code == 403

    async def test_change_password_missing_fields(
        self, client: AsyncClient, auth_headers
    ):
        """Смена пароля без обязательных полей"""
        response = await client.put(
            "/api/auth/change-password",
            headers=auth_headers,
            json={
                "old_password": "testpassword123"
            }
        )

        assert response.status_code == 422


class TestRefreshToken:
    """Тесты обновления токена POST /api/auth/refresh-token"""

    async def test_refresh_token_success(self, client: AsyncClient, test_user, auth_headers):
        """Успешное обновление токена"""
        response = await client.post(
            "/api/auth/refresh-token",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user_id"] == test_user.id

    async def test_refresh_token_new_token_works(
        self, client: AsyncClient, auth_headers
    ):
        """Новый токен должен работать"""
        refresh_response = await client.post(
            "/api/auth/refresh-token",
            headers=auth_headers
        )

        assert refresh_response.status_code == 200
        new_token = refresh_response.json()["access_token"]

        me_response = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {new_token}"}
        )
        assert me_response.status_code == 200

    async def test_refresh_token_unauthorized(self, client: AsyncClient):
        """Обновление токена без авторизации"""
        response = await client.post("/api/auth/refresh-token")

        assert response.status_code == 403

    async def test_refresh_token_invalid_token(self, client: AsyncClient):
        """Обновление с невалидным токеном"""
        response = await client.post(
            "/api/auth/refresh-token",
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401
