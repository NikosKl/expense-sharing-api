from datetime import datetime, timezone

from app.db.session import DBSession
from app.services.recurring_expense_service import process_due_recurring_expenses


def main() -> None:
    db = DBSession()
    now = datetime.now(timezone.utc)

    try:
        expenses_processed_count = process_due_recurring_expenses(db, now)

        print(f'{expenses_processed_count} expenses processed.')

    finally:
        db.close()


if __name__ == "__main__":
    main()
