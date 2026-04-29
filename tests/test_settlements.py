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

    response = client.post(f'/groups/{group_id}/settlements', json=settlement_payload, headers=owner['headers'])
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

def test_payer_not_group_member(client):
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
        'payer_id': new_user['user']['id'],
        'receiver_id': owner['user']['id'],
        'amount': 13,
        'settled_at': datetime.now(timezone.utc).isoformat(),
    }

    response = client.post(f'/groups/{group_id}/settlements', json=settlement_payload, headers=owner['headers'])
    assert response.status_code == 400

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






