from datetime import datetime, timezone
from decimal import Decimal

from tests.helpers import create_authenticated_group_members, create_authenticated_user


def test_get_settlement_suggestions_success(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense',
        'total_amount': 20,
        'split_type': 'equal',
        'expense_date': datetime.now(timezone.utc).isoformat(),
        'participants': [
            {'user_id': owner['user']['id']},
            {'user_id': member['user']['id']},
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=expense_payload, headers=owner['headers'])
    assert response.status_code == 200

    response = client.get(f'/groups/{group_id}/settlement-suggestions', headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()

    suggestion_group_id = data['group_id']
    assert suggestion_group_id == group_id
    assert len(data['suggestions']) == 1

    suggestion = data['suggestions'][0]
    suggestion_payer_id = suggestion['payer_id']
    suggestion_receiver_id = suggestion['receiver_id']

    assert suggestion_payer_id == member['user']['id']
    assert suggestion_receiver_id == owner['user']['id']
    assert Decimal(suggestion['amount']) == Decimal(10)

def test_get_settlement_suggestions_forbidden_for_non_member(client):
    context = create_authenticated_group_members(client)

    group_id = context['group']['id']

    new_user = create_authenticated_user(
        client,
        email='new_user@example.com',
        username='new user',
        password='long_password')

    response = client.get(f'/groups/{group_id}/settlement-suggestions', headers=new_user['headers'])
    assert response.status_code == 403

def test_get_settlement_suggestions_empty_with_no_expenses(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    group_id = context['group']['id']

    response = client.get(f'/groups/{group_id}/settlement-suggestions', headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()

    assert data['group_id'] == group_id

    suggestions = data['suggestions']
    assert len(suggestions) == 0

def test_get_settlement_suggestions_empty_when_expense_settled(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense',
        'total_amount': 20,
        'split_type': 'equal',
        'expense_date': datetime.now(timezone.utc).isoformat(),
        'participants': [
            {'user_id': owner['user']['id']},
            {'user_id': member['user']['id']},
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=expense_payload, headers=owner['headers'])
    assert response.status_code == 200

    settlement_payload = {
        'payer_id': member['user']['id'],
        'receiver_id': owner['user']['id'],
        'amount': 10,
        'settled_at': datetime.now(timezone.utc).isoformat(),
    }

    response = client.post(f'/groups/{group_id}/settlements', json=settlement_payload, headers=member['headers'])
    assert response.status_code == 200

    response = client.get(f'/groups/{group_id}/settlement-suggestions', headers=member['headers'])
    assert response.status_code == 200

    data = response.json()
    suggestions = data['suggestions']

    assert len(suggestions) == 0

def test_get_settlement_suggestions_multiple_debtors_and_creditors(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    new_user = create_authenticated_user(
        client,
        email='new_user@example.com',
        username='new user',
        password='long_password')

    another_user = create_authenticated_user(
        client,
        email='another_user@example.com',
        username='another user',
        password='long_password'
    )

    response = client.post(f'/groups/{group_id}/members', json={'user_id': new_user['user']['id']}, headers=owner['headers'])
    assert response.status_code == 200
    response = client.post(f'/groups/{group_id}/members', json={'user_id': another_user['user']['id']}, headers=owner['headers'])
    assert response.status_code == 200

    expense_one_payload = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense',
        'total_amount': 30,
        'split_type': 'equal',
        'expense_date': datetime.now(timezone.utc).isoformat(),
        'participants': [
            {'user_id': owner['user']['id']},
            {'user_id': member['user']['id']},
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=expense_one_payload, headers=owner['headers'])
    assert response.status_code == 200

    expense_two_payload = {
        'payer_id': new_user['user']['id'],
        'title': 'test_expense',
        'total_amount': 50,
        'split_type': 'equal',
        'expense_date': datetime.now(timezone.utc).isoformat(),
        'participants': [
            {'user_id': new_user['user']['id']},
            {'user_id': member['user']['id']},
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=expense_two_payload, headers=owner['headers'])
    assert response.status_code == 200

    expense_three_payload = {
        'payer_id': new_user['user']['id'],
        'title': 'test_expense',
        'total_amount': 10,
        'split_type': 'equal',
        'expense_date': datetime.now(timezone.utc).isoformat(),
        'participants': [
            {'user_id': another_user['user']['id']},
            {'user_id': new_user['user']['id']},
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=expense_three_payload, headers=owner['headers'])
    assert response.status_code == 200

    response = client.get(f'/groups/{group_id}/balances', headers=owner['headers'])
    assert response.status_code == 200

    data = response.json()
    balances = data['balances']

    owner_balance = next(balance for balance in balances if balance['user_id'] == owner['user']['id'] )
    member_balance = next(balance for balance in balances if balance['user_id'] == member['user']['id'] )
    new_user_balance = next(balance for balance in balances if balance['user_id'] == new_user['user']['id'])
    another_user_balance = next(balance for balance in balances if balance['user_id'] == another_user['user']['id'])

    response = client.get(f'/groups/{group_id}/settlement-suggestions', headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    suggestions = data['suggestions']

    for suggestion in suggestions:
        assert Decimal(suggestion['amount']) > 0

    expected_payer_ids = [
        member['user']['id'],
        another_user['user']['id'],
    ]

    for suggestion in suggestions:
        assert suggestion['payer_id'] in expected_payer_ids

    expected_receiver_ids = [
        owner['user']['id'],
        new_user['user']['id']
    ]

    for suggestion in suggestions:
        assert suggestion['receiver_id'] in expected_receiver_ids

    paid_by_user = {}
    received_by_user = {}

    for suggestion in suggestions:
        payer_id = suggestion['payer_id']
        receiver_id = suggestion['receiver_id']
        amount = Decimal(suggestion['amount'])

        paid_by_user[payer_id] = paid_by_user.get(payer_id, Decimal('0')) + amount
        received_by_user[receiver_id] = received_by_user.get(receiver_id, Decimal('0')) + amount

    assert paid_by_user[member['user']['id']] == -Decimal(member_balance['amount'])
    assert paid_by_user[another_user['user']['id']] == -Decimal(another_user_balance['amount'])
    assert received_by_user[owner['user']['id']] == Decimal(owner_balance['amount'])
    assert received_by_user[new_user['user']['id']] == Decimal(new_user_balance['amount'])