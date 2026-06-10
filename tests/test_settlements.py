import uuid
from datetime import timezone, datetime
from decimal import Decimal
from tests.helpers import create_authenticated_group_members, create_authenticated_user


def test_create_settlement_success(client):
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

    settlement_payload = {
        'payer_id': member['user']['id'],
        'receiver_id': owner['user']['id'],
        'amount': 13,
        'settled_at': datetime.now(timezone.utc).isoformat(),
    }

    response = client.post(f'/groups/{group_id}/settlements', json=settlement_payload, headers=member['headers'])
    assert response.status_code == 200

    data = response.json()
    assert data['group_id'] == group_id
    assert 'payer_id' in data
    assert data['payer_id'] == member['user']['id']
    assert 'receiver_id' in data
    assert data['receiver_id'] == owner['user']['id']
    assert Decimal(data['amount']) == Decimal(settlement_payload['amount'])
    assert data['note'] is None
    assert 'settled_at' in data
    assert 'created_at' in data

    assert 'created_by' in data
    assert data['created_by'] == member['user']['id']
    assert data['created_by'] == data['payer_id']

def test_non_payer_cannot_create_settlement(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    settlement_payload = {
        'payer_id': member['user']['id'],
        'receiver_id': owner['user']['id'],
        'amount': 13,
        'settled_at': datetime.now(timezone.utc).isoformat(),
    }

    response = client.post(f'/groups/{group_id}/settlements', json=settlement_payload, headers=owner['headers'])
    assert response.status_code == 403

def test_receiver_not_group_member(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    group_id = context['group']['id']

    new_user = create_authenticated_user(
        client,
        email='new_user@example.com',
        username='new_user',
        password='long_password'
    )

    settlement_payload = {
        'payer_id': owner['user']['id'],
        'receiver_id': new_user['user']['id'],
        'amount': 13,
        'settled_at': datetime.now(timezone.utc).isoformat(),
    }

    response = client.post(f'/groups/{group_id}/settlements', json=settlement_payload, headers=owner['headers'])
    assert response.status_code == 400

def test_current_user_not_group_member(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    new_user = create_authenticated_user(
        client,
        email='new_user@example.com',
        username='new_user',
        password='long_password'
    )

    settlement_payload = {
        'payer_id': owner['user']['id'],
        'receiver_id': member['user']['id'],
        'amount': 13,
        'settled_at': datetime.now(timezone.utc).isoformat(),
    }

    response = client.post(f'/groups/{group_id}/settlements', json=settlement_payload, headers=new_user['headers'])
    assert response.status_code == 403

def test_nonexistent_group(client):

    context = create_authenticated_group_members(client)
    owner = context['owner']
    member = context['member']

    group_id = uuid.uuid4()

    settlement_payload = {
        'payer_id': owner['user']['id'],
        'receiver_id': member['user']['id'],
        'amount': 13,
        'settled_at': datetime.now(timezone.utc).isoformat(),
    }

    response = client.post(f'/groups/{group_id}/settlements', json=settlement_payload, headers=owner['headers'])
    assert response.status_code == 404

def test_payer_equals_receiver(client):

    context = create_authenticated_group_members(client)
    owner = context['owner']
    group_id = context['group']['id']

    settlement_payload = {
        'payer_id': owner['user']['id'],
        'receiver_id': owner['user']['id'],
        'amount': 13,
        'settled_at': datetime.now(timezone.utc).isoformat(),
    }

    response = client.post(f'/groups/{group_id}/settlements', json=settlement_payload, headers=owner['headers'])
    assert response.status_code == 422
    data = response.json()
    assert 'payer_id and receiver_id cannot be the same' in data['detail'][0]['msg']

def test_non_positive_settlement_amount(client):

    context = create_authenticated_group_members(client)
    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    settlement_payload = {
        'payer_id': owner['user']['id'],
        'receiver_id': member['user']['id'],
        'amount': -10,
        'settled_at': datetime.now(timezone.utc).isoformat(),
    }

    response = client.post(f'/groups/{group_id}/settlements', json=settlement_payload, headers=owner['headers'])
    assert response.status_code == 422

    settlement_payload = {
        'payer_id': owner['user']['id'],
        'receiver_id': member['user']['id'],
        'amount': 0,
        'settled_at': datetime.now(timezone.utc).isoformat(),
    }

    response = client.post(f'/groups/{group_id}/settlements', json=settlement_payload, headers=owner['headers'])
    assert response.status_code == 422

def test_payer_with_non_negative_balance_cannot_create_settlement(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense',
        'total_amount': 10,
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

    settlement_payload = {
        'payer_id': owner['user']['id'],
        'receiver_id': member['user']['id'],
        'amount': 5,
        'settled_at': datetime.now(timezone.utc).isoformat()
    }

    response = client.post(f'/groups/{group_id}/settlements', json=settlement_payload, headers=owner['headers'])
    assert response.status_code == 400

def test_receiver_with_non_positive_balance_cannot_create_settlement(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    new_user = create_authenticated_user(
        client,
        email='new_user@example.com',
        username='new_user',
        password='long_password'
    )

    response = client.post(f'/groups/{group_id}/members', json={'user_id':new_user['user']['id']}, headers=owner['headers'])
    assert response.status_code == 200

    expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense',
        'total_amount': 10,
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
        'receiver_id': new_user['user']['id'],
        'amount': 5,
        'settled_at': datetime.now(timezone.utc).isoformat()
    }

    response = client.post(f'/groups/{group_id}/settlements', json=settlement_payload, headers=member['headers'])
    assert response.status_code == 400

def test_settlement_cannot_be_greater_than_balance(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense',
        'total_amount': 10,
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

    settlement_payload = {
        'payer_id': member['user']['id'],
        'receiver_id': owner['user']['id'],
        'amount': 15,
        'settled_at': datetime.now(timezone.utc).isoformat()
    }

    response = client.post(f'/groups/{group_id}/settlements', json=settlement_payload, headers=member['headers'])
    assert response.status_code == 400
    data = response.json()
    assert data['detail'] == 'Settlement amount exceeds the allowed outstanding balance'

def test_valid_settlement_reduce_balance(client):
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
        'amount': 5,
        'settled_at': datetime.now(timezone.utc).isoformat()
    }

    response = client.post(f'/groups/{group_id}/settlements', json=settlement_payload, headers=member['headers'])
    assert response.status_code == 200

    response = client.get(f'/groups/{group_id}/balances', headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    balances = data['balances']
    owner_balance = next(balance for balance in balances if balance['user_id'] == owner['user']['id'])
    assert Decimal(owner_balance['amount']) == Decimal(5)
    member_balance = next(balance for balance in balances if balance['user_id'] == member['user']['id'])
    assert Decimal(member_balance['amount']) == Decimal(-5)

def test_delete_settlement_success(client):
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
        'settled_at': datetime.now(timezone.utc).isoformat()
    }

    response = client.post(f'/groups/{group_id}/settlements', json=settlement_payload, headers=member['headers'])
    assert response.status_code == 200
    data = response.json()
    settlement_id = data['id']

    response = client.delete(f'/settlements/{settlement_id}', headers=member['headers'])
    assert response.status_code == 204
    assert not response.content

def test_delete_settlement_not_found(client):

    context = create_authenticated_group_members(client)
    member = context['member']
    settlement_id = uuid.uuid4()

    response = client.delete(f'/settlements/{settlement_id}', headers=member['headers'])
    assert response.status_code == 404

def test_delete_settlement_not_authorized(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    expense_payload = {
        'payer_id': member['user']['id'],
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
        'payer_id': owner['user']['id'],
        'receiver_id': member['user']['id'],
        'amount': 10,
        'settled_at': datetime.now(timezone.utc).isoformat()
    }

    response = client.post(f'/groups/{group_id}/settlements', json=settlement_payload, headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    settlement_id = data['id']

    response = client.delete(f'/settlements/{settlement_id}', headers=member['headers'])
    assert response.status_code == 403

def test_delete_settlement_removed_from_group_list(client):
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
        'settled_at': datetime.now(timezone.utc).isoformat()
    }

    response = client.post(f'/groups/{group_id}/settlements', json=settlement_payload, headers=member['headers'])
    assert response.status_code == 200
    data = response.json()
    settlement_id = data['id']

    response = client.delete(f'/settlements/{settlement_id}', headers=member['headers'])
    assert response.status_code == 204

    response = client.get(f'/groups/{group_id}/settlements', headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    settlement_ids = {settlement['id'] for settlement in data}
    assert settlement_id not in settlement_ids

def test_delete_settlements_balance_recalculation_after_delete(client):
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
        'settled_at': datetime.now(timezone.utc).isoformat()
    }

    response = client.post(f'/groups/{group_id}/settlements', json=settlement_payload, headers=member['headers'])
    assert response.status_code == 200
    data = response.json()
    settlement_id = data['id']

    response = client.get(f'/groups/{group_id}/balances', headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    balances = data['balances']
    owner_balance = next(balance for balance in balances if balance['user_id'] == owner['user']['id'])
    assert Decimal(owner_balance['amount']) == Decimal('0')
    member_balance = next(balance for balance in balances if balance['user_id'] == member['user']['id'])
    assert Decimal(member_balance['amount']) == Decimal('0')

    response = client.delete(f'/settlements/{settlement_id}', headers=member['headers'])
    assert response.status_code == 204

    response = client.get(f'/groups/{group_id}/balances', headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    balances = data['balances']
    owner_balance = next(balance for balance in balances if balance['user_id'] == owner['user']['id'])
    assert Decimal(owner_balance['amount']) == Decimal('10')
    member_balance = next(balance for balance in balances if balance['user_id'] == member['user']['id'])
    assert Decimal(member_balance['amount']) == Decimal('-10')

def test_delete_settlement_removed_creator_cannot_delete(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']
    user_id = member['user']['id']

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
        'settled_at': datetime.now(timezone.utc).isoformat()
    }

    response = client.post(f'/groups/{group_id}/settlements', json=settlement_payload, headers=member['headers'])
    assert response.status_code == 200
    data = response.json()
    settlement_id = data['id']

    response = client.delete(f'/groups/{group_id}/members/{user_id}', headers=owner['headers'])
    assert response.status_code == 204

    response = client.delete(f'/settlements/{settlement_id}', headers=member['headers'])
    assert response.status_code == 403

def test_patch_settlement_success(client):
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
        'settled_at': datetime.now(timezone.utc).isoformat()
    }

    response = client.post(f'/groups/{group_id}/settlements', json=settlement_payload, headers=member['headers'])
    assert response.status_code == 200
    data = response.json()
    settlement_id = data['id']
    assert Decimal(data['amount']) == Decimal('10')

    response = client.get(f'/groups/{group_id}/balances', headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    balances = data['balances']
    owner_balance = next(balance for balance in balances if balance['user_id'] == owner['user']['id'])
    assert Decimal(owner_balance['amount']) == Decimal(0)
    member_balance = next(balance for balance in balances if balance['user_id'] == member['user']['id'])
    assert Decimal(member_balance['amount']) == Decimal(0)

    updated_settlement_payload = {
        'amount': 5,
        'note': 'note added',
        'settled_at': '2026-06-04T15:30:00+03:00',
    }

    response = client.patch(f'/settlements/{settlement_id}', json=updated_settlement_payload, headers=member['headers'])
    assert response.status_code == 200
    data = response.json()
    assert data['note'] == 'note added'
    assert Decimal(data['amount']) == Decimal(5)
    assert data['settled_at'] == updated_settlement_payload['settled_at']

    response = client.get(f'/groups/{group_id}/balances', headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    balances = data['balances']
    owner_balance = next(balance for balance in balances if balance['user_id'] == owner['user']['id'])
    assert Decimal(owner_balance['amount']) == Decimal(5)
    member_balance = next(balance for balance in balances if balance['user_id'] == member['user']['id'])
    assert Decimal(member_balance['amount']) == Decimal(-5)

def test_patch_settlement_receiver_success(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    new_user = create_authenticated_user(
        client,
        email='new_user@example.com',
        username='new_user',
        password='long_password',
    )

    response = client.post(f'/groups/{group_id}/members', json={'user_id': new_user['user']['id']}, headers=owner['headers'])
    assert response.status_code == 200

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

    expense_payload = {
        'payer_id': new_user['user']['id'],
        'title': 'test_expense',
        'total_amount': 20,
        'split_type': 'equal',
        'expense_date': datetime.now(timezone.utc).isoformat(),
        'participants': [
            {'user_id': new_user['user']['id']},
            {'user_id': member['user']['id']},
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=expense_payload, headers=new_user['headers'])
    assert response.status_code == 200

    settlement_payload = {
        'payer_id': member['user']['id'],
        'receiver_id': owner['user']['id'],
        'amount': 5,
        'settled_at': datetime.now(timezone.utc).isoformat()
    }

    response = client.post(f'/groups/{group_id}/settlements', json=settlement_payload, headers=member['headers'])
    assert response.status_code == 200
    data = response.json()
    settlement_id = data['id']

    updated_settlement_payload = {
        'receiver_id': new_user['user']['id'],
    }

    response = client.patch(f'/settlements/{settlement_id}', json=updated_settlement_payload, headers=member['headers'])
    assert response.status_code == 200
    data = response.json()
    assert data['receiver_id'] == new_user['user']['id']
    assert data['payer_id'] == member['user']['id']
    assert Decimal(data['amount']) == Decimal('5')

    response = client.get(f'/groups/{group_id}/balances', headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    balances = data['balances']
    owner_balance = next(balance for balance in balances if balance['user_id'] == owner['user']['id'])
    assert Decimal(owner_balance['amount']) == Decimal(10)
    member_balance = next(balance for balance in balances if balance['user_id'] == member['user']['id'])
    assert Decimal(member_balance['amount']) == Decimal(-15)
    new_user_balance = next(balance for balance in balances if balance['user_id'] == new_user['user']['id'])
    assert Decimal(new_user_balance['amount']) == Decimal(5)

def test_patch_settlement_not_found(client):
    context = create_authenticated_group_members(client)

    member = context['member']

    settlement_payload = {
        'amount': 20
    }

    new_settlement_id = uuid.uuid4()

    response = client.patch(f'/settlements/{new_settlement_id}', json=settlement_payload, headers=member['headers'])
    assert response.status_code == 404

def test_patch_settlement_non_creator_cannot_update(client):
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
        'settled_at': datetime.now(timezone.utc).isoformat()
    }

    response = client.post(f'/groups/{group_id}/settlements', json=settlement_payload, headers=member['headers'])
    assert response.status_code == 200
    data = response.json()
    settlement_id = data['id']

    updated_settlement_payload = {
        'amount': 5,
        'note': 'note added',
        'settled_at': '2026-06-04T15:30:00+03:00',
    }

    response = client.patch(f'/settlements/{settlement_id}', json=updated_settlement_payload, headers=owner['headers'])
    assert response.status_code == 403

def test_patch_settlement_receiver_not_in_group(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    new_user = create_authenticated_user(
        client,
        email='new_user@example.com',
        username='new_user',
        password='long_password',
    )

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
        'amount': 5,
        'settled_at': datetime.now(timezone.utc).isoformat()
    }

    response = client.post(f'/groups/{group_id}/settlements', json=settlement_payload, headers=member['headers'])
    assert response.status_code == 200
    data = response.json()
    settlement_id = data['id']

    updated_settlement_payload = {
        'receiver_id': new_user['user']['id'],
    }

    response = client.patch(f'/settlements/{settlement_id}', json=updated_settlement_payload, headers=member['headers'])
    assert response.status_code == 400

def test_patch_settlement_receiver_equal_to_payer(client):
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
        'amount': 5,
        'settled_at': datetime.now(timezone.utc).isoformat()
    }

    response = client.post(f'/groups/{group_id}/settlements', json=settlement_payload, headers=member['headers'])
    assert response.status_code == 200
    data = response.json()
    settlement_id = data['id']

    updated_settlement_payload = {
        'receiver_id': member['user']['id'],
    }

    response = client.patch(f'/settlements/{settlement_id}', json=updated_settlement_payload, headers=member['headers'])
    assert response.status_code == 400

def test_patch_settlement_amount_too_large(client):
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
        'settled_at': datetime.now(timezone.utc).isoformat()
    }

    response = client.post(f'/groups/{group_id}/settlements', json=settlement_payload, headers=member['headers'])
    assert response.status_code == 200
    data = response.json()
    settlement_id = data['id']

    updated_settlement_payload = {
        'amount': 15,
        'note': 'note added',
        'settled_at': '2026-06-04T15:30:00+03:00',
    }

    response = client.patch(f'/settlements/{settlement_id}', json=updated_settlement_payload, headers=member['headers'])
    assert response.status_code == 400

def test_list_group_settlements_success(client):
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

    first_settlement_payload = {
        'payer_id': member['user']['id'],
        'receiver_id': owner['user']['id'],
        'amount': 5,
        'note': 'first settlement',
        'settled_at': '2026-06-04T15:30:00+03:00',
    }

    second_settlement_payload = {
        'payer_id': member['user']['id'],
        'receiver_id': owner['user']['id'],
        'amount': 15,
        'note': 'second settlement',
        'settled_at': '2026-06-08T15:30:00+03:00',
    }

    response = client.post(f'/groups/{group_id}/settlements', json=first_settlement_payload, headers=member['headers'])
    assert response.status_code == 200
    data = response.json()
    first_settlement_id = data['id']
    response = client.post(f'/groups/{group_id}/settlements', json=second_settlement_payload, headers=member['headers'])
    assert response.status_code == 200
    data = response.json()
    second_settlement_id = data['id']

    response = client.get(f'/groups/{group_id}/settlements', headers=member['headers'])
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    settlement_ids = [settlement['id'] for settlement in data]
    assert [second_settlement_id, first_settlement_id] == settlement_ids
    assert 'id' in data[0]
    assert 'created_by' in data[0]
    assert 'group_id' in data[0]
    assert 'payer_id' in data[0]
    assert 'receiver_id' in data[0]
    assert 'amount' in data[0]
    assert 'note' in data[0]
    assert 'settled_at' in data[0]
    assert 'created_at' in data[0]

def test_list_group_settlements_forbidden_for_non_member(client):
    context = create_authenticated_group_members(client)
    group_id = context['group']['id']

    new_user = create_authenticated_user(
        client,
        email='new_user@example.com',
        username='new_user',
        password='long_password',
    )

    response = client.get(f'/groups/{group_id}/settlements', headers=new_user['headers'])
    assert response.status_code == 403

def test_list_group_settlements_forbidden_for_removed_member(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']
    member_id = member['user']['id']

    response = client.delete(f'/groups/{group_id}/members/{member_id}', headers=owner['headers'])
    assert response.status_code == 204

    response = client.get(f'/groups/{group_id}/settlements', headers=member['headers'])
    assert response.status_code == 403

def test_list_group_settlements_filter_by_payer(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    new_user = create_authenticated_user(
        client,
        email='new_user@example.com',
        username='new_user',
        password='long_password',
    )

    response = client.post(f'/groups/{group_id}/members', json={'user_id': new_user['user']['id']}, headers=owner['headers'])
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
            {'user_id': new_user['user']['id']},
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=expense_payload, headers=owner['headers'])
    assert response.status_code == 200

    member_settlement_payload = {
        'payer_id': member['user']['id'],
        'receiver_id': owner['user']['id'],
        'amount': 5,
        'note': 'first settlement',
        'settled_at': datetime.now(timezone.utc).isoformat(),
    }

    new_user_settlement_payload = {
        'payer_id': new_user['user']['id'],
        'receiver_id': owner['user']['id'],
        'amount': 15,
        'note': 'second settlement',
        'settled_at': datetime.now(timezone.utc).isoformat(),
    }

    response = client.post(f'/groups/{group_id}/settlements', json=member_settlement_payload, headers=member['headers'])
    assert response.status_code == 200
    data = response.json()
    member_settlement_id = data['id']

    response = client.post(f'/groups/{group_id}/settlements', json=new_user_settlement_payload, headers=new_user['headers'])
    assert response.status_code == 200

    params = {'payer_id': member['user']['id']}

    response = client.get(f"/groups/{group_id}/settlements", params=params, headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]['id'] == member_settlement_id
    assert all(settlement['payer_id'] == member['user']['id'] for settlement in data)

def test_list_group_settlements_filter_by_receiver(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    new_user = create_authenticated_user(
        client,
        email='new_user@example.com',
        username='new_user',
        password='long_password',
    )


    response = client.post(f'/groups/{group_id}/members', json={'user_id': new_user['user']['id']}, headers=owner['headers'])
    assert response.status_code == 200

    owner_expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'owner_paid_expense',
        'total_amount': 100,
        'split_type': 'exact',
        'expense_date': datetime.now(timezone.utc).isoformat(),
        'participants': [
            {'user_id': owner['user']['id'], 'amount': 10},
            {'user_id': member['user']['id'], 'amount': 90},
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=owner_expense_payload, headers=owner['headers'])
    assert response.status_code == 200

    new_user_expense_payload = {
        'payer_id': new_user['user']['id'],
        'title': 'new_user_paid_expense',
        'total_amount': 100,
        'split_type': 'exact',
        'expense_date': datetime.now(timezone.utc).isoformat(),
        'participants': [
            {'user_id': new_user['user']['id'], 'amount': 10},
            {'user_id': member['user']['id'], 'amount': 90},
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=new_user_expense_payload, headers=new_user['headers'])
    assert response.status_code == 200

    first_settlement_payload = {
        'payer_id': member['user']['id'],
        'receiver_id': owner['user']['id'],
        'amount': 5,
        'note': 'first settlement',
        'settled_at': datetime.now(timezone.utc).isoformat(),
    }

    second_settlement_payload = {
        'payer_id': member['user']['id'],
        'receiver_id': new_user['user']['id'],
        'amount': 15,
        'note': 'second settlement',
        'settled_at': datetime.now(timezone.utc).isoformat(),
    }

    response = client.post(f'/groups/{group_id}/settlements', json=first_settlement_payload, headers=member['headers'])
    assert response.status_code == 200
    data = response.json()
    first_settlement_id = data['id']

    response = client.post(f'/groups/{group_id}/settlements', json=second_settlement_payload, headers=member['headers'])
    assert response.status_code == 200

    params = {'receiver_id': owner['user']['id']}

    response = client.get(f"/groups/{group_id}/settlements", params=params, headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]['id'] == first_settlement_id
    assert all(settlement['receiver_id'] == owner['user']['id'] for settlement in data)

def test_list_group_settlements_filter_by_receiver_and_payer(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    new_user = create_authenticated_user(
        client,
        email='new_user@example.com',
        username='new_user',
        password='long_password',
    )

    response = client.post(f'/groups/{group_id}/members', json={'user_id': new_user['user']['id']}, headers=owner['headers'])
    assert response.status_code == 200

    other_user = create_authenticated_user(
        client,
        email='other_user@example.com',
        username='other_user',
        password='long_password',
    )

    response = client.post(f'/groups/{group_id}/members', json={'user_id': other_user['user']['id']}, headers=owner['headers'])
    assert response.status_code == 200

    owner_expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'owner_paid_expense',
        'total_amount': 110,
        'split_type': 'exact',
        'expense_date': datetime.now(timezone.utc).isoformat(),
        'participants': [
            {'user_id': owner['user']['id'], 'amount': 10},
            {'user_id': member['user']['id'], 'amount': 50},
            {'user_id': other_user['user']['id'], 'amount': 50},
        ],
    }

    response = client.post(f'/groups/{group_id}/expenses', json=owner_expense_payload, headers=owner['headers'])
    assert response.status_code == 200

    new_user_expense_payload = {
        'payer_id': new_user['user']['id'],
        'title': 'new_user_paid_expense',
        'total_amount': 110,
        'split_type': 'exact',
        'expense_date': datetime.now(timezone.utc).isoformat(),
        'participants': [
            {'user_id': new_user['user']['id'], 'amount': 10},
            {'user_id': member['user']['id'], 'amount': 50},
            {'user_id': other_user['user']['id'], 'amount': 50},
        ],
    }

    response = client.post(f'/groups/{group_id}/expenses', json=new_user_expense_payload, headers=new_user['headers'])
    assert response.status_code == 200

    first_settlement_payload = {
        'payer_id': member['user']['id'],
        'receiver_id': owner['user']['id'],
        'amount': 5,
        'note': 'matches both filters',
        'settled_at': datetime.now(timezone.utc).isoformat(),
    }

    second_settlement_payload = {
        'payer_id': member['user']['id'],
        'receiver_id': new_user['user']['id'],
        'amount': 15,
        'note': 'matches payer only',
        'settled_at': datetime.now(timezone.utc).isoformat(),
    }

    third_settlement_payload = {
        'payer_id': other_user['user']['id'],
        'receiver_id': owner['user']['id'],
        'amount': 5,
        'note': 'matches receiver only',
        'settled_at': datetime.now(timezone.utc).isoformat(),
    }

    response = client.post(f'/groups/{group_id}/settlements', json=first_settlement_payload, headers=member['headers'])
    assert response.status_code == 200
    data = response.json()
    matching_settlement_id = data['id']

    response = client.post(f'/groups/{group_id}/settlements', json=second_settlement_payload, headers=member['headers'])
    assert response.status_code == 200

    response = client.post(f'/groups/{group_id}/settlements', json=third_settlement_payload, headers=other_user['headers'])
    assert response.status_code == 200

    params = {
        'payer_id': member['user']['id'],
        'receiver_id': owner['user']['id']}

    response = client.get(f'/groups/{group_id}/settlements', params=params, headers=owner['headers'])

    assert response.status_code == 200
    data = response.json()

    assert len(data) == 1
    assert data[0]['id'] == matching_settlement_id
    assert data[0]['payer_id'] == member['user']['id']
    assert data[0]['receiver_id'] == owner['user']['id']

    assert all(
        settlement['payer_id'] == member['user']['id']
        and settlement['receiver_id'] == owner['user']['id']
        for settlement in data
    )

def test_list_group_settlements_pagination(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'new expense',
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

    first_settlement_payload = {
        'payer_id': member['user']['id'],
        'receiver_id': owner['user']['id'],
        'amount': 5,
        'note': 'first settlement',
        'settled_at': '2026-06-04T15:30:00+03:00',
    }

    response = client.post(f'/groups/{group_id}/settlements', json=first_settlement_payload, headers=member['headers'])
    assert response.status_code == 200

    second_settlement_payload = {
        'payer_id': member['user']['id'],
        'receiver_id': owner['user']['id'],
        'amount': 5,
        'note': 'first settlement',
        'settled_at': '2026-06-06T15:30:00+03:00',
    }

    response = client.post(f'/groups/{group_id}/settlements', json=second_settlement_payload, headers=member['headers'])
    assert response.status_code == 200
    data = response.json()
    second_settlement_id = data['id']

    third_settlement_payload = {
        'payer_id': member['user']['id'],
        'receiver_id': owner['user']['id'],
        'amount': 5,
        'note': 'first settlement',
        'settled_at': '2026-06-08T15:30:00+03:00',
    }

    response = client.post(f'/groups/{group_id}/settlements', json=third_settlement_payload, headers=member['headers'])
    assert response.status_code == 200
    data = response.json()
    third_settlement_id = data['id']

    params = {
        'payer_id': member['user']['id'],
        'receiver_id': owner['user']['id'],
        'limit': 2,
        'offset': 0
    }

    response = client.get(f'/groups/{group_id}/settlements', params=params, headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    settlement_ids = [settlement['id'] for settlement in data]
    assert [third_settlement_id, second_settlement_id] == settlement_ids

def test_list_group_settlements_pagination_second_newest_result(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'new expense',
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

    first_settlement_payload = {
        'payer_id': member['user']['id'],
        'receiver_id': owner['user']['id'],
        'amount': 5,
        'note': 'first settlement',
        'settled_at': '2026-06-04T15:30:00+03:00',
    }

    response = client.post(f'/groups/{group_id}/settlements', json=first_settlement_payload, headers=member['headers'])
    assert response.status_code == 200

    second_settlement_payload = {
        'payer_id': member['user']['id'],
        'receiver_id': owner['user']['id'],
        'amount': 5,
        'note': 'first settlement',
        'settled_at': '2026-06-06T15:30:00+03:00',
    }

    response = client.post(f'/groups/{group_id}/settlements', json=second_settlement_payload, headers=member['headers'])
    assert response.status_code == 200
    data = response.json()
    second_settlement_id = data['id']

    third_settlement_payload = {
        'payer_id': member['user']['id'],
        'receiver_id': owner['user']['id'],
        'amount': 5,
        'note': 'first settlement',
        'settled_at': '2026-06-08T15:30:00+03:00',
    }

    response = client.post(f'/groups/{group_id}/settlements', json=third_settlement_payload, headers=member['headers'])
    assert response.status_code == 200

    params = {
        'payer_id': member['user']['id'],
        'receiver_id': owner['user']['id'],
        'limit': 1,
        'offset': 1
    }

    response = client.get(f'/groups/{group_id}/settlements', params=params, headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    settlement_ids = [settlement['id'] for settlement in data]
    assert [second_settlement_id] == settlement_ids

def test_list_group_settlements_rejects_zero_limit(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    group_id = context['group']['id']

    params = {
        'limit': 0,
    }

    response = client.get(f'/groups/{group_id}/settlements', params=params, headers=owner['headers'])
    assert response.status_code == 422

def test_list_group_settlements_rejects_negative_offset(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    group_id = context['group']['id']

    params = {
        'offset': -1
    }

    response = client.get(f'/groups/{group_id}/settlements', params=params, headers=owner['headers'])
    assert response.status_code == 422


