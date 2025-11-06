# API для транзакций

**Сохраните токен в переменную**

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "login": "estepanov",
    "password": "NewSecurePassword"
  }' | jq -r '.access_token')

echo "Token: $TOKEN"
```
## 1. Получить список транзакций с пагинацией и фильтрами
```bash
Базовый запрос
curl -X GET "http://localhost:8000/api/transactions?page=1&size=10" \
  -H "Authorization: Bearer $TOKEN" | jq

С фильтрами
curl -X GET "http://localhost:8000/api/transactions?page=1&size=10&name=продукты" \
  -H "Authorization: Bearer $TOKEN" | jq
```
## 2. Получить конкретную транзакцию
```bash
curl -X GET http://localhost:8000/api/transactions/1 \
  -H "Authorization: Bearer $TOKEN" | jq
```
## 3. Создать транзакцию
```bash
curl -X POST http://localhost:8000/api/transactions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "Покупка продуктов",
    "transaction_date": "2024-01-15",
    "group_id": 1
  }' | jq
```
## 4. Обновить транзакцию
```bash
curl -X PUT http://localhost:8000/api/transactions/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "Обновлённая покупка продуктов",
    "transaction_date": "2024-01-16"
  }' | jq
```
## 5. Удалить транзакцию
```bash
curl -X DELETE http://localhost:8000/api/transactions/1 \
  -H "Authorization: Bearer $TOKEN" | jq
```