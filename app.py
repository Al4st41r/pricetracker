# app.py

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import requests
from bs4 import BeautifulSoup
import schedule
import time
import csv
import os
import re
import threading
import base64
from werkzeug.middleware.proxy_fix import ProxyFix
from urllib.parse import urljoin, urlparse
from datetime import datetime, timedelta
from parsers import parsers
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

APP_VERSION = "0.6.0"

app = Flask(__name__)
app.config['SECRET_KEY'] = 'a_super_secret_key' # Replace with a real secret key in production
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'pricetracker.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- Database Models ---

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    email_notifications = db.Column(db.Boolean, default=True)
    items = db.relationship('TrackedItem', backref='owner', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class TrackedItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    css_selector = db.Column(db.String(500), nullable=False)
    current_price = db.Column(db.String(50))
    target_price = db.Column(db.String(50))
    price_change_status = db.Column(db.String(10))
    currency = db.Column(db.String(10))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    needs_browser_check = db.Column(db.Boolean, default=False)
    last_check_method = db.Column(db.String(50))
    last_browser_check = db.Column(db.DateTime)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))




def detect_currency(price_str):
    if not isinstance(price_str, str):
        return 'GBP'
    if '€' in price_str:
        return 'EUR'
    if '$' in price_str:
        return 'USD'
    if '£' in price_str:
        return 'GBP'
    return 'GBP' # Default currency

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user is None or not user.check_password(request.form.get('password')):
            flash('Invalid username or password', 'error')
            return redirect(url_for('login'))
        login_user(user, remember=True)
        flash('Logged in successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        if User.query.filter_by(username=request.form.get('username')).first():
            flash('Username already exists', 'error')
            return redirect(url_for('register'))
        if User.query.filter_by(email=request.form.get('email')).first():
            flash('Email address already in use', 'error')
            return redirect(url_for('register'))
        user = User(username=request.form.get('username'), email=request.form.get('email'))
        user.set_password(request.form.get('password'))
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')


@app.route('/reset_password_request', methods=['POST'])
@login_required
def reset_password_request():
    # In a real application, you would generate a secure token
    # and send an email with a password reset link.
    flash('A password reset link has been sent to your email address.', 'success')
    send_email(
        to=current_user.email,
        subject='Password Reset Request',
        body='Please click the link to reset your password'
    )
    return redirect(url_for('settings'))

@app.route('/debug')
def debug():
    return jsonify(dict(request.headers))

@app.route('/proxy')
def proxy():
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'URL is required'}), 400

    # Validate URL format
    if not url.startswith('http'):
        return jsonify({'error': 'Invalid URL format. URL must start with http:// or https://'}), 400

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        response.raise_for_status()  # Raise an exception for bad status codes

        soup = BeautifulSoup(response.text, 'html.parser')

        # Remove CSP meta tags
        for tag in soup.find_all('meta', attrs={'http-equiv': re.compile('Content-Security-Policy', re.IGNORECASE)}):
            tag.decompose()

        base_url = response.url

        # Rewrite relative URLs to absolute URLs
        for tag in soup.find_all(['link', 'script', 'img'], href=True):
            tag['href'] = urljoin(base_url, tag['href'])
        for tag in soup.find_all(['script', 'img'], src=True):
            tag['src'] = urljoin(base_url, tag['src'])

        return jsonify({'html': str(soup)})
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if e.response else 0
        if status_code == 403:
            return jsonify({'error': 'This website is blocking automated access (403 Forbidden). This site requires browser emulation to track prices.'}), 403
        elif status_code == 404:
            return jsonify({'error': 'Product page not found (404). Please check the URL is correct.'}), 404
        else:
            return jsonify({'error': f'HTTP {status_code} error accessing this website.'}), 500
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Request timed out. The website took too long to respond.'}), 500
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Could not access website: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

