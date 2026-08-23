import uuid
from datetime import datetime, timezone

from tests.helpers import create_authenticated_group_with_expense, create_authenticated_user, \
    create_authenticated_group_members


def test_audit_log_success(client):
    context = create_authenticated_group_with_expense(client)

    owner = context['owner']
    group_id = context['group']['id']

    response = client.get(f'/groups/{group_id}/audit-logs', headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()

    expense_logs = [log for log in data if log['action'] == 'expense.created']

    assert len(expense_logs) == 1

    expense_log = expense_logs[0]

    assert expense_log['action'] == 'expense.created'
    assert expense_log['target_type'] == 'expense'
    assert expense_log['performed_by_id'] == owner['user']['id']
    assert expense_log['group_id'] == group_id

def test_audit_log_forbidden_for_non_member(client):
    context = create_authenticated_group_with_expense(client)

    group_id = context['group']['id']

    new_user = create_authenticated_user(
        client,
        email='new_user@example.com',
        username='new_user',
        password='long_password'
    )

    response = client.get(f'/groups/{group_id}/audit-logs', headers=new_user['headers'])
    assert response.status_code == 403

def test_audit_log_group_not_found(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']

    group_id = uuid.uuid4()

    response = client.get(f'/groups/{group_id}/audit-logs', headers=owner['headers'])
    assert response.status_code == 404

def test_audit_log_pagination(client):
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
        'limit': 2,
        'offset': 0
    }

    response = client.get(f'/groups/{group_id}/audit-logs', params=params, headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()

    assert len(data) == 2

def test_audit_log_rejects_zero_limit(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    group_id = context['group']['id']

    params = {
        'limit': 0
    }

    response = client.get(f'/groups/{group_id}/audit-logs', params=params, headers=owner['headers'])
    assert response.status_code == 422


def test_audit_log_rejects_negative_offset(client):
    context = create_authenticated_group_members(client)

    owner = context['owner']
    group_id = context['group']['id']

    params = {
        'offset': -1
    }

    response = client.get(f'/groups/{group_id}/audit-logs', params=params, headers=owner['headers'])
    assert response.status_code == 422

def test_audit_log_update_success(client):
    context = create_authenticated_group_with_expense(client)
    owner = context['owner']
    group_id = context['group']['id']
    expense_id = context['expense']['id']

    update_payload = {
        'title': 'updated test expense',
        'description': 'updated description',
        'expense_date': '2026-05-21T15:30:00+03:00'
    }

    response = client.patch(f'/expenses/{expense_id}', json=update_payload, headers=owner['headers'])
    assert response.status_code == 200

    response = client.get(f'/groups/{group_id}/audit-logs', headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()

    expense_logs = [log for log in data if log['action'] == 'expense.updated']
    assert len(expense_logs) == 1

    expense_log = expense_logs[0]
    assert expense_log['action'] == 'expense.updated'

def test_audit_log_delete_expense(client):
    context = create_authenticated_group_with_expense(client)
    owner = context['owner']
    group_id = context['group']['id']
    expense_id = context['expense']['id']

    response = client.delete(f'/expenses/{expense_id}', headers=owner['headers'])
    assert response.status_code == 204

    response = client.get(f'/groups/{group_id}/audit-logs', headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()

    expense_log = next((log for log in data if log['action'] == 'expense.deleted'), None)
    assert expense_log is not None
    assert expense_log['action'] == 'expense.deleted'

def test_audit_log_create_settlement_success(client):
    context = create_authenticated_group_with_expense(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    settlement_payload = {
        'payer_id': member['user']['id'],
        'receiver_id': owner['user']['id'],
        'amount': 13,
        'settled_at': datetime.now(timezone.utc).isoformat(),
    }

    response = client.post(f'/groups/{group_id}/settlements', json=settlement_payload, headers=member['headers'])
    assert response.status_code == 200

    response = client.get(f'/groups/{group_id}/audit-logs', headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    settlement_log = next((log for log in data if log['action'] == 'settlement.created'), None)
    assert settlement_log is not None
    assert settlement_log['action'] == 'settlement.created'

def test_audit_log_update_settlement(client):
    context = create_authenticated_group_with_expense(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    settlement_payload = {
        'payer_id': member['user']['id'],
        'receiver_id': owner['user']['id'],
        'amount': 13,
        'settled_at': datetime.now(timezone.utc).isoformat(),
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

    response = client.patch(f'/settlements/{settlement_id}', json=updated_settlement_payload, headers=member['headers'])
    assert response.status_code == 200

    response = client.get(f'/groups/{group_id}/audit-logs', headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    update_settlement_log = next((log for log in data if log['action'] == 'settlement.updated'), None)
    assert update_settlement_log is not None
    assert update_settlement_log['action'] == 'settlement.updated'

def test_audit_log_delete_settlement(client):
    context = create_authenticated_group_with_expense(client)

    owner = context['owner']
    member = context['member']
    group_id = context['group']['id']

    settlement_payload = {
        'payer_id': member['user']['id'],
        'receiver_id': owner['user']['id'],
        'amount': 13,
        'settled_at': datetime.now(timezone.utc).isoformat(),
    }

    response = client.post(f'/groups/{group_id}/settlements', json=settlement_payload, headers=member['headers'])
    assert response.status_code == 200
    data = response.json()
    settlement_id = data['id']

    response = client.delete(f'/settlements/{settlement_id}', headers=member['headers'])
    assert response.status_code == 204

    response = client.get(f'/groups/{group_id}/audit-logs', headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    delete_settlement_log = next((log for log in data if log['action'] == 'settlement.deleted'), None)
    assert delete_settlement_log is not None
    assert delete_settlement_log['action'] == 'settlement.deleted'

def test_audit_log_group_member_added(client):
    context = create_authenticated_group_with_expense(client)

    owner = context['owner']
    group_id = context['group']['id']

    response = client.get(f'/groups/{group_id}/audit-logs', headers=owner['headers'])
    assert response.status_code == 200

    data = response.json()
    group_member_log = next((log for log in data if log['action'] == 'group_member.added'), None)
    assert group_member_log is not None
    assert group_member_log['action'] == 'group_member.added'

def test_audit_log_group_member_removed(client):
    context = create_authenticated_group_with_expense(client)

    owner = context['owner']
    group_id = context['group']['id']

    new_user = create_authenticated_user(
        client,
        email='new_user@example.com',
        username='new_user',
        password='long_password'
    )

    user_id = new_user['user']['id']

    response = client.post(f'/groups/{group_id}/members', json={'user_id': user_id}, headers=owner['headers'])
    assert response.status_code == 200

    response = client.delete(f'/groups/{group_id}/members/{user_id}', headers=owner['headers'])
    assert response.status_code == 204

    response = client.get(f'/groups/{group_id}/audit-logs', headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    group_member_log = next((log for log in data if log['action'] == 'group_member.removed'), None)
    assert group_member_log is not None
    assert group_member_log['action'] == 'group_member.removed'