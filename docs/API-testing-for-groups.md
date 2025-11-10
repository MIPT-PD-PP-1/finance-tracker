# API для групп

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

## 1. Создать группу

```bash
curl -X POST http://localhost:8000/api/groups \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "Тестовая группа"
  }' | jq
```

## 2. Получить список групп

```bash
curl -X GET http://localhost:8000/api/groups \
  -H "Authorization: Bearer $TOKEN" | jq
```

## 3. Посмотреть конкретную группу

```bash
curl -X GET http://localhost:8000/api/groups/1 \
  -H "Authorization: Bearer $TOKEN" | jq
```

## 4. Обновить группу

```bash
curl -X PUT http://localhost:8000/api/groups/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "Обновлённая тестовая группа"
  }' | jq
```

## 5. Добавить пользователя в группу

```bash
curl -X POST http://localhost:8000/api/groups/1/users/2 \
  -H "Authorization: Bearer $TOKEN" | jq
```

## 6. Список пользователей группы

```bash
curl -X GET http://localhost:8000/api/groups/1/users \
  -H "Authorization: Bearer $TOKEN" | jq
```

## 7. Удалить пользователя из группы

```bash
curl -X DELETE http://localhost:8000/api/groups/1/users/2 \
  -H "Authorization: Bearer $TOKEN" | jq
```

## 8. Удалить группу

```bash
curl -X DELETE http://localhost:8000/api/groups/1 \
  -H "Authorization: Bearer $TOKEN" | jq
```

