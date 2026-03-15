"""
Debug Amazon HTML to see what we're actually getting.
"""

import requests
from bs4 import BeautifulSoup

AMAZON_URL = 'https://www.amazon.co.uk/Vox-amPlug3-AP3-AC-Headphone-Amplifier/dp/B0CSJTJF92/'

def debug_amazon():
    print("Fetching Amazon page...")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-GB,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }

    response = requests.get(AMAZON_URL, headers=headers, timeout=15)

    print(f"Status: {response.status_code}")
    print(f"Size: {len(response.text)} bytes")
    print(f"\n" + "=" * 60)
    print("HTML Content (first 3000 chars):")
    print("=" * 60)
    print(response.text[:3000])
    print("=" * 60)

    # Parse and look for price-related elements
    soup = BeautifulSoup(response.text, 'html.parser')

    print("\nSearching for price-related elements...")
    print("=" * 60)

    # Look for elements with 'price' in class or id
    price_elements = soup.find_all(lambda tag: (
        (tag.has_attr('class') and any('price' in c.lower() for c in tag.get('class', []))) or
        (tag.has_attr('id') and 'price' in tag.get('id', '').lower())
    ))

    if price_elements:
        print(f"\nFound {len(price_elements)} price-related elements:")
        for i, elem in enumerate(price_elements[:10], 1):  # Show first 10
            print(f"\n{i}. Tag: {elem.name}")
            if elem.has_attr('class'):
                print(f"   Class: {' '.join(elem.get('class', []))}")
            if elem.has_attr('id'):
                print(f"   ID: {elem.get('id')}")
            text = elem.get_text(strip=True)[:100]
            print(f"   Text: {text}")
    else:
        print("No price-related elements found!")

    # Check for common currency symbols
    print("\n" + "=" * 60)
    print("Checking for currency symbols in text...")
    print("=" * 60)

    text_content = soup.get_text()
    if '£' in text_content:
        print("✓ Found '£' symbol in page")
        # Find context around £ symbol
        lines = text_content.split('\n')
        for line in lines:
            if '£' in line:
                print(f"  {line.strip()}")
                break
    else:
        print("❌ No '£' symbol found")

    if '$' in text_content:
        print("✓ Found '$' symbol in page")
    if '€' in text_content:
        print("✓ Found '€' symbol in page")

if __name__ == '__main__':
    debug_amazon()
