def get_auth_headers(client, email='test_user@example.com', username='test_user', password='long_password'):
    payload = {'email': email, 'username': username, 'password': password}
    client.post('/auth/register', json=payload)
    login_payload = {'username': email, 'password': password}
    response = client.post('/auth/login', data=login_payload)
    data = response.json()
    token = data['access_token']
    return {'Authorization': f'Bearer {token}'}

def create_authenticated_user(client, email='test_user@example.com', username='test_user', password='long_password'):
    payload = {'email': email, 'username': username, 'password': password}
    response = client.post('/auth/register', json=payload)
    user_data = response.json()
    login_payload = {'username': email, 'password': password}
    response = client.post('/auth/login', data=login_payload)
    data = response.json()
    token = data['access_token']
    return {
        'user': user_data,
        'headers': {'Authorization': f'Bearer {token}'}}