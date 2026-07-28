import uuid
from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.models import Expense, RecurringExpense
from app.services.recurring_expense_service import calculate_next_run_at, process_due_recurring_expenses
from tests.helpers import create_authenticated_group_members, create_authenticated_user


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


def test_create_exact_recurring_expenses_success(client):
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
        'split_type': 'exact',
        'participants': [
            {'user_id': member['user']['id'], 'amount': 60},
            {'user_id': owner['user']['id'], 'amount': 40},
        ]
    }

    response = client.post(f'/groups/{group_id}/recurring-expenses', json=recurring_expense_payload, headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()

    assert data['split_type'] == 'exact'
    assert Decimal(data['total_amount']) == Decimal('100')

    split_amount = [Decimal(split['amount_owed']) for split in data['splits']]
    assert sum(split_amount) == Decimal(data['total_amount'])


def test_create_percentage_recurring_expenses_success(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    recurring_expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'recurring expense',
        'total_amount': 50,
        'frequency': 'monthly',
        'next_run_at': '2026-08-21T15:30:00+03:00',
        'split_type': 'percentage',
        'participants': [
            {'user_id': member['user']['id'], 'percentage': 70},
            {'user_id': owner['user']['id'], 'percentage': 30},
        ]
    }

    response = client.post(f'/groups/{group_id}/recurring-expenses', json=recurring_expense_payload, headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()

    assert data['split_type'] == 'percentage'
    assert Decimal(data['total_amount']) == Decimal('50')

    splits = {split['user_id']: split['amount_owed'] for split in data['splits']}
    assert Decimal(splits[member['user']['id']]) == Decimal('35')
    assert Decimal(splits[owner['user']['id']]) == Decimal('15')


def test_get_group_recurring_expenses_filters_by_is_active(client):
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

    response = client.post(f'/groups/{group_id}/recurring-expenses', json=recurring_expense_payload,
                           headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    recurring_expense_id = data['id']

    response = client.delete(f'/recurring-expenses/{recurring_expense_id}', headers=owner['headers'])
    assert response.status_code == 204

    params = {
        'is_active': True
    }

    response = client.get(f'/groups/{group_id}/recurring-expenses', params=params, headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()

    assert data == []

    params = {
        'is_active': False
    }

    response = client.get(f'/groups/{group_id}/recurring-expenses', params=params, headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()

    assert len(data) == 1
    assert data[0]['is_active'] is False


def test_recurring_expense_without_participants(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    group_id = context['group']['id']

    recurring_expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'recurring expense',
        'total_amount': 100,
        'frequency': 'monthly',
        'next_run_at': '2026-08-21T15:30:00+03:00',
        'split_type': 'equal',
        'participants': []
    }

    response = client.post(f'/groups/{group_id}/recurring-expenses', json=recurring_expense_payload, headers=owner['headers'])
    assert response.status_code == 422


def test_recurring_expense_invalid_frequency(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    recurring_expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'recurring expense',
        'total_amount': 100,
        'frequency': '',
        'next_run_at': '2026-08-21T15:30:00+03:00',
        'split_type': 'equal',
        'participants': [
            {'user_id': member['user']['id']},
            {'user_id': owner['user']['id']},
        ]
    }

    response = client.post(f'/groups/{group_id}/recurring-expenses', json=recurring_expense_payload, headers=owner['headers'])
    assert response.status_code == 422


def test_recurring_expense_invalid_payer(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    user = uuid.uuid4()

    recurring_expense_payload = {
        'payer_id': str(user),
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
    assert response.status_code == 400


def test_recurring_expense_non_member_cannot_create_recurring_expense(client):
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

    response = client.post(f'/groups/{group_id}/recurring-expenses', json=recurring_expense_payload, headers=new_user['headers'])
    assert response.status_code == 403


def test_recurring_expense_non_member_cannot_list_recurring_expenses(client):
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

    response = client.get(f'/groups/{group_id}/recurring-expenses', headers=new_user['headers'])
    assert response.status_code == 403


def test_recurring_expense_non_creator_cannot_cancel_recurring_expense(client):
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

    response = client.delete(f'/recurring-expenses/{recurring_expense_id}', headers=member['headers'])
    assert response.status_code == 403


def test_recurring_expense_cancel_invalid_id(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    new_recurring_expense_id = uuid.uuid4()

    response = client.delete(f'/recurring-expenses/{new_recurring_expense_id}', headers=owner['headers'])
    assert response.status_code == 404


def test_calculate_next_run_at_daily():
    current_next_run_at = datetime.fromisoformat('2026-08-21T15:30:00+03:00')
    date = calculate_next_run_at(current_next_run_at, frequency='daily')
    assert date == datetime.fromisoformat('2026-08-22T15:30:00+03:00')


def test_calculate_next_run_at_weekly():
    current_next_run_at = datetime.fromisoformat('2026-08-21T15:30:00+03:00')
    date = calculate_next_run_at(current_next_run_at, frequency='weekly')
    assert date == datetime.fromisoformat('2026-08-28T15:30:00+03:00')


def test_calculate_next_run_at_monthly():
    current_next_run_at = datetime.fromisoformat('2026-08-21T15:30:00+03:00')
    date = calculate_next_run_at(current_next_run_at, frequency='monthly')
    assert date == datetime.fromisoformat('2026-09-21T15:30:00+03:00')


def test_calculate_next_run_at_monthly_handles_end_of_month():
    current_next_run_at = datetime.fromisoformat('2026-01-31T15:30:00+03:00')
    date = calculate_next_run_at(current_next_run_at, frequency='monthly')
    assert date == datetime.fromisoformat('2026-02-28T15:30:00+03:00')


def test_calculate_next_run_at_invalid_frequency():
    current_next_run_at = datetime.fromisoformat('2026-08-21T15:30:00+03:00')
    with pytest.raises(ValueError):
        calculate_next_run_at(current_next_run_at, frequency='invalid')


def test_process_due_recurring_expenses_returns_zero_when_none_due(client, db_session):
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

    now = datetime.fromisoformat('2026-08-01T15:30:00+03:00')
    created_count = process_due_recurring_expenses(db_session, now)

    assert created_count == 0


def test_process_due_recurring_expenses_creates_expense_and_advances_next_run_at(client, db_session):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    recurring_expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'recurring expense',
        'total_amount': 100,
        'frequency': 'monthly',
        'next_run_at': '2026-08-01T15:30:00+03:00',
        'split_type': 'equal',
        'participants': [
            {'user_id': member['user']['id']},
            {'user_id': owner['user']['id']},
        ]
    }

    response = client.post(f'/groups/{group_id}/recurring-expenses', json=recurring_expense_payload, headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()

    now = datetime.fromisoformat('2026-08-01T15:30:00+03:00')
    created_count = process_due_recurring_expenses(db_session, now)

    assert created_count == 1

    group_uuid = uuid.UUID(group_id)

    stmt = select(Expense).where(Expense.title == 'recurring expense', Expense.group_id == group_uuid)
    expense = db_session.scalar(stmt)

    assert expense is not None
    assert expense.expense_date == now

    stmt = select(RecurringExpense).where(RecurringExpense.id == data['id'], RecurringExpense.group_id == group_uuid)
    recurring_expense = db_session.scalar(stmt)

    assert recurring_expense is not None
    assert recurring_expense.next_run_at == datetime.fromisoformat('2026-09-01T15:30:00+03:00')


def test_process_due_recurring_expenses_ignores_inactive_recurring_expenses(client, db_session):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    recurring_expense_payload = {
        'payer_id': owner['user']['id'],
        'title': 'recurring expense',
        'total_amount': 100,
        'frequency': 'monthly',
        'next_run_at': '2026-08-01T15:30:00+03:00',
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

    now = datetime.fromisoformat('2026-08-01T15:30:00+03:00')
    created_count = process_due_recurring_expenses(db_session, now)

    assert created_count == 0

    group_uuid = uuid.UUID(group_id)

    stmt = select(Expense).where(Expense.title == 'recurring expense', Expense.group_id == group_uuid)
    expenses = db_session.scalars(stmt).all()

    assert expenses == []
