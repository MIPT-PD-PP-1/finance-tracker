# 💸 Приложение для отслеживания расходов

Приложение для управления личными финансами, позволяющее пользователям фиксировать доходы и расходы и получать аналитику по ним. 📊

## ✨ Функции

- ➕ Добавление транзакций;
- 📈 Аналитика по категориям и периодам;
- 🥧 Визуализация данных;
- 🧹 Сортировка транзакций по дате и категориям;
- 📤 Экспорт данных в `.csv` и `.xlsx`;
- ⏰ Напоминания о регулярных платежах.

## 🏗️ Архитектура

### 🌐 API

#### 🔐 Аутентификации

| Эндпоинт          | Метод | Описание                    | Путь                      |
| ----------------- | ----- | --------------------------- | ------------------------- |
| Регистрация       | POST  | Создать нового пользователя | /api/auth/register        |
| Авторизация       | POST  | Вход и получение токенов    | /api/auth/login           |
| Смена пароля      | PUT   | Смена пароля                | /api/auth/change-password |
| Обновление токена | POST  | Обновить токена             | /api/auth/refresh-token   |

#### 💼 Транзакции

| Эндпоинт                 | Метод  | Описание                                   | Путь                   |
| ------------------------ | ------ | ------------------------------------------ | ---------------------- |
| Получить список          | GET    | Список транзакций с пагинацией и фильтрами | /api/transactions      |
| Создать транзакцию       | POST   | Добавить доход или расход                  | /api/transactions      |
| Редактировать транзакцию | PUT    | Обновить данные транзакции                 | /api/transactions/{id} |
| Удалить транзакцию       | DELETE | Удалить транзакцию                         | /api/transactions/{id} |

#### 👥 Группы

| Эндпоинт             | Метод  | Описание                       | Путь                       |
| -------------------- | ------ | ------------------------------ | -------------------------- |
| Получить список      | GET    | Список групп пользователей     | /api/groups                |
| Создать группу       | POST   | Создать новую группу           | /api/groups                |
| Редактировать группу | PUT    | Обновить данные группы         | /api/groups/{id}           |
| Удалить группу       | DELETE | Удалить группу                 | /api/groups/{id}           |
| Получить аналитику   | GET    | Аналитика по расходам в группе | /api/groups/{id}/analytics |

### 🗄️ База данных

```mermaid
erDiagram
    USER {
        int id PK
        string first_name
        string last_name
        string login
        string password
    }

    GROUP {
        int id PK
        string name
        int owner_id FK
    }

    TRANSACTION {
        int id PK
        string name
        string type "income/expense"
        string category
        decimal amount
        date transaction_date
        int user_id FK
        int group_id FK
    }

    USER ||--o{ GROUP : "belongs"
    USER ||--o{ TRANSACTION : "creates"
    GROUP ||--o{ TRANSACTION : "contains"
```

## 🚀 Запуск проекта

1. Клонирование репозитория
```bash
git clone git@github.com:MIPT-PD-PP-1/finance-tracker.git
cd finance-tracker
```

2. Сборка и запуск
```bash
docker compose up -d --build
```

3. Проверка состояния
```bash
docker compose ps
```

4. Остановка
```bash
docker compose down
```

