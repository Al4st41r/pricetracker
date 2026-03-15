"""
Amazon UK parser for PriceTracker.

Supports: amazon.co.uk, amazon.com, amazon.de, amazon.fr, etc.
"""

import re

domains = [
    'amazon.co.uk',
    'amazon.com',
    'amazon.de',
    'amazon.fr',
    'amazon.es',
    'amazon.it'
]

def parse(soup):
    """
    Parses the price from an Amazon product page.

    Args:
        soup: A BeautifulSoup object representing the page.

    Returns:
        A dictionary with 'price', 'currency', and 'selector' keys,
        or None if the price cannot be found.
    """

    # Amazon has multiple price formats depending on the product type
    # Try each selector in order of reliability
    selectors = [
        # Main price (most common)
        '.a-price.aok-align-center span.a-offscreen',
        '.a-price span.a-offscreen',

        # Deal price
        '#priceblock_dealprice',
        '#priceblock_ourprice',

        # Sale price
        '#priceblock_saleprice',

        # Kindle/Digital content
        '#kindle-price',
        '.kindle-price',

        # Buybox price
        '#buybox .a-price span.a-offscreen',

        # Price whole + fraction combination
        '.a-price-whole',
    ]

    for selector in selectors:
        price_element = soup.select_one(selector)
        if price_element:
            price_text = price_element.get_text(strip=True)

            # Clean up the price text
            # Amazon often includes currency symbol and price together
            if price_text:
                # Detect currency from the price text
                currency = detect_currency(price_text, soup)

                return {
                    'price': price_text,
                    'currency': currency,
                    'selector': selector
                }

    return None


def detect_currency(price_text, soup):
    """
    Detects currency from price text or page metadata.

    Args:
        price_text: The price string
        soup: BeautifulSoup object for fallback detection

    Returns:
        Currency code (e.g., 'GBP', 'USD', 'EUR')
    """
    # Check for currency symbols in price text
    if '£' in price_text:
        return 'GBP'
    elif '$' in price_text:
        # Could be USD, CAD, AUD, etc. - check domain
        return 'USD'
    elif '€' in price_text:
        return 'EUR'

    # Fallback: check meta tags or domain
    # Look for currency in meta tags
    meta_currency = soup.find('meta', attrs={'property': 'product:price:currency'})
    if meta_currency and meta_currency.get('content'):
        return meta_currency['content']

    # Default to GBP (since most tracked sites are .co.uk)
    return 'GBP'
