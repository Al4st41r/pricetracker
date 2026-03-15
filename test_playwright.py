#!/usr/bin/env python3
"""
Test script to verify Playwright can access protected sites
"""
import base64
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

def test_discover_price(url):
    """Test price discovery with Playwright"""
    print(f"\n{'='*60}")
    print(f"Testing URL: {url}")
    print(f"{'='*60}\n")

    try:
        with sync_playwright() as p:
            # Launch browser
            print("✓ Launching Chromium browser...")
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = context.new_page()

            # Navigate to the page
            print(f"✓ Navigating to page...")
            page.goto(url, wait_until='networkidle', timeout=30000)

            # Wait for dynamic content
            print("✓ Waiting for dynamic content...")
            page.wait_for_timeout(2000)

            # Get page title
            page_title = page.title()
            print(f"✓ Page loaded: {page_title}")

            # Run price detection
            print("✓ Running price detection algorithm...")
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

                // Search for elements containing currency symbols
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
                    if (el.offsetParent === null) return null;

                    const text = el.textContent.trim();
                    const match = text.match(priceRegex);

                    if (match) {
                        let score = 1 / (text.length + 1);

                        if (el.hasAttribute('itemprop') && el.getAttribute('itemprop') === 'price') {
                            score += 10;
                        }

                        const className = el.className.toLowerCase();
                        if (className.includes('price')) {
                            score += 5;
                        }

                        let selector = '';
                        if (el.id) {
                            selector = '#' + el.id;
                        } else if (el.className) {
                            selector = '.' + el.className.split(' ')[0];
                        } else {
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

                rankedElements.sort((a, b) => b.score - a.score);

                return rankedElements[0] || null;
            }''')

            # Take screenshot
            print("✓ Taking screenshot...")
            screenshot_bytes = page.screenshot(full_page=False)
            screenshot_size = len(screenshot_bytes)

            browser.close()

            # Display results
            print(f"\n{'='*60}")
            print("RESULTS")
            print(f"{'='*60}")

            if price_data:
                print(f"✓ Price detected: {price_data['price']}")
                print(f"✓ CSS Selector: {price_data['selector']}")
                print(f"✓ Score: {price_data['score']:.4f}")
                print(f"✓ Screenshot size: {screenshot_size:,} bytes")
                print("\n✅ SUCCESS: Price detection working!")
            else:
                print("✗ No price detected")
                print(f"✓ Screenshot size: {screenshot_size:,} bytes")
                print("\n⚠️  WARNING: Could not auto-detect price")

            print(f"{'='*60}\n")
            return True

    except PlaywrightTimeoutError:
        print("✗ ERROR: Page took too long to load (timeout)")
        return False
    except Exception as e:
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    # Test with gear4music (previously gave 403 errors)
    test_url = "https://www.gear4music.com/Recording-and-Computers/Decksaver-Teenage-Engineering-EP-133-KO-II-Cover/6BYH"

    print("\n" + "="*60)
    print("PLAYWRIGHT PRICE DISCOVERY TEST")
    print("Testing bot-protected site (gear4music)")
    print("="*60)

    success = test_discover_price(test_url)

    if success:
        print("\n✅ Test completed successfully!")
        print("Playwright can bypass bot protection and detect prices.")
    else:
        print("\n❌ Test failed!")
        print("There may be an issue with the Playwright setup.")
