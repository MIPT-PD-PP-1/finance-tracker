import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import AsyncGenerator
import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/finance_tracker_test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-at-least-32-characters")

from app.database import Base, get_db
from app.main import app
from app.utils import hash_password, create_access_token
from app.models import User, Group, Transaction, TransactionType

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", os.getenv("DATABASE_URL"))

engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False
)

TestSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    user = User(
        first_name="Test",
        last_name="User",
        login="testuser",
        password=hash_password("testpassword123")
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_user2(db_session: AsyncSession) -> User:
    user = User(
        first_name="Test2",
        last_name="User2",
        login="testuser2",
        password=hash_password("testpassword456")
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_headers(test_user: User) -> dict:
    token = create_access_token(data={"sub": test_user.id})
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def auth_headers2(test_user2: User) -> dict:
    token = create_access_token(data={"sub": test_user2.id})
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def test_group(db_session: AsyncSession, test_user: User) -> Group:
    group = Group(
        name="Test Group",
        owner_id=test_user.id
    )
    group.users.append(test_user)
    db_session.add(group)
    await db_session.commit()
    await db_session.refresh(group)
    return group


@pytest_asyncio.fixture
async def test_transaction(db_session: AsyncSession, test_user: User) -> Transaction:
    transaction = Transaction(
        name="Test Transaction",
        type=TransactionType.expense,
        category="Food",
        amount=100.50,
        description="Test description",
        user_id=test_user.id
    )
    db_session.add(transaction)
    await db_session.commit()
    await db_session.refresh(transaction)
    return transaction


@pytest_asyncio.fixture
async def test_transaction_with_group(
    db_session: AsyncSession,
    test_user: User,
    test_group: Group
) -> Transaction:
    transaction = Transaction(
        name="Group Transaction",
        type=TransactionType.income,
        category="Salary",
        amount=5000.00,
        description="Monthly salary",
        user_id=test_user.id
    )
    transaction.groups.append(test_group)
    db_session.add(transaction)
    await db_session.commit()
    await db_session.refresh(transaction)
    return transaction
