import uuid
from tests.helpers import create_authenticated_user

def test_owner_can_add_group_member(client):
    owner = create_authenticated_user(client)

    response = client.post('/auth/register', json={
        'email': 'user_b@example.com',
        'username': 'user_b',
        'password': 'long_password',
    })
    assert response.status_code == 200
    member_data = response.json()
    member_id = member_data['id']

    response = client.post('/groups', json={'name': 'test_group'}, headers=owner['headers'])
    assert response.status_code == 200
    group_data = response.json()
    group_id = group_data['id']

    response = client.post(f'/groups/{group_id}/members', json={'user_id': member_id}, headers=owner['headers'])
    assert response.status_code == 200

    data = response.json()
    assert data['user_id'] == member_id
    assert data['group_id'] == group_id
    assert data['role'] == 'member'
    assert member_id != group_data['created_by']

def test_non_owner_cannot_add_member(client):
    owner = create_authenticated_user(client)
    member = create_authenticated_user(
        client,
        email='member_a@example.com',
        username='member_a',
        password='long_password',
    )

    response = client.post('/groups', json={'name': 'test_group'}, headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    group_id = data['id']

    response = client.post(f'/groups/{group_id}/members', json={'user_id': member['user']['id']}, headers=owner['headers'])
    assert response.status_code == 200

    target_user = create_authenticated_user(
        client,
        email='target_user@example.com',
        username='target_user',
        password='long_password',
    )

    response = client.post(f'/groups/{group_id}/members', json={'user_id': target_user['user']['id']}, headers=member['headers'])
    assert response.status_code == 403

def test_cannot_add_nonexistent_user(client):
    owner = create_authenticated_user(client)

    member_id = uuid.uuid4()

    response = client.post('/groups', json={'name': 'test_group'}, headers=owner['headers'])
    assert response.status_code == 200
    group_data = response.json()
    group_id = group_data['id']

    response = client.post(f'/groups/{group_id}/members', json={'user_id': str(member_id)}, headers=owner['headers'])
    assert response.status_code == 404

def cannot_add_duplicate_member(client):
    owner = create_authenticated_user(client)
    member = create_authenticated_user(client)

    response = client.post('/groups', json={'name': 'test_group'}, headers=owner['headers'])
    assert response.status_code == 200
    group_data = response.json()
    group_id = group_data['id']

    response = client.post(f'/groups/{group_id}/members', json={'user_id': member['user']['id']}, headers=owner['headers'])
    assert response.status_code == 200
    response = client.post(f'/groups/{group_id}/members', json={'user_id': member['user']['id']},headers=owner['headers'])
    assert response.status_code == 409