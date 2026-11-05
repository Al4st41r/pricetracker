"""Unit tests (no browser) for SSRF protection, auth on /proxy, alerts and the check job."""

import itertools
import os
import re

import pytest
import requests

import app as app_module
from app import (
    TrackedItem,
    UnsafeURLError,
    User,
    db,
    safe_get,
    validate_public_url,
)

_counter = itertools.count()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def user(app):
    n = next(_counter)
    with app.app_context():
        u = User(username=f'unit{n}', email=f'unit{n}@example.com')
        u.set_password('pw-12345678')
        db.session.add(u)
        db.session.commit()
        return {'id': u.id, 'username': u.username, 'password': 'pw-12345678'}


@pytest.fixture()
def logged_in(client, user):
    client.post('/login', data={'username': user['username'], 'password': user['password']})
    return client


# --- validate_public_url / safe_get -------------------------------------------------

@pytest.mark.parametrize('url', [
    'file:///etc/passwd',
    'javascript:alert(1)',
    'ftp://example.com/x',
    'gopher://example.com',
    'http://127.0.0.1:5012/',
    'http://localhost/',
    'http://10.0.0.5/',
    'http://192.168.1.1/',
    'http://172.16.0.1/',
    'http://169.254.169.254/latest/meta-data/',
    'http://[::1]/',
    'http://[::ffff:127.0.0.1]/',
    'http://0.0.0.0/',
    'http:///nohost',
    '',
])
def test_validate_rejects_unsafe_urls(url):
    with pytest.raises(UnsafeURLError):
        validate_public_url(url)


def test_validate_accepts_public_ip_literal():
    assert validate_public_url('https://93.184.216.34/product') == 'https://93.184.216.34/product'


class _Resp:
    def __init__(self, status=200, location=None, text=''):
        self.status_code = status
        self.headers = {'Location': location} if location else {}
        self.is_redirect = bool(location)
        self.is_permanent_redirect = False
        self.text = text


def test_safe_get_rechecks_redirect_targets(monkeypatch):
    calls = []

    def fake_get(url, **kwargs):
        calls.append(url)
        assert kwargs['allow_redirects'] is False
        return _Resp(302, location='http://127.0.0.1:5012/secret')

    monkeypatch.setattr(requests, 'get', fake_get)
    with pytest.raises(UnsafeURLError):
        safe_get('https://93.184.216.34/start')
    assert calls == ['https://93.184.216.34/start']  # the loopback hop was never fetched


def test_safe_get_follows_public_redirects(monkeypatch):
    responses = iter([_Resp(301, location='/next'), _Resp(200, text='ok')])
    monkeypatch.setattr(requests, 'get', lambda url, **kw: next(responses))
    assert safe_get('https://93.184.216.34/start').text == 'ok'


# --- routes -----------------------------------------------------------------------

def test_proxy_requires_login(client):
    resp = client.get('/proxy?url=https://93.184.216.34/')
    assert resp.status_code == 302
    assert '/login' in resp.headers['Location']


def test_proxy_rejects_internal_address(logged_in):
    resp = logged_in.get('/proxy?url=http://127.0.0.1:5012/')
    assert resp.status_code == 400


def test_debug_route_removed(client):
    assert client.get('/debug').status_code == 404


@pytest.mark.parametrize('url', ['javascript:alert(1)', 'file:///etc/passwd', 'http://127.0.0.1/', 'http://169.254.169.254/'])
def test_track_item_rejects_unsafe_urls(logged_in, url, app):
    resp = logged_in.post('/track_item', data={'url': url, 'target_price': '10', 'css_selector': '.p'})
    assert resp.status_code == 400
    with app.app_context():
        assert TrackedItem.query.filter_by(url=url).count() == 0


def test_discover_price_rejects_internal_address(logged_in):
    resp = logged_in.post('/discover_price', json={'url': 'http://10.0.0.1/'})
    assert resp.status_code == 400


# --- configuration ---------------------------------------------------------------

def test_cookie_flags_configured_in_source():
    # The test fixture overrides Secure for plain HTTP, so check the module defaults.
    src = open(app_module.__file__).read()
    assert "SESSION_COOKIE_HTTPONLY'] = True" in src
    assert "SESSION_COOKIE_SAMESITE'] = 'Lax'" in src
    assert "SESSION_COOKIE_SECURE'] = _cookie_secure" in src
    assert app_module.app.config['SESSION_COOKIE_HTTPONLY'] is True
    assert app_module.app.config['SESSION_COOKIE_SAMESITE'] == 'Lax'


def test_static_urls_are_versioned(client):
    html = client.get('/login').get_data(as_text=True)
    assert re.search(r'css/app\.css\?v=\w+', html)


# --- alerts and the nightly job ----------------------------------------------------

def test_send_email_defined_before_main_block():
    """When run as a script, app.run() blocks, so send_email must precede the guard."""
    src = open(app_module.__file__).read()
    assert src.index('def send_email') < src.index("if __name__ == '__main__'")


def _make_item(app, user_id, **kw):
    with app.app_context():
        item = TrackedItem(
            product_name=kw.get('name', 'Widget'), url=kw.get('url', 'https://93.184.216.34/w'),
            css_selector=kw.get('selector', '.price'), current_price=kw.get('current', '20.00'),
            target_price=kw.get('target', '10.00'), currency='GBP', user_id=user_id,
        )
        db.session.add(item)
        db.session.commit()
        return item.id


def test_price_drop_sends_alert(app, user, monkeypatch):
    sent = []
    monkeypatch.setattr(app_module, 'send_email', lambda **kw: sent.append(kw))
    item_id = _make_item(app, user['id'])
    with app.app_context():
        item = db.session.get(TrackedItem, item_id)
        app_module.update_item_price(item, '£9.50', 'css_selector')
        db.session.commit()
    assert len(sent) == 1
    assert 'Widget' in sent[0]['subject']


def test_check_prices_survives_one_failing_item(app, user, monkeypatch):
    bad = _make_item(app, user['id'], name='Bad')
    good = _make_item(app, user['id'], name='Good')

    def fake_check(item):
        if item.product_name == 'Bad':
            raise RuntimeError('boom')
        item.current_price = '5.00'

    monkeypatch.setattr(app_module, 'check_item', fake_check)
    app_module.check_prices()
    with app.app_context():
        assert db.session.get(TrackedItem, good).current_price == '5.00'
        assert db.session.get(TrackedItem, bad).current_price == '20.00'


def test_safe_check_prices_never_raises(monkeypatch):
    def boom():
        raise RuntimeError('boom')
    monkeypatch.setattr(app_module, 'check_prices', boom)
    app_module.safe_check_prices()  # must not raise


def test_check_item_sends_user_agent_and_ignores_error_pages(app, user, monkeypatch):
    seen = {}

    class Page:
        text = '<span class="price">£1.00</span>'
        def raise_for_status(self):
            raise requests.exceptions.HTTPError('500')

    def fake_get(url, **kw):
        seen['headers'] = kw.get('headers')
        return Page()

    monkeypatch.setattr(app_module, 'safe_get', fake_get)
    monkeypatch.setattr(app_module, 'browser_check_price', lambda url: (None, None))
    item_id = _make_item(app, user['id'])
    with app.app_context():
        item = db.session.get(TrackedItem, item_id)
        app_module.check_item(item)
        assert item.current_price == '20.00'  # error page was not parsed as a price
    assert 'Mozilla' in seen['headers']['User-Agent']
