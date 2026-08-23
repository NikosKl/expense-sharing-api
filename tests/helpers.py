from datetime import datetime, timezone


def create_authenticated_user(client, email='test_user@example.com', username='test_user', password='long_password'):
    payload = {'email': email, 'username': username, 'password': password}
    response = client.post('/auth/register', json=payload)
    assert response.status_code == 200
    user_data = response.json()
    login_payload = {'username': email, 'password': password}
    response = client.post('/auth/login', data=login_payload)
    assert response.status_code == 200
    data = response.json()
    token = data['access_token']
    return {
        'user': user_data,
        'headers': {'Authorization': f'Bearer {token}'}}

def create_authenticated_group_members(client):
    owner = create_authenticated_user(client)

    member = create_authenticated_user(
        client,
        email='member_a@example.com',
        username='member_a',
        password='long_password',
    )

    response = client.post('/groups', json={'name': 'test_group'}, headers=owner['headers'])
    assert response.status_code == 200
    group = response.json()
    group_id = group['id']


    response = client.post(f'/groups/{group_id}/members', json={'user_id': member['user']['id']}, headers=owner['headers'])
    assert response.status_code == 200
    group_member = response.json()

    return {
        'owner': owner,
        'member': member,
        'group': group,
        'group_member': group_member,
    }

def create_authenticated_group_with_expense(client):
    owner = create_authenticated_user(client)

    member = create_authenticated_user(
        client,
        email='member_a@example.com',
        username='member_a',
        password='long_password',
    )

    response = client.post('/groups', json={'name': 'test_group'}, headers=owner['headers'])
    assert response.status_code == 200
    group = response.json()
    group_id = group['id']

    response = client.post(f'/groups/{group_id}/members', json={'user_id': member['user']['id']},
                           headers=owner['headers'])
    assert response.status_code == 200
    group_member = response.json()

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
    group_expense = response.json()

    return {
        'owner': owner,
        'member': member,
        'group': group,
        'group_member': group_member,
        'expense': group_expense
    }