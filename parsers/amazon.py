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
    selectors = [
        # Main price (most common)
        '.a-price.aok-align-center span.a-offscreen',
        '.a-price span.a-offscreen',
        '#price_inside_buybox',
        '#newBuyBoxPrice',
        '.a-size-medium.a-color-price.header-price',

        # Deal price
        '#priceblock_dealprice',
        '#priceblock_ourprice',
        '[data-asin-price]',

        # Sale price
        '#priceblock_saleprice',
        '.priceBlockStrikePriceString',

        # Kindle/Digital content
        '#kindle-price',
        '.kindle-price',
        '#price',

        # Buybox price
        '#buybox .a-price span.a-offscreen',

        # Price whole + fraction combination
        '.a-price-whole',
        
        # Fallback meta tags
        'meta[property="product:price:amount"]',
        'meta[property="og:price:amount"]',
        'meta[itemprop="price"]',
        '[itemprop="price"]',
    ]

    for selector in selectors:
        price_element = soup.select_one(selector)
        if price_element:
            if price_element.name == 'meta':
                price_text = price_element.get('content', '')
            else:
                price_text = price_element.get_text(strip=True)

            # Clean up the price text
            if price_text:
                # Detect currency
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
    if '£' in price_text or 'GBP' in price_text.upper():
        return 'GBP'
    elif '$' in price_text or 'USD' in price_text.upper():
        return 'USD'
    elif '€' in price_text or 'EUR' in price_text.upper():
        return 'EUR'

    # Look for currency in meta tags
    meta_currency = soup.find('meta', attrs={'property': 'product:price:currency'})
    if not meta_currency:
        meta_currency = soup.find('meta', attrs={'itemprop': 'priceCurrency'})
    
    if meta_currency and meta_currency.get('content'):
        return meta_currency['content']

    # Default to GBP (since most tracked sites are .co.uk)
    return 'GBP'
