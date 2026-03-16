"""
Shared pytest fixtures for E2E tests.

Starts a live Flask server against a temporary SQLite database and seeds it
with a test user and a tracked item.  The server runs for the duration of the
test session; individual tests receive a fresh browser page via pytest-playwright.
"""

import os
import threading

import pytest
from werkzeug.serving import make_server

# Env vars must be set before app is imported (root conftest.py handles this,
# but we guard here too in case tests are collected in isolation).
os.environ.setdefault('SECRET_KEY', 'test-secret-key-for-testing-only')
os.environ.setdefault('JS_APP_ROOT', '')

from app import app as flask_app, db, User, TrackedItem, PriceHistory  # noqa: E402

TEST_HOST = '127.0.0.1'
TEST_PORT = 9753


# ---------------------------------------------------------------------------
# Application / database fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope='session')
def app(tmp_path_factory):
    """Configure the Flask app with a temporary test database."""
    db_path = tmp_path_factory.mktemp('testdb') / 'test.db'
    flask_app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'SECRET_KEY': 'test-secret-key-for-testing-only',
        'JS_APP_ROOT': '',
        'WTF_CSRF_ENABLED': False,
    })
    with flask_app.app_context():
        db.create_all()
    yield flask_app
    with flask_app.app_context():
        db.drop_all()


@pytest.fixture(scope='session')
def live_server(app):
    """Start a WSGI server in a daemon thread and return its base URL."""
    server = make_server(TEST_HOST, TEST_PORT, app)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f'http://{TEST_HOST}:{TEST_PORT}'
    server.shutdown()


# ---------------------------------------------------------------------------
# Seed data fixtures  (session-scoped so data is created once)
# ---------------------------------------------------------------------------

@pytest.fixture(scope='session')
def test_user(app):
    """Create a persistent test user and return its credentials."""
    with app.app_context():
        user = User(username='e2euser', email='e2e@example.com')
        user.set_password('E2ePass123!')
        db.session.add(user)
        db.session.commit()
        user_id = user.id
    return {'id': user_id, 'username': 'e2euser', 'password': 'E2ePass123!'}


@pytest.fixture(scope='session')
def test_item(app, test_user):
    """Seed a tracked item for the test user and return its id."""
    with app.app_context():
        item = TrackedItem(
            product_name='Test Widget',
            url='https://example.com/widget',
            css_selector='#price',
            current_price='49.99',
            target_price='45.00',
            price_change_status='same',
            currency='GBP',
            user_id=test_user['id'],
            needs_browser_check=False,
            last_check_method='css_selector',
        )
        db.session.add(item)
        db.session.commit()
        history = PriceHistory(item_id=item.id, price=49.99)
        db.session.add(history)
        db.session.commit()
        item_id = item.id
    return {'id': item_id}


# ---------------------------------------------------------------------------
# Browser helper fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def logged_in_page(page, live_server, test_user):
    """Return a Playwright page that is already authenticated."""
    page.goto(f'{live_server}/login')
    page.fill('#username', test_user['username'])
    page.fill('#password', test_user['password'])
    page.click('button[type="submit"]')
    page.wait_for_url(f'{live_server}/')
    return page