@app.route('/discover_price', methods=['POST'])
@login_required
def discover_price():
    """
    Use Playwright to discover price on a product page.
    Handles JavaScript-rendered content and bot protection.
    """
    data = request.get_json()
    url = data.get('url')

    if not url:
        return jsonify({'error': 'URL is required'}), 400

    if not url.startswith('http'):
        return jsonify({'error': 'Invalid URL format'}), 400

    try:
        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = context.new_page()

            # Navigate to the page
            print(f"Navigating to {url}...")
            page.goto(url, wait_until='networkidle', timeout=30000)

            # Wait a bit for any dynamic content
            page.wait_for_timeout(2000)

            # Get page title
            page_title = page.title()

            # Run auto-detection script in browser context
            price_data = page.evaluate('''() => {
                const currencySymbols = ['£', '$', '€'];
                const priceRegex = /([£$€]\\s*\\d+[.,]\\d{2})/;

                let potentialElements = [];

                // Look for itemprop="price"
                const itempropElements = Array.from(document.querySelectorAll('[itemprop="price"]'));
                potentialElements.push(...itempropElements);

                // Look for common price class names
                const priceClassElements = Array.from(document.querySelectorAll('[class*="price"], [class*="Price"]'));
                potentialElements.push(...priceClassElements);

                // Search for elements containing currency symbols (leaf nodes only)
                const allElements = Array.from(document.querySelectorAll('*'));
                for (const element of allElements) {
                    if (element.children.length === 0) {
                        const text = element.textContent.trim();
                        if (currencySymbols.some(symbol => text.includes(symbol))) {
                            potentialElements.push(element);
                        }
                    }
                }

                // Rank elements
                const rankedElements = potentialElements.map(el => {
                    // Skip hidden elements
                    if (el.offsetParent === null) return null;

                    const text = el.textContent.trim();
                    const match = text.match(priceRegex);

                    if (match) {
                        let score = 1 / (text.length + 1);

                        // Boost score for semantic markup
                        if (el.hasAttribute('itemprop') && el.getAttribute('itemprop') === 'price') {
                            score += 10;
                        }

                        // Boost score for price-related classes
                        const className = el.className.toLowerCase();
                        if (className.includes('price')) {
                            score += 5;
                        }

                        // Generate selector
                        let selector = '';
                        if (el.id) {
                            selector = '#' + el.id;
                        } else if (el.className) {
                            selector = '.' + el.className.split(' ')[0];
                        } else {
                            // Fallback to tag name
                            selector = el.tagName.toLowerCase();
                        }

                        return {
                            price: match[1],
                            score: score,
                            selector: selector,
                            text: text
                        };
                    }
                    return null;
                }).filter(Boolean);

                // Sort by score
                rankedElements.sort((a, b) => b.score - a.score);

                return rankedElements[0] || null;
            }''')

            # Take screenshot
            screenshot_bytes = page.screenshot(full_page=False)
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')

            browser.close()

            if price_data:
                return jsonify({
                    'success': True,
                    'price': price_data['price'],
                    'selector': price_data['selector'],
                    'page_title': page_title,
                    'screenshot': screenshot_base64
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Could not auto-detect price on this page. Please use the manual inspector.',
                    'page_title': page_title,
                    'screenshot': screenshot_base64
                })

    except PlaywrightTimeoutError:
        return jsonify({'error': 'Page took too long to load. Please try again.'}), 500
    except Exception as e:
        print(f"Error in discover_price: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error loading page: {str(e)}'}), 500

@app.route('/track_item', methods=['POST'])
@login_required
def track_item():
    print("Received request to track item.")
    url = request.form.get('url')
    css_selector = request.form.get('css_selector')
    target_price = request.form.get('target_price')
    product_name = request.form.get('product_name', 'N/A')
    print(f"Form data received: URL={url}, Selector={css_selector}, Target={target_price}, Product={product_name}")

    if not all([url, target_price]):
        return jsonify({'error': 'URL and target price are required'}), 400

    try:
        formatted_target_price = "{:.2f}".format(float(target_price))
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid target price format'}), 400

    current_price_str_raw = 'N/A'
    currency = 'GBP'
    current_price = 'N/A'
    last_check_method = 'unknown'
    needs_browser_check = False

    domain = urlparse(url).netloc
    if domain in parsers:
        try:
            response = requests.get(url, timeout=10)
            response.encoding = 'utf-8'
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            price_info = parsers[domain](soup)
            if price_info:
                current_price_str_raw = price_info['price']
                currency = price_info['currency']
                css_selector = price_info['selector']
                current_price = re.sub(r'[^\d.]', '', current_price_str_raw)
                last_check_method = 'parser'
            else:
                return jsonify({'error': 'Could not find the price for the given URL.'}), 400
        except requests.exceptions.RequestException as e:
            return jsonify({'error': f'Error fetching URL: {e}'}), 500
    else:
        if not css_selector:
            return jsonify({'error': 'CSS selector is required for unsupported websites.'}), 400
        try:
            response = requests.get(url, timeout=10)
            response.encoding = 'utf-8'
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            price_element = soup.select_one(css_selector)
            if price_element:
                current_price_str_raw = price_element.get_text(strip=True)
                currency = detect_currency(current_price_str_raw)
                current_price = re.sub(r'[^\d.]', '', current_price_str_raw)
                last_check_method = 'css_selector'
            else:
                print(f"CSS selector failed during initial tracking for {url}")
                # If CSS selector fails immediately, maybe it needs browser check
                needs_browser_check = True
        except requests.exceptions.RequestException as e:
            print(f"Error fetching current price for {url} during tracking: {e}")
            needs_browser_check = True
        except Exception as e:
            print(f"An unexpected error occurred while getting current price for {url}: {e}")
            needs_browser_check = True

    new_item = TrackedItem(
        product_name=product_name,
        url=url,
        css_selector=css_selector,
        current_price=current_price,
        target_price=formatted_target_price,
        price_change_status='new',
        currency=currency,
        user_id=current_user.id,
        needs_browser_check=needs_browser_check,
        last_check_method=last_check_method
    )
    db.session.add(new_item)
    db.session.commit()
    return jsonify({'message': 'Item tracked successfully'}), 200

@app.route('/get_tracked_items')
@login_required
def get_tracked_items():
    print(f"Getting tracked items for user {current_user.id}")
    items = TrackedItem.query.filter_by(user_id=current_user.id).all()
    print(f"Found {len(items)} items for user {current_user.id}")
    return jsonify([{
        'id': item.id,
        'Product Name': item.product_name,
        'URL': item.url,
        'CSS Selector': item.css_selector,
        'Current Price': item.current_price,
        'Target Price': item.target_price,
        'Price Change Status': item.price_change_status,
        'Currency': item.currency,
        'Needs Browser Check': item.needs_browser_check,
        'Last Check Method': item.last_check_method,
        'Last Browser Check': item.last_browser_check.isoformat() if item.last_browser_check else None
    } for item in items])

@app.route('/delete_item', methods=['POST'])
@login_required
def delete_item():
    item_id = request.form.get('id')
    item = TrackedItem.query.get_or_404(item_id)
    if item.owner != current_user:
        return jsonify({'error': 'Forbidden'}), 403
    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'Item deleted successfully'}), 200

