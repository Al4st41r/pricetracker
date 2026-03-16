"""
E2E tests for item detail page and price-alert dispatch.
"""

from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Scenario 9: Item detail page renders product info and price chart
# ---------------------------------------------------------------------------

def test_item_detail_page_shows_product_info(logged_in_page, live_server, test_item):
    page = logged_in_page
    page.goto(f'{live_server}/item/{test_item["id"]}')

    # Heading contains the product name
    assert page.locator('h1', has_text='Test Widget').is_visible()

    # All four info cards render
    assert page.locator('.info-label', has_text='Current Price').is_visible()
    assert page.locator('.info-label', has_text='Target Price').is_visible()
    assert page.locator('.info-label', has_text='Status').is_visible()

    # Chart canvas placeholder is in the DOM
    assert page.locator('#priceChart').count() == 1

    # History table section heading is present
    assert page.locator('h2', has_text='Price History Log').is_visible()

    # Back link returns to the dashboard
    assert page.get_by_role('link', name='← Back to Dashboard').is_visible()


# ---------------------------------------------------------------------------
# Scenario 10: Price alert fires (send_email called) when target price is met
# ---------------------------------------------------------------------------

def test_price_alert_sent_when_target_price_met(app, test_user):
    """
    Verifies the email notification path end-to-end at the application layer.

    A TrackedItem is seeded with current_price above target_price.  The
    price-check scheduler is invoked with requests.get mocked to return a
    price below the target.  send_email must be called at least once for
    this item.
    """
    from app import db, TrackedItem, check_prices

    with app.app_context():
        item = TrackedItem(
            product_name='Alert Test Item',
            url='https://example.com/alert-item',
            css_selector='#price',
            current_price='60.00',
            target_price='50.00',
            price_change_status='same',
            currency='GBP',
            user_id=test_user['id'],
            needs_browser_check=False,
            last_check_method='css_selector',
        )
        db.session.add(item)
        db.session.commit()
        item_id = item.id

    mock_response = MagicMock()
    mock_response.text = '<html><span id="price">£45.00</span></html>'
    mock_response.status_code = 200
    mock_response.encoding = 'utf-8'
    mock_response.raise_for_status = lambda: None

    with app.app_context():
        with patch('app.requests.get', return_value=mock_response), \
             patch('app.parsers', {}), \
             patch('app.send_email') as mock_email:
            check_prices()

        # At least one email sent for the alert item
        assert mock_email.called
        subjects = [call.kwargs.get('subject', '') or (call.args[1] if len(call.args) > 1 else '')
                    for call in mock_email.call_args_list]
        assert any('Alert Test Item' in s for s in subjects)

        updated = TrackedItem.query.get(item_id)
        assert float(updated.current_price) == 45.00
        assert updated.price_change_status == 'down'
