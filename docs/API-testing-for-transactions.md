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

## 1. Создать транзакцию
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
  "group_id": 7
}' | jq
```

## 2. Обновить транзакцию
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
  "group_id": 7
}' | jq
```

## 3. Посмотреть транзакции

**Посмотреть транзакции**

```bash
curl -X GET "http://localhost:8000/api/transactions?page=1&size=20" \
  -H "Authorization: Bearer $TOKEN" | jq
```

**С фильтрами (категория: еда)**

```bash
curl -X GET "http://localhost:8000/api/transactions?page=1&size=20&category=Food" \
  -H "Authorization: Bearer $TOKEN" | jq
```

**Конкретная транзакция**

```bash
curl -X GET http://localhost:8000/api/transactions/1 \
  -H "Authorization: Bearer $TOKEN" | jq
```

## 4. Удалить транзакцию

```bash
curl -X DELETE http://localhost:8000/api/transactions/1 \
  -H "Authorization: Bearer $TOKEN" | jq
```

## 5. Получить транзакции группы
```bash
curl -X "GET" \
  "http://localhost:8000/api/transactions/group/7?page=1&size=20&type=expense&user_id=2" \
  -H "accept: application/json" \
  -H "Authorization: Bearer $TOKEN" | jq
```

## 6. Получить статистику группы
```bash
curl -X "GET" \
  "http://localhost:8000/api/transactions/group/7/stats" \
  -H "accept: application/json" \
  -H "Authorization: Bearer $TOKEN" | jq
```
