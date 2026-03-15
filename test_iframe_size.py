"""
Test script to check iframe size and take screenshots
"""

from playwright.sync_api import sync_playwright
import time

def test_iframe():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1280, 'height': 720})

        # Navigate to the site
        print("Navigating to PriceTracker...")
        page.goto('http://127.0.0.1:5012/')

        # Wait for page to load
        time.sleep(2)

        # Take screenshot of landing page
        print("Taking screenshot of landing page...")
        page.screenshot(path='/home/pi/WebApps/pricetracker/screenshot_landing.png')
        print("✓ Saved screenshot_landing.png")

        # Check if we need to login
        if page.url.endswith('/login'):
            print("\nNeed to login first...")
            page.fill('#username', 'aogle')
            page.fill('#password', 'test123')  # Replace with actual password
            page.click('button[type="submit"]')
            time.sleep(2)

        # Take screenshot after login
        page.screenshot(path='/home/pi/WebApps/pricetracker/screenshot_after_login.png')
        print("✓ Saved screenshot_after_login.png")

        # Try to track an item
        print("\nTrying to load a product page...")
        page.fill('#url-input', 'https://www.jonesbootmaker.com/products/eastbourne-leather-chelsea-boots-eastbourne-322-611-black')
        page.click('button[type="submit"]')

        # Wait for iframe to load
        print("Waiting for iframe to load...")
        time.sleep(5)

        # Take screenshot with iframe
        page.screenshot(path='/home/pi/WebApps/pricetracker/screenshot_with_iframe.png', full_page=True)
        print("✓ Saved screenshot_with_iframe.png (full page)")

        # Check iframe dimensions
        print("\nChecking iframe dimensions...")

        # Check if page-content exists
        page_content = page.query_selector('#page-content')
        if page_content:
            box = page_content.bounding_box()
            print(f"#page-content dimensions: {box['width']}px × {box['height']}px")
        else:
            print("✗ #page-content not found")

        # Check iframe dimensions
        iframe_elem = page.query_selector('.page-iframe')
        if iframe_elem:
            box = iframe_elem.bounding_box()
            print(f".page-iframe dimensions: {box['width']}px × {box['height']}px")

            # Get computed styles
            styles = page.evaluate('''() => {
                const iframe = document.querySelector('.page-iframe');
                if (iframe) {
                    const computed = window.getComputedStyle(iframe);
                    return {
                        width: computed.width,
                        height: computed.height,
                        minWidth: computed.minWidth,
                        minHeight: computed.minHeight,
                        display: computed.display,
                        position: computed.position
                    };
                }
                return null;
            }''')

            print(f"\nComputed styles:")
            for key, value in styles.items():
                print(f"  {key}: {value}")
        else:
            print("✗ .page-iframe not found")

        print("\n" + "="*60)
        print("Test complete! Check the screenshot files.")
        print("="*60)

        browser.close()

if __name__ == '__main__':
    test_iframe()