@app.route('/update_item', methods=['POST'])
@login_required
def update_item():
    item_id = request.form.get('id')
    item = TrackedItem.query.get_or_404(item_id)
    if item.owner != current_user:
        return jsonify({'error': 'Forbidden'}), 403

    new_product_name = request.form.get('product_name')
    new_target_price = request.form.get('target_price')

    if not all([new_product_name, new_target_price]):
        return jsonify({'error': 'Missing data for update'}), 400

    try:
        formatted_target_price = "{:.2f}".format(float(new_target_price))
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid target price format for update'}), 400

    item.product_name = new_product_name
    item.target_price = formatted_target_price
    db.session.commit()

    return jsonify({'message': 'Item updated successfully'}), 200

def update_item_price(item, new_price_str, method):
    """
    Update item price data and handle alerts.
    """
    detected_currency = detect_currency(new_price_str)
    
    # Update currency if it changed
    if item.currency != detected_currency:
        item.currency = detected_currency

    try:
        cleaned_new_price = float(re.sub(r'[^\d.]', '', new_price_str))
        cleaned_target_price = float(re.sub(r'[^\d.]', '', item.target_price))
        cleaned_old_current_price = None
        if item.current_price and item.current_price != 'N/A':
            try:
                cleaned_old_current_price = float(re.sub(r'[^\d.]', '', item.current_price))
            except (ValueError, TypeError):
                cleaned_old_current_price = None

        if cleaned_old_current_price is not None:
            if cleaned_new_price > cleaned_old_current_price:
                item.price_change_status = 'up'
            elif cleaned_new_price < cleaned_old_current_price:
                item.price_change_status = 'down'
            else:
                item.price_change_status = 'same'
        else:
            item.price_change_status = 'new'

        item.current_price = "{:.2f}".format(cleaned_new_price)
        item.last_check_method = method

        if cleaned_new_price <= cleaned_target_price:
            if item.owner.email_notifications:
                send_email(
                    to=item.owner.email,
                    subject=f"Price Alert for {item.product_name}",
                    body=f"""The price of {item.product_name} has dropped to {item.currency}{item.current_price}!

Tracked URL: {item.url}"""
                )
            alert_message = f"""*** PRICE ALERT! ***
Product: {item.product_name}
URL: {item.url}
New Price: {item.currency}{item.current_price}
Target Price: {item.currency}{item.target_price}
"""
            print(alert_message)
        return True
    except (ValueError, TypeError) as e:
        print(f"Could not convert price to number for {item.product_name}: {e}")
        # Keep original string if conversion fails
        item.current_price = new_price_str
        item.last_check_method = method
        return True

