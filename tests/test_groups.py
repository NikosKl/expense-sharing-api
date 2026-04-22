import uuid
from tests.helpers import create_authenticated_user


def test_create_group(client):

    owner = create_authenticated_user(client)
    payload = {
        'name': 'test_group',
        'description': 'test description'
    }

    response = client.post('/groups', json=payload, headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    assert data['name'] == 'test_group'
    assert data['description'] == 'test description'

def test_get_all_groups(client):
    owner = create_authenticated_user(
        client,
        email='owner@example.com',
        username='owner',
        password='long_password'
    )
    response = client.post('/groups', json={'name': 'test_group_1'}, headers=owner['headers'])
    assert response.status_code == 200
    group_a = response.json()
    group_a_id = group_a['id']

    member = create_authenticated_user(
        client,
        email='member@example.com',
        username='member',
        password='long_password'
    )

    response = client.post('/groups', json={'name': 'test_group_2'}, headers=member['headers'])
    assert response.status_code == 200
    group_one = response.json()
    group_one_id = group_one['id']

    response = client.post('/groups', json={'name': 'test_group_3'}, headers=member['headers'])
    assert response.status_code == 200
    group_two = response.json()
    group_two_id = group_two['id']

    response = client.get('/groups', headers=member['headers'])
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    returned_ids = [group['id'] for group in data]
    assert group_a_id not in returned_ids
    assert group_one_id in returned_ids
    assert group_two_id in returned_ids

def test_get_group(client):
    owner = create_authenticated_user(client)
    payload = {
        'name': 'test_group'
    }

    response = client.post('/groups', json=payload, headers=owner['headers'])
    assert response.status_code == 200

    data = response.json()
    group_id = data['id']

    response = client.get(f'/groups/{group_id}', headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    assert data['id'] == group_id
    assert data['name'] == 'test_group'

def test_group_not_found(client):
    headers = create_authenticated_user(client)

    missing_group = uuid.uuid4()
    response = client.get(f'/groups/{missing_group}', headers=headers['headers'])
    assert response.status_code == 404

def test_inaccessible_group(client):
    owner = create_authenticated_user(
        client,
        email='owner@example.com',
        username='owner',
        password='long_password'
    )
    member = create_authenticated_user(
        client,
        email='member@example.com',
        username='member',
        password='long_password'
    )

    response = client.post('/groups', json={'name': 'test_group'}, headers=owner['headers'])
    assert response.status_code == 200
    data = response.json()
    group_id = data['id']
    response = client.get(f'/groups/{group_id}', headers=member['headers'])
    assert response.status_code == 404