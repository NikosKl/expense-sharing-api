from tests.conftest import get_auth_headers

def test_create_group(client):

    headers = get_auth_headers(client)
    payload = {
        'name': 'test_group',
        'description': 'test description'
    }

    response = client.post('/groups', json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data['name'] == 'test_group'
    assert data['description'] == 'test description'

def test_get_all_groups(client):
    headers_one = get_auth_headers(
        client,
        email='test_user_one@example.com',
        username='test_user_one',
        password='long_password'
    )
    response = client.post('/groups', json={'name': 'test_group_1'}, headers=headers_one)
    assert response.status_code == 200

    headers_two = get_auth_headers(
        client,
        email='test_user_two@example.com',
        username='test_user_two',
        password='long_password'
    )

    response = client.post('/groups', json={'name': 'test_group_2'}, headers=headers_two)
    assert response.status_code == 200

    response = client.post('/groups', json={'name': 'test_group_3'}, headers=headers_two)
    assert response.status_code == 200

    response = client.get('/groups', headers=headers_two)
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2