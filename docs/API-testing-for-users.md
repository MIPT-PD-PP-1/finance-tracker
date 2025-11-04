# API для пользователей

## 1. Регистрация нового пользователя

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Егор",
    "last_name": "Степанов",
    "login": "estepanov",
    "password": "SecurePassword"
  }' | jq
```

## 2. Вход и получение токена

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "login": "estepanov",
    "password": "SecurePassword"
  }' | jq
```

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

## 3. Просмотр пользователя

```bash
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer $TOKEN" | jq
```

## 4. Смена пароля

```bash
curl -X PUT http://localhost:8000/api/auth/change-password \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "old_password": "SecurePassword",
    "new_password": "NewSecurePassword"
  }' | jq
```

## 5. Обновление токена

```bash
curl -X POST http://localhost:8000/api/auth/refresh-token \
  -H "Authorization: Bearer $TOKEN" | jq
```

