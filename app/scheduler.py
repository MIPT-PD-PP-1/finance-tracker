from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from datetime import datetime, timedelta
from app.models import Transaction
from app.database import AsyncSessionLocal

scheduler = AsyncIOScheduler()


async def process_recurring_payments():
    async with AsyncSessionLocal() as db:
        try:
            now = datetime.utcnow()

            result = await db.execute(
                select(Transaction).where(
                    Transaction.is_recurring == True,
                    Transaction.next_run <= now
                )
            )
            transactions = result.scalars().all()

            if not transactions:
                return

            for rec_transaction in transactions:
                new_transaction = Transaction(
                    name=rec_transaction.name,
                    type=rec_transaction.type,
                    category=rec_transaction.category,
                    amount=rec_transaction.amount,
                    description=rec_transaction.description,
                    user_id=rec_transaction.user_id,
                    groups=rec_transaction.groups,
                    is_recurring=False,
                    created_at=datetime.utcnow(),
                )
                db.add(new_transaction)


                if hasattr(rec_transaction, 'recurring_period_days'):
                    rec_transaction.next_run = now + timedelta(
                        days=rec_transaction.recurring_period_days
                    )

            await db.commit()
            print(f"Обработано {len(payments)} повторяющихся платежей")

        except Exception as e:
            await db.rollback()
            print(f"Ошибка при обработке повторяющихся платежей: {e}")
            raise

async def check_reminders():
    async with AsyncSessionLocal() as db:

        try:
            now = datetime.utcnow()

            result = await db.execute(
                select(Transaction).where(
                    Transaction.is_recurring == True,
                    Transaction.next_run.isnot(None)
                )
            )
            transactions = result.scalars().all()

            if not transactions:
                return

            has_reminders = False

            for transaction in transactions:
                days_left = (transaction.next_run.date() - now.date()).days

                if days_left == 0:
                    print(f"🔔 СЕГОДНЯ: {transaction.name} - {transaction.amount} руб.")
                    has_reminders = True
                elif days_left == 1:
                    print(f"📅 ЗАВТРА: {transaction.name} - {transaction.amount} руб.")
                    has_reminders = True
                elif days_left == 3:
                    print(f"⏳ ЧЕРЕЗ 3 ДНЯ: {transaction.name} - {transaction.amount} руб.")
                    has_reminders = True
                elif days_left == 7:
                    print(f"🗓️ ЧЕРЕЗ НЕДЕЛЮ: {transaction.name} - {transaction.amount} руб.")
                    has_reminders = True
                elif days_left < 0:
                    print(f"❌ ПРОСРОЧЕНО ({abs(days_left)} дней): {transaction.name} - {transaction.amount} руб.")
                    has_reminders = True

            if not has_reminders:
                print("📭 Ближайших напоминаний нет")

            print("=" * 60 + "\n")

        except Exception as e:
            print(f"❌ Ошибка при проверке напоминаний: {e}")


def start_scheduler():
    scheduler.add_job(
        process_recurring_payments,
        'cron',
        hour=0,
        minute=0,
        id='process_recurring_payments',
        replace_existing=True
    )

    scheduler.add_job(
        check_reminders,
        'cron',
        hour=9,
        minute=0,
        id='check_payment_reminders_morning',
        replace_existing=True
    )

    scheduler.add_job(
        check_reminders,
        'cron',
        hour=18,
        minute=0,
        id='check_payment_reminders_evening',
        replace_existing=True
    )

    scheduler.start()


def shutdown_scheduler():
    scheduler.shutdown()
