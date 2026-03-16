"""
E2E tests for the main dashboard: authenticated view and adding a tracked item.
"""

from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Scenario 6: Authenticated dashboard renders the tracker UI
# ---------------------------------------------------------------------------

def test_authenticated_dashboard_shows_tracker_ui(logged_in_page, live_server, test_user):
    page = logged_in_page
    page.goto(f'{live_server}/')
    # "Track a New Item" section must be visible
    assert page.locator('h2', has_text='Track a New Item').is_visible()
    # URL input present
    assert page.locator('#url-input').is_visible()
    # Nav username link present
    assert page.get_by_role('link', name=test_user['username']).is_visible()


# ---------------------------------------------------------------------------
# Scenario 7: Dashboard AJAX endpoint returns tracked items
# ---------------------------------------------------------------------------

def test_dashboard_ajax_returns_tracked_items(logged_in_page, live_server, test_item):
    """
    /get_tracked_items must return JSON containing the seeded item.
    Uses page.request so it inherits the authenticated session cookie.
    """
    page = logged_in_page
    # Ensure we're logged in (navigate to the dashboard first)
    page.goto(f'{live_server}/')
    page.wait_for_load_state('networkidle')

    response = page.request.get(f'{live_server}/get_tracked_items')
    assert response.status == 200
    items = response.json()
    assert len(items) >= 1
    assert any(i['Product Name'] == 'Test Widget' for i in items)


# ---------------------------------------------------------------------------
# Scenario 8: Add tracked item via the /track_item API
# ---------------------------------------------------------------------------

def test_add_tracked_item_via_api(logged_in_page, live_server, app):
    """
    Posts directly to /track_item with a mocked HTTP fetch so no real
    network request is made.  Verifies the response and database state.
    """
    page = logged_in_page

    mock_response = MagicMock()
    mock_response.text = '<html><span id="price">£29.99</span></html>'
    mock_response.status_code = 200
    mock_response.encoding = 'utf-8'
    mock_response.raise_for_status = lambda: None

    with patch('app.requests.get', return_value=mock_response):
        response = page.request.post(
            f'{live_server}/track_item',
            form={
                'url': 'https://example.com/new-product',
                'css_selector': '#price',
                'target_price': '25.00',
                'product_name': 'API-Added Product',
            },
        )

    assert response.status == 200
    data = response.json()
    assert data.get('message') == 'Item tracked successfully'

    # Verify it persists in the database
    with app.app_context():
        from app import TrackedItem
        item = TrackedItem.query.filter_by(product_name='API-Added Product').first()
        assert item is not None
        assert item.target_price == '25.00'
