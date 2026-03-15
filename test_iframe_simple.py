"""
Simple test to check landing page and iframe container
"""

from playwright.sync_api import sync_playwright
import time

def test_landing_page():
    print("Starting Playwright test...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 720})
        page = context.new_page()

        # Navigate to the site
        print("\n1. Testing landing page...")
        page.goto('http://127.0.0.1:5012/')
        time.sleep(2)

        # Take screenshot of landing page
        page.screenshot(path='/home/pi/WebApps/pricetracker/screenshot_landing.png')
        print("   ✓ Screenshot saved: screenshot_landing.png")
        print(f"   URL: {page.url}")
        print(f"   Title: {page.title()}")

        # Check if #page-content exists (should be on authenticated page)
        page_content = page.query_selector('#page-content')
        if page_content:
            print("\n2. Found #page-content element")
            box = page_content.bounding_box()
            if box:
                print(f"   Dimensions: {box['width']}px × {box['height']}px")
        else:
            print("\n2. #page-content not found (user not logged in)")

        # Check for track form
        track_form = page.query_selector('#track-form')
        if track_form:
            print("\n3. Found #track-form")
        else:
            print("\n3. #track-form not found")

        browser.close()
        print("\n" + "="*60)
        print("Test complete!")
        print("Screenshot saved to: screenshot_landing.png")
        print("="*60)

if __name__ == '__main__':
    test_landing_page()
