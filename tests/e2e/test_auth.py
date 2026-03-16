"""
E2E tests for authentication: register, login, and logout flows.
"""


# ---------------------------------------------------------------------------
# Scenario 1: Unauthenticated home page shows welcome copy
# ---------------------------------------------------------------------------

def test_unauthenticated_home_shows_welcome(page, live_server):
    page.goto(f'{live_server}/')
    assert page.locator('h1', has_text='Welcome to Price Tracker').is_visible()
    # Nav links present (target the nav element to avoid strict-mode conflicts
    # with duplicate links in the page body)
    assert page.locator('nav').get_by_role('link', name='Register').is_visible()
    assert page.locator('nav').get_by_role('link', name='Login').is_visible()


# ---------------------------------------------------------------------------
# Scenario 2: User registration
# ---------------------------------------------------------------------------

def test_user_can_register(page, live_server):
    page.goto(f'{live_server}/register')
    page.fill('#username', 'newuser_reg')
    page.fill('#email', 'newuser_reg@example.com')
    page.fill('#password', 'Passw0rd!')
    page.click('button[type="submit"]')
    # Successful registration redirects to /login
    page.wait_for_url(f'{live_server}/login')
    assert page.url == f'{live_server}/login'


# ---------------------------------------------------------------------------
# Scenario 3: Login with valid credentials
# ---------------------------------------------------------------------------

def test_user_can_login(page, live_server, test_user):
    page.goto(f'{live_server}/login')
    page.fill('#username', test_user['username'])
    page.fill('#password', test_user['password'])
    page.click('button[type="submit"]')
    page.wait_for_url(f'{live_server}/')
    # After login the nav shows the username
    assert page.get_by_role('link', name=test_user['username']).is_visible()


# ---------------------------------------------------------------------------
# Scenario 4: Login with wrong password shows error
# ---------------------------------------------------------------------------

def test_login_with_wrong_password_shows_error(page, live_server, test_user):
    page.goto(f'{live_server}/login')
    page.fill('#username', test_user['username'])
    page.fill('#password', 'WrongPassword!')
    page.click('button[type="submit"]')
    # Stays on login page
    assert page.url == f'{live_server}/login'
    # Flash error is visible
    assert page.locator('.flash').count() > 0


# ---------------------------------------------------------------------------
# Scenario 5: Logout redirects to login page
# ---------------------------------------------------------------------------

def test_user_can_logout(logged_in_page, live_server):
    page = logged_in_page
    page.get_by_role('link', name='Logout').click()
    # Logout redirects to the index page; the welcome message confirms the
    # session has ended.
    page.wait_for_url(f'{live_server}/')
    assert page.locator('h1', has_text='Welcome to Price Tracker').is_visible()
