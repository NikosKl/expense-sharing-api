from sqlalchemy import select
from app.models import User

def test_register(client):
    response = client.post('/auth/register', json={
        'email': 'test_user@example.com',
        'username': 'test_user',
        'password': 'long_password'})

    assert response.status_code == 200

    data = response.json()

    assert 'id' in data
    assert 'email' in data
    assert 'username' in data
    assert 'password' not in data

def test_login(client):
    payload = {
        'email': 'test_user@example.com',
        'username': 'test_user',
        'password': 'long_password'}

    response = client.post('/auth/register', json=payload)

    assert response.status_code == 200

    response = client.post('/auth/login', data={'username': payload['email'], 'password': payload['password']})

    assert response.status_code == 200

    data = response.json()
    assert 'access_token' in data
    assert data['token_type'] == 'bearer'

def test_duplicate_email(client):
    payload = {
        'email': 'test_user@example.com',
        'username': 'test_user',
        'password': 'long_password'}

    response = client.post('/auth/register', json=payload)
    assert response.status_code == 200
    response = client.post('/auth/register', json={'email': 'test_user@example.com', 'username': 'new_test_user', 'password': 'long_password'})
    assert response.status_code == 409
    data = response.json()
    assert data['detail'] == 'User already exists'

def test_duplicate_username(client):
    payload = {
        'email': 'test_user@example.com',
        'username': 'test_user',
        'password': 'long_password'}

    response = client.post('/auth/register', json=payload)
    assert response.status_code == 200
    response = client.post('/auth/register', json={'email': 'new_test_user@example.com', 'username': 'test_user', 'password': 'long_password'})
    assert response.status_code == 409
    data = response.json()
    assert data['detail'] == 'User already exists'

def test_login_nonexistent_password(client):
    payload = {
        'email': 'test_user@example.com',
        'username': 'test_user',
        'password': 'long_password'}

    response = client.post('/auth/register', json=payload)

    assert response.status_code == 200

    response = client.post('/auth/login', data={'username': 'test_user@example.com', 'password': 'wrong_password'})

    assert response.status_code == 401

def test_login_nonexistent_email(client):
    payload = {
        'email': 'test_user@example.com',
        'username': 'test_user',
        'password': 'long_password'}

    response = client.post('/auth/register', json=payload)

    assert response.status_code == 200

    response = client.post('/auth/login', data={'username': 'wrong_user@example.com', 'password': 'long_password'})

    assert response.status_code == 401

def test_protected_route_valid_token(client):
    payload = {
        'email': 'test_user@example.com',
        'username': 'test_user',
        'password': 'long_password'}

    response = client.post('/auth/register', json=payload)
    assert response.status_code == 200
    register_data = response.json()
    response = client.post('/auth/login', data={'username': payload['email'], 'password': payload['password']})
    assert response.status_code == 200

    data = response.json()
    token = data['access_token']
    headers = {'Authorization': f'Bearer {token}'}

    response = client.get('/auth/me', headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data['id']
    assert data['id'] == register_data['id']
    assert data['email'] == payload['email']
    assert data['username'] == payload['username']
    assert data['is_active'] is True
    assert 'password' not in data

def test_protected_route_invalid_token(client):
    headers = {'Authorization': 'Bearer wrong_token'}

    response = client.get('/auth/me', headers=headers)
    assert response.status_code == 401

def test_protected_route_missing_token(client):
    response = client.get('/auth/me')
    assert response.status_code == 401

def test_register_missing_password(client):
    response = client.post('/auth/register', json={
        'email': 'test_user@example.com',
        'username': 'test_user'})
    assert response.status_code == 422

def test_login_missing_password(client):
    payload = {
        'email': 'test_user@example.com',
        'username': 'test_user',
        'password': 'long_password'}
    response = client.post('/auth/register', json=payload)
    assert response.status_code == 200

    response = client.post('/auth/login', data={'username': 'test_user@example.com'})
    assert response.status_code == 422

def test_login_missing_email(client):
    payload = {
        'email': 'test_user@example.com',
        'username': 'test_user',
        'password': 'long_password'}
    response = client.post('/auth/register', json=payload)
    assert response.status_code == 200

    response = client.post('/auth/login', data={'password': 'long_password'})
    assert response.status_code == 422

def test_register_short_password(client):
    response = client.post('/auth/register', json={
        'email': 'test_user@example.com',
        'username': 'test_user',
        'password': 'short'})

    assert response.status_code == 422

def test_register_invalid_email(client):
    payload = {
        'email': 'test_email',
        'username': 'test_user',
        'password': 'long_password'
    }

    response = client.post('/auth/register', json=payload)
    assert response.status_code == 422

def test_normalization_behavior(client):
    payload = {
        'email': 'TEST_USER@EXAMPLE.COM',
        'username': 'TEST_USER',
        'password': 'long_password'}
    response = client.post('/auth/register', json=payload)
    assert response.status_code == 200
    register_data = response.json()

    assert register_data['email'] == 'test_user@example.com'
    assert register_data['username'] == 'test_user'

    response = client.post('/auth/login', data={'username': 'test_user@example.com', 'password': 'long_password'})
    assert response.status_code == 200
    data = response.json()
    token = data['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    response = client.get('/auth/me', headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data['email'] == 'test_user@example.com'
    assert data['username'] == 'test_user'

def test_inactive_user_login_behavior(client, db_session):
    payload = {
        'email': 'TEST_USER@EXAMPLE.COM',
        'username': 'TEST_USER',
        'password': 'long_password'}
    response = client.post('/auth/register', json=payload)
    assert response.status_code == 200

    data = response.json()
    stmt = select(User).where(User.email == data['email'])
    user = db_session.scalar(stmt)
    assert user is not None

    user.is_active = False
    db_session.commit()

    response = client.post('/auth/login', data={'username': payload['email'], 'password': payload['password']})
    assert response.status_code == 403