
import unittest
from unittest.mock import patch, MagicMock
from app import app, db, TrackedItem, User, check_prices, update_item_price
import datetime

class TestFallbackSystem(unittest.TestCase):
    def setUp(self):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['TESTING'] = True
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()

        # Create a test user
        self.user = User(username='testuser', email='test@example.com')
        self.user.set_password('password')
        db.session.add(self.user)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    @patch('app.requests.get')
    @patch('app.parsers')
    def test_tier1_parser_success(self, mock_parsers, mock_requests):
        # Setup item
        item = TrackedItem(
            product_name='Test Item',
            url='https://example.com/item',
            css_selector='#price',
            target_price='50.00',
            user_id=self.user.id,
            currency='GBP'
        )
        db.session.add(item)
        db.session.commit()

        # Mock parser
        mock_parsers.__contains__.return_value = True
        mock_parser_func = MagicMock(return_value={'price': '£45.00', 'currency': 'GBP', 'selector': '#price'})
        mock_parsers.__getitem__.return_value = mock_parser_func

        # Mock requests
        mock_requests.return_value.text = '<html></html>'
        mock_requests.return_value.status_code = 200

        check_prices()

        updated_item = TrackedItem.query.get(item.id)
        self.assertEqual(updated_item.current_price, '45.00')
        self.assertEqual(updated_item.last_check_method, 'parser')

    @patch('app.requests.get')
    @patch('app.parsers')
    def test_tier2_css_selector_success(self, mock_parsers, mock_requests):
        # Setup item
        item = TrackedItem(
            product_name='Test Item',
            url='https://example.com/item',
            css_selector='#price',
            target_price='50.00',
            user_id=self.user.id,
            currency='GBP'
        )
        db.session.add(item)
        db.session.commit()

        # Mock parser to fail or not exist
        mock_parsers.__contains__.return_value = False

        # Mock requests with HTML containing price
        mock_requests.return_value.text = '<html><span id="price">£48.00</span></html>'
        mock_requests.return_value.status_code = 200

        check_prices()

        updated_item = TrackedItem.query.get(item.id)
        self.assertEqual(updated_item.current_price, '48.00')
        self.assertEqual(updated_item.last_check_method, 'css_selector')

    @patch('app.browser_check_price')
    @patch('app.requests.get')
    @patch('app.parsers')
    def test_tier3_browser_fallback(self, mock_parsers, mock_requests, mock_browser_check):
        # Setup item
        item = TrackedItem(
            product_name='Test Item',
            url='https://example.com/item',
            css_selector='#wrong-selector',
            target_price='50.00',
            user_id=self.user.id,
            currency='GBP'
        )
        db.session.add(item)
        db.session.commit()

        # Mock parser and CSS selector to fail
        mock_parsers.__contains__.return_value = False
        mock_requests.return_value.text = '<html><span id="real-price">£42.00</span></html>'
        mock_requests.return_value.status_code = 200

        # Mock browser check
        mock_browser_check.return_value = ('£42.00', '#real-price')

        check_prices()

        updated_item = TrackedItem.query.get(item.id)
        self.assertEqual(updated_item.current_price, '42.00')
        self.assertEqual(updated_item.last_check_method, 'browser')
        self.assertEqual(updated_item.css_selector, '#real-price')

    @patch('app.browser_check_price')
    @patch('app.requests.get')
    @patch('app.parsers')
    def test_weekly_browser_check(self, mock_parsers, mock_requests, mock_browser_check):
        # Setup item with needs_browser_check=True and old last_browser_check
        old_date = datetime.datetime.now() - datetime.timedelta(days=8)
        item = TrackedItem(
            product_name='Test Item',
            url='https://example.com/item',
            css_selector='#price',
            target_price='50.00',
            user_id=self.user.id,
            currency='GBP',
            needs_browser_check=True,
            last_browser_check=old_date
        )
        db.session.add(item)
        db.session.commit()

        # Mock parser and CSS selector to succeed (but we expect browser check to trigger anyway due to weekly schedule)
        mock_parsers.__contains__.return_value = False
        mock_requests.return_value.text = '<html><span id="price">£49.00</span></html>'
        mock_requests.return_value.status_code = 200

        # Mock browser check
        mock_browser_check.return_value = ('£47.00', '#price')

        check_prices()

        updated_item = TrackedItem.query.get(item.id)
        # Browser check should override because it happens last and we mocked it to return 47.00
        # and it SHOULD be triggered.
        self.assertEqual(updated_item.current_price, '47.00')
        self.assertEqual(updated_item.last_check_method, 'browser')
        self.assertGreater(updated_item.last_browser_check, old_date)

if __name__ == '__main__':
    unittest.main()
