import uuid

from sqlalchemy.orm import Session
from app.models import User
from app.schemas.settlement import SettlementSuggestionsResponse, SettlementSuggestion
from app.services.helpers import calculate_group_balances


def get_settlement_suggestions(db: Session, current_user: User, group_id: uuid.UUID) -> SettlementSuggestionsResponse:
    group_balances = calculate_group_balances(db, current_user, group_id)

    debtors = []
    creditors = []

    for user_id, amount in group_balances.items():
        if amount < 0:
            debtors.append({'user_id': user_id, 'amount': abs(amount)})
        elif amount > 0:
            creditors.append({'user_id': user_id, 'amount': amount})

    sorted_debtors = sorted(debtors, key=lambda k: str(k['user_id']))
    sorted_creditors = sorted(creditors, key=lambda k: str(k['user_id']))

    debtor_index = 0
    creditor_index = 0
    suggestions = []

    while debtor_index < len(sorted_debtors) and creditor_index < len(sorted_creditors):
        debtor = sorted_debtors[debtor_index]
        creditor = sorted_creditors[creditor_index]

        amount = min(debtor['amount'], creditor['amount'])

        suggestions.append(SettlementSuggestion(
            payer_id=debtor['user_id'],
            receiver_id=creditor['user_id'],
            amount=amount,
        ))

        debtor['amount'] -= amount
        creditor['amount'] -= amount

        if debtor['amount'] == 0:
            debtor_index += 1
        if creditor['amount'] == 0:
            creditor_index += 1

    return SettlementSuggestionsResponse(
        group_id=group_id,
        suggestions=suggestions
    )


