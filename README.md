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

### 🌐 API

#### 🔐 Аутентификации

- 📝 Регистрация
- 🔑 Аутентификация
- 🔁 Обновление токена
- 🔒 Смена пароля


#### 💼 Транзакции

- ➕ Создание
- ✏️ Редактирование
- 🗑️ Удаление
- 📚 Чтение


#### 👥 Группы

- ➕ Создание
- ✏️ Редактирование
- 🗑️ Удаление
- 📚 Чтение
- 📊 Аналитика
