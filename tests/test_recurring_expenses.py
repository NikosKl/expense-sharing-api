from decimal import Decimal

from tests.helpers import create_authenticated_group_members


def test_create_equal_recurring_expenses_success(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    recurring_expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'recurring expense',
        'total_amount': 100,
        'frequency': 'monthly',
        'next_run_at': '2026-08-21T15:30:00+03:00',
        'split_type': 'equal',
        'participants': [
            {'user_id': member['user']['id']},
            {'user_id': owner['user']['id']},
        ]
    }

    response = client.post(f'/groups/{group_id}/recurring-expenses', json=recurring_expense_payload, headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()

    assert data['split_type'] == 'equal'
    assert len(data['splits']) == 2
    assert data['title'] == 'recurring expense'
    assert data['frequency'] == 'monthly'
    assert Decimal(data['total_amount']) == Decimal('100')
    assert data['payer_id'] == owner['user']['id']
    assert data['description'] is None
    assert data['is_active'] is True

    split_amount = [Decimal(split['amount_owed']) for split in data['splits']]
    assert sum(split_amount) == Decimal(data['total_amount'])


def test_get_group_recurring_expenses_success(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    recurring_expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'recurring expense',
        'total_amount': 100,
        'frequency': 'monthly',
        'next_run_at': '2026-08-21T15:30:00+03:00',
        'split_type': 'equal',
        'participants': [
            {'user_id': member['user']['id']},
            {'user_id': owner['user']['id']},
        ]
    }

    response = client.post(f'/groups/{group_id}/recurring-expenses', json=recurring_expense_payload, headers=owner['headers'])
    assert response.status_code == 200

    response = client.get(f'/groups/{group_id}/recurring-expenses', headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()

    assert len(data) == 1

    returned_ids = {splits['user_id'] for splits in data[0]['splits']}
    expected_ids = {member['user']['id'], owner['user']['id']}

    assert returned_ids == expected_ids


def test_cancel_recurring_expense_success(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    recurring_expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'recurring expense',
        'total_amount': 100,
        'frequency': 'monthly',
        'next_run_at': '2026-08-21T15:30:00+03:00',
        'split_type': 'equal',
        'participants': [
            {'user_id': member['user']['id']},
            {'user_id': owner['user']['id']},
        ]
    }

    response = client.post(f'/groups/{group_id}/recurring-expenses', json=recurring_expense_payload, headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    recurring_expense_id = data['id']

    response = client.delete(f'/recurring-expenses/{recurring_expense_id}', headers=owner['headers'])
    assert response.status_code == 204

    response = client.get(f'/groups/{group_id}/recurring-expenses', headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()

    assert len(data) == 1
    assert data[0]['is_active'] is False