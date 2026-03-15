"""
Live parser test - fetches real URLs and tests parser extraction.
"""

import requests
from bs4 import BeautifulSoup
from parsers import parsers
from urllib.parse import urlparse

# Test URLs - add real product URLs here
TEST_URLS = [
    # Add real product URLs from your tracked sites
    # Example:
    # 'https://www.amazon.co.uk/dp/B08N5WRWNW',
    # 'https://www.ebay.co.uk/itm/123456789',
]

def test_parser(url):
    """
    Test a parser with a real URL.

    Args:
        url: Product URL to test

    Returns:
        dict with test results
    """
    print(f"\nTesting: {url}")
    print("-" * 60)

    # Extract domain
    parsed_url = urlparse(url)
    domain = parsed_url.netloc

    # Remove www. prefix for matching
    domain_without_www = domain.replace('www.', '')

    # Check if parser exists
    parser = parsers.get(domain) or parsers.get(domain_without_www)

    if not parser:
        print(f"❌ No parser found for domain: {domain}")
        return {
            'url': url,
            'domain': domain,
            'success': False,
            'error': 'No parser found'
        }

    print(f"✓ Parser found for: {domain}")

    # Fetch the page
    try:
        print(f"Fetching URL...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        print(f"✓ Page fetched successfully (Status: {response.status_code})")
    except Exception as e:
        print(f"❌ Failed to fetch page: {e}")
        return {
            'url': url,
            'domain': domain,
            'success': False,
            'error': f'Fetch error: {e}'
        }

    # Parse HTML
    soup = BeautifulSoup(response.text, 'html.parser')

    # Try parser
    try:
        print(f"Running parser...")
        result = parser(soup)

        if result:
            print(f"✓ Parser extracted price successfully!")
            print(f"  Price: {result['price']}")
            print(f"  Currency: {result['currency']}")
            print(f"  Selector: {result['selector']}")
            return {
                'url': url,
                'domain': domain,
                'success': True,
                'price': result['price'],
                'currency': result['currency'],
                'selector': result['selector']
            }
        else:
            print(f"❌ Parser returned None (price not found)")
            return {
                'url': url,
                'domain': domain,
                'success': False,
                'error': 'Parser returned None'
            }
    except Exception as e:
        print(f"❌ Parser error: {e}")
        return {
            'url': url,
            'domain': domain,
            'success': False,
            'error': f'Parser error: {e}'
        }

def main():
    print("=" * 60)
    print("PriceTracker Live Parser Test")
    print("=" * 60)

    if not TEST_URLS:
        print("\n⚠ No test URLs defined!")
        print("\nTo test parsers with real URLs:")
        print("1. Edit this file (test_parser_live.py)")
        print("2. Add product URLs to the TEST_URLS list")
        print("3. Run this script again")
        print("\nExample:")
        print("  TEST_URLS = [")
        print("      'https://www.amazon.co.uk/dp/PRODUCT_ID',")
        print("      'https://www.johnlewis.com/product/...',")
        print("  ]")
        print("\n" + "=" * 60)
        return

    results = []
    for url in TEST_URLS:
        result = test_parser(url)
        results.append(result)

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]

    print(f"\nTotal tests: {len(results)}")
    print(f"✓ Successful: {len(successful)}")
    print(f"❌ Failed: {len(failed)}")

    if successful:
        print("\nSuccessful extractions:")
        for r in successful:
            print(f"  • {r['domain']}: {r['price']} {r['currency']}")

    if failed:
        print("\nFailed extractions:")
        for r in failed:
            print(f"  • {r['domain']}: {r['error']}")

    print("\n" + "=" * 60)

if __name__ == '__main__':
    main()