def browser_check_price(url):
    """
    Use Playwright to get price from a URL.
    Returns (price_str, selector) or (None, None).
    """
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = context.new_page()
            page.goto(url, wait_until='networkidle', timeout=30000)
            page.wait_for_timeout(2000)

            # Use the same auto-detection script as discover_price
            price_data = page.evaluate('''() => {
                const currencySymbols = ['£', '$', '€'];
                const priceRegex = /([£$€]\\s*\\d+[.,]\\d{2})/;
                let potentialElements = [];
                const itempropElements = Array.from(document.querySelectorAll('[itemprop="price"]'));
                potentialElements.push(...itempropElements);
                const priceClassElements = Array.from(document.querySelectorAll('[class*="price"], [class*="Price"]'));
                potentialElements.push(...priceClassElements);
                const allElements = Array.from(document.querySelectorAll('*'));
                for (const element of allElements) {
                    if (element.children.length === 0) {
                        const text = element.textContent.trim();
                        if (currencySymbols.some(symbol => text.includes(symbol))) {
                            potentialElements.push(element);
                        }
                    }
                }
                const rankedElements = potentialElements.map(el => {
                    if (el.offsetParent === null) return null;
                    const text = el.textContent.trim();
                    const match = text.match(priceRegex);
                    if (match) {
                        let score = 1 / (text.length + 1);
                        if (el.hasAttribute('itemprop') && el.getAttribute('itemprop') === 'price') score += 10;
                        const className = el.className.toLowerCase();
                        if (className.includes('price')) score += 5;
                        let selector = el.id ? '#' + el.id : (el.className ? '.' + el.className.split(' ')[0] : el.tagName.toLowerCase());
                        return { price: match[1], score: score, selector: selector };
                    }
                    return null;
                }).filter(Boolean);
                rankedElements.sort((a, b) => b.score - a.score);
                return rankedElements[0] || null;
            }''')
            browser.close()
            if price_data:
                return price_data['price'], price_data['selector']
    except Exception as e:
        print(f"Browser check failed for {url}: {e}")
    return None, None

def check_prices():
    with app.app_context():
        print("Checking prices...")
        items = TrackedItem.query.all()
        for item in items:
            print(f"Checking {item.product_name} at {item.url}")
            new_price_str = None
            method = None
            
            # Tier 1: Site-specific Parser
            domain = urlparse(item.url).netloc
            if domain in parsers:
                try:
                    response = requests.get(item.url, timeout=10)
                    response.encoding = 'utf-8'
                    soup = BeautifulSoup(response.text, 'html.parser')
                    price_info = parsers[domain](soup)
                    if price_info:
                        new_price_str = price_info['price']
                        method = 'parser'
                        print(f"Parser success for {item.product_name}")
                except Exception as e:
                    print(f"Parser failed for {item.product_name}: {e}")

            # Tier 2: CSS Selector (BeautifulSoup)
            if not new_price_str and item.css_selector:
                try:
                    response = requests.get(item.url, timeout=10)
                    response.encoding = 'utf-8'
                    soup = BeautifulSoup(response.text, 'html.parser')
                    price_element = soup.select_one(item.css_selector)
                    if price_element:
                        new_price_str = price_element.get_text(strip=True)
                        method = 'css_selector'
                        print(f"CSS selector success for {item.product_name}")
                except Exception as e:
                    print(f"CSS selector failed for {item.product_name}: {e}")

            # Tier 3: Browser Recheck (Playwright)
            time_for_weekly_check = False
            if item.needs_browser_check:
                if not item.last_browser_check or (datetime.now() - item.last_browser_check) > timedelta(days=7):
                    time_for_weekly_check = True

            if not new_price_str or time_for_weekly_check:
                reason = "Failure" if not new_price_str else "Weekly check"
                print(f"Attempting browser check for {item.product_name} (Reason: {reason})")
                browser_price, new_selector = browser_check_price(item.url)
                if browser_price:
                    # If we got here because of failure, mark as needs browser
                    if not new_price_str:
                        item.needs_browser_check = True
                    
                    new_price_str = browser_price
                    method = 'browser'
                    item.last_browser_check = datetime.now()
                    # If we found a new selector, update it
                    if new_selector and new_selector != item.css_selector:
                        item.css_selector = new_selector
                    print(f"Browser check success for {item.product_name}")
                else:
                    print(f"Browser check failed for {item.product_name}")

            if new_price_str:
                update_item_price(item, new_price_str, method)

        db.session.commit()
        print("Price checking complete.")


def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1) # check every 1 second

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    # Schedule the price checking function to run once a day
    schedule.every().day.at("00:00").do(check_prices) # Run at midnight

    # Start the scheduler in a separate thread
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True # Daemonize thread so it exits when main program exits
    scheduler_thread.start()

    app.run(debug=True, port=5012)

def send_email(to, subject, body):
    # This is a dummy email function. In a real application, you would use
    # a library like smtplib to send emails.
    print("---- SENDING EMAIL ----")
    print(f"To: {to}")
    print(f"Subject: {subject}")
    print(f"Body: {body}")
    print("-----------------------")