# API для транзакций

**Сохраните токен в переменную**

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "login": "estepanov",
    "password": "SecurePassword"
  }' | jq -r '.access_token')

echo "Token: $TOKEN"
```
## 1. Получить список транзакций с пагинацией и фильтрами
```bash
Базовый запрос для конкретного пользователя
curl -X "GET" \
  "http://localhost:8000/api/transactions?page=1&size=20&type=expense&user_id=2" \
  -H "accept: application/json" \
  -H "Authorization: Bearer $TOKEN" | jq

С фильтрами (категория: еда)
curl -X "GET" \
  "http://localhost:8000/api/transactions?page=1&size=20&type=expense&category=Food&user_id=2" \
  -H "accept: application/json" \
  -H "Authorization: Bearer $TOKEN" | jq
```
## 2. Получить конкретную транзакцию
```bash
curl -X GET http://localhost:8000/api/transactions/12 \
  -H "Authorization: Bearer $TOKEN" | jq
```
## 3. Создать транзакцию
```bash
curl -X "POST" \
  "http://localhost:8000/api/transactions" \
  -H "accept: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
 -d '{
  "name": "Juice",
  "type": "expense",
  "category": "Food",
  "amount": 350,
  "transaction_date": "2025-11-09"
}' | jq
```
## 4. Обновить транзакцию
```bash
curl -X "PUT" \
  "http://localhost:8000/api/transactions/13" \
  -H "accept: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
  "name": "Potato",
  "type": "expense",
  "category": "Food",
  "amount": 150,
  "transaction_date": "2025-11-09",
  "user_id": 2,
  "group_id": 0
}' | jq
```
## 5. Удалить транзакцию
```bash
curl -X "DELETE" \
  "http://localhost:8000/api/transactions/7" \
  -H "accept: */*" \
  -H "Authorization: Bearer $TOKEN" | jq
```