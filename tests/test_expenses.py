import uuid
from datetime import timezone, datetime
from decimal import Decimal
from tests.helpers import create_authenticated_group_members, create_authenticated_user


def test_create_equal_split_expenses_success(client):
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
            {
                'user_id': member['user']['id'],
            },
            {
                'user_id': owner['user']['id'],
            }
        ]}

    response = client.post(f'/groups/{group_id}/expenses', json=expense_payload, headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    assert data['payer_id'] == owner['user']['id']
    assert Decimal(data['total_amount']) == Decimal('100')
    assert data['split_type'] == 'equal'
    assert data['description'] is None
    assert data['group_id'] == group_id
    assert data['title'] == 'test_expense'

def test_payer_not_group_member(client):
    context = create_authenticated_group_members(client)

    new_member_id = uuid.uuid4()

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    expense_payload = {
        'payer_id': str(new_member_id),
        'title': 'test_expense',
        'total_amount': 100,
        'split_type': 'equal',
        'expense_date': datetime.now(timezone.utc).isoformat(),
        'participants': [
            {'user_id': owner['user']['id']},
            {'user_id': member['user']['id']}
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=expense_payload, headers=owner['headers'] )
    assert response.status_code == 400

def test_participant_not_group_member(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    new_member_id = uuid.uuid4()

    expense_payload = {
        'payer_id': member['user']['id'],
        'title': 'test_expense',
        'total_amount': 100,
        'split_type': 'equal',
        'expense_date': datetime.now(timezone.utc).isoformat(),
        'participants': [
            {'user_id': owner['user']['id']},
            {'user_id': str(new_member_id)}
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=expense_payload, headers=owner['headers'])
    assert response.status_code == 400

def test_current_user_not_in_the_group(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    outsider = create_authenticated_user(
        client,
        email='outsider@example.com',
        username='outsider',
        password='long_password',
    )

    expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense',
        'total_amount': 100,
        'split_type': 'equal',
        'expense_date': datetime.now(timezone.utc).isoformat(),
        'participants': [
            {'user_id': owner['user']['id']},
            {'user_id': member['user']['id']}
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=expense_payload, headers=outsider['headers'])
    assert response.status_code == 403

def test_non_existent_group_expense(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = uuid.uuid4()

    expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense',
        'total_amount': 100,
        'split_type': 'equal',
        'expense_date': datetime.now(timezone.utc).isoformat(),
        'participants': [
            {'user_id': owner['user']['id']},
            {'user_id': member['user']['id']}
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=expense_payload, headers=owner['headers'])
    assert response.status_code == 404

def test_expense_splits(client):
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
            {'user_id': member['user']['id']}
        ]}

    response = client.post(f'/groups/{group_id}/expenses', json=expense_payload, headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    assert data['split_type'] == 'equal'
    assert 'splits' in data
    assert len(data['splits']) == 2

    split_user_ids = {split['user_id'] for split in data['splits']}
    assert split_user_ids == {
        owner['user']['id'],
        member['user']['id']
    }
    split_amount = [Decimal(split['amount_owed']) for split in data['splits']]
    assert sum(split_amount) == Decimal('100')
    assert all(amount == Decimal('50') for amount in split_amount)

def test_no_participants_in_expense(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    group_id = context['group']['id']

    expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense',
        'total_amount': 100,
        'split_type': 'equal',
        'expense_date': datetime.now(timezone.utc).isoformat(),
        'participants': []
    }

    response = client.post(f'/groups/{group_id}/expenses', json=expense_payload, headers=owner['headers'])
    assert response.status_code == 422

def test_unsupported_split_type(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense',
        'total_amount': 100,
        'split_type': 'exact',
        'expense_date': datetime.now(timezone.utc).isoformat(),
        'participants': [
            {'user_id': owner['user']['id']},
            {'user_id': member['user']['id']}
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=expense_payload, headers=owner['headers'])
    assert response.status_code == 422

def test_negative__amount_in_expense(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense',
        'total_amount': -100,
        'split_type': 'equal',
        'expense_date': datetime.now(timezone.utc).isoformat(),
        'participants': [
            {'user_id': owner['user']['id']},
            {'user_id': member['user']['id']}
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=expense_payload, headers=owner['headers'])
    assert response.status_code == 422

def test_zero_amount_in_expense(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense',
        'total_amount': 0,
        'split_type': 'equal',
        'expense_date': datetime.now(timezone.utc).isoformat(),
        'participants': [
            {'user_id': owner['user']['id']},
            {'user_id': member['user']['id']}
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=expense_payload, headers=owner['headers'])
    assert response.status_code == 422

def test_list_expenses_success(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    expense_payload_a = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense_a',
        'total_amount': 100,
        'split_type': 'equal',
        'expense_date': datetime.now(timezone.utc).isoformat(),
        'participants': [
            {'user_id': owner['user']['id']},
            {'user_id': member['user']['id']}
        ]}

    response = client.post(f'/groups/{group_id}/expenses', json=expense_payload_a, headers=owner['headers'])
    assert response.status_code == 200

    expense_payload_b = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense_b',
        'total_amount': 50,
        'split_type': 'equal',
        'expense_date': datetime.now(timezone.utc).isoformat(),
        'participants': [
            {'user_id': owner['user']['id']},
            {'user_id': member['user']['id']}
        ]}

    response = client.post(f'/groups/{group_id}/expenses', json=expense_payload_b, headers=owner['headers'])
    assert response.status_code == 200

    response = client.get(f'/groups/{group_id}/expenses', headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()

    assert len(data) == 2

    returned_ids = {expense['title'] for expense in data}

    assert returned_ids == {
        'test_expense_a',
        'test_expense_b'
    }

def test_list_returns_only_that_groups_expenses(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member_a = context['member']
    group_a_id = context['group']['id']

    member_b = create_authenticated_user(
        client,
        email='member_b@example.com',
        username='member_b',
        password='long_password'
    )

    response = client.post('/groups', json={'name': 'group_b'}, headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    group_b_id = data['id']

    response = client.post(f'/groups/{group_b_id}/members', json={'user_id': member_b['user']['id']}, headers=owner['headers'])
    assert response.status_code == 200

    expense_payload_a = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense_a',
        'total_amount': 100,
        'split_type': 'equal',
        'expense_date': datetime.now(timezone.utc).isoformat(),
        'participants': [
            {'user_id': member_a['user']['id']},
            {'user_id': owner['user']['id']}
        ]
    }
    response = client.post(f'/groups/{group_a_id}/expenses', json=expense_payload_a, headers=owner['headers'])
    assert response.status_code == 200

    expense_payload_b = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense_b',
        'total_amount': 50,
        'split_type': 'equal',
        'expense_date': datetime.now(timezone.utc).isoformat(),
        'participants': [
            {'user_id': member_b['user']['id']},
            {'user_id': owner['user']['id']}
        ]
    }

    response = client.post(f'/groups/{group_b_id}/expenses', json=expense_payload_b, headers=owner['headers'])
    assert response.status_code == 200

    response = client.get(f'/groups/{group_a_id}/expenses', headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]['title'] == 'test_expense_a'

def test_list_non_member_failure(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    user = create_authenticated_user(
        client,
        email='user@example.com',
        username='user',
        password='long_password'
    )

    expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense',
        'total_amount': 100,
        'split_type': 'equal',
        'expense_date': datetime.now(timezone.utc).isoformat(),
        'participants': [
            {'user_id': owner['user']['id']},
            {'user_id': member['user']['id']}
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=expense_payload, headers=owner['headers'])
    assert response.status_code == 200

    response = client.get(f'/groups/{group_id}/expenses', headers=user['headers'])
    assert response.status_code == 403

def test_list_expenses_nonexistent_group(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    new_group_id = uuid.uuid4()

    expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense',
        'total_amount': 100,
        'split_type': 'equal',
        'expense_date': datetime.now(timezone.utc).isoformat(),
        'participants': [
            {'user_id': owner['user']['id']},
            {'user_id': member['user']['id']}
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=expense_payload, headers=owner['headers'])
    assert response.status_code == 200

    response = client.get(f'/groups/{new_group_id}/expenses', headers=owner['headers'])
    assert response.status_code == 404