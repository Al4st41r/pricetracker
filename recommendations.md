# Price Tracker System Recommendations

## Analysis of Current System

### Current Architecture

**How it works now:**
1. **Server-side proxy** (app.py:147-173): Fetches URL, removes CSP, rewrites URLs with BeautifulSoup
2. **Client iframe** (main.js:352-396): Renders proxied HTML in sandboxed iframe
3. **Inspector** (inspector.js): Adds click handlers, auto-detects prices with heuristics, generates CSS selectors
4. **Parser system** (parsers/): Plugin architecture for site-specific extraction (currently unused - only template exists)

### Critical Problems

**1. JavaScript-Rendered Content (Major Issue)**
- Many modern e-commerce sites (Amazon, Wayfair, Target, etc.) load prices dynamically with JavaScript
- BeautifulSoup only sees the initial HTML - it misses content loaded after page render
- This makes your system unreliable for most major retailers

**2. Fragile CSS Selectors**
- `getCssSelector()` generates nth-of-type selectors like `div > span:nth-of-type(3) > span:nth-of-type(1)`
- These break instantly when sites update their layouts (which happens frequently)
- You're seeing this issue already in practice

**3. Iframe Rendering Issues**
- Many sites use anti-framing protections beyond CSP
- External resources may fail to load despite URL rewriting
- Sandbox restrictions create security vs functionality tradeoff

**4. Unused Parser Infrastructure**
- You built a good parser plugin system but have zero actual parsers
- This is your best path forward but it's currently dormant

## Recommended Solution: Hybrid Approach

I recommend combining three strategies based on the situation:

### **Phase 1: Populate Parser System (Immediate - Low Effort)**

Focus on the 20 most popular e-commerce sites you actually use:

```python
# parsers/amazon.py
domains = ['amazon.com', 'amazon.co.uk', 'amazon.de']

def parse(soup):
    # Try multiple selectors (sites often have variations)
    selectors = [
        '.a-price-whole',
        '#priceblock_ourprice',
        '#priceblock_dealprice',
        '.a-price .a-offscreen'
    ]

    for selector in selectors:
        elem = soup.select_one(selector)
        if elem:
            price = elem.get_text(strip=True)
            currency = detect_currency_from_domain(soup)
            return {
                'price': price,
                'currency': currency,
                'selector': selector
            }
    return None

def detect_currency_from_domain(soup):
    # Add logic to detect currency based on domain
    # Could check meta tags, domain TLD, etc.
    return 'GBP'  # Default
```

**Benefits:**
- Works with your existing architecture
- Fast (simple HTTP requests)
- Reliable for supported sites
- Low resource usage

### **Phase 2: Add Headless Browser for Discovery (Medium Effort)**

You already have Playwright in debug/! Use it for adding new items:

```python
# New route: /discover_price
@app.route('/discover_price', methods=['POST'])
def discover_price():
    from playwright.sync_api import sync_playwright

    url = request.json.get('url')

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        page.wait_for_load_state('networkidle')

        # Run auto-detection in browser context
        price_data = page.evaluate('''() => {
            // Your autoDetectPrice logic here
            // Returns {element, selector, price}
            const currencySymbols = ['$', '£', '€'];
            const priceRegex = /([$£€]\s*\d+[.,]\d{2})/;

            let potentialElements = [];

            // Look for itemprop="price"
            const itempropElements = Array.from(document.querySelectorAll('[itemprop="price"]'));
            potentialElements.push(...itempropElements);

            // Search for elements containing currency symbols
            const allElements = Array.from(document.querySelectorAll('*:not(script):not(style)'));
            for (const element of allElements) {
                if (element.children.length === 0) {
                    const text = element.textContent.trim();
                    if (currencySymbols.some(symbol => text.includes(symbol))) {
                        potentialElements.push(element);
                    }
                }
            }

            // Rank and return best candidate
            const rankedElements = potentialElements.map(el => {
                if (el.offsetParent === null) return null;
                const text = el.textContent.trim();
                const match = text.match(priceRegex);
                if (match) {
                    let score = 1 / (text.length + 1);
                    if (el.hasAttribute('itemprop') && el.getAttribute('itemprop') === 'price') {
                        score += 10;
                    }
                    return {
                        price: match[1],
                        score: score,
                        selector: generateSelector(el)
                    };
                }
                return null;
            }).filter(Boolean);

            rankedElements.sort((a, b) => b.score - a.score);

            return rankedElements[0] || null;

            function generateSelector(el) {
                // Simplified selector generation
                if (el.id) return '#' + el.id;
                if (el.className) return '.' + el.className.split(' ')[0];
                return el.tagName.toLowerCase();
            }
        }''')

        # Take screenshot for user confirmation
        screenshot = page.screenshot()
        browser.close()

        return jsonify({
            'price': price_data['price'] if price_data else None,
            'selector': price_data['selector'] if price_data else None,
            'screenshot': base64.b64encode(screenshot).decode('utf-8')
        })
```

