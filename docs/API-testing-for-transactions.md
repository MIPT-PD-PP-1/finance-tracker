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

**Транзакция без группы**

```bash
curl -X POST http://localhost:8000/api/transactions \
  -H "accept: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
  "name": "Pizza",
  "type": "expense",
  "category": "Food",
  "amount": 590,
  "description": "Pizza delivery",
  "group_ids": []
}' | jq
```

**Транзакция с добавлением в одну группу**

```bash
curl -X POST http://localhost:8000/api/transactions \
  -H "accept: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
  "name": "Phone",
  "type": "expense",
  "category": "Tech",
  "amount": 22590,
  "description": "My new phone",
  "group_ids": [1]
}' | jq
```

**Транзакция с добавлением сразу в несколько групп**

```bash
curl -X POST http://localhost:8000/api/transactions \
  -H "accept: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
  "name": "Sneakers",
  "type": "expense",
  "category": "Clothes",
  "amount": 11590,
  "description": "Adidas",
  "group_ids": [1, 2]
}' | jq
```

## 2. Обновить транзакцию
```bash
curl -X PUT http://localhost:8000/api/transactions/1 \
  -H "accept: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
  "name": "New Pizza",
  "type": "expense",
  "category": "Food",
  "amount": 690,
  "transaction_datetime": "2025-11-13T20:59:08.221Z",
  "description": "New description ",
  "group_ids": [
    1, 2
  ]
}' | jq
```

## 3. Посмотреть транзакции пользователя

**Посмотреть транзакции**

```bash
curl -X GET "http://localhost:8000/api/transactions?page=1&size=20" \
  -H "accept: application/json" \
  -H "Authorization: Bearer $TOKEN" | jq
```

**С фильтрами (категория: еда)**

```bash
curl -X GET "http://localhost:8000/api/transactions?page=1&size=20&category=Food" \
  -H "accept: application/json" \
  -H "Authorization: Bearer $TOKEN" | jq
```

**Конкретная транзакция**

```bash
curl -X GET http://localhost:8000/api/transactions/1 \
  -H "accept: application/json" \
  -H "Authorization: Bearer $TOKEN" | jq
```

## 4. Удалить транзакцию

```bash
curl -X DELETE http://localhost:8000/api/transactions/1 \
  -H "accept: */*" \
  -H "Authorization: Bearer $TOKEN" | jq
```

## 5. Получить транзакции группы
```bash
curl -X GET "http://localhost:8000/api/transactions/group/1?page=1&size=20" \
  -H "accept: application/json" \
  -H "Authorization: Bearer $TOKEN" | jq
```

## 6. Получить статистику группы
```bash
curl -X GET "http://localhost:8000/api/transactions/group/1/stats" \
  -H "accept: application/json" \
  -H "Authorization: Bearer $TOKEN" | jq
```
