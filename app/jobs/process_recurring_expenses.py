import logging
from datetime import datetime, timezone

from app.core.logging import configure_logging
from app.db.session import DBSession
from app.services.recurring_expense_service import process_due_recurring_expenses


def main() -> None:
    configure_logging()
    logger = logging.getLogger('app.jobs.process_recurring_expenses')

    db = DBSession()
    now = datetime.now(timezone.utc)

    try:
        expenses_processed_count = process_due_recurring_expenses(db, now)

        logger.info('%s recurring expenses processed', expenses_processed_count)
    except Exception:
        logger.exception('Recurring expense processor failed')
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
