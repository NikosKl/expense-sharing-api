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
        'split_type': 'custom',
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

def test_list_expenses_response_includes_nested_splits(client):
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
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=expense_payload, headers=owner['headers'])
    assert response.status_code == 200

    response = client.get(f'/groups/{group_id}/expenses', headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    returned_id = [splits['user_id'] for splits in data[0]['splits']]
    assert member['user']['id'] in returned_id
    assert owner['user']['id'] in returned_id

def test_get__expense_by_id_success(client):
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
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=expense_payload, headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    expense_id = data['id']

    response = client.get(f'/expenses/{expense_id}', headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    assert data['id'] == expense_id
    assert data['title'] == expense_payload['title']
    assert Decimal(data['total_amount']) == Decimal(expense_payload['total_amount'])
    assert data['split_type'] == expense_payload['split_type']
    assert 'splits' in data
    assert len(data['splits']) == 2
    split_user_ids = {split['user_id'] for split in data['splits']}
    assert split_user_ids == {
        owner['user']['id'],
        member['user']['id']
    }


def test_get_expense_by_id_not_found(client):
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
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=expense_payload, headers=owner['headers'])
    assert response.status_code == 200

    new_expense_id = uuid.uuid4()

    response = client.get(f'/expenses/{new_expense_id}', headers=owner['headers'])
    assert response.status_code == 404

def test_non_group_member_cannot_get_expense_by_id(client):
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
    data = response.json()
    expense_id = data['id']

    response = client.get(f'/expenses/{expense_id}', headers=new_user['headers'])
    assert response.status_code == 403

def test_exact_split_expense_success(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense',
        'total_amount': 50,
        'split_type': 'exact',
        'expense_date': datetime.now(timezone.utc).isoformat(),
        'participants': [
            {'user_id': owner['user']['id'], 'amount': 30},
            {'user_id': member['user']['id'], 'amount': 20}
        ]}

    response = client.post(f'/groups/{group_id}/expenses', json=expense_payload, headers=owner['headers'])
    assert response.status_code == 200

    data = response.json()
    assert data['split_type'] == 'exact'
    assert Decimal(data['total_amount']) == Decimal('50')

    splits = {split['user_id']: split['amount_owed'] for split in data['splits']}

    assert Decimal(splits[owner['user']['id']]) == Decimal('30')
    assert Decimal(splits[member['user']['id']]) == Decimal('20')

def test_exact_split_sum_mismatch(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense',
        'total_amount': 50,
        'split_type': 'exact',
        'expense_date': datetime.now(timezone.utc).isoformat(),
        'participants': [
            {'user_id': owner['user']['id'], 'amount': 30},
            {'user_id': member['user']['id'], 'amount': 30}
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=expense_payload, headers=owner['headers'])
    assert response.status_code == 422

def test_exact_split_without_participants(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    group_id = context['group']['id']

    expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense',
        'total_amount': 50,
        'split_type': 'exact',
        'expense_date': datetime.now(timezone.utc).isoformat(),
        'participants': []
    }

    response = client.post(f'/groups/{group_id}/expenses', json=expense_payload, headers=owner['headers'])
    assert response.status_code == 422

def test_exact_split_with_non_positive_amount(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense',
        'total_amount': 50,
        'split_type': 'exact',
        'expense_date': datetime.now(timezone.utc).isoformat(),
        'participants': [
            {'user_id': owner['user']['id'], 'amount': 30},
            {'user_id': member['user']['id'], 'amount': -20}
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=expense_payload, headers=owner['headers'])
    assert response.status_code == 422

def test_percentage_split_expense_success(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense',
        'total_amount': 50,
        'split_type': 'percentage',
        'expense_date': datetime.now(timezone.utc).isoformat(),
        'participants': [
            {'user_id': owner['user']['id'], 'percentage': 70},
            {'user_id': member['user']['id'], 'percentage': 30}
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=expense_payload, headers=owner['headers'])
    assert response.status_code == 200

    data = response.json()
    assert data['split_type'] == 'percentage'
    assert Decimal(data['total_amount']) == Decimal('50')

    splits = {split['user_id']: split['amount_owed'] for split in data['splits']}
    assert Decimal(splits[owner['user']['id']]) == Decimal('35')
    assert Decimal(splits[member['user']['id']]) == Decimal('15')

def test_percentage_total_not_correct(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense',
        'total_amount': 100,
        'split_type': 'percentage',
        'expense_date': datetime.now(timezone.utc).isoformat(),
        'participants': [
            {'user_id': owner['user']['id'], 'percentage': 50},
            {'user_id': member['user']['id'], 'percentage': 40}
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=expense_payload, headers=owner['headers'])
    assert response.status_code == 422

def test_percentage_split_without_participants(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    group_id = context['group']['id']

    expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense',
        'total_amount': 50,
        'split_type': 'percentage',
        'expense_date': datetime.now(timezone.utc).isoformat(),
        'participants': []
    }

    response = client.post(f'/groups/{group_id}/expenses', json=expense_payload, headers=owner['headers'])
    assert response.status_code == 422

def test_percentage_split_with_non_positive_amount(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense',
        'total_amount': 50,
        'split_type': 'percentage',
        'expense_date': datetime.now(timezone.utc).isoformat(),
        'participants': [
            {'user_id': owner['user']['id'], 'percentage': 70},
            {'user_id': member['user']['id'], 'percentage': -40}
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=expense_payload, headers=owner['headers'])
    assert response.status_code == 422

def test_percentage_split_sum_expense(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense',
        'total_amount': 50.24,
        'split_type': 'percentage',
        'expense_date': datetime.now(timezone.utc).isoformat(),
        'participants': [
            {'user_id': owner['user']['id'], 'percentage': 70},
            {'user_id': member['user']['id'], 'percentage': 30}
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=expense_payload, headers=owner['headers'])
    assert response.status_code == 200

    data = response.json()

    splits = {split['user_id']: Decimal(split['amount_owed']) for split in data['splits']}
    assert Decimal(splits[owner['user']['id']]) == Decimal('35.17')
    assert Decimal(splits[member['user']['id']]) == Decimal('15.07')
    assert sum(splits.values()) == Decimal('50.24')

def test_patch_metadata_only_success(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense',
        'total_amount': 50,
        'split_type': 'equal',
        'expense_date': datetime.now(timezone.utc).isoformat(),
        'participants': [
            {'user_id': owner['user']['id']},
            {'user_id': member['user']['id']}
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=expense_payload, headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    expense_id = data['id']
    split_ids = {split['id'] for split in data['splits']}

    update_payload = {
        'title': 'updated test expense',
        'description': 'updated description',
        'expense_date': '2026-05-21T15:30:00+03:00'
    }

    response = client.patch(f'/expenses/{expense_id}', json=update_payload, headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    updated_split_ids = {split['id'] for split in data['splits']}

    assert data['title'] == 'updated test expense'
    assert data['description'] == 'updated description'
    assert data['expense_date'] == update_payload['expense_date']
    assert Decimal(data['total_amount']) == Decimal('50')
    assert data['split_type'] == 'equal'
    assert data['payer_id'] == owner['user']['id']
    assert split_ids == updated_split_ids

    split_user_ids = {split['user_id'] for split in data['splits']}
    assert split_user_ids == {
        owner['user']['id'],
        member['user']['id']
    }
    split_amount = [Decimal(split['amount_owed']) for split in data['splits']]
    assert sum(split_amount) == Decimal('50')
    assert all(amount == Decimal('25') for amount in split_amount)

def test_patch_payer_only_success(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense',
        'total_amount': 50,
        'split_type': 'exact',
        'expense_date': datetime.now(timezone.utc).isoformat(),
        'participants': [
            {'user_id': owner['user']['id'], 'amount': 40},
            {'user_id': member['user']['id'], 'amount': 10}
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=expense_payload, headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    expense_id = data['id']
    split_ids = {split['id'] for split in data['splits']}

    update_payload = {
        'payer_id': member['user']['id'],
    }

    response = client.patch(f'/expenses/{expense_id}', json=update_payload, headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    updated_splits = {split['id'] for split in data['splits']}

    assert data['payer_id'] == member['user']['id']
    assert split_ids == updated_splits

    splits = {split['user_id']: split['amount_owed'] for split in data['splits']}

    assert Decimal(splits[owner['user']['id']]) == Decimal('40')
    assert Decimal(splits[member['user']['id']]) == Decimal('10')

def test_patch_invalid_payer(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    new_user = create_authenticated_user(
        client,
        email='new_user@example.com',
        username='new user',
        password='long_password',
    )

    expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense',
        'total_amount': 50,
        'split_type': 'equal',
        'expense_date': datetime.now(timezone.utc).isoformat(),
        'participants': [
            {'user_id': owner['user']['id'],},
            {'user_id': member['user']['id']}
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=expense_payload, headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    expense_id = data['id']

    update_payload = {
        'payer_id': new_user['user']['id'],
    }

    response = client.patch(f'/expenses/{expense_id}', json=update_payload, headers=owner['headers'])
    assert response.status_code == 400

def test_patch_split_equal_success(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense',
        'total_amount': 50,
        'split_type': 'equal',
        'expense_date': datetime.now(timezone.utc).isoformat(),
        'participants': [
            {'user_id': owner['user']['id']},
            {'user_id': member['user']['id']}
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=expense_payload, headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    expense_id = data['id']

    update_payload = {
        'total_amount': 100,
        'split_type': 'equal',
        'participants': [
            {'user_id': owner['user']['id']},
            {'user_id': member['user']['id']}
        ]
    }

    response = client.patch(f'/expenses/{expense_id}', json=update_payload, headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()

    assert Decimal(data['total_amount']) == Decimal('100')

    split_user_ids = {split['user_id'] for split in data['splits']}
    assert split_user_ids == {
        owner['user']['id'],
        member['user']['id']
    }
    split_amount = [Decimal(split['amount_owed']) for split in data['splits']]
    assert sum(split_amount) == Decimal('100')
    assert all(amount == Decimal('50') for amount in split_amount)

def test_patch_equal_to_exact_success(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense',
        'total_amount': 50,
        'split_type': 'equal',
        'expense_date': datetime.now(timezone.utc).isoformat(),
        'participants': [
            {'user_id': owner['user']['id']},
            {'user_id': member['user']['id']}
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=expense_payload, headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    expense_id = data['id']

    update_payload = {
        'total_amount': 50,
        'split_type': 'exact',
        'participants': [
            {'user_id': owner['user']['id'], 'amount': 40},
            {'user_id': member['user']['id'], 'amount': 10},
        ]
    }

    response = client.patch(f'/expenses/{expense_id}', json=update_payload, headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()

    assert Decimal(data['total_amount']) == Decimal('50')
    assert data['split_type'] == 'exact'

    splits = {split['user_id']: split['amount_owed'] for split in data['splits']}

    assert Decimal(splits[owner['user']['id']]) == Decimal('40')
    assert Decimal(splits[member['user']['id']]) == Decimal('10')

def test_patch_exact_to_percentage_success(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense',
        'total_amount': 50,
        'split_type': 'exact',
        'expense_date': datetime.now(timezone.utc).isoformat(),
        'participants': [
            {'user_id': owner['user']['id'], 'amount': 40},
            {'user_id': member['user']['id'], 'amount': 10}
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=expense_payload, headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    expense_id = data['id']

    update_payload = {
        'total_amount': 50,
        'split_type': 'percentage',
        'participants': [
            {'user_id': owner['user']['id'], 'percentage': 90},
            {'user_id': member['user']['id'], 'percentage': 10},
        ]
    }

    response = client.patch(f'/expenses/{expense_id}', json=update_payload, headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()

    assert Decimal(data['total_amount']) == Decimal('50')
    assert data['split_type'] == 'percentage'

    splits = {split['user_id']: split['amount_owed'] for split in data['splits']}

    assert Decimal(splits[owner['user']['id']]) == Decimal('45')
    assert Decimal(splits[member['user']['id']]) == Decimal('5')

def test_patch_missing_split_fields(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense',
        'total_amount': 50,
        'split_type': 'exact',
        'expense_date': datetime.now(timezone.utc).isoformat(),
        'participants': [
            {'user_id': owner['user']['id'], 'amount': 40},
            {'user_id': member['user']['id'], 'amount': 10}
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=expense_payload, headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    expense_id = data['id']

    update_payload = {
        'total_amount': 100,
    }

    response = client.patch(f'/expenses/{expense_id}', json=update_payload, headers=owner['headers'])
    assert response.status_code == 422

def test_patch_non_creator_failure(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense',
        'total_amount': 50,
        'split_type': 'exact',
        'expense_date': datetime.now(timezone.utc).isoformat(),
        'participants': [
            {'user_id': owner['user']['id'], 'amount': 40},
            {'user_id': member['user']['id'], 'amount': 10}
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=expense_payload, headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    expense_id = data['id']

    update_payload = {
        'total_amount': 50,
        'split_type': 'percentage',
        'participants': [
            {'user_id': owner['user']['id'], 'percentage': 90},
            {'user_id': member['user']['id'], 'percentage': 10},
        ]
    }

    response = client.patch(f'/expenses/{expense_id}', json=update_payload, headers=member['headers'])
    assert response.status_code == 403

def test_patch_expense_not_found(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense',
        'total_amount': 50,
        'split_type': 'exact',
        'expense_date': datetime.now(timezone.utc).isoformat(),
        'participants': [
            {'user_id': owner['user']['id'], 'amount': 40},
            {'user_id': member['user']['id'], 'amount': 10}
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=expense_payload, headers=owner['headers'])
    assert response.status_code == 200

    expense_id = uuid.uuid4()

    update_payload = {
        'total_amount': 50,
        'split_type': 'percentage',
        'participants': [
            {'user_id': owner['user']['id'], 'percentage': 90},
            {'user_id': member['user']['id'], 'percentage': 10},
        ]
    }

    response = client.patch(f'/expenses/{expense_id}', json=update_payload, headers=owner['headers'])
    assert response.status_code == 404

def test_patch_equal_split_cannot_have_participant_amounts(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense',
        'total_amount': 50,
        'split_type': 'exact',
        'expense_date': datetime.now(timezone.utc).isoformat(),
        'participants': [
            {'user_id': owner['user']['id'], 'amount': 40},
            {'user_id': member['user']['id'], 'amount': 10}
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=expense_payload, headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    expense_id = data['id']

    update_payload = {
        'total_amount': 50,
        'split_type': 'equal',
        'participants': [
            {'user_id': owner['user']['id'], 'amount': 25},
            {'user_id': member['user']['id'], 'amount': 25},
        ]
    }

    response = client.patch(f'/expenses/{expense_id}', json=update_payload, headers=owner['headers'])
    assert response.status_code == 422

def test_patch_exact_update_missing_amount(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense',
        'total_amount': 50,
        'split_type': 'equal',
        'expense_date': datetime.now(timezone.utc).isoformat(),
        'participants': [
            {'user_id': owner['user']['id']},
            {'user_id': member['user']['id']}
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=expense_payload, headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    expense_id = data['id']

    update_payload = {
        'total_amount': 50,
        'split_type': 'exact',
        'participants': [
            {'user_id': owner['user']['id']},
            {'user_id': member['user']['id']},
        ]
    }

    response = client.patch(f'/expenses/{expense_id}', json=update_payload, headers=owner['headers'])
    assert response.status_code == 422

def test_patch_percentage_update_missing_percentage(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense',
        'total_amount': 50,
        'split_type': 'equal',
        'expense_date': datetime.now(timezone.utc).isoformat(),
        'participants': [
            {'user_id': owner['user']['id']},
            {'user_id': member['user']['id']}
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=expense_payload, headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    expense_id = data['id']

    update_payload = {
        'total_amount': 50,
        'split_type': 'percentage',
        'participants': [
            {'user_id': owner['user']['id'], 'amount': 25},
            {'user_id': member['user']['id'], 'amount': 25},
        ]
    }

    response = client.patch(f'/expenses/{expense_id}', json=update_payload, headers=owner['headers'])
    assert response.status_code == 422

def test_delete_expense_success(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense',
        'total_amount': 50,
        'split_type': 'equal',
        'expense_date': datetime.now(timezone.utc).isoformat(),
        'participants': [
            {'user_id': owner['user']['id']},
            {'user_id': member['user']['id']},
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=expense_payload, headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    expense_id = data['id']

    response = client.delete(f'/expenses/{expense_id}', headers=owner['headers'])
    assert response.status_code == 204
    assert not response.content

def test_delete_expense_not_found(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    expense_id = uuid.uuid4()

    response = client.delete(f'/expenses/{expense_id}', headers=owner['headers'])
    assert response.status_code == 404

def test_delete_expense_not_authorized(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense',
        'total_amount': 50,
        'split_type': 'equal',
        'expense_date': datetime.now(timezone.utc).isoformat(),
        'participants': [
            {'user_id': owner['user']['id']},
            {'user_id': member['user']['id']}
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=expense_payload, headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    expense_id = data['id']

    response = client.delete(f'/expenses/{expense_id}', headers=member['headers'])
    assert response.status_code == 403

def test_delete_expense_not_retrievable(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense',
        'total_amount': 50,
        'split_type': 'equal',
        'expense_date': datetime.now(timezone.utc).isoformat(),
        'participants': [
            {'user_id': owner['user']['id']},
            {'user_id': member['user']['id']}
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=expense_payload, headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    expense_id = data['id']

    response = client.delete(f'/expenses/{expense_id}', headers=owner['headers'])
    assert response.status_code == 204

    response = client.get(f'/expenses/{expense_id}', headers=owner['headers'])
    assert response.status_code == 404

def test_delete_expense_from_expense_list(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense',
        'total_amount': 50,
        'split_type': 'equal',
        'expense_date': datetime.now(timezone.utc).isoformat(),
        'participants': [
            {'user_id': owner['user']['id']},
            {'user_id': member['user']['id']}
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=expense_payload, headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    expense_id = data['id']

    response = client.delete(f'/expenses/{expense_id}', headers=owner['headers'])
    assert response.status_code == 204

    response = client.get(f'/groups/{group_id}/expenses', headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    expense_ids = {expense['id'] for expense in data}
    assert expense_id not in expense_ids

def test_list_group_expenses_ordering(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    first_expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense',
        'total_amount': 50,
        'split_type': 'equal',
        'expense_date': '2026-06-08T15:30:00+03:00',
        'participants': [
            {'user_id': owner['user']['id']},
            {'user_id': member['user']['id']}
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=first_expense_payload, headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    first_expense_id = data['id']

    second_expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense',
        'total_amount': 50,
        'split_type': 'equal',
        'expense_date': '2026-06-09T15:30:00+03:00',
        'participants': [
            {'user_id': owner['user']['id']},
            {'user_id': member['user']['id']}
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=second_expense_payload, headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    second_expense_id = data['id']

    third_expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense',
        'total_amount': 50,
        'split_type': 'equal',
        'expense_date': '2026-06-11T15:30:00+03:00',
        'participants': [
            {'user_id': owner['user']['id']},
            {'user_id': member['user']['id']}
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=third_expense_payload, headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    third_expense_id = data['id']

    response = client.get(f'/groups/{group_id}/expenses', headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    expense_ids = [expense['id'] for expense in data]
    assert [third_expense_id, second_expense_id, first_expense_id] == expense_ids

def test_list_group_expenses_pagination(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    first_expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense',
        'total_amount': 50,
        'split_type': 'equal',
        'expense_date': '2026-06-08T15:30:00+03:00',
        'participants': [
            {'user_id': owner['user']['id']},
            {'user_id': member['user']['id']}
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=first_expense_payload, headers=owner['headers'])
    assert response.status_code == 200

    second_expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense',
        'total_amount': 50,
        'split_type': 'equal',
        'expense_date': '2026-06-09T15:30:00+03:00',
        'participants': [
            {'user_id': owner['user']['id']},
            {'user_id': member['user']['id']}
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=second_expense_payload, headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    second_expense_id = data['id']

    third_expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense',
        'total_amount': 50,
        'split_type': 'equal',
        'expense_date': '2026-06-11T15:30:00+03:00',
        'participants': [
            {'user_id': owner['user']['id']},
            {'user_id': member['user']['id']}
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=third_expense_payload, headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    third_expense_id = data['id']

    params = {
        'limit': 2,
        'offset': 0
    }

    response = client.get(f'/groups/{group_id}/expenses', params=params, headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    expense_ids = [expense['id'] for expense in data]
    assert [third_expense_id, second_expense_id] == expense_ids

def test_list_group_expenses_pagination_second_newest_result(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    first_expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense',
        'total_amount': 50,
        'split_type': 'equal',
        'expense_date': '2026-06-08T15:30:00+03:00',
        'participants': [
            {'user_id': owner['user']['id']},
            {'user_id': member['user']['id']}
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=first_expense_payload, headers=owner['headers'])
    assert response.status_code == 200

    second_expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense',
        'total_amount': 50,
        'split_type': 'equal',
        'expense_date': '2026-06-09T15:30:00+03:00',
        'participants': [
            {'user_id': owner['user']['id']},
            {'user_id': member['user']['id']}
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=second_expense_payload, headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    second_expense_id = data['id']

    third_expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense',
        'total_amount': 50,
        'split_type': 'equal',
        'expense_date': '2026-06-11T15:30:00+03:00',
        'participants': [
            {'user_id': owner['user']['id']},
            {'user_id': member['user']['id']}
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=third_expense_payload, headers=owner['headers'])
    assert response.status_code == 200

    params = {
        'limit': 1,
        'offset': 1
    }

    response = client.get(f'/groups/{group_id}/expenses', params=params, headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    expense_ids = [expense['id'] for expense in data]
    assert [second_expense_id] == expense_ids

def test_list_group_expenses_rejects_zero_limit(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    group_id = context['group']['id']

    params = {
        'limit': 0
    }

    response = client.get(f'/groups/{group_id}/expenses', params=params, headers=owner['headers'])
    assert response.status_code == 422

def test_list_group_expenses_rejects_negative_offset(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    group_id = context['group']['id']

    params = {
        'offset': -1
    }

    response = client.get(f'/groups/{group_id}/expenses', params=params, headers=owner['headers'])
    assert response.status_code == 422

def test_list_group_expenses_filtered_by_payer_id(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    owner_expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense',
        'total_amount': 50,
        'split_type': 'equal',
        'expense_date': datetime.now(timezone.utc).isoformat(),
        'participants': [
            {'user_id': owner['user']['id']},
            {'user_id': member['user']['id']}
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=owner_expense_payload, headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    expense_id = data['id']

    member_expense_payload = {
        'payer_id': member['user']['id'],
        'title': 'test_expense',
        'total_amount': 50,
        'split_type': 'equal',
        'expense_date': datetime.now(timezone.utc).isoformat(),
        'participants': [
            {'user_id': owner['user']['id']},
            {'user_id': member['user']['id']}
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=member_expense_payload, headers=owner['headers'])
    assert response.status_code == 200

    params = {
        'payer_id': owner['user']['id']
    }

    response = client.get(f'/groups/{group_id}/expenses', params=params, headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    expense_ids = [expense['id'] for expense in data]
    assert [expense_id] == expense_ids
    assert all(expense['payer_id'] == owner['user']['id'] for expense in data)

def test_list_group_expenses_filtered_by_date_from(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    first_expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense',
        'total_amount': 50,
        'split_type': 'equal',
        'expense_date': '2026-06-10T15:30:00+03:00',
        'participants': [
            {'user_id': owner['user']['id']},
            {'user_id': member['user']['id']}
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=first_expense_payload, headers=owner['headers'])
    assert response.status_code == 200

    second_expense_payload = {
        'payer_id': member['user']['id'],
        'title': 'test_expense',
        'total_amount': 50,
        'split_type': 'equal',
        'expense_date': '2026-06-08T15:30:00+03:00',
        'participants': [
            {'user_id': owner['user']['id']},
            {'user_id': member['user']['id']}
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=second_expense_payload, headers=owner['headers'])
    assert response.status_code == 200

    third_expense_payload = {
        'payer_id': member['user']['id'],
        'title': 'test_expense',
        'total_amount': 50,
        'split_type': 'equal',
        'expense_date': '2026-06-13T15:30:00+03:00',
        'participants': [
            {'user_id': owner['user']['id']},
            {'user_id': member['user']['id']}
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=third_expense_payload, headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    third_expense_id = data['id']

    params = {
        'date_from': '2026-06-11T15:30:00+03:00'
    }

    response = client.get(f'/groups/{group_id}/expenses', params=params, headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()

    assert len(data) == 1
    expense_ids = [expense['id'] for expense in data]
    assert [third_expense_id] == expense_ids

def test_list_group_expenses_filtered_by_date_to(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    first_expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense',
        'total_amount': 50,
        'split_type': 'equal',
        'expense_date': '2026-06-10T15:30:00+03:00',
        'participants': [
            {'user_id': owner['user']['id']},
            {'user_id': member['user']['id']}
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=first_expense_payload, headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    first_expense_id = data['id']

    second_expense_payload = {
        'payer_id': member['user']['id'],
        'title': 'test_expense',
        'total_amount': 50,
        'split_type': 'equal',
        'expense_date': '2026-06-08T15:30:00+03:00',
        'participants': [
            {'user_id': owner['user']['id']},
            {'user_id': member['user']['id']}
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=second_expense_payload, headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    second_expense_id = data['id']

    third_expense_payload = {
        'payer_id': member['user']['id'],
        'title': 'test_expense',
        'total_amount': 50,
        'split_type': 'equal',
        'expense_date': '2026-06-13T15:30:00+03:00',
        'participants': [
            {'user_id': owner['user']['id']},
            {'user_id': member['user']['id']}
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=third_expense_payload, headers=owner['headers'])
    assert response.status_code == 200

    params = {
        'date_to': '2026-06-10T15:30:00+03:00'
    }

    response = client.get(f'/groups/{group_id}/expenses', params=params, headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()

    assert len(data) == 2
    expense_ids = [expense['id'] for expense in data]
    assert [first_expense_id, second_expense_id] == expense_ids

def test_list_group_expenses_filtered_by_date_to_and_date_from(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    first_expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'test_expense',
        'total_amount': 50,
        'split_type': 'equal',
        'expense_date': '2026-06-10T15:30:00+03:00',
        'participants': [
            {'user_id': owner['user']['id']},
            {'user_id': member['user']['id']}
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=first_expense_payload, headers=owner['headers'])
    assert response.status_code == 200

    second_expense_payload = {
        'payer_id': member['user']['id'],
        'title': 'test_expense',
        'total_amount': 50,
        'split_type': 'equal',
        'expense_date': '2026-06-11T15:30:00+03:00',
        'participants': [
            {'user_id': owner['user']['id']},
            {'user_id': member['user']['id']}
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=second_expense_payload, headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    second_expense_id = data['id']

    third_expense_payload = {
        'payer_id': member['user']['id'],
        'title': 'test_expense',
        'total_amount': 50,
        'split_type': 'equal',
        'expense_date': '2026-06-13T15:30:00+03:00',
        'participants': [
            {'user_id': owner['user']['id']},
            {'user_id': member['user']['id']}
        ]
    }

    response = client.post(f'/groups/{group_id}/expenses', json=third_expense_payload, headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    third_expense_id = data['id']

    params = {
        'date_from': '2026-06-11T15:30:00+03:00',
        'date_to': '2026-06-13T15:30:00+03:00',
    }

    response = client.get(f'/groups/{group_id}/expenses', params=params, headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()

    assert len(data) == 2
    expense_ids = [expense['id'] for expense in data]
    assert [third_expense_id, second_expense_id] == expense_ids