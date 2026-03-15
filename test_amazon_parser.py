"""
Quick test of Amazon parser with tracked item.
"""

import requests
from bs4 import BeautifulSoup
from parsers import parsers
from urllib.parse import urlparse

# Amazon product from tracked items
AMAZON_URL = 'https://www.amazon.co.uk/Vox-amPlug3-AP3-AC-Headphone-Amplifier/dp/B0CSJTJF92/'

def test_amazon():
    print("=" * 60)
    print("Testing Amazon UK Parser")
    print("=" * 60)
    print(f"\nURL: {AMAZON_URL}")
    print("-" * 60)

    # Check parser exists
    domain = 'amazon.co.uk'
    if domain not in parsers:
        print(f"❌ Parser not found for {domain}")
        return

    print(f"✓ Parser found for {domain}")

    # Fetch page
    print(f"\nFetching page...")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(AMAZON_URL, headers=headers, timeout=15)
        response.raise_for_status()
        print(f"✓ Page fetched (Status: {response.status_code}, Size: {len(response.text)} bytes)")
    except Exception as e:
        print(f"❌ Fetch failed: {e}")
        return

    # Parse
    print(f"\nParsing HTML...")
    soup = BeautifulSoup(response.text, 'html.parser')

    # Run parser
    print(f"Running parser...")
    try:
        result = parsers[domain](soup)

        if result:
            print(f"\n✓ SUCCESS!")
            print(f"-" * 60)
            print(f"Price:     {result['price']}")
            print(f"Currency:  {result['currency']}")
            print(f"Selector:  {result['selector']}")
            print(f"-" * 60)
        else:
            print(f"\n❌ Parser returned None")
            print(f"Price element not found with any known selectors")

    except Exception as e:
        print(f"\n❌ Parser error: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)

if __name__ == '__main__':
    test_amazon()
