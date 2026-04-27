import uuid
from datetime import timezone, datetime
from decimal import Decimal
from tests.helpers import create_authenticated_group_members, create_authenticated_user


def test_group_balance_data(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense',
        'total_amount': 100,
        'split_type': 'equal',
        'expense_date': datetime.now(timezone.utc).isoformat(),
        'participants': [
            {'user_id': owner['user']['id']},
            {'user_id': member['user']['id']},
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=expense_payload, headers=owner['headers'])
    assert response.status_code == 200

    response = client.get(f'/groups/{group_id}/balances', headers=owner['headers'])
    assert response.status_code == 200

    data = response.json()
    assert data['group_id'] == group_id

    balances = data['balances']
    assert len(balances) == 2
    for balance in balances:
        assert set(balance.keys()) == {'user_id', 'amount'}

def test_group_single_expense_balance(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense',
        'total_amount': 100,
        'split_type': 'equal',
        'expense_date': datetime.now(timezone.utc).isoformat(),
        'participants': [
            {'user_id': owner['user']['id']},
            {'user_id': member['user']['id']},
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=expense_payload, headers=owner['headers'])
    assert response.status_code == 200

    response = client.get(f'/groups/{group_id}/balances', headers=owner['headers'])
    assert response.status_code == 200

    data = response.json()
    balances = data['balances']

    owner_balance = next(balance for balance in balances if balance['user_id'] == owner['user']['id'])
    assert Decimal(owner_balance['amount']) > 0
    assert Decimal(owner_balance['amount']) == Decimal('50')
    member_balance = next(balance for balance in balances if balance['user_id'] == member['user']['id'])
    assert Decimal(member_balance['amount']) < 0
    assert Decimal(member_balance['amount']) == Decimal('-50')

def test_group_multiple_expenses_balance(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    expense_payload_a = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense_a',
        'total_amount': 30,
        'split_type': 'equal',
        'expense_date': datetime.now(timezone.utc).isoformat(),
        'participants': [
            {'user_id': owner['user']['id']},
            {'user_id': member['user']['id']},
        ]
    }

    expense_payload_b = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense_a',
        'total_amount': 20,
        'split_type': 'equal',
        'expense_date': datetime.now(timezone.utc).isoformat(),
        'participants': [
            {'user_id': owner['user']['id']},
            {'user_id': member['user']['id']},
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=expense_payload_a, headers=owner['headers'])
    assert response.status_code == 200
    response = client.post(f'/groups/{group_id}/expenses', json=expense_payload_b, headers=owner['headers'])
    assert response.status_code == 200

    response = client.get(f'/groups/{group_id}/balances', headers=owner['headers'])
    assert response.status_code == 200

    data = response.json()
    balances = data['balances']

    owner_balance = next(balance for balance in balances if balance['user_id'] == owner['user']['id'])
    assert Decimal(owner_balance['amount']) == Decimal('25')
    member_balance = next(balance for balance in balances if balance['user_id'] == member['user']['id'])
    assert Decimal(member_balance['amount']) == Decimal('-25')

def test_zero_balance_member_is_included(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    new_member = create_authenticated_user(
        client,
        email='new_member@example.com',
        username='new_member',
        password='long_password',

    )

    response = client.post(f'/groups/{group_id}/members', json={'user_id': new_member['user']['id']}, headers=owner['headers'])
    assert response.status_code == 200

    expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense',
        'total_amount': 100,
        'split_type': 'equal',
        'expense_date': datetime.now(timezone.utc).isoformat(),
        'participants': [
            {'user_id': owner['user']['id']},
            {'user_id': member['user']['id']},
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=expense_payload, headers=owner['headers'])
    assert response.status_code == 200

    response = client.get(f'/groups/{group_id}/balances', headers=owner['headers'])
    assert response.status_code == 200

    data = response.json()
    balances = data['balances']

    owner_balance = next(balance for balance in balances if balance['user_id'] == owner['user']['id'])
    assert Decimal(owner_balance['amount']) == Decimal('50')
    member_balance = next(balance for balance in balances if balance['user_id'] == member['user']['id'])
    assert Decimal(member_balance['amount']) == Decimal('-50')
    new_member_balance = next(balance for balance in balances if balance['user_id'] == new_member['user']['id'])
    assert Decimal(new_member_balance['amount']) == Decimal('0')

def test_balances_is_sorted(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    new_member = create_authenticated_user(
        client,
        email='new_member@example.com',
        username='new_member',
        password='long_password',

    )

    response = client.post(f'/groups/{group_id}/members', json={'user_id': new_member['user']['id']}, headers=owner['headers'])
    assert response.status_code == 200

    expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense',
        'total_amount': 100,
        'split_type': 'equal',
        'expense_date': datetime.now(timezone.utc).isoformat(),
        'participants': [
            {'user_id': owner['user']['id']},
            {'user_id': member['user']['id']},
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=expense_payload, headers=owner['headers'])
    assert response.status_code == 200

    response = client.get(f'/groups/{group_id}/balances', headers=owner['headers'])
    assert response.status_code == 200

    data = response.json()
    balances = data['balances']
    returned_user_ids = [balance['user_id'] for balance in balances]
    assert returned_user_ids == sorted(returned_user_ids)

def test_balance_non_member(client):
    context = create_authenticated_group_members(client)

    group_id = context['group']['id']

    user = create_authenticated_user(
        client,
        email='user@example.com',
        username='user',
        password='long_password',

    )

    response = client.get(f'/groups/{group_id}/balances', headers=user['headers'])
    assert response.status_code == 403

def test_balance_nonexistent_group(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']

    new_group_id = uuid.uuid4()

    response = client.get(f'/groups/{new_group_id}/balances', headers=owner['headers'])
    assert response.status_code == 404