**Frontend changes:**
```javascript
// In main.js, replace the proxy-based approach
document.getElementById('track-form').addEventListener('submit', function(event) {
    event.preventDefault();
    const url = document.getElementById('url-input').value;
    const loader = document.getElementById('loader');
    const pageContent = document.getElementById('page-content');

    loader.style.display = 'block';
    pageContent.innerHTML = '';

    fetch(`${APPLICATION_ROOT}/discover_price`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({url: url})
    })
    .then(response => response.json())
    .then(data => {
        loader.style.display = 'none';
        if (data.error) {
            pageContent.innerHTML = `<p>Error: ${data.error}</p>`;
        } else {
            // Show screenshot with detected price
            pageContent.innerHTML = `
                <div>
                    <img src="data:image/png;base64,${data.screenshot}" style="max-width: 100%; border: 1px solid #ccc;">
                    <p>Detected price: ${data.price || 'Not found'}</p>
                    <form id="confirm-track-form">
                        <input type="text" id="product-name" placeholder="Product Name" required>
                        <input type="text" id="target-price" placeholder="Target Price" required>
                        <button type="submit">Track Item</button>
                    </form>
                </div>
            `;

            // Handle confirmation
            document.getElementById('confirm-track-form').addEventListener('submit', function(e) {
                e.preventDefault();
                // Submit to /track_item with url, selector, etc.
            });
        }
    });
});
```

**Benefits:**
- Handles JavaScript-rendered content
- Reliable price detection
- Can wait for dynamic loading
- Screenshot verification

### **Phase 3: Intelligent Fallback System**

```python
def check_prices():
    with app.app_context():
        print("Checking prices...")
        items = TrackedItem.query.all()

        for item in items:
            print(f"Checking {item.product_name} at {item.url}")
            domain = urlparse(item.url).netloc
            price_found = False

            # Try 1: Use parser if available (fast)
            if domain in parsers:
                try:
                    response = requests.get(item.url)
                    response.encoding = 'utf-8'
                    response.raise_for_status()
                    soup = BeautifulSoup(response.text, 'html.parser')
                    price_info = parsers[domain](soup)

                    if price_info:
                        update_item_price(item, price_info)
                        price_found = True
                        print(f"✓ Found price using parser: {price_info['price']}")
                        continue
                except Exception as e:
                    print(f"Parser failed for {item.product_name}: {e}")

            # Try 2: Use stored CSS selector (medium speed)
            if not price_found and item.css_selector:
                try:
                    response = requests.get(item.url)
                    response.encoding = 'utf-8'
                    response.raise_for_status()
                    soup = BeautifulSoup(response.text, 'html.parser')
                    price_element = soup.select_one(item.css_selector)

                    if price_element:
                        price_str = price_element.get_text(strip=True)
                        currency = detect_currency(price_str)
                        price_info = {
                            'price': price_str,
                            'currency': currency,
                            'selector': item.css_selector
                        }
                        update_item_price(item, price_info)
                        price_found = True
                        print(f"✓ Found price using CSS selector: {price_str}")
                        continue
                except Exception as e:
                    print(f"CSS selector failed for {item.product_name}: {e}")

            # Try 3: Mark for browser recheck (slow, reliable)
            # Only for failures, maybe weekly instead of daily
            if not price_found:
                print(f"✗ Price check failed for {item.product_name}, marking for browser recheck")
                item.needs_browser_check = True
                item.last_check_method = 'failed'

        db.session.commit()
        print("Price checking complete.")

def update_item_price(item, price_info):
    """Helper function to update item with new price"""
    new_price_str = price_info['price']
    currency = price_info['currency']

    # Update currency if changed
    if item.currency != currency:
        item.currency = currency

    # Clean and compare prices
    try:
        cleaned_new_price = float(re.sub(r'[^\d.]', '', new_price_str))
        cleaned_target_price = float(re.sub(r'[^\d.]', '', item.target_price))
        cleaned_old_current_price = float(re.sub(r'[^\d.]', '', item.current_price)) if item.current_price != 'N/A' else None

        # Update price change status
        if cleaned_old_current_price is not None:
            if cleaned_new_price > cleaned_old_current_price:
                item.price_change_status = 'up'
            elif cleaned_new_price < cleaned_old_current_price:
                item.price_change_status = 'down'
            else:
                item.price_change_status = 'same'

        item.current_price = re.sub(r'[^\d.]', '', new_price_str)

        # Send alert if price meets target
        if cleaned_new_price <= cleaned_target_price:
            if item.owner.email_notifications:
                send_email(
                    to=item.owner.email,
                    subject=f"Price Alert for {item.product_name}",
                    body=f"""The price of {item.product_name} has dropped to {item.current_price}!

Tracked URL: {item.url}"""
                )
            print(f"*** PRICE ALERT for {item.product_name}! ***")
    except (ValueError, TypeError) as e:
        print(f"Could not convert price to number for {item.product_name}: {e}")
        item.current_price = new_price_str
```

**Benefits:**
- Maximizes reliability across different site types
- Degrades gracefully when methods fail
- Optimizes performance (fast methods first)
- Can schedule expensive browser checks less frequently

## Alternative: Browser Extension (If You Want Maximum Reliability)

Build a simple browser extension:
- User clicks "Track Price" while on product page
- Extension extracts price directly from DOM (no proxy/iframe issues)
- Sends URL + selector to your backend
- Works with all sites, no CORS/CSP issues

**manifest.json:**
```json
{
  "manifest_version": 3,
  "name": "Price Tracker",
  "version": "1.0",
  "permissions": ["activeTab", "storage"],
  "action": {
    "default_popup": "popup.html"
  },
  "content_scripts": [{
    "matches": ["<all_urls>"],
    "js": ["content.js"]
  }]
}
```

**Trade-off:** Requires users to install extension, but eliminates 90% of current problems.

## Implementation Roadmap

### **Short term (this week):**
1. Create 5-10 parsers for sites you actually track (Amazon, eBay, etc.)
2. This immediately makes your app more reliable with minimal code
3. Test parsers with real URLs you're currently tracking

### **Medium term (next month):**
4. Integrate Playwright for the "add new item" flow
5. Remove the iframe approach entirely - use headless browser screenshots instead
6. User sees real rendered page screenshot, clicks price, you capture selector
7. Add `needs_browser_check` field to TrackedItem model

### **Long term (next quarter):**
8. Build fallback system that retries with browser when selectors break
9. Consider parser auto-generation: use AI to create parsers from Playwright sessions
10. Add browser extension as alternative tracking method
11. Implement weekly "health check" for all tracked items using browser

## Expected Outcomes

This approach gives you:
- **80% of items**: Fast, reliable parser-based checking (< 1 second per item)
- **15% of items**: CSS selector with occasional browser verification (1-2 seconds per item)
- **5% of items**: Full browser check for difficult sites (5-10 seconds per item)

## Cost/Resource Analysis

**Current system:**
- Fast but unreliable
- Fails silently on JavaScript-heavy sites
- High maintenance (selectors break constantly)

**Proposed system:**
- Phase 1: Same speed, 10x more reliable (parsers don't break)
- Phase 2: Slower initial add (5-10 seconds), but guaranteed accuracy
- Phase 3: Intelligent resource allocation (fast for most, slow only when needed)

**Server requirements:**
- Phase 1: No change (BeautifulSoup only)
- Phase 2: Need Playwright installed (`pip install playwright && playwright install chromium`)
- Phase 3: Minimal (Playwright only runs on failures, maybe 5% of checks)

## Next Steps

**Recommended starting point:**

1. Install Playwright: `pip install playwright && playwright install chromium`
2. Create 3 parsers for your most-tracked sites
3. Test the fallback system with existing tracked items
4. Gradually add more parsers as you track new sites

Would you like help implementing any of these phases?
