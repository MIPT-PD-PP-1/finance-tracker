"""
Тесты транзакций (Transactions Tests)

Эндпоинты:
- GET /api/transactions - Получить список транзакций
- POST /api/transactions - Создать транзакцию
- PUT /api/transactions/{id} - Редактировать транзакцию
- DELETE /api/transactions/{id} - Удалить транзакцию
- GET /api/transactions/{id} - Получить транзакцию по ID
"""
import pytest
from httpx import AsyncClient
from decimal import Decimal


class TestGetTransactions:
    """Тесты получения списка транзакций GET /api/transactions"""

    async def test_get_transactions_success(
        self, client: AsyncClient, auth_headers, test_transaction
    ):
        """Успешное получение списка транзакций"""
        response = await client.get("/api/transactions", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert "pages" in data
        assert len(data["items"]) >= 1

    async def test_get_transactions_empty(self, client: AsyncClient, auth_headers):
        """Получение пустого списка транзакций"""
        response = await client.get("/api/transactions", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    async def test_get_transactions_pagination(
        self, client: AsyncClient, auth_headers, test_user, db_session
    ):
        """Тест пагинации транзакций"""
        from app.models import Transaction, TransactionType

        for i in range(25):
            t = Transaction(
                name=f"Transaction {i}",
                type=TransactionType.expense,
                category="Test",
                amount=10.00,
                user_id=test_user.id
            )
            db_session.add(t)
        await db_session.commit()

        response = await client.get(
            "/api/transactions?page=1&size=10",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 10
        assert data["total"] == 25
        assert data["pages"] == 3

        response2 = await client.get(
            "/api/transactions?page=2&size=10",
            headers=auth_headers
        )
        assert response2.status_code == 200
        data2 = response2.json()
        assert len(data2["items"]) == 10

    async def test_get_transactions_filter_by_type(
        self, client: AsyncClient, auth_headers, test_user, db_session
    ):
        """Фильтрация транзакций по типу"""
        from app.models import Transaction, TransactionType

        t1 = Transaction(
            name="Income 1",
            type=TransactionType.income,
            category="Salary",
            amount=1000.00,
            user_id=test_user.id
        )
        t2 = Transaction(
            name="Expense 1",
            type=TransactionType.expense,
            category="Food",
            amount=50.00,
            user_id=test_user.id
        )
        db_session.add_all([t1, t2])
        await db_session.commit()

        response = await client.get(
            "/api/transactions?type=income",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["type"] == "income"

    async def test_get_transactions_filter_by_category(
        self, client: AsyncClient, auth_headers, test_user, db_session
    ):
        """Фильтрация транзакций по категории"""
        from app.models import Transaction, TransactionType

        t1 = Transaction(
            name="Food expense",
            type=TransactionType.expense,
            category="Food",
            amount=50.00,
            user_id=test_user.id
        )
        t2 = Transaction(
            name="Transport expense",
            type=TransactionType.expense,
            category="Transport",
            amount=30.00,
            user_id=test_user.id
        )
        db_session.add_all([t1, t2])
        await db_session.commit()

        response = await client.get(
            "/api/transactions?category=Food",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["category"] == "Food"

    async def test_get_transactions_unauthorized(self, client: AsyncClient):
        """Получение транзакций без авторизации"""
        response = await client.get("/api/transactions")

        assert response.status_code == 403


class TestCreateTransaction:
    """Тесты создания транзакции POST /api/transactions"""

    async def test_create_transaction_success(
        self, client: AsyncClient, auth_headers
    ):
        """Успешное создание транзакции"""
        response = await client.post(
            "/api/transactions",
            headers=auth_headers,
            json={
                "name": "New Transaction",
                "type": "expense",
                "category": "Shopping",
                "amount": 150.50,
                "description": "Test purchase"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Transaction"
        assert data["type"] == "expense"
        assert data["category"] == "Shopping"
        assert float(data["amount"]) == 150.50
        assert data["description"] == "Test purchase"
        assert "id" in data
        assert "transaction_datetime" in data

    async def test_create_transaction_income(
        self, client: AsyncClient, auth_headers
    ):
        """Создание транзакции типа income"""
        response = await client.post(
            "/api/transactions",
            headers=auth_headers,
            json={
                "name": "Salary",
                "type": "income",
                "category": "Work",
                "amount": 5000.00
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["type"] == "income"

    async def test_create_transaction_with_group(
        self, client: AsyncClient, auth_headers, test_group
    ):
        """Создание транзакции с привязкой к группе"""
        response = await client.post(
            "/api/transactions",
            headers=auth_headers,
            json={
                "name": "Group Transaction",
                "type": "expense",
                "category": "Shared",
                "amount": 200.00,
                "group_ids": [test_group.id]
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert len(data["groups"]) == 1
        assert data["groups"][0]["id"] == test_group.id

    async def test_create_transaction_missing_required_fields(
        self, client: AsyncClient, auth_headers
    ):
        """Создание транзакции без обязательных полей"""
        response = await client.post(
            "/api/transactions",
            headers=auth_headers,
            json={
                "name": "Incomplete"
            }
        )

        assert response.status_code == 422

    async def test_create_transaction_invalid_amount(
        self, client: AsyncClient, auth_headers
    ):
        """Создание транзакции с отрицательной суммой"""
        response = await client.post(
            "/api/transactions",
            headers=auth_headers,
            json={
                "name": "Invalid",
                "type": "expense",
                "category": "Test",
                "amount": -100.00
            }
        )

        assert response.status_code == 422

    async def test_create_transaction_zero_amount(
        self, client: AsyncClient, auth_headers
    ):
        """Создание транзакции с нулевой суммой"""
        response = await client.post(
            "/api/transactions",
            headers=auth_headers,
            json={
                "name": "Zero",
                "type": "expense",
                "category": "Test",
                "amount": 0
            }
        )

        assert response.status_code == 422

    async def test_create_transaction_unauthorized(self, client: AsyncClient):
        """Создание транзакции без авторизации"""
        response = await client.post(
            "/api/transactions",
            json={
                "name": "Test",
                "type": "expense",
                "category": "Test",
                "amount": 100.00
            }
        )

        assert response.status_code == 403


class TestGetTransaction:
    """Тесты получения транзакции по ID GET /api/transactions/{id}"""

    async def test_get_transaction_success(
        self, client: AsyncClient, auth_headers, test_transaction
    ):
        """Успешное получение транзакции по ID"""
        response = await client.get(
            f"/api/transactions/{test_transaction.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_transaction.id
        assert data["name"] == test_transaction.name

    async def test_get_transaction_not_found(
        self, client: AsyncClient, auth_headers
    ):
        """Получение несуществующей транзакции"""
        response = await client.get(
            "/api/transactions/99999",
            headers=auth_headers
        )

        assert response.status_code == 404

    async def test_get_transaction_other_user(
        self, client: AsyncClient, auth_headers2, test_transaction
    ):
        """Получение транзакции другого пользователя"""
        response = await client.get(
            f"/api/transactions/{test_transaction.id}",
            headers=auth_headers2
        )

        assert response.status_code == 404

    async def test_get_transaction_unauthorized(
        self, client: AsyncClient, test_transaction
    ):
        """Получение транзакции без авторизации"""
        response = await client.get(
            f"/api/transactions/{test_transaction.id}"
        )

        assert response.status_code == 403


class TestUpdateTransaction:
    """Тесты редактирования транзакции PUT /api/transactions/{id}"""

    async def test_update_transaction_success(
        self, client: AsyncClient, auth_headers, test_transaction
    ):
        """Успешное обновление транзакции"""
        response = await client.put(
            f"/api/transactions/{test_transaction.id}",
            headers=auth_headers,
            json={
                "name": "Updated Transaction",
                "amount": 200.00
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Transaction"
        assert float(data["amount"]) == 200.00

    async def test_update_transaction_type(
        self, client: AsyncClient, auth_headers, test_transaction
    ):
        """Обновление типа транзакции"""
        response = await client.put(
            f"/api/transactions/{test_transaction.id}",
            headers=auth_headers,
            json={
                "type": "income"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "income"

    async def test_update_transaction_category(
        self, client: AsyncClient, auth_headers, test_transaction
    ):
        """Обновление категории транзакции"""
        response = await client.put(
            f"/api/transactions/{test_transaction.id}",
            headers=auth_headers,
            json={
                "category": "New Category"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["category"] == "New Category"

    async def test_update_transaction_add_group(
        self, client: AsyncClient, auth_headers, test_transaction, test_group
    ):
        """Добавление группы к транзакции"""
        response = await client.put(
            f"/api/transactions/{test_transaction.id}",
            headers=auth_headers,
            json={
                "group_ids": [test_group.id]
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["groups"]) == 1
        assert data["groups"][0]["id"] == test_group.id

    async def test_update_transaction_remove_groups(
        self, client: AsyncClient, auth_headers, test_transaction_with_group
    ):
        """Удаление групп у транзакции"""
        response = await client.put(
            f"/api/transactions/{test_transaction_with_group.id}",
            headers=auth_headers,
            json={
                "group_ids": []
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["groups"]) == 0

    async def test_update_transaction_not_found(
        self, client: AsyncClient, auth_headers
    ):
        """Обновление несуществующей транзакции"""
        response = await client.put(
            "/api/transactions/99999",
            headers=auth_headers,
            json={"name": "Updated"}
        )

        assert response.status_code == 404

    async def test_update_transaction_other_user(
        self, client: AsyncClient, auth_headers2, test_transaction
    ):
        """Обновление транзакции другого пользователя"""
        response = await client.put(
            f"/api/transactions/{test_transaction.id}",
            headers=auth_headers2,
            json={"name": "Hacked"}
        )

        assert response.status_code == 404

    async def test_update_transaction_invalid_amount(
        self, client: AsyncClient, auth_headers, test_transaction
    ):
        """Обновление транзакции с невалидной суммой"""
        response = await client.put(
            f"/api/transactions/{test_transaction.id}",
            headers=auth_headers,
            json={"amount": -50.00}
        )

        assert response.status_code == 422

    async def test_update_transaction_unauthorized(
        self, client: AsyncClient, test_transaction
    ):
        """Обновление транзакции без авторизации"""
        response = await client.put(
            f"/api/transactions/{test_transaction.id}",
            json={"name": "Updated"}
        )

        assert response.status_code == 403


class TestDeleteTransaction:
    """Тесты удаления транзакции DELETE /api/transactions/{id}"""

    async def test_delete_transaction_success(
        self, client: AsyncClient, auth_headers, test_transaction
    ):
        """Успешное удаление транзакции"""
        response = await client.delete(
            f"/api/transactions/{test_transaction.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        assert "успешно удалена" in response.json()["message"]

        get_response = await client.get(
            f"/api/transactions/{test_transaction.id}",
            headers=auth_headers
        )
        assert get_response.status_code == 404

    async def test_delete_transaction_not_found(
        self, client: AsyncClient, auth_headers
    ):
        """Удаление несуществующей транзакции"""
        response = await client.delete(
            "/api/transactions/99999",
            headers=auth_headers
        )

        assert response.status_code == 404

    async def test_delete_transaction_other_user(
        self, client: AsyncClient, auth_headers2, test_transaction
    ):
        """Удаление транзакции другого пользователя"""
        response = await client.delete(
            f"/api/transactions/{test_transaction.id}",
            headers=auth_headers2
        )

        assert response.status_code == 404

    async def test_delete_transaction_unauthorized(
        self, client: AsyncClient, test_transaction
    ):
        """Удаление транзакции без авторизации"""
        response = await client.delete(
            f"/api/transactions/{test_transaction.id}"
        )

        assert response.status_code == 403


class TestGetGroupTransactions:
    """Тесты получения транзакций группы GET /api/transactions/group/{group_id}"""

    async def test_get_group_transactions_success(
        self, client: AsyncClient, auth_headers, test_group, test_transaction_with_group
    ):
        """Успешное получение транзакций группы"""
        response = await client.get(
            f"/api/transactions/group/{test_group.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 1

    async def test_get_group_transactions_empty(
        self, client: AsyncClient, auth_headers, test_group
    ):
        """Получение пустого списка транзакций группы"""
        response = await client.get(
            f"/api/transactions/group/{test_group.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []

    async def test_get_group_transactions_not_found(
        self, client: AsyncClient, auth_headers
    ):
        """Получение транзакций несуществующей группы"""
        response = await client.get(
            "/api/transactions/group/99999",
            headers=auth_headers
        )

        assert response.status_code == 404

    async def test_get_group_transactions_forbidden(
        self, client: AsyncClient, auth_headers2, test_group
    ):
        """Получение транзакций группы не членом группы"""
        response = await client.get(
            f"/api/transactions/group/{test_group.id}",
            headers=auth_headers2
        )

        assert response.status_code == 403

    async def test_get_group_transactions_unauthorized(
        self, client: AsyncClient, test_group
    ):
        """Получение транзакций группы без авторизации"""
        response = await client.get(
            f"/api/transactions/group/{test_group.id}"
        )

        assert response.status_code == 403